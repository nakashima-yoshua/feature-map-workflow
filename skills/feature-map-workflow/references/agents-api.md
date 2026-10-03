# Agents API integration

## Purpose

Use the OpenAI Agents API as an optional execution runtime for Feature Map Workflow without making the workflow depend on one agent product.

The workflow contract remains repository-owned:

- source and tests are canonical implementation evidence;
- Feature Map XML stores durable knowledge only;
- xquery-mcp provides narrow XML reads and XSD validation;
- exact Git state, permissions, schema validity, and irreversible actions remain deterministic or human-controlled.

Agents API supplies a managed harness, session state, tools, environments, context management, and optional subagents. It does not become the source of truth.

## Current API surface

The public beta uses `client.beta.agents.sessions.create(...)`.

For local/private repositories, prefer a self-hosted environment so the workspace remains under the repository owner's control:

```python
environment={
    "type": "self_hosted",
    "workspace_directory": "/path/to/repository",
    "capability_directories": ["/path/to/repository/skills"],
}
```

The API key needs the Agents API session permissions documented by OpenAI. Keep the key outside the agent workspace.

Official references:

- https://developers.openai.com/api/docs/guides/agents-api/overview
- https://developers.openai.com/api/docs/guides/agents-api/quickstart
- https://developers.openai.com/api/docs/guides/agents-api/sessions

## Reader / writer rule

Use multi-agent execution only for work that can be separated cleanly.

Default shape:

```text
Parent Agent (single canonical writer)
  |
  +-- Source Reader
  +-- Test Reader
  +-- Data / Config Reader
  +-- Runtime / Evidence Reader
```

Reader subagents may:

- search source and tests;
- inspect configuration and data definitions;
- collect evidence;
- return candidate findings with file/symbol references.

Reader subagents must not:

- edit Feature Map XML;
- edit source or tests;
- commit, push, merge, deploy, or mutate external systems.

Only the parent/writer may apply canonical repository changes. Before a write it must reconcile reader findings against current repository state.

This preserves the existing Single Writer rule in `repository-coordination.md`.

## Session scope

Prefer one session per bounded feature/change rather than one permanent session for the whole repository.

Reuse a session while:

- the feature objective and authority are unchanged;
- the same Feature Map remains the working index;
- follow-up work is part of the same acceptance boundary.

Start a new session when the target feature, authority, or repository/worktree boundary changes materially.

## Context policy

Do not load the entire Feature Map or repository into the prompt.

The parent agent should:

1. read the workflow skill;
2. locate the target Feature Map;
3. query only relevant XML sections;
4. delegate independent read-only investigation when useful;
5. synthesize evidence;
6. apply one minimal write set;
7. validate XML after changes;
8. report only the delta and remaining open items.

## Failure handling

Treat these separately:

- agent/session failure: retry or resume the session;
- tool failure: inspect the tool result;
- domain failure: report the feature operation as failed/blocked as appropriate;
- stale repository state: re-read current state before writing;
- ambiguous authority or acceptance: stop the affected write and ask one clarification.

A completed agent turn does not prove that every tool succeeded. Verify the actual repository and validation results.
