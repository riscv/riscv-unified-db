---
phase: 02-deterministic-measurement-spine
reviewed: 2026-07-31T20:56:26Z
depth: standard
files_reviewed: 49
files_reviewed_list:
  - experiments/specchoice-v1.3.2/config/measurement/pr2164-adapter-rules-v1.json
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
  - experiments/specchoice-v1.3.2/reports/h1/h1-source-gold-review-v2/h1-source-gold-review-v2.json
  - experiments/specchoice-v1.3.2/reports/h1/h1-source-gold-review-v2/h1-source-gold-review-v2.md
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/adapter.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/attempts.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/cli.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/h1.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/preflight.py
  - experiments/specchoice-v1.3.2/tests/test_measurement_adapter.py
  - experiments/specchoice-v1.3.2/tests/test_measurement_attempts.py
  - experiments/specchoice-v1.3.2/tests/test_measurement_h1.py
  - experiments/specchoice-v1.3.2/tests/test_measurement_scoring.py
findings:
  critical: 0
  warning: 2
  info: 0
  total: 2
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-07-31T20:56:26Z
**Depth:** standard
**Files Reviewed:** 49
**Status:** issues_found

## Summary

Re-reviewed the five fix commits (`f51b73c8` through `e8ea1df3`), Phase 02 plans/context/research, the v2 H1 packet, and all 12 persisted adversarial attempts. CR-01 through CR-04 are closed: attempts replay the bound raw predictions and terminal artifacts; evidence hashes are fixture-scoped; every oracle attempt is retained and replayed; and the v2 packet is unsigned, decision-free, and keeps `external_publication_authorized: false`. WR-01 and WR-03 are also closed through exclusive/atomic publication. WR-02 is only partially closed, and the full focused suite is presently red.

The v2 report validator replayed all 12 custodial attempts successfully, the v2 H1 packet and Markdown projection validated, and source-authority validation passed. The four unaffected focused modules pass (26 tests). The advertised five-module suite fails two scoring oracle cases.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: Fixture-scoping fix leaves the required scoring-oracle test suite red

**Classification:** WARNING

**File:** `experiments/specchoice-v1.3.2/tests/test_measurement_scoring.py:49-83`

**Issue:** `mutate_for_oracle()` takes the evidence span from `POS_CSR_RW_MTVEC_ACCESS` (`target_span`) and reuses it for the `NEG_EXT_GATED_PBMTE` mutations. The repaired preflight correctly rejects that foreign source with `EVIDENCE_SOURCE_NOT_DECLARED_FOR_FIXTURE`, so the test cannot find the expected `UNEXPECTED_ACCEPTED_PARAMETER` or `NEGATIVE_UNNECESSARILY_SURFACED` diagnostic. The mandated five-module Phase 2 gate therefore fails with two errors, and this test no longer proves those two frozen diagnostics.

**Fix:** Derive a valid span from `NEG_EXT_GATED_PBMTE` for `negative-accepted` and `negative-review`, matching `cli._fixture_span()`, then assert that the only expected diagnostic is the scoring diagnostic. Keep a separate negative test for cross-fixture spans.

### WR-02: Versioned rule validation still accepts an empty mandatory-field contract

**Classification:** WARNING

**File:** `experiments/specchoice-v1.3.2/src/specchoice_measurement/adapter.py:301-308`

**Issue:** The new validation checks only that `expected_fields` is a dictionary with the two expected keys; it never validates either list's exact required fields or even list type. A canonical rules file with both lists set to `[]` is accepted and produces a valid 11-record adapter batch. That leaves a score-bearing portion of the purportedly versioned adapter contract decorative and does not fully close the prior WR-02 requirement that every declared rule field be enforced.

**Fix:** Require the exact immutable mapping below (and add a negative regression test for empty, missing, reordered, or non-string fields):

```python
EXPECTED_FIELDS = {
    "candidate_or_negative": ["expect_extract", "expect_params", "id"],
    "positive": ["class", "expect_extract", "expect_status", "gold_name", "id", "must_have_excerpt"],
}
if rules["expected_fields"] != EXPECTED_FIELDS:
    raise AdapterError("ADAPTER_RULES_INVALID")
```

---

_Reviewed: 2026-07-31T20:56:26Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
