# Human Work Direction and Focused Verification Brief

## Goal

Human time is a constrained resource. Before asking a person to verify a feature, batch compatible checks into **few, safe human sessions** and supply a **feature-focused understanding brief**. Share setup, not case-specific starting state, oracle, evidence or status. Test scripts/results stay canonical; Feature Map XML remains the durable knowledge index. The brief and human session plan are derived artifacts, not a second specification or evidence of test execution.

Use this as an **optional conditional planning gate** after test boundaries are established and before human verification or acceptance. Skip the overhead when there is one trivial action.

## Diagram selection: no three-diagram limit

Select existing, evidence-backed diagrams for the current question, without a
quota. Use [Diagram Selection](diagram-selection.md) only when choosing views.
The generator does not invent relationships; a JOIN does not prove a physical FK.
Keep diagrams in per-feature XML and human HTML, not a global content collection.

## Session batching procedure

Before batching, reduce both cases and their input conditions to changed program
guarantees and significant affected regression using [Test Strategy](test-strategy.md#select-changed-behavior-before-selecting-cases).
Consolidating all old cases without reviewing their value merely makes an oversized
plan easier to execute. Separate environment readiness from functional judgments;
reuse existing accepted evidence instead of opening another human session. If
setup/locator repair repeatedly produces no functional evidence, stop at the
planned review point and choose a working environment, narrower sufficient
boundary or explicit blocker. Do not extend free-form UI exploration indefinitely.

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

Use [Human Work Plan v2](human-work-plan-v2.md) only for reusable operations and
separately traceable checkpoints. It owns the trial, procedure, dependency,
reset/restart, formal-result mapping and measurement contract. v1 and Result v1
remain compatible; trivial actions need no v2 plan.

## Excel evidence handoff

When a customer or human reviewer needs the standard functional-test workbook, generate it with `scripts/build_functional_test_excel.py` and the locally provided `test_template.xlsx`, following `functional-test-excel.md`. Human Work Plan groups setup and manual actions; **FT-xx** sheets keep per-case plans and independent evidence. Keep `verifyCaseId` and sourceRevision links, and never infer approval from a draft session plan.

## Code-review handoff: one focused decision package

Use [Code Review](code-review.md#human-review-brief-in-the-pr-description-or-review-reply)
for the revision-bound human decision packet. Do not duplicate it in another plan.

## Human efficiency metrics

Measure human sessions, hands-on minutes, setup switches, interruptions/retries and end-to-end time alongside individually verified/blocked case counts. Optimize these jointly: a faster batch that destroys test independence or delays an urgent release is **not** a success. Do not save work plans or results as repeated XML prose, and do not commit customer screenshots or production data.

## AI tool context from canonical data

FMW HTML is human-facing output only. Do not feed it into a model or parse it to
retrieve cases, operations, state or evidence. This does not prohibit ordinary
web UI testing or markup/rendering checks of generated human output.

For bounded AI/tool reads, query XML through XPath/XQuery/PTC or emit JSON directly:

    python skills/feature-map-workflow/scripts/build_verification_brief.py --feature-map examples/fictional-stock-request/feature-map.xml --use-case UC-SUBMIT --case V-SUBMIT --plan examples/fictional-stock-request/human-work-plan.v2.example.json --format json

JSON goes to stdout without creating HTML. It preserves global invariants,
constraints and all open items, plus complete touched sessions (including other
cases, dependencies/reset/recovery). It validates the complete supplied v1/v2 plan,
keeps only used procedure snapshots, and identifies selected vs related cases.
Version 1 JSON includes catalog/omitted counts and historical status counts; omitted
failed/blocked case IDs remain visible for investigation. Hashes bind the exact parsed XML/JSON;
recorded statuses are historical map
records, never a current execution or approval. Native results/evidence remain
canonical. Use explicit case IDs to avoid selecting every case by default.
HTML-only output, CDN, force and diagram flags are rejected for JSON.
