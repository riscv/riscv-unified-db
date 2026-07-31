---
phase: 02
fixed_at: 2026-07-31T20:30:00+02:00
review_path: .planning/phases/02-deterministic-measurement-spine/02-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 7
skipped: 0
status: all_fixed
---

# Phase 02: Code Review Fix Report

**Fixed at:** 2026-07-31T20:30:00+02:00
**Source review:** `.planning/phases/02-deterministic-measurement-spine/02-REVIEW.md`
**Iteration:** 1

**Summary:**

- Findings in scope: 7
- Fixed: 7
- Skipped: 0

## Fixed Issues

### CR-01: Attempt validation authenticates hashes, not the measured result

**Files modified:** `attempts.py`, `preflight.py`, `test_measurement_attempts.py`
**Commit:** f51b73c8
**Evidence:** Validation now rebuilds the bound adapter, preflights stored raw predictions, rescoring and byte-compares each terminal artifact and binding. A self-consistent forged metrics manifest is rejected.

### CR-02: Evidence from another fixture is accepted as evidence for the scored fixture

**Files modified:** `preflight.py`, `strict_json.py`, parsing/scoring tests
**Commit:** 48e8d731
**Evidence:** Evidence source hashes are scoped to the scored fixture; a copied valid span from another fixture is rejected.

### CR-03: The adversarial oracle report claims custody for deleted attempts

**Files modified:** `cli.py`, `test_measurement_attempts.py`
**Commit:** 57bb3db1
**Evidence:** Report v2 retains 12 diagnostic-only attempts and validator replays each persisted raw mutation, oracle result, and attempt digest.

### CR-04: H1 approval can be fabricated by a machine-authored JSON file

**Files modified:** `h1.py`, H1 tests, unsigned v2 H1 evidence
**Commit:** 33c38609
**Evidence:** A local `approved` JSON decision now raises `H1_MANUAL_AUTHORIZATION_REQUIRED`; the new packet is unsigned and `external_publication_authorized` remains false.

### WR-01: Adapter output creation is overwriteable through a check/write race

**Files modified:** `cli.py`, `test_measurement_adapter.py`
**Commit:** 6de395f5
**Evidence:** Adapter output uses exclusive creation and directory fsync, and rejects existing and symlink targets.

### WR-02: The versioned adapter rules are largely decorative and forbid a successor version

**Files modified:** `adapter.py`, `test_measurement_adapter.py`
**Commit:** e8ea1df3
**Evidence:** The adapter validates the complete rule contract, requires the declared score-bearing fields, rejects missing positive evidence requirements, and accepts constrained `pr2164-adapter-vN` identifiers.

### WR-03: H1 packet publication can leave an unrecoverable half-packet

**Files modified:** `h1.py`, H1 tests
**Commit:** 33c38609
**Evidence:** JSON and Markdown are staged, validated, fsynced, and published together as a no-replace packet directory; identical or split paths are rejected.

## Tests

- Focused five-module Phase 2 suite passed: 33 tests.
- `validate-h1-packet` passed for `h1-source-gold-review-v2`.

## Human Checkpoint Required

The earlier H1 decision SHA `854641363240105acf9840dd6d6d9a01e0188b1c3b235a97559d290cccd3c0ec`, bound to packet SHA `a897029b51a386917b2baf45410e7ed1e56a7208f68cabffdab72ee2b6a37936`, is invalid for the v2 adversarial report and packet. No replacement decision or signature was generated. A user must independently review and authorize the new unsigned packet SHA `4482bfe4c28a825e86365420c071ed267afc3d0370ce333e4cdd16916b58c81c` through the separate manual authorization mechanism before Phase 3 may proceed. External publication remains unauthorized.

---

_Fixed: 2026-07-31T20:30:00+02:00_
_Fixer: the agent (gsd-code-fixer)_
_Iteration: 1_
