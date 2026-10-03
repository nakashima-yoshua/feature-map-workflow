[日本語](README.ja.md) | English

# Feature Map Workflow Plugin

A Source-first development workflow that carries one compact Feature Map XML through catch-up, clarification, design, implementation, and verification.

## Architecture

- Source code: implementation truth
- Tests: executable behavior evidence
- Feature Map XML: human/AI navigation, durable rules, invariants, decisions, verification evidence, scope boundaries, and open blockers
- XSD: structural contract
- XSLT: one-page human view
- Git: change history
- xquery-mcp: narrow XPath/XQuery reads, XML formatting, and XSD validation
- Codex hooks: context gate, lifecycle timing, edit tracking, and completion gates
- Jev: optional bounded judgment for prompt-time context sufficiency and completion-time durable-map updates
- Operable Japanese: meaning-first rendering rules aligned with `natural-japanese` principles

## Design principle

The plugin separates internal meaning from human-facing prose.

```text
User request
  -> Context Sufficiency Gate
  -> meaning contract (only needed slots)
  -> source / tests / Feature Map investigation
  -> action or one clarification
  -> natural professional Japanese rendering
```

Priority:

```text
meaning preservation > operability > naturalness > brevity
```

The internal meaning contract may use `goal / actor / action / target / condition / scope / exclude / authority / doneWhen / certainty`. These are not persisted as a second specification. Only durable feature knowledge belongs in Feature Map XML.

## First-time setup

This plugin pins `xquery-mcp` 1.4.0.3 as a local .NET tool. Restore it once from NuGet.

Windows PowerShell:

```powershell
./scripts/setup-xquery-mcp.ps1
```

macOS/Linux:

```sh
./scripts/setup-xquery-mcp.sh
```

Requires .NET 10 SDK.

Codex plugin hooks are non-managed hooks. Review and trust `hooks/hooks.json` and `hooks/feature_map_hook.py` before enabling them. Hook scripts run only where the execution environment contains the plugin files; a web-only install does not deploy local scripts.

## Hook behavior

The bundled hooks are intentionally narrow:

1. `UserPromptSubmit`: scan for advisory ambiguity signals, read compact Feature Map context, and inject a context-sufficiency policy. It does not block merely because a vague word was detected. If a material gap remains after local investigation, Codex asks one precise natural-Japanese question before the affected action.
2. `SessionStart`: find one Feature Map, parse it locally, and add only a compact context slice.
3. `PostToolUse` on `Edit|Write`: track changed files and detect malformed Feature Map XML without emitting routine context.
4. `PostToolUse` on `mcp__xquery__xml_validate_schema`: remember the canonical hash of an XML payload that xquery-mcp confirmed as valid.
5. `Stop`: enforce local consistency checks, require XSD validation after a Feature Map change, and optionally ask Jev whether code/test changes likely require a durable Feature Map delta.

The prompt-time hook uses `additionalContext`, not a hard prompt block. Context sufficiency is semantic; regex matches are only signals. This lets Codex inspect source/tests/config/Feature Map before deciding whether a question is actually required.

Stop continuation is capped by `FEATURE_MAP_MAX_STOP_BLOCKS` (default `2`) to prevent loops.

## Operable Japanese

User-facing instructions and clarification questions follow these rules:

- fix meaning before wording;
- ask only for material gaps;
- state the current interpretation before a clarification;
- make `はい` or a short correction sufficient where practical;
- preserve scope, exclusions, certainty, numbers, and code identifiers;
- avoid undefined `適宜`, `必要に応じて`, `関連箇所`, `全部`, and similar execution words;
- avoid telegraphic controlled-language fragments when ordinary Japanese can express the same meaning safely;
- use one semantic claim per sentence without mechanically splitting a natural condition-action pair.

If the `natural-japanese` skill is available, its quick-mode principles should be used for the final rendering after the meaning is fixed. The plugin also bundles a compact standalone version of the required principles in `references/operable-japanese.md`.

## Mermaid diagrams

Feature Map 1.3 can carry Mermaid source directly in XML. Use CDATA so Mermaid symbols stay readable.

```xml
<diagrams>
  <diagram id="DG1" kind="sequence" title="Receiving flow"><![CDATA[
sequenceDiagram
    User->>ReceivingService: Import
    ReceivingService->>InventoryService: GetStock
    InventoryService-->>ReceivingService: Stock
  ]]></diagram>
</diagrams>
```

`feature-map.xsl` renders these blocks automatically. The generated HTML first loads `feature-map.mermaid.min.js` from the same directory. If that file is absent, it falls back to pinned Mermaid 12.0.0 on jsDelivr. Rendering uses Mermaid `securityLevel: strict`.
Mermaid 12 targets modern browsers (including Safari 17.4+). The renderer pins `layout: dagre`, `theme: default`, and `look: classic` so diagrams keep a conventional UML-like appearance across the v12 default-style change.

For an offline/local runtime, copy Mermaid beside the Feature Map:

```sh
./scripts/setup-mermaid.sh .
```

```powershell
./scripts/setup-mermaid.ps1 -Destination .
```

Do not generate diagrams mechanically from every class. Keep them only when they reduce the cost of understanding a boundary, interaction, state transition, or data relationship.

## OSS repository files

This distribution is ready to become the repository root. It includes `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `.github/CODEOWNERS`, Issue/PR templates, Dependabot configuration, CI/release workflows, and `docs/github-repository-settings.md`. Review the owner-specific placeholders before publishing.

## Optional Jev integration

Jev is disabled by default and split into two independent call sites.

### Completion-time Jev

Set `FEATURE_MAP_JEV_MODE`:

- `off`: no TypeSafe completion call (default).
- `metadata`: Feature Map state, changed file names, and git diff statistics.
- `summary`: metadata plus the current Codex assistant message, capped at 3000 characters.
- `diff`: summary plus a git diff, capped at 8000 characters.

It returns bounded judgments such as `update_required`, `update_section`, and `human_review_required`.

### Prompt-time context Jev

Set `FEATURE_MAP_CONTEXT_JEV_MODE`:

- `off`: no TypeSafe prompt-time call (default).
- `metadata`: Feature Map metadata, prompt length, local signal categories, and high-impact-open counts. No prompt text is sent.
- `prompt`: metadata plus the submitted prompt, capped at 3000 characters.

It returns advisory `context_sufficient`, `question_required`, and `missing_context_type` judgments. Codex still checks local evidence and writes the final question.

Both Jev paths require `TYPESAFE_API_KEY` and are fail-open. TypeSafe outages never stop development.

Example:

```sh
export TYPESAFE_API_KEY='...'
export FEATURE_MAP_JEV_MODE='summary'
export FEATURE_MAP_CONTEXT_JEV_MODE='metadata'
```

PowerShell:

```powershell
$env:TYPESAFE_API_KEY = '...'
$env:FEATURE_MAP_JEV_MODE = 'summary'
$env:FEATURE_MAP_CONTEXT_JEV_MODE = 'metadata'
```

Optional tuning:

- `FEATURE_MAP_JEV_MODEL` (default `jev-latest`)
- `FEATURE_MAP_JEV_UPDATE_THRESHOLD` (default `0.70`)
- `FEATURE_MAP_JEV_REVIEW_THRESHOLD` (default `0.85`)
- `FEATURE_MAP_CONTEXT_QUESTION_THRESHOLD` (default `0.75`)
- `FEATURE_MAP_MAX_STOP_BLOCKS` (default `2`)
- `FEATURE_MAP_PATH` (explicit Feature Map path when a repository has multiple maps)

Important: Jev is an external TypeSafe API. Do not enable content-bearing modes for source or prompt material that policy or contract forbids sending to that service. The plugin sends no repository or prompt content to TypeSafe while both Jev modes are `off`.

## Feature Map 1.3

Version 1.3 retains the 1.2 context fields and adds optional Mermaid diagrams:

- `goal/exclude`: explicit out-of-scope boundary when needed.
- `open/item@type`: classifies durable missing context such as `scope`, `authority`, `business-rule`, `expected-behavior`, `acceptance`, `external-dependency`, `data`, or `environment`.
- `diagrams/diagram`: Mermaid source for compact class, sequence, use-case, state, ER, flow, or architecture diagrams.

The bundled XSD still accepts Feature Map `1.1` and `1.2` for compatibility.

## Normal workflow

1. Receive the user's request.
2. Let the context gate reuse conversation and local evidence before deciding whether a question is needed.
3. If a critical gap remains, ask one natural-Japanese clarification. Do not edit the affected scope until resolved.
4. Create or locate the feature's `feature-map.xml`.
5. Use XPath to read only relevant nodes.
6. Inspect source/tests directly.
7. Patch only durable knowledge deltas into the XML.
8. Validate the current XML against `feature-map.xsd` with xquery-mcp.
9. Let the Stop hook catch missing validation or a likely missing durable update.
10. Keep history in Git; do not add a change-log section to the XML.

The reusable workflow lives in `skills/feature-map-workflow/`.
