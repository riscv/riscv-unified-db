---
phase: 02-deterministic-measurement-spine
plan: "04"
subsystem: deterministic measurement custody
tags: [python, canonical-json, immutable-attempts, fsync, diagnostic-only]
requires:
  - phase: 02-03
    provides: complete all-11 scoring and frozen structured diagnostic oracles
provides:
  - immutable, no-replace formal all-11 measurement attempt
  - separate canonical diagnostic-only adversarial oracle result
  - CLI validators for formal attempt and adversarial report bindings
affects: [02-05, h1-review, measurement-evidence]
tech-stack:
  added: []
  patterns: [exclusive-create-and-fsync, non-cyclic-manifest-digest, formal-diagnostic-role-separation]
key-files:
  created:
    - experiments/specchoice-v1.3.2/runs/measurement-attempts/formal-golden-pr2164-v1/attempt.json
    - experiments/specchoice-v1.3.2/runs/measurement-attempts/formal-golden-pr2164-v1/parsed-predictions.json
    - experiments/specchoice-v1.3.2/runs/measurement-attempts/formal-golden-pr2164-v1/diagnostics.json
    - experiments/specchoice-v1.3.2/runs/measurement-attempts/formal-golden-pr2164-v1/case-outcomes.json
    - experiments/specchoice-v1.3.2/runs/measurement-attempts/formal-golden-pr2164-v1/metrics.json
    - experiments/specchoice-v1.3.2/runs/measurement-attempts/formal-golden-pr2164-v1/report.json
    - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v1.json
  modified:
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/attempts.py
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/cli.py
    - experiments/specchoice-v1.3.2/tests/test_measurement_attempts.py
key-decisions:
  - "Formal authority is limited to a clean accepted-v2 all-11 attempt; warning, invalid, and diagnostic-only material cannot be promoted."
  - "The adversarial report records only exact frozen diagnostics and diagnostic-only custody hashes; it emits neither metrics nor H1 disposition."
patterns-established:
  - "Recover raw prediction bytes from manifest base64 before comparing their SHA-256, then validate every canonical sibling hash."
  - "Publish machine evidence through exclusive writes plus directory fsync; retain a pre-existing target unchanged."
requirements-completed: [TS-03, TS-04, TS-05]
coverage:
  - id: D1
    description: Formal accepted-v2 golden evidence covers all 11 fixtures with empty diagnostics, completed formal status, and independently denominated metrics.
    requirement: TS-03
    verification:
      - kind: unit
        ref: experiments/specchoice-v1.3.2/tests/test_measurement_attempts.py#test_formal_cli_writes_one_clean_all_eleven_attempt_and_refuses_regeneration
        status: pass
      - kind: integration
        ref: PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m specchoice_measurement.cli validate-attempt --attempt runs/measurement-attempts/formal-golden-pr2164-v1
        status: pass
    human_judgment: false
  - id: D2
    description: Attempt custody losslessly preserves raw predictions and rejects replacement, race collisions, tampered siblings, invalid role promotion, and invalid preflight score artifacts.
    requirement: TS-04
    verification:
      - kind: unit
        ref: experiments/specchoice-v1.3.2/tests/test_measurement_attempts.py
        status: pass
    human_judgment: false
  - id: D3
    description: Every frozen adversarial case is executed and recorded as diagnostic_only with its complete matching structured diagnostic record.
    requirement: TS-05
    verification:
      - kind: unit
        ref: experiments/specchoice-v1.3.2/tests/test_measurement_attempts.py#test_adversarial_cli_is_diagnostic_only_and_matches_every_frozen_oracle
        status: pass
      - kind: integration
        ref: PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m specchoice_measurement.cli validate-adversarial-report --report reports/h1/adversarial-oracle-results-v1.json
        status: pass
    human_judgment: false
metrics:
  duration: 29min
  tasks_completed: 3
  test_count: 25
  completed_date: 2026-07-31
status: complete
---

# Phase 02 Plan 04: Immutable Measurement Attempts Summary

The accepted-v2 golden inputs now have a no-replace, fsynced all-11 formal attempt, while the frozen adversarial matrix remains a separate diagnostic-only report with no H1 or metrics authority.

## Performance

- **Duration:** 29 min
- **Started:** 2026-07-31T19:33:05+02:00
- **Completed:** 2026-07-31T20:02:09+02:00
- **Tasks:** 3/3
- **Files modified:** 10

## Accomplishments

- Reused the Phase 1 exclusive-write, directory-fsync, and native no-replace primitives to publish closed terminal attempts with base64 raw recovery, a non-cyclic manifest digest, and bound canonical sibling artifacts.
- Generated `formal-golden-pr2164-v1`: all 11 accepted-v2 fixtures, `formal/completed`, `diagnostics=[]`, exact 7/7 surfacing, 7/7 disposition, 6/6 identity, and 7/7 evidence integrity metrics.
- Generated a canonical 12-case adversarial oracle result. Each case is `diagnostic_only`, contains a matching full structured diagnostic record, and carries no metric, formal, H1, model, remote, or publication authority.

## Task Commits

1. **Task 1: Prove immutable no-replace attempt custody end to end** — `25fbeef4` (RED), `a068cadc` (GREEN)
2. **Task 2: Generate and validate the warning-free formal golden attempt** — `1f3c8ca1` (RED), `b21defaf` (GREEN)
3. **Task 3: Generate the separate exact-code adversarial artifact** — `4810523d` (RED), `617216f5` (GREEN)

## Evidence Identities

- Formal attempt manifest SHA-256: `fde98401e7e62d0daa127a730ee9473cd857772722e057bcd4975b2ae2ef74de`
- Formal non-cyclic attempt digest: `c81649ae4aaa4c29be289af1855934f66c907f8a0bf0a2e6c2ce2407bd3da756`
- Adversarial report SHA-256: `a8be040df32a68be69c79a531d3288988bffe2f7642a8a3f01cbe8796fb37941`
- Frozen diagnostic-oracle SHA-256: `826edde1d07a895a933b2c13588dec1c3330da8304a52527816cafa7faa5ddd9`

## Files Created/Modified

- `experiments/specchoice-v1.3.2/src/specchoice_measurement/attempts.py` — staged terminal-attempt custody and validation.
- `experiments/specchoice-v1.3.2/src/specchoice_measurement/cli.py` — constrained formal runner, attempt validator, diagnostic-only adversarial runner, and report validator.
- `experiments/specchoice-v1.3.2/tests/test_measurement_attempts.py` — TDD coverage for formal generation, all binding preservation, diagnostics-only separation, and collision/tamper protection.
- `experiments/specchoice-v1.3.2/runs/measurement-attempts/formal-golden-pr2164-v1/` — six canonical, hash-bound formal artifacts.
- `experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v1.json` — immutable exact oracle result.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_measurement_adapter tests.test_measurement_parsing tests.test_measurement_scoring tests.test_measurement_attempts -q` — 25 passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m specchoice_measurement.cli validate-attempt --attempt runs/measurement-attempts/formal-golden-pr2164-v1` — formal completed attempt valid.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m specchoice_measurement.cli validate-adversarial-report --report reports/h1/adversarial-oracle-results-v1.json` — 12-case diagnostic-only report valid.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m specchoice_evidence.cli validate-phase2-source-authority --authority phase2/source-authority.json --bundle bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2` — active accepted-v2 authority valid for 11 fixtures and 28 raw files.
- `git diff --check` — passed.

## TDD Gate Compliance

- RED commits: `25fbeef4`, `1f3c8ca1`, `4810523d`.
- GREEN commits: `a068cadc`, `b21defaf`, `617216f5`.

## Decisions Made

- Formal measurement authority remains restricted to a clean exact all-11 `formal/completed` attempt.
- Diagnostic-only success is an oracle-equivalence result, not an H1 decision, approval, metric, or promotion signal.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Made adversarial report publication exclusive and fsynced**
- **Found during:** Task 3
- **Issue:** The report needed the same immutable no-replace durability boundary as the terminal evidence it summarizes; a normal file write could race an existing report target.
- **Fix:** Reused Phase 1 exclusive-create and directory-fsync helpers, and surface `ADVERSARIAL_REPORT_EXISTS` without modifying an existing target.
- **Files modified:** `experiments/specchoice-v1.3.2/src/specchoice_measurement/cli.py`
- **Verification:** 25-test cumulative suite and report validator passed.
- **Committed in:** `617216f5`

**Total deviations:** 1 auto-fixed (Rule 2).
**Impact on plan:** Strengthens the declared immutable diagnostic-evidence boundary without adding dependencies or authority.

## Known Stubs

None.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan 02-05 can consume the byte-stable formal attempt and separately validated diagnostic-only report for H1 packet construction, while human review and every H1 disposition remain uncreated and unauthorized.

## Self-Check: PASSED

All ten declared artifacts exist; task commits `25fbeef4`, `a068cadc`, `1f3c8ca1`, `b21defaf`, `4810523d`, and `617216f5` exist; the 25-test suite and both artifact validators pass; no tracked files were deleted. Pre-existing `.DS_Store` files remain unstaged.
