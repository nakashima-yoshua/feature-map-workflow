# Target Reachability and Test Fixture Discovery

## Purpose and trigger

Use this workflow when a requested legacy behavior cannot be exercised because the path from the real entry point to the target method, procedure, branch, or data read is unclear, or required DB/API/configuration state is missing. Examples: a batch EXE dispatches by arguments and a DB flag; an INNER JOIN silently removes a target row; an external API reply prevents the target BL from being called.

This is an optional investigation within existing `catchup` or `change` mode, **not** a new Feature Map mode, required test framework, general source indexer, or promise of full automatic test-data generation. Minimize the work needed to demonstrate **one requested target behavior**. Follow `legacy-analysis.md` for broader system boundaries and `test-strategy.md` for the cheapest trustworthy test layer.

## Inputs and authorization

Before preparing or executing anything, identify or discover:

- **Target**: symbol/procedure/branch and the exact observation wanted (entry reached, branch taken, expected input rows, DB effect, output).
- **Launch**: known executable, arguments, job/event/scheduler trigger, site/user/role and deployed version; if not known, investigate candidates.
- **Boundary**: what must run for real (application/DB/procedure) and what can be stubbed (API, file receiver, message broker).
- **Environment**: test DB/schema, binaries, configuration, credentials, business date, and isolation/cleanup method.
- **Authority**: permitted read, fixture changes, execution, external calls, and whether observed data may be copied. Never infer write/execute permission from permission to investigate.

Default to read-only repository, schema, configuration and log inspection. For fixture insertion, starting an EXE, changing configuration, triggering queues/jobs, or sending API requests, use only an explicitly authorized isolated environment and scope. Do not seed production, bypass application authorization, use real credentials in fixtures, or silently contact live external systems. Prefer synthetic data and offline stubs; honor customer confidentiality. If safe execution is unavailable, stop at an executable plan marked **not run**.

## Two-direction route discovery

1. **Backward from target**: find callers, control predicates, argument/data producers, error/early-return gates, and the path-specific side effects. Include DB procedure, script, process, event, reflection and dynamically selected routes.
2. **Forward from launch**: inspect argument parsing, job routing, config, permissions, process/service/scheduler entry, and the runtime version. Where possible, join this reachable prefix to a backward candidate.
3. **Select a candidate path**: choose the shortest low-risk path that still runs the required behavior for real. Alternate OR-routes need not all be prepared. Never bypass a business or security gate merely to make a test pass.
4. **Mark evidence**: distinguish *possible* (source/metadata/config says the route exists), *observed* (a trace shows traversal), *observed-only* (trace exists but mechanism is unexplained), and *unresolved* (missing edge or condition).

A static call graph alone is insufficient for dispatch chosen by DB values, Registry/configuration, reflection, events, dynamic SQL, batch orchestration, message queues, and scheduled jobs. If a concrete launch-to-target link cannot be justified, record the gap; do not invent it.

## Path-specific prerequisite closure

For the selected path, work backwards from **each gate that must succeed** and recursively expand the conditions required to satisfy it. Record the *provenance* (file:symbol:line, SQL/procedure, schema, config key, API contract, runtime log), not just a proposed value.

| Domain | Typical gate and investigation |
| --- | --- |
| Control | argument, role, status branch, early return, exception, feature flag |
| DB / data | SQL parameters, JOIN filters, master/code tables, FK/default/constraint, view/procedure/trigger, required absence (NOT EXISTS), transaction visibility |
| External | request method/path/body/headers, response code/shape, paging, correlation, auth, sequential or stateful replies |
| Environment | file/Registry/env/secret reference, site/tenant, binary version, permission, feature flag, filesystem path |
| Time / order | fixed business date, cutoff, predecessor batch, async completion, cache state, retries, locks and concurrent state |

Model predicates as **AND/OR/NOT**, not merely a list of required tables. For a SQL read, inspect the exact query and bound parameter values, then derive the minimum satisfying row set; evaluate each JOIN and WHERE filter (including filters that turn a LEFT JOIN into effective inner filtering). Consider negative prerequisites such as *no matching processed row exists*. Do not traverse every schema edge: stop at conditions that can change this chosen path.

Label each prerequisite separately with:

- **Condition**: predicate and dependencies, including negative conditions and alternatives.
- **Source**: inspectable evidence or `unresolved`; do not present a hypothesis as observed fact.
- **Plan**: read-only check; fixture seed/setup; stub; or manual prerequisite.
- **State**: `unknown`, `inferred`, `prepared`, `observed`, `blocked`.
- **Scope**: environment and effect of satisfying it.

A fixture is **ready** only after its selected path's known prerequisites are prepared, absent-row requirements are checked, DB constraints are consistent, stubs are deterministic, and cleanup is defined. Ready does not imply reached.

## Build the smallest reproducible scenario

Use existing project-native tests/fixtures. Create temporary scenario artifacts only if needed; do not introduce a parallel specification or require YAML/JSON/XML in every repository.

Minimum scenario contract:

| Field | Required record |
| --- | --- |
| Target | method/branch + specific expected observation |
| Launch | EXE/event/job, arguments, runtime identity and configuration |
| Real vs stub | actual DB/application/procedure; sandbox/stubbed external interface |
| Prerequisites | referenced condition IDs; setup order; expected row counts/responses; required absent state |
| Run and cleanup | exact authorized invocation, environment isolation, reset/rollback/retry handling |
| Assertions | target entry **and** intended branch/data/effects, not just process exit code |
| Evidence | trace/SQL counts/API capture/DB before-after/test result with paths, timestamps and version |
| Exclusions | what a stubbed or unobserved interface does not prove |

Prefer idempotent setup and deterministic cleanup. Apply data prerequisites in dependency order, after checking for a cycle or required predecessor action. Do a read-only preflight before expensive execution: prove selected SQL predicates and row counts against the test DB when possible; check stub request matching, time, flags, files and credentials. An unknown condition must remain visible and may block execution; do not simply insert random data until the query returns rows.

A runnable scenario can use files such as `tests/scenarios/SC1/seed.sql`, `stubs.json`, `run.ps1`, `assertions`, and `evidence/` **only if these fit the existing repository conventions**. These are test artifacts, not durable Feature Map XML sections.

## Forward verification and blocking frontier

1. Run only in the authorized boundary. Capture start arguments/version/config identity and checkpoints along the expected route.
2. Find the **first blocking frontier**: the earliest expected gate that did not pass, or the earliest observed divergence. If no trace exists, capture a narrower, safe observation before guessing.
3. Compare **expected predicate, actual bound values, retrieved row counts, exception/return reason, API request/response, and observed execution path**.
4. Correct only the evidenced missing prerequisite or the route hypothesis; re-check downstream prerequisites affected by the change. Do not refactor business code as a shortcut.
5. Rerun from a reset, controlled initial state. Bound investigation by scope and available budget; after repeated inconclusive attempts, report the blocker and cheapest next observation rather than looping.

For a 0-row SQL result, first check bound parameters, then isolate the failing WHERE/JOIN predicates with diagnostic read-only queries and DB metadata. For an unexpected API outcome, compare request/response contract and stub matching before changing application code. For asynchronous paths, distinguish “not yet observed” from “will never run”; use bounded waits and evidence of queue/job state.

## Proof levels and HALT

Report proof levels independently:

1. **Route discovered**: source/metadata support a possible path; no execution proof.
2. **Target reached**: trace proves the requested method/branch executed.
3. **Behavior verified**: requested input, rows, output and/or side effects match assertions.
4. **Reproducible**: reset + rerun produce the same outcome in the stated environment.

Do not upgrade a level because a fixture was written, the EXE returned 0, a stub answered successfully, or one method was covered. A stub proves application behavior at the stub boundary, **not** live integration. A possible-only path is never counted as observed; record observed-only routes as unresolved.

**HALT** on missing execution authority, production-only/unsafe dependencies, unknown credential or sensitive-data handling, destructive unisolated effects, unresolvable environment mismatch, or a material uncertainty that changes expected behavior. Return the route found, blocking frontier, missing prerequisites, evidence, and one next action rather than falsely reporting success.

## Fictional worked example

Target: `InventoryBL.Calculate`, specifically the branch reached when an exportable shipment has enough stock.

~~~text
Launch: Batch.exe --job=Export --site=P1
Possible route: Main -> JobDispatcher -> ExportBL -> InventoryBL.Calculate
Gate C1: export.enabled = true (config)
Gate C2: shipment.status = READY and shipment.site = P1 (DB)
Gate C3: product_master matches shipment.product_id (INNER JOIN)
Gate C4: stock_lot has sufficient allocatable quantity (DB)
Gate C5: partner API returns active customer (stubbed external boundary)
Gate C6: no already-exported record exists (NOT EXISTS)
~~~

If the first run stops after querying shipments with zero rows, C5 is **not yet tested**. Inspect bound site/status and C2-C3-C6 with read-only diagnostic queries. A synthetic READY shipment alone will not satisfy a missing product master, and adding data without checking C6 may invalidate the query. Once preflight passes, rerun and capture a trace at `InventoryBL.Calculate`, the actual input/branch, and the expected DB/file effect. Reset and repeat to justify reproducibility.

This example is illustrative, not evidence from a real target system. Do not copy its schema, business values, or executable command into another project without matching local source evidence.

## Output and Feature Map integration

During investigation, return a compact progress record rather than a full graph:

~~~text
Target: <symbol + branch/observation>
Launch/path: <candidate or observed path>
Frontier: <first unexplained or failed gate>
Prerequisites: <condition IDs with known/prepared/blocked status>
Verification: <route discovered | reached | behavior verified | reproducible>
Evidence: <source, diagnostic query, trace, test path, or none>
Next: <smallest safe next action or HALT reason>
~~~

Use Feature Map as the durable **index**, not the place to store an entire execution graph or scenario dump:

- `sourceMap/ref`: non-obvious entry point and source/data/API navigation references.
- `knowledge/rule` / `constraint`: confirmed, durable behavior and environment limits only.
- `verify/case`: representative test and evidence references; do not copy all fixture rows/trace events.
- `open/item`: unresolved gating dependency, type `data`, `environment`, `external-dependency`, etc., with cheapest useful `next`.
- `diagrams/diagram`: optional compact route only if it materially reduces understanding cost.

Do not change the XSD, invent a new mode, or mark the Feature Map `verified` based solely on a speculative route or successful setup.