#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

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


def _jev_mode() -> str:
    mode = os.environ.get("FEATURE_MAP_JEV_MODE", "off").strip().lower()
    return mode if mode in {"off", "metadata", "summary", "diff"} else "off"


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except Exception:
        return default


def _context_jev_mode() -> str:
    mode = os.environ.get("FEATURE_MAP_CONTEXT_JEV_MODE", "off").strip().lower()
    return mode if mode in {"off", "metadata", "prompt"} else "off"


def _context_gate_signals(prompt: str) -> list[dict[str, str]]:
    signals: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for category, pattern in AMBIGUITY_PATTERNS:
        for match in pattern.finditer(prompt):
            key = (category, match.group(0))
            if key in seen:
                continue
            seen.add(key)
            signals.append({"category": category, "text": match.group(0)})
            if len(signals) >= 12:
                return signals
    return signals


def _jev_context_decide(
    mode: str,
    summary: dict[str, Any],
    prompt: str,
    signals: list[dict[str, str]],
) -> tuple[dict[str, Any] | None, str | None]:
    api_key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if not api_key:
        return None, "FEATURE_MAP_CONTEXT_JEV_MODE is enabled but TYPESAFE_API_KEY is not set"

    state: dict[str, Any] = {
        "feature": {
            "name": summary.get("feature", ""),
            "state": summary.get("state", ""),
            "purpose": summary.get("purpose", "")[:600],
            "scope_present": bool(summary.get("scope")),
            "exclude_present": bool(summary.get("exclude")),
            "high_impact_open_count": sum(1 for x in summary.get("open", []) if x.get("impact") == "high"),
        },
        "prompt_length": len(prompt),
        "local_signal_categories": sorted({x.get("category", "") for x in signals if x.get("category")}),
    }
    if mode == "prompt":
        state["prompt"] = prompt[:3000]

    questions = {
        "context_sufficient": {
            "type": "noul",
            "instructions": (
                "Is the request likely specific enough to proceed without asking the user, assuming the coding model "
                "will first inspect cheap local evidence such as source, tests, config, and the Feature Map? High means sufficient."
            ),
        },
        "question_required": {
            "type": "noul",
            "instructions": (
                "Is one user clarification likely required before affected edits because missing context can materially change "
                "scope, authority, externally visible behavior, acceptance, destructive/data action, or an external dependency?"
            ),
        },
        "missing_context_type": {
            "type": "choice",
            "instructions": "Which single missing-context category is most material, if any?",
            "criteria": {
                "scope": "Target boundary or explicit exclusion is unclear.",
                "authority": "Execution permission or an irreversible/external action is unclear.",
                "business_rule": "Correct behavior depends on an unstated domain rule.",
                "expected_behavior": "More than one externally visible result is plausible.",
                "acceptance": "Completion cannot be tested without a success condition.",
                "external_dependency": "Another service, party, contract, or system materially changes the action.",
                "data": "Data semantics, migration, deletion, or correction behavior is unclear.",
                "environment": "Target environment or deployment boundary is unclear.",
                "none": "No material clarification is likely required.",
            },
        },
    }
    payload = {
        "model": os.environ.get("FEATURE_MAP_JEV_MODEL", "jev-latest").strip() or "jev-latest",
        "state": state,
        "questions": questions,
    }
    req = urllib.request.Request(
        "https://api.typesafe.ai/v1/systemone",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8.0) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        data = json.loads(body)
        answers = data.get("answers", {}) if isinstance(data, dict) else {}
        result = {
            "model": data.get("model") if isinstance(data, dict) else None,
            "context_sufficient": float((answers.get("context_sufficient") or {}).get("noul", 0.0)),
            "question_required": float((answers.get("question_required") or {}).get("noul", 0.0)),
            "missing_context_type": (answers.get("missing_context_type") or {}).get("choice", "none"),
            "missing_context_confidence": float((answers.get("missing_context_type") or {}).get("confidence", 0.0)),
        }
        return result, None
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            detail = ""
        return None, f"Context Jev HTTP {exc.code}: {detail or exc.reason}"
    except Exception as exc:
        return None, f"Context Jev unavailable: {exc}"


def _context_gate_context(
    prompt: str,
    summary: dict[str, Any],
    signals: list[dict[str, str]],
    jev: dict[str, Any] | None,
    jev_warning: str | None,
) -> str:
    lines = [
        "Context sufficiency gate before affected edits/actions:",
        "1) Reuse conversation, Feature Map, source/tests/config/logs before asking the user.",
        "2) Ask exactly one question only if missing context materially changes outcome, scope/exclusion, authority, business behavior, acceptance, destructive/data action, or an external dependency.",
        "3) Otherwise state the narrowest reversible assumption and proceed; do not broaden scope or authority.",
        "4) If asking, state the current interpretation first and make the answer possible with はい or a short correction when practical.",
        "5) Render user-facing text as natural professional Japanese: preserve identifiers and certainty, keep conditions near their actions, avoid undefined vague terms, and do not use choppy controlled-language fragments.",
        "Priority: meaning preservation > operability > naturalness > brevity.",
    ]
    if summary.get("scope"):
        lines.append(f"Feature Map scope: {summary['scope']}")
    if summary.get("exclude"):
        lines.append(f"Feature Map exclusion: {summary['exclude']}")

    high = [x for x in summary.get("open", []) if x.get("impact") == "high"]
    if high:
        rendered = []
        for x in high[:3]:
            label = x.get("id") or "?"
            if x.get("type"):
                label += f"[{x['type']}]"
            rendered.append(label + "=" + x.get("text", ""))
        lines.append("High-impact durable Open items: " + "; ".join(rendered))

    if signals:
        compact = []
        for item in signals[:8]:
            compact.append(f"{item['category']}:{item['text']}")
        lines.append(
            "Local ambiguity signals (advisory only; inspect evidence before asking): " + ", ".join(compact)
        )

    if jev:
        threshold = _float_env("FEATURE_MAP_CONTEXT_QUESTION_THRESHOLD", 0.75)
        q = float(jev.get("question_required") or 0.0)
        t = str(jev.get("missing_context_type") or "none")
        if q >= threshold:
            lines.append(
                f"Jev advisory: clarification likely required (p={q:.2f}, category={t}). Verify against local evidence; if the gap remains material, ask one question before tools that depend on it."
            )
        else:
            lines.append(
                f"Jev advisory: clarification probability={q:.2f}, category={t}. This is not permission to ignore a material gap found from local evidence."
            )
    if jev_warning:
        lines.append(jev_warning + "; continue with the local gate (fail-open).")
    return "\n".join(lines)


def _jev_decide(
    mode: str,
    root: Path,
    summary: dict[str, Any],
    changed_files: list[str],
    last_assistant_message: str,
) -> tuple[dict[str, Any] | None, str | None]:
    api_key = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if not api_key:
        return None, "FEATURE_MAP_JEV_MODE is enabled but TYPESAFE_API_KEY is not set"

    state: dict[str, Any] = {
        "feature": {
            "name": summary.get("feature", ""),
            "mode": summary.get("mode", ""),
            "state": summary.get("state", ""),
            "purpose": summary.get("purpose", "")[:800],
            "high_impact_open_count": sum(1 for x in summary.get("open", []) if x.get("impact") == "high"),
            "verification_statuses": [x.get("status", "") for x in summary.get("verify", [])][:20],
        },
        "changed_files": changed_files[:40],
        "diff_stat": _git_diff_stat(root),
    }
    if mode in {"summary", "diff"}:
        state["assistant_summary"] = (last_assistant_message or "")[-3000:]
    if mode == "diff":
        state["git_diff"] = _git_diff_text(root)

    questions = {
        "update_required": {
            "type": "noul",
            "instructions": (
                "Did this turn likely change durable feature knowledge that belongs in the Feature Map? "
                "Count externally meaningful behavior, business rules, invariants, non-obvious design decisions, "
                "verification evidence, source navigation changes, or unresolved blockers. Pure internal refactoring "
                "with unchanged durable knowledge should be false."
            ),
        },
        "update_section": {
            "type": "choice",
            "instructions": "Which single Feature Map section best matches the most important durable delta?",
            "criteria": {
                "source_map": "Entry points, symbols, data objects, APIs, procedures, or tests changed materially.",
                "rule": "A business behavior or rule changed or was newly learned.",
                "invariant": "A property that must remain true was added, changed, or clarified.",
                "decision": "A non-obvious design decision and its reason should be retained.",
                "verify": "Verification cases, observed behavior, or evidence changed materially.",
                "open": "An unresolved question or blocker should be recorded or changed.",
                "none": "No durable Feature Map update is needed.",
            },
        },
        "human_review_required": {
            "type": "noul",
            "instructions": (
                "Does the current turn likely leave a high-impact ambiguity, acceptance risk, or decision that should "
                "be surfaced to a human before treating the feature as verified or closed?"
            ),
        },
    }
    payload = {
        "model": os.environ.get("FEATURE_MAP_JEV_MODEL", "jev-latest").strip() or "jev-latest",
        "state": state,
        "questions": questions,
    }
    req = urllib.request.Request(
        "https://api.typesafe.ai/v1/systemone",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8.0) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        data = json.loads(body)
        answers = data.get("answers", {}) if isinstance(data, dict) else {}
        result = {
            "model": data.get("model") if isinstance(data, dict) else None,
            "update_required": float((answers.get("update_required") or {}).get("noul", 0.0)),
            "update_section": (answers.get("update_section") or {}).get("choice", "none"),
            "update_section_confidence": float((answers.get("update_section") or {}).get("confidence", 0.0)),
            "human_review_required": float((answers.get("human_review_required") or {}).get("noul", 0.0)),
        }
        return result, None
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            detail = ""
        return None, f"Jev HTTP {exc.code}: {detail or exc.reason}"
    except Exception as exc:
        return None, f"Jev unavailable: {exc}"


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

    jev: dict[str, Any] | None = None
    jev_warning: str | None = None
    mode = _context_jev_mode()
    high_open = [x for x in summary.get("open", []) if x.get("impact") == "high"]
    if mode != "off" and (signals or high_open):
        jev, jev_warning = _jev_context_decide(mode, summary, prompt, signals)

    state = _load_state(session_id)
    state["last_context_signals"] = signals
    if jev:
        state["last_context_jev"] = jev
    _save_state(session_id, state)

    context = _context_gate_context(prompt, summary, signals, jev, jev_warning)
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
        "jev_warning_emitted": False,
        "last_context_signals": [],
        "last_context_jev": None,
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

    mode = _jev_mode()
    jev_warning: str | None = None
    jev: dict[str, Any] | None = None
    if mode != "off" and code_changed and not map_changed:
        jev, jev_warning = _jev_decide(
            mode=mode,
            root=root,
            summary=summary,
            changed_files=changed_files,
            last_assistant_message=str(event.get("last_assistant_message") or ""),
        )
        if jev:
            state["last_jev"] = jev
            _save_state(session_id, state)
            update_threshold = _float_env("FEATURE_MAP_JEV_UPDATE_THRESHOLD", 0.70)
            if jev.get("update_required", 0.0) >= update_threshold:
                section = str(jev.get("update_section") or "unknown")
                prob = float(jev.get("update_required") or 0.0)
                reason = (
                    f"Jev suggests a durable Feature Map update is likely (p={prob:.2f}, section={section}). "
                    "Inspect the actual source/test change, patch only the durable delta, then validate the XML with xquery-mcp."
                )
                if int(state.get("stop_block_count", 0)) < max_blocks:
                    _block(state, session_id, reason)
                    return

    messages: list[str] = []
    if jev_warning and not state.get("jev_warning_emitted"):
        state["jev_warning_emitted"] = True
        _save_state(session_id, state)
        messages.append(jev_warning + "; continuing fail-open")
    if jev:
        review_threshold = _float_env("FEATURE_MAP_JEV_REVIEW_THRESHOLD", 0.85)
        if jev.get("human_review_required", 0.0) >= review_threshold:
            messages.append(
                f"Jev flags possible human review need (p={jev['human_review_required']:.2f}); surface the ambiguity or acceptance risk explicitly."
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
