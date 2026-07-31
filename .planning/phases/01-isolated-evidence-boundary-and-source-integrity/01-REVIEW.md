---
phase: 01-isolated-evidence-boundary-and-source-integrity
reviewed: 2026-07-31T08:25:46Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - experiments/specchoice-v1.3.2/receipts/reviewer-boundary-decision-v6.json
  - experiments/specchoice-v1.3.2/receipts/integrity-receipt-v6.json
  - experiments/specchoice-v1.3.2/receipts/integrity-receipt-v6.md
  - experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py
  - experiments/specchoice-v1.3.2/tests/test_receipts.py
  - .planning/phases/01-isolated-evidence-boundary-and-source-integrity/01-05-SUMMARY.md
findings:
  critical: 1
  warning: 0
  info: 0
  total: 1
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-31T08:25:46Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

The v6 evidence is preserved byte-for-byte and the path portability repair correctly canonicalizes all four restart-lineage paths from default, absolute, and relative inputs across experiment, repository, and external working directories. The original v6 receipt remains non-finalizable. However, the repair permits its pre-fix v6 decision to be reused to mint a new canonical schema-4 receipt that active finalization accepts. This bypasses the required new v7 exact-basis human authorization.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Pre-fix v6 authorization can be reissued and finalized after the repair

**File:** `experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py:620-635` (finalizer reuse at `685-699`; regression codified at `tests/test_receipts.py:339-366`)

**Issue:** `command_write_local_mvp_receipt` validates and rebuilds material using the decision's old `reviewed_revision`, then emits the repaired canonical lineage. `command_finalize_review` repeats that same historical-material calculation instead of requiring a post-`b86ad102` basis/authorization. Consequently, the v6 decision pinned to `a8fc3dee...` and basis `17b3e616...` can create a temporary canonical schema-4 receipt and `finalize-review` returns `{"outcome":"pass"}`. A fresh proposal at `a2eef6f0...` is different (`receipt_basis_sha256` `c0229000...`), so this permits authorization from before the portability repair to approve the repaired output. The new round-trip test explicitly accepts this bypass.

**Fix:** Bind schema-3 authorization and the receipt basis to a canonical issuance-context digest that includes the active restart-lineage mapping and the producer revision/context. Verify that digest in both write and finalize paths; reject v6 with a dedicated stale-context error, and require a newly generated v7 proposal and human schema-3 decision before issuing a receipt. Replace the existing v6-pass regression with a rejection regression; the success round trip must use a newly authorized v7 decision.

```python
current_context = _active_receipt_issuance_context_sha256()
if decision["issuance_context_sha256"] != current_context:
    raise ReceiptError("LOCAL_RECEIPT_ISSUANCE_CONTEXT_MISMATCH")
```

Include `issuance_context_sha256` in the canonical proposal/basis and schema-3 decision, so a post-authorization writer repair cannot reuse an earlier decision merely by regenerating a receipt.

## Verified Controls

- The committed v6 JSON, decision, and Markdown are unchanged since `2ae36b46`; the Markdown deterministically renders from the preserved JSON. Raw v6 active finalization still rejects with `RESTART_LINEAGE_PROJECTION_MISMATCH`.
- The writer's lineage helper uses exactly `config/boundary_allowlist-v5-gap-closure.json`, `baselines/phase-start-v5-gap-closure.json`, `receipts/boundary-restart-v5.json`, and `baselines/phase-start-v2.json` for default, absolute, and relative path inputs from all tested working directories. Finalizer uses the same mapping and rejects path drift.
- Existing historical-receipt rejection, per-commit A/M/D/T history capture, full revision validation, proposal-only behavior, and current staged/worktree/untracked boundary-gate tests continue to pass.
- The accepted bundle identity remains `source-contract-v2-pr2192-86a0021b-verifier-rooted-v1`; its core/root/snapshot hashes are unchanged, and external publication remains false.

## Validation

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -v` — 72 tests passed.
- Portable default/absolute/relative lineage probe — passed across experiment root, repository root, and `/private/tmp`.
- Raw v6 finalization — blocked as expected; reconstructed v6 receipt with the old decision — incorrectly finalized, reproducing CR-01.
- Fresh HEAD proposal — emitted a new full revision and basis (`c0229000...`), distinct from v6.
- v6 preservation/Markdown determinism and `git diff --check 2ae36b46^..a2eef6f0` — passed.

## Authorization Checkpoint

Do not enter the v7 exact-basis human-authorization checkpoint yet. First close CR-01 and demonstrate that the old v6 decision cannot issue or finalize a repaired receipt. Only then may a newly computed v7 basis be presented for human authorization; no v7 decision or receipt currently exists.

---

_Reviewed: 2026-07-31T08:25:46Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
