---
phase: 03-human-reviewed-data-preregistration
plan: 02
subsystem: data-integrity
tags: [family-registry, deterministic-split, leakage-audit, human-review, red-path]
requires:
  - phase: 03-human-reviewed-data-preregistration
    provides: frozen candidate inventory and approved WARL legal-set pair from plan 03-01
provides:
  - closed, definition-first family registry with one approved primary assignment
  - deterministic prototype, strict-core, auxiliary, and quarantine membership
  - content-bound family/split packet, readiness, and human decision
affects: [03-03-relevance-metamorphic, 03-04-h2-red-feasibility]
actuals:
  tokens: 8981
  tasks: 3
  commits: 4
tech-stack:
  added: []
  patterns: [canonical-json-authority, pure-function-split, registry-wide-invalidation, no-membership-override]
key-files:
  created:
    - experiments/specchoice-v1.3.2/src/specchoice_data/splits.py
    - experiments/specchoice-v1.3.2/src/specchoice_data/split_review.py
    - experiments/specchoice-v1.3.2/tests/test_data_splits.py
    - experiments/specchoice-v1.3.2/data/preregistration/family-registry-v1.json
    - experiments/specchoice-v1.3.2/data/preregistration/split-manifest-v1.json
    - experiments/specchoice-v1.3.2/reports/h2/family-split-review-v1/review-packet.json
    - experiments/specchoice-v1.3.2/reports/h2/family-split-review-v1/review-packet.md
    - experiments/specchoice-v1.3.2/receipts/family-split-review-readiness-v1.json
    - experiments/specchoice-v1.3.2/reviews/family-split-review-decision-v1.json
  modified: []
key-decisions:
  - "The sole approved pair is assigned to primary family warl_legal_set; mtvec_mode and synthetic_status_field remain descriptive secondary tags only."
  - "Split membership is the deterministic projection of approved identities and the frozen primary-family assignment; no move or promotion control exists."
  - "The prototype contains one pair, while strict core and auxiliary are empty; no case is moved or fabricated to satisfy a threshold."
  - "Empty held-out populations remain valid audited Red evidence and do not authorize a model experiment."
patterns-established:
  - "Definition before assignment: approve closed family semantics before binding any item to a primary family."
  - "Pure split: derive membership from example and primary-family disjointness, never reviewer preference or expected usefulness."
requirements-completed: [TS-08, TS-09, H2-01]
coverage:
  - id: D1
    description: Closed family definitions, exact primary assignments, dependent invalidation, and global prototype reuse are fail-closed.
    requirement: TS-08
    verification:
      - kind: unit
        ref: tests/test_data_splits.py
        status: pass
    human_judgment: false
  - id: D2
    description: Strict and auxiliary membership is a canonical pure function with example, family, and demonstration leakage audits.
    requirement: TS-09
    verification:
      - kind: unit
        ref: tests/test_data_splits.py
        status: pass
    human_judgment: false
  - id: D3
    description: Family definition, sole assignment, and every derived membership set have explicit content-bound human approval.
    requirement: H2-01
    verification:
      - kind: manual_procedural
        ref: reviews/family-split-review-decision-v1.json#decision_sha256=0f12780e551f07f001dbc7a6097fb5553abe79a870da0de65fd339e6bc1b610a
        status: pass
    human_judgment: true
    rationale: Family semantics and the correctness of the source-bound primary assignment require human judgment.
duration: multi-session
completed: 2026-08-03
status: complete
---

# Phase 3 Plan 02: Family Registry and Leakage-Safe Split Summary

**One approved family and one prototype pair are frozen; strict-core and auxiliary membership remain empty by deterministic derivation, preserving the required Red path without moving or inventing cases.**

## Performance

- **Duration:** multi-session
- **Completed:** 2026-08-03T23:17:19Z
- **Tasks:** 3
- **Files created/modified:** 9

## Accomplishments

- Implemented dependency-free closed-registry validation, registry-wide dependent invalidation, global example/span reuse checks, and demonstration leakage checks.
- Froze the approved `warl_legal_set` family definition and assigned `WARL_IMPLEMENTATION_SELECTED_VS_ISA_FIXED` as its sole primary-family member.
- Derived the split without an override: prototype pair count `1`, strict-core case count `0`, auxiliary case count `0`, quarantined count `0`.
- Published and approved a content-bound family/split packet, readiness receipt, and human decision while retaining `model_experiment_authorized: false` downstream.

## Task Commits

1. **Task 1: Family and reuse invariants** — `c2d5409a`, `053af5e0`
2. **Task 2: Deterministic split and leakage validation** — `053af5e0`
3. **Task 3: Family/split packet and human decision** — `667289a0`, `001d9180`

## Authoritative Identities

| Artifact | Logical/content SHA-256 | File SHA-256 |
|---|---|---|
| Family registry | `0974b5444856078306e754b3a5b2cdc01655e2f6fd2c714fd379f8dc75332bc6` | `33dfbce9ce02a1864697de2945df9d2f6811019e8c9d077226727f3a9ce54ceb` |
| Split manifest | `e3797b5f1dd714ebe690fb8033745a09ae272a026b0d03b5a1cf4550a131f658` | `bf0e77b63c66a2fc9868c62c0c1b8ae35088f127662c7c0f88adcdca6c5bced7` |
| Family/split review packet | `1eb575426ad089e9a3d1d9faf9a8a7ca8293335b9269e14ef425735e45044a38` | `537a0ea80b72cd98741e26771d7b7e0892b9a5e340bf50e385f4b62174e54ac8` |
| Family/split review Markdown | n/a | `013a236fb642e9e77ed60c43f84f138ca790dda43508439fb238893a25f53858` |
| Family/split readiness | `1ec0a588707210fe89601956a4cd116d12219940eca73cb8629e9f7bafdb62c6` | `b40c1463edf4c4b5937a937a1e4fcaab99759f90f5bc409f46ad05e53623925d` |
| Family/split decision | `0f12780e551f07f001dbc7a6097fb5553abe79a870da0de65fd339e6bc1b610a` | `5e1c642316d6ae923ed8e375bfd5e0ac36c30027cb4b87296ce269a0d4a62828` |

## Deterministic Membership

| Population | Count | Members |
|---|---:|---|
| Prototype pairs | 1 | `WARL_IMPLEMENTATION_SELECTED_VS_ISA_FIXED` |
| Strict-core held-out cases | 0 | none |
| Auxiliary held-out cases | 0 | none |
| Quarantined items | 0 | none |

All reuse and leakage diagnostic lists are empty, the manifest is structurally ready, and the empty strict core remains explicit rather than omitted or replaced.

## Decisions Made

- The approved `warl_legal_set` definition covers whether a CSR field's legal written values are implementation-selected or fixed by the ISA.
- Inclusion requires exact source spans, canonical `choice_object: legal_set`, and the implementation-selected versus ISA-fixed boundary. Access mode, count, width, extension gating, and non-value-set uniformity constraints are excluded.
- The sole approved item has one primary family. Its concrete objects are retained as secondary tags and cannot affect split isolation.
- The reviewer acknowledged every deterministically derived membership list as-is: no item was moved, promoted, or fabricated.

## Deviations from Plan

### Auto-fixed Issues

**1. Preserve the frozen Phase 2 lifecycle successor**

- **Found during:** Task 1 implementation
- **Issue:** The plan named `specchoice_data/cli.py`, but modifying it would invalidate the already-approved Phase 2 forward-only lifecycle closure.
- **Fix:** Added the dedicated `specchoice_data/split_review.py` module for packet, readiness, and decision operations.
- **Verification:** All admission and split tests pass; the frozen CLI and upstream authority bytes remain unchanged.
- **Committed in:** `667289a0`

**Total deviations:** 1 lifecycle-preservation fix with no semantic or scope expansion.

## Verification

- `python -m unittest tests.test_data_admission tests.test_data_splits` — 18 passed.
- `ruff check --isolated src/specchoice_data tests/test_data_admission.py tests/test_data_splits.py` — passed.
- Production family registry, split manifest, packet, readiness, and decision — valid against current canonical bytes.
- Registry definition or assignment changes invalidate dependent artifacts rather than repairing them.
- Example/span reuse, strict-family overlap, and demonstration leakage each fail closed in tests.
- No network, model, retrieval, publication, push, or deployment action occurred.

## Next Phase Readiness

- Plan 03-03 must preserve the empty strict core and may not reinterpret auxiliary or synthetic metamorphic cases as natural qualifying pairs.
- Relevance and metamorphic contracts can be preregistered deterministically, but cannot authorize model execution while natural coverage remains below Yellow.
- Plan 03-04 must report `red_required` from one qualifying natural pair and zero held-out cases, with corpus coverage and pair-admission failure analysis.

## Self-Check: PASSED

- All declared artifacts exist and every recorded SHA-256 was recomputed from current bytes.
- All 18 admission and split tests pass, and the family/split decision validates against exact registry, manifest, packet, and readiness identities.
- Prototype, strict, auxiliary, and quarantine memberships match the approved deterministic derivation exactly.

---
*Phase: 03-human-reviewed-data-preregistration*
*Completed: 2026-08-03*
