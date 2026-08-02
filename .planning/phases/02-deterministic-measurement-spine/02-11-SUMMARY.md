---
phase: 02-deterministic-measurement-spine
plan: 11
subsystem: source-custody
tags: [local-acceptance, accepted-v3, pending-cutover, descriptor-custody]
requires:
  - phase: 02-10
    provides: verifier-rooted v3 candidate and copied-isolation audit
provides:
  - Explicit hash-bound local acceptance for the reviewed v3 candidate
  - Immutable accepted v3 bundle with a reviewed, non-effective pending cutover
  - Historical v2 authority preserved byte-for-byte while active v2 remains eligible
affects: [02-12, 02-13, 02-16, source-authority]
tech-stack:
  added: []
  patterns: [descriptor-held source inventory, non-effective transition validation, versioned local acceptance]
key-files:
  created:
    - experiments/specchoice-v1.3.2/receipts/local-acceptance-v10.json
    - experiments/specchoice-v1.3.2/bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v3
    - experiments/specchoice-v1.3.2/phase2/source-authority-v10-pending.json
    - experiments/specchoice-v1.3.2/receipts/pending/fixture-closure-transition-v2-to-v3.json
  modified:
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/bundle.py
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py
    - experiments/specchoice-v1.3.2/tests/test_fixture_closure.py
key-decisions:
  - "The user's explicit accept is recorded under a non-personal independent-local-reviewer role, remains local-only, and grants no external publication authority."
  - "Accepted v3 is staged from descriptor-held candidate bytes; the v10 transition stays non-effective until the explicit Wave 16 cutover."
patterns-established:
  - "Pending source cutovers validate future authority bytes while reporting eligible: false and requiring canonical revocation absence."
requirements-completed: [TS-03, TS-04, TS-05]
coverage:
  - id: D1
    description: Hash-bound local v3 acceptance decision validates through the public read-only CLI.
    requirement: TS-03
    verification:
      - kind: integration
        ref: specchoice_evidence.cli validate-local-acceptance-decision-v10
        status: pass
    human_judgment: false
  - id: D2
    description: Accepted v3 and its non-effective pending authority/transition validate without changing active v2.
    requirement: TS-04
    verification:
      - kind: integration
        ref: specchoice_evidence.cli verify-accepted and validate-pending-source-cutover-v10
        status: pass
    human_judgment: false
  - id: D3
    description: The expected-red partition remains fixed at 66 focused, 143 discovered, and 138 green tests.
    requirement: TS-05
    verification:
      - kind: integration
        ref: tests/phase1_expected_red_oracle.py --expected-focused 66 --expected-discovered 143 --expected-green 138
        status: pass
    human_judgment: false
metrics:
  duration: 1h
  completed: 2026-08-02
status: complete
---

# Phase 02 Plan 11: Local v3 acceptance and pending cutover summary

**A human-approved, hash-bound v3 successor is accepted locally with a verified non-effective v10 transition, while active v2 remains byte-identical, eligible, and unrevoked.**

## Performance

- **Duration:** 1h
- **Completed:** 2026-08-02T09:11:55Z
- **Tasks:** 3/3
- **Files modified:** 47

## Accomplishments

- Confirmed Task 1 commit `bab35259` and request SHA-256 `5b40bbc4c5bb8f19488139845129fcaa4945d62e330e6f35727c71582cf64cf2`; recorded the user's explicit `accept` in decision SHA-256 `dcb0fb1fdec27c4095be5a31f69cb4b305b8f2dd0ec43d1642ab34d7879a51c5` without attributing a named individual.
- Created accepted `source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v3` with reviewed core/root identities `a3f9f570...` / `4ead0825...`, staged from descriptor-held candidate inventory rather than `copytree` reopening.
- Preserved active v2 and `source-authority-v9-historical.json` at the identical SHA-256 `6943ae60b5a22b4cc262bbcc0c252fbd9a31e5e5cbaac9f79976087b63a4ce23`; pending authority is `e1681a34...`, transition is `472bc062...`, and canonical revocation remains absent.

## Verification

- `validate-local-acceptance-decision-v10` returned `local_acceptance_decision_valid` with decision `accept` and the exact request hash.
- The two disposable public acceptance/copy-isolation tests passed.
- `verify-accepted` passed; `validate-pending-source-cutover-v10` returned `pending_cutover_valid_non_effective` and `eligible: false`.
- Historical v2 validated as inspection-only with `eligible: false`; active v2 validated as `eligible: true` with no canonical revocation.
- `phase1_expected_red_oracle.py --expected-focused 66 --expected-discovered 143 --expected-green 138` exited 0.
- Protected controls remained unchanged from `bf91185887590799e76a3077ca03fd7f319e88e2`.

## Task Commits

1. **Task 1: Prove v3 acceptance and non-effective pending cutover in disposable public trees** — `bab35259` (feat)
2. **Task 2: Independently author local acceptance** — `2bc39fa8` (feat)
3. **Task 3: Publish accepted v3 and stage a non-effective reviewed cutover** — `fe7914cc` (feat)

## Decisions Made

- The explicit human response was materialized as a local-only `accept` decision under the generic role `independent-local-reviewer`; it authorizes neither named-person attribution nor publication.
- The only real v3 materialization path reads the complete candidate inventory through no-follow descriptors, holds bytes in memory, then verifies and publishes the fresh accepted directory without source `copytree`.
- The v10 authority and transition are reviewable but explicitly non-effective; only Plan 02-16 may write canonical revocation or replace active authority.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Registered the required public local-acceptance decision validator.**
- **Found during:** Task 2
- **Issue:** The documented `validate-local-acceptance-decision-v10` command was not present in the CLI parser.
- **Fix:** Added a canonical, read-only CLI route and covered it inside the existing disposable acceptance test.
- **Files modified:** `src/specchoice_evidence/cli.py`, `tests/test_fixture_closure.py`
- **Committed in:** `2bc39fa8`

**2. [Rule 1 - Bug] Replaced real-v3 candidate `copytree` with descriptor-held inventory staging.**
- **Found during:** Task 3
- **Issue:** The v10 acceptance path reopened and copied candidate paths after validation, contradicting the plan's anti-substitution custody boundary.
- **Fix:** Held every candidate leaf through no-follow descriptor reads, wrote only those held bytes into staging, then revalidated staging before no-replace publication.
- **Files modified:** `src/specchoice_evidence/bundle.py`
- **Committed in:** `fe7914cc`

**3. [Rule 1 - Bug] Registered the required public non-effective pending-cutover validator.**
- **Found during:** Task 3
- **Issue:** The plan's `validate-pending-source-cutover-v10` verification command was not available.
- **Fix:** Added the read-only validator, including active-v2 hash binding, transition projection checks, and canonical-revocation absence; covered it in the existing disposable flow.
- **Files modified:** `src/specchoice_evidence/cli.py`, `tests/test_fixture_closure.py`
- **Committed in:** `fe7914cc`

**Total deviations:** 3 auto-fixed (Rule 1). **Impact:** All changes close documented verification and custody requirements without changing active authority or expanding publication scope.

## Known Stubs

None. The three literal `TODO` values in copied accepted raw gold YAML are frozen authoritative input, not executable or UI placeholders.

## Issues Encountered

The first Task 2 validation exposed missing public CLI registration; it was corrected before acceptance materialization. Git staging required the repository's approved local Git write permission.

## User Setup Required

None — all actions were local-only and no service, credential, network, model/API, deployment, or publication operation was used.

## Next Phase Readiness

Plans 02-12 and 02-13 may consume the verified pending authority only as non-effective evidence. Active v2 stays authoritative until the explicitly deferred 02-16 cutover.

## Self-Check: PASSED

- Required acceptance, accepted-v3, historical, pending, and transition artifacts exist.
- Task commits `bab35259`, `2bc39fa8`, and `fe7914cc` exist.
- Active v2 remains byte-identical to its historical copy.

---
*Phase: 02-deterministic-measurement-spine*
*Completed: 2026-08-02*
