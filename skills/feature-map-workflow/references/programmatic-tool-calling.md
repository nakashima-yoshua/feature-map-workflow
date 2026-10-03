# Programmatic Tool Calling

## Purpose

Use Programmatic Tool Calling (PTC) only for bounded stages whose control flow is predictable and whose intermediate tool output can be reduced before it reaches the reasoning model.

For Feature Map Workflow, the primary target is read-heavy XML and repository investigation.

Good candidates:

- run several independent XPath queries and return one compact projection;
- query multiple known Feature Map sections and remove empty/duplicate results;
- aggregate deterministic counts/statuses;
- perform bounded XQuery projections;
- run schema/query validation and return only structured failures and evidence.

Keep semantic investigation adaptive when each result can change the next question.

## Routing boundary

Default routing:

```text
Predictable read / filter / join / aggregate / validate
  -> Programmatic Tool Calling

Semantic investigation / design decision
  -> direct model + direct tools

Write / approval / external side effect / Git publication
  -> direct tool call behind explicit authority
```

Do not use PTC merely because several calls can run in parallel. Use it when code can safely reduce the intermediate result.

## Feature Map tool policy

When xquery-mcp is available, PTC may orchestrate these bounded tools:

- `xpath_evaluate`
- `xquery_evaluate`
- `xquery_validate`
- `xml_validate_schema`
- `xml_format` when formatting is returned as data rather than written as a file

PTC must not:

- edit Feature Map XML;
- apply patches;
- invoke shell commands that mutate the repository;
- commit, push, merge, deploy, or change external state;
- bypass the Context Sufficiency Gate or approval boundary.

If a program returns an incomplete or contradictory result, return a structured failure to the model rather than silently guessing.

## Expected result shape

Prefer a compact JSON-like result with evidence references instead of prose.

```json
{
  "ok": true,
  "feature": "receiving",
  "sections": {
    "goal": "...",
    "open_high": ["O-12"],
    "verify_failed": []
  },
  "evidence": [
    "feature-map.xml:/feature/goal",
    "feature-map.xml:/feature/open/item[@impact='high']"
  ]
}
```

The model remains responsible for semantic interpretation.

## Limits

Define before execution:

- the exact tools allowed for the stage;
- expected output fields;
- maximum calls or retries;
- stop conditions;
- what evidence must survive reduction.

Avoid a generated program that can recursively broaden its own scope.

## Agents API

The Agents API enables Programmatic Tool Calling in the managed harness. Keep an explicit `programmatic_tool_calling` tool entry in examples so the intended dependency is visible.

For local xquery-mcp, connect the server over stdio from the session environment and restrict `allowed_tools` to the known read/query/validation surface.

Official reference:

- https://developers.openai.com/api/docs/guides/tools-programmatic-tool-calling
- https://developers.openai.com/api/docs/guides/agents-api/tools/mcp
