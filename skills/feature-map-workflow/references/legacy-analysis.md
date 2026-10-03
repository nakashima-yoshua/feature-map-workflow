# Legacy Analysis

## Purpose

Recover explainable business behavior, execution boundaries, data effects, dynamic routes, and unknown areas from legacy systems without requiring a redesign first.

The target is not a complete prose translation of source code. The target is an evidence-backed map that lets a developer, tester, and business user answer:

- what business scenario is being executed;
- where execution starts;
- which rules and states affect the result;
- what data changes;
- what code/DB/external paths are possible;
- what was actually observed;
- where a useful test boundary exists;
- what remains unknown.

## Evidence sources

Do not limit analysis to the repository.

Use available evidence from:

- C# / VB.NET / other application source;
- WinForms event wiring and designer metadata;
- SQL and PL/SQL;
- DB metadata: tables, views, procedures, functions, triggers, jobs, synonyms, DB links;
- master/configuration tables;
- app/web configuration;
- Registry and environment variables;
- deployed EXE/DLL versions and hashes;
- batch/PowerShell/VBScript;
- runtime process/DLL/file/SQL traces;
- logs;
- test data and DB before/after snapshots;
- operator runbooks and manual steps.

Treat deployed binaries and runtime configuration as evidence separate from source control. A repository revision is not automatically the code actually running on every workstation/server.

## Analysis model

Use multiple graph views instead of one call graph:

1. **Structure Graph** — executable, assembly, class, method, procedure, table, screen.
2. **Control Flow Graph** — branches, exceptions, retry, rollback, recovery.
3. **Data Flow Graph** — field/table/file/API value lineage.
4. **State Graph** — DB state, global/static state, cache, master values, status transitions.
5. **Dynamic Dispatch Graph** — DB/config/reflection/plugin/process/script-selected execution.
6. **Temporal / Event Graph** — UI events, timers, scheduler, callbacks, polling, async work.
7. **Deployment Graph** — machine, binary, version, config, environment, user/site.
8. **Operational Graph** — human steps, manual jobs, file moves, recovery procedures.

The implementation may store these graphs in any practical internal representation. Do not force all nodes and edges into Feature Map XML.

## Hidden dependency checklist

Actively search for dependencies that a static call graph can miss:

- `Process.Start`, `ShellExecute`, child processes;
- reflection, `Assembly.Load`, `Activator.CreateInstance`;
- COM/ActiveX and Registry-based ProgIDs;
- P/Invoke / unmanaged DLLs;
- DB-driven class/program/procedure selection;
- dynamic SQL / `EXECUTE IMMEDIATE`;
- triggers, jobs, queues, synonyms, DB links;
- configuration/Registry/environment switches;
- feature flags and role/permission tables;
- timers, `BackgroundWorker`, tasks, callbacks, event handlers;
- file-drop integration, watched folders, CSV/fixed-length interfaces;
- scheduled tasks, services, BAT/PowerShell scripts;
- business-date, month-end, cutoff, expiry, holiday conditions;
- retry, duplicate execution, recovery modes;
- transaction isolation, locks, concurrent update paths;
- manual operator steps that connect otherwise unrelated systems.

## Recursive boundary discovery

For mixed legacy methods, do not refactor first.

Use this analysis loop:

```text
structural extraction
  -> semantic responsibility classification
  -> SINGLE / MIXED / UNKNOWN
  -> if MIXED, inspect child blocks/calls
  -> repeat until useful responsibility boundaries appear
```

Useful responsibility classes include:

- UI input/output;
- validation;
- business rule;
- orchestration;
- DB read;
- DB write;
- transaction;
- external I/O;
- technical control;
- unknown.

A useful boundary candidate may be a screen, event handler, method, stored procedure, DB effect, file boundary, or executable process.

Probabilistic classifiers such as Jev may assist with bounded classification, but exact call facts, DB metadata, file existence, hashes, and runtime observations must come from deterministic evidence.

## Possible vs observed

Maintain separate concepts:

- **Possible graph:** paths supported by source/configuration/DB/deployment evidence.
- **Observed graph:** paths captured during representative execution.

Compare them.

Cases worth investigation include:

- possible but never observed;
- observed but not explained statically;
- possible only in one environment/site/role;
- route selected by data values whose valid domain is unknown.

Do not label a possible-only route as obsolete without separate evidence.

## Runtime verification

Where safe and feasible, execute representative scenarios and collect:

- entry action;
- process tree;
- loaded modules where useful;
- SQL/procedure calls;
- files read/written/moved;
- external request capture;
- DB before/after;
- result/error/retry state.

Runtime evidence confirms a path; it does not prove every possible path was exercised.

## Data semantics

Recover data meaning, not only schema.

Look for:

- code/master tables;
- magic and sentinel values;
- nullable values with special meaning;
- status codes and transition rules;
- composite conditions;
- date/time semantics;
- field-level lineage from UI/input through DB and external output.

Record business-significant semantics as rules/invariants only when evidence supports them. Keep uncertain meanings under `open`.

## Concurrency and recovery

Treat these as first-class behavior:

- transaction boundaries;
- commit/rollback points;
- isolation and locks;
- duplicate button/file/job execution;
- timeout and retry behavior;
- partial updates;
- restart/recovery path;
- operator reprocessing.

A normal-path trace alone is insufficient where these paths materially affect data integrity.

## Output into Feature Map

Persist only the durable, expensive-to-reconstruct result:

- purpose and representative scenarios;
- important entry points and data objects;
- non-obvious boundaries;
- business rules/invariants;
- important dynamic/external dependencies;
- representative diagrams;
- verification evidence;
- unresolved dependencies and the cheapest next action.

Do not store a full class catalog, call graph, SQL catalog, runtime trace, or generated analysis dump in Feature Map XML. Keep those as analysis artifacts and refer to them when useful.

## Explanation output

Generate role-appropriate views from the same evidence.

For business readers, explain:

- trigger;
- condition;
- business decision;
- data/state effect;
- result;
- exceptions in ordinary terminology.

For engineers, expose:

- source/procedure/table references;
- control/data/dynamic routes;
- transaction/error/retry behavior;
- confidence/verification status.

For testers, expose:

- scenario;
- rule/state/effect denominator;
- test boundary;
- expected observation;
- unverified/unknown routes.

Always distinguish confirmed observation, evidence-backed inference, and unresolved uncertainty.
