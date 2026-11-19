---
name: parms-merge-sail-udb
description: Reconcile UDB and Sail parameters against the RISC-V ISA manual, produce provenance reports and class counts, and cluster unmatched classes into evidence-based future-development directions. Use when the user asks to merge or compare Sail and UDB parameter data.
---

# Merge Sail and UDB parameter definitions into DSL examples

Use these five environment variables as the skill's required input/output contract:

- `UDB_REPO`: UDB checkout; read-only input.
- `SAIL_RISCV_REPO`: Sail RISC-V checkout; read-only input.
- `ISA_MANUAL_REPO`: ISA manual checkout; read-only semantic reference.
- `SAIL_RISCV_BUILD`: Sail RISC-V build tree containing the generated config schema; read-only input.
- `PARMS_DSL_EXAMPLES`: the sole output directory for `unified.parm`, `summary.md`, `summary.json`, class and development-cluster Markdown files, and the generated `README.md`/`README.html`/`README.pdf` overview. It must point directly to the existing `unify-parms` subdirectory, where the previous output files have been moved; do not use its parent directory or create a nested `unify-parms/unify-parms`.

Require all five variables to be set to non-empty paths. Resolve them canonically and verify that the four inputs are readable directories and `PARMS_DSL_EXAMPLES` is the existing writable, traversable `unify-parms` directory. Confirm the repository roots and expected project structure by inspection rather than assuming particular file layouts. Stop on a missing, ambiguous, or mismatched path; do not substitute another checkout or output location. The output tree must not overlap any input tree (be equal to, inside, or an ancestor of an input).

Search all `*.adoc` files under the required `ISA_MANUAL_REPO` input. Use the config schema at `$SAIL_RISCV_BUILD/sail_riscv_config_schema.json`; do not substitute a different schema. Keep all four source inputs read-only.

Before analysis, record the Git branch and working-tree status for each source input that is a Git repository. Preserve all pre-existing changes. Never write, move, rename, delete, or change permissions under any of the four source inputs. Do not run commands that update their Git state. All run-generated files, temporary artifacts, and reports belong under `PARMS_DSL_EXAMPLES`; the reusable Venn helper is stored in this skill's `scripts/` directory. The intended outputs are `unified.parm`, `summary.md`, `summary.json`, `class-venn.svg`, `README.md`, `README.html`, `README.pdf`, the six standard class Markdown files specified below, and `no-udb-clusters.md` and `no-sail-clusters.md`; create `only-spec.md` or `none.md` only if those classes occur as specified below. Whenever `summary.json` is created or recreated, immediately regenerate `class-venn.svg` from that file before refreshing the README or its HTML/PDF versions. Do not create `report.md` or modify unrelated output files.

## Classify every UDB parameter

Inspect the `rv-parm` DSL and `appendix.parm` in `PARMS_DSL_EXAMPLES` first. Read the live UDB parameter YAMLs, schemas, Sail sources, config schema, and ISA manual directly; follow relevant local includes and references. Do not assume field meanings or DSL syntax from memory.

For every parameter record in YAML files recursively under `$UDB_REPO/spec/std/isa/param`, derive search terms from its `name`, `long_name`, and `description`. Search for the concept in every `*.sail` file under `$SAIL_RISCV_REPO` and in the Sail RISC-V config schema described above. Search the applicable `*.adoc` specification files under `$ISA_MANUAL_REPO` both for concept presence and for the normative rule that defines it. Confirm matches semantically; string hits alone are candidates, not proof. Use stable architectural identity and source-backed meaning, not similar names alone. Record source paths and line numbers or JSON pointers for evidence.

Assign one three-bit class to each parameter concept or Sail config leaf, with this exact bit layout:

- bit 0 (least significant): the concept is found in an AsciiDoc specification file;
- bit 1: the concept has a UDB representation. Normally this is a parameter YAML under `spec/std/isa/param`; for the Sail extension-support setting described in the reverse-sweep rule below, the corresponding extension YAML under `spec/std/isa/ext` is the UDB representation;
- bit 2: the concept is found in a Sail `*.sail` source or the config schema.

Compute the value as `(spec_present ? 1 : 0) | (udb_present ? 2 : 0) | (sail_present ? 4 : 0)`. For the UDB-first records, `udb_present` is always true; reverse-sweep Sail-only entries have it false. Preserve the full three-bit representation in the `class` field using syntax accepted by the `rv-parm` DSL; do not confuse its bit pattern with an unmarked decimal value. For example, bits `111` mean the concept is present in all three sources; bits `110` mean UDB and Sail present but no AsciiDoc mention; bits `100` and `101` are Sail-only classes without and with a spec match, respectively.

Track spec-presence separately from finding the required normative rule anchor: a concept mention can set bit 0 even when a normative anchor cannot be established. In that case, report the missing anchor rather than fabricating one. Likewise, set the Sail bit only when a source-backed concept match is established. Record unmatched, ambiguous, and conflicting evidence explicitly.

## Reverse sweep: Sail config leaves to UDB and spec

After the UDB-first pass, traverse the config schema at `$SAIL_RISCV_BUILD/sail_riscv_config_schema.json` and enumerate its parameter leaf nodes. Resolve schema references and nested object structure as needed; exclude structural containers that do not represent parameter values. For each leaf, derive its full dotted hierarchical name (for example, `base.xlen`) and retain its JSON Pointer and schema definition. Treat a leaf as already covered only when the first pass established a semantic mapping to that same Sail setting; a textual hit alone is not sufficient.

For each uncovered Sail leaf, first apply any representation-specific mapping rule, then compare its hierarchical name and schema meaning against the `name`, `long_name`, and `description` of UDB parameter YAMLs. Confirm approximate matches semantically and use architectural identity, not name similarity alone.

For a leaf whose full hierarchical name has the form `extensions.<EXTNAME>.supported`, treat it as an extension-support declaration, not as an ordinary UDB parameter. Check for the corresponding file `$UDB_REPO/spec/std/isa/ext/<EXTNAME>.yaml` (the sibling `ext` directory of `$UDB_REPO/spec/std/isa/param`, equivalently `$UDB_REPO/spec/std/isa/param/../ext/<EXTNAME>.yaml`). For example, Sail `extensions.Zimop.supported` maps to UDB `spec/std/isa/ext/Zimop.yaml`. If that exact file exists, its presence denotes UDB support for the extension: set the UDB bit, cite the extension YAML path and relevant identity/evidence, and do not classify the leaf as Sail-only just because no same-named parameter YAML exists. This mapping is specific to the exact `extensions.<EXTNAME>.supported` shape; do not infer it for other leaves or treat an unrelated similarly named file as a match. If the extension YAML is absent or its identity is uncertain, continue normal semantic matching and record the uncertainty rather than assuming a match.

For this special rule, the exact extension YAML path/name is itself the UDB representation (the file's presence denotes extension support); do not require a separate UDB parameter YAML or a field literally named `supported` inside the extension file. Inspect its contents only as needed to verify the extension identity or resolve a filename/alias mismatch.

For an ordinary leaf with exactly one matching UDB parameter, it must currently be in a UDB-present/Sail-absent class (`0b010` or `0b011`); add the Sail mapping to that UDB record, including the full hierarchical name, JSON Schema type, enum/const values, and relevant defaults or constraints present in the schema. Preserve the schema pointer as evidence and update the class Sail bit to 1 (`0b110` or `0b111`, according to spec presence). Do not create a duplicate record. If multiple plausible UDB matches exist, record the ambiguity and leave the affected UDB records unchanged pending resolution.

For an extension-support leaf matched by the extension-file rule, record one mapping entry for the Sail leaf and UDB extension declaration, unless that same concept is already represented by an existing unified record. Preserve its Sail schema metadata and JSON Pointer, identify the UDB counterpart as an extension declaration (not a parameter YAML), and classify it with the UDB bit set. Do not fabricate a UDB parameter identity or parameter-YAML fields.

If no UDB representation matches, create one Sail-only record in `unified.parm` and the appropriate class Markdown file (`0b100` if no spec match, `0b101` if a spec match exists). Use the full dotted schema name as the stable Sail identity and preserve its schema type, enum/const values, defaults, constraints, and JSON Pointer. Mark the record as Sail-only; do not fabricate a UDB YAML identity or UDB-derived content. Search the manual for the concept and, separately, for the AsciiDoc location where it is first defined or described rather than merely used. Record the best defining evidence and normative anchor when available. Apply the existing class rule for spec presence (semantic concept presence anywhere in the AsciiDoc corpus), and report separately when only use-sites were found or the defining location/anchor remains unresolved.

Append or refresh a concise `Sail-to-UDB reverse sweep` section in `summary.md` with the number of schema leaves examined, already covered in the first pass, matched back to UDB (including extension-declaration matches), unmatched as Sail-only, ambiguous, and with/without a defining spec location or normative anchor. Report extension-declaration matches separately from parameter-YAML matches, and include how many UDB parameter records were enriched, how many extension-mapping records were added, and how many new Sail-only records were added to `unified.parm`. Preserve the rest of the summary and avoid duplicate sections on reruns. When this sweep changes a UDB record's class or Sail metadata, update its class report; when it yields an extension mapping or Sail-only leaf, add it to `unified.parm` and its class report. Regenerate only affected class reports, preserving unrelated user-maintained content and deterministic ordering.

## Generate and verify `unified.parm`

Write one `rv-parm` record to `$PARMS_DSL_EXAMPLES/unified.parm` for each UDB parameter, each unmatched Sail schema leaf, and each Sail extension-support leaf matched through a UDB extension declaration when it is not already represented by an existing record. Follow the structure and style of `appendix.parm`. Merge an ordinary matched Sail leaf into its existing UDB parameter record rather than duplicating it. For an extension-file match, identify the record as an extension-support mapping and retain the UDB extension YAML as provenance; do not present it as a UDB parameter YAML or invent parameter fields. Preserve source-backed content and add the three-bit `class`, `hierarchy_level` when Sail nesting establishes it, `spec-anchor` when a normative AsciiDoc anchor is found, and relevant Sail schema metadata. For Sail-only records, use the full dotted config name as the Sail identity and retain the schema type, values/enum, and other relevant constraints without inventing UDB fields. Derive `hierarchy_level` from the Sail representation's actual nesting; for example, Sail config `base.xlen` gives `hierarchy_level = "base"` for the UDB `MXLEN.yaml` parameter. Follow existing DSL conventions for missing optional fields and for encoding anchor values.

Before changing `unified.parm`, inspect its current contents. It is the explicitly designated output and may be updated to contain this workflow's records, but preserve unrelated existing records and formatting; do not replace the file wholesale if it contains user-maintained material. Inspect each designated Markdown output before updating it, preserving unrelated user-maintained material. Do not overwrite other existing files, delete stale outputs, or clean the output directory implicitly. Keep names and ordering deterministic. If a record-level collision cannot be reconciled safely, leave that record unchanged and report the conflict.

Validate `unified.parm` with the DSL's parser, typechecker, or documented validation command. Also verify that every UDB parameter and every unmatched Sail schema leaf has exactly one corresponding record, that matched Sail leaves are merged into (not duplicated beside) their UDB record, and that each class agrees with the recorded source evidence. If the DSL format, identity mapping, or a conflict cannot be resolved from the supplied sources, do not invent syntax or discard fields; report the exact issue and leave affected records unmodified. Distinguish passed, failed, and not-run validation, and do not install dependencies or alter source repositories as an implicit validation step.

## Generate class files and summaries

Name each class report by the number and identity of sources present or absent, using the bit layout already defined above (`spec` = bit 0, `udb` = bit 1, `sail` = bit 2):

- If exactly one source is present, name the file `only-<source>.md`.
- If exactly one source is absent, name it `no-<source>.md`.
- If all three sources are present, use `all.md`.
- If no sources are present (`0b000`), use `none.md` and raise a prominent alert in `summary.md`; do not silently drop the record. This class should be impossible for records collected by this workflow.
- `0b001` (`spec` only) is reserved for a future spec-only record source; if one is added, name its report `only-spec.md`. The current UDB-first and Sail-reverse passes do not generate spec-only records.

The complete naming map is:

| Class | Meaning | File |
|---|---|---|
| `0b000` | No source | `none.md` (alert) |
| `0b001` | Spec only | `only-spec.md` (reserved) |
| `0b010` | UDB only | `only-udb.md` |
| `0b011` | UDB and spec, no Sail | `no-sail.md` |
| `0b100` | Sail only | `only-sail.md` |
| `0b101` | Spec and Sail, no UDB | `no-udb.md` |
| `0b110` | UDB and Sail, no spec | `no-spec.md` |
| `0b111` | UDB, spec, and Sail | `all.md` |

Create a report for each of the six classes produced by the current workflow (`0b010`, `0b011`, `0b100`, `0b101`, `0b110`, `0b111`), even when it has no entries. Create `only-spec.md` if a future workflow adds spec-only records, and `none.md` if an impossible `0b000` record is encountered.

Create `summary.json` as a JSON object with `sets` and `classes` arrays. `sets` contains exactly three objects for Spec, Sail, and UDB, each with `name` and `size`; `size` is the total number of unique parameter concepts/records whose class includes that source, computed from the class counts. Count a Sail extension-support leaf matched to a UDB extension declaration as UDB-present, but count it only once. `classes` contains one object for every generated class report, sorted by binary class value. Each class object has exactly these fields: `class` (the three-bit class string, such as `0b011`), `count` (integer number of entries in that class report, including zero for an empty class), and `filename` (the Markdown report basename). Include `only-spec.md` or `none.md` if either is generated. Example shape: `{ "sets": [{"name":"Spec","size":395},{"name":"Sail","size":418},{"name":"UDB","size":305}], "classes": [{"class":"0b010","count":4,"filename":"only-udb.md"}] }`.

Whenever `summary.json` is created or recreated, run `scripts/class_venn.py "$PARMS_DSL_EXAMPLES/summary.json" --output "$PARMS_DSL_EXAMPLES/class-venn.svg" --force` before refreshing `README.md`, `README.html`, or `README.pdf`. This is a required output-generation step, not an opt-in visualization. The helper treats the sets as Spec, UDB, and Sail in that order, maps class counts to their exact intersection regions, and derives outer labels from set metadata as `<name> (<size>)` (for example, `UDB (305)`). Region labels are left-aligned and contain their count and bracketed report filename (for example, `42 [no-sail.md]`). Each region label links to the class report named by its `filename` field; links are resolved relative to the summary and SVG locations. It verifies that each declared set size agrees with the class counts. Pass `--force` so an existing diagram is replaced from the current summary. The helper requires `matplotlib` and `matplotlib-venn` in the selected Python environment; do not install them implicitly. If generation fails, report the error and stop the output-refresh workflow rather than treating an older SVG or README as current; do not silently leave a stale diagram presented as the result for the new summary. The `0b000` region is outside all three sets, so the script alerts and refuses to plot a positive count for that class.

Put each UDB parameter, each Sail-only record, and each extension-support mapping record in exactly one class file, matching its `class` in `unified.parm`. Label Sail-only entries clearly and extension-file matches as UDB extension declarations, not parameter YAMLs; do not count a Sail leaf merged into an existing record as a second entry. Sort entries deterministically by name. Include enough source-backed detail to review each entry: UDB identity and relevant content when present, class, Sail hierarchical name/type/values and source line or schema pointer, spec evidence and normative anchor when present, and explicit unmatched or unresolved status. For extension mappings cite the corresponding `spec/std/isa/ext/<EXTNAME>.yaml`. Preserve parameter-specific uncertainty and partial-match notes. If a class has no entries, still create its file with a brief no-entries notice.

## Cluster future-development candidates

Create `no-udb-clusters.md` for entries in `no-udb.md` (`0b101`: spec and Sail, no UDB representation) and `no-sail-clusters.md` for entries in `no-sail.md` (`0b011`: UDB and spec, no Sail representation). Always create both cluster reports, including a short no-candidates notice when the corresponding class report is empty. These are navigation and triage views over the class reports: they do not create new parameter records, change class membership, or change class counts. Do not add cluster reports to the `summary.json` `classes` array.

Group entries by shared architectural concept, subsystem, behavior, or likely engineering task—not merely by similar identifiers or wording. Use the class-report evidence to explain each cluster's commonality and why it may point to a useful next investigation. Link each listed parameter to its heading in the corresponding class report and cite relevant spec/Sail/UDB evidence. State a tentative development direction or investigation question, along with confidence and unresolved caveats. Treat absence from a source as a candidate gap, not proof that the source is deficient: explicitly distinguish likely in-scope omissions from configuration-only concepts, intentional non-coverage, and cases needing human triage. Do not prescribe implementation changes unsupported by the sources.

Give every entry exactly one primary cluster in its own class's cluster report; use an explicit `Needs triage` cluster where evidence does not support a stronger grouping. Cross-cutting tags may be included as secondary navigation, but must not inflate unique cluster totals. Sort clusters and members deterministically. Summarize cluster names, member counts, and top-level investigation themes in `summary.md`; link both cluster reports from `summary.md` and the README. In the README, present these as possible future directions, not confirmed defects or implementation commitments.

Write a short `summary.md` instead of `report.md`. It should identify the inspected source paths and revisions, link to `unified.parm`, `summary.json`, and all generated class files (the six standard files plus `only-spec.md` or `none.md` if either is created), summarize UDB-backed and Sail-only totals by class (distinguishing parameter-YAML matches from extension-declaration matches), give forward and reverse matched/unmatched counts and anchor-resolved/unresolved totals, include the number of new extension-mapping and Sail-only `unified.parm` records, mention ambiguous or conflicting cases, and record validation commands/results and pre-existing source-tree changes. Keep per-parameter provenance in the class files rather than duplicating the full mapping in the summary. Do not create or update `report.md`.

## Create a README overview and HTML/PDF versions

Create or refresh `README.md` as the entry point to the reconciliation reports only after regenerating `class-venn.svg` from the current `summary.json`. Link to `summary.md`, `summary.json`, every generated class report, and both cluster reports; embed the newly generated `class-venn.svg` near the top and link to it. Explain the UDB-first and Sail-first passes, the evidence-based fuzzy/semantic matching approach (including that literal identifier equality or a similarity score alone is not proof), how specification concept presence differs from finding a defining normative anchor, and how ambiguous or rejected near-matches are handled. Include a concise future-directions section that links the `no-udb` and `no-sail` clusters and makes clear that they are evidence-backed candidates for human review, not automatically confirmed gaps. Use counts and outcomes from the current `summary.md`/`summary.json`; do not hard-code prior run totals. Until the parameter DSL supports the additional fields and can generate downstream workflow artifacts, do not mention or link to `unified.parm`, the DSL, or its parser/validation status in the README. Preserve unrelated existing README material when refreshing it.

In the README, document the special Sail extension-support mapping: `extensions.<EXTNAME>.supported` is checked against UDB `spec/std/isa/ext/<EXTNAME>.yaml`, and that extension declaration is distinct from a parameter YAML.

Convert the Markdown overview to a standalone HTML page with Pandoc, keeping relative links and assets valid from the same output directory:

```bash
pandoc README.md --from=gfm --to=html5 --standalone --metadata pagetitle="Unified UDB, Sail, and ISA-manual parameter comparison" --output=README.html
```

The README already has its visible H1. Do not pass Pandoc `title` metadata, which adds a second visible title block; use `pagetitle` for the browser/document title only.

Do not install Pandoc or dependencies implicitly. If Pandoc is unavailable, report the HTML conversion as not run. Inspect an existing `README.html` before replacing it; it is a designated generated output and may be refreshed from the current README when that is the requested workflow.

Also generate `README.pdf` from the current README using an already-installed PDF conversion path compatible with its linked/embedded assets (including SVG when the diagram is present). Prefer a Pandoc-supported PDF engine. For example, when WeasyPrint is installed:

```bash
pandoc README.md --from=gfm --to=pdf --standalone --pdf-engine=weasyprint --output=README.pdf
```

Choose another supported, installed Pandoc PDF engine when appropriate. If none is installed but Chromium is available, use the Pandoc-generated HTML and headless Chromium as a fallback, with the absolute HTML URI so relative SVG/report links resolve from the output directory:

```bash
chromium --headless --disable-gpu --no-pdf-header-footer --print-to-pdf=README.pdf file:///absolute/path/to/README.html
```

Use the installed Chromium executable name where it differs. Do not install Pandoc, a PDF engine, Chromium, or dependencies implicitly. If no compatible conversion path is available, leave any existing PDF untouched and report PDF conversion as not run. Inspect an existing `README.pdf` before replacing it. Verify that the generated PDF is non-empty and parseable when a PDF inspection tool is available.

Before updating any designated output, inspect whether it already exists and preserve unrelated user-maintained content. Do not delete stale files or clean the output directory implicitly. After generation, verify that every UDB parameter has exactly one `unified.parm` record and one class-file entry, every extension-support leaf matched through an extension YAML is represented exactly once with that YAML cited, and every genuinely Sail-only leaf has exactly one Sail-only record in `unified.parm` and one class-file entry. Verify that the `no-udb` and `no-sail` cluster reports each account for every entry in their respective class report exactly once as a primary cluster, that reported cluster/member totals agree, and that all cluster and evidence links resolve. Check that `summary.json` has exactly one entry per generated class report, its counts agree with report entries and `unified.parm` classes, filenames agree with the naming map, and that `class-venn.svg` was regenerated with `--force` from this exact `summary.json` before refreshing the README. Confirm the SVG's intersection counts and report links agree with `summary.json`; verify reverse-sweep totals agree with Sail-only and extension-mapping entries and the summary, README links and embedded assets resolve, README omits DSL references until enabled as described above, the HTML and PDF pages were produced from the current README (or their conversion status is reported as not run), and evidence citations resolve. Also verify that the input repositories remain unchanged.

Finish with the resolved directories, generated files, match/unmatched summary, validation results, and any decisions or conflicts that need the user's direction.
