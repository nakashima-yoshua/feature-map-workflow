# Decision Providers

## Purpose

Bounded probabilistic judgments are behind a provider boundary so the workflow does not depend on one classifier vendor.

The provider may advise:

- whether clarification is likely required;
- which missing-context category is most material;
- whether a durable Feature Map update is likely;
- which Feature Map section is the best candidate;
- whether human review is likely required.

It must never establish repository facts or perform writes.

## Providers

### off

Default. No external decision call.

### jev

Legacy-compatible external provider using the TypeSafe Jev API. No new Jev dependency is needed for OpenAI or the runner.

The existing `FEATURE_MAP_JEV_*` variables remain supported for backward compatibility.

### openai

Implemented public-beta adapter for `POST https://api.openai.com/v1/decisions`.
The default model is `gpt-6-luna`; authentication uses `OPENAI_API_KEY`, without
TypeSafe credentials. Request `input` is a JSON text string; `questions[]` has
named `predicate` and `choice` items. Predicate answers normalize `probability`
to the existing hook's numeric fields. Choice questions use
`choices[{value,description}]`; named `answers[]` normalize to the existing
result keys. There is no Jev `state`, `noul`, or `criteria` wire format.

Context questions are `context_sufficient`, `question_required` and
`missing_context_type`. Completion questions are `update_required`,
`update_section` and `human_review_required`. No score or open-ended business
decision is requested. The beta boundary is isolated in `OpenAIDecisionsProvider`.
See the [official guide](https://developers.openai.com/api/docs/guides/decisions)
and [API reference](https://developers.openai.com/api/reference/cli/resources/decisions/methods/create).

Missing/duplicate/unnamed answers, refusal, wrong model/type, unknown choices,
nonfinite or out-of-range numbers and malformed response bodies produce
undetermined advice, never a fabricated zero/false answer. 401/403/429/5xx and
timeouts fail open for advice only; deterministic/permission/approval gates keep
their independent fail-closed policy. No retries or raw response logging occurs.
Redirects are refused to avoid forwarding credentials to another host.

Selecting `openai` does not enable either call site automatically. Generic modes
default to `off` and never inherit legacy Jev content modes. Explicit `off`
overrides old modes. Old unset-provider Jev configurations continue to select Jev.

### Data handling

OpenAI `metadata` contains only counts, presence flags and fixed categories/statuses;
it does not send feature names, purpose, source paths, prompt, diff or assistant
text. `prompt` opts into up to 3000 characters of submitted text; `summary` into
up to 3000 characters of assistant text; `diff` additionally into 8000 characters
of source diff. Known credential patterns, secret environment values, PEM private
keys and email addresses are redacted before truncation. This is not comprehensive
PII/DLP filtering. If content cannot be sent under contract, use `off`; review
content before opting in. Model selection and input mode changes need evaluation,
not silent promotion of beta quality to production quality.

Repository tests mock transport, both hook call sites, failure modes and legacy
selection. Live API cost, latency and accuracy are not measured. A separately
authorized optional smoke test can call `context_decide` and `completion_decide`
with synthetic non-sensitive inputs, record only normalized answers and measured
timing, and leave required gates untouched.

## Generic configuration

Select the provider:

```sh
FEATURE_MAP_DECISION_PROVIDER=off
FEATURE_MAP_DECISION_PROVIDER=jev
FEATURE_MAP_DECISION_PROVIDER=openai
```

Generic privacy/input modes:

```sh
FEATURE_MAP_DECISION_CONTEXT_MODE=off|metadata|prompt
FEATURE_MAP_DECISION_COMPLETION_MODE=off|metadata|summary|diff
```

Generic thresholds:

- `FEATURE_MAP_DECISION_CONTEXT_THRESHOLD` (default 0.75)
- `FEATURE_MAP_DECISION_UPDATE_THRESHOLD` (default 0.70)
- `FEATURE_MAP_DECISION_REVIEW_THRESHOLD` (default 0.85)
- `FEATURE_MAP_DECISION_MODEL` (provider-specific model identifier)

When the generic variables are absent and Jev legacy modes are enabled, the provider is inferred as `jev`.

## Boundary

Keep these deterministic:

- file existence and exact source references;
- Git state, hashes, branches, and commits;
- XML parsing and XSD validity;
- numeric policy thresholds;
- permissions and authorization;
- destructive or irreversible actions;
- queue/dependency/conflict transitions.

A provider result is advisory evidence only. The coding model or deterministic policy must reconcile it with current repository evidence before acting.
