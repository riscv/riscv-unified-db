---
phase: 01-isolated-evidence-boundary-and-source-integrity
plan: 02
subsystem: testing
tags: [python-stdlib, canonical-json, sha256, incident-policy, audit-receipt]
requires:
  - phase: 01-01
    provides: approved active boundary baseline and scoped .DS_Store policy
provides:
  - standalone-first canonical environment decision
  - one-way non-canonical environment audit receipt
  - cumulative 90-minute dependency incident state machine
affects: [01-03, source-custody, offline-replay]
tech-stack:
  added: []
  patterns: [stable canonical projection separate from non-canonical audit evidence, cumulative incident clock]
key-files:
  created:
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/environment.py
    - experiments/specchoice-v1.3.2/receipts/environment-decision.json
    - experiments/specchoice-v1.3.2/audit/environment/environment-receipt-phase-start-001.json
  modified:
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py
    - experiments/specchoice-v1.3.2/tests/test_environment.py
key-decisions:
  - "standalone_first is the primary normal route; full UDB setup was neither required nor attempted."
  - "Canonical identity contains only stable tools, capabilities, policy, route, and incident outcome; audit evidence points one-way by SHA-256."
  - "The first concrete dependency failure or setup action starts one 90-minute cumulative clock that cannot pause or reset."
patterns-established:
  - "Canonical decision: deterministic JSON and SHA-256, never read from or reference its audit receipt."
  - "Dependency incident: retain first trigger, store detailed events only in non-canonical audit evidence, stop at the frozen ceiling."
requirements-completed: [TS-01]
coverage:
  - id: D1
    description: Standalone-first canonical decision and one-way non-canonical audit receipt
    requirement: TS-01
    verification:
      - kind: unit
        ref: PYTHONPATH=src python3 -m unittest tests.test_environment -v
        status: pass
    human_judgment: false
  - id: D2
    description: Cumulative 90-minute incident policy for restored, resolved, and ceiling-exceeded states
    requirement: TS-01
    verification:
      - kind: unit
        ref: tests/test_environment.py#EnvironmentDecisionTests
        status: pass
    human_judgment: false
duration: 7min
completed: 2026-07-30
status: complete
---

# Phase 01 Plan 02: Standalone Environment Identity Summary

**A hashable standalone-first environment decision now records actual CPython/Git identities while keeping machine-local operational evidence in a one-way audit receipt and enforcing a cumulative 90-minute dependency ceiling.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-07-30T14:05:48Z
- **Completed:** 2026-07-30T14:12:15Z
- **Tasks:** 2/2
- **Files modified:** 7

## Accomplishments

- Added `record-environment`, which atomically writes the stable canonical decision before the non-canonical receipt that references its SHA-256.
- Recorded the normal route as `standalone_first`, with full UDB setup `required:false` and `attempted:false`, no incident, and no fallback trigger.
- Added injected-clock incident tests for not-triggered, restored standalone, dependency-resolved, and ceiling-exceeded outcomes; retries, alternatives, builds, and waits cannot reset or pause elapsed wall-clock time.

## Task Commits

1. **Task 1: Emit one canonical standalone-first decision and its one-way audit receipt** — `df942575`, `7ff8d237` (test, feat)
2. **Task 2: Prove cumulative incident timing and the 90-minute fail-safe** — `1b33b391`, `37f15401` (test, feat)

**Additional fix:** `4d998419` (fix: sanitize audit path fragments)

## Files Created/Modified

- `experiments/specchoice-v1.3.2/src/specchoice_evidence/environment.py` — stable decision projection, local observation, audit writer, and cumulative incident state machine.
- `experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py` — `record-environment` command.
- `experiments/specchoice-v1.3.2/receipts/environment-decision.json` — canonical normal-route identity, SHA-256 `9f0342c4d2848200e5f894c834f69e828aeb70a7fb813e541258f43d7fc3d246`.
- `experiments/specchoice-v1.3.2/audit/environment/environment-receipt-phase-start-001.json` — non-canonical receipt with the one-way digest reference.
- `experiments/specchoice-v1.3.2/tests/test_environment.py` — deterministic identity, one-way receipt, sanitization, and incident-policy coverage.
- `experiments/specchoice-v1.3.2/README.md` — dependency boundary and no-endpoint/no-schema rationale.

## Decisions Made

- Standalone-first is the selected primary route. The incident is not triggered, and full UDB setup was not attempted.
- CPython and Git CLI implementation/version fields are canonical tool identities; timestamps, paths, host/platform details, commands, and event logs are audit-only.
- Ceiling exceedance stops environment expansion with `red_blocker` evidence; it does not reinterpret the standalone route as a fallback.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Sanitized embedded absolute-path fragments in audit values.**
- **Found during:** Task 2 final security scan
- **Issue:** A command or result string could contain an absolute path without being entirely an absolute-path value.
- **Fix:** Redact embedded absolute-path fragments as well as sensitive command arguments and sensitive mapping keys.
- **Files modified:** `src/specchoice_evidence/environment.py`, `tests/test_environment.py`
- **Verification:** Full 28-test experiment suite passes, including credential and embedded-path audit fixtures.
- **Committed in:** `4d998419`

---

**2. [Rule 1 - Tracking] Corrected plan-progress metadata after the state updater left front-matter progress at zero and phase labels as unknown.**
- **Found during:** Plan finalization
- **Issue:** The generated body showed 2/4 and 50%, but YAML `percent` remained `0` and newly added decisions were labelled `Phase ?`.
- **Fix:** Aligned the state front matter, activity text, and decision labels with the authoritative Plan 01 result.
- **Files modified:** `.planning/STATE.md`
- **Verification:** STATE front matter and body now both show 2/4 and 50%.

**Total deviations:** 2 auto-fixed issues (Rule 2 security hardening; Rule 1 tracking correction).
**Impact on plan:** Both changes preserve the required security and planning evidence without scope expansion.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 01-03 can use the stable environment-decision digest as an immutable Phase 1 input.
- The active boundary baseline remains `e8f7e153ffbc5285b361039153f8eea6205448e9f82e2b14efa9af3e74912e15`; the scoped `.DS_Store` policy stays visible and nonblocking only.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_environment -v` — 9 tests passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -v` — 28 tests passed.
- Two `record-environment` runs with different audit-only metadata produced byte-identical canonical decisions and the same SHA-256.
- `check-boundary` reported `blocking_violations: 0` against the active baseline.

## Self-Check: PASSED

- Required canonical decision, audit receipt, source module, CLI, README, and test file exist.
- All five implementation commits are present in Git history.
- Stub scan found no rendering placeholders, TODO/FIXME markers, or empty mock data in plan-created/modified files.

---
*Phase: 01-isolated-evidence-boundary-and-source-integrity*
*Completed: 2026-07-30*
