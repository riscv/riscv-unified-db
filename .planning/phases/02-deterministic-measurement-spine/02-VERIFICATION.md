---
phase: 02-deterministic-measurement-spine
verified: 2026-08-01T21:09:50Z
status: gaps_found
next_action: "Critical custody gaps found. Plan and implement the fixes, then re-run verification."
next_command: "/gsd:plan-phase 02 --gaps"
score: "31/35 must-haves verified"
behavior_unverified: 0
overrides_applied: 3
re_verification:
  previous_status: gaps_found
  previous_score: "33/35"
  gaps_closed:
    - "CR-01: adversarial-report formal-attempt lineage now derives from the supplied replay-validated formal/completed attempt."
    - "CR-02: post-authority adapter source/gold conflicts retain source identity and complete typed provenance."
    - "WR-01: adapter subprocess tests use sys.executable."
  gaps_remaining:
    - "Authoritative leaf paths are inspected and then reopened by pathname in H1, preflight, and the adapter."
  regressions: []
overrides:
  - must_have: "No Phase 1 custody module, accepted bundle byte, registry byte, source-authority byte, core UDB schema, generated data, model, external API, publication state, or remote repository is modified."
    reason: "Accepted only for commit 9d641ec8 in experiments/specchoice-v1.3.2/src/specchoice_evidence/filesystem.py: its descriptor-bound read_authoritative_file() single-descriptor leaf-read TOCTOU hardening. No other Phase 1 file, custody weakening, semantic rewrite, evidence mutation, authority expansion, remote/publication action, modification, or exception is accepted."
    accepted_by: "developer"
    accepted_at: "2026-08-01T07:25:55.903Z"
  - must_have: "The focused four-module pre-H1 suite passes without modifying or weakening any Phase 1 custody module, accepted byte, source-authority record, or live-boundary assertion."
    reason: "Accepted only for commit 9d641ec8 in experiments/specchoice-v1.3.2/src/specchoice_evidence/filesystem.py: its descriptor-bound read_authoritative_file() single-descriptor leaf-read TOCTOU hardening. No other Phase 1 file, custody weakening, semantic rewrite, evidence mutation, authority expansion, remote/publication action, modification, or exception is accepted."
    accepted_by: "developer"
    accepted_at: "2026-08-01T07:25:55.903Z"
  - must_have: "The final five-module focused Phase 2 suite passes without modifying or weakening any Phase 1 custody module, accepted byte, source-authority record, or live-boundary assertion."
    reason: "Accepted only for commit 9d641ec8 in experiments/specchoice-v1.3.2/src/specchoice_evidence/filesystem.py: its descriptor-bound read_authoritative_file() single-descriptor leaf-read TOCTOU hardening. No other Phase 1 file, custody weakening, semantic rewrite, evidence mutation, authority expansion, remote/publication action, modification, or exception is accepted."
    accepted_by: "developer"
    accepted_at: "2026-08-01T07:25:55.903Z"
gaps:
  - truth: "Phase 2 consumes only accepted-v2 authoritative bytes through the no-follow custody boundary; a substituted leaf is rejected before any semantic, H1, or evidence-span use."
    status: failed
    reason: "Three consumers inspect a path and then reopen it with Path.read_bytes(). A replacement between those operations can make them consume an external symlink target or block on a FIFO. The existing descriptor-bound read_authoritative_file() is not used on these paths."
    artifacts:
      - path: "experiments/specchoice-v1.3.2/src/specchoice_measurement/h1.py"
        issue: "_read_canonical() (lines 41-52) and validate_h1_packet() (lines 270-287) call inspect_authoritative_path() followed by Path.read_bytes()."
      - path: "experiments/specchoice-v1.3.2/src/specchoice_measurement/preflight.py"
        issue: "_source_bytes_by_fixture() (lines 37-59) inspects each fixture source and then reopens it by pathname."
      - path: "experiments/specchoice-v1.3.2/src/specchoice_measurement/adapter.py"
        issue: "_raw_identity() (lines 120-134) has the same inspect-then-read sequence for every score-bearing raw file."
    missing:
      - "Replace each authoritative regular-file inspect-then-read sequence with read_authoritative_file(root, relative_path), and parse/use only its returned bytes."
      - "Add deterministic race regressions that swap a checked H1 packet, Markdown projection, decision, adapter raw leaf, and preflight fixture source immediately before os.open; each must fail closed without consuming external bytes or blocking on a special file."
human_verification:
  - test: "Confirm the separately recorded H1 reviewer approval for packet 4482bfe4c28a825e86365420c071ed267afc3d0370ce333e4cdd16916b58c81c."
    expected: "The approval is an explicit human act for all 11 semantics, is local-Phase-3-only, and does not authorize publication."
    why_human: "Code proves that an approved JSON decision raises H1_MANUAL_AUTHORIZATION_REQUIRED and that publication is false; it cannot prove who authored an external/manual approval."
---

# Phase 2: Deterministic Measurement Spine Verification Report

**Phase Goal:** As a human RISC-V reviewer, I want to trust the experiment's adjudication semantics and diagnostics, so that I can review the measurement spine before any frame, retrieval, or model result is considered.

**Verified:** 2026-08-01T21:09:50Z
**Status:** gaps_found  
**Re-verification:** Yes — after Plans 02-06 and 02-07

## Escalation Gate

The phase cannot pass. Plan 02-07 genuinely closes the two earlier implementation blockers: the forged formal-attempt digest is rejected when validation receives a real replay-validated formal attempt, and an adapter source/gold conflict keeps the verified source identity and typed provenance while exposing zero records. The focused suite and all stored normal-path artifacts therefore pass.

That evidence does not establish the required custody boundary. `read_authoritative_file()` was created to bind path inspection and byte consumption to one `O_NOFOLLOW` descriptor, but Phase 2 still performs inspection and a later path-based read in H1, preflight, and the adapter. A minimal isolated reproduction inspected a regular file, replaced it with a symlink, then read external bytes successfully (`inspect_then_Path.read_bytes=EXTERNAL_BYTES`). This is an observable TOCTOU defect, not an uncertain or cosmetic review concern.

## User Flow Coverage

| Step | Expected | Evidence in codebase | Status |
| --- | --- | --- | --- |
| Inspect frozen source/gold semantics | One accepted-v2 11-fixture/28-raw interpretation is active. | Source-authority validator returned `status: valid`, `fixture_count: 11`, and `raw_file_count: 28`. | ✓ VERIFIED |
| Score the canonical golden input | Six positives accept, four negatives remain unsurfaced, and the candidate is surfaced then `classify_out`. | The 61-test focused suite, including scoring tests, passed. | ✓ VERIFIED |
| Reject malformed canonical input | Unknown keys, invalid enums, duplicate/conflicting inputs, and noncanonical no-findings reject without repair. | Parsing/preflight tests passed; the current schema and named legacy ingress are substantive and wired. | ✓ VERIFIED |
| Trace diagnostics and evidence | Rejected or warning outcomes are attributable to stable structured fields and accepted source bytes. | Stable diagnostics work on the normal path, but the adapter/preflight can reopen a post-inspection substituted source leaf. | ✗ FAILED — BLOCKER |
| Review H1 | Packet is hash-bound, local-only, and cannot authorize publication or machine approval. | Packet validation passed and requires `external_publication_authorized: false`; approved JSON decisions deliberately raise `H1_MANUAL_AUTHORIZATION_REQUIRED`. H1 itself can still reopen a substituted packet/Markdown/decision leaf. | ✗ FAILED — BLOCKER |
| Outcome | Reviewer can trust the spine before later work. | The custody policy is bypassable on critical source and H1 read paths. | ✗ FAILED — BLOCKER |

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | TS-03 golden scoring covers the exact 11 accepted-v2 fixtures, including surfaced-then-`classify_out` candidate semantics. | ✓ VERIFIED | Focused 61-test run passed; formal attempt validates as `formal/completed`; source authority validates 11/28. |
| 2 | TS-04 canonical ingress strictly rejects unknown, invalid, duplicate, and noncanonical no-finding inputs without repair. | ✓ VERIFIED | `strict_json.py` plus `preflight.py` are exercised by the focused parsing tests. |
| 3 | TS-05 preserves stable structured diagnostics and keeps `ACCEPTED_PARAMETER_NAME_MISSING` warning-only. | ✓ VERIFIED | Scoring/adversarial-oracle tests and the v2 report validator passed; CR-02 regression passes. |
| 4 | CR-01 ties adversarial-report validation to an independently verified `formal/completed` attempt rather than a report-declared digest. | ✓ VERIFIED | `validate_adversarial_report()` validates the supplied path first; the named forged-digest regression passes. |
| 5 | CR-02 preserves verified source identity and complete source/gold conflict provenance while returning no score-eligible records. | ✓ VERIFIED | The named public-builder provenance regression passes. |
| 6 | D-01/D-02/D-06/D-08 authoritative paths are consumed under the Phase 1 no-follow custody policy. | ✗ FAILED — BLOCKER | Adapter, preflight, and H1 inspect first, then call `Path.read_bytes()` on the same pathname. |
| 7 | D-09/D-10/D-11/D-12 maintain complete preflight, warning separation, immutable attempts, and formal/diagnostic-only separation. | ✓ VERIFIED | Focused tests pass; the stored formal attempt and adversarial report validate without regeneration. |
| 8 | D-13/D-14 machine-created approval remains impossible and actual reviewer approval remains a separate human checkpoint. | ⚠️ HUMAN CHECK REQUIRED | `h1.py` rejects any approved JSON decision with `H1_MANUAL_AUTHORIZATION_REQUIRED`; authorship of a manual approval is not programmatically provable. |
| 9 | D-15/D-16 H1 binds only verified, contained local artifacts and remains local-only/non-public. | ✗ FAILED — BLOCKER | Publication flag is correctly false, but packet, Markdown, decision, and supporting canonical values can be reopened after inspection. |
| 10 | Frozen accepted-v2 evidence, source-authority, Phase 1 v7 artifacts, and core UDB remain unchanged, apart from the accepted `filesystem.py` hardening override. | ✓ PASSED (override) | `git diff a650945d..HEAD` shows no changes under accepted bundle, source-authority, v7 baseline, v9 receipts, or Phase 1 planning; the sole Phase 1 code path changed is the three-times-scoped `filesystem.py` override. |
| 11 | The repository retains the specified focused and phase-aware regression partition. | ✓ VERIFIED | 61/61 focused tests passed. Discovery found 132 methods: 127 green plus the exact five expected-red methods, producing five failures and one error. |

**Score:** 31/35 de-duplicated plan must-haves verified. The three accepted custody-scope statements count as `PASSED (override)`; the four affected D-01/D-02/D-06/D-08/D-15/D-16 custody truths are not verified.

### D-01 through D-16 Contract Coverage

| Contract | Status | Evidence |
| --- | --- | --- |
| D-01, D-02 | ✗ FAILED | Accepted authority validates, but adapter `_raw_identity()` reopens checked raw leaves by pathname. |
| D-03, D-04 | ✓ VERIFIED | One versioned 11/28 batch, bounded fields, deterministic rule hash, and no mixed batch are exercised by tests. |
| D-05, D-07 | ✓ VERIFIED | Closed current schema and explicit legacy-only `reject` normalization are covered. |
| D-06, D-08 | ✗ FAILED | Preflight source evidence uses inspect-then-read, so exact bytes can be consumed outside the protected descriptor boundary. |
| D-09, D-10 | ✓ VERIFIED | Complete preflight and warning-only accepted-name handling are covered by focused tests. |
| D-11, D-12 | ✓ VERIFIED | Formal and diagnostic-only attempts validate separately with immutable no-replace artifacts. |
| D-13, D-14 | ⚠️ HUMAN CHECK REQUIRED | Code enforces the three-state machine/no-machine-approval guard; human authorship remains a manual fact. |
| D-15, D-16 | ✗ FAILED | Normal H1 bindings validate, but H1 canonical/Markdown reads do not retain the checked descriptor. |

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `phase2/source-authority.json` and accepted-v2 bundle | Finite 11/28 authority | ✓ VERIFIED | Validator returned the pinned generation, commit/tree, hashes, and local-only state. |
| `src/specchoice_measurement/{strict_json.py,diagnostics.py,scoring.py,attempts.py}` | Strict deterministic measurement and immutable attempt boundary | ✓ VERIFIED | Substantive, wired, and exercised by the 61-test focused run. |
| `src/specchoice_measurement/adapter.py` | Accepted-only adapter with custody-bound raw reads | ✗ FAILED | Substantive and normally wired, but `_raw_identity()` reopens a checked leaf. |
| `src/specchoice_measurement/preflight.py` | Exact authoritative evidence-span input | ✗ FAILED | `_source_bytes_by_fixture()` reopens a checked fixture source. |
| `src/specchoice_measurement/h1.py` and H1 v2 packet | Contained hash-bound local review evidence | ✗ FAILED | `_read_canonical()` and Markdown validation reopen checked leaves. |
| `src/specchoice_measurement/cli.py`, `domain.py`, and Plan 02-07 tests | CR-01/CR-02/WR-01 repair | ✓ VERIFIED | Explicit formal-attempt CLI propagation, typed provenance, and both named tests pass. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| Accepted-v2 authority | Adapter batch | Authority CLI + accepted-bundle verifier | ⚠️ PARTIAL — BLOCKER | Authority itself validates, but adapter raw-byte consumption is not descriptor-bound. |
| Adapter batch | Preflight/scorer | Valid all-11 complete batch only | ✓ WIRED | Focused tests cover score eligibility and no formal metrics on invalid input. |
| Fixture source bytes | Evidence-span validation | SHA-256 plus exact byte range/text | ✗ NOT WIRED — BLOCKER | Preflight reopens after inspection, so the checked leaf is not necessarily the consumed leaf. |
| Verified formal attempt | Adversarial report | Explicit `--formal-attempt` and replay validation | ✓ WIRED | CR-01 targeted regression passed. |
| Verified formal/adversarial evidence | H1 packet/Markdown/decision | Recomputed bindings and canonical projection | ✗ PARTIAL — BLOCKER | Normal hashes validate, but H1 reads are still path-reopenable. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| Adapter batch | 11 records / 28 raw identities | Active accepted-v2 authority | Yes on ordinary execution; source authority is valid. | ⚠️ UNSAFE FLOW |
| Preflight source map | Raw fixture source bytes | Adapter-declared accepted bundle paths | Bytes are hash-compared, but originate from a second pathname open. | ✗ HOLLOW CUSTODY |
| H1 canonical values | Packet, decision, Markdown, formal diagnostics | Repository-contained paths | Normal H1 validation succeeds, but checked identity and consumed bytes are split. | ✗ HOLLOW CUSTODY |
| Adversarial report lineage | `formal_attempt_sha256` | Supplied replay-validated formal attempt | Yes. | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| CR-01 forged formal digest rejects | `python3 -m unittest tests.test_measurement_attempts.MeasurementAttemptTests.test_adversarial_report_rejects_forged_formal_attempt_binding -q` | 1 passed | ✓ PASS |
| CR-02 public conflict retains provenance | `python3 -m unittest tests.test_measurement_adapter.MeasurementAdapterTests.test_public_builder_preserves_conflict_provenance -q` | 1 passed | ✓ PASS |
| Focused Phase 2 + filesystem suite | `python3 -m unittest tests.test_measurement_adapter tests.test_measurement_parsing tests.test_measurement_scoring tests.test_measurement_attempts tests.test_measurement_h1 tests.test_filesystem_boundary -q` | 61 passed | ✓ PASS |
| Accepted-v2 authority | `python3 -m specchoice_evidence.cli validate-phase2-source-authority ...` | `status: valid`, 11 fixtures, 28 raw files | ✓ PASS |
| Stored formal/adversarial/H1 evidence | `validate-attempt`; `validate-adversarial-report --formal-attempt`; `validate-h1-packet` | All exit 0 | ✓ PASS |
| Inspect/read race | Isolated temp-root reproduction: inspect regular leaf, replace with symlink, then `Path.read_bytes()` | `inspect_then_Path.read_bytes=EXTERNAL_BYTES` | ✗ FAIL — BLOCKER |
| Discovery partition | `unittest.defaultTestLoader.discover("tests")` partitioned by runtime IDs | 132 total; 127 green; exact five expected-red produce 5 failures and 1 error | ✓ PASS |

### Probe Execution

No declared or conventional `scripts/*/tests/probe-*.sh` probe exists for this phase. **SKIPPED (no phase probe entry points).** The seven spec-less assumptions remain explicit and were not promoted to evidence.

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| TS-03 | 02-01, 02-03, 02-04, 02-05, 02-07 | Versioned adapter and deterministic all-11 golden runner | ✗ BLOCKED | Normal scoring works, but score-bearing raw-file reads can escape the accepted custody boundary. |
| TS-04 | 02-02, 02-04, 02-05, 02-07 | Closed canonical adjudication schema/no silent repair | ✓ SATISFIED | Focused parsing/preflight tests pass. |
| TS-05 | 02-02 through 02-07 | Stable structured diagnostics and warning-only identity absence | ✗ BLOCKED | Diagnostics are stable on normal input, but evidence/H1 diagnostic provenance can consume a substituted leaf. |

No orphaned Phase 2 requirement was found. The later milestone phases do not explicitly schedule repair of this no-follow custody regression, so it is not deferred.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `src/specchoice_measurement/h1.py` | 43-46, 281-282 | Inspect then reopen authoritative leaf | 🛑 BLOCKER | Packet, decision, canonical artifacts, and Markdown can cross the path boundary after inspection. |
| `src/specchoice_measurement/preflight.py` | 51-54 | Inspect then reopen fixture source | 🛑 BLOCKER | Evidence validation can consume a substituted source leaf. |
| `src/specchoice_measurement/adapter.py` | 124-131 | Inspect then reopen score-bearing raw leaf | 🛑 BLOCKER | Adapter can consume external bytes despite accepted-v2-only policy. |

No Phase 2 `TBD`, `FIXME`, `XXX`, `TODO`, `HACK`, placeholder, or empty implementation marker was found. The ambient `.DS_Store` files and the excluded untracked `02-REVIEW-FIX 2.md` were not read, used, or modified.

### Human Verification Required

### 1. H1 independent approval record

**Test:** Inspect the separately recorded approval for packet `4482bfe4c28a825e86365420c071ed267afc3d0370ce333e4cdd16916b58c81c` and all 11 review semantics.

**Expected:** It is an explicit human, local-Phase-3-only decision; `external_publication_authorized` remains `false`.

**Why human:** Code intentionally refuses to treat any approved JSON file as authority. It cannot attest who made a manual approval. This check cannot waive the custody blocker.

### Gaps Summary

Plan 02-07 closed the preceding formal-lineage and conflict-provenance defects, and its 61-test / 132-discovery regression claims are reproducible. The phase nevertheless fails its central trust promise because three active consumers ignore the descriptor-bound reader that Phase 1 now provides:

1. **Authoritative leaf reads are not atomic with their custody checks.** Replace the H1, preflight, and adapter inspect-then-read flows with `read_authoritative_file()` and add race/special-file regressions at every affected public boundary.

This is one root-cause gap with three production call sites. It is not addressed by a later phase and cannot be accepted by the existing narrow `filesystem.py` override, because the override added the safe primitive rather than waiving its use.

---

_Verified: 2026-08-01T21:09:50Z_
_Verifier: the agent (gsd-verifier)_
