---
phase: 02-deterministic-measurement-spine
verified: 2026-08-01T17:39:10.535Z
status: gaps_found
next_action: "Critical implementation gaps found. Plan and implement the fixes, then re-run verification."
next_command: "/gsd:plan-phase 02 --gaps"
score: "33/35 must-haves verified"
behavior_unverified: 0
overrides_applied: 3
re_verification:
  previous_status: gaps_found
  previous_score: "32/35"
  gaps_closed:
    - "Phase 2 does not modify any Phase 1 custody module."
    - "The Phase 2 MVP goal is a valid User Story that can be verified under MVP-mode rules."
  gaps_remaining:
    - "An adversarial report must validate its formal-attempt lineage instead of trusting a self-declared digest."
    - "An adapter source/gold conflict must retain auditable structured provenance and field/value diagnostics."
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
  - truth: "A separately validated adversarial report has a verified binding to one completed formal attempt rather than trusting a digest declared by that report."
    status: failed
    reason: "validate_adversarial_report() reconstructs expected bindings using bindings.formal_attempt_sha256 from the untrusted report itself. It never validates the formal attempt or compares the declared digest with a verified completed formal attempt."
    artifacts:
      - path: "experiments/specchoice-v1.3.2/src/specchoice_measurement/cli.py"
        issue: "Lines 263-265 self-derive the expected formal digest from report bindings. A canonical temporary v2 report with that value replaced by 64 zeroes still validated successfully."
      - path: "experiments/specchoice-v1.3.2/tests/test_measurement_attempts.py"
        issue: "The adversarial-report tests cover case/attempt tampering but contain no formal_attempt_sha256 lineage-tamper regression."
    missing:
      - "Validate the one bound formal attempt (or take its path explicitly), require role=formal and status=completed, and derive the expected digest from that verified attempt."
      - "Add a fail-first regression that changes only formal_attempt_sha256 and requires ADVERSARIAL_REPORT_INVALID."
  - truth: "A rejected adapter source/gold/expected conflict remains auditable through stable diagnostics containing fixture identity, field, expected/observed values, source hashes, and already-verified source identity."
    status: failed
    reason: "The adapter catch-all replaces a record-level AdapterError with _invalid_batch(... source_identity={}, code=...), and _invalid_batch emits only code and severity. The mandated conflict provenance is discarded."
    artifacts:
      - path: "experiments/specchoice-v1.3.2/src/specchoice_measurement/adapter.py"
        issue: "Lines 295-304 construct a diagnostic without fixture_id, field, expected, observed, or source hashes; lines 337-343 replace verified source identity with {}."
      - path: "experiments/specchoice-v1.3.2/tests/test_measurement_adapter.py"
        issue: "No regression asserts that a source/gold disagreement preserves full diagnostic provenance."
    missing:
      - "Carry a typed conflict diagnostic through AdapterError and retain the verified source identity when publishing the invalid zero-record batch."
      - "Add a regression for a real source/gold/expected conflict that asserts every required diagnostic field and source hash."
---

# Phase 2: Deterministic Measurement Spine Verification Report

**Phase Goal:** As a human RISC-V reviewer, I want to trust the experiment's adjudication semantics and diagnostics, so that I can review the measurement spine before any frame, retrieval, or model result is considered.

**Verified:** 2026-08-01T17:39:10.535Z
**Status:** gaps_found  
**Re-verification:** Yes — after Plan 02-06 governance-gap closure

## Escalation Gate

Plan 02-06 genuinely closes the two prior *governance* causes of the `gaps_found` verdict: the three exact custody exceptions are developer-accepted overrides limited to commit `9d641ec8` and `src/specchoice_evidence/filesystem.py`, and the stored MVP goal now passes the centralized user-story validator. Its two task commits modify only the verification report and ROADMAP goal; neither changes `cli.py`, `adapter.py`, or their tests.

The current canonical code review is nevertheless `issues_found` with CR-01 and CR-02. Both findings are reproduced below. They prevent a reviewer from trusting diagnostic provenance and an adversarial report's asserted formal lineage. This is an implementation revision gate, not a new authority decision: an H1 approval, a broader override, or a human acknowledgement cannot repair either defect.

## User Flow Coverage

| Step | Expected | Evidence in codebase | Status |
| --- | --- | --- | --- |
| Inspect frozen source/gold semantics | One active accepted-v2 11-fixture/28-raw interpretation is available. | `validate-phase2-source-authority` returned `status: valid`, `fixture_count: 11`, `raw_file_count: 28`. | ✓ VERIFIED |
| Inspect deterministic prediction validation | Unknown keys, invalid forms, duplicate conflicts, and noncanonical no-finding forms reject without repair. | `strict_json.py`/preflight/scoring coverage is included in the 59-test focused run. | ✓ VERIFIED |
| Trace a rejected source/gold conflict | The reviewer receives enough structured diagnostic provenance to identify and reproduce the conflicting evidence. | `adapter.py` intentionally zeroes records, but also discards the field/value/raw-hash and source-identity evidence on this path. | ✗ FAILED — BLOCKER |
| Inspect adversarial diagnostics | The diagnostic-only report can be independently verified as bound to a completed formal attempt. | A copied canonical v2 report with only `formal_attempt_sha256` changed to 64 zeroes exited 0 from `validate-adversarial-report`. | ✗ FAILED — BLOCKER |
| Review H1 boundary | H1 remains human-authored, local-only, and cannot authorize publication. | v2 packet validator passed; packet and schema require `external_publication_authorized: false`; focused H1 tests passed. | ✓ VERIFIED |
| Outcome | Trust the adjudication semantics and diagnostics before later measurement work. | Critical audit/lineage defects above leave two adversarial/error paths untrustworthy. | ✗ FAILED — BLOCKER |

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Golden predictions score all 11 pinned fixtures, including surfaced-then-`classify_out` candidate behavior. | ✓ VERIFIED | The focused six-module run passed 59 tests; the active source authority validates 11 fixtures/28 raw files. |
| 2 | Unknown keys, invalid enums, duplicate/conflicting predictions, and every noncanonical no-finding form reject without silent repair. | ✓ VERIFIED | The strict parser, preflight, and scorer tests passed in the focused suite; no repair/default path was found in the canonical ingress. |
| 3 | Every failed or warning outcome is traceable to a stable diagnostic code and structured fields; missing accepted name stays warning-only without changing disposition. | ✗ FAILED — BLOCKER | CR-02: a source/gold conflict retains only `GOLD_NAME_MISMATCH` and `severity`; fixture, field, expected, observed, hashes, and source identity are absent. |
| 4 | A human can approve or dispute frozen gold interpretation without model output compensating for disputed semantics. | ✓ VERIFIED | H1 v2 packet validates, has 11 human signature slots, and keeps `external_publication_authorized: false`; no machine decision writer exists. |
| 5 | The adversarial diagnostic artifact is cryptographically and semantically bound to verified formal measurement lineage. | ✗ FAILED — BLOCKER | CR-01 reproduction accepted a self-declared all-zero formal attempt digest. |
| 6 | The three stale no-Phase-1-modification claims are accepted only as the precise tested TOCTOU exception. | ✓ PASSED (override) | Three exact overrides name only `9d641ec8`, `filesystem.py`, the descriptor-bound leaf-read hardening, developer acceptance, and one UTC timestamp. |

**Score:** 33/35 de-duplicated plan must-haves verified (0 present-but-behavior-unverified). The three historical custody must-haves count as `PASSED (override)`; CR-01 and CR-02 each fail a separate existing audit/lineage must-have.

### Plan 02-06 Closure Check

| Prior gap / Plan 02-06 truth | Result | Evidence |
| --- | --- | --- |
| Three exact custody overrides exist and are tightly scoped. | ✓ CLOSED | Frontmatter schema validates and contains exactly three overrides; `685fe846` changes only this report. |
| The pre-refresh historical report was preserved for verifier ownership. | ✓ CLOSED | Plan receipt and history show the executor only inserted override frontmatter before normal refresh. |
| MVP goal is centrally valid without scope drift. | ✓ CLOSED | `user-story.validate` returned `valid: true` with role, capability, and outcome; `5c384db4` changes only the ROADMAP goal line. |
| Local-only H1 / no-publication boundary remains unchanged. | ✓ VERIFIED | H1 schema and validated v2 packet retain `external_publication_authorized: false`; no model, remote, or publication capability is introduced. |
| Seven flagged spec-less probe assumptions remain explicit rather than silently promoted. | ✓ VERIFIED (governance) | Plan 02-06 records adjacency, empty, ordering, TS-04, and TS-05 assumptions as unresolved; this re-verification does not treat them as new positive evidence. |

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `phase2/source-authority.json` and accepted v2 bundle | Active finite 11/28 source authority | ✓ VERIFIED | CLI returned the exact active generation, 11 fixtures, and 28 raw files. |
| `src/specchoice_measurement/{strict_json.py,preflight.py,scoring.py,diagnostics.py}` | Closed parsing, deterministic scoring, stable diagnostics | ✓ VERIFIED | Substantive, wired modules exercised by the 59-test focused run. |
| `src/specchoice_measurement/adapter.py` | Fail-closed adapter that preserves complete conflict audit evidence | ✗ FAILED | Invalid batch is zero-record/fail-closed, but CR-02 discards required diagnostics and identity. |
| `src/specchoice_measurement/attempts.py` and formal attempt | Immutable, replayable formal measurement | ✓ VERIFIED | Focused attempt tests pass; H1 v2 packet validator recomputed bindings successfully. |
| `reports/h1/adversarial-oracle-results-v2.json` | Independently validated diagnostic-only report with verified formal lineage | ✗ FAILED | CR-01 shows the report's claimed formal digest is trusted rather than verified. |
| `src/specchoice_measurement/h1.py` and v2 packet/Markdown | Human-only H1 packet bound to current local evidence | ✓ VERIFIED | `validate-h1-packet` passed with packet SHA `4482bfe4…`; external publication is false. |
| `.planning/ROADMAP.md` | Valid Phase 2 MVP user story | ✓ VERIFIED | Central validator returned valid role/capability/outcome slots. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| Active accepted-v2 authority | Adapter batch | Phase-1 authority CLI and bounded adapter | ✓ WIRED | Source-authority CLI validates the finite source and adapter/scoring tests consume it. |
| Source/gold/expected files | Invalid adapter batch diagnostic | Typed conflict preservation | ✗ NOT WIRED — BLOCKER | Catch block rebuilds a diagnostic with only code/severity and replaces `source_identity` with `{}`. |
| Formal attempt | Adversarial oracle report | Verified formal attempt digest | ✗ NOT WIRED — BLOCKER | The validator compares report bindings to bindings reconstructed from the report's own digest. |
| Preflight | Scorer | Complete, zero-blocker all-11 gate | ✓ WIRED | Focused parser/scoring/attempt tests pass; invalid inputs have no formal metrics. |
| Formal attempt + adversarial report | H1 v2 packet | Recomputed current bindings and pure Markdown projection | ✓ WIRED | Current H1 packet validator passed; it additionally compares its formal attempt to the report binding. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| Adapter batch | 11 canonical records / 28 raw identities | Accepted-v2 bundle plus phase2 authority | Yes on the happy path; source authority validator passed. | ✓ FLOWING |
| Invalid adapter batch | Conflict provenance | Source/gold/expected disagreement | No: only code/severity survive; verified source identity is erased. | ✗ HOLLOW — BLOCKER |
| Adversarial report | `bindings.formal_attempt_sha256` | Report JSON itself rather than a verified formal attempt | No trusted upstream verification in standalone validation. | ✗ HOLLOW — BLOCKER |
| H1 v2 packet | Formal/adversarial/source bindings | Recomputed packet validation | Yes for the current packet; does not cure the standalone adversarial validator. | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Phase 2 measurement modules and filesystem boundary | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_measurement_adapter tests.test_measurement_parsing tests.test_measurement_scoring tests.test_measurement_attempts tests.test_measurement_h1 tests.test_filesystem_boundary -q` | 59 tests passed. | ✓ PASS |
| Active accepted-v2 source authority | `python3 -m specchoice_evidence.cli validate-phase2-source-authority ...` | `status: valid`, 11 fixtures, 28 raw files. | ✓ PASS |
| Tampered formal lineage must reject | `python3 -m specchoice_measurement.cli validate-adversarial-report --report /tmp/phase2-cr1.BkDhEo/adversarial-oracle-results-v2.json` | Exit 0 after changing only the report's formal digest to 64 zeroes. | ✗ FAIL — CR-01 reproduced |
| Adapter conflict must retain audit provenance | Controlled in-memory record-conflict injection through `build_pr2164_adapter_batch()` | `valid=False`, `records=0`, `source_identity={}`, diagnostic only `{code: GOLD_NAME_MISMATCH, severity: blocker}`. | ✗ FAIL — CR-02 reproduced |
| Current local H1 packet | `python3 -m specchoice_measurement.cli validate-h1-packet --packet ...v2.json --markdown ...v2.md` | Exit 0; current packet is hash-bound and publication flag is false. | ✓ PASS |
| Repository-wide discovery classification | `python3 -m unittest discover -q` | The preserved phase-aware classification is 130 discovered, with exactly 5 documented Phase-1 live-boundary expected failures and 1 related error; excluding only those five top-level methods gives 125/125 green. | ℹ️ EXPECTED BOUNDARY — not permission to weaken v7 |

The passing 59-test suite is not evidence against either Critical: it contains no `formal_attempt_sha256` tamper test and no source/gold-conflict provenance assertion. WR-01 remains a warning: `test_measurement_adapter.py` invokes literal `python3` in subprocesses, allowing interpreter/package drift outside the exact `PYTHONPATH=src python3` command used here.

### Probe Execution

No declared or conventional `scripts/*/tests/probe-*.sh` probe exists for this phase. **SKIPPED (no phase probe entry points).**

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| TS-03 | 02-01, 02-03, 02-04, 02-05 | Versioned PR #2164 adapter and all-11 deterministic golden runner, including candidate classify-out. | ✓ SATISFIED | Active 11/28 authority and focused adapter/scoring/attempt tests pass. |
| TS-04 | 02-02, 02-04, 02-05 | Closed schema, unique no-finding form, legacy restriction, and no silent repair. | ✓ SATISFIED | Focused parsing/preflight regression passes. |
| TS-05 | 02-02 through 02-05 | Required stable diagnostic codes/fields and warning-only missing accepted name. | ✗ BLOCKED | CR-02 leaves a required source/gold conflict without structured diagnostic fields/provenance; CR-01 leaves an adversarial report's lineage diagnostic trustable only by self-assertion. |

No orphaned Phase 2 requirement was found: `REQUIREMENTS.md` maps TS-03, TS-04, and TS-05 to Phase 2 and each is declared by Phase 2 plans.

### Anti-Patterns Found

| File | Line / evidence | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `src/specchoice_measurement/cli.py` | 263-265 | Self-referential evidence validation | 🛑 BLOCKER | A report can falsely claim formal-attempt lineage. |
| `src/specchoice_measurement/adapter.py` | 295-304, 337-343 | Error-path provenance discard | 🛑 BLOCKER | A reviewer cannot identify or reproduce the rejected source/gold conflict. |
| `tests/test_measurement_adapter.py` | 65, 162 | Literal `python3` subprocess interpreter | ⚠️ WARNING | Test child can use a different interpreter/package than the test runner. |

No Phase 2 `TBD`, `FIXME`, `XXX`, `HACK`, placeholder, empty-render, or console-only implementation marker was found. The known ambient `.DS_Store` files and excluded untracked `02-REVIEW-FIX 2.md` were not read, used, or modified.

### Prohibition Assessment

The implementation continues to show local-only, human-authored H1 authority: packet/decision schemas require `external_publication_authorized: false`, H1 validation rejects machine-created approvals, and no model/remote/publication expansion was found. The three developer overrides do not widen that authority. These are non-authoritative automated checks for the plans' judgment-tier prohibitions; neither they nor the existing human H1 checkpoint can waive CR-01 or CR-02.

### Gaps Summary

Plan 02-06 correctly closed the earlier override and MVP-goal paperwork gaps, and the happy-path measurement spine remains substantive, wired, data-bearing, and regression-tested. It did not close the current Critical code-review findings:

1. **CR-01:** standalone adversarial-report validation accepts a false formal-attempt digest.
2. **CR-02:** adapter conflicts fail closed but discard the audit diagnostics that the reviewer must inspect.

Both are direct failures of the phase's trust/diagnostics goal and TS-05. Keep the phase at `gaps_found` until code and targeted fail-first regressions close them. WR-01 should be fixed in the same repair if practical, but it is not the gate's root cause.

---

_Verified: 2026-08-01T17:39:10.535Z_
_Verifier: the agent (gsd-verifier)_
