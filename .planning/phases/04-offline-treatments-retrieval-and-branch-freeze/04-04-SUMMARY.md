---
phase: 04-offline-treatments-retrieval-and-branch-freeze
plan: 04
subsystem: offline-branch-authority
tags: [specchoice, h3, red-branch, immutable-evidence, no-model]
requires:
  - phase: 03-human-reviewed-data-preregistration
    provides: accepted red_required Phase 3 authority and H2 bindings
provides:
  - immutable v4 human approved_red decision
  - immutable v4 zero-count Red branch authority
  - no-H4/no-model/no-provider execution contract for downstream consumption
affects: [phase-05, branch-gating, execution-safety]
actuals:
  tokens: 3562
  tasks: 3
  commits: 3
tech-stack:
  added: []
  patterns: [descriptor-bound exact-resume publication, human-approved immutable authority]
key-files:
  created:
    - experiments/specchoice-v1.3.2/reviews/h3-branch-decision-v4.json
    - experiments/specchoice-v1.3.2/phase4/branch-authority-v4.json
  modified:
    - .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-04-SUMMARY.md
key-decisions:
  - "The approved successor is Red-only with N_strict=0 and repeat_count=0; no Green or Yellow alternative is current authority."
  - "H4, provider, credentials, model execution, production retrieval, and external calls remain structurally unauthorized."
patterns-established:
  - "Post-decision leaves are published only through frozen descriptor-bound writers and exact-resume validation."
requirements-completed: [TS-10]
coverage: []
duration: 5min
completed: 2026-08-04
status: complete
---

# Phase 04 Plan 04: Approved Red Authority v4 Summary

**Human-approved, descriptor-bound H3 v4 Red authority fixing zero execution counts and no-H4/no-model reachability.**

## Performance

- **Duration:** 5min
- **Started:** 2026-08-04T16:13:51Z
- **Completed:** 2026-08-04T16:18:44Z
- **Tasks:** 3/3 complete (one pre-decision lifecycle task; two post-decision publication tasks)
- **Files modified:** 3

## Accomplishments

- Validated the complete ordered human approval source, including seven approved acknowledgment categories, all human-owned fields, canonical UTC time, and the derived decision self-hash.
- Recomputed and retained the frozen v4 packet, readiness, inventory, and no-model roots; validated all v1-v3 predecessor identities, including the intentionally absent v3 decision/authority leaves.
- Published exactly the predeclared post-decision leaves through the frozen writers, then passed descriptor-bound exact-resume and post-publication lifecycle checks.
- Confirmed the Phase 5 input is only the v4 Red authority: `N_strict=0`, `repeat_count=0`, `h4_required=false`, and no provider, model, credential, external-call, or production-retrieval authorization.

## Immutable Bindings

| Binding | SHA-256 |
| --- | --- |
| Human authorization source (raw) | `c323d161d784e2322e9fa2d6da7f3b71633901cc84a0819c4fc0d9d781bf2d3c` |
| v4 packet | `d97f1dfd0afe95d067ebee6e8fafa0227703e9ff1a6152dfb5331534036d8cb2` |
| v4 readiness | `fcf13bcaa5f468ebc9cff816313876c4e47abd344d0e1210a2edc55e908d2a12` |
| v4 freeze inventory | `3d960f12b7e68c3dd22dd95faddcde787532b2ab2f3305e0e527fab746c9b3d4` |
| v4 no-model reachability | `3c8120345d0051d2969c329f37e4690a82479987cda25fa6437610984aaec508` |
| v3 historical human source (raw) | `d98fc8967cdba51283924b457c6b24a3f3dde540cd997867eea748b787e606cc` |
| v4 decision (self) | `199c480e1fbc8a9c04574762a9afb356a350660320db6a769d908ce4e8a0f343` |
| v4 authority (self) | `ed285c330c73ba90c7832f83900273f4d9545fc54033831eee5fe39dea4836fe` |
| v4 authority freeze root | `037b3f91077e53e03dfbf44ba3d6b7e71856d1f14998d9d2f3511216943dbd4a` |

## Task Commits

1. **Task 1: Freeze H3 v4 lifecycle** — `fe303882` (feat)
2. **Task 2: Record approved immutable Red decision** — `3ccc019a` (feat)
3. **Task 3: Publish approved-Red-only authority** — `257507fb` (feat)
4. **Plan metadata:** pending (docs)

## Verification

- Full Phase 4 / predecessor / Wave 1-3 suite passed: data admission, splits, relevance, H2, A/B/C frame and prompt contracts, retrieval contract, H3, canonical JSON, and filesystem boundaries.
- Ruff passed for `src/specchoice_treatments` and the four Phase 4 test modules.
- `git diff --check` passed.
- Exact-resume and descriptor-bound post-publication lifecycle validation passed after both leaves were published.
- Frozen v4 packet, Markdown, readiness, H3 source, package export, and H3 test bytes were unchanged; no source, test, or schema change was made after approval.

## Decisions Made

- Applied the human `approved_red` authorization exactly as supplied; it authorizes only the local Red feasibility branch bound to the frozen roots.
- Preserved all v1-v3 artifacts, including the v3 absence of a persisted decision and authority, as historical non-current predecessors.
- Did not update `ROADMAP.md` or `STATE.md`, create an H4 artifact, or expose any model/provider/network/retrieval execution surface.

## Deviations from Plan

None — this run was the approved v4 post-decision publication of pre-frozen writers and artifacts; no frozen implementation or test was altered.

## Known Stubs

None.

## Threat Flags

None. The published authority adds no network endpoint, authentication path, file-access pattern, schema change, provider configuration, credential path, or execution entry point.

## Next Phase Readiness

Phase 5 may consume only `phase4/branch-authority-v4.json` as the Red, zero-count, no-H4/no-model contract. No model, provider, credential, external call, production retrieval, H4 process, external publication, or upstream submission is authorized.

## Self-Check: PASSED

- Confirmed both published v4 leaves and this summary exist.
- Confirmed publication commits `3ccc019a` and `257507fb` exist.

---
*Phase: 04-offline-treatments-retrieval-and-branch-freeze*
*Completed: 2026-08-04*
