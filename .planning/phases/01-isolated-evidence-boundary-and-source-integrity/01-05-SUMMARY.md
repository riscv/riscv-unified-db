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
    - experiments/specchoice-v1.3.2/receipts/reviewer-boundary-decision-v6.json
    - experiments/specchoice-v1.3.2/receipts/integrity-receipt-v6.json
    - experiments/specchoice-v1.3.2/receipts/integrity-receipt-v6.md
    - experiments/specchoice-v1.3.2/receipts/reviewer-boundary-decision-v7.json
    - experiments/specchoice-v1.3.2/receipts/integrity-receipt-v7.json
    - experiments/specchoice-v1.3.2/receipts/integrity-receipt-v7.md
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
  - v6 remains preserved as an authorized but non-finalizable receipt attempt because its restart-lineage paths were not portable.
  - Accepted bundle remains local-only with external publication prohibited.
  - A local MVP receipt decision is valid only for one immutable reviewed Git revision and its canonical committed-change projection.
metrics:
  tasks: 3
status: verification_pending
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
- `2ae36b46` preserved the authorized v6 decision and schema-4 receipt unchanged after active finalization rejected absolute restart-lineage paths with `RESTART_LINEAGE_PROJECTION_MISMATCH`.
- `b86ad102` made writer and finalizer share one canonical experiment-relative lineage mapping and added path-mode plus finalization-roundtrip regressions.
- `b39bbc9b` added an exact post-review delta gate: after the decision's reviewed revision, only the named decision/receipt/Markdown, canonical future-control files, and `.DS_Store` may change.
- `206d68ea` preserved the authorized v7 decision and finalized schema-4 receipt/Markdown bound to reviewed revision `39d70ca978ffb6798f4070904d1c66643b3e7711`.

## Verification

- Full stdlib suite: 76 tests passed using `PYTHONDONTWRITEBYTECODE=1`.
- v5 restart validation and the current combined `check-boundary` gate pass with zero blockers; `.DS_Store` entries retain `DS_STORE_IGNORED_OS_METADATA` and are not attributed.
- Historical schema-2 and schema-3 receipts now fail active finalization with `HISTORICAL_RECEIPT_NOT_FINALIZABLE`; they cannot bypass the revision-pinned authorization route.
- The add-then-delete regression proves a clean final tree cannot erase a committed out-of-boundary history event from either the frozen projection or current gate.
- The canonical-path roundtrip exposed stale-decision replay before the post-review gate was added; the committed v6 attempt remains intentionally unchanged and non-finalizable.
- Reusing the stale v6 decision after the portability repair now fails before writing with `LOCAL_RECEIPT_POST_REVIEW_DELTA_BLOCKING`; no replacement files are created.
- v7 active finalization passes before and after its artifact commit with receipt self-hash `4b02a68d2cd9207e81a1b17ac7e06e81693088c4f43138eaac6d134e28144900`; canonical JSON file SHA-256 is `e9736da91b5728952cd4a03081f7c3855cd9e2b9c046f939696dc66243ce2d8a`.
- v7 binds projection `6ca959fdf8bb48fbcef5a7c3ca035e0374973e3461c95bb4e4157c7c0c0b88e9` and basis `bedd658c8b52ee41c7f780a5e6a455a9e47d1ff9409c27b1225e7d04d45935f3`; external publication remains false.
- Copied accepted bundle verified with Git unavailable; before/after SHA-256 inventories were identical.
- Accepted identity is unchanged: generation `source-contract-v2-pr2192-86a0021b-verifier-rooted-v1`, core `6ca1f176c84464d499d6c0e81d03ba3f23fdcdd1b5bd43bc28d9b2153a797495`, root `aacdda8218e3779747ae2dec45f9da81822f615ec4b257e55b0766baf8317d5a`, snapshot `1c81f84cf4894a7ecfde4b72e17d6e479a91cb0cfa408258611b00bdf5e2e397`, publication false.

## Deviations from Plan

- [Rule 1 - Bug] Non-repository fixture compatibility was restored for legacy patched live-path tests.
- Recovery sequencing required the v5 receipt regression to be added after local implementation assembly but before the Task 2 commit; no RED claim is made for that test.
- Review exposed three authority gaps after the initial v5 implementation. Each finding and fix remains in immutable Git history; no failed receipt generation was overwritten.
- The first authorized schema-4 attempt exposed a writer/finalizer path-basis mismatch. The failed v6 files were committed before the generator was repaired, so v7 requires a new reviewed revision, basis, and explicit authorization.
- Review then demonstrated that an old decision could otherwise be replayed through the repaired writer. The post-review delta gate closes that replay path without changing the existing schema-3 decision or schema-4 receipt semantics.
- CR-01, CR-02, WR-01, and WR-02 remain out-of-scope hardening debt.

## Self-Check: PASSED

All v5-v7 artifacts and recorded task commits exist. The authorized v7 receipt passes the active machine gate and offline bundle replay; only the downstream security and independent phase-verification gates remain. No external publication is authorized.
