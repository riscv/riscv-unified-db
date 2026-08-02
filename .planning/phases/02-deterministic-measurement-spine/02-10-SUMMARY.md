---
phase: 02-deterministic-measurement-spine
plan: 10
subsystem: source-custody
tags: [fixture-closure, candidate, verifier-rooted-v3, offline-replay]
requires:
  - phase: 02-09
    provides: descriptor-rooted candidate construction and expected-red gate
provides:
  - Human-authorized, proposal-bound v3 candidate construction decision
  - Immutable v3 candidate with hardened embedded verifier and copied-isolation audit
affects: [02-11, source-authority, local-acceptance]
tech-stack:
  added: []
  patterns: [closed proposal-decision binding, candidate-only construction, copied-isolation replay]
key-files:
  created:
    - experiments/specchoice-v1.3.2/receipts/source-contract-decision-v3-pr2164-fixture-closure-verifier-rooted-v3.json
    - experiments/specchoice-v1.3.2/receipts/fixture-closure-candidate-audit-v3.json
    - experiments/specchoice-v1.3.2/bundles/candidates/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v3/snapshot-manifest.json
  modified:
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/bundle.py
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py
    - experiments/specchoice-v1.3.2/tests/test_fixture_closure.py
key-decisions:
  - "The explicit user authorization is bound only to proposal SHA-256 2bbaa0a4ba3a4abd298b45b85c1e05950020a00ffd47bd10e1b89b8d09eb815b and fixed source bf91185887590799e76a3077ca03fd7f319e88e2."
  - "The v3 bundle remains candidate-only, downstream-ineligible, and externally unpublished; no local acceptance or authority cutover occurred."
metrics:
  duration: 1h
  completed: 2026-08-02
status: complete
requirements-completed: [TS-03, TS-04, TS-05]
coverage:
  - id: D1
    description: Exact proposal-bound human construction decision validates through the dedicated public CLI.
    requirement: TS-03
    verification:
      - kind: unit
        ref: tests/test_source_contract.py#test_v3_fixture_construction_decision_binds_exact_proposal_and_source
        status: pass
    human_judgment: false
  - id: D2
    description: Candidate-only v3 source bundle has fresh identities, unchanged raw custody, and copied-isolation replay.
    requirement: TS-04
    verification:
      - kind: integration
        ref: specchoice_evidence.cli validate-fixture-candidate-v3
        status: pass
    human_judgment: false
---

# Phase 02 Plan 10: Verifier-rooted v3 candidate summary

The exact authorized v3 fixture candidate is now immutable and independently replay-verified, while active v2 authority and all acceptance/publication states remain unchanged.

## Accomplishments

- Recorded the explicit `authorize` decision with the exact proposal hash, generation, and fixed-source commit; decision receipt SHA-256: `e5fbfde1380a9194779b0e72218c9a33dab6345f41d325223630c8b63afbd0b2`.
- Built `source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v3` as `status: candidate`, `downstream_eligible: false`, and `external_publication_authorized: false`.
- Bound all 28 raw artifacts, the 11-fixture 6/4/1 registry partition, four measurement controls, five embedded verifier artifacts, and a copied-isolation replay in audit SHA-256 `e9c2c37821186bf4c4179872e846ab8e6781c74ad38f073cec2690c063e109fd`.

## Verification

- Dedicated construction-decision validator passed with `construction_authorized: true`.
- Reworked source-contract and candidate-custody unit tests passed; candidate validation passed through `validate-fixture-candidate-v3`.
- A disposable copied bundle ran only `verify_bundle.py` with `PYTHONPATH` absent, `PATH=/nonexistent`, repository modules unavailable, and the original bundle outside the replay root.
- `tests/phase1_expected_red_oracle.py --expected-focused 66 --expected-discovered 141 --expected-green 136` exited `0`.
- Exact protected-path comparison from `bf91185887590799e76a3077ca03fd7f319e88e2` found no change in accepted bundles, active authority, registry, controls, golden/adversarial evidence, or local-acceptance receipt.

## Task Commits

1. Task 1 — `2dbfd23a` (`feat`): emitted the closed verifier-rooted-v3 proposal and dedicated decision validator.
2. Task 2 — `0b291edb` (`feat`): recorded the user-authorized, exact proposal-bound construction decision.
3. Task 3 — `0ab0f938` (`feat`): constructed and audited the immutable, ineligible v3 candidate.

## Key Identities

- Core SHA-256: `a3f9f570412f7b4851b6cf31906516cdcf4d29b9bf77b5494cd68b0e073ace08`
- Snapshot manifest SHA-256: `c917d0228ab9053032951a0d2d2c0f13a33ccc7e34b6575121f7b995ed38dc83`
- Root SHA-256: `4ead0825002c60eca58070d3104c59dbfa58a3d184f6f81a70b18be7e94677c5`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected an incomplete proposal digest during decision materialization**

- **Found during:** Task 2 validation.
- **Issue:** The first local serialization omitted two characters from the exact proposal SHA-256 and correctly failed closed.
- **Fix:** Replaced it with the independently verified proposal digest before validation and commit.
- **Files modified:** `source-contract-decision-v3-pr2164-fixture-closure-verifier-rooted-v3.json`.
- **Verification:** Dedicated validator returned `decision_valid` and `construction_authorized: true`.
- **Commit:** `0b291edb`.

**Total deviations:** 1 auto-fixed (Rule 1). **Impact:** No candidate existed before the corrected, successful validation.

## Known Stubs

None. Three literal `TODO` values in copied frozen gold YAML are preserved authoritative raw input, not executable or UI placeholders.

## Self-Check: PASSED

- Required proposal, decision, candidate manifest, and audit files exist.
- Task commits `2dbfd23a`, `0b291edb`, and `0ab0f938` exist.
- The exact 66/141/136 phase gate passed with exit code `0`.
