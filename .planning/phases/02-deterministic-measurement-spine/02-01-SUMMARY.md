---
phase: 02-deterministic-measurement-spine
plan: 01
subsystem: deterministic-measurement-adapter
tags: [ts-03, accepted-v2, pr-2164, canonical-json, fail-closed]
requires: [phase2-source-authority, accepted-v2-fixture-bundle]
provides: [canonical-pr2164-adapter-batch, adapter-closure-gate]
affects: [02-02, 02-03, 02-04, 02-05]
tech-stack:
  added: [python-standard-library]
  patterns: [accepted-authority-before-semantic-read, bounded-yaml-reader, immutable-canonical-output]
key-files:
  created:
    - experiments/specchoice-v1.3.2/config/measurement/pr2164-adapter-rules-v1.json
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/__init__.py
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/domain.py
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/adapter.py
    - experiments/specchoice-v1.3.2/src/specchoice_measurement/cli.py
    - experiments/specchoice-v1.3.2/tests/test_measurement_adapter.py
  modified: []
decisions:
  - Adapter authority is delegated to the existing Phase 1 source-authority CLI and accepted-bundle verifier; Phase 2 does not duplicate custody policy.
  - Score eligibility is one finite, ordered 11-fixture and 28-raw-file batch with one adapter version and rule SHA-256; invalid batches expose diagnostics but no records.
requirements-completed: [TS-03]
coverage:
  - id: D1
    description: "Accepted-v2-only versioned PR #2164 adapter, domain records, canonical rules, and adapt-pr2164 CLI tracer."
    requirement: TS-03
    verification:
      - kind: unit
        ref: "experiments/specchoice-v1.3.2/tests/test_measurement_adapter.py#test_accepted_v2_builds_the_complete_canonical_partition"
        status: pass
      - kind: integration
        ref: "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m specchoice_evidence.cli validate-phase2-source-authority --authority phase2/source-authority.json --bundle bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"
        status: pass
    human_judgment: false
  - id: D2
    description: "Fail-closed complete-batch closure diagnostics, source rejection, and no-replace canonical output policy."
    requirement: TS-03
    verification:
      - kind: unit
        ref: "experiments/specchoice-v1.3.2/tests/test_measurement_adapter.py#test_incomplete_duplicate_reordered_and_mixed_batches_have_all_blockers_and_no_records"
        status: pass
      - kind: unit
        ref: "experiments/specchoice-v1.3.2/tests/test_measurement_adapter.py#test_adapter_preserves_authoritative_bytes_and_refuses_output_overwrite"
        status: pass
    human_judgment: false
metrics:
  duration: 7m
  tasks_completed: 2
  test_count: 5
  completed_date: 2026-07-31
status: complete
---

# Phase 2 Plan 01: Accepted-v2 PR #2164 Adapter Summary

The deterministic adapter converts only the active accepted verifier-rooted v2 bundle into one canonical, hash-bound 11-fixture batch, while exposing no records whenever provenance or complete-batch closure fails.

## Completed Tasks

1. Added the `specchoice_measurement` domain, canonical rules, bounded PR #2164 YAML reader, and `adapt-pr2164` CLI tracer. Every raw file is checked through the Phase 1 regular-file API against its registry path, length, and SHA-256 before semantic decoding.
2. Added complete-batch closure validation: unique sorted fixture IDs, the exact 11/28 universe, single adapter/rule/source identity, deterministic diagnostics, candidate 0-name semantics, rejected historical/candidate authority, and no-replace output handling.

## Verification

- `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_measurement_adapter -q` — 5 passed.
- `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m specchoice_evidence.cli validate-phase2-source-authority --authority phase2/source-authority.json --bundle bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2` — valid exact 11/28 accepted-v2 authority.
- Equivalent CLI runs produced the same canonical batch bytes and `adapter_batch_sha256` `86fcdba7906ab5158fd31b92bd673976e9ffcfd5903b0521e083264173276494`.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m compileall -q src/specchoice_measurement` and `git diff --check` passed.

## TDD Gate Compliance

- RED: `d53fbdff` and `2326ef2e` recorded failing adapter tracer and closure-matrix tests before their implementations existed.
- GREEN: `bbc30a6e` and `e07884bf` implemented the tracer and closure gates; the focused suite passes.

## Deviations from Plan

None - plan executed as written. The bounded reader treats observed nested YAML as immutable provenance and only interprets the declared score-bearing top-level fields.

## Security / Trust Surface

No new network, provider, model, publication, core-UDB, or Phase 1 custody surface was introduced. The new local CLI writes only a caller-supplied path that does not already exist.

## Self-Check: PASSED

All six declared task artifacts exist; task commits `d53fbdff`, `bbc30a6e`, `2326ef2e`, and `e07884bf` exist; focused verification passed. No stubs, skipped tests, or unrun verification remain. Pre-existing `.DS_Store` paths and the orchestration-owned `STATE.md` remain unstaged.
