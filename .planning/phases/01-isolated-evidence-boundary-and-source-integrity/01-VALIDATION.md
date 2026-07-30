---
phase: 1
slug: isolated-evidence-boundary-and-source-integrity
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-30
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for the four-plan, eleven-task execution graph.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Python standard-library `unittest` |
| **Config file** | none — Wave 0 creates the experiment-local `tests/` package |
| **Working directory** | `experiments/specchoice-v1.3.2/` |
| **Quick run command** | `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -v` |
| **Full suite command** | `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -v` |
| **Offline replay authority** | `tests.test_bundle_verifier` must copy an accepted synthetic bundle outside the repository and run its embedded verifier with Git and network made unavailable |
| **Estimated runtime** | less than 60 seconds for local fixtures; canonical-remote construction is a separate state-aware check |

The full suite uses disposable Git repositories, temporary filesystem fixtures, an
injected clock, a failing Git shim, and a blocked-socket guard. It never requires
`bin/setup`, `bin/doctor`, the full UDB toolchain, or a third-party Python package.

---

## Sampling Rate

- **After every task commit:** Run the task's exact command from the map below.
- **After every plan wave:** Run the full suite from
  `experiments/specchoice-v1.3.2/`.
- **After Wave 3:** Also validate the real PR #2192 rejected receipt and confirm that no
  accepted generation or downstream-eligible root exists for the uncorrected contract.
- **After Wave 4:** Run the copied-bundle offline replay fixture, boundary classification,
  receipt determinism tests, and the state-appropriate reviewer finalization command.
- **Before `$gsd-verify-work`:** The full suite and all applicable reviewer decisions must
  be green. The known uncorrected #2192 route remains a canonical nonzero blocker, not a
  test failure to suppress.
- **Max local feedback latency:** 60 seconds.

---

## Per-Task Verification Map

All task IDs below are derived from the current `01-01-PLAN.md` through
`01-04-PLAN.md`. “Wave 0 dependency” names the test file or deterministic fixture that
must exist before the mapped verification can be considered covered.

| Task ID | Plan | Wave | Requirement | Decision / Threat | Secure behavior and evidence | Automated or deterministic command | Wave 0 dependency | Status |
|---------|------|------|-------------|-------------------|------------------------------|------------------------------------|-------------------|--------|
| 01-01-01 | 01 | 1 | TS-01 | D-14–D-16; T-01-01, T-01-02, T-01-03 | The first implementation write is the immutable canonical baseline; exact allowlist classification keeps pre-existing `.DS_Store` visible and rejects later out-of-boundary delta and prohibited file kinds | `PYTHONPATH=src python3 -m unittest tests.test_canonical tests.test_filesystem_boundary -v` | `tests/__init__.py`, `tests/test_canonical.py`, `tests/test_filesystem_boundary.py` baseline/delta fixture | ⬜ pending |
| 01-01-02 | 01 | 1 | TS-01 | D-14–D-16; T-01-02, T-01-03 | Prefix collisions, path escapes, symlinks, special files, mount uncertainty, hardlink dependency, malformed lengths/digests, and baseline overwrite attempts fail closed | `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -v` | `tests/test_canonical.py`, `tests/test_filesystem_boundary.py` adversarial filesystem fixtures | ⬜ pending |
| 01-01-03 | 01 | 1 | TS-01 | D-14, D-15; T-01-01, T-01-02 | Reviewer approval binds the exact baseline and allowlist hashes before any GSD control-file update; a dispute requires a new baseline generation | `PYTHONPATH=src python3 -m specchoice_evidence.cli validate-control-decision receipts/control-update-decision-plan01.json` | `tests/test_filesystem_boundary.py` immutable-baseline and exact-allowlist fixture; human baseline review | ⬜ pending / manual gate |
| 01-02-01 | 02 | 2 | TS-01 | D-09, D-10, D-12, D-13; T-01-04, T-01-06 | Canonical evidence records standalone-first stable capabilities and policy; non-canonical audit data points one-way to its digest and cannot pollute experiment identity | `PYTHONPATH=src python3 -m unittest tests.test_environment -v` | `tests/test_environment.py` stable-field, sanitization, and one-way-link fixtures | ⬜ pending |
| 01-02-02 | 02 | 2 | TS-01 | D-11; T-01-05, T-01-07 | The first concrete dependency failure starts one cumulative 90-minute wall-clock incident; retries, alternatives, builds, downloads, and waits never reset or pause it | `PYTHONPATH=src python3 -m unittest tests.test_environment -v` | `tests/test_environment.py` injected-clock no-incident, restored, resolved, and ceiling-exceeded fixtures | ⬜ pending |
| 01-03-01 | 03 | 3 | TS-02 | D-06, D-07; T-01-08 | Local Git commit/tree/equality-or-ancestry proof is authoritative; the frozen PR #2192 pin emits `PR_PIN_NOT_REACHABLE`, a deterministic rejected receipt, and no accepted generation/root | `PYTHONPATH=src python3 -m unittest tests.test_git_proof -v` | `tests/test_git_proof.py` disposable equal-head, ancestor, unrelated-commit, missing-object, and real #2192 rejection fixtures | ⬜ pending |
| 01-03-02 | 03 | 3 | TS-02 | D-01, D-06, D-07; T-01-08, T-01-10 | Reviewer either records the Red blocker or authorizes one versioned corrected PR/pin plus exact non-empty consumed path/role inventory; no approval can waive ancestry or raw-byte custody | `PYTHONPATH=src python3 -m specchoice_evidence.cli validate-source-decision receipts/source-publication-decision.json` | `tests/test_git_proof.py` #2192 rejected-receipt fixture and `tests/test_bundle_verifier.py` request-inventory validation fixtures; human source decision | ⬜ pending / manual gate |
| 01-03-03 | 03 | 3 | TS-02 | D-01–D-08; T-01-09, T-01-10, T-01-11, T-01-12 | Exact raw bytes and explicit derived lineage form the two-level manifest and packaging-independent logical root; null/duplicate/alias/collision inputs, binding tamper, interruption, or concurrent publication cannot expose accepted state | `PYTHONPATH=src python3 -m unittest tests.test_git_proof tests.test_bundle_verifier -v` | `tests/test_bundle_verifier.py` raw/derived, manifest projection, top-level/per-snapshot binding tamper, repack, concurrency, and interruption fixtures | ⬜ pending |
| 01-04-01 | 04 | 4 | TS-01, TS-02 | D-02, D-05, D-07–D-09; T-01-14, T-01-15 | A copied accepted synthetic bundle verifies only from its rooted stdlib verifier with `.git`, network, and a usable Git executable unavailable; rejected/partial state and every snapshot-binding tamper fail | `PYTHONPATH=src python3 -m unittest tests.test_bundle_verifier -v` | `tests/test_bundle_verifier.py` copied-directory process fixture, failing Git shim, blocked-socket guard, self-verifier tamper, and snapshot-binding tamper matrix | ⬜ pending |
| 01-04-02 | 04 | 4 | TS-01, TS-02 | D-14–D-18; T-01-16, T-01-17, T-01-19 | Canonical JSON self-hash, five boundary classifications, accepted-or-rejected source identity, blocking diagnostics, JSON-only Markdown, and package-incomplete-on-render-failure semantics are deterministic | `PYTHONPATH=src python3 -m unittest tests.test_bundle_verifier tests.test_receipts tests.test_filesystem_boundary -v` | `tests/test_receipts.py` golden/self-hash/Markdown-failure/#2192-blocked fixtures plus `tests/test_filesystem_boundary.py` classification fixtures | ⬜ pending |
| 01-04-03 | 04 | 4 | TS-01, TS-02 | D-07, D-17, D-18; T-01-18 | Human approval cites the exact receipt and accepted identity but cannot override any source, offline-verifier, boundary, or receipt failure; blocked/disputed state prevents Phase 1 completion | `PYTHONPATH=src python3 -m specchoice_evidence.cli finalize-review --decision receipts/reviewer-boundary-decision.json --receipt receipts/integrity-receipt.json --markdown receipts/integrity-receipt.md` | `tests/test_receipts.py` reviewer-override/finalization fixtures and `tests/test_bundle_verifier.py` accepted-versus-rejected eligibility fixture; human final review | ⬜ pending / manual gate |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky · “manual gate” means the
deterministic validator is automated but the disposition remains human-owned.*

### Task-ID reconciliation

| Plan | Planned tasks | Mapped task IDs | Result |
|------|---------------|-----------------|--------|
| 01 | 3 | 01-01-01, 01-01-02, 01-01-03 | exact |
| 02 | 2 | 01-02-01, 01-02-02 | exact |
| 03 | 3 | 01-03-01, 01-03-02, 01-03-03 | exact |
| 04 | 3 | 01-04-01, 01-04-02, 01-04-03 | exact |
| **Total** | **11** | **11 unique IDs** | **no missing or orphan mapping** |

---

## Wave 0 Requirements

- [ ] `experiments/specchoice-v1.3.2/tests/__init__.py` — local test package marker.
- [ ] `experiments/specchoice-v1.3.2/tests/test_canonical.py` — canonical bytes, stable
  ordering, strict length/digest fields, and non-cyclic hash projections.
- [ ] `experiments/specchoice-v1.3.2/tests/test_filesystem_boundary.py` — immutable
  baseline, exact allowlist, five delta classifications, `lstat`, special-file,
  hardlink, mount uncertainty, prefix-collision, and escape cases.
- [ ] `experiments/specchoice-v1.3.2/tests/test_environment.py` — standalone-first stable
  environment identity, audit sanitization/one-way reference, and injected cumulative
  incident-clock cases.
- [ ] `experiments/specchoice-v1.3.2/tests/test_git_proof.py` — disposable Git graph/object
  success and failure cases plus the frozen PR #2192 rejected proof.
- [ ] `experiments/specchoice-v1.3.2/tests/test_bundle_verifier.py` — request-inventory
  validation, raw/derived custody, manifest/root/binding tamper cases, publication
  concurrency/interruption, and copied accepted-bundle replay with Git/network unavailable.
- [ ] `experiments/specchoice-v1.3.2/tests/test_receipts.py` — canonical receipt
  self-hash, accepted-versus-rejected state, five boundary classifications, JSON-only
  Markdown determinism/failure, reviewer-override rejection, and finalization cases.

Wave 0 is fully specified but not yet complete: these files are created during execution
by Plans 01–04 and do not exist at planning time. Therefore `wave_0_complete` and
`nyquist_compliant` remain `false` until the files exist, the mapped commands pass, and
the validation lifecycle is promoted by `$gsd-validate-phase 1`.

---

## Required State-Aware Checks

### Real frozen-contract rejected path

After Plan 03, inspect
`bundles/rejected/pr-2192-current-head/attempt-receipt.json` and run the source-decision
validator. The evidence must name the frozen pin, observed head, pinned tree, and
`PR_PIN_NOT_REACHABLE`; the construction/finalization command must return nonzero and
must expose no accepted generation, accepted status, or downstream-eligible root.

### Synthetic accepted/offline path

`tests.test_bundle_verifier` must construct a disposable accepted candidate, embed and
root the verifier, copy the generation outside the repository, and invoke it using the
current Python executable while:

- `.git` and repository modules are absent;
- a Git shim fails every invocation;
- socket/network access is blocked; and
- only bundle-relative regular files and directories are readable.

The same suite must tamper every top-level and per-snapshot
generation/`root_sha256`/`manifest_sha256` binding, snapshot identity, final manifest
self-digest, raw/derived bytes, and embedded verifier bytes and prove each returns nonzero.

### Integrity receipt semantics

`tests.test_receipts` must prove that:

- the JSON self-hash omits only `receipt_sha256`;
- the receipt contains exactly one accepted generation identity or one rejected-attempt
  identity, never both;
- all five boundary classifications remain visible, including pre-existing `.DS_Store`;
- Markdown reads validated JSON only and is byte-identical on rerender;
- Markdown failure leaves valid JSON authoritative but makes the reviewer package
  incomplete/nonzero; and
- the unresolved #2192 route is a canonical blocked/fail receipt, never a passing zero.

---

## Manual-Only Verifications

| Plan / task | Behavior | Requirement | Why Manual | Test instructions |
|-------------|----------|-------------|------------|-------------------|
| 01 / 01-01-03 | Approve the immutable phase-start baseline and exact control-file allowlist | TS-01 | Start-state attribution is a costly human authority boundary | Inspect HEAD, staged/tracked/untracked state, every pre-existing `.DS_Store`, exact allowlist, baseline/allowlist hashes, and overwrite refusal; approve or restart with a new baseline generation |
| 03 / 01-03-02 | Resolve the frozen PR #2192 mismatch and exact consumed-file inventory | TS-02 | The current pin is not reachable from the PR head and the frozen contract does not enumerate exact consumed paths | Compare the Git-native rejected receipt with the frozen contract; choose `record-red-blocker` or authorize a versioned correction with exact PR/pin and path/role entries; never waive ancestry or raw-byte custody |
| 04 / 01-04-03 | Accept, dispute, or block the final source/boundary package | TS-01, TS-02 | Only the reviewer can authorize downstream use of one machine-eligible accepted identity | Recompute baseline/manifest/root/receipt hashes, rerun copied-bundle offline replay, inspect environment route/incident evidence, inspect every boundary classification, compare Markdown facts with JSON, and approve only when all automated gates already pass |

---

## Validation Sign-Off

- [x] All 11 current tasks have an automated or deterministic verification command.
- [x] All 11 current tasks identify their Wave 0 test file/fixture dependency.
- [x] Sampling continuity has no three consecutive tasks without automated verification.
- [x] Environment evidence, real #2192 rejection, copied-bundle offline replay,
  snapshot-binding tamper, receipt semantics, boundary classification, and reviewer gates
  are represented.
- [x] No watch-mode flags or third-party test dependency is planned.
- [ ] Wave 0 files exist and every mapped command passes.
- [ ] Required reviewer dispositions are recorded against exact artifact hashes.
- [ ] `$gsd-validate-phase 1` promotes the document and sets
  `nyquist_compliant: true` only after execution evidence exists.

**Approval:** validation graph reconciled; execution and reviewer sign-off pending.
