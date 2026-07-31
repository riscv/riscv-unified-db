---
phase: 02-deterministic-measurement-spine
plan: "02"
subsystem: deterministic measurement validation
tags: [python, json, preflight, diagnostics, evidence-integrity]
requires:
  - phase: 02-01
    provides: accepted-v2 PR #2164 adapter batch and raw-file identities
provides:
  - closed current JSON adjudication contract with one named legacy ingress
  - duplicate-safe parsing, exact byte-span validation, and complete pure preflight
  - deterministically ordered typed diagnostics for downstream scoring
affects: [02-03, measurement-scoring, immutable-attempts, H1]
tech-stack:
  added: []
  patterns: [duplicate-safe JSON decoder, closed-schema validation, complete-batch preflight, raw-byte evidence validation]
key-files:
  created:
    - experiments/specchoice-v1.3.2/config/measurement/canonical-adjudication-schema-v1.json
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/strict_json.py
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/diagnostics.py
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/preflight.py
    - experiments/specchoice-v1.3.2/tests/test_measurement_parsing.py
  modified: []
key-decisions:
  - "Current canonical JSON accepts only current-v1; reject is normalized solely by legacy-pr2164-v1 with an explicit warning record."
  - "Invalid preflight exposes sorted diagnostics and raw hash only; score-bearing parsed predictions are withheld."
patterns-established:
  - "Validate raw evidence slices against accepted source bytes before any canonical text projection."
  - "Sort diagnostics only once using (severity_rank, code, fixture_id, field, occurrence)."
requirements-completed: [TS-04, TS-05]
coverage:
  - id: D1
    description: Closed canonical adjudication schema with the sole no-finding representation and named legacy alias.
    requirement: TS-04
    verification:
      - kind: unit
        ref: tests/test_measurement_parsing.py#test_complete_current_schema_payload_is_valid_with_explicit_empty_diagnostics
        status: pass
    human_judgment: false
  - id: D2
    description: Strict JSON decoder and closed current-schema validator reject malformed and noncanonical score-bearing input.
    requirement: TS-04
    verification:
      - kind: unit
        ref: tests/test_measurement_parsing.py#test_duplicate_keys_constants_and_noncanonical_no_finding_are_blockers
        status: pass
      - kind: unit
        ref: tests/test_measurement_parsing.py#test_closed_schema_and_complete_batch_collect_all_blockers
        status: pass
    human_judgment: false
  - id: D3
    description: Typed diagnostics use a stable total ordering and retain explicit empty output.
    requirement: TS-05
    verification:
      - kind: unit
        ref: tests/test_measurement_parsing.py#test_equivalent_blockers_have_byte_identical_total_diagnostic_ordering
        status: pass
    human_judgment: false
  - id: D4
    description: Pure preflight validates all accepted-v2 fixtures and exact independent evidence ranges before exposing parsed predictions.
    requirement: TS-04
    verification:
      - kind: unit
        ref: tests/test_measurement_parsing.py#test_evidence_spans_are_exact_and_adjacent_or_duplicate_spans_remain_independent
        status: pass
      - kind: integration
        ref: python3 -m specchoice_evidence.cli validate-phase2-source-authority --authority phase2/source-authority.json --bundle bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2
        status: pass
    human_judgment: false
  - id: D5
    description: Task-owned TDD parsing matrix proves current/legacy separation, no-repair behavior, and deterministic diagnostics.
    requirement: TS-05
    verification:
      - kind: unit
        ref: tests/test_measurement_parsing.py
        status: pass
    human_judgment: false
duration: 6min
completed: 2026-07-31
status: complete
---

# Phase 02 Plan 02: Strict Canonical Prediction Preflight Summary

**Raw JSON predictions now cross a closed current schema, byte-exact evidence validation, and complete deterministic preflight before any scoring surface exists.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-07-31T15:11:16Z
- **Completed:** 2026-07-31T15:17:30Z
- **Tasks:** 2/2
- **Files modified:** 5

## Accomplishments

- Added a canonical, reviewable JSON contract with explicit no-finding and legacy-ingress semantics.
- Added duplicate-key-safe JSON parsing, closed-object validation, exact authoritative byte-span checks, and side-effect-free complete-batch preflight.
- Added a focused six-test TDD matrix for malformed payloads, no-finding states, evidence ranges, legacy normalization, and total diagnostic ordering.

## Task Commits

1. **Task 1: Parse one complete current-schema prediction set without repair** — `7507ca68` (RED test), `71156b01` (GREEN feature)
2. **Task 2: Isolate the legacy alias and freeze diagnostic ordering** — `d5efd9c4` (RED test), `a3951e5a` (GREEN feature)
3. **Rule 1 correction:** `75b2a8e2` (canonical schema bytes and bounded evidence path verification)

## Files Created/Modified

- `experiments/specchoice-v1.3.2/config/measurement/canonical-adjudication-schema-v1.json` — canonical closed contract for payloads, predictions, adjudications, and spans.
- `experiments/specchoice-v1.3.2/src/specchoice_measurement/strict_json.py` — raw JSON decoder, current/legacy ingress boundary, and semantic validator.
- `experiments/specchoice-v1.3.2/src/specchoice_measurement/diagnostics.py` — frozen diagnostic record and total sort key.
- `experiments/specchoice-v1.3.2/src/specchoice_measurement/preflight.py` — pure full-batch terminal decision with no score/report fields on blockers.
- `experiments/specchoice-v1.3.2/tests/test_measurement_parsing.py` — focused parser/preflight contract matrix.

## Decisions Made

- `current-v1` rejects `reject`; only `legacy-pr2164-v1` maps it to `classify_out` and preserves raw-before/raw-after values in `LEGACY_PARAMETER_STATUS_NORMALIZED`.
- Validation reads fixture-source bytes only through accepted-v2 identities and reports every traversable blocker before withholding parsed predictions.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Determinism and path-boundary bug] Canonicalized schema bytes and reused accepted-path validation**
- **Found during:** Task 02-02-02 verification
- **Issue:** The reviewable schema serialized valid JSON but not the repository's canonical JSON byte form; preflight also needed to enforce the existing path primitives before reading adapter-declared source bytes.
- **Fix:** Rewrote the schema in canonical key order and routed source-byte reads through `require_relative_posix_path` and `inspect_authoritative_path`.
- **Files modified:** `canonical-adjudication-schema-v1.json`, `preflight.py`, `strict_json.py`
- **Verification:** Focused parsing and adapter tests, authority validation, and canonical-byte assertion all passed.
- **Committed in:** `75b2a8e2`

**Total deviations:** 1 auto-fixed (Rule 1).
**Impact on plan:** Tightens the planned deterministic and T-02-PATH safeguards without expanding scope.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 02-03 can consume only zero-blocker `PreflightResult.parsed_predictions`; invalid input has no score-bearing payload, metrics, report, approval, or publication fields.

## Self-Check: PASSED

- All five declared artifacts exist.
- All five task commits (`7507ca68`, `71156b01`, `d5efd9c4`, `a3951e5a`, `75b2a8e2`) exist in Git history.
- No known stubs, skipped tests, or unrun verification remain.
