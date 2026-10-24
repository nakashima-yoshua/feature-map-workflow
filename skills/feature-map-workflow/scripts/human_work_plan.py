"""Validate optional procedure-based work plans; never execute or approve checks."""
from __future__ import annotations

from copy import deepcopy
from datetime import date
import math
import re


def string(item, key, where):
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where}.{key} must be a nonempty string")
    return value.strip()


def strings(item, key, where, *, empty=False):
    value = item.get(key)
    if (not isinstance(value, list) or (not value and not empty)
            or any(not isinstance(x, str) or not x.strip() for x in value)):
        raise ValueError(f"{where}.{key} must be a list of nonempty strings")
    return [x.strip() for x in value]


def objects(item, key, where):
    value = item.get(key)
    if not isinstance(value, list) or not value or any(not isinstance(x, dict) for x in value):
        raise ValueError(f"{where}.{key} must be a nonempty list of objects")
    return value


def identifier(item, key, where):
    value = string(item, key, where)
    if re.search(r"[\s|]", value):
        raise ValueError(f"{where}.{key} cannot contain whitespace or a pipe")
    return value


def normalize_v2(raw, case_ids, source_revision=None):
    """Resolve frozen procedure references into a serial, reviewable plan snapshot.

    Applicability equality is a planning check, not proof of actual runtime state.
    Steps remain ordered; parallelSafe is advice, never a scheduler instruction.
    """
    if not isinstance(raw, dict) or type(raw.get("version")) is not int or raw["version"] != 2:
        raise ValueError("Expected Human Work Plan version 2")
    plan = deepcopy(raw)
    environment = string(plan, "environment", "plan")
    revision = string(plan, "sourceRevision", "plan")
    if source_revision is not None and revision != source_revision:
        raise ValueError("Work plan sourceRevision does not match the workbook")
    strings(plan, "preflight", "plan")
    procedures = {}
    for part in objects(plan, "procedures", "plan"):
        pid = identifier(part, "id", "procedure")
        if pid in procedures:
            raise ValueError(f"Repeated procedure ID: {pid}")
        for field in ("revision", "sourceRef", "action", "precondition", "postcondition",
                      "resetBefore", "recovery"):
            string(part, field, pid)
        if part.get("status") not in {"draft", "active", "retired"}:
            raise ValueError(f"{pid}: unknown procedure lifecycle status")
        if part.get("status") == "active":
            try:
                verified = date.fromisoformat(string(part, "verifiedAt", pid))
            except ValueError as exc:
                raise ValueError(f"{pid}: active procedure needs a valid verifiedAt date") from exc
            if verified > date.today():
                raise ValueError(f"{pid}: active procedure verifiedAt cannot be in the future")
        for field in ("parallelSafe", "destructive"):
            if type(part.get(field)) is not bool:
                raise ValueError(f"{pid}.{field} must be boolean")
        if part["destructive"] and part["parallelSafe"]:
            raise ValueError(f"{pid}: destructive operations cannot declare parallelSafe")
        if not isinstance(part.get("appliesTo"), dict):
            raise ValueError(f"{pid}: appliesTo is required")
        for field in ("environment", "sourceRevision", "actor", "data"):
            string(part["appliesTo"], field, pid + ".appliesTo")
        procedures[pid] = part

    seen_sessions, seen_operations, bindings, conditions, covered = set(), set(), set(), set(), set()
    last_numbers = {}
    selected = set(case_ids)
    required = plan.get("requiredConditions")
    if not isinstance(required, dict) or set(required) != selected:
        raise ValueError("requiredConditions must identify exactly the selected cases")
    required_pairs = set()
    for cid in selected:
        condition_ids = strings(required, cid, "requiredConditions")
        if len(set(condition_ids)) != len(condition_ids):
            raise ValueError("Repeated required condition ID")
        required_pairs.update((cid, condition) for condition in condition_ids)
    for session in objects(plan, "sessions", "plan"):
        sid = string(session, "id", "session")
        if sid in seen_sessions:
            raise ValueError(f"Repeated session ID: {sid}")
        seen_sessions.add(sid)
        string(session, "title", sid)
        actor = string(session, "actor", sid)
        for field in ("sharedSetup", "stopOn", "cleanup"):
            strings(session, field, sid)
        prior = set()
        for step in objects(session, "steps", sid):
            oid = identifier(step, "id", sid)
            if oid in seen_operations:
                raise ValueError(f"Repeated operation ID: {oid}")
            seen_operations.add(oid)
            pid = string(step, "procedureId", oid)
            if pid not in procedures:
                raise ValueError(f"{oid}: unknown procedure {pid}")
            part = procedures[pid]
            if string(step, "procedureRevision", oid) != part["revision"] or part["status"] == "retired":
                raise ValueError(f"{oid}: stale or retired procedure reference")
            context = dict(environment=environment, sourceRevision=revision, actor=actor,
                           data=string(step, "data", oid))
            if any(context[key] != part["appliesTo"][key] for key in context):
                raise ValueError(f"{oid}: procedure applicability mismatch")
            dependencies = strings(step, "dependsOn", oid, empty=True)
            if len(set(dependencies)) != len(dependencies) or not set(dependencies) <= prior:
                raise ValueError(f"{oid}: dependencies must be earlier steps in the same session")
            if string(step, "restartFrom", oid) not in prior | {oid}:
                raise ValueError(f"{oid}: restartFrom must be this or an earlier session step")
            trial = step.get("trial")
            if not isinstance(trial, dict) or trial.get("mode") not in {"required", "delta", "reuse"}:
                raise ValueError(f"{oid}: trial mode must be required, delta or reuse")
            string(trial, "reason", oid + ".trial")
            if trial["mode"] == "reuse":
                if part["status"] != "active":
                    raise ValueError(f"{oid}: reuse requires an active verified procedure")
                string(trial, "recordRef", oid + ".trial")
            for check in objects(step, "checks", oid):
                cid = string(check, "caseId", oid)
                check["caseId"] = cid  # All downstream projections use the validated ID.
                if cid not in selected:
                    raise ValueError(f"{oid}: unknown or unselected case ID {cid}")
                for field in ("conditionId", "requirementRef", "expected", "capture"):
                    string(check, field, oid + ".check")
                identifier(check, "conditionId", oid + ".check")
                number = check.get("stepNo")
                if type(number) is not int or number < 1:
                    raise ValueError(f"{oid}: stepNo must be a positive integer")
                if number != last_numbers.get(cid, 0) + 1:
                    raise ValueError(f"{oid}: case stepNo must follow operation order consecutively from 1")
                last_numbers[cid] = number
                if "status" in check:
                    raise ValueError("Work plan checks cannot contain execution results")
                binding = (cid, number)
                condition = (cid, check["conditionId"])
                if binding in bindings or condition in conditions:
                    raise ValueError(f"{oid}: duplicate case step or condition binding")
                bindings.add(binding); conditions.add(condition); covered.add(cid)
            step["procedure"] = part
            prior.add(oid)
    if covered != selected:
        raise ValueError("Plan checks must cover exactly the selected case IDs")
    if conditions != required_pairs:
        raise ValueError("Plan checks must cover exactly the required condition IDs")

    if "measurements" in plan:
        measured = plan["measurements"]
        if not isinstance(measured, dict):
            raise ValueError("measurements must be an object")
        string(measured, "reference", "measurements")
        minutes = measured.get("minutes")
        allowed = {"preparation", "setup", "execution", "waiting", "switching", "rework", "evidence", "maintenance"}
        if not isinstance(minutes, dict) or not minutes or not set(minutes) <= allowed:
            raise ValueError("Unknown or empty measured time categories")
        for value in minutes.values():
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError("Measured minutes must be finite nonnegative numbers")
    return plan


def case_checkpoints(plan):
    """Project shared operations back to independent per-case, numbered rows."""
    cases = {}
    for session in plan["sessions"]:
        for step in session["steps"]:
            for check in step["checks"]:
                cases.setdefault(check["caseId"], []).append((session, step, check))
    for entries in cases.values():
        entries.sort(key=lambda entry: entry[2]["stepNo"])
    return cases
