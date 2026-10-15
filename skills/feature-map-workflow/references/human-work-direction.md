# Human Work Direction and Focused Verification Brief

## Goal

Human time is a constrained resource. Before asking a person to verify a feature, batch compatible checks into **few, safe human sessions** and supply a **feature-focused understanding brief**. Share setup, not case-specific starting state, oracle, evidence or status. Test scripts/results stay canonical; Feature Map XML remains the durable knowledge index. The brief and human session plan are derived artifacts, not a second specification or evidence of test execution.

Use this as an **optional conditional planning gate** after test boundaries are established and before human verification or acceptance. Skip the overhead when there is one trivial action.

## Diagram selection: no three-diagram limit

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

## Human efficiency metrics

Measure human sessions, hands-on minutes, setup switches, interruptions/retries and end-to-end time alongside individually verified/blocked case counts. Optimize these jointly: a faster batch that destroys test independence or delays an urgent release is **not** a success. Do not save work plans or results as repeated XML prose, and do not commit customer screenshots or production data.
