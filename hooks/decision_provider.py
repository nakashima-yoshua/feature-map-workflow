from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Mapping


class DecisionProvider:
    name = "off"

    def context_decide(
        self,
        mode: str,
        summary: dict[str, Any],
        prompt: str,
        signals: list[dict[str, str]],
    ) -> tuple[dict[str, Any] | None, str | None]:
        return None, None

    def completion_decide(
        self,
        mode: str,
        summary: dict[str, Any],
        changed_files: list[str],
        last_assistant_message: str,
        diff_stat: str,
        git_diff: str,
    ) -> tuple[dict[str, Any] | None, str | None]:
        return None, None


class OffDecisionProvider(DecisionProvider):
    name = "off"


class UnavailableDecisionProvider(DecisionProvider):
    def __init__(self, name: str, reason: str) -> None:
        self.name = name
        self.reason = reason

    def _warning(self, mode: str) -> tuple[None, str | None]:
        if mode == "off":
            return None, None
        return None, f"Decision provider {self.name!r} is unavailable: {self.reason}"

    def context_decide(
        self,
        mode: str,
        summary: dict[str, Any],
        prompt: str,
        signals: list[dict[str, str]],
    ) -> tuple[dict[str, Any] | None, str | None]:
        return self._warning(mode)

    def completion_decide(
        self,
        mode: str,
        summary: dict[str, Any],
        changed_files: list[str],
        last_assistant_message: str,
        diff_stat: str,
        git_diff: str,
    ) -> tuple[dict[str, Any] | None, str | None]:
        return self._warning(mode)


class JevDecisionProvider(DecisionProvider):
    name = "jev"

    def __init__(self, env: Mapping[str, str] | None = None) -> None:
        self.env = env if env is not None else os.environ

    def _model(self) -> str:
        return (
            self.env.get("FEATURE_MAP_DECISION_MODEL")
            or self.env.get("FEATURE_MAP_JEV_MODEL")
            or "jev-latest"
        ).strip() or "jev-latest"

    def _request(
        self,
        payload: dict[str, Any],
        label: str,
    ) -> tuple[dict[str, Any] | None, str | None]:
        api_key = self.env.get("TYPESAFE_API_KEY", "").strip()
        if not api_key:
            return None, f"{label} is enabled but TYPESAFE_API_KEY is not set"

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
            return data if isinstance(data, dict) else {}, None
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                detail = ""
            return None, f"{label} HTTP {exc.code}: {detail or exc.reason}"
        except Exception as exc:
            return None, f"{label} unavailable: {exc}"

    def context_decide(
        self,
        mode: str,
        summary: dict[str, Any],
        prompt: str,
        signals: list[dict[str, str]],
    ) -> tuple[dict[str, Any] | None, str | None]:
        state: dict[str, Any] = {
            "feature": {
                "name": summary.get("feature", ""),
                "state": summary.get("state", ""),
                "purpose": summary.get("purpose", "")[:600],
                "scope_present": bool(summary.get("scope")),
                "exclude_present": bool(summary.get("exclude")),
                "high_impact_open_count": sum(
                    1 for x in summary.get("open", []) if x.get("impact") == "high"
                ),
            },
            "prompt_length": len(prompt),
            "local_signal_categories": sorted(
                {x.get("category", "") for x in signals if x.get("category")}
            ),
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
        data, warning = self._request(
            {"model": self._model(), "state": state, "questions": questions},
            "Context Jev",
        )
        if warning or data is None:
            return None, warning
        answers = data.get("answers", {})
        return {
            "provider": self.name,
            "model": data.get("model"),
            "context_sufficient": float((answers.get("context_sufficient") or {}).get("noul", 0.0)),
            "question_required": float((answers.get("question_required") or {}).get("noul", 0.0)),
            "missing_context_type": (answers.get("missing_context_type") or {}).get("choice", "none"),
            "missing_context_confidence": float(
                (answers.get("missing_context_type") or {}).get("confidence", 0.0)
            ),
        }, None

    def completion_decide(
        self,
        mode: str,
        summary: dict[str, Any],
        changed_files: list[str],
        last_assistant_message: str,
        diff_stat: str,
        git_diff: str,
    ) -> tuple[dict[str, Any] | None, str | None]:
        state: dict[str, Any] = {
            "feature": {
                "name": summary.get("feature", ""),
                "mode": summary.get("mode", ""),
                "state": summary.get("state", ""),
                "purpose": summary.get("purpose", "")[:800],
                "high_impact_open_count": sum(
                    1 for x in summary.get("open", []) if x.get("impact") == "high"
                ),
                "verification_statuses": [
                    x.get("status", "") for x in summary.get("verify", [])
                ][:20],
            },
            "changed_files": changed_files[:40],
            "diff_stat": diff_stat[:4000],
        }
        if mode in {"summary", "diff"}:
            state["assistant_summary"] = (last_assistant_message or "")[-3000:]
        if mode == "diff":
            state["git_diff"] = git_diff[:8000]

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
        data, warning = self._request(
            {"model": self._model(), "state": state, "questions": questions},
            "Jev",
        )
        if warning or data is None:
            return None, warning
        answers = data.get("answers", {})
        return {
            "provider": self.name,
            "model": data.get("model"),
            "update_required": float((answers.get("update_required") or {}).get("noul", 0.0)),
            "update_section": (answers.get("update_section") or {}).get("choice", "none"),
            "update_section_confidence": float(
                (answers.get("update_section") or {}).get("confidence", 0.0)
            ),
            "human_review_required": float(
                (answers.get("human_review_required") or {}).get("noul", 0.0)
            ),
        }, None


def _normalize_mode(value: str | None, allowed: set[str]) -> str:
    mode = (value or "off").strip().lower()
    return mode if mode in allowed else "off"


def get_decision_provider(env: Mapping[str, str] | None = None) -> DecisionProvider:
    env = env if env is not None else os.environ
    selected = (env.get("FEATURE_MAP_DECISION_PROVIDER") or "").strip().lower()
    if not selected:
        legacy_completion = _normalize_mode(
            env.get("FEATURE_MAP_JEV_MODE"),
            {"off", "metadata", "summary", "diff"},
        )
        legacy_context = _normalize_mode(
            env.get("FEATURE_MAP_CONTEXT_JEV_MODE"),
            {"off", "metadata", "prompt"},
        )
        selected = "jev" if legacy_completion != "off" or legacy_context != "off" else "off"

    if selected == "off":
        return OffDecisionProvider()
    if selected == "jev":
        return JevDecisionProvider(env)
    if selected == "openai":
        return UnavailableDecisionProvider(
            "openai",
            "the OpenAI Decisions API adapter is reserved until a public, stable API contract is available",
        )
    return UnavailableDecisionProvider(selected, "unknown provider")


def context_mode(provider_name: str, env: Mapping[str, str] | None = None) -> str:
    env = env if env is not None else os.environ
    generic = env.get("FEATURE_MAP_DECISION_CONTEXT_MODE")
    if generic is not None:
        return _normalize_mode(generic, {"off", "metadata", "prompt"})
    if provider_name == "jev":
        return _normalize_mode(
            env.get("FEATURE_MAP_CONTEXT_JEV_MODE"),
            {"off", "metadata", "prompt"},
        )
    return "off"


def completion_mode(provider_name: str, env: Mapping[str, str] | None = None) -> str:
    env = env if env is not None else os.environ
    generic = env.get("FEATURE_MAP_DECISION_COMPLETION_MODE")
    if generic is not None:
        return _normalize_mode(generic, {"off", "metadata", "summary", "diff"})
    if provider_name == "jev":
        return _normalize_mode(
            env.get("FEATURE_MAP_JEV_MODE"),
            {"off", "metadata", "summary", "diff"},
        )
    return "off"
