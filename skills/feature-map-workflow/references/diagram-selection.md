# Purpose-driven Diagram Selection

Choose diagrams for the **question being investigated**, not to meet a fixed diagram count. Every generated view must be grounded in source, schema, approved requirements, or reproducible evidence. Prefer an existing diagram and update only its materially changed slice. This guide extends, rather than replaces, [Three Complementary Views](three-view-understanding.md) and [Human Work Direction](human-work-direction.md).

## Candidate catalog (17 views)

| View | Question | Representation |
| --- | --- | --- |
| Use case | Who wants which outcome? | `kind=usecase`, Mermaid flowchart for broad compatibility |
| Activity | Which decisions and paths matter? | `kind=activity`, Mermaid flowchart |
| Sequence | Which calls/payloads occur in what order? | `kind=sequence`, Mermaid sequenceDiagram |
| State | Which transitions are permitted? | `kind=state`, Mermaid stateDiagram-v2 |
| ER | Which persisted entities and verified keys relate? | `kind=er`, Mermaid erDiagram |
| Data flow (DFD) | Which payloads enter, transform, and leave? | `kind=flowchart`, titled Data Flow / データフロー |
| Data lineage | Where did a field originate, and how was it transformed? | `kind=flowchart`, titled Data Lineage / データリネージ |
| System context | Which actors/external systems cross the boundary? | `kind=architecture` or flowchart, title システムコンテキスト |
| Component | Which components own responsibilities? | `kind=architecture` or flowchart, title コンポーネント |
| Dependency | Which callers/callees are impacted? | `kind=flowchart`, title 依存関係 |
| Deployment | Where does each runtime live? | `kind=architecture` or flowchart, title 配置図 |
| Class | Which objects/types and responsibilities matter? | `kind=class`, Mermaid classDiagram |
| Decision table | Which combinations lead to which outcomes? | Existing referenced Markdown table preferred; diagram only if useful, title 決定表 |
| CRUD matrix | Which feature reads/creates/updates/deletes which store? | Existing referenced Markdown table preferred; diagram only if useful, title CRUD |
| Traceability | Which use case, source, test and evidence correspond? | `kind=flowchart`, title トレーサビリティ |
| Timing | Which wait/time boundary matters? | `kind=sequence` or flowchart, title タイミング図 |
| Batch/job dependency | What starts after what, and what is blocked on failure? | `kind=flowchart`, title ジョブ依存 |

These are **candidate notations**, not 17 required generated artifacts. Labels in the title disambiguate specialized views without introducing schema kinds or a new renderer.

## Selection rule

1. Start with the target `useCase`, purpose, and a concrete question from the change or verification cases.
2. Trace code, tests, configuration, SQL and read-only DB metadata; keep observations, assumptions, and approved expectations separate.
3. Prefer a data-bearing **sequence diagram** when order and named payloads both matter. Keep a DFD when many stores/transformations matter without order. Use lineage when provenance or column-level transformations matter. Do not merge these views mechanically.
4. For database changes consider ER + CRUD, and dependency/lineage only when their additional questions are material. Never infer physical FK/cardinality from a JOIN.
5. For branch-heavy testing consider activity, decision table, state and traceability. Matrix/table representations may remain external documents and be referenced rather than embedded as Mermaid.
6. Choose a minimal set of **existing evidenced diagrams** for human briefs. The selector may recommend a role but must not fabricate it. `--diagram` explicitly selects scoped existing diagram IDs.
7. Reconcile diagrams via stable use-case IDs, exact DB/source object names and `sourceMap`/`verify` references. Record unsupported paths under `open` with a confirming action.
8. Avoid diagram sprawl: retire stale diagrams, do not duplicate obvious code, avoid unbounded raw SQL, and leave unrelated feature maps untouched.

## Examples of purpose selection

| Purpose | Useful starting candidates |
| --- | --- |
| Feature overview | Use case, context, activity |
| Payload/process tracing | Data-bearing sequence; DFD for broad routes; lineage for provenance |
| DB change impact | ER, CRUD matrix, dependency graph |
| Functional verification | Activity, decision table, state when relevant, traceability |
| External integration or batch | Context, sequence, batch dependency, timing when necessary |

## Compatibility and verification

Keep existing Feature Map XSD v1.3, `diagrams/diagram` and its allowed `kind` values unchanged. The focused brief classifies specialized diagrams by **title** and selects only those already in XML. A title is presentation metadata, **not evidence**. Tests should cover title role classification, focused use-case filtering, no fabrication, explicit overrides, and absence of regressions for generic diagrams. Render the actual Mermaid in a compatible viewer before claiming visual verification.
