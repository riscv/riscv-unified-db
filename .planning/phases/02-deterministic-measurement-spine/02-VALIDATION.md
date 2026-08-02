---
phase: 2
slug: deterministic-measurement-spine
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-31
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

`wave_0_complete: false` is intentional: Phase 2 has no independent global Wave 0. Each owning TDD task creates its test module first, observes RED, and implements in the same plan wave. The original matrix below preserves execution waves 1–5; the appended Wave 8 gap-closure rows extend those same modules without rewriting that history.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python `unittest` (existing) |
| **Config file** | none — standard module execution with `PYTHONPATH=src` |
| **Quick run command** | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_measurement_adapter tests.test_measurement_parsing tests.test_measurement_scoring -q` |
| **Plan 04 pre-H1 suite** | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_measurement_adapter tests.test_measurement_parsing tests.test_measurement_scoring tests.test_measurement_attempts -q` |
| **Historical Plan 05 final five-module suite** | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_measurement_adapter tests.test_measurement_parsing tests.test_measurement_scoring tests.test_measurement_attempts tests.test_measurement_h1 -q` |
| **Wave 8 final focused gate (64 tests)** | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_measurement_adapter tests.test_measurement_parsing tests.test_measurement_scoring tests.test_measurement_attempts tests.test_measurement_h1 tests.test_filesystem_boundary -q` |
| **Wave 8 repository partition** | Runtime discovery must find exactly 135 methods: 130 green plus the unchanged five Phase 1 expected-red methods, whose aggregate remains five failures and one error. |
| **Estimated runtime** | ~15 seconds |

The focused Phase 2 commands are the green gate for this phase. Plan 04 runs the complete four-module pre-H1 suite because `test_measurement_h1.py` is first created by its owning Task 02-05-01; Plan 05 then extends the same accumulated suite to all five modules. This is one continuous TDD chain, not a missing global scaffold wave.

Wave 8 adds exactly three public-boundary regression methods to the currently verified baseline of 61 focused tests and 132 discovered methods. Task 02-08-01 adds the adapter and preflight methods; Task 02-08-02 adds one parameterized H1 method covering packet, Markdown, decision, `_SCHEMA`, and `_H1_SCHEMA` leaves. Therefore the final expectations are 64 focused tests and 135 discovered methods, partitioned as 130 green plus the same five expected-red methods.

Repository-wide `unittest discover` includes Phase 1 live-boundary assertions that intentionally reject later-phase artifacts. It is preserved as historical custody evidence, is not a Phase 2 acceptance command, and must never be made green by rebasing, suppressing, or weakening Phase 1 custody/live-boundary behavior.

---

## Sampling Rate

- **After every task commit:** Run the focused module created/owned by that task plus `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m specchoice_evidence.cli validate-phase2-source-authority --authority phase2/source-authority.json --bundle bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2`.
- **After Plans 01–03:** Run the accumulated modules that exist through that plan.
- **During Plan 04:** Run the four-module pre-H1 suite after each task, then validate the immutable formal attempt and separate adversarial artifact.
- **During Plan 05:** Create `test_measurement_h1.py` first, run the final five-module suite after each automated task, validate the H1 JSON/Markdown binding, and rerun the decision validator after the human-authored file is supplied.
- **During Plan 08 / Wave 8:** Extend the existing adapter, parsing, and H1 test modules fail-first; run the two Task 02-08-01 public methods, then the one Task 02-08-02 public method; finish with the six-module 64-test gate and the 135 = 130 green + five expected-red repository partition.
- **Before `$gsd-verify-work`:** The Wave 8 six-module suite must be 64/64 green; repository discovery must preserve the 135 = 130 green + five expected-red partition; the golden H1 packet must contain no unexpected diagnostic; the human H1 decision must be recorded before Phase 3.
- **Max feedback latency:** 30 seconds for automated focused/full-suite checks; the H1 human decision is a separate manual gate.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | TS-03 | T-02-01, T-02-03 | Accept only the verifier-rooted accepted-v2 authority; reject path/source drift before record emission. | TDD unit + integration | `python3 -m unittest tests.test_measurement_adapter -q` | ❌ task creates first | ⬜ pending |
| 02-01-02 | 01 | 1 | TS-03 | T-02-01, T-02-03 | Produce exactly 11 canonical records bound to all 28 raw identities and the 6/4/1 partition. | TDD unit + integration | `python3 -m unittest tests.test_measurement_adapter -q` | ❌ created by 02-01-01 | ⬜ pending |
| 02-02-01 | 02 | 2 | TS-04, TS-05 | T-02-01, T-02-02 | Enforce JSON-only formal input, exact closed evidence-span shape, and strict no-finding/unknown/duplicate rejection without repair. | TDD unit + adversarial | `python3 -m unittest tests.test_measurement_parsing -q` | ❌ task creates first | ⬜ pending |
| 02-02-02 | 02 | 2 | TS-04, TS-05 | T-02-02, T-02-03 | Keep legacy alias mapping at a separately declared ingress and preserve raw-before/raw-after trace plus stable ordering. | TDD unit + adversarial | `python3 -m unittest tests.test_measurement_parsing -q` | ❌ created by 02-02-01 | ⬜ pending |
| 02-03-01 | 03 | 3 | TS-03, TS-05 | T-02-02, T-02-04 | Score exact all-11 golden semantics with independent surfacing/disposition/identity/evidence outcomes. | TDD unit + integration | `python3 -m unittest tests.test_measurement_scoring -q` | ❌ task creates first | ⬜ pending |
| 02-03-02 | 03 | 3 | TS-03, TS-05 | T-02-03, T-02-04 | Validate every exact half-open raw evidence span independently and cover required structured diagnostics. | TDD unit + adversarial | `python3 -m unittest tests.test_measurement_scoring -q` | ❌ created by 02-03-01 | ⬜ pending |
| 02-04-01 | 04 | 4 | TS-03, TS-04, TS-05 | T-02-03, T-02-04 | Test exclusive-create/fsync/no-replace attempts and preserve invalid/diagnostic-only role separation. | TDD unit + integration | `python3 -m unittest tests.test_measurement_attempts -q` | ❌ task creates first | ⬜ pending |
| 02-04-02 | 04 | 4 | TS-03, TS-04, TS-05 | T-02-01, T-02-03 | Generate and validate the warning-free formal all-11 attempt with no metrics on blocking input. | TDD integration | `python3 -m unittest tests.test_measurement_adapter tests.test_measurement_parsing tests.test_measurement_scoring tests.test_measurement_attempts -q` | ❌ created by 02-04-01 | ⬜ pending |
| 02-04-03 | 04 | 4 | TS-04, TS-05 | T-02-01, T-02-02, T-02-04 | Generate a separate diagnostic-only adversarial result whose exact codes/fields match the oracle and confer no authority. | TDD integration + adversarial | `python3 -m unittest tests.test_measurement_adapter tests.test_measurement_parsing tests.test_measurement_scoring tests.test_measurement_attempts -q` | ❌ created by 02-04-01 | ⬜ pending |
| 02-05-01 | 05 | 5 | TS-03, TS-04, TS-05 | T-02-01, T-02-02, T-02-04 | Test H1 packet/decision closed schemas, all bindings, three dispositions, per-fixture signatures, and no machine approval. | TDD unit + integration | `python3 -m unittest tests.test_measurement_adapter tests.test_measurement_parsing tests.test_measurement_scoring tests.test_measurement_attempts tests.test_measurement_h1 -q` | ❌ task creates first | ⬜ pending |
| 02-05-02 | 05 | 5 | TS-03, TS-04, TS-05 | T-02-03, T-02-04 | Generate canonical H1 JSON and pure Markdown from Plan 04 evidence, then reject any changed source/adapter/schema/attempt/diagnostic binding. | integration | `python3 -m unittest tests.test_measurement_adapter tests.test_measurement_parsing tests.test_measurement_scoring tests.test_measurement_attempts tests.test_measurement_h1 -q` | ❌ created by 02-05-01 | ⬜ pending |
| 02-05-03 | 05 | 5 | TS-05 | T-02-04 | Validate only an independently human-authored approved/disputed/incomplete decision; preserve local-only and no-publication authority. | automated binding check + human review | `python3 -m specchoice_measurement.cli validate-h1-decision --packet reports/h1/h1-source-gold-review-v1.json --decision reviews/h1-source-gold-decision-v1.json` | ❌ reviewer creates at checkpoint | ⬜ pending |

The historical task IDs and waves above exactly match the original five PLAN files. Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky.

### Wave 8 Gap-Closure Addendum

The historical rows above remain the Plans 01–05 contract. These rows map the two tasks added by `02-08-PLAN.md` after verification found the descriptor/path TOCTOU gap.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-08-01 | 08 | 8 | TS-03, TS-04, TS-05 | T-02-08-01, T-02-08-02 | Bind adapter raw leaves and preflight fixture sources to bytes returned by one no-follow descriptor; swapped links and FIFOs fail closed without external-byte use or blocking. | TDD public-boundary integration | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_measurement_adapter.MeasurementAdapterTests.test_public_builder_rejects_swapped_raw_leaf_and_fifo_without_consuming_or_blocking tests.test_measurement_parsing.MeasurementParsingTests.test_public_preflight_rejects_swapped_fixture_source_and_fifo_without_consuming_or_blocking -q` | ✅ extends existing modules | ⬜ pending |
| 02-08-02 | 08 | 8 | TS-03, TS-04, TS-05 | T-02-08-03, T-02-08-04, T-02-08-05 | Bind H1 evidence, packet, Markdown, decision, `_SCHEMA`, and `_H1_SCHEMA` hashing/parsing/comparison to descriptor-returned bytes while preserving local-only human authority and the repository test partition. | TDD public-boundary integration + phase gate | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_measurement_h1.H1PacketTests.test_public_h1_validators_reject_swapped_packet_markdown_and_decision_leaves_and_fifos_without_consuming_or_blocking -q && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_measurement_adapter tests.test_measurement_parsing tests.test_measurement_scoring tests.test_measurement_attempts tests.test_measurement_h1 tests.test_filesystem_boundary -q` | ✅ extends existing module | ⬜ pending |

Wave 8 completion additionally runs the `02-08-02` discovery script from the plan: it discovers runtime IDs, requires exactly 135 methods, excludes only the exact five preserved Phase 1 expected-red IDs, runs the remaining 130 green, and confirms the expected-red aggregate is five failures plus one error. The six-module command above is the final focused 64-test gate.

---

## Per-Plan TDD Prerequisites (No Independent Wave 0)

- [ ] Task 02-01-01 creates `tests/test_measurement_adapter.py` before adapter production code.
- [ ] Task 02-02-01 creates `tests/test_measurement_parsing.py` before parser/preflight production code.
- [ ] Task 02-03-01 creates `tests/test_measurement_scoring.py` before scorer production code.
- [ ] Task 02-04-01 creates `tests/test_measurement_attempts.py` before attempt-custody production code.
- [ ] Task 02-05-01 creates `tests/test_measurement_h1.py` before H1 packet/decision production code.
- [ ] Task 02-08-01 extends exactly two existing public-boundary test modules before adapter/preflight production substitutions and observes both methods RED.
- [ ] Task 02-08-02 extends the existing single H1 public-boundary method before H1 production substitutions; its subtests cover packet, Markdown, decision, `_SCHEMA`, and `_H1_SCHEMA` swaps/FIFOs without creating another test method.
- [ ] Every owner observes RED before implementation and retains the accumulated earlier modules in its plan-level suite.
- [ ] The exact Phase 2 source-authority validator accompanies every task without modifying Phase 1 custody code or live-boundary assertions.

---

## Manual-Only Verifications

| Task ID | Behavior | Requirement | Why Manual | Test Instructions |
|---------|----------|-------------|------------|-------------------|
| 02-05-03 | Record the H1 accept/dispute/incomplete decision for the hash-bound golden packet. | TS-05 | D-13 and D-16 forbid machine-created approval; automation may only validate binding and decision shape. | Run the final five-module suite and H1 packet validators; inspect all 11 fixture semantics and bindings; independently author the canonical decision; rerun validation and confirm any source/rule/schema/golden/attempt/diagnostic change invalidates it. |

---

## Validation Sign-Off

- [ ] Every production-code task creates or extends tests in its owning plan and has an `<automated>` verification.
- [ ] Sampling continuity: Plans 01–03 grow focused coverage, Plan 04 runs the complete four-module pre-H1 suite, Plan 05 runs all five modules, and Wave 8 finishes with the six-module 64-test focused gate.
- [ ] No independent global Wave 0 is referenced or required.
- [ ] No watch-mode flags.
- [ ] Feedback latency < 30 seconds for automated checks.
- [ ] Golden formal attempt has no unexpected warning or error; adversarial results remain separate and diagnostic-only.
- [ ] H1 JSON/Markdown bindings validate, the human H1 decision is recorded and hash-valid, and disputed/incomplete remains blocking.
- [ ] Phase 1 custody/live-boundary checks are unchanged and never weakened to satisfy Phase 2.
- [ ] Runtime discovery is exactly 135 = 130 green + the unchanged five Phase 1 expected-red methods, and the expected-red aggregate remains five failures plus one error.
- [ ] `nyquist_compliant: true` is set only after every automated and human gate above passes.

**Approval:** pending

---

## Corrective validation addendum — plans 02-09 through 02-17

This addendum is append-only. It supersedes projected execution counts and approval status above without rewriting historical validation evidence.

`nyquist_compliant: false`

**Approval:** pending — candidate construction, local acceptance, and H1 decision are three independent blocking human gates.

### Corrective waves

| Wave | Plan | Automated closure | Blocking human gate | Evidence boundary |
|---:|---|---|---|---|
| 9 | 02-09 | Dirfd-rooted stable read/tree/write primitives; held-inventory accepted materialization; reusable full-partition phase gate | none | Code/tests only; no evidence generation |
| 10 | 02-10 | Versioned v3 construction contracts, exact 11/28/6-4-1 plus five verifier artifacts, copied-isolation verification | Candidate-construction decision | Candidate only; active authority remains v2 |
| 11 | 02-11 | Versioned v10 acceptance, accepted-v3, historical v2, exact pending authority and non-effective transition | Local-acceptance decision | v2 remains active/unrevoked; no cutover |
| 12 | 02-12 | Accepted-v3 acceptance/integrity/offline-replay receipt custody only | none | Active v2 and pending transition remain unchanged; no consumer migration |
| 13 | 02-13 | Adapter/preflight explicit pending-v3 migration and non-authoritative readiness rehearsal | none | Active v2 remains authoritative; no formal/adversarial/H1 work |
| 14 | 02-14 | Formal/adversarial descriptor-held pending-v3 migration in disposable rehearsals | none | No authoritative evidence or active switch |
| 15 | 02-15 | Remaining defaults, public H1 leaf matrix, schema-v2, decision-free readiness and read-only decision contracts | none | No actual readiness/evidence/cutover/human decision |
| 16 | 02-16 | Idempotent anti-rollback cutover followed by formal-v2, adversarial-v3 and packet-v3 | none | pending-v3 rehearsal → canonical revocation → exact active-v3 replacement → active-v3 validation → formal-v2 → adversarial-v3 → packet-v3 |
| 17 | 02-17 | Absolute-root readiness, human H1 decision and four fresh same-commit reports | H1 decision | Local-only decision; no external publication authority |

Every wave uses the predecessor SUMMARY task commit as trust baseline and compares the live worktree directly to it, never `base..HEAD`; tracked/staged/worktree/untracked/ignored paths, tracked `receipts/`, `.DS_Store`, and absent-or-ignored `gen/` are explicit. After Wave 11 the five embedded verifier artifacts, accepted-v3, historical/pending/active-v2 authority, and pending transition are frozen. Wave 12 allowlists only receipt-writer/tests plus five successor receipts; Wave 13 only adapter/preflight/readiness rehearsal; Wave 14 only formal/adversarial reader code/tests; Wave 15 only H1/default/schema code/tests. Wave 16 alone may publish canonical revocation and replace active authority with exact pending bytes, then create successor evidence. Wave 17 only creates readiness, the human decision, and four reports; ROADMAP.md and STATE.md remain frozen.

### Corrective task and baseline map

The corrective set contains exactly 17 tasks. Every task must record its starting baseline, phase-gate receipt and final task commit in its owning SUMMARY; checkpoint tasks additionally record the independently supplied decision hash.

| Task ID | Owner | Trust baseline | Required gate / checkpoint |
|---|---|---|---|
| 02-09-01 | Descriptor-rooted public tracer | 02-08 final task commit | Wave 9: 66/141/136 |
| 02-09-02 | Remaining reopen removal and oracle | prior task commit | Wave 9: 66/141/136 |
| 02-10-01 | v3 construction proposal | 02-09-SUMMARY final task commit | Wave 10: 66/141/136 |
| 02-10-02 | Human construction authorization | prior task commit | blocking `authorize|reject` validator |
| 02-10-03 | Isolated v3 candidate/audit | validated construction decision | Wave 10: 66/141/136 |
| 02-11-01 | v3 acceptance/pending-cutover tracer | 02-10-SUMMARY final task commit | Wave 11: 66/143/138 |
| 02-11-02 | Human local acceptance | prior task commit | blocking `accept|reject` validator |
| 02-11-03 | Accepted-v3 and non-effective transition | validated local acceptance | Wave 11: 66/143/138 |
| 02-12-01 | Receipt-custody tracer | 02-11-SUMMARY final task commit | focused receipt method, then Wave 12 gate |
| 02-12-02 | Five accepted-v3 receipts | prior task commit | Wave 12: 66/144/139 |
| 02-13-01 | Adapter/preflight pending-v3 migration | 02-12-SUMMARY final task commit | Wave 13: 69/147/142 |
| 02-14-01 | Formal/adversarial read-graph migration | 02-13-SUMMARY final task commit | Wave 14: 71/149/144 |
| 02-15-01 | H1/default/schema/readiness contracts | 02-14-SUMMARY final task commit | Wave 15: 72/150/145 and WR-01 public matrix |
| 02-16-01 | Idempotent anti-rollback cutover/evidence | 02-15-SUMMARY final task commit | Wave 16: 72/150/145 after exact ordered state machine |
| 02-17-01 | Absolute-root final readiness | 02-16-SUMMARY final task commit | Wave 17: 72/150/145 piped into readiness-v3 |
| 02-17-02 | Human H1 decision | validated readiness-v3 | blocking decision-v2 validator with seven responses |
| 02-17-03 | Four fresh reports | current pre-report HEAD | same `audited_commit`; SECURITY/VERIFICATION/REVIEW contract |

### Exact semantic expected-red oracle

`experiments/specchoice-v1.3.2/tests/phase1_expected_red_oracle.py` is outside discovery and is the reusable phase gate. Given expected focused/discovered/green counts, it discovers all tests, identifies exactly the five red top-level IDs, excludes only those and requires every remainder green, runs the six focused modules, and separately uses binary `TemporaryFile(mode="w+b")` plus `TextIOWrapper` to assert:

- exactly five top-level methods run;
- exactly five failures and one error;
- zero skipped, expected-failure, and unexpected-success outcomes;
- racing empty target: expected `LOCAL_ACCEPTED_TARGET_EXISTS`, observed `FIXTURE_CLOSURE_ACCEPTANCE_BOUNDARY_BLOCKING`;
- no-replace unavailable: expected `ATOMIC_NO_REPLACE_UNAVAILABLE`, observed `FIXTURE_CLOSURE_ACCEPTANCE_BOUNDARY_BLOCKING`;
- `REGISTRY_MISMATCH` subtest: expected its named code, observed `FIXTURE_CLOSURE_ACCEPTANCE_BOUNDARY_BLOCKING`;
- `BASIS_MISMATCH` subtest: expected its named code, observed `FIXTURE_CLOSURE_ACCEPTANCE_BOUNDARY_BLOCKING`;
- current-v7-basis: `BundleError: FIXTURE_CLOSURE_ACCEPTANCE_BOUNDARY_BLOCKING`;
- active-defaults receipt: `AssertionError: 1 != 0`.

No corrective plan may weaken, skip, mark expected, or rewrite these five baseline methods or the current-v7 basis to make them green.

On success the gate emits exactly one closed canonical stdout receipt containing focused/discovered/green/red counts, five IDs, six normalized outcome statuses, zero-outcome counters, and stable oracle status. Readiness hashes those actual bytes; counts are never copied from prose.

### New discovered test methods

| Plan | Module | Method | Focused delta | Discovery delta |
|---|---|---|---:|---:|
| 02-09 | `test_filesystem_boundary` | `test_dirfd_reader_rejects_root_and_intermediate_rebind_without_escape` | +1 | +1 |
| 02-09 | `test_filesystem_boundary` | `test_dirfd_reader_rejects_regular_to_fifo_immediate_open_without_blocking` | +1 | +1 |
| 02-09 | `test_bundle_verifier` | `test_public_source_verifier_rejects_rebound_root_intermediate_and_fifo_leafs` | 0 | +1 |
| 02-09 | `test_bundle_verifier` | `test_descriptor_tree_closure_rejects_rebind_without_pathname_walk` | 0 | +1 |
| 02-09 | `test_fixture_closure` | `test_source_authority_and_bundle_consumers_reuse_descriptor_bound_canonical_bytes` | 0 | +1 |
| 02-09 | `test_fixture_closure` | `test_public_candidate_and_acceptance_paths_reject_rebound_control_leaves` | 0 | +1 |
| 02-11 | `test_fixture_closure` | `test_v3_local_acceptance_prepares_pending_cutover_without_switching_v2` | 0 | +1 |
| 02-11 | `test_fixture_closure` | `test_v3_copied_offline_replay_uses_embedded_hardened_verifier` | 0 | +1 |
| 02-12 | `test_fixture_closure` | `test_v3_acceptance_receipts_and_copied_replay_bind_same_identity` | 0 | +1 |
| 02-13 | `test_measurement_adapter` | `test_public_builder_binds_complete_validator_receipt_and_rejects_post_validation_authority_replacement` | +1 | +1 |
| 02-13 | `test_measurement_adapter` | `test_public_builder_rejects_rebound_rules_authority_and_registry_roles` | +1 | +1 |
| 02-13 | `test_measurement_parsing` | `test_public_preflight_reuses_one_descriptor_read_per_fixture` | +1 | +1 |
| 02-14 | `test_measurement_attempts` | `test_public_formal_cli_rejects_prediction_schema_manifest_and_retained_artifact_leaf_races` | +1 | +1 |
| 02-14 | `test_measurement_attempts` | `test_public_adversarial_validator_rejects_report_oracle_golden_schema_and_attempt_leaf_races` | +1 | +1 |
| 02-15 | `test_measurement_h1` | `test_public_h1_reuses_validated_attempt_and_adversarial_objects_without_reopen` | +1 | +1 |

### Rewritten test methods (zero count delta)

- `test_repository_decision_binds_v2_candidate_authority_without_accepted_generation` → `test_v3_fixture_construction_decision_binds_exact_proposal_and_source`
- `test_complete_candidate_is_ineligible_and_rejects_extra_or_missing_files` → `test_verifier_rooted_v3_candidate_has_fresh_root_and_unchanged_source_hashes`, retaining missing/extra/ineligible assertions
- `test_accepted_v2_builds_the_complete_canonical_partition` → `test_explicit_pending_v3_builds_the_complete_canonical_partition`
- `test_public_builder_rejects_swapped_raw_leaf_and_fifo_without_consuming_or_blocking`
- `test_public_preflight_rejects_swapped_fixture_source_and_fifo_without_consuming_or_blocking`
- `test_attempt_validation_rejects_leaf_swaps_before_no_follow_open`
- `test_public_h1_validators_reject_swapped_packet_markdown_and_decision_leaves_and_fifos_without_consuming_or_blocking`
- `test_h1_exposes_only_packet_and_existing_decision_validation` → `test_h1_v3_exposes_readiness_and_v2_decision_validation_without_human_writers`

### Count derivation and gates

- Historical baseline: 64 focused, 135 discovered, 130 green, five red top-level IDs, six normalized red outcomes.
- Wave 9: 66 focused / 141 discovered / 136 green.
- Wave 10: 66 / 141 / 136.
- Wave 11: 66 / 143 / 138.
- Wave 12: 66 / 144 / 139.
- Wave 13: 69 / 147 / 142.
- Wave 14: 71 / 149 / 144.
- Wave 15: 72 / 150 / 145.
- Wave 16: 72 / 150 / 145.
- Wave 17: 72 / 150 / 145.

Every wave invokes the phase gate with its row's expected counts. The gate owns focused/discovery execution and exact red partitioning; raw discovery is not a substitute because the intentional red partition exits nonzero.

### Authoritative leaf-role matrix

The public, non-mocked matrix covers controls; raw/source; registry/authority; distinct core and snapshot manifests; five verifier artifacts; formal/adversarial retained artifacts; report/oracle/golden/canonical schema/H1 schema-v2; packet/Markdown/readiness/decision; and descriptor-rooted destination parents. Applicable roles receive symlink, FIFO, deterministic replacement, mutation-performed, bounded-completion coverage. Read stability compares pre/post mode/dev/ino/nlink/size/mtime_ns/ctime_ns; tree closure compares held-directory metadata plus exact no-extra/no-missing inventory. Writer root/intermediate rebind asserts zero escaped writes; accepted materialization uses verified held bytes, never verify-then-copytree. Invalid adapter batches have `records=()` and only verified provenance; stable errors include role blockers, `ATTEMPT_SCHEMA_UNREADABLE`, `ADVERSARIAL_REPORT_INVALID`, and enclosing H1 errors.

### Cutover and schema contracts

- Candidate and accepted lifecycles have distinct core/snapshot/root identities; byte identity is required only for 28 raw files, registry, and all five verifier artifacts.
- Closed schemas/stdout use unambiguous `core_sha256` and `snapshot_manifest_sha256`; legacy `manifest_sha256`, if retained, explicitly means snapshot self-digest.
- Pending transition is non-effective through Wave 15. Wave 16 first completes a pending-v3 rehearsal, then publishes its exact bytes canonically, making v2 active validation fail closed, and then atomically replaces active authority with exact reviewed pending-v3 bytes as the last authority mutation. Resume is idempotent: an existing canonical revocation or active-v3 authority is accepted only when byte-identical to the reviewed pending artifact and validator-green; mismatches fail closed without overwrite, repair, deletion, rebase, rollback or fallback.
- Plan 11 owns and disposable-tree tests both public cutover commands before real state exists: version-aware `validate-phase2-source-authority --revocation ... --authority-mode active|historical-inspection` and the forward-only `activate-pending-source-cutover-v10`. Plan 16 invokes that exact mutator; it may not use an ad hoc copy/replace script.
- Active validation requires exact v3 plus revocation/transition digest. Historical v2 validation is inspection-only and never grants eligibility.
- `h1-review-schema-v2.json` is a new immutable successor; schema-v1 and historical packet/decision bytes are never changed or treated as byte-equivalent.
- Packet-v3 build and validation require explicit `--schema config/measurement/h1-review-schema-v2.json`; successor H1 operations have no implicit schema default.
- Wave 16 evidence order is exact: pending-v3 rehearsal only → canonical revocation → active-v3 exact replacement → active-v3 validation → `runs/measurement-attempts/formal-golden-pr2164-v2` → adversarial-v3 → packet-v3. A failure after cutover leaves v3 active and Phase 2 open; it never restores v2.
- Wave 17 writes `receipts/h1-review-readiness-v3.json` exactly once with `set -o pipefail`, the canonical phase-gate stdout, all explicit artifact bindings and a normalized absolute no-`..` 02-16-SUMMARY path. Verification/resume pipes a fresh oracle receipt only into the read-only validator; it never reinvokes the no-replace writer. The human decision uses `aggregate_disposition` and `external_publication_authorized: false`.

### Human-owned unresolved assumptions

The H1 packet must expose, and only the Wave 17 human decision may resolve, these exact closed `semantic_responses` identifiers:

1. `ts03_adjacency` — TS-03 adjacency.
2. `ts03_empty_null_single_element` — TS-03 empty/null/single-element behavior.
3. `ts03_equal_element_stable_order` — TS-03 equal-element stable ordering.
4. `ts04_unclassified_manual_review` — TS-04 unclassified/manual-review handling.
5. `ts05_adjacency` — TS-05 adjacency.
6. `ts05_empty_null_single_element` — TS-05 empty/null/single-element behavior.
7. `ts05_equal_element_stable_order` — TS-05 equal-element stable ordering.

The three independent human gates are Plan 10 candidate construction, Plan 11 local acceptance, and Plan 17 H1 decision. The H1 decision contains exactly 11 packet-bound `fixture_reviews` plus the seven closed response objects; its read-only validator emits one canonical closed receipt, and the final report gate consumes that receipt rather than bare JSON. The Phase 1 security/verifier refresh must include Plans/SUMMARYs 02-09 through 02-12 plus accepted-v3, canonical revocation and active-v3. All four final reports must bind the same current pre-report `audited_commit` in their unique first YAML frontmatter; body lines cannot satisfy gate fields. Phase 2 REVIEW must be `clean` with critical/warning/info/total all zero, and an approved Phase 2 VERIFICATION must record `score: "35/35 must-haves verified"` while disputed/incomplete records `gaps_found` and enumerates all seven response IDs.

Until all automated gates and all three independent human checkpoints pass, this addendum remains `nyquist_compliant: false` and approval remains pending.
