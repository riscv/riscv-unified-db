---
phase: 02-deterministic-measurement-spine
plan: 12
subsystem: source-custody
tags: [accepted-v3, receipt-custody, copied-offline-replay, pending-cutover]
requires:
  - phase: 02-11
    provides: hash-bound local acceptance and a non-effective v10 pending cutover
provides:
  - Immutable cross-bound acceptance, integrity, and copied-offline replay receipts for accepted v3
  - Descriptor-rooted no-replace receipt writes with replayed tamper, missing, and extra-file rejection
affects: [02-13, 02-16, source-authority]
tech-stack:
  added: []
  patterns: [descriptor-held canonical reads, O_EXCL-O_NOFOLLOW receipt writes, embedded-verifier copied replay]
key-files:
  created:
    - experiments/specchoice-v1.3.2/receipts/fixture-closure-acceptance-audit-v3.json
    - experiments/specchoice-v1.3.2/receipts/fixture-closure-acceptance-audit-v3.md
    - experiments/specchoice-v1.3.2/receipts/integrity-receipt-v10.json
    - experiments/specchoice-v1.3.2/receipts/integrity-receipt-v10.md
    - experiments/specchoice-v1.3.2/receipts/fixture-closure-offline-replay-v3.json
  modified:
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/receipt.py
    - experiments/specchoice-v1.3.2/tests/test_fixture_closure.py
key-decisions:
  - "Accepted-v3 receipt custody is a local-only attestation layer and does not migrate consumers or activate the pending cutover."
  - "The new writer reuses the accepted-bundle verifier and descriptor-held canonical inputs; it writes only new immutable receipt leaves."
metrics:
  duration: 10m
  completed: 2026-08-02
status: complete
---

# Phase 02 Plan 12: Accepted v3 receipt custody summary

**Accepted-v3 now has canonical acceptance, integrity, and copied-isolation replay receipts, all cross-bound to the same local-only non-effective pending transition.**

## Accomplishments

- Added the public `write-accepted-v3-receipts` path. It validates the reviewed request/decision lineage, active and historical v2 equivalence, pending-v10 transition, accepted-v3 identity, fixed 11/28/6-4-1 inventory, and all five embedded verifier artifacts before writing anything.
- Added descriptor-held canonical reads plus `O_EXCL | O_NOFOLLOW` leaf creation with file and parent-directory `fsync`; receipt destinations are never replaced.
- Added immutable `fixture-closure-acceptance-audit-v3`, `integrity-receipt-v10`, and copied-offline replay evidence. The Markdown files are pure JSON-derived projections.
- Proved copied verification runs without repository modules, original bundle paths, Git executable/objects, or network; tampered, missing, and extra artifacts each fail closed.

## Verification

- TDD RED: `test_v3_acceptance_receipts_and_copied_replay_bind_same_identity` failed because the public writer did not yet exist.
- TDD GREEN: `PYTHONPATH=src python3 -m unittest tests.test_fixture_closure.FixtureClosureCandidateTests.test_v3_acceptance_receipts_and_copied_replay_bind_same_identity -v` passed.
- `validate-pending-source-cutover-v10` passed with `status: pending_cutover_valid_non_effective` and `eligible: false`.
- `tests/phase1_expected_red_oracle.py --expected-focused 66 --expected-discovered 144 --expected-green 139` exited 0.
- Protected v2, historical/pending authority, pending transition, local acceptance artifacts, and candidate audit are unchanged from the 02-11 task baseline `fe7914ccec24c8de0f68ecaeadadfc83119fda38`.

## Receipt Hashes

| Artifact | SHA-256 |
| --- | --- |
| `fixture-closure-acceptance-audit-v3.json` | `9505552ba5770ce5f215b1058e959194e291f425f946cb1ace1f672f37f25aa3` |
| `fixture-closure-acceptance-audit-v3.md` | `6ab9674991a73c49141b0b54e92f49efc21eb4cc60c2d146d176bd43686d1ec0` |
| `integrity-receipt-v10.json` | `16a47946f2af6e191dfa7b5db8ac157d6771e3f90e199285e08ea1cef45adabc` |
| `integrity-receipt-v10.md` | `4ed7f214240c7f74461cf01d6711dab2e5240aab04e7af02fc4d7b17dd603dc2` |
| `fixture-closure-offline-replay-v3.json` | `87ea6e8e80937413e10f5e33666e41d138d6eb2e64289b6cf24620d4a3e6bdf4` |

## Task Commits

1. **Task 1 RED: Add failing accepted-v3 receipt test** — `e4f1e0a5` (`test`)
2. **Task 1 GREEN: Write accepted-v3 custody receipts** — `38103210` (`feat`)
3. **Task 2: Attest accepted-v3 receipt custody** — `dd23387b` (`feat`)

## Decisions Made

- Receipt schemas preserve the human acceptance fields verbatim while asserting `local_only: true` and `external_publication_authorized: false`; they infer neither publication authority nor a v3 activation.
- The copied replay receipt records a successful clean embedded-verifier run only after negative copies for tamper, missing, and extra artifacts fail.

## Deviations from Plan

None — plan executed as written.

## Known Stubs

None.

## Threat Flags

None. The new local CLI write path is constrained to no-replace descriptor-rooted receipt leaves and is covered by the Plan 02-12 tampering mitigations.

## Self-Check: PASSED

- All five required receipt artifacts exist and their recorded SHA-256 values match their canonical bytes.
- Task commits `e4f1e0a5`, `38103210`, and `dd23387b` exist.
- The active v2 authority, historical v2, pending authority, and pending transition remain unchanged and non-effective.
