---
phase: 02-deterministic-measurement-spine
plan: "03"
subsystem: deterministic measurement scoring
tags: [python, scoring, diagnostics, evidence-integrity, ts-03, ts-05]
requires:
  - phase: 02-01
    provides: accepted-v2 PR #2164 adapter batch and raw-source identities
  - phase: 02-02
    provides: strict current-schema preflight and deterministic diagnostic ordering
provides:
  - exact all-11 golden scoring with separate surfacing, disposition, identity, and evidence metrics
  - complete structured adversarial diagnostic oracles bound to raw-input identities
  - raw-byte evidence, UTF-8-boundary, duplicate/adjacent-span, and input-order tests
affects: [02-04, immutable-attempts, H1-source-gold-review]
tech-stack:
  added: []
  patterns: [pure-score-gate, independently-denominated-metrics, complete-structured-diagnostic-oracles]
key-files:
  created:
    - experiments/specchoice-v1.3.2/fixtures/measurement/golden-predictions-v1.json
    - experiments/specchoice-v1.3.2/fixtures/measurement/adversarial/required-diagnostics-v1.json
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/scoring.py
    - experiments/specchoice-v1.3.2/tests/test_measurement_scoring.py
  modified:
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/diagnostics.py
key-decisions:
  - "Formal scoring is gated by one exact 11-fixture preflight identity and never publishes metrics for partial or diagnostic-only input."
  - "All frozen adversarial checks compare a complete stable diagnostic record, including finding identity where a scoring finding exists."
patterns-established:
  - "Score dimensions remain separately denominated; warnings can lower identity coverage without changing surfacing or disposition."
  - "Evidence spans are raw-byte exact and retain declared duplicate, adjacent, and input ordering semantics."
requirements-completed: [TS-03, TS-05]
coverage:
  - id: D1
    description: Exact all-11 golden scoring produces the required 6/4/1 outcomes with independently denominated metrics and no formal metrics for ineligible input.
    requirement: TS-03
    verification:
      - kind: unit
        ref: experiments/specchoice-v1.3.2/tests/test_measurement_scoring.py#test_exact_all_eleven_golden_outcomes_keep_dimensions_independent
        status: pass
      - kind: unit
        ref: experiments/specchoice-v1.3.2/tests/test_measurement_scoring.py#test_invalid_or_diagnostic_only_preflight_never_emits_formal_metrics
        status: pass
    human_judgment: false
  - id: D2
    description: Candidate disposition, accepted-name warning separation, and every frozen adversarial diagnostic oracle are deterministic and fully structured.
    requirement: TS-05
    verification:
      - kind: unit
        ref: experiments/specchoice-v1.3.2/tests/test_measurement_scoring.py#test_every_required_diagnostic_oracle_is_complete_and_exact
        status: pass
      - kind: unit
        ref: experiments/specchoice-v1.3.2/tests/test_measurement_scoring.py#test_name_warning_preserves_semantics_and_matches_structured_oracle
        status: pass
    human_judgment: false
  - id: D3
    description: Evidence span claims are raw-byte exact, including duplicate/adjacent preservation, UTF-8-boundary rejection, and input-order-independent outcomes.
    requirement: TS-05
    verification:
      - kind: unit
        ref: experiments/specchoice-v1.3.2/tests/test_measurement_scoring.py#test_exact_duplicate_and_adjacent_spans_remain_distinct
        status: pass
      - kind: unit
        ref: experiments/specchoice-v1.3.2/tests/test_measurement_scoring.py#test_invalid_utf8_boundary_is_rejected_without_repair
        status: pass
      - kind: unit
        ref: experiments/specchoice-v1.3.2/tests/test_measurement_scoring.py#test_case_and_warning_diagnostic_order_are_input_order_independent
        status: pass
      - kind: integration
        ref: PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m specchoice_evidence.cli validate-phase2-source-authority --authority phase2/source-authority.json --bundle bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2
        status: pass
    human_judgment: false
metrics:
  duration: 7m
  tasks_completed: 2
  test_count: 19
  completed_date: 2026-07-31
status: complete
---

# Phase 02 Plan 03: Golden Scoring and Diagnostic Oracles Summary

The all-11 accepted-v2 golden path now emits separately auditable score dimensions while each adversarial mutation resolves to one complete, stable diagnostic record tied to exact raw evidence.

## Performance

- **Duration:** 7 min
- **Started:** 2026-07-31T17:20:46Z
- **Completed:** 2026-07-31T17:27:17Z
- **Tasks:** 2/2
- **Files modified:** 5

## Accomplishments

- Added the all-11 formal scoring tracer: six positive accepts, four negative no-findings, and the surfaced-then-`classify_out` candidate, with distinct surfacing, disposition, identity, and evidence-integrity denominators.
- Preserved the warning-only name-missing path: it lowers identity from 6/6 to 5/6 without altering the 7/7 surfacing or disposition result.
- Converted every adversarial entry into a complete expected record and tested exact raw-byte spans, duplicate/adjacent preservation, UTF-8 boundaries, and deterministic input ordering.

## Task Commits

1. **Task 1: Score the exact golden all-11 path with independent outcomes** — `ab759a39` (RED), `2dced145` (GREEN)
2. **Task 2: Verify exact spans and every required diagnostic oracle** — `d8649c60` (RED), `d49499c9` (GREEN)

## Files Created/Modified

- `experiments/specchoice-v1.3.2/fixtures/measurement/golden-predictions-v1.json` — canonical exact prediction set for the all-11 formal path.
- `experiments/specchoice-v1.3.2/fixtures/measurement/adversarial/required-diagnostics-v1.json` — raw-input-bound, complete expected diagnostic records.
- `experiments/specchoice-v1.3.2/src/specchoice_measurement/diagnostics.py` — stable diagnostics including optional finding identity.
- `experiments/specchoice-v1.3.2/src/specchoice_measurement/scoring.py` — pure score gate, independent metrics, and finding-bound scoring diagnostics.
- `experiments/specchoice-v1.3.2/tests/test_measurement_scoring.py` — golden, adversarial, raw-byte, and ordering contracts.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_measurement_scoring -q` — 8 passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_measurement_adapter tests.test_measurement_parsing tests.test_measurement_scoring -q` — 19 passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m specchoice_evidence.cli validate-phase2-source-authority --authority phase2/source-authority.json --bundle bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2` — accepted-v2 authority valid for exact 11 fixtures and 28 raw files.
- `git diff --check` — passed.

## TDD Gate Compliance

- RED commits: `ab759a39`, `d8649c60`.
- GREEN commits: `2dced145`, `d49499c9`.

## Decisions Made

- Formal metrics remain unavailable for partial, invalid, or diagnostic-only results.
- Every frozen adversarial entry asserts full diagnostic fields rather than only a diagnostic code.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Completed the structured adversarial oracle matrix**
- **Found during:** Task 2 verification
- **Issue:** Eleven frozen mutations specified only a code, so they could not prove diagnostic field stability or finding identity.
- **Fix:** Added complete expected records for all mutations, bound scoring diagnostics to their finding IDs, and added exact-oracle, UTF-8-boundary, and order tests.
- **Files modified:** `required-diagnostics-v1.json`, `diagnostics.py`, `scoring.py`, `test_measurement_scoring.py`
- **Verification:** Focused scoring suite (8 tests), cumulative adapter/parsing/scoring suite (19 tests), and accepted-v2 authority validation passed.
- **Committed in:** `d49499c9`

**Total deviations:** 1 auto-fixed (Rule 2).
**Impact on plan:** Completes the planned TS-05 oracle contract without adding dependencies or expanding the experiment boundary.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 02-04 can create immutable formal and diagnostic-only attempts from a fully deterministic, evidence-bound scoring result. No model, API, publication, push, Phase 1 custody, or core-UDB surface was changed.

## Self-Check: PASSED

All five plan artifacts exist; task commits `ab759a39`, `2dced145`, `d8649c60`, and `d49499c9` exist; no tracked files were deleted; no stubs, skipped tests, or unrun verification remain. Pre-existing `.DS_Store` files remain unstaged.
