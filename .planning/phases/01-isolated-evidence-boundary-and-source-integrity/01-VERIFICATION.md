---
phase: 01-isolated-evidence-boundary-and-source-integrity
verified: 2026-07-30T16:07:15Z
status: gaps_found
score: 8/9 must-haves verified
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "Only experiments/specchoice-v1.3.2/ and the exact control-file allowlist are attributable Phase 1 changes; every other out-of-boundary delta fails closed."
    status: failed
    reason: "01-REVIEW.md was added after baseline commit 30d192d7 outside the immutable allowlist. The runtime boundary guard also omits it because it inspects only uncommitted Git deltas, not baseline HEAD through current HEAD."
    artifacts:
      - path: ".planning/phases/01-isolated-evidence-boundary-and-source-integrity/01-REVIEW.md"
        issue: "Committed by 0a52078c after the active phase-start baseline, but is neither under experiments/specchoice-v1.3.2/ nor an exact allowed control file."
      - path: "experiments/specchoice-v1.3.2/src/specchoice_evidence/baseline.py"
        issue: "capture_current_paths() uses git diff/git diff --cached/current untracked paths only, so committed post-baseline changes are invisible to check-boundary."
    missing:
      - "A fail-closed committed-history comparison from the recorded phase-start commit to the reviewed revision, or another immutable audit mechanism that includes all post-baseline changes."
      - "Developer-directed recovery for the already-recorded out-of-boundary review artifact; do not silently reclassify it or widen the immutable baseline."
---

# Phase 1: Isolated Evidence Boundary and Source Integrity Verification Report

**Phase Goal:** The operator and reviewer can work from a self-contained experiment boundary whose public source identity is independently verifiable.

**Verified:** 2026-07-30T16:07:15Z

**Status:** gaps_found

**Re-verification:** No — initial verification

## MVP Framing Discrepancy

ROADMAP marks the phase `mvp`, but its goal is not a valid required user story. The canonical validator returned `valid: false` because it lacks the required `As a …, I want to …, so that ….` form. Consequently, a formal MVP User Flow Coverage/UAT cannot be generated. This is a planning-process warning, not an alternative acceptance of the technical evidence below; correct the goal through `/gsd mvp-phase 1` before an MVP-form UAT is attempted.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Operator can create, test, and inspect the dependency-light prototype without changing core UDB schemas, generated architecture data, or root dependency state. | ✓ VERIFIED | `git diff 30d192d7..HEAD` contains no changes under `spec/`, `cfgs/`, `gen/`, `backends/`, `tools/`, or root dependency manifests; implementation and 51 stdlib `unittest` tests are under `experiments/specchoice-v1.3.2/`. |
| 2 | Reviewer can verify every named snapshot and stable hashes for every consumed source file. | ✓ VERIFIED | `validate-source-decision` reported six snapshots and seven consumed files; both candidate and accepted generation recomputed core `6ca1f176…`, root `aacdda82…`, and the accepted snapshot manifest self-digest `1c81f84c…`. |
| 3 | Recorded environment decision is reproducible and retains the dependency-light fallback policy. | ✓ VERIFIED | Canonical environment receipt selects `standalone_first`, reports full UDB setup `attempted:false`/`required:false`, and carries the 90-minute cumulative-wall-clock policy; all nine environment tests passed within the 51-test suite. |
| 4 | Only the experiment root and exact control-file allowlist are attributable; all non-`.DS_Store` out-of-boundary changes fail closed. | ✗ FAILED — BLOCKER | `git diff --name-only 30d192d7..HEAD` found `.planning/phases/01-isolated-evidence-boundary-and-source-integrity/01-REVIEW.md` outside the fixed allowlist. Commit `0a52078c` added it after the baseline. `check-boundary` incorrectly reports zero violations because it does not inspect committed history. |
| 5 | Authoritative paths reject escapes, links, special files, mount uncertainty, and hardlink-dependent layouts. | ✓ VERIFIED | `test_filesystem_boundary` covers prefix collision, escape, symlink, FIFO, mount, hardlink, and baseline-overwrite paths; the full suite passed. |
| 6 | The accepted generation replays from bundle-relative Python stdlib code with no local Git object or network dependency. | ✓ VERIFIED | Full-suite copied-bundle process test passed with a failing Git shim and blocked sockets. Independent copied actual-bundle run from `/private/tmp/specchoice-phase1-replay.X4xUa7/bundle` passed with no `.git` and `PATH=/nonexistent`. |
| 7 | Canonical JSON receipt is authoritative and Markdown is a deterministic JSON-only projection; rejected #2192 evidence cannot pass. | ✓ VERIFIED | `finalize-review` passed for receipt SHA `6162288c…`; receipt tests cover Markdown failure and rejected-source failure. `render_markdown()` validates and renders only receipt fields, while `validate_receipt()` rejects a passing rejected-attempt identity. |
| 8 | Local acceptance binds the exact verifier-rooted generation and forbids external publication. | ✓ VERIFIED | Valid reviewer decision binds generation `source-contract-v2-pr2192-86a0021b-verifier-rooted-v1`, core/root/snapshot hashes, and `external_publication_authorized:false`; `finalize-review` passed. |
| 9 | The frozen uncorrected PR #2192 route remains rejected rather than being silently accepted. | ✓ VERIFIED | `test_frozen_pr_2192_is_a_rejected_receipt_without_accepted_identity` passed; the historical receipt is separately hash-bound by the source decision. |

**Score:** 8/9 truths verified (0 present-but-behavior-unverified).

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `baselines/phase-start-v2.json` | Immutable active start state | ✓ VERIFIED | Canonical validation passed; SHA-256 is `e8f7e153ffbc5285b361039153f8eea6205448e9f82e2b14efa9af3e74912e15`; restart lineage to v1 validated. |
| `config/boundary_allowlist.json` and `baseline.py` | Exact boundary enforcement | ⚠️ HOLLOW — BLOCKER | Allowlist is narrow and correct, but `baseline.py:168-176` collects only live worktree/index/untracked paths and therefore misses `01-REVIEW.md` in committed history. |
| `environment.py` plus canonical/audit environment records | Stable standalone-first environment contract | ✓ VERIFIED | Decision/audit one-way digest link and incident state-machine tests pass. |
| `git_proof.py`, `bundle.py`, source decision, candidate and accepted manifests | Source proof, custody, content identity | ✓ VERIFIED | Local validators and candidate verification recomputed the expected identities; seven raw consumed files are recorded. |
| `bundles/accepted/source-contract-v2-pr2192-86a0021b-verifier-rooted-v1/verify_bundle.py` | Bundle-local offline replay entry point | ✓ VERIFIED | Executed successfully from a copied bundle with no repository metadata or usable `PATH`. |
| `integrity-receipt.json`, Markdown projection, reviewer decision | Local-MVP integrity gate | ✓ VERIFIED | Receipt self-hash and finalization are valid; Markdown exactly matches JSON-only renderer. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| Active baseline | Boundary receipt/check | `phase_start_baseline_sha256` and classifications | ✗ NOT WIRED FOR COMMITTED DELTAS | Both the current receipt and `check-boundary` cite the v2 SHA, but the classifier’s Git queries omit committed changes after the baseline. |
| Source decision/proposal | Candidate and accepted manifests | exact snapshot/request inventory, raw hashes, core/root/binding recomputation | ✓ WIRED | Source decision validation and candidate verification passed; tamper coverage passed in `test_bundle_verifier`. |
| Embedded verifier | Accepted bundle | bundle-relative `verify_bundle.py` plus rooted copied verifier modules | ✓ WIRED | Actual copied-bundle replay passed; full test blocks Git and sockets. |
| Canonical receipt | Markdown | `render_markdown(validate_receipt(...))` | ✓ WIRED | `finalize-review` passed and source makes no filesystem/Git/hash lookup during rendering. |

### Data-Flow Trace (Level 4)

No UI or dynamic rendering artifacts are in scope. The applicable data flows are the source-decision inventory to rooted raw blobs, and canonical receipt JSON to Markdown; both were traced above. The boundary flow is incomplete for committed deltas and is the blocking gap.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Full local contract | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -v` | 51 tests passed in 3.995s; expected tamper diagnostic emitted within a passing negative test. | ✓ PASS |
| Boundary state before report | `… cli check-boundary --baseline baselines/phase-start-v2.json` | 0 reported blockers; result is contradicted by independent committed-history audit. | ✗ FAIL |
| Active source/receipt identity | `validate-baseline`, `validate-restart-lineage`, `validate-control-decision`, `validate-source-decision`, `verify-candidate`, `finalize-review` | All passed with the stated v2 baseline and accepted local identity. | ✓ PASS |
| Actual offline replay | copied `verify_bundle.py` with `.git` absent and empty `PATH` | `bundle verified`. | ✓ PASS |

### Probe Execution

Step 7c: SKIPPED — no phase-declared `probe-*.sh` scripts or probe PASS-marker contract exists. The Python test suite and copied-bundle replay are the declared runnable checks.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| TS-01 | 01-01, 01-02, 01-04 | Dependency-light isolated experiment with no core schema/generated-data modification. | ✗ BLOCKED | Core/dependency isolation is intact, but the frozen D-14 exact-boundary control fails for the post-baseline `01-REVIEW.md` change and the guard cannot observe this class of change. |
| TS-02 | 01-03, 01-04 | Source manifest pins named PR snapshots and hashes every consumed file. | ✓ SATISFIED | Six snapshot identities, seven raw files, core/root/self-digest verification, rejected #2192 evidence, and no-Git/no-network replay all passed. |

No requirement mapped to Phase 1 is orphaned: the plans cover both TS-01 and TS-02, and REQUIREMENTS maps only those two IDs to this phase.

### Anti-Patterns and Review Findings

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `.planning/.../01-REVIEW.md` | whole artifact | Post-baseline out-of-allowlist committed change | 🛑 BLOCKER | Violates D-14 and user-frozen fail-closed boundary rule. |
| `src/specchoice_evidence/source_contract.py` | 236-261, 316-324 | CR-01: reviewer authorization is a fixed token/booleans, not independently authenticated | ⚠️ WARNING | Real human provenance cannot be mechanically proved. Frozen TS-01/TS-02 require a recorded human decision, not a signature trust root; therefore this is not the observed boundary blocker, but it must not be presented as authentication. |
| `src/specchoice_evidence/receipt.py` | 270-281 | CR-02 / WR-02: receipt paths use unconditional writes and write Markdown before final JSON | ⚠️ WARNING | Existing receipt packages can be replaced or left split-brain by a later command. Existing bundle generations remain create-once; frozen requirements do not expressly mandate create-once receipt filenames, so this is hardening debt rather than a second proven goal failure. |
| `src/specchoice_evidence/cli.py` | 311-316 | WR-01: candidate construction parses the decision without the canonical-byte check used by `validate-source-decision` | ⚠️ WARNING | Candidate construction can bypass the advertised canonical-decision gate. It does not grant external publication and current accepted bytes verify, but should be unified before relying on that command as decision evidence. |

No unreferenced `TBD`, `FIXME`, or `XXX` debt marker was found in Phase 1 implementation, tests, or receipts.

## Gaps Summary

Phase 1 cannot pass its frozen fail-closed boundary contract. The sole code review document was committed after the active baseline at a path not listed in that baseline’s exact allowlist. This is not a `.DS_Store` exception. The runtime guard returns a misleading clean result because its delta source stops at the current worktree/index and does not compare the baseline commit to the reviewed revision.

No later roadmap phase specifically owns Phase 1 boundary recovery, so this gap is not deferred. Recovery needs a developer decision: preserve the current evidence, then use an explicit D-15-style recovery/change-control path and make the guard audit committed post-baseline changes before re-verification. Do not silently delete, reclassify, or allowlist the existing violation.

---

_Verified: 2026-07-30T16:07:15Z_

_Verifier: the agent (gsd-verifier)_
