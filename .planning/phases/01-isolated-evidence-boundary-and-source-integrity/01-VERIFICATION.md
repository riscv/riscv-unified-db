---
phase: 01-isolated-evidence-boundary-and-source-integrity
verified: 2026-07-31T08:53:22Z
status: passed
score: 9/9 must-haves verified
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 8/9
  gaps_closed:
    - "Only experiments/specchoice-v1.3.2/ and the exact control-file allowlist are attributable Phase 1 changes; every other out-of-boundary delta fails closed."
  gaps_remaining: []
  regressions: []
---

# Phase 1: Isolated Evidence Boundary and Source Integrity Verification Report

**Phase Goal:** The operator and reviewer can work from a self-contained experiment boundary whose public source identity is independently verifiable.

**Verified:** 2026-07-31T08:53:22Z

**Status:** passed

**Re-verification:** Yes — after committed-history gap closure and authorized v7 local receipt.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Operator can create, test, and inspect all prototype artifacts under `experiments/specchoice-v1.3.2/` without changing core UDB schemas, generated architecture data, or root dependency state. | ✓ VERIFIED | `git diff --name-only 93024b81^..HEAD` found no changes under `spec/`, `cfgs/`, `gen/`, `backends/`, `tools/`, or root dependency manifests. The runnable prototype and all tests remain under the isolated experiment root. |
| 2 | Reviewer can verify every named PR snapshot against its frozen commit and reproduce the stable hash of every consumed source file. | ✓ VERIFIED | The 76-test suite passed source-contract and bundle-verifier cases, including exact Git blobs, six frozen snapshots, seven consumed files, non-cyclic core/root/snapshot binding, and tamper rejection. The accepted bundle replay independently verified its rooted raw content. |
| 3 | Operator can reproduce the recorded environment decision and use the dependency-light fallback policy without weakening source verification. | ✓ VERIFIED | `environment.py` constructs the stable `standalone_first` projection (`full_udb_setup.required:false`, `attempted:false`) and its cumulative 90-minute incident policy. The full suite passed all nine environment transition/one-way audit tests. |
| 4 | Only the experiment root and exact control-file allowlist are attributable; every other non-`.DS_Store` committed or live delta fails closed. | ✓ VERIFIED | Active v5 `check-boundary --reviewed-revision 39d70ca978ffb6798f4070904d1c66643b3e7711` returned `blocking_violations:0`, with `history_start_commit:54cda4f5…`, 31 classified paths, and all post-baseline committed events retained. `baseline.py` walks `start..reviewed` with NUL-safe per-commit A/M/D/T events, then merges staged/worktree/untracked state. Full-suite add→delete, committed violation, and current-vs-frozen-projection tests passed. |
| 5 | Authoritative paths reject escapes, links, special files, mount uncertainty, hardlink-dependent layouts, prefix collisions, and malformed length/digest values. | ✓ VERIFIED | `filesystem.py` is wired through baseline capture/classification; `test_filesystem_boundary` and `test_canonical` passed path-escape, symlink, FIFO, mount, hardlink, exact-allowlist, overwrite, integer-length, and lowercase-SHA-256 cases. |
| 6 | The accepted generation replays from bundle-relative Python stdlib code with no local Git object or network dependency. | ✓ VERIFIED | The full suite passed its copied-bundle Git/socket-blocked test. Independently, I copied `bundles/accepted/source-contract-v2-pr2192-86a0021b-verifier-rooted-v1` to `/private/tmp`, confirmed zero `.git` directories, set `PATH=/nonexistent`, invoked `/opt/homebrew/bin/python3` (Python 3.14.5) directly, and received `bundle verified` / exit 0. |
| 7 | Canonical JSON receipt is authoritative, Markdown is its deterministic JSON-only projection, and rejected #2192 evidence cannot pass. | ✓ VERIFIED | `receipt.py` validates canonical receipt bytes and self-hash before `render_markdown`; the full suite passed Markdown-failure and rejected-source tests. The frozen #2192 test asserts `PR_PIN_NOT_REACHABLE` has no accepted identity. |
| 8 | Local acceptance binds exactly one verifier-rooted accepted generation, uses reviewed revision `39d70ca978ffb6798f4070904d1c66643b3e7711`, and forbids external publication. | ✓ VERIFIED | `reviewer-boundary-decision-v7.json` and `integrity-receipt-v7.json` bind projection `6ca959fdf8bb48fbcef5a7c3ca035e0374973e3461c95bb4e4157c7c0c0b88e9`, basis `bedd658c8b52ee41c7f780a5e6a455a9e47d1ff9409c27b1225e7d04d45935f3`, and receipt self-hash `4b02a68d2cd9207e81a1b17ac7e06e81693088c4f43138eaac6d134e28144900`. `finalize-review` returned pass; its code requires the exact decision hash, identity, revision-bound projection, basis, Markdown projection, clean current boundary, and `external_publication_authorized:false`. |
| 9 | A stale v6 authority cannot authorize the current receipt after post-review changes, while the accepted generation identity remains unchanged. | ✓ VERIFIED | Finalizing v6 explicitly returned `RESTART_LINEAGE_PROJECTION_MISMATCH` / exit 2. The 76-test suite passed `test_v6_decision_cannot_rebuild_a_receipt_after_post_review_code_changes`, historical-receipt finalization rejection, and post-review delta tests. v7 retains generation `source-contract-v2-pr2192-86a0021b-verifier-rooted-v1`, core `6ca1f176c84464d499d6c0e81d03ba3f23fdcdd1b5bd43bc28d9b2153a797495`, root `aacdda8218e3779747ae2dec45f9da81822f615ec4b257e55b0766baf8317d5a`, and snapshot manifest `1c81f84cf4894a7ecfde4b72e17d6e479a91cb0cfa408258611b00bdf5e2e397`. |

**Score:** 9/9 truths verified (0 present-but-behavior-unverified).

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `baselines/phase-start-v5-gap-closure.json` and `receipts/boundary-restart-v5.json` | Immutable D-15 restart generation and historic v2 incident record | ✓ VERIFIED | Canonical v5 baseline SHA is `a0b9f9f…`; restart lineage is bound to the v2 baseline, v5 allowlist, incident receipt, reason `D15_RESTART_COMMITTED_HISTORY_BLIND_SPOT`, and reviewed revision. Historical v2/v6 evidence remains present rather than rewritten. |
| `config/boundary_allowlist-v5-gap-closure.json` and `baseline.py` | Exact boundary enforcement, including history | ✓ VERIFIED | One root (`experiments/specchoice-v1.3.2/`) plus nine exact control files, including `01-REVIEW.md`, `01-SECURITY.md`, and this report. The code uses full immutable commits, per-commit A/M/D/T capture, and live-state merge; no net-diff shortcut exists. |
| `canonical.py` and `filesystem.py` | Canonical bytes and fail-closed authoritative path policy | ✓ VERIFIED | Both have substantive validators and are called by baseline, bundle, receipt, and verifier paths; 76 focused stdlib tests pass. |
| `environment.py`, canonical environment decision, and audit receipt | Standalone-first stable identity and one-way audit record | ✓ VERIFIED | Canonical decision contains only stable fields; audit receipt has one-way `canonical_environment_decision_sha256` reference. |
| `git_proof.py`, `bundle.py`, source contract, rejected receipt, and accepted manifests | Frozen source proof, raw-byte custody, immutable accepted generation | ✓ VERIFIED | Construction proof and accepted bundle verification are substantive and exercised by the suite, including raw/derived/tamper/concurrency cases. |
| Accepted bundle `verify_bundle.py` and embedded verifier | Bundle-local offline verification entry point | ✓ VERIFIED | Copied-bundle replay passed without repository metadata or a usable command path. |
| `integrity-receipt-v7.json`, `integrity-receipt-v7.md`, and v7 decision | Revision-bound local-only completion gate | ✓ VERIFIED | JSON self-hash recomputed exactly; Markdown equals `render_markdown(receipt)`; v7 finalization succeeds only under the authorized local-only decision. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- |
| v5 baseline | Boundary check and frozen receipt basis | `phase_start_baseline_sha256`, baseline commit through exact reviewed revision | ✓ WIRED | `check_boundary()` resolves immutable full commits, calls `capture_committed_history()` and `capture_live_state()`, and keeps every event in `committed_changes`; active review projection is clean. |
| Boundary restart artifacts | v5 lineage and v7 receipt | path/SHA-256 bindings and canonical active-lineage projection | ✓ WIRED | Finalizer calls `validate_boundary_restart()` and rejects a lineage/path/projection mismatch before accepting the receipt. |
| Source decision/request inventory | Git proof → candidate/accepted bundle | exact PR ref, commit/tree/ancestry, raw Git bytes, canonical manifest/root binding | ✓ WIRED | Source, bundle, and verifier tests pass; copied accepted generation recomputes independently. |
| Accepted bundle entry point | embedded verifier and local bundle bytes | bundle-relative `verify_bundle.py` | ✓ WIRED | Direct copied replay succeeded with no `.git` and empty `PATH`. |
| v7 decision | v7 receipt and Markdown | decision hash, revision/projection/basis, `render_markdown(validate_receipt(...))` | ✓ WIRED | v7 finalization returned the expected receipt self-hash; stale v6 failed before finalization. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `baseline.py` | `committed_changes` plus `live_changes` | immutable Git `start..reviewed` walk plus index/worktree/untracked capture | Per-commit records, including add/delete/revert history, classified under the exact allowlist | ✓ FLOWING |
| accepted bundle verifier | core/root/snapshot bindings and raw hashes | bundle-local raw content, manifests, and embedded verifier modules | Independent recomputation succeeds after copying out of the repository | ✓ FLOWING |
| v7 receipt/Markdown | canonical receipt fields | canonical decision, frozen boundary projection, environment digest, accepted identity | Self-hash and deterministic Markdown projection recompute exactly | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Full Phase 1 stdlib contract | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -v` | 76 tests passed in 11.834s. | ✓ PASS |
| Frozen history-aware boundary | `check-boundary --baseline baselines/phase-start-v5-gap-closure.json --reviewed-revision 39d70ca…` | `blocking_violations:0`; full post-baseline committed record retained; `.DS_Store` records are visible/non-attributed/nonblocking. | ✓ PASS |
| Authorized v7 local receipt | `finalize-review --decision reviewer-boundary-decision-v7.json --receipt integrity-receipt-v7.json --markdown integrity-receipt-v7.md` | `{"outcome":"pass","receipt_sha256":"4b02a68d…"}`. | ✓ PASS |
| Stale v6 authority rejection | same finalizer with v6 decision/receipt/Markdown | `RESTART_LINEAGE_PROJECTION_MISMATCH`, exit 2. | ✓ PASS (negative check) |
| Offline accepted-bundle replay | copy bundle; `PATH=/nonexistent /opt/homebrew/bin/python3 verify_bundle.py` | No copied `.git`; `bundle verified`, exit 0. | ✓ PASS |

### Probe Execution

Step 7c: SKIPPED — Phase 1 declares no `probe-*.sh` contract. The full stdlib suite, active boundary gate, finalization gate, and copied-bundle replay are its executable verification contract.

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| TS-01 | 01-01, 01-02, 01-04, 01-05 | Dependency-light isolated experiment with no core schema/generated-data modification. | ✓ SATISFIED | No core/root dependency changes; exact v5 restart allowlist; history plus live boundary gate; path-policy tests; standalone-first environment evidence; local-only receipt. |
| TS-02 | 01-03, 01-04 | Frozen public snapshot pinning and stable hashes for every consumed file. | ✓ SATISFIED | Git proof, rejected #2192 path, versioned correction/accepted generation, raw byte hashes, non-cyclic manifests, and offline bundle replay all pass. |

No Phase 1 requirement is orphaned: plans declare both TS-01 and TS-02, which are the only IDs ROADMAP and REQUIREMENTS assign to this phase.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| Phase 1 implementation, tests, and current v5/v7 custody artifacts | — | No unreferenced `TBD`, `FIXME`, or `XXX`; no user-visible placeholder or empty implementation found. | ℹ️ Info | No blocker. The prior committed-history blind spot is specifically covered by code and behavioral tests. |

## Local-Only Boundary

This is a local acceptance of one immutable generation, not publication approval. Both v7 decision and receipt require `external_publication_authorized:false`; no push, PR, upload, or other external publication is authorized by this result.

## Gaps Summary

None. The prior blocker is closed by a new immutable v5 restart lineage, an exact restart-only allowlist, full per-commit history plus live-state boundary classification, and revision-pinned v7 authority. The active boundary, authorized finalization, stale-v6 rejection, and offline bundle replay all passed independently.

---

_Verified: 2026-07-31T08:53:22Z_

_Verifier: the agent (gsd-verifier)_
