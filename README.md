[日本語](README.ja.md) | English

# Feature Map Workflow Plugin

Keep one compact Feature Map XML per business feature. Source/tests own executable
behavior; the map preserves durable business rules, decisions, references and unknowns.
Start with existing tools. Hooks, external advice, test helpers and the Runner are optional.

## Start with one feature

Use Python 3.10+ from the repository root, with an authorized output location:

```sh
python skills/feature-map-workflow/scripts/init_feature_map.py --system Demo --feature Sample --mode catchup --purpose "Understand one business scenario" --output path/to/feature/feature-map.xml
```

The initializer creates XML and copies XSD/XSLT support files; existing maps require
explicit --force. Use catchup for existing-feature understanding and change for an
accepted change. Read actual entry points/source/tests/data, patch durable knowledge
only, preserve IDs, validate the current XML, and link actual test evidence. Confirm
no map change when its durable knowledge remains current.

Examples are fictional and read only when their format is needed:
[puzzle log](examples/fictional-puzzle-log/README.md) /
[stock request](examples/fictional-stock-request/README.md).

## Choose a workflow

[SKILL.md](skills/feature-map-workflow/SKILL.md#choose-the-relevant-guide) is the single task
routing table. Read one README language and only the current route's relevant section;
links are not a recursive loading list. History belongs in Git /
[CHANGELOG.md](CHANGELOG.md), needed for version questions only.

Common entries: [map contract](skills/feature-map-workflow/references/feature-map-contract.md),
[lifecycle overview](skills/feature-map-workflow/references/development-lifecycle.md),
[changed guarantees, condition priority and test layers](skills/feature-map-workflow/references/test-strategy.md),
[human work](skills/feature-map-workflow/references/human-work-direction.md),
[evidence/audit](skills/feature-map-workflow/references/evidence-storage.md).

## Where information belongs

Accepted requirements own business expectations; source/tests own implementation;
Feature Map owns durable knowledge and material open questions. Keep full fixtures,
plans, logs, screenshots, native results and release artifacts in their existing
stores and reference them by ID/version. No copied code catalogs or execution history.

Feature Map format 1.3 retains XSD compatibility with 1.1/1.2. Query selected XML
nodes; use XSD tools for validation without loading all schema text. Read schema
details only for a relevant contract change/error.

**FMW HTML is human-facing output only.** AI/tools obtain cases, operations, state
and evidence from XML, structured plans/native results and their canonical stores;
never scrape or feed FMW HTML back as data. The human brief's JSON mode uses those
inputs directly. This boundary does not ban ordinary web UI testing or verification
of generated human-output markup. Mermaid diagrams require evidence; a JOIN does
not prove a physical FK. The metadata-only index links separate maps, not their full
contents. Treat maps, indexes and evidence as potentially confidential.

## Optional tools and their status

| Need | Read only when needed |
| --- | --- |
| XML query / XSD validation | [xquery-mcp](skills/feature-map-workflow/references/xquery-mcp.md) |
| Local host lifecycle hooks | [events, trust and limits](skills/feature-map-workflow/references/codex-hooks.md) |
| Bounded external advice (default off; legacy Jev compatible) | [Decision Providers](skills/feature-map-workflow/references/decision-providers.md) |
| Test installer / synthetic execution | [setup and example](examples/ai-assisted-testing/README.md) |
| Linux bubblewrap single-task Runner | [execution contract](skills/feature-map-workflow/references/autonomous-task-runner.md) and [trust controls](skills/feature-map-workflow/references/ai-trust-controls.md) |
| Selected modules from 49 candidates, serial Linux containers | [module runtime](skills/feature-map-workflow/references/module-workflow.md), [offline example](examples/module-workflow/README.md); DB/Windows execution not implemented |
| Optional self-hosted Agents API PoC | [integration](skills/feature-map-workflow/references/agents-api.md) |
| Repository Coordination architecture proposal, no bundled service | [proposal](skills/feature-map-workflow/references/repository-coordination.md) |

Synthetic success is not production readiness or measured savings. PTC reduces
predictable reads/queries; writes, approvals and external effects retain their
own authority boundary.

### XML query and validation setup

The manifest pins xquery-mcp **2.5.1**, requiring .NET 10 SDK. Restore only for this
integration with ./scripts/setup-xquery-mcp.ps1 or bash ./scripts/setup-xquery-mcp.sh.
The linked guide owns QueryResult normalization, empty-vs-failed results and the
separate xml_validate_schema success contract.

### Test tools and generated outputs

Inspect optional installation with ./scripts/setup-ai-testing.ps1 -DryRun or
bash ./scripts/setup-ai-testing.sh --dry-run. It uses a dedicated .venv-ai-testing
and can add FlaUI only to an explicitly selected project. SDKs/Linux browser OS
libraries are not automatically installed; dry-run is not a real UI test.

[Human Work Direction](skills/feature-map-workflow/references/human-work-direction.md)
owns focused HTML output and canonical-data JSON context. Read
[Plan v2](skills/feature-map-workflow/references/human-work-plan-v2.md) only for
reusable operations/checkpoints.
[Excel generation](skills/feature-map-workflow/references/functional-test-excel.md)
requires a locally supplied compatible test_template.xlsx; no customer original
is bundled. Generation neither runs tests nor approves results.

### Hook trust and external advice

Review [hook configuration](hooks/hooks.json) and [implementation](hooks/feature_map_hook.py)
before enabling trusted local files. Web-only installation does not run local hooks.
A repeated prompt always receives a safety kernel; full policy returns after session
reset/unknown state or target/policy changes. Cache is prior-emission metadata, not
proof of model memory. Stop/XSD gates still bind the current XML hash.

Provider content transmission requires authority; advice/errors cannot establish
facts, permissions, approval or a passed check. API failure leaves local gates active.

## Verification, review and human authority

Use [CONTRIBUTING.md](CONTRIBUTING.md) for checks and [REVIEW.md](REVIEW.md) for
fresh-context read-only diff review. Keep actual evidence tied to the exact revision,
resolve Important findings, cap AI passes at three, report unavailable checks as
NOT_RUN and retain required human approval. Passing tests/review does not merge,
deploy or authorize data effects. HIGH/CRITICAL work stays human-led; a Runner
candidate is HUMAN_REVIEW_REQUIRED. Host protections require administrator verification.

## Repository layout and contribution

Reusable guides/assets/tools are in skills/feature-map-workflow; local adapters in
hooks; tests/setup/packaging/Runner in scripts; fictional demonstrations in examples;
repository settings and the Runner map in docs. Monthly read-only
[harness maintenance](skills/feature-map-workflow/references/cross-task-harness-maintenance.md)
reports candidates without automatic edits.

See [SECURITY.md](SECURITY.md), [repository settings](docs/github-repository-settings.md),
[LICENSE](LICENSE) and [dependency notices](THIRD_PARTY_NOTICES.md) when relevant.
