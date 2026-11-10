# Workspace Profile Contract

This contract reuses an existing workspace development profile. It is a mapping
of local policy and tools, not a second project record. It does not introduce a
new mandatory file format, database, service or parser dependency.

## Resolve

1. Read the active repository and workspace instructions, then use their explicit
   development-profile locator. User and repository instructions override profile
   defaults. If no profile is configured, use generic FMW with the repository's
   own rules; do not invent a client-specific default.
2. For an existing profile, resolve `workflow.common_skill` to
   `feature-map-workflow`; this identifies the current entrypoint and must not
   invoke FMW recursively. Resolve any adapter or profile skill only when it is a
   non-recursive workspace mapping or repository-specific procedure. If both keys
   identify the same skill, load it once. Do not invoke a retired development
   workflow, or route an adapter back to FMW.
3. Map `lifecycle`, `quality_gates` and `workflow.gate_policy` onto the existing
   FMW phases by evidence and actual decision mode. Use a configured
   `lifecycle.fmw_phase_mapping` when present. Phase IDs are navigation; a gate is
   not automatically passed when a phase is visited. Missing gate policy preserves
   existing project rules rather than waiving an established approval.
4. Resolve `standards.common_skill`, the applicable document profile, `estimation`,
   `documents`, `paths`, `workflow.repository_adapter`, semantic
   `workflow.child_skills`, and optional `system_analysis` from the workspace.
   Keep document IDs, customer terms, paths, encodings, estimation units and
   saved-connection aliases in the workspace; never copy credentials or originals.
5. Resolve `source_of_truth` before writing mutable project facts, approval
   references or estimate history. Apply a scope-specific override only when its
   eligibility is established. Preserve existing project authorities; a new chat
   or issue is not proof of a new project. If eligibility or a required mapping is
   unknown, stop only the affected store write and report the missing decision.
6. Resolve optional `workflow.agent_roles` and limits only when delegation is
   authorized by the user and runtime. Use the lower applicable limit and one
   writer per worktree. A missing role does not authorize a different client's role
   or data store; the parent may perform work within its own authority.
7. Use the workspace's actual `workflow.policies` for optional flow, security and
   lifecycle controls. They never waive explicit legal, contractual, repository,
   security, privacy, user or project obligations.

## Ownership and compatibility

- Keep accepted requirements, design and acceptance in the established project
  authority, including `DESIGN.md` where that workspace requires it. Keep code,
  test results, original approvals and commercial information in their own stores.
- A scope-specific project-store override must be propagated to every child that
  writes project facts. A default-only client must not write a scoped project.
- A specialized capability may be called directly from its mapped skill or
  repository procedure. If unavailable, use only an authorized documented
  fallback; report unperformed work rather than inventing a substitute.
- Migrate consumers and validate their discovery and routing before retiring an
  old workflow. Preserve the original profile, version, dependencies and recovery
  procedure in an archive outside active discovery. A migration does not grant
  authority to modify unrelated projects or change their established decisions.

For optional profile shape, role fallbacks, investigation and security mappings,
see [Workspace Profile Examples And Compatibility](workspace-profile-examples.md).
