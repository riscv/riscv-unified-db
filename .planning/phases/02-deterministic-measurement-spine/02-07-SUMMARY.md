---
phase: 02-deterministic-measurement-spine
plan: "07"
subsystem: deterministic measurement custody
tags: [python, formal-attempt-lineage, adapter-diagnostics, canonical-json]
requires:
  - phase: 02-06
    provides: critical-gap analysis and preserved local-only H1 evidence
provides:
  - standalone adversarial-report validation rooted in a verified formal attempt
  - fail-closed adapter conflict batches with complete verified provenance
affects: [phase-02-verification, h1-review, later-measurement]
tech-stack:
  added: []
  patterns: [explicit-authority-path, typed-conflict-diagnostic, same-interpreter-subprocess]
key-files:
  created: []
  modified:
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/cli.py
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/h1.py
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/adapter.py
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/domain.py
    - experiments/specchoice-v1.3.2/tests/test_measurement_attempts.py
    - experiments/specchoice-v1.3.2/tests/test_measurement_adapter.py
key-decisions:
  - "Standalone adversarial validation derives formal lineage only from an explicitly supplied, replay-validated formal/completed attempt."
  - "Post-authority adapter conflicts retain verified source identity and one typed Diagnostic while still exposing zero records."
requirements-completed: [TS-03, TS-04, TS-05]
coverage:
  - id: D1
    description: "Standalone adversarial reports reject a digest-only formal-attempt lineage forgery and preserve the local H1 v2 boundary."
    requirement: TS-05
    verification:
      - kind: unit
        ref: experiments/specchoice-v1.3.2/tests/test_measurement_attempts.py#MeasurementAttemptTests.test_adversarial_report_rejects_forged_formal_attempt_binding
        status: pass
      - kind: integration
        ref: "python3 -m specchoice_measurement.cli validate-adversarial-report --report reports/h1/adversarial-oracle-results-v2.json --formal-attempt runs/measurement-attempts/formal-golden-pr2164-v1"
        status: pass
    human_judgment: false
  - id: D2
    description: "Public adapter conflict results retain verified source identity and source/gold hashes without producing score-eligible records."
    requirement: TS-05
    verification:
      - kind: unit
        ref: experiments/specchoice-v1.3.2/tests/test_measurement_adapter.py#MeasurementAdapterTests.test_public_builder_preserves_conflict_provenance
        status: pass
      - kind: integration
        ref: "tests.test_measurement_adapter tests.test_measurement_parsing tests.test_measurement_scoring tests.test_measurement_attempts tests.test_measurement_h1 tests.test_filesystem_boundary"
        status: pass
    human_judgment: false
metrics:
  duration: 6m
  tasks_completed: 2
  files_modified: 6
  completed_date: 2026-08-01
status: complete
---

# Phase 02 Plan 07: Critical Measurement Trust Repairs Summary

**Standalone adversarial validation now proves formal-attempt lineage from replayed bytes, while adapter conflicts retain complete source/gold provenance with zero score-eligible records.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-08-01T20:46:47Z
- **Completed:** 2026-08-01T20:52:42Z
- **Tasks:** 2/2
- **Files modified:** 6

## Accomplishments

- Closed CR-01 with a required `validate-adversarial-report --formal-attempt PATH` input. The standalone validator, generation self-check, H1 binding path, and tests now use the verified `formal/completed` attempt SHA-256 rather than a report-declared digest.
- Closed CR-02 by carrying a typed `GOLD_NAME_MISMATCH` Diagnostic through `AdapterError`, retaining verified six-field source identity plus deterministic `fixture_expected` and `fixture_gold` hashes, while returning `records=()`.
- Closed WR-01 solely in the two adapter subprocess tests with `sys.executable`; no production interpreter policy or dependency changed.

## Task Commits

1. **Task 1: Root standalone adversarial validation in verified formal-attempt bytes** — `bfcadfd9` (fix)
2. **Task 2: Preserve source/gold conflict provenance through the public adapter builder** — `bdc6e0a3` (fix)

## Verification

- RED observed for `test_adversarial_report_rejects_forged_formal_attempt_binding`: a copied canonical report with only `formal_attempt_sha256` changed to 64 zeroes incorrectly validated before the repair. It passes after the repair.
- RED observed for `test_public_builder_preserves_conflict_provenance`: the public builder cleared verified `source_identity` after an injected parsed gold-name conflict. It passes after the repair.
- `tests.test_measurement_attempts` plus `tests.test_measurement_h1`: 16 passed; the real formal attempt, v2 adversarial report using explicit formal input, and H1 v2 packet/Markdown validation passed without regeneration.
- Focused Phase 2 plus filesystem partition: 61/61 passed.
- Source authority stayed `valid` with exactly 11 fixtures and 28 raw files.
- Discovery classified 132 methods as exactly 127 green plus the preserved five Phase 1 live-boundary expected-red methods, whose result remains 5 failures and 1 error.

## Files Created/Modified

- `experiments/specchoice-v1.3.2/src/specchoice_measurement/cli.py` — validates a supplied formal attempt before accepting report bindings and exposes the required CLI path.
- `experiments/specchoice-v1.3.2/src/specchoice_measurement/h1.py` — passes the existing formal attempt path into standalone adversarial validation.
- `experiments/specchoice-v1.3.2/src/specchoice_measurement/adapter.py` — preserves typed conflict provenance and post-verification identity.
- `experiments/specchoice-v1.3.2/src/specchoice_measurement/domain.py` — serializes deterministic role-keyed source hashes in the existing Diagnostic.
- `experiments/specchoice-v1.3.2/tests/test_measurement_attempts.py` — covers digest-only lineage tampering.
- `experiments/specchoice-v1.3.2/tests/test_measurement_adapter.py` — covers public-builder provenance and same-interpreter subprocesses.

## Decisions Made

- Formal report lineage must be recomputed from independently supplied, replay-validated formal evidence; H1's subsequent comparison remains defense in depth.
- Conflict audit data remains inside the established `Diagnostic` contract instead of creating a parallel diagnostic or custody path.
- H1 remains human-authored and local-only; frozen evidence bytes and `external_publication_authorized=false` are unchanged.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Used discovery's actual top-level test IDs for the strict expected-red partition**
- **Found during:** Task 2 verification
- **Issue:** `unittest.defaultTestLoader.discover("tests")` returns `test_fixture_closure...` and `test_receipts...` IDs in this checkout, whereas the plan's embedded set prefixes them with `tests.`. The original exact assertion therefore failed before test execution.
- **Fix:** Re-ran the same 132-method partition with only that runtime-discovered namespace spelling corrected; the five method names, 127-green exclusion, and 5-failure/1-error signature were unchanged.
- **Files modified:** None
- **Verification:** 132 discovered = 127 green + 5 preserved expected-red; all green passed and the red signature matched.

**Total deviations:** 1 auto-fixed (Rule 3).
**Impact on plan:** Verification-only namespace correction; no production, Phase 1, v7, or frozen-evidence behavior changed.

## Known Stubs

None.

## Issues Encountered

The plan's discovery assertion used a package-qualified test-ID spelling that this invocation of `unittest discover` does not emit. The method identity and required expected-red result were verified with the actual discovery IDs.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

CR-01 and CR-02 are covered by fail-first regressions. The accepted-v2 11/28 authority, H1 v2 packet validation, local-only boundary, and Phase 1 expected-red classification remain intact; no model, remote, publication, or external authority was introduced.

## Self-Check: PASSED

All six declared implementation/test files and both task commits (`bfcadfd9`, `bdc6e0a3`) exist. `git diff --check` passed, no tracked files were deleted, and only the pre-existing allowed untracked files remain alongside this summary before metadata commit.
