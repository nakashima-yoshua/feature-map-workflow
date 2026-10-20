# Feature Map Contract

## Purpose

Feature Map XML is a compact navigation and decision artifact shared by a developer and AI during catch-up and development. It is not a second copy of source code.

## Per-feature boundaries and HTML presentation

- Keep **one Feature Map XML per cohesive business feature**, not one growing document per application. Split when independent business scenarios have different triggers, data effects, ownership, or acceptance conditions. Do not split merely because a file reaches a speculative size threshold.
- Store the meaningful business rules for that feature completely. Refer to other Feature Maps or source objects rather than duplicating their knowledge; cross-feature understanding does **not** authorize unrelated code migration.
- The existing `feature-map.xsl` displays purpose and primary scenarios/rules first. Additional scenarios/rules and technical source references, verification evidence, and diagrams are available in native HTML `details`; opening Diagrams triggers Mermaid loading. Collapsing content reduces visual load and startup work, **not the bytes in an individual XML/HTML document**.
- For many features, generate a **metadata-only directory** with `scripts/build_feature_index.py`. It contains titles, systems, states, short purposes, and relative links to XML files; it does not concatenate full Feature Maps, diagrams or evidence. Refresh it when files change; it is a regenerable display artifact, not a new source of truth.
- Existing XML/XSD v1.3, links to tests, and the XSLT file association remain unchanged. No new runtime server, database, JavaScript framework or mandatory external service.

## Information test

Before writing any item, classify it:

- Directly visible in code -> omit.
- Discoverable immediately by symbol/file search -> store only a reference.
- Requires tracing multiple files/data sources -> store a short rule or flow fact.
- Requires business/domain knowledge -> store it, including newly understood business scenarios, material decisions, state/data effects, and exceptions for the investigated feature.
- Explains a non-obvious design choice -> store it with the reason.
- Defines an external constraint or acceptance condition -> store it.
- Not confirmed -> store it under `open`; do not infer it as fact.
- Transient prompt ambiguity -> do not store unless it is durable feature knowledge.

## Root attributes

- `version`: schema contract. Current template: `1.3`. The bundled XSD also accepts `1.1` and `1.2` for compatibility.
- `mode`: `catchup` or `change`.
- `state`: `draft`, `investigating`, `ready`, `verified`, `closed`.

Use `catchup` to understand existing business scenarios, entry points, data flow and blockers; use `change` for the accepted change, its impact, invariants and verification. Neither mode authorizes changing neighboring features.

| State | Meaning |
| --- | --- |
| `draft` | A shell exists; important knowledge may still be missing. |
| `investigating` | Source/evidence tracing is in progress. |
| `ready` | Enough information exists to implement or explain safely. |
| `verified` | Required verification has evidence and no unresolved high-impact blocker remains. |
| `closed` | The agreed work is complete and the map remains as its durable index. |

Do not mark a map `verified` or `closed` while a high-impact `open/item` or a failed/blocked verification case remains. These states describe evidence and work; they grant no business acceptance, merge or release authority.

From the repository root, generate an optional index for a directory of maps:

```sh
python skills/feature-map-workflow/scripts/build_feature_index.py --root path/to/maps
# Refresh explicitly after map changes:
python skills/feature-map-workflow/scripts/build_feature_index.py --root path/to/maps --force
```

The output is `path/to/maps/feature-map-index.html`. Keep each map's XSD/XSLT support files at its declared paths. The index is a derived local view and may contain confidential feature names or purpose excerpts.

## Sections

### `meta`

Identity only: system, feature, optional environment.

### `goal`

- `purpose`: why the feature exists / what change is intended.
- `done`: minimum acceptance/completion condition.
- `scope`: concise included boundary when needed.
- `exclude`: explicitly unchanged boundary when stating it prevents scope ambiguity.

Do not duplicate the same boundary in both `scope` and `exclude`.

### `useCase`

Repeat only when scenarios materially differ in control flow, data effects, or acceptance. Do not enumerate cosmetic UI variants.

### `sourceMap/ref`

Navigation index. Prefer a stable symbol or data object name. `target` should be concise and grep/IDE-friendly. Use `access` for data/API direction when useful.

### `diagrams/diagram`

Optional Mermaid source for visual knowledge that is expensive to reconstruct mentally from several references. Use CDATA and keep the diagram small. Supported intent labels are `class`, `sequence`, `usecase`, `state`, `activity`, `er`, `flowchart`, `architecture`, and `other`.

Use diagrams for cross-boundary interactions, meaningful state transitions, or compact structural relationships. Do not generate a complete class diagram, call graph, or branch map from code. Source remains canonical. A diagram that becomes stale or duplicates obvious code should be removed rather than expanded.

For data-backed legacy features, follow [Three Complementary Views](three-view-understanding.md): `flowchart TD` for business decisions and exceptions; `flowchart LR` for payload movement, reads/writes and transaction boundaries; `erDiagram` for verified table keys/relationships. Each useful view has a stable diagram ID and a title naming the same `useCase` (for example, `UC-SUBMIT`), and uses consistent DB object names with `sourceMap`. Not every feature needs all three diagrams. A JOIN does not establish a physical FK; when key, cardinality or relationship status is uncertain, omit that ER edge and retain the open question rather than inventing it.

The XSLT renders Mermaid automatically. It prefers a local `feature-map.mermaid.min.js` and otherwise loads pinned Mermaid `12.0.0` from jsDelivr.

For human verification, the [focused brief and human-work direction](human-work-direction.md) may select **any number of relevant views**, including UML activity, use-case, state, sequence or class diagrams in addition to DFD, ER and architecture. No three-view quota or numeric diagram cap exists. Selection never grants authority to invent a missing fact or approve a DB relation. Render the brief from existing XML; keep human session plans and test results external and regenerable.

### `knowledge`

- `rule`: business behavior. Say whether an important rule describes observed legacy behavior or an approved business expectation; do not infer approval from source code alone.
- `invariant`: behavior/data property that must not be broken by changes.
- `decision`: non-obvious implementation/design decision plus `reason`.
- `constraint`: external, operational, contractual, compatibility, or environment limit.

### `verify/case`

Keep only representative cases that prove behavior or protect important branches. `observe` records actual behavior; `evidence` points to tests, logs, DB evidence, commits, or other inspectable sources.

### `open/item`

Only unresolved matters that affect understanding, implementation, or acceptance. `next` must state the cheapest useful next action.

Optional `type` values classify the missing durable context:

- `scope`
- `authority`
- `business-rule`
- `expected-behavior`
- `acceptance`
- `external-dependency`
- `data`
- `environment`
- `other`

Do not add an Open item only because a user prompt contains a vague word. First check whether source, tests, configuration, or existing Feature Map content resolves it.

## Business knowledge and migration boundaries

- Document the understood end-to-end business scenario and material dependencies; this can include more code than will be modified. Use `goal`, `useCase`, `knowledge`, `sourceMap`, `verify` and `open` rather than adding a second specification.
- For proposed migration, `goal/scope` and `goal/exclude` describe the **authorized change** only. Referenced neighboring components may be understood but are not thereby approved for replacement.
- Record a non-obvious selection between no change, a legacy fix, or a migrated slice under `knowledge/decision` with its reason. Do not add a decision merely to restate an obvious one-line fix.
- Preserve material contradictions between current observed behavior and business-confirmed intent under `open` until resolved. The existing `open/item` and `verify/case` status express uncertainty and actual evidence; no new confidence or migration status attribute is required.
- The human-facing documentation is the XSLT view of the existing Feature Map. Put test fixtures, traces and full old/new comparisons beside tests and link representative evidence only.

## Stable IDs

`id` is optional but recommended when a node will be referenced or updated repeatedly. Keep IDs short (`UC1`, `R1`, `I1`, `D1`, `V1`, `O1`) and never renumber merely for appearance.

## Prohibited duplication

Do not add:

- change history (Git owns it);
- class/method catalogs;
- full SQL descriptions;
- prose versions of code branches;
- generated diagrams that merely mirror classes or branches already obvious from source;
- generic technical explanations;
- meeting-style narrative;
- transient hook state or Jev probabilities;
- duplicated requirements/design/test documents.

## Update rule

Patch only the smallest durable knowledge delta. When a feature is investigated, newly confirmed domain knowledge must be preserved even if code is left unchanged or only a small slice is migrated. At change completion, review the Feature Map; update new durable findings or explicitly report that the existing map remains accurate. Internal refactoring that preserves externally meaningful behavior usually requires only source reference updates, or no Feature Map change at all.

## Change impact and verification linkage

For a material change, use the **existing** `goal/scope` and `goal/exclude` to delimit edits; `sourceMap` may reference wider affected callers without authorizing their modification. Use `knowledge/invariant`, `knowledge/constraint`, `knowledge/decision` (with reasons), representative `verify/case` and material `open/item` to preserve only knowledge expensive to rediscover.

When relevant, the reviewer should be able to follow: **changed feature or source reference -> affected invariant/contract/behavior -> concrete test or observation -> actual evidence**. Refer to tests and CI rather than embedding logs or duplicating test plans. If a dynamic invocation, configuration, DB side effect or cross-feature path has not been verified, mark the consequential gap `open` and specify the least expensive next check; absence of static references is not proof of non-impact.

Do not create items solely to satisfy this linkage for obvious low-risk edits. The map remains a durable feature index, not a second PR checklist or a claim that all impact paths are known. Completion and human authority still follow [Development Lifecycle](development-lifecycle.md) and [Code Review](code-review.md).
