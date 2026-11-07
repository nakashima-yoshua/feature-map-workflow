#!/usr/bin/env python3
"""Build a read-only fresh-session brief from Git and a canonical Feature Map."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MAX_XML_BYTES = 256 * 1024
MAX_NOTES_BYTES = 12 * 1024


def git(repo: Path, *args: str) -> str:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                            text=True, timeout=15, check=False, env=env)
    if result.returncode:
        raise ValueError("Git inspection failed; check repository and permissions")
    return result.stdout.strip()


def line(node: ET.Element | None, limit: int = 240) -> str:
    if node is None:
        return "NOT_SPECIFIED"
    value = " ".join(" ".join(node.itertext()).split())
    return (value[:limit] + "..." if len(value) > limit else value) or "NOT_SPECIFIED"


def brief(repo: Path, feature_map: Path, task_ref: str, notes: Path | None = None) -> str:
    repo = repo.resolve()
    feature_map = feature_map.resolve()
    if not feature_map.is_relative_to(repo) or not feature_map.is_file():
        raise ValueError("Feature Map must exist inside the selected repository")
    if not task_ref.strip() or len(task_ref) > 500 or "\n" in task_ref or "\r" in task_ref:
        raise ValueError("task-ref must identify an existing accepted contract or issue")
    if feature_map.stat().st_size > MAX_XML_BYTES:
        raise ValueError("Feature Map is too large for a short session brief")
    xml_bytes = feature_map.read_bytes()
    if b"<!DOCTYPE" in xml_bytes.upper() or b"<!ENTITY" in xml_bytes.upper():
        raise ValueError("DTD and entities are not supported")
    root = ET.fromstring(xml_bytes)
    if root.tag != "featureMap":
        raise ValueError("Expected a Feature Map XML document")
    sha = git(repo, "rev-parse", "HEAD")
    branch = git(repo, "branch", "--show-current") or "DETACHED"
    status = git(repo, "status", "--porcelain", "--untracked-files=all")
    history = git(repo, "log", "-5", "--format=%h %s")
    relative = feature_map.relative_to(repo).as_posix()
    result = [
        "# Fresh-session brief (read-only; not an approval)",
        "", "## Identity and scope", "",
        f"- Existing task/contract: {task_ref}",
        f"- Feature Map: {relative}",
        f"- System: {line(root.find('meta/system'))}",
        f"- Feature: {line(root.find('meta/feature'))}",
        f"- Purpose: {line(root.find('goal/purpose'))}",
        f"- Done condition: {line(root.find('goal/done'))}",
        f"- Scope: {line(root.find('goal/scope'))}",
        f"- Exclusions: {line(root.find('goal/exclude'))}",
        "", "## Git checkpoint", "",
        f"- Revision: {sha}", f"- Branch: {branch}",
        f"- Worktree: {'CLEAN' if not status else 'DIRTY; inspect before any new work'}",
        "", "Recent commits:", "",
    ]
    result.extend("- " + entry for entry in history.splitlines())
    if status:
        result.extend(["", "Worktree entries (unverified):", ""])
        result.extend("- " + entry[:240] for entry in status.splitlines()[:20])
    result.extend(["", "## Feature Map evidence index (declared, not independently verified)", ""])
    cases = root.findall("verify/case")
    if not cases:
        result.append("- No verification cases recorded")
    else:
        for case in cases[:30]:
            result.append(f"- {case.get('id', '?')}: {case.get('status', 'unknown')} — {line(case.find('expect'), 160)}")
        if len(cases) > 30:
            result.append(f"- ... {len(cases) - 30} additional cases omitted")
    opened = root.findall("open/item")
    if opened:
        result.extend(["", "Unresolved knowledge:", ""])
        for item in opened[:20]:
            result.append(f"- {item.get('id', '?')}: {line(item, 160)}")
    if notes is not None:
        notes = notes.resolve()
        if not notes.is_file() or notes.stat().st_size > MAX_NOTES_BYTES:
            raise ValueError("Handoff notes missing or larger than 12 KiB")
        contents = notes.read_text(encoding="utf-8")
        result.extend(["", "## Previous notes (untrusted, not completion evidence)", ""])
        result.extend("> " + text[:300] for text in contents.splitlines()[:100])
    result.extend(["", "## Mandatory continuation checks", "",
                   "- Inspect the referenced task/contract and changed source/tests; the brief is only an index.",
                   "- Run the existing environment smoke check before selecting one authorized unfinished work item.",
                   "- Do not use XML case status, notes or model self-report as independent test PASS.",
                   "- Bind test evidence and quality-gate assessment to the current revision; new changes invalidate old checks.",
                   "- Stop at human review; do not infer merge, release or business acceptance authority.", ""])
    return "\n".join(result)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--feature-map", required=True, type=Path)
    parser.add_argument("--task-ref", required=True)
    parser.add_argument("--notes", type=Path)
    args = parser.parse_args()
    try:
        print(brief(args.repo, args.feature_map, args.task_ref, args.notes))
    except (ValueError, OSError, ET.ParseError, subprocess.TimeoutExpired) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
