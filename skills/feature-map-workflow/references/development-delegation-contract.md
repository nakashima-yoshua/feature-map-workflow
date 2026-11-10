# Development Delegation Contract

Use this reference only when delegation is permitted and can change the next decision more cheaply or independently than parent-only work.

## Decision And Wave Rules

- Keep simple, coupled, or write-heavy work in the parent.
- Split independent request evidence, current-system evidence, or review dimensions; do not split sequential reasoning for appearance.
- Use dependency waves only for actual independent work; a phase transition does not create a new wave or owner.
- Join and adopt the current wave before opening dependent work.
- Use one writer. Parallel writers require isolated worktrees, the same fixed base, exclusive paths, and independent verification.

## Semantic Role Routing

Resolve roles from the active profile; never infer a customer-specific agent name.

| Work shape | Preferred semantic role | Compatibility fallback |
| --- | --- | --- |
| bounded extraction or inventory | `evidence` | `read` or parent |
| requirement, current-state, or impact synthesis | `analysis` | `read` or parent |
| approved design artifact | `design` | `write` or parent |
| estimate, plan, work breakdown, or progress artifact | `planning` | `write` or parent |
| approved implementation batch | `change` | `write` or parent |
| test asset, execution, or verification evidence | `verification` | `write` or parent |
| requirements, work-package, or archive document | `documentation` | `write` or parent |
| customer-facing communication draft | `communication` | `read` or parent |
| independent assurance | `review` | authorized independent reviewer; parent for ordinary non-independent review |
| costly-to-reverse one-shot advice | `advisor` | parent |

Prefer the phase-specific role when it exists. Use an elevated generic writer only after recording why the ordinary phase role is unavailable, blocked, or insufficient. A role name selects responsibility and access boundary; its model and reasoning settings belong to the installed agent configuration.

Keep low-effort evidence extraction and template drafting bounded to clear sources and explicit output fields. Send noisy evidence or material conflicts to analysis or the parent. Use the advisor for one consequential decision after ordinary analysis is insufficient, not routine review. Check runtime availability before dispatch; if a configured advisor is unavailable, keep advice in an authorized capable parent or use a permitted read-only fallback. Missing evidence or permissions require resolution, not a model upgrade.

## Parent-To-Child Packet

Send five essentials in plain prose or a small structure; accept equivalent field names and the legacy expanded packet:

```yaml
objective: one checkable outcome or decision input
scope: bounded target and explicit exclusions
authority: read_only or bounded_write; applicable permissions and constraints
evidence: direct source locators and relevant current facts
completion: acceptance conditions and required checks
```

Add context only when it changes execution: profile locator, required Skill, repository rules, unresolved assumptions, output location, bounded budget, or specific stop conditions. A task ID, phase name, empty registry, empty risk list, and repeated known facts are not prerequisites by themselves.

Require an immutable source snapshot for review; require a fixed base, governing approved design/source, and explicit allowed paths for writing. Repository instructions must be available to a writer through a configured adapter or direct `AGENTS.md` and rule locators. A missing adapter name alone is not a blocker when those rules fully govern the bounded write. Do not imply authorization beyond the parent or user grant.

Legacy optional fields remain valid:

```yaml
profile_locator: path-or-resource-for-the-active-development-profile
repository_adapter: exact-skill-name-or-null
required_skill: exact-skill-name-or-null
```

When a task needs a Skill, supply its exact name and accessible locator. Null is valid when no specialized Skill is needed and the governing design and repository rules are sufficient. Supply an escalation reason for an elevated writer; missing evidence or permission never justifies model escalation.

## Child-To-Parent Result

Return the outcome and completion status, material findings with evidence, changes and checks if any, unresolved blockers, and recommended next decision. Use the old result schema when a consumer requires it; do not fill empty administrative fields for appearance. Distinguish completed work from partial or blocked work.

The parent verifies material claims, compares changed paths with the allowlist, resolves conflicts, and assigns the final adoption classification. Children are not alone in the codebase: preserve others' edits and report unexpected overlap.

## Stop Rules

Return `complete` when acceptance conditions are satisfied. Return `partial` on budget exhaustion with unfinished work, or `blocked` when required evidence or permission is missing, sources conflict materially, the Skill is unavailable, a write escapes allowed paths, a mandatory check unexpectedly fails, or a parent/human decision is required. Never expand scope merely to avoid a blocked result.
