# Jev Decision Provider

Jev is the currently implemented external provider behind the generic DecisionProvider boundary. See `decision-providers.md` for provider selection and generic environment variables.


## Role

Jev is an optional decision layer. It must not become the source of truth.

Use it for bounded semantic judgments after exact code has already collected state.

### Completion judgment

- `update_required` (Noul): probability that a durable Feature Map delta is needed.
- `update_section` (Choice): `source_map`, `rule`, `invariant`, `decision`, `verify`, `open`, or `none`.
- `human_review_required` (Noul): probability that an ambiguity/acceptance risk should be surfaced to a person.

### Context-sufficiency judgment

When explicitly enabled for `UserPromptSubmit`:

- `context_sufficient` (Noul): probability that the request has enough context to proceed without a user clarification after available local evidence is considered.
- `question_required` (Noul): probability that one user clarification is materially required before affected edits/actions.
- `missing_context_type` (Choice): `scope`, `authority`, `business_rule`, `expected_behavior`, `acceptance`, `external_dependency`, `data`, `environment`, or `none`.

The coding model still decides whether the gap is real. Jev does not write the question and never directly blocks or edits anything.

Do not use Jev for XML validity, numeric thresholds, permissions, Git state, file existence, or exact code facts.

## API

The hook calls `POST https://api.typesafe.ai/v1/systemone` directly using `TYPESAFE_API_KEY`. No TypeSafe SDK is bundled.

Default model alias: `jev-latest`.

## Completion privacy modes

Jev completion judgment is off by default.

Set `FEATURE_MAP_JEV_MODE` explicitly:

- `off`: no completion external call.
- `metadata`: Feature Map state/purpose, changed file names, and git diff statistics.
- `summary`: metadata plus the current assistant message, capped at 3000 characters.
- `diff`: summary plus git diff text, capped at 8000 characters.

## Context-gate privacy modes

Context Jev is independently off by default. Set `FEATURE_MAP_CONTEXT_JEV_MODE`:

- `off`: no prompt-time external call.
- `metadata`: send Feature Map metadata, prompt length, local risk categories, and high-impact-open counts. Do not send prompt text or matched phrases.
- `prompt`: metadata plus the submitted prompt, capped at 3000 characters.

Before using `prompt`, verify that project/client policy permits sending user prompt content to TypeSafe. A TypeSafe API failure is fail-open; the local context gate still runs.

## Thresholds

- `FEATURE_MAP_JEV_UPDATE_THRESHOLD`: default `0.70`.
- `FEATURE_MAP_JEV_REVIEW_THRESHOLD`: default `0.85`.
- `FEATURE_MAP_CONTEXT_QUESTION_THRESHOLD`: default `0.75`.
- `FEATURE_MAP_JEV_MODEL`: default `jev-latest`.

Thresholds are policy, not model facts. Evaluate them on representative project examples before relying on them for automation.

## Action policy

A high `update_required` result can cause one bounded Stop continuation if the Feature Map stayed unchanged. The coding model must then inspect the actual source/test delta and decide what, if anything, is true enough to store.

A high `question_required` result only strengthens the developer context given to the coding model. The model must verify the ambiguity against local evidence and, if still material, ask one natural-Japanese question before the affected operation.

Never write a rule/invariant/decision merely because Jev selected that section. Never ask a user merely because Jev produced a high probability when the repository already resolves the issue.
