from __future__ import annotations

import json
import math
import os
import re
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


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class OpenAIDecisionsProvider(DecisionProvider):
    """Beta adapter. Advice only: never establishes permissions or verification."""

    name = "openai"
    ENDPOINT = "https://api.openai.com/v1/decisions"
    CONTEXT_CHOICES = {
        "scope": "Target or exclusions are unclear.",
        "authority": "Permission for an external or irreversible action is unclear.",
        "business_rule": "A domain rule is missing.",
        "expected_behavior": "Multiple externally visible results are plausible.",
        "acceptance": "An observable success condition is missing.",
        "external_dependency": "An external contract or dependency is unclear.",
        "data": "Data semantics or migration behavior is unclear.",
        "environment": "The execution or deployment boundary is unclear.",
        "none": "No material clarification appears necessary.",
    }
    SECTION_CHOICES = {
        "source_map": "Source, test, data or API navigation changed.",
        "rule": "A durable business rule changed.",
        "invariant": "A property that must remain true changed.",
        "decision": "A non-obvious design decision should be retained.",
        "verify": "Verification evidence changed.",
        "open": "An unresolved material blocker changed.",
        "none": "No durable Feature Map delta is needed.",
    }

    def __init__(self, env: Mapping[str, str] | None = None) -> None:
        self.env = env if env is not None else os.environ

    def _redact(self, text: str) -> str:
        # Content modes are explicit opt-in, not a guarantee of anonymization.
        for name, value in self.env.items():
            if re.search(r"key|token|secret|password", name, re.I) and len(value) >= 8:
                text = text.replace(value, "[REDACTED]")
        text = re.sub(r"-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----",
                      "[REDACTED PRIVATE KEY]", text, flags=re.S)
        text = re.sub(r"\b(?:sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9_]{8,})\b", "[REDACTED]", text)
        text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[REDACTED EMAIL]", text)
        text = re.sub(r"(?im)((?:api[_-]?key|password|token|secret)\s*[=:]\s*)[^\s,;]+",
                      r"\1[REDACTED]", text)
        return text

    @staticmethod
    def _probability(value: Any) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("invalid probability")
        if not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("invalid probability")
        return float(value)

    def _request(self, state: dict[str, Any], questions: list[dict[str, Any]],
                 confidence_key: str) -> tuple[dict[str, Any] | None, str | None]:
        key = self.env.get("OPENAI_API_KEY", "").strip()
        if not key:
            return None, "OpenAI Decisions is enabled but OPENAI_API_KEY is not set"
        model = self.env.get("FEATURE_MAP_DECISION_MODEL", "gpt-6-luna").strip() or "gpt-6-luna"
        payload = {"model": model, "input": self._redact(json.dumps(state, ensure_ascii=False)),
                   "questions": questions}
        req = urllib.request.Request(self.ENDPOINT, method="POST",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            opener = urllib.request.build_opener(_NoRedirect())
            with opener.open(req, timeout=8.0) as response:
                raw = response.read(65537)
            if len(raw) > 65536:
                raise ValueError("response too large")
            data = json.loads(raw)
            if not isinstance(data, dict) or not isinstance(data.get("answers"), list):
                raise ValueError("invalid response")
            if data.get("model", model) != model:
                raise ValueError("unexpected model")
            by_name: dict[str, Any] = {}
            for answer in data["answers"]:
                if not isinstance(answer, dict) or not isinstance(answer.get("name"), str):
                    raise ValueError("unnamed answer")
                if answer["name"] in by_name:
                    raise ValueError("duplicate answer")
                by_name[answer["name"]] = answer
            if set(by_name) != {q["name"] for q in questions}:
                raise ValueError("missing or unexpected answer")
            result: dict[str, Any] = {"provider": self.name, "model": model}
            for question in questions:
                answer = by_name[question["name"]]
                if answer.get("type") != question["type"]:
                    raise ValueError("refusal or changed answer type")
                if question["type"] == "predicate":
                    result[question["name"]] = self._probability(answer.get("probability"))
                else:
                    choice = answer.get("choice")
                    if not isinstance(choice, str) or choice not in {c["value"] for c in question["choices"]}:
                        raise ValueError("invalid choice")
                    result[question["name"]] = choice
                    result[confidence_key] = self._probability(answer.get("confidence"))
                    if "probabilities" in answer:
                        probabilities = answer["probabilities"]
                        if not isinstance(probabilities, list):
                            raise ValueError("invalid choice distribution")
                        values = [p.get("value") for p in probabilities if isinstance(p, dict)]
                        if len(values) != len(probabilities) or len(values) != len(set(values)) or \
                                set(values) != {c["value"] for c in question["choices"]}:
                            raise ValueError("invalid choice distribution")
                        if abs(sum(self._probability(p.get("probability")) for p in probabilities) - 1) > .01:
                            raise ValueError("invalid choice distribution")
            return result, None
        except urllib.error.HTTPError as exc:
            # Never include response bodies, headers, credentials, or request text.
            return None, f"OpenAI Decisions HTTP {exc.code}; advisory unavailable"
        except Exception as exc:
            return None, f"OpenAI Decisions unavailable ({type(exc).__name__}); advisory undetermined"

    @staticmethod
    def _predicate(name: str, instructions: str) -> dict[str, Any]:
        return {"name": name, "type": "predicate", "instructions": instructions}

    @staticmethod
    def _choice(name: str, instructions: str, choices: dict[str, str]) -> dict[str, Any]:
        return {"name": name, "type": "choice", "instructions": instructions,
                "choices": [{"value": value, "description": description}
                            for value, description in choices.items()]}

    def context_decide(self, mode, summary, prompt, signals):
        if mode not in {"metadata", "prompt"}:
            return None, None
        state = {"scope_present": bool(summary.get("scope")),
                 "exclude_present": bool(summary.get("exclude")),
                 "high_impact_open_count": sum(x.get("impact") == "high" for x in summary.get("open", [])),
                 "prompt_length": len(prompt),
                 "local_signal_categories": sorted({x.get("category") for x in signals
                     if x.get("category") in {"scope", "criteria", "authority"}})}
        if mode == "prompt":
            state["prompt"] = self._redact(prompt)[:3000]
        return self._request(state, [
            self._predicate("context_sufficient", "Is local context likely sufficient after checking source, tests and the Feature Map?"),
            self._predicate("question_required", "Is a human clarification likely required for materially missing scope, authority, behavior, acceptance or dependency?"),
            self._choice("missing_context_type", "Select the most material missing-context category.", self.CONTEXT_CHOICES),
        ], "missing_context_confidence")

    def completion_decide(self, mode, summary, changed_files, last_assistant_message, diff_stat, git_diff):
        if mode not in {"metadata", "summary", "diff"}:
            return None, None
        state = {"changed_file_count": len(changed_files),
                 "high_impact_open_count": sum(x.get("impact") == "high" for x in summary.get("open", [])),
                 "verification_statuses": [x.get("status") for x in summary.get("verify", [])
                     if x.get("status") in {"passed", "failed", "blocked", "planned", "not-run"}][:20]}
        if mode in {"summary", "diff"}:
            state["assistant_summary"] = self._redact(last_assistant_message or "")[-3000:]
        if mode == "diff":
            state["git_diff"] = self._redact(git_diff)[:8000]
        return self._request(state, [
            self._predicate("update_required", "Did durable feature knowledge change? Internal refactoring alone is not a durable delta."),
            self._choice("update_section", "Select the section for the most important durable delta.", self.SECTION_CHOICES),
            self._predicate("human_review_required", "Is a material ambiguity or acceptance risk likely to need human review? This is advice, never approval."),
        ], "update_section_confidence")


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
        return OpenAIDecisionsProvider(env)
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
