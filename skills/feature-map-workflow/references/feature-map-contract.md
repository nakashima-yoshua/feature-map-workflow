# Feature Map Contract

## Purpose

Feature Map XML is a compact navigation and decision artifact shared by a developer and AI during catch-up and development. It is not a second copy of source code.

## Information test

Before writing any item, classify it:

- Directly visible in code -> omit.
- Discoverable immediately by symbol/file search -> store only a reference.
- Requires tracing multiple files/data sources -> store a short rule or flow fact.
- Requires business/domain knowledge -> store it.
- Explains a non-obvious design choice -> store it with the reason.
- Defines an external constraint or acceptance condition -> store it.
- Not confirmed -> store it under `open`; do not infer it as fact.
- Transient prompt ambiguity -> do not store unless it is durable feature knowledge.

## Root attributes

- `version`: schema contract. Current template: `1.3`. The bundled XSD also accepts `1.1` and `1.2` for compatibility.
- `mode`: `catchup` or `change`.
- `state`: `draft`, `investigating`, `ready`, `verified`, `closed`.

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

The XSLT renders Mermaid automatically. It prefers a local `feature-map.mermaid.min.js` and otherwise loads pinned Mermaid `12.0.0` from jsDelivr.

### `knowledge`

- `rule`: business behavior.
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

Patch only the smallest durable knowledge delta. Internal refactoring that preserves externally meaningful behavior usually requires only source reference updates, or no Feature Map change at all.
