#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_VERSIONS = ("2025-11-25", "2025-06-18")
REQUIRED_TOOLS = {
    "xml_validate_schema",
    "xml_format",
    "xpath_evaluate",
    "xquery_evaluate",
    "xquery_validate",
}
VALIDATION_OK = "Valid: XML conforms to the schema."

ADAPTER_PATH = ROOT / "skills" / "feature-map-workflow" / "scripts" / "xquery_result.py"
SPEC = importlib.util.spec_from_file_location("feature_map_xquery_result", ADAPTER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {ADAPTER_PATH}")
ADAPTER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ADAPTER
SPEC.loader.exec_module(ADAPTER)
parse_query_result = ADAPTER.parse_query_result


class McpProcess:
    def __init__(self) -> None:
        self.proc = subprocess.Popen(
            ["dotnet", "tool", "run", "xquery-mcp"],
            cwd=ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        if self.proc.stdin is None or self.proc.stdout is None:
            raise RuntimeError("failed to open xquery-mcp stdio")
        self.messages: queue.Queue[dict[str, Any]] = queue.Queue()
        self.reader = threading.Thread(target=self._read_stdout, daemon=True)
        self.reader.start()

    def _read_stdout(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError as exc:
                self.messages.put({"_decode_error": f"{exc}: {line[:500]}"})
                continue
            if isinstance(message, dict):
                self.messages.put(message)

    def send(self, message: dict[str, Any]) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        self.proc.stdin.flush()

    def response(self, request_id: int, timeout: float = 15.0) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"timeout waiting for JSON-RPC id={request_id}")
            message = self.messages.get(timeout=remaining)
            if "_decode_error" in message:
                raise RuntimeError(message["_decode_error"])
            if message.get("id") == request_id:
                return message

    def call_tool(self, request_id: int, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            }
        )
        response = self.response(request_id)
        if "error" in response:
            raise RuntimeError(f"{name} JSON-RPC error: {response['error']}")
        return response.get("result", {})

    def close(self) -> None:
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=5)


def try_protocol(protocol_version: str) -> tuple[bool, str]:
    mcp = McpProcess()
    try:
        mcp.send(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": protocol_version,
                    "capabilities": {},
                    "clientInfo": {
                        "name": "feature-map-workflow-ci",
                        "version": "1.0.0",
                    },
                },
            }
        )
        initialized = mcp.response(1)
        if "error" in initialized:
            return False, f"initialize {protocol_version}: {initialized['error']}"

        negotiated = initialized.get("result", {}).get("protocolVersion")
        mcp.send({"jsonrpc": "2.0", "method": "notifications/initialized"})

        mcp.send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        listed = mcp.response(2)
        if "error" in listed:
            return False, f"tools/list: {listed['error']}"

        tools = listed.get("result", {}).get("tools", [])
        names = {tool.get("name") for tool in tools if isinstance(tool, dict)}
        missing = sorted(REQUIRED_TOOLS - names)
        if missing:
            return False, f"required MCP tools missing: {missing}"

        xml = "<root><value>ok</value></root>"
        xsd = (
            '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
            '<xs:element name="root"><xs:complexType><xs:sequence>'
            '<xs:element name="value" type="xs:string"/>'
            "</xs:sequence></xs:complexType></xs:element></xs:schema>"
        )
        validation = mcp.call_tool(3, "xml_validate_schema", {"xml": xml, "xsd": xsd})
        validation_text = json.dumps(validation, ensure_ascii=False)
        if VALIDATION_OK not in validation_text:
            return False, f"xml_validate_schema contract changed: {validation_text[:1000]}"

        xpath = parse_query_result(
            mcp.call_tool(4, "xpath_evaluate", {"xpath": "/root/value/text()", "xml": xml})
        )
        if not xpath.ok or xpath.value != "ok":
            return False, f"xpath_evaluate structured result unexpected: {xpath.to_dict()}"

        empty = parse_query_result(
            mcp.call_tool(5, "xquery_evaluate", {"query": "()"})
        )
        if not empty.is_empty_sequence:
            return False, f"xquery_evaluate empty-sequence contract changed: {empty.to_dict()}"

        invalid = parse_query_result(
            mcp.call_tool(6, "xquery_validate", {"query": "for $x in"})
        )
        if invalid.ok or not invalid.errors or not invalid.errors[0].code:
            return False, f"xquery_validate error contract changed: {invalid.to_dict()}"

        print(
            "xquery-mcp MCP smoke test passed "
            f"(requested={protocol_version}, negotiated={negotiated or 'unknown'}, "
            f"xpath=ok, empty=count0, error={invalid.errors[0].code})"
        )
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
    finally:
        mcp.close()


def main() -> int:
    failures: list[str] = []
    for protocol_version in PROTOCOL_VERSIONS:
        ok, detail = try_protocol(protocol_version)
        if ok:
            return 0
        failures.append(detail)
    print("xquery-mcp MCP smoke test failed:", file=sys.stderr)
    for failure in failures:
        print(f"- {failure}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
