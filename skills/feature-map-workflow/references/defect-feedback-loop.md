# Defect Feedback Loop

Convert a defect or incident into workflow evidence instead of treating it only as an implementation task.

## Classify

Record:

- defect or incident ID;
- source phase and detection phase;
- affected requirement, design, implementation, test, release, and operation scope;
- missing review and test viewpoints;
- containment, corrective action, preventive action, and effect check;
- residual risk and client explanation need;
- standard, checklist, or reusable failure-case candidate.

## Route

1. Route evidence gaps to the configured review Skill.
2. Resolve root-cause, CAPA, incident, operational-quality, and regression document roles through the workspace document profile.
3. Add lifecycle, performance, logging, recovery, and accumulated-state viewpoints when applicable.
4. Bind the correction to affected requirement and design snapshots.
5. Mark prior gate decisions `superseded` when their evidence changed.
6. Persist mandatory defect and CAPA evidence before closure.

## Immediate Stop

Stop the affected implementation and release flow for a critical or major incident, production data-integrity risk, business stop, unknown blast radius, or missing containment owner. Continue unrelated safe work only when dependencies and capacity allow it.

Do not restart until impact is bounded, corrected requirements or design are reviewed when affected, mandatory verification is green, residual risk is recorded, and the authorized human records the restart decision.

## Complete

Do not close the loop until the source and detection phases are classified, review/test coverage is dispositioned, CAPA necessity is decided, required evidence is persisted, and the effect-check owner and method are known.
