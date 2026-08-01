---
phase: 02-deterministic-measurement-spine
plan: 08
subsystem: specchoice-measurement
tags: [filesystem-custody, deterministic-measurement, h1, regression]
requires: [02-07]
provides: [descriptor-bound-authoritative-leaf-consumption]
affects: [adapter, preflight, h1-validation]
tech_stack:
  added: []
  patterns: [existing-read_authoritative_file, public-boundary-regressions]
key_files:
  created: []
  modified:
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/adapter.py
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/preflight.py
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/h1.py
    - experiments/specchoice-v1.3.2/tests/test_measurement_adapter.py
    - experiments/specchoice-v1.3.2/tests/test_measurement_parsing.py
    - experiments/specchoice-v1.3.2/tests/test_measurement_h1.py
decisions:
  - Reuse the Phase 1 descriptor-bound reader at each authoritative byte consumer; add no wrapper or dependency.
  - Keep H1 human-authored and local-only with external_publication_authorized=false.
metrics:
  tasks_completed: 2
  files_modified: 6
status: complete
---

# Phase 02 Plan 08: Descriptor-Bound Measurement Reads Summary

**Adapter, preflight, and H1 validation now consume only bytes returned by the Phase 1 no-follow descriptor reader, with public symlink/FIFO regressions at every score-bearing boundary.**

## Tasks Completed

1. **Task 02-08-01: Bind accepted adapter and preflight source bytes to one checked descriptor**
   - Replaced adapter `_raw_identity` inspection-plus-path-read with one `read_authoritative_file` result and retained declared length/SHA-256 checks and stable invalid zero-record translation.
   - Replaced preflight `_source_bytes_by_fixture` inspection-plus-path-read with descriptor-returned fixture bytes only.
   - Added RED→GREEN public regressions:
     - `MeasurementAdapterTests.test_public_builder_rejects_swapped_raw_leaf_and_fifo_without_consuming_or_blocking`
     - `MeasurementParsingTests.test_public_preflight_rejects_swapped_fixture_source_and_fifo_without_consuming_or_blocking`
   - Commit: `8592e090`

2. **Task 02-08-02: Bind every H1 evidence, schema, packet, Markdown, and decision leaf to one checked descriptor**
   - Updated `_read_canonical_value`, `_expected_bindings`, and the Markdown branch of `validate_h1_packet` to use descriptor-returned bytes.
   - Removed all four direct `_SCHEMA`/`_H1_SCHEMA` pathname reads; the three canonical schema digest uses share one returned byte string and the H1 review schema uses its own returned byte string.
   - Added the single RED→GREEN public regression `H1PacketTests.test_public_h1_validators_reject_swapped_packet_markdown_and_decision_leaves_and_fifos_without_consuming_or_blocking`, covering packet, Markdown, decision, `_SCHEMA`, and `_H1_SCHEMA` leaves.
   - Commit: `e52f35a0`

## Verification

- Task 1 RED: both new public tests failed before the consumer modules imported the helper seam; GREEN: both passed after the substitutions.
- Task 2 RED: the single parameterized H1 public test failed for packet, Markdown, decision, canonical schema, and H1 schema before the substitutions; GREEN: all subtests passed afterward.
- Focused suite: `64/64` passing (adapter 9, parsing 8, scoring 8, attempts 10, H1 7, filesystem 22).
- Active source authority: valid with exactly `11` fixtures and `28` raw files.
- Stored formal attempt, explicit-formal adversarial report, and H1 packet/Markdown all validated without regeneration.
- Discovery assertion exercised 135 runtime IDs: 130 green tests plus the exact five Phase 1 expected-red identities, preserving the five-failure/one-error signature.
- `git diff --check` passed. The exact 02-07-to-HEAD protected-boundary diff was empty for accepted bundle, source authority, formal/adversarial/H1/decision evidence, baselines, allowlist, Phase 1 planning, `spec/`, and generated data.
- Task commits contain only the six files declared in the plan; no dependency, schema, evidence, baseline, allowlist, restart receipt, core UDB, model, remote, or publication change was introduced.

## Decisions Made

- The existing Phase 1 `read_authoritative_file` is the single authoritative descriptor-bound byte source for this repair.
- H1 remains human-authored and local-only; `external_publication_authorized` remains `false`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Preserve the existing missing-source diagnostic semantics in the preflight regression**

- **Found during:** Task 02-08-01 GREEN verification.
- **Issue:** When a declared fixture-source descriptor read fails, the existing closed-schema preflight contract emits `EVIDENCE_SOURCE_UNKNOWN`, because no verified bytes remain in the global source-hash index. The plan text named `EVIDENCE_SOURCE_NOT_DECLARED_FOR_FIXTURE`, which applies only to a verified global source hash owned by another fixture.
- **Fix:** Assert the established deterministic blocking `EVIDENCE_SOURCE_UNKNOWN` result; parsed predictions remain withheld and no external bytes are consumed.
- **Files modified:** `experiments/specchoice-v1.3.2/tests/test_measurement_parsing.py`
- **Commit:** `8592e090`

## Known Stubs

None.

## Self-Check: PASSED

- All six declared source/test files exist and are present in the two task commits.
- Commits `8592e090` and `e52f35a0` exist.
- All automated verification and immutable-boundary checks listed above passed.
