# Phase 3: Human-Reviewed Data Preregistration - Pattern Map

**Mapped:** 2026-08-03

## New File to Existing Analog Map

| New Phase 3 role | Planned path | Closest existing analog | Pattern to reuse |
|---|---|---|---|
| Canonical data schema/validation | `src/specchoice_data/schema.py` | `src/specchoice_measurement/strict_json.py` | duplicate-key rejection, exact-key validation, typed enums, no repair |
| Inventory/provenance admission | `src/specchoice_data/admission.py` | `src/specchoice_evidence/filesystem.py`, `src/specchoice_measurement/preflight.py` | descriptor-bound leaves, complete-batch preflight, stable diagnostics |
| Review packet/readiness/decision | `src/specchoice_data/review.py` | `src/specchoice_measurement/h1.py` | decision-free readiness, exact human payload, hash binding, no inference |
| Family/split/leakage | `src/specchoice_data/splits.py` | `src/specchoice_measurement/adapter.py` | exact version/source identity, fail-closed batch output |
| Relevance/metamorphic | `src/specchoice_data/relevance.py` | `src/specchoice_measurement/domain.py`, `h1.py` | closed domain enums, evidence-preserving review items |
| H2 authority/eligibility | `src/specchoice_data/h2.py` | `src/specchoice_measurement/final_reports.py` | approved-only terminal projection, recompute before write |
| Local CLI | `src/specchoice_data/cli.py` | `src/specchoice_measurement/cli.py` | thin argparse dispatch to domain functions |
| Canonical artifacts | `data/preregistration/`, `reports/h2/`, `receipts/`, `reviews/`, `phase3/` | existing `reports/h1/`, `receipts/`, `reviews/`, `phase2/` | one-way data -> packet -> readiness -> decision -> authority chain |

## Required Reuse Points

- Import `canonical_json_bytes`, `sha256_bytes`, `require_sha256`, and canonical text normalization from `specchoice_evidence.canonical`; do not create a second serializer.
- Import descriptor-bound readers/writers from `specchoice_evidence.filesystem`; do not use `Path.read_text()` for authoritative leaves.
- Import `decode_strict_json` for untrusted JSON inputs and preserve duplicate-key/non-finite rejection.
- Reuse `Diagnostic` ordering and fields for all machine admission failures.
- Follow H1's separate packet, readiness, decision, and approved-only terminal stages, but define Phase 3 semantics in the new package rather than adding another H1 version branch.
- Keep all code and generated data under `experiments/specchoice-v1.3.2/`; do not touch core UDB schemas, `spec/`, `backends/`, or generated architecture data.

## Boundary Rules

The new package may depend on `specchoice_evidence` and the stable diagnostic/strict JSON utilities from `specchoice_measurement`. Existing packages must not import `specchoice_data`; Phase 3 is downstream of Phase 2. Human-readable Markdown may depend on canonical Phase 3 evidence, never the reverse.

No planned file matches a database ORM schema pattern. No schema push task is applicable. No UI or external API integration is in scope.
