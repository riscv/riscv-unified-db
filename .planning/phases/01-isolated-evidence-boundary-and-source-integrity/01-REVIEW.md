---
phase: 01-isolated-evidence-boundary-and-source-integrity
reviewed: 2026-07-30T18:42:00Z
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
  warning: 0
  info: 0
  total: 2
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-30T18:42:00Z
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

The direct constructor checks added for the prior review are effective: schema-3 construction now rejects a wrong basis, schema-3 validation rejects a lineage/top-level baseline mismatch, and finalization rejects a modified lineage projection. The provenance fix also retains committed/staged/worktree evidence for baseline-inventory paths. The submitted tests meaningfully exercise A/M/D/T records, deduplication, malformed raw Git output, and missing/non-descendant revisions; the focused 26-test suite passed.

However, the authorized v5 command path bypasses the repaired constructor check by passing its freshly computed basis rather than the reviewer-approved basis. The committed v5 artifact proves the bypass: its receipt basis is `f402e860...`, while its hash-bound reviewer decision records `32d6146a...`; `finalize-review` still returns `pass`. Separately, v5 remains opt-in even though it is the active recovery lineage: CLI defaults resolve to v2 from the experiment directory (and v1 from the repository root), and a v5 receipt can be emitted without a restart receipt. Phase 01 is not ready for ASVS L1 or independent verification.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Canonical v5 write/finalize path still bypasses the reviewer-approved receipt basis

**Classification:** BLOCKER

**File:** `experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py:423-444`

**Issue:** `_write_local_mvp_receipt()` computes `basis` from current facts, then supplies that same value as `reviewed_receipt_basis_sha256` to `build_local_mvp_receipt()` at line 443. This makes the constructor comparison at `receipt.py:224-226` tautological and entirely skips `decision["reviewed_receipt_basis_sha256"]`. `command_write_local_mvp_receipt()` never calls the preflight that does compare the decision basis (`cli.py:386-404`). Finalization only checks the decision file hash and generation (`cli.py:519-527`), not the receipt basis against that decision. The shipped receipt's basis differs from the reviewed decision's basis yet finalizes successfully, so an altered boundary projection can be self-hashed and presented as a passing local receipt without the required reviewer basis.

**Fix:** Make the write path validate and pass the decision's frozen basis; independently enforce the same equality during finalization.

```python
_validate_local_mvp_receipt_basis(args, decision)
reviewed_basis = decision["reviewed_receipt_basis_sha256"]
assert isinstance(reviewed_basis, str)
receipt = build_local_mvp_receipt(
    ..., reviewed_receipt_basis_sha256=reviewed_basis,
    restart_lineage=restart_lineage,
)

# command_finalize_review, after local_decision validation
if receipt.get("receipt_basis_sha256") != local_decision["reviewed_receipt_basis_sha256"]:
    raise ReceiptError("LOCAL_RECEIPT_BASIS_MISMATCH")
```

Add an integration test through `write-local-mvp-receipt` and `finalize-review` that changes the recomputed boundary basis while retaining valid schema-3 lineage, then asserts both commands fail. Regenerate the receipt only under a reviewer decision bound to its new basis.

### CR-02: Active v5 recovery lineage is neither the CLI default nor required for local receipt issuance

**Classification:** BLOCKER

**File:** `experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py:47-50`

**Issue:** `_default_active_baseline()` selects only `phase-start-v2.json`; it never selects the declared active v5 baseline. Therefore `check-boundary` and `write-local-mvp-receipt` default to v2 when invoked from the experiment directory (`cli.py:547`, `cli.py:649`), and to the nonexistent v1 fallback when invoked from the repository root. In addition, `--restart-receipt` is optional (`cli.py:653`), so even an explicit v5 baseline can produce schema 2 without restart lineage. This permits the normal receipt command to omit the v5 committed-history recovery and its projection checks, defeating the intended active local-only boundary.

**Fix:** Resolve the active v5 baseline deterministically, and require a validated restart receipt whenever that baseline is used.

```python
def _default_active_baseline() -> Path:
    return Path("baselines/phase-start-v5-gap-closure.json")

# In _write_local_mvp_receipt after resolving baseline:
if baseline.name == "phase-start-v5-gap-closure.json" and args.restart_receipt is None:
    raise ReceiptError("RESTART_RECEIPT_REQUIRED")
```

Add CLI tests, with the experiment directory as the working directory, asserting that every boundary/receipt default is v5 and that a v5 write without `--restart-receipt` fails closed. Keep explicit schema-2 compatibility available only through an intentional historical path, not the active command default.

---

_Reviewed: 2026-07-30T18:42:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
