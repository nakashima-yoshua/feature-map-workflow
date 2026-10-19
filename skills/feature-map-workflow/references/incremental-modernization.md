# Change-Driven Incremental Modernization

## Purpose and budget rule

Modernize legacy software **only when a requested business feature or defect fix creates a justified opportunity**. The objective is affordable delivery and steadily reusable business knowledge, not the maximum amount of rewritten code. Do not run a portfolio-wide assessment, mass agent fan-out, or a new migration platform by default.

This workflow adds no Feature Map mode, XML/XSD field, mandatory runner, external service, or additional specification. It applies the existing `catchup` and `change` modes. Treat legacy modernization as an optional implementation decision, **not** a required phase for every change.

## Two different boundaries

1. **Understanding boundary**: the selected business scenario from actual UI/API/EXE/job trigger through outcome; inspect connected rules, reads/writes, transactions, configurations, DB routines and external interfaces that can materially affect the result. Follow unknown dependencies only until the feature is safe to explain and change. Do not survey unrelated modules.
2. **Migration boundary**: the smallest *cohesive, deployable, testable and reversible* responsibility that meets the requested behavior. Usually narrower than understanding. A few lines are not necessarily the smallest safe boundary if excessive adapters, round trips, split transactions or operational coupling make them expensive.

Record the two boundaries separately: `goal/scope` and `goal/exclude` define the authorized **change**, while `sourceMap`, `useCase` and relevant rules can cover surrounding **understanding**. Mention understood-but-unmodified dependencies without implying they are approved for replacement.

## Step 1: Understand the feature and preserve domain knowledge

First reuse any existing Feature Map and confirm it against the current source, tests, configuration and deployment context. Investigate only what the change requires. Use `legacy-analysis.md` and, if the desired branch is unreachable, `target-reachability.md`.

Document the business explanation **as soon as it is understood**, before considering replacement:

- business purpose and actor/trigger, scenario inputs and expected business outcome (`goal` and `useCase`);
- human-readable business rules, state transitions, decision criteria, exceptions and data effects (`knowledge/rule`, `invariant`, `constraint`);
- important entry points, tables, DB procedures, dynamic dispatch and external interfaces (`sourceMap`, and a compact diagram only if it reduces effort);
- verified observations and runnable/reproducible evidence (`verify/case` links to tests, logs and DB snapshots);
- unsupported assumptions and unresolved domain questions (`open/item` with a next action).

**Do not equate observed legacy behavior with approved business intent.** State clearly in plain text whether a rule describes observed current behavior or business-confirmed desired behavior. Source-only inference without verification is not approved business policy. Put consequential uncertainty under `open`; if observed and intended behavior conflict, obtain a business decision before treating the difference as a defect to fix. The existing XML fields suffice; do not invent confidence attributes or a second business specification.

A document should let a future engineer and a business stakeholder answer *what happens, why, under which conditions, and with what data effect*, without rereading multiple source files. Do not recreate obvious class/method catalogs or SQL text. The XSLT view is the human-facing document; XML remains the canonical durable index and Git stores change history.

## Step 2: Choose the cheapest safe change

Compare these three outcomes on **delivery cost + future maintenance/operation + verification + coexistence cost**, not rewritten lines alone:

| Outcome | Choose when |
| --- | --- |
| **Keep as-is** | The request needs no software change, or modernization offers no justified value. Knowledge capture can still be valuable. |
| **Change existing legacy code** | A bounded fix is safer and cheaper than introducing a new execution boundary. |
| **Migrate one slice** | A stable responsibility boundary can be replaced with a clear improvement while existing callers, data and external contracts stay compatible. |

Prefer the cheapest option that meets the requested acceptance criteria and long-term safety. A migration decision requires: its business scenario; start/end of the replacement; in-scope and explicitly excluded components; contracts/data ownership/transaction boundary; deployment and coexistence plan; tests and rollback; and why an existing-code fix is insufficient. Keep the explanation short and record a durable non-obvious choice in `knowledge/decision` with a reason. A rejected migration does **not** create a backlog obligation by itself.

Escalate for approval before changes to production data, public APIs, authentication, data ownership, external contracts, or irreversible operations. Do not equate permission to plan modernization with permission to deploy.

### Optional A/B/C decision for a legacy feature addition

Use this comparison inside existing basic/detailed design when a new rule may justify a responsibility boundary. **A is the first candidate**; if A meets acceptance safely at lower total cost, do not recommend B/C. If no software change is needed, retain the keep-as-is outcome above; choosing A also permits leaving the architecture unchanged. This is a design aid, not another gate or required report.

Reuse Step 1 evidence rather than starting a second investigation:

| Needed for this decision | Existing investigation owner |
| --- | --- |
| Actual UI/API/batch/EXE entry to the selected rule, dispatch, DB/PL/SQL and external I/O | [Legacy analysis](legacy-analysis.md#analysis-model) and its [hidden dependencies](legacy-analysis.md#hidden-dependency-checklist); use [target reachability](target-reachability.md#two-direction-route-discovery) only when the route/prerequisites are unclear |
| Data lineage, writes, side effects, locks, transaction ownership, retries and operator recovery | Legacy analysis: [data semantics](legacy-analysis.md#data-semantics) and [concurrency/recovery](legacy-analysis.md#concurrency-and-recovery) |
| Implicit configuration, permissions, deployment assumptions and existing tests/logs | Legacy analysis: [evidence sources](legacy-analysis.md#evidence-sources) and [runtime verification](legacy-analysis.md#runtime-verification) |

Keep important references in `sourceMap`, proven constraints in `knowledge`, and unknowns in `open` with a next action. An unobserved transaction or entry route stays unknown; source analysis alone does not prove runtime behavior.

| Option | Applicable condition | Cost or reason to reject |
| --- | --- | --- |
| **A. Local change in the current structure** | The rule is cohesive in an existing method/procedure and its tests can protect the change without a new boundary. | First choice. Reject only with concrete evidence of scattered changes, unsafe coupling or excessive verification/maintenance cost. |
| **B. Extract only the new Application/Domain responsibility** | A distinct business rule can avoid Infrastructure dependencies; a small port and thin legacy adapter remove demonstrated coupling or make important combinations testable. | Keep the entry and existing DB transaction owner. Reject if adapters duplicate shared rules, add round trips, split transactions or cost more than A. No prescribed DI/ORM/framework or project count. |
| **C. Replace one slice gradually** | An existing entry can safely route an authorized subset to old/new implementations (**Strangler Fig**). For replacement *inside the same entry*, consider **Branch by Abstraction** through one shared contract. | Requires controlled routing, equivalent contract/state effects and a practical switchback. Reject when traffic, data ownership, coexistence, performance or recovery cannot be controlled. Do not add routing just to justify C. |

For A/B/C, record a short comparison in the existing change plan or `knowledge/decision @reason`. Cover these dimensions with evidence, estimates or explicit unknowns:

- **Change spread and rules:** affected callers/DB objects, independent new rules versus rules shared with legacy callers, and who owns each rule. Avoid two authoritative implementations of the same rule.
- **Dependencies and tests:** compile-time dependency direction, the concrete coupling a port removes, and the cheapest characterization/functional/DB tests. Domain must not depend on SQL/ORM/UI/legacy implementations; an Application-owned port may be implemented by Infrastructure.
- **Runtime and recovery:** query/round-trip count, latency/throughput, transaction/isolation/locking and retry/duplicate semantics, deployment/coexistence and rollback cost. Preserve existing DB/PL/SQL ownership; do not mechanically move stored logic into Domain.
- **Total cost and operation:** implementation, test, migration and cutback effort, future maintenance, team skills/support capacity and who can operate the result. Label estimated costs; do not invent measured savings or require numeric scoring.

For a small C#/.NET + DB adoption and rejection walkthrough, see the [fictional request-review example](../../../examples/legacy-feature-boundary/README.md). Its sketches are a **design proposal**, not a bundled business implementation or real-system verification. The conceptual sources are [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html), [Strangler Fig](https://martinfowler.com/bliki/StranglerFigApplication.html) and [Branch by Abstraction](https://martinfowler.com/bliki/BranchByAbstraction.html); none makes extraction mandatory.

## Step 3: Establish observable legacy behavior

For each materially affected business rule, choose the **lowest-cost reliable** verification layer (existing integration/DB tests, CLI, UI automation, or manual evidence). Cover normal flow, important boundary and failure cases, DB before/after state, transaction/retry effects and downstream outputs where applicable. Preserve input fixtures and evidence beside the tests; Feature Map keeps compact references.

When both old and new versions can execute, run them against equivalent isolated initial state and inputs; compare externally meaningful outputs and data effects. Normalize only explicitly approved nondeterministic fields (e.g. generated IDs and timestamps). Record accepted intentional differences and their business reason; never silently accept discrepancies or assert equivalence based on AI judgment.

Connect this evidence to the existing [test boundary contract](test-strategy.md#test-boundary-contract), not a separate architecture test stage. Characterization tests describe observed behavior; functional expectations still need their existing business authority. For A/B/C, check caller/API and error contracts, data/schema and role/permission compatibility, rollback after partial failure, retry/duplicates, representative performance and operator logs. Pure-rule tests cannot prove these DB/entry effects. If automation is unavailable, name the human check, expected observation, evidence location and owner; retain `not-run` until performed. A code switchback does not undo committed data or external effects: require an authorized recovery path for those separately.

If the old version is not runnable, use trustworthy recorded evidence and mark what remains **not verified**. An observed single scenario is not proof of all behavior; avoid claiming universal equivalence. Keep tests and comparisons limited to the replaced slice and its material contracts.

## Step 4: Implement one slice, verify and finish

- Make the smallest approved change. Leave unrelated legacy modules running; use an adapter/strangler boundary only when integration truly requires it.
- Keep DB ownership and transaction semantics explicit. Do not split a transaction between old and new components without design/approval.
- Verify representative legacy/new behavior and required boundary/error/retry/permission cases. Run build and closest automated checks, with human review of uncertain business oracles.
- Check documentation **as a completion condition**: update the existing Feature Map with newly established business knowledge, decisions, changed source references, and verification evidence. If everything is already accurate, record in the PR/delivery summary that the map was reviewed with no durable delta; do not make empty XML edits.
- Explicitly report **understood scope**, **modified/migrated scope**, **unmodified dependencies**, **observed vs approved behavior**, **verified/not-run/failed evidence**, and **remaining blockers**. Advance `verified`/`closed` only under existing state rules.

HALT when the slice cannot be isolated safely, an important business rule is unknown, required old/new effects cannot be compared with justified evidence, or scope/approval changes. Offer the least-cost next investigation instead of broadening migration silently.

## Example: fictional inventory import

A request changes import error handling. Investigation spans upload -> validation -> import -> stock DB update -> notification. The change boundary can still be **only the validation responsibility**, leaving stock persistence and notification in the legacy system. Preserve the existing transaction/response contract.

In the existing Feature Map (the XML elements below fit schema v1.3; they are *illustrative entries*, not a new format):

- `useCase/scenario`: "When an operator imports a stock file, invalid rows are reported and valid rows are handled according to the confirmed import policy."
- `knowledge/rule`: "Observed current behavior: an invalid product code rejects its row; evidence: integration test import-invalid-product."
- `knowledge/invariant`: "No stock quantity changes for rejected rows."
- `knowledge/decision @reason`: "Migrate only import validation; persistence stays legacy, avoiding a split DB transaction and additional integration service."
- `sourceMap/ref`: existing UI/handler, validation method and DB procedure references.
- `verify/case`: expected legacy/new validation output and DB effects, linked to real tests/logs; mark `planned` or `not-run` until actually executed.
- `open/item`: "Whether partial imports are allowed" until a responsible business owner confirms the rule.

Avoid treating this fictional illustration as a real customer's specification.

## Exit criteria

A feature change is ready for review when (1) the business scenario and material rules are intelligible and linked to evidence, with uncertainties explicit; (2) the implementation boundary is approved and smaller than or equal to what was actually authorized; (3) required checks ran or limitations are stated without claiming proof; (4) the Feature Map was updated or explicitly reviewed as already current; and (5) unrelated migration, new infrastructure and unapproved deployment did not occur.
