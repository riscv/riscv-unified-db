---
phase: 02-deterministic-measurement-spine
verified: 2026-07-31T22:38:45Z
status: gaps_found
next_action: "Gaps found. Plan the fixes, then re-run execute-phase before shipping."
next_command: "/gsd:plan-phase 02 --gaps"
score: "32/35 must-haves verified"
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "Phase 2 does not modify any Phase 1 custody module."
    status: failed
    reason: "The current Phase 2 history modifies the Phase 1 custody module `src/specchoice_evidence/filesystem.py` in commit `9d641ec8`, contrary to the Plan 02-01, 02-04, and 02-05 must-have wording. The modification is a tested TOCTOU hardening, but no accepted verification override records this intentional deviation."
    artifacts:
      - path: "experiments/specchoice-v1.3.2/src/specchoice_evidence/filesystem.py"
        issue: "Modified by Phase 2 after its Phase 1 introduction; `git log --follow` shows `2f3e509b` then `9d641ec8`."
    missing:
      - "Record a developer-accepted override or revise/replan the three stale no-Phase-1-modification must-haves; retain the hardening and its regression tests."
  - truth: "The Phase 2 MVP goal is a valid User Story that can be verified under MVP-mode rules."
    status: partial
    reason: "`user-story.validate` rejects the ROADMAP goal because it lacks the required `As a …, I want to …, so that ….` slots. The MVP verifier contract therefore forbids an official MVP goal-achievement PASS."
    artifacts:
      - path: ".planning/ROADMAP.md"
        issue: "Phase 2 is marked `Mode: mvp` but its goal is a declarative statement rather than a User Story."
    missing:
      - "Run `/gsd mvp-phase 2` (or otherwise explicitly correct the mode/goal contract), then re-run verification."
---

# Phase 2: Deterministic Measurement Spine Verification Report

**Phase Goal:** The reviewer can trust the experiment's adjudication semantics and diagnostics before any frame, retrieval, or model result is considered.

**Verified:** 2026-07-31T22:38:45Z  
**Status:** gaps_found  
**Re-verification:** No — initial verification

## Escalation Gate

This phase is marked MVP, but the roadmap goal is not a valid User Story. The centralized `user-story.validate` check rejects it for missing role, capability, and outcome slots. Under the MVP verifier contract, that prevents an official MVP PASS even though the technical evidence below was independently checked.

Separately, three plan must-haves prohibit modifying any Phase 1 custody module. Actual Git history proves that Phase 2 modified `src/specchoice_evidence/filesystem.py` in `9d641ec8` to harden a Phase 2 attempt-read TOCTOU path. The change is substantively tested and does not weaken custody, but it is still a literal must-have failure until the developer accepts and records the intentional deviation. Neither fact may be silently treated as a green result.

## User Flow Coverage

The intended reviewer flow is technically present, but MVP-mode user-flow certification is blocked by the malformed phase goal above.

| Step | Expected | Evidence in codebase | Status |
| --- | --- | --- | --- |
| Inspect source/gold semantics | The reviewer receives one complete accepted-v2 interpretation of all 11 fixtures. | `adapter.py` validates Phase 1 source authority and produces the complete 11/28 canonical batch; the source-authority command returned `status: valid`. | ✓ VERIFIED |
| Inspect deterministic adjudication | Noncanonical predictions fail visibly instead of being repaired. | `strict_json.py` has duplicate-key-safe decoding, closed objects, current/legacy ingress separation, explicit no-finding invariants, and raw-byte span checks. | ✓ VERIFIED |
| Inspect score and diagnostics | The reviewer sees independent golden outcomes and stable diagnostic fields. | `scoring.py` emits separate surfacing/disposition/identity/evidence metrics; the formal attempt replayed as `formal/completed`. | ✓ VERIFIED |
| Review H1 material | The reviewer sees a hash-bound v2 packet with no machine decision or publication authority. | v2 packet validator passed; its 11 signature slots are blank and `external_publication_authorized` is false. The separately supplied human checkpoint approved all 11 v2 semantics for local Phase 3 only. | ✓ VERIFIED (human checkpoint) |
| Outcome | The roadmap must be a valid MVP User Story before this user-flow evidence can become an official MVP verdict. | `user-story.validate` returned `valid: false`. | ✗ BLOCKER |

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Golden predictions score all 11 pinned fixtures, including surfaced-then-`classify_out` candidate behavior. | ✓ VERIFIED | Full focused suite passed; formal attempt validator returned `formal/completed`; metrics show 7/7 surfacing, 7/7 disposition, 6/6 identity, and 7/7 evidence. |
| 2 | Unknown keys, invalid enums, duplicate/conflicting predictions, and every noncanonical no-finding form reject without repair. | ✓ VERIFIED | `strict_json.py` enforces exact key sets and duplicate-key decoding; parsing tests exercise duplicate keys, non-finite constants, legacy/current separation, unknown fields, and no-finding variants. |
| 3 | Failed/warning outcomes have stable structured diagnostics; a missing accepted name is warning-only and does not rewrite disposition. | ✓ VERIFIED | `diagnostics.py` defines the total sort key; 12 persisted diagnostic-only adversarial attempts replay against complete oracles. The name-warning test proves identity 5/6 while surfacing/disposition remain 7/7. |
| 4 | A human may review frozen gold semantics without model output compensating for a disputed interpretation. | ✓ VERIFIED | v2 H1 packet/Markdown validate from disk; no v2 JSON decision exists, the old v1 decision is rejected, and the explicitly supplied human checkpoint approves all 11 semantics for local-only Phase 3. |
| 5 | Phase 2 leaves every Phase 1 custody module unmodified. | ✗ FAILED — BLOCKER | `git log --follow -- src/specchoice_evidence/filesystem.py` shows Phase 2 commit `9d641ec8` after Phase 1 commit `2f3e509b`; three plan must-haves explicitly prohibit this. |

**Score:** 32/35 de-duplicated plan must-haves verified (0 present-but-behavior-unverified). The three failed must-haves are the repeated no-Phase-1-module-modification claim; they share the one root cause above.

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `config/measurement/pr2164-adapter-rules-v1.json` | Versioned bounded adapter rules | ✓ VERIFIED | Canonical JSON with 11/28 closure and explicit score-bearing allowlist. |
| `src/specchoice_measurement/adapter.py` | Accepted-v2-only adapter | ✓ VERIFIED | Substantive 351-line implementation; validates authority, bundle, raw identity, finite batch, and deterministic diagnostics. |
| `config/measurement/canonical-adjudication-schema-v1.json` | Closed adjudication contract | ✓ VERIFIED | Canonical contract matches `strict_json.py` exact payload/prediction/adjudication/span checks. |
| `src/specchoice_measurement/{strict_json.py,preflight.py,diagnostics.py}` | Strict validation and complete diagnostics | ✓ VERIFIED | Closed parsing, full preflight collection, exact evidence checks, and one ordering key. The `return {}` source-index fallback is safe failure behavior, not a rendered/data stub. |
| `fixtures/measurement/golden-predictions-v1.json` | Exact all-11 formal prediction input | ✓ VERIFIED | Bound by the formal attempt and adversarial report validators. |
| `src/specchoice_measurement/scoring.py` | Independent scoring dimensions | ✓ VERIFIED | Substantive 268-line scorer; formal mode rejects incomplete/diagnostic-only inputs and has no blended score. |
| `src/specchoice_measurement/attempts.py` plus formal attempt directory | Immutable replayable formal evidence | ✓ VERIFIED | Descriptor-backed attempt reads, raw-byte recovery, replay, canonical siblings, and no-replace publication all exercised by tests. |
| `reports/h1/adversarial-oracle-results-v2.json` | Separate diagnostic-only oracle report | ✓ VERIFIED | Validator replayed all 12 persisted diagnostic-only attempts with exact structured diagnostics. |
| `config/measurement/h1-review-schema-v1.json` and `src/specchoice_measurement/h1.py` | H1 packet and human-only decision boundary | ✓ VERIFIED | No decision writer exists; approved JSON is deliberately rejected with `H1_MANUAL_AUTHORIZATION_REQUIRED`. |
| `reports/h1/h1-source-gold-review-v2/` | Current canonical H1 JSON and Markdown projection | ✓ VERIFIED | Packet validator passed; logical `packet_sha256` is `4482bfe4c28a825e86365420c071ed267afc3d0370ce333e4cdd16916b58c81c`. |
| `reviews/h1-source-gold-decision-v1.json` | Current H1 authority | ⚠️ SUPERSEDED | Present but intentionally non-authoritative. Its validator invocation against the v1 packet fails `H1_BINDINGS_INVALID`; it was not used for Phase 3 progression. |
| `src/specchoice_evidence/filesystem.py` | Unchanged Phase 1 custody module | ✗ FAILED | Modified by Phase 2 commit `9d641ec8`; its new descriptor-backed read hardens rather than weakens custody, but violates the literal no-modification must-have. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `phase2/source-authority.json` | Adapter batch | Phase 1 authority CLI plus accepted-bundle verifier | ✓ WIRED | Independent command returned the exact 11-fixture/28-raw active v2 identity. |
| Adapter batch | Strict preflight | Exact adapter SHA and fixture-owned source hashes | ✓ WIRED | `validate_current_payload()` rejects adapter hash mismatch and fixture-crossing evidence. |
| Preflight | Scorer | Zero-blocker complete all-11 gate | ✓ WIRED | `score_prediction_batch()` returns no formal metrics for invalid or `diagnostic_only` input. |
| Scorer | Formal attempt | Replayable role-separated custody | ✓ WIRED | Formal validator recomputed the adapter/preflight/scoring payloads from base64 raw input. |
| Frozen adversarial oracle | v2 adversarial report | 12 diagnostic-only attempts, exact record comparison | ✓ WIRED | `validate-adversarial-report` passed. |
| Formal attempt + adversarial report | v2 H1 packet/Markdown | Current hash recomputation and pure projection | ✓ WIRED | `validate-h1-packet` passed; Markdown is regenerated from canonical JSON. |
| H1 packet | Local Phase 3 checkpoint | Explicit separate human review; no JSON approval route | ✓ WIRED (human) | Direct user checkpoint approved all 11 v2 items for local progression only; no v2 decision file was created. |

### Data-Flow Trace (Level 4)

| Artifact | Data variable | Source | Produces real data | Status |
| --- | --- | --- | --- | --- |
| Adapter batch | 11 canonical fixture records | Accepted verifier-rooted v2 bundle validated against local authority | 28 raw files, finite 11 records | ✓ FLOWING |
| Formal attempt | Parsed predictions, outcomes, metrics | Golden JSON → preflight → scorer | Complete all-11 `formal/completed` replay | ✓ FLOWING |
| H1 v2 packet | Bindings and 11 fixture reviews | Formal attempt + v2 adversarial report + current source identities | Hash-bound, canonical JSON and deterministic Markdown | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Measurement/attempt/H1 and filesystem custody contracts | `python3 -m unittest tests.test_measurement_* tests.test_filesystem_boundary -q` | 59 tests passed in 27.306s | ✓ PASS |
| Active accepted-v2 authority | `python3 -m specchoice_evidence.cli validate-phase2-source-authority …` | `status: valid`, exact 11/28 v2 identity | ✓ PASS |
| Formal golden attempt replay | `python3 -m specchoice_measurement.cli validate-attempt …formal-golden-pr2164-v1` | `formal/completed`, attempt digest `c81649ae…` | ✓ PASS |
| Separate adversarial evidence replay | `python3 -m specchoice_measurement.cli validate-adversarial-report …v2.json` | 12 matched diagnostic-only cases | ✓ PASS |
| Current H1 v2 packet and Markdown | `python3 -m specchoice_measurement.cli validate-h1-packet …v2.json …v2.md` | Passed; logical packet SHA `4482bfe4…` | ✓ PASS |
| Machine approval is impossible | Named `test_existing_signed_human_decision_is_validated_without_repair_or_upgrade` | Passed; an approved JSON decision raises `H1_MANUAL_AUTHORIZATION_REQUIRED` | ✓ PASS |
| Superseded v1 decision cannot authorize current packet | `validate-h1-decision --packet …v1.json --decision …v1.json` | Exit nonzero: `H1_BINDINGS_INVALID` | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| TS-03 | 02-01, 02-03, 02-04, 02-05 | Versioned PR #2164 adapter and deterministic all-11 golden runner, including candidate classify-out | ✓ SATISFIED | Source authority, adapter, formal replay, and v2 H1 packet all validate. |
| TS-04 | 02-02, 02-04, 02-05 | Strict canonical schema, sole no-finding form, legacy restriction, and no silent repair | ✓ SATISFIED | Closed parser/preflight tests pass; invalid inputs have no metrics/report authority. |
| TS-05 | 02-02 through 02-05 | Stable structured diagnostics and warning-only missing accepted name | ✓ SATISFIED | Exact 12-case adversarial replay and warning-separation tests pass. |

No orphaned Phase 2 requirement was found: `REQUIREMENTS.md` maps TS-03, TS-04, and TS-05 to Phase 2 and every ID appears in the plan frontmatter.

### Anti-Patterns Found

| File | Line / evidence | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `src/specchoice_evidence/filesystem.py` | Commit `9d641ec8` | Phase 1 custody module modified | 🛑 BLOCKER | Violates the explicit Phase 2 no-modification must-haves despite being a security hardening. |

No `TBD`, `FIXME`, `XXX`, `HACK`, placeholder, empty-render, or console-only implementation marker was found in the Phase 2 measurement code, fixtures, attempts, reports, or tests. `git diff --check` is clean. The known ambient `.DS_Store` files and untracked `02-REVIEW-FIX 2.md` were intentionally not treated as Phase 2 evidence or modified.

### Prohibition Assessment

The plan's judgment-tier prohibitions cannot receive a silent automated pass. The implementation and focused tests provide non-authoritative evidence that there is no silent semantic repair, no partial/diagnostic promotion, no machine H1 approval, and no external-publication authority. Human review is recommended for those prohibitions. The stricter literal prohibition against modifying a Phase 1 custody module is not satisfied and is the blocking gap above.

### Gaps Summary

The measurement spine itself is substantive, wired, data-bearing, and behaviorally exercised: all independent tests and artifact validators pass, the user-provided H1 checkpoint is explicit, and no model/remote/publication authority is present. This report still cannot certify the phase as passed:

1. A Phase 1 custody module was modified by Phase 2 without a recorded override, even though the modification is a tested TOCTOU hardening.
2. Phase 2 is configured as MVP while its ROADMAP goal is not a User Story; the MVP verifier must refuse an official user-flow verdict until that contract is corrected.

**Intentional-deviation override suggestion:** if the developer accepts the Phase 1 hardening as within Phase 2 scope, record a precise override for the no-modification must-have (including the security rationale, acceptor, and acceptance timestamp), rather than silently treating it as compliant.

---

_Verified: 2026-07-31T22:38:45Z_  
_Verifier: the agent (gsd-verifier)_
