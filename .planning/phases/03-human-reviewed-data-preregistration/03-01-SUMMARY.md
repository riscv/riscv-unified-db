---
phase: 03-human-reviewed-data-preregistration
plan: 01
subsystem: data-integrity
tags: [canonical-json, descriptor-bound-io, human-review, candidate-inventory, red-path]
requires:
  - phase: 02-deterministic-measurement-spine
    provides: accepted-v6 source authority, approved H1 decision, and forward-only lifecycle closure
provides:
  - descriptor-bound Phase 3 candidate admission and immutable inventory validation
  - one approved H1-consistent WARL legal-set directed pair
  - content-bound pair packet, readiness, human decision, and rejected-combination audit
affects: [03-02-family-split, 03-03-relevance-metamorphic, 03-04-h2-red-feasibility]
actuals:
  tokens: 19587
  tasks: 3
  commits: 9
tech-stack:
  added: []
  patterns: [canonical-json-authority, descriptor-bound-raw-byte-spans, no-replace-inventory, explicit-human-disposition]
key-files:
  created:
    - experiments/specchoice-v1.3.2/config/data/phase3-data-schema-v1.json
    - experiments/specchoice-v1.3.2/src/specchoice_data/admission.py
    - experiments/specchoice-v1.3.2/src/specchoice_data/review.py
    - experiments/specchoice-v1.3.2/src/specchoice_data/worksheet.py
    - experiments/specchoice-v1.3.2/data/preregistration/candidates-v1/candidate-inventory.json
    - experiments/specchoice-v1.3.2/reviews/pair-review-decision-v1.json
    - experiments/specchoice-v1.3.2/reviews/pair-authoring-rejections-v1.json
  modified:
    - experiments/specchoice-v1.3.2/tests/test_data_admission.py
key-decisions:
  - "The complete v1 inventory contains exactly one natural pair; no weak pair, replacement, or upstream H1 reopening is permitted to meet thresholds."
  - "The accepted pair uses canonical choice_object legal_set while preserving the concrete mtvec MODE and synthetic status-field targets in side provenance."
  - "The cache-block proposal was rejected for a real choice_object mismatch, and the CSR-access proposal was rejected because its contrast is H1-approved not_surfaced rather than classify_out."
  - "Insufficient pair coverage is preserved for deterministic red_required evaluation; model execution and external publication remain unauthorized."
patterns-established:
  - "Candidate freeze: enumerate the complete canonical candidate tree before review and reject any later path or byte change as CANDIDATE_INVENTORY_CHANGED."
  - "Review order: approve positive and contrast sides independently before the directed relationship and aggregate decision."
requirements-completed: [TS-08, TS-09, H2-01]
coverage:
  - id: D1
    description: Descriptor-bound candidate admission validates exact sources, spans, claims, pair structure, and diagnostics.
    requirement: TS-08
    verification:
      - kind: unit
        ref: tests/test_data_admission.py
        status: pass
    human_judgment: false
  - id: D2
    description: Complete inventory is frozen before review and any added, removed, renamed, or changed candidate invalidates v1.
    requirement: TS-09
    verification:
      - kind: unit
        ref: tests.test_data_admission.DataAdmissionTests.test_complete_inventory_is_frozen_before_review
        status: pass
      - kind: unit
        ref: tests.test_data_admission.DataAdmissionTests.test_invalid_candidates_remain_auditable_and_cannot_be_backfilled
        status: pass
    human_judgment: false
  - id: D3
    description: Both pair sides and their directed relationship have explicit content-bound human approval.
    requirement: H2-01
    verification:
      - kind: manual_procedural
        ref: reviews/pair-review-decision-v1.json#decision_sha256=6b30af40b1f8292e17a9a81c4dc296b2308a1828963ed36380c2e301c540cf07
        status: pass
    human_judgment: true
    rationale: Pair semantics and controlled-minimal-contrast validity require RISC-V human judgment.
duration: multi-session
completed: 2026-08-03
status: complete
---

# Phase 3 Plan 01: Candidate Admission and Pair Review Summary

**One immutable, approved WARL legal-set pair survives the H1-consistency and controlled-contrast gates; insufficient coverage is preserved for a reproducible Red path without quota filling.**

## Performance

- **Duration:** multi-session
- **Completed:** 2026-08-03T23:03:20Z
- **Tasks:** 3
- **Files created/modified:** 14

## Accomplishments

- Implemented a dependency-free canonical schema, decision-free worksheet, descriptor-bound admission pipeline, pair packet/readiness, and explicit decision validator.
- Froze exactly one candidate with inventory content hash `1618b52bd109acaeff2953cd3644f4968eef7569a4e488a9b94bf330579fe934`; production admission reports `valid` with no diagnostics.
- Published approved pair decision `6b30af40b1f8292e17a9a81c4dc296b2308a1828963ed36380c2e301c540cf07` and retained both rejected authoring combinations outside the inventory.
- Preserved local-only custody, frozen H1 semantics, and `model_experiment_authorized: false` for downstream deterministic Red evaluation.

## Task Commits

1. **Task 1: Authority-to-review tracer** — `8f1d73f9`, `a776944e`, `c4c9a844`
2. **Task 2: Human-authored inventory freeze** — `3e0cabae`, `9b44eaee`, `5b784eb2`
3. **Task 3: Pair packet and human decision** — `a1aeef66`, `2f850700`, `27233289`

## Authoritative Identities

| Artifact | Logical/content SHA-256 | File SHA-256 |
|---|---|---|
| Phase 3 schema | `4eb4098ddd33712495526126d804408b2536b7a4ee182f00a97b3536c2b03530` | same |
| Candidate inventory | `1618b52bd109acaeff2953cd3644f4968eef7569a4e488a9b94bf330579fe934` | `eaba09bcc2486cff24f03f9d4e7ca6b59b29b69a6f1aac8822d8d9518ced70e8` |
| Frozen pair candidate | n/a | `ef9cbc256c452c0f999a07e36321237919bd0ba5bf19f8a62a5f8b581490db4f` |
| Pair review packet | `9892c771a2fbeed98b2ee1c97666946fda9b083d726c6c58ee0ad4d579efc8a0` | `50fbe3aea9686dfd0f8d73a7cb9b73536f35e5459f01d38972f7fd120b4c7d82` |
| Pair review Markdown | n/a | `788a8a66bd9be34a10695a8473a24f0eee6d5b0b05f6ca766d57d7d7f73f20f2` |
| Pair readiness | `2b6d4a4745aba02a593660ffb18f30e4ab146d6be11ce199666e2c2f6a51a18c` | `5e2509c0aa81f57343a69c1ada1e4cdeb791010f47fb3710f1ffc6f222a63d1d` |
| Pair decision | `6b30af40b1f8292e17a9a81c4dc296b2308a1828963ed36380c2e301c540cf07` | `a9b054dc998849f66813bdec9e5b3f487500b12000630ee90ff70ea0c356cee8` |
| Rejected-combination audit | n/a | `81ad6508763ebfe6523d17b8ee66fe0f88779369b8b8afb09072bbb92077952a` |

## Decisions Made

- `WARL_IMPLEMENTATION_SELECTED_VS_ISA_FIXED` is the sole approved natural pair. Both sides use canonical `choice_object: legal_set`; the coupled discriminating axes are `authority` and `choice_space_origin`.
- `POS_DIRECT_CACHE_BLOCK` versus `NEG_SHALL_NO_DELEGATION` is excluded because a numeric value and a cross-hart uniformity constraint are different choice objects.
- `POS_CSR_RW_MTVEC_ACCESS` versus `NEG_FIXED_ENCODING` is excluded because the latter is frozen as `not_surfaced`; translating it to `classify_out` would rewrite H1.
- The remaining `classify_out` fixture, `NEG_EXT_GATED_PBMTE`, has no same-object positive partner. The corpus therefore cannot reach Yellow or Green without prohibited upstream reopening or weak pairing.

## Deviations from Plan

### Auto-fixed Issues

**1. Missing complete-tree revalidation before review**

- **Found during:** Task 2 verification
- **Issue:** The initial tracer checked a selected entry but did not reject an additional unlisted file elsewhere in the frozen tree.
- **Fix:** Added `validate_candidate_inventory_v1`, on-disk inventory verification, full path/hash/length/kind equality, and the two planned inventory tests.
- **Verification:** 9/9 `tests.test_data_admission` tests pass; production inventory and pair both validate.
- **Committed in:** `9b44eaee`, `5b784eb2`

**2. Preserve rejected authoring decisions outside the candidate inventory**

- **Found during:** Human candidate authoring checkpoint
- **Issue:** Chat-only rejection history would not provide reproducible failure analysis.
- **Fix:** Added canonical `pair-authoring-rejections-v1.json` bound to H1, inventory, and pair decision identities.
- **Verification:** Canonical byte encoding and SHA-256 verified locally.
- **Committed in:** `27233289`

**Total deviations:** 2 correctness/audit fixes. Neither changes the frozen candidate count or expands semantic scope.

## Verification

- `python -m unittest tests.test_data_admission` — 9 passed.
- `ruff check --isolated src/specchoice_data tests/test_data_admission.py` — passed.
- Production inventory revalidation — valid.
- Production pair admission — valid, diagnostics empty.
- Production pair decision CLI validation — valid.
- Working-tree diff for `phase2/`, `bundles/accepted/`, `spec/`, and `backends/` — empty.
- No network, model, retrieval, publication, push, or deployment action occurred.

## Next Phase Readiness

- Plan 03-02 may consume one approved qualifying pair and must preserve the insufficient corpus without reuse or backfill.
- Downstream eligibility must deterministically report `red_required` because pair count `1 < 4` Yellow threshold; final model experiment authorization remains false.
- Corpus coverage and rejected-pair analysis are now machine-addressable inputs for the requested final Red feasibility runner.

## Self-Check: PASSED

- All declared artifacts exist and their recorded SHA-256 values were recomputed.
- All Task 1-3 acceptance checks passed; the inventory, packet, readiness, and decision validate against current canonical bytes.
- The frozen inventory contains no backfill candidate and the upstream Phase 2/H1 authority remains unchanged.

---
*Phase: 03-human-reviewed-data-preregistration*
*Completed: 2026-08-03*
