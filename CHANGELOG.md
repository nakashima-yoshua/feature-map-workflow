# Changelog

All notable user-visible changes are documented here.

## Unreleased

- Update the pinned xquery-mcp dependency to 2.5.1.
- Add an MCP contract smoke test that launches the pinned server, lists required tools, and calls `xml_validate_schema`.
- Normalize xquery-mcp 2.5.1 QueryResult JSON for XPath/XQuery execution, including success, empty-sequence, and structured-error handling.

## 0.4.0

- Add Feature Map schema version 1.3.
- Add optional Mermaid diagrams in `diagrams/diagram`.
- Render Mermaid diagrams in the XSLT HTML view.
- Prefer a local Mermaid 12.0.0 runtime with pinned-CDN fallback.
- Add offline Mermaid setup scripts.
- Add OSS repository templates, CI/release workflows, and recommended GitHub settings.

## 0.3.0

- Add context sufficiency gate and `UserPromptSubmit` hook.
- Add operable Japanese guidance with natural-Japanese rendering principles.
- Add Feature Map 1.2 `goal/exclude` and `open/item@type`.

## 0.2.0

- Add Codex lifecycle hooks and optional Jev completion decisions.
- Add xquery-mcp validation tracking.

## 0.1.0

- Initial Source-first Feature Map workflow.
