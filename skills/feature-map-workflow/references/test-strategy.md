# Test Strategy

## Purpose

Place each behavior at the cheapest stable test layer that can prove it, while keeping end-to-end coverage focused on business flows.

The default order is:

```text
Business scenario
  -> E2E
  -> condition/state/boundary coverage at integration/service/DB level
  -> residual unit tests only where lower-level isolation adds value
```

Do not maximize test count. Minimize duplicated guarantees and untested behavior.

This is test-design order; it does not require E2E-first execution or all detailed
tests/data before implementation. The [lifecycle](development-lifecycle.md#lifecycle)
owns feature-sized iteration, independent data/oracles and risk-based tailoring.
For unknown operations use [Human Work Direction](human-work-direction.md);
its v2 contract owns trials, consolidation and total-cost measurements. Reuse known
procedures; keep individual judgment, safety, evidence and human approval.

## Select changed behavior before selecting cases

Start from the agreed change and its actual base/candidate identities. A later
test-launcher change is not the baseline for the whole business feature. Map each
changed rule, state, UI binding or data effect to the smallest affected caller and
downstream boundary. Inspect unchanged dependencies only far enough to establish
that boundary; do not turn their entire behavior into new acceptance work.

Classify **each input condition**, not only the case heading:

| Priority | Protection | Selection |
| --- | --- | --- |
| P1 | Data loss/corruption, unauthorized operation, unintended writes or serious business misjudgment | Keep distinct normal, rejection and consequential boundary/state paths in the changed/affected flow. |
| P2 | Primary changed journey or rule; a failure materially prevents ordinary work | Keep one representative success and each materially different failure/transition. |
| P3 | Cosmetic/rare variation or unchanged low-impact behavior | Omit from the current required run, or retain an existing cheap regression by reference. Add only for a distinct demonstrated risk. |

Cost chooses the observation method and execution order; it does not downgrade
P1/P2 risk. An unavailable required path stays blocked until a justified scope
decision or adequate evidence resolves it.

For each retained condition record the requirement/change reference, concrete
defect it detects, input class, expected effect, cheapest sufficient layer and
evidence needed. Use existing case tables/test parameters rather than a new
registry. Keep a normal representative and only boundaries that change program
behavior; do not multiply all text types, adjacent valid values, screens and roles
into a Cartesian product. A shared dependency does not by itself make two input
conditions equivalent.

Distinguish these scopes:

- **Changed program guarantees:** new/modified rules, validation, state handling,
  authorization binding, transaction and error behavior.
- **Affected regression:** the nearest real caller or consumer that could break
  because of that change. Use a few representative integration/UI journeys.
- **Environment prerequisites:** connectivity, schema installation, capacity,
  login setup and operating-system configuration. Preflight once for the planned
  session; they are not customer functional cases unless the change delivers them.
- **Unchanged functionality:** full login, reporting, file-dialog and external
  system suites are outside this run absent a concrete impact path or obligation.

A pure serializer/formatter needs deterministic tests, not a complete business
environment. A stored-program safety/transaction guarantee still needs the real
DB boundary; source review, parse-only checks and mocks cannot replace it. A
changed UI binding still needs a real UI observation. An unchanged history screen
is not a prerequisite for proving a changed caller's persisted business effect
unless the accepted requirement explicitly includes that screen.

### Inventory and reduce an existing plan

Keep the original plan/results immutable. For every old condition choose retain,
equivalent representative, lower-layer supplement, unchanged/out of scope, or
oracle/method correction. Record the reason, replacement/reference, old result
and the authority for material scope/oracle changes. Apply an already explicit
user decision; do not ask for the same decision again. Contractual or other
mandatory acceptance cannot be removed by the agent merely because it is costly.

Do not delete a known failure to improve the denominator. Preserve it and its
disposition even when its condition leaves the required run; unresolved material
failures and unverified changed guarantees still block the relevant conclusion.
Do not mark excluded conditions PASS or NOT APPLICABLE merely because they were
excluded. Report old-plan results separately from the revised-plan denominator.

If an old expectation contains an unrelated screen or an unreachable UI input,
review its source before spending on reachability. A corrected expectation gets
an explicit amendment/new condition identity. Reuse only the observed subset of
existing evidence that proves the new expectation; retain the old blocked/failed
result. A changed method is never retroactively described as the old UI test.

### Keep preparation proportional

Before building fixtures, compare reusing a working authorized environment,
existing tests/procedures and a smaller real entry boundary with constructing a
new environment. Close only the prerequisites needed for the selected behavior.
Do not build a general recovery engine, broad DB clone or automation framework
solely to get past one blocked case without an explicit cost/benefit decision.
Keep required isolation, authorization and recovery; choose a cheaper safe route
or leave the case blocked when those costs dominate.

Set a project-appropriate preparation/diagnosis budget and review point before
another setup or automation attempt. At that point report functional conditions
closed, remaining blockers, new evidence and the cheapest safe alternative.
Preparation checks, helper tests and metadata captures do not count as product
conditions completed. Record measured active/wait/setup time when available;
file counts and elapsed wall time are not measurements of engineering effort.

Freeze shared candidate/environment evidence once per unchanged session. Capture
per-condition input, initial state, expectation, decisive observation and only
the affected side effects/reset needed for independence. Broader snapshots are
justified by uncertainty or blast radius, not by a default demand to export every
table for every click. Reuse valid evidence and rerun only conditions affected by
a changed program, assertion, fixture or dependency. Stop after the selected
guarantees and required defect dispositions have adequate proof.

## Condition selection and verification cost

Minimize total preparation, execution, evidence, diagnosis/rerun and maintenance
cost **subject to agreed quality, safety, traceability and reproducibility**.
Fewest tests/clicks is not the objective; cheap execution does not establish PASS.

1. Fix the mandatory set first: acceptance conditions, material risks, important
   boundaries, branches and state transitions. Keep its denominator, source version
   and exclusion reasons in the existing project test/acceptance record.
2. For each acceptance condition, select factors that can change its judgment,
   equivalence partitions/representatives/boundaries, feasibility constraints and
   important interactions. Avoid the full Cartesian product. Unreachable states
   are not the same as operations that must be attempted and correctly rejected.
3. Pairwise is a candidate for ordinary interactions, not a universal guarantee.
   Explicitly select justified higher-order combinations for material risks.
   Start abnormal checks with one fault; combine faults only for evidenced concerns
   such as error priority, authorization bypass or transaction atomicity.
4. Record selected strength/constraints and omitted conditions with reasons; trace
   condition IDs -> scenarios -> consolidated operations/checkpoints. Requirements,
   necessary conditions and code-path coverage have different denominators.
   Do not redefine the denominator silently to fit a budget.

For each proposed addition record the unchecked guarantee, failure impact, difference
from existing evidence, cheapest reliable layer and total-cost rationale. Adopt,
defer or reject with a reason in the existing plan/change record. Weak proposals
need not become tests; unknown material risks cannot be discarded as mere expense.
For interaction background see [NIST combinatorial testing](https://www.nist.gov/publications/combinatorial-testing);
its research is not proof of this project's sufficiency or savings.

Trial only unknown/changed operations. Choose automation by creation/maintenance
cost versus plausible repeated-run savings and reliability; do not force every
check into automation. Keep the AI-trial -> deterministic Playwright/FlaUI route
in [AI-assisted Testing](ai-assisted-testing.md#from-screen-trials-to-deterministic-regression).

### Completion and budget decisions

Finish only when mandatory checks/evidence and required gates are satisfied, and
the responsible owner disposes of remaining defects, not-run work and residual risk.
Keep failed/blocked/not-run results intact; acceptance never rewrites them into PASS.
If a budget/effort limit is exceeded, stop affected advancement for a human decision
on scope, deadline and risk acceptance. Rebaseline any agreed scope/version change;
never silently drop mandatory checks or terminate successfully on budget alone.
Set scales/budgets per project; no universal numerical target is imposed.

Keep one lightweight selection/adoption/exit record in existing project test docs.
Reference it from existing plan preflight, session stopOn and the review packet;
v2 requiredConditions records agreed necessary IDs, not the complete factor model.
No new mandatory v1/v2 fields, condition generator, cost solver or automatic
sufficiency/approval gate is implemented. Existing HTML/JSON carries those
checkpoints. Practical sufficiency and cost effectiveness remain unverified until
an authorized pilot measures preparation, runs, rework, evidence and maintenance.

## Choose the next guide

| Current question | Guide |
| --- | --- |
| Which test layer proves the behavior? | Continue with this strategy and [Coverage Model](coverage-model.md). |
| Why can the real entry point not reach the selected branch? | [Target Reachability](target-reachability.md) |
| How should UI/CLI/DB execution capture evidence? | [AI-assisted Testing](ai-assisted-testing.md) |
| Which checks need a human, and which setup can be shared? | [Human Work Direction](human-work-direction.md) |
| How should a supplied customer workbook receive case/step evidence? | [Functional Test Excel](functional-test-excel.md) |

Use only the route needed for the current question. Each guide keeps its own execution, evidence and HALT conditions.

## Test layers

### E2E

Use for a small number of business-significant flows.

Typical boundary:

```text
UI or public entry
  -> application
  -> real DB
  -> external-system stub/sandbox
```

Prefer real application and database behavior. Stub external systems when real connectivity would make tests unstable, unsafe, expensive, or non-repeatable.

### Integration / Service

Use for rule combinations, data conditions, transaction behavior, and state transitions that would be expensive to enumerate through the UI.

Typical boundary:

```text
Application/service entry
  -> business logic
  -> repository / PL/SQL
  -> real test DB
```

### DB Integration

Use when important behavior lives in SQL, stored procedures, triggers, jobs, or DB-driven dispatch.

Test the DB object directly when that is the actual behavioral boundary. Do not force a C# unit-test shape around PL/SQL-owned logic.

### Unit

Use only for remaining deterministic logic where isolation provides cheaper, faster, clearer proof:

- calculations;
- date/rounding rules;
- state decisions;
- high-combination pure rules;
- algorithms without meaningful external I/O.

Avoid tests for trivial property access, framework behavior, or mappings already covered more effectively elsewhere.

### Manual

Use only when automation cost is not justified or the behavior depends on human judgment, physical devices, unsupported legacy UI surfaces, or one-off acceptance. Record the observation and evidence.

When manual work is necessary for several independent cases, apply [Human Work Direction](human-work-direction.md) to reduce the number of human sessions and environment/screen switches. Group shared setup, but require an independently verified fixture/reset, oracle, evidence and status for **each verification ID**. Do not substitute one combined PASS for distinct case results. Prefer machine preflight and evidence capture before human interaction; split cases whose side effects or approvals cannot safely coexist.

## Functional-test Excel deliverable

For customer-facing, human-reviewed functional tests, use the original `test_template.xlsx` as the workbook format (cover/list/FT-xx). See `functional-test-excel.md` for the generator and mapping. Select materially relevant cases, keep expectations reviewable, and retain the unique Feature Map verification ID on each case sheet. Do not convert all unit tests to Excel, skip important cases because the template has ten initial slots, or mark a case passed merely because the workbook formula shows a summary. The workbook is a deliverable, not business-logic truth.

## Test boundary contract

Every non-trivial test should make these boundaries explicit, either in test code/fixtures or in durable documentation when the boundary is expensive to reconstruct:

- **Entry point:** UI, API, batch, service, procedure, method.
- **System under test:** components expected to run for real.
- **DB boundary:** real test DB, container/VM DB, controlled schema, mock only when justified.
- **External boundary:** real, sandbox, stub, fake, or out of scope.
- **Transaction boundary:** what commits or rolls back together.
- **Data boundary:** initial records, shared masters, generated data, cleanup policy.
- **Time boundary:** real clock, fixed clock, business date.
- **Async boundary:** queue/job/event behavior and wait strategy.
- **Verification point:** response, UI state, DB state, file, event, log, external request.
- **Exclusion:** what this test does not guarantee.
- **Cleanup:** rollback, truncate, snapshot restore, disposable environment.

Example:

```text
Scenario: inventory allocation at the exact boundary

Entry:
  RegisterOrder

Real:
  C# application logic
  Oracle
  PKG_ORDER

Stub:
  SAP endpoint

Initial state:
  STOCK.QTY = 20

Input:
  ORDER.QTY = 20

Observe:
  ORDER inserted
  STOCK.QTY = 0
  SAP_QUEUE inserted

Does not prove:
  SAP accepted the message
```

## Placement rule

Choose the test layer by behavior, not by code shape.

Prefer the lowest layer that still proves the required guarantee, except when using a lower layer would replace real behavior with unrealistic mocks.

A practical decision sequence:

1. Is this a business-significant workflow? Consider E2E.
2. Does the guarantee depend on DB/transaction/stored-procedure behavior? Prefer integration/DB.
3. Is the behavior a rule combination or state transition that does not require UI? Prefer integration/service.
4. Is the behavior deterministic and cheap to isolate without distorting design? Consider unit.
5. Is the same guarantee already protected adequately? Do not duplicate unless the overlap protects a different failure mode.
6. If no stable automated boundary exists, use manual evidence and record the limitation.

## Legacy Windows Forms

Do not begin by refactoring the application into ideal layers.

Use this order:

```text
Business scenario
  -> current execution path
  -> DB before/after
  -> existing method/procedure boundaries
  -> executable test
  -> smallest extraction only where testing is otherwise impractical
```

Useful boundaries may already exist at:

- Form / screen;
- event handler;
- called method;
- service-like method hidden inside the form;
- stored procedure;
- table effect;
- external file or process boundary.

An event handler containing UI, SQL, business rules, and file/process I/O is a valid initial E2E boundary even if it is a poor long-term design. Extract only the parts that produce a clear testing or maintainability payoff.

When an EXE, event, or job cannot reach a target BL because data/config/API prerequisites are unknown, use `target-reachability.md` for backwards/forwards path discovery, read-only preflight, isolated fixture setup, and blocking-frontier validation. A fixture or stub does not by itself prove real target execution.

## AI-assisted execution and human review

Use `ai-assisted-testing.md` for the optional AI-to-runner integration. Assign each
step to the least costly reliable actor:

- **AI:** inspect Feature Map/source/tests, select materially different scenarios,
  discover reachability prerequisites and draft project-native tests/fixtures;
  diagnose unexpected evidence from a bounded, sanitized context.
- **Code:** perform repeatable UI/CLI/API/DB interactions, deterministic assertions,
  reset/cleanup, log/trace/screenshot collection and result serialization.
- **Human:** establish ambiguous business oracles, approve consequential fixture
  writes/external boundaries, review changed assertions and accept residual risk.

Treat AI-generated expected values inferred only from implementation as unverified.
Never let automated UI-locator repair silently change business assertions. A
browserless HTTP smoke test proves transport/DB effects, not real UI typing.
Use Playwright for essential Web UI paths, FlaUI for automatable Windows UI, and
visual AI selectively where stable identifiers are unavailable. Avoid forcing
all branch/value combinations through a fragile UI test. Do not extend the
existing Linux bubblewrap Task Runner to live UI or writable DB execution.

## Evidence

A passing UI message is not enough for DB-heavy business systems. Prefer observable business effects such as:

- row inserts/updates/deletes;
- state transitions;
- history rows;
- queue/outbox rows;
- emitted files;
- process launches;
- external request capture;
- retry/error state.

Keep exact evidence in tests, logs, snapshots, or CI artifacts. Feature Map XML should retain only representative verification knowledge and references.
