# Phase 2: Deterministic Measurement Spine - Pattern Map

**Mapped:** 2026-07-31
**Files analyzed:** 17 planned source/config/test files
**Analogs found:** 15 / 17

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `config/measurement/pr2164-adapter-rules-v1.json` | config | transform | `config/fixture-registry-pr2164-v1.json` | exact |
| `config/measurement/canonical-adjudication-schema-v1.json` | config | transform | `config/fixture-registry-pr2164-v1.json` | role-match |
| `fixtures/measurement/golden-predictions-v1.json` | config | transform | `receipts/local-acceptance-v9.json` | role-match |
| `fixtures/measurement/adversarial/*.json` | test fixture | transform | `tests/test_fixture_closure.py` | role-match |
| `src/specchoice_measurement/domain.py` | model | transform | `src/specchoice_evidence/receipt.py` | role-match |
| `src/specchoice_measurement/diagnostics.py` | utility | transform | `src/specchoice_evidence/source_contract.py` | role-match |
| `src/specchoice_measurement/adapter.py` | service | file-I/O | `src/specchoice_evidence/verify.py` | exact |
| `src/specchoice_measurement/strict_json.py` | utility | transform | `src/specchoice_evidence/canonical.py` | partial; duplicate-key decoder is new |
| `src/specchoice_measurement/preflight.py` | service | batch | `src/specchoice_evidence/source_contract.py` | role-match |
| `src/specchoice_measurement/scoring.py` | service | transform | `src/specchoice_evidence/receipt.py` | partial; metrics are new |
| `src/specchoice_measurement/attempts.py` | service | file-I/O | `src/specchoice_evidence/bundle.py` | exact |
| `src/specchoice_measurement/h1.py` | service | transform | `src/specchoice_evidence/receipt.py` | exact |
| `src/specchoice_measurement/cli.py` | controller | request-response | `src/specchoice_evidence/cli.py` | exact |
| `tests/test_measurement_adapter.py` | test | file-I/O | `tests/test_fixture_closure.py` | exact |
| `tests/test_measurement_parsing.py` | test | transform | `tests/test_canonical.py` | role-match |
| `tests/test_measurement_scoring.py` | test | transform | `tests/test_receipts.py` | role-match |
| `tests/test_measurement_attempts.py`, `tests/test_measurement_h1.py` | test | file-I/O / transform | `tests/test_fixture_closure.py`, `tests/test_receipts.py` | role-match |

## Pattern Assignments

### `src/specchoice_measurement/adapter.py` (service, file-I/O)

**Analog:** `experiments/specchoice-v1.3.2/src/specchoice_evidence/verify.py`

Use the accepted-bundle verifier first, then inspect every declared source path through the Phase 1 filesystem API. Do not traverse fixture directories independently or read a file before the path check. Preserve the raw bytes/hash before interpreting the bounded PR #2164 YAML syntax.

**Imports and authority-read pattern** (`verify.py:12-20, 50-62`):

```python
from .canonical import canonical_json_bytes, require_byte_length, require_sha256, sha256_bytes
from .filesystem import FilesystemPolicyError, inspect_authoritative_path, require_relative_posix_path

def _load_canonical(root: Path, relative_path: str, code: str) -> tuple[dict[str, Any], bytes]:
    try:
        evidence = inspect_authoritative_path(root, relative_path)
        if evidence.file_kind != "regular_file":
            raise BundleVerificationError(code)
        raw = (root / relative_path).read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (FilesystemPolicyError, OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BundleVerificationError(code) from error
    if not isinstance(value, dict) or canonical_json_bytes(value) != raw:
        raise BundleVerificationError(code)
    return value, raw
```

**Finite-set/closed-key pattern** (`source_contract.py:54-87`):

```python
if not isinstance(registry, Mapping) or set(registry) != {
    "fixture_count", "fixtures", "pinned_commit_sha", "pinned_tree_sha", "pull_request",
    "raw_file_count", "repository", "schema_version", "snapshot_id",
}:
    raise FixtureRegistryError("FIXTURE_REGISTRY_INVALID")
```

Apply this style to adapter rules and the score-bearing subset: enumerate allowed input keys, validate all eleven fixture IDs in sorted order, and collect a sorted diagnostic record for each disagreement. A blocking adapter result must contain zero score-eligible records.

### `src/specchoice_measurement/strict_json.py` (utility, transform)

**Analog:** `experiments/specchoice-v1.3.2/src/specchoice_evidence/canonical.py`

**Canonical projection and raw-byte separation** (`canonical.py:20-46`):

```python
def normalize_canonical_text(value: str) -> str:
    return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))

def canonical_json_bytes(value: Any) -> bytes:
    normalized = normalize_canonical_value(value)
    return (
        json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
```

Copy the projection/hash boundary, but add a Phase-2-only `json.loads` decoder using `object_pairs_hook` that rejects duplicate keys and `parse_constant` that rejects non-JSON constants. Validate exact key sets at payload, prediction, adjudication, and evidence-span levels before any semantic checks. Preserve raw input bytes; call canonical projection only after successful validation. The legacy ingress may rewrite only `reject -> classify_out`, emitting a normalization diagnostic with before/after values; current-schema parsing must reject `reject`.

### `src/specchoice_measurement/preflight.py` and `diagnostics.py` (service/utility, batch/transform)

**Analog:** `experiments/specchoice-v1.3.2/src/specchoice_evidence/source_contract.py`

**Stable code plus exception translation** (`source_contract.py:47-52, 78-87`):

```python
def _fixture_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise FixtureRegistryError("FIXTURE_PATH_INVALID")
    try:
        return require_relative_posix_path(value).as_posix()
    except FilesystemPolicyError as error:
        raise FixtureRegistryError(str(error)) from error

if fixture_id in seen_ids:
    raise FixtureRegistryError("FIXTURE_DUPLICATE")
```

Use typed/frozen diagnostic records, each carrying at least `code`, `fixture_id` when available, field/path, expected/observed values, severity, and source identities. Sort diagnostics by a declared tuple (for example fixture ID, code, field, occurrence) once at the end. Preflight must be pure: it returns parsed predictions plus the complete sorted diagnostic list and never calls scoring or writes metrics.

### `src/specchoice_measurement/scoring.py` (service, transform)

**Analog:** `experiments/specchoice-v1.3.2/src/specchoice_evidence/receipt.py`

**Hash non-cyclic canonical projections, not mutable objects** (`receipt.py:15-25, 61-88`):

```python
def _receipt_projection(receipt: dict[str, Any]) -> dict[str, Any]:
    projected = dict(receipt)
    projected.pop("receipt_sha256", None)
    return projected

def _hashed(receipt: dict[str, Any]) -> dict[str, Any]:
    projected = _receipt_projection(receipt)
    projected["receipt_sha256"] = sha256_bytes(canonical_json_bytes(projected))
    return projected
```

Score only canonical adapter records and only after preflight has no blocking diagnostic. Emit independent per-case and aggregate fields for surfacing, disposition, identity, and evidence integrity; preserve the candidate as surfaced then `classify_out`. `ACCEPTED_PARAMETER_NAME_MISSING` is warning-only: it changes identity coverage but cannot revise surfacing/disposition or invalidate an otherwise valid measurement attempt.

### `src/specchoice_measurement/attempts.py` (service, file-I/O)

**Analog:** `experiments/specchoice-v1.3.2/src/specchoice_evidence/bundle.py`

**Exact writes with fsync** (`bundle.py:151-164`):

```python
def _sync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)

def _write_exact(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
```

**No-replace publication rule** (`bundle.py:460-465`):

```python
def _native_publish_no_replace(source: Path, target: Path) -> None:
    """Atomically rename a staged directory only when its target does not exist.

    This intentionally has no `os.replace` fallback: replacing an attacker-created
    directory would undermine the immutable-generation namespace.
    """
```

Stage every attempt under a sibling temporary directory. Write one closed attempt manifest that embeds lossless base64 raw-prediction bytes, their SHA-256, the complete binding map, and terminal status; write parsed projection, diagnostics, and any permitted score artifacts separately. Use exclusive-create writes, fsync, then the proven no-replace directory publish primitive. Validation must recover the exact original raw bytes from the manifest before comparing their hash. An existing attempt ID is an error, never a reason to overwrite or merge. Failed preflight attempts are immutable audit artifacts but contain no metrics/report authority.

### `src/specchoice_measurement/h1.py` (service, transform)

**Analog:** `experiments/specchoice-v1.3.2/src/specchoice_evidence/receipt.py`

**Deterministic human projection test pattern** (`tests/test_receipts.py:71-84`):

```python
receipt = validate_receipt(receipt_path)
self.assertEqual(render_markdown(receipt), (root / "receipts/integrity-receipt-v5.md").read_text(encoding="utf-8"))
self.assertEqual(render_markdown(json.loads(receipt_path.read_text(encoding="utf-8"))), render_markdown(receipt))
```

Make canonical JSON the authority and Markdown a pure projection. Hash the packet after excluding only its self-hash. Validate that every binding hash (accepted fixture root/generation, registry, adapter version/rule hash, schema, golden set, formal attempt, diagnostics) still matches. The validator may accept only the three declared decision strings, but no command constructs `approved`; it merely validates a human-authored decision. Any fixture dispute forces aggregate `disputed`.

### `src/specchoice_measurement/cli.py` (controller, request-response)

**Analog:** `experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py`

**Command handler and exit pattern** (`cli.py:595-615, 876-1054`):

```python
def command_validate_phase2_source_authority(args: argparse.Namespace) -> int:
    raw = args.authority.read_bytes()
    authority = json.loads(raw.decode("utf-8"))
    if not isinstance(authority, dict) or canonical_json_bytes(authority) != raw:
        raise ReceiptError("PHASE2_SOURCE_AUTHORITY_NOT_CANONICAL")
    verified = verify_accepted_bundle(args.bundle)
    # compare all bound identities before returning a canonical result
    return 0

def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.handler(args)
    except (..., ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2
```

Use `argparse` subcommands with `Path` arguments and `set_defaults(handler=...)`. Formal command validates source authority, adapter batch and complete eleven-case prediction identity before creating an attempt. Its blocking diagnostics result in nonzero exit and no metrics. Targeted runs explicitly produce `diagnostic_only`; H1 command rejects that status.

### Test modules (test, file-I/O / transform)

**Analogs:** `tests/test_canonical.py`, `tests/test_fixture_closure.py`, `tests/test_receipts.py`

**Compact value-contract test** (`test_canonical.py:16-33`):

```python
for invalid in (-1, True, 1.5, "1"):
    with self.assertRaisesRegex(CanonicalValueError, "INVALID_BYTE_LENGTH"):
        require_byte_length(invalid)
```

**Parameterized adversarial code matrix** (`test_fixture_closure.py:48-62`):

```python
for mutation, code in (...):
    invalid = copy.deepcopy(self.registry)
    mutation(invalid)
    with self.subTest(code=code), self.assertRaisesRegex(FixtureRegistryError, code):
        validate_fixture_registry(invalid)
```

**No-replace race test** (`test_fixture_closure.py:78-154`): patch the native publisher to create the target just before publication, assert the stable target-exists code, then assert that the competing target contents were not altered.

Use `unittest.TestCase`, `tempfile.TemporaryDirectory`, `copy.deepcopy`, and `unittest.mock`. For every adversarial prediction, assert the complete structured diagnostic oracle (code and fields), not merely an exception. For H1, assert byte-identical packet/Markdown projection and that each changed bound hash invalidates the decision.

## Shared Patterns

### Canonical JSON versus raw bytes

**Source:** `src/specchoice_evidence/canonical.py:20-46`
**Apply to:** adapter records, parsed projections, metrics, attempts, H1 JSON/Markdown.

Raw source/prediction identity is `sha256_bytes(raw)`, without decoding or normalization. NFC/LF/sorted-key canonical JSON is only a derived view and always ends in exactly one LF. Do not use canonical serialization to decide raw evidence equality.

### Filesystem/path safety

**Source:** `src/specchoice_evidence/filesystem.py:27-88`
**Apply to:** source authority, adapter input, attempt-root handling.

Use `require_relative_posix_path`, component-wise `lstat`, `O_NOFOLLOW`, `fstat` inode/device comparison, and regular-file-only checks. Reuse this API; do not add a simpler `Path.resolve()` based reader for authoritative inputs.

### Immutable artifact namespaces

**Source:** `src/specchoice_evidence/bundle.py:151-164, 460-465`
**Apply to:** adapter batches, formal/diagnostic attempts, H1 packet/decision.

Exclusive creation plus synced staged directories and native no-replace publication is mandatory. No `os.replace` fallback exists for immutable terminal namespaces.

### Authority CLI and errors

**Source:** `src/specchoice_evidence/cli.py:595-615, 876-1054`
**Apply to:** Phase 2 CLI.

Validate canonical source-authority bytes and accepted bundle identity before domain work. Commands return `0` only for non-blocking terminal statuses; caught stable `ValueError` family errors print a code to stderr and return `2`.

## No Analog Found

| File/Concern | Role | Data Flow | Reason |
|---|---|---|---|
| duplicate-key-safe closed prediction decoder | utility | transform | Existing code uses ordinary `json.loads`; Phase 2 must add `object_pairs_hook` / `parse_constant` protection. |
| independent surfacing/disposition/identity/evidence metrics | service | transform | Phase 1 has hash-bound receipts but no measurement scorer; use its deterministic projection discipline, not its business logic. |

## Metadata

**Analog search scope:** `experiments/specchoice-v1.3.2/src/specchoice_evidence/`, `experiments/specchoice-v1.3.2/tests/`, accepted verifier-rooted v2 bundle
**Files scanned:** 11 source/test analogs and Phase 2 upstream artifacts
**Pattern extraction date:** 2026-07-31
