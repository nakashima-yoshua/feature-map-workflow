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

Current implemented external provider using the TypeSafe Jev API.

The existing `FEATURE_MAP_JEV_*` variables remain supported for backward compatibility.

### openai

Reserved provider name for the OpenAI Decisions API.

The adapter intentionally remains unavailable until a public stable API contract is available. Selecting it currently fails open with a warning; the workflow continues using local deterministic/model policy.

Do not guess undocumented endpoints or payloads.

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
