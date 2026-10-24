# Human Work Direction and Focused Verification Brief

## Goal

Human time is a constrained resource. Before asking a person to verify a feature, batch compatible checks into **few, safe human sessions** and supply a **feature-focused understanding brief**. Share setup, not case-specific starting state, oracle, evidence or status. Test scripts/results stay canonical; Feature Map XML remains the durable knowledge index. The brief and human session plan are derived artifacts, not a second specification or evidence of test execution.

Use this as an **optional conditional planning gate** after test boundaries are established and before human verification or acceptance. Skip the overhead when there is one trivial action.

## Diagram selection: no three-diagram limit

For the extended 17-view candidate catalog and selection/reconciliation rules, see [Diagram Selection](diagram-selection.md). These are candidates, never required diagram counts. Specialized diagram titles (e.g. データリネージ, CRUD, 決定表, ジョブ依存) can be selected from already documented views; a recommendation must not generate unsupported content.


Select the existing evidence-backed view that answers the tester's question. There is **no numeric cap** and no mandatory triad:

| Question | Useful notation | Existing Feature Map diagram kind |
| --- | --- | --- |
| Who does what, which branch or error happens? | UML-style activity/business flow | activity / flowchart, Mermaid flowchart TD |
| Which actor or role may use the feature? | Use case | usecase, represented via supported Mermaid flowchart |
| What data travels to DB/files/APIs? | Data flow (DFD, not UML) | flowchart, titled Data Flow / データフロー |
| How do relevant tables and keys relate? | ER (not UML) | er, Mermaid erDiagram |
| Which operations are valid in which state? | UML state machine | state, Mermaid stateDiagram-v2 |
| What is the order of calls, retries and external effects? | UML sequence | sequence, Mermaid sequenceDiagram |
| What object responsibilities matter? | UML class | class, Mermaid classDiagram |
| Which service/deployment boundaries affect a test? | Architecture | architecture |

Diagram candidates are selected conservatively from the chosen verification cases (type, condition, expectation), sourceMap reference kinds and access, existing diagram kind and title. Activity for business decisions, data flow for DB/API effects, ER for multiple relevant tables, state for transitions/duplicates, sequence for retries/external I/O, use case for roles/permissions, class for object relationships, architecture for multi-boundary interactions. Do not infer unsupported relationships or generate fabricated diagrams. The script draws **only diagrams already in the Feature Map**. Add any missing diagram only after source/code/read-only-DB investigation and approval of material business semantics. Diagram IDs supplied explicitly can override auto selection without a fixed count.

Show the first relevant diagram, keep the rest collapsible. Diagrams stay in per-feature XML, not copied into a global HTML. ER foreign keys and cardinality must be supported by actual evidence; a JOIN alone is not an enforced FK.

## Session batching procedure

1. List requested verification IDs; separate deterministic automation from human interaction and human business judgment.
2. Determine actual environment, revision, operator role, approved expected result, test-data initialization, evidence and cleanup for each case.
3. Run authorized machine preflight and prepare isolated fixtures/evidence capture **before** inviting a person. Do not assert preflight was done merely because the run sheet lists it.
4. Group cases sharing environment/role/screen/setup **only when each case's starting state can be restored and checked**. Keep urgent blockers independent and never batch over incompatible or unsafe states.
5. Minimize logins, manual switching and waiting. Put common setup once per session, then order case-specific action, reset, expected result and evidence under a unique verification ID.
6. Provide human instructions: purpose and selected figures, single-session setup, exact case sequence, HALT conditions and cleanup. The runner/human must confirm prerequisites and authorization.
7. Preserve every case's individual observed effects, status and evidence in the project's existing runner/JUnit/TRX/result.json. Human approval remains separate. Failure or uncontrolled dependency blocks affected downstream cases; do not report them as passed.

**HALT** on unapproved business oracle, unsafe DB/external action, failed data reset, mismatched revision/environment or missing evidence isolation. The work plan is not an authority to run privileged actions.

## Generated HTML and JSON plan

Generate a brief with Python standard library:

    python skills/feature-map-workflow/scripts/build_verification_brief.py --feature-map examples/fictional-stock-request/feature-map.xml --use-case UC-SUBMIT --plan examples/fictional-stock-request/human-work-plan.example.json --output verification-brief.html

Explicit diagram override (repeat any number of diagram IDs):

    python skills/feature-map-workflow/scripts/build_verification_brief.py --feature-map examples/fictional-stock-request/feature-map.xml --use-case UC-SUBMIT --diagram DG-FLOW --diagram DG-DFD --diagram DG-ER --plan examples/fictional-stock-request/human-work-plan.example.json --force

Other options: repeat --case for selected verification IDs; a multi-use-case map requires both explicit --use-case and --case. --diagram is optional. --output must remain inside the feature directory. --force replaces an existing regular HTML file. Without --plan, the generated brief reports **HALT: no executable human instruction defined** instead of guessing actions.

The plan is an optional JSON object with version=1, environment, sourceRevision, nonempty preflight[], sessions[]. Each session requires id, title, actor, nonempty sharedSetup[], stopOn[], cleanup[] and steps[]. Each step requires caseId, resetBefore, action, capture. Every selected case must appear exactly once across sessions; the generator rejects unknown, duplicate and missing case IDs. See the fictional JSON example for a complete template.

The generator only **reads** input data, escapes user-controlled text, rejects XML DTD, writes output atomically and never runs tests or connects to DB. Mermaid uses only a local feature-map.mermaid.min.js beside output by default; --allow-cdn opts into a pinned public CDN fallback. When no runtime is available, Mermaid source remains readable. No external library is needed to generate the HTML, and no new Feature Map mode, XSD element or service is introduced.

## Procedure-based plan version 2

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
  positive `stepNo`, authoritative `requirementRef` (including agreed version),
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

## Excel evidence handoff

When a customer or human reviewer needs the standard functional-test workbook, generate it with `scripts/build_functional_test_excel.py` and the locally provided `test_template.xlsx`, following `functional-test-excel.md`. Human Work Plan groups setup and manual actions; **FT-xx** sheets keep per-case plans and independent evidence. Keep `verifyCaseId` and sourceRevision links, and never infer approval from a draft session plan.

## Code-review handoff: one focused decision package

In addition to functional testing, apply the same human-time optimization to the [risk-tiered code review](code-review.md): **machine evidence first, human judgment on the smallest consequential scope**. Collect actual CI/build/test evidence, the exact PR/head SHA and the fresh-context AI review's Important findings and dispositions before calling on a human. For a multi-feature PR, group common environmental/revision checks, not business acceptance or domain-specific judgments.

Give the reviewer a compact PR brief: (1) accepted purpose and unchanged behavior; (2) actual changes and risk tier; (3) tests run and what they cannot prove; (4) unresolved findings and decisions; (5) the minimum helpful UML/DFD/ER diagrams, if any; (6) a separate code/config revert path and DB/external-effect recovery requirements. Use existing Feature Map/PR/test evidence links rather than copying new specifications or raw logs.

The reviewer must explicitly authorize the **current revision** under the repository's host policy. An advisory AI review cannot approve it. If a required security or business decision has no owner, or an Important finding is unresolved, report **HALT** rather than drafting a favorable approval. Measure hands-on review time, wait time and correction loops alongside real regressions and reverts.

## Human efficiency metrics

Measure human sessions, hands-on minutes, setup switches, interruptions/retries and end-to-end time alongside individually verified/blocked case counts. Optimize these jointly: a faster batch that destroys test independence or delays an urgent release is **not** a success. Do not save work plans or results as repeated XML prose, and do not commit customer screenshots or production data.
