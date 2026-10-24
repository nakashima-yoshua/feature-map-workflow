# AI-assisted functional testing and evidence

## Purpose and ownership

Integrate AI-assisted testing with the existing Source-first Feature Map workflow. This is **optional guidance and a test-runner adapter contract**, not a mandatory new test runtime, XML schema, MCP server, or agent. Keep the current `catchup` and `change` modes and use `test-strategy.md` and `target-reachability.md` as the existing boundaries.

AI explores and drafts; deterministic code executes and asserts; a human determines important business expectations and accepts risk.

| Responsibility | Owner |
| --- | --- |
| Read the selected feature, scenarios, rules, entry points and existing tests | AI (read-only) |
| Select minimal distinct cases and find target-path prerequisites | AI proposes, human reviews material gaps |
| Define authoritative expected behavior | Approved contract/invariants or human |
| Generate project-native test code and synthetic fixtures | AI proposes for review |
| Run UI/API/job/DB actions and compare stable expected values | Code |
| Capture DB state, screenshots, trace, logs and execution identity | Code |
| Explain unexpected failures and first blocking gate | AI, from sanitized evidence |
| Accept exceptions, oracles, changed assertions and residual risks | Human |

## Workflow and decision rules

1. Start from the selected Feature Map `goal`, `useCase`, `sourceMap`, `knowledge`, `verify` and blocking `open` items. Use existing source and tests to fill only relevant details.
2. Choose the **cheapest reliable test boundary**. Use a few material business flows at UI/E2E; check the other conditions, states, boundary values, retries and DB effects at integration/DB/unit level where cheaper. Do not maximize test count.
3. Keep a distinct **test oracle**: accepted requirement, business invariant, previously approved expected state, or explicit human judgment. A model's restatement of implementation behavior is not an approved expectation. Missing material oracle => `blocked`.
4. If the real entry cannot reach the target, apply `target-reachability.md`: forward/backward route inspection, AND/OR/NOT prerequisites, read-only preflight, synthetic fixtures/stubs, authorized isolated execution, and deterministic reset/cleanup.
5. Prefer the project's existing test runner. Use Playwright for essential browser flows; FlaUI for Windows UI with stable automation controls; visual AI (e.g. Midscene) only where deterministic controls are impractical. Use DB/procedure/service/CLI tests for inexpensive branching.
6. Capture observable effects, not just button clicks or exit codes. Retain before/after DB state, changed records, relevant logs, browser screenshots/traces, and an execution identity. Separate `route discovered`, `target reached`, `behavior verified`, and `reproducible`.
7. On `failed` or `blocked`, AI may analyze the smallest sanitized evidence slice and propose fixes. **Never auto-rewrite an assertion or expected value to produce PASS.**
8. Keep complete test catalogs and evidence outside Feature Map XML. Patch only confirmed durable rules, important representative `verify/case` references or blockers, and validate through the existing XSD/Hooks.
9. For manual or hybrid steps, apply `human-work-direction.md`: have deterministic tools prepare fixtures and preflight first; use a focused UML/DFD/ER brief to orient the tester, and batch compatible manual actions by environment, role, setup and screen **without** combining case-specific initial state, expectations, status or evidence. Generate the derived HTML with `scripts/build_verification_brief.py`; an optional plan JSON lists per-case reset, human action, evidence capture and session-wide stop conditions. Human review remains mandatory for material oracles and authorization. Generating the brief itself proves nothing.

## From screen trials to deterministic regression

Use authorized AI-led screen interaction during trials to discover the real target,
prerequisites, operations, checkpoints, expected observations and evidence. Once the
procedure is stable, move repeatable execution, assertions and evidence capture to
project-native deterministic automation wherever its total cost is justified. Do not
make open-ended visual AI exploration the normal execution mode for every regression.
Retain human/AI steps only for unsupported controls, costly one-off work or actual
human judgment, with explicit limitations and separate observations.

For Web paths, Playwright is a candidate: prefer role/label/test-ID locators over
brittle screen coordinates or long DOM paths; retain bounded business-state assertions
in addition to action auto-waiting. See the primary [locator](https://playwright.dev/docs/locators),
[actionability](https://playwright.dev/docs/actionability) and
[trace](https://playwright.dev/docs/trace-viewer) documentation. A completed click is
not proof of the business result; traces supplement case-specific assertions.

For Windows/.NET/WinForms, evaluate FlaUI against the actual UI Automation exposure.
Its [official README](https://github.com/FlaUI/FlaUI/blob/main/README.md) covers Windows
UI frameworks and documents differences between UIA2 and UIA3, including possible
WinForms issues with UIA3. Choose a backend and stable element identity only after a
small target-control trial; the existing optional FlaUI.UIA3 installer is not proof
that every application/control is supported. Avoid a universal support claim.

Before adopting either adapter, verify authorized environment/access, stable element
identification, deterministic state/data initialization, bounded condition-based waits,
failure screenshots/logs/traces, cleanup and restart behavior. Bind automation source,
procedure revision, operation/check IDs and implementation revision to native results.
Preserve failed attempts and create a new run on retry; never repair a locator by
silently weakening the business assertion. Compare preparation, execution, waiting,
intervention and ongoing maintenance against the manual/AI alternative.

This change implements the optional work-plan validation and brief/Excel projection,
**not** a v2-to-Playwright/FlaUI compiler, universal executor or automatic optimizer.
Reuse the existing optional setup, fictional Playwright example and Result v1 adapter
contract. Actual project-specific automation and measured benefit remain subsequent
work with their own authorized environment and acceptance evidence.

## Result contract (version 1)

The optional procedure-based Human Work Plan v2 is a planning input, not a new
result schema. Preserve per-case native results after shared operations; use
`checks[].conditionId`, and `stepNo` when projecting into Excel. Keep operation ID,
procedure revision and the accepted requirement/specification reference in the
frozen plan/private execution record. A plan's required/delta/reuse trial choice
cannot assert execution, adopt evidence or establish PASS. Prepare specification-led
input/fixture/expected data for the next feature slice before implementation;
trial actual operations only when needed, then verify the consolidated plan.

Test tools retain their native JUnit/TRX/Playwright reports. To connect them to Feature Map, emit a compact `result.json` for each run:

| Field | Meaning |
| --- | --- |
| `schemaVersion`, `runId`, `timestamp` | Format, unique run and UTC time |
| `featureMap`, `useCaseId`, `verifyCaseId`, `testRef` | Existing durable navigation anchors |
| `runner`, `sourceRevision`, `environment`, `fixtureRef` | Actual execution identity and setup |
| `status` | `passed`, `failed`, `blocked`, `not-run` |
| `checks` | Named deterministic checks, retaining failed assertions |
| `expected`, `observed` | Bounded structured state comparisons |
| `evidence` | Relative paths to evidence files in a run directory |
| `limitations`, `error` | Excluded or unverified guarantees and blockers |

`passed` requires all required assertions in the **actual execution boundary**; `failed` means an observed assertion mismatch; `blocked` means a dependency, authorization, environment or expected-result issue stopped verification; `not-run` means execution was not attempted. A successful HTTP smoke is **not** evidence of UI typing or visual correctness.

## Excel functional-test handoff

For work that requires the standard Japanese functional-test workbook, see `functional-test-excel.md`. A `result.json` can be imported into the provided `test_template.xlsx` layout only when the revision and verify case match and a case step is associated with its actual evidence. Adding `stepNo` and step-specific `evidence` to applicable checks is optional: whole-run results remain in the original JSON and are not extrapolated to all Excel step cells. Keep Excel formulas and human judgments intact.

## Evidence/privacy/sandbox

When evidence must remain auditable, apply [Evidence Storage](evidence-storage.md)
at design, run finalization and handoff. Seal original files outside disposable
worktrees, register manifest hashes and condition-specific references in a private
catalog, and preserve gaps. File integrity and past PASS do not prove a current
test. Customer workbooks are separate sanitized projections of the execution record.

- PASS: save minimal checks, important DB differences and representative screenshots only when needed.
- FAIL/BLOCKED: also save bounded diagnostic logs, failure screenshot/trace when possible and the first blocking gate.
- Screenshots and traces may contain PII, credentials, tokens and private business records. Use synthetic data in public demos; apply redaction **before** storage or model transmission, restrict access and set retention. Never commit customer/production snapshots.
- Bind human acceptance to exact source revision and evidence run. A new revision requires a fresh verification decision.
- **Do not repurpose scripts/task_runner.py**: it uses Linux bubblewrap, protected test paths and no network. Browser/Windows/DB E2E execution needs a separately authorized isolated environment and its project-native runner. Preserve existing approvals, hook gates, test protections and HALT rules.

## Optional tool installation

For the fictional browser-to-SQLite example, use the source-controlled installer
`scripts/setup-ai-testing.py`, or the `.ps1` / `.sh` wrappers. It defaults to
Playwright Python (pinned in `scripts/requirements-ai-testing.txt`) and Chromium
in a dedicated `.venv-ai-testing`. A dry-run (`--dry-run`) previews commands;
`--check` verifies package/browser presence; `--smoke` executes the actual
browser/UI/DB scenario in an authorized isolated environment.

On Windows, `--windows-ui-project path/to/TestProject.csproj` optionally
adds pinned FlaUI.UIA3 only to that explicitly authorized test project.
`--with-xquery` optionally restores the existing pinned .NET local tool.
`--skip-web` skips Playwright when only .NET functionality is needed.
No package or service is mandatory for ordinary Feature Map use. Do not install
GUI tools into the existing Linux bubblewrap Task Runner. Do not auto-install
Python, .NET SDK, system OS libraries or privileged dependencies.

## Runnable example and rollout

See `examples/ai-assisted-testing/README.md`. The example reuses the existing fictional puzzle Feature Map IDs, launches a loopback-only Python app using fresh SQLite, verifies an HTTP registration and DB transition, and saves structured evidence. Its optional Playwright mode performs real input/click/screenshot/trace where a browser is installed. It uses no AI/API key and no customer data.

Adopt in phases: (1) use the map to plan minimal cases and oracles, (2) prove one repeated path with isolated fixtures and evidence, (3) add AI failure analysis or alternative UI adapters **only after measuring** end-to-end effort, intervention and maintenance against manual testing.
