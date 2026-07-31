---
phase: 01-isolated-evidence-boundary-and-source-integrity
plan: 07
subsystem: source-custody
tags: [v7-lineage, local-acceptance, fixture-closure, offline-replay]
requires: [01-06]
provides: [accepted-pr2164-11-fixture-source, phase2-source-authority]
affects: [phase-02-input-authority]
tech-stack: [python-standard-library]
key-files:
  created:
    - experiments/specchoice-v1.3.2/bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v1/snapshot-manifest.json
    - experiments/specchoice-v1.3.2/phase2/source-authority.json
    - experiments/specchoice-v1.3.2/receipts/integrity-receipt-v8.json
  modified:
    - experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py
decisions:
  - V7 is the current boundary lineage; v5 and v6 remain explicit historical paths.
  - The v3 candidate remains immutable and ineligible; only its separate accepted tree is downstream eligible locally.
metrics:
  tasks_completed: 3
  test_count: 83
status: complete
---

# Phase 1 Plan 07: Local Accepted Fixture Closure Summary

The complete PR #2164 11-fixture source is now a separately rooted, local-only accepted v3 generation, bound to the canonical fixture registry for later Phase 2 consumption.

## Completed Tasks

1. Switched default boundary and receipt controls to immutable v7 lineage while retaining readable historical v5/v6 paths.
2. Created and independently verified `source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v1` under `bundles/accepted/`; the candidate tree was not modified.
3. Added the registry-bound `phase2/source-authority.json`, v8 local receipt, and a copied-bundle replay proof with no Git executable, Git objects, repository modules, network, or `PYTHONPATH`.

## Verification

- Full stdlib suite: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -q` — 83 passed.
- Accepted manifest SHA-256: `dd260724117c32bec5dac09fd3d3fc32665a942f2a60abf43a28176bb2f98cad`.
- Accepted root SHA-256: `bd3d88b022680068f4cd57b7926e8d97b69766077cae0d52402a717d70bf4851`.
- V8 integrity receipt SHA-256: `bdf98390c620b89ce978e35faf2acc85c101257917e27dc5a1f7225df939ccfc`.
- Copied replay: `env -i PATH=/nonexistent "$PYTHON_BIN" "$REPLAY_TMP/bundle/verify_bundle.py"` — passed.
- Current boundary: v7 baseline `b338372c74c605aa8b294ee30bcc39410422a6a5673e15061f86f28188debecb` — zero blocking violations.

## Local-only State

- Candidate manifest SHA-256 remains `155ec1fdfa4342ad0c3a36a9906fdbc3af6770aed324b5e9ccf5161350af9da7`, with `status: candidate` and `downstream_eligible: false`.
- Accepted v3 has `status: accepted`, `downstream_eligible: true`, `offline_replay_proven: true`, and `external_publication_authorized: false`.
- No push, PR, upload, publication, Phase 2 plan/context, evaluator, scoring, model call, or UDB setup occurred.

## Deviations from Plan

### Auto-fixed Issues

1. [Rule 1 - Bug] Preserved the fixture-registry artifact when re-rooting the accepted tree; omitting it caused the independent closure verifier to reject the bundle as containing an extra file.

## Self-Check: PASSED

The accepted manifest, source-authority pin, v8 JSON/Markdown receipt, and all referenced tests exist. `.DS_Store` files remain untracked and non-attributed.
