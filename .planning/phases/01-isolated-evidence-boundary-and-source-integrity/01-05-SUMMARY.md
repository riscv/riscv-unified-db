---
phase: 01-isolated-evidence-boundary-and-source-integrity
plan: 05
subsystem: evidence-boundary
tags: [git-history, canonical-json, local-only]
requires: [01-04]
provides: [v5-history-aware-boundary, v5-integrity-receipt]
affects: [TS-01]
tech-stack: [python-stdlib, git-cli]
key-files:
  created:
    - experiments/specchoice-v1.3.2/receipts/boundary-restart-v5.json
    - experiments/specchoice-v1.3.2/config/boundary_allowlist-v5-gap-closure.json
    - experiments/specchoice-v1.3.2/baselines/phase-start-v5-gap-closure.json
    - experiments/specchoice-v1.3.2/receipts/integrity-receipt-v5.json
    - experiments/specchoice-v1.3.2/receipts/integrity-receipt-v5.md
  modified:
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/baseline.py
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/bundle.py
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/receipt.py
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/source_contract.py
    - experiments/specchoice-v1.3.2/tests/test_bundle_verifier.py
    - experiments/specchoice-v1.3.2/tests/test_filesystem_boundary.py
    - experiments/specchoice-v1.3.2/tests/test_receipts.py
decisions:
  - v3 and v4 remain preserved, non-accepted evidence; v5 is the active recovery lineage.
  - Accepted bundle remains local-only with external publication prohibited.
  - A local MVP receipt decision is valid only for one immutable reviewed Git revision and its canonical committed-change projection.
metrics:
  tasks: 3
status: human_gate_pending
---

# Phase 01 Plan 05: v5 history-aware boundary recovery Summary

Canonical v5 recovery evidence now detects committed post-baseline changes while preserving the unchanged local accepted source identity.

## Completed Work

- `54cda4f5` amended the recovery control: v3 is `BASELINE_NOT_CANONICAL`; v4 is `BASELINE_CAPTURED_AFTER_RED` and neither is accepted.
- `93024b81` captured canonical LF-terminated v5 restart, allowlist, and pre-implementation baseline bound to `54cda4f5f7e01b84defcc09a380d54f664c78d62`.
- `6dba9ed` supplied fresh RED; its clean-worktree committed violation failed with `0 != 1` before implementation.
- `80fe1ffb` added committed A/M/D/T collection, live-layer merge and one-path classification with `.DS_Store` visible/nonblocking handling.
- `2e397d43` issued schema-3 v5 integrity JSON/Markdown and its behavior-level regression.
- `2b878a2c` and `20226897` bound schema-3 receipt lineage and preserved committed/live provenance.
- `e5a97340` made issuance and finalization share the same local boundary gate and selected v5 as the active default.
- `35302680` froze receipt authority to an explicit reviewed revision, canonical committed projection, and receipt basis while retaining a separate current-state gate.
- `e780289b` added regression coverage for revision pinning, old-decision rejection, provenance, and current-state enforcement.
- `b1709931` prohibited active finalization of historical schema-2/schema-3 receipts; only a schema-4 receipt with a schema-3 revision-pinned decision can reach active pass.
- `7fb9d18f` replaced net-tree committed-history comparison with deterministic per-commit A/M/D/T events, preserving an out-of-boundary add even when a later commit deletes the path.

## Verification

- Full stdlib suite: 70 tests passed using `PYTHONDONTWRITEBYTECODE=1`.
- v5 restart validation and the current combined `check-boundary` gate pass with zero blockers; `.DS_Store` entries retain `DS_STORE_IGNORED_OS_METADATA` and are not attributed.
- Historical schema-2 and schema-3 receipts now fail active finalization with `HISTORICAL_RECEIPT_NOT_FINALIZABLE`; they cannot bypass the revision-pinned authorization route.
- The add-then-delete regression proves a clean final tree cannot erase a committed out-of-boundary history event from either the frozen projection or current gate.
- Copied accepted bundle verified with Git unavailable; before/after SHA-256 inventories were identical.
- Accepted identity is unchanged: generation `source-contract-v2-pr2192-86a0021b-verifier-rooted-v1`, core `6ca1f176c84464d499d6c0e81d03ba3f23fdcdd1b5bd43bc28d9b2153a797495`, root `aacdda8218e3779747ae2dec45f9da81822f615ec4b257e55b0766baf8317d5a`, snapshot `1c81f84cf4894a7ecfde4b72e17d6e479a91cb0cfa408258611b00bdf5e2e397`, publication false.

## Deviations from Plan

- [Rule 1 - Bug] Non-repository fixture compatibility was restored for legacy patched live-path tests.
- Recovery sequencing required the v5 receipt regression to be added after local implementation assembly but before the Task 2 commit; no RED claim is made for that test.
- Review exposed three authority gaps after the initial v5 implementation. Each finding and fix remains in immutable Git history; no failed receipt generation was overwritten.
- CR-01, CR-02, WR-01, and WR-02 remain out-of-scope hardening debt.

## Self-Check: PASSED

All v5 artifacts exist, are canonical, and the recorded task commits exist. A new local receipt can be issued only after independent review freezes one exact revision and the user authorizes its computed proposal-only basis. No external publication is authorized.
