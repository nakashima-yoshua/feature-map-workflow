# Optional OKF reference export from Feature Map XML

Feature Map XML remains the canonical **per-feature** knowledge. The optional exporter
creates a small, **draft-only** Open Knowledge Format v0.2 Markdown concept for
cross-project navigation. It does not change the XML, duplicate its full rules,
validate the truth of those rules, execute tests, or grant approval.

## Export one approved source revision

Run after validating the exact Feature Map and obtaining its actual Git commit SHA.
The example below uses placeholders: supply real authorized paths and the pinned URL.

```sh
python skills/feature-map-workflow/scripts/export_okf_reference.py \
  --xml path/to/feature-map.xml \
  --source-url https://git.example.net/team/project/blob/<40-hex-commit>/path/to/feature-map.xml \
  --revision <40-hex-commit> \
  --output path/to/okf-bundle/concepts/my-feature.md
```

The script validates against the bundled `feature-map.xsd` (override with `--xsd`),
reads only `meta/system`, `meta/feature`, and `goal/purpose`, and writes a new file
with `status: draft`, `generated`, and a revision-pinned `sources` entry.
It refuses to overwrite an existing output. `--generated-at` can fix an ISO 8601
timestamp to make regeneration reproducible. The source URL must be HTTPS and contain
the specified commit SHA as a path segment; this enforces *pin syntax*, not
external source authenticity.

After export, manually place the concept in an OKF bundle and link it from the
bundle's `index.md` and `log.md`. Let that bundle's owner run its own OKF lint and
source review. A passed lint verifies metadata/links, **not** business truth.
Do not invent a `human:` verification event or mark `stable` without an actual
reviewer checking the pinned original.

No OKF package, AI service, network access, or ADS/quality-gate dependency is
introduced to the Feature Map Core. Existing XML/XSD v1.1/v1.2/v1.3 and FMW
human-facing HTML remain unchanged. Never feed generated HTML back as data.
