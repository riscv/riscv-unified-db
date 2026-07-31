---
phase: 02-deterministic-measurement-spine
reviewed: 2026-07-31T19:47:47Z
depth: standard
files_reviewed: 30
files_reviewed_list:
  - experiments/specchoice-v1.3.2/config/measurement/canonical-adjudication-schema-v1.json
  - experiments/specchoice-v1.3.2/config/measurement/h1-review-schema-v1.json
  - experiments/specchoice-v1.3.2/config/measurement/pr2164-adapter-rules-v1.json
  - experiments/specchoice-v1.3.2/fixtures/measurement/adversarial/required-diagnostics-v1.json
  - experiments/specchoice-v1.3.2/fixtures/measurement/golden-predictions-v1.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v1.json
  - experiments/specchoice-v1.3.2/reports/h1/h1-source-gold-review-v1.json
  - experiments/specchoice-v1.3.2/reports/h1/h1-source-gold-review-v1.md
  - experiments/specchoice-v1.3.2/reviews/h1-source-gold-decision-v1.json
  - experiments/specchoice-v1.3.2/runs/measurement-attempts/formal-golden-pr2164-v1/attempt.json
  - experiments/specchoice-v1.3.2/runs/measurement-attempts/formal-golden-pr2164-v1/case-outcomes.json
  - experiments/specchoice-v1.3.2/runs/measurement-attempts/formal-golden-pr2164-v1/diagnostics.json
  - experiments/specchoice-v1.3.2/runs/measurement-attempts/formal-golden-pr2164-v1/metrics.json
  - experiments/specchoice-v1.3.2/runs/measurement-attempts/formal-golden-pr2164-v1/parsed-predictions.json
  - experiments/specchoice-v1.3.2/runs/measurement-attempts/formal-golden-pr2164-v1/report.json
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/__init__.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/adapter.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/attempts.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/cli.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/diagnostics.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/domain.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/h1.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/preflight.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/scoring.py
  - experiments/specchoice-v1.3.2/src/specchoice_measurement/strict_json.py
  - experiments/specchoice-v1.3.2/tests/test_measurement_adapter.py
  - experiments/specchoice-v1.3.2/tests/test_measurement_attempts.py
  - experiments/specchoice-v1.3.2/tests/test_measurement_h1.py
  - experiments/specchoice-v1.3.2/tests/test_measurement_parsing.py
  - experiments/specchoice-v1.3.2/tests/test_measurement_scoring.py
findings:
  critical: 4
  warning: 3
  info: 0
  total: 7
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-07-31T19:47:47Z
**Depth:** standard
**Files Reviewed:** 30
**Status:** issues_found

## Summary

The formal 11-fixture artifacts and the supplied H1 decision currently validate, and the focused suite reports 31 passing tests. That does not establish the required custody and authority properties: the validators accept self-consistent fabricated measurement evidence, the adversarial report retains no verifiable attempt evidence, evidence spans are not fixture-bound, and a JSON file with arbitrary text can impersonate the required human approval. These defects can incorrectly authorize local Phase 3 progression. The existing `external_publication_authorized: false` flag must remain false; none of the findings authorizes publication.

## Critical Issues

### CR-01: Attempt validation authenticates hashes, not the measured result

**Classification:** BLOCKER

**File:** `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_measurement/attempts.py:180-218`; `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_measurement/h1.py:105-161`

**Issue:** `validate_measurement_attempt()` verifies that artifacts match hashes chosen by the same manifest, but never replays preflight/scoring from `raw_predictions_base64`, validates the parsed-predictions projection, or derives `case-outcomes.json`, `metrics.json`, and `report.json`. An attacker with write access can replace all sibling artifacts, recompute their hashes and `attempt_sha256`, retain the current bindings and an empty diagnostics file, and obtain a `formal/completed` result. `_expected_bindings()` uses that validator and checks only the empty diagnostics artifact, so the forged result can enter an otherwise valid H1 packet.

**Fix:** Make attempt validation reconstruct the adapter from the bound source, decode and preflight the stored raw predictions, rerun `score_prediction_batch()`, and compare canonical bytes of every derived artifact and terminal role/status. H1 must consume that replay-validated result rather than self-asserted artifact hashes.

### CR-02: Evidence from another fixture is accepted as evidence for the scored fixture

**Classification:** BLOCKER

**File:** `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_measurement/strict_json.py:97-121`; `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_measurement/preflight.py:37-59`

**Issue:** The preflight builds one global `sha256 -> bytes` map for every fixture source. `_validate_span()` only tests membership in that global map, so a prediction for fixture A can cite a valid byte span from fixture B. It then passes parsing and evidence-integrity scoring even though the cited evidence is not authoritative evidence for the finding being adjudicated. This violates the fixture-specific evidence requirement and can inflate a formal score.

**Fix:** Build an allowed source-hash set per `fixture_id` from that record's `fixture_source` raw files. Pass that fixture-scoped map/set into span validation and reject any span whose hash is not declared for the current fixture. Add a negative test that copies an exact valid span from a different fixture.

### CR-03: The adversarial oracle report claims custody for deleted attempts

**Classification:** BLOCKER

**File:** `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_measurement/cli.py:157-195`; `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_measurement/cli.py:244-248`

**Issue:** Each diagnostic-only attempt is created under `TemporaryDirectory` and is deleted before the report is written. The retained report contains only unresolvable SHA-256 strings. Its validator accepts arbitrary 64-character values for both `attempt_sha256` and `raw_predictions_sha256`; it never recreates each mutation, validates a persisted attempt, or checks the oracle's `raw_input_identity`. Therefore a forged canonical report can assert all expected diagnostics and pass validation without any corresponding execution or immutable custody, yet its hash is accepted by H1.

**Fix:** Persist each diagnostic-only attempt under an immutable report-owned attempt root and bind its manifest digest in the report. During validation, recover the raw payload, apply or independently verify the declared mutation against the golden hash, replay preflight/scoring, and require the actual persisted attempt digest and diagnostics to match.

### CR-04: H1 approval can be fabricated by a machine-authored JSON file

**Classification:** BLOCKER

**File:** `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_measurement/h1.py:274-316`

**Issue:** The H1 decision validator treats arbitrary nonempty `reviewer` and `signature` strings as the required human approval. The `human_authored` schema assertion is never validated, and there is no user-owned signature, protected authorization record, or manual gate outside the process that writes the JSON. Any automation can generate 11 matching semantic hashes, set `aggregate_disposition` to `approved`, and pass validation, contrary to D-13's rule that machines cannot override blocking states. This is an authority escalation even though external publication remains false.

**Fix:** Do not treat a local free-form JSON record as human authority. Require a user-controlled signing mechanism verified against a separately protected public key, or keep the validator's result explicitly non-authoritative and require a distinct manual authorization gate before Phase 3 consumes `approved`. Test that a synthesized reviewer/signature pair is rejected.

## Warnings

### WR-01: Adapter output creation is overwriteable through a check/write race

**Classification:** WARNING

**File:** `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_measurement/cli.py:23-35`

**Issue:** `exists()` is checked before `write_bytes()`, which opens its target with truncation. If a file appears after the check, the command overwrites it; a broken symlink can also evade `exists()` and redirect the write. This contradicts the immutable/no-replace adapter artifact boundary.

**Fix:** Require an approved output directory, reject all symlinks with `lstat`, and use the existing exclusive-create/fsync helper (`_write_exact`) followed by directory sync. Add a race and broken-symlink regression test.

### WR-02: The versioned adapter rules are largely decorative and forbid a successor version

**Classification:** WARNING

**File:** `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_measurement/adapter.py:143-186`; `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_measurement/adapter.py:293-299`

**Issue:** The code hard-codes `pr2164-adapter-v1` and ignores most declared rules (`expected_fields`, `score_bearing_allowlist`, category derivation, and counts). It also silently treats a missing positive `must_have_excerpt` as false. A legitimate transformation-rule correction cannot create `pr2164-adapter-v2` as D-04 requires, while a rule-file change can alter its hash without changing the actual transformation semantics.

**Fix:** Validate every score-bearing rule field and all required fixture fields, drive transformation from that canonical rule object, and accept a constrained versioned identifier with an explicit immutable-version policy. Reject missing evidence requirements instead of defaulting them to false.

### WR-03: H1 packet publication can leave an unrecoverable half-packet

**Classification:** WARNING

**File:** `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_measurement/h1.py:238-250`

**Issue:** JSON is independently written before Markdown. If the Markdown write fails or both paths are identical, the JSON packet remains while the immutable no-replace rule prevents regeneration. The saved packet cannot pass `validate_h1_packet()` without its projection, leaving a stuck and misleading review artifact.

**Fix:** Reject identical paths, stage both files in one new directory, validate both staged bytes, fsync, and publish the directory atomically/no-replace. Clean up only the unpublished staging directory on failure.

---

_Reviewed: 2026-07-31T19:47:47Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
