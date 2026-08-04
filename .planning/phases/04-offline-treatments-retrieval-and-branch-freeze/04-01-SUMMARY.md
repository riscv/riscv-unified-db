---
phase: 04-offline-treatments-retrieval-and-branch-freeze
plan: 01
subsystem: offline treatment contracts
tags: [python, unittest, strict-json, canonical-json, delegation-frame]
requires:
  - phase: 03-human-reviewed-data-preregistration
    provides: red-required authority and frozen offline evaluation boundaries
provides:
  - Closed source-bound A/B/C treatment response parser with three DelegationFrame axes
  - Canonical preregistered advisory patterns with deterministic warning-only evaluation
  - Offline adversarial fixtures and regression tests for all Wave 1 contract boundaries
affects: [04-02 offline prompts, 04-03 retrieval contract, 04-04 Red branch freeze]
actuals:
  tokens: 9596
  tasks: 2
  commits: 5
tech-stack:
  added: []
  patterns:
    - Existing strict JSON decoder, canonical JSON bytes, SHA-256, and ordered Diagnostic records
    - Advisory evaluation is a pure post-parse, warning-only projection
key-files:
  created:
    - experiments/specchoice-v1.3.2/src/specchoice_treatments/__init__.py
    - experiments/specchoice-v1.3.2/config/treatments/frame-advisory-patterns-v1.json
    - experiments/specchoice-v1.3.2/fixtures/treatments/frame-response-adversarial-v1.json
  modified:
    - experiments/specchoice-v1.3.2/src/specchoice_treatments/schema.py
    - experiments/specchoice-v1.3.2/tests/test_treatments_frame.py
key-decisions:
  - "B and C use the same closed parser/output schema; only A is frame-free."
  - "Advisory patterns are canonical config validated at import and return only ordered warning Diagnostics."
  - "No provider, model, retrieval, CLI, dependency, or external-action surface is introduced in Wave 1."
patterns-established:
  - "Frame evidence spans retain independent half-open raw-byte ranges, including equal and adjacent spans."
  - "Malformed raw JSON remains raw bytes in tests so strict decoding catches duplicate and non-UTF-8 input before canonicalization."
requirements-completed: [H1-01]
coverage:
  - id: D1
    description: Closed source-bound B/C DelegationFrame parser and frame-free A boundary.
    requirement: H1-01
    verification:
      - kind: unit
        ref: experiments/specchoice-v1.3.2/tests/test_treatments_frame.py
        status: pass
    human_judgment: false
  - id: D2
    description: Preregistered advisory combinations remain deterministic warnings without changing parser validity or values.
    requirement: H1-01
    verification:
      - kind: unit
        ref: experiments/specchoice-v1.3.2/tests/test_treatments_frame.py#test_advisories_are_ordered_nonblocking_and_exact
        status: pass
    human_judgment: false
duration: 1h 15m
completed: 2026-08-04
status: complete
---

# Phase 04 Plan 01: Offline Treatment Frame Contract Summary

**Closed A/B/C DelegationFrame parsing with source-bound evidence spans and canonical warning-only advisory patterns, entirely offline.**

## Performance

- **Duration:** 1h 15m
- **Started:** 2026-08-04T10:32:15Z
- **Completed:** 2026-08-04T11:46:50Z
- **Tasks:** 2/2
- **Files modified:** 8

## Accomplishments

- Parsed the production-quality B tracer response from strict raw JSON through exact UTF-8 source spans to a byte-stable canonical projection.
- Closed A/B/C boundaries, frozen all three frame axes and enums, and covered malformed JSON, frame, span, and adjudication cases with stable errors.
- Added two canonical advisory patterns; matching frames return ordered warning Diagnostics without changing parsed values or validity.

## Contract Identities

| Artifact | SHA-256 |
| --- | --- |
| `delegation-frame-contract-v1.json` | `77bc927c5f3d6f3001930344539942237af1ba2d4e61bb2f22dcc5bb254bd4de` |
| `frame-advisory-patterns-v1.json` | `739be159d93479f3ed769694081f6fbf4eabb524b7c4b19030828b802a795db6` |
| `frame-source-v1.txt` | `031f97bef2b7ed8524962920629f20058f4c059b5d100a18dc17e4f37f3b00e8` |
| `frame-response-b-valid-v1.json` | `2621380e84145c8294bf805f35a8147a742ea11a46bd799fb6d5a96cf73d6258` |
| `frame-response-adversarial-v1.json` | `e13adfe1d8ae2d6406e1c0a9158ceea94b6abb55fa069c71b67d8d006891e3a8` |

## Public Symbols

`TreatmentContractError`, `ParsedTreatmentResponse`, `REQUIRED_FRAME_AXES`, `FRAME_ENUMS`, `FRAME_COMBINATION_REQUIRES_REVIEW`, `parse_treatment_response_v1`, `validate_delegation_frame_v1`, `validate_source_span_v1`, and `evaluate_frame_advisories_v1` are the only Wave 1 package exports.

## Validation

- Passed: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_treatments_frame tests.test_canonical -q` — 15 tests.
- Passed: cumulative Wave 1 unittest command covering data admission/splits/relevance/H2, treatment frames, canonicalization, and filesystem boundary tests.
- Passed: `git diff --check`.
- Not run: the plan's Ruff command because neither `ruff` nor `mise` is available in the current execution environment. No replacement linter or dependency was added.

## Task Commits

1. **Task 1: Parse one valid source-bound B response end to end** — `60d22c6c` (RED test), `98394e5f` (implementation).
2. **Task 2: Close A/B/C boundaries and non-blocking advisory behavior** — `0d310a38` (RED test), `526a846f` (implementation), `a9238d52` (boundary regression coverage).

## Files Created/Modified

- `experiments/specchoice-v1.3.2/src/specchoice_treatments/schema.py` — strict response/frame/span parsing and advisory evaluation.
- `experiments/specchoice-v1.3.2/src/specchoice_treatments/__init__.py` — explicit Wave 1 public API.
- `experiments/specchoice-v1.3.2/config/treatments/delegation-frame-contract-v1.json` — canonical response/frame contract.
- `experiments/specchoice-v1.3.2/config/treatments/frame-advisory-patterns-v1.json` — canonical preregistered warnings.
- `experiments/specchoice-v1.3.2/fixtures/treatments/frame-source-v1.txt` — synthetic source bytes.
- `experiments/specchoice-v1.3.2/fixtures/treatments/frame-response-b-valid-v1.json` — valid source-bound B response.
- `experiments/specchoice-v1.3.2/fixtures/treatments/frame-response-adversarial-v1.json` — canonical raw adversarial table.
- `experiments/specchoice-v1.3.2/tests/test_treatments_frame.py` — 11 frame tests; 15 tests together with canonical regressions.

## Decisions Made

- B and C have identical closed frame/output schemas, while A forbids the frame entirely.
- Warning diagnostics are evaluated only after parsing and remain separate from blocker diagnostics, parsed fields, and `ParsedTreatmentResponse.valid`.
- The canonical config is checked for strict JSON, exact keys, known enum values, duplicate IDs, expected diagnostic, stable ID order, and canonical bytes before use.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Ruff is unavailable from both PATH and mise in this execution environment, so its specified lint verification was not run. The unit and cumulative verification commands passed; the missing lint invocation is tracked in the cross-phase Windows ledger.

## User Setup Required

None - no external service configuration, command surface, provider/model path, retrieval path, or external action was added.

## Next Phase Readiness

Wave 2 can build offline prompt fixtures on the closed parser contract. It must preserve the frame-free A boundary, identical B/C output shape, source-bound evidence, and non-authorizing advisory behavior.

## Self-Check: PASSED

- All eight listed contract/parser/config/fixture/test files exist.
- All five task commits are present in Git history.
- No tracked-file deletions were introduced by the task commits.

---
*Phase: 04-offline-treatments-retrieval-and-branch-freeze*
*Completed: 2026-08-04*
