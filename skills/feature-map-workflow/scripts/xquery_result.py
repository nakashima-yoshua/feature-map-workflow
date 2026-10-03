#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from typing import Any


class QueryResultContractError(ValueError):
    pass


@dataclass(frozen=True)
class QueryError:
    code: str
    message: str
    line: int | None = None
    column: int | None = None
    source_snippet: str | None = None
    spec_url: str | None = None


@dataclass(frozen=True)
class QueryResult:
    ok: bool
    value: str | None
    count: int | None
    elapsed_ms: int | None
    errors: tuple[QueryError, ...]

    @property
    def is_empty_sequence(self) -> bool:
        return self.ok and self.count == 0 and self.value is None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "value": self.value,
            "count": self.count,
            "elapsed_ms": self.elapsed_ms,
            "errors": [asdict(error) for error in self.errors],
        }


def _json_object(value: Any, depth: int = 0) -> dict[str, Any]:
    if depth > 6:
        raise QueryResultContractError("QueryResult nesting is too deep")

    if isinstance(value, dict):
        if isinstance(value.get("ok"), bool):
            return value

        content = value.get("content")
        if isinstance(content, list):
            candidates: list[dict[str, Any]] = []
            for part in content:
                if not isinstance(part, dict) or part.get("type") != "text":
                    continue
                text = part.get("text")
                if not isinstance(text, str):
                    continue
                try:
                    candidates.append(_json_object(text, depth + 1))
                except QueryResultContractError:
                    pass
            if len(candidates) == 1:
                return candidates[0]
            if len(candidates) > 1:
                raise QueryResultContractError("multiple QueryResult JSON objects found in MCP content")

        for key in ("result", "tool_response", "toolResponse", "value"):
            if key in value:
                try:
                    return _json_object(value[key], depth + 1)
                except QueryResultContractError:
                    pass

        raise QueryResultContractError("no QueryResult JSON object found in mapping")

    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise QueryResultContractError("empty QueryResult text")
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError as exc:
            raise QueryResultContractError(f"QueryResult text is not JSON: {exc}") from exc
        return _json_object(decoded, depth + 1)

    raise QueryResultContractError(f"unsupported QueryResult payload type: {type(value).__name__}")


def _optional_int(obj: dict[str, Any], key: str) -> int | None:
    value = obj.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise QueryResultContractError(f"{key} must be an integer or null")
    return value


def _optional_str(obj: dict[str, Any], key: str) -> str | None:
    value = obj.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise QueryResultContractError(f"{key} must be a string or null")
    return value


def parse_query_result(payload: Any) -> QueryResult:
    obj = _json_object(payload)

    ok = obj.get("ok")
    if not isinstance(ok, bool):
        raise QueryResultContractError("ok must be a boolean")

    value = _optional_str(obj, "value")
    count = _optional_int(obj, "count")
    elapsed_ms = _optional_int(obj, "elapsedMs")

    raw_errors = obj.get("errors")
    if raw_errors is None:
        raw_errors = []
    if not isinstance(raw_errors, list):
        raise QueryResultContractError("errors must be an array or null")

    errors: list[QueryError] = []
    for index, raw in enumerate(raw_errors):
        if not isinstance(raw, dict):
            raise QueryResultContractError(f"errors[{index}] must be an object")
        code = raw.get("code")
        message = raw.get("message")
        if not isinstance(code, str) or not code:
            raise QueryResultContractError(f"errors[{index}].code must be a non-empty string")
        if not isinstance(message, str) or not message:
            raise QueryResultContractError(f"errors[{index}].message must be a non-empty string")
        errors.append(
            QueryError(
                code=code,
                message=message,
                line=_optional_int(raw, "line"),
                column=_optional_int(raw, "column"),
                source_snippet=_optional_str(raw, "sourceSnippet"),
                spec_url=_optional_str(raw, "specUrl"),
            )
        )

    if ok and errors:
        raise QueryResultContractError("successful QueryResult must not contain errors")
    if not ok and not errors:
        raise QueryResultContractError("failed QueryResult must contain at least one error")

    return QueryResult(
        ok=ok,
        value=value,
        count=count,
        elapsed_ms=elapsed_ms,
        errors=tuple(errors),
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        result = parse_query_result(payload)
    except (json.JSONDecodeError, QueryResultContractError) as exc:
        print(json.dumps({"ok": False, "contract_error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    json.dump(result.to_dict(), sys.stdout, ensure_ascii=False, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
