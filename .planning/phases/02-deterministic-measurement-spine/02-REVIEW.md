---
phase: 02-deterministic-measurement-spine
reviewed: 2026-07-31T21:07:22Z
depth: standard
files_reviewed: 69
files_reviewed_list:
  - experiments/specchoice-v1.3.2/config/measurement/canonical-adjudication-schema-v1.json
  - experiments/specchoice-v1.3.2/config/measurement/h1-review-schema-v1.json
  - experiments/specchoice-v1.3.2/config/measurement/pr2164-adapter-rules-v1.json
  - experiments/specchoice-v1.3.2/fixtures/measurement/adversarial/required-diagnostics-v1.json
  - experiments/specchoice-v1.3.2/fixtures/measurement/golden-predictions-v1.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v1.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-01/attempt.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-01/diagnostics.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-01/parsed-predictions.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-02/attempt.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-02/diagnostics.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-02/parsed-predictions.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-03/attempt.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-03/diagnostics.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-03/parsed-predictions.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-04/attempt.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-04/diagnostics.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-04/parsed-predictions.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-05/attempt.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-05/diagnostics.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-05/parsed-predictions.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-06/attempt.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-06/diagnostics.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-06/parsed-predictions.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-07/attempt.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-07/diagnostics.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-07/parsed-predictions.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-08/attempt.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-08/diagnostics.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-08/parsed-predictions.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-09/attempt.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-09/diagnostics.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-09/parsed-predictions.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-10/attempt.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-10/diagnostics.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-10/parsed-predictions.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-11/attempt.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-11/diagnostics.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-11/parsed-predictions.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-12/attempt.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-12/diagnostics.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2-attempts/oracle-12/parsed-predictions.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v2.json
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
  critical: 0
  warning: 1
  info: 0
  total: 1
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-07-31T21:07:22Z
**Depth:** standard
**Files Reviewed:** 69
**Status:** issues_found

## Summary

The two latest fixes resolve the prior scoring-suite regression and enforce the exact `expected_fields` contract. The full five-module Phase 02 suite passes (35 tests), and the Phase 2 source-authority, v2 adversarial-report, and v2 H1 JSON/Markdown validators all pass. The current H1 v2 packet has 11 blank signature slots, no v2 decision artifact, and `external_publication_authorized: false`; its deliberate manual gate remains intact.

The original CR-01 through CR-04 and WR-01 through WR-03 are otherwise closed: attempts are replay-derived, evidence spans are fixture-scoped, all twelve current oracle attempts are retained, adapter and packet publication are no-replace/atomic, and a machine-created `approved` H1 decision is rejected with `H1_MANUAL_AUTHORIZATION_REQUIRED`. One report-custody path boundary remains open.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: Adversarial-report validation accepts attempts outside its owned custody directory

**Classification:** WARNING

**File:** `experiments/specchoice-v1.3.2/src/specchoice_measurement/cli.py:271-281`

**Issue:** The report is meant to retain each oracle attempt under `{report.stem}-attempts`, but `case["attempt_id"]` is only checked as a string before it is appended to that root. A `Path` join with an absolute string discards `attempt_root`, while `..` components can escape it. The validator therefore accepts a canonical report whose 12 cases reference valid diagnostic attempts elsewhere on disk. This weakens the report-owned immutable-custody guarantee that closed CR-03 and makes validation depend on external paths rather than only the report packet.

**Reproduction:** Replacing every v2 case `attempt_id` with the absolute path to its existing `oracle-NN` directory, while leaving a present empty `{report.stem}-attempts` directory, is accepted by `validate_adversarial_report()`.

**Fix:** Require the generated, path-safe identifier for each position and resolve/check the path before reading it. For example:

```python
expected_id = f"oracle-{index:02d}"
if case.get("attempt_id") != expected_id:
    raise AttemptError("ADVERSARIAL_REPORT_INVALID")
attempt_path = attempt_root / expected_id
```

Also add regressions for absolute paths, `..`, and a valid attempt stored outside the report-owned root.

---

_Reviewed: 2026-07-31T21:07:22Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
