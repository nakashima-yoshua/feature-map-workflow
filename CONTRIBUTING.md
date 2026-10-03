# Contributing

Thank you for contributing to Feature Map Workflow.

## Scope

Keep the project focused on one goal: reduce documentation overhead while preserving enough durable context for humans and AI to develop safely from source code.

Good changes improve one of these areas:

- Feature Map XML/XSD/XSLT;
- Mermaid rendering;
- Codex lifecycle hooks;
- xquery-mcp integration;
- bounded Jev decisions;
- context sufficiency and operable Japanese;
- validation, packaging, or documentation.

Avoid broad framework additions unless they remove more complexity than they add.

## Development

1. Fork the repository and create a topic branch.
2. Make the smallest coherent change.
3. Run applicable local checks, including `python scripts/test_xquery_result.py`.
4. If you changed XML/XSD/XSLT, validate the affected maps against `feature-map.xsd` and confirm that the generated HTML contains the Mermaid blocks.
5. Update `CHANGELOG.md` for user-visible changes.
6. Open a pull request with the behavior change, reason, and verification evidence.

## Pull requests

A pull request should explain:

- what changed;
- why the change is needed;
- what is intentionally unchanged;
- how the change was verified.

Do not include generated binaries, API keys, local `.plugin-data`, or downloaded Mermaid runtime files.

## Compatibility

The bundled XSD intentionally accepts older Feature Map versions when practical. A schema change that breaks existing `1.1`, `1.2`, or `1.3` maps requires an explicit migration note and a major-version decision.
