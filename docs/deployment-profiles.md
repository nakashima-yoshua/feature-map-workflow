# Deployment profiles: Core, AI Assist, Automation

Choose **Core** first. The profiles are capabilities, not three forks, packages, mandatory installations or new data formats. They reuse one Feature Map XML contract, schema and source/tests as canonical evidence. Enabling an optional profile does not alter acceptance, permission or approval boundaries.

| Profile | Minimum local requirements | Optional dependencies | Capabilities / limits |
| --- | --- | --- | --- |
| Core | Python 3.10+; `lxml` for standalone XSD validation | Git; browser; local Mermaid JS for offline diagrams | Create/maintain Feature Map XML, validate with adjacent XSD, XSLT human view, metadata-only HTML index; no AI execution |
| AI Assist | Core + an authorized AI host/model when AI assistance is desired | Codex Hooks; xquery-mcp 2.5.1 (.NET 10 SDK); OpenAI or Jev Decisions API | Guided analysis, implementation and reviews. Provider defaults to `off`; costs depend on chosen AI/API. None of these are Core requirements |
| Automation | Core + explicitly chosen runtime | bubblewrap and Linux for single-task Runner; Docker Engine/Compose v2, Landlock-capable Linux kernel, `lxml` for serial module workflow; test-specific tools | Bounded task execution and native evidence. Docker is required only for the Compose module workflow. Database/Windows execution adapters remain unavailable |

## Core: local, no Docker, no Jev, no API key

From repository root (use `python3` instead of `python` on hosts where required):

```sh
python -m pip install lxml
python skills/feature-map-workflow/scripts/init_feature_map.py --system Demo --feature Sample --mode catchup --purpose "Understand one scenario" --output sample/feature-map.xml
python skills/feature-map-workflow/scripts/validate_feature_map.py sample/feature-map.xml
python skills/feature-map-workflow/scripts/build_feature_index.py --root sample
python scripts/test_core_profile.py
```

The init script is standard-library-only, copies XSD/XSLT beside the new XML, and refuses overwrites unless `--force` is explicitly supplied. The standalone validator requires only `lxml`; it uses the adjacent XSD by default and does not require `xquery-mcp`, a .NET SDK, hooks or a model. The index is an HTML page containing metadata and relative links to maps, not copied detailed knowledge. Open `sample/feature-map.xml` in a browser supporting local XML/XSLT to inspect the human-facing view; browser support for `file://` varies. Mermaid diagrams additionally need the optional local Mermaid runtime or access to the pinned CDN: the core data and validation are offline, but **diagram rendering is not guaranteed offline without that local asset**. Do not send confidential XML to a CDN.

`python scripts/test_core_profile.py` covers creation, XSD success/failure, DTD rejection, XSLT transformation and index generation in temporary paths. CI runs it on Linux, Windows and macOS with no Docker, external decision provider, AI credentials, .NET or MCP setup. This is a test of the Core workflow, not acceptance of any customer's requirements or production test evidence.

## AI Assist: opt in

- The Skill works as a guide without Codex; intelligent interpretation/generation requires a separately available model and may incur usage charges.
- For local Codex Hooks inspect `hooks/hooks.json` before enabling; Web-only plugin installation does not execute local hooks.
- For selective XML querying and MCP XSD validation see `skills/feature-map-workflow/references/xquery-mcp.md` and install .NET 10 only if chosen.
- External decision calls use `FEATURE_MAP_DECISION_PROVIDER=off` by default. `jev` and `openai` are independent opt-ins; neither is a prerequisite for the other. Authorize data transmission and associated costs before turning either on.

## Automation: opt in

- For Linux bubblewrap single-task Runner, read `skills/feature-map-workflow/references/autonomous-task-runner.md`; do not substitute an unisolated fallback.
- For serial Docker Compose modules, read `skills/feature-map-workflow/references/module-workflow.md`. Its 49 entries are candidates, not 49 implemented algorithms, and DB/Windows capabilities are blocked.
- For test installation/Excel production, follow the relevant reference. Generated artifacts do not run or approve customer tests by themselves.

Compatibility: no Feature Map schema changes, directory migration, new mandatory framework, default external calls or automatic merges/deployments are introduced by this split.
