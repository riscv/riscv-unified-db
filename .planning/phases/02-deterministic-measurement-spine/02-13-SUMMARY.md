---
phase: 02-deterministic-measurement-spine
plan: 13
subsystem: measurement-custody
tags: [python, adapter, preflight, descriptor-custody, pending-v3]
requires:
  - phase: 02-12
    provides: accepted-v3 receipts and a non-effective v10 pending authority
provides:
  - Explicit pending-v3 adapter/preflight rehearsal with active-v2 defaults unchanged
  - Canonical cutover-validator receipt binding and descriptor-held source bytes
affects: [02-14, 02-15, 02-16]
tech-stack:
  added: []
  patterns: [explicit pending authority inputs, closed subprocess stdout receipt, single descriptor-read source maps]
key-files:
  created: [experiments/specchoice-v1.3.2/receipts/source-cutover-readiness-v10.json]
  modified:
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/adapter.py
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/preflight.py
    - experiments/specchoice-v1.3.2/tests/test_measurement_adapter.py
    - experiments/specchoice-v1.3.2/tests/test_measurement_parsing.py
key-decisions:
  - "Pending v3 is accepted only through explicit pending-authority and transition arguments; no default authority changed."
  - "The public validator's one canonical stdout object is compared to descriptor-held authority, transition, bundle, registry, and acceptance-audit results."
patterns-established:
  - "Pending cutover consumers must preserve verifier-proven provenance while returning zero records on custody failure."
  - "Preflight derives fixture and SHA maps from the same descriptor-held source read."
requirements-completed: [TS-03, TS-04, TS-05]
coverage:
  - id: D1
    description: Explicit pending-v3 adapter boundary remains non-effective and validates complete canonical custody.
    requirement: TS-03
    verification:
      - kind: unit
        ref: tests/test_measurement_adapter.py#test_explicit_pending_v3_builds_the_complete_canonical_partition
        status: pass
    human_judgment: false
  - id: D2
    description: Preflight reuses descriptor-held fixture bytes exactly once per fixture.
    requirement: TS-04
    verification:
      - kind: unit
        ref: tests/test_measurement_parsing.py#test_public_preflight_reuses_one_descriptor_read_per_fixture
        status: pass
    human_judgment: false
  - id: D3
    description: The immutable readiness receipt records only the pending-v3 adapter/preflight rehearsal.
    requirement: TS-05
    verification:
      - kind: other
        ref: tests/phase1_expected_red_oracle.py --expected-focused 69 --expected-discovered 147 --expected-green 142
        status: pass
    human_judgment: false
duration: 11min
completed: 2026-08-02
status: complete
---

# Phase 02 Plan 13: Pending-v3 Adapter Custody Summary

**Explicit pending-v3 adapter/preflight rehearsal bound to canonical validator custody while active-v2 remains the untouched default.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-08-02T09:30:34Z
- **Completed:** 2026-08-02T09:41:54Z
- **Tasks:** 1
- **Files modified:** 5

## Accomplishments

- Added explicit pending-authority and transition inputs, invoking the public validator with `sys.executable` and an explicit source environment.
- Bound closed canonical stdout to held pending/active/transition, accepted bundle, registry, partition, and acceptance-audit identities; custody failures return zero records with verified provenance.
- Derived preflight fixture and SHA maps from one descriptor-held read and wrote the no-replace non-authoritative readiness receipt.

## Task Commits

1. **Task 1: Bind adapter and preflight to explicit pending-v3 held results** - `3ea0e3c6` (test, RED)
2. **Task 1: Bind adapter and preflight to explicit pending-v3 held results** - `1678f5d4` (feat, GREEN)

## Files Created/Modified

- `experiments/specchoice-v1.3.2/src/specchoice_measurement/adapter.py` - Explicit pending-v3 validator binding, descriptor-held inputs, and fail-closed provenance.
- `experiments/specchoice-v1.3.2/src/specchoice_measurement/preflight.py` - One-read fixture/SHA source map derivation.
- `experiments/specchoice-v1.3.2/tests/test_measurement_adapter.py` - Pending-v3, receipt-replacement, subprocess-environment, and authority/rule boundary tests.
- `experiments/specchoice-v1.3.2/tests/test_measurement_parsing.py` - Single descriptor-read preflight regression test.
- `experiments/specchoice-v1.3.2/receipts/source-cutover-readiness-v10.json` - Immutable pending-v3 adapter/preflight readiness, SHA-256 `24dc6bbfc56c1fbcdc856015673b109987b2e7683465f57d6bd20225689bbdc5`.

## Decisions Made

- Pending v3 requires both explicit custody arguments; omitting either is a blocker, while the legacy active-v2 invocation keeps its original public authority gate.
- The readiness receipt records `cutover_effective: false`, local-only policy, and no measurement attempt, evidence, H1, cutover, or publication authority.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_measurement_adapter tests.test_measurement_parsing -v` — 20/20 passed.
- `PYTHONPATH=src python3 tests/phase1_expected_red_oracle.py --expected-focused 69 --expected-discovered 147 --expected-green 142` — passed with the exact fixed red partition.
- Protected-source hashes unchanged: active-v2 `6943ae60b5a22b4cc262bbcc0c252fbd9a31e5e5cbaac9f79976087b63a4ce23`, pending-v3 `e1681a347a6d9cbdf6d0f19863b4d2856a36663949fcc0a6f4d2960c5dd8e6d1`, transition `472bc06268c2e7c70d6975717f9d0f60b14e1a495cbca73342e9effe7bb33543`.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Next Phase Readiness

Adapter/preflight is ready for the downstream formal and adversarial reader migration in 02-14. Active-v2 authority and canonical revocation remain untouched.

## Self-Check: PASSED

- Confirmed the five planned task files and commits `3ea0e3c6` and `1678f5d4` exist.

---
*Phase: 02-deterministic-measurement-spine*
*Completed: 2026-08-02*
