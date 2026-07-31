---
phase: 02
fixed_at: 2026-07-31T21:02:28Z
review_path: .planning/phases/02-deterministic-measurement-spine/02-REVIEW.md
iteration: 2
findings_in_scope: 2
fixed: 2
skipped: 0
status: all_fixed
---

# Phase 02: Code Review Fix Report

**Fixed at:** 2026-07-31T21:02:28Z
**Source review:** `.planning/phases/02-deterministic-measurement-spine/02-REVIEW.md`
**Iteration:** 2

**Summary:**

- Findings in scope: 2
- Fixed: 2
- Skipped: 0

## Fixed Issues

### WR-01: Fixture-scoping fix leaves the required scoring-oracle test suite red

**Files modified:** `experiments/specchoice-v1.3.2/tests/test_measurement_scoring.py`
**Commit:** 66d45dd0
**Applied fix:** The two negative oracle mutations now use `cli._fixture_span()` for `NEG_EXT_GATED_PBMTE`, preserving fixture-scoped valid evidence and restoring the expected scoring diagnostics. The separate cross-fixture rejection test remains in the parsing suite.

### WR-02: Versioned rule validation still accepts an empty mandatory-field contract

**Files modified:** `experiments/specchoice-v1.3.2/src/specchoice_measurement/adapter.py`, `experiments/specchoice-v1.3.2/tests/test_measurement_adapter.py`
**Commit:** 076871fd
**Applied fix:** The adapter now requires the exact immutable `expected_fields` mapping. Regressions reject empty, missing, reordered, and non-string field variants.

## Validation

- Full five-module Phase 2 suite: 35 tests passed.
- Phase 2 source-authority validator passed.
- Adversarial report v2 and H1 packet v2 validators passed.

## Human Checkpoint Required

The v2 H1 packet remains unsigned and `external_publication_authorized: false`. No decision, signature, approval, external authority, or publication action was created or reused. Manual review remains required before downstream progression.

---

_Fixed: 2026-07-31T21:02:28Z_
_Fixer: the agent (gsd-code-fixer)_
_Iteration: 2_
