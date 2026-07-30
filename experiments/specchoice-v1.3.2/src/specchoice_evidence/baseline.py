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
class CommittedPathChange:
    path: str
    change_kind: str
    old_mode: str
    new_mode: str
    old_object: str
    new_object: str


@dataclass(frozen=True)
class BoundaryResult:
    baseline_sha256: str
    classifications: list[dict[str, object]]
    blocking_violations: int
    history_start_commit: str | None = None
    reviewed_revision: str | None = None
    unique_changed_path_count: int = 0


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
    if payload.get("schema_version") not in {"1", "3"}:
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


def _commit(root: Path, revision: str) -> str:
    try:
        value = subprocess.run(["git", "-C", os.fspath(root), "rev-parse", "--verify", f"{revision}^{{commit}}"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode("ascii").strip()
    except (subprocess.CalledProcessError, UnicodeDecodeError) as error:
        raise BaselineError("BOUNDARY_HISTORY_REVISION_INVALID") from error
    if len(value) != 40 or any(char not in "0123456789abcdef" for char in value):
        raise BaselineError("BOUNDARY_HISTORY_REVISION_INVALID")
    return value


def capture_committed_history(root: Path, start_commit: str, reviewed_revision: str) -> list[CommittedPathChange]:
    start, reviewed = _commit(root, start_commit), _commit(root, reviewed_revision)
    if subprocess.run(["git", "-C", os.fspath(root), "merge-base", "--is-ancestor", start, reviewed]).returncode:
        raise BaselineError("BOUNDARY_HISTORY_NOT_DESCENDANT")
    try:
        raw = subprocess.run(["git", "-C", os.fspath(root), "diff", "--raw", "-z", "--no-renames", "--diff-filter=AMDT", start, reviewed], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.split(b"\0")
    except subprocess.CalledProcessError as error:
        raise BaselineError("BOUNDARY_HISTORY_PARSE_ERROR") from error
    records: list[CommittedPathChange] = []
    for header, raw_path in zip(raw[0::2], raw[1::2]):
        if not header or not raw_path: continue
        try: fields = header.decode("ascii").split(); path = _relative(raw_path.decode("utf-8", "surrogateescape"))
        except UnicodeDecodeError as error: raise BaselineError("BOUNDARY_HISTORY_PARSE_ERROR") from error
        if len(fields) != 5 or not fields[0].startswith(":") or fields[4] not in {"A", "M", "D", "T"}: raise BaselineError("BOUNDARY_HISTORY_PARSE_ERROR")
        old_mode, new_mode, old_object, new_object = fields[0][1:], fields[1], fields[2], fields[3]
        records.append(CommittedPathChange(path, {"A":"added","M":"modified","D":"deleted","T":"type_changed"}[fields[4]], old_mode, new_mode, old_object, new_object))
    return records


def capture_live_state(root: Path) -> dict[str, list[dict[str, str]]]:
    layers = {"staged": _git_paths(root, "diff", "--cached", "--name-only", "-z"), "worktree": _git_paths(root, "diff", "--name-only", "-z"), "untracked": _git_paths(root, "ls-files", "--others", "--exclude-standard", "-z")}
    layers["untracked"] |= {path for path in _git_paths(root, "ls-files", "--others", "--ignored", "--exclude-standard", "-z") if _is_ds_store(path)}
    return {path: [{"source": source} for source, paths in layers.items() if path in paths] for path in sorted(set().union(*layers.values()))}


def merge_boundary_changes(committed: list[CommittedPathChange], live: dict[str, list[dict[str, str]]]) -> dict[str, dict[str, object]]:
    merged: dict[str, dict[str, object]] = {}
    for change in committed:
        merged[change.path] = {"path": change.path, "change_sources": ["committed_history"], "committed_change": {"change_kind": change.change_kind, "old_mode": change.old_mode, "new_mode": change.new_mode, "old_object": change.old_object, "new_object": change.new_object}, "change_kind": change.change_kind, "old_mode": change.old_mode, "new_mode": change.new_mode, "live_changes": []}
    for path, changes in live.items():
        record = merged.setdefault(path, {"path": path, "change_sources": [], "live_changes": []})
        record["live_changes"] = changes; record["change_sources"] = sorted(set([*record["change_sources"], *(item["source"] for item in changes)]))
    return merged


def capture_current_paths(root: Path) -> set[str]:
    """Collect the current delta plus visible `.DS_Store` metadata paths."""
    return set(capture_live_state(root))


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


def check_boundary(root: Path, baseline_path: Path, *, reviewed_revision: str = "HEAD") -> BoundaryResult:
    """Classify delta against one fixed baseline without reinterpretation."""
    baseline, baseline_sha256 = load_baseline(baseline_path)
    worktree = baseline["worktree"]
    prior_entries = [*worktree["tracked_changes"], *worktree["untracked_files"]]
    prior_paths = {str(item["path"]): item for item in prior_entries}
    start = baseline.get("repository", {}).get("head_commit") if isinstance(baseline.get("repository"), dict) else None
    reviewed = _commit(root, reviewed_revision) if start else None
    live = capture_live_state(root) if start else {path: [{"source": "legacy_live"}] for path in capture_current_paths(root)}
    merged = merge_boundary_changes(capture_committed_history(root, str(start), str(reviewed)) if start else [], live)
    current_paths = set(merged)
    try: current_paths.discard(baseline_path.relative_to(root).as_posix()); merged.pop(baseline_path.relative_to(root).as_posix(), None)
    except ValueError: pass
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
        record = _classification(path, "new_out_of_boundary", allowed=allowed); record.update(merged[path]); classifications.append(record)
    blocking = sum(bool(item["blocking"]) for item in classifications)
    return BoundaryResult(baseline_sha256, classifications, blocking, str(start) if start else None, reviewed, len(classifications))


def validate_boundary_restart(baseline_path: Path, previous_baseline_path: Path, allowlist_path: Path, incident_receipt_path: Path) -> dict[str, object]:
    baseline, baseline_sha = load_baseline(baseline_path); _, previous_sha = load_baseline(previous_baseline_path)
    raw_allow, raw_incident = allowlist_path.read_bytes(), incident_receipt_path.read_bytes()
    try: allow, incident = json.loads(raw_allow), json.loads(raw_incident)
    except json.JSONDecodeError as error: raise BaselineError("BOUNDARY_RESTART_INVALID") from error
    if baseline.get("schema_version") != "3" or canonical_json_bytes(allow) != raw_allow or canonical_json_bytes(incident) != raw_incident: raise BaselineError("BOUNDARY_RESTART_NOT_CANONICAL")
    restart = baseline.get("restart")
    if not isinstance(restart, dict) or restart.get("reason_code") != "D15_RESTART_COMMITTED_HISTORY_BLIND_SPOT" or restart.get("scope") != "gap_closure_only": raise BaselineError("BOUNDARY_RESTART_BINDING_MISMATCH")
    if restart.get("previous_baseline", {}).get("sha256") != previous_sha or restart.get("incident_receipt", {}).get("sha256") != sha256_bytes(raw_incident) or restart.get("v4_allowlist", {}).get("sha256") != sha256_bytes(raw_allow): raise BaselineError("BOUNDARY_RESTART_BINDING_MISMATCH")
    if baseline.get("allowlist") != allow or baseline.get("future_control_exact_files") != allow.get("exact_files") or incident.get("receipt_sha256") != sha256_bytes(canonical_json_bytes({key:value for key,value in incident.items() if key != "receipt_sha256"})): raise BaselineError("BOUNDARY_RESTART_BINDING_MISMATCH")
    return {"baseline": {"path": baseline_path.as_posix(), "sha256": baseline_sha}, "allowlist": {"path": allowlist_path.as_posix(), "sha256": sha256_bytes(raw_allow)}, "incident_receipt": {"path": incident_receipt_path.as_posix(), "sha256": sha256_bytes(raw_incident)}, "previous_baseline": {"path": previous_baseline_path.as_posix(), "sha256": previous_sha}, "reviewed_revision": restart.get("reviewed_revision"), "reason_code": restart["reason_code"], "scope": restart["scope"]}
