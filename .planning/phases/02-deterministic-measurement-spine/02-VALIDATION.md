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
