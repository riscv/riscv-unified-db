---
phase: 1
slug: isolated-evidence-boundary-and-source-integrity
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-30
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python standard-library `unittest` |
| **Config file** | none — Wave 0 creates the experiment-local `tests/` package |
| **Quick run command** | `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -v` |
| **Full suite command** | `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -v` plus one copied-bundle offline replay with Git unavailable |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -v`
- **After every plan wave:** Run the full suite plus one copied-bundle offline replay with Git unavailable
- **Before `$gsd-verify-work`:** Full suite, accepted/rejected state tests, boundary receipt, and reviewer checkpoint must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | TS-01 | T-01 / T-02 | Canonical phase-start baseline distinguishes pre-existing files from later out-of-boundary changes | unit + filesystem integration | `PYTHONPATH=src python3 -m unittest tests.test_filesystem_boundary -v` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | TS-01 | T-03 | Symlinks, special files, path escapes, and hardlink-dependent accepted content fail closed | unit | `PYTHONPATH=src python3 -m unittest tests.test_filesystem_boundary -v` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | TS-01 | — | Canonical environment identity contains standalone-first fields and excludes non-canonical audit data | unit | `PYTHONPATH=src python3 -m unittest tests.test_canonical -v` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 2 | TS-02 | T-04 | Construction proves commit/tree objects and PR-head equality or ancestry before accepting a generation | isolated Git integration | `PYTHONPATH=src python3 -m unittest tests.test_git_proof -v` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 2 | TS-02 | The current PR #2192 mismatch produces a deterministic rejected receipt and no accepted generation or root | isolated Git integration | `PYTHONPATH=src python3 -m unittest tests.test_git_proof -v` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 3 | TS-02 | Offline verification recomputes raw bytes, derived lineage, manifest hash, root, and receipt without Git or network | unit + process isolation | `PYTHONPATH=src python3 -m unittest tests.test_bundle_verifier -v` | ❌ W0 | ⬜ pending |
| 01-03-02 | 03 | 3 | TS-01, TS-02 | Canonical JSON and derived Markdown are byte-stable and contain the same facts | golden + determinism | `PYTHONPATH=src python3 -m unittest tests.test_receipts -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `experiments/specchoice-v1.3.2/tests/__init__.py` — local test package marker
- [ ] `experiments/specchoice-v1.3.2/tests/test_canonical.py` — canonical bytes, sorting, hashing, and no-computed-field-cycle tests
- [ ] `experiments/specchoice-v1.3.2/tests/test_filesystem_boundary.py` — baseline delta, allowlist, `lstat`, special-file, hardlink, and escape tests
- [ ] `experiments/specchoice-v1.3.2/tests/test_git_proof.py` — isolated Git success fixtures and the frozen PR #2192 rejection case
- [ ] `experiments/specchoice-v1.3.2/tests/test_bundle_verifier.py` — accepted-bundle replay with Git and network unavailable
- [ ] `experiments/specchoice-v1.3.2/tests/test_receipts.py` — authoritative JSON and derived Markdown determinism

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Reviewer accepts the experiment boundary and standalone-first environment decision | TS-01 | Roadmap human checkpoint requires reviewer authority | Inspect the canonical environment decision, immutable phase-start baseline, allowlist, and passing boundary receipt; record approval or disputes before Phase 2 |
| Reviewer resolves the frozen PR #2192 identity mismatch before any claim that all six snapshots form an accepted generation | TS-02 | The frozen pin is currently not reachable from the current PR head and cannot be silently rewritten | Inspect the Git-native rejected receipt and supporting metadata; either independently validate the frozen identity or approve a versioned source-contract correction through project change control |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
