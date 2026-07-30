---
phase: 01-isolated-evidence-boundary-and-source-integrity
reviewed: 2026-07-30T22:07:48Z
depth: standard
files_reviewed: 13
files_reviewed_list:
  - experiments/specchoice-v1.3.2/baselines/phase-start-v5-gap-closure.json
  - experiments/specchoice-v1.3.2/receipts/boundary-restart-v5.json
  - experiments/specchoice-v1.3.2/config/boundary_allowlist-v5-gap-closure.json
  - experiments/specchoice-v1.3.2/receipts/integrity-receipt-v5.json
  - experiments/specchoice-v1.3.2/receipts/integrity-receipt-v5.md
  - experiments/specchoice-v1.3.2/src/specchoice_evidence/baseline.py
  - experiments/specchoice-v1.3.2/src/specchoice_evidence/bundle.py
  - experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py
  - experiments/specchoice-v1.3.2/src/specchoice_evidence/receipt.py
  - experiments/specchoice-v1.3.2/src/specchoice_evidence/source_contract.py
  - experiments/specchoice-v1.3.2/tests/test_bundle_verifier.py
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

**Reviewed:** 2026-07-30T22:07:48Z
**Depth:** standard
**Files Reviewed:** 13
**Status:** issues_found

## Summary

Fourth independent review of `35302680`, `e780289b`, and `55a7963e` found
that the new proposal-only basis command correctly separates a full,
revision-pinned committed projection from the moving current-state gate. It is
read-only, cannot self-approve a decision, and the existing v5 decision/receipt
basis mismatch correctly fails closed with `LOCAL_RECEIPT_BASIS_MISMATCH`.

The immutable v5 baseline/restart/allowlist and v5 receipt/Markdown remain
canonical. The accepted identity remains
`source-contract-v2-pr2192-86a0021b-verifier-rooted-v1` with the recorded
core/root/snapshot hashes, and external publication is still false.

Two critical bypasses remain: finalization still accepts the legacy schema-2
pair as a current pass, and the current combined boundary gate misses an
out-of-boundary file that was committed and then deleted before finalization.
The exact-basis human authorization checkpoint must not open yet.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: `finalize-review` still promotes the historical schema-2 receipt as a current pass

**File:** `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py:608-689`, `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_evidence/source_contract.py:296-365`

**Issue:** The new active issuance path rejects schema-2 authority in
`_validate_local_mvp_receipt_basis()` (`cli.py:513-518`), but
`command_finalize_review()` accepts receipt schemas 2/3/4 and explicitly loads
the decision with `allow_historical=True` (`cli.py:611-643`, `649-663`). It
does not require a schema-4 receipt and schema-3 revision-pinned decision.

On the current checkout, this command succeeds and emits a machine-eligible
pass for the old authority:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m specchoice_evidence.cli \
  finalize-review --decision receipts/reviewer-boundary-decision.json \
  --receipt receipts/integrity-receipt.json --markdown receipts/integrity-receipt.md
# {"outcome":"pass",...}
```

That pair is schema-2 and carries the old basis `32d6146a...`; it bypasses the
new exact-basis human checkpoint even though the schema-3 v5 receipt correctly
fails it. An explicit receipt pathname is not a sufficient historical-only
guard because the command's success result is indistinguishable from active
phase finalization.

**Fix:** Make `finalize-review` for the active v5 route require receipt schema
4 and decision schema 3, including the revision and committed-projection
bindings. Move schemas 2/3 to a separate read-only historical-verification
command (or an explicit historical mode that can never emit `outcome: pass` or
advance phase state). Add a regression that the exact command above fails with
a stable `HISTORICAL_RECEIPT_NOT_FINALIZABLE` diagnostic.

### CR-02: A committed-and-reverted out-of-boundary change is invisible to both frozen and current gates

**File:** `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_evidence/baseline.py:205-238`, `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_evidence/baseline.py:262-304`, `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_evidence/baseline.py:437-445`

**Issue:** `capture_committed_history()` is implemented as one net
`git diff --raw start reviewed` (`baseline.py:210-214`), rather than traversing
the commits in the range. If a forbidden file is added in one post-baseline
commit and deleted in a later clean commit, the range's final tree has no path
delta. The function returns no record, so both
`committed_boundary_projection()` and `check_current_boundary()` report zero
blockers. This contradicts the requirement that any later clean committed
out-of-boundary path remains blocking.

Reproduction in a disposable repository: baseline -> commit `outside.txt` ->
commit deletion of `outside.txt`; `git diff --raw --no-renames
--diff-filter=AMDT <baseline> HEAD` is empty even though both forbidden commits
remain in history.

**Fix:** Build committed history by walking every commit in
`start..reviewed` (including the relevant merge-parent handling) and aggregate
raw A/M/D/T records per path. Preserve at least one history event for an
added-then-deleted path and classify an out-of-boundary path as blocking even
when its final tree entry is absent. Add a test that commits, removes, and then
successfully reaches a clean worktree; assert both the frozen projection at a
post-delete revision and `check_current_boundary()` remain blocking.

## Verified Non-Findings

- `compute-local-mvp-receipt-basis` has no write path and emits
  `proposal_only:true`; it cannot grant approval itself.
- The frozen projection remains unchanged after later allowed decision/receipt
  commits, while a persistent clean committed violation is detected by the
  separate current gate.
- The old decision with the existing v5 receipt rejects with
  `LOCAL_RECEIPT_BASIS_MISMATCH`; that behavior is the correct human gate, not
  a defect.
- Accepted-bundle identity and `external_publication_authorized:false` did not
  drift.

## Validation Performed

- Full stdlib suite: 68 tests passed.
- `compute-local-mvp-receipt-basis` at the full current commit produced a
  canonical `proposal_only` result from the experiment cwd.
- v5 JSON and deterministic Markdown projection validated.
- Historical schema-2 finalization was executed and reproduced the CR-01
  bypass; the old-decision/v5-receipt finalization correctly returned
  `LOCAL_RECEIPT_BASIS_MISMATCH`.
- A disposable Git history reproduction confirmed the CR-02 net-diff blind
  spot.

---

_Reviewed: 2026-07-30T22:07:48Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
