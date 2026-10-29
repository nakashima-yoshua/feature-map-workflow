# Development Lifecycle

## Purpose

Feature Map is the cross-phase knowledge index. Source/tests, accepted specifications,
native results, approvals, release artifacts and Git history retain their own authority.
Both catchup and change use this lifecycle; no new mode or enforced state machine is added.

## Target-first progressive refinement

The agreed post-task state is the organizing reference, including the deliverable,
repository, evidence, maintainability and entry point for the next authorized
change. Requirements define outcomes and acceptance, specifications refine
behavior and observations, designs refine ownership and physical paths where
needed, and implementation/verification establishes actual revisions and proof.
The current-state/target-state difference determines necessary work; previously
satisfied outputs need not be recreated. Revisit target assumptions as evidence
arrives rather than forcing premature paths or a fixed waterfall. Phase IDs and
existing authority boundaries remain unchanged. See
[Target State and Handoff](target-state-and-handoff.md).

## Lifecycle

This is a standard proposal to tailor by feature and risk, not project approval of
every stage. Existing phase IDs are lookup keys, not a waterfall requirement.

Use this feature-sized flow:

```text
Purpose / scope / risk / exclusions
  -> agreed specification and acceptance baseline, reviewed for testability
  -> representative scenarios + important boundary/error conditions
  -> input data + prerequisite data + specification-derived expected results
  -> small design / implementation / local-verification iterations
  -> selective trials on the actual product + consolidated work plan
  -> required formal verification + individual judgments and evidence
  -> QA evaluation + human risk disposition and release/delivery authorization
  -> release / handoff / preserved evidence + continuation-ready baseline
  -> operational feedback to requirements, procedures and regression tests
```

Before preparing a formal run, apply the condition-level
[change/risk selection](test-strategy.md#select-changed-behavior-before-selecting-cases).
Verify the changed program guarantees and their consequential impact paths, reuse
matching existing evidence, and keep environment construction outside functional
completion counts. A preparation-budget review may change the safe route or leave
a blocker; it never supplies missing proof or waives mandatory acceptance.

Feedback to an earlier phase is allowed whenever new evidence contradicts an assumption. Do not force work through a gate merely to preserve phase order.

A post-test change to responsibility, persisted state or the delivered operation
returns only the affected slice to design/implementation/verification. Record the
changed guarantee, reusable evidence and smallest missing check in the existing
task record; follow [Test Strategy](test-strategy.md#reassess-evidence-after-responsibility-or-artifact-changes).
It is not packaging-only merely because the business goal is unchanged. Before
freezing source/DB assets, apply [Customer Deliverables](customer-deliverables.md).
Workspace-specific database, designer, encoding and history procedures belong in
the workspace adapter, not a second workflow or the generic Feature Map schema.

| Work boundary | Existing phases | Entry and exit / minimum useful artifact |
| --- | --- | --- |
| Purpose and authorized slice | 1–2 | Request and context -> agreed goal, risk, scope and exclusions |
| Specification and acceptance | 2–3 | Authorized slice -> identifiable agreed specification/oracle version; QA reviews observability before agreement |
| Design and test preparation | 3–8 | Accepted baseline -> selected scenarios, input/fixture data, independent expectations and a feasible test boundary for the next slice |
| Implementation and local verification | 6–9 | Prepared slice -> small tested candidate; revise design/data/implementation from actual evidence |
| Trial and work-plan preparation | 5 and the manual-verification handoff in 9 | Actual operations or reusable procedures -> only necessary trials, per-operation checkpoints, dependency/reset/restart plan and its validity review |
| Formal verification | 9 and the verification input to 12 | Valid plan, authorized environment and candidate -> per-case/condition results, exact revision and original evidence; seal after runs rather than waiting until delivery |
| QA evaluation and authorization | 9–10 and 12 | Results and gaps -> QA conclusion, unresolved defects/risks, human disposition and applicable release/delivery authorization |
| Release and handoff | 10–12, including conditional 11a | Authorized candidate -> artifact digest, as-built references, customer-safe materials, handoff/acceptance, archived evidence and next-task re-entry references |
| Operation and learning | 1–2/7/9 on a subsequent authorized change | Incident/observation -> corrected specification, minimal regression and applicable procedure knowledge |

Prepare enough specification-derived data and independent expected results for the
next feature-sized iteration. Include important invalid states; never derive the
oracle from the implementation's answer. Select security/privacy, transaction,
nonfunctional, regression and change-impact checks according to actual risk.

### Early feedback before expanding work

Use the existing purpose, scope and acceptance baseline to establish the deliverable's
user, intended decision or action, and necessary detail. Reuse available answers;
apply the [Context Gate](context-gate.md) only for material unresolved gaps.

Choose the next small unit by its observable outcome and what evidence is needed
to continue. Check assumptions whose correction would cause substantial rework
before expanding dependent work. Use the cheapest sufficient outline, representative
scenario or minimal implementation; do not require fixed 15-minute units or a
30-percent completion checkpoint.

| Work | Early check | Basis for continuing |
| --- | --- | --- |
| Decision material | Outline and one representative comparison | The content and detail answer the intended decision; resolve material ambiguity with the decision owner before polishing the full document. |
| Screen change | One representative input/display flow with specification-derived expectations | Observe whether the selected behavior matches the accepted specification before repeating the pattern across the screen. A mock establishes only what it actually shows. |
| Investigation | One actual entry point and its relevant source/data path | Confirm that the path addresses the target scenario before broadening the investigation; retain unverified dependencies as unknowns. |

Existing specifications, source and tests can resolve checks within authorized work;
seek human judgment only where business meaning, scope, authority or material risk
remains unresolved. A clear low-risk change needs no separate checkpoint or new
approval round. Keep transient plans and feedback in the existing task record;
only durable feature knowledge belongs in XML. Early feedback does not replace
required verification, revision-bound review or human acceptance. Stop when the
accepted done condition and required checks are satisfied.

### Tailoring and stop conditions

Reuse current designs, fixtures and procedures. Skip trials for known unchanged
operations and omit irrelevant diagrams/plans/customer materials; record material
omissions and reasons in the existing change record. A trial is preparation, not
PASS. Formal reuse requires the same identity, oracle, reproducibility, original
evidence and an actual adoption decision; do not automatically run every test twice.
The [procedure contract](human-work-plan-v2.md) owns these details.

HALT affected advancement for a materially unagreed oracle, unknown authority,
unsafe/non-resettable state, missing required evidence, failed required checks or
unaccepted material risk. Project scales, thresholds and tailoring are human decisions.

The [condition/cost strategy](test-strategy.md#condition-selection-and-verification-cost) owns condition selection, additions and exit/budget decisions; apply it during test preparation and QA handoff.

### Select the next route

Read only the current question's route, not all links recursively:

- Legacy change choices: [Incremental Modernization](incremental-modernization.md).
- Test placement/coverage: [Test Strategy](test-strategy.md), then its selected route.
- Actual-operation trials and consolidated plans: [Human Work Direction](human-work-direction.md).
- Stable AI screen trials to deterministic Playwright/FlaUI execution:
  [AI-assisted Testing](ai-assisted-testing.md#from-screen-trials-to-deterministic-regression).
- Phase 9 review / Phase 10 handoff: [Code Review](code-review.md).
- Explicit maintenance investigation: [Maintenance Triage](maintenance-triage.md).
- Audit request: [Audit Evidence Traceability](audit-evidence-traceability.md).
- Optional, non-authoritative phase advice: [Decision Providers](decision-providers.md#work-phase-and-observation-policy).

Upstream owns accepted requirement/acceptance IDs and versions, development their
realization, QA conformance and proof. QA reviews testability before agreement.
These are responsibilities, not required headcount; record self-review limits.
Humans agree business meaning, accept residual risk and authorize delivery/release.
Version, impact, approval and preservation are shared procedures, not extra packages.
AI proposals and tools do not provide that authority. FMW HTML is a human view;
AI/tools retrieve canonical XML/structured plans/native results instead.

## Phase contract

The [phase contracts](lifecycle-phase-contracts.md#phase-contract) own detailed inputs, activities, durable deltas, gates, HALT and outputs. Read only the phase needed now. Existing phase IDs and links remain stable.

### 1. Context Sufficiency

See [this phase contract](lifecycle-phase-contracts.md#1-context-sufficiency).

### 2. Requirements

See [this phase contract](lifecycle-phase-contracts.md#2-requirements).

### 3. Basic Design

See [this phase contract](lifecycle-phase-contracts.md#3-basic-design).

### 4. Business Scenario / E2E Design

See [this phase contract](lifecycle-phase-contracts.md#4-business-scenario--e2e-design).

### 5. Test Boundary Design

See [this phase contract](lifecycle-phase-contracts.md#5-test-boundary-design).

### 6. Detailed Design

See [this phase contract](lifecycle-phase-contracts.md#6-detailed-design).

### 7. Condition / State / Boundary Tests

See [this phase contract](lifecycle-phase-contracts.md#7-condition--state--boundary-tests).

### 8. Residual Unit Tests

See [this phase contract](lifecycle-phase-contracts.md#8-residual-unit-tests).

### 9. Implementation + CI

See [this phase contract](lifecycle-phase-contracts.md#9-implementation--ci).

### 10. Release Package / CD

See [this phase contract](lifecycle-phase-contracts.md#10-release-package--cd).

### 11. As-Built View

See [this phase contract](lifecycle-phase-contracts.md#11-as-built-view).

### 11a. Customer Submission Materials Organization (when requested)

See [this phase contract](lifecycle-phase-contracts.md#11a-customer-submission-materials-organization-when-requested).

### 12. Delivery / Acceptance

See [this phase contract](lifecycle-phase-contracts.md#12-delivery--acceptance).

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
