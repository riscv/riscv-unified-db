# Phase 1: Isolated Evidence Boundary and Source Integrity - Pattern Map

**Mapped:** 2026-07-30
**Files analyzed:** 23 planned files
**Analogs found:** 9 / 23

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `experiments/specchoice-v1.3.2/README.md` | config/documentation | request-response | `AGENTS.md` | partial |
| `src/specchoice_evidence/canonical.py` | utility | transform | `tools/scripts/gen_schema_index.py` | partial |
| `src/specchoice_evidence/filesystem.py` | utility | file-I/O | `tools/mcp_gen_server/server.py` | partial |
| `src/specchoice_evidence/baseline.py` | service | file-I/O | no close analog | none |
| `src/specchoice_evidence/git_proof.py` | service | request-response | `tools/scripts/download_schema_releases.py` | role-match |
| `src/specchoice_evidence/bundle.py` | service | file-I/O | `tools/scripts/gen_schema_index.py` | partial |
| `src/specchoice_evidence/verify.py` | service | file-I/O | no close analog | none |
| `src/specchoice_evidence/receipt.py` | service | transform | `tools/scripts/gen_schema_index.py` | partial |
| `src/specchoice_evidence/cli.py` | controller | request-response | `tools/scripts/download_schema_releases.py` | role-match |
| `config/source_snapshots.json` | config | transform | `spec/schemas/*.json` | partial |
| `config/boundary_allowlist.json` | config | transform | `cfgs/memmap.json` | partial |
| `tests/__init__.py` | test | n/a | no close analog | none |
| `tests/test_canonical.py` | test | transform | no `unittest` analog | none |
| `tests/test_filesystem_boundary.py` | test | file-I/O | no `unittest` analog | none |
| `tests/test_git_proof.py` | test | request-response | no `unittest` analog | none |
| `tests/test_bundle_verifier.py` | test | file-I/O | no `unittest` analog | none |
| `tests/test_receipts.py` | test | transform | no `unittest` analog | none |
| `bundles/accepted/<generation>/...` | data | file-I/O | no close analog | none |
| `bundles/rejected/<attempt-id>/...` | data | event-driven | no close analog | none |
| `receipts/environment-decision.json` | data | transform | `tools/scripts/gen_schema_index.py` | partial |
| `receipts/environment-audit.json` | data | transform | no close analog | none |
| `receipts/integrity-receipt.json` | data | transform | `tools/scripts/gen_schema_index.py` | partial |
| `receipts/integrity-receipt.md` | data | transform | `tools/scripts/gen_pages_index.py` | partial |

`bundles/` and `receipts/` are runtime data outputs rather than source files. The planner should create their parent directories or generate them through commands, never commit a mutable accepted generation in place.

## Pattern Assignments

### `src/specchoice_evidence/canonical.py` (utility, transform)

**Analog:** `tools/scripts/gen_schema_index.py` (partial; the Phase 1 canonical-byte contract is new).

**Imports and typed helper pattern** (lines 10-16):

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path

type SchemaIndex = dict[str, list[str]]
```

**JSON output pattern** (lines 61-67):

```python
output_json.parent.mkdir(parents=True, exist_ok=True)
output_json.write_text(json.dumps({"schemas": schemas}, indent=2) + "\n", encoding="utf-8")
print(f"Schema index written to {output_json}")
```

**Apply:** retain stdlib imports, future annotations, `Path`, typed public helpers, UTF-8 and final LF. Replace ordinary pretty JSON with the one owned `canonical_json_bytes()` implementation required by D-04/D-08; raw bundle source must be read and hashed as bytes, not passed through text normalization.

---

### `src/specchoice_evidence/filesystem.py`, `baseline.py`, and `verify.py` (utility/service, file-I/O)

**Closest analog:** `tools/mcp_gen_server/server.py` (partial; it shows repository traversal but is not safe enough to copy as an integrity guard).

**Traversal and explicit path conversion pattern** (lines 291-306):

```python
paths: list[Path] = []
if not GEN_DIR.exists():
    return paths
for root, _dirs, files in os.walk(GEN_DIR):
    root_p = Path(root)
    ...
    for f in files:
        ...
        p = root_p / f
        ...
        paths.append(p)
return paths
```

**Input-type failure pattern** (lines 366-374):

```python
rel = args.get("path")
if not isinstance(rel, str):
    raise TypeError("'path' arg must be a string")
p = _ensure_in_gen(Path(rel))
data = _load_yaml(p)
return {"path": rel, "data": data}
```

**Apply:** build a fresh stricter guard: validate POSIX-relative input before joining, `os.lstat` every component and leaf, allow only independent directories/regular files, then read. Do not reuse `_ensure_in_gen` as the Phase 1 containment proof because D-16 requires rejection before symlink following. `baseline.py` must serialize the entire start state and never mutate it; `verify.py` must be stdlib-only and must never import/call `git_proof.py`.

---

### `src/specchoice_evidence/git_proof.py` and `cli.py` (service/controller, request-response)

**Analog:** `tools/scripts/download_schema_releases.py`.

**CLI construction pattern** (lines 23-43):

```python
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gen-schemas-dir", type=Path, default=DEFAULT_GEN_SCHEMAS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()
```

**Checked subprocess + captured output pattern** (lines 65-81):

```python
result = subprocess.run(
    ["gh", "release", "list", "--limit", str(RELEASE_LIST_LIMIT)],
    check=True,
    capture_output=True,
    text=True,
)
return set(result.stdout.splitlines())
```

**Top-level command boundary** (lines 143-160):

```python
def main() -> None:
    args = parse_args()
    ...

if __name__ == "__main__":
    main()
```

**Apply:** use an injected/small Git runner around `subprocess.run`; represent nonzero `merge-base --is-ancestor` and missing objects as stable Phase 1 diagnostic data rather than leaking platform stderr. Only the construction commands may call it. `cli.py` should expose separate `capture-baseline`, `build`, `verify`, and `receipt` subcommands; `verify` cannot construct or fetch. On D-07 failures, write only a rejected-attempt receipt and return nonzero, without an accepted generation/root.

---

### `src/specchoice_evidence/bundle.py` and `receipt.py` (service, file-I/O/transform)

**Analog:** `tools/scripts/gen_schema_index.py`.

**Read/validate/return pattern** (lines 28-35):

```python
def load_schemas(index_path: Path) -> SchemaIndex:
    if not index_path.is_file():
        return {}

    data: dict[str, SchemaIndex] = json.loads(index_path.read_text(encoding="utf-8"))
    return data["schemas"]
```

**Deterministic sorting pattern** (lines 38-50):

```python
for schema_entry in sorted(schemas_dir.iterdir()):
    if not schema_entry.is_dir():
        continue
    versions = sorted(
        version_dir.name for version_dir in schema_entry.iterdir() if version_dir.is_dir()
    )
```

**Apply:** route all writes through staging and validate raw lengths/hashes, derived lineage, content-manifest hash, and logical root before publishing a *new* accepted directory. Keep the non-self-referential content-manifest projection distinct from its accepted identity. `receipt.py` must derive Markdown only from parsed/validated canonical JSON—no filesystem/Git recalculation—and record Markdown failure as incomplete reviewer packaging without invalidating the JSON authority.

---

### `config/*.json`, `README.md`, and local `tests/` (config/documentation/test)

**Existing convention sources:** `pyproject.toml` lines 1-3 and 20-24; `.pre-commit-config.yaml` lines 1-22.

```toml
# SPDX-License-Identifier: BSD-3-Clause-Clear
...
[tool.ruff]
line-length = 100
extend-exclude = [ "ext" ]
```

```yaml
default_language_version:
  python: python3.12
...
      - id: end-of-file-fixer
```

**Apply:** use SPDX-compatible headers in Python/Markdown where appropriate, LF endings/final newline, 100-column Python formatting, and valid JSON. There is no close local `unittest` analog—the existing `tools/python/auto-inst/test_parsing.py` is pytest-based—so implement the research-prescribed isolated `unittest` package rather than introducing pytest or a root dependency. Tests should own temporary fixtures and cover both accepted and rejected state paths.

## Shared Patterns

### Python source conventions

**Sources:** `pyproject.toml` lines 1-3, 20-24; `tools/scripts/gen_schema_index.py` lines 1-16.

Use SPDX header, `from __future__ import annotations`, stdlib imports first, typed public functions, `Path` rather than raw paths, UTF-8 text I/O, final LF, and Ruff’s 100-column limit. Phase code remains under `experiments/specchoice-v1.3.2/` and adds no root dependency.

### Filesystem safety and deterministic ordering

**Source:** `tools/mcp_gen_server/server.py` lines 291-306 and `tools/scripts/gen_schema_index.py` lines 38-50.

Use explicit `Path` objects and sorted discovery. Phase 1 strengthens this with `lstat`, special-file/link rejection, independently verified bytes, POSIX-relative paths, and explicit root containment before open; these are locked custody requirements, not reusable UDB behavior.

### Process errors and receipt states

**Source:** `tools/scripts/download_schema_releases.py` lines 65-81, 115-140.

Construction code captures subprocess results, but Phase 1 converts expected Git failures into stable diagnostic-code receipts. `accepted` is a distinct published state; a failure (notably #2192’s unreachable frozen pin) has no accepted generation ID or downstream-eligible root.

## No Analog Found

| File/group | Role | Data Flow | Reason |
|---|---|---|---|
| `baseline.py` | service | file-I/O | No existing immutable worktree-baseline/delta classifier. |
| `verify.py` | service | file-I/O | No existing offline-only source-bundle verifier. |
| `bundles/accepted` and `bundles/rejected` state model | data | file-I/O/event-driven | No immutable accepted/rejected publication model. |
| `tests/test_*.py` | test | varied | Repository Python tests use pytest; Phase 1 is deliberately stdlib `unittest`. |
| canonical manifests, roots, and integrity receipts | data/service | transform | New contract; use the canonical algorithms and fixtures from `01-RESEARCH.md`, not existing schema JSON conventions. |

## Metadata

**Analog search scope:** `tools/scripts/`, `tools/mcp_gen_server/`, `tools/python/`, root Python/pre-commit configuration, schema/config JSON.
**Files scanned:** 10 primary analog/config files.
**Pattern extraction date:** 2026-07-30
