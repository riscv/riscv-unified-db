# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Immutable phase-start baseline and five-way boundary classification."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .canonical import canonical_json_bytes, require_byte_length, require_sha256, sha256_bytes
from .filesystem import FilesystemPolicyError, inspect_authoritative_path


class BaselineError(ValueError):
    """Stable baseline validation or capture diagnostic."""


CLASSIFICATIONS = {
    "allowed_phase_change",
    "preexisting_unrelated",
    "new_out_of_boundary",
    "modified_out_of_boundary",
    "deleted_out_of_boundary",
}

DS_STORE_DIAGNOSTIC = "DS_STORE_IGNORED_OS_METADATA"


@dataclass(frozen=True)
class BoundaryResult:
    baseline_sha256: str
    classifications: list[dict[str, object]]
    blocking_violations: int


def _is_ds_store(path: str) -> bool:
    return path.rsplit("/", 1)[-1] == ".DS_Store"


def _relative(path: str) -> str:
    if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path:
        raise BaselineError("PATH_ESCAPE_DETECTED")
    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise BaselineError("PATH_ESCAPE_DETECTED")
    return path


def path_is_allowed(path: str, allowlist: dict[str, object]) -> bool:
    """Use exact paths or a slash-terminated root; never prefix matching."""
    candidate = _relative(path)
    roots = allowlist.get("roots", [])
    exact_files = allowlist.get("exact_files", [])
    if not isinstance(roots, list) or not isinstance(exact_files, list):
        raise BaselineError("INVALID_ALLOWLIST")
    return candidate in exact_files or any(
        isinstance(root, str) and root.endswith("/") and candidate.startswith(root) for root in roots
    )


def load_baseline(path: Path) -> tuple[dict[str, Any], str]:
    """Load and validate immutable canonical baseline bytes and field invariants."""
    raw = path.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BaselineError("INVALID_BASELINE_JSON") from error
    if canonical_json_bytes(payload) != raw:
        raise BaselineError("BASELINE_NOT_CANONICAL")
    if payload.get("schema_version") != "1":
        raise BaselineError("UNSUPPORTED_BASELINE_SCHEMA")
    worktree = payload.get("worktree")
    if not isinstance(worktree, dict):
        raise BaselineError("INVALID_BASELINE")
    for section in ("tracked_changes", "untracked_files"):
        entries = worktree.get(section)
        if not isinstance(entries, list):
            raise BaselineError("INVALID_BASELINE")
        paths: list[str] = []
        for item in entries:
            if not isinstance(item, dict):
                raise BaselineError("INVALID_BASELINE")
            paths.append(_relative(str(item.get("path", ""))))
            if item.get("file_kind") == "regular_file":
                require_byte_length(item.get("byte_length"))
                require_sha256(item.get("sha256"))
        if paths != sorted(paths) or len(paths) != len(set(paths)):
            raise BaselineError("BASELINE_PATHS_NOT_SORTED")
    allowlist = payload.get("allowlist")
    if not isinstance(allowlist, dict):
        raise BaselineError("INVALID_ALLOWLIST")
    return payload, sha256_bytes(raw)


def capture_baseline(destination: Path, payload: dict[str, Any]) -> str:
    """Create a new canonical generation; never overwrite an existing baseline."""
    if destination.exists() or destination.is_symlink():
        raise BaselineError("BASELINE_ALREADY_EXISTS")
    destination.parent.mkdir(parents=True, exist_ok=True)
    encoded = canonical_json_bytes(payload)
    temporary = destination.with_name(f".{destination.name}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    except FileExistsError as error:
        raise BaselineError("BASELINE_ALREADY_EXISTS") from error
    return sha256_bytes(encoded)


def create_restart_baseline(
    previous_path: Path,
    destination: Path,
    *,
    previous_reference: str,
    reason_code: str,
    remediation: dict[str, object],
) -> tuple[str, str]:
    """Create a D-15 successor without recapturing or reclassifying start state."""
    previous, previous_sha256 = load_baseline(previous_path)
    _relative(previous_reference)
    if not isinstance(reason_code, str) or not reason_code:
        raise BaselineError("INVALID_RESTART_REASON")
    if not isinstance(remediation, dict):
        raise BaselineError("INVALID_RESTART_REMEDIATION")
    payload = json.loads(canonical_json_bytes(previous).decode("utf-8"))
    payload["restart"] = {
        "previous_baseline": {"path": previous_reference, "sha256": previous_sha256},
        "reason_code": reason_code,
        "remediation": remediation,
        "schema_version": "1",
    }
    return capture_baseline(destination, payload), previous_sha256


def validate_restart_lineage(baseline_path: Path, previous_path: Path) -> tuple[str, str]:
    """Prove a successor retained its predecessor's attribution inventory exactly."""
    current, current_sha256 = load_baseline(baseline_path)
    previous, previous_sha256 = load_baseline(previous_path)
    restart = current.get("restart")
    if not isinstance(restart, dict):
        raise BaselineError("RESTART_LINEAGE_MISSING")
    predecessor = restart.get("previous_baseline")
    if not isinstance(predecessor, dict) or predecessor.get("sha256") != previous_sha256:
        raise BaselineError("RESTART_LINEAGE_MISMATCH")
    for key in ("allowlist", "file_kind_policy", "index", "repository", "worktree"):
        if current.get(key) != previous.get(key):
            raise BaselineError("RESTART_RECLASSIFICATION_DETECTED")
    return current_sha256, previous_sha256


def _git_paths(root: Path, *arguments: str) -> set[str]:
    output = subprocess.run(
        ["git", "-C", os.fspath(root), *arguments],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout
    return {item.decode("utf-8", "surrogateescape") for item in output.split(b"\0") if item}


def capture_current_paths(root: Path) -> set[str]:
    """Collect the current delta plus visible `.DS_Store` metadata paths."""
    paths = (
        _git_paths(root, "diff", "--name-only", "-z")
        | _git_paths(root, "diff", "--cached", "--name-only", "-z")
        | _git_paths(root, "ls-files", "--others", "--exclude-standard", "-z")
    )
    ignored = _git_paths(root, "ls-files", "--others", "--ignored", "--exclude-standard", "-z")
    return paths | {path for path in ignored if _is_ds_store(path)}


def _current_fingerprint(root: Path, path: str) -> dict[str, object] | None:
    """Read a current path only after the filesystem policy accepts its components."""
    candidate = root.joinpath(*_relative(path).split("/"))
    try:
        details = candidate.lstat()
    except FileNotFoundError:
        return None
    if stat.S_ISDIR(details.st_mode):
        return {"file_kind": "directory"}
    try:
        evidence = inspect_authoritative_path(root, path)
    except FilesystemPolicyError as error:
        return {"diagnostic": str(error), "file_kind": "rejected"}
    return {
        "byte_length": evidence.byte_length,
        "file_kind": evidence.file_kind,
        "sha256": evidence.sha256,
    }


def _matches_baseline(entry: dict[str, object], current: dict[str, object]) -> bool:
    if entry.get("file_kind") != current.get("file_kind"):
        return False
    if entry.get("file_kind") != "regular_file":
        return True
    return (
        entry.get("byte_length") == current.get("byte_length")
        and entry.get("sha256") == current.get("sha256")
    )


def _classification(
    path: str,
    status: str,
    *,
    allowed: bool,
) -> dict[str, object]:
    """Return a visible classification without granting `.DS_Store` attribution."""
    if _is_ds_store(path):
        return {
            "path": path,
            "status": status,
            "attributed_to_phase": False,
            "blocking": False,
            "diagnostic": DS_STORE_DIAGNOSTIC,
        }
    if status == "preexisting_unrelated":
        return {"path": path, "status": status, "attributed_to_phase": False, "blocking": False}
    if allowed:
        return {"path": path, "status": "allowed_phase_change", "attributed_to_phase": True, "blocking": False}
    return {"path": path, "status": status, "attributed_to_phase": True, "blocking": True}


def check_boundary(root: Path, baseline_path: Path) -> BoundaryResult:
    """Classify delta against one fixed baseline without reinterpretation."""
    baseline, baseline_sha256 = load_baseline(baseline_path)
    worktree = baseline["worktree"]
    prior_entries = [*worktree["tracked_changes"], *worktree["untracked_files"]]
    prior_paths = {str(item["path"]): item for item in prior_entries}
    current_paths = capture_current_paths(root)
    current_paths.discard(baseline_path.relative_to(root).as_posix())
    classifications: list[dict[str, object]] = []
    for path in sorted(prior_paths):
        current = _current_fingerprint(root, path)
        if current is not None and _matches_baseline(prior_paths[path], current):
            classifications.append(_classification(path, "preexisting_unrelated", allowed=False))
        else:
            allowed = path_is_allowed(path, baseline["allowlist"])
            status = "deleted_out_of_boundary" if current is None else "modified_out_of_boundary"
            classifications.append(_classification(path, status, allowed=allowed))
    for path in sorted(current_paths - set(prior_paths)):
        allowed = path_is_allowed(path, baseline["allowlist"])
        classifications.append(_classification(path, "new_out_of_boundary", allowed=allowed))
    blocking = sum(bool(item["blocking"]) for item in classifications)
    return BoundaryResult(baseline_sha256, classifications, blocking)
