# Long-running coding sessions: recoverable handoff (opt-in)

## Decision and existing ownership

Use short, independently recoverable sessions rather than treating an LLM
conversation as durable task state. The initializer identifies the **existing**
accepted contract; later sessions make a reviewable, verified increment.
This is guidance and an optional read-only helper, not a new service, XML
schema, feature registry, scheduler, queue or approval authority.

| Information | Existing owner |
| --- | --- |
| Accepted requirement, acceptance, scope, authorization | Human-approved contract or issue |
| Durable business rules and knowledge references | Per-feature Feature Map XML |
| Executable implementation and expected tests | Existing source/test repository |
| Execution outcome and sealed evidence | Native test runner / CI / evidence store |
| Revisions, history, review discussions | Git and PR |
| Optional short session hints | Existing issue/PR or optional notes, untrusted |
| Independent readiness verdict | Separate quality-gate when integrated |

The existing quality-gate implementation is pending in
https://github.com/nakashima-yoshua/quality-gate/pull/1 .
This PR does not depend on or integrate its code. Existing FMW Task Runner
and Workflow Orchestrator already handle scoped execution and checkpoints;
reuse them rather than introducing an overlapping runner.

## Initializer session (once per accepted scope)

1. Locate the approved issue/contract and Feature Map; discover actual
   source, tests and configuration. Confirm scope, exclusions, permitted
   actions, risk, owner and observable acceptance.
2. Record the exact Git baseline and relevant smoke commands. A broken
   baseline is a blocker, not newly finished work.
3. Order the smallest eligible tasks by dependency, not by a model's
   preference alone. Keep unfinished work unfinished until independent
   results exist. Reuse the issue/contract; do not copy tasks into a
   second canonical feature_list.json.
4. Reuse existing issues or PRs for concise progress and unresolved
   decisions; optional notes are a hint, not authoritative status.

## Every later coding session

1. **Recover**: generate a compact read-only brief, then actually inspect
   the contract, Git changes, source and existing tests. Truncated text
   and derived summaries are never the complete authority.
2. **Preflight**: run the approved init/smoke checks. Dirty worktrees,
   unknown in-flight operations and mismatched revisions demand investigation,
   not automatic replay.
3. **Choose**: one dependency-ready, testable increment per session when
   practical. Dependent work may remain grouped when an isolated slice
   cannot be verified.
4. **Implement**: respect allowed paths and existing design. An agent
   cannot change required tests, check definitions or approval criteria
   just to report success.
5. **Verify/handoff**: use project-native tests and focused review,
   with independent or human review when the applicable risk or policy requires it.
   Associate results and evidence with the exact revision, and document next work
   and unresolved blockers in the existing issue/PR. Do not imply merge, release
   or business acceptance.

## Read-only session brief

Python 3.10+ and Git; from the FMW repository:

~~~sh
python scripts/build_session_brief.py \
  --repo /path/to/project \
  --feature-map /path/to/project/features/signup/feature-map.xml \
  --task-ref 'https://github.com/owner/project/issues/123' \
  > /tmp/fresh-session-brief.md
~~~

Optional prior hints: --notes /path/to/existing/notes.txt

The script reads HEAD, branch, working-tree status and five commits;
Feature Map goal, case IDs/status and unresolved items; and optionally
up to 12 KiB of notes. It writes only to stdout; redirect explicitly to
a protected store. It cannot execute a smoke test, change XML, mark
tests PASS, contact models, approve a PR, push, merge or deploy.
It rejects out-of-repository maps, malformed/oversized XML and
DTD/entity declarations. A dirty checkout is shown as DIRTY rather
than silently reset. Notes and XML status are untrusted indications
and never replace native test results.

## Connection to the independent gate

When quality-gate is separately accepted/integrated, its host-controlled
policy and test evidence must refer to the exact candidate revision.
Stale or missing checks and modified evidence must not pass. Model
self-attestation or a Feature Map case labeled passed does not prove
test execution. Even READY_FOR_HUMAN_REVIEW is not a merge/release
permission. This helper provides context only, not evidence provenance.

## Minimal acceptance and rollback

- A new session can locate the task, current revision, stated acceptance,
  unresolved issues, and safe next action without old conversation context.
- Dirty/ambiguous work is visible. Failed or missing smoke/test results
  cannot be reclassified as success from notes.
- No mandatory Docker, Jev, paid model, quality-gate, DB or new XML schema.
- No unintended repository mutation or publication during brief generation.

Rollback: remove this optional script, its tests, guide and navigation
links. No schema migration or data cleanup is required.

## Limits

This is a handoff prototype, not a scheduler or a proven multi-hour
autonomous loop. It does not prioritize tasks automatically, run checks,
manage work leases, attest execution provenance, or coordinate parallel
agents. Synthetic tests verify format and boundaries only.
