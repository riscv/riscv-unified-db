---
phase: 01-isolated-evidence-boundary-and-source-integrity
reviewed: 2026-07-30T21:46:42Z
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
  critical: 1
  warning: 0
  info: 0
  total: 1
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-30T21:46:42Z
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

This iteration reviewed the same ten v5-boundary files after commits `2b878a2c`,
`20226897`, and `e5a97340`. The two prior implementation defects are fixed:
the active baseline/restart defaults are absolute v5 paths from either repository
or experiment cwd, v5 without restart fails closed, and both write/accept and
finalization enforce the decision's receipt-basis hash.

The existing decision basis
`32d6146ad1e6a75d8a83b29bdb82ed80289f3a16d4c1ddf1cdd838fbc71c399a`
does not match the existing v5 receipt basis
`f402e860e4dd31dd0af1d21bf3b16740d5357e6fc9adabada3cafdb3306ef8d8`.
`finalize-review` now correctly rejects that pair with
`LOCAL_RECEIPT_BASIS_MISMATCH`; this is not a bypass. The accepted source
identity, its immutable artifacts, and `external_publication_authorized:false`
remain unchanged.

However, a replacement authorized decision/receipt cannot be created through a
stable, formal frozen-basis workflow. This is a code blocker, not merely pending
human authorization.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: No constructible, revision-pinned v5 receipt-basis workflow

**File:** `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py:404-473`, `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_evidence/baseline.py:301-339`, `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_evidence/source_contract.py:296-345`

**Issue:** The fix correctly rejects a basis mismatch, but it provides no formal
CLI command that computes and freezes the receipt basis for an exact reviewed
commit before a new decision and receipt are added. `check-boundary` accepts
`--reviewed-revision` but only emits classifications, not the basis
(`cli.py:97-116`). More importantly, `check_boundary()` always merges
`capture_live_state(root)` even when a revision is supplied
(`baseline.py:308-312`), while the write and accept paths call it with the
implicit moving `HEAD` (`cli.py:412`, `459`) and expose no reviewed-revision
argument. The local-decision schema has no revision/projection binding
(`source_contract.py:299-345`).

Consequently, calculating a basis before creating a new decision/receipt is not
replayable: the new files are in the allowed experiment root and change the
classification list used by `local_receipt_basis_sha256()`
(`receipt.py:64-84`). Calculating after adding them instead computes a different
basis. There is also no CLI output that a reviewer can independently place into
a canonical decision without importing a private Python helper. The current
`LOCAL_RECEIPT_BASIS_MISMATCH` is therefore correctly fail-closed, but there is
no safe, supported route to issue the next authorized receipt.

**Fix:** Add a formal, non-mutating `compute-local-mvp-receipt-basis` command
that requires a full immutable `--reviewed-revision`, exact baseline,
environment decision, and approved generation; it must emit canonical basis
inputs and the resulting digest evaluated against that revision. Extend the
local-acceptance decision (new schema version, retaining schema-2 read
compatibility only for explicitly selected historical evidence) with the
resolved commit and basis/projection hash. Make `accept-local-mvp` and
`write-local-mvp-receipt` recompute exactly that pinned projection, and make
`finalize-review` verify the same binding. Preserve a separate fail-closed live
state check so uncommitted/staged changes cannot be silently excluded from the
gate. Add regression tests that (1) freeze at a named commit, (2) add the
decision and receipt afterwards, and (3) still reproduce the frozen basis while
rejecting a moving, unrelated, or dirty revision.

## Blocking Human Authorization (not a code finding)

After CR-01 is fixed, a reviewer must issue a new canonical decision carrying
the formal command's exact v5 revision and basis evidence, then create and
finalize the new receipt. The old decision and existing v5 receipt must not be
manually patched or treated as accepted. Until that receipt finalizes, Phase 01
is not ready for independent phase verification.

## Validation Performed

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_receipts -v` — 12 passed.
- `check-boundary --reviewed-revision HEAD` — v5 baseline, 0 blockers; only
  `.DS_Store` records are non-blocking OS metadata.
- `finalize-review` against the old decision and v5 receipt — rejected with
  `LOCAL_RECEIPT_BASIS_MISMATCH`, as required.

---

_Reviewed: 2026-07-30T21:46:42Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
