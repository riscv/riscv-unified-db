# Phase 4: Offline Treatments, Retrieval, and Branch Freeze - Pattern Map

**Mapped:** 2026-08-04
**Files analyzed:** 18 likely new source/test/contract/artifact paths
**Analogs found:** 18 / 18 (some Phase 4 domain logic is new; its boundary mechanics have exact analogs)

## File Classification

| New/modified file or artifact | Role | Data flow | Closest analog | Match |
|---|---|---|---|---|
| `src/specchoice_treatments/__init__.py` | package | transform | `src/specchoice_data/__init__.py` | exact |
| `src/specchoice_treatments/schema.py` | model/utility | transform | `src/specchoice_measurement/strict_json.py`, `src/specchoice_data/relevance.py` | role-match |
| `src/specchoice_treatments/prompts.py` | service | transform/file-I/O | `src/specchoice_data/review.py`, `src/specchoice_evidence/canonical.py` | role-match |
| `src/specchoice_treatments/retrieval.py` | service | transform/request-response | `src/specchoice_data/relevance.py` | partial (new lexical domain) |
| `src/specchoice_treatments/h3.py` | service | file-I/O/request-response | `src/specchoice_data/h2.py` | exact |
| `src/specchoice_treatments/cli.py` | route/controller | request-response | `src/specchoice_data/cli.py` | exact |
| `config/treatments/*.json` | config | transform | `config/data/phase3-data-schema-v1.json` | role-match |
| `fixtures/treatments/*.json` | fixture | file-I/O | `fixtures/measurement/adversarial/*.json` | role-match |
| `fixtures/treatments/*.txt` | fixture | file-I/O | `bundles/accepted/.../raw/*` authority treatment | partial |
| `prompts/treatments/*.txt` | artifact | file-I/O | `reports/h2/*/review-packet.md` | partial (raw text, not Markdown projection) |
| `prompts/treatments/*manifest*.json` | artifact | file-I/O | `reports/h2/data-eligibility-v1.json` | exact |
| `reports/h3/*packet*.json` | artifact | file-I/O | `reports/h2/h2-data-review-v1/review-packet.json` | exact |
| `reports/h3/*packet*.md` | artifact | file-I/O | `reports/h2/h2-data-review-v1/review-packet.md` | exact |
| `reports/h3/*retrieval*.json` | artifact | transform/file-I/O | `reports/h2/data-eligibility-v1.json` | role-match |
| `receipts/h3-*-readiness-v1.json` | receipt | file-I/O | `receipts/h2-data-review-readiness-v1.json` | exact |
| `reviews/h3-*-decision-v1.json` | human decision | file-I/O | `reviews/h2-data-decision-v1.json` | exact |
| `phase4/*authority*.json` | authority | file-I/O | `phase3/data-authority-v1.json` | exact |
| `tests/test_treatments_{frame,prompts,retrieval,h3}.py` | test | batch | `tests/test_data_h2.py`, `tests/test_filesystem_boundary.py` | exact |

## Pattern Assignments

### `src/specchoice_treatments/schema.py` (strict contract parser, transform)

**Primary analogs:** `src/specchoice_measurement/strict_json.py`; `src/specchoice_data/relevance.py`.

**Copy imports and decode boundary from** `strict_json.py:7-52`:

```python
from specchoice_evidence.canonical import canonical_json_bytes
from .diagnostics import Diagnostic

def decode_strict_json(raw: bytes) -> object:
    text = raw.decode("utf-8")
    return json.loads(text, object_pairs_hook=_reject_duplicate_keys, parse_constant=_reject_constant)
```

Use this before every Phase 4 JSON exact-key check. Do not use plain `json.loads`; duplicate keys must fail before fields are inspected.

**Copy exact-key and traversable-diagnostics style from** `strict_json.py:68-78, 155-207`:

```python
actual = set(value)
for key in sorted(expected - actual):
    diagnostics.append(Diagnostic("FIELD_MISSING", "blocker", fixture_id, f"{field}.{key}", expected="present"))
for key in sorted(actual - expected):
    diagnostics.append(Diagnostic("FIELD_UNKNOWN", "blocker", fixture_id, f"{field}.{key}", observed=value[key]))
return actual == set(expected)
```

Keep parsing fail-closed but collect deterministically sortable diagnostics for structurally traversable input. B/C must require exactly the three axes and one non-empty source-bound span per axis; A must reject/omit the frame rather than receive a dummy frame.

**Copy source-bound frame shape from** `relevance.py:185-211`:

```python
_FRAME_AXES = {"authority", "choice_object", "choice_space_origin"}
if not isinstance(frame, Mapping) or set(frame) != _FRAME_AXES:
    raise RelevanceValidationError("METAMORPHIC_SOURCE_INVALID")
```

Replace the Phase 3 non-empty-string condition with the frozen Phase 4 enums, including `unknown`; retain the exact three-key set rule. Verify spans against raw target bytes using the byte-range/text technique in `strict_json.py:83-151`, never normalized prompt text.

### `src/specchoice_treatments/prompts.py` (raw prompt renderer, manifest, transform/file-I/O)

**Primary analogs:** `src/specchoice_evidence/canonical.py`; `src/specchoice_data/review.py`.

**Canonical JSON and hash reuse from** `canonical.py:18-53`:

```python
def canonical_json_bytes(value: Any) -> bytes:
    normalized = normalize_canonical_value(value)
    return (json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
```

Prompt authority is deliberately different: render and retain raw UTF-8/LF bytes, then call `sha256_bytes(prompt_raw)`. Canonicalize only response records, bundle/diff manifests, budget records, and H3 inputs. Do not normalize raw prompt bytes through `normalize_canonical_text`.

**Markdown is projection-only; copy from** `review.py:33-42` or `h2.py:477-485`:

```python
return (... "## Canonical packet\n\n```json\n"
        + canonical_json_bytes(dict(packet)).decode("utf-8").rstrip("\n")
        + "\n```\n").encode("utf-8")
```

Use this only for an optional human-readable H3 report. A/B/C prompts must remain separate raw `.txt` artifacts, not a Markdown-derived source of truth.

**New, tightly scoped domain work:** render named sections before final concatenation and return a section-hash/diff manifest. Compare every shared section byte-for-byte; permit only A↔B frame presence and B↔C pair selection. Record the raw-byte SHA-256, UTF-8 byte count, Unicode code-point count, LF line count, and one explicitly frozen standard-library lexical count. No padding or provider-token field is permitted (`not_applicable_red` only).

### `src/specchoice_treatments/retrieval.py` (test-only TF-IDF/cosine verifier, transform)

**Closest analog:** `src/specchoice_data/relevance.py:15-72, 76-131`.

Reuse its closed-registry discipline: `Mapping` input checks, exact allowed keys, sorted/unique identifiers, self-hash construction, and a stable `ValueError` subclass (`RetrievalContractError`). In particular, copy the recursive forbidden-field boundary idea from `relevance.py:55-62` for rejecting authority/gold/frame/relevance/ranking fields as query material.

```python
def _contains_forbidden_rank_field(value: object) -> bool:
    if isinstance(value, Mapping):
        return bool(_FORBIDDEN_RANK_FIELDS & set(value)) or any(
            _contains_forbidden_rank_field(item) for item in value.values()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_rank_field(item) for item in value)
    return False
```

The scoring implementation itself has no existing analog and should be minimal standard-library code (`collections.Counter`, `math`, `re`). Freeze its tokenizer, normalized document construction, TF/IDF formula, zero-vector convention, and score serialization in one canonical config before emitting fixtures. Require synthetic target and every complete pair to have `test_only: true` and `count_eligible: false` before tokenization. Query only frozen target source text.

**Locked final ordering (from Research D-08):**

```python
if len(distinct_eligible_pairs) < 2:
    raise RetrievalContractError("INSUFFICIENT_RETRIEVAL_PAIRS")
return sorted(scored_pairs, key=lambda item: (-item.score, item.pair_id))[:2]
```

Always return two whole pairs and their scores—even zero scores. Never add a threshold, partial ranking, embedding, vector store, learned reranker, Phase 3 corpus fallback, or production entry point.

### `src/specchoice_treatments/h3.py` (H3 readiness/decision/Red authority, file-I/O)

**Exact analog:** `src/specchoice_data/h2.py:91-105, 455-645`.

**Authoritative canonical reader pattern** (`h2.py:96-105`):

```python
_, raw = read_authoritative_file(root, relative)
value = decode_strict_json(raw)
if not isinstance(value, dict) or canonical_json_bytes(value) != raw:
    raise H2ValidationError("H2_CHAIN_INPUT_INVALID")
```

Adapt error names to H3; use it to read all Phase 3 authority/report/packet/readiness/decision leaves and all Phase 4 canonical JSON leaves. Reuse `validate_phase3_chain_v1` and `validate_phase3_data_authority_v1`, rather than copying or re-deriving Phase 3 counts, labels, splits, or eligibility.

**Decision-free packet/readiness sequence** (`h2.py:455-506`): build a canonical packet with exact bindings and an explicit non-authority warning; render Markdown from that packet; then make readiness bind `packet_sha256`, `markdown_sha256`, source-chain identity, and `status: ready_for_human`. Machine code must not add any reviewer field.

**Human decision validation** (`h2.py:513-555`): require an exact key set, canonical self-hash, exact packet/readiness bindings, non-empty reviewer attestation fields, canonical UTC, declared disposition enum, and ordered acknowledgement categories. For H3 use only `{approved_red, disputed, incomplete}`—do not inherit H2's `approved` enum.

**Approval-before-write guard** (`h2.py:618-645`):

```python
validate_h3_decision_v1(decision=decision, packet=packet, readiness=readiness)
if decision.get("aggregate_disposition") != "approved_red":
    raise H3ValidationError("H3_APPROVAL_REQUIRED")
write_exact_descriptor_files(output_root, payloads)
```

Only an exact `approved_red` decision can publish an authority. Its closed fields must include `N_strict: 0`, `repeat_count: 0`, `h4_required: false`, `h4_reason: not_applicable_red`, `provider_config_present: false`, `model_snapshot: not_applicable_red`, `credentials_boundary: not_applicable_red`, and `external_calls_authorized: false`. `disputed` and `incomplete` may validate as decisions but must create no authority; frozen drift must raise a version-successor error.

### `src/specchoice_treatments/cli.py` (offline CLI, request-response)

**Exact analog:** `src/specchoice_data/cli.py:128-205`.

```python
parser = argparse.ArgumentParser(prog="specchoice-data")
commands = parser.add_subparsers(dest="command", required=True)
command = commands.add_parser("...")
command.add_argument("--...", type=Path, required=True)
command.set_defaults(handler=_handler)

try:
    args = build_parser().parse_args(argv)
    return int(args.handler(args))
except (DataAdmissionError, ValueError) as error:
    print(str(error), file=sys.stderr)
    return 2
```

Use the same required-subparser/handler/error-exit style, with an intentionally exact allowlist containing only `verify-retrieval-contract`. Validate input paths with descriptor-bound readers and emit canonical JSON to `sys.stdout.buffer`. H3 is library-first unless a later plan proves a command does not expand this allowlist. Do not register model/provider/run/H3 execution commands; unknown commands must reach argparse failure without network activity.

### `config/treatments/*.json` and `fixtures/treatments/*` (closed config and isolated fixtures, file-I/O)

**Closest analogs:** `config/data/phase3-data-schema-v1.json`, `fixtures/measurement/adversarial/required-diagnostics-v*.json`, and Phase 3 preregistration artifacts.

All machine JSON should already equal `canonical_json_bytes(decoded_value)`. Use explicit schema/version and self-hash fields like `relevance.py:50-53`; include sorted arrays wherever order contributes to identity (`relevance.py:41-48`). Keep fixture root physically and semantically separate from `data/preregistration/`: synthetic prompt target and each corpus item visibly require `test_only=true` plus `count_eligible=false`; contract responses visibly require `origin=contract_fixture` plus `model_generated=false`.

Create only the minimal files needed by the four strictly sequential objectives:

1. Wave 1: closed frame/response/advisory configs plus B/C valid and adversarial response fixtures.
2. Wave 2: one synthetic target, at least three complete synthetic pairs, A/B/C raw prompt bytes, human contract responses, and canonical prompt/diff/budget manifest.
3. Wave 3: one closed lexical-retrieval config and canonical verification report.
4. Wave 4: H3 packet, Markdown projection, readiness, human decision template/record, Red authority, and closed no-model inventory/report.

No provider/model/configuration/credential/environment-variable file is a Phase 4 artifact.

### `tests/test_treatments_{frame,prompts,retrieval,h3}.py` (unittest batch tests)

**Primary analog:** `tests/test_data_h2.py:1-258`; filesystem adversarial analog: `tests/test_filesystem_boundary.py:627-771`.

Copy the standard harness: `unittest.TestCase`, `Path(__file__).parents[1]` experiment root, `TemporaryDirectory`, `deepcopy` mutation, `assertRaisesRegex` for stable codes, and a local `_hash()` helper that hashes a dict excluding its self-hash (`test_data_h2.py:26-91`).

Build each test module around its single wave objective:

- `test_treatments_frame.py`: valid B/C `unknown`; extra/missing axis; invalid enum; duplicate raw JSON key; A-frame rejection; empty/non-UTF-8/out-of-range/mismatched source span; advisory warning ordering and non-blocking result.
- `test_treatments_prompts.py`: raw LF bytes/hashes; canonical response/manifest; equal pair counts/shared-section hashes; only allowed A↔B and B↔C deltas; padding/unrelated delta failure; count determinism; contract response cannot enter raw/run evidence.
- `test_treatments_retrieval.py`: distinct complete top two; target-dependent rank; zero-score result; score tie by `pair_id`; `<2` raises `INSUFFICIENT_RETRIEVAL_PAIRS` with no partial list; Phase 3/non-test corpus and target reject before ranking; CLI has only one command; patched socket/HTTP sentinel sees no activity.
- `test_treatments_h3.py`: H3 packet/readiness recomputes exact Phase 3 roots; only `approved_red` writes identical-resume authority; `disputed`, `incomplete`, missing/changed decision, input drift, divergent pre-existing output, symlink/partial destination, H4/model escalation, forbidden imports, and unknown model commands all fail closed.

## Shared Patterns

### Canonical JSON and identities

**Source:** `src/specchoice_evidence/canonical.py:18-53`
**Apply to:** every JSON config, response, manifest, report, readiness, decision, and authority.

Use NFC/LF recursively, sorted keys, compact separators, trailing LF, and `sha256_bytes`; validate boolean-vs-int and SHA format via `require_byte_length`/`require_sha256` where needed. Raw source/prompt bytes are hashed untouched.

### Descriptor-bound authoritative I/O and exact resume

**Source:** `src/specchoice_evidence/filesystem.py:198-234, 251-345, 616-700`
**Apply to:** all H3 input reads and any prompt/report/readiness/authority publication.

Use `read_authoritative_file` for leaves and `write_exact_descriptor_files` for a related artifact set. The latter sorts paths, rejects invalid/overlapping targets, refuses unsafe leaf kinds and divergent existing bytes, and permits only exact resume. Never replace it with `Path.read_bytes`/`write_bytes`, a prior `exists()` check, symlink-following, or custom atomic writer.

### Fail-closed errors and stable diagnostics

**Source:** `src/specchoice_measurement/diagnostics.py:10-46`; `src/specchoice_data/h2.py:513-645`.
**Apply to:** schema, retrieval, prompt diff, CLI, and H3.

Use package-specific `ValueError` subclasses with stable uppercase codes. Where multiple validation findings are retained, serialize `ordered_diagnostics`; do not use input traversal order. Authority writers validate all bindings and the explicit approval state before any write.

### Human authority remains separate from machine readiness

**Source:** `src/specchoice_data/review.py:18-140`; `src/specchoice_data/h2.py:455-555`.
**Apply to:** H3 packet/readiness/decision/authority.

The packet is decision-free; Markdown is a canonical JSON projection; readiness only binds exact machine products; human decision has required non-empty identity/attestation/signature/timestamp plus content hashes. Neither readiness nor `incomplete`/`disputed` is authority.

### Strictly sequential implementation order

**Source:** `04-RESEARCH.md:290-301`; `ROADMAP.md:245-271`.
**Apply to:** plan construction.

Use exactly four serial waves with one objective each: `frame → prompts → retrieval → H3`. Wave N tests must pass before Wave N+1 adds dependent artifacts; do not parallelize files across objectives or combine the no-model gate with a retrieval/model feature.

## No Analog Found

| New area | Role | Data flow | Why no exact analog / planner guidance |
|---|---|---|---|
| Frozen standard-library TF-IDF/cosine formula | service | transform | No lexical retriever exists. Implement the smallest local pure function after freezing a canonical lexical config; no dependency or learned component. |
| Raw A/B/C structural-diff allowlist and natural token accounting | utility | transform | Existing reports show canonical projection but not controlled prompt comparison. Build named-section byte hashes and deterministic counts; do not pad. |
| Static/runtime absence audit for model/network/credentials surfaces | security utility | batch | Existing filesystem hardening is relevant but there is no prior no-model audit. Keep it a small AST/import + CLI inventory + patched-network test, scoped to Phase 4 package. |

## Metadata

**Analog search scope:** `experiments/specchoice-v1.3.2/src`, `tests`, `config`, `fixtures`, `data`, `reports`, `receipts`, `reviews`, and Phase 1–3 planning/verification artifacts.
**Files scanned:** 18 focused source/test/contract analogs plus Phase 3 summaries and verification.
**Pattern extraction date:** 2026-08-04.
