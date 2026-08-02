---
phase: 02-deterministic-measurement-spine
plan: 15
subsystem: measurement-custody
tags: [python, h1, pending-v3, readiness, human-decision, descriptor-custody]
requires:
  - phase: 02-14
    provides: descriptor-held pending-v3 formal and adversarial rehearsal inputs
provides:
  - Explicit schema-v2 H1 packet and one-time readiness receipt contracts
  - Read-only, packet-and-readiness-bound H1 human-decision-v2 validation
affects: [02-16, 02-17, measurement-reporting]
tech-stack:
  added: []
  patterns: [explicit schema selection, no-replace readiness receipt, closed human-decision validation]
key-files:
  created:
    - experiments/specchoice-v1.3.2/config/measurement/h1-review-schema-v2.json
  modified:
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/h1.py
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/cli.py
    - experiments/specchoice-v1.3.2/tests/test_measurement_h1.py
    - experiments/specchoice-v1.3.2/tests/test_measurement_adapter.py
key-decisions:
  - "H1 packet v2 must receive its schema explicitly; successor packets cannot select a schema by default."
  - "Readiness is immutable and decision-free; the only successor decision API validates closed human-authored data."
  - "The adapter CLI keeps active-v2 unchanged and exposes pending-v3 only through explicit authority and transition inputs."
patterns-established:
  - "Bind receipt inputs by canonical held bytes and validate existing receipts against fresh exact inputs without rewriting."
requirements-completed: [TS-03, TS-04, TS-05]
coverage:
  - id: D1
    description: Explicit schema-v2 H1 packet plus one-time readiness receipt validates packet, Markdown, retained evidence, phase-gate stdin bytes, and a disposable summary projection.
    requirement: TS-03
    verification:
      - kind: unit
        ref: tests/test_measurement_h1.py#test_readiness_is_one_time_and_validator_is_read_only
        status: pass
    human_judgment: false
  - id: D2
    description: Closed decision-v2 validator binds all eleven packet fixtures and seven named semantic responses without offering a decision writer, default, or inference path.
    requirement: TS-04
    verification:
      - kind: unit
        ref: tests/test_measurement_h1.py#test_v2_decision_validator_checks_closed_human_contract_without_authoring
        status: pass
    human_judgment: false
  - id: D3
    description: Public H1 and adapter contracts preserve the pending-v3 rehearsal boundary and exact fixed-red oracle partition.
    requirement: TS-05
    verification:
      - kind: other
        ref: tests/phase1_expected_red_oracle.py --expected-focused 72 --expected-discovered 150 --expected-green 145
        status: pass
    human_judgment: false
duration: 11min
completed: 2026-08-02
status: complete
---

# Phase 02 Plan 15: H1 Readiness and Decision Contracts Summary

**Explicit schema-v2 H1 packets, one-time readiness receipts, and read-only human decision-v2 validation preserve pending-v3 rehearsal while active-v2 remains authoritative.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-08-02T11:35:00Z
- **Completed:** 2026-08-02T11:46:16Z
- **Tasks:** 1
- **Files modified:** 5

## Accomplishments

- Added immutable `h1-review-schema-v2.json` and made H1 packet construction and validation require it explicitly.
- Added `write-h1-readiness-v3` and `validate-h1-readiness-v3`: no-replace creation binds formal/adversarial, packet/Markdown, schema, pending authority, revocation, offline replay, phase-gate stdin, and a disposable absolute summary projection.
- Added `validate-h1-decision-v2`, which checks exact hashes, eleven fixture reviews, seven closed semantic responses, aggregate consistency, and `external_publication_authorized: false` without creating a human decision.
- Routed the adapter CLI test through explicit pending-v3 authority and transition inputs without altering active-v2 custody.

## Task Commits

1. **Task 1: Carry held attempt and adversarial identities into decision-free H1 readiness** - `20c39761` (test, RED)
2. **Task 1: Carry held attempt and adversarial identities into decision-free H1 readiness** - `ac949686` (feat, GREEN)

## Files Created/Modified

- `experiments/specchoice-v1.3.2/config/measurement/h1-review-schema-v2.json` - Closed successor schema; SHA-256 `e9b78cbba7564c2c2eddb0d4d3fff4ee14f020c601770b171124812b520e2ee8`.
- `experiments/specchoice-v1.3.2/src/specchoice_measurement/h1.py` - Explicit-schema packet, no-replace readiness writer/read-only validator, and closed decision-v2 validator.
- `experiments/specchoice-v1.3.2/src/specchoice_measurement/cli.py` - Explicit schema/readiness/decision command contracts and optional pending-v3 adapter inputs.
- `experiments/specchoice-v1.3.2/tests/test_measurement_h1.py` - WR-01 public role matrix and readiness/decision contract tests.
- `experiments/specchoice-v1.3.2/tests/test_measurement_adapter.py` - Explicit pending-v3 CLI fixture rewrite.

## Decisions Made

- Schema-v1 is historical and unchanged; schema-v2 is the required explicit successor for all new H1 packet and decision paths.
- The decision validator reports only a canonical validation receipt; no public or private H1 human-disposition writer, default, or approval inference was introduced.
- No real readiness receipt, H1 decision, authority cutover, revocation, report, or publication artifact was created.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_measurement_h1 tests.test_measurement_adapter -v` — 19/19 passed.
- `PYTHONPATH=src python3 tests/phase1_expected_red_oracle.py --expected-focused 72 --expected-discovered 150 --expected-green 145` — passed with the fixed five-parent/six-outcome red partition.
- Protected files unchanged: schema-v1 `42b5c2ad7b0022872805b2f02b87084be8b0eee55ee39c15ff1fe06d1ef85373`; active-v2 authority `6943ae60b5a22b4cc262bbcc0c252fbd9a31e5e5cbaac9f79976087b63a4ce23`; pending-v3 authority `e1681a347a6d9cbdf6d0f19863b4d2856a36663949fcc0a6f4d2960c5dd8e6d1`; readiness `24dc6bbfc56c1fbcdc856015673b109987b2e7683465f57d6bd20225689bbdc5`; transition `472bc06268c2e7c70d6975717f9d0f60b14e1a495cbca73342e9effe7bb33543`.
- Protected-path inspection was restricted to plan-declared paths because another agent's excluded planning file must not be enumerated.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Issues Encountered

None.

## Next Phase Readiness

02-16 can consume the explicit successor contracts when it performs its separately authorized cutover work. Actual readiness execution, human disposition, H1 packet, formal/adversarial evidence, authority cutover, and publication remain intentionally absent.

## Self-Check: PASSED

- Confirmed `h1.py` and `h1-review-schema-v2.json` exist and task commits `20c39761` and `ac949686` are reachable.

---
*Phase: 02-deterministic-measurement-spine*
*Completed: 2026-08-02*
