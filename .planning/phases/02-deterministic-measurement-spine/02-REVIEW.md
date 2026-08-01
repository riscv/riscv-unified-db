---
phase: 02-deterministic-measurement-spine
reviewed: 2026-08-01T21:02:01Z
depth: standard
files_reviewed: 32
files_reviewed_list:
  - experiments/specchoice-v1.3.2/config/measurement/canonical-adjudication-schema-v1.json
  - experiments/specchoice-v1.3.2/config/measurement/h1-review-schema-v1.json
  - experiments/specchoice-v1.3.2/config/measurement/pr2164-adapter-rules-v1.json
  - experiments/specchoice-v1.3.2/fixtures/measurement/adversarial/required-diagnostics-v1.json
  - experiments/specchoice-v1.3.2/fixtures/measurement/golden-predictions-v1.json
  - experiments/specchoice-v1.3.2/reports/h1/adversarial-oracle-results-v1.json
  - experiments/specchoice-v1.3.2/reports/h1/h1-source-gold-review-v1.json
  - experiments/specchoice-v1.3.2/reports/h1/h1-source-gold-review-v1.md
  - experiments/specchoice-v1.3.2/reports/h1/h1-source-gold-review-v2/h1-source-gold-review-v2.json
  - experiments/specchoice-v1.3.2/reports/h1/h1-source-gold-review-v2/h1-source-gold-review-v2.md
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
  critical: 1
  warning: 0
  info: 0
  total: 1
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-08-01T21:02:01Z
**Depth:** standard
**Files Reviewed:** 32
**Status:** issues_found

## Summary

All listed source, test, and evidence artifacts were reviewed at standard depth, including the call sites affected by the 02-07 repair. Prior CR-01 is closed: standalone adversarial validation now derives its required formal-attempt digest from a supplied, verified `formal/completed` attempt. Prior CR-02 is closed: a source/gold disagreement retains the fixture, field, expected/observed values, relevant raw hashes, and verified source identity. The former `python3` subprocess warning is also closed by using `sys.executable`.

The H1 packet, formal attempt, and v2 adversarial report validate against the active accepted-v2 authority, and the focused suite passes 39 tests. However, two remaining read paths still split custody inspection from the path-based read, leaving a documented no-follow boundary vulnerable to a time-of-check/time-of-use swap.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: H1 and evidence-span readers reopen checked leaves by pathname

**File:** `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_measurement/h1.py:43-46`; `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_measurement/h1.py:281-282`; `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_measurement/preflight.py:51-54`
**Issue:** These paths call `inspect_authoritative_path()` and then consume the same leaf using `Path.read_bytes()`. A concurrent local writer can replace the verified regular file with a symlink, FIFO, or external file after the inspection and before the second open. This bypasses the Phase 1 custody policy even though `read_authoritative_file()` was introduced precisely to keep the checked identity and consumed bytes on one `O_NOFOLLOW` descriptor. H1 validation can therefore read a decision, packet, or Markdown projection from outside the experiment boundary; preflight can likewise consume a substituted source leaf. The retained hash comparisons catch many changed-byte cases, but they do not enforce the required source-ownership and special-file rejection boundary, and a FIFO can also turn validation into an unbounded blocking read.
**Fix:** Replace every inspect-then-read leaf flow with `read_authoritative_file()` and parse/use the returned bytes. For example:

```python
from specchoice_evidence.filesystem import read_authoritative_file

relative = _relative(path, code)
_, raw = read_authoritative_file(_ROOT, relative)
value = json.loads(raw.decode("utf-8"))
```

Apply the same pattern to the H1 Markdown read and `_source_bytes_by_fixture()`, retaining the existing digest checks against the returned `FileEvidence`. Add deterministic race regressions that replace `packet.json`, the Markdown file, and a declared fixture source with an external symlink immediately before `os.open`; each must fail closed and must not consume the external bytes.

---

_Reviewed: 2026-08-01T21:02:01Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
