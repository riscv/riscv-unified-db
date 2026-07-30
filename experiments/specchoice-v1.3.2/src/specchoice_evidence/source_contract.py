# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Validation for reviewer-pending versioned source-contract proposals.

The proposal is deliberately not a source-publication decision.  It captures
the exact evidence a reviewer must approve before any accepted bundle can be
constructed, while keeping the frozen contract and its rejected receipt intact.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from collections.abc import Mapping
from pathlib import Path
from .canonical import require_byte_length, require_sha256
from .filesystem import FilesystemPolicyError, require_relative_posix_path
from .git_proof import GitProofError


class SourceContractProposalError(ValueError):
    """A stable diagnostic for incomplete or unverifiable correction proposals."""


def _require_string(mapping: Mapping[str, object], field: str) -> str:
    value = mapping.get(field)
    if not isinstance(value, str) or not value:
        raise SourceContractProposalError(f"PROPOSAL_{field.upper()}_MISSING")
    return value


def _require_mapping(value: object, code: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise SourceContractProposalError(code)
    return value


def _normalized_path(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise SourceContractProposalError(f"PROPOSAL_{field.upper()}_MISSING")
    try:
        return require_relative_posix_path(value).as_posix()
    except FilesystemPolicyError as error:
        raise SourceContractProposalError(str(error)) from error


def _require_git_sha(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 40:
        raise SourceContractProposalError(f"PROPOSAL_{field.upper()}_INVALID")
    try:
        int(value, 16)
    except ValueError as error:
        raise SourceContractProposalError(f"PROPOSAL_{field.upper()}_INVALID") from error
    return value


def _validate_transforms(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise SourceContractProposalError("PROPOSAL_DECLARED_TRANSFORMS_MISSING")
    normalized: list[dict[str, object]] = []
    for transform in value:
        mapping = _require_mapping(transform, "PROPOSAL_TRANSFORM_INVALID")
        parameters = mapping.get("parameters")
        if not isinstance(parameters, Mapping):
            raise SourceContractProposalError("PROPOSAL_TRANSFORM_PARAMETERS_MISSING")
        normalized.append(
            {
                "name": _require_string(mapping, "name"),
                "parameters": dict(parameters),
                "proposed_derived_path": _normalized_path(
                    mapping.get("proposed_derived_path"), "proposed_derived_path"
                ),
                "version": _require_string(mapping, "version"),
            }
        )
    return normalized


def validate_source_contract_proposal(proposal: object) -> dict[str, object]:
    """Validate complete reviewer-pending source custody fields without publishing."""
    payload = _require_mapping(proposal, "INVALID_SOURCE_CONTRACT_PROPOSAL")
    if payload.get("schema_version") != "1":
        raise SourceContractProposalError("UNSUPPORTED_SOURCE_CONTRACT_PROPOSAL_SCHEMA")
    if payload.get("status") != "pending_reviewer_approval":
        raise SourceContractProposalError("SOURCE_CONTRACT_PROPOSAL_NOT_PENDING")
    if payload.get("proposed_contract_version") != "2":
        raise SourceContractProposalError("INVALID_PROPOSED_CONTRACT_VERSION")
    _require_string(payload, "requested_generation_label")
    base_contract = _require_mapping(payload.get("base_frozen_contract"), "BASE_CONTRACT_MISSING")
    _normalized_path(base_contract.get("path"), "base_contract_path")
    try:
        require_sha256(base_contract.get("sha256"))
    except ValueError as error:
        raise SourceContractProposalError("BASE_CONTRACT_SHA256_INVALID") from error
    rejected = _require_mapping(payload.get("historical_rejected_receipt"), "REJECTED_RECEIPT_MISSING")
    _normalized_path(rejected.get("path"), "historical_rejected_receipt_path")
    try:
        require_sha256(rejected.get("sha256"))
    except ValueError as error:
        raise SourceContractProposalError("REJECTED_RECEIPT_SHA256_INVALID") from error

    raw_snapshots = payload.get("snapshots")
    if not isinstance(raw_snapshots, list) or not raw_snapshots:
        raise SourceContractProposalError("PROPOSAL_SNAPSHOTS_EMPTY")
    snapshots: dict[str, dict[str, object]] = {}
    for raw_snapshot in raw_snapshots:
        snapshot = _require_mapping(raw_snapshot, "PROPOSAL_SNAPSHOT_INVALID")
        snapshot_id = _require_string(snapshot, "snapshot_id")
        if snapshot_id in snapshots:
            raise SourceContractProposalError("PROPOSAL_SNAPSHOT_DUPLICATE")
        pull_request = snapshot.get("pull_request")
        if isinstance(pull_request, bool) or not isinstance(pull_request, int) or pull_request < 1:
            raise SourceContractProposalError("PROPOSAL_PULL_REQUEST_INVALID")
        for field in ("pinned_commit_sha", "pinned_tree_sha", "canonical_pr_head_sha"):
            _require_git_sha(snapshot.get(field), field)
        reachability = snapshot.get("reachability")
        if reachability not in {"equal_head", "reachable_ancestor"}:
            raise SourceContractProposalError("PROPOSAL_REACHABILITY_INVALID")
        change_control = snapshot.get("change_control")
        if change_control not in {"unchanged", "versioned_correction"}:
            raise SourceContractProposalError("PROPOSAL_CHANGE_CONTROL_INVALID")
        snapshots[snapshot_id] = dict(snapshot)
    if list(snapshots) != sorted(snapshots):
        raise SourceContractProposalError("PROPOSAL_SNAPSHOT_ORDER_NONDETERMINISTIC")

    raw_files = payload.get("consumed_files")
    if not isinstance(raw_files, list) or not raw_files:
        raise SourceContractProposalError("PROPOSAL_CONSUMED_FILES_EMPTY")
    normalized_files: list[dict[str, object]] = []
    identities: set[tuple[str, str]] = set()
    local_paths: set[str] = set()
    for raw_file in raw_files:
        file = _require_mapping(raw_file, "PROPOSAL_CONSUMED_FILE_INVALID")
        snapshot_id = _require_string(file, "snapshot_id")
        if snapshot_id not in snapshots:
            raise SourceContractProposalError("PROPOSAL_FILE_SNAPSHOT_UNKNOWN")
        upstream_path = _normalized_path(file.get("upstream_path"), "upstream_path")
        local_bundle_path = _normalized_path(file.get("local_bundle_path"), "local_bundle_path")
        identity = (snapshot_id, upstream_path)
        if identity in identities or local_bundle_path in local_paths:
            raise SourceContractProposalError("PROPOSAL_CONSUMED_FILE_DUPLICATE")
        identities.add(identity)
        local_paths.add(local_bundle_path)
        try:
            raw_byte_length = require_byte_length(file.get("raw_byte_length"))
            raw_sha256 = require_sha256(file.get("raw_sha256"))
        except ValueError as error:
            raise SourceContractProposalError("PROPOSAL_RAW_DIGEST_OR_LENGTH_INVALID") from error
        if file.get("raw_authoritative") is not True:
            raise SourceContractProposalError("PROPOSAL_RAW_AUTHORITY_MISSING")
        normalized_files.append(
            {
                "declared_transforms": _validate_transforms(file.get("declared_transforms")),
                "experimental_role": _require_string(file, "experimental_role"),
                "local_bundle_path": local_bundle_path,
                "raw_authoritative": True,
                "raw_byte_length": raw_byte_length,
                "raw_sha256": raw_sha256,
                "snapshot_id": snapshot_id,
                "upstream_path": upstream_path,
                "why_consumed": _require_string(file, "why_consumed"),
            }
        )
    if normalized_files != sorted(
        normalized_files,
        key=lambda item: (str(item["snapshot_id"]), str(item["upstream_path"]), str(item["local_bundle_path"])),
    ):
        raise SourceContractProposalError("PROPOSAL_CONSUMED_FILE_ORDER_NONDETERMINISTIC")
    return {"consumed_files": normalized_files, "snapshots": snapshots}


def _approved_contract(proposal: Mapping[str, object]) -> dict[str, object]:
    """Return the exact proposal projection a proposal-only decision may bind."""
    return {
        "base_frozen_contract": proposal["base_frozen_contract"],
        "consumed_files": proposal["consumed_files"],
        "historical_rejected_receipt": proposal["historical_rejected_receipt"],
        "proposed_contract_version": proposal["proposed_contract_version"],
        "requested_generation_label": proposal["requested_generation_label"],
        "snapshots": proposal["snapshots"],
    }


def validate_source_publication_decision(
    decision: object,
    proposal: object,
    *,
    proposal_path: str,
    proposal_sha256: str,
) -> dict[str, object]:
    """Validate a narrow proposal-only approval without authorizing custody actions."""
    validate_source_contract_proposal(proposal)
    proposal_payload = _require_mapping(proposal, "INVALID_SOURCE_CONTRACT_PROPOSAL")
    payload = _require_mapping(decision, "INVALID_SOURCE_PUBLICATION_DECISION")
    expected_fields = {
        "approval_scope",
        "approved_contract",
        "authorization",
        "proposal",
        "reviewer",
        "schema_version",
        "state",
    }
    if set(payload) != expected_fields:
        raise SourceContractProposalError("SOURCE_DECISION_FIELDS_INVALID")
    if payload.get("schema_version") != "1":
        raise SourceContractProposalError("UNSUPPORTED_SOURCE_DECISION_SCHEMA")
    if payload.get("state") != "contract_approved":
        raise SourceContractProposalError("SOURCE_DECISION_NOT_CONTRACT_APPROVED")
    if payload.get("approval_scope") != "proposal_only":
        raise SourceContractProposalError("SOURCE_DECISION_SCOPE_INVALID")

    proposal_binding = _require_mapping(payload.get("proposal"), "SOURCE_DECISION_PROPOSAL_MISSING")
    if set(proposal_binding) != {"path", "sha256"}:
        raise SourceContractProposalError("SOURCE_DECISION_PROPOSAL_BINDING_INVALID")
    if _normalized_path(proposal_binding.get("path"), "decision_proposal_path") != proposal_path:
        raise SourceContractProposalError("SOURCE_DECISION_PROPOSAL_PATH_MISMATCH")
    try:
        proposal_digest = require_sha256(proposal_binding.get("sha256"))
    except ValueError as error:
        raise SourceContractProposalError("SOURCE_DECISION_PROPOSAL_SHA256_INVALID") from error
    if proposal_digest != proposal_sha256:
        raise SourceContractProposalError("SOURCE_DECISION_PROPOSAL_SHA256_MISMATCH")

    approved_contract = _require_mapping(
        payload.get("approved_contract"), "SOURCE_DECISION_CONTRACT_MISSING"
    )
    if dict(approved_contract) != _approved_contract(proposal_payload):
        raise SourceContractProposalError("SOURCE_DECISION_CONTRACT_MISMATCH")
    reviewer = _require_mapping(payload.get("reviewer"), "SOURCE_DECISION_REVIEWER_MISSING")
    if reviewer != {"approval_token": "approve-proposal-only"}:
        raise SourceContractProposalError("SOURCE_DECISION_REVIEWER_APPROVAL_INVALID")
    authorization = _require_mapping(
        payload.get("authorization"), "SOURCE_DECISION_AUTHORIZATION_MISSING"
    )
    expected_authorization = {
        "accepted_publication_authorized": False,
        "candidate_construction_authorized": False,
        "source_extraction_authorized": False,
    }
    if dict(authorization) != expected_authorization:
        raise SourceContractProposalError("SOURCE_DECISION_AUTHORIZATION_INVALID")
    return dict(payload)


def require_source_extraction_authorization(decision: Mapping[str, object]) -> None:
    """Fail closed unless a later, separately authorized decision permits extraction."""
    authorization = _require_mapping(
        decision.get("authorization"), "SOURCE_DECISION_AUTHORIZATION_MISSING"
    )
    if authorization.get("source_extraction_authorized") is not True:
        raise SourceContractProposalError("SOURCE_EXTRACTION_NOT_AUTHORIZED")


def require_candidate_construction_authorization(decision: Mapping[str, object]) -> None:
    """Fail closed unless a later decision expressly permits candidate construction."""
    authorization = _require_mapping(
        decision.get("authorization"), "SOURCE_DECISION_AUTHORIZATION_MISSING"
    )
    if authorization.get("candidate_construction_authorized") is not True:
        raise SourceContractProposalError("CANDIDATE_CONSTRUCTION_NOT_AUTHORIZED")


def require_accepted_publication_authorization(decision: Mapping[str, object]) -> None:
    """Fail closed unless a later decision expressly permits accepted publication."""
    authorization = _require_mapping(
        decision.get("authorization"), "SOURCE_DECISION_AUTHORIZATION_MISSING"
    )
    if authorization.get("accepted_publication_authorized") is not True:
        raise SourceContractProposalError("ACCEPTED_PUBLICATION_NOT_AUTHORIZED")


def _run_git(repository: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            ("git", "-C", os.fspath(repository), *arguments), check=False, capture_output=True
        )
    except FileNotFoundError as error:
        raise GitProofError("GIT_CAPABILITY_UNAVAILABLE") from error
    except OSError as error:
        raise GitProofError("GIT_SUBPROCESS_FAILED") from error


def _git_stdout(repository: Path, *arguments: str) -> bytes:
    result = _run_git(repository, *arguments)
    if result.returncode != 0:
        raise SourceContractProposalError("PROPOSAL_GIT_OBJECT_UNAVAILABLE")
    return result.stdout


def verify_source_contract_proposal_git(proposal: object, repository: Path) -> None:
    """Prove every proposed pin, tree, reachability, and raw Git blob locally."""
    normalized = validate_source_contract_proposal(proposal)
    snapshots = normalized["snapshots"]
    assert isinstance(snapshots, dict)
    for snapshot in snapshots.values():
        assert isinstance(snapshot, dict)
        pull_request = snapshot["pull_request"]
        pinned = snapshot["pinned_commit_sha"]
        expected_head = snapshot["canonical_pr_head_sha"]
        expected_tree = snapshot["pinned_tree_sha"]
        assert isinstance(pull_request, int)
        assert isinstance(pinned, str)
        assert isinstance(expected_head, str)
        assert isinstance(expected_tree, str)
        head = _git_stdout(repository, "rev-parse", f"refs/specchoice/pr/{pull_request}").decode(
            "ascii", "strict"
        ).strip()
        if head != expected_head:
            raise SourceContractProposalError("PROPOSAL_CANONICAL_PR_HEAD_MISMATCH")
        _git_stdout(repository, "cat-file", "-e", f"{pinned}^{{commit}}")
        actual_tree = _git_stdout(repository, "rev-parse", f"{pinned}^{{tree}}").decode(
            "ascii", "strict"
        ).strip()
        if actual_tree != expected_tree:
            raise SourceContractProposalError("PROPOSAL_PINNED_TREE_MISMATCH")
        ancestry = _run_git(repository, "merge-base", "--is-ancestor", pinned, head)
        if ancestry.returncode == 1:
            raise SourceContractProposalError("PROPOSAL_PIN_NOT_REACHABLE")
        if ancestry.returncode != 0:
            raise SourceContractProposalError("PROPOSAL_GIT_ANCESTRY_FAILED")

    files = normalized["consumed_files"]
    assert isinstance(files, list)
    for file in files:
        assert isinstance(file, dict)
        snapshot = snapshots[file["snapshot_id"]]
        assert isinstance(snapshot, dict)
        pinned = snapshot["pinned_commit_sha"]
        assert isinstance(pinned, str)
        object_ref = f"{pinned}:{file['upstream_path']}"
        object_type = _git_stdout(repository, "cat-file", "-t", object_ref).decode("ascii", "strict").strip()
        if object_type != "blob":
            raise SourceContractProposalError("PROPOSAL_CONSUMED_PATH_NOT_REGULAR_FILE")
        raw = _git_stdout(repository, "show", object_ref)
        if len(raw) != file["raw_byte_length"]:
            raise SourceContractProposalError("PROPOSAL_RAW_BYTE_LENGTH_MISMATCH")
        if hashlib.sha256(raw).hexdigest() != file["raw_sha256"]:
            raise SourceContractProposalError("PROPOSAL_RAW_SHA256_MISMATCH")
