# Security Policy

## Supported versions

Security fixes are applied to the latest released minor version. Older versions may receive fixes when the change is small and low risk.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability involving hook execution, command construction, secret handling, external API calls, XML/HTML rendering, or prompt/tool injection.

Use GitHub Private Vulnerability Reporting when it is enabled for this repository. If it is not available, contact the maintainer through the private contact method listed in the repository profile.

Include the affected version, reproduction steps, expected impact, and any known mitigation. Do not include live credentials or third-party secrets.

## Security design notes

- External decision providers are opt-in; only advisory failures are fail-open.
- Runner evaluation requires OS isolation, fixed criteria, explicit file paths and bounded budgets; missing isolation is fail-closed.
- Model proposals cannot approve themselves or publish changes. Human review is a separate revision-bound host operation.
- API content modes and the Codex broker need explicit transmission opt-in. Redaction is defense in depth, not comprehensive DLP.
- The plugin does not vendor xquery-mcp binaries.
- Mermaid rendering uses `securityLevel: strict`.
- The HTML renderer prefers a local pinned Mermaid runtime and otherwise loads the same pinned version from a CDN.
- Repository secrets must never be stored in Feature Map XML.
