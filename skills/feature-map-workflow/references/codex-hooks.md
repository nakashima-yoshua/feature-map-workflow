# Codex Hook Integration

## Purpose

Use lifecycle hooks to enforce timing, not to replace source analysis. Keep exact checks deterministic. Use model/Jev judgment only where semantic interpretation is actually required.

## Bundled events

### UserPromptSubmit

`matcher` is not used for this event in Codex.

The hook:

1. Reads the submitted prompt.
2. Detects advisory ambiguity signals such as undefined scope words or operation criteria.
3. Reads compact Feature Map context when available.
4. Adds developer context that requires a context-sufficiency check before affected edits.
5. Optionally asks Jev for `context_sufficient`, `question_required`, and `missing_context_type` when context Jev is explicitly enabled.

The hook does **not** mechanically block the user's prompt merely because a vague word appears. The coding model must first reuse conversation/repository/Feature Map evidence. If a material gap remains, it asks one concise natural-Japanese question before the affected action.

### SessionStart

- Discover exactly one Feature Map.
- Prefer `FEATURE_MAP_PATH` when a repository contains more than one candidate.
- Parse XML locally.
- Add only feature identity, purpose, scope/exclusion, high-impact open items, pending verification, and a few key references to model context.
- Store a canonical XML hash as the session baseline.

### PostToolUse: Edit/Write

- Track the current git-changed file set.
- Track the current Feature Map hash.
- If the Feature Map becomes malformed, add a short correction context immediately.
- Do not call Jev per edit; avoid latency/cost on the hot path.

### PostToolUse: xquery schema validation

When the tool name is `mcp__xquery__xml_validate_schema` and the response confirms validity, store a canonical hash of the exact XML payload. Stop can then prove that the current XML version was validated, rather than merely remembering that some older version was validated.

### Stop

Apply gates in this order:

1. XML must be well-formed.
2. `verified`/`closed` must not coexist with high-impact open items or failed/blocked verification.
3. If the Feature Map changed during the session, the current canonical hash must have a successful xquery-mcp XSD validation.
4. If the map did not change but code/tests did and Jev is enabled, ask whether a durable map delta is likely.
5. Treat Jev human-review probability as advisory; do not automatically approve/reject work from it.

`FEATURE_MAP_MAX_STOP_BLOCKS` defaults to `2` so an unhealthy hook cannot create an unbounded continue loop.

## UserPromptSubmit output policy

Codex supports `hookSpecificOutput.additionalContext` for this event. This plugin uses it rather than hard-blocking the prompt. A clarification needs model reasoning and natural-language rendering, while a regex match does not prove that the request is unsafe or incomplete.

The injected policy is intentionally narrow:

- ask only when missing context materially changes outcome, scope, authority, irreversible/external action, business rule, or acceptance;
- use local evidence before asking;
- otherwise state a narrow reversible assumption and proceed;
- when asking, give the current interpretation first and ask one question;
- preserve meaning, identifiers, modality, scope, and exclusions while rendering natural Japanese.

## Configuration

- `FEATURE_MAP_PATH`: explicit XML path, absolute or repo-relative.
- `FEATURE_MAP_MAX_STOP_BLOCKS`: maximum Stop continuations caused by this plugin; default `2`.
- `FEATURE_MAP_CONTEXT_JEV_MODE`: `off` (default), `metadata`, or `prompt`.
- `FEATURE_MAP_CONTEXT_QUESTION_THRESHOLD`: advisory Jev question threshold; default `0.75`.

Plugin hooks are non-managed hooks and require explicit user trust in Codex. They run only where their scripts exist in the execution environment.
