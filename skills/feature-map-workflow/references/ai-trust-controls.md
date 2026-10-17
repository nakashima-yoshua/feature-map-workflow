# AI trust boundaries and seven safety acceptance principles

## Scope and authority

This is a set of **acceptance criteria for the existing Feature Map Workflow**, not a
second control plane or a new agent framework. Treat generated proposals, model
judgments, retrieved documents, repository contents, and test output as untrusted
inputs. Only the host-controlled Task Runner, fixed tests, repository permissions,
and an authenticated human reviewer may authorize effects.

- **Model / Decision Provider:** propose, classify, explain. Never establish
  permissions, approve a change, disable a gate, or mark their own output accepted.
  An optional second model can help with a consequential ambiguous judgment,
  but model consensus is not a substitute for deterministic checks or human review.
- **Codex Hooks:** advisory context and development completion checks. Hooks alone
  are not an OS security boundary and must not be described as enforcing access.
- **Task Runner / host:** enforce exact paths, approved commands, isolation,
  fixed budgets, HALT, evidence integrity and the separation of review and execution.
  Code/settings/run store/approval inputs must be outside model write permission.
- **Git / CI / human:** retain independently inspectable revisions, mandatory tests
  and review decisions. Configure repository Rulesets and authenticated write/merge
  rights in the host; an actor name in JSON is not authentication.

Do not change Feature Map XML/XSD or introduce audit databases, queues, required
multimodel voting, or new always-on services for this policy.

## Acceptance matrix

| Principle | Existing mechanism | Required acceptance observation | Limitation / dependency |
| --- | --- | --- | --- |
| 1. Model diversity | Optional OpenAI / Jev / off behind DecisionProvider | A failed, disputed or unavailable provider cannot override deterministic gates; escalate consequential ambiguity to an independent reviewer | Multiple models are optional, not a required per-task cost |
| 2. Observable operations | Run IDs, exact revisions, saved logs/patches, evidence hashes, Git/CI | An independent reviewer can identify the evaluated revision, test inputs, results and HALT reason, and detect altered run evidence against a separately retained anchor | Local hashes alone do not prevent an actor with write access from rewriting both evidence and hashes; see independent anchoring |
| 3. Testability | XSD, fixed checks, CI, negative tests | Wrong paths, forged approval, failed checks, modified evidence, unavailable sandbox and operator stop all fail safely | Passing tests do not prove business correctness; Issue #18 validates a real model end-to-end |
| 4. Independent controls | Fixed Runner configuration and OS sandbox | Model proposals cannot edit checks, protected paths, privileges or authorizations; OS permissions exclude the model from policy inputs | Runtime and host identity/permissions require Issue #13 and #17 sign-off |
| 5. Independent audit | Human Review Request and revision-bound review | Self-check stops at HUMAN_REVIEW_REQUIRED; the human reads the exact candidate and verified evidence before approval | Host authentication and PR protection still need configuration and testing |
| 6. Containment | bubblewrap evaluator, budgets, HALT | Operator can request stop without acquiring the run lock; running model/evaluator command polls the stop request and terminates its process group; further work must not reach human-review-ready state | An uninterruptible host operation, escaped descendants or process crash may require host-level kill/revocation and manual inspection |
| 7. Incident disclosure | SECURITY.md private reporting channel | Operators can contain, preserve minimal evidence outside the model's control, assess exposure, notify maintainers privately and decide on a suitable disclosure | Do not send live keys, source, personal data or raw logs into public issues |

## Operator stop (host-only, opt-in Task Runner)

Issue a stop from an account that has OS access to the private run directory,
**not from model-provided input**. The stop marker is an exclusive 0600 file.
The command does not acquire `run.lock`, so an executing runner can observe it.

```sh
python scripts/task_runner.py stop /path/outside/repo/runs/RUN_ID
python scripts/task_runner.py status /path/outside/repo/runs/RUN_ID
```

`stop` is a **request**, not an acknowledgement that all processes have ended.
The runner checks before work, between phases, and while waiting for broker or
evaluator process output. A detected request raises `operator_stop`, kills the
process group for that command, records `HALT` and preserves inspection evidence.
The marker remains in place; `resume` must not silently unlock a stopped run.
A completed run is not retroactively stopped. A run caught after a crash may
need process and evidence inspection; never assume automatic rollback.

If the runner/host does not respond, the operator must use host process management,
disconnect external credentials/network if necessary, then inspect the source,
run store, worktree and remote state before initiating **a new approved run**.
This CLI is not a daemon or a substitute for OS-level emergency controls.

## Independent evidence anchoring

The existing `state.json` includes hashes of evaluator logs, patches and model
proposals. The new `evidence_anchor` is a compact digest of the run identity,
source/candidate revision, approved config and evaluator fingerprints, and the
saved evidence-hash list. It is a **tamper-detection anchor**, not a signature,
identity proof or write-once audit log.

After the run reaches `HUMAN_REVIEW_REQUIRED` or `NO_CHANGE`, obtain the anchor
and retain it in an independently permission-controlled place (for example,
a protected CI artifact, access-controlled review record, or human-controlled
signed note), **not only within the run directory**:

```sh
python scripts/task_runner.py verify /path/outside/repo/runs/RUN_ID
python scripts/task_runner.py verify /path/outside/repo/runs/RUN_ID --expected-anchor TRUSTED_ANCHOR
```

The second command checks both the independently retained anchor and the
already-existing per-file hashes and exact local review target revision. A mismatch
invalidates review and HALTs; do not approve or publish. Do not equate a matching
anchor with business correctness, a trusted test definition, or adequate protection
against malicious host administrators. Independent retention and GitHub host
permissions are operational prerequisites, not automatically created here.
The initial anchor must itself be collected from a trusted run after checking the
approved config/environment and must be protected from the model.

## Threat-driven acceptance tests

Use the existing `scripts/test_task_runner.py` and CI workflow:
- Non-approved MEDIUM, HIGH/CRITICAL, forged approval and out-of-scope paths are rejected.
- Unavailable Linux isolation, stale revisions, failing or modified checks HALT.
- Operator stop before execution does not call the model/evaluator.
- Stop during a long-running process interrupts it and requests group termination.
- Stop after a passing candidate check prevents adoption or self-approval.
- Resealing altered local evidence fails when compared with an independently saved anchor.
- An ordinary passing candidate still requires a human decision on the exact revision.

Also manually rehearse a stop and the independent anchor comparison in the actual
host environment before enabling use. Keep synthetic or approved test data in CI.

## Release boundary and known gaps

A merged feature is **not a release approval**. These tracking records describe
acceptance concerns; an Issue's closure is not evidence that its checks passed:
- #13–#17: independent approval, evidence coverage, input/runtime budgets and OS permissions;
- #18: actual Codex-to-Runner end-to-end evidence;
- #20: HALT/recovery and evidence-retention drill;
- #21–#22: efficiency comparison, release acceptance and withdrawal.

In particular, #14's candidate-diff completeness / NO_CHANGE problems and #16's
runtime fingerprint concerns are not fixed by an emergency stop or evidence anchor.
Treat these as release blockers until separately tested and accepted on the
actual release candidate. Check linked changes and evidence rather than inferring
readiness from Issue status. Follow
`SECURITY.md` for private incident handling; never put sensitive exploits or
real customer information in a public review or CI log.
