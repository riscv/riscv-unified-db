# Phase 2: Deterministic Measurement Spine - Research

**Researched:** 2026-07-31  
**Domain:** Offline, stdlib-first canonicalization, strict adjudication validation, deterministic scoring, and immutable local review custody  
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

## Implementation Decisions

### Adapter Normalization Boundary

- **D-01:** The scorer consumes versioned canonical adapter records only. Authoritative fixture bytes remain unchanged; each canonical record binds the adapter version, raw SHA-256 identities, original fields and values, transformation rule identity, and normalized fields and values.
- **D-02:** Any disagreement among fixture directory identity, registry identity, `expected.yaml`, `gold.yaml`, or other score-bearing sources blocks the complete adapter batch. The failed attempt records a stable diagnostic code, fixture ID, conflicting field, expected and observed values, and source hashes. It emits no score-eligible canonical records and measurement does not start.
- **D-03:** Only an explicit allowlist of fields may affect scoring: case identity, positive/negative/candidate category, `expect_extract`, normalized expected parameter count and names, and evidence requirements. Other upstream fields remain reviewable provenance and cannot alter disposition, denominators, or pass criteria.
- **D-04:** A transformation-rule correction creates a new immutable adapter version and rule hash, then symmetrically rebuilds and retests all 11 fixtures. Old records are never overwritten, adapter versions are never mixed within one measurement run, and every downstream artifact binds one exact adapter version.

### Compatibility Ingress and Strict Validation

- **D-05:** `reject` may normalize to `classify_out` only at an explicitly declared legacy-schema ingress. The raw input and before/after values remain preserved under a stable normalization diagnostic. The current canonical schema rejects `reject` as invalid.
- **D-06:** The complete score-bearing payload uses closed schemas at every level, including top-level, adjudication, and evidence-span objects. Extra provenance may appear only in a separate versioned envelope that cannot affect scoring.
- **D-07:** Canonical no-finding predictions must explicitly encode `surfaced: false`, `parameter_status: null`, `proposed_name: null`, and `evidence_spans: []`. Missing fields are invalid; the parser never supplies default nulls or empty containers.
- **D-08:** The parser never trims, case-folds, fuzzily matches, or rewrites semantic values or evidence. Evidence must match authoritative raw source text. NFC normalization applies only to the post-validation canonical report projection, while raw input remains separately preserved.

### Failure Collection and Exit Behavior

- **D-09:** Before scoring, a side-effect-free preflight validates every fixture and prediction and collects the complete diagnostic set in deterministic order. Any blocking error invalidates the whole batch, yields a nonzero exit, and prevents partial pass rates or formal metrics from being published.
- **D-10:** `ACCEPTED_PARAMETER_NAME_MISSING` remains an identity warning only. A structurally valid run may finish with exit zero and status `completed_with_warnings`; surfacing and disposition stay unchanged, identity coverage decreases independently, and the H1 packet exposes the warning prominently.
- **D-11:** Every invocation becomes an immutable attempt containing input hashes, adapter version, raw predictions, parsed results, separate diagnostics, and terminal status. Failed attempts remain auditable but never become measurement authority. Only attempts that pass preflight may emit canonical metrics and reports.
- **D-12:** Targeted case runs are permitted only as `diagnostic_only` development artifacts. Every formal attempt and H1 report runs all 11 fixtures under one adapter, schema, and prediction-set identity. Formal evidence never splices results from different attempts.

### H1 Review Disposition

- **D-13:** H1 has exactly three formal dispositions: `approved`, `disputed`, and `incomplete`. Only an explicit human `approved` decision permits Phase 3. `disputed` identifies rejected gold or adapter semantics; `incomplete` identifies missing material or signature. Machines cannot override either blocking state.
- **D-14:** The reviewer signs each fixture and its key semantics before issuing the aggregate disposition: category, `expect_extract`, normalized parameter count and names, candidate surfaced-then-`classify_out` semantics, and adapter lineage. Any disputed item makes the overall decision `disputed`.
- **D-15:** The formal golden attempt contains no unexpected warning or error. Adversarial tests may intentionally trigger diagnostics and pass only when code and structured fields exactly match the test oracle. Expected adversarial diagnostics do not block H1; unexpected golden diagnostics do.
- **D-16:** H1 approval is an immutable decision bound to the accepted fixture generation/root, fixture registry, adapter version and rule hash, canonical schema, golden prediction set, formal attempt, diagnostics, and H1 packet. Any bound change invalidates approval and requires a new version and review. H1 authorizes local Phase 3 progression only and never authorizes external publication.

### the agent's Discretion

The planner may choose internal Python module and class names, schema file decomposition, CLI command names, attempt-directory naming, and additional stable diagnostic codes. Those choices must preserve the frozen adapter, validation, attempt, canonicalization, and H1 contracts above. The planner may reuse the existing stdlib canonicalization and filesystem-verification modules or isolate measurement equivalents, provided Phase 1 custody artifacts are not weakened or retroactively modified.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within Phase 2 scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TS-03 | Run a versioned PR #2164 adapter and deterministic measurement runner for golden predictions across all 11 fixtures, including candidate surfacing then classify-out. | Versioned adapter batch, all-fixture preflight, canonical scorer, immutable attempts, and golden fixture test strategy below. [VERIFIED: codebase grep] |
| TS-04 | Strictly validate the canonical adjudication schema: unique nullable no-finding form, reject `parameter_status:not_surfaced`, unknown keys, invalid enums, and silent repair. | Closed JSON parser/validator design, duplicate-key rejection, explicit legacy ingress, and adversarial parser matrix below. [VERIFIED: 02-CONTEXT.md] |
| TS-05 | Expose required diagnostics with structured fields; an accepted unnamed parameter is an identity warning only. | Stable diagnostic record, deterministic preflight collector, metric separation, and formal-golden warning gate below. [VERIFIED: frozen execution baseline §§6.3, 11.3] |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- Keep the experiment isolated under `experiments/specchoice-v1.3.2/`; do not change root UDB schemas, generated data, or the core Ruby toolchain for this phase. [VERIFIED: AGENTS.md; 02-CONTEXT.md]
- Treat repository schemas/APIs and `spec/` data as fast-changing; consume the Phase 1 pinned source authority rather than live UDB interfaces. [VERIFIED: AGENTS.md; 01-VERIFICATION.md]
- Use `./bin/regress --all` for a repository PR only after the project setup is available; Phase 2's standalone experiment validation must not require `bin/setup`, Ruby, IDL, C++, or Node. [VERIFIED: AGENTS.md; 01-CONTEXT.md]
- Follow Conventional Commit style if a commit is later authorized; PR text must be concise and PR validation is CI-owned. [VERIFIED: AGENTS.md]

## Summary

Phase 2 should be a small, offline Python package that starts by validating `phase2/source-authority.json` against the accepted `source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2` bundle. The authoritative universe is exactly 11 fixtures (6 positive, 4 negative, 1 candidate) and 28 raw files; the current source-authority command validates the generation, root, manifest, registry, commit/tree, local-only flag, and counts. [VERIFIED: local `validate-phase2-source-authority`; codebase registry]

The phase needs two explicit data boundaries. First, the adapter converts only the accepted raw fixture set into a single immutable, hash-bound canonical batch. Second, the measurement runner accepts one complete prediction set, preserves raw bytes, performs a full side-effect-free preflight, and only then scores. This prevents a locally convenient subset, parser repair, or a source mismatch from becoming formal measurement authority. [VERIFIED: 02-CONTEXT.md]

The existing `specchoice_evidence` package already supplies canonical UTF-8 JSON, NFC/LF projection, raw-byte SHA-256, regular-file/path checks, an authority CLI, and `unittest` patterns. Reuse those primitives by import, but place Phase 2 domain behavior in a sibling `specchoice_measurement` package so Phase 1 custody behavior is neither edited nor weakened. [VERIFIED: codebase grep]

**Primary recommendation:** Implement a JSON-only canonical prediction contract with a bounded PR #2164 adapter, explicit legacy `reject` ingress, exhaustive deterministic preflight, and append-only attempt/H1 artifacts; do not add a generic YAML parser, a schema package, model integration, or any external dependency. [VERIFIED: 02-CONTEXT.md; CITED: https://docs.python.org/3/library/json.html]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Validate accepted fixture authority and raw-file integrity | Local API / Backend | Filesystem / Storage | The runner must establish its local, hash-bound source before semantic adaptation. [VERIFIED: codebase `command_validate_phase2_source_authority`] |
| Adapt raw PR #2164 fixture bytes into canonical records | Local API / Backend | Filesystem / Storage | Raw bytes remain authoritative; the adapter is a deterministic derived-artifact producer. [VERIFIED: 02-CONTEXT.md] |
| Parse and validate prediction payloads | Local API / Backend | — | Closed-schema validation, legacy ingress, and diagnostics are deterministic local business logic. [VERIFIED: frozen execution baseline §11.3] |
| Score surfacing, disposition, identity, and evidence integrity | Local API / Backend | — | These results are derived from canonical records and parsed predictions; no browser, model, or network tier is authorized. [VERIFIED: 02-CONTEXT.md] |
| Persist append-only attempts and H1 review packet | Filesystem / Storage | Local API / Backend | Immutable files bind raw inputs, derived outputs, and human decision without external publication. [VERIFIED: 02-CONTEXT.md] |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python standard library | Python 3.14.5 available | `json`, `hashlib`, `pathlib`, `dataclasses`, `argparse`, `unittest`, `unicodedata`, and `tempfile` | The current experiment is already stdlib-first; these primitives cover deterministic JSON, hashing, paths, CLI, immutable staging tests, and Unicode projection. [VERIFIED: local environment; codebase grep] |
| `specchoice_evidence.canonical` | repository-local | Canonical JSON, raw SHA-256, NFC/LF report projection, SHA and length validators | Existing tests prove sorted canonical bytes and distinguish raw bytes from normalized text. [VERIFIED: `tests/test_canonical.py`] |
| `specchoice_evidence.filesystem` / `verify` | repository-local | Regular-file and path checks, accepted-bundle verification | Phase 1 already rejects path escapes and special files before downstream use. [VERIFIED: `filesystem.py`; `01-VERIFICATION.md`] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `json.loads` with `object_pairs_hook` and `parse_constant` | Python stdlib | Decode JSON while rejecting duplicate object keys and non-JSON constants before schema validation | Use for raw prediction and canonical configuration decoding; ordinary `json.loads` alone would silently overwrite duplicate keys. [CITED: https://docs.python.org/3/library/json.html] |
| `json.dumps(..., ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)` | Python stdlib | Byte-stable canonical JSON after validation | Use only for canonical derivative artifacts, then append exactly one LF through the existing helper. [CITED: https://docs.python.org/3/library/json.html] |
| `hashlib.sha256` | Python stdlib | Raw-byte and canonical-artifact identities | Use for every input, rule, adapter batch, prediction set, attempt, and H1 binding. [CITED: https://docs.python.org/3/library/hashlib.html] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| JSON-only canonical prediction input | General YAML prediction ingestion | Python has no YAML parser in its standard library; a generic YAML dependency or parser expands the trusted surface without helping the frozen Phase 2 contract. Formal canonical prediction input is JSON-only; any compatibility route is a separately declared legacy ingress and never an implicit canonical parser feature. [RESOLVED: D-05, D-06, D-09; final Plan 02] |
| Explicit closed-schema validator | JSON Schema framework | A framework adds an unneeded package and does not remove the need to define D-05/D-07 semantic cross-field invariants or stable diagnostics. [VERIFIED: 02-CONTEXT.md; ASSUMED] |
| Sibling `specchoice_measurement` package | Adding domain logic to Phase 1 custody modules | Separation keeps Phase 1's accepted-bundle verifier stable while allowing normal imports of its primitives. [VERIFIED: codebase grep; 02-CONTEXT.md] |

**Installation:** No package installation. [VERIFIED: 02-CONTEXT.md]

**Package Legitimacy Audit:** Not applicable — Phase 2 must remain stdlib-first and installs no external package. [VERIFIED: 02-CONTEXT.md]

## Architecture Patterns

### System Architecture Diagram

```text
accepted v2 bundle + source-authority.json
                |
                v
   Phase 1 authority / raw-byte verifier
                |
       mismatch |--> immutable invalid adapter attempt + sorted diagnostics (stop)
                v
  PR #2164 adapter rules (version + rule hash)
                |
                v
 immutable canonical adapter batch (11 records, one version)
                |
raw prediction JSON -> strict/legacy ingress -> closed-schema preflight
                |                            |
                |                     blocking diagnostics? -- yes --> immutable invalid attempt (nonzero; no metrics)
                v                            no
     raw input + normalization trace         |
                                             v
                    canonical scorer + exact evidence verifier
                                             |
                                             v
       immutable formal attempt: case outcomes, metrics, diagnostics, report
                                             |
                                             v
          H1 packet (canonical JSON + deterministic Markdown projection)
                                             |
                              explicit human decision only
                       approved | disputed | incomplete
```

The arrows are one-way: authoritative raw files are never rewritten; canonical records do not mutate raw files; an invalid preflight cannot emit score-eligible metrics; and the H1 machine can validate a decision but cannot choose `approved`. [VERIFIED: 02-CONTEXT.md]

### Recommended Project Structure

```text
experiments/specchoice-v1.3.2/
├── config/measurement/
│   ├── pr2164-adapter-rules-v1.json        # canonical, immutable rule source
│   └── canonical-adjudication-schema-v1.json # reviewable closed-contract description
├── fixtures/measurement/
│   ├── golden-predictions-v1.json
│   └── adversarial/                        # one canonical input + oracle per case
├── src/specchoice_measurement/
│   ├── adapter.py                           # accepted-bundle-only PR #2164 adapter
│   ├── domain.py                            # frozen dataclasses/enums and artifact views
│   ├── strict_json.py                       # duplicate-key-safe decoder and closed validation
│   ├── diagnostics.py                       # stable typed diagnostic records/sorting
│   ├── preflight.py                         # complete-batch validation, no scoring
│   ├── scoring.py                           # independent case outcomes and aggregates
│   ├── attempts.py                          # no-replace attempt staging/publication
│   ├── h1.py                                # packet, decision validation, deterministic Markdown
│   └── cli.py                               # adapter, diagnostic-only, formal, H1 commands
├── tests/
│   ├── test_measurement_adapter.py
│   ├── test_measurement_parsing.py
│   ├── test_measurement_scoring.py
│   ├── test_measurement_attempts.py
│   └── test_measurement_h1.py
└── runs/measurement-attempts/<attempt-id>/  # append-only terminal attempts
```

Keep Phase 2 outputs beneath the existing experiment boundary. Treat an adapter rules file, schema description, golden prediction set, and an H1 decision as versioned input artifacts whose canonical hashes are carried forward, not as mutable settings. [VERIFIED: 02-CONTEXT.md]

### Pattern 1: Versioned adapter batch, not direct fixture scoring

**What:** Verify `phase2/source-authority.json`, then build a canonical batch for all 11 fixture IDs in sorted order. Each record must include `adapter_version`, `rule_sha256`, source generation/root/registry identities, raw source file entries `{path, role, sha256, byte_length}`, original score-bearing fields, normalized category/count/name/evidence requirement fields, and an adapter-record hash. [VERIFIED: local authority command; 02-CONTEXT.md]

**When to use:** Every formal or diagnostic invocation. The scorer consumes only this batch, never the raw `expected.yaml`/`gold.yaml` files directly. [VERIFIED: 02-CONTEXT.md]

**Implementation guidance:** Make the adapter's source reader deliberately bounded to the known PR #2164 field syntax. It must extract only the allowlisted scoring fields, preserve raw file bytes/hashes for all source content, and reject unsupported/missing/duplicate score-bearing fields. Do not build a general YAML implementation and do not make non-allowlisted prose, schema, or other upstream metadata score-bearing. [VERIFIED: 02-CONTEXT.md; ASSUMED]

### Pattern 2: Two-stage parser with an explicit compatibility boundary

**What:** Decode raw JSON into a lossless parse representation that detects duplicate keys; optionally transform only legacy `parameter_status:"reject"` to `"classify_out"` at a named legacy ingress; then run the current closed-schema validator. Persist raw bytes, parsed result, and normalization diagnostics separately. [VERIFIED: 02-CONTEXT.md; CITED: https://docs.python.org/3/library/json.html]

**When to use:** All prediction files. Canonical formal input is JSON; the legacy ingress is an explicit compatibility route, never a current-schema convenience. [VERIFIED: 02-CONTEXT.md]

**Required schema checks:**

- The top-level prediction payload, each prediction, `adjudication`, and each evidence-span object have exact permitted key sets; reject unknown, omitted, and duplicate keys. [VERIFIED: 02-CONTEXT.md]
- `surfaced:false` must explicitly carry `parameter_status:null`, `proposed_name:null`, and `evidence_spans:[]`; `not_surfaced` is only a derived result, never an input enum. [VERIFIED: 02-CONTEXT.md]
- `surfaced:true` requires `parameter_status` in `accept|classify_out|review`, an explicit `proposed_name` field, and a non-empty evidence-span list. `proposed_name:null` is valid for a surfaced classify-out/review case; only `accept` plus null produces the accepted-name identity warning. [VERIFIED: frozen execution baseline §§6.2, 11.3; 02-CONTEXT.md]
- Validate evidence against raw source bytes before any Unicode normalization. The closed record is exactly `{source_sha256,start_byte,end_byte,text}`; `[start_byte,end_byte)` is a non-empty half-open byte range within the named raw source, each span is validated independently, adjacent or duplicate spans are never implicitly merged, and the decoded raw slice must equal `text`. [RESOLVED: D-06, D-08; final Plans 02-03]

### Pattern 3: Collect-then-decide preflight

**What:** Run validation over source authority, adapter batch, full fixture universe, complete prediction coverage, duplicate/conflict rules, and evidence claims without writing metrics. Append all diagnostics, sort by a total key such as `(severity_rank, code, fixture_id, field, occurrence)`, then make exactly one terminal preflight decision. [VERIFIED: 02-CONTEXT.md]

**When to use:** Before every formal score and before creating H1 material. A targeted run is allowed only when labeled `diagnostic_only`; it must be unable to produce an H1 packet. [VERIFIED: 02-CONTEXT.md]

**Outcome rule:** Blocking diagnostics produce `invalid_preflight`, nonzero exit, and no canonical metrics/report. `ACCEPTED_PARAMETER_NAME_MISSING` is nonblocking, preserves surfacing/disposition, lowers only identity coverage, and yields `completed_with_warnings` if no blocker exists. [VERIFIED: 02-CONTEXT.md]

### Pattern 4: Immutable attempt publication

**What:** Stage an attempt directory, write canonical JSON artifacts, self-hash/bind its inputs, then publish with no-replace semantics. A caller supplies a validated attempt label; collisions fail rather than overwrite. [VERIFIED: `bundle.py`; 02-CONTEXT.md]

**When to use:** Every run, including invalid attempts. A terminal attempt should contain `attempt.json`, raw prediction bytes, parsed projection, diagnostics, terminal status, and—only after passing preflight—case outcomes, metrics, and deterministic report. [VERIFIED: 02-CONTEXT.md]

### Pattern 5: H1 packet and human-only gate

**What:** Generate one canonical packet binding accepted source identity, adapter batch/rule, schema, golden prediction hash, formal attempt hash, diagnostics hash, per-fixture semantics, and an aggregate review template. Validate a separate immutable reviewer decision with exactly `approved|disputed|incomplete`; a deterministic Markdown view is derived from JSON only. [VERIFIED: 02-CONTEXT.md]

**When to use:** Only after a complete all-11 formal golden attempt with no unexpected warning/error. An expected diagnostic from a separate adversarial test is not a golden warning and cannot be spliced into H1. [VERIFIED: 02-CONTEXT.md]

### Anti-Patterns to Avoid

- **Direct scoring from `expected.yaml`/`gold.yaml`:** It bypasses the required adapter lineage and makes transformation versions invisible. Use the canonical adapter batch. [VERIFIED: 02-CONTEXT.md]
- **Fail-fast parser/scorer:** It hides additional blockers and can leave a partial pass rate visible. Collect all preflight diagnostics first. [VERIFIED: 02-CONTEXT.md]
- **Defaulting omitted nulls or arrays:** It turns malformed no-finding input into a valid prediction. Require every canonical field. [VERIFIED: 02-CONTEXT.md]
- **Naive `json.loads`:** Default duplicate-key handling retains only the last value, defeating duplicate-prediction evidence. Use a duplicate-key-detecting hook. [CITED: https://docs.python.org/3/library/json.html; ASSUMED]
- **Normalizing raw evidence before checking it:** NFC/LF normalization can make nonidentical raw source/evidence appear equal. Validate exact raw slices first. [VERIFIED: `canonical.py`; 02-CONTEXT.md]
- **Reusing a Phase 1 “current boundary” full-suite result as a Phase 2 test gate:** Its checks intentionally see later Phase 2 planning files as out-of-Phase-1 changes. Keep Phase 2 unit tests focused and preserve the Phase 1 evidence history unchanged. [VERIFIED: local test execution]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Canonical JSON and SHA-256 | A second serializer/hash convention | `specchoice_evidence.canonical` | It already produces sorted UTF-8 JSON with a terminal LF and separates raw-byte hashes from normalized views. [VERIFIED: `canonical.py`] |
| Accepted-bundle/path verification | A relaxed Phase 2 directory walk | `validate-phase2-source-authority`, `verify_accepted_bundle`, and filesystem primitives | Phase 1 already binds the accepted generation and rejects special files/path escapes. [VERIFIED: `cli.py`; `01-VERIFICATION.md`] |
| Generic YAML parser | A partial “YAML-compatible” language | A deliberately bounded adapter reader for only the known raw source fields | Generic YAML is outside this phase and creates ambiguous parsing/security surface; source bytes remain the authority. [VERIFIED: 02-CONTEXT.md; ASSUMED] |
| Schema framework / fuzzy matching | General validation, case-folding, trimming, or approximate evidence search | Explicit closed validators and exact raw-byte offsets/text checks | The frozen contract requires stable diagnostics and no semantic repair. [VERIFIED: 02-CONTEXT.md] |
| Human approval automation | Auto-approval/signature inference | A human-authored H1 decision validated for binding/completeness | Machines may validate but cannot override `disputed` or `incomplete`. [VERIFIED: 02-CONTEXT.md] |

**Key insight:** The difficult part is custody and semantic separation, not scoring arithmetic. Reusing Phase 1 primitives and keeping the adapter/parser contracts narrow makes failures auditable instead of silently “helpful.” [VERIFIED: 01-VERIFICATION.md; 02-CONTEXT.md]

## Common Pitfalls

### Pitfall 1: Treating the candidate as a negative

**What goes wrong:** A runner rewards `surfaced:false` for `CAND_WARL_FIXED_LEGAL_SET`, hiding the reviewable finding.  
**Why it happens:** Both candidate and negative have zero expected accepted parameters, but only candidate has `expect_extract:true`.  
**How to avoid:** Derive category from both normalized dimensions and require surfaced plus `classify_out` for the sole candidate.  
**Warning signs:** Candidate denominator passes while its case outcome says `not_surfaced`. [VERIFIED: frozen execution baseline §6.1; registry]

### Pitfall 2: Conflating disposition and identity

**What goes wrong:** An accepted prediction with no name is marked disposition-incorrect, or its name warning is repaired to an invented value.  
**Why it happens:** Scoring fields are collapsed into one boolean.  
**How to avoid:** Store independent surfacing, disposition, identity, and evidence outcomes; emit only `ACCEPTED_PARAMETER_NAME_MISSING` as a nonblocking identity warning.  
**Warning signs:** A warning changes accepted/classify-out totals or a run exits nonzero solely because of the warning. [VERIFIED: 02-CONTEXT.md; frozen execution baseline §6.3]

### Pitfall 3: Partial results after a blocker

**What goes wrong:** A malformed prediction for one fixture still yields a denominator/pass rate for the other ten.  
**Why it happens:** Validation and scoring run in the same loop.  
**How to avoid:** Make preflight a pure full-batch pass and gate metrics/report creation on zero blocking diagnostics.  
**Warning signs:** An invalid attempt contains a `metrics.json` or Markdown claim. [VERIFIED: 02-CONTEXT.md]

### Pitfall 4: Losing input provenance in “canonical” output

**What goes wrong:** Normalized values overwrite raw evidence or the adapter records lack a rule/source hash.  
**Why it happens:** Canonicalization is treated as cleanup instead of a one-way derivation.  
**How to avoid:** Persist raw bytes/hashes and source paths alongside original score-bearing fields and normalized fields; normalize only a post-validation report projection.  
**Warning signs:** Recomputing an adapter record cannot identify its precise accepted generation, raw files, and rule version. [VERIFIED: `canonical.py`; 02-CONTEXT.md]

### Pitfall 5: Letting a legacy alias leak into the current schema

**What goes wrong:** Current canonical prediction files contain `reject`, or parser behavior varies based on hidden compatibility code.  
**Why it happens:** Ingress and canonical schema are not separate.  
**How to avoid:** Give the legacy route a distinct declared format/version, preserve before/after values plus diagnostic, and reject `reject` on the current route.  
**Warning signs:** The same file is valid with and without a legacy flag. [VERIFIED: 02-CONTEXT.md]

### Pitfall 6: Non-deterministic audit artifacts

**What goes wrong:** Equivalent inputs produce reordered diagnostics or timestamp/path-dependent core reports.  
**Why it happens:** Dict insertion order, filesystem traversal, exception text, and wall-clock values leak into authority bytes.  
**How to avoid:** Use sorted fixture IDs, a specified diagnostic sort key, canonical JSON, repository-relative paths, and a separate noncanonical audit receipt for operational detail.  
**Warning signs:** Repeated runs have different artifact hashes with identical inputs. [VERIFIED: frozen execution baseline §15; `canonical.py`]

## Code Examples

Verified patterns from the existing repository and official Python documentation:

### Canonical artifact bytes

```python
# Source: experiments/specchoice-v1.3.2/src/specchoice_evidence/canonical.py
from specchoice_evidence.canonical import canonical_json_bytes, sha256_bytes

payload_bytes = canonical_json_bytes(report)
payload_sha256 = sha256_bytes(payload_bytes)
```

This existing helper normalizes only the derived report, sorts keys, uses compact JSON, and appends one LF. [VERIFIED: `canonical.py`]

### Duplicate-key-safe JSON boundary

```python
# Source: https://docs.python.org/3/library/json.html
import json

class DuplicateJsonKey(ValueError):
    pass

def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKey(key)
        result[key] = value
    return result

def reject_non_json_constant(value: str) -> object:
    raise ValueError(f"non-JSON constant: {value}")

raw = prediction_path.read_bytes()
decoded = json.loads(
    raw.decode("utf-8"),
    object_pairs_hook=reject_duplicate_keys,
    parse_constant=reject_non_json_constant,
)
# Apply the explicit legacy ingress (if selected), then exact closed-schema checks.
```

Map the caught exceptions into stable diagnostic records rather than publishing Python exception text. [CITED: https://docs.python.org/3/library/json.html; VERIFIED: 02-CONTEXT.md]

### Exact evidence validation before report normalization

```python
# Source: Phase 2 contract; field names are the recommended schema under planner discretion.
raw_source = source_path.read_bytes()
if span["source_sha256"] != sha256_bytes(raw_source):
    add_blocker("EVIDENCE_SOURCE_HASH_MISMATCH", case_id, "source_sha256")
elif not (0 <= span["start_byte"] < span["end_byte"] <= len(raw_source)):
    add_blocker("EVIDENCE_SPAN_OUT_OF_RANGE", case_id, "evidence_spans")
else:
    observed = raw_source[span["start_byte"]:span["end_byte"]].decode("utf-8")
    if observed != span["text"]:
        add_blocker("EVIDENCE_SPAN_NOT_FOUND", case_id, "evidence_spans")
```

Do not trim, NFC-normalize, or fuzzy-search either side of this check. [VERIFIED: 02-CONTEXT.md]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Phase 1 only established accepted source custody and a Phase 2 source pin. | Phase 2 will add a versioned adapter, strict canonical adjudication, scoring, attempts, and H1 review. | Phase 2 planning boundary | The existing package has no evaluator/scorer yet; do not mistake the source authority for measurement implementation. [VERIFIED: `01-VERIFICATION.md`; codebase files] |
| Historical v1 fixture closure was preserved but revoked from downstream authority. | Accepted `...verifier-rooted-v2` is the only active downstream-eligible fixture generation. | Phase 1 closure repair | Adapter input must be v2 only; no fallback to v1 or candidates. [VERIFIED: `01-VERIFICATION.md`; local authority command] |

**Deprecated/outdated:**

- Direct or historical fixture-generation consumption: replaced by `phase2/source-authority.json` validation against the accepted v2 bundle. [VERIFIED: `01-VERIFICATION.md`; `cli.py`]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | RESOLVED — Formal canonical Phase 2 prediction input is JSON-only. Legacy compatibility is a separately named ingress and cannot make YAML or aliases part of the canonical schema. | Standard Stack; Pattern 2 | Locked by D-05, D-06, and D-09 and implemented by final Plan 02. |
| A2 | A bounded field reader is preferable to a generic YAML parser for adapter source material. | Pattern 1; Don't Hand-Roll | If raw fixture syntax changes within the pinned generation, the adapter reader must be expanded under a new rule version. |
| A3 | RESOLVED — Evidence spans use exactly `{source_sha256,start_byte,end_byte,text}` with a non-empty half-open byte range `[start_byte,end_byte)`, per-span independent raw-byte validation, and no implicit merging. | Pattern 2; Code Examples | Locked by D-06 and D-08 and implemented by final Plans 02-03. |

## Open Questions (RESOLVED)

1. **Canonical input format scope**
   - What we know: The frozen baseline permits machine-readable YAML or JSON, while Python stdlib and Phase 2's no-dependency direction favor JSON. [VERIFIED: frozen execution baseline §11.3; local environment]
   - Resolution: Formal canonical Phase 2 prediction input is JSON-only. Any compatibility input is handled only by a separately declared legacy ingress, preserves raw bytes plus explicit normalization diagnostics, and must pass the current closed canonical schema after that ingress. YAML is not a formal canonical prediction input. [RESOLVED: D-05, D-06, D-09; final Plan 02]

2. **Evidence-span record fields**
   - What we know: Evidence spans must be closed, non-empty when surfaced, and exactly match authoritative raw source text. [VERIFIED: 02-CONTEXT.md; frozen execution baseline §11.3]
   - Resolution: The exact closed record is `{source_sha256,start_byte,end_byte,text}`. The range is mandatory, half-open `[start_byte,end_byte)`, within bounds, non-empty, and UTF-8-decodable; its raw slice must equal `text`. Each span is retained and validated independently, including adjacent or duplicate spans, with no implicit merge, trimming, normalization, deduplication, or fuzzy lookup. [RESOLVED: D-06, D-08; final Plans 02-03]

3. **Phase 1 boundary test coexistence**
   - What we know: Running the current all-tests discovery after committed Phase 2 planning artifacts produces Phase 1 boundary blockers; the focused canonical test and Phase 2 authority command pass. [VERIFIED: local test execution]
   - Resolution: Phase 2 uses its focused suite plus the exact source-authority validator. It must not rebase, relax, suppress, or otherwise weaken any Phase 1 custody or live-boundary check to make repository-wide discovery green; Phase 1 failures caused by later planning artifacts remain preserved boundary evidence, not Phase 2 test failures to repair. [RESOLVED: D-09 and the Phase 1 non-weakening constraint; final Plans 01-05]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | Adapter, strict parser, scorer, tests, CLI | ✓ | 3.14.5 | — [VERIFIED: local environment] |
| Python standard library | Canonical JSON, hashing, paths, Unicode, tests | ✓ | bundled with Python 3.14.5 | — [VERIFIED: local environment] |
| Git | Existing Phase 1 authority verification only | ✓ | 2.54.0 | No Phase 2 adapter fallback; it consumes accepted local bundle. [VERIFIED: local environment; 01-VERIFICATION.md] |
| Network/model provider/external API | None | Not required | — | Remain out of scope. [VERIFIED: 02-CONTEXT.md] |

**Missing dependencies with no fallback:** None. [VERIFIED: local environment]

**Missing dependencies with fallback:** None. [VERIFIED: local environment]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Python `unittest` (existing) [VERIFIED: codebase tests] |
| Config file | none — standard discovery with `PYTHONPATH=src` [VERIFIED: codebase tests] |
| Quick run command | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_measurement_adapter tests.test_measurement_parsing tests.test_measurement_scoring -q` [RESOLVED: final Plans 01-03] |
| Full Phase 2 suite command | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_measurement_adapter tests.test_measurement_parsing tests.test_measurement_scoring tests.test_measurement_attempts tests.test_measurement_h1 -q` [RESOLVED: final Plan 05] |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TS-03 | Adapter verifies accepted verifier-rooted source authority and builds all 11 canonical records; golden run accepts six positives, rejects four negatives, and surfaces/classifies out candidate. | unit + integration | `python3 -m unittest tests.test_measurement_adapter tests.test_measurement_scoring -q` | ❌ owning tasks create first |
| TS-04 | Closed objects reject unknown/missing/duplicate keys, invalid enum, `not_surfaced`, all noncanonical no-finding forms, and unscoped legacy aliases. | unit/adversarial | `python3 -m unittest tests.test_measurement_parsing -q` | ❌ owning task creates first |
| TS-05 | Every required stable code has exact structured fields; unnamed accepted parameter is warning-only and expected adversarial failures do not make formal golden invalid. | unit + integration | `python3 -m unittest tests.test_measurement_scoring tests.test_measurement_attempts tests.test_measurement_h1 -q` | ❌ owning tasks create first |

### Required Test Matrix

- Adapter: active v2 only; all 11 records and 28 raw identities; 6/4/1 category totals; each directory/registry/expected/gold disagreement produces a sorted blocker and emits no score-eligible batch. [VERIFIED: 02-CONTEXT.md; registry]
- Parsing: malformed JSON; duplicate JSON key; top-level and nested unknown keys; missing explicit no-finding fields; invalid enum; forbidden `not_surfaced`; forbidden current `reject`; declared legacy `reject` mapping with raw-before/raw-after trace. [VERIFIED: 02-CONTEXT.md; frozen execution baseline §11.3]
- Scoring: exact golden all-11 run; each candidate failure mode; positive classified out; missing expected; negative unnecessarily surfaced; unexpected accepted; exact/missing/incorrect identity; empty/not-found/range-invalid evidence. [VERIFIED: frozen execution baseline §6.3; 02-CONTEXT.md]
- Attempts: deterministic complete diagnostic ordering; blocking run is nonzero and lacks metrics/report; warning-only run is zero and `completed_with_warnings`; no-replace collision; diagnostic-only cannot be designated formal. [VERIFIED: 02-CONTEXT.md]
- H1: golden must have no unexpected warnings/errors; adversarial oracle checks exact code and fields; one disputed fixture forces aggregate dispute; source/rule/schema/golden/attempt/diagnostic changes invalidate approval; no machine-created approval. [VERIFIED: 02-CONTEXT.md]

### Sampling Rate

- **Per task commit:** Run the focused tests created first and owned by that task plus `validate-phase2-source-authority`. [RESOLVED: final Plans 01-05]
- **Per plan wave:** Plans 01-03 run their accumulated focused modules; Plan 04 runs the four-module pre-H1 suite and formal/adversarial validators; Plan 05 adds `test_measurement_h1` and runs the final five-module suite. No independent global test-scaffolding wave exists. [RESOLVED: final Plans 01-05]
- **Phase gate:** Full Phase 2 suite green, golden H1 packet has no unexpected diagnostic, and human H1 decision is recorded before Phase 3 planning/execution. [VERIFIED: 02-CONTEXT.md]

### Per-Plan TDD Prerequisites (No Independent Wave 0)

- [ ] Plan 01 Task 02-01-01 creates `tests/test_measurement_adapter.py` before adapter production code.
- [ ] Plan 02 Task 02-02-01 creates `tests/test_measurement_parsing.py` before parser/preflight production code.
- [ ] Plan 03 Task 02-03-01 creates `tests/test_measurement_scoring.py` before scorer production code.
- [ ] Plan 04 Task 02-04-01 creates `tests/test_measurement_attempts.py` before attempt-custody production code.
- [ ] Plan 05 Task 02-05-01 creates `tests/test_measurement_h1.py` before H1 packet/decision production code.
- [ ] The focused Phase 2 target grows monotonically from those owning tasks. Repository-wide discovery is not a Phase 2 gate, and Phase 1 custody/live-boundary assertions remain unchanged. [RESOLVED: final Plans 01-05]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V1 Architecture | yes | Preserve authority → adapter → preflight → score → H1 trust boundaries and forbid external/model paths. [VERIFIED: 02-CONTEXT.md] |
| V2 Authentication | no | No user authentication or remote service exists in Phase 2. [VERIFIED: 02-CONTEXT.md] |
| V3 Session Management | no | No sessions/cookies/tokens exist in Phase 2. [VERIFIED: 02-CONTEXT.md] |
| V4 Access Control | limited | File-path capability is restricted to the accepted bundle, experiment root, and no-replace attempt target. [VERIFIED: 01-VERIFICATION.md; 02-CONTEXT.md] |
| V5 Input Validation | yes | Duplicate-key-safe JSON decoding, closed object schemas, exact types/enums, cross-field no-finding invariant, and no silent repair. [VERIFIED: 02-CONTEXT.md; CITED: https://docs.python.org/3/library/json.html] |
| V6 Cryptography | yes | Use `hashlib.sha256` for integrity binding only; do not hand-roll hashes or claim authenticity from a hash alone. [CITED: https://docs.python.org/3/library/hashlib.html; ASSUMED] |
| V12 Files and Resources | yes | Reuse Phase 1 regular-file, path-escape, raw-byte hash, and accepted-bundle verification controls. [VERIFIED: `filesystem.py`; `01-VERIFICATION.md] |

### Known Threat Patterns for the measurement stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Duplicate JSON keys overwrite an earlier decision | Tampering | `object_pairs_hook` rejects duplicates and emits a stable validation diagnostic. [CITED: https://docs.python.org/3/library/json.html; ASSUMED] |
| Extra fields smuggle score-affecting data | Tampering | Exact key sets at every score-bearing level; separate versioned provenance envelope is never passed to scorer. [VERIFIED: 02-CONTEXT.md] |
| Raw source/evidence drift or normalization hides mismatch | Tampering | Hash raw bytes, validate exact byte slice/text before report projection, retain raw input separately. [VERIFIED: `canonical.py`; 02-CONTEXT.md] |
| Subset/partial attempt is presented as formal evidence | Repudiation | Full all-11 preflight, formal-attempt flag, immutable hash-bound attempt directory, H1 rejects diagnostic-only material. [VERIFIED: 02-CONTEXT.md] |
| Path escape/symlink/special file enters source input | Tampering / Elevation | Reuse Phase 1 accepted-bundle and filesystem verifier; do not reimplement a looser file walk. [VERIFIED: `filesystem.py`; `01-VERIFICATION.md] |

## Sources

### Primary (HIGH confidence)

- [Phase 2 context](02-CONTEXT.md) — locked D-01 through D-16, scope, reusable assets, and H1 authority.
- [Phase 1 verification](../01-isolated-evidence-boundary-and-source-integrity/01-VERIFICATION.md) — accepted v2 source lineage and the current 11-fixture/28-file closure.
- [Fixture registry](/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/config/fixture-registry-pr2164-v1.json) and [Phase 2 authority](/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/phase2/source-authority.json) — local verified source identity.
- [Frozen execution baseline](/Users/zhdeng/Downloads/LFX_RISCV_SpecChoice_v1.3.2_frozen_execution_baseline.md) §§6.1–6.3, 11.3, 14–16 — canonical state, diagnostics, parsing, layout, and determinism contract.
- [Canonical primitives](/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_evidence/canonical.py) and [authority CLI](/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py) — existing reusable implementation.

### Secondary (MEDIUM confidence)

- [Python `json` documentation](https://docs.python.org/3/library/json.html) — serialization and decoder hooks.
- [Python `hashlib` documentation](https://docs.python.org/3/library/hashlib.html) — SHA-256 availability.

### Tertiary (LOW confidence)

- No web-only source is used for a locked decision. A1 and A3 are resolved by D-05/D-06/D-08/D-09 and the final plan set; only the bounded pinned-fixture reader remains an implementation assumption under the agent's discretion. [VERIFIED: 02-CONTEXT.md; final Plans 01-05]

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — current local Python, existing Phase 1 primitives, and official Python documentation were checked. [VERIFIED: local environment; codebase grep]
- Architecture: HIGH — the complete trust/attempt/H1 behavior is locked by D-01–D-16 and validated against current source authority. [VERIFIED: 02-CONTEXT.md; local authority command]
- Pitfalls: HIGH — candidate semantics, diagnostics, no-finding representation, and source custody are specified by the frozen contract and observed code/tests. [VERIFIED: frozen execution baseline; codebase tests]

**Research date:** 2026-07-31  
**Valid until:** 2026-08-30 for codebase findings; revalidate active source-authority and working-tree test behavior before execution. [ASSUMED]
