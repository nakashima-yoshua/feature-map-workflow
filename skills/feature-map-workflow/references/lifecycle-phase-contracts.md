# Lifecycle Phase Contracts

Read only the selected phase below; the [lifecycle overview](development-lifecycle.md) owns ordering, tailoring and shared authority.

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

**Activity:** identify purpose, done condition, included/excluded scope, business rules, invariants, and material use cases. Define the desired *post-task outcome* and observable acceptance, including relevant maintenance and continuation needs; do not require file paths or a fixed repository layout yet. For an investigated legacy feature, record reusable business understanding even if no migration follows. Distinguish observed current behavior from business-confirmed desired behavior; unresolved intent is not silently promoted into a requirement.

**Durable Feature Map delta:** `goal`, `useCase`, `knowledge/rule`, `knowledge/invariant`, `knowledge/constraint`, unresolved `open` items.

**Hard gate:** required identifiers are unique and XML remains schema-valid after any change.

**Semantic gate:** requirement is testable enough to derive observable outcomes.

**HALT:** conflicting requirements, missing authority, or unknown acceptance condition changes implementation.

**Output:** bounded requirement set and acceptance basis.

### 3. Basic Design

**Input:** bounded requirements and current architecture.

**Activity:** refine the same target into logical deliverable owners, likely existing repository modules/locations, entry points, responsibility boundaries, data/API direction, external systems, state transitions, and non-obvious design decisions. Avoid inventing directories before inspecting conventions. If modernization is considered, distinguish the wider understanding boundary from the smallest safe migration boundary. Compare leaving code unchanged, modifying legacy code, and migrating one functional slice; justify the chosen option with coexistence, verification and operating costs. For a legacy feature addition, optionally use the [A/B/C boundary comparison](incremental-modernization.md#optional-abc-decision-for-a-legacy-feature-addition) here; keep A (local change) first and introduce only justified Application/Domain or replacement boundaries. For data-backed legacy features, use [Three Complementary Views](three-view-understanding.md) when useful: connect business flow, data flow and evidence-backed ER to the same scenario and source/data references; do not invent FK/cardinality facts or create a whole-schema diagram.

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

When audit traceability is required, establish external case/condition IDs,
private preservation root, exact baseline and per-condition evidence expectations
here. Follow [Evidence Storage](evidence-storage.md); keep customer output free
of internal environment and management details.

**Optional human-work direction input:** if several test boundaries require human action, inventory the shared environment, role, fixture/reset costs and evidence mechanisms now; group only after the separate test cases and oracles are established. See `human-work-direction.md`.

For requested customer test plans, select the audience, customer-safe fields and
external IDs now using [Customer Deliverables](customer-deliverables.md). A design
submission can be prepared before execution; keep all unperformed conditions
explicitly not-run.

### 6. Detailed Design

**Input:** basic design, scenarios, test boundaries.

**Activity:** refine logical outputs into concrete source/test/configuration paths where justified by the existing repository, and settle transaction boundaries, error handling, important algorithms, DB effects, external I/O, and implementation decisions that cannot be inferred cheaply from code. Preserve the accepted outcome while leaving reversible details open if their early choice adds no value.

**Durable Feature Map delta:** only non-obvious `decision`, `invariant`, `constraint`, or source navigation changes.

**Hard gate:** no contradiction with accepted requirements/invariants.

**Semantic gate:** detail is sufficient to implement without inventing new business behavior.

**HALT:** detailed design reveals an unresolved requirement or architecture issue.

**Output:** implementable design.

### 7. Condition / State / Boundary Tests

**Input:** rules, state transitions, input domains, effects.

**Activity:** prepare and verify the important equivalence classes, boundary values, state transitions, errors, permissions, retries, duplicates, and DB side effects below the E2E layer, incrementally with implementation. Prepare the next slice's input, prerequisite data and specification-derived expected result; do not require the whole catalog before coding.

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

**Activity:** compare the refined target to actual paths and current evidence, reuse already satisfied parts, implement the smallest safe change and run build, static checks, and relevant tests. For a migrated slice, keep surrounding legacy contracts unchanged unless separately approved and verify old/new observable outputs and data effects with equivalent isolated inputs wherever feasible. Before requesting human review, conduct a **separate-context, read-only AI diff review** using `REVIEW.md` and `code-review.md` when available, checking the accepted change, important invariants and actual evidence. Triage concrete Important findings and cap AI review/fix passes at **three**; if review is unavailable, record NOT_RUN and hand the risk to a human rather than claiming AI approval.

**Durable Feature Map delta:** changed source/test references and newly confirmed durable knowledge only.

**Hard gate:** build and required deterministic checks pass.

**Semantic gate:** failures are correctly routed to implementation, test, environment, specification, or human review. Findings have actual path:line, triggering case, consequences and disposition; risk tier comes from changed behavior/paths, not author identity.

**HALT:** required CI fails; a discovered behavior contradicts accepted knowledge; an unresolved material/security finding exists; or three AI passes have not converged and the human has not decided how to proceed.

**Output:** tested commit candidate with revision-bound review summary and unresolved human decisions (no machine-generated approval).

**Before manual verification:** run automated preflight first, then issue a short focused brief plus an explicitly reviewed human session plan. Without approved oracle, isolatable test state or authorized environment, report HALT instead of inventing runnable steps.

For unclear operations, use the conditional procedure trials and optional v2 work
plan in [Human Work Direction](human-work-direction.md#procedure-based-plan-version-2).
Validate the consolidated sequence before required formal checks; retain individual
case/condition results, blocked versus not-run versus failed, and the original
evidence. A plan or trial does not by itself establish QA acceptance.

### 10. Release Package / CD

**Input:** CI-verified candidate, risk-tiered review summary, and the human approval/authority required by repository policy for the exact candidate revision.

**Activity:** produce one immutable deployment artifact, migration/config contract, manifest, checksums, and release evidence as appropriate. Identify exact source commit, actual release artifact and rollback/operating references; do not equate a prepared package with deployment.

**Durable Feature Map delta:** normally references only; release artifacts remain canonical outside the XML.

**Hard gate:** package is reproducible and the exact artifact can be identified.

**Semantic gate:** deployment risk or human approval requirement; any `HIGH`/`CRITICAL` change affecting authorization, DB migrations, secrets, CI/release or irreversible effects receives appropriately authorized expert review and a realistic recovery plan.

**HALT:** artifact cannot be reproduced, migration is ambiguous, environment-specific changes are unreviewed, required human approval is missing/stale, or an Important/security finding remains unaddressed. CI and advisory AI review do **not** authorize merge or deployment.

**Output:** release package ready for the authorized deployment process.

### 11. As-Built View

**Input:** current source/tests, Feature Map, verification evidence, release evidence.

**Activity:** render role-specific views from existing truth rather than rewriting specifications from scratch. Check that a future maintainer can navigate from the entry point through the agreed behavior, code/tests and revision-bound evidence without the previous conversation. Check that the Feature Map already preserves newly understood business purpose, scenarios, rules, data/state effects and unresolved intent. If not, patch the durable knowledge now; document observed behavior separately from approved intent.

**Durable Feature Map delta:** none merely for documentation appearance.

**Hard gate:** rendered data comes from current valid XML and current references.

**Semantic gate:** explanation must distinguish confirmed, inferred, and unknown information.

**HALT:** generated prose conflicts with inspectable evidence.

**Output:** business, developer, tester, or delivery-oriented view.

For customer-facing document creation and checks, use [Customer Deliverables](customer-deliverables.md).

### 11a. Customer Submission Materials Organization (when requested)

**Input:** customer candidates, required/optional scope, exact hashes and evidence.
Design/interim submissions may use the current view before product acceptance.

**Activity:** follow [Customer Deliverables §5](customer-deliverables.md#5-エビデンスが揃った提出資材を整理する):
select evidence-backed files, create a new customer-only package and contents
list, reconcile every file/archive entry with a private hash manifest.

**Durable Feature Map delta:** normally none; keep records in the private index.

**Hard gate:** required checks and claim-specific evidence match each included
file, revision and scope. Plan/document evidence cannot prove functional PASS.

**Semantic gate:** preserve failures and not-run states; do not hide scope gaps.

**HALT:** unsupported/stale files, internal information, hash/list mismatches or
missing required materials. Keep the eligible subset as preparation, not ready.

**Output:** verified customer package/list and private selection, exclusion and
evidence mappings. Organization grants no sending authority or acceptance.

### 12. Delivery / Acceptance

**Input:** release package, acceptance evidence, unresolved items.

**Activity:** verify done condition, required deliverables, and responsibility boundary. Also verify the proportionate continuation-ready handoff: actual source baseline and branch/PR/CI disposition, reproducible setup/test entry points where required, persistent knowledge, original evidence references, remaining issues with owner/next action, and relevant recovery/backup limitations. A clean Git tree alone is insufficient. Keep delivery readiness, actual acceptance, and continuation readiness distinct; inspect/report only, never silently merge, delete branches, deploy or transmit. Confirm the investigated business flow is documented, the actual migrated/changed boundary is explicit, required evidence is available or honestly reported as not-run, and the Feature Map was updated or explicitly reviewed as already current.

**Durable Feature Map delta:** final verification evidence and unresolved acceptance blockers.

**Hard gate:** required verification is passed and required artifacts exist. A changed Feature Map must pass the existing XSD check; do not require an XML edit when no durable knowledge changed.

**Semantic gate:** no unresolved high-impact blocker remains.

**HALT:** failed/blocked verification, missing acceptance evidence, or unresolved high-impact `open` item.

**Output:** accepted delivery (when actually authorized) and an inspectable next-task starting point, or explicit continuation blockers; Feature Map may move to `closed` only under its existing criteria. See [Target State and Handoff](target-state-and-handoff.md).

For customer submission, use the exact package fixed in Phase 11a; any file
change requires renewed affected checks and package reconciliation.
Customer submission is a separate recorded action under [Customer Deliverables](customer-deliverables.md).
Check the exact frozen files, authorized recipients and transmission scope; record
actual sending separately from document creation and product acceptance. Design
review or an interim report need not wait for final product acceptance, but must
show failed, blocked and unperformed work honestly.

**For human acceptance:** reuse the case-specific evidence and source revision from earlier runs. Batching manual work never turns an unexecuted or unapproved case into PASS.

For an auditable handoff, validate the registered manifest/file hashes and open
representative originals from the [private evidence index](evidence-storage.md).
Report missing current results, historical applicability and backup/restore state
separately; a generated index is not acceptance.
