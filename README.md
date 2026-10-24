[日本語](README.ja.md) | English

# Feature Map Workflow Plugin

Carry one compact Feature Map XML per business feature through investigation, design, implementation, verification and delivery. Source and tests remain implementation evidence; the map preserves business rules, decisions, navigation and unresolved questions that are expensive to reconstruct.

Start with the map and your existing tools. Hooks, external advice, test helpers and the bounded Task Runner are optional. The repository-coordination service is an architecture proposal, not a bundled runtime.

## Start with one feature

Run commands from the repository root with Python 3.10 or later. Replace the sample names and output path with your feature's authorized location:

```sh
python skills/feature-map-workflow/scripts/init_feature_map.py --system Demo --feature Sample --mode catchup --purpose "Understand one business scenario" --output path/to/feature/feature-map.xml
```

The initializer creates a map and copies its XSD/XSLT support files. It refuses to overwrite an existing map unless `--force` is supplied. Use `catchup` for understanding an existing feature and `change` for an accepted change; keep stable IDs when updating either.

1. Read the real entry point, source, tests and relevant data/configuration.
2. Keep only durable knowledge and references in the map; preserve unknowns under `open`.
3. Patch the smallest changed nodes and validate the current XML against its XSD.
4. Run the required tests separately and link their actual evidence.
5. Review the map before completion; leave it unchanged when its durable knowledge is already current.

For a complete starting example, see the [fictional puzzle log](examples/fictional-puzzle-log/README.md) or [fictional stock request](examples/fictional-stock-request/README.md). Their invented rules and relationships are examples, not evidence about a real system. The puzzle-log example includes a PowerShell XML-to-HTML renderer.

## Choose a workflow

Read the guide for the current task rather than loading every reference.

| Goal | Guide |
| --- | --- |
| Decide what belongs in a map, split feature boundaries or create an HTML index | [Feature Map Contract](skills/feature-map-workflow/references/feature-map-contract.md) |
| Work across requirements, design, tests, implementation and delivery | [Development Lifecycle](skills/feature-map-workflow/references/development-lifecycle.md) |
| Understand unfamiliar code, dynamic dispatch, SQL and runtime dependencies | [Legacy Analysis](skills/feature-map-workflow/references/legacy-analysis.md) |
| Reach a selected EXE/job/UI-to-BL path and discover minimal fixtures | [Target Reachability](skills/feature-map-workflow/references/target-reachability.md) |
| Compare local change, minimal Application/Domain boundaries or gradual replacement for a legacy slice | [Incremental Modernization](skills/feature-map-workflow/references/incremental-modernization.md) |
| Connect business flow, data flow and evidenced ER relationships | [Three Complementary Views](skills/feature-map-workflow/references/three-view-understanding.md) |
| Select the minimum useful diagrams for understanding, change impact and testing | [Diagram Selection](skills/feature-map-workflow/references/diagram-selection.md) |
| Choose test layers and state what the evidence covers | [Test Strategy](skills/feature-map-workflow/references/test-strategy.md) and [Coverage Model](skills/feature-map-workflow/references/coverage-model.md) |
| Execute repeatable UI/CLI/DB tests and retain evidence | [AI-assisted Testing](skills/feature-map-workflow/references/ai-assisted-testing.md) |
| Reduce human setup and context switching without combining test outcomes | [Human Work Direction](skills/feature-map-workflow/references/human-work-direction.md) |
| Fill a supplied customer workbook from planned cases and step evidence | [Functional Test Excel](skills/feature-map-workflow/references/functional-test-excel.md) |
| Review a tested candidate and prepare human approval | [Code Review](skills/feature-map-workflow/references/code-review.md) and [REVIEW.md](REVIEW.md) |
| Investigate explicitly requested maintenance or workflow inefficiency | [Maintenance Triage](skills/feature-map-workflow/references/maintenance-triage.md), using the [YAGNI / whole-system principles](skills/feature-map-workflow/references/yagni-whole-system-optimization.md) |
| Learn reusable methods across new tasks; audit and calibrate harness guidance | [Cross-task Harness Maintenance](skills/feature-map-workflow/references/cross-task-harness-maintenance.md) |

Monthly read-only GitHub Actions inventories structural drift; semantic proofreading, consolidation and adoption remain human-reviewed and optional. No automatic Skill rewrites are triggered.

These guides use the existing development phases; they do not require a new phase, report or tool for every task. Trace the relevant business scenario, then change only the approved boundary. Consider no change when its value is lower than the implementation, verification or operational cost.

## Where information belongs

| Information | Owner |
| --- | --- |
| Implementation and executable behavior evidence | Source and tests |
| Business expectations and authority to accept them | Approved requirements, invariants and human decisions |
| Durable feature knowledge and material unknowns | Feature Map XML |
| Fixtures, detailed test plans, screenshots, logs, DB observations and release artifacts | Their existing test/evidence/artifact stores, referenced by the map |
| Change history | Git |
| XML structure and human presentation | XSD and XSLT |

The current Feature Map format is 1.3; the XSD also accepts 1.1 and 1.2. History, class catalogs, copied SQL and full execution traces do not belong in the map. Distinguish observed legacy behavior from approved business intent.

Mermaid diagrams live in existing `diagrams/diagram` nodes as CDATA. Use them when a sequence, boundary, state or data relationship is easier to understand visually. A SQL JOIN does not prove a physical FK, and generating a diagram does not verify behavior. Human briefs may select any number of relevant UML/DFD/ER views.

The XSLT keeps technical detail and diagrams collapsible. An optional metadata-only feature index links individual maps without merging their contents; see [the map contract](skills/feature-map-workflow/references/feature-map-contract.md). Customer XML, evidence and generated indexes can contain confidential information; keep them in authorized storage.

## Optional tools and their status

| Component | Available scope | Start here |
| --- | --- | --- |
| xquery-mcp | Pinned XML query, formatting and XSD-validation integration | [Tool/result contract](skills/feature-map-workflow/references/xquery-mcp.md) |
| Codex hooks | Bundled context, edit-tracking and completion checks; requires a host that runs the trusted files | [Hook events and limits](skills/feature-map-workflow/references/codex-hooks.md) |
| Decision Providers | Implemented bounded advice; external calls default off | [Selection and privacy](skills/feature-map-workflow/references/decision-providers.md), [legacy Jev](skills/feature-map-workflow/references/jev.md) |
| AI test helpers | Optional installer, executable synthetic example, brief and workbook generators | [Installer and example](examples/ai-assisted-testing/README.md) |
| Task Runner | Implemented opt-in single-task attempts; Linux bubblewrap is required for evaluation | [Execution/restart contract](skills/feature-map-workflow/references/autonomous-task-runner.md), [offline example](examples/task-runner/README.md) |
| Agents API | Optional self-hosted proof of concept with read-only readers and one canonical writer | [Integration](skills/feature-map-workflow/references/agents-api.md), [example](examples/agents-api/README.md) |
| Repository Coordination | Architecture contract for a future API/queue/projection service; no such service is bundled | [Proposal and MVP boundary](skills/feature-map-workflow/references/repository-coordination.md) |

Implementation and synthetic tests do not establish production readiness or measured delivery savings. Keep the [Runner release gaps and AI trust controls](skills/feature-map-workflow/references/ai-trust-controls.md) visible when considering adoption. Programmatic Tool Calling is limited to predictable reads, queries and reduction; writes, approval and external effects keep their direct authority boundary. See the [calling policy](skills/feature-map-workflow/references/programmatic-tool-calling.md).

### XML query and validation setup

The local .NET tool manifest pins `xquery-mcp` **2.5.1** and requires .NET 10 SDK. Restore it only when that integration is needed:

```powershell
./scripts/setup-xquery-mcp.ps1
```

```sh
bash ./scripts/setup-xquery-mcp.sh
```

XPath/XQuery execution tools return a structured `QueryResult`; normalize it with the bundled adapter before using its value. An empty sequence is distinct from failure. `xml_validate_schema` retains its separate plain-text success contract; details belong in [xquery-mcp Integration](skills/feature-map-workflow/references/xquery-mcp.md).

### Test tools and generated outputs

The optional installer creates `.venv-ai-testing`, installs pinned Playwright/Chromium and can restore xquery-mcp or add FlaUI only to an explicitly selected test project. Inspect the plan first:

```powershell
./scripts/setup-ai-testing.ps1 -DryRun
```

```sh
bash ./scripts/setup-ai-testing.sh --dry-run
```

Use the [installer guide](examples/ai-assisted-testing/README.md) for installation, `--check`/`-Check`, smoke tests and platform prerequisites. Python/.NET SDKs and Linux browser OS libraries are not installed automatically. A dry-run is not a real browser or desktop test.

The [focused verification brief](skills/feature-map-workflow/references/human-work-direction.md) selects existing diagrams, expectations and a reviewed session plan. The [Excel generator](skills/feature-map-workflow/references/functional-test-excel.md) needs a locally supplied compatible `test_template.xlsx`; no customer original is bundled. Both outputs are derived artifacts. They do not execute tests or approve business expectations; an unperformed case stays unperformed, and a run-level PASS cannot fill unsupported step results.

### Hook trust and external advice

Review [hooks/hooks.json](hooks/hooks.json) and [the hook implementation](hooks/feature_map_hook.py) before enabling them. Scripts run only where the host has the plugin files; a web-only installation does not deploy them locally. Prompt-time ambiguity signals guide investigation; material missing context, not a matching word alone, determines whether to ask one question. Stop validation is tied to the current XML hash and has bounded continuations.

Decision Providers are optional advice, with `FEATURE_MAP_DECISION_PROVIDER=off|jev|openai`. OpenAI supports opt-in current-work phase classification and defaults to observation before advisory adoption. Existing `FEATURE_MAP_JEV_*` settings remain compatible. Each provider's metadata/content modes have their own payload contract; check [Decision Providers](skills/feature-map-workflow/references/decision-providers.md) and [Jev](skills/feature-map-workflow/references/jev.md) before enabling transmission. Advice cannot establish facts, override required checks or grant authority. API failures remain undetermined advice; local gates continue to apply.

## Verification, review and human authority

Run required deterministic checks on the exact candidate, then request a fresh-context read-only diff review using [REVIEW.md](REVIEW.md). Resolve concrete findings with source/evidence, cap AI review/fix passes at three, and bind human review to the current commit. Record unavailable checks as `NOT_RUN` and separate source, mocked, runtime and business-acceptance evidence.

The bounded Runner accepts LOW and appropriately pre-approved MEDIUM work; HIGH/CRITICAL work stays human-led. Passing checks lead to `HUMAN_REVIEW_REQUIRED`, never automatic approval or publication. A clean AI review, a PR template or a policy document does not enforce GitHub Rulesets. Required human approval, host permissions, recovery and actual CI remain independent.

For user-facing Japanese, preserve meaning, scope, certainty and identifiers before shortening prose. Use the [context gate](skills/feature-map-workflow/references/context-gate.md) and [Operable Japanese](skills/feature-map-workflow/references/operable-japanese.md); reuse available facts before asking a consequential clarification.

## Repository layout and contribution

| Location | Content |
| --- | --- |
| [skills/feature-map-workflow/](skills/feature-map-workflow/) | Reusable Skill entry point, task guides, XML/XSD/XSLT assets and feature tools |
| [hooks/](hooks/) | Local lifecycle hooks and optional Decision Provider adapters |
| [scripts/](scripts/) | Setup, tests, validation, packaging and the bounded Runner |
| [examples/](examples/) | Fictional maps, synthetic tests and optional runtime examples |
| [docs/](docs/) | Repository settings guidance and the existing Runner Feature Map |
| [.github/](.github/) | CI/release definitions and collaboration templates |

See [CONTRIBUTING.md](CONTRIBUTING.md) for focused checks and PR expectations, [SECURITY.md](SECURITY.md) for private vulnerability reporting, and [GitHub repository settings](docs/github-repository-settings.md) for administrator-owned protection settings. License and dependency notices are in [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
