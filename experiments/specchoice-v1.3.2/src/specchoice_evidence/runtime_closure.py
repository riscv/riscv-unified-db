# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Deterministic, local-only byte custody for executable closure receipts."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from .canonical import require_byte_length, require_sha256, sha256_bytes
from .filesystem import require_relative_posix_path


class RuntimeClosureError(ValueError):
    """Stable failure for an executable closure mismatch."""


def closure_entry(root: Path, relative_path: str) -> dict[str, object]:
    """Capture one existing ordinary file using an experiment-relative path."""
    try:
        normalized = str(require_relative_posix_path(relative_path))
        candidate = (root / normalized).resolve(strict=True)
        root_real = root.resolve(strict=True)
    except (OSError, ValueError) as error:
        raise RuntimeClosureError("RUNTIME_CLOSURE_PATH_INVALID") from error
    if candidate == root_real or root_real not in candidate.parents or not candidate.is_file():
        raise RuntimeClosureError("RUNTIME_CLOSURE_PATH_INVALID")
    raw = candidate.read_bytes()
    return {"byte_length": len(raw), "path": normalized, "sha256": sha256_bytes(raw)}


def build_runtime_closure(root: Path, relative_paths: list[str]) -> dict[str, object]:
    """Freeze an exact, sorted finite file inventory for later no-write preflight."""
    if not isinstance(relative_paths, list) or not relative_paths:
        raise RuntimeClosureError("RUNTIME_CLOSURE_INPUT_INVALID")
    try:
        normalized = sorted(str(require_relative_posix_path(path)) for path in relative_paths)
    except (TypeError, ValueError) as error:
        raise RuntimeClosureError("RUNTIME_CLOSURE_INPUT_INVALID") from error
    if len(set(normalized)) != len(normalized):
        raise RuntimeClosureError("RUNTIME_CLOSURE_INPUT_INVALID")
    return {
        "entries": [closure_entry(root, path) for path in normalized],
        "schema_version": "runtime-executable-closure-v1",
    }


def verify_runtime_closure(closure: object, root: Path) -> dict[str, object]:
    """Prove every bound entry still has exactly the frozen bytes before mutation."""
    if not isinstance(closure, Mapping) or closure.get("schema_version") != "runtime-executable-closure-v1":
        raise RuntimeClosureError("RUNTIME_CLOSURE_INVALID")
    entries = closure.get("entries")
    if not isinstance(entries, list) or not entries:
        raise RuntimeClosureError("RUNTIME_CLOSURE_INVALID")
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, Mapping) or set(entry) != {"byte_length", "path", "sha256"}:
            raise RuntimeClosureError("RUNTIME_CLOSURE_ENTRY_INVALID")
        try:
            path = str(require_relative_posix_path(entry["path"]))
            length = require_byte_length(entry["byte_length"])
            digest = require_sha256(entry["sha256"])
        except (KeyError, ValueError) as error:
            raise RuntimeClosureError("RUNTIME_CLOSURE_ENTRY_INVALID") from error
        if path in seen:
            raise RuntimeClosureError("RUNTIME_CLOSURE_ENTRY_INVALID")
        seen.add(path)
        current = closure_entry(root, path)
        if current["byte_length"] != length or current["sha256"] != digest:
            raise RuntimeClosureError("RUNTIME_CLOSURE_ENTRY_MISMATCH")
    return dict(closure)


def no_user_site_environment() -> dict[str, str]:
    """Return the only environment projection accepted by closure preflights."""
    return {
        "PYTHONDONTWRITEBYTECODE": os.environ.get("PYTHONDONTWRITEBYTECODE", ""),
        "PYTHONNOUSERSITE": os.environ.get("PYTHONNOUSERSITE", ""),
        "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
    }
