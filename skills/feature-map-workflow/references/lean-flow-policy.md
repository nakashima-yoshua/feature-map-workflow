# Lean Development Flow Policy

Apply this optional policy only when enabled by the active workspace profile. It controls flow; it never replaces contractual, regulatory, safety, repository, deliverable, or human-gate requirements.

## Pull And Ready

- Let downstream capacity pull work only when the item is ready.
- Derive WIP limits from actual implementation, review, and test capacity; do not invent a universal number.
- Require confirmed value and scope, acceptance conditions, inputs, dependencies, owner, bounded output, verification path, and recorded blockers before Ready.

## Small Batch

- Prefer the smallest reviewable, testable, and operationally safe slice.
- Align requirement, design, implementation, test, documentation, and release evidence for the same slice.
- Keep deferred scope visible and avoid unsafe partial-state or migration boundaries.

## Stop And Correct

- Treat unexpected mandatory failures, final red tests, release blockers, missing acceptance evidence, critical incidents, data-integrity risk, business stops, and unknown blast radius as stop signals for the affected flow.
- Record signal, affected work, detection time, evidence, owner, containment, unblock condition, and restart decision.
- Prefer recurrence prevention through an existing test, validation, type, constraint, template, checklist, or verified automation point.

## Improve

Use cycle time, blocked time, rework, escaped defects, and WIP trends to improve the process, not rank people. Promote a standard change only after evidence or an authorized process decision.
