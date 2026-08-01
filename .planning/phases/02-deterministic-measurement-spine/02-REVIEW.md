---
phase: 02-deterministic-measurement-spine
reviewed: 2026-08-01T17:09:14Z
depth: standard
files_reviewed: 32
files_reviewed_list:
  - experiments/specchoice-v1.3.2/config/measurement/canonical-adjudication-schema-v1.json
  - experiments/specchoice-v1.3.2/config/measurement/h1-review-schema-v1.json
  - experiments/specchoice-v1.3.2/config/measurement/pr2164-adapter-rules-v1.json
  - experiments/specchoice-v1.3.2/fixtures/measurement/adversarial/required-diagnostics-v1.json
  - experiments/specchoice-v1.3.2/fixtures/measurement/golden-predictions-v1.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v1.json
  - experiments/specchoice-v1.3.2/reports/h1/h1-source-gold-review-v1.json
  - experiments/specchoice-v1.3.2/reports/h1/h1-source-gold-review-v1.md
  - experiments/specchoice-v1.3.2/reports/h1/h1-source-gold-review-v2/h1-source-gold-review-v2.json
  - experiments/specchoice-v1.3.2/reports/h1/h1-source-gold-review-v2/h1-source-gold-review-v2.md
  - experiments/specchoice-v1.3.2/reviews/h1-source-gold-decision-v1.json
  - experiments/specchoice-v1.3.2/runs/measurement-attempts/formal-golden-pr2164-v1/attempt.json
  - experiments/specchoice-v1.3.2/runs/measurement-attempts/formal-golden-pr2164-v1/case-outcomes.json
  - experiments/specchoice-v1.3.2/runs/measurement-attempts/formal-golden-pr2164-v1/diagnostics.json
  - experiments/specchoice-v1.3.2/runs/measurement-attempts/formal-golden-pr2164-v1/metrics.json
  - experiments/specchoice-v1.3.2/runs/measurement-attempts/formal-golden-pr2164-v1/parsed-predictions.json
  - experiments/specchoice-v1.3.2/runs/measurement-attempts/formal-golden-pr2164-v1/report.json
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/__init__.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/adapter.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/attempts.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/cli.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/diagnostics.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/domain.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/h1.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/preflight.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/scoring.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/strict_json.py
  - experiments/specchoice-v1.3.2/tests/test_measurement_adapter.py
  - experiments/specchoice-v1.3.2/tests/test_measurement_attempts.py
  - experiments/specchoice-v1.3.2/tests/test_measurement_h1.py
  - experiments/specchoice-v1.3.2/tests/test_measurement_parsing.py
  - experiments/specchoice-v1.3.2/tests/test_measurement_scoring.py
findings:
  critical: 2
  warning: 1
  info: 0
  total: 3
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-08-01T17:09:14Z
**Depth:** standard
**Files Reviewed:** 32
**Status:** issues_found

## Summary

The canonical adapter, closed prediction parsing, scoring, immutable-attempt replay, H1 packet projection, and supplied v1/v2 evidence artifacts were reviewed. The local-only H1 boundary and `external_publication_authorized: false` remain intact. However, two validator paths incorrectly attest to incomplete or false evidence lineage. The focused 37-test measurement suite passes when run with the same absolute source path used by the current interpreter; the test suite itself has one interpreter-selection defect.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Adversarial-report validation trusts the report's claimed formal-attempt hash

**File:** `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_measurement/cli.py:263`
**Issue:** `validate_adversarial_report()` builds its expected bindings using `str(bindings.get("formal_attempt_sha256"))`, i.e. the untrusted value it is meant to validate. It validates each diagnostic-only case but never validates the formal attempt or compares the claimed digest with it. A canonical copied v2 report with only that hash replaced by 64 zeroes returns success, so a report can be declared valid while falsely claiming its prerequisite formal-measurement lineage.
**Fix:** Validate the one bound formal attempt (or accept its path as an explicit argument), obtain its verified `attempt_sha256`, require `role == "formal"` and `status == "completed"`, and use that verified digest when constructing `_adversarial_bindings` rather than the report's value.

### CR-02: Adapter failure handling discards the conflict evidence required for audit

**File:** `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_measurement/adapter.py:337`
**Issue:** A record-level source/gold/expected disagreement raises an `AdapterError`, but the catch block replaces it with an `_invalid_batch()` containing only a code and an empty `source_identity` (lines 338-343). `_invalid_batch()` itself constructs a diagnostic with no fixture ID, field, expected value, observed value, or source hashes (lines 295-304). This violates the locked failure-audit contract: a rejected adapter is fail-closed, but reviewers cannot determine which evidence conflicted or reproduce the diagnosis from the emitted batch.
**Fix:** Carry a structured diagnostic (including fixture ID, field, expected/observed values, and both source hashes) in a typed adapter failure; preserve the already-verified source identity; then emit that diagnostic in the invalid batch/immutable failed-adaptation artifact while retaining zero score-eligible records.

## Warnings

### WR-01: CLI tests can execute a different, unconfigured Python interpreter

**File:** `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/tests/test_measurement_adapter.py:65`
**Issue:** The subprocess tests invoke literal `python3` rather than the interpreter running the tests. In this checkout, the test interpreter has the source package available while `python3` resolves to a different Python 3.14 installation and fails with `ModuleNotFoundError`, producing false failures or testing the wrong installed package.
**Fix:** Import `sys` and construct both subprocess commands with `sys.executable` (and, if needed, an explicit absolute source environment) so the child uses the same tested package and interpreter.

---

_Reviewed: 2026-08-01T17:09:14Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
