# Unified Development Workflow

Use Feature Map Workflow as the single development entrypoint. Its existing
feature-sized lifecycle remains the common sequence; project profiles supply
local stores, gate mappings and operational adapters. This guidance routes work;
it does not implement a scheduler, create approval authority or replace the
existing systems of record.

## Project, intent and knowledge

1. Identify the existing project, owner, repository, base revision, authorized
   scope, exclusions, relevant original request and acceptance source. A new chat
   or issue is not automatically a new project. Reuse existing work locations.
2. For each development project, maintain at least one Feature Map. Reuse current
   maps; split independent business features when useful. Do not bulk-create maps
   in unrelated projects. A read-only investigation does not authorize file writes:
   report a missing map and prepare its creation for authorized project work.
3. Gather only prior specifications, answers, decisions, versions, source, tests
   and runtime evidence needed for the present decision. Check their applicability;
   distinguish observed behavior, approved intent, inference and unknowns. Preserve
   existing behavior outside the accepted change. Do not convert an old concern
   into a new requirement or customer commitment without authorization.
4. Accepted requirements and acceptance remain in their existing authority; a
   workspace may designate `DESIGN.md`. Source/tests and actual results own
   implementation evidence. The map preserves reusable feature knowledge and
   references; it does not approve the specification or replace original evidence.
5. Update only confirmed affected map knowledge when an authorized change makes it
   stale; preserve stable IDs and unrelated nodes. Validate changed XML against its
   applicable XSD. Format validation is not a product test or acceptance.

## Resolve the workspace profile

Read [Workspace Profile Contract](workspace-profile-contract.md) before routing
project work. Use the selected repository's instructions and explicit profile;
never select a client, database, owner, template or connection by guesswork.
The profile maps the FMW entrypoint to local rules and specialized skills, not to
another development-workflow entrypoint. If a required mapping is absent, stale,
or recursively routes back to a workflow, stop the affected routing or store write;
continue independent read-only investigation and report the gap. Generic FMW use
without a workspace profile remains available under the actual repository rules.

## Advance one useful slice

Use [Development Lifecycle](development-lifecycle.md) phases as lookup keys, not
mandatory serial handoffs. Resolve the workspace's gate names and evidence from
its profile. A gate is an evidence checkpoint or a human decision according to the
applicable profile and existing project, contract, repository and user rules.

1. Resolve unstable scope through intake and unclear behavior through evidence-led
   system analysis. Ask only for facts or decisions that cannot be established
   from applicable sources and materially affect the next action.
2. Freeze the accepted scope and relevant design snapshot. Route design intent to
   its existing authority, estimates to the commercial source, and work/ownership
   to the authorized project store. A phase transition does not require a new
   document. Create detailed artifacts only for an actual obligation or review need.
3. Design, implement and verify the smallest safe business slice. Load repository
   editing, encoding, database, history and delivery rules inside the writer.
   Preserve atomicity where partially applied state would be unsafe.
4. Select tests for changed guarantees and concrete affected paths. Reuse suitable
   evidence and environments; check each case's prerequisites and interference,
   adjusting or restoring only the required state. Continue independent runnable
   cases when another case is blocked. A plan, setup or schema check is not a test.
5. Review the actual diff and results. The parent performs the ordinary review;
   use independent review for material risk, configured triggers or binding
   obligations. Preserve existing project and repository review requirements.
6. For delivery, identify the tested candidate, applicable migration/recovery,
   residual risk and required decision before the authorized operation. Record
   prepared, tested, submitted, accepted, deployed and integrated separately.
   A prepared draft does not authorize external transmission or publication.
7. After delivery, record incidents, actuals, handoff and retained evidence when
   applicable. Archive under the responsible workspace's retention policy.

At consequential client decisions or blockers, provide a concise evidence-backed
communication. At system-understanding questions, explain the relevant scenario,
data and state path at the requested depth. Neither track creates a mandatory
document or extra approval. Optional specialized skills are selected by semantic
role from the profile; they do not become competing development workflows.

## Decisions, failures and retained state

Keep one owner for the business outcome. An evidence checkpoint records its
snapshot, result, evaluator and outstanding conditions; never invent a human
approver. A required human decision records the actual decision owner, candidate,
time and conditions. Reuse authorization that already covers the same scope and
operation. Material evidence changes supersede only affected decisions and tests.

For incidents or defects, apply [Defect Feedback Loop](defect-feedback-loop.md)
when relevant; record the affected behavior, evidence, containment, correction,
regression and residual-risk disposition in the existing sources.
Stop only affected work for unexpected mandatory failures, critical unknown impact,
unsafe state or missing required decisions; independent safe work may continue.
For a critical incident, resume affected work only after containment, affected
requirements and checks, residual risk and the required human restart decision
are established. Record whether preventive action and an effect check are needed.
When retained files, data, logs, queues, retries or backups can accumulate, check
ownership, bounded retention, cleanup, failure recovery, capacity and operational
handoff; test an accumulated state when that risk makes it necessary. Use the
conditional [Lifecycle Quality Review](lifecycle-quality-review.md) for details.

When the workspace enables [Lean Flow](lean-flow-policy.md), let ready work be
pulled according to actual downstream capacity. Establish scope, acceptance, inputs, owner,
dependencies and a verification path before marking an item ready. Prefer small
reviewable slices without breaking safe transaction boundaries; record blockers
and recurrence prevention in existing records. Do not invent universal WIP limits,
metrics, documents or human gates.

Delegate only where the active user and runtime instructions permit it and a
bounded assignment adds value. Use the conditional [Development Delegation
Contract](development-delegation-contract.md) for role and packet details. Keep one writer per worktree, give any reviewer the
actual immutable inputs, and leave adoption and the final decision with the parent.
Do not create a new agent, approval, artifact or metric merely because a phase exists.

For migration or routing changes, use the synthetic [Development Workflow
Evaluation Cases](development-workflow-evaluation-cases.md) where relevant;
case outcomes are not a substitute for actual test or acceptance evidence.
