# AI-assisted testing integration: fictional runnable example

This example **does not call an AI model**. It demonstrates how AI-planned,
project-native tests can connect to the existing fictional puzzle Feature Map,
produce repeatable DB assertions and export evidence. All IDs, names and data
are fictional and unrelated to actual customer systems.

## Test boundary

- Feature Map: `../fictional-puzzle-log/feature-map.xml`
- Existing anchors: `UC-REGISTER` and `TEST-REGISTER`
- Entry: browser UI (optional) or HTTP form submission (offline CI smoke)
- Real: local Python Web server and fresh isolated SQLite database
- Prerequisite: puzzle_catalog contains `PZ-001`; puzzle_record initially empty
- Expected: registration says Registered; exactly one `pending` record is inserted
- Reset: a new database and directory per execution
- Excluded: real Oracle, Windows UI, SAP, production data, external connections

## Run offline (Python standard library)

From repository root:

~~~sh
python examples/ai-assisted-testing/run_demo.py --engine http
python -m unittest discover -s examples/ai-assisted-testing -p test_demo.py -v
~~~

Each run prints a unique path to `result.json` under the OS temp directory.
The offline test checks PASS, deliberate FAIL, new isolated run, and missing
Feature Map anchors. To inspect results in a designated directory:

~~~sh
python examples/ai-assisted-testing/run_demo.py --engine http --output ./local-test-evidence
~~~

A deliberately wrong oracle should exit 1 and report `failed` without
changing the application or the previously approved default oracle:

~~~sh
python examples/ai-assisted-testing/run_demo.py --engine http --expected-name WRONG
~~~

## Optional real browser execution

Requires the optional Playwright Python package and Chromium, installed in an
**approved test environment**:

~~~sh
python -m pip install playwright
python -m playwright install chromium
python examples/ai-assisted-testing/run_demo.py --engine browser
~~~

An existing approved Chromium installation may be selected through
`PLAYWRIGHT_CHROMIUM_EXECUTABLE`. If the browser is unavailable or its loopback
connection is blocked by the environment, `result.json` records `blocked`
plus `error.log`. Do not bypass environment/network policy.

In browser mode the runner fills the two fields and clicks Register, then
captures `screenshots/01-input.png`, `screenshots/02-result.png`, `trace.zip`,
console logs and DB before/after/diff. **HTTP mode is not a UI test and does
not claim screenshots or traces.**

## Evidence

Each run writes `result.json`, `before.json`, `after.json`, `diff.json`,
`operation.log` and a synthetic `fixture.sqlite3`. Browser runs also capture
screenshots and trace if available. The normalized result includes original
Feature Map IDs, revision, runner, environment, fixture, status, assertions,
expected/observed data, diagnostic error and evidence paths.

The temporary results are not an alternative Feature Map specification.
Do not promote transient run counts/statuses into Feature Map XML, and never
commit real customer data or traces containing credentials.

## Adapting to an existing system

Choose one approved scenario and business expectation from Feature Map;
explore only the dependencies needed to reach the target; use isolated synthetic
fixtures; generate test code for the project-native runner; and retain a
version-bound result with screen/log/DB evidence. Keep UI/E2E flows few and
business significant, moving ordinary condition/boundary coverage to cheaper
service/DB tests. See
`skills/feature-map-workflow/references/ai-assisted-testing.md`.
