## What changed

<!-- Describe only the accepted, implemented behavior. Link the focused Feature Map or issue if useful. -->

## Why / accepted outcome

<!-- What problem and business rule or test does this change satisfy? -->

## Intentionally unchanged

<!-- State the important adjacent behavior and scope boundaries. -->

## Risk

<!-- Choose ONE from changed behavior and touched paths, not author identity. See REVIEW.md. -->
- [ ] LOW — docs, comments, harmless metadata
- [ ] MEDIUM — ordinary behavior or business logic
- [ ] HIGH — auth, privacy, DB/integration, CI/release, security/approval controls
- [ ] CRITICAL / unknown — human-led risk assessment and HALT

Reason and affected boundary:
<!-- DB, external API, security, release/installer or recovery impact; say none when substantiated. -->

## Testing

<!-- Give the actual command, output/status, exact tested revision and evidence links. Mark not-run honestly. -->
- Tested commit SHA:
- Commands + results:
- Feature Map / use-case / verify-case / evidence references (if applicable):
- Not tested / guarantees not established:

## Independent AI review (advisory; never approval)

<!-- New context, read-only; use REVIEW.md and references/code-review.md. -->
- Status: NOT_RUN / reviewed / unresolved
- Reviewed base -> head SHA:
- Passes (max 3):
- Important / Nit / Pre-existing / Unverified findings:
- Finding dispositions (fixed SHA / concrete dismissal / human decision / HALT):
- Security review: not needed with reason / reviewed with evidence / NOT_RUN (escalate)

## Human review / outstanding decisions

<!-- Human decision and host approval apply to the *current* SHA. An agent cannot approve its own PR. -->
- Business / scope / risk decisions required:
- Reviewer or review reference:
- Remaining blockers or acknowledged limitations:
- [ ] Required human sign-off for this exact revision is recorded outside the model

## How to revert / recover

- Code/config revert procedure and rollback condition:
- DB migration / externally visible effects (how restored, or why not applicable):
- Rollout / monitoring / recovery owner (if applicable):

## Verification checklist

- [ ] `python scripts/test_xquery_result.py` (or justified N/A)
- [ ] XML/XSD/XSLT changes validated (or justified N/A)
- [ ] Hook changes smoke-tested (or justified N/A)
- [ ] No credentials, generated runtime files, or `.plugin-data` included
- [ ] CI result and SHA were inspected; advisory review did not substitute for required host approvals
