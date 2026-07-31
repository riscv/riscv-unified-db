---
phase: 02-deterministic-measurement-spine
reviewed: 2026-07-31T22:07:27Z
depth: deep
files_reviewed: 12
files_reviewed_list:
  - .planning/phases/02-deterministic-measurement-spine/02-REVIEW.md
  - .planning/phases/02-deterministic-measurement-spine/02-REVIEW-FIX.md
  - experiments/specchoice-v1.3.2/src/specchoice_evidence/filesystem.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/attempts.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/cli.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/h1.py
  - experiments/specchoice-v1.3.2/tests/test_measurement_attempts.py
  - experiments/specchoice-v1.3.2/phase2/source-authority.json
  - experiments/specchoice-v1.3.2/runs/measurement-attempts/formal-golden-pr2164-v1/attempt.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2.json
  - experiments/specchoice-v1.3.2/reports/h1/h1-source-gold-review-v2/h1-source-gold-review-v2.json
  - experiments/specchoice-v1.3.2/reports/h1/h1-source-gold-review-v2/h1-source-gold-review-v2.md
findings:
  critical: 1
  warning: 0
  info: 0
  total: 1
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-07-31T22:07:27Z
**Depth:** deep
**Files Reviewed:** 12
**Status:** issues_found

## Summary

This focused convergence review examined commit `aec8b209` and manual fix iteration 4. It confirms that a leaf which is already a symbolic link is rejected for `attempt.json` and each manifest-declared artifact, and that the adversarial-report validator maps those failures to `ADVERSARIAL_REPORT_INVALID`.

The custody boundary remains bypassable, however: the code checks a pathname with the Phase 1 inspector and then reopens that pathname with `Path.read_bytes()`. A local writer can replace the checked regular leaf with an external symbolic link in that interval; validation then consumes the external bytes and succeeds. The same helper is used for `attempt.json` and every manifest-declared artifact, so the remaining CR-01 is not closed.

The focused attempts suite (8 tests), full five-module Phase 2 suite (36 tests), active v2 source-authority validation, formal-attempt validation, v2 adversarial-report validation, and v2 H1 JSON/Markdown validation all passed. The v2 H1 packet remains unsigned in all 11 signature slots, has no v2 decision file, remains manually gated, and retains `external_publication_authorized: false`.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Leaf custody check and leaf read are not atomic

**Classification:** BLOCKER

**File:** `experiments/specchoice-v1.3.2/src/specchoice_measurement/attempts.py:182-185, 266-268`

**Issue:** `_read_attempt_file()` invokes `inspect_authoritative_path()`—which safely opens and verifies a regular, non-symlink leaf—but discards that opened content and immediately reads the pathname again via `(attempt_root / name).read_bytes()`. The second open follows links. A controlled probe copied a valid `attempt.json` outside an owned attempt, replaced the owned file with a symlink immediately after the inspector returned, and `validate_measurement_attempt()` still returned `completed`. The identical helper is used for every manifest artifact, so `diagnostics.json`, `parsed-predictions.json`, and every formal score artifact retain the same escape.

Static-link tests pass because they install the link before inspection; they do not cover replacement after inspection and before the second open. `validate_adversarial_report()` at `cli.py:285-289` only catches the resulting `AttemptError`, so it cannot close a successful raced read.

**Fix:** Consume bytes from the descriptor that passed the no-follow inspection. Extend the Phase 1 filesystem primitive with a read API that returns the buffered bytes (or expose an equivalent descriptor-backed reader) and have `_read_attempt_file()` use those bytes directly; do not call `Path.read_bytes()` after the custody check. Add a regression that swaps each leaf to an external symlink from the inspector hook and asserts both `validate_measurement_attempt()` and `validate_adversarial_report()` fail closed.

---

_Reviewed: 2026-07-31T22:07:27Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: deep_
