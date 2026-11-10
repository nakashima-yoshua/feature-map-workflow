# Lifecycle Quality Review

Use this reference when files, generated artifacts, backups, queues, logs, retries, temporary records, or other retained objects can accumulate.

## Design Gate

Detect missing lifecycle ownership by design review at the latest. For every retained object, identify creator, consumer, cleanup owner, retention, deletion or archive condition, retry behavior, failure handling, manual recovery, and monitoring.

Treat unbounded accumulation, full-set startup scans, missing cleanup ownership, unsafe retry, and manual-recovery gaps as design defects.

## Review Viewpoints

- bounded retention and cleanup;
- startup, scan, search, storage, and processing impact at accumulated volume;
- retry, rerun, duplicate input, cancel, and abnormal-end idempotency;
- consistency across database, file, queue, process, and recovery records;
- configuration ownership, defaults, migration, rollback, and environment differences;
- logs and metrics that identify target, cause, impact, and recovery need;
- sensitive-value protection and privileged-operation traceability;
- separation of automatic recovery from manual-recovery artifacts;
- operational handoff and safe manual procedures.

Add project-specific review viewpoint IDs through the workspace review profile rather than hard-coding one client's review document.

## Test And Operation

When accumulated state is a material risk, test a representative accumulated state at a scale relevant to that risk. Check only affected startup, scan, processing, storage, queue, retry, cleanup, archive, recovery, and monitoring behavior. Reuse suitable evidence.

If monitoring or large-state testing is omitted, record the bounded-risk reason and authorized disposition.
