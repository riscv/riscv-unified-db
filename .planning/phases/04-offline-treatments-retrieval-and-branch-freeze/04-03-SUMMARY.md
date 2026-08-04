---
phase: 04-offline-treatments-retrieval-and-branch-freeze
plan: 03
subsystem: offline-retrieval-contract
tags: [python, offline, retrieval, tf-idf, cosine, filesystem-boundary]
requires:
  - phase: 04-02
    provides: Canonical test-only target, complete-pair corpus, and explicit prompt C selection.
provides:
  - Descriptor-bound singleton CLI for deterministic test-only complete-pair retrieval.
  - Closed TF-IDF/cosine ranking with zero-score ties, recursive authority-field rejection, and no network surface.
affects: [04-04, h3-red-freeze]
tech-stack:
  added: []
  patterns: [descriptor-bound reads, canonical JSON output, standard-library TF-IDF/cosine, exact error codes]
key-files:
  created: []
  modified:
    - experiments/specchoice-v1.3.2/src/specchoice_treatments/__init__.py
    - experiments/specchoice-v1.3.2/src/specchoice_treatments/retrieval.py
    - experiments/specchoice-v1.3.2/src/specchoice_treatments/cli.py
    - experiments/specchoice-v1.3.2/src/specchoice_treatments/prompts.py
    - experiments/specchoice-v1.3.2/config/treatments/lexical-retrieval-contract-v1.json
    - experiments/specchoice-v1.3.2/reports/h3/test-only-retrieval-contract-v1.json
    - experiments/specchoice-v1.3.2/tests/test_treatments_retrieval.py
key-decisions:
  - "The retrieval command remains a four-explicit-input, descriptor-bound test-only verifier; no ambient manifest default is permitted."
  - "Pair member order is non-authoritative: full-precision cosine then pair_id produces stable top-two output, including zero-score ties."
  - "The H2-02 unclassified probe remains an explicit flagged assumption: a non-empty target and at least two distinct complete pair IDs are required by the test contract."
actuals:
  tokens: 12639
  tasks: 2
  commits: 5
duration: multi-session continuation
completed: 2026-08-04
status: complete
---

# Phase 04 Plan 03: Offline Retrieval Contract Summary

**A descriptor-bound, standard-library TF-IDF/cosine verifier ranks exactly two isolated synthetic pairs with deterministic zero/tie behavior and no production or network entry point.**

## Accomplishments

- Delivered the sole `verify-retrieval-contract` CLI surface with four explicit relative inputs: target, corpus, config, and prompt manifest. Its successful stdout is canonical JSON; invalid parser, path, authority, and isolation inputs return exit code 2 before ranking.
- Bound the report to distinct config, target file/record/source, corpus file/content, and prompt-manifest identities. The target `source_text` remains the sole query text and the selected IDs must match prompt C.
- Closed D-08 boundaries: two complete pairs are always returned without a similarity threshold, zero cosine scores are retained, exact full-precision ties resolve by ascending `pair_id`, and corpus member order cannot affect output.
- Rejected empty/null targets, all recursive D-07 authority/ranking fields, non-test/count-eligible roots and items, duplicate IDs, incomplete sides, Phase 3 authority/candidate inputs, absolute/traversal/symlink paths, and unknown execution-like commands.
- Proved no network calls around successful or rejected CLI paths by patching socket primitives; AST import checks also exclude network, provider-SDK, and credential-library dependencies from the retrieval boundary.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_treatments_retrieval tests.test_treatments_prompts tests.test_treatments_frame tests.test_canonical tests.test_filesystem_boundary -q` — 62 passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -q` — completed successfully. `VERIFIER_ARTIFACT_TAMPERED` is expected output from the copied-verifier tampering rejection test.
- `git diff --check` — passed.
- Ruff was unavailable in the environment (`RUFF_UNAVAILABLE`); no dependency was installed.

## Task Commits

1. **Task 1: Rank one synthetic target through the sole CLI to two whole pairs** — `93958108`, `9824ab0e`, `9f5547b8`, `fa280d54`.
2. **Task 2: Close zero/tie/insufficient/leakage boundaries and prove no production reachability** — `18a304c4`.

## Deviations from Plan

### Auto-fixed Issues

1. **[Rule 1 - Bug] Made equivalent corpus member order non-authoritative**
   - **Found during:** Task 2
   - **Issue:** The tracer rejected an otherwise identical reversed pair list before tie ordering could run, contradicting the frozen input-order determinism contract.
   - **Fix:** Retained duplicate detection but removed input-list sort enforcement; ranking still sorts full-precision scores and `pair_id`.
   - **Files modified:** `experiments/specchoice-v1.3.2/src/specchoice_treatments/retrieval.py`, `experiments/specchoice-v1.3.2/tests/test_treatments_retrieval.py`
   - **Commit:** `18a304c4`

2. **[Rule 1 - Bug] Normalized parser failures to the CLI exit-2 contract**
   - **Found during:** Task 2
   - **Issue:** Unknown commands raised `SystemExit` to in-process callers rather than returning the CLI's documented code.
   - **Fix:** `main()` now returns argparse's exit code while retaining argparse's canonical stderr.
   - **Files modified:** `experiments/specchoice-v1.3.2/src/specchoice_treatments/cli.py`, `experiments/specchoice-v1.3.2/tests/test_treatments_retrieval.py`
   - **Commit:** `18a304c4`

## Known Stubs

None.

## Scope Confirmation

No provider, model, network, credential, production retrieval, H3, or Wave 4 surface was added. The committed report remains test-only and count-ineligible; it is not H2, model, or experiment evidence.

## Self-Check: PASSED

- All retrieval, CLI, config, report, and test artifacts exist at their declared paths.
- All five Task 1/Task 2 commits are present in Git history.

---
*Phase: 04-offline-treatments-retrieval-and-branch-freeze*
*Completed: 2026-08-04*
