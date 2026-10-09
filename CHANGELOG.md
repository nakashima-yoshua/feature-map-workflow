# Changelog

All notable user-visible changes are documented here.

## Unreleased

- Add a provider-neutral DecisionProvider boundary while preserving legacy Jev configuration.
- Implement the public-beta OpenAI Decisions API adapter with named predicate/choice normalization, default-off content controls, sanitized failures and legacy Jev compatibility.
- Add an optional single-task runner with fixed paths/checks, Linux OS-isolated evaluation, bounded retries, durable checkpoints, local candidate evidence and independent revision-bound human review.
- Add an offline repair/retry example and mandatory real-sandbox CI checks; keep HIGH/CRITICAL work human-led and defer queues, multiple agents and UI expansion.
- Add an OpenAI Agents API self-hosted PoC with multi-agent read delegation and a single canonical writer.
- Add bounded Programmatic Tool Calling guidance for read/query/reduction stages and stdio xquery-mcp integration.
- Define one-writer-per-worktree rules for concurrent agent work.
- Add an optional repository-coordination architecture for multi-agent asynchronous writes, dependency scheduling, conflict control, Git publication, and rebuildable XML projections.
- Define Knowledge, Coordination, and Projection planes without mixing runtime queue state into Feature Map XML.
- Update the pinned xquery-mcp dependency to 2.5.1.
- Add an MCP contract smoke test that launches the pinned server, lists required tools, and calls `xml_validate_schema`.
- Normalize xquery-mcp 2.5.1 QueryResult JSON for XPath/XQuery execution, including success, empty-sequence, and structured-error handling.
- Add a fully fictional Feature Map example with Mermaid diagrams and a PowerShell HTML rendering guide.

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
