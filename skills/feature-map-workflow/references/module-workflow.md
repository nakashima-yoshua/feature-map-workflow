# Optional serial module workflow

Use this route only to run an explicitly configured, LOW-risk feature slice on
Ubuntu/Linux containers. The ordinary Skill, Hooks and single-task Runner remain
usable independently. This is not the Repository Coordination API/queue proposal.

## Logical modules and physical runners

The versioned [catalog](../assets/task-modules.json) contains the proposed 49
candidates across 10 stages, with their existing FMW phase references. Inspect it
with `python3 scripts/workflow_orchestrator.py catalog` from the repository root.
Its order is a navigation aid, not a requirement to run every module. Choose the
steps needed for one feature and define the observable expectation before code.
Start scenario/test design from requirements/basic design; iterate locally instead
of completing all documents or tests for an entire project before implementation.

The catalog is not 49 implemented business algorithms. An AI proposal handler or
an approved command realizes each selected module for the particular project.
`default_runner` is advice; the explicit step configuration owns the actual mapping.
Generated requirements/designs are drafts against the protected canonical contract,
not automatic business agreement. QA checks may occur inside any selected phase.

```mermaid
sequenceDiagram
  actor Operator
  participant Host as Host launcher
  participant O as Orchestrator
  participant A as AI Runner
  participant B as Build/Test Runner
  participant S as Private run store
  Operator->>Host: Reviewed configuration + committed source
  Host->>S: Freeze baseline, identity, config
  Host->>O: Start Compose services
  O->>A: Fixed request + selected input hashes
  A-->>O: Structured proposal
  O->>O: Validate complete proposal; apply allowed edits
  O->>B: Fixed argv + candidate identity
  B-->>O: Exit status + native result files
  O->>S: Verify and seal results
  alt Required checks pass on the final candidate
    O-->>Operator: HUMAN_REVIEW_REQUIRED + manifest
  else Failure, stop, ambiguity or changed evidence
    O-->>Operator: HALT + retained diagnostic evidence
  end
```

Compose starts all three services once. Orchestrator writes requests into a
read-only worker mount and consumes role-specific results. It has no Docker socket
or network. Workers cannot write its state, baseline or candidate; only Orchestrator
applies proposed edits. Each worker claims a step once by exclusive directory
creation. The Build service runs commands against the read-only candidate, with
temporary outputs and no model credentials or network. These are OS mount/process
boundaries; prompts alone are not isolation.

Build child processes additionally enter a Landlock filesystem domain before
exec: system runtimes, image configuration, proc and the candidate are readable;
only the command's private temporary/output directory is writable. Worker request
and result namespaces are not granted, so candidate code cannot forge a future
step's observation. Linux x86_64/aarch64 with Landlock ABI 3+ is required; unavailable
isolation fails closed. No privileged container or relaxed fallback is enabled.
See [Linux's Landlock contract](https://docs.kernel.org/userspace-api/landlock.html).

## One project configuration

Use [the offline example](../../../examples/module-workflow/workflow.json) as a
complete configuration, not a global installation setting. It owns:

- `source_subdir`, `contract_ref`, purpose, exclusions, LOW risk, invariant and
  acceptance references, exact allowed/protected files;
- selected `steps`: unique ID, catalog module, runner, earlier dependencies,
  required input files, required output files, time budget and handler mode;
- `verification_steps`, total elapsed-time budget and cumulative artifact budget;
- external-input authorization and the reviewed CLI version only for live Codex.

The selected source subtree must be committed and clean. It is exported at the
actual HEAD into a private run; no original worktree edit, git push or merge occurs.
The source tree is limited to 64 MiB / 10,000 regular files, each proposal to the
existing Runner's 2 MiB contract, each run to 100 serial steps / 24 hours. Symlinks,
special files, `.env*` and control paths are unsupported. Select a component subtree
without credentials or private customer material; archives are not sanitization.

`needs` names preceding steps; missing references, cycles/forward references,
unknown fields/modules and missing capabilities fail before dispatch. Only passed
dependencies advance. `verification_steps` must reference selected Build/Test
steps. Their recorded candidate hash must equal the final candidate hash; a later
AI edit cannot reuse an earlier PASS.

Every required verification step also declares `verification_result`, naming one
of its output JSON files. Successful native results must contain `status: "passed"`
and a nonempty `checks` list; each check has a nonempty `name`, `expected`, `observed`
and boolean `passed: true`. Missing/empty/failed observations cannot satisfy the
gate even if the command exits zero. The ordinary test remains responsible for
computing the meaningful comparison; these structural checks do not approve its
business oracle or establish completeness by themselves.

AI modes return only `proposal.json` in the existing `status`/`changes` contract.
`recorded-proposal` reads an explicitly protected fixture. `codex` uses the existing
tool-disabled, read-only `CodexProposer`; it does not give the model source write
access. Ordinary code checks every proposed path/content before applying anything.
Protect specification, oracle, tests, helper scripts and configuration; generated
prose cannot rewrite them. The existing `feature-map.xml` is not AI-editable here.
Maintain durable map knowledge through the ordinary Skill after review.

Build `command` mode invokes the fixed `argv` without a shell. The argv and
protected checker scripts are trusted configuration, not instructions read from
model output; candidate code and its transitive execution remain untrusted and
stay inside the child sandbox. Use `FMW_OUTPUT_DIR` for required output files; the worker copies
only the declared files into its result. Write caches/intermediates under `/tmp`.
A successful command proves its observed exit status, not each business condition.
Keep native per-case results and use the existing Result v1 adapter when connecting
actual tests to maps/plans. The synthetic example uses a small native observation
file; it does not claim full Result v1 or customer-acceptance evidence.

## Run on Ubuntu

Prerequisites: Git, Python 3.10+ with the existing `lxml` dependency, Docker Engine
and Docker Compose v2. Use an approved Python environment. Host installation,
Docker permissions, endpoint access and production deployment are not performed by
this command. Source/configuration must be reviewed and under your authority.
The Linux host kernel must provide Landlock ABI 3+ to Build children; image build
success alone does not establish this host capability.

From a clean checkout containing this example:

```sh
python3 scripts/workflow_compose.py start \
  --repo . --config examples/module-workflow/workflow.json \
  --store "$HOME/.local/share/fmw/runs"
```

The launcher prints the new run path and starts the three services. It removes
those containers afterwards, preserving all run files. A successful run stops at
`HUMAN_REVIEW_REQUIRED`, never APPROVED. Exit 2 indicates HALT, an infrastructure
failure or incomplete execution. Read the final state rather than treating an
exited container or built image as success.

Replace `<run>` below with that exact private run directory:

```sh
python3 scripts/workflow_orchestrator.py status --run <run>
python3 scripts/workflow_orchestrator.py stop --run <run>
python3 scripts/workflow_compose.py resume --run <run>
python3 scripts/workflow_compose.py down --run <run>
```

`resume` accepts unchanged configuration/runtime/input and reuses completed
evidence. It does not resubmit dispatched requests or replay a claimed worker job.
HALT and human-review-required runs are terminal. A new attempt needs a new run;
preserve the prior one and its reason in the project's existing change record.

After an abrupt host/process failure, a stale `state/orchestrator.lock` may remain.
First stop this exact Compose project and prove its containers/processes are gone.
The operator may then remove only that lock and resume with the same runtime.
A request written before interruption can finish once or its existing result can
be adopted. A missing request, partially imported evidence or a claimed job with
no result HALTs rather than guessing/replaying. Inspect it, retain it, and create
a new run after resolving the cause. Do not edit status or manufacture a result.

## Live Codex and optional SDK

Live Codex is opt-in, and must use an already authorized credential file outside
the repository. No key is created or written by this runtime. Do not put a key in
JSON, argv, a Docker build argument/context, Git, logs or a shared HOME.

Change the selected AI steps to `mode: "codex"`, remove their `proposal` field,
select only authorized `inputs`, and set `external_input_allowed: true` plus
`codex_version: "codex-cli 0.159.0-alpha.3"` in the project configuration. Select
the existing private file via `FMW_CODEX_KEY_FILE`, then use:

```sh
python3 scripts/workflow_compose.py --override runtime/compose.codex.yaml start \
  --repo . --config /path/to/reviewed-workflow.json \
  --store "$HOME/.local/share/fmw/runs"
```

The override installs the broker's exact reviewed CLI version, gives only the AI
service the secret mount and enables its network. The broker reads it into its own
process environment, passes only selected source text, and restores the prior
environment afterwards. Build commands receive a separate minimal environment.
Limit model-endpoint egress on the host before opting in. Live API authentication,
CLI sandbox compatibility and business benefit require their own environment test.
Version mismatch HALTs; do not silently upgrade the CLI or enable privileged mode.
See [the existing broker contract](autonomous-task-runner.md#execution-and-privacy-boundaries).

Only the two repository overrides named here are accepted. The launcher validates
the rendered service commands, mount sources/access, users, resource limits,
networking, build context and credential placement before starting services.
An arbitrary external Compose file is not execution authority. Preserve the same
approved overrides when resuming a nonterminal run.

For .NET Linux builds add `--override runtime/compose.dotnet.yaml`. This supplies
.NET 10 SDK/Python; it does not make .NET Framework or Windows UI tests run on
Linux. Redirect MSBuild `bin`/`obj`, NuGet/CLI caches and test results to temporary
or output paths in the approved command, and preinstall reviewed dependencies in
the image. The default Build network remains off. Do not relax isolation merely to
restore packages. SDK availability and actual project build/test acceptance are
different checks.
Temporary filesystems are non-executable: for managed console probes use
`-p:UseAppHost=false` and invoke the resulting DLL with `dotnet`; do not enable
temporary native executables merely to bypass this boundary.

The `database` and `windows` capabilities are deliberately unavailable in this
stage. Configuration selecting them returns BLOCKED before execution. Existing
DB services remain separate and untouched. Add an explicitly authorized adapter
when an actual project needs DB connectivity or a Windows host; container count
does not track module count.

## Evidence, retention and review

Each private `<run>` owns:

| Location | Content / writer |
| --- | --- |
| `state/config.json`, `state/identity.json`, `state/baseline/` | Frozen configuration, exact source revision, source/config/runtime/deployment hashes; host creates |
| `state/state.json`, `requests/` | Checkpoints, dispatch identity and stop control; Orchestrator/operator writes |
| `candidate/` | Reviewed-scope proposal application; Orchestrator writes |
| `results/ai/`, `results/build/` | Separate worker claims, logs and declared output files |
| `state/evidence/<step>/` | Byte-checked adopted observations; Orchestrator writes, workers cannot access |
| `state/final-manifest.json` | Final candidate and sealed evidence identity, with human authority explicitly separate |

Archive/copy the successful final manifest hash to an independent authorized review
record, and apply [Evidence Storage](evidence-storage.md) for project audit needs.
Local hashes are tamper-evident comparisons, not signatures/WORM, authentication or
protection from an administrator rewriting the entire store. No automatic merge,
publication, approval, customer submission or retention deletion is provided.

The operator owns storage capacity, private access, backups and retention. Failed
and ambiguous runs are kept; review and retention release precede deletion. The
launcher removes only this run's Compose containers, not images/volumes belonging
to other projects or any run evidence. The store must be outside disposable Git
worktrees and tool caches. Observe accumulated storage without full-store startup
scans; the runtime reads only the selected bounded run.

Review the exact baseline-to-candidate files, native condition observations,
protected specification, manifest and remaining gaps. Generated archives are
internal candidates until the existing customer-safe checks and human authority
are satisfied. This route does not replace the existing Task Runner's risk/approval
policy or widen its writable/network boundary.
