#!/usr/bin/env python3
"""Contracts shared by the opt-in serial workflow and its isolated workers."""
from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any

from task_runner import Halt, digest, relative, safe_file

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "skills/feature-map-workflow/assets/task-modules.json"
MAX_FILE = 2 * 1024 * 1024
MAX_TREE = 64 * 1024 * 1024
MAX_FILES = 10000
ROLES = {"ai", "build"}
TERMINAL = {"HALT", "HUMAN_REVIEW_REQUIRED"}


def atomic_json(path: Path, value: Any) -> None:
    """Atomic host checkpoints; directory fsync is supported/required on Linux."""
    if path.is_symlink():
        raise Halt("Linked checkpoints are forbidden", "permission")
    temp = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    try:
        with temp.open("xb") as stream:
            stream.write((json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
        if os.name == "posix":
            fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
    finally:
        temp.unlink(missing_ok=True)


def read(path: Path, limit: int = MAX_FILE) -> Any:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise Halt("Missing, linked or oversized structured input", "integrity")
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise Halt("Duplicate JSON key", "specification")
            out[key] = value
        return out
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)
    except (UnicodeError, ValueError):
        raise Halt("Invalid JSON input", "specification") from None


def path_name(value: Any) -> str:
    name = relative(value)
    if ":" in name or any(x.startswith(".env") for x in name.split("/")):
        raise Halt("Drive or secret paths are not supported", "permission")
    return name


def identifier(value: Any) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", value):
        raise Halt("Invalid identifier", "specification")
    return value


def strings(value: Any, *, empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not empty) or any(
            not isinstance(x, str) or not x.strip() for x in value) or len(set(value)) != len(value):
        raise Halt("Expected a unique list of nonempty strings", "specification")
    return value


def integer(value: Any, maximum: int) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise Halt("Budget outside supported limits", "budget")
    return value


def catalog(path: Path = CATALOG) -> dict[str, dict]:
    data = read(path)
    items = data.get("modules", [])
    if data.get("version") != 1 or len(items) != 49 or [x["number"] for x in items] != list(range(1, 50)):
        raise Halt("Invalid 49-module catalog", "specification")
    out = {identifier(x["id"]): x for x in items}
    if len(out) != 49 or len({x["phase"] for x in items}) != 10:
        raise Halt("Duplicate modules or missing phases", "specification")
    return out


def validate(config: Any) -> dict:
    required = {"version", "workflow_id", "purpose", "source_subdir", "contract_ref", "acceptance",
                "invariants", "exclude", "risk", "allowed_paths", "protected_paths", "max_seconds",
                "max_artifact_bytes", "steps", "verification_steps"}
    optional = {"external_input_allowed", "codex_version"}
    if not isinstance(config, dict) or not required <= config.keys() or config.keys() - required - optional:
        raise Halt("Missing or unknown workflow fields", "specification")
    if config["version"] != 1 or config["risk"] != "LOW":
        raise Halt("This first-stage workflow supports explicit LOW risk only", "permission")
    identifier(config["workflow_id"])
    if not isinstance(config["purpose"], str) or not config["purpose"].strip():
        raise Halt("Purpose is required", "specification")
    for field in ("acceptance", "invariants", "exclude", "allowed_paths", "protected_paths", "verification_steps"):
        strings(config[field])
    for field in ("source_subdir", "contract_ref"):
        path_name(config[field])
    for field in ("allowed_paths", "protected_paths"):
        for name in config[field]:
            path_name(name)
    protected = set(config["protected_paths"])
    if config["contract_ref"] not in protected:
        raise Halt("The canonical specification must be protected", "permission")
    for name in config["allowed_paths"]:
        if name in protected or Path(name).name in {"feature-map.xml", ".gitignore"} or any(
            re.search(r"(^|[_.-])(test|tests|spec|specs)([_.-]|$)", part, re.I) for part in name.split("/")):
            raise Halt("Tests, expectations and knowledge are protected", "permission")
    integer(config["max_seconds"], 86400)
    integer(config["max_artifact_bytes"], MAX_TREE)
    if type(config.get("external_input_allowed", False)) is not bool:
        raise Halt("External input needs explicit boolean authorization", "permission")
    if "codex_version" in config and not isinstance(config["codex_version"], str):
        raise Halt("Invalid reviewed CLI version", "specification")
    modules = catalog()
    steps = config["steps"]
    if not isinstance(steps, list) or not 1 <= len(steps) <= 100:
        raise Halt("Select between 1 and 100 steps", "specification")
    seen = {}
    for step in steps:
        if not isinstance(step, dict):
            raise Halt("Step must be a structured object", "specification")
        common = {"id", "module", "runner", "needs", "inputs", "outputs", "seconds", "mode"}
        fields = {"proposal"} if step.get("mode") == "recorded-proposal" else {"argv"} if step.get("mode") == "command" else set()
        if not common <= step.keys() or step.keys() - common - fields:
            raise Halt("Missing or unknown step fields", "specification")
        sid = identifier(step["id"])
        if sid in seen or step["module"] not in modules:
            raise Halt("Duplicate step or unknown module", "specification")
        if step["runner"] not in ROLES:
            raise Halt("BLOCKED: database/Windows runner capability is not implemented", "capability")
        needs = strings(step["needs"], empty=True)
        if any(dep not in seen for dep in needs):
            raise Halt("Dependencies must precede the step; cycles are forbidden", "specification")
        for field in ("inputs", "outputs"):
            for name in strings(step[field], empty=field == "outputs"):
                path_name(name)
        integer(step["seconds"], config["max_seconds"])
        if step["runner"] == "ai":
            if step["mode"] not in {"recorded-proposal", "codex"} or step["outputs"] != ["proposal.json"]:
                raise Halt("AI returns only the fixed proposal contract", "specification")
            if step["mode"] == "recorded-proposal":
                path_name(step["proposal"])
                if step["proposal"] not in step["inputs"] or step["proposal"] not in protected:
                    raise Halt("Recorded proposals must be fixed protected inputs", "permission")
            elif not config.get("external_input_allowed") or not config.get("codex_version"):
                raise Halt("Codex needs explicit source transmission and reviewed version", "permission")
        else:
            if step["mode"] != "command" or not isinstance(step.get("argv"), list) or not step["argv"] or any(
                    not isinstance(x, str) or not x or "\x00" in x for x in step["argv"]):
                raise Halt("Build commands must be fixed argv arrays", "specification")
        seen[sid] = step
    if any(sid not in seen or seen[sid]["runner"] != "build" for sid in config["verification_steps"]):
        raise Halt("Required verification must name selected Build/Test steps", "specification")
    return config


def file_hash(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise Halt("Only regular artifact files are supported", "integrity")
    size = path.stat().st_size
    if size > MAX_TREE:
        raise Halt("Artifact file exceeds size limit", "budget")
    return {"bytes": size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def tree(root: Path) -> dict:
    if root.is_symlink() or not root.is_dir():
        raise Halt("Invalid source/artifact root", "integrity")
    out = {}
    total = 0
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise Halt("Symlinks are not supported in snapshots", "permission")
        if path.is_dir():
            continue
        name = path_name(path.relative_to(root).as_posix())
        out[name] = file_hash(path)
        total += out[name]["bytes"]
        if len(out) > MAX_FILES or total > MAX_TREE:
            raise Halt("Snapshot exceeds first-stage limits", "budget")
    return out


def inputs(root: Path, names: list[str]) -> dict:
    return {name: file_hash(safe_file(root, path_name(name))) for name in names}


def layout(root: Path) -> None:
    if root.is_symlink():
        raise Halt("Linked run roots are forbidden", "permission")
    for name in ("state", "candidate", "requests/ai", "requests/build", "results/ai", "results/build"):
        (root / name).mkdir(parents=True, exist_ok=True)


def lock(path: Path) -> int:
    """Fail closed; stale ownership is resolved only after operators stop all services."""
    try:
        return os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise Halt("Run is owned or interrupted; inspect it before unlocking", "ownership") from None
