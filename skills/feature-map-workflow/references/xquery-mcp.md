# xquery-mcp Integration

The plugin pins `xquery-mcp` as a local .NET tool so an MCP-capable host can use XPath/XQuery and XSD validation without sending the entire Feature Map into model context.

## Pinned dependency

- Package: `xquery-mcp`
- Version: `2.5.1`
- Runtime: .NET 10
- License: Apache-2.0
- Upstream: https://github.com/phoenixmldb/xquery-mcp
- Documentation: https://phoenixml.dev/tools/xquery-mcp

The plugin intentionally does not vendor the large self-contained platform binaries. Run the plugin setup script once to restore the pinned local .NET tool from NuGet.

## Tool mapping

| Need | MCP tool |
|---|---|
| Read one section/nodes | `xpath_evaluate` |
| Cross-section projection | `xquery_evaluate` |
| Validate an XQuery before reuse | `xquery_validate` |
| Validate Feature Map structure | `xml_validate_schema` |
| Normalize XML formatting | `xml_format` |
| Diagnose XPath/XQuery error | `xquery_explain_error` / spec lookup tools |

## Structured QueryResult contract

In xquery-mcp 2.5.1, `xpath_evaluate`, `xquery_evaluate`, and `xquery_validate` return a JSON object as MCP text content. The current shape is:

```json
{
  "ok": true,
  "value": "...",
  "count": null,
  "elapsedMs": 3
}
```

Failures use:

```json
{
  "ok": false,
  "errors": [
    {
      "code": "XPST0003",
      "message": "...",
      "line": 1,
      "column": 8,
      "sourceSnippet": "for $x in",
      "specUrl": null
    }
  ]
}
```

An empty sequence is successful and is represented by `ok=true`, `count=0`, with no `value` key. Do not confuse it with an empty string or an error.

The bundled `scripts/xquery_result.py` accepts either the inner JSON object, a JSON string, or an MCP `content:[{type:"text",text:"..."}]` envelope and normalizes it to:

- `ok`
- `value`
- `count`
- `elapsed_ms`
- `errors[].code/message/line/column/source_snippet/spec_url`

Treat unexpected shapes as contract failures instead of guessing. This is deliberately strict so an upstream protocol change is caught by CI.

`xml_validate_schema` is not part of this adapter. It still returns the plain string `Valid: XML conforms to the schema.`, and the Codex PostToolUse hook continues to use that contract.

## Context-minimizing patterns

Read rules only:

```xpath
/featureMap/knowledge/rule
```

Read unresolved high-impact items:

```xpath
/featureMap/open/item[@impact='high']
```

Read source targets:

```xpath
/featureMap/sourceMap/ref/@target
```

Read verification cases not yet passed:

```xpath
/featureMap/verify/case[@status != 'passed']
```

Use XQuery only when it genuinely compresses multiple nodes, for example returning a compact projection of IDs, types, status, and conditions rather than the entire XML.

## Safety

Keep DTD/external entity processing disabled. Do not broaden file access merely to make an XML query convenient. Treat source code, XSD, and XML as repository-scoped inputs.

## Hook integration

The Codex `PostToolUse` hook watches `mcp__xquery__xml_validate_schema`. When xquery-mcp returns `Valid: XML conforms to the schema.`, the hook stores a canonical hash of the validated XML payload. The Stop hook compares that hash with the current Feature Map, so a later edit invalidates the previous validation automatically.

Do not replace this with a boolean `validated=true`; validation must be tied to the exact XML content.
