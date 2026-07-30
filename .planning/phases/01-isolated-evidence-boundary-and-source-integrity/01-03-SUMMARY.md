---
phase: 01-isolated-evidence-boundary-and-source-integrity
plan: 03
subsystem: source-custody
tags: [python-stdlib, git-object-proof, sha256, canonical-json, offline-candidate]
requires:
  - phase: 01-02
    provides: standalone environment identity and passing boundary policy
provides:
  - exact Git-blob custody proof for seven approved files across six snapshots
  - deterministic non-accepted candidate manifests and logical root
  - closed accepted-publication CLI boundary pending Plan 04 offline replay proof
affects: [01-04, source-custody, offline-replay, measurement-fixtures]
tech-stack:
  added: []
  patterns: [Git blob extraction before byte custody, core-to-root-to-final-binding without a hash cycle, candidate-only atomic staging]
key-files:
  created:
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/bundle.py
    - experiments/specchoice-v1.3.2/tests/test_bundle_verifier.py
    - experiments/specchoice-v1.3.2/bundles/candidates/source-contract-v2-pr2192-86a0021b/snapshot-manifest.json
  modified:
    - experiments/specchoice-v1.3.2/receipts/source-publication-decision.json
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/source_contract.py
key-decisions:
  - "The reviewer authorization is limited to the exact proposal SHA ee04a35d... and candidate construction; it permits Git extraction but not accepted publication."
  - "Candidate identity is core manifest SHA-256 b280d5... plus logical root d19165..., with the final snapshot binding self-digested outside the root preimage."
  - "Plan 04 offline replay proof remains a hard prerequisite: publish-accepted rejects and bundles/accepted/ is absent."
patterns-established:
  - "Raw custody: read only pin:path Git blobs, check blob type, byte length, and SHA-256 before and after staging."
  - "Final binding: keep computed generation/root fields out of content-manifest-core, then self-digest snapshot-manifest after core/root recomputation."
requirements-completed: [TS-02]
coverage:
  - id: D1
    description: Exact approved Git blobs are materialized into a deterministic non-accepted candidate with raw byte custody.
    requirement: TS-02
    verification:
      - kind: integration
        ref: PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m specchoice_evidence.cli verify-source-contract-proposal-git --git-repository /private/tmp/specchoice-candidate-proof-JqDaZz/proof.git
        status: pass
      - kind: unit
        ref: tests/test_bundle_verifier.py#CandidateBundleTests
        status: pass
    human_judgment: false
  - id: D2
    description: Candidate core, root, and snapshot binding reject tampering and accepted publication remains impossible.
    requirement: TS-02
    verification:
      - kind: unit
        ref: PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -v
        status: pass
      - kind: other
        ref: specchoice-evidence publish-accepted --decision receipts/source-publication-decision.json
        status: pass
    human_judgment: false
duration: 49min
completed: 2026-07-30
status: complete
---

# Phase 01 Plan 03: Source Candidate Construction Summary

**Seven reviewer-approved Git blobs now form a byte-verified, content-addressed candidate whose canonical core SHA-256 is `b280d5dadafbb9cc27c49484e12c15020357cc3e4f3e92ec4bb37757ce7b5f45` and logical root is `d191657162be538c78d374c4ef8a1d6dd154fe61de7b30ab7e2a69d246002d9b`, while accepted publication remains closed.**

## Performance

- **Duration:** 49 min
- **Started:** 2026-07-30T14:15:00Z
- **Completed:** 2026-07-30T15:04:15Z
- **Tasks:** 3/3
- **Files modified:** 16

## Accomplishments

- Preserved the frozen #2192 rejection, then recorded the reviewer’s narrow `candidate_construction_only` authorization bound to proposal SHA-256 `ee04a35d92c2c6442852f921d8507d608f538191a78d2a829ccb51449719723e`.
- Fetched exact canonical PR refs and pins into a disposable bare Git repository, re-proved each snapshot’s commit/tree/reachability and copied only the seven approved `pin:path` blobs.
- Created `bundles/candidates/source-contract-v2-pr2192-86a0021b/` with raw content, core manifest, deterministic root, and final self-digested snapshot binding; all seven staged raw SHA-256 values match the approved inventory.
- Added fail-closed inventory, raw-custody, collision, special-file, interruption, existing-target, and binding-tamper coverage. `publish-accepted` returns `ACCEPTED_PUBLICATION_NOT_AUTHORIZED`; no `bundles/accepted/` directory exists.

## Task Commits

1. **Task 1: Prove each PR identity with local Git objects and preserve the #2192 rejection** — `48445f3e`, `1a39ad2c` (test, feat)
2. **Task 2: Resolve the source inventory and #2192 contract before accepted publication** — `90b3b8b4`, `f870782a` (feat, feat)
3. **Task 3: Build raw/derived manifests and prepare a publishable candidate without exposing accepted state** — `0a2c9ae2` (feat)

## Files Created/Modified

- `experiments/specchoice-v1.3.2/src/specchoice_evidence/bundle.py` — candidate-only atomic staging, raw Git blob custody, core/root construction, and offline candidate verification.
- `experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py` — candidate build/verify commands and a deliberately closed accepted-publication command.
- `experiments/specchoice-v1.3.2/src/specchoice_evidence/git_proof.py` — blob-type-checked `pin:path` reader.
- `experiments/specchoice-v1.3.2/src/specchoice_evidence/source_contract.py` — exact proposal-bound candidate authorization validation.
- `experiments/specchoice-v1.3.2/receipts/source-publication-decision.json` — canonical narrow construction authorization with `accepted_publication_authorized:false`.
- `experiments/specchoice-v1.3.2/bundles/candidates/source-contract-v2-pr2192-86a0021b/` — seven raw source blobs plus deterministic core and snapshot manifests.
- `experiments/specchoice-v1.3.2/tests/test_bundle_verifier.py` — custody, atomic candidate, collision, interruption, special-file, and tamper tests.

## Decisions Made

- Candidate construction is authorized only for the exact reviewed proposal and exact seven-file inventory; it does not alter the frozen contract or the #2192 rejected receipt.
- No derived artifacts are present. The final binding explicitly records empty derived-artifact arrays, so raw authority and transform lineage are unambiguous.
- The candidate is not downstream eligible and has neither offline replay proof nor accepted-publication authority. Plan 04 must add and prove bundle-alone replay before any later accepted-state decision.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Tracking] Corrected GSD tracking fields after state update.**
- **Found during:** Plan finalization
- **Issue:** The updater correctly recorded 3/4 in the body but left front-matter `percent: 0`, labelled the two new decisions as `Phase ?`, and did not mark the Wave 3 plan line complete.
- **Fix:** Aligned the state front matter/body/activity/decision labels and the Wave 3 roadmap item with the committed Plan 03 result.
- **Files modified:** `.planning/STATE.md`, `.planning/ROADMAP.md`
- **Verification:** State now reports 3/4 and 75%; the roadmap reports 3/4 plans executed with 01-03 checked.

**Total deviations:** 1 auto-fixed tracking issue (Rule 1).
**Impact on plan:** Tracking now accurately represents the committed candidate; no source, candidate, or accepted-publication authority changed.

## Issues Encountered

- The checkout did not retain the approved pin objects. A disposable bare repository fetched the canonical PR refs and exact pin objects, after the user approved the needed upstream access; extraction then used Git objects only.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 01-04 can add the self-contained offline verifier to the non-accepted candidate, recompute the manifests/root, and independently prove bundle-alone replay.
- Accepted publication remains a hard gate: it needs both that Plan 04 proof and a new explicit accepted-publication authorization. The candidate must not be treated as accepted or downstream eligible.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -v` — 45 tests passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m specchoice_evidence.cli verify-source-contract-proposal-git --git-repository /private/tmp/specchoice-candidate-proof-JqDaZz/proof.git` — all six snapshot proofs and all seven raw blob checks passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m specchoice_evidence.cli verify-candidate bundles/candidates/source-contract-v2-pr2192-86a0021b` — core/root/final binding recomputed successfully.
- `check-boundary` reported `blocking_violations: 0` against the active baseline.
- `publish-accepted` rejected with `ACCEPTED_PUBLICATION_NOT_AUTHORIZED`; `bundles/accepted/` is absent.

## Self-Check: PASSED

- Required candidate module, tests, decision, raw blobs, core manifest, and snapshot manifest exist.
- Task commits `48445f3e`, `1a39ad2c`, `90b3b8b4`, `f870782a`, and `0a2c9ae2` are present; Task 3 contains no tracked file deletion.
- Stub scan found no placeholders, TODO/FIXME markers, or empty mock data in Task 3 code and tests.

---
*Phase: 01-isolated-evidence-boundary-and-source-integrity*
*Completed: 2026-07-30*
