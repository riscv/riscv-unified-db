---
phase: 02
fixed_at: 2026-07-31T22:13:10Z
review_path: .planning/phases/02-deterministic-measurement-spine/02-REVIEW.md
iteration: 5
findings_in_scope: 1
fixed: 1
skipped: 0
status: all_fixed
---

# Phase 02: Code Review Fix Report

**Fixed at:** 2026-07-31T22:13:10Z
**Source review:** `.planning/phases/02-deterministic-measurement-spine/02-REVIEW.md`
**Iteration:** 5 (manual fix round)

**Summary:**

- Findings in scope: 1
- Fixed: 1
- Skipped: 0

## Fixed Issues

### CR-01: Leaf custody check and leaf read are not atomic

**Files modified:** `experiments/specchoice-v1.3.2/src/specchoice_evidence/filesystem.py`, `experiments/specchoice-v1.3.2/src/specchoice_measurement/attempts.py`, `experiments/specchoice-v1.3.2/tests/test_filesystem_boundary.py`, `experiments/specchoice-v1.3.2/tests/test_measurement_attempts.py`
**Commit:** 9d641ec8
**Applied fix:** Phase 1 now exposes a descriptor-backed regular-file reader that requires `O_NOFOLLOW`, checks the opened descriptor's regular-file/device/inode identity against the inspected path, and returns exactly those buffered bytes. Attempt validation consumes that returned buffer rather than reopening a pathname. Direct-symlink coverage remains; new deterministic hooks replace `attempt.json` and `diagnostics.json` with valid external symlinks after `lstat` and immediately before `open`, proving the external bytes are rejected rather than consumed. Unsupported no-follow platforms fail closed.

## Validation

- `tests.test_measurement_attempts` plus `tests.test_filesystem_boundary`: 31 tests passed.
- Full five-module Phase 2 suite: 37 tests passed.
- `validate-phase2-source-authority` passed against the active accepted v2 generation.
- Formal-attempt, v2 adversarial-report, and v2 H1 JSON/Markdown validators passed.

## Human Checkpoint Required

The v2 H1 packet remains unsigned and `external_publication_authorized: false`. No decision, signature, approval, external authority, or publication action was created or reused. Manual review remains required before downstream progression.

---

_Fixed: 2026-07-31T22:13:10Z_
_Fixer: the agent (gsd-code-fixer)_
_Iteration: 5_
