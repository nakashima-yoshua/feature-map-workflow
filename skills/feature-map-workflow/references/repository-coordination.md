# Repository Coordination

## Purpose

Use this extension when Feature Map Workflow grows beyond one coding session and multiple humans or agents need to issue asynchronous changes against the same repository.

The extension does not replace the Source-first contract. Source and tests remain implementation and behavior truth. Feature Map XML remains the durable knowledge index. Repository Coordination adds a safe execution boundary around workflow state, Git publication, and cross-document XML queries.

This is an architecture contract for the extension. It does not require every component to be implemented before the basic Feature Map workflow can be used.

## Three-plane model

Keep three concerns separate.

### Knowledge Plane

Owns information needed to understand and change the software.

- source and tests;
- Feature Map XML;
- durable rules, invariants, design decisions, verification evidence, boundaries, and unresolved knowledge;
- narrow XPath/XQuery reads through xquery-mcp.

Feature Map XML must not become a job queue, lock table, retry ledger, or operation journal.

### Coordination Plane

Owns durable workflow state and transient execution state.

Durable XML may represent:

- Task;
- Decision;
- Message;
- Dependency;
- other repository-level workflow resources that must survive process restarts and remain Git-reviewable.

Transient SQLite state may represent:

- Command / Operation queue;
- idempotency keys;
- conflict reservations;
- retry count and next retry time;
- operation journal;
- scheduler state;
- workflow-run execution state;
- lock/lease/heartbeat data if later required.

Do not store a canonical Task or durable Decision only in SQLite.

### Projection Plane

Owns rebuildable indexes and query views derived from canonical XML.

Typical responsibilities:

- cross-document XML search;
- dependency-graph traversal;
- compact projections for AI context;
- indexes for status, identifiers, references, and full text;
- projection freshness metadata.

BaseX is one candidate because it can index and query multiple XML resources, but the contract must not require BaseX. Keep the Projection Engine replaceable.

xquery-mcp and a Projection Engine solve different problems:

- xquery-mcp: narrow XPath/XQuery/XSD work against explicit XML inputs;
- Projection Engine: persistent cross-document query/index service over repository XML.

## Source-of-truth matrix

| Concern | Canonical owner |
| --- | --- |
| implementation | source code |
| executable behavior evidence | tests |
| durable feature knowledge | Feature Map XML |
| durable workflow state | Coordination XML |
| runtime queue/retry/lock state | SQLite |
| change history | Git |
| shared published state | Git remote |
| cross-document search/index | Projection Engine, derived |
| generated AI context | derived view, never canonical |

Git history should not be duplicated into XML.

## Repository API boundary

Humans and agents should use semantic commands rather than unrestricted storage primitives.

Prefer commands such as:

- create-task;
- start-task;
- complete-task;
- append-message;
- add-decision;
- add-dependency;
- cancel-operation.

Low-level XML CRUD may exist internally, but do not expose arbitrary paths, raw XQuery Update, raw Git commands, or shell execution as the normal agent interface.

A command expresses intent. Acceptance of a command does not mean that the canonical state has already changed.

## Asynchronous write flow

Use this default flow:

    Command received
      -> idempotency check
      -> conflict check + reservation
      -> enqueue
      -> dependency readiness check
      -> Single Writer claims operation
      -> fetch remote state
      -> revalidate versions/conflicts/dependencies
      -> update canonical XML
      -> XSD validation
      -> semantic repository validation
      -> Git commit
      -> Git push
      -> projection update in one projection transaction
      -> operation completed

An HTTP implementation would normally return an accepted/queued result before the write reaches Git.

The human-review workflow is post-publication:

    change
      -> commit
      -> push
      -> human review
      -> correction requested
      -> new operation
      -> new commit

Do not amend, rebase, or force-push published history merely to make the workflow appear linear.

## Single Writer

Start with one writer per repository.

Reads, searches, and AI-context construction may run concurrently. Canonical writes should be serialized until there is evidence that multiple writers are necessary.

A Single Writer substantially reduces filesystem, XML, and Git race conditions without requiring distributed locking.

Use a service-owned worktree. Do not let the coordination service modify a developer's dirty working tree.

### Worktree policy

Use one writable worktree for each active canonical writer/feature-change boundary.

- create the worktree from a known published base commit or branch;
- give only the designated writer mutation authority in that worktree;
- reader agents may inspect the same snapshot or their own read-only worktrees;
- never run two canonical writers against the same writable worktree;
- before committing, re-read the branch/worktree state and recheck conflicts;
- after an external update makes the base stale, refresh or recreate the worktree rather than force-writing over it;
- published history is corrected with a new commit, not amend/rebase/force-push.

Worktrees isolate filesystem and branch state; they do not replace dependency, conflict, idempotency, or authorization checks.

## Idempotency

Clients and agents retry after timeouts. Every externally submitted command must have a stable operation identifier or idempotency key.

Submitting the same idempotency key again returns the existing operation instead of creating a duplicate.

Idempotency is separate from conflict detection: two different operations may be individually idempotent and still conflict with each other.

## Conflict model

Conflict answers:

> May these operations coexist safely?

Use logical resource keys instead of only file names.

Examples:

    task:TASK-21
    decision:D-014
    feature:receiving

The enqueue path must atomically:

    check conflict
      -> reserve resource key
      -> insert queue item

Use one SQLite transaction so two simultaneous requests cannot both observe an unreserved resource.

Recheck conflicts immediately before execution because external Git activity or an earlier queued operation may have changed the assumptions.

Avoid shared aggregate XML where possible. If TASK-21 and TASK-45 are independent, updating them should not require both operations to rewrite one project-wide summary file. Derive aggregate counts and progress in the Projection Plane instead.

## Optimistic concurrency

Every read intended to support a later write should expose a resourceVersion.

A Git blob hash is a useful candidate for XML files.

A command that depends on an earlier read supplies expectedVersion. Before applying the command, compare it with the current resource version.

If it changed, mark the operation stale/conflicted and require re-evaluation. Do not silently overwrite the newer state.

Do not reject only because repository HEAD changed. Unrelated source-code changes may leave the target coordination resource unchanged.

## Dependency model

Dependency answers:

> In what order may work run?

It is not the same as conflict.

Represent durable task dependencies in canonical XML. A Projection Engine may index the graph for efficient traversal.

Start with success dependencies:

    TASK-A -> TASK-B -> TASK-C

B is not runnable until A succeeds. C is not runnable until B succeeds.

If A has a domain failure:

    TASK-A = failed
    TASK-B = blocked
    TASK-C = blocked

B and C are blocked because they were never executed; do not mark them failed.

Validate new dependencies for cycles before accepting them:

    A -> B
    B -> C
    C -> A

must be rejected.

More conditions such as failure/always may be added later, but do not implement them before a real use case requires them.

## Workflow Run

Keep each execution attempt identifiable.

Example:

    RUN-001
      TASK-A succeeded
      TASK-B failed
      TASK-C blocked

A retry creates a new run rather than rewriting RUN-001.

This preserves evidence for debugging, review, and later learning.

## Operation state

Task state and Operation state are different domains.

A practical Operation model may include:

- accepted;
- queued;
- waiting_dependency;
- applying;
- local_committed;
- pushed;
- indexing;
- completed;
- retrying;
- stale;
- failed;
- blocked;
- cancelled;
- superseded.

Use only the states required by the current implementation. Do not add states merely because this list exists.

Canonical Task state must not be changed merely because an Operation is queued. Expose pending intent separately.

Example:

    canonical task: implementing
    pending operation: complete-task / queued

## Failure classification

Do not collapse every error into task failure.

### Domain failure

The task itself failed. This may block success-dependent downstream tasks.

### Infrastructure failure

Examples: Git remote unavailable, projection unavailable, filesystem failure, network failure.

Retry or pause execution. Do not mark the business task failed merely because infrastructure is unavailable.

### Conflict / stale

The state changed after the command was based on it. Re-read and re-evaluate.

### Validation failure

The requested mutation is invalid: schema error, illegal state transition, dangling reference, dependency cycle, missing resource, or similar.

Reject without applying the mutation.

## Crash recovery

Assume the service may stop after any durable side effect.

Persist an Operation Journal, for example:

    accepted
      -> queued
      -> applying
      -> local_committed
      -> pushed
      -> indexing
      -> completed

On restart, inspect durable state before retrying.

The critical ambiguity is:

    Git push succeeded
      -> process died before recording success

Before pushing again, inspect the remote commit/ref and continue from the actual state.

At minimum retain:

- retry_count;
- next_retry_at;
- last_error.

A dead-letter or terminal intervention state may be added when operationally necessary.

## Git publication

Push is the shared-publication boundary.

Use this order:

    canonical XML update
      -> validation
      -> commit
      -> push
      -> projection update

If push fails, the shared canonical state has not advanced.

If push succeeds but projection update fails:

    Git remote = current
    Projection = lagging

Retry projection independently.

Do not make the projection authoritative merely because it is easier to query.

## State revision

Timestamps help humans but do not prove consistency.

Track a stateRevision for the managed XML subtree. A Git tree hash is a strong candidate.

Projection metadata should include at least:

- sourceCommit;
- sourceStateRevision;
- indexedAt;
- status: fresh, lagging, or failed.

Freshness is determined primarily by revision equality:

    current coordination XML stateRevision
    ==
    projection sourceStateRevision

Repository HEAD alone is insufficient because source code may change while coordination XML does not.

## Atomic projection update

A single published state revision may modify several XML files. Do not expose a projection where only part of that revision has been indexed.

Apply all changes for one stateRevision in one projection transaction when the engine supports it, and update projection metadata in the same transaction.

Readers should see either the complete previous revision or the complete new revision.

## AI context

Do not send all repository XML to a model.

Build role/task-specific context from the Knowledge and Projection planes.

Examples:

Planner context:

- goal;
- open tasks;
- dependencies;
- unresolved decisions;
- current revisions.

Coder context:

- target task;
- requirements/rules;
- durable decisions;
- constraints;
- related source/test references;
- expected resource version.

Reviewer context:

- task;
- acceptance basis;
- relevant decisions;
- changed evidence;
- test results;
- published revision.

Every generated context should carry enough revision metadata to tell whether it is current.

## Feature Map relationship

Do not mirror queue/runtime state into Feature Map XML.

Do not copy every coordination Decision into Feature Map either. Promote a decision only when it becomes durable feature knowledge that is expensive or ambiguous to reconstruct. Apply the existing Feature Map contract when deciding whether to retain it.

A Feature Map may be queried together with coordination resources when building AI context, but their schemas and lifecycle states remain separate.

Feature Map states such as draft/investigating/ready/verified/closed are knowledge-maturity states. They are not Task or Operation states.

## Validation

Use both structural and semantic validation.

Structural validation:

- XML is well-formed;
- XML conforms to its XSD.

Semantic repository validation should cover at least:

- unique identifiers;
- valid references;
- no dangling dependency;
- no dependency cycle;
- legal state transitions;
- path/ID consistency;
- deletion/reference rules.

Prefer logical archive/delete semantics for durable referenced resources. Physical deletion should be exceptional.

## Security boundary

Agent-facing APIs must not accept arbitrary filesystem paths or raw shell/Git commands as normal operations.

Keep XML external entities disabled. Do not enable DTD/XInclude unless an explicit use case justifies the additional attack surface.

Record the actor for operations so a Git commit and Operation Journal can be correlated with a human or agent request.

Bounded classifiers such as Jev may advise semantic routing, but exact versions, graph cycles, Git state, schema validity, permissions, transitions, retry policy, and conflict reservations belong in deterministic code.

## MVP boundary

Start with:

- one repository;
- one Repository Service;
- one SQLite runtime database;
- one Single Writer;
- canonical coordination XML;
- Git commit/push;
- one replaceable Projection Engine;
- query-generated AI contexts.

Do not require for the MVP:

- RabbitMQ or Kafka;
- distributed queues;
- multiple writers;
- distributed locks;
- distributed transactions;
- exactly-once infrastructure;
- complex priority scheduling;
- a mandatory BaseX dependency;
- automatic history rewriting.

Build the smallest vertical slice first:

    canonical XML
      -> Repository API command
      -> SQLite queue
      -> Single Writer
      -> validate
      -> commit/push
      -> projection
      -> AI context query

## Required verification scenarios

Before treating the coordination extension as production-ready, cover at least:

- duplicate submission with the same idempotency key;
- simultaneous updates to one conflict key;
- external Git update while an operation is queued;
- resourceVersion mismatch;
- push rejection;
- crash immediately after successful push;
- projection update failure after push;
- stale projection detection;
- dependency failure propagation;
- dependency cycle rejection;
- invalid XML/XSD;
- dangling references;
- service restart and operation recovery.

## Non-goals

This extension does not turn Feature Map Workflow into a generic distributed workflow engine.

It exists to preserve the current Source-first, compact-knowledge model while giving multi-agent repository work a controlled execution path.
