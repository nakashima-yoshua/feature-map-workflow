# Autonomous Task Runner

The opt-in runner in `scripts/task_runner.py` handles one automatically evaluable
task. It fixes a baseline, applies bounded proposals, runs approved checks, and
preserves evidence for a human. See [Issue #8](https://github.com/nakashima-yoshua/feature-map-workflow/issues/8).
No queue, database, multiple agents, or new XML schema is introduced.

## Phase 0: accountability and connection contract

Canonical business goals, Capability/Requirement/Rule/Invariant IDs, design
decisions, acceptance, and risk acceptance belong to humans and their existing
[System Understanding Architecture](https://github.com/nakashima-yoshua/system-understanding-architecture)
documents. A task's `contract_ref` links the existing Change Contract or approved
Issue; use existing stable IDs in `invariants` and `acceptance`. Do not copy whole
requirements into a second specification.

| Asset | Responsibility |
| --- | --- |
| Existing Change Contract / requirements / ADR | Human-defined purpose, scope, rules, risk and authorization |
| Feature Map 1.3 | Durable goal, boundaries, navigation, knowledge and representative verification |
| Source / existing tests | Implementation and executable expected behavior |
| Git / CI | Exact revisions and shared validation evidence |
| Runner config | Approved exact paths, argv arrays, budgets and references |
| Run directory outside the repository | Checkpoints, failed attempts, logs, candidate patch and review request |
| Human review operation | Decision bound to an exact revision and evidence reference |

`config.json` is an immutable snapshot for that run. SHA-256 binds the config,
runner implementation and existing XSD; changing any of them requires a new run.
Evaluation commands and protected paths cannot be changed by a proposal. Only
the host runner applies validated `changes[{path,content}]` data to its detached
worktree; paths are exact files, not wildcards. The original checkout stays intact.

| Risk | Before execution | After successful checks |
| --- | --- | --- |
| LOW | Human-authored scope and acceptance | Lightweight human review |
| MEDIUM | Human Contract approval matching config hash and starting revision | Human implementation review |
| HIGH | HALT in this MVP; use prior design approval and an independent verification/review process | High-risk human review outside this runner |
| CRITICAL / unknown | HALT; human-led process | Not an autonomous task |

A MEDIUM prior approval is supplied separately from the model's proposal:

```json
{
  "decision": "approved",
  "reviewer": "responsible-human",
  "revision": "<starting-full-Git-SHA>",
  "config_hash": "<task_runner.digest(config)>",
  "evidence_ref": "<existing-Contract-review-reference>"
}
```

The operator must keep the runner, approval inputs and run store outside model
write access. Reviewer names are audit metadata, not identity authentication.
Human review CLI access must be reserved to the responsible human using host
permissions or the existing PR review process; this MVP is not an approval server.
Repository Rulesets and merge/deployment permissions remain separately configured.

The final `human-review-request.json` follows this order: business purpose and
exclusions; invariants; data/contracts/side effects; migration/failure/recovery;
test evidence and limits; high-risk differences; unresolved items; requested human
decision. It separates `CONFIRMED`, `INFERRED`, `UNVERIFIED`, `HUMAN_DECISION` and
references the exact candidate commit, environment, commands, logs and patch.

`HUMAN_REVIEW_REQUIRED` means self-check completed. It never means approved,
mergeable or release-ready. `review_state` is separate and supports APPROVED,
CONDITIONAL, CHANGES_REQUESTED, REJECTED and DEFERRED. Revisions/evidence changed
after review invalidate the decision. No runner command pushes, merges or deploys.

### Required acceptance examples

| Scenario | Observable outcome |
| --- | --- |
| LOW fix with existing tests | Baseline recorded, approved path changed, checks pass, human review required |
| MEDIUM without matching approval | HALT before model/evaluator execution |
| HIGH / CRITICAL / unclear risk | HALT for the independent human-led process |
| Out-of-scope path or fake APPROVED in proposal | Entire proposal rejected before the first file write |
| Failing check | Failed evidence retained; bounded retry or HALT, never completion |
| Revision changed after approval | Review invalidated, no old approval reused |
| Human requests rework | Explicit new run linked to the request, fresh evidence and human review |

### YAGNI and whole-system adoption

Use existing Issue/PR/Contract fields when needed for purpose, constraint evidence,
outcome metric, the smallest intervention (including no change), protected
conditions, adoption and withdrawal. An optional `optimization` object can link
these facts; it has no authorization effect and is not a new required form.

* Unknown constraint: measure or defer; do not launch a large automated change.
* Minor, obvious fix: existing purpose, acceptance and invariants suffice.
* Faster generation with a longer review queue: judge total accepted-delivery time.
* Faster candidate violating an invariant: failing mandatory checks reject it.
* Missing required approval: HALT regardless of measured improvement.

Compare a representative task against manual Codex + Hooks before expanding use.
Track intervention count, total delivery/review time, defects and rework in the
existing Issue/PR. Recorded run times and success rates are not proof of business
benefit. Token usage is recorded only if Codex reports it; costs remain unknown
without billing evidence. Phase 4 is deliberately deferred until measurements
justify coordination or additional infrastructure.

## Execution and privacy boundaries

1. Start from a clean checkout and an approved config; create a detached Git
   worktree and a private run directory outside the source repository.
2. Check risk/approval, source revision, XML/XSD, high-impact Open items and any
   non-passed Feature Map verification cases before executing affected work.
3. Probe Linux bubblewrap isolation. If unavailable, HALT; no unsafe fallback.
4. Execute baseline checks with the same fixed argv arrays used for candidates.
5. Get a JSON proposal; validate every path/type/size before any write.
6. Evaluate with a read-only worktree, private temporary directory, isolated
   processes/network, cleared environment, no host HOME and hidden Git metadata.
7. Accept only a passing candidate (and a strictly improved numeric metric if
   configured); preserve its local commit and patch for review. A passing unchanged
   baseline may produce `NO_CHANGE`. There is no automatic publication.

The configured commands are human-approved executable code. Do not allow changes
to helpers, fixtures, configuration or dependencies that define expected results;
identify them in `protected_paths` and omit them from `allowed_paths`. All test-like
paths and the referenced Feature Map are protected. This MVP freezes Feature Map
updates during attempts; apply any durable knowledge delta afterwards through the
existing Skill/Hooks/xquery-mcp workflow. Hooks are not replaced or weakened.
Tests may still have blind spots: a passed candidate always needs human review.

The evaluator mounts only system runtimes, the worktree, `/proc` for isolated
processes, synthetic `/dev`, and temporary storage. `runtime_ro` optionally grants
read-only access to specific installed SDK locations. There are no writable source
mounts, network interfaces to the host, inherited credentials or access to the
source repository Git directory. Commands requiring a network, writable project
build outputs or other services must be adapted to temporary outputs or remain
outside this MVP. Do not enable privileged containers to bypass this boundary.

The default offline `--proposal` path replays JSON data from a prior human/Codex
session and never invokes a model or runs commands embedded in the proposal.
Without `--proposal`, the optional Codex broker requires both
`external_input_allowed: true` and the reviewed `codex_version` value
`codex-cli 0.159.0-alpha.3`. Version mismatch HALTs. The broker executes `codex exec`
read-only in a separate empty directory with fresh CODEX_HOME, no project/user
configuration, no plugins/MCP, disabled shell, exec, apps, browsing, image,
computer-use, multiple-agent and hook capabilities, no approvals, and a fixed
output schema. It receives only explicit `read_paths` text plus bounded task
context; it cannot directly edit the worktree or review store. Existing task
implementation/hooks remain in the normal developer session; the broker only
proposes edits. See the official [non-interactive CLI guide](https://developers.openai.com/codex/noninteractive).

The broker inherits an existing `OPENAI_API_KEY` only for its own API authentication;
it does not create, store or print keys. Configure network egress to approved model
endpoints in the host environment and review source data before opt-in. No real
Codex/API request is made by repository tests. Logs are bounded and redact known
credential patterns, environment secrets and emails; that is defense in depth,
not comprehensive DLP. Do not put secrets or personal data in an input repository,
config or proposal. Credential-like filenames and obvious secret content are
rejected. Live quality, billing and model accuracy require a separately authorized
smoke test.

## Limits, restart and human operations

`max_attempts`, `max_seconds` and `command_seconds` are fixed positive budgets.
Wall time includes downtime. Commands have output limits and timeouts; process
groups are terminated on timeout/overflow. Repeated identical failed proposals
HALT. Failures distinguish implementation, specification, environment, permission,
evaluation-unavailable, repository-conflict and budget categories.

State is atomically saved before potentially interrupted work and after verified
checkpoints. Completed attempts retain commands, results, logs and patch evidence.
Failed modifications are reset only inside the runner-owned worktree, never the
source checkout. Resume checks config/implementation/XSD hashes, revisions,
worktree cleanliness, evidence hashes and remaining budget. A safe checkpoint
resumes with the next attempt and does not rerun the baseline. An in-flight crash
HALTs for inspection instead of replaying an unknown side effect. Completed runs
are idempotent when resumed. An exclusive OS file lock prevents concurrent writers.

```sh
python scripts/task_runner.py start --repo /path/to/clean-repo \
  --config /path/to/approved-task.json --store /path/outside/repo/runs \
  --proposal /path/to/proposal.json
python scripts/task_runner.py status /path/to/runs/RUN_ID
python scripts/task_runner.py resume /path/to/runs/RUN_ID --proposal /path/to/next-proposal.json
python scripts/task_runner.py review /path/to/runs/RUN_ID \
  --reviewer responsible-human --revision EXACT_CANDIDATE_SHA \
  --decision CHANGES_REQUESTED --evidence-ref 'existing-PR-review-reference'
python scripts/task_runner.py retry /path/to/runs/RUN_ID \
  --store /path/outside/repo/runs --feedback-ref 'existing-PR-review-reference' \
  --proposal /path/to/revised-proposal.json
```

`retry` requires a human change request on the unchanged reviewed revision. It
creates a new run and worktree from the current clean source checkout, links the
feedback, rechecks the baseline and does not carry over the previous approval.
Supply `--config` for newly approved criteria and `--approval` for MEDIUM tasks.
Terminal HALTs are not automatically unlocked; inspect evidence and create a new
approved run. Keep run evidence while review is pending. Remove worktrees using
`git worktree remove` only after the responsible human has retained needed artifacts.

The runnable offline example is in `examples/task-runner/README.md`. Run
`python scripts/test_task_runner.py`; on supported Linux also set
`REQUIRE_RUNNER_SANDBOX=1` to make actual OS isolation checks mandatory.
