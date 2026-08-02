---
phase: 02-deterministic-measurement-spine
plan: 14
subsystem: measurement-custody
tags: [python, descriptor-custody, pending-v3, formal, adversarial, fail-closed]
requires:
  - phase: 02-13
    provides: explicit pending-v3 adapter/preflight authority rehearsal
provides:
  - Descriptor-held pending-v3 formal measurement and adversarial validation inputs
  - Public leaf-race regressions for formal and adversarial custody paths
affects: [02-15, 02-16]
tech-stack:
  added: []
  patterns: [descriptor-held canonical bytes, explicit pending-v3 custody, validated formal digest derivation]
key-files:
  created: []
  modified:
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/attempts.py
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/cli.py
    - experiments/specchoice-v1.3.2/tests/test_measurement_attempts.py
    - experiments/specchoice-v1.3.2/tests/test_measurement_parsing.py
    - experiments/specchoice-v1.3.2/tests/test_measurement_scoring.py
key-decisions:
  - "Formal and adversarial public commands require explicit pending-v3 authority and transition inputs while legacy active-v2 validation remains readable."
  - "Formal-attempt and adversarial-report identity is derived from descriptor-held validated bytes and objects, never a reopened path or report self-claim."
patterns-established:
  - "Use read_authoritative_file once at public custody boundaries, then carry the returned bytes through validation, retention, and replay."
  - "Adversarial validation independently validates the referenced formal attempt and derives its digest from that held result."
requirements-completed: [TS-03, TS-04, TS-05]
coverage:
  - id: D1
    description: Formal public rehearsal holds pending-v3 prediction and schema bytes through immutable attempt validation.
    requirement: TS-03
    verification:
      - kind: unit
        ref: tests/test_measurement_attempts.py#test_public_formal_cli_rejects_prediction_schema_manifest_and_retained_artifact_leaf_races
        status: pass
    human_judgment: false
  - id: D2
    description: Adversarial public validation holds report, oracle, golden, schema, and formal-attempt identities under explicit pending-v3 custody.
    requirement: TS-04
    verification:
      - kind: unit
        ref: tests/test_measurement_attempts.py#test_public_adversarial_validator_rejects_report_oracle_golden_schema_and_attempt_leaf_races
        status: pass
    human_judgment: false
  - id: D3
    description: The Phase 2 focused suite preserves the fixed red partition while accepting the two new public custody regressions.
    requirement: TS-05
    verification:
      - kind: other
        ref: tests/phase1_expected_red_oracle.py --expected-focused 71 --expected-discovered 149 --expected-green 144
        status: pass
    human_judgment: false
duration: 14min
completed: 2026-08-02
status: complete
---

# Phase 02 Plan 14: Pending-v3 Formal and Adversarial Custody Summary

**Descriptor-held pending-v3 formal and adversarial rehearsals reject raced leaves while preserving active-v2 authority and all evidence artifacts.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-08-02T11:16:31Z
- **Completed:** 2026-08-02T11:30:03Z
- **Tasks:** 1
- **Files modified:** 5

## Accomplishments

- Routed formal public rehearsal through descriptor-held prediction and schema bytes plus explicit pending-v3 authority/transition inputs.
- Routed adversarial generation and validation through held report, oracle, golden, schema, and independently validated formal-attempt custody.
- Added public race coverage for all formal/adversarial control leaves and rebound disposable parsing/scoring fixtures to the pending-v3 mirror.

## Task Commits

1. **Task 1: Carry one held pending-v3 identity through formal and adversarial public paths** - `4adb631e` (test, RED)
2. **Task 1: Carry one held pending-v3 identity through formal and adversarial public paths** - `98fb2d47` (feat, GREEN)

## Files Created/Modified

- `experiments/specchoice-v1.3.2/src/specchoice_measurement/attempts.py` - Carries held schema bytes into immutable attempt bindings and replay validation.
- `experiments/specchoice-v1.3.2/src/specchoice_measurement/cli.py` - Makes formal/adversarial public custody explicit and descriptor-rooted.
- `experiments/specchoice-v1.3.2/tests/test_measurement_attempts.py` - Covers public formal/adversarial leaf races and non-authoritative pending-v3 rehearsal.
- `experiments/specchoice-v1.3.2/tests/test_measurement_parsing.py` - Uses the explicit pending-v3 adapter mirror.
- `experiments/specchoice-v1.3.2/tests/test_measurement_scoring.py` - Rebinds disposable golden payloads to the pending-v3 adapter identity.

## Decisions Made

- Pending-v3 authority and transition are mandatory for public formal/adversarial rehearsal; no command replaces or revokes active-v2.
- Retained attempts replay from caller-held adapter/schema values where supplied; standalone adversarial validation derives the formal digest from independent attempt validation.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_measurement_attempts tests.test_measurement_parsing tests.test_measurement_scoring -v` — 29/29 passed.
- `PYTHONPATH=src python3 tests/phase1_expected_red_oracle.py --expected-focused 71 --expected-discovered 149 --expected-green 144` — passed with the fixed five-method/six-outcome red partition.
- Protected task commits contain only the five allowed files; the worktree is clean for those paths.
- Immutable hashes unchanged: active-v2 `6943ae60b5a22b4cc262bbcc0c252fbd9a31e5e5cbaac9f79976087b63a4ce23`, pending-v3 `e1681a347a6d9cbdf6d0f19863b4d2856a36663949fcc0a6f4d2960c5dd8e6d1`, readiness `24dc6bbfc56c1fbcdc856015673b109987b2e7683465f57d6bd20225689bbdc5`, transition `472bc06268c2e7c70d6975717f9d0f60b14e1a495cbca73342e9effe7bb33543`.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Next Phase Readiness

Formal and adversarial consumers now support the non-authoritative pending-v3 rehearsal boundary. Active-v2, readiness, authority, report, evidence, and H1 artifacts remain unchanged; 02-15 retains its assigned readiness work.

## Self-Check: PASSED

- Confirmed all five planned files and task commits `4adb631e` and `98fb2d47` exist.

---
*Phase: 02-deterministic-measurement-spine*
*Completed: 2026-08-02*
