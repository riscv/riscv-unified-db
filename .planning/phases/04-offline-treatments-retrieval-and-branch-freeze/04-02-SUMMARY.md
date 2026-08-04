---
phase: 04-offline-treatments-retrieval-and-branch-freeze
plan: 02
subsystem: offline-treatment-contracts
tags: [python, canonical-json, sha256, prompt-contracts, offline]
requires:
  - phase: 04-01
    provides: Closed DelegationFrame parser and source-bound response contract.
provides:
  - Exact UTF-8/LF A/B/C prompt bytes with canonical manifest and offline accounting.
  - Test-only complete-pair corpus and isolated human contract-response fixtures.
affects: [04-03, retrieval-contract, 04-04, h3-red-freeze]
actuals:
  tokens: 24180
  tasks: 3
  commits: 6
tech-stack:
  added: []
  patterns: [descriptor-bound exact-resume publication, named-section diff allowlist, parser projection for fixture isolation]
key-files:
  created:
    - experiments/specchoice-v1.3.2/fixtures/treatments/contract-response-a-v1.json
    - experiments/specchoice-v1.3.2/fixtures/treatments/contract-response-b-v1.json
    - experiments/specchoice-v1.3.2/fixtures/treatments/contract-response-c-v1.json
    - experiments/specchoice-v1.3.2/prompts/treatments/prompt-bundle-manifest-v1.json
  modified:
    - experiments/specchoice-v1.3.2/src/specchoice_treatments/prompts.py
    - experiments/specchoice-v1.3.2/tests/test_treatments_prompts.py
key-decisions:
  - "Contract fixtures retain their isolation envelope and only their Wave 1 projection reaches the closed parser."
  - "Raw prompt bytes are authoritative; JSON canonicalisation is limited to fixtures and the manifest."
  - "A/B permit only frame/output differences, while B/C permit only the two-pair demonstration selection difference."
requirements-completed: [H1-01]
coverage:
  - id: D1
    description: Exact raw A/B/C prompt bundle, manifest hashes, counts, and bounded structural differences.
    requirement: H1-01
    verification:
      - kind: unit
        ref: tests/test_treatments_prompts.py#PromptBundleTests
        status: pass
      - kind: integration
        ref: tests/test_treatments_frame.py tests/test_canonical.py tests/test_filesystem_boundary.py
        status: pass
    human_judgment: false
  - id: D2
    description: Human-authored, test-only and non-counting contract response fixtures remain unusable as model or run evidence.
    requirement: H1-01
    verification:
      - kind: unit
        ref: tests/test_treatments_prompts.py#test_contract_responses_parse_and_remain_human_authored
        status: pass
      - kind: unit
        ref: tests/test_treatments_prompts.py#test_fixture_or_response_authority_escalation_is_rejected
        status: pass
    human_judgment: false
duration: multi-session continuation
completed: 2026-08-04
status: complete
---

# Phase 04 Plan 02: Offline Prompt Contract Bundle Summary

**Raw UTF-8/LF A/B/C prompt bytes, isolated human contract responses, and a fail-closed canonical manifest for the Red offline branch.**

## Accomplishments

- Retained the corrected complete-pair payload and ranked C selection: A/B select `SYNTH_PAIR_ALPHA`, `SYNTH_PAIR_BETA`; C selects `SYNTH_PAIR_ALPHA`, `SYNTH_PAIR_GAMMA` from the score-bearing receipt.
- Added canonical human contract responses. Each is `origin=contract_fixture`, `model_generated=false`, `test_only=true`, and `count_eligible=false`; only its closed Wave 1 projection is parsed.
- Published A/B/C raw bytes and canonical manifest via `write_exact_descriptor_files`, permitting byte-identical resume while rejecting partial, divergent, or unsafe output destinations.
- Enforced named-section diffs: A↔B is exactly `frame_instructions`, `output_schema`; B↔C is exactly `demonstrations`. Reordering, padding, unequal demonstrations, and unrelated drift fail closed.

## Artifact Identities

| Artifact | SHA-256 | Accounting |
| --- | --- | --- |
| Contract | `f44b88a903bc177801cce5f8880f7bb518365a6fc737c4e2246d7c9b5565020c` | canonical JSON |
| Target source | `326b6a1274252ca7a69ceff68685f6b3f4e5067eacd83411b9fcfceff77da2c4` | raw source bytes |
| Complete-pair corpus | `d71740c08cd3955f8106c5ad43d4b6216179f1562268b534ad43a69e2ac9efb1` | canonical JSON |
| Prompt A | `e1fd43004b695d6d859fc174443cf106f70a0f34e3a252046b4d63f558a5f8d5` | 6110 bytes, 6110 code points, 31 LF lines, 547 lexical tokens |
| Prompt B | `15e59c817a87adbe1bfb5d8275781ea9d4072606c25314f17da4349f0c2a0e9c` | 6567 bytes, 6567 code points, 40 LF lines, 611 lexical tokens |
| Prompt C | `c212d652f97b40a34d48a92ab453852a24def823198418ad00ea79b9270bd4b0` | 6576 bytes, 6576 code points, 40 LF lines, 611 lexical tokens |
| Response A | `9e0052cb5b261e8ad221b4772ae83004fdc96cf62001e5f7d336f2f5df65cb63` | canonical fixture JSON |
| Response B | `2f52efe839f5eaedcd2ba383a409a3ad5e339568d490726f25147a0a2f0912b3` | canonical fixture JSON |
| Response C | `496cb70e94bf96faf8d873ad44086999a3309519a2e72d0ea77042338a3015a1` | canonical fixture JSON |
| Bundle manifest | `b44dee82b7473ebcbe0a3410649b60da75ed21232fd59bf3a59537b7ca1b67e4` | canonical JSON |

All provider token fields are the literal `not_applicable_red`; no provider, model, network, credential, or CLI surface was added.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_treatments_prompts tests.test_treatments_frame tests.test_canonical tests.test_filesystem_boundary -q` — 48 passed.
- Independently recomputed manifest self-hash and each prompt SHA-256, byte count, Unicode code-point count, LF-line count, and frozen `re.findall(r"(?u)\b\w+\b", ...)` count — passed.
- The broader Wave 2 unittest command completed twice without a non-zero status, but its tool session did not return stdout; the focused task/predecessor/canonical/filesystem suite above is the retained explicit evidence.

## Task Commits

1. **Task 1: Render one complete named-section A/B/C bundle in memory** — `51b17f4a`, `7e2fb29c`, `0b97d9b5`, `9c391548`.
2. **Task 2: Freeze complete-pair and human contract-response isolation** — `f0130745`.
3. **Task 3: Publish exact prompt bytes, allowlisted diffs, hashes, and offline counts** — `17a85ef2`.

## Deviations from Plan

### Auto-fixed Issues

1. **[Rule 1 - Bug] Preserved canonical payload corrections in the tracer boundary**
   - **Found during:** Task 1
   - **Fix:** Kept the corrected `not_surfaced` encoding, source-vs-record hash split, score-bearing C ranking receipt with tie-breaking validation, complete pair `final_status` labels, and fixed corpus binding.
   - **Committed in:** `0b97d9b5`, `9c391548`.

**Total deviations:** 1 corrective preservation. No scope expansion.

## Issues Encountered

- Ruff is not installed in the execution environment (`RUFF_UNAVAILABLE`), so that optional static check was not run. Python unit coverage and independent raw-byte recomputation passed.

## Known Stubs

None.

## Next Phase Readiness

Wave 3 can consume only the committed synthetic target/corpus and score-bearing C receipt to prove deterministic test-only retrieval. The bundle remains strictly offline and non-authoritative for model or experiment-run evidence.

## Self-Check: PASSED

- All 14 plan artifacts exist at their declared paths.
- All six task commits are present in Git history.

---
*Phase: 04-offline-treatments-retrieval-and-branch-freeze*
*Completed: 2026-08-04*
