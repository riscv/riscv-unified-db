---
phase: 02-deterministic-measurement-spine
plan: 09
subsystem: source-evidence-custody
tags: [filesystem, descriptor-rooted, custody, expected-red]
requires: [02-08]
provides: [descriptor-bound-source-consumers, expected-red-semantic-gate]
affects: [phase2-source-authority, fixture-closure-acceptance]
tech-stack:
  added: []
  patterns: [stdlib-dirfd-reading, canonical-byte-reuse, closed-test-partition]
key-files:
  created:
    - experiments/specchoice-v1.3.2/tests/phase1_expected_red_oracle.py
  modified:
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/filesystem.py
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/verify.py
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/bundle.py
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py
    - experiments/specchoice-v1.3.2/tests/test_filesystem_boundary.py
    - experiments/specchoice-v1.3.2/tests/test_bundle_verifier.py
    - experiments/specchoice-v1.3.2/tests/test_fixture_closure.py
decisions:
  - Candidate controls and Phase 2 source-authority receipt reuse descriptor-bound canonical bytes instead of reopening pathname leaves.
  - The Phase 1 expected-red baseline is a non-discovered gate with a fixed 66/141/136 partition.
metrics:
  duration: 32m
  completed: 2026-08-02
status: complete
---

# Phase 02 Plan 09: Descriptor-rooted source custody summary

Every active source verifier and Phase 2 authority receipt now derives control and bundle bytes from descriptor-held reads, while an exact semantic gate pins the five expected-red Phase 1 methods.

## Tasks Completed

1. Descriptor-rooted public tracer — `18bda2e5`, `ebaa3f3d`
2. Candidate, acceptance, CLI, and expected-red closure — `7af430a9`

## Verification

- The four Task 1 race regressions pass against root, intermediate, regular-leaf/FIFO, and closure rebind classes.
- Task 2’s two public regressions pass.
- `py_compile` passes for the touched modules and oracle.
- `phase1_expected_red_oracle.py --expected-focused 66 --expected-discovered 141 --expected-green 136` completes the closed partition gate.
- Protected-root comparison against baseline `79a6da9d` is empty for accepted bundles, receipts, Phase 2 authority, baselines, config, `spec/`, `gen/`, and Phase 1 planning.

## Key Decisions

- Candidate verification now uses descriptor-scoped tree enumeration rather than a pathname `os.walk` pass.
- Phase 2 authority validation emits one canonical closed receipt from the verified bundle leaves.
- The oracle keeps diagnostics on stderr and uses binary-safe temporary streams for unittest execution.

## Deviations from Plan

None - plan executed exactly as written.

## Protected Path Gate

Baseline: `79a6da9d` (the 02-08 predecessor trust anchor).

The exact protected-root diff is empty. No accepted-v1/v2 bytes, prior receipts, active authority, baselines, policy/config, `spec/`, or generated outputs changed.

## Self-Check: PASSED

- Required source modules and the oracle exist.
- Task commits `18bda2e5`, `ebaa3f3d`, and `7af430a9` exist.
