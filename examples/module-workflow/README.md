# Offline module workflow example

This fictional Python example exercises the optional serial Docker workflow.
It never contacts a model, DB, customer system or repository remote.

The protected specification says `value()` must return integer `2`; baseline code
returns `1`. Recorded JSON stands in for two AI proposals: a requirements summary
and the code repair. Fixed commands then parse/build the source, observe the actual
behavior, verify real container isolation and generate a two-file candidate ZIP.
Successful execution ends at `HUMAN_REVIEW_REQUIRED`; nothing is sent or approved.

See [the runtime guide](../../skills/feature-map-workflow/references/module-workflow.md)
for Ubuntu prerequisites, the one-file configuration contract and recovery.

From a clean committed checkout, with an external private evidence store:

```sh
python3 scripts/workflow_compose.py start --repo . \
  --config examples/module-workflow/workflow.json \
  --store "$HOME/.local/share/fmw/runs"
```

For automated integration verification:

```sh
python3 scripts/test_workflow_orchestrator.py
python3 scripts/test_workflow_compose.py --store "$HOME/.local/share/fmw/compose-tests"
```

The second command runs real Compose twice: a successful candidate and a deliberately
omitted repair whose independent expectation fails. It checks that failure evidence
survives, dependent packaging stays not-run, original source stays unchanged, source
mounts are read-only, Build cannot access control state/other worker results/model
credentials/Docker socket, and Build has no external network. Run directories are
retained at the supplied store; only this test's containers are removed.

The result files are native synthetic observations, not invented customer test
records. Live Codex, actual .NET builds, real DB/UI behavior, host deployment and
customer acceptance require separate evidence; see the guide's explicit opt-ins.
