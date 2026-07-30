---
phase: 01-isolated-evidence-boundary-and-source-integrity
reviewed: 2026-07-30T18:16:43Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - experiments/specchoice-v1.3.2/receipts/boundary-restart-v5.json
  - experiments/specchoice-v1.3.2/config/boundary_allowlist-v5-gap-closure.json
  - experiments/specchoice-v1.3.2/baselines/phase-start-v5-gap-closure.json
  - experiments/specchoice-v1.3.2/receipts/integrity-receipt-v5.json
  - experiments/specchoice-v1.3.2/receipts/integrity-receipt-v5.md
  - experiments/specchoice-v1.3.2/src/specchoice_evidence/baseline.py
  - experiments/specchoice-v1.3.2/src/specchoice_evidence/receipt.py
  - experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py
  - experiments/specchoice-v1.3.2/tests/test_filesystem_boundary.py
  - experiments/specchoice-v1.3.2/tests/test_receipts.py
findings:
  critical: 2
  warning: 2
  info: 0
  total: 4
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-30T18:16:43Z
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

The v5 baseline, allowlist, restart receipt, history-aware Git query, receipt projection, and focused tests were reviewed in context. The original TS-01 committed-history blind spot is closed for endpoint changes: `check-boundary` now resolves the baseline commit, rejects non-descendant revisions, and compares it through an exact reviewed commit. The current invocation showed all non-metadata v5 changes allowed and all `.DS_Store` paths visible but nonblocking.

That improvement is not sufficient to advance the phase. The newly introduced schema-3 receipt path can mint a passing self-hashed receipt without the reviewer-approved receipt basis and does not prove that its claimed v5 lineage baseline is the baseline named by the receipt. These are integrity-boundary failures. 01-05 is **not ready** for ASVS L1 security audit or independent phase verification until the blockers are fixed and re-reviewed.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: v5 receipt construction bypasses the reviewer-approved basis

**Classification:** BLOCKER

**File:** `experiments/specchoice-v1.3.2/src/specchoice_evidence/receipt.py:223`

**Issue:** The mismatch check is conditioned on `restart_lineage is None`. Every v5/schema-3 receipt supplies restart lineage, so `build_local_mvp_receipt()` accepts an arbitrary `reviewed_receipt_basis_sha256` and then emits a passing, self-hashed receipt based on newly computed boundary facts. A direct call with a deliberately wrong basis (`"0" * 64`) and valid lineage returns `outcome: "pass"`. This defeats the required binding between the recorded reviewer decision and the local receipt basis; the CLI's earlier preflight check does not make the constructor safe against a changed boundary state or other callers.

**Fix:** Enforce the basis comparison for every receipt version before constructing the receipt.

```python
basis = local_receipt_basis_sha256(
    baseline_sha256, environment_sha256, source_identity, records
)
if reviewed_receipt_basis_sha256 != basis:
    raise ReceiptError("LOCAL_RECEIPT_BASIS_MISMATCH")
```

Add a schema-3 regression that passes a valid `restart_lineage` with a wrong reviewer basis and asserts `LOCAL_RECEIPT_BASIS_MISMATCH`.

### CR-02: Schema-3 validation accepts a receipt whose lineage names a different baseline

**File:** `experiments/specchoice-v1.3.2/src/specchoice_evidence/receipt.py:165`

**Classification:** BLOCKER

**Issue:** `validate_receipt()` checks only that each `restart_lineage` hash is syntactically a SHA-256 value. It never requires `restart_lineage["baseline"]["sha256"]` to equal `phase_start_baseline_sha256`, nor binds the other lineage fields to the stated restart generation. Consequently, a canonical, self-hashed passing schema-3 receipt can pair its boundary classifications and top-level baseline digest with an unrelated but well-formed lineage. `finalize-review` relies on this validator, so it does not repair the missing check. The committed v5 artifact happens to match, but the validator does not prove the claimed v5 binding.

**Fix:** Reject mismatched lineage fields in the canonical validator, then add a negative finalization test.

```python
if lineage["baseline"]["sha256"] != receipt["phase_start_baseline_sha256"]:
    raise ReceiptError("RESTART_LINEAGE_BASELINE_MISMATCH")
```

Also validate the lineage projection against `validate_boundary_restart()` in the command path, including its fixed predecessor, allowlist, incident-receipt paths, and reviewed revision.

## Warnings

### WR-01: Baseline-inventory paths discard committed and live provenance

**Classification:** WARNING

**File:** `experiments/specchoice-v1.3.2/src/specchoice_evidence/baseline.py:306`

**Issue:** `merge_boundary_changes()` correctly combines committed and live sources, but `check_boundary()` handles every path already in `prior_paths` by creating a fresh classification and never copies the corresponding `merged[path]` fields. A modified/deleted path present in the phase-start inventory therefore loses `change_sources`, `committed_change`, `live_changes`, modes, and change kind; if its bytes still match the snapshot, it is reported as `preexisting_unrelated` even when it was subsequently committed. This violates the v5 per-path source-preservation contract and prevents an independent reviewer from seeing how that path entered the result.

**Fix:** Merge evidence into the classification for both baseline-inventory and newly discovered paths, and base a `preexisting_unrelated` result on the absence of post-baseline contributors as well as matching bytes. Add a fixture where an inventory path has both a committed change and a worktree change, then assert one record contains all sources.

### WR-02: Required history edge cases have no regression coverage

**Classification:** WARNING

**File:** `experiments/specchoice-v1.3.2/tests/test_filesystem_boundary.py:33`

**Issue:** The only v5 committed-history test creates one added path. No submitted test exercises committed modified, deleted, or type-changed records, deduplication of a path present in history and live layers, malformed raw-diff rejection, or an invalid/non-descendant reviewed revision. The receipt test at `tests/test_receipts.py:22` checks the recorded artifact but does not test either schema-3 binding failure above. These are the exact fail-closed cases introduced by 01-05, so the suite cannot reliably prevent their regression.

**Fix:** Add isolated Git-fixture tests for A/M/D/T, history-plus-staged/worktree deduplication, malformed/truncated raw records, and invalid/non-descendant revisions; add schema-3 receipt tampering tests for reviewer basis and lineage/top-level baseline mismatch.

## Historical Advisory Debt (not reclassified in this scope)

The earlier report's CR-01, CR-02, WR-01, and WR-02 remain historical out-of-scope hardening debt: reviewer authorization is not independently authenticated, receipt writes are replaceable/not crash-atomic, and candidate construction bypasses the canonical decision loader. 01-05 did not materially worsen those items, so they are retained as advisory context and are not included in this report's severity counts.

---

_Reviewed: 2026-07-30T18:16:43Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
