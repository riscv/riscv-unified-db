---
phase: 01-isolated-evidence-boundary-and-source-integrity
plan: 06
subsystem: source-custody
tags: [fixture-closure, offline-verification, immutable-candidate]
requires: [01-05]
provides: [pr2164-11-fixture-candidate]
affects: [phase-02-input-authority]
tech-stack: [python-standard-library, git-cli-construction-only]
key-files:
  created:
    - experiments/specchoice-v1.3.2/config/fixture-registry-pr2164-v1.json
    - experiments/specchoice-v1.3.2/bundles/candidates/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v1/snapshot-manifest.json
  modified:
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/source_contract.py
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/bundle.py
decisions:
  - Exact PR #2164 fixture authority is a finite named 11-directory/28-blob registry.
  - The completed v3 generation remains candidate-only and locally ineligible.
metrics:
  tasks_completed: 2
status: complete
---

# Phase 1 Plan 06: Fixture Source Closure Summary

The complete frozen PR #2164 fixture set is now locally materialized as an immutable, offline-verifiable candidate without granting downstream eligibility or external-publication authority.

## Completed Tasks

1. Defined a canonical registry for the exact 11 fixture directories and 28 raw blobs; it validates bidirectionally against the pinned local Git commit/tree.
2. Constructed `source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v1`, including raw bytes, manifests, the registry, and an embedded stdlib verifier.

## Verification

- `python3 -m unittest tests.test_bundle_verifier tests.test_fixture_closure -v` — 12 passed.
- `python3 -m specchoice_evidence.cli verify-candidate ...` — candidate verified.
- Embedded `python3 verify_bundle.py` — bundle verified without Git or network.
- Historical v2 accepted-path snapshot manifest remains SHA-256 `be220c0a858ac6d018dd48015a39e5ea1b68f75af21ad91ca13335eab3e6bebd`; its root remains `aacdda8218e3779747ae2dec45f9da81822f615ec4b257e55b0766baf8317d5a`.

## Candidate Identity

- Generation: `source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v1`
- Root SHA-256: `76706a429cfb5f87472cb7d184ba1feae34e38ca6b311d8abef25a95fc4046fa`
- Manifest SHA-256: `4a9e3822f5c42ca178d145c8b20971dd649adb02e46ecf2fbdc4c532c530a42c`
- Status: `candidate`; `downstream_eligible: false`; `external_publication_authorized: false`.

## Deviations from Plan

### Auto-fixed Issues

1. [Rule 1 - Bug] The embedded Python verifier can cause interpreter bytecode caches during replay. Tree closure now excludes only `__pycache__`/`.pyc` runtime cache files while continuing to reject every other unmanifested file. This keeps copied-bundle replay deterministic and preserves fail-closed raw/verifier custody.

## Self-Check: PASSED

The registry, candidate manifests, embedded verifier, receipts, and both task commits exist. No `.DS_Store` file was staged or modified.
