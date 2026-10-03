# Recommended GitHub repository settings

These settings assume a small maintainer team and a public OSS repository. Start strict on automation and secrets, but avoid review rules that make a one-person maintainer unable to merge.

## Repository identity

Recommended repository name: `feature-map-workflow`

Suggested description:

> Source-first Feature Map XML workflow for Codex: Mermaid diagrams, context gates, xquery-mcp validation, optional Jev decisions, and minimal durable documentation.

Suggested topics:

`codex`, `openai`, `developer-tools`, `xml`, `xquery`, `xpath`, `xsd`, `mermaid`, `uml`, `source-first`, `requirements`, `ai-agents`

Set visibility to **Public** and default branch to **main**.

## General

Enable:

- Issues
- Automatically delete head branches

Keep disabled initially unless there is a clear use case:

- Wikis — documentation should stay versioned in the repository
- Projects — use Issues first for a small project
- Discussions — enable later if support/community traffic justifies it

Pull request merge policy:

- Enable **Squash merging**
- Disable merge commits
- Disable rebase merging unless contributors need commit-preserving history
- Enable automatic deletion of merged head branches

This keeps `main` linear and release notes readable.

## Ruleset for `main`

Prefer a repository **ruleset** over a legacy branch-protection rule.

Target: default branch (`main`)

Recommended rules:

- Block force pushes
- Block branch deletion
- Require a pull request before merging
- Require conversation resolution before merging
- Require status checks before merging
- Require linear history

Required status check after the first CI run:

- `validate`

Review count:

- One-person maintainer: **0 required approvals** initially, or allow the maintainer role to bypass the approval requirement. Still require the PR and CI path for normal changes.
- Two or more maintainers: **1 required approval** for ordinary changes.

Do not require signed commits by default. They improve provenance but increase contributor friction. Enable later if the maintainer policy explicitly requires signing.

Do not allow ordinary contributors to bypass the ruleset.

## Actions

Repository Settings → Actions → General:

- Default `GITHUB_TOKEN` permission: **Read repository contents and packages**
- Do not allow GitHub Actions to create or approve pull requests by default
- Allow only actions needed by the workflows, or use the organization allow-list if available

Individual workflows should request additional permissions explicitly. The release workflow in this repository requests `contents: write` only for tag releases.

## Security and analysis

For a public repository, enable:

- Dependabot alerts
- Dependabot security updates
- Secret scanning
- Push protection
- Code scanning / CodeQL default setup when available
- Private vulnerability reporting

Keep `SECURITY.md` in the default branch even when private vulnerability reporting is enabled. It documents supported versions and the disclosure policy.

## Releases

Use semantic tags such as `v0.4.0`.

The included release workflow packages the repository into `dist/feature-map-plugin.zip` and creates a GitHub Release when a `v*` tag is pushed.

Before the first public release:

1. Replace placeholder ownership in `.github/CODEOWNERS` if needed.
2. Confirm `LICENSE` and `THIRD_PARTY_NOTICES.md`.
3. Confirm Mermaid and xquery-mcp pinned versions.
4. Run `python scripts/validate_repository.py`.
5. Review `SECURITY.md` and enable private vulnerability reporting.
6. Create the `main` ruleset after the `validate` check has appeared at least once.

## Secrets

No repository secret is required for the base plugin.

Do not add `TYPESAFE_API_KEY` to the repository for normal CI. Jev integration is optional runtime behavior and should be configured by users in their own environment. If future integration tests require a secret, use a dedicated low-privilege test credential and never expose it to workflows triggered from untrusted forks.
