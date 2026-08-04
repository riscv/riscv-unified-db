---
phase: 03-human-reviewed-data-preregistration
plan: 03
subsystem: data-integrity
tags: [relevance, metamorphic, preregistration, frozen-inventory, red-path]
requires:
  - phase: 03-human-reviewed-data-preregistration
    provides: approved family registry and deterministic split from plan 03-02
provides:
  - complete empty relevance registry for the empty strict and auxiliary populations
  - explicit unavailable records for all four required metamorphic directions
  - decision-free packet/readiness and content-bound human exclusion decision
affects: [03-04-h2-red-feasibility, 06-03-metamorphic-evaluation]
actuals:
  tokens: 12652
  tasks: 3
  commits: 4
tech-stack:
  added: []
  patterns: [exact-coverage-registry, no-ranking-fields, explicit-unavailability, synthetic-non-counting]
key-files:
  created:
    - experiments/specchoice-v1.3.2/src/specchoice_data/relevance.py
    - experiments/specchoice-v1.3.2/tests/test_data_relevance.py
    - experiments/specchoice-v1.3.2/data/preregistration/pair-relevance-registry-v1.json
    - experiments/specchoice-v1.3.2/data/preregistration/metamorphic-registry-v1.json
    - experiments/specchoice-v1.3.2/reports/h2/relevance-metamorphic-review-v1/review-packet.json
    - experiments/specchoice-v1.3.2/reports/h2/relevance-metamorphic-review-v1/review-packet.md
    - experiments/specchoice-v1.3.2/receipts/relevance-metamorphic-review-readiness-v1.json
    - experiments/specchoice-v1.3.2/reviews/relevance-metamorphic-review-decision-v1.json
  modified: []
key-decisions:
  - "Empty strict and auxiliary populations require exactly empty relevance rows and an empty PairHit-eligible denominator."
  - "The frozen candidate inventory contains no metamorphic candidate; all four required directions are explicitly unavailable and human-excluded rather than synthesized after freeze."
  - "Every metamorphic direction and synthetic side is non-counting by construction; unavailable directions cannot be treated as dataset evidence."
  - "The approved review records the complete Red audit state and does not authorize retrieval, model execution, or replacement candidates."
patterns-established:
  - "No-rank relevance: semantic relevance records contain no rank, score, similarity, or top-k field."
  - "Frozen absence: required but unavailable directions remain named, reasoned, and human-reviewed instead of silently omitted."
requirements-completed: [TS-08, TS-09, H2-01]
coverage:
  - id: D1
    description: Strict and auxiliary relevance coverage is exact, separately represented, and ranking-free.
    requirement: TS-08
    verification:
      - kind: unit
        ref: tests/test_data_relevance.py
        status: pass
    human_judgment: false
  - id: D2
    description: Four exact metamorphic direction IDs are present, non-counting, and either fully source-validated or explicitly unavailable.
    requirement: TS-09
    verification:
      - kind: unit
        ref: tests/test_data_relevance.py
        status: pass
    human_judgment: false
  - id: D3
    description: Empty relevance membership and all four unavailable metamorphic directions have explicit content-bound human dispositions.
    requirement: H2-01
    verification:
      - kind: manual_procedural
        ref: reviews/relevance-metamorphic-review-decision-v1.json#decision_sha256=5eac50a3ce9ae823b0fc9efd88aa28e7f7f4f44cef1ae54bb70333420f5d32ea
        status: pass
    human_judgment: true
    rationale: The reviewer must control whether frozen relevance and metamorphic semantics are approved, disputed, or excluded.
duration: multi-session
completed: 2026-08-04
status: complete
---

# Phase 3 Plan 03: Relevance and Metamorphic Preregistration Summary

**Relevance is completely empty because the held-out populations are empty, and all four required metamorphic directions remain explicit human-excluded gaps because candidate inventory v1 contains no frozen metamorphic candidate.**

## Performance

- **Duration:** multi-session
- **Completed:** 2026-08-04T07:03:25Z
- **Tasks:** 3
- **Files created/modified:** 8

## Accomplishments

- Implemented exact strict/auxiliary relevance coverage, explicit `no_relevant_pair`, structure/axis compatibility, and hard rejection of ranking fields.
- Implemented source-bound metamorphic validation for future frozen authoritative or human-synthetic candidates, including exact edits, human approval, direction/version binding, and zero count eligibility.
- Published the current frozen-inventory result: zero relevance rows, zero PairHit-eligible cases, zero available metamorphic candidates, and four explicit unavailable directions.
- Collected a complete human decision excluding all four unavailable directions without adding, replacing, or synthesizing evidence.

## Task Commits

1. **Task 1: Relevance coverage invariants** — `cd5a2600`, `464a8601`
2. **Task 2: Metamorphic direction and source validation** — `464a8601`
3. **Task 3: Packet, readiness, and human decision** — `1a2bf94c`, `a9287864`

## Authoritative Identities

| Artifact | Logical/content SHA-256 | File SHA-256 |
|---|---|---|
| Pair relevance registry | `247be76e7a8c5eb3d46edf9fde72a42c11bc307d010a777f36f5ff69c8f374cd` | `ffa608bc3326cde6cb6b581b4567f2404ef92d1b5ca3483393757716b24e0fa3` |
| Metamorphic registry | `dec1c4a48dd97dcdadd3cc3fb1d61f3cb726e9e883517eab08ea5c0b83188656` | `78290c9c1eb4f4eea60b92f3d1cd1e87fd07d4f480313da711e6574b2629d12e` |
| Review packet | `4ba2e5e4e1ed8ee7e537a31ca0226c1e0cf478d7b496626ade91420a3503855a` | `3db32bb3a06382943783c4747196a00f6365ccba9a2527c004e44d3e04012344` |
| Review Markdown | n/a | `c04067806b7b4b3f9cebb6b2d5c6a1e74e0e6c50bbe3869d4846f2981c3b763f` |
| Review readiness | `fa9be90546437a774ca5591255e5c5e34712e3c39edde2933164ef3f37afa63d` | `1998fb91c2532106911153dfac0429363dace07a92e45fbb56d1c8857f231c8f` |
| Review decision | `5eac50a3ce9ae823b0fc9efd88aa28e7f7f4f44cef1ae54bb70333420f5d32ea` | `9c343eadcea61f16825cbcaf79de5dba4cdd167304ff3cca5b10a7ebaad750c1` |

## Coverage Results

| Category | Count | State |
|---|---:|---|
| Strict relevance rows | 0 | complete for empty strict core |
| Auxiliary relevance rows | 0 | complete for empty auxiliary set |
| PairHit-eligible strict cases | 0 | empty denominator |
| Available metamorphic directions | 0 | no frozen candidates |
| Unavailable metamorphic directions | 4 | explicitly excluded by human review |

The four named gaps are `choice_space_origin`, `hardware_software_authority`, `normative_note_example`, and `warl_fixed_legal_set`. Every row has `count_eligible: false` and the same frozen-inventory rationale.

## Decisions Made

- Absence is not interpreted as negative relevance: exact empty split membership requires exact empty relevance rows.
- No frozen metamorphic candidate exists, so no semantic text, expected delta, or provenance record is generated after inventory freeze.
- All four required direction records remain visible and human-excluded; none is silently dropped or replaced.
- The aggregate human approval certifies the completeness of this Red audit state only.

## Deviations from Plan

### Auto-fixed Issues

**1. Represent frozen metamorphic absence without post-freeze synthesis**

- **Found during:** Task 2 production materialization
- **Issue:** The plan described four available contracts, but the human-frozen inventory contains only the natural pair and explicitly forbids later candidate additions or replacements.
- **Fix:** Extended the closed registry with one explicit `unavailable` state per required direction. Available candidates still require exact source/edit validation; current unavailable records carry no invented semantic text and are human-excluded.
- **Verification:** The registry contains exactly four required IDs, available count is zero, unavailable count is four, every row is non-counting, and the human decision explicitly excludes each row.
- **Committed in:** `1a2bf94c`, `a9287864`

**2. Preserve the frozen Phase 2 CLI authority**

- **Found during:** Task 1 implementation
- **Issue:** Editing the plan-listed `specchoice_data/cli.py` would invalidate the approved Phase 2 lifecycle successor.
- **Fix:** Kept all review construction and validation in the dedicated `specchoice_data.relevance` module.
- **Verification:** The frozen CLI remains unchanged and all cumulative Phase 3 tests pass.
- **Committed in:** `464a8601`

**Total deviations:** 2 authority-preserving fixes; neither expands the candidate inventory or authorizes model execution.

## Verification

- `python -m unittest tests.test_data_admission tests.test_data_splits tests.test_data_relevance` — 30 passed.
- `ruff check --isolated src/specchoice_data tests/test_data_admission.py tests/test_data_splits.py tests/test_data_relevance.py` — passed.
- Production relevance registry, metamorphic registry, packet, readiness, and decision — valid against current canonical bytes.
- Authoritative span mutation, incomplete synthetic edit/approval, model generation, count eligibility, source reversal, and direction-set drift fail closed in tests.
- No retrieval rank, prompt, model output, model call, network, publication, push, or deployment action occurred.

## Next Phase Readiness

- Plan 03-04 can consume one qualifying natural pair, zero strict cases, zero PairHit-eligible cases, and four human-excluded unavailable metamorphic directions.
- Deterministic eligibility must be `red_required`; model experiment authorization remains false.
- H2 reporting must retain the metamorphic gaps as separate audit evidence and must not reinterpret them as invalid natural pairs or threshold counts.

## Self-Check: PASSED

- All declared artifacts exist and every recorded SHA-256 was recomputed from current bytes.
- All 30 cumulative Phase 3 tests pass and the decision validates against the exact packet and readiness.
- The candidate inventory, Phase 2 authority, frozen CLI, family registry, and split manifest remain unchanged.

---
*Phase: 03-human-reviewed-data-preregistration*
*Completed: 2026-08-04*
