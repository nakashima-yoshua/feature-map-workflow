# Human Work Plan v2

Both generators still accept v1. The new plan never executes an operation or
changes Result v1 or the Feature Map XSD.

Use v2 only when several real operations need reusable procedures or separately
traceable checkpoints. Keep a trivial action on v1 or use no extra work-plan artifact.
See `examples/fictional-stock-request/human-work-plan.v2.example.json` for a wholly
fictional, unexecuted example. Pass it through the same `--plan` or `--human-plan`
options. No optimizer, runtime, DB connection or new service is introduced.

The conditional work sequence is: select verification/acceptance conditions -> trial
only unknown or changed operations -> specify operations/checkpoints -> reuse parts
and consolidate a safe route -> review/try affected parts of the consolidated plan
-> execute with individual judgments/evidence -> improve from measurements. Follow
[Development Lifecycle](development-lifecycle.md) for the preceding feature-sized
data/design/implementation loop and the later QA/release/operation boundaries.

During necessary screen trials, AI can identify operations and observation points;
after stabilization, prefer deterministic project-native execution and evidence
capture. Follow [the automation transition](ai-assisted-testing.md#from-screen-trials-to-deterministic-regression)
for Web/Playwright and Windows/FlaUI suitability, waits, reset and recovery checks.
The work-plan generators do not perform this conversion or execute those tools.

### Minimal data contract

- Retain `environment`, `sourceRevision`, `preflight` and sessions with `id`, `title`,
  `actor`, `sharedSetup`, `stopOn`, `cleanup` and ordered `steps`.
- `requiredConditions` maps every selected case ID to its agreed necessary condition
  IDs. Checks must cover that set exactly, so dropping an operation cannot silently
  turn partial coverage into a complete plan. Changing this set is a scope/plan change,
  not a way to improve a percentage.
- `procedures[]` is a frozen snapshot of reusable instructions: `id`, `revision`,
  canonical `sourceRef`, lifecycle `status` (`draft`, `active`, `retired`), and
  `verifiedAt` for active parts. Include `action`, `precondition`, `postcondition`,
  `resetBefore`, `recovery`, boolean `parallelSafe` and `destructive`, and exact
  `appliesTo` values for `environment`, `sourceRevision`, `actor` and `data`.
  Retired parts cannot be selected; destructive operations cannot declare parallel
  safety. Equality is a planning check, never proof of actual runtime state or authority.
- Each operation has a unique `id`, exact `procedureId`/`procedureRevision`, `data`,
  `dependsOn` and `restartFrom`. Dependencies must precede it in the same session;
  restart is at this or an earlier operation. The generator displays a reviewed
  **serial order**. It does not schedule parallel work, infer a safe state transition
  or restore data. Check actual prerequisites/reset and stop affected downstream work
  on failure; preserve the failed attempt and use a new execution identity on rerun.
- Each operation's nonempty `checks[]` maps case-specific `caseId`, `conditionId`,
  `stepNo` consecutive from 1 in actual per-case operation order, authoritative
  `requirementRef` (including agreed version),
  `expected` and `capture`. A case/step and case/condition pair must be unique.
  Identifiers cannot contain whitespace or `|`. Shared operations have independent
  checkpoints for each case; sharing login, navigation or observation never shares PASS.
  Case-wide accepted expectations remain in their existing specification/Feature Map.
- `trial` contains `mode` (`required`, `delta`, `reuse`) and `reason`. Reuse additionally
  requires an active dated procedure and `recordRef`. Required/delta may be pending:
  the brief explicitly identifies trial state, without asserting completion. During
  trials record actual operations, data/state, expectations, observations/evidence,
  execution/wait time, friction and recovery/restart. Do not repeat all known tests.

The core owns this record/validation method and role boundaries. Projects own their
business oracle, approved data, roles, environmental constraints, dangerous effects,
retention/access policy and customer layout. Keep canonical procedure definitions
with existing project fixtures/docs; a plan is a versioned execution snapshot linked
to them, not a competing requirement or a new public knowledge database. Record
validation date/applicability, revisit stale parts on change, and retire obsolete
ones. Promote common guidance only under the existing
[cross-task maintenance rules](cross-task-harness-maintenance.md); a necessary trial
of an unknown operation is different from automatically repeating completed tasks
to optimize the Harness.

### Formal results, evidence and costs

Exploratory trials and formal judgments are separate. A trial execution may be
reused only if the agreed requirements, exact specification/implementation/plan,
environment/data, reproducibility and original record/evidence meet the formal
contract. Obtain the actual adoption decision; a work plan never promotes it.
The existing evidence catalog rejects `preparation` as current `functional` proof.
Do not rewrite a sealed preparation run into PASS; preserve its provenance and
perform a formal run if the formal conditions were not met.

Keep native Result v1 (`passed`, `failed`, `blocked`, `not-run`) and individual
`checks[]`. Actual assertion mismatch is `failed`; unmet prerequisites preventing
verification are `blocked`; unattempted work is `not-run`. Do not mark downstream
checks failed merely because an earlier operation blocked them. Freeze the plan
and procedure snapshot with `planSHA256`; link operation ID/procedure revision,
requirement/condition, case, run and evidence in the private record/catalog.

The brief displays each shared operation once and every mapped checkpoint. Excel
projects checkpoints back to their own case/`stepNo` rows and preserves pending
human judgment. Its v2 rows retain `CONDITION:... | OPERATION:... | PROCEDURE:...`
trace labels; mapped Result v1 checks must carry the matching `conditionId` as well
as `stepNo` and actual evidence. Existing v1 books/results retain their behavior.
The Excel cover uses the validated v2 environment; an explicit incompatible
`--environment` is rejected rather than relabeling procedures for another target.
There are six rows per case: split a larger case explicitly; never truncate or
silently discard checkpoints. Evidence may be captured together only when each
case's observation and native result remain independently attributable. The current
Excel importer requires separate evidence records for different steps.

Optional `measurements` has a nonempty evidence `reference` and `minutes` using
any applicable categories: `preparation`, `setup`, `execution`, `waiting`, `switching`,
`rework`, `evidence`, `maintenance`. Values are finite nonnegative observations,
not targets; absence displays unmeasured. Record rerun scope, duplicated work saved
and remaining gaps in that referenced existing record when useful. No numerical
threshold or monetary conversion is imposed. Count measurement/record maintenance
itself; omit low-value detail. Evaluate product quality separately from QA efficiency.
Only after practical benefit is measured should more structured libraries, route
assistance or automation be proposed.
