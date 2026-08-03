---
phase: 03
slug: human-reviewed-data-preregistration
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-08-03
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python standard-library `unittest` |
| **Config file** | none |
| **Quick run command** | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m unittest <focused-module>` |
| **Full suite command** | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m unittest tests.test_data_admission tests.test_data_splits tests.test_data_relevance tests.test_data_h2 tests.test_canonical tests.test_filesystem_boundary` |
| **Estimated runtime** | under 30 seconds |

## Sampling Rate

- **After every task:** Run the task's focused `unittest` module.
- **After every plan wave:** Run all Phase 3 test modules completed through that wave.
- **Before `$gsd-verify-work`:** Run the full suite above; it must be green.
- **Max feedback latency:** 30 seconds.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | TS-08, TS-09, H2-01 | T-03-01-01..05 | Descriptor-bound tracer rejects stale/unlisted source and inferred review | integration | `python -m unittest tests.test_data_admission` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | H2-01 | T-03-01-02..06 | Full inventory is frozen before review and cannot be backfilled | integration | `python -m unittest tests.test_data_admission` | ❌ W0 | ⬜ pending |
| 03-01-03 | 01 | 1 | TS-09, H2-01 | T-03-01-03..06 | Human pair decisions bind exact packet/readiness hashes | integration | `python -m unittest tests.test_data_admission` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 2 | TS-08, TS-09 | T-03-02-01..05 | Registry changes invalidate all dependent assignments | unit | `python -m unittest tests.test_data_splits` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 2 | TS-08 | T-03-02-02..06 | Split derivation enforces example and family isolation | integration | `python -m unittest tests.test_data_splits` | ❌ W0 | ⬜ pending |
| 03-02-03 | 02 | 2 | TS-09 | T-03-02-03..06 | Human membership decisions cannot override deterministic split rules | integration | `python -m unittest tests.test_data_splits` | ❌ W0 | ⬜ pending |
| 03-03-01 | 03 | 3 | TS-08, TS-09 | T-03-03-01..05 | Every strict case has explicit relevance or no-relevant-pair | unit | `python -m unittest tests.test_data_relevance` | ❌ W0 | ⬜ pending |
| 03-03-02 | 03 | 3 | TS-09 | T-03-03-02..06 | Four exact directions exist and synthetic text cannot count | integration | `python -m unittest tests.test_data_relevance` | ❌ W0 | ⬜ pending |
| 03-03-03 | 03 | 3 | TS-09 | T-03-03-03..06 | Human relevance/metamorphic decision binds complete registries | integration | `python -m unittest tests.test_data_relevance` | ❌ W0 | ⬜ pending |
| 03-04-01 | 04 | 4 | TS-08, TS-09, H2-01 | T-03-04-01..06 | Whole-chain readiness recomputes every authority and count | integration | `python -m unittest tests.test_data_h2` | ❌ W0 | ⬜ pending |
| 03-04-02 | 04 | 4 | TS-09, H2-01 | T-03-04-02..06 | Only a complete human H2 decision can authorize data root | integration | `python -m unittest tests.test_data_h2` | ❌ W0 | ⬜ pending |
| 03-04-03 | 04 | 4 | TS-08, TS-09, H2-01 | T-03-04-03..06 | Eligibility is exact, deterministic, and never final branch authority | integration | `python -m unittest tests.test_data_h2 tests.test_canonical tests.test_filesystem_boundary` | ❌ W0 | ⬜ pending |

## Wave 0 Requirements

- [ ] `tests/test_data_admission.py` — temporary accepted-source fixtures and tracer/full-inventory admission coverage.
- [ ] `tests/test_data_splits.py` — registry, reuse, leakage, and deterministic split fixtures.
- [ ] `tests/test_data_relevance.py` — relevance completeness and metamorphic fixtures.
- [ ] `tests/test_data_h2.py` — readiness, human-decision, eligibility, and data-root fixtures.

No framework or dependency installation is required.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Approve/dispute/exclude pair sides and relationships | TS-09, H2-01 | Semantic authority is human-only | Inspect exact spans and hashes in the pair packet; return every required decision field. |
| Approve family definitions and primary assignments | TS-09 | Machines cannot define or relabel semantic families | Review definition/inclusion/exclusion criteria before item assignments and sign the complete decision. |
| Approve relevance and metamorphic expectations | TS-09 | Relevance and expected direction are preregistered semantic judgments | Review every strict case and all four directions before retrieval, then sign the complete decision. |
| Approve H2 data root and audited counts | TS-09, H2-01 | Machine readiness is not approval | Compare recomputed hashes/counts, inspect quarantined items, and choose approved/disputed/incomplete. |

## Validation Sign-Off

- [x] All tasks have planned automated verification or Wave 0 dependencies.
- [x] Sampling continuity has no three consecutive tasks without automated verification.
- [x] Wave 0 covers every missing test module.
- [x] No watch-mode flags are used.
- [x] Expected feedback latency is under 30 seconds.
- [x] `nyquist_compliant: true` is set in frontmatter.

**Approval:** pending Phase 3 execution
