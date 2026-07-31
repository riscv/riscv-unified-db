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


class FixtureRegistryError(ValueError):
    """Stable diagnostic for PR #2164 finite-set fixture custody failures."""


_FIXTURE_BASE = "tools/python/param-extraction-eval/cases"
_EXPECTED_FIXTURES = {
    "CAND_WARL_FIXED_LEGAL_SET": ("candidate", "candidates", ("expected.yaml", "source.txt")),
    "NEG_EXT_GATED_PBMTE": ("negative", "negatives", ("expected.yaml", "source.txt")),
    "NEG_FIXED_ENCODING": ("negative", "negatives", ("expected.yaml", "source.txt")),
    "NEG_SHALL_NO_DELEGATION": ("negative", "negatives", ("expected.yaml", "source.txt")),
    "NEG_SOFTWARE_ADVICE": ("negative", "negatives", ("expected.yaml", "source.txt")),
    "POS_CSR_RW_MTVEC_ACCESS": ("positive", "positives", ("expected.yaml", "gold.yaml", "source.txt")),
    "POS_DIRECT_CACHE_BLOCK": ("positive", "positives", ("expected.yaml", "gold.yaml", "source.txt")),
    "POS_DIRECT_NUM_PMP": ("positive", "positives", ("expected.yaml", "gold.yaml", "source.txt")),
    "POS_RECALL_COUNT_GEILEN": ("positive", "positives", ("expected.yaml", "gold.yaml", "source.txt")),
    "POS_WARL_ASID_WIDTH": ("positive", "positives", ("expected.yaml", "gold.yaml", "source.txt")),
    "POS_WARL_MTVEC_MODES": ("positive", "positives", ("expected.yaml", "gold.yaml", "source.txt")),
}
_FIXTURE_ROLES = {
    "expected.yaml": "fixture_expected",
    "gold.yaml": "fixture_gold",
    "source.txt": "fixture_source",
}
_FIXTURE_COMMIT = "22e84458c87a7ccf4c07034de1eb6d0bf9764144"
_FIXTURE_TREE = "af003b427c66bd8ac9803a91b3bf363a1b1304d9"


def _fixture_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise FixtureRegistryError("FIXTURE_PATH_INVALID")
    try:
        return require_relative_posix_path(value).as_posix()
    except FilesystemPolicyError as error:
        raise FixtureRegistryError(str(error)) from error


def validate_fixture_registry(registry: object) -> dict[str, object]:
    """Validate the finite named PR #2164 set before it can reach construction."""
    if not isinstance(registry, Mapping) or set(registry) != {
        "fixture_count", "fixtures", "pinned_commit_sha", "pinned_tree_sha", "pull_request",
        "raw_file_count", "repository", "schema_version", "snapshot_id",
    }:
        raise FixtureRegistryError("FIXTURE_REGISTRY_INVALID")
    if registry.get("schema_version") != "1" or registry.get("repository") != "riscv/riscv-unified-db":
        raise FixtureRegistryError("FIXTURE_REGISTRY_INVALID")
    if registry.get("snapshot_id") != "evaluation_fixtures" or registry.get("pull_request") != 2164:
        raise FixtureRegistryError("FIXTURE_REGISTRY_IDENTITY_MISMATCH")
    if registry.get("pinned_commit_sha") != _FIXTURE_COMMIT or registry.get("pinned_tree_sha") != _FIXTURE_TREE:
        raise FixtureRegistryError("FIXTURE_REGISTRY_PIN_MISMATCH")
    fixtures = registry.get("fixtures")
    if not isinstance(fixtures, list):
        raise FixtureRegistryError("FIXTURE_REGISTRY_INVALID")
    if not fixtures:
        raise FixtureRegistryError("FIXTURE_REGISTRY_EMPTY")
    normalized: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    total = 0
    for fixture in fixtures:
        if not isinstance(fixture, Mapping) or set(fixture) != {"fixture_class", "fixture_id", "files"}:
            raise FixtureRegistryError("FIXTURE_ENTRY_INVALID")
        fixture_id = fixture.get("fixture_id")
        fixture_class = fixture.get("fixture_class")
        if not isinstance(fixture_id, str) or not fixture_id:
            raise FixtureRegistryError("FIXTURE_ID_INVALID")
        if fixture_id in seen_ids:
            raise FixtureRegistryError("FIXTURE_DUPLICATE")
        seen_ids.add(fixture_id)
        expected = _EXPECTED_FIXTURES.get(fixture_id)
        if expected is None:
            raise FixtureRegistryError("FIXTURE_SET_MISMATCH")
        expected_class, directory, expected_names = expected
        if fixture_class != expected_class:
            raise FixtureRegistryError("FIXTURE_CLASS_MISMATCH")
        files = fixture.get("files")
        if not isinstance(files, list) or not files:
            raise FixtureRegistryError("FIXTURE_FILE_SET_MISMATCH")
        seen_names: set[str] = set()
        normalized_files: list[dict[str, object]] = []
        for file in files:
            if not isinstance(file, Mapping) or set(file) != {
                "filename", "local_bundle_path", "raw_byte_length", "raw_sha256", "role", "upstream_path",
            }:
                raise FixtureRegistryError("FIXTURE_FILE_INVALID")
            filename = file.get("filename")
            if not isinstance(filename, str) or filename in seen_names:
                raise FixtureRegistryError("FIXTURE_FILE_DUPLICATE")
            seen_names.add(filename)
            if filename not in expected_names:
                raise FixtureRegistryError("FIXTURE_FILE_SET_MISMATCH")
            if file.get("role") != _FIXTURE_ROLES[filename]:
                raise FixtureRegistryError("FIXTURE_ROLE_MISMATCH")
            upstream = _fixture_path(file.get("upstream_path"))
            local = _fixture_path(file.get("local_bundle_path"))
            if upstream != f"{_FIXTURE_BASE}/{directory}/{fixture_id}/{filename}" or local != f"raw/evaluation_fixtures/{fixture_id}/{filename}":
                raise FixtureRegistryError("FIXTURE_PATH_MISMATCH")
            try:
                length = require_byte_length(file.get("raw_byte_length"))
                digest = require_sha256(file.get("raw_sha256"))
            except ValueError as error:
                raise FixtureRegistryError("FIXTURE_DIGEST_OR_LENGTH_INVALID") from error
            normalized_files.append({
                "filename": filename, "local_bundle_path": local, "raw_byte_length": length,
                "raw_sha256": digest, "role": _FIXTURE_ROLES[filename], "upstream_path": upstream,
            })
        if set(seen_names) != set(expected_names):
            raise FixtureRegistryError("FIXTURE_FILE_SET_MISMATCH")
        if [item["filename"] for item in normalized_files] != sorted(expected_names):
            raise FixtureRegistryError("FIXTURE_FILE_ORDER_NONDETERMINISTIC")
        normalized.append({"fixture_class": expected_class, "fixture_id": fixture_id, "files": normalized_files})
        total += len(normalized_files)
    if seen_ids != set(_EXPECTED_FIXTURES):
        raise FixtureRegistryError("FIXTURE_SET_MISMATCH")
    if [item["fixture_id"] for item in normalized] != sorted(_EXPECTED_FIXTURES):
        raise FixtureRegistryError("FIXTURE_ORDER_NONDETERMINISTIC")
    if registry.get("fixture_count") != len(_EXPECTED_FIXTURES) or registry.get("raw_file_count") != total or total != 28:
        raise FixtureRegistryError("FIXTURE_COUNT_MISMATCH")
    return {"fixture_count": len(_EXPECTED_FIXTURES), "fixtures": normalized, "raw_file_count": total}


def verify_fixture_registry_git(registry: object, repository: Path) -> None:
    """Prove the exact registry against the cached Git PR ref and pinned blobs."""
    normalized = validate_fixture_registry(registry)
    def git_stdout(*arguments: str) -> bytes:
        result = _run_git(repository, *arguments)
        if result.returncode != 0:
            raise FixtureRegistryError("FIXTURE_GIT_OBJECT_UNAVAILABLE")
        return result.stdout
    head = git_stdout("rev-parse", "refs/specchoice/pr-2164-head").decode("ascii", "strict").strip()
    if head != _FIXTURE_COMMIT:
        raise FixtureRegistryError("FIXTURE_PR_HEAD_MISMATCH")
    tree = git_stdout("rev-parse", f"{_FIXTURE_COMMIT}^{{tree}}").decode("ascii", "strict").strip()
    if tree != _FIXTURE_TREE:
        raise FixtureRegistryError("FIXTURE_TREE_MISMATCH")
    ancestry = _run_git(repository, "merge-base", "--is-ancestor", _FIXTURE_COMMIT, head)
    if ancestry.returncode != 0:
        raise FixtureRegistryError("FIXTURE_PIN_NOT_REACHABLE")
    for fixture in normalized["fixtures"]:
        assert isinstance(fixture, dict)
        for file in fixture["files"]:
            assert isinstance(file, dict)
            object_ref = f"{_FIXTURE_COMMIT}:{file['upstream_path']}"
            if git_stdout("cat-file", "-t", object_ref).decode("ascii", "strict").strip() != "blob":
                raise FixtureRegistryError("FIXTURE_NON_REGULAR_FILE")
            raw = git_stdout("show", object_ref)
            if len(raw) != file["raw_byte_length"]:
                raise FixtureRegistryError("FIXTURE_RAW_BYTE_LENGTH_MISMATCH")
            if hashlib.sha256(raw).hexdigest() != file["raw_sha256"]:
                raise FixtureRegistryError("FIXTURE_RAW_SHA256_MISMATCH")


def validate_fixture_closure_proposal(proposal: object) -> dict[str, object]:
    """Validate the compact v3 proposal that binds the full registry by digest."""
    if not isinstance(proposal, Mapping) or set(proposal) != {
        "base_source_snapshots", "fixture_registry", "generation", "pinned_commit_sha",
        "pinned_tree_sha", "schema_version", "status",
    }:
        raise SourceContractProposalError("FIXTURE_CLOSURE_PROPOSAL_INVALID")
    if proposal.get("schema_version") != "1" or proposal.get("status") != "pending_reviewer_approval":
        raise SourceContractProposalError("FIXTURE_CLOSURE_PROPOSAL_INVALID")
    if proposal.get("generation") != "source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2":
        raise SourceContractProposalError("FIXTURE_CLOSURE_GENERATION_INVALID")
    if proposal.get("pinned_commit_sha") != _FIXTURE_COMMIT or proposal.get("pinned_tree_sha") != _FIXTURE_TREE:
        raise SourceContractProposalError("FIXTURE_CLOSURE_PIN_INVALID")
    normalized: dict[str, object] = {}
    for field, expected_path in (
        ("base_source_snapshots", "config/source_snapshots.json"),
        ("fixture_registry", "config/fixture-registry-pr2164-v1.json"),
    ):
        binding = proposal.get(field)
        if not isinstance(binding, Mapping) or set(binding) != {"path", "sha256"}:
            raise SourceContractProposalError("FIXTURE_CLOSURE_BINDING_INVALID")
        if _normalized_path(binding.get("path"), f"{field}_path") != expected_path:
            raise SourceContractProposalError("FIXTURE_CLOSURE_BINDING_INVALID")
        try:
            normalized[field] = {"path": expected_path, "sha256": require_sha256(binding.get("sha256"))}
        except ValueError as error:
            raise SourceContractProposalError("FIXTURE_CLOSURE_BINDING_INVALID") from error
    return normalized


def validate_fixture_closure_decision(
    decision: object, proposal: object, *, proposal_path: str, proposal_sha256: str
) -> dict[str, object]:
    """Allow local candidate construction only; never authorise acceptance or publication."""
    validate_fixture_closure_proposal(proposal)
    if not isinstance(decision, Mapping) or set(decision) != {
        "approval_scope", "authorization", "proposal", "reviewer", "schema_version", "state",
    }:
        raise SourceContractProposalError("FIXTURE_CLOSURE_DECISION_INVALID")
    if decision.get("schema_version") != "1" or decision.get("approval_scope") != "local_candidate_construction_only" or decision.get("state") != "candidate_construction_authorized":
        raise SourceContractProposalError("FIXTURE_CLOSURE_DECISION_INVALID")
    if decision.get("authorization") != {
        "candidate_construction_authorized": True,
        "downstream_eligible": False,
        "external_publication_authorized": False,
    }:
        raise SourceContractProposalError("FIXTURE_CLOSURE_AUTHORIZATION_INVALID")
    if decision.get("reviewer") != {"approval_token": "authorize-v7-local-receipt-basis-only"}:
        raise SourceContractProposalError("FIXTURE_CLOSURE_REVIEWER_INVALID")
    binding = decision.get("proposal")
    if not isinstance(binding, Mapping) or set(binding) != {"path", "sha256"}:
        raise SourceContractProposalError("FIXTURE_CLOSURE_DECISION_INVALID")
    if _normalized_path(binding.get("path"), "fixture_closure_proposal_path") != proposal_path:
        raise SourceContractProposalError("FIXTURE_CLOSURE_PROPOSAL_MISMATCH")
    try:
        digest = require_sha256(binding.get("sha256"))
    except ValueError as error:
        raise SourceContractProposalError("FIXTURE_CLOSURE_PROPOSAL_MISMATCH") from error
    if digest != proposal_sha256:
        raise SourceContractProposalError("FIXTURE_CLOSURE_PROPOSAL_MISMATCH")
    return dict(decision)


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
    if payload.get("proposed_contract_version") not in {"2", "3"}:
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
    """Validate a hash-bound approval with explicit, non-escalating authority."""
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
    approval_scope = payload.get("approval_scope")
    state = payload.get("state")
    if approval_scope not in {"proposal_only", "candidate_construction_only"}:
        raise SourceContractProposalError("SOURCE_DECISION_SCOPE_INVALID")
    expected_state = {
        "proposal_only": "contract_approved",
        "candidate_construction_only": "candidate_construction_authorized",
    }[approval_scope]
    if state != expected_state:
        raise SourceContractProposalError("SOURCE_DECISION_STATE_INVALID")

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
    expected_reviewer = {
        "proposal_only": {"approval_token": "approve-proposal-only"},
        "candidate_construction_only": {
            "approval_token": "authorize-candidate-construction-only"
        },
    }[approval_scope]
    if reviewer != expected_reviewer:
        raise SourceContractProposalError("SOURCE_DECISION_REVIEWER_APPROVAL_INVALID")
    authorization = _require_mapping(
        payload.get("authorization"), "SOURCE_DECISION_AUTHORIZATION_MISSING"
    )
    expected_authorization = {
        "proposal_only": {
            "accepted_publication_authorized": False,
            "candidate_construction_authorized": False,
            "source_extraction_authorized": False,
        },
        "candidate_construction_only": {
            "accepted_publication_authorized": False,
            "candidate_construction_authorized": True,
            "source_extraction_authorized": True,
        },
    }[approval_scope]
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
    if "external_publication_authorized" in authorization:
        if authorization.get("external_publication_authorized") is not True:
            raise SourceContractProposalError("EXTERNAL_PUBLICATION_NOT_AUTHORIZED")
        return
    if authorization.get("accepted_publication_authorized") is not True:
        raise SourceContractProposalError("ACCEPTED_PUBLICATION_NOT_AUTHORIZED")


def validate_local_accepted_generation_decision(
    decision: object, *, allow_historical: bool = False
) -> dict[str, object]:
    """Validate the local-only reviewer disposition without granting publication authority."""
    payload = _require_mapping(decision, "INVALID_LOCAL_ACCEPTANCE_DECISION")
    expected_fields = {
        "approval_scope",
        "approved_generation",
        "authorization",
        "reviewed_receipt_basis_sha256",
        "reviewer",
        "schema_version",
        "state",
    }
    schema_version = payload.get("schema_version")
    if schema_version == "3":
        expected_fields |= {
            "committed_boundary_projection_sha256",
            "phase_start_baseline_sha256",
            "reviewed_revision",
        }
    if set(payload) != expected_fields:
        raise SourceContractProposalError("LOCAL_ACCEPTANCE_DECISION_FIELDS_INVALID")
    if schema_version not in {"2", "3"}:
        raise SourceContractProposalError("UNSUPPORTED_LOCAL_ACCEPTANCE_DECISION_SCHEMA")
    if schema_version == "2" and not allow_historical:
        raise SourceContractProposalError("LOCAL_ACCEPTANCE_HISTORICAL_DECISION_REQUIRES_EXPLICIT_PATH")
    if payload.get("approval_scope") != "local_accepted_generation_only":
        raise SourceContractProposalError("LOCAL_ACCEPTANCE_SCOPE_INVALID")
    if payload.get("state") != "local_accepted_generation_authorized":
        raise SourceContractProposalError("LOCAL_ACCEPTANCE_STATE_INVALID")
    reviewer = _require_mapping(payload.get("reviewer"), "LOCAL_ACCEPTANCE_REVIEWER_MISSING")
    if dict(reviewer) != {"disposition": "approved_local_only"}:
        raise SourceContractProposalError("LOCAL_ACCEPTANCE_REVIEWER_INVALID")
    authorization = _require_mapping(payload.get("authorization"), "LOCAL_ACCEPTANCE_AUTHORIZATION_MISSING")
    if dict(authorization) != {
        "external_publication_authorized": False,
        "local_accepted_generation_authorized": True,
    }:
        raise SourceContractProposalError("LOCAL_ACCEPTANCE_AUTHORIZATION_INVALID")
    binding = _require_mapping(payload.get("approved_generation"), "LOCAL_ACCEPTANCE_BINDING_MISSING")
    if set(binding) != {
        "candidate_relative_path",
        "core_sha256",
        "generation",
        "root_sha256",
        "snapshot_manifest_sha256",
    }:
        raise SourceContractProposalError("LOCAL_ACCEPTANCE_BINDING_INVALID")
    _normalized_path(binding.get("candidate_relative_path"), "candidate_relative_path")
    _require_string(binding, "generation")
    for field in ("core_sha256", "root_sha256", "snapshot_manifest_sha256"):
        try:
            require_sha256(binding.get(field))
        except ValueError as error:
            raise SourceContractProposalError("LOCAL_ACCEPTANCE_BINDING_INVALID") from error
    try:
        require_sha256(payload.get("reviewed_receipt_basis_sha256"))
    except ValueError as error:
        raise SourceContractProposalError("LOCAL_ACCEPTANCE_RECEIPT_BASIS_INVALID") from error
    if schema_version == "3":
        revision = payload.get("reviewed_revision")
        if not isinstance(revision, str) or len(revision) != 40 or any(char not in "0123456789abcdef" for char in revision):
            raise SourceContractProposalError("LOCAL_ACCEPTANCE_REVIEWED_REVISION_INVALID")
        for field in ("phase_start_baseline_sha256", "committed_boundary_projection_sha256"):
            try:
                require_sha256(payload.get(field))
            except ValueError as error:
                raise SourceContractProposalError("LOCAL_ACCEPTANCE_PROJECTION_BINDING_INVALID") from error
    return dict(payload)


def require_local_accepted_generation_authorization(
    decision: Mapping[str, object], identity: Mapping[str, object], snapshot_manifest_sha256: str,
    *, allow_historical: bool = False,
) -> None:
    """Require exact local-only authority for one already-verified candidate identity."""
    validated = validate_local_accepted_generation_decision(decision, allow_historical=allow_historical)
    binding = _require_mapping(validated["approved_generation"], "LOCAL_ACCEPTANCE_BINDING_MISSING")
    for field in ("generation", "root_sha256", "manifest_sha256"):
        expected_field = "core_sha256" if field == "manifest_sha256" else field
        if binding.get(expected_field) != identity.get(field):
            raise SourceContractProposalError("LOCAL_ACCEPTANCE_IDENTITY_MISMATCH")
    if binding.get("snapshot_manifest_sha256") != snapshot_manifest_sha256:
        raise SourceContractProposalError("LOCAL_ACCEPTANCE_SNAPSHOT_MISMATCH")


def validate_fixture_closure_local_acceptance_decision(decision: object) -> dict[str, object]:
    """Validate the v3 fixture-only local acceptance authority.

    This deliberately has a separate schema from the historical generic local
    acceptance decision.  It binds the registry and immutable v7 restart lineage,
    which are material to downstream fixture completeness.
    """
    payload = _require_mapping(decision, "FIXTURE_CLOSURE_ACCEPTANCE_DECISION_INVALID")
    if set(payload) != {
        "approval_scope", "approved_generation", "authorization", "fixture_registry_sha256",
        "reviewer", "schema_version", "state", "v7_basis",
    }:
        raise SourceContractProposalError("FIXTURE_CLOSURE_ACCEPTANCE_DECISION_FIELDS_INVALID")
    if payload.get("schema_version") != "1" or payload.get("approval_scope") != "fixture_closure_local_acceptance_only" or payload.get("state") != "fixture_closure_local_acceptance_authorized":
        raise SourceContractProposalError("FIXTURE_CLOSURE_ACCEPTANCE_DECISION_INVALID")
    if _require_mapping(payload.get("reviewer"), "FIXTURE_CLOSURE_ACCEPTANCE_REVIEWER_INVALID") != {"disposition": "approved_local_only"}:
        raise SourceContractProposalError("FIXTURE_CLOSURE_ACCEPTANCE_REVIEWER_INVALID")
    if _require_mapping(payload.get("authorization"), "FIXTURE_CLOSURE_ACCEPTANCE_AUTHORIZATION_INVALID") != {
        "external_publication_authorized": False,
        "fixture_closure_local_acceptance_authorized": True,
    }:
        raise SourceContractProposalError("FIXTURE_CLOSURE_ACCEPTANCE_AUTHORIZATION_INVALID")
    binding = _require_mapping(payload.get("approved_generation"), "FIXTURE_CLOSURE_ACCEPTANCE_BINDING_INVALID")
    if set(binding) != {"candidate_relative_path", "core_sha256", "generation", "root_sha256", "snapshot_manifest_sha256"}:
        raise SourceContractProposalError("FIXTURE_CLOSURE_ACCEPTANCE_BINDING_INVALID")
    _normalized_path(binding.get("candidate_relative_path"), "fixture_closure_candidate_relative_path")
    _require_string(binding, "generation")
    for field in ("core_sha256", "root_sha256", "snapshot_manifest_sha256"):
        try:
            require_sha256(binding.get(field))
        except ValueError as error:
            raise SourceContractProposalError("FIXTURE_CLOSURE_ACCEPTANCE_BINDING_INVALID") from error
    try:
        require_sha256(payload.get("fixture_registry_sha256"))
    except ValueError as error:
        raise SourceContractProposalError("FIXTURE_CLOSURE_ACCEPTANCE_REGISTRY_INVALID") from error
    basis = _require_mapping(payload.get("v7_basis"), "FIXTURE_CLOSURE_ACCEPTANCE_BASIS_INVALID")
    if set(basis) != {"allowlist_sha256", "baseline_sha256", "restart_receipt_sha256", "reviewed_revision"}:
        raise SourceContractProposalError("FIXTURE_CLOSURE_ACCEPTANCE_BASIS_INVALID")
    revision = basis.get("reviewed_revision")
    if not isinstance(revision, str) or len(revision) != 40 or any(char not in "0123456789abcdef" for char in revision):
        raise SourceContractProposalError("FIXTURE_CLOSURE_ACCEPTANCE_BASIS_INVALID")
    for field in ("allowlist_sha256", "baseline_sha256", "restart_receipt_sha256"):
        try:
            require_sha256(basis.get(field))
        except ValueError as error:
            raise SourceContractProposalError("FIXTURE_CLOSURE_ACCEPTANCE_BASIS_INVALID") from error
    return dict(payload)


def require_fixture_closure_local_acceptance_authorization(
    decision: object, identity: Mapping[str, object], snapshot_manifest_sha256: str,
    registry_sha256: str, v7_basis: Mapping[str, object],
) -> None:
    """Require exact authority for a current, complete fixture candidate."""
    payload = validate_fixture_closure_local_acceptance_decision(decision)
    binding = _require_mapping(payload["approved_generation"], "FIXTURE_CLOSURE_ACCEPTANCE_BINDING_INVALID")
    for actual, bound in (("generation", "generation"), ("manifest_sha256", "core_sha256"), ("root_sha256", "root_sha256")):
        if binding.get(bound) != identity.get(actual):
            raise SourceContractProposalError("FIXTURE_CLOSURE_ACCEPTANCE_IDENTITY_MISMATCH")
    if binding.get("snapshot_manifest_sha256") != snapshot_manifest_sha256:
        raise SourceContractProposalError("FIXTURE_CLOSURE_ACCEPTANCE_SNAPSHOT_MISMATCH")
    if payload.get("fixture_registry_sha256") != registry_sha256:
        raise SourceContractProposalError("FIXTURE_CLOSURE_ACCEPTANCE_REGISTRY_MISMATCH")
    if payload.get("v7_basis") != dict(v7_basis):
        raise SourceContractProposalError("FIXTURE_CLOSURE_ACCEPTANCE_BASIS_MISMATCH")


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
