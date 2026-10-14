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

## Step 3: Establish observable legacy behavior

For each materially affected business rule, choose the **lowest-cost reliable** verification layer (existing integration/DB tests, CLI, UI automation, or manual evidence). Cover normal flow, important boundary and failure cases, DB before/after state, transaction/retry effects and downstream outputs where applicable. Preserve input fixtures and evidence beside the tests; Feature Map keeps compact references.

When both old and new versions can execute, run them against equivalent isolated initial state and inputs; compare externally meaningful outputs and data effects. Normalize only explicitly approved nondeterministic fields (e.g. generated IDs and timestamps). Record accepted intentional differences and their business reason; never silently accept discrepancies or assert equivalence based on AI judgment.

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
