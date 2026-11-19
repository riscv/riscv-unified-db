# UDB–Sail parameter merge summary

## Outputs

- [`unified.parm`](unified.parm)
- [`summary.json`](summary.json)
- [`only-udb.md`](only-udb.md) — class `0b010`: **4** entries
- [`no-sail.md`](no-sail.md) — class `0b011`: **42** entries
- [`only-sail.md`](only-sail.md) — class `0b100`: **20** entries
- [`no-udb.md`](no-udb.md) — class `0b101`: **15** entries
- [`no-spec.md`](no-spec.md) — class `0b110`: **41** entries
- [`all.md`](all.md) — class `0b111`: **343** entries
- [Sail without UDB: future-development clusters](no-udb-clusters.md)
- [UDB without Sail: future-development clusters](no-sail-clusters.md)

## Refreshed source inventory

- UDB parameters: **318** YAML files under `/home/adingank/git/forks/ajit-udb/spec/std/isa/param`.
- Matching Sail extension declarations: **112** exact `extensions.<EXTNAME>.supported` leaves backed by `/home/adingank/git/forks/ajit-udb/spec/std/isa/ext/<EXTNAME>.yaml`; these are extension declarations, not parameter YAMLs.
- Current record totals: **465** (318 parameter YAML concepts, 112 extension declarations, and 35 Sail-only concepts).
- Class counts: `0b010` 4, `0b011` 42, `0b100` 20, `0b101` 15, `0b110` 41, `0b111` 343.

## UDB-first pass

- UDB parameter records examined: **318**; semantic Sail matches: **272**; semantic AsciiDoc concept matches: **283**.
- Normative anchors resolved: **261**; unresolved among spec-present UDB parameters: **22**. Concept presence and a defining normative rule are tracked separately.
- The 13 newly added UDB YAMLs were mapped to existing Sail settings. Twelve are Stateen controls; for `MSTATEEN1/2/3_SE0_TYPE`, UDB's SE0 label differs from Sail/spec's SE1/SE2/SE3 bit label, while both descriptions target access to the matching stateen bank. The reports retain this as a human-review caveat.
- `HEDELEG_IAM_WRITABLE` maps to Sail `extensions.H.hedeleg_zero_writable`; `norm:hedeleg_acc` requires `hedeleg.IAM` writable at IALIGN=32 and does not dictate the optional IALIGN=16 choice.
- The rejected near-match `FORCE_UPGRADE_CBO_INVAL_TO_FLUSH` versus `base.reserved_behavior.xenvcfg_cbie` remains unresolved: the Sail setting concerns reserved CBIE=0b10 writes, not CBIE=0b11 invalidate-versus-flush behavior.

## Sail-to-UDB reverse sweep

- Config-schema leaves examined: **323**. Already semantically covered by the first pass: **116** (including the rebuilt schema leaves for non-standard MISA and the two Stateen CSRIND fields).
- Newly mapped to UDB parameter YAMLs: **13**; mapped to UDB extension declarations: **112**; unmatched as Sail-only records: **35**; ambiguous parent/near matches left unresolved: **47** (45 nested under parent-level mappings and two plausible direct-mode children).
- Of the 35 remaining Sail-only entries, **12** have a defining-location candidate and **23** do not; **12** have a confidently identified normative anchor and **23** do not. See per-entry caveats in [`only-sail.md`](only-sail.md) and [`no-udb.md`](no-udb.md).
- Existing records reclassified as extension mappings: **112** (no duplicate records added); UDB parameter records enriched with new reverse matches: **13**; new Sail-only record added to `unified.parm`: **1** (`base.reserved_behavior.illegal_privilege`).
- The new illegal-privilege setting is class `0b101`: the manual specifies legal MPP encodings at `src/priv/machine.adoc:392-393` (`norm:mstatus_xpp_enc`), but does not normatively select Sail's ignore-versus-lowest policy for illegal values.

## Potential future-development clusters

- [`no-udb-clusters.md`](no-udb-clusters.md): 15 remaining candidates in 4 primary clusters — Base ISA and architectural control defaults (4), Reserved and constrained behavior policies (7), Platform and hart integration (3), Vector profile and vector extensions (1).
- [`no-sail-clusters.md`](no-sail-clusters.md): existing 42 candidates in 9 primary clusters. These are investigation prompts, not confirmed defects.

## Sources and recorded state

| Input | Revision / path | Recorded state |
|---|---|---|
| UDB | `/home/adingank/git/forks/ajit-udb`, `cadd46e22487a2002cead3883b34e72766103cdf` (`main`) | 85 pre-existing status entries; preserved |
| Sail RISC-V | `/home/adingank/git/forks/ajit-sail-riscv`, `dc286e66aecf4f6cc2dd6b2716be1067d1664f99` (`master`) | clean; simulator `0.16` |
| ISA manual | `/home/adingank/git/forks/ajit-isa-manual`, `b3967cd97c2c32c4fe010ea969d73c647ecec14b` (`main`) | clean |
| Sail config schema | `/home/adingank/git/forks/ajit-sail-riscv/build/sail_riscv_config_schema.json` | simulator `0.16`; SHA-256 `ec97be07aa3d6d9be25af3540968a6af02e71ffd04486bb612fee57dc384d814` |

## Validation

- Source inventories, unique parameter identities, 112 exact extension-file mappings, class totals, summary-set sizes, class-page totals, and cluster primary membership: **PASS** (checked by the refresh run).
- Source repositories remained unchanged during reconciliation; UDB's 85 pre-existing status entries were preserved. Sail build completed successfully and the binary reports `0.16`.
- The pre-existing `class-venn.svg` was preserved, not regenerated; its region counts may reflect the previous class totals. The refreshed `summary.json` is authoritative for current counts.
- The parser command `/home/adingank/.local/share/mise/installs/node/24.18.0/bin/node packages/cli/bin/cli.js generate unified.parm --destination /tmp` **FAILED**: the current grammar rejects the custom `class` field (expects a normative-rule tag) and also rejects unsupported domain/record syntax. No parser or grammar changes were made.
