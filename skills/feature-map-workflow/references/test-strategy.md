# Test Strategy

## Purpose

Place each behavior at the cheapest stable test layer that can prove it, while keeping end-to-end coverage focused on business flows.

The default order is:

```text
Business scenario
  -> E2E
  -> condition/state/boundary coverage at integration/service/DB level
  -> residual unit tests only where lower-level isolation adds value
```

Do not maximize test count. Minimize duplicated guarantees and untested behavior.

## Test layers

### E2E

Use for a small number of business-significant flows.

Typical boundary:

```text
UI or public entry
  -> application
  -> real DB
  -> external-system stub/sandbox
```

Prefer real application and database behavior. Stub external systems when real connectivity would make tests unstable, unsafe, expensive, or non-repeatable.

### Integration / Service

Use for rule combinations, data conditions, transaction behavior, and state transitions that would be expensive to enumerate through the UI.

Typical boundary:

```text
Application/service entry
  -> business logic
  -> repository / PL/SQL
  -> real test DB
```

### DB Integration

Use when important behavior lives in SQL, stored procedures, triggers, jobs, or DB-driven dispatch.

Test the DB object directly when that is the actual behavioral boundary. Do not force a C# unit-test shape around PL/SQL-owned logic.

### Unit

Use only for remaining deterministic logic where isolation provides cheaper, faster, clearer proof:

- calculations;
- date/rounding rules;
- state decisions;
- high-combination pure rules;
- algorithms without meaningful external I/O.

Avoid tests for trivial property access, framework behavior, or mappings already covered more effectively elsewhere.

### Manual

Use only when automation cost is not justified or the behavior depends on human judgment, physical devices, unsupported legacy UI surfaces, or one-off acceptance. Record the observation and evidence.

## Test boundary contract

Every non-trivial test should make these boundaries explicit, either in test code/fixtures or in durable documentation when the boundary is expensive to reconstruct:

- **Entry point:** UI, API, batch, service, procedure, method.
- **System under test:** components expected to run for real.
- **DB boundary:** real test DB, container/VM DB, controlled schema, mock only when justified.
- **External boundary:** real, sandbox, stub, fake, or out of scope.
- **Transaction boundary:** what commits or rolls back together.
- **Data boundary:** initial records, shared masters, generated data, cleanup policy.
- **Time boundary:** real clock, fixed clock, business date.
- **Async boundary:** queue/job/event behavior and wait strategy.
- **Verification point:** response, UI state, DB state, file, event, log, external request.
- **Exclusion:** what this test does not guarantee.
- **Cleanup:** rollback, truncate, snapshot restore, disposable environment.

Example:

```text
Scenario: inventory allocation at the exact boundary

Entry:
  RegisterOrder

Real:
  C# application logic
  Oracle
  PKG_ORDER

Stub:
  SAP endpoint

Initial state:
  STOCK.QTY = 20

Input:
  ORDER.QTY = 20

Observe:
  ORDER inserted
  STOCK.QTY = 0
  SAP_QUEUE inserted

Does not prove:
  SAP accepted the message
```

## Placement rule

Choose the test layer by behavior, not by code shape.

Prefer the lowest layer that still proves the required guarantee, except when using a lower layer would replace real behavior with unrealistic mocks.

A practical decision sequence:

1. Is this a business-significant workflow? Consider E2E.
2. Does the guarantee depend on DB/transaction/stored-procedure behavior? Prefer integration/DB.
3. Is the behavior a rule combination or state transition that does not require UI? Prefer integration/service.
4. Is the behavior deterministic and cheap to isolate without distorting design? Consider unit.
5. Is the same guarantee already protected adequately? Do not duplicate unless the overlap protects a different failure mode.
6. If no stable automated boundary exists, use manual evidence and record the limitation.

## Legacy Windows Forms

Do not begin by refactoring the application into ideal layers.

Use this order:

```text
Business scenario
  -> current execution path
  -> DB before/after
  -> existing method/procedure boundaries
  -> executable test
  -> smallest extraction only where testing is otherwise impractical
```

Useful boundaries may already exist at:

- Form / screen;
- event handler;
- called method;
- service-like method hidden inside the form;
- stored procedure;
- table effect;
- external file or process boundary.

An event handler containing UI, SQL, business rules, and file/process I/O is a valid initial E2E boundary even if it is a poor long-term design. Extract only the parts that produce a clear testing or maintainability payoff.

## Evidence

A passing UI message is not enough for DB-heavy business systems. Prefer observable business effects such as:

- row inserts/updates/deletes;
- state transitions;
- history rows;
- queue/outbox rows;
- emitted files;
- process launches;
- external request capture;
- retry/error state.

Keep exact evidence in tests, logs, snapshots, or CI artifacts. Feature Map XML should retain only representative verification knowledge and references.
