# Third-party notices

## xquery-mcp

- Project: https://github.com/phoenixmldb/xquery-mcp
- Package: xquery-mcp 2.5.1
- License: Apache-2.0

The plugin does not vendor the xquery-mcp binary. The setup script restores the pinned .NET tool from NuGet.

## TypeSafe Jev

- API: https://api.typesafe.ai/v1/systemone
- Product: https://typesafe.ai/

No TypeSafe SDK code is bundled. The optional hook integration calls the documented HTTPS API directly when the user explicitly enables a Jev mode and provides `TYPESAFE_API_KEY`.

## Mermaid

- Project: https://github.com/mermaid-js/mermaid
- Runtime version used by the HTML view: 12.0.0
- License: MIT

The plugin does not vendor Mermaid by default. The XSLT can load the pinned runtime from jsDelivr, and `scripts/setup-mermaid.*` can download a local copy plus the Mermaid license for offline rendering.
