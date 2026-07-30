# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Fail-closed construction and offline verification for candidate bundles.

Candidate construction is deliberately distinct from publication: this module only
materializes ``bundles/candidates/<generation>`` and never creates or writes an
``accepted`` namespace.  Plan 04 must supply the offline replay proof before a
separate accepted-state transition can exist.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

from .canonical import canonical_json_bytes, require_byte_length, require_sha256, sha256_bytes
from .filesystem import FilesystemPolicyError, inspect_authoritative_path, require_relative_posix_path
from .git_proof import GitProofError, read_pinned_blob
from .source_contract import (
    SourceContractProposalError,
    require_accepted_publication_authorization,
    require_candidate_construction_authorization,
    require_source_extraction_authorization,
    validate_source_publication_decision,
)
from .verify import _bundle_artifacts, embed_verifier_artifacts


class BundleError(ValueError):
    """Stable construction or offline-verification diagnostic."""


def _mapping(value: object, code: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise BundleError(code)
    return value


def _canonical_load(path: Path, code: str) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BundleError(code) from error
    if not isinstance(payload, dict) or canonical_json_bytes(payload) != raw:
        raise BundleError(code)
    return payload


def _relative(path: object, code: str) -> str:
    if not isinstance(path, str):
        raise BundleError(code)
    try:
        return require_relative_posix_path(path).as_posix()
    except FilesystemPolicyError as error:
        raise BundleError(str(error)) from error


def _file_key(entry: Mapping[str, object]) -> tuple[str, str, str]:
    return (
        str(entry["snapshot_id"]),
        str(entry["upstream_path"]),
        str(entry["local_bundle_path"]),
    )


def _has_path_collision(paths: list[str]) -> bool:
    parsed = sorted(PurePosixPath(path) for path in paths)
    for index, path in enumerate(parsed):
        for other in parsed[index + 1 :]:
            if path == other or path in other.parents or other in path.parents:
                return True
    return False


def _approved_inventory(
    decision: object, proposal: object
) -> tuple[dict[str, object], dict[str, dict[str, object]], list[dict[str, object]]]:
    try:
        validated = validate_source_publication_decision(
            decision,
            proposal,
            proposal_path="receipts/source-contract-correction-proposal-v2.json",
            proposal_sha256=sha256_bytes(canonical_json_bytes(proposal)),
        )
        require_source_extraction_authorization(validated)
        require_candidate_construction_authorization(validated)
    except SourceContractProposalError as error:
        raise BundleError(str(error)) from error
    contract = _mapping(validated.get("approved_contract"), "CANDIDATE_CONTRACT_MISSING")
    raw_snapshots = contract.get("snapshots")
    raw_files = contract.get("consumed_files")
    if not isinstance(raw_snapshots, list) or not raw_snapshots:
        raise BundleError("SNAPSHOT_INVENTORY_EMPTY")
    if not isinstance(raw_files, list) or not raw_files:
        raise BundleError("CONSUMED_FILE_INVENTORY_EMPTY")
    snapshots: dict[str, dict[str, object]] = {}
    for raw in raw_snapshots:
        snapshot = dict(_mapping(raw, "SNAPSHOT_INVENTORY_INVALID"))
        identifier = snapshot.get("snapshot_id")
        if not isinstance(identifier, str) or not identifier or identifier in snapshots:
            raise BundleError("SNAPSHOT_INVENTORY_DUPLICATE")
        snapshots[identifier] = snapshot
    files: list[dict[str, object]] = []
    identities: set[tuple[str, str]] = set()
    local_paths: list[str] = []
    for raw in raw_files:
        entry = dict(_mapping(raw, "CONSUMED_FILE_INVENTORY_INVALID"))
        snapshot_id = entry.get("snapshot_id")
        if not isinstance(snapshot_id, str) or snapshot_id not in snapshots:
            raise BundleError("CONSUMED_FILE_SNAPSHOT_UNKNOWN")
        upstream = _relative(entry.get("upstream_path"), "UPSTREAM_PATH_INVALID")
        local = _relative(entry.get("local_bundle_path"), "LOCAL_PATH_INVALID")
        role = entry.get("experimental_role")
        if not isinstance(role, str) or not role:
            raise BundleError("CONSUMED_FILE_ROLE_MISSING")
        try:
            entry["raw_byte_length"] = require_byte_length(entry.get("raw_byte_length"))
            entry["raw_sha256"] = require_sha256(entry.get("raw_sha256"))
        except ValueError as error:
            raise BundleError("RAW_DIGEST_OR_LENGTH_INVALID") from error
        if entry.get("raw_authoritative") is not True or not isinstance(entry.get("declared_transforms"), list):
            raise BundleError("RAW_AUTHORITY_OR_TRANSFORM_INVALID")
        identity = (snapshot_id, upstream)
        if identity in identities:
            raise BundleError("CONSUMED_FILE_DUPLICATE")
        identities.add(identity)
        entry["upstream_path"] = upstream
        entry["local_bundle_path"] = local
        local_paths.append(local)
        files.append(entry)
    if _has_path_collision(local_paths):
        raise BundleError("LOCAL_PATH_COLLISION")
    return validated, snapshots, sorted(files, key=_file_key)


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


def _core_and_artifacts(
    snapshots: Mapping[str, Mapping[str, object]], files: list[dict[str, object]], root: Path, git_repository: Path
) -> tuple[dict[str, object], list[dict[str, object]]]:
    artifacts: list[dict[str, object]] = []
    grouped: dict[str, list[dict[str, object]]] = {identifier: [] for identifier in snapshots}
    for entry in files:
        snapshot = snapshots[entry["snapshot_id"]]
        pinned = snapshot.get("pinned_commit_sha")
        if not isinstance(pinned, str):
            raise BundleError("PINNED_COMMIT_INVALID")
        try:
            raw = read_pinned_blob(git_repository, pinned, entry["upstream_path"])
        except GitProofError as error:
            raise BundleError(str(error)) from error
        if len(raw) != entry["raw_byte_length"]:
            raise BundleError("RAW_BYTE_LENGTH_MISMATCH")
        if sha256_bytes(raw) != entry["raw_sha256"]:
            raise BundleError("RAW_SHA256_MISMATCH")
        local = str(entry["local_bundle_path"])
        _write_exact(root / local, raw)
        evidence = inspect_authoritative_path(root, local)
        if evidence.file_kind != "regular_file" or evidence.byte_length != len(raw) or evidence.sha256 != entry["raw_sha256"]:
            raise BundleError("STAGED_RAW_CUSTODY_MISMATCH")
        consumed = {
            "declared_transforms": entry["declared_transforms"],
            "derived_artifacts": [],
            "experimental_role": entry["experimental_role"],
            "local_bundle_path": local,
            "raw_authoritative": True,
            "raw_byte_length": len(raw),
            "raw_sha256": entry["raw_sha256"],
            "upstream_path": entry["upstream_path"],
        }
        grouped[str(entry["snapshot_id"])].append(consumed)
        artifacts.append({
            "byte_length": len(raw), "kind": "raw", "local_bundle_path": local,
            "raw_sha256": entry["raw_sha256"], "relationship": "authoritative_raw",
        })
    core_snapshots = []
    for snapshot_id in sorted(snapshots):
        snapshot = snapshots[snapshot_id]
        core_snapshots.append({
            "consumed_files": sorted(grouped[snapshot_id], key=lambda item: (item["upstream_path"], item["local_bundle_path"])),
            "pinned_commit_sha": snapshot["pinned_commit_sha"],
            "pinned_tree_sha": snapshot["pinned_tree_sha"],
            "pull_request": snapshot["pull_request"], "repository": snapshot["repository"],
            "snapshot_id": snapshot_id,
        })
    return {"schema_version": "1", "snapshots": core_snapshots}, sorted(artifacts, key=lambda item: item["local_bundle_path"])


def _root_digest(manifest_sha256: str, artifacts: list[dict[str, object]]) -> str:
    return sha256_bytes(canonical_json_bytes({
        "artifacts": artifacts, "manifest_sha256": manifest_sha256, "root_schema_version": "1"
    }))


def _snapshot_manifest(core: dict[str, object], generation: str, manifest_sha256: str, root_sha256: str) -> dict[str, object]:
    snapshots: list[dict[str, object]] = []
    for snapshot in core["snapshots"]:
        assert isinstance(snapshot, dict)
        snapshots.append({
            **snapshot,
            "generation": generation,
            "manifest_sha256": manifest_sha256,
            "root_sha256": root_sha256,
        })
    manifest = {
        "content_manifest_core": core, "generation": generation,
        "manifest_sha256": manifest_sha256, "root_sha256": root_sha256,
        "schema_version": "1", "snapshots": snapshots, "status": "candidate",
        "downstream_eligible": False, "accepted_publication_authorized": False,
        "offline_replay_proven": False,
    }
    manifest["snapshot_manifest_sha256"] = sha256_bytes(canonical_json_bytes(manifest))
    return manifest


def construct_candidate(decision: object, proposal: object, git_repository: Path, candidates_root: Path) -> dict[str, object]:
    """Extract exact approved blobs into a deterministic, explicitly non-accepted candidate."""
    validated, snapshots, files = _approved_inventory(decision, proposal)
    del validated
    contract = _mapping(_mapping(decision, "INVALID_SOURCE_DECISION").get("approved_contract"), "CANDIDATE_CONTRACT_MISSING")
    generation = contract.get("requested_generation_label")
    if not isinstance(generation, str) or not generation or "/" in generation or "\\" in generation:
        raise BundleError("CANDIDATE_GENERATION_INVALID")
    target = candidates_root / generation
    if target.exists() or target.is_symlink():
        raise BundleError("CANDIDATE_TARGET_EXISTS")
    candidates_root.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{generation}.staging-", dir=candidates_root))
    try:
        core, artifacts = _core_and_artifacts(snapshots, files, temporary, git_repository)
        core["bundle_artifacts"] = embed_verifier_artifacts(temporary)
        artifacts.extend(_bundle_artifacts(core, temporary))
        core_bytes = canonical_json_bytes(core)
        manifest_sha256 = sha256_bytes(core_bytes)
        root_sha256 = _root_digest(manifest_sha256, artifacts)
        _write_exact(temporary / "content-manifest-core.json", core_bytes)
        final = _snapshot_manifest(core, generation, manifest_sha256, root_sha256)
        _write_exact(temporary / "snapshot-manifest.json", canonical_json_bytes(final))
        verify_candidate(temporary)
        _sync_directory(temporary)
        _sync_directory(candidates_root)
        if target.exists() or target.is_symlink():
            raise BundleError("CANDIDATE_TARGET_EXISTS")
        os.replace(temporary, target)
        _sync_directory(candidates_root)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
    return {"generation": generation, "manifest_sha256": manifest_sha256, "root_sha256": root_sha256, "status": "candidate"}


def verify_candidate(candidate: Path) -> dict[str, object]:
    """Offline recomputation of raw custody, core/root, and final non-cyclic binding."""
    core_path = candidate / "content-manifest-core.json"
    final_path = candidate / "snapshot-manifest.json"
    core = _canonical_load(core_path, "CONTENT_MANIFEST_CORE_INVALID")
    final = _canonical_load(final_path, "SNAPSHOT_MANIFEST_INVALID")
    if final.get("status") != "candidate" or final.get("downstream_eligible") is not False or final.get("accepted_publication_authorized") is not False or final.get("offline_replay_proven") is not False:
        raise BundleError("CANDIDATE_ACCEPTED_STATE_FORBIDDEN")
    actual_manifest = sha256_bytes(core_path.read_bytes())
    if final.get("manifest_sha256") != actual_manifest:
        raise BundleError("MANIFEST_SHA256_MISMATCH")
    without_self = dict(final)
    supplied_self = without_self.pop("snapshot_manifest_sha256", None)
    if supplied_self != sha256_bytes(canonical_json_bytes(without_self)):
        raise BundleError("SNAPSHOT_MANIFEST_SELF_DIGEST_MISMATCH")
    if final.get("content_manifest_core") != core:
        raise BundleError("SNAPSHOT_CORE_PROJECTION_MISMATCH")
    generation, root_sha256 = final.get("generation"), final.get("root_sha256")
    if not isinstance(generation, str) or not isinstance(root_sha256, str):
        raise BundleError("SNAPSHOT_BINDING_MISSING")
    artifacts: list[dict[str, object]] = []
    snapshots = core.get("snapshots")
    if not isinstance(snapshots, list) or not snapshots:
        raise BundleError("SNAPSHOT_INVENTORY_EMPTY")
    for core_snapshot, final_snapshot in zip(snapshots, final.get("snapshots", []), strict=True):
        if not isinstance(core_snapshot, dict) or not isinstance(final_snapshot, dict):
            raise BundleError("SNAPSHOT_MANIFEST_INVALID")
        if final_snapshot.get("generation") != generation or final_snapshot.get("root_sha256") != root_sha256 or final_snapshot.get("manifest_sha256") != actual_manifest:
            raise BundleError("SNAPSHOT_BINDING_MISMATCH")
        if {key: value for key, value in final_snapshot.items() if key not in {"generation", "root_sha256", "manifest_sha256"}} != core_snapshot:
            raise BundleError("SNAPSHOT_CORE_PROJECTION_MISMATCH")
        for file in core_snapshot.get("consumed_files", []):
            if not isinstance(file, dict):
                raise BundleError("CONSUMED_FILE_INVENTORY_INVALID")
            local = _relative(file.get("local_bundle_path"), "LOCAL_PATH_INVALID")
            try:
                evidence = inspect_authoritative_path(candidate, local)
            except FilesystemPolicyError as error:
                raise BundleError(str(error)) from error
            if evidence.file_kind != "regular_file" or evidence.byte_length != file.get("raw_byte_length") or evidence.sha256 != file.get("raw_sha256"):
                raise BundleError("STAGED_RAW_CUSTODY_MISMATCH")
            artifacts.append({"byte_length": evidence.byte_length, "kind": "raw", "local_bundle_path": local, "raw_sha256": evidence.sha256, "relationship": "authoritative_raw"})
    if "bundle_artifacts" in core:
        try:
            artifacts.extend(_bundle_artifacts(core, candidate))
        except Exception as error:
            raise BundleError(str(error)) from error
    recomputed = _root_digest(actual_manifest, sorted(artifacts, key=lambda item: item["local_bundle_path"]))
    if recomputed != root_sha256:
        raise BundleError("ROOT_SHA256_MISMATCH")
    return {"generation": generation, "manifest_sha256": actual_manifest, "root_sha256": root_sha256, "status": "candidate"}


def publish_accepted(decision: object) -> None:
    """Deliberately closed publication boundary until Plan 04 proves offline replay."""
    try:
        require_accepted_publication_authorization(_mapping(decision, "INVALID_SOURCE_DECISION"))
    except SourceContractProposalError as error:
        raise BundleError(str(error)) from error
    raise BundleError("OFFLINE_REPLAY_PROOF_REQUIRED")
