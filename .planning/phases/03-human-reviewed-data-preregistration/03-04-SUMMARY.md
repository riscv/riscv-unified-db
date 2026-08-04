---
phase: 03-human-reviewed-data-preregistration
plan: 04
subsystem: data-integrity
tags: [h2, whole-chain-validation, eligibility, data-authority, red-required]
requires:
  - phase: 03-human-reviewed-data-preregistration
    provides: approved pair, split, relevance, and metamorphic decisions from plans 03-01 through 03-03
provides:
  - descriptor-bound whole-chain H2 recomputation and separate count audit
  - approved human H2 decision over exact identities, exclusions, counts, and thresholds
  - immutable Phase 3 data authority with deterministic red_required eligibility
  - reproducible corpus coverage and pair-admission failure analysis
affects: [04-offline-treatments-retrieval-branch-freeze, 05-red-no-call-evidence, 07-feasibility-conclusion]
actuals:
  tokens: 19876
  tasks: 3
  commits: 6
tech-stack:
  added: []
  patterns: [whole-chain-recompute, separate-count-buckets, approved-only-authority, exact-resume-no-replace]
key-files:
  created:
    - experiments/specchoice-v1.3.2/src/specchoice_data/h2.py
    - experiments/specchoice-v1.3.2/tests/test_data_h2.py
    - experiments/specchoice-v1.3.2/reports/h2/h2-data-review-v1/review-packet.json
    - experiments/specchoice-v1.3.2/reports/h2/h2-data-review-v1/review-packet.md
    - experiments/specchoice-v1.3.2/receipts/h2-data-review-readiness-v1.json
    - experiments/specchoice-v1.3.2/reviews/h2-data-decision-v1.json
    - experiments/specchoice-v1.3.2/phase3/data-authority-v1.json
    - experiments/specchoice-v1.3.2/reports/h2/data-eligibility-v1.json
    - experiments/specchoice-v1.3.2/reports/h2/data-eligibility-v1.md
  modified: []
key-decisions:
  - "Whole-chain recomputation confirms one qualifying natural pair, zero strict cases, zero auxiliary cases, and four unavailable metamorphic directions."
  - "The two rejected pair proposals remain excluded for CHOICE_OBJECT_MISMATCH and H1_STATUS_CONFLICT; neither is repaired or replaced."
  - "Exact threshold arithmetic selects red_required: Yellow shortfalls are three pairs and six strict cases; Green shortfalls are five pairs and ten strict cases."
  - "Human H2 approval authorizes only the Phase 3 data-feasibility authority; retrieval, model execution, external publication, and final Phase 4 branch authority remain false."
patterns-established:
  - "Terminal authority: reopen and recompute every upstream identity immediately before approved-only output construction."
  - "Red is evidence: insufficient complete reviewed data publishes one deterministic status rather than becoming invalid or triggering quota filling."
requirements-completed: [TS-08, TS-09, H2-01]
coverage:
  - id: D1
    description: The H2 runner reopens and recomputes the full Phase 2/3 evidence chain and fails closed on any frozen-input drift.
    requirement: TS-08
    verification:
      - kind: integration
        ref: tests/test_data_h2.py
        status: pass
    human_judgment: false
  - id: D2
    description: Corpus coverage, exclusions, pair-admission failures, thresholds, and exact Red status remain separate and reproducible.
    requirement: TS-09
    verification:
      - kind: integration
        ref: reports/h2/data-eligibility-v1.json#report_sha256=1122215c23874298157c45de67925116253f25081e6966b140b8a396fade538c
        status: pass
    human_judgment: false
  - id: D3
    description: H2 approval binds exact chain, packet, readiness, counts, exclusions, invariants, and deterministic eligibility.
    requirement: H2-01
    verification:
      - kind: manual_procedural
        ref: reviews/h2-data-decision-v1.json#decision_sha256=a0045fae47903cef91062896c52761e1e6277efcf3ba89ba4032a211e58f8cb6
        status: pass
    human_judgment: true
    rationale: Only the human reviewer may accept the complete data root and Red feasibility conclusion.
duration: multi-session
completed: 2026-08-04
status: complete
---

# Phase 3 Plan 04: H2 Data Authority and Red Eligibility Summary

**The complete approved Phase 3 chain deterministically yields `red_required`: one qualifying natural pair, zero strict cases, four unavailable metamorphic directions, and no model, retrieval, publication, or execution authority.**

## Performance

- **Duration:** multi-session
- **Completed:** 2026-08-04T07:22:25Z
- **Tasks:** 3
- **Files created/modified:** 9

## Accomplishments

- Implemented a dependency-free H2 runner that reopens and recomputes every Phase 2/3 authority, registry, split, review packet, readiness, and human decision.
- Produced a disjoint count audit, corpus coverage shortfalls, and the two exact rejected-pair analyses without omitting or backfilling any item.
- Collected approved human H2 decision `a0045fae47903cef91062896c52761e1e6277efcf3ba89ba4032a211e58f8cb6` over seven explicit acknowledgment categories.
- Published data authority `e84344483d5404fe1a4030a694b25ccd5edbccd8f695d369081b54ab2c69eb12` and eligibility report `1122215c23874298157c45de67925116253f25081e6966b140b8a396fade538c` with one status: `red_required`.

## Task Commits

1. **Task 1: Whole-chain H2 readiness and count audit** — `6e2d41cc`, `5b3bd604`, `f0b497fc`, `46de28a3`
2. **Task 2: Human H2 decision** — `dcc3c0ab`
3. **Task 3: Approved-only authority and eligibility reports** — `3b681603`

## Authoritative Identities

| Artifact | Logical/content SHA-256 | File SHA-256 |
|---|---|---|
| Recomputed Phase 3 chain | `e17ff113dc768b97a9c9f647dcccf3b6499e7f17a7dca21e1346a7daa6fab2c0` | n/a |
| H2 review packet | `4637874bf5c9778f8d0ba4c85b4f4fcea6c08d1cbf2ce0feb181cd15ab05d761` | `2924f5af2a5a01a82b8522970e5852d872c0cc71afe24c1230ddb51cca813c40` |
| H2 review Markdown | n/a | `dc93d110b8e532160ea19e4dd49da34afb410b509fbe870d6d3fb02c8e0ab6ab` |
| H2 readiness | `dfba81b01d678568196ce1a24d3b1b255052cdef4f85ad2df5c8f7358085b2e7` | `f1ca51317182ab48b7313aca0841906618127fbdde35c2d2bc3e4c11ee33077e` |
| H2 decision | `a0045fae47903cef91062896c52761e1e6277efcf3ba89ba4032a211e58f8cb6` | `2896f0df3e0b73a96056b9e9348a3424936aa15280389112a0a4b815840784a1` |
| Phase 3 data authority | `e84344483d5404fe1a4030a694b25ccd5edbccd8f695d369081b54ab2c69eb12` | `da8650a49940f88629ea5bf3eee83dc6091fad19577dd5b54399525c0617db77` |
| Data eligibility report | `1122215c23874298157c45de67925116253f25081e6966b140b8a396fade538c` | `d38cbe8af33b72f91cecf42cdf42d3c56824bc2bd48877386454fe8c2e214f81` |
| Data eligibility Markdown | n/a | `56b8c311ef31f276214eaf2831e38cc0d07883ba991a175899cbe1e71b3d8d29` |

## Final Eligibility

| Evidence | Observed | Yellow requirement | Green requirement |
|---|---:|---:|---:|
| Qualifying natural pairs | 1 | 4 | 6 |
| Strict approved cases | 0 | 6 | 10 |
| Available metamorphic directions | 0 | reviewed required directions | reviewed required directions |
| Unavailable human-excluded directions | 4 | separate, non-counting | separate, non-counting |

- Yellow shortfall: 3 qualifying pairs and 6 strict cases.
- Green shortfall: 5 qualifying pairs and 10 strict cases.
- Final Phase 3 eligibility: `red_required`.
- `retrieval_authorized=false`, `model_execution_authorized=false`, `external_publication_authorized=false`, `phase4_decision_required=true`.

## Pair-Admission Failure Analysis

1. `POS_DIRECT_CACHE_BLOCK` versus `NEG_SHALL_NO_DELEGATION` — `CHOICE_OBJECT_MISMATCH`: direct numeric choice versus a uniformity constraint.
2. `POS_CSR_RW_MTVEC_ACCESS` versus `NEG_FIXED_ENCODING` — `H1_STATUS_CONFLICT`: the frozen H1 state is `not_surfaced`, not Phase 3 `classify_out`.

Both rejections are bound into the chain and reports; neither was repaired, relabeled, or replaced.

## Decisions Made

- `red_required` is a valid complete result because the evidence chain and reviews are complete even though counts are insufficient.
- H2 approval acknowledges data feasibility and the exact Red conclusion only. It cannot select or authorize the Phase 4 execution branch.
- The sole qualifying ID is `WARL_IMPLEMENTATION_SELECTED_VS_ISA_FIXED`; strict and auxiliary contributor lists remain empty.
- The four unavailable metamorphic IDs remain in quarantine/exclusion reporting and never enter dataset counts.

## Deviations from Plan

### Auto-fixed Issues

**1. Preserve the frozen Phase 2 CLI authority**

- **Found during:** Task 1 implementation
- **Issue:** The plan named `specchoice_data/cli.py`, but changing it would invalidate the approved Phase 2 lifecycle successor.
- **Fix:** Implemented all H2 behavior in the dedicated `specchoice_data.h2` module.
- **Verification:** The frozen CLI remains unchanged; the H2 runner reuses its read-only lifecycle gate.
- **Committed in:** `5b3bd604`

**2. Make the requested failure and corpus audits terminal outputs**

- **Found during:** Task 1 packet construction
- **Issue:** Count buckets alone did not preserve the reasons rejected authoring proposals could not enter the frozen inventory.
- **Fix:** Bound `pair-authoring-rejections-v1.json`, retained both rationales, and added explicit Yellow/Green shortfalls to packet, authority, and eligibility report.
- **Verification:** Rejection file SHA-256 `81ad6508763ebfe6523d17b8ee66fe0f88779369b8b8afb09072bbb92077952a` is in the chain; both failure rows and all shortfalls are present in canonical output.
- **Committed in:** `f0b497fc`

**Total deviations:** 2 evidence-preservation fixes with no semantic expansion or authorization change.

## Verification

- Cumulative Phase 3 plus canonical/filesystem suite — 72 tests passed.
- `ruff check --isolated src/specchoice_data tests/test_data_admission.py tests/test_data_splits.py tests/test_data_relevance.py tests/test_data_h2.py` — passed.
- Current production chain, H2 packet, readiness, decision, authority, eligibility JSON, and Markdown were independently rebuilt and matched byte-for-byte.
- Frozen-input mutation, incomplete/disputed H2, divergent exact-resume targets, invalid eligibility scope, and stale authority fail closed in tests.
- The H2 runner performed no retrieval, prompt assembly, model call, aggregate experiment measurement, discovery, network, publication, push, deployment, or remote mutation.

## Threat Outcomes

| Threat | Outcome |
|---|---|
| Frozen input tampering | blocked by full recomputation and chain hash |
| Inferred or spoofed H2 approval | blocked by seven explicit acknowledgments, identity, rationale, signature, attestation, and UTC timestamp |
| Eligibility authority escalation | blocked by three false authorization booleans and required Phase 4 decision |
| Count/exclusion repudiation | blocked by exact sorted ID buckets and retained rejection rationales |
| Divergent output replacement | blocked by descriptor-bound no-replace exact-resume writer |
| Same-version repair after drift | blocked by `FROZEN_INPUT_CHANGE_REQUIRES_NEW_EXPERIMENT_VERSION` |

## Next Phase Readiness

- Phase 4 receives an approved Phase 3 data authority whose only eligibility is `red_required`.
- Phase 4 must select and freeze the Red no-model branch; it cannot reinterpret this data authority as permission for retrieval or model execution.
- Downstream Red phases can reuse the deterministic runner, coverage audit, and pair-admission failure analysis without reopening H1 or the candidate inventory.

## Self-Check: PASSED

- All declared artifacts exist and every recorded SHA-256 was recomputed from current bytes.
- The complete 72-test validation partition and static checks pass.
- The exact approved H2 decision reproduces the same authority and `red_required` eligibility with all execution/publication permissions false.

---
*Phase: 03-human-reviewed-data-preregistration*
*Completed: 2026-08-04*
