---
phase: 02-deterministic-measurement-spine
reviewed: 2026-07-31T21:18:09Z
depth: deep
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
  critical: 1
  warning: 0
  info: 0
  total: 1
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-07-31T21:18:09Z
**Depth:** deep
**Files Reviewed:** 69
**Status:** issues_found

## Summary

This convergence review replayed the Phase 2 authority, measurement, adversarial, and H1 validation chain and examined the original review at `7cd40a81`, the three fix iterations, and `29798a2a`. CR-01, CR-02, CR-04, WR-01 through WR-03, and the report-level absolute-path and `..` traversal cases are closed. The report-owned attempt directory is also rejected when it is itself a symbolic link.

The latest fix is incomplete, however: an owned `oracle-NN` directory can contain symbolic links for its manifest or artifacts, and the validator follows them. This lets an H1-bound adversarial report validate using evidence stored outside its declared report-owned custody root. The v2 H1 packet is correctly unsigned (all 11 signature slots are null), has no corresponding v2 decision file, remains manually gated, and sets `external_publication_authorized: false`; this finding does not change those states.

Validation run successfully:

- The full five-module Phase 2 `unittest` suite.
- `validate-phase2-source-authority` against the active accepted v2 fixture generation.
- Formal attempt, v2 adversarial-report, and v2 H1 JSON/Markdown validators.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Report-owned attempts may delegate their manifest or artifacts through symbolic links

**Classification:** BLOCKER

**File:** `experiments/specchoice-v1.3.2/src/specchoice_measurement/attempts.py:178-185, 213-215, 246-255`; `experiments/specchoice-v1.3.2/src/specchoice_measurement/cli.py:271-285`

**Issue:** Commit `29798a2a` constrains every case to its generated `oracle-NN` name and rejects a symlinked attempt directory, which closes the absolute-ID, `..`, and directory-symlink variants. But `validate_measurement_attempt()` reads `attempt.json` and each declared artifact with `Path.read_bytes()` without requiring those entries to be regular non-symlink files. `validate_adversarial_report()` therefore accepts a regular report-owned `oracle-01` directory whose `attempt.json` is a link to an otherwise valid attempt outside `{report.stem}-attempts`.

**Reproduction:** In a temporary copy of `adversarial-oracle-results-v2.json` and its `-attempts` directory, copy `oracle-01/attempt.json` outside the attempt root, replace the in-root file with a symbolic link to that external copy, then call `validate_adversarial_report()`. It returns `diagnostic_only`.

This reopens the immutable-custody boundary from original CR-03: the report JSON can be H1-bound while its supposedly retained attempt evidence is not owned by the report packet.

**Fix:** Make attempt validation enforce the same fail-closed filesystem policy for the attempt root, `attempt.json`, and every manifest-declared artifact before reading it. Reuse the project filesystem primitive (or an equivalent `lstat`-based regular-file check that rejects links and special files) and add regressions for an external `attempt.json`, `diagnostics.json`, and `parsed-predictions.json` reached through links inside a regular `oracle-NN` directory. The report validator should surface the same `ADVERSARIAL_REPORT_INVALID` result for each case.

---

_Reviewed: 2026-07-31T21:18:09Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: deep_
