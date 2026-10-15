# Three Complementary Views for Business-System Understanding

## Purpose

For an unfamiliar or legacy **data-backed business feature**, combine three small, evidence-backed views:

| View | Answers | Existing XML representation |
| --- | --- | --- |
| **Business flow** | Who triggers the feature? What decisions, outcomes and exceptions matter? | `diagrams/diagram kind="flowchart"` with Mermaid `flowchart TD` |
| **Data flow** | What enters/leaves each process? Which data stores, procedures and external interfaces are read or written? | `diagrams/diagram kind="flowchart"` with Mermaid `flowchart LR` |
| **ER diagram** | Which entities/keys/relationships support this particular feature? | `diagrams/diagram kind="er"` with Mermaid `erDiagram` |

Use distinct titles and stable IDs such as `DG-BUSINESS`, `DG-DATA` and `DG-ER`. The **same `useCase` ID and the same data object names** must connect the three views. The existing XSD 1.3 and XSLT already support both Mermaid forms and render diagrams in the collapsed Diagrams section; do not add a DFD-specific XML type, another document, a database connector or a new renderer.

Three views are a *recommended set when they each explain a material question*, not a quota: omit an obvious or irrelevant view and say why. Do not draw every screen, class, column or schema table.

## Procedure

1. **Define the slice and basis of evidence.** Select one business feature and representative use case (`UC-...`). Read existing Feature Map first. Record the trigger, outcome, error path and in/out scope. Investigate connected dependencies only until the scenario can be explained and changed safely. The *understood* flow may be wider than any authorized *migration*.
2. **Trace facts before drawing.** Walk from UI/API/EXE/job entry through source, SQL/PLSQL, procedures, DB writes and external calls. Prefer read-only source and schema metadata. Identify affected tables/views, declared PK/unique/FK constraints, and columns relevant to decisions and effects. Check runtime trace or DB before/after only in an isolated, explicitly authorized environment. Do not execute unapproved SQL writes or connect to production simply to draw a diagram.
3. **Business flow (why / when).** Draw actor/trigger → decision points → business result and consequential exception. Use business language, not a call graph. Base decision rules on `knowledge/rule` and `useCase`. Preserve important observed-vs-intended differences under `open`.
4. **Data flow (what moves / changes).** Draw the processes and *named payloads* crossing application, DB, file, queue and external boundaries. Label read/write and significant transaction boundaries. Use actual SQL/query, procedure, API or observable side effects as evidence. A data-flow edge does **not** imply a foreign key or successful runtime observation.
5. **ER (how the persisted data relates).** From read-only schema/catalog metadata, draw only tables relevant to the use case, plus the nearest necessary master/association tables. Include PK/FK and only key business-decision columns. Check join predicates, views, triggers and dynamic SQL separately: a SQL JOIN is **not** proof that an FK constraint exists. Mark a verified but unenforced logical join explicitly in the relationship label (e.g., `"logical JOIN; no FK"`) *only if cardinality itself is supported*. If cardinality, join key, or physical FK status is not established, **do not invent a relationship**; add an `open/item` with the cheapest confirming step.
6. **Reconcile the views.** Follow each important business outcome: **UC → flow decision → data process / external effect → table & key (ER) → sourceMap ref → representative verify/case**. Confirm no modeled DB write lacks a business scenario, no data-flow store is silently substituted with an unrelated ER entity, and the ER relationships are consistent with the known joins and declared constraints. Treat missing evidence as unknown, not as a successful verification.
7. **Persist only durable knowledge.** Add just the representative three Mermaid definitions to the feature's existing XML `diagrams`, using CDATA and `title` to identify role and `UC` linkage. Keep code/table/procedure/test navigation in `sourceMap/ref`, domain rules in `knowledge`, reproducible observations in `verify/case`, and uncertainties in `open/item`. Keep full DDL, column catalogs, test data, runtime traces and screenshots with their native source/evidence files; do not embed them in the diagrams or final HTML.

## Evidence rules by database

- **Oracle**: inspect authorized schema dictionary data for table/column definitions, keys and constraints; additionally inspect views, PL/SQL, synonyms, triggers and any DB-link dependencies used by the selected path. Resolve synonyms/aliases before asserting a table relationship.
- **PostgreSQL**: inspect `pg_catalog` / `information_schema` metadata in read-only mode, plus relevant views, functions, triggers and application SQL.
- **DB2**: inspect the appropriate platform's system catalog (for example `SYSCAT` on Db2 LUW), plus SQL/SQL PL, views and application/batch SQL. Catalog names differ across Db2 platforms; do not assume a Db2 LUW query works on Db2 for i or Db2 z/OS.
- **Any DB**: a *declared FK* is a catalog fact; an *application-level relationship* may be evidenced by stable keys and SQL joins but is not an enforced FK; *assumed* relations remain unresolved. Master/config flags may choose runtime paths not visible from schema alone. Capture source references and the basis for each non-obvious link.

If database access is unavailable, read versioned DDL/schema scripts and source SQL with provenance; label the diagram as **source-derived / not runtime-confirmed**. If neither metadata nor reliable source supports a relationship, leave it out. Never claim that a model-derived diagram is an authoritative schema snapshot.

## Lightweight review and stop conditions

- The feature and UC are the same across the three views; map boundaries and important effects align.
- At least one inspectable `sourceMap` reference backs relevant code and DB objects, or unresolved dependencies are explicitly `open`.
- ER cardinalities/FK status are not invented; logical joins without physical FKs are not presented as enforced constraints.
- Normal and consequential exception paths, transactions and side effects are represented to the extent needed for the requested change.
- Unknown business meaning, permission to access the database, or disputed intended behavior blocks **claims of verification** and any affected migration, not harmless documentation of established facts.
- XML passes the existing XSD check; the XSLT produces three separate titled Mermaid blocks when supplied, with no new schema/runtime dependency. Render in a Mermaid-capable browser if available before claiming graphical rendering was visually verified.

Do not overwrite a broader existing diagram when adding a narrow one. Retain stable IDs, avoid duplicate entities across feature maps where references suffice, and update only the affected view when a future feature change warrants it.

## Fully fictional example

See [`examples/fictional-stock-request/feature-map.xml`](../../../examples/fictional-stock-request/feature-map.xml). The example demonstrates how the three views share a single `UC-SUBMIT` and the `REQUEST`, `REQUEST_LINE` and `ITEM` names while making **no claim** that a real database exists or that its behavior has been tested.
