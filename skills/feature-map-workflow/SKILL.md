---
name: feature-map-workflow
description: Maintain one Source-first Feature Map XML as the lightweight handoff artifact throughout system catch-up, requirements clarification, design, implementation, and verification. Use when analyzing unfamiliar or legacy code, planning or implementing a feature change, minimizing Markdown/specification output, mapping business rules to source/data/tests, maintaining compact Mermaid UML diagrams inside Feature Map XML, rendering those diagrams in the HTML view, updating Feature Map XML, validating it against XSD, using XPath/XQuery through xquery-mcp, working in Codex with lifecycle hooks and optional Jev judgments, or converting ambiguous Japanese development instructions into precise but natural, executable instructions and clarification questions.
---

# Feature Map Workflow

Use one Feature Map XML per feature as the durable human/AI index. Treat source code and tests as implementation truth; never translate source code into prose merely to create documentation.

## Core contract

- Keep `Source / Tests` as implementation and behavior truth.
- Keep `Feature Map XML` only for information that is costly or ambiguous to reconstruct from code.
- Keep change history in Git, not in XML.
- Prefer `file:symbol`, table, procedure, API, test, log, or commit references over explanations.
- Never regenerate the full XML when a minimal node patch is sufficient.
- Use Mermaid diagrams only when a relationship, sequence, or state transition is cheaper to understand visually than from source references. Do not diagram every class or branch.
- Do not create separate requirements/design/implementation/test Markdown documents unless explicitly requested.
- Apply YAGNI to **whole-system outcomes**, not merely local code size or runtime. Before adding architecture, tools, or automation, identify the actual constraint, consider no change, preserve safety/human approval, and measure impact on the path to accepted delivery.
- Keep user-facing responses delta-oriented. Do not echo the full Feature Map unless asked.
- Preserve user intent before optimizing wording. Use this priority: `meaning preservation > operability > naturalness > brevity`.

Read `references/feature-map-contract.md` when creating or restructuring a map. Read `references/agents-api.md` when running the workflow through the OpenAI Agents API or delegating read-only investigation to subagents. Read `references/repository-coordination.md` when multiple agents or humans need asynchronous repository-level commands, dependency-aware scheduling, conflict control, Git publication, or cross-document XML projection. Read `references/development-lifecycle.md` when planning work across requirements, design, tests, implementation, CI/CD, documentation, and delivery. Read `references/yagni-whole-system-optimization.md` when evaluating workflow bottlenecks, automation scope, change-vs-no-change tradeoffs, or end-to-end improvement. Read `references/test-strategy.md` when choosing E2E/integration/DB/unit boundaries. Read `references/coverage-model.md` when defining behavioral coverage denominators or completion evidence. Read `references/legacy-analysis.md` when tracing unfamiliar or legacy systems, especially dynamic/data-driven execution. Read `references/operable-japanese.md` before writing clarification questions or converting vague development instructions into executable Japanese. Read `references/context-gate.md` when deciding whether to ask the user or proceed with an assumption. Read `references/xquery-mcp.md` for XPath/XQuery/XSD operations. Read `references/programmatic-tool-calling.md` when several deterministic read/query/validation tool calls can be reduced in code. Read `references/decision-providers.md` when configuring bounded decision engines. Read `references/codex-hooks.md` when hooks are active or need troubleshooting. Read `references/jev.md` only when the optional Jev decision layer is enabled or being configured.

## Context sufficiency gate

Before editing code, files, schemas, data, configuration, or external systems:

1. Reuse the current conversation, Feature Map, source, tests, configuration, logs, and other available evidence before asking the user.
2. Determine whether any missing information materially changes:
   - objective or expected behavior;
   - target or scope;
   - explicit exclusions;
   - execution authority or an irreversible/external action;
   - business rule or acceptance condition;
   - external dependency, data assumption, or environment.
3. If the missing information is low-risk, reversible, and does not change the intended result, state the minimum assumption and proceed.
4. If it materially changes the result, authority, or major risk, ask exactly one question before changing anything affected by that ambiguity.
5. State the current interpretation before the question. Make the answer possible with `はい` or a short correction whenever practical.
6. Do not ask for information that can be established cheaply from the repository or Feature Map.

When a missing fact is durable feature knowledge, record it as an `open/item` with a `type`. Do not persist transient conversational uncertainty merely because the hook detected it.

## Operable Japanese

Construct meaning first; render Japanese second. Internally identify only the slots needed for the current operation:

`goal / actor / action / target / condition / scope / exclude / authority / doneWhen / certainty`

Do not require every slot for every request. A slot matters only when omitting it can change the action or result.

For user-facing Japanese:

- lead with the conclusion or current interpretation;
- keep one semantic claim per sentence, but do not mechanically split a natural condition-action pair;
- omit the subject when Japanese naturally permits it, but state the actor when responsibility is ambiguous;
- keep conditions close to the action they govern;
- avoid undefined `適宜`, `必要に応じて`, `関連箇所`, `全部`, `問題があれば`, and similar execution words;
- preserve `must / should / may`, confirmed/assumed/unknown status, scope, exclusions, numbers, and identifiers;
- keep file names, symbols, APIs, DB objects, and other identifiers unchanged unless the task explicitly renames them;
- avoid over-formal preambles, choppy telegraphic Japanese, and repeated template phrasing;
- prefer ordinary professional Japanese over a literal controlled-language style.

If the `natural-japanese` skill is available in the runtime, use its quick-mode principles for the final human-facing rendering after meaning is fixed. Do not let naturalization add facts, remove conditions, broaden scope, or upgrade uncertainty.

## Feature Map workflow

1. Locate the target feature, existing Feature Map XML, XSD, source entry points, tests, and relevant data objects.
2. If no Feature Map exists, create one from `assets/feature-map.example.xml` or run `scripts/init_feature_map.py`.
3. Read only XML sections needed for the current task. Prefer xquery-mcp `xpath_evaluate` instead of loading the whole document when the MCP server is available.
4. Inspect source/tests directly. Record only:
   - purpose and done condition;
   - include/exclude scope when it prevents ambiguity;
   - use cases that materially change control flow or data behavior;
   - source/data/test navigation references;
   - compact Mermaid diagrams for non-obvious cross-boundary relationships, sequences, or state transitions;
   - business rules and invariants;
   - non-obvious design decisions and external constraints;
   - verification cases and observed evidence;
   - unresolved questions that affect implementation or acceptance.
5. Apply the smallest XML patch. Preserve unrelated nodes and stable IDs.
6. Validate the current XML against `assets/feature-map.xsd` with xquery-mcp `xml_validate_schema` whenever available.
7. If validation fails, fix only the smallest failing node and validate again.
8. At completion, update only durable knowledge, references, verification results, or open items that actually changed. If none changed, leave the Feature Map untouched.

## Mermaid diagrams

Feature Map 1.3 can contain optional `diagrams/diagram` nodes. Store Mermaid source as CDATA so symbols and line breaks survive XML parsing. Use a stable ID when the diagram will be patched repeatedly.

```xml
<diagrams>
  <diagram id="DG1" kind="sequence" title="Order flow"><![CDATA[
sequenceDiagram
    User->>API: Submit order
    API->>DB: Insert order
    DB-->>API: OK
    API-->>User: Accepted
  ]]></diagram>
</diagrams>
```

Allowed `kind` labels are `class`, `sequence`, `usecase`, `state`, `activity`, `er`, `flowchart`, `architecture`, and `other`. The label documents intent; Mermaid syntax remains the source of rendering truth.

The bundled XSLT renders each node as a Mermaid block. It first tries `feature-map.mermaid.min.js` beside the XML/XSLT and falls back to Mermaid `12.0.0` from jsDelivr. Use `scripts/setup-mermaid.*` from the plugin root when an offline/local runtime is preferred. Rendering uses Mermaid `securityLevel: strict`.

Do not create a diagram when source references are already easier to understand. Prefer diagrams for:

- cross-module or external-system sequences;
- state machines and retry/rollback transitions;
- a small class relationship that explains a non-obvious boundary;
- data/entity relationships that materially affect behavior.

## Full lifecycle policy

Feature Map is the durable cross-phase index, not a container for every phase artifact. When the task spans development phases, follow `references/development-lifecycle.md`.

Keep these boundaries:

- requirements/design decisions that are expensive to reconstruct may become durable Feature Map knowledge;
- detailed test catalogs remain in tests/test data, while representative guarantees and evidence may be referenced by `verify`;
- CI results, generated coverage reports, runtime traces, and release artifacts remain canonical outside XML;
- legacy analysis may use richer internal graphs and evidence artifacts, but only durable findings, navigation references, representative diagrams, and unresolved blockers belong in Feature Map XML.

For testing, use `references/test-strategy.md` and `references/coverage-model.md`. Prefer business scenarios at E2E, condition/state/data behavior at integration or DB level, and residual unit tests only where isolation adds value.

For unfamiliar/legacy systems, use `references/legacy-analysis.md`. Distinguish possible, observed, observed-only, and unresolved execution paths. Never hide unknown areas behind a single coverage percentage.

## Agent runtime policy

When the OpenAI Agents API is used as the execution runtime, follow `references/agents-api.md`.

- Keep Feature Map Workflow runtime-independent; Agents API is an optional harness, not the source of truth.
- Use reader subagents only for independent investigation.
- Keep reader subagents read-only.
- Keep one parent/canonical writer for repository changes.
- Re-read current repository state before the writer applies a change assembled from parallel findings.
- Use one bounded session per feature/change boundary where practical.

## Repository coordination extension

Feature Map remains a knowledge index. Do not store queue state, leases, retries, operation journals, or projection metadata inside Feature Map XML.

When work expands from one agent editing one feature into multiple humans/agents issuing asynchronous repository-level changes, follow references/repository-coordination.md.

Keep these planes separate:

- Knowledge Plane: source/tests plus Feature Map durable knowledge.
- Coordination Plane: durable Task/Decision/Message/Dependency XML plus transient SQLite operation state.
- Projection Plane: a rebuildable multi-document XML index used for cross-document queries and role-specific AI context.

Use Repository API commands rather than unrestricted XML, XQuery Update, Git, shell, or arbitrary-path access. Writes should be idempotent, queued, dependency-aware, conflict-checked at enqueue and again before execution, serialized by one writer per repository, validated, committed, pushed, and only then projected.

Treat dependency and conflict as different concerns. Dependency decides execution order; conflict decides whether operations may coexist. Downstream work blocked by an upstream domain failure is blocked, not failed.

Use resource versions for optimistic concurrency and a repository XML stateRevision for projection freshness. Time stamps are informational; hashes/revisions establish consistency.

Do not require BaseX specifically. A BaseX-like XML database is one Projection Engine option. xquery-mcp remains suitable for narrow single-document XPath/XQuery/XSD work. Keep the projection behind an interface so it can be rebuilt or replaced without changing the agent-facing command contract.

## Modes

### `catchup`

Prioritize business scenario, entry points, processing boundaries, data flow, important branches, representative data, observed behavior/evidence, and blockers to confident understanding. Do not document class/method catalogs or obvious code.

### `change`

Prioritize purpose/done condition, impact scope, explicit exclusions, changed source references, invariants, non-obvious decisions, representative verification cases, evidence, and unresolved acceptance issues.

## State transitions

Use states conservatively:

- `draft`: shell exists; important sections may be missing.
- `investigating`: evidence/source tracing is in progress.
- `ready`: enough information exists to implement or explain safely.
- `verified`: required verification has evidence and no unresolved high-impact blocker remains.
- `closed`: work is complete and the map remains only as the durable index.

Never mark `verified` or `closed` while a high-impact `open/item` or failed/blocked verification case remains.

## Codex hook policy

When the bundled hooks are active:

- Let `UserPromptSubmit` add a compact context-sufficiency policy and ambiguity signals. It should not mechanically block every vague phrase.
- If that context indicates a material gap, ask one natural-Japanese clarification before affected edits. Otherwise proceed with the narrowest reasonable assumption.
- Let `SessionStart` load only a compact Feature Map slice; do not immediately reload the whole XML.
- Let `PostToolUse` track edits and xquery-mcp schema validation silently.
- Treat a `Stop` continuation as a completion gate, not as a request for broad documentation.
- When Stop reports missing XSD validation, call xquery-mcp `xml_validate_schema` on the current XML and XSD.
- When Stop reports a Jev-suggested durable delta, inspect the actual source/test change before editing XML. Jev suggests a branch; it does not establish a fact.
- Never satisfy a hook by inventing rules, decisions, evidence, or open issues.
- Do not loop indefinitely. The hook has a bounded continuation count and may eventually warn rather than block.

Hooks are a Codex/Work runtime feature. Do not assume ordinary Chat runs them.

## Decision provider boundary

Use a configured decision provider only for bounded judgments such as:

- whether a durable Feature Map update is likely;
- which one section is the best candidate for that delta;
- whether a high-impact ambiguity likely needs human review;
- optionally, whether a submitted request likely needs clarification and which missing-context category is dominant.

Keep exact facts, file discovery, XML parsing, Git state, schema validity, thresholds, and permissions in ordinary code. Keep free-form investigation, design, implementation, and final Japanese phrasing in the coding model. Never let a provider result directly write XML or become the sole basis for asking the user.

The decision layer is disabled by default. OpenAI Decisions API is the public-beta provider; Jev remains a legacy-compatible implementation. Respect repository/client data-handling rules before enabling any external provider. Refusals, API errors and malformed answers are undetermined advice, never evidence of approval or verification.

## Optional bounded task execution

Use `references/autonomous-task-runner.md` for tasks with fixed executable acceptance, approved paths and bounded retries. `scripts/task_runner.py` requires Linux OS isolation for evaluation and stores run state outside Feature Map XML. LOW tasks require post-implementation human review; MEDIUM tasks also require revision/config-bound prior Contract approval. HIGH/CRITICAL tasks remain human-led outside this MVP. A passing candidate is `HUMAN_REVIEW_REQUIRED`, never automatically approved, pushed, merged or deployed. No API/model call is made without explicit opt-in. Update durable Feature Map knowledge afterwards through this existing workflow, not in trial logs.

## Programmatic Tool Calling policy

Use Programmatic Tool Calling only for bounded, predictable read/query/filter/aggregate/validation stages that can return a smaller structured result. Prefer direct tool calls when each result changes the next semantic decision, and for writes, approvals, final native-artifact validation, Git publication, or external side effects. See `references/programmatic-tool-calling.md`.

## xquery-mcp policy

Prefer:

- `xpath_evaluate`: retrieve narrow node sets.
- `xml_validate_schema`: validate current Feature Map XML after edits.
- `xml_format`: normalize formatting only when needed.
- `xquery_evaluate`: compact projections or consistency checks that XPath alone cannot express cleanly.
- `xquery_validate`: validate a reusable/complex XQuery before execution.

For xquery-mcp 2.5.1 execution tools (`xpath_evaluate`, `xquery_evaluate`, `xquery_validate`), treat the returned text as an encoded `QueryResult` JSON envelope, not as the business value itself:

- `ok=true` with `value`: use only `value`.
- `ok=true` with `count=0` and no `value`: treat as a valid empty sequence, not an error.
- `ok=false`: inspect `errors[].code/message/line/column/sourceSnippet/specUrl`; use `xquery_suggest_fix` or `xquery_explain_error` when it reduces guesswork.
- Use `scripts/xquery_result.py` when deterministic normalization is needed.
- Keep `xml_validate_schema` on its existing plain-text contract; the Codex validation hook intentionally depends on that exact success path.

Do not use XQuery to generate prose. Use it to reduce context and target exact nodes.

## Output contract

For analysis/review tasks, answer with only what changed or what matters now:

```text
Feature: <name>
State: <state>
Changed:
- <section/node>: <delta>
Open:
- <blocking unknown, if any>
Verify:
- <next evidence/test>
```

If a clarification is required, return the clarification instead of this status format.

If no durable map update is needed, say `NO FEATURE MAP CHANGE` plus the implementation/test result if useful.
