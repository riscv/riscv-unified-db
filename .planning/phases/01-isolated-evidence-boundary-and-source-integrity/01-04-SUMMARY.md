---
phase: 01-isolated-evidence-boundary-and-source-integrity
plan: 04
subsystem: local-evidence-custody
tags: [python-stdlib, offline-verifier, local-only, sha256, canonical-json]
requires:
  - phase: 01-03
    provides: verifier-rooted seven-blob candidate with exact core and root identities
provides:
  - immutable local-only accepted copy of the verifier-rooted generation
  - canonical local-MVP integrity receipt and JSON-derived Markdown review view
  - explicit separation between local acceptance and external publication authority
affects: [phase-02, source-custody, offline-replay]
tech-stack:
  added: []
  patterns: [same-filesystem staging rename, exact identity binding, JSON-only Markdown, no-network replay]
key-files:
  created:
    - experiments/specchoice-v1.3.2/bundles/accepted/source-contract-v2-pr2192-86a0021b-verifier-rooted-v1/
    - experiments/specchoice-v1.3.2/receipts/reviewer-boundary-decision.json
  modified:
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/bundle.py
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/receipt.py
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py
    - experiments/specchoice-v1.3.2/receipts/integrity-receipt.json
    - experiments/specchoice-v1.3.2/receipts/integrity-receipt.md
decisions:
  - "The exact verifier-rooted bundle is accepted only for local MVP use; external publication/distribution remains explicitly unauthorized."
  - "Local acceptance binds the generation, core SHA-256, logical root, and snapshot-manifest self-digest without changing any bundle byte."
  - "The reviewer decision binds a cycle-free receipt basis; the canonical receipt then binds the decision digest."
metrics:
  duration: 32min
  completed: 2026-07-30
  tasks_completed: 3
  files_changed: 24
status: complete
---

# Phase 01 Plan 04: Local-Only MVP Acceptance Summary

**The exact verifier-rooted generation is now immutable and usable for local/offline MVP work, while all external publication remains prohibited.**

## Local Accepted Identity

- Generation: `source-contract-v2-pr2192-86a0021b-verifier-rooted-v1`
- Core SHA-256: `6ca1f176c84464d499d6c0e81d03ba3f23fdcdd1b5bd43bc28d9b2153a797495`
- Logical root SHA-256: `aacdda8218e3779747ae2dec45f9da81822f615ec4b257e55b0766baf8317d5a`
- Snapshot-manifest self-digest: `1c81f84cf4894a7ecfde4b72e17d6e479a91cb0cfa408258611b00bdf5e2e397`
- Integrity receipt SHA-256: `6162288ca08ada06797453b8d95824e4e138c331092d61e078d9bed9fd4209af`
- Reviewer decision SHA-256: `ef2d5252ec8ddc48272bf699674f08f9c10754bfc31caf65efe52fd76d50e737`
- Local authority: `local_accepted_generation_authorized: true`
- External authority: `external_publication_authorized: false`

## Accomplishments

- Copied the exact verifier-rooted candidate to `bundles/accepted/` with same-filesystem staging and atomic rename. The local copy retains the candidate manifests and all rooted bytes unchanged; it does not claim an external publication state.
- Added fail-closed local-acceptance validation that binds only the reviewed generation/core/root/snapshot identity and rejects overwrite or any external-publication request.
- Issued a schema-v2 canonical `outcome: pass` local-MVP integrity receipt. Its Markdown is generated only from validated JSON, and it explicitly says external publication is false.
- Proved copied-directory replay with no repository `.git`, a failing Git shim, blocked sockets, and the full raw/core/snapshot/verifier tamper matrix.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -v` — 51 tests passed.
- Focused accepted/local/boundary suite — 26 tests passed.
- `check-boundary --baseline baselines/phase-start-v2.json` — 0 blocking violations; all `.DS_Store` records remain visible and non-attributed.
- `finalize-review --decision receipts/reviewer-boundary-decision.json ...` — canonical local receipt and Markdown projection passed.
- `diff -qr` between candidate and local accepted generation — byte-identical contents.
- No network, push, PR, upload, deployment, or other external publication operation was run.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Receipt ordering] Preflight the receipt basis before a new local acceptance rename.**
- **Found during:** Task 3 local finalization.
- **Issue:** A first local copy was correctly created before the receipt basis was checked; the new allowed paths changed the complete boundary classification basis.
- **Fix:** Kept the already byte-verified immutable copy untouched, changed future `accept-local-mvp` flow to validate the basis before rename, and added a receipt-only command that validates an existing exact copy without mutating it.
- **Files modified:** `src/specchoice_evidence/cli.py`, `src/specchoice_evidence/bundle.py`.
- **Commit:** `c0a1e9c9`.

### Contract Clarification

The original checkpoint describes a reviewer decision and final receipt as mutually cited. Directly hashing both references would be cyclic. The local-MVP schema therefore has the reviewer bind a deterministic receipt-basis projection, while the final canonical receipt binds the reviewer-decision digest. This preserves both references without a fixed-point hash.

## Known Stubs

None.

## External Publication Boundary

This plan authorizes local development and testing only. It does not authorize Git push, PR creation, artifact upload, release, deployment, registry publication, or distribution outside this checkout.

## Self-Check: PASSED

- The local accepted generation, canonical receipt, Markdown projection, and reviewer decision exist and validate.
- Task commits `c2ab2147`, `6ac773cb`, `3b17d43a`, `7d9e36a4`, `c6150959`, `ae1f0e95`, `f7e290d1`, `01337d1d`, and `c0a1e9c9` exist.
- No tracked file deletion occurred in the Task 3 commit; `.DS_Store` files remain untracked and untouched.
