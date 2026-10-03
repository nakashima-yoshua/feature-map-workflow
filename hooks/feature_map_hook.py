#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from decision_provider import completion_mode, context_mode, get_decision_provider

PLUGIN_ROOT = Path(os.environ.get("PLUGIN_ROOT", Path(__file__).resolve().parents[1])).resolve()
PLUGIN_DATA = Path(os.environ.get("PLUGIN_DATA", PLUGIN_ROOT / ".plugin-data")).resolve()

CODE_SUFFIXES = {
    ".cs", ".fs", ".vb", ".java", ".kt", ".kts", ".rs", ".go", ".py", ".js", ".jsx",
    ".ts", ".tsx", ".sql", ".ps1", ".sh", ".bash", ".zsh", ".xml", ".xaml", ".json",
    ".yaml", ".yml", ".toml", ".proto", ".graphql", ".csproj", ".fsproj", ".vbproj",
}
TEST_MARKERS = ("test", "tests", "spec", "specs")
FEATURE_MAP_BASENAMES = ("feature-map.xml", "feature_map.xml")

# These are advisory signals, not proof that a clarification is required.
# The model must first reuse conversation/repository/Feature Map evidence.
AMBIGUITY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("scope", re.compile(r"関連(?:する)?(?:箇所|コード|ファイル|処理|テーブル|部分|機能)?|全部|すべて|一式|可能な限り|徹底的に")),
    ("criteria", re.compile(r"必要に応じて|必要なら|適宜|適切に|問題があれば|いい感じ(?:に)?|最適化|改善|整理|統一|標準化|あとは任せる")),
    ("authority", re.compile(r"削除|移行|本番(?:環境)?|公開|外部送信|送信|課金|権限|認証|契約|スキーマ変更")),
)



def _emit(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    sys.stdout.write("\n")


def _read_event() -> dict[str, Any]:
    try:
        data = json.load(sys.stdin)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _run(args: list[str], cwd: Path, timeout: float = 5.0) -> str:
    try:
        p = subprocess.run(
            args,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except Exception:
        return ""
    return p.stdout.strip() if p.returncode == 0 else ""


def _git_root(cwd: Path) -> Path | None:
    out = _run(["git", "rev-parse", "--show-toplevel"], cwd)
    if not out:
        return None
    p = Path(out)
    return p.resolve() if p.exists() else None


def _git_changed_files(root: Path) -> list[str]:
    names: set[str] = set()
    for args in (
        ["git", "diff", "--name-only", "--"],
        ["git", "diff", "--cached", "--name-only", "--"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ):
        out = _run(args, root)
        if out:
            names.update(line.strip().replace("\\", "/") for line in out.splitlines() if line.strip())
    return sorted(names)


def _git_diff_stat(root: Path) -> str:
    parts: list[str] = []
    for args in (
        ["git", "diff", "--stat", "--no-ext-diff", "--"],
        ["git", "diff", "--cached", "--stat", "--no-ext-diff", "--"],
    ):
        out = _run(args, root)
        if out:
            parts.append(out)
    return "\n".join(parts)[:4000]


def _git_diff_text(root: Path) -> str:
    parts: list[str] = []
    for args in (
        ["git", "diff", "--unified=0", "--no-ext-diff", "--"],
        ["git", "diff", "--cached", "--unified=0", "--no-ext-diff", "--"],
    ):
        out = _run(args, root, timeout=8.0)
        if out:
            parts.append(out)
    return "\n".join(parts)[:8000]


def _find_feature_map(cwd: Path) -> tuple[Path | None, list[Path]]:
    root = _git_root(cwd) or cwd
    override = os.environ.get("FEATURE_MAP_PATH", "").strip()
    if override:
        p = Path(override)
        if not p.is_absolute():
            p = root / p
        p = p.resolve()
        return (p if p.is_file() else None, [p])

    exact: list[Path] = []
    for rel in (
        "feature-map.xml",
        ".feature-map/feature-map.xml",
        "docs/feature-map.xml",
        "design/feature-map.xml",
    ):
        p = (root / rel).resolve()
        if p.is_file():
            exact.append(p)
    if len(exact) == 1:
        return exact[0], exact
    if len(exact) > 1:
        return None, exact

    matches: list[Path] = []
    if (root / ".git").exists():
        out = _run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], root)
        for rel in out.splitlines() if out else []:
            p = (root / rel).resolve()
            low = p.name.lower()
            if p.is_file() and p.suffix.lower() == ".xml" and "feature-map" in low:
                matches.append(p)
    matches = sorted(set(matches))
    if len(matches) == 1:
        return matches[0], matches
    return None, matches


def _xml_canonical_hash_from_text(text: str) -> str:
    try:
        canonical = ET.canonicalize(xml_data=text, strip_text=True, with_comments=False)
        data = canonical.encode("utf-8")
    except Exception:
        data = text.encode("utf-8", errors="replace")
    return hashlib.sha256(data).hexdigest()


def _xml_canonical_hash(path: Path) -> str:
    return _xml_canonical_hash_from_text(path.read_text(encoding="utf-8"))


def _parse_feature_map(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        root = ET.parse(path).getroot()
    except Exception as exc:
        return None, str(exc)

    def text(xpath: str) -> str:
        node = root.find(xpath)
        return (node.text or "").strip() if node is not None and node.text else ""

    open_items: list[dict[str, str]] = []
    for node in root.findall("./open/item"):
        open_items.append(
            {
                "id": node.attrib.get("id", ""),
                "type": node.attrib.get("type", ""),
                "impact": node.attrib.get("impact", ""),
                "next": node.attrib.get("next", ""),
                "text": (node.text or "").strip(),
            }
        )

    verify: list[dict[str, str]] = []
    for node in root.findall("./verify/case"):
        verify.append(
            {
                "id": node.attrib.get("id", ""),
                "type": node.attrib.get("type", ""),
                "status": node.attrib.get("status", ""),
                "condition": ((node.findtext("condition") or "").strip()),
            }
        )

    entries: list[str] = []
    for ref in root.findall("./sourceMap/ref"):
        if ref.attrib.get("kind") in {"entry", "test", "procedure", "api"}:
            target = ref.attrib.get("target", "").strip()
            if target:
                entries.append(target)

    diagrams: list[str] = []
    for node in root.findall("./diagrams/diagram"):
        label = node.attrib.get("id", "") or node.attrib.get("title", "") or "diagram"
        kind = node.attrib.get("kind", "")
        diagrams.append(f"{label}:{kind}" if kind else label)

    data = {
        "version": root.attrib.get("version", ""),
        "mode": root.attrib.get("mode", ""),
        "state": root.attrib.get("state", ""),
        "system": text("./meta/system"),
        "feature": text("./meta/feature"),
        "purpose": text("./goal/purpose"),
        "done": text("./goal/done"),
        "scope": text("./goal/scope"),
        "exclude": text("./goal/exclude"),
        "open": open_items,
        "verify": verify,
        "entries": entries[:8],
        "diagrams": diagrams[:6],
    }
    return data, None


def _data_dir() -> Path:
    try:
        PLUGIN_DATA.mkdir(parents=True, exist_ok=True)
        return PLUGIN_DATA
    except Exception:
        return Path.cwd()


def _session_path(session_id: str) -> Path:
    key = hashlib.sha256(session_id.encode("utf-8", errors="replace")).hexdigest()[:24]
    return _data_dir() / f"feature-map-session-{key}.json"


def _load_state(session_id: str) -> dict[str, Any]:
    p = _session_path(session_id)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_state(session_id: str, state: dict[str, Any]) -> None:
    p = _session_path(session_id)
    try:
        p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except Exception:
        return str(path)


def _session_context(feature_map: Path, summary: dict[str, Any], root: Path) -> str:
    high = [x for x in summary.get("open", []) if x.get("impact") == "high"]
    pending = [x for x in summary.get("verify", []) if x.get("status") != "passed"]
    lines = [
        f"Feature Map: {_relative(feature_map, root)}",
        f"Feature: {summary.get('feature') or '(unnamed)'} | mode={summary.get('mode')} state={summary.get('state')}",
    ]
    if summary.get("purpose"):
        lines.append(f"Purpose: {summary['purpose']}")
    if summary.get("scope"):
        lines.append(f"Scope: {summary['scope']}")
    if summary.get("exclude"):
        lines.append(f"Exclude: {summary['exclude']}")
    if high:
        lines.append(
            "High-impact open: "
            + "; ".join(
                (x.get("id") or "?")
                + (f"[{x.get('type')}]" if x.get("type") else "")
                + "="
                + x.get("text", "")
                for x in high[:3]
            )
        )
    if pending:
        lines.append("Verify pending: " + ", ".join((x.get("id") or "?") + ":" + x.get("status", "") for x in pending[:6]))
    if summary.get("entries"):
        lines.append("Key refs: " + ", ".join(summary["entries"][:6]))
    if summary.get("diagrams"):
        lines.append("Diagrams: " + ", ".join(summary["diagrams"][:4]))
    lines.append("Source/tests are canonical. Patch only durable Feature Map deltas; do not restate code as prose.")
    return "\n".join(lines)


def _looks_like_code_or_test(path: str, feature_map: Path | None, root: Path) -> bool:
    p = Path(path)
    if feature_map is not None:
        try:
            if (root / p).resolve() == feature_map.resolve():
                return False
        except Exception:
            pass
    low_parts = [part.lower() for part in p.parts]
    if any(part in {"bin", "obj", "node_modules", "vendor", ".git"} for part in low_parts):
        return False
    if p.suffix.lower() in CODE_SUFFIXES:
        return True
    return any(marker in low_parts for marker in TEST_MARKERS)


def _compact_tool_response(value: Any) -> str:
    try:
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return str(value)


def _float_env(name: str, default: float, legacy_name: str | None = None) -> float:
    raw = os.environ.get(name)
    if raw is None and legacy_name:
        raw = os.environ.get(legacy_name)
    try:
        return float(raw if raw is not None else str(default))
    except Exception:
        return default


def _block(state: dict[str, Any], session_id: str, reason: str) -> None:
    state["stop_block_count"] = int(state.get("stop_block_count", 0)) + 1
    _save_state(session_id, state)
    _emit({"decision": "block", "reason": reason})


def _handle_user_prompt(event: dict[str, Any]) -> None:
    cwd = Path(event.get("cwd") or os.getcwd()).resolve()
    session_id = str(event.get("session_id") or "unknown")
    prompt = str(event.get("prompt") or "")
    signals = _context_gate_signals(prompt)

    feature_map, _ = _find_feature_map(cwd)
    summary: dict[str, Any] = {}
    if feature_map:
        parsed, error = _parse_feature_map(feature_map)
        if not error and parsed:
            summary = parsed

    decision: dict[str, Any] | None = None
    decision_warning: str | None = None
    provider = get_decision_provider()
    mode = context_mode(provider.name)
    high_open = [x for x in summary.get("open", []) if x.get("impact") == "high"]
    if mode != "off" and (signals or high_open):
        decision, decision_warning = provider.context_decide(mode, summary, prompt, signals)

    state = _load_state(session_id)
    state["last_context_signals"] = signals
    if decision:
        state["last_context_decision"] = decision
    _save_state(session_id, state)

    context = _context_gate_context(prompt, summary, signals, decision, decision_warning)
    _emit({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    })


def _handle_session_start(event: dict[str, Any]) -> None:
    cwd = Path(event.get("cwd") or os.getcwd()).resolve()
    root = _git_root(cwd) or cwd
    session_id = str(event.get("session_id") or "unknown")
    feature_map, matches = _find_feature_map(cwd)
    state: dict[str, Any] = {
        "session_id": session_id,
        "root": str(root),
        "feature_map": str(feature_map) if feature_map else None,
        "feature_map_candidates": [str(x) for x in matches],
        "feature_map_hash_start": None,
        "validated_hash": None,
        "edit_count": 0,
        "stop_block_count": 0,
        "changed_files": _git_changed_files(root) if (root / ".git").exists() else [],
        "decision_warning_emitted": False,
        "last_context_signals": [],
        "last_context_decision": None,
    }

    if feature_map:
        try:
            state["feature_map_hash_start"] = _xml_canonical_hash(feature_map)
        except Exception:
            pass
    _save_state(session_id, state)

    if feature_map:
        summary, error = _parse_feature_map(feature_map)
        if error:
            context = f"Feature Map found at {_relative(feature_map, root)} but XML parsing failed: {error}"
        else:
            context = _session_context(feature_map, summary or {}, root)
        _emit({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}})
        return

    if len(matches) > 1:
        rels = ", ".join(_relative(x, root) for x in matches[:8])
        context = f"Feature Map workflow found multiple candidate XML files ({rels}). Set FEATURE_MAP_PATH for this session before relying on automatic hooks."
        _emit({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}})
        return

    _emit({"continue": True})


def _handle_post_tool(event: dict[str, Any]) -> None:
    cwd = Path(event.get("cwd") or os.getcwd()).resolve()
    root = _git_root(cwd) or cwd
    session_id = str(event.get("session_id") or "unknown")
    state = _load_state(session_id)
    feature_map, _ = _find_feature_map(cwd)
    tool_name = str(event.get("tool_name") or "")

    if tool_name.endswith("xml_validate_schema"):
        tool_input = event.get("tool_input") if isinstance(event.get("tool_input"), dict) else {}
        xml_text = tool_input.get("xml") if isinstance(tool_input, dict) else None
        response_text = _compact_tool_response(event.get("tool_response"))
        if isinstance(xml_text, str) and "Valid: XML conforms to the schema." in response_text:
            state["validated_hash"] = _xml_canonical_hash_from_text(xml_text)
            state["last_validation_tool"] = tool_name
            _save_state(session_id, state)
        _emit({})
        return

    state["edit_count"] = int(state.get("edit_count", 0)) + 1
    if (root / ".git").exists():
        state["changed_files"] = _git_changed_files(root)
    if feature_map:
        state["feature_map"] = str(feature_map)
        try:
            current_hash = _xml_canonical_hash(feature_map)
            state["feature_map_hash_current"] = current_hash
        except Exception as exc:
            state["feature_map_parse_error"] = str(exc)
            _save_state(session_id, state)
            _emit({
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": f"Feature Map XML is not well-formed after the edit: {exc}. Fix only the malformed XML before continuing.",
                }
            })
            return
    _save_state(session_id, state)
    _emit({})


def _handle_stop(event: dict[str, Any]) -> None:
    cwd = Path(event.get("cwd") or os.getcwd()).resolve()
    root = _git_root(cwd) or cwd
    session_id = str(event.get("session_id") or "unknown")
    state = _load_state(session_id)
    feature_map, matches = _find_feature_map(cwd)
    max_blocks = max(0, int(os.environ.get("FEATURE_MAP_MAX_STOP_BLOCKS", "2") or "2"))

    if feature_map is None:
        if len(matches) > 1:
            _emit({"continue": True, "systemMessage": "Feature Map hooks could not select one XML. Set FEATURE_MAP_PATH to enable automatic completion checks."})
        else:
            _emit({"continue": True})
        return

    summary, parse_error = _parse_feature_map(feature_map)
    if parse_error:
        if int(state.get("stop_block_count", 0)) < max_blocks:
            _block(state, session_id, f"Feature Map XML is malformed: {parse_error}. Fix the smallest XML error before finishing.")
        else:
            _emit({"continue": True, "systemMessage": f"Feature Map XML remains malformed: {parse_error}"})
        return
    summary = summary or {}

    high_open = [x for x in summary.get("open", []) if x.get("impact") == "high"]
    bad_verify = [x for x in summary.get("verify", []) if x.get("status") in {"failed", "blocked"}]
    if summary.get("state") in {"verified", "closed"} and (high_open or bad_verify):
        issues = []
        if high_open:
            issues.append("high-impact Open items remain")
        if bad_verify:
            issues.append("failed/blocked verification cases remain")
        if int(state.get("stop_block_count", 0)) < max_blocks:
            _block(state, session_id, "Feature Map state is inconsistent: " + " and ".join(issues) + ". Do not leave state as verified/closed until resolved or downgraded.")
        else:
            _emit({"continue": True, "systemMessage": "Feature Map state is inconsistent: " + " and ".join(issues)})
        return

    try:
        current_hash = _xml_canonical_hash(feature_map)
    except Exception as exc:
        _emit({"continue": True, "systemMessage": f"Could not hash Feature Map: {exc}"})
        return

    start_hash = state.get("feature_map_hash_start")
    map_changed = bool(start_hash and current_hash != start_hash)
    validated = state.get("validated_hash") == current_hash
    if map_changed and not validated:
        reason = (
            "Feature Map XML changed, but XSD validation of the current XML was not observed. "
            "Use xquery-mcp xml_validate_schema with the current Feature Map XML and feature-map.xsd; "
            "fix only the failing node if validation fails."
        )
        if int(state.get("stop_block_count", 0)) < max_blocks:
            _block(state, session_id, reason)
        else:
            _emit({"continue": True, "systemMessage": reason})
        return

    changed_files = _git_changed_files(root) if (root / ".git").exists() else list(state.get("changed_files") or [])
    code_changed = any(_looks_like_code_or_test(p, feature_map, root) for p in changed_files)

    provider = get_decision_provider()
    mode = completion_mode(provider.name)
    decision_warning: str | None = None
    decision: dict[str, Any] | None = None
    if mode != "off" and code_changed and not map_changed:
        decision, decision_warning = provider.completion_decide(
            mode=mode,
            summary=summary,
            changed_files=changed_files,
            last_assistant_message=str(event.get("last_assistant_message") or ""),
            diff_stat=_git_diff_stat(root),
            git_diff=_git_diff_text(root) if mode == "diff" else "",
        )
        if decision:
            state["last_decision"] = decision
            _save_state(session_id, state)
            update_threshold = _float_env("FEATURE_MAP_DECISION_UPDATE_THRESHOLD", 0.70, "FEATURE_MAP_JEV_UPDATE_THRESHOLD")
            if decision.get("update_required", 0.0) >= update_threshold:
                section = str(decision.get("update_section") or "unknown")
                prob = float(decision.get("update_required") or 0.0)
                reason = (
                    f"{decision.get('provider', 'decision')} suggests a durable Feature Map update is likely (p={prob:.2f}, section={section}). "
                    "Inspect the actual source/test change, patch only the durable delta, then validate the XML with xquery-mcp."
                )
                if int(state.get("stop_block_count", 0)) < max_blocks:
                    _block(state, session_id, reason)
                    return

    messages: list[str] = []
    if decision_warning and not state.get("decision_warning_emitted"):
        state["decision_warning_emitted"] = True
        _save_state(session_id, state)
        messages.append(decision_warning + "; continuing fail-open")
    if decision:
        review_threshold = _float_env("FEATURE_MAP_DECISION_REVIEW_THRESHOLD", 0.85, "FEATURE_MAP_JEV_REVIEW_THRESHOLD")
        if decision.get("human_review_required", 0.0) >= review_threshold:
            messages.append(
                f"{decision.get('provider', 'decision')} flags possible human review need (p={decision['human_review_required']:.2f}); surface the ambiguity or acceptance risk explicitly."
            )

    payload: dict[str, Any] = {"continue": True}
    if messages:
        payload["systemMessage"] = " ".join(messages)
    _emit(payload)


def main() -> int:
    event = _read_event()
    action = sys.argv[1] if len(sys.argv) > 1 else str(event.get("hook_event_name") or "")
    if action in {"user-prompt", "UserPromptSubmit"}:
        _handle_user_prompt(event)
    elif action in {"session-start", "SessionStart"}:
        _handle_session_start(event)
    elif action in {"post-tool", "PostToolUse"}:
        _handle_post_tool(event)
    elif action in {"stop", "Stop"}:
        _handle_stop(event)
    else:
        _emit({"continue": True})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
