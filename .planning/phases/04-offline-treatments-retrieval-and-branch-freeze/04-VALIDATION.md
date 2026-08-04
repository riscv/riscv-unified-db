---
phase: 4
slug: offline-treatments-retrieval-and-branch-freeze
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false)
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-08-04
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python 3.14.5 standard-library `unittest` |
| **Config file** | none — existing tests run with `PYTHONPATH=src` |
| **Quick run command** | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_treatments_frame tests.test_treatments_prompts tests.test_treatments_retrieval tests.test_treatments_h3 -q` |
| **Full suite command** | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_data_admission tests.test_data_splits tests.test_data_relevance tests.test_data_h2 tests.test_treatments_frame tests.test_treatments_prompts tests.test_treatments_retrieval tests.test_treatments_h3 tests.test_canonical tests.test_filesystem_boundary -q && ruff check --isolated src/specchoice_treatments tests/test_treatments_frame.py tests/test_treatments_prompts.py tests/test_treatments_retrieval.py tests/test_treatments_h3.py` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run the wave-specific new `unittest` module plus `tests.test_canonical` and, for file-writing work, `tests.test_filesystem_boundary`.
- **After every plan wave:** Run the cumulative command declared in that wave's PLAN; the terminal full suite above is required after Wave 4.
- **Before `$gsd-verify-work`:** Full suite, Ruff, and `git diff --check` must be green.
- **Max feedback latency:** 10 seconds.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | H1-01 | T-04-01 | Strict UTF-8/duplicate-key/exact-key validation rejects malformed A/B/C frame records and verifies verbatim source spans. | unit/adversarial | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_treatments_frame tests.test_canonical -q` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | H1-01 | T-04-01 | B/C accept exactly three frozen axes including `unknown`; A has no frame; advisory output is stable and non-blocking. | unit | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_treatments_frame -q` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 2 | H1-01 | T-04-02 | Closed named sections render complete in-memory A/B/C prompts from one non-empty test-only target, with exact frame/shared-section and UTF-8/LF boundaries. | unit/tracer | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_treatments_prompts.PromptBundleTests.test_named_section_tracer_renders_three_systems tests.test_treatments_prompts.PromptBundleTests.test_frame_and_shared_sections_are_exact tests.test_treatments_prompts.PromptBundleTests.test_target_and_raw_text_boundaries_fail_closed -q` | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 2 | H1-01 | T-04-02 | Synthetic target/pairs/responses remain `test_only`, `count_eligible=false`, and contract responses cannot be represented as model/run evidence. | adversarial | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_treatments_prompts.PromptBundleTests.test_three_complete_pairs_and_two_pair_selections tests.test_treatments_prompts.PromptBundleTests.test_contract_responses_parse_and_remain_human_authored tests.test_treatments_prompts.PromptBundleTests.test_fixture_or_response_authority_escalation_is_rejected -q` | ❌ W0 | ⬜ pending |
| 04-02-03 | 02 | 2 | H1-01 | T-04-02 | Raw UTF-8/LF prompts, canonical response/manifest hashes, allowlisted treatment diffs, exact offline counts, and exact-resume publication reproduce byte-for-byte. | unit/integration | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_treatments_prompts tests.test_treatments_frame tests.test_canonical tests.test_filesystem_boundary -q` | ❌ W0 | ⬜ pending |
| 04-03-01 | 03 | 3 | H2-02 | Target-only TF-IDF/cosine returns exactly two complete pairs in score-descending, `pair_id`-ascending order, including zero-score ties. | unit | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_treatments_retrieval -q` | ❌ W0 | ⬜ pending |
| 04-03-02 | 03 | 3 | H2-02 | Fewer than two pairs, non-test inputs, incomplete pairs, authority/gold/frame leakage, and Phase 3 corpus reuse fail before ranking with no partial result. | integration/security | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_treatments_retrieval tests.test_filesystem_boundary -q` | ❌ W0 | ⬜ pending |
| 04-04-01 | 04 | 4 | TS-10 | T-04-04 | H3 recomputes exact Phase 3/4 bindings, embeds the complete freeze/no-model audit, and emits machine-only decision-free Red packet/readiness. | integration/security | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_treatments_h3.H3ContractTests.test_machine_readiness_recomputes_phase3_and_phase4_roots tests.test_treatments_h3.H3ContractTests.test_freeze_inventory_is_complete_sorted_and_content_bound tests.test_treatments_h3.H3ContractTests.test_no_model_reachability_is_static_and_runtime tests.test_data_h2 -q` | ❌ W0 | ⬜ pending |
| 04-04-02 | 04 | 4 | TS-10 | T-04-04 | A separate complete human decision binds exact packet/readiness; machine readiness cannot infer `approved_red`, and disputed/incomplete remains non-authorizing. | manual/unit | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_treatments_h3.H3ContractTests.test_missing_payload_differs_from_complete_incomplete_decision tests.test_treatments_h3.H3ContractTests.test_human_decision_binds_exact_packet_and_readiness tests.test_treatments_h3.H3ContractTests.test_machine_never_infers_approved_red -q` | ❌ W0 | ⬜ pending |
| 04-04-03 | 04 | 4 | TS-10 | T-04-04 | Approved-red-only authority fixes `N_strict=0`, `repeat_count=0`, `h4_required=false`, and all no-provider/no-model fields; drift, unsafe resume, H4 escalation, forbidden imports/commands, or network activity fail closed. | adversarial/security/runtime | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_treatments_h3 tests.test_filesystem_boundary tests.test_data_h2 -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `experiments/specchoice-v1.3.2/tests/test_treatments_frame.py` — H1-01 strict frame, span, A/B/C, and advisory coverage.
- [ ] `experiments/specchoice-v1.3.2/tests/test_treatments_prompts.py` — raw prompt, hash, allowlisted diff, count, and contract-response isolation coverage.
- [ ] `experiments/specchoice-v1.3.2/tests/test_treatments_retrieval.py` — H2-02 target-only pair ranking, zero/tie/insufficient, CLI, and test-only boundary coverage.
- [ ] `experiments/specchoice-v1.3.2/tests/test_treatments_h3.py` — TS-10 readiness, decision, authority, exact-resume, filesystem, and no-model reachability coverage.
- [ ] No framework installation — existing `unittest` and Ruff are sufficient.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Authorize the immutable Red branch contract | TS-10 | The machine may prove readiness and validate a decision record, but the locked contract requires a separate human authorization and forbids machine self-approval. | Review the H3 packet and readiness bindings; confirm `N_strict=0`, `repeat_count=0`, `h4_required=false`, `h4_reason=not_applicable_red`, all no-provider fields, and the acknowledged disputed/incomplete recovery path; then supply a canonical `approved_red` decision record with reviewer identity, UTC timestamp, attestation, and exact packet/readiness hashes. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verification or Wave 0 dependencies.
- [ ] Sampling continuity: no three consecutive tasks without automated verification.
- [ ] Wave 0 covers all missing test references.
- [ ] No watch-mode flags.
- [ ] Feedback latency is below 10 seconds.
- [ ] The four waves remain strictly sequential and each verifies exactly one objective.
- [ ] Human H3 authorization is distinct from machine readiness and publication validation.
- [x] `nyquist_compliant: true` is set in frontmatter after all task mappings match final plans.

**Approval:** pending
