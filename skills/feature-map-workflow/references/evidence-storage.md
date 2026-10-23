# Audit-ready evidence storage

Use this route when evidence must remain traceable after a chat, worktree or test
environment is gone. Keep the existing test runner and Result v1 contract from
[AI-assisted Testing](ai-assisted-testing.md). This adds preservation and an audit
index, not another test runtime or approval authority.

## Three locations, one lookup path

| Location | Owns | Rule |
| --- | --- | --- |
| Stable private evidence store outside disposable worktrees | Original result files, screenshots, logs, observations, sealed manifests | Copy selected files byte-for-byte; never move/delete originals or reuse run IDs |
| Project-owned internal catalog in its authorized repository | External test/condition IDs, exact plan/source baseline, run manifest hashes, applicability and gaps | One writer; changes are reviewable history; no credentials or raw customer snapshots |
| Customer deliverable | Business operations, input, expected/observed results, customer-safe evidence references | No local paths, environment/connection details, repository/Issue/PR IDs or internal aliases |

The audit route is **customer test number → individual condition → execution
identity → native result/check → actual sealed file**. A past run may appear as
a historical reference, without claiming it verifies the current condition.

Resolve the store root from a local configuration or explicit `--store`, not a
user-specific path in the reusable Skill. Choose a project-owned location that
survives worktree cleanup. Do not use the tool cache, chat attachment cache,
temporary output, or a shared mutable `latest/` folder as the original store.

```text
<private-store>/<project-id>/
  reservations/<run-id>.json
  runs/<run-id>/
    manifest.json
    evidence/<original relative paths>
  audit/<snapshot-id>/index.html
  audit/<snapshot-id>/index.json
<project-documents>/audit/catalog.json
```

`manifest.json` records project/run identity, sealing time, evidence category,
execution metadata, each relative path, byte length and SHA-256. The catalog
records the manifest hash too: rewriting a file and its manifest must not silently
match the registered snapshot. These are tamper-evident checks, not WORM storage,
a digital signature, a timestamp authority or proof against an attacker who can
rewrite both the catalog history and the store. Do not describe them as such.

## Apply at the existing workflow boundaries

1. **Design:** freeze customer test/condition IDs and the plan hash. Record the
   actual source baseline, storage owner, private store alias, retention/hold,
   backup state and evidence needed per condition. No result => `not-run`.
2. **Before execution:** confirm the authorized target and initial state in the
   private execution record; avoid repeating common setup. Do not put those
   details into the customer workbook.
3. **After each run:** keep native results and per-condition checks. Capture the
   observations, assertions, relevant state differences and cleanup outcome.
   On failure/blockage keep the first blocking frontier and diagnostic evidence.
4. **Seal:** copy only selected evidence into a new run directory and verify it.
   Failed imports remain `.pending-*`; they are not sealed runs. A reservation
   also prevents cooperating writers from reusing an in-progress run ID. Do not
   automatically retry, overwrite or erase an ambiguous partial import.
5. **Register:** add manifest hashes and scoped references to the internal catalog.
   Keep `historical`, `preparation`, `artifact-check` and `functional` separate.
   Record an unknown historical revision as unknown; never invent one.
6. **Audit/handoff:** validate file integrity and baseline, generate a searchable
   local index, and test opening representative raw files. Show missing results
   and applicability questions. Add only a representative catalog reference or
   blocker to Feature Map XML; the detailed registry stays outside the XML.
7. **Retention:** hold evidence through the agreed audit/acceptance period and
   unresolved disputes. No automatic expiry/deletion. Release a hold only under
   the project owner's explicit disposition and the existing cleanup authority.

Storage or reference integrity does not prove the test oracle, completeness of
observations, business acceptance or customer delivery. In particular, a saved
Excel, a build log or an overall run PASS does not make every condition pass.

## Existing-result integration and deterministic checks

`scripts/evidence_catalog.py` uses Python's standard library and never connects
to the application, DB, remote service or model. It has three bounded operations:

```sh
python scripts/evidence_catalog.py seal --request /private/import.json \
  --store /private/evidence --project fictional --run RUN-001
python scripts/evidence_catalog.py validate --catalog /private/catalog.json \
  --store /private/evidence
python scripts/evidence_catalog.py report --catalog /private/catalog.json \
  --store /private/evidence --case FT-01 \
  --output /private/evidence/fictional/audit/AUDIT-001
```

Omit `--case` for the full index; a condition number is also accepted. Reports
are private, derived, new-only output. The HTML has local relative links and no
remote assets. Regenerate a new snapshot after a catalog correction.

The seal request contains `sourceRoot`, `metadata.category`, and a nonempty
`files` array of `{path, sha256?}`. Source paths must be relative to that root.
When an existing run supplies hashes, pass them as `sha256`; reject a mismatch
before copying. No recursive discovery, source deletion or credential extraction
is performed by the tool. Paths, symlinks, Windows reparse points and duplicate
case-insensitive destinations are checked; source changes during copying fail.

The catalog contains `schemaVersion: 1`, `projectId`, `baseline` with
`sourceRevision` and `planSHA256`, `runs` with `{id, manifestSHA256}`, and `cases`
with `{id, title, conditions, references}`. Each condition has an external `id`
and `status`. References specify `{runId, paths, note}`; the note states the
actual covered boundary and why it does or does not apply to the current plan.

For an executed condition, `execution` identifies `runId` and sealed
`resultPath`. Its manifest category must be `functional` and its source and
plan hashes must match the baseline. The native Result v1 file must match run,
source and `verifyCaseId` (default: case ID; an internal mapping is allowed in the
catalog only). Add `checks[].conditionId` for the individual external condition,
with matching `status` and nonempty `evidence`. Check evidence paths are relative
to that original result file. Run-wide PASS alone is rejected. This optional
field does not change existing result producers or the Feature Map XSD.

`not-run` has no execution claim. Historical/preparation/artifact-check data can
be referenced but cannot satisfy a current execution. New revision/plan changes
require a new applicability decision and result; do not rewrite old results.

## Privacy, backup and recovery

Keep originals only in the authorized private store. Inspect sensitive content
before granting access or exporting it. Preserve any necessary redacted copy as
a distinct derived artifact linked to the original hash; never silently alter
the original. Do not commit or send raw screenshots, traces, credentials or
customer data to a public repository. The index may itself be confidential.

A stable local directory is **not an off-device backup**. Record backup status
as `unconfigured`, `copied-unverified` or `restore-verified`, with destination
alias, copied snapshot hashes, owner and the last restore-check reference.
At a run-finalization or handoff boundary, copy sealed runs and the corresponding
catalog snapshot to an approved separate device/service, verify hashes, then
reopen representative files from the restored copy. A second folder on the
same disk is not that backup. Do not configure services, credentials, schedules,
retention deletion or external transfers without their own authorization.

Until that operation is actually evidenced, show the missing backup/recovery
boundary in the audit index. Check access controls for the selected store; an
unverified inherited ACL is not a claim of restricted access. Published policy,
read-only file attributes and a Git commit do not prove server-side immutability.

### Report and recovery proof constraints

Reports may create only a new snapshot below `<store>/<project>/audit/`; output
inside any sealed run or another project is rejected. The catalog bytes used for
validation also supply the report hash. JSON and HTML retain the baseline,
condition ID, native case ID, run ID, result path and each check evidence path.

`restore-verified` requires a sealed `receipt: {runId, path}` in `backup` and a
nonempty `destinationAlias`. The receipt JSON must contain `schemaVersion: 1`,
`type: "backup-restore-receipt"`, matching `projectId` and `destinationAlias`,
`owner`, `checkedAt`, `restoreCheck: "passed"`, and `restoredManifests` mapping
all catalog run IDs except the receipt run itself to their exact manifest hashes.
Adding a new run invalidates that complete-snapshot claim until recovery proof
covers it. Validation checks the recorded receipt; it does not probe the backup
service or infer that a storage location is available now.

`copied-unverified` likewise requires destination alias and a sealed receipt,
using `type: "backup-copy-receipt"`, `copyCheck: "passed"` and
`copiedManifests` in place of the restore fields; `owner`, `checkedAt`, project
and all covered manifest hashes are mandatory. This proves only the recorded
copy operation, not recovery. A bare status string is rejected.
