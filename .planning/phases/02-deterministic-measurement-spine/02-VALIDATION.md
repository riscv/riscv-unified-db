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

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python `unittest` (existing) |
| **Config file** | none — standard module execution with `PYTHONPATH=src` |
| **Quick run command** | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_measurement_adapter tests.test_measurement_parsing tests.test_measurement_scoring -q` |
| **Full suite command** | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_measurement_adapter tests.test_measurement_parsing tests.test_measurement_scoring tests.test_measurement_attempts tests.test_measurement_h1 -q` |
| **Estimated runtime** | ~15 seconds |

The focused Phase 2 commands are the green gate for this phase. Repository-wide
`unittest discover` currently includes Phase 1 live-boundary assertions that
intentionally reject later-phase artifacts; it is therefore recorded as a known
historical-boundary limitation, not used as the Phase 2 acceptance command, and
must not be "fixed" by weakening Phase 1 custody behavior.

---

## Sampling Rate

- **After every task commit:** Run the focused test module(s) owned by the task plus `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m specchoice_evidence.cli validate-phase2-source-authority`.
- **After every plan wave:** Run the full Phase 2 suite and one golden formal CLI invocation in a temporary attempt root.
- **Before `$gsd-verify-work`:** Full Phase 2 suite must be green; the golden H1 packet must contain no unexpected diagnostic; the human H1 decision must be recorded before Phase 3.
- **Max feedback latency:** 30 seconds for the automated focused/full suite; the H1 human decision is a separate manual gate.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 0 | TS-03 | T-02-01, T-02-03 | Accept only the verifier-rooted v2 bundle; reject path/source drift before record emission. | unit + integration | `python3 -m unittest tests.test_measurement_adapter -q` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | TS-03 | T-02-03 | Produce exactly 11 canonical records bound to all 28 raw identities and the 6/4/1 partition. | unit + integration | `python3 -m unittest tests.test_measurement_adapter -q` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 0 | TS-04 | T-02-01, T-02-02 | Reject duplicate, unknown, missing, ill-typed, invalid-enum, and noncanonical no-finding input without repair. | unit + adversarial | `python3 -m unittest tests.test_measurement_parsing -q` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 1 | TS-04 | T-02-02 | Keep any declared legacy alias mapping at an explicit ingress and preserve raw-before/raw-after trace. | unit + adversarial | `python3 -m unittest tests.test_measurement_parsing -q` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 0 | TS-03, TS-05 | T-02-04 | Test golden and adversarial scoring, stable diagnostic fields, and independent metrics before implementation. | unit + integration | `python3 -m unittest tests.test_measurement_scoring -q` | ❌ W0 | ⬜ pending |
| 02-03-02 | 03 | 1 | TS-03, TS-05 | T-02-03, T-02-04 | Validate evidence spans against authoritative raw bytes and classify the candidate out without contaminating aggregate metrics. | unit + integration | `python3 -m unittest tests.test_measurement_scoring -q` | ❌ W0 | ⬜ pending |
| 02-04-01 | 04 | 0 | TS-05 | T-02-03, T-02-04 | Test no-replace attempts, deterministic diagnostics, formal/diagnostic-only separation, and hash invalidation. | unit + integration | `python3 -m unittest tests.test_measurement_attempts tests.test_measurement_h1 -q` | ❌ W0 | ⬜ pending |
| 02-04-02 | 04 | 1 | TS-03, TS-04, TS-05 | T-02-01, T-02-02, T-02-03, T-02-04 | Golden all-11 run and adversarial oracle bind exact codes/fields; no machine-created H1 approval. | integration + adversarial | `python3 -m unittest tests.test_measurement_adapter tests.test_measurement_parsing tests.test_measurement_scoring tests.test_measurement_attempts tests.test_measurement_h1 -q` | ❌ W0 | ⬜ pending |

*Task IDs are seeded from the roadmap's four-plan tracer-first structure and must be synchronized with the final PLAN files before execution.*

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_measurement_adapter.py` — TS-03 adapter and v2-only source-contract matrix.
- [ ] `tests/test_measurement_parsing.py` — TS-04 strict JSON and explicit legacy-ingress matrix.
- [ ] `tests/test_measurement_scoring.py` — TS-03/TS-05 golden/adversarial outcomes and metric independence.
- [ ] `tests/test_measurement_attempts.py` — D-09–D-12 immutable attempts and preflight exits.
- [ ] `tests/test_measurement_h1.py` — D-13–D-16 human-decision binding and invalidation checks.
- [ ] Focused Phase 2 test target — document and expose the exact authority + measurement command without changing Phase 1's historical live-boundary assertions.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Record the H1 accept/dispute decision for the hash-bound golden packet. | TS-05 | D-16 forbids machine-created approval; automation may only validate binding and decision shape. | Run the full Phase 2 suite and golden formal CLI; inspect the immutable packet and diagnostics; record the authorized human decision with exact bound hashes; rerun H1 validation and confirm any source/rule/schema/golden/attempt/diagnostic change invalidates it. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verification or Wave 0 dependencies.
- [ ] Sampling continuity: no 3 consecutive tasks without automated verification.
- [ ] Wave 0 covers all missing test references.
- [ ] No watch-mode flags.
- [ ] Feedback latency < 30 seconds for automated checks.
- [ ] Golden H1 packet has no unexpected warnings or errors.
- [ ] Human H1 decision is recorded and hash-valid.
- [ ] `nyquist_compliant: true` set in frontmatter by validation after all gates pass.

**Approval:** pending
