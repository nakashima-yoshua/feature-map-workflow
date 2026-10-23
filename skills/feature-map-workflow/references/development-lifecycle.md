# Development Lifecycle

## Purpose

Use the Feature Map as a compact cross-phase index while keeping source, tests, CI evidence, release artifacts, and Git history as their own sources of truth.

This policy applies to both `catchup` and `change` mode. Do not add a third Feature Map mode merely to represent a lifecycle phase.

## Lifecycle

Use this default flow:

```text
Context Sufficiency
  -> Requirements
  -> Basic Design
  -> Business Scenario / E2E Design
  -> Test Boundary Design
  -> Detailed Design
  -> Condition / State / Boundary Tests
  -> Residual Unit Tests
  -> Implementation + CI
  -> Release Package / CD
  -> As-Built View
  -> Delivery / Acceptance
```

Feedback to an earlier phase is allowed whenever new evidence contradicts an assumption. Do not force work through a gate merely to preserve phase order.

For changes to legacy functionality, apply [Change-Driven Incremental Modernization](incremental-modernization.md) across existing phases. Investigate enough of the surrounding business flow to document it accurately, but change or migrate only an approved, cohesive slice. Modernization is a choice in design, not a new mandatory lifecycle phase.

Before a phase requests multiple manual inspections, UI actions or human business approvals, optionally apply [Human Work Direction](human-work-direction.md): preflight by code, select useful UML/DFD/ER views for the **focused feature**, and batch compatible human actions without merging the individual test oracles or statuses. It is a **conditional cross-phase gate**, not a thirteenth mandatory lifecycle stage.

For code-changing work, apply [Evidence-based Code Review](code-review.md) **within Phase 9 and its handoff to Phase 10**: independent, fresh-context diff review after deterministic verification; bounded correction and re-review; risk-tiered human approval tied to the current revision. This is not a separate mandatory phase or a replacement for GitHub host protections.

For an **explicit request to investigate maintenance or workflow inefficiency**, use [Evidence-based Maintenance Triage](maintenance-triage.md) to decide whether a small experiment is worthwhile. This is an optional, initially read-only activity within existing phases; code changes still require the usual tests, approvals and review.

For an **audit or evidence-traceability request**, use [Audit Evidence Traceability](audit-evidence-traceability.md) to assemble an on-demand index from existing requirement IDs, Feature Map references, exact code/review revision, actual test runs, human approvals and release digests. Keep source systems as the authorities for their own records; distinguish missing, not-run, stale and unverified evidence. Do not create a new mandatory phase, duplicate all artifacts, or treat an index as approval.

## Phase contract

For every phase, distinguish:

- **Input**: evidence required to start.
- **Activity**: work performed in the phase.
- **Durable Feature Map delta**: only knowledge worth retaining.
- **Hard gate**: deterministic condition checked by tools or ordinary code.
- **Semantic gate**: bounded judgment requiring interpretation.
- **HALT condition**: material uncertainty or failure that prevents safe continuation.
- **Output**: evidence or artifact passed to the next phase.

### 1. Context Sufficiency

**Input:** user request, current conversation, Feature Map, source, tests, configuration, logs.

**Activity:** resolve what can be established locally before asking a question.

**Durable Feature Map delta:** only unresolved durable knowledge under `open`.

**Hard gate:** target repository/feature can be identified and required files are readable.

**Semantic gate:** whether a remaining gap materially changes scope, authority, expected behavior, acceptance, data, environment, or an external dependency.

**HALT:** a material gap remains and affected work would be unsafe or materially different.

**Output:** executable interpretation or one clarification question.

### 2. Requirements

**Input:** request, business context, current behavior, constraints.

**Activity:** identify purpose, done condition, included/excluded scope, business rules, invariants, and material use cases. For an investigated legacy feature, record reusable business understanding even if no migration follows. Distinguish observed current behavior from business-confirmed desired behavior; unresolved intent is not silently promoted into a requirement.

**Durable Feature Map delta:** `goal`, `useCase`, `knowledge/rule`, `knowledge/invariant`, `knowledge/constraint`, unresolved `open` items.

**Hard gate:** required identifiers are unique and XML remains schema-valid after any change.

**Semantic gate:** requirement is testable enough to derive observable outcomes.

**HALT:** conflicting requirements, missing authority, or unknown acceptance condition changes implementation.

**Output:** bounded requirement set and acceptance basis.

### 3. Basic Design

**Input:** bounded requirements and current architecture.

**Activity:** identify entry points, responsibility boundaries, data/API direction, external systems, state transitions, and non-obvious design decisions. If modernization is considered, distinguish the wider understanding boundary from the smallest safe migration boundary. Compare leaving code unchanged, modifying legacy code, and migrating one functional slice; justify the chosen option with coexistence, verification and operating costs. For a legacy feature addition, optionally use the [A/B/C boundary comparison](incremental-modernization.md#optional-abc-decision-for-a-legacy-feature-addition) here; keep A (local change) first and introduce only justified Application/Domain or replacement boundaries. For data-backed legacy features, use [Three Complementary Views](three-view-understanding.md) when useful: connect business flow, data flow and evidence-backed ER to the same scenario and source/data references; do not invent FK/cardinality facts or create a whole-schema diagram.

**Durable Feature Map delta:** `sourceMap`, compact `diagrams`, `decision`, `constraint`, `invariant`.

**Hard gate:** referenced source/data objects exist where they are expected to exist.

**Semantic gate:** proposed boundary preserves required behavior and avoids unnecessary redesign.

**HALT:** architecture choice changes public behavior, data contract, authentication/authorization, persistence model, or external contract without approval.

**Output:** implementation-relevant boundary map.

### 4. Business Scenario / E2E Design

**Input:** requirements, use cases, basic design.

**Activity:** define representative end-to-end business scenarios before detailed implementation decisions.

**Durable Feature Map delta:** representative `verify/case` entries and scenario references only when they protect meaningful behavior.

**Hard gate:** each required scenario has an observable expected result.

**Semantic gate:** decide whether a scenario is business-significant enough for E2E rather than a lower test layer.

**HALT:** expected behavior cannot be observed or acceptance remains ambiguous.

**Output:** small E2E set focused on business flow.

### 5. Test Boundary Design

**Input:** scenario, dependencies, data effects, external interfaces.

**Activity:** define where the test enters, what runs for real, what is stubbed, what state is controlled, what is observed, and what the test does not guarantee. When launch-to-target prerequisites are unclear, use `target-reachability.md` to select one real route and discover its minimum fixture/setup closure before attempting execution.

**Durable Feature Map delta:** only non-obvious boundaries that are expensive to reconstruct. See `test-strategy.md`.

**Hard gate:** all required dependencies are either real, controlled, stubbed, or explicitly out of scope.

**Semantic gate:** choose the cheapest stable layer that can prove the behavior.

**HALT:** a required dependency cannot be controlled or observed.

**Output:** executable test boundary.

**Optional human-work direction input:** if several test boundaries require human action, inventory the shared environment, role, fixture/reset costs and evidence mechanisms now; group only after the separate test cases and oracles are established. See `human-work-direction.md`.

### 6. Detailed Design

**Input:** basic design, scenarios, test boundaries.

**Activity:** settle transaction boundaries, error handling, important algorithms, DB effects, external I/O, and implementation decisions that cannot be inferred cheaply from code.

**Durable Feature Map delta:** only non-obvious `decision`, `invariant`, `constraint`, or source navigation changes.

**Hard gate:** no contradiction with accepted requirements/invariants.

**Semantic gate:** detail is sufficient to implement without inventing new business behavior.

**HALT:** detailed design reveals an unresolved requirement or architecture issue.

**Output:** implementable design.

### 7. Condition / State / Boundary Tests

**Input:** rules, state transitions, input domains, effects.

**Activity:** cover equivalence classes, boundary values, state transitions, errors, permissions, retries, duplicates, and DB side effects below the E2E layer.

**Durable Feature Map delta:** representative verification cases only. Do not store generated combinatorial test catalogs in XML.

**Hard gate:** selected denominator items have a planned or existing test reference.

**Semantic gate:** remove redundant combinations that prove no distinct behavior.

**HALT:** a high-impact rule or state has no feasible verification path.

**Output:** integration/service/DB-focused test set.

### 8. Residual Unit Tests

**Input:** behavior not efficiently protected by E2E/integration tests.

**Activity:** isolate deterministic calculations, state decisions, date/rounding rules, and other logic whose combinations are cheaper to prove in-process.

**Durable Feature Map delta:** normally none unless the unit-level rule itself is durable domain knowledge.

**Hard gate:** the unit under test has deterministic inputs/outputs or controlled collaborators.

**Semantic gate:** whether the upper test layers already provide sufficient protection.

**HALT:** none by default; fall back to a higher test layer if isolation is artificial or costly.

**Output:** minimum useful unit tests.

### 9. Implementation + CI

**Input:** implementable design and test plan.

**Activity:** implement the smallest safe change and run build, static checks, and relevant tests. For a migrated slice, keep surrounding legacy contracts unchanged unless separately approved and verify old/new observable outputs and data effects with equivalent isolated inputs wherever feasible. Before requesting human review, conduct a **separate-context, read-only AI diff review** using `REVIEW.md` and `code-review.md` when available, checking the accepted change, important invariants and actual evidence. Triage concrete Important findings and cap AI review/fix passes at **three**; if review is unavailable, record NOT_RUN and hand the risk to a human rather than claiming AI approval.

**Durable Feature Map delta:** changed source/test references and newly confirmed durable knowledge only.

**Hard gate:** build and required deterministic checks pass.

**Semantic gate:** failures are correctly routed to implementation, test, environment, specification, or human review. Findings have actual path:line, triggering case, consequences and disposition; risk tier comes from changed behavior/paths, not author identity.

**HALT:** required CI fails; a discovered behavior contradicts accepted knowledge; an unresolved material/security finding exists; or three AI passes have not converged and the human has not decided how to proceed.

**Output:** tested commit candidate with revision-bound review summary and unresolved human decisions (no machine-generated approval).

**Before manual verification:** run automated preflight first, then issue a short focused brief plus an explicitly reviewed human session plan. Without approved oracle, isolatable test state or authorized environment, report HALT instead of inventing runnable steps.

### 10. Release Package / CD

**Input:** CI-verified candidate, risk-tiered review summary, and the human approval/authority required by repository policy for the exact candidate revision.

**Activity:** produce one immutable deployment artifact, migration/config contract, manifest, checksums, and release evidence as appropriate.

**Durable Feature Map delta:** normally references only; release artifacts remain canonical outside the XML.

**Hard gate:** package is reproducible and the exact artifact can be identified.

**Semantic gate:** deployment risk or human approval requirement; any `HIGH`/`CRITICAL` change affecting authorization, DB migrations, secrets, CI/release or irreversible effects receives appropriately authorized expert review and a realistic recovery plan.

**HALT:** artifact cannot be reproduced, migration is ambiguous, environment-specific changes are unreviewed, required human approval is missing/stale, or an Important/security finding remains unaddressed. CI and advisory AI review do **not** authorize merge or deployment.

**Output:** release package ready for the authorized deployment process.

### 11. As-Built View

**Input:** current source/tests, Feature Map, verification evidence, release evidence.

**Activity:** render role-specific views from existing truth rather than rewriting specifications from scratch. Check that the Feature Map already preserves newly understood business purpose, scenarios, rules, data/state effects and unresolved intent. If not, patch the durable knowledge now; document observed behavior separately from approved intent.

**Durable Feature Map delta:** none merely for documentation appearance.

**Hard gate:** rendered data comes from current valid XML and current references.

**Semantic gate:** explanation must distinguish confirmed, inferred, and unknown information.

**HALT:** generated prose conflicts with inspectable evidence.

**Output:** business, developer, tester, or delivery-oriented view.

### 12. Delivery / Acceptance

**Input:** release package, acceptance evidence, unresolved items.

**Activity:** verify done condition, required deliverables, and responsibility boundary. Confirm the investigated business flow is documented, the actual migrated/changed boundary is explicit, required evidence is available or honestly reported as not-run, and the Feature Map was updated or explicitly reviewed as already current.

**Durable Feature Map delta:** final verification evidence and unresolved acceptance blockers.

**Hard gate:** required verification is passed and required artifacts exist. A changed Feature Map must pass the existing XSD check; do not require an XML edit when no durable knowledge changed.

**Semantic gate:** no unresolved high-impact blocker remains.

**HALT:** failed/blocked verification, missing acceptance evidence, or unresolved high-impact `open` item.

**Output:** accepted delivery; Feature Map may move to `closed`.

**For human acceptance:** reuse the case-specific evidence and source revision from earlier runs. Batching manual work never turns an unexecuted or unapproved case into PASS.

## Responsibility split

Use the cheapest reliable mechanism for each kind of work:

- **Deterministic tools:** file discovery, parsing, compilation, tests, schema validation, Git state, hashes, exact thresholds.
- **Coding model / LLM:** investigation, explanation, design, generation, repair, synthesis across evidence.
- **Jev or another bounded classifier:** optional closed-choice classification or confidence scoring where policy permits.
- **Ordinary policy code:** thresholds, retries, allowed transitions, HALT rules, permissions.
- **Human:** business decisions, material scope/authority changes, irreversible external actions, final acceptance where required.

Never let a probabilistic classifier directly mutate the Feature Map, merge code, deploy, or establish an unverified fact.

## Cross-phase change consistency contract

For code-changing work, trace the **accepted change -> affected contracts/invariants -> observable checks -> actual evidence or explicit uncertainty** across existing phases. This is a conditional cross-phase check, **not** another lifecycle stage, artifact, mandatory checklist or permission to modify additional code.

- **Before design (Phases 1-3):** establish the authorized change boundary separately from the wider analysis boundary. Identify directly and indirectly affected callers, shared contracts, data and state effects only as far as evidence and risk justify. For dynamic dispatch, configuration, SQL/DB triggers and external integrations, treat undiscovered paths as `UNVERIFIED`, never as proven unaffected.
- **During test design (Phases 4-8):** pair each material affected invariant, interface or behavior with the cheapest observable verification and actual test boundary. A planned or passing local test does not establish unexercised cross-feature behavior. Record material gaps under existing `open` items or in the change/PR evidence, not a new schema.
- **After implementation (Phases 9-10):** use the existing independent revision-bound diff review to examine requirement fit, responsibility/dependency direction, API/DB/external/error contracts, state/transaction effects, regression reach and maintenance cost. Distinguish tested from inferred behavior and follow existing risk-tier/HALT/human-approval rules.
- **At completion:** update only confirmed durable Feature Map knowledge. Keep ephemeral review records, test logs and decisions in their existing owners (source/tests/CI/PR/Git). No change to XML/XSD, review authority or Task Runner limits.

For a trivial internal change, existing checks and focused diff review may discharge the contract without written repetition. For material contract changes, unresolved high-impact uncertainty or missing authorization, HALT only the affected advancement and request human judgment. See [Code Review](code-review.md) and [Feature Map Contract](feature-map-contract.md).
