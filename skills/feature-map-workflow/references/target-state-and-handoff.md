# Target State, Progressive Refinement, and Reusable Handoff

## Purpose

Work backwards from the **state that must exist after the task**, not from a
fixed list of documents or phases. The target includes the usable deliverable,
its accepted behavior and evidence, the maintainable repository and operating
state, and a clear starting point for the next authorized change. This is a
cross-phase working rule for both `catchup` and `change`, not a new mandatory
phase, Feature Map schema, execution engine, or approval authority.

Distinguish three boundaries:

1. **Delivery-ready**: the agreed candidate and required evidence are available.
2. **Accepted/closed**: the authorized recipient has actually accepted it where
   acceptance is required, and the remaining risks have a documented disposition.
3. **Continuation-ready**: someone with no access to the previous conversation
   can locate the baseline, reproduce relevant checks, understand remaining work,
   and begin the next *authorized* task without reconstructing the project.

These are independent assertions. A PR, tag, document or successful CI run does
not establish customer acceptance, deployment, successful recovery or continuation
readiness by itself.

## Start with the target, then refine it

Describe the target using the smallest useful set of facts; reuse the current
requirement, task/issue, Feature Map `goal/done`, project conventions and CI.
Do not require a separate target-state file for every feature.

| Stage | Refine the *same* target into | Do not prematurely assert |
| --- | --- | --- |
| Request / requirements (phases 1-2) | Purpose, user outcome, scope/exclusions, observable acceptance, downstream owner and continuation needs | File names, implementation technology or an unapproved business expectation |
| Specification / scenarios (phases 2, 4-5, 7-8) | Behavior, inputs, outputs, boundaries, exceptions, test oracles and required evidence | Passing tests or a design derived solely from current code |
| Basic design (phase 3) | Logical components, interfaces, data ownership, dependencies, likely existing-repository locations | A new folder hierarchy merely for appearance |
| Detailed design (phase 6) | Physical source/test/config locations **where needed**, change boundaries, failure/transaction behavior and checks | A compulsory file per requirement or an immutable initial design |
| Implementation / verification (phase 9) | Actual paths, revisions, observed results and remaining gaps; revise the target only when the agreed requirement changes | Treating an existing file or green process exit as functional proof |
| Release / as-built / delivery (phases 10-12) | Exact package/baseline, checks and references, operating/recovery context, handoff and next-task entry point | Merge, deployment, sending or acceptance without the required authority |

Refinement is not a one-way waterfall. New evidence may invalidate an assumption:
update the **existing** requirement/decision and its dependent target references,
re-evaluate affected work, and preserve the old verified baseline. Keep identity
stable for traceability; do not multiply documents or copy the same specification
into separate phase artifacts. If a target detail is unknown, label it unknown
with the cheapest decision or observation needed.

## Target versus current state

For each requested scope, compare target to the current repository and evidence:

- **Already satisfied**: cite the exact source, test, revision or evidence;
  reuse it only if the acceptance basis and applicability still match.
- **Missing or inconsistent**: identify the smallest change and its necessary
  predecessors; check expensive assumptions before producing downstream files.
- **Not required**: omit the artifact or step and note the reason only when
  omission is material to review, safety or acceptance.
- **Blocked or unknown**: keep the gap visible, identify owner/next check, and
  stop only affected work when its progression would be unsafe or misleading.

Use the dependency graph to order only necessary work. Recheck the target after
each meaningful change; avoid a final mass filing/reorganization pass. Temporary
prototypes, downloaded references and trial results may be discarded under the
applicable retention/authorization rules. Never silently discard original
evidence or unpublished work.

## Artifact locations and Git repository shape

Start from existing project conventions, build/test tooling and owning modules.
Choose logical deliverable ownership before physical paths. Prefer a cohesive
product/system repository that survives individual assignments; associate each
assignment with issues, change branches and PRs instead of cloning a new repository
per ticket. Multi-repository or monorepo boundaries require a concrete ownership,
release or dependency reason.

- **During requirements:** identify logical outputs and acceptance; do not
  fabricate `src/`, `docs/` or `tests/` directories before learning the project.
- **During design:** map each output to its *existing* source, test, specification
  or evidence owner; identify proposed new paths only where necessary.
- **During implementation:** mutate only authorized paths. No unrelated moves,
  bulk renames, history rewrites, forced cleanups or repository-wide migrations.
- **At handoff:** identify the exact baseline commit (and release artifact/tag if
  actually created), change/PR disposition, required check outcomes, outstanding
  issues or branches with owner/next action, entry-point README/build instructions,
  and private evidence/backup references when required.

Check Git facts using read-only native commands and remote state as needed:
`git status --porcelain`, `git log -1`, branch/PR status and CI runs. A clean
working tree does not prove all necessary changes were committed or pushed.
Do not require every branch to be deleted or every issue to be closed; retained
work must be explainable and reachable. Never merge, tag, delete branches, deploy
or push as a side effect of an inspection. Follow the existing human authorization
boundary for such actions. Raw customer evidence, secrets, private run stores
and temporary build output remain outside the repository unless explicitly
approved and safe.

## Optional target-state index

For large or multi-output work with meaningful cross-phase dependencies, keep
a compact *index* in the project's existing task/configuration area. The following
is **illustrative JSON, not a required schema and not an executable verifier**:

```json
{
  "target": "Authorized inventory inquiry change",
  "scopeRef": "issue-or-agreed-spec-ref",
  "outputs": [
    {
      "id": "A1",
      "purpose": "Observable inventory lookup",
      "owner": "existing source/test modules",
      "path": null,
      "acceptanceRef": "approved requirement or test oracle",
      "evidenceRef": null
    }
  ],
  "closure": {
    "baseline": null,
    "handoffRef": "existing README or issue",
    "remainingRef": "existing issue or decision record"
  }
}
```

As understanding improves, resolve `path` to actual files and `evidenceRef`
to actual revision-bound observations. `null` means unknown/not yet established,
never "passed". A generated output or release manifest may already supply this
index: reference it instead of creating another file. Do not overwrite execution
manifests, accepted specifications, CI records or the private evidence catalog.
If no independent index improves discovery, use the task/PR and `goal/done` alone.

## Closure and next-task check

Apply the following conditionally, proportional to change size, project ownership
and risk; record concrete results in existing task/PR, release and evidence records.

| Question | Minimum reliable check |
| --- | --- |
| Is the agreed result present? | Inspect actual outputs, paths, scope and exact baseline |
| Is its behavior proved? | Read the required revision-bound checks and gaps, not just file existence or CI summary |
| Is Git ready for handoff? | Compare working tree, branch, remote/PR, CI and release state; disposition any unintended or ambiguous change |
| Can work resume? | From a fresh checkout or appropriately isolated worktree, find the real entry point, documented build/test instructions, dependencies and non-secret configuration; actually replay a representative check when required |
| Can it be maintained/audited? | Follow requirements/decision -> source/test -> version -> original evidence and any operational rollback/restore reference |
| Is the next step obvious? | Point to outstanding issues, risk owner, known limitations and the next cheapest authorized action |

If a required check cannot run, mark it **NOT_RUN/UNKNOWN** and report the
limitation; a README link or an AI claim cannot substitute for a fresh-checkout
or recovery test. A fresh-checkout smoke check is valuable but is not compulsory
for trivial changes. Distinguish local reproducibility, deployment readiness and
off-device backup/restore evidence.

**Authority:** the automated checks may inspect and report, but may not infer
human approval, accept risk, release, merge, send deliverables, change Git remote
history or clean/delete work. Completion and continuation readiness are separate
from permission to start the next scope.

## Existing owners and related routes

- Accepted requirements and acceptance criteria remain authoritative for business
  meaning; implementation and tests remain authoritative for executable behavior.
- Per-feature XML `goal/done`, `useCase`, `knowledge`, `sourceMap`,
  `verify` and `open` hold **only durable** feature knowledge and references.
- Git owns code history, PRs and branches; the project's issue/task owns transient
  status, next actions and work handoff. The optional [Repository Coordination]
  (repository-coordination.md) is still a proposal, not an installed service.
- Native test/CI results and [Evidence Storage](evidence-storage.md) own evidence;
  [Customer Deliverables](customer-deliverables.md) owns the customer package and
  its checks; [Development Lifecycle](development-lifecycle.md) and its
  [phase contracts](lifecycle-phase-contracts.md) own phase boundaries.

Never create a second full specification, a parallel feature-by-feature XML
manifest, a new Git directory convention, or an additional release gate solely
to implement this method.
