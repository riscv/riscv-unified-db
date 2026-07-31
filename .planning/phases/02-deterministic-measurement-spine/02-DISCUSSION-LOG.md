# Phase 2: Deterministic Measurement Spine - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-31
**Phase:** 2-deterministic-measurement-spine
**Areas discussed:** Adapter normalization boundary, Compatibility ingress and strict validation, Failure collection and exit behavior, H1 review disposition

---

## Adapter Normalization Boundary

### Scorer input authority

| Option | Description | Selected |
|--------|-------------|----------|
| Versioned canonical adapter record | Preserve raw bytes and bind normalized output to adapter version, source hashes, original values, and transformation rules. | ✓ |
| Transform at scoring time | Read and normalize raw fixtures during every scoring run without a persistent canonical adapter artifact. | |
| Carry upstream fields into scoring | Make the scorer directly understand all heterogeneous legacy fixture fields. | |

**User's choice:** Versioned canonical adapter record.

### Conflicting fixture semantics

| Option | Description | Selected |
|--------|-------------|----------|
| Block the complete batch | Save a structured failed-attempt receipt and emit no score-eligible records. | ✓ |
| Isolate one fixture | Continue adapting and scoring the remaining fixtures. | |
| Choose one source | Prefer one conflicting gold field and continue with a warning. | |

**User's choice:** Block the complete batch and preserve deterministic conflict evidence.

### Score-bearing fields

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit scoring allowlist | Preserve other fields as provenance without allowing them to affect metrics. | ✓ |
| All known fields may score | Allow class, skill risk, and other source metadata to affect results. | |
| Discard non-scoring fields | Remove all extra fixture context from canonical records. | |

**User's choice:** Explicitly separate score-bearing and provenance-only fields.

### Adapter corrections

| Option | Description | Selected |
|--------|-------------|----------|
| New version and full rebuild | Rebuild and retest all 11 fixtures under one new adapter/rule identity. | ✓ |
| Patch affected fixtures | Mix old and new adapter versions within a batch. | |
| Overwrite in place | Replace existing canonical records under unchanged paths. | |

**User's choice:** Create a new immutable adapter version and rebuild all 11 fixtures.

---

## Compatibility Ingress and Strict Validation

### Legacy `reject` alias

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit legacy ingress only | Preserve raw input and emit a stable before/after normalization diagnostic; canonical input rejects the alias. | ✓ |
| Accept everywhere | Normalize the alias for all prediction versions. | |
| Reject everywhere | Remove all legacy compatibility. | |

**User's choice:** Permit the alias only at an explicitly versioned legacy ingress.

### Unknown keys

| Option | Description | Selected |
|--------|-------------|----------|
| Closed schema at every score-bearing level | Put extra provenance only in a separate non-scoring envelope. | ✓ |
| Top-level closure only | Ignore unknown nested adjudication and evidence keys. | |
| Free-form extensions | Permit arbitrary extension content inside canonical predictions. | |

**User's choice:** Recursively reject unknown score-bearing keys.

### Missing no-finding fields

| Option | Description | Selected |
|--------|-------------|----------|
| Missing fields are invalid | Require the full explicit nullable/empty representation. | ✓ |
| Fill all defaults | Repair omitted nulls and arrays with a warning. | |
| Fill empty containers only | Repair only missing arrays. | |

**User's choice:** Never supply canonical defaults.

### Semantic string normalization

| Option | Description | Selected |
|--------|-------------|----------|
| No semantic repair | Require exact values and raw-source evidence matching; apply NFC only after validation in canonical reports. | ✓ |
| Normalize before validation | Trim, case-fold, and NFC-normalize semantic inputs. | |
| Normalize enums only | Case-normalize decision enums but not names or evidence. | |

**User's choice:** Do not repair semantic strings.

---

## Failure Collection and Exit Behavior

### Validation scope

| Option | Description | Selected |
|--------|-------------|----------|
| Complete preflight, then block | Collect all deterministic diagnostics but publish no partial formal metrics when a blocker exists. | ✓ |
| Fail on first error | Stop after the first blocking diagnostic. | |
| Score valid cases | Publish partial metrics for the valid subset. | |

**User's choice:** Validate the complete input set before an all-or-nothing scoring decision.

### Identity warning status

| Option | Description | Selected |
|--------|-------------|----------|
| Complete with warnings | Exit zero, preserve disposition, and decrease identity coverage independently. | ✓ |
| Treat warning as blocker | Suppress all formal metrics until names are present. | |
| Hide warning from run status | Record only in a diagnostics file. | |

**User's choice:** Use `completed_with_warnings` and expose identity impact to H1.

### Attempt retention

| Option | Description | Selected |
|--------|-------------|----------|
| Immutable attempt per invocation | Retain failed and warning evidence while separating it from formal authority. | ✓ |
| Successful runs only | Discard failed invocation artifacts. | |
| Mutable latest | Overwrite earlier attempts on each rerun. | |

**User's choice:** Persist every invocation as an immutable attempt.

### Targeted reruns

| Option | Description | Selected |
|--------|-------------|----------|
| Diagnostic-only targeted runs | Require every formal attempt to rerun all 11 cases under one identity. | ✓ |
| Incremental formal replacement | Splice repaired cases into older attempts. | |
| No targeted runs | Require full runs even during development. | |

**User's choice:** Allow targeted diagnostics but never splice formal evidence.

---

## H1 Review Disposition

### Formal states

| Option | Description | Selected |
|--------|-------------|----------|
| `approved / disputed / incomplete` | Only explicit human approval advances; disputes and incomplete reviews remain distinct blockers. | ✓ |
| `pass / pass_with_warnings / fail` | Allow runner status to stand in for semantic review. | |
| Boolean approval | Collapse disputes and missing review into one false state. | |

**User's choice:** Use three explicit human-review states.

### Review granularity

| Option | Description | Selected |
|--------|-------------|----------|
| Per fixture and key semantic field | Sign all 11 fixture interpretations before the aggregate disposition. | ✓ |
| Aggregate summary only | Review only final counts and reports. | |
| Exceptions only | Automatically accept cases without diagnostics. | |

**User's choice:** Require complete fixture-level semantic review.

### Diagnostic effect on H1

| Option | Description | Selected |
|--------|-------------|----------|
| Separate expected adversarial diagnostics | Permit exact oracle-matching negative tests; block unexpected golden diagnostics. | ✓ |
| Waive golden warnings | Let reviewer acknowledgments override unexpected golden warnings. | |
| Block every diagnostic | Treat expected adversarial diagnostics as H1 failures. | |

**User's choice:** Distinguish expected diagnostic tests from unexpected golden-run diagnostics.

### Approval binding

| Option | Description | Selected |
|--------|-------------|----------|
| Immutable hash-bound decision | Bind every relevant fixture, adapter, schema, prediction, attempt, diagnostic, and packet identity. | ✓ |
| Mutable path binding | Keep approval valid when files under `latest/` change. | |
| Human prose only | Store approval without machine-verifiable identity. | |

**User's choice:** Use an immutable hash-bound H1 decision that authorizes local progression only.

---

## the agent's Discretion

- Internal module/class names, schema decomposition, CLI names, attempt-directory names, and additional stable diagnostic codes remain planner choices within the locked contracts.

## Deferred Ideas

None — discussion stayed within Phase 2 scope.
