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

## AI-agent incident containment and reporting

For an unexpected model action, prompt/tool injection, attempted permission bypass,
untrusted tool output, evidence mismatch, or exposure of source/credentials:

1. From an account outside the model's write permissions, run
   `python scripts/task_runner.py stop /private/runs/RUN_ID` for an active Task Runner run.
   Check `status`; stop is only a request. If it cannot complete, use host process
   management to terminate the runner and escaped children, disable relevant network
   or credentials as needed, and verify what actually stopped.
2. Preserve the exact Git revision, task configuration, run state, hashes, sanitized
   logs/patches and the independent evidence anchor in a host-controlled location.
   Do not modify or erase the original records during initial containment.
3. Determine which files, approvals, dependencies and external endpoints were
   accessible; compare actual output/side effects against the approved scope.
   Treat unverified actions as unresolved. Revoke and rotate potentially exposed
   credentials through their usual operators.
4. Report privately through the channel above, with observed impact and mitigation.
   Share only sanitized evidence and never publish live credentials, customer data
   or exploit details in a public Issue/PR.
5. The maintainer decides on notification/disclosure and remediation appropriate
   to the confirmed impact. Resume work only through a newly reviewed run and
   independent regression evidence; no automatic HALT unlock or release approval.

See [AI trust controls](skills/feature-map-workflow/references/ai-trust-controls.md)
for acceptance criteria, stop semantics, tamper-detection limits, and remaining
host/release prerequisites. Not every AI mistake is a security vulnerability;
use the same containment and evidence discipline when the impact is uncertain.
