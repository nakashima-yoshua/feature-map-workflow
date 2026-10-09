# Offline task-runner experiment

This fixture replays prewritten JSON proposals. It makes no model/API call and
does not claim to measure autonomous model quality. It proves the baseline,
failed correction, valid repair, fixed tests, source isolation and human-review
boundary with the same runner used for live opt-in work.

## Change Contract

The LOW-risk purpose is to repair `app.py:value` to return 2. Its existing test and
`INV-VALUE` are authoritative. Only `app.py` may change. API calls, publication,
test changes, privileges and production data are excluded. The source fixture
must remain unchanged. A successful candidate needs a human review; a failed
candidate cannot be approved by the agent.

Manual repair is the simpler alternative for this tiny defect. The runner is a
bounded experiment in evidence collection and retries, not a requirement to
automate simple work. Measure total accepted-delivery cost on real tasks before
adoption. No new queue or UI is justified by this fixture.

## Run

Requires Python, Git, `lxml`, Linux and a working `bwrap` installation. From the
plugin root, copy the fixture to a new directory and initialize its own repo:

```sh
cp -R examples/task-runner/fixture /tmp/feature-map-runner-demo
git -C /tmp/feature-map-runner-demo init
git -C /tmp/feature-map-runner-demo add .
git -C /tmp/feature-map-runner-demo -c user.name=Demo -c user.email=demo@localhost \
  commit -m 'Independent failing baseline'
python scripts/task_runner.py start --repo /tmp/feature-map-runner-demo \
  --config examples/task-runner/task.json --store /tmp/feature-map-runner-runs \
  --proposal examples/task-runner/proposal-bad.json \
  --proposal examples/task-runner/proposal-good.json
```

Expected: baseline failed, attempt 1 failed, attempt 2 passed, status
`HUMAN_REVIEW_REQUIRED`, review state `UNREVIEWED`. The source repo still returns 1;
the detached candidate returns 2. Inspect `state.json`, check logs,
`candidate.patch` and `human-review-request.json` under the printed run directory.
Commands exit 2 on HALT, 0 on a completed checkpoint/review request.

To exercise checkpoint resume, add `--pause-after 1` and supply only the bad
proposal to `start`, then:

```sh
python scripts/task_runner.py resume /tmp/feature-map-runner-runs/RUN_ID \
  --proposal examples/task-runner/proposal-good.json
```

Expected: the failed attempt remains in history and the baseline is not repeated.
See [the runner contract](../../skills/feature-map-workflow/references/autonomous-task-runner.md)
for MEDIUM prior approval, exact-revision review and human-requested rework.
