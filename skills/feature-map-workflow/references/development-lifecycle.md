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

**Activity:** identify purpose, done condition, included/excluded scope, business rules, invariants, and material use cases.

**Durable Feature Map delta:** `goal`, `useCase`, `knowledge/rule`, `knowledge/invariant`, `knowledge/constraint`, unresolved `open` items.

**Hard gate:** required identifiers are unique and XML remains schema-valid after any change.

**Semantic gate:** requirement is testable enough to derive observable outcomes.

**HALT:** conflicting requirements, missing authority, or unknown acceptance condition changes implementation.

**Output:** bounded requirement set and acceptance basis.

### 3. Basic Design

**Input:** bounded requirements and current architecture.

**Activity:** identify entry points, responsibility boundaries, data/API direction, external systems, state transitions, and non-obvious design decisions.

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

**Activity:** implement the smallest safe change and run build, static checks, and relevant tests.

**Durable Feature Map delta:** changed source/test references and newly confirmed durable knowledge only.

**Hard gate:** build and required deterministic checks pass.

**Semantic gate:** failures are correctly routed to implementation, test, environment, specification, or human review.

**HALT:** required CI fails, or a discovered behavior contradicts accepted knowledge.

**Output:** tested commit candidate.

### 10. Release Package / CD

**Input:** CI-approved commit.

**Activity:** produce one immutable deployment artifact, migration/config contract, manifest, checksums, and release evidence as appropriate.

**Durable Feature Map delta:** normally references only; release artifacts remain canonical outside the XML.

**Hard gate:** package is reproducible and the exact artifact can be identified.

**Semantic gate:** deployment risk or human approval requirement.

**HALT:** artifact cannot be reproduced, migration is ambiguous, or environment-specific changes are unreviewed.

**Output:** release package ready for the authorized deployment process.

### 11. As-Built View

**Input:** current source/tests, Feature Map, verification evidence, release evidence.

**Activity:** render role-specific views from existing truth rather than rewriting specifications from scratch.

**Durable Feature Map delta:** none merely for documentation appearance.

**Hard gate:** rendered data comes from current valid XML and current references.

**Semantic gate:** explanation must distinguish confirmed, inferred, and unknown information.

**HALT:** generated prose conflicts with inspectable evidence.

**Output:** business, developer, tester, or delivery-oriented view.

### 12. Delivery / Acceptance

**Input:** release package, acceptance evidence, unresolved items.

**Activity:** verify done condition, required deliverables, and responsibility boundary.

**Durable Feature Map delta:** final verification evidence and unresolved acceptance blockers.

**Hard gate:** required verification is passed and required artifacts exist.

**Semantic gate:** no unresolved high-impact blocker remains.

**HALT:** failed/blocked verification, missing acceptance evidence, or unresolved high-impact `open` item.

**Output:** accepted delivery; Feature Map may move to `closed`.

## Responsibility split

Use the cheapest reliable mechanism for each kind of work:

- **Deterministic tools:** file discovery, parsing, compilation, tests, schema validation, Git state, hashes, exact thresholds.
- **Coding model / LLM:** investigation, explanation, design, generation, repair, synthesis across evidence.
- **Jev or another bounded classifier:** optional closed-choice classification or confidence scoring where policy permits.
- **Ordinary policy code:** thresholds, retries, allowed transitions, HALT rules, permissions.
- **Human:** business decisions, material scope/authority changes, irreversible external actions, final acceptance where required.

Never let a probabilistic classifier directly mutate the Feature Map, merge code, deploy, or establish an unverified fact.
