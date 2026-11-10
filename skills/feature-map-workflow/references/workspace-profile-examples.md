# Workspace Profile Examples And Compatibility

# Workflow Profile Contract

Use a mapping-only workspace profile. Keep project facts, credentials, customer source material, and mutable approval state outside the profile.

## Minimum Shape

```yaml
profile_id: example
profile_version: 1

lifecycle:
  phases: []

quality_gates: {}
documents: {}

workflow:
  common_skill: feature-map-workflow
  adapter_skill: example-development-profile
  profile_skill: example-development-profile
  repository_adapter: example-repo-operating-rules
  child_skills:
    request_intake: client-request-intake
    requirements_document: client-requirements-md-writer
    system_analysis: legacy-system-analysis
    design: design-document-bootstrap
    review: review-readiness
    effort_estimate: effort-estimate-writer
    development_plan: development-plan-writer
    work_breakdown: work-breakdown-writer
    progress: progress-tracking-writer
    manual_test: manual-test-runbook-and-data
    test_evidence_excel: client-test-evidence-excel-writer
    archive: current-system-archive-packager
    work_documentation: work-documentation-guide
    client_communication: client-communication-support
    system_understanding: system-understanding-support
    delivery_communication: client-delivery-email-draft-ja
  agent_roles:
    evidence: example_evidence_worker
    analysis: example_analysis_worker
    design: example_design_worker
    planning: example_planning_worker
    change: example_change_worker
    verification: example_verification_worker
    documentation: example_documentation_worker
    communication: example_communication_worker
    review: example_review_worker
    read: example_read_worker
    write: example_write_worker
    advisor: example_advisor
  limits:
    max_parallel_readers: 2
    max_active_children: 3
    max_depth: 1
    max_active_writers: 1
  gate_policy:
    default_mode: evidence_checkpoint
    human_decision_gates: [GATE-50]
    existing_project_decisions: preserve
  policies:
    lean_flow: false
    lifecycle_review: conditional
    security_assurance:
      default_level: standard
      dedicated_requirements: required_when_applicable
      dedicated_design: required_when_applicable
      dedicated_review: required_when_applicable
      dedicated_verification: required_when_applicable
      standalone_deliverable: conditional
      estimation:
        security_specific_work_items: included_when_applicable
        security_contingency: included_when_evidenced
      retained_controls:
        secret_and_credential_protection: true
        existing_authentication_authorization_regression: true
      activate_stricter_controls_when:
        explicit_approved_security_scope: true
        legal_or_contractual_security_obligation: true
  document_policy:
    design_authority: DESIGN.md
    additional_documents: evidence_triggered
    additional_document_triggers:
      explicit_contract_or_client_submission: true
      legal_or_regulatory_obligation: true
      independent_approval_audience: true
      high_cost_executable_operation: true
      scale_or_complexity_requires_separate_review: true

source_of_truth:
  mutable_project_facts: authorized-project-store
  approvals_and_audit: authorized-project-store
  code_and_sanitized_documents: version-control
  estimation_history: configured-estimation-store

adapters: []
```

## Resolution Rules

1. Explicit user and repository instructions override profile defaults.
2. Resolve customer document IDs and requiredness from the document-standard profile, never from the common workflow.
3. Resolve a child by semantic key. The concrete Skill name may differ by workspace.
4. Treat agent-role mappings as optional. Prefer `evidence`, `analysis`, `design`, `planning`, `change`, `verification`, `documentation`, and `communication` when configured. Use `read` as the compatibility fallback for `evidence`, `analysis`, and `communication`; use `write` as the compatibility or explicitly elevated fallback for the write roles.
5. If a named role is unavailable, keep work in the parent or use an authorized built-in role with the same access boundary.
6. Apply the lower of runtime limits and profile limits.
7. Treat missing systems-of-record mappings as blockers for persistence, not permission to write elsewhere.
8. Resolve `workflow.repository_adapter` before delegating a repository write. Invoke database, encoding, or release adapters only when their scope is active.
9. Never put model slugs in this contract. Model selection belongs to installed agent configuration.
10. Use the established requirements and design authority, including `DESIGN.md` when the workspace requires it. Change size affects evidence depth and optional artifacts, not the source-of-truth model.
11. Select additional documents only from actual trigger evidence and the active document profile. Record purpose, owner, source references, maintenance trigger, and supersession rule.
12. Keep customer document IDs in the document profile. A detailed artifact may expand the established design topic but must not become an unlinked competing authority.
13. Invalidate only decisions and evidence affected by a change. Repeat the scope decision when scope, exclusions, expected results, cost, or decision ownership changes.
14. Resolve `workflow.policies.security_assurance` before selecting security-specific requirements, design, review, verification, deliverables, or estimate items. A workspace may set a relaxed default only in its approved profile; do not use that setting to relax privacy, legal, contractual, secret-handling, or existing access-control regression obligations.
15. Treat `activate_stricter_controls_when` entries as OR conditions. When one is evidenced, record a scope decision before adding the affected activities, deliverables, or estimate items; do not silently absorb them into an accepted estimate.

## Conditional Detailed Documents

The document profile may retain customer IDs and detailed-document roles. Set them optional by default and attach stable `required_when` or `condition` evidence. A selected detail document derives its scope from the established design authority, links implementation evidence instead of copying it, and records how it is superseded. Contractual commercial documents remain a separate authority.

## Optional Reusable-Document Mappings

Configure these keys when the corresponding common Skill is enabled:

```yaml
documents:
  design_master_role: design_master
  requirements_master_role: null
  delivery_email_role: example_delivery_email_draft

paths:
  current_system: knowledge/current-system
  project_package: "docs/{YYMMDD}{TYPE}_{topic}"
```

`client-requirements-md-writer` targets `documents.design_master_role` through the active document profile. `requirements_master_role` is a version 1/2 compatibility fallback only. `client-delivery-email-draft-ja` resolves `documents.delivery_email_role`. `current-system-archive-packager` and `work-documentation-guide` resolve their locations from `paths`. A missing mapping is a fallback or blocker defined by the called Skill, never permission to borrow another workspace's value.

Profile-template insertion by `client-requirements-md-writer` requires the documented Japanese semantic section headings. A workspace using a different language or section structure must provide an approved token template; the common workflow must not infer insertion boundaries.

## Compatibility

### Optional current-system investigation settings

`system_analysis.default_domains` is a nonempty list of unique logical domain names. `system_analysis.investigation_reference` is a workspace-root-relative path to the workspace-owned investigation standard. Configure both together. Keep client domain names and path candidates in the workspace, never in the common workflow or agent definition.

Before current-system investigation, the common workflow passes the resolved settings, profile locator, and explicit user scope overrides to the configured analysis Skill. The analysis Skill also resolves them on direct invocation. First assess all configured domains for relevance, then deepen relevant traces and follow evidenced dependencies beyond the defaults. Record explicit exclusions instead of overriding the user's requested scope. Reconcile each domain's evidence or unknowns before adopting the result; no separate document or human gate is introduced by this setting.

If the section is absent, retain request-driven investigation. If a configured reference is missing, report that mapping gap and continue independent evidence collection with the known domain list; do not claim complete application of the workspace standard. A logical domain may share physical files with another domain. Resolve the actual product root from repository evidence whether invoked at workspace or nested product level, rather than blindly appending a product prefix.

### Existing profiles

Profiles without `workflow` remain valid for document selection but are not sufficient for automated workflow routing. A client adapter may supply the missing routing during migration. Migrate and verify affected consumers before retiring an old workflow entry or folder.

## Continuous Execution And Support

`workflow.gate_policy` distinguishes evidence checkpoints from human decisions for newly planned work. Read [Unified Development Workflow](unified-development.md) for precedence, existing-project preservation, required operation decisions, and recording. Missing policy preserves the older profile's established gate rules. Explicit project obligations override the default.

The optional `client_communication` and `system_understanding` child mappings default to the common Skills shown above. They work without a client delivery template; formal delivery email still requires its own approved mapping. These are parent-owned support capabilities, not mandatory agent assignments or additional documents. Missing customer configuration never authorizes borrowing another client's values.
