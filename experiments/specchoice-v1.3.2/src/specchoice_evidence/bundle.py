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
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

from .canonical import canonical_json_bytes, require_byte_length, require_sha256, sha256_bytes
from .filesystem import FilesystemPolicyError, inspect_authoritative_path, require_relative_posix_path
from .git_proof import GitProofError, read_pinned_blob
from .source_contract import (
    FixtureRegistryError,
    SourceContractProposalError,
    require_accepted_publication_authorization,
    require_candidate_construction_authorization,
    require_fixture_closure_local_acceptance_authorization,
    require_local_accepted_generation_authorization,
    require_source_extraction_authorization,
    validate_source_publication_decision,
    validate_fixture_registry,
    validate_fixture_closure_decision,
    validate_fixture_closure_proposal,
    verify_fixture_registry_git,
)
from .verify import (
    _bundle_artifacts,
    _raw_artifacts,
    embed_verifier_artifacts,
    verify_accepted_bundle,
    verify_candidate_bundle,
)


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
        decision_mapping = _mapping(decision, "INVALID_SOURCE_DECISION")
        proposal_binding = _mapping(decision_mapping.get("proposal"), "SOURCE_DECISION_PROPOSAL_MISSING")
        proposal_path = _relative(proposal_binding.get("path"), "SOURCE_DECISION_PROPOSAL_BINDING_INVALID")
        validated = validate_source_publication_decision(
            decision,
            proposal,
            proposal_path=proposal_path,
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
        "artifacts": sorted(artifacts, key=lambda item: str(item["local_bundle_path"])),
        "manifest_sha256": manifest_sha256,
        "root_schema_version": "1",
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
        "external_publication_authorized": False,
        "offline_replay_proven": False,
    }
    manifest["snapshot_manifest_sha256"] = sha256_bytes(canonical_json_bytes(manifest))
    return manifest


def construct_candidate(
    decision: object,
    proposal: object,
    git_repository: Path,
    candidates_root: Path,
    *,
    fixture_registry_path: Path | None = None,
) -> dict[str, object]:
    """Extract exact approved blobs into a deterministic, explicitly non-accepted candidate."""
    validated, snapshots, files = _approved_inventory(decision, proposal)
    del validated
    registry_bytes: bytes | None = None
    if fixture_registry_path is not None:
        try:
            registry_bytes = fixture_registry_path.read_bytes()
            registry = json.loads(registry_bytes.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise BundleError("FIXTURE_REGISTRY_INVALID") from error
        if canonical_json_bytes(registry) != registry_bytes:
            raise BundleError("FIXTURE_REGISTRY_NOT_CANONICAL")
        try:
            normalized = validate_fixture_registry(registry)
            verify_fixture_registry_git(registry, git_repository)
        except FixtureRegistryError as error:
            raise BundleError(str(error)) from error
        registry_files = {
            (file["upstream_path"], file["local_bundle_path"], file["raw_byte_length"], file["raw_sha256"], file["role"])
            for fixture in normalized["fixtures"]
            for file in fixture["files"]
            if isinstance(fixture, dict) and isinstance(file, dict)
        }
        proposal_files = {
            (entry["upstream_path"], entry["local_bundle_path"], entry["raw_byte_length"], entry["raw_sha256"], entry["experimental_role"])
            for entry in files
        }
        if registry_files != proposal_files:
            raise BundleError("FIXTURE_REGISTRY_PROPOSAL_MISMATCH")
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
        if registry_bytes is not None:
            _write_exact(temporary / "fixture-registry-pr2164-v1.json", registry_bytes)
            core["fixture_closure"] = {
                "fixture_count": 11,
                "raw_file_count": 28,
                "registry_path": "fixture-registry-pr2164-v1.json",
                "registry_sha256": sha256_bytes(registry_bytes),
            }
            fixture_registry_artifact = {
                "byte_length": len(registry_bytes),
                "kind": "fixture_registry",
                "local_bundle_path": "fixture-registry-pr2164-v1.json",
                "relationship": "fixture_registry",
                "sha256": sha256_bytes(registry_bytes),
            }
        else:
            fixture_registry_artifact = None
        core["bundle_artifacts"] = embed_verifier_artifacts(temporary)
        if fixture_registry_artifact is not None:
            core["bundle_artifacts"].append(fixture_registry_artifact)
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


def construct_fixture_closure_candidate(
    decision: object,
    proposal: object,
    fixture_registry_path: Path,
    git_repository: Path,
    candidates_root: Path,
) -> dict[str, object]:
    """Build the v3 finite-set candidate from a compact digest-bound proposal."""
    try:
        proposal_raw = canonical_json_bytes(proposal)
        validate_fixture_closure_decision(
            decision,
            proposal,
            proposal_path="receipts/source-contract-proposal-v3-pr2164-fixture-closure-v2.json",
            proposal_sha256=sha256_bytes(proposal_raw),
        )
        bindings = validate_fixture_closure_proposal(proposal)
        registry_raw = fixture_registry_path.read_bytes()
        registry = json.loads(registry_raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, SourceContractProposalError) as error:
        raise BundleError("FIXTURE_CLOSURE_PROPOSAL_INVALID") from error
    if canonical_json_bytes(registry) != registry_raw:
        raise BundleError("FIXTURE_REGISTRY_NOT_CANONICAL")
    registry_binding = bindings["fixture_registry"]
    source_binding = bindings["base_source_snapshots"]
    assert isinstance(registry_binding, dict) and isinstance(source_binding, dict)
    if sha256_bytes(registry_raw) != registry_binding["sha256"]:
        raise BundleError("FIXTURE_REGISTRY_BINDING_MISMATCH")
    source_snapshots = fixture_registry_path.with_name("source_snapshots.json")
    try:
        source_raw = source_snapshots.read_bytes()
        source_payload = json.loads(source_raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BundleError("SOURCE_SNAPSHOTS_BINDING_MISMATCH") from error
    if canonical_json_bytes(source_payload) != source_raw or sha256_bytes(source_raw) != source_binding["sha256"]:
        raise BundleError("SOURCE_SNAPSHOTS_BINDING_MISMATCH")
    try:
        normalized = validate_fixture_registry(registry)
        verify_fixture_registry_git(registry, git_repository)
    except FixtureRegistryError as error:
        raise BundleError(str(error)) from error
    consumed_files = []
    for fixture in normalized["fixtures"]:
        assert isinstance(fixture, dict)
        for file in fixture["files"]:
            assert isinstance(file, dict)
            consumed_files.append({
                "declared_transforms": [],
                "experimental_role": file["role"],
                "local_bundle_path": file["local_bundle_path"],
                "raw_authoritative": True,
                "raw_byte_length": file["raw_byte_length"],
                "raw_sha256": file["raw_sha256"],
                "snapshot_id": "evaluation_fixtures",
                "upstream_path": file["upstream_path"],
                "why_consumed": "Frozen PR #2164 finite-set fixture custody input.",
            })
    generic_proposal = {
        "base_frozen_contract": {"path": "config/source_snapshots.json", "sha256": source_binding["sha256"]},
        "consumed_files": sorted(consumed_files, key=lambda item: (item["snapshot_id"], item["upstream_path"], item["local_bundle_path"])),
        "historical_rejected_receipt": {"path": "bundles/rejected/pr-2192-current-head/attempt-receipt.json", "sha256": "0" * 64},
        "proposed_contract_version": "3",
        "requested_generation_label": proposal["generation"],
        "schema_version": "1",
        "snapshots": [{
            "canonical_pr_head_sha": "22e84458c87a7ccf4c07034de1eb6d0bf9764144",
            "change_control": "versioned_correction",
            "pinned_commit_sha": "22e84458c87a7ccf4c07034de1eb6d0bf9764144",
            "pinned_tree_sha": "af003b427c66bd8ac9803a91b3bf363a1b1304d9",
            "pull_request": 2164,
            "reachability": "equal_head",
            "repository": "riscv/riscv-unified-db",
            "snapshot_id": "evaluation_fixtures",
        }],
        "status": "pending_reviewer_approval",
    }
    generic_decision = {
        "approval_scope": "candidate_construction_only",
        "approved_contract": {
            key: generic_proposal[key]
            for key in ("base_frozen_contract", "consumed_files", "historical_rejected_receipt", "proposed_contract_version", "requested_generation_label", "snapshots")
        },
        "authorization": {
            "accepted_publication_authorized": False,
            "candidate_construction_authorized": True,
            "source_extraction_authorized": True,
        },
        "proposal": {
            "path": "receipts/source-contract-proposal-v3-pr2164-fixture-closure-v2.json",
            "sha256": sha256_bytes(canonical_json_bytes(generic_proposal)),
        },
        "reviewer": {"approval_token": "authorize-candidate-construction-only"},
        "schema_version": "1",
        "state": "candidate_construction_authorized",
    }
    return construct_candidate(
        generic_decision,
        generic_proposal,
        git_repository,
        candidates_root,
        fixture_registry_path=fixture_registry_path,
    )


def _replace_exact(path: Path, content: bytes) -> None:
    """Replace a generated manifest atomically after recomputing all bound fields."""
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _run_embedded_verifier(bundle: Path) -> None:
    completed = subprocess.run(
        [sys.executable, "verify_bundle.py"], cwd=bundle, check=False, capture_output=True, text=True
    )
    if completed.returncode != 0:
        raise BundleError("EMBEDDED_VERIFIER_FAILED")


def construct_verifier_rooted_candidate(
    source_candidate: Path, candidates_root: Path, generation: str
) -> dict[str, object]:
    """Derive a fresh non-accepted identity with the verifier bytes in its logical root.

    The historical source candidate is recomputed before copying.  This keeps its exact
    seven approved raw blobs intact and never creates, renames, or writes an accepted path.
    """
    if not generation or "/" in generation or "\\" in generation:
        raise BundleError("CANDIDATE_GENERATION_INVALID")
    source_identity = verify_candidate(source_candidate)
    if source_identity.get("status") != "candidate":
        raise BundleError("SOURCE_CANDIDATE_NOT_ELIGIBLE")
    target = candidates_root / generation
    if target.exists() or target.is_symlink():
        raise BundleError("CANDIDATE_TARGET_EXISTS")
    candidates_root.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{generation}.staging-", dir=candidates_root))
    try:
        shutil.rmtree(temporary)
        shutil.copytree(source_candidate, temporary)
        (temporary / "content-manifest-core.json").unlink()
        (temporary / "snapshot-manifest.json").unlink()
        core = _canonical_load(source_candidate / "content-manifest-core.json", "CONTENT_MANIFEST_CORE_INVALID")
        if "bundle_artifacts" in core:
            raise BundleError("SOURCE_CANDIDATE_ALREADY_ROOTED")
        core["bundle_artifacts"] = embed_verifier_artifacts(temporary)
        core_bytes = canonical_json_bytes(core)
        manifest_sha256 = sha256_bytes(core_bytes)
        artifacts = _raw_artifacts(core, temporary) + _bundle_artifacts(core, temporary)
        root_sha256 = _root_digest(manifest_sha256, artifacts)
        _write_exact(temporary / "content-manifest-core.json", core_bytes)
        final = _snapshot_manifest(core, generation, manifest_sha256, root_sha256)
        _write_exact(temporary / "snapshot-manifest.json", canonical_json_bytes(final))
        verify_candidate_bundle(temporary)
        _run_embedded_verifier(temporary)
        final["offline_replay_proven"] = True
        final["snapshot_manifest_sha256"] = sha256_bytes(canonical_json_bytes({
            key: value for key, value in final.items() if key != "snapshot_manifest_sha256"
        }))
        _replace_exact(temporary / "snapshot-manifest.json", canonical_json_bytes(final))
        verify_candidate_bundle(temporary)
        _run_embedded_verifier(temporary)
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
    return {
        "generation": generation,
        "manifest_sha256": manifest_sha256,
        "root_sha256": root_sha256,
        "status": "candidate",
    }


def verify_candidate(candidate: Path) -> dict[str, object]:
    """Offline recomputation of raw custody, core/root, and final non-cyclic binding."""
    core_path = candidate / "content-manifest-core.json"
    final_path = candidate / "snapshot-manifest.json"
    core = _canonical_load(core_path, "CONTENT_MANIFEST_CORE_INVALID")
    final = _canonical_load(final_path, "SNAPSHOT_MANIFEST_INVALID")
    if final.get("status") != "candidate" or final.get("downstream_eligible") is not False or final.get("accepted_publication_authorized") is not False or final.get("external_publication_authorized", False) is not False or not isinstance(final.get("offline_replay_proven"), bool):
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
            except OSError as error:
                raise BundleError("STAGED_RAW_CUSTODY_MISMATCH") from error
            if evidence.file_kind != "regular_file" or evidence.byte_length != file.get("raw_byte_length") or evidence.sha256 != file.get("raw_sha256"):
                raise BundleError("STAGED_RAW_CUSTODY_MISMATCH")
            artifacts.append({"byte_length": evidence.byte_length, "kind": "raw", "local_bundle_path": local, "raw_sha256": evidence.sha256, "relationship": "authoritative_raw"})
    if "bundle_artifacts" in core:
        try:
            artifacts.extend(_bundle_artifacts(core, candidate))
        except Exception as error:
            raise BundleError(str(error)) from error
    expected = {"content-manifest-core.json", "snapshot-manifest.json"}
    expected.update(str(item["local_bundle_path"]) for item in artifacts)
    actual: set[str] = set()
    for directory, names, entries in os.walk(candidate, topdown=True, followlinks=False):
        current = Path(directory)
        for name in [*names, *entries]:
            relative = (current / name).relative_to(candidate).as_posix()
            if "__pycache__" in relative.split("/") or relative.endswith(".pyc"):
                continue
            try:
                evidence = inspect_authoritative_path(candidate, relative)
            except FilesystemPolicyError as error:
                raise BundleError(str(error)) from error
            if evidence.file_kind == "regular_file":
                actual.add(relative)
    if expected - actual:
        raise BundleError("BUNDLE_MISSING_FILE")
    if actual - expected:
        raise BundleError("BUNDLE_EXTRA_FILE")
    recomputed = _root_digest(actual_manifest, sorted(artifacts, key=lambda item: item["local_bundle_path"]))
    if recomputed != root_sha256:
        raise BundleError("ROOT_SHA256_MISMATCH")
    # Keep candidate and embedded accepted verification on the same finite-set
    # closure rule.  The embedded verifier is copied into accepted generations.
    try:
        verify_candidate_bundle(candidate)
    except BundleVerificationError as error:
        raise BundleError(str(error)) from error
    return {"generation": generation, "manifest_sha256": actual_manifest, "root_sha256": root_sha256, "status": "candidate"}


def publish_accepted(decision: object) -> None:
    """Deliberately closed publication boundary until Plan 04 proves offline replay."""
    try:
        require_accepted_publication_authorization(_mapping(decision, "INVALID_SOURCE_DECISION"))
    except SourceContractProposalError as error:
        raise BundleError(str(error)) from error
    raise BundleError("OFFLINE_REPLAY_PROOF_REQUIRED")


def accept_local_candidate(
    decision: object, candidate: Path, accepted_root: Path, *, allow_historical: bool = False
) -> dict[str, object]:
    """Atomically pin one already-rooted candidate for local MVP use only.

    The copied directory retains the candidate's bytes and its non-external manifest state.
    Local acceptability is therefore represented only by the separately hash-bound decision;
    no external publication state is synthesized or implied.
    """
    identity = verify_candidate(candidate)
    final = _canonical_load(candidate / "snapshot-manifest.json", "SNAPSHOT_MANIFEST_INVALID")
    snapshot_sha256 = final.get("snapshot_manifest_sha256")
    if not isinstance(snapshot_sha256, str):
        raise BundleError("SNAPSHOT_MANIFEST_SELF_DIGEST_MISMATCH")
    try:
        require_local_accepted_generation_authorization(
            _mapping(decision, "INVALID_LOCAL_ACCEPTANCE_DECISION"),
            identity,
            snapshot_sha256,
            allow_historical=allow_historical,
        )
    except SourceContractProposalError as error:
        raise BundleError(str(error)) from error
    generation = identity["generation"]
    assert isinstance(generation, str)
    target = accepted_root / generation
    if target.exists() or target.is_symlink():
        raise BundleError("LOCAL_ACCEPTED_TARGET_EXISTS")
    accepted_root.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{generation}.staging-", dir=accepted_root))
    try:
        shutil.rmtree(temporary)
        shutil.copytree(candidate, temporary)
        if (temporary / "content-manifest-core.json").read_bytes() != (
            candidate / "content-manifest-core.json"
        ).read_bytes() or (temporary / "snapshot-manifest.json").read_bytes() != (
            candidate / "snapshot-manifest.json"
        ).read_bytes():
            raise BundleError("LOCAL_ACCEPTED_COPY_IDENTITY_MISMATCH")
        if verify_candidate(temporary) != identity:
            raise BundleError("LOCAL_ACCEPTED_COPY_IDENTITY_MISMATCH")
        _run_embedded_verifier(temporary)
        _sync_directory(temporary)
        _sync_directory(accepted_root)
        if target.exists() or target.is_symlink():
            raise BundleError("LOCAL_ACCEPTED_TARGET_EXISTS")
        os.replace(temporary, target)
        _sync_directory(accepted_root)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
    return identity


def accept_fixture_closure_candidate(
    candidate: Path, accepted_root: Path, decision: object, v7_basis: Mapping[str, object]
) -> dict[str, object]:
    """Promote only the complete v3 candidate into a fresh local accepted tree.

    This is a local lifecycle transition, not an external publication operation.  The
    candidate is verified before copying and never changed.  The accepted tree gets a
    freshly rooted core/manifest because its embedded verifier and lifecycle state are
    part of its own content address.
    """
    identity = verify_candidate(candidate)
    generation = identity.get("generation")
    if generation != "source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2":
        raise BundleError("FIXTURE_CLOSURE_ACCEPTANCE_GENERATION_INVALID")
    final_candidate = _canonical_load(candidate / "snapshot-manifest.json", "SNAPSHOT_MANIFEST_INVALID")
    snapshot_sha256 = final_candidate.get("snapshot_manifest_sha256")
    if not isinstance(snapshot_sha256, str):
        raise BundleError("SNAPSHOT_MANIFEST_SELF_DIGEST_MISMATCH")
    registry = candidate / "fixture-registry-pr2164-v1.json"
    try:
        registry_sha256 = sha256_bytes(registry.read_bytes())
        require_fixture_closure_local_acceptance_authorization(
            decision, identity, snapshot_sha256, registry_sha256, v7_basis
        )
    except (OSError, SourceContractProposalError) as error:
        raise BundleError(str(error)) from error
    target = accepted_root / generation
    if target.exists() or target.is_symlink():
        raise BundleError("LOCAL_ACCEPTED_TARGET_EXISTS")
    accepted_root.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{generation}.staging-", dir=accepted_root))
    try:
        shutil.rmtree(temporary)
        shutil.copytree(candidate, temporary)
        (temporary / "content-manifest-core.json").unlink()
        (temporary / "snapshot-manifest.json").unlink()
        core = _canonical_load(candidate / "content-manifest-core.json", "CONTENT_MANIFEST_CORE_INVALID")
        closure = core.get("fixture_closure")
        if not isinstance(closure, dict) or closure.get("fixture_count") != 11 or closure.get("raw_file_count") != 28:
            raise BundleError("FIXTURE_CLOSURE_ACCEPTANCE_INCOMPLETE")
        registry_artifacts = [
            artifact for artifact in core.get("bundle_artifacts", [])
            if isinstance(artifact, dict) and artifact.get("kind") == "fixture_registry"
        ]
        if len(registry_artifacts) != 1:
            raise BundleError("FIXTURE_CLOSURE_REGISTRY_ARTIFACT_MISSING")
        core["bundle_artifacts"] = embed_verifier_artifacts(temporary) + registry_artifacts
        core_bytes = canonical_json_bytes(core)
        manifest_sha256 = sha256_bytes(core_bytes)
        _write_exact(temporary / "content-manifest-core.json", core_bytes)
        artifacts = _raw_artifacts(core, temporary) + _bundle_artifacts(core, temporary)
        root_sha256 = _root_digest(manifest_sha256, artifacts)
        snapshots = [
            {**snapshot, "generation": generation, "manifest_sha256": manifest_sha256, "root_sha256": root_sha256}
            for snapshot in core["snapshots"]
        ]
        final: dict[str, object] = {
            "accepted_publication_authorized": False,
            "content_manifest_core": core,
            "downstream_eligible": True,
            "external_publication_authorized": False,
            "generation": generation,
            "manifest_sha256": manifest_sha256,
            "offline_replay_proven": True,
            "root_sha256": root_sha256,
            "schema_version": "1",
            "snapshots": snapshots,
            "status": "accepted",
        }
        final["snapshot_manifest_sha256"] = sha256_bytes(canonical_json_bytes(final))
        _write_exact(temporary / "snapshot-manifest.json", canonical_json_bytes(final))
        # The embedded verifier re-parses the frozen registry and proves its
        # bidirectional equality with the raw manifest inventory before acceptance.
        verified = verify_accepted_bundle(temporary)
        _run_embedded_verifier(temporary)
        _sync_directory(temporary)
        _sync_directory(accepted_root)
        if target.exists() or target.is_symlink():
            raise BundleError("LOCAL_ACCEPTED_TARGET_EXISTS")
        os.replace(temporary, target)
        _sync_directory(accepted_root)
        return verified
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
