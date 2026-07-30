---
phase: 01-isolated-evidence-boundary-and-source-integrity
plan: 01
subsystem: evidence-boundary
tags: [python, stdlib, sha256, canonical-json, filesystem-policy]
requires: []
provides:
  - "Immutable Phase 1 v2 baseline with a reproducible SHA-256 identity"
  - "Exact experiment/control allowlist and fail-closed filesystem boundary CLI"
  - "Reviewer-approved control-plane receipt bound to baseline, allowlist, and policy hashes"
affects: [01-02, 01-03, 01-04, phase-01-verification]
tech-stack:
  added: [Python standard library unittest]
  patterns: [canonical JSON bytes, exact path allowlist, lstat-before-open, immutable-generation receipts]
key-files:
  created:
    - experiments/specchoice-v1.3.2/baselines/phase-start-v2.json
    - experiments/specchoice-v1.3.2/config/boundary_allowlist.json
    - experiments/specchoice-v1.3.2/receipts/control-update-decision-plan01.json
  modified:
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/baseline.py
    - experiments/specchoice-v1.3.2/tests/test_filesystem_boundary.py
key-decisions:
  - "Use phase-start-v2.json (e8f7e153ffbc5285b361039153f8eea6205448e9f82e2b14efa9af3e74912e15) as the active immutable Phase 1 baseline while retaining v1 as historical evidence."
  - "Treat .DS_Store as visible non-attributed macOS metadata only under the phase-01 policy override; all other outside-boundary changes remain blocking."
  - "Permit GSD control-file updates only after a canonical reviewer approval binds the exact baseline, allowlist, and policy hashes."
patterns-established:
  - "Every later boundary receipt must cite the active phase-start baseline SHA-256."
  - "Boundary paths match one slash-terminated root or an exact control file, never a prefix."
requirements-completed: [TS-01]
coverage:
  - id: D1
    description: "Immutable baseline, exact allowlist, and fail-closed filesystem guard are independently executable."
    requirement: TS-01
    verification:
      - kind: unit
        ref: "PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -v"
        status: pass
      - kind: integration
        ref: "PYTHONPATH=src python3 -m specchoice_evidence.cli check-boundary"
        status: pass
    human_judgment: false
  - id: D2
    description: "Reviewer approval authorizes the narrow control-plane transition for the active baseline."
    requirement: TS-01
    verification:
      - kind: integration
        ref: "PYTHONPATH=src python3 -m specchoice_evidence.cli validate-control-decision receipts/control-update-decision-plan01.json"
        status: pass
    human_judgment: true
    rationale: "Start-state attribution and the approval disposition are human authority decisions."
duration: 10min
completed: 2026-07-30
status: complete
---

# Phase 01 Plan 01: Immutable Boundary Baseline Summary

**A canonical v2 Phase 1 baseline, exact filesystem boundary guard, and human-approved control receipt now protect all later source-custody work.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-07-30T13:48:57Z
- **Completed:** 2026-07-30T13:58:52Z
- **Tasks:** 3/3
- **Files modified:** 14

## Accomplishments

- Captured immutable, canonical start-state evidence with exact byte length and SHA-256 validation.
- Enforced narrow root/exact-control-file attribution and fail-closed handling of path escapes, links, special files, mount uncertainty, and hardlink dependencies.
- Recorded the approved control update against active baseline `e8f7e153ffbc5285b361039153f8eea6205448e9f82e2b14efa9af3e74912e15`, allowlist `a245121d9688fa4a4d14356c8bffd1dffd7994ce2395466b8e8afd886bc05ee0`, and policy `fb1b3267200fa9d58df7ca9348ea941737cc32e24a93c424727121afb909955d`.

## Task Commits

1. **Task 1: Capture immutable baseline and prove the boundary tracer** — `b33adc25` (feat)
2. **Task 2: Expand adversarial filesystem and canonical coverage** — `7e67921b`, `2f3e509b`, `ffbf86f7` (test, feat, test)
3. **Task 3: Approve immutable baseline for control updates** — `74369d77` (feat)

## Files Created/Modified

- `experiments/specchoice-v1.3.2/baselines/phase-start-v1.json` and `phase-start-v2.json` — immutable baseline lineage.
- `experiments/specchoice-v1.3.2/config/boundary_allowlist.json` — one experiment root and exact GSD-control exceptions.
- `experiments/specchoice-v1.3.2/src/specchoice_evidence/{canonical,filesystem,baseline,cli}.py` — stdlib-only canonicalization, filesystem policy, delta classification, and CLI entry points.
- `experiments/specchoice-v1.3.2/receipts/control-update-decision-plan01.json` — canonical approved control-plane receipt.
- `experiments/specchoice-v1.3.2/tests/{test_canonical,test_filesystem_boundary}.py` — deterministic boundary, policy, and receipt validation.

## Decisions Made

- The active baseline is v2; historical v1 remains unchanged and independently hashable.
- The user's explicit `.DS_Store` instruction is scoped to Phase 01 through a hash-bound policy override. It preserves visibility and non-attribution, not a general out-of-boundary exception.
- Control-file updates begin only after the approved receipt validates against all three immutable inputs.

## Deviations from Plan

### User-Authorized Policy Override

**1. [User-authorized boundary policy] Preserve visible `.DS_Store` churn as non-blocking Phase 01 OS metadata.**
- **Found during:** Tasks 1–2
- **Issue:** macOS modified and created `.DS_Store` paths after baseline capture, which otherwise require a D-15 restart.
- **Fix:** Retained historical v1, recorded restart lineage to v2, and used the phase-scoped policy override expressly authorized by the user. All non-`.DS_Store` changes remain fail-closed.
- **Files modified:** `baselines/phase-start-v2.json`, `baselines/phase-start-v2-restart.json`, `baselines/ds-store-policy-override-v1.json`, `src/specchoice_evidence/{baseline,cli}.py`
- **Verification:** `check-boundary` reports every visible `.DS_Store` classification and `blocking_violations: 0`.
- **Committed in:** `b33adc25`, `2f3e509b`, `ffbf86f7`

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added the plan-specified control-decision validator.**
- **Found during:** Task 3
- **Issue:** `validate-control-decision` was named by the plan but absent from the CLI, so the approval receipt could not be validated.
- **Fix:** Added canonical receipt, exact-artifact binding, policy-schema, approval, and dispute checks with a regression test.
- **Files modified:** `src/specchoice_evidence/cli.py`, `tests/test_filesystem_boundary.py`, `receipts/control-update-decision-plan01.json`
- **Verification:** 19/19 tests pass and the prescribed validator returns `control_update_approved`.
- **Committed in:** `74369d77`

**Total deviations:** 2 auto-fixed issues (one blocking verifier and one tracking inconsistency) plus 1 user-authorized, scoped policy decision.

**2. [Rule 1 - Tracking] Corrected the GSD progress front matter after the state command calculated 25% but left `percent: 0`.**
- **Found during:** Plan finalization
- **Fix:** Aligned the state front matter and activity text with the recorded 1/4 completed-plan result.
- **Files modified:** `.planning/STATE.md`
- **Verification:** `state.load` and the Phase 1 roadmap row both report plan 1/4 and 25% progress.

## Issues Encountered

- The initial Task 3 verifier invocation exposed the missing plan-specified subcommand. It was repaired before the approval receipt was committed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 01-02 can rely on the active baseline and must cite its SHA-256 in any boundary receipt.
- The Phase 01 `.DS_Store` policy remains deliberately narrow; it does not waive checks for ordinary files.

## Self-Check: PASSED

- Required receipt exists and validates against the active baseline, allowlist, and policy.
- All five Task commits are present in Git history.
- No plan-created or plan-modified file contains a known rendering stub.

---
*Phase: 01-isolated-evidence-boundary-and-source-integrity*
*Completed: 2026-07-30*
