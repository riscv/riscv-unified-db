# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Append-only v6 construction and v13 local-acceptance state machine.

This module deliberately keeps machine construction separate from human
decisions.  Every writer takes a previously authored decision as inert input,
revalidates the complete runtime closure and authority head, and only then
opens a no-replace target.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path

from .bundle import (
    BundleError,
    _bundle_artifacts,
    _publish_directory_no_replace,
    _raw_artifacts,
    _root_digest,
    _run_embedded_verifier,
    _snapshot_manifest,
    _sync_directory,
    _write_exact,
    verify_candidate,
)
from .canonical import canonical_json_bytes, require_byte_length, require_sha256, sha256_bytes
from .filesystem import (
    FilesystemPolicyError,
    enumerate_authoritative_files,
    read_authoritative_file,
    replace_descriptor_file,
    require_relative_posix_path,
    write_exact_descriptor_files,
)
from .runtime_closure import (
    RuntimeClosureError,
    future_target_inventory_v6,
    validate_future_target_occupancy_v6,
    verify_runtime_closure_v2,
)
from .source_contract import (
    SourceContractProposalError,
    validate_v5_rejected_pre_authorization_receipt,
)
from .verify import embed_verifier_artifacts, verify_accepted_bundle


class SuccessorProtocolError(ValueError):
    """Stable diagnostic for v6/v13 successor protocol failure."""


_EXPERIMENT_PREFIX = "experiments/specchoice-v1.3.2"
_GENERATION_V6 = "source-contract-v6-pr2164-semantic-gold-executable-closure-verifier-rooted-v6"
_ACCEPTED_V3_RELATIVE = (
    f"{_EXPERIMENT_PREFIX}/bundles/accepted/"
    "source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v3"
)
_PACKET_RELATIVE = (
    f"{_EXPERIMENT_PREFIX}/receipts/"
    "source-contract-proposal-v6-pr2164-semantic-gold-executable-closure-verifier-rooted-v6"
)
_DECISION_RELATIVE = (
    f"{_EXPERIMENT_PREFIX}/receipts/"
    "source-contract-construction-decision-v6-pr2164-semantic-gold-executable-closure-verifier-rooted-v6.json"
)
_CANDIDATE_RELATIVE = f"{_EXPERIMENT_PREFIX}/bundles/candidates/{_GENERATION_V6}"
_AUDIT_RELATIVE = f"{_EXPERIMENT_PREFIX}/receipts/{_GENERATION_V6}/candidate-audit-v6.json"
_REQUEST_RELATIVE = f"{_EXPERIMENT_PREFIX}/receipts/local-acceptance-request-v13.json"
_ACCEPTANCE_DECISION_RELATIVE = f"{_EXPERIMENT_PREFIX}/receipts/local-acceptance-decision-v13.json"
_ACCEPTED_RELATIVE = f"{_EXPERIMENT_PREFIX}/bundles/accepted/{_GENERATION_V6}"
_AUTHORITY_RELATIVE = f"{_EXPERIMENT_PREFIX}/phase2/source-authority.json"
_V5_REJECTION_RELATIVE = (
    f"{_EXPERIMENT_PREFIX}/receipts/"
    "source-contract-construction-proposal-v5-non-executable-supersession-v1.json"
)

_PROPOSAL_INPUTS = (
    f"{_EXPERIMENT_PREFIX}/receipts/source-contract-construction-authorization-v4-non-executable-supersession-v1.json",
    f"{_EXPERIMENT_PREFIX}/receipts/runtime-executable-closure-v1.json",
    f"{_EXPERIMENT_PREFIX}/receipts/source-contract-proposal-v5-pr2164-semantic-gold-executable-closure-verifier-rooted-v5.json",
    f"{_EXPERIMENT_PREFIX}/receipts/source-contract-construction-proposal-v5-supersession-v4.json",
    f"{_EXPERIMENT_PREFIX}/receipts/source-contract-proposal-v4-pr2164-semantic-gold-closure-verifier-rooted-v4.json",
    f"{_EXPERIMENT_PREFIX}/receipts/source-contract-construction-proposal-v4-supersession-v3.json",
    f"{_EXPERIMENT_PREFIX}/receipts/source-contract-construction-decision-v4-pr2164-semantic-gold-closure-verifier-rooted-v4.json",
    f"{_EXPERIMENT_PREFIX}/reviews/h1-source-gold-ontology-decision-v1.json",
    f"{_EXPERIMENT_PREFIX}/config/fixture-registry-pr2164-v6.json",
    f"{_EXPERIMENT_PREFIX}/config/fixture-repairs/pr2164-semantic-gold-v5/repair-manifest.json",
    f"{_EXPERIMENT_PREFIX}/config/measurement/pr2164-semantic-gold-contract-v2.json",
    f"{_EXPERIMENT_PREFIX}/config/measurement/pr2164-adapter-rules-v3.json",
    f"{_EXPERIMENT_PREFIX}/config/measurement/canonical-adjudication-schema-v3.json",
    f"{_EXPERIMENT_PREFIX}/config/measurement/h1-semantic-review-questions-v2.json",
    f"{_EXPERIMENT_PREFIX}/config/measurement/h1-review-schema-v4.json",
    f"{_EXPERIMENT_PREFIX}/fixtures/measurement/golden-predictions-v4.json",
    f"{_EXPERIMENT_PREFIX}/fixtures/measurement/adversarial/required-diagnostics-v4.json",
    ".planning/ROADMAP.md",
    ".planning/REQUIREMENTS.md",
    ".planning/phases/01-isolated-evidence-boundary-and-source-integrity/01-VERIFICATION.md",
    ".planning/phases/01-isolated-evidence-boundary-and-source-integrity/01-REVIEW.md",
    ".planning/phases/02-deterministic-measurement-spine/02-VERIFICATION.md",
    ".planning/phases/02-deterministic-measurement-spine/02-REVIEW.md",
    ".planning/phases/02-deterministic-measurement-spine/02-19-PLAN.md",
)


def _canonical_object(path: Path, diagnostic: str) -> tuple[dict[str, object], bytes]:
    try:
        evidence, raw = read_authoritative_file(path.parent, path.name)
        value = json.loads(raw.decode("utf-8"))
    except (FilesystemPolicyError, OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SuccessorProtocolError(diagnostic) from error
    if evidence.file_kind != "regular_file" or not isinstance(value, dict) or canonical_json_bytes(value) != raw:
        raise SuccessorProtocolError(diagnostic)
    return value, raw


def _run_isolated_verifier(bundle: Path) -> None:
    try:
        completed = subprocess.run(
            [sys.executable, "-I", "-B", "verify_bundle.py"], cwd=bundle,
            env={"PATH": "/nonexistent", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1"},
            check=False, capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise SuccessorProtocolError("V6_ISOLATED_REPLAY_FAILED") from error
    if completed.returncode != 0 or completed.stdout != "bundle verified\n":
        raise SuccessorProtocolError("V6_ISOLATED_REPLAY_FAILED")


def _binding(repository: Path, relative: str) -> dict[str, object]:
    try:
        relative = require_relative_posix_path(relative).as_posix()
        raw = (repository / relative).read_bytes()
    except (OSError, ValueError) as error:
        raise SuccessorProtocolError("V6_PROPOSAL_INPUT_INVALID") from error
    return {"byte_length": len(raw), "path": relative, "sha256": sha256_bytes(raw)}


def _validate_registry_v6(repository: Path) -> tuple[dict[str, object], bytes]:
    registry_path = repository / f"{_EXPERIMENT_PREFIX}/config/fixture-registry-pr2164-v6.json"
    registry, registry_raw = _canonical_object(registry_path, "V6_REGISTRY_INVALID")
    required = {
        "file_entries", "fixture_count", "fixture_ids", "ontology_decision_sha256", "partition",
        "raw_file_count", "repair_manifest", "repair_manifest_byte_length", "repair_manifest_sha256",
        "schema_version",
    }
    entries = registry.get("file_entries")
    if (
        set(registry) != required or registry.get("schema_version") != "6"
        or registry.get("fixture_count") != 11 or registry.get("raw_file_count") != 29
        or registry.get("partition") != {"candidate": 2, "negative": 3, "positive": 6}
        or not isinstance(entries, list) or len(entries) != 29
    ):
        raise SuccessorProtocolError("V6_REGISTRY_INVALID")
    manifest_relative = registry.get("repair_manifest")
    if not isinstance(manifest_relative, str):
        raise SuccessorProtocolError("V6_REGISTRY_INVALID")
    manifest_path = repository / _EXPERIMENT_PREFIX / manifest_relative
    manifest, manifest_raw = _canonical_object(manifest_path, "V6_REPAIR_MANIFEST_INVALID")
    if (
        len(manifest_raw) != registry.get("repair_manifest_byte_length")
        or sha256_bytes(manifest_raw) != registry.get("repair_manifest_sha256")
        or manifest.get("payload_count") != 9
        or not isinstance(manifest.get("payloads"), list)
    ):
        raise SuccessorProtocolError("V6_REPAIR_MANIFEST_INVALID")
    accepted = repository / _ACCEPTED_V3_RELATIVE
    seen: set[tuple[str, str]] = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {
            "byte_length", "fixture_id", "origin", "path", "role", "sha256"
        }:
            raise SuccessorProtocolError("V6_REGISTRY_ENTRY_INVALID")
        origin, source = entry.get("origin"), entry.get("path")
        if origin not in {"accepted-v3", "repair-v5"} or not isinstance(source, str):
            raise SuccessorProtocolError("V6_REGISTRY_ENTRY_INVALID")
        source_path = accepted / source if origin == "accepted-v3" else repository / _EXPERIMENT_PREFIX / source
        try:
            raw = source_path.read_bytes()
            length = require_byte_length(entry.get("byte_length"))
            digest = require_sha256(entry.get("sha256"))
        except (OSError, ValueError) as error:
            raise SuccessorProtocolError("V6_REGISTRY_ENTRY_INVALID") from error
        identity = (str(entry.get("fixture_id")), str(entry.get("role")))
        if identity in seen or len(raw) != length or sha256_bytes(raw) != digest:
            raise SuccessorProtocolError("V6_REGISTRY_ENTRY_INVALID")
        seen.add(identity)
    return registry, registry_raw


def _proposal_inputs(repository: Path) -> list[dict[str, object]]:
    _, _ = _validate_registry_v6(repository)
    manifest, _ = _canonical_object(
        repository / f"{_EXPERIMENT_PREFIX}/config/fixture-repairs/pr2164-semantic-gold-v5/repair-manifest.json",
        "V6_REPAIR_MANIFEST_INVALID",
    )
    payloads = manifest.get("payloads")
    if not isinstance(payloads, list):
        raise SuccessorProtocolError("V6_REPAIR_MANIFEST_INVALID")
    paths = set(_PROPOSAL_INPUTS)
    for item in payloads:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise SuccessorProtocolError("V6_REPAIR_MANIFEST_INVALID")
        paths.add(f"{_EXPERIMENT_PREFIX}/{item['path']}")
    return [_binding(repository, path) for path in sorted(paths)]


def _parse_closure_v2(repository: Path, closure_raw: bytes) -> dict[str, object]:
    try:
        closure = json.loads(closure_raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SuccessorProtocolError("RUNTIME_CLOSURE_V2_INVALID") from error
    if not isinstance(closure, dict) or canonical_json_bytes(closure) != closure_raw:
        raise SuccessorProtocolError("RUNTIME_CLOSURE_V2_INVALID")
    try:
        return verify_runtime_closure_v2(closure, repository)
    except RuntimeClosureError as error:
        raise SuccessorProtocolError(str(error)) from error


def _validate_v5_rejection(repository: Path, raw: bytes) -> dict[str, object]:
    try:
        receipt = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SuccessorProtocolError("V5_REJECTED_HISTORY_RECEIPT_INVALID") from error
    if not isinstance(receipt, dict) or canonical_json_bytes(receipt) != raw:
        raise SuccessorProtocolError("V5_REJECTED_HISTORY_RECEIPT_INVALID")
    experiment = repository / _EXPERIMENT_PREFIX
    try:
        return validate_v5_rejected_pre_authorization_receipt(
            receipt,
            runtime_closure_raw=(experiment / "receipts/runtime-executable-closure-v1.json").read_bytes(),
            proposal_raw=(experiment / "receipts/source-contract-proposal-v5-pr2164-semantic-gold-executable-closure-verifier-rooted-v5.json").read_bytes(),
            supersession_raw=(experiment / "receipts/source-contract-construction-proposal-v5-supersession-v4.json").read_bytes(),
            repository_root=repository,
        )
    except (OSError, SourceContractProposalError) as error:
        raise SuccessorProtocolError(str(error)) from error


def build_source_contract_proposal_v6(
    repository: Path, *, closure_raw: bytes, authority_pre_state_raw: bytes, v5_rejection_raw: bytes,
) -> dict[str, object]:
    """Build the exact decision-free v6 proposal from code-derived inventories."""
    closure = _parse_closure_v2(repository, closure_raw)
    _validate_v5_rejection(repository, v5_rejection_raw)
    current_authority = (repository / _AUTHORITY_RELATIVE).read_bytes()
    if current_authority != authority_pre_state_raw:
        raise SuccessorProtocolError("V6_AUTHORITY_PRE_STATE_MISMATCH")
    return {
        "authority_pre_state": {
            "byte_length": len(authority_pre_state_raw), "path": _AUTHORITY_RELATIVE,
            "sha256": sha256_bytes(authority_pre_state_raw),
        },
        "bound_inputs": _proposal_inputs(repository),
        "external_publication_authorized": False,
        "freeze_commit": closure["freeze_commit"],
        "generation": _GENERATION_V6,
        "local_only": True,
        "runtime_closure_v2": {
            "byte_length": len(closure_raw),
            "path": f"{_EXPERIMENT_PREFIX}/receipts/runtime-executable-closure-v2.json",
            "sha256": sha256_bytes(closure_raw),
        },
        "schema_version": "fixture-construction-proposal-v6",
        "status": "awaiting_human_construction_authorization",
        "targets": future_target_inventory_v6(),
        "v5_rejected_history": {
            "byte_length": len(v5_rejection_raw), "path": _V5_REJECTION_RELATIVE,
            "sha256": sha256_bytes(v5_rejection_raw),
        },
    }


def _supersession_v5(proposal_raw: bytes, rejection_raw: bytes) -> dict[str, object]:
    return {
        "rejected_v5": {"path": _V5_REJECTION_RELATIVE, "sha256": sha256_bytes(rejection_raw)},
        "schema_version": "source-contract-construction-proposal-v6-supersession-v5",
        "status": "v5_rejected_pre_authorization_v6_pending_human_authorization",
        "successor": {"path": f"{_PACKET_RELATIVE}/proposal.json", "sha256": sha256_bytes(proposal_raw)},
    }


def validate_source_contract_proposal_v6(
    repository: Path, packet_directory: Path, *, closure_raw: bytes,
    authority_pre_state_raw: bytes, v5_rejection_raw: bytes,
    allowed_existing_targets: set[str] | frozenset[str] = frozenset(),
) -> dict[str, object]:
    proposal, proposal_raw = _canonical_object(packet_directory / "proposal.json", "V6_PROPOSAL_NOT_CANONICAL")
    supersession, _ = _canonical_object(packet_directory / "supersession-v5.json", "V6_SUPERSESSION_NOT_CANONICAL")
    expected = build_source_contract_proposal_v6(
        repository, closure_raw=closure_raw, authority_pre_state_raw=authority_pre_state_raw,
        v5_rejection_raw=v5_rejection_raw,
    )
    if proposal != expected or supersession != _supersession_v5(proposal_raw, v5_rejection_raw):
        raise SuccessorProtocolError("V6_PROPOSAL_BINDING_MISMATCH")
    try:
        validate_future_target_occupancy_v6(repository, allowed_existing=allowed_existing_targets)
    except RuntimeClosureError as error:
        raise SuccessorProtocolError(str(error)) from error
    return proposal


def write_source_contract_proposal_packet_v6(
    repository: Path, packet_directory: Path, *, closure_raw: bytes,
    authority_pre_state_raw: bytes, v5_rejection_raw: bytes,
) -> dict[str, object]:
    """Publish proposal+supersession as one atomic no-replace rooted packet."""
    repository = repository.resolve(strict=True)
    expected_packet = repository / _PACKET_RELATIVE
    if packet_directory.resolve() != expected_packet.resolve():
        raise SuccessorProtocolError("V6_PROPOSAL_PACKET_PATH_INVALID")
    proposal = build_source_contract_proposal_v6(
        repository, closure_raw=closure_raw, authority_pre_state_raw=authority_pre_state_raw,
        v5_rejection_raw=v5_rejection_raw,
    )
    validate_future_target_occupancy_v6(repository)
    if packet_directory.exists() or packet_directory.is_symlink():
        raise SuccessorProtocolError("V6_PROPOSAL_PACKET_OCCUPIED")
    proposal_raw = canonical_json_bytes(proposal)
    supersession_raw = canonical_json_bytes(_supersession_v5(proposal_raw, v5_rejection_raw))
    packet_directory.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".proposal-v6.staging-", dir=packet_directory.parent))
    try:
        _write_exact(temporary / "proposal.json", proposal_raw)
        _write_exact(temporary / "supersession-v5.json", supersession_raw)
        validate_source_contract_proposal_v6(
            repository, temporary, closure_raw=closure_raw,
            authority_pre_state_raw=authority_pre_state_raw, v5_rejection_raw=v5_rejection_raw,
        )
        _sync_directory(temporary)
        _publish_directory_no_replace(temporary, packet_directory, "V6_PROPOSAL_PACKET_OCCUPIED")
        _sync_directory(packet_directory.parent)
    except (BundleError, RuntimeClosureError) as error:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise SuccessorProtocolError(str(error)) from error
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
    return {"proposal_sha256": sha256_bytes(proposal_raw), "supersession_sha256": sha256_bytes(supersession_raw)}


def _utc_timestamp(value: object, diagnostic: str) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise SuccessorProtocolError(diagnostic)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise SuccessorProtocolError(diagnostic) from error
    if parsed.tzinfo is None or parsed.isoformat().replace("+00:00", "Z") != value:
        raise SuccessorProtocolError(diagnostic)
    return value


def _require_human_fields(payload: Mapping[str, object], diagnostic: str) -> None:
    for field in ("reviewer", "rationale", "attestation"):
        if not isinstance(payload.get(field), str) or not str(payload[field]).strip():
            raise SuccessorProtocolError(diagnostic)
    _utc_timestamp(payload.get("decision_timestamp"), diagnostic)


def _decision_self_hash(payload: Mapping[str, object], diagnostic: str) -> None:
    projected = dict(payload)
    supplied = projected.pop("decision_sha256", None)
    if not isinstance(supplied, str) or supplied != sha256_bytes(canonical_json_bytes(projected)):
        raise SuccessorProtocolError(diagnostic)


def validate_fixture_construction_decision_v6(
    repository: Path, decision: object, packet_directory: Path, *, closure_raw: bytes,
    authority_pre_state_raw: bytes, v5_rejection_raw: bytes,
    allowed_existing_targets: set[str] | frozenset[str] | None = None,
) -> dict[str, object]:
    """Validate a human-only construction disposition against all frozen bytes."""
    if not isinstance(decision, Mapping):
        raise SuccessorProtocolError("V6_CONSTRUCTION_DECISION_INVALID")
    required = {
        "attestation", "authority_pre_state_sha256", "decision", "decision_sha256",
        "decision_timestamp", "external_publication_authorized", "local_only",
        "proposal_sha256", "rationale", "reviewer", "runtime_closure_v2_sha256",
        "schema_version", "supersession_sha256", "v5_rejected_history_sha256",
    }
    if (
        set(decision) != required
        or decision.get("schema_version") != "fixture-construction-decision-v6"
        or decision.get("decision") not in {"authorize", "reject"}
        or decision.get("local_only") is not True
        or decision.get("external_publication_authorized") is not False
    ):
        raise SuccessorProtocolError("V6_CONSTRUCTION_DECISION_INVALID")
    _require_human_fields(decision, "V6_CONSTRUCTION_DECISION_INVALID")
    _decision_self_hash(decision, "V6_CONSTRUCTION_DECISION_INVALID")
    proposal_raw = (packet_directory / "proposal.json").read_bytes()
    supersession_raw = (packet_directory / "supersession-v5.json").read_bytes()
    expected = {
        "authority_pre_state_sha256": sha256_bytes(authority_pre_state_raw),
        "proposal_sha256": sha256_bytes(proposal_raw),
        "runtime_closure_v2_sha256": sha256_bytes(closure_raw),
        "supersession_sha256": sha256_bytes(supersession_raw),
        "v5_rejected_history_sha256": sha256_bytes(v5_rejection_raw),
    }
    if any(decision.get(field) != digest for field, digest in expected.items()):
        raise SuccessorProtocolError("V6_CONSTRUCTION_DECISION_BINDING_MISMATCH")
    validate_source_contract_proposal_v6(
        repository, packet_directory, closure_raw=closure_raw,
        authority_pre_state_raw=authority_pre_state_raw, v5_rejection_raw=v5_rejection_raw,
        allowed_existing_targets=(
            {_DECISION_RELATIVE} if allowed_existing_targets is None else allowed_existing_targets
        ),
    )
    return dict(decision)


def _candidate_local_path(entry: Mapping[str, object]) -> str:
    role_names = {
        "fixture_expected": "expected.yaml",
        "fixture_gold": "gold.yaml",
        "fixture_source": "source.txt",
    }
    fixture_id, role = entry.get("fixture_id"), entry.get("role")
    if not isinstance(fixture_id, str) or role not in role_names:
        raise SuccessorProtocolError("V6_REGISTRY_ENTRY_INVALID")
    return f"raw/evaluation_fixtures/{fixture_id}/{role_names[str(role)]}"


def _candidate_source(repository: Path, entry: Mapping[str, object]) -> Path:
    path = entry.get("path")
    if not isinstance(path, str):
        raise SuccessorProtocolError("V6_REGISTRY_ENTRY_INVALID")
    if entry.get("origin") == "accepted-v3":
        return repository / _ACCEPTED_V3_RELATIVE / path
    if entry.get("origin") == "repair-v5":
        return repository / _EXPERIMENT_PREFIX / path
    raise SuccessorProtocolError("V6_REGISTRY_ENTRY_INVALID")


def construct_fixture_construction_candidate_v6(
    repository: Path, decision: object, packet_directory: Path, *, closure_raw: bytes,
    authority_pre_state_raw: bytes, v5_rejection_raw: bytes,
) -> dict[str, object]:
    """Construct the exact 11-fixture/29-file candidate after authorization."""
    validated = validate_fixture_construction_decision_v6(
        repository, decision, packet_directory, closure_raw=closure_raw,
        authority_pre_state_raw=authority_pre_state_raw, v5_rejection_raw=v5_rejection_raw,
    )
    if validated["decision"] != "authorize":
        raise SuccessorProtocolError("V6_CONSTRUCTION_NOT_AUTHORIZED")
    allowed = {_DECISION_RELATIVE}
    validate_future_target_occupancy_v6(repository, allowed_existing=allowed)
    registry, registry_raw = _validate_registry_v6(repository)
    target = repository / _CANDIDATE_RELATIVE
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{_GENERATION_V6}.staging-", dir=target.parent))
    try:
        entries = registry["file_entries"]
        assert isinstance(entries, list)
        consumed: list[dict[str, object]] = []
        for entry in entries:
            assert isinstance(entry, dict)
            raw = _candidate_source(repository, entry).read_bytes()
            local = _candidate_local_path(entry)
            if len(raw) != entry["byte_length"] or sha256_bytes(raw) != entry["sha256"]:
                raise SuccessorProtocolError("V6_REGISTRY_ENTRY_INVALID")
            _write_exact(temporary / local, raw)
            consumed.append({
                "declared_transforms": [], "derived_artifacts": [],
                "experimental_role": entry["role"], "local_bundle_path": local,
                "raw_authoritative": True, "raw_byte_length": len(raw),
                "raw_sha256": entry["sha256"], "upstream_path": entry["path"],
            })
        registry_local = "fixture-registry-pr2164-v6.json"
        _write_exact(temporary / registry_local, registry_raw)
        predecessor, _ = _canonical_object(
            repository / _ACCEPTED_V3_RELATIVE / "content-manifest-core.json",
            "V6_PREDECESSOR_INVALID",
        )
        predecessor_snapshots = predecessor.get("snapshots")
        if not isinstance(predecessor_snapshots, list) or len(predecessor_snapshots) != 1 or not isinstance(predecessor_snapshots[0], dict):
            raise SuccessorProtocolError("V6_PREDECESSOR_INVALID")
        source_snapshot = predecessor_snapshots[0]
        snapshot = {
            key: source_snapshot[key]
            for key in ("pinned_commit_sha", "pinned_tree_sha", "pull_request", "repository", "snapshot_id")
        }
        snapshot["consumed_files"] = sorted(consumed, key=lambda item: str(item["local_bundle_path"]))
        core: dict[str, object] = {"schema_version": "1", "snapshots": [snapshot]}
        registry_artifact = {
            "byte_length": len(registry_raw), "kind": "fixture_registry",
            "local_bundle_path": registry_local, "relationship": "fixture_registry",
            "sha256": sha256_bytes(registry_raw),
        }
        core["bundle_artifacts"] = [*embed_verifier_artifacts(temporary), registry_artifact]
        core_raw = canonical_json_bytes(core)
        core_sha = sha256_bytes(core_raw)
        artifacts = _raw_artifacts(core, temporary) + _bundle_artifacts(core, temporary)
        root_sha = _root_digest(core_sha, artifacts)
        _write_exact(temporary / "content-manifest-core.json", core_raw)
        final = _snapshot_manifest(core, _GENERATION_V6, core_sha, root_sha)
        final["offline_replay_proven"] = True
        without_self = dict(final)
        without_self.pop("snapshot_manifest_sha256")
        final["snapshot_manifest_sha256"] = sha256_bytes(canonical_json_bytes(without_self))
        _write_exact(temporary / "snapshot-manifest.json", canonical_json_bytes(final))
        identity = validate_fixture_candidate_v6(temporary, registry=registry, registry_raw=registry_raw)
        _run_embedded_verifier(temporary)
        _run_isolated_verifier(temporary)
        _sync_directory(temporary)
        _publish_directory_no_replace(temporary, target, "V6_CANDIDATE_TARGET_OCCUPIED")
        _sync_directory(target.parent)
        return identity
    except (BundleError, OSError) as error:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise SuccessorProtocolError(str(error)) from error
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise


def validate_fixture_candidate_v6(
    candidate: Path, *, registry: Mapping[str, object], registry_raw: bytes,
) -> dict[str, object]:
    """Verify candidate root plus exact registry-to-raw bidirectional equality."""
    try:
        identity = verify_candidate(candidate)
    except BundleError as error:
        raise SuccessorProtocolError(str(error)) from error
    if identity.get("generation") != _GENERATION_V6:
        raise SuccessorProtocolError("V6_CANDIDATE_GENERATION_INVALID")
    actual_registry = (candidate / "fixture-registry-pr2164-v6.json").read_bytes()
    if actual_registry != registry_raw:
        raise SuccessorProtocolError("V6_CANDIDATE_REGISTRY_MISMATCH")
    entries = registry.get("file_entries")
    if not isinstance(entries, list) or len(entries) != 29:
        raise SuccessorProtocolError("V6_CANDIDATE_REGISTRY_MISMATCH")
    expected: set[str] = set()
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise SuccessorProtocolError("V6_CANDIDATE_REGISTRY_MISMATCH")
        local = _candidate_local_path(entry)
        expected.add(local)
        try:
            evidence, _ = read_authoritative_file(candidate, local)
        except (FilesystemPolicyError, OSError) as error:
            raise SuccessorProtocolError("V6_CANDIDATE_RAW_MISMATCH") from error
        if evidence.byte_length != entry.get("byte_length") or evidence.sha256 != entry.get("sha256"):
            raise SuccessorProtocolError("V6_CANDIDATE_RAW_MISMATCH")
    core, _ = _canonical_object(candidate / "content-manifest-core.json", "V6_CANDIDATE_CORE_INVALID")
    actual = {
        str(item.get("local_bundle_path"))
        for snapshot in core.get("snapshots", []) if isinstance(snapshot, dict)
        for item in snapshot.get("consumed_files", []) if isinstance(item, dict)
    }
    if actual != expected:
        raise SuccessorProtocolError("V6_CANDIDATE_RAW_MISMATCH")
    final, _ = _canonical_object(candidate / "snapshot-manifest.json", "V6_CANDIDATE_MANIFEST_INVALID")
    return {
        "core_sha256": identity["manifest_sha256"], "generation": identity["generation"],
        "root_sha256": identity["root_sha256"],
        "snapshot_manifest_sha256": final["snapshot_manifest_sha256"], "status": "candidate",
    }


def build_fixture_candidate_audit_v6(
    repository: Path, candidate: Path, decision_raw: bytes, packet_directory: Path,
    closure_raw: bytes,
) -> dict[str, object]:
    registry, registry_raw = _validate_registry_v6(repository)
    identity = validate_fixture_candidate_v6(candidate, registry=registry, registry_raw=registry_raw)
    return {
        "candidate": identity,
        "construction_decision_sha256": sha256_bytes(decision_raw),
        "external_publication_authorized": False,
        "local_only": True,
        "proposal_sha256": sha256_bytes((packet_directory / "proposal.json").read_bytes()),
        "raw_file_count": 29,
        "registry_sha256": sha256_bytes(registry_raw),
        "runtime_closure_v2_sha256": sha256_bytes(closure_raw),
        "schema_version": "fixture-candidate-audit-v6",
        "status": "candidate_valid_local_acceptance_pending",
    }


def _accepted_projection_v6(candidate: Path) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    registry, registry_raw = _canonical_object(candidate / "fixture-registry-pr2164-v6.json", "V6_CANDIDATE_REGISTRY_MISMATCH")
    candidate_identity = validate_fixture_candidate_v6(candidate, registry=registry, registry_raw=registry_raw)
    core, _ = _canonical_object(candidate / "content-manifest-core.json", "V6_CANDIDATE_CORE_INVALID")
    final = {
        "accepted_publication_authorized": False,
        "content_manifest_core": core,
        "downstream_eligible": True,
        "external_publication_authorized": False,
        "generation": _GENERATION_V6,
        "manifest_sha256": candidate_identity["core_sha256"],
        "offline_replay_proven": True,
        "root_sha256": candidate_identity["root_sha256"],
        "schema_version": "1",
        "snapshots": [
            {
                **snapshot, "generation": _GENERATION_V6,
                "manifest_sha256": candidate_identity["core_sha256"],
                "root_sha256": candidate_identity["root_sha256"],
            }
            for snapshot in core["snapshots"]
        ],
        "status": "accepted",
    }
    final["snapshot_manifest_sha256"] = sha256_bytes(canonical_json_bytes(final))
    projection = {
        "core_sha256": candidate_identity["core_sha256"], "generation": _GENERATION_V6,
        "root_sha256": candidate_identity["root_sha256"],
        "snapshot_manifest_sha256": final["snapshot_manifest_sha256"],
    }
    return projection, core, final


def build_local_acceptance_request_v13(
    repository: Path, candidate: Path, audit_raw: bytes, construction_decision_raw: bytes,
    packet_directory: Path, closure_raw: bytes, authority_pre_state_raw: bytes,
) -> dict[str, object]:
    """Build a machine-only request that grants no acceptance authority."""
    try:
        audit = json.loads(audit_raw.decode("utf-8"))
        construction = json.loads(construction_decision_raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SuccessorProtocolError("LOCAL_ACCEPTANCE_REQUEST_V13_INPUT_INVALID") from error
    if (
        not isinstance(audit, dict) or canonical_json_bytes(audit) != audit_raw
        or not isinstance(construction, dict) or canonical_json_bytes(construction) != construction_decision_raw
        or construction.get("decision") != "authorize"
    ):
        raise SuccessorProtocolError("LOCAL_ACCEPTANCE_REQUEST_V13_INPUT_INVALID")
    projection, _, _ = _accepted_projection_v6(candidate)
    if audit.get("candidate") != {
        **{key: projection[key] for key in ("core_sha256", "generation", "root_sha256")},
        "snapshot_manifest_sha256": _canonical_object(candidate / "snapshot-manifest.json", "V6_CANDIDATE_MANIFEST_INVALID")[0]["snapshot_manifest_sha256"],
        "status": "candidate",
    }:
        raise SuccessorProtocolError("LOCAL_ACCEPTANCE_REQUEST_V13_AUDIT_MISMATCH")
    if (repository / _AUTHORITY_RELATIVE).read_bytes() != authority_pre_state_raw:
        raise SuccessorProtocolError("V6_AUTHORITY_PRE_STATE_MISMATCH")
    return {
        "authorization": {"external_publication_authorized": False, "local_acceptance_authorized": False},
        "authority_pre_state_sha256": sha256_bytes(authority_pre_state_raw),
        "candidate": audit["candidate"],
        "construction": {
            "audit_sha256": sha256_bytes(audit_raw),
            "decision_sha256": sha256_bytes(construction_decision_raw),
            "proposal_sha256": sha256_bytes((packet_directory / "proposal.json").read_bytes()),
            "supersession_sha256": sha256_bytes((packet_directory / "supersession-v5.json").read_bytes()),
        },
        "external_publication_authorized": False,
        "local_only": True,
        "projected_accepted": projection,
        "requested_targets": {
            "accepted_bundle": _ACCEPTED_RELATIVE,
            "historical_authority": f"{_EXPERIMENT_PREFIX}/phase2/source-authority-v13-historical.json",
            "pending_authority": f"{_EXPERIMENT_PREFIX}/phase2/source-authority-v13-pending.json",
            "transition": f"{_EXPERIMENT_PREFIX}/receipts/pending/fixture-closure-transition-v3-to-v6.json",
        },
        "runtime_closure_v2_sha256": sha256_bytes(closure_raw),
        "schema_version": "local-acceptance-request-v13",
        "status": "pending_independent_local_acceptance",
    }


def validate_local_acceptance_request_v13(
    request: object, *, candidate: Path, audit_raw: bytes, construction_decision_raw: bytes,
    packet_directory: Path, closure_raw: bytes, authority_pre_state_raw: bytes, repository: Path,
) -> dict[str, object]:
    expected = build_local_acceptance_request_v13(
        repository, candidate, audit_raw, construction_decision_raw, packet_directory,
        closure_raw, authority_pre_state_raw,
    )
    if not isinstance(request, Mapping) or dict(request) != expected:
        raise SuccessorProtocolError("LOCAL_ACCEPTANCE_REQUEST_V13_INVALID")
    return dict(request)


def validate_local_acceptance_decision_v13(
    decision: object, request: object, *, request_sha256: str,
) -> dict[str, object]:
    if not isinstance(request, Mapping) or request.get("schema_version") != "local-acceptance-request-v13":
        raise SuccessorProtocolError("LOCAL_ACCEPTANCE_REQUEST_V13_INVALID")
    if not isinstance(decision, Mapping):
        raise SuccessorProtocolError("LOCAL_ACCEPTANCE_DECISION_V13_INVALID")
    required = {
        "attestation", "candidate", "decision", "decision_sha256", "decision_timestamp",
        "external_publication_authorized", "projected_accepted", "rationale", "request_sha256",
        "reviewer", "schema_version",
    }
    if (
        set(decision) != required or decision.get("schema_version") != "local-acceptance-decision-v13"
        or decision.get("decision") not in {"accept", "reject"}
        or decision.get("external_publication_authorized") is not False
    ):
        raise SuccessorProtocolError("LOCAL_ACCEPTANCE_DECISION_V13_INVALID")
    _require_human_fields(decision, "LOCAL_ACCEPTANCE_DECISION_V13_INVALID")
    _decision_self_hash(decision, "LOCAL_ACCEPTANCE_DECISION_V13_INVALID")
    if (
        decision.get("request_sha256") != request_sha256
        or decision.get("candidate") != request.get("candidate")
        or decision.get("projected_accepted") != request.get("projected_accepted")
    ):
        raise SuccessorProtocolError("LOCAL_ACCEPTANCE_DECISION_V13_BINDING_MISMATCH")
    return dict(decision)


def accept_fixture_closure_candidate_v13(
    repository: Path, candidate: Path, request: object, decision: object,
) -> dict[str, object]:
    """Atomically publish accepted-v6 only after the second human decision."""
    request_raw = canonical_json_bytes(request)
    validated = validate_local_acceptance_decision_v13(decision, request, request_sha256=sha256_bytes(request_raw))
    if validated["decision"] != "accept":
        raise SuccessorProtocolError("LOCAL_ACCEPTANCE_V13_REJECTED")
    target = repository / _ACCEPTED_RELATIVE
    if target.exists() or target.is_symlink():
        raise SuccessorProtocolError("LOCAL_ACCEPTED_V6_TARGET_OCCUPIED")
    projection, core, final = _accepted_projection_v6(candidate)
    if projection != request.get("projected_accepted"):
        raise SuccessorProtocolError("LOCAL_ACCEPTANCE_V13_PROJECTION_MISMATCH")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{_GENERATION_V6}.accepted-staging-", dir=target.parent))
    try:
        shutil.rmtree(temporary)
        shutil.copytree(candidate, temporary)
        (temporary / "snapshot-manifest.json").unlink()
        _write_exact(temporary / "snapshot-manifest.json", canonical_json_bytes(final))
        verified = verify_accepted_bundle(temporary)
        _run_embedded_verifier(temporary)
        _run_isolated_verifier(temporary)
        _sync_directory(temporary)
        _publish_directory_no_replace(temporary, target, "LOCAL_ACCEPTED_V6_TARGET_OCCUPIED")
        _sync_directory(target.parent)
    except (BundleError, OSError) as error:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise SuccessorProtocolError(str(error)) from error
    return {**verified, "snapshot_manifest_sha256": final["snapshot_manifest_sha256"]}


def _canonical_bytes(value: Mapping[str, object]) -> bytes:
    return canonical_json_bytes(dict(value))


def build_pending_source_cutover_v13(
    repository: Path, *, authority_pre_state_raw: bytes, request_raw: bytes,
    decision_raw: bytes,
) -> dict[str, dict[str, object]]:
    accepted = repository / _ACCEPTED_RELATIVE
    try:
        accepted_identity = verify_accepted_bundle(accepted)
    except Exception as error:
        raise SuccessorProtocolError("ACCEPTED_V6_INVALID") from error
    final, _ = _canonical_object(accepted / "snapshot-manifest.json", "ACCEPTED_V6_INVALID")
    identity = {
        "core_sha256": accepted_identity["manifest_sha256"], "generation": _GENERATION_V6,
        "root_sha256": accepted_identity["root_sha256"],
        "snapshot_manifest_sha256": final["snapshot_manifest_sha256"],
    }
    pending = {
        "accepted_identity": identity,
        "authority_pre_state_sha256": sha256_bytes(authority_pre_state_raw),
        "decision_sha256": sha256_bytes(decision_raw),
        "external_publication_authorized": False,
        "fixture_count": 11,
        "generation": _GENERATION_V6,
        "local_only": True,
        "raw_file_count": 29,
        "request_sha256": sha256_bytes(request_raw),
        "schema_version": "13",
        "status": "pending_cutover_v13",
    }
    pending_raw = _canonical_bytes(pending)
    transition = {
        "accepted_identity": identity,
        "from_authority_sha256": sha256_bytes(authority_pre_state_raw),
        "pending_authority_sha256": sha256_bytes(pending_raw),
        "schema_version": "fixture-closure-transition-v3-to-v6",
        "status": "pending_non_effective",
        "to_generation": _GENERATION_V6,
    }
    transition_raw = _canonical_bytes(transition)
    readiness = {
        "cutover_effective": False,
        "external_publication_authorized": False,
        "local_only": True,
        "pending_authority_sha256": sha256_bytes(pending_raw),
        "schema_version": "source-cutover-readiness-v13",
        "status": "ready_for_atomic_activation",
        "transition_sha256": sha256_bytes(transition_raw),
    }
    return {"pending": pending, "readiness": readiness, "transition": transition}


def prepare_pending_source_cutover_v13(
    repository: Path, *, authority_pre_state_raw: bytes, request_raw: bytes, decision_raw: bytes,
) -> dict[str, object]:
    if (repository / _AUTHORITY_RELATIVE).read_bytes() != authority_pre_state_raw:
        raise SuccessorProtocolError("V6_AUTHORITY_PRE_STATE_MISMATCH")
    values = build_pending_source_cutover_v13(
        repository, authority_pre_state_raw=authority_pre_state_raw,
        request_raw=request_raw, decision_raw=decision_raw,
    )
    payloads = {
        f"{_EXPERIMENT_PREFIX}/phase2/source-authority-v13-historical.json": authority_pre_state_raw,
        f"{_EXPERIMENT_PREFIX}/phase2/source-authority-v13-pending.json": _canonical_bytes(values["pending"]),
        f"{_EXPERIMENT_PREFIX}/receipts/pending/fixture-closure-transition-v3-to-v6.json": _canonical_bytes(values["transition"]),
        f"{_EXPERIMENT_PREFIX}/receipts/pending/source-cutover-readiness-v13.json": _canonical_bytes(values["readiness"]),
    }
    try:
        write_exact_descriptor_files(repository, payloads)
    except FilesystemPolicyError as error:
        raise SuccessorProtocolError(str(error)) from error
    return {path: sha256_bytes(raw) for path, raw in sorted(payloads.items())}


def validate_pending_source_cutover_v13(
    repository: Path, *, authority_pre_state_raw: bytes, request_raw: bytes, decision_raw: bytes,
) -> dict[str, dict[str, object]]:
    expected = build_pending_source_cutover_v13(
        repository, authority_pre_state_raw=authority_pre_state_raw,
        request_raw=request_raw, decision_raw=decision_raw,
    )
    paths = {
        "pending": f"{_EXPERIMENT_PREFIX}/phase2/source-authority-v13-pending.json",
        "readiness": f"{_EXPERIMENT_PREFIX}/receipts/pending/source-cutover-readiness-v13.json",
        "transition": f"{_EXPERIMENT_PREFIX}/receipts/pending/fixture-closure-transition-v3-to-v6.json",
    }
    historical = (repository / f"{_EXPERIMENT_PREFIX}/phase2/source-authority-v13-historical.json").read_bytes()
    if historical != authority_pre_state_raw:
        raise SuccessorProtocolError("PENDING_CUTOVER_V13_HISTORICAL_MISMATCH")
    for name, relative in paths.items():
        current, _ = _canonical_object(repository / relative, "PENDING_CUTOVER_V13_INVALID")
        if current != expected[name]:
            raise SuccessorProtocolError("PENDING_CUTOVER_V13_INVALID")
    return expected


def _accepted_v6_final_authority(
    pending: Mapping[str, object], transition_raw: bytes, decision_raw: bytes,
) -> dict[str, object]:
    identity = pending.get("accepted_identity")
    if not isinstance(identity, Mapping):
        raise SuccessorProtocolError("PENDING_CUTOVER_V13_INVALID")
    return {
        "accepted_identity": dict(identity),
        "decision_sha256": sha256_bytes(decision_raw),
        "external_publication_authorized": False,
        "fixture_count": 11,
        "generation": _GENERATION_V6,
        "local_only": True,
        "manifest_sha256": identity["snapshot_manifest_sha256"],
        "raw_file_count": 29,
        "root_sha256": identity["root_sha256"],
        "schema_version": "13",
        "status": "accepted_cutover_v13",
        "transition_sha256": sha256_bytes(transition_raw),
    }


def _accepted_v6_receipts(
    *, pre_state_raw: bytes, pending_raw: bytes, transition_raw: bytes,
    readiness_raw: bytes, final_authority_raw: bytes, request_raw: bytes,
    decision_raw: bytes, accepted_identity: Mapping[str, object],
) -> dict[str, bytes]:
    revocation = {
        "from_authority_sha256": sha256_bytes(pre_state_raw),
        "pending_authority_sha256": sha256_bytes(pending_raw),
        "schema_version": "fixture-closure-revocation-v3-to-v6",
        "status": "superseded_by_accepted_v6",
        "to_authority_sha256": sha256_bytes(final_authority_raw),
        "transition_sha256": sha256_bytes(transition_raw),
    }
    audit = {
        "accepted_identity": dict(accepted_identity),
        "authority_sha256": sha256_bytes(final_authority_raw),
        "decision_sha256": sha256_bytes(decision_raw),
        "request_sha256": sha256_bytes(request_raw),
        "schema_version": "fixture-closure-acceptance-audit-v6",
        "status": "accepted_local_only",
    }
    replay = {
        "accepted_identity": dict(accepted_identity),
        "copied_isolation_replay": "passed",
        "external_publication_authorized": False,
        "schema_version": "fixture-closure-offline-replay-v6",
        "status": "verified",
    }
    revocation_raw = _canonical_bytes(revocation)
    audit_raw = _canonical_bytes(audit)
    replay_raw = _canonical_bytes(replay)
    integrity = {
        "acceptance_audit_sha256": sha256_bytes(audit_raw),
        "active_authority_sha256": sha256_bytes(final_authority_raw),
        "offline_replay_sha256": sha256_bytes(replay_raw),
        "pending_authority_sha256": sha256_bytes(pending_raw),
        "readiness_sha256": sha256_bytes(readiness_raw),
        "revocation_sha256": sha256_bytes(revocation_raw),
        "schema_version": "integrity-receipt-v14",
        "status": "accepted_v6_state_chain_verified",
        "transition_sha256": sha256_bytes(transition_raw),
    }
    return {
        f"{_EXPERIMENT_PREFIX}/receipts/fixture-closure-revocation-v3-to-v6.json": revocation_raw,
        f"{_EXPERIMENT_PREFIX}/receipts/fixture-closure-acceptance-audit-v6.json": audit_raw,
        f"{_EXPERIMENT_PREFIX}/receipts/fixture-closure-offline-replay-v6.json": replay_raw,
        f"{_EXPERIMENT_PREFIX}/receipts/integrity-receipt-v14.json": _canonical_bytes(integrity),
    }


def activate_pending_source_cutover_v13(
    repository: Path, *, authority_pre_state_raw: bytes, request_raw: bytes, decision_raw: bytes,
) -> dict[str, object]:
    """Resume safely across exact partial writes, then replace the authority head once."""
    values = validate_pending_source_cutover_v13(
        repository, authority_pre_state_raw=authority_pre_state_raw,
        request_raw=request_raw, decision_raw=decision_raw,
    )
    pending_raw = _canonical_bytes(values["pending"])
    transition_raw = _canonical_bytes(values["transition"])
    readiness_raw = _canonical_bytes(values["readiness"])
    final_authority = _accepted_v6_final_authority(values["pending"], transition_raw, decision_raw)
    final_authority_raw = _canonical_bytes(final_authority)
    identity = values["pending"]["accepted_identity"]
    assert isinstance(identity, Mapping)
    receipts = _accepted_v6_receipts(
        pre_state_raw=authority_pre_state_raw, pending_raw=pending_raw,
        transition_raw=transition_raw, readiness_raw=readiness_raw,
        final_authority_raw=final_authority_raw, request_raw=request_raw,
        decision_raw=decision_raw, accepted_identity=identity,
    )
    authority_path = repository / _AUTHORITY_RELATIVE
    current = authority_path.read_bytes()
    if current not in {authority_pre_state_raw, final_authority_raw}:
        raise SuccessorProtocolError("V13_AUTHORITY_HEAD_DIVERGED")
    try:
        write_exact_descriptor_files(repository, receipts)
        if current == authority_pre_state_raw:
            replace_descriptor_file(
                (repository / _AUTHORITY_RELATIVE).parent,
                Path(_AUTHORITY_RELATIVE).name,
                final_authority_raw,
                authority_pre_state_raw,
            )
    except FilesystemPolicyError as error:
        raise SuccessorProtocolError(str(error)) from error
    if authority_path.read_bytes() != final_authority_raw:
        raise SuccessorProtocolError("V13_AUTHORITY_ACTIVATION_FAILED")
    verify_accepted_v6_receipts(
        repository, authority_pre_state_raw=authority_pre_state_raw,
        request_raw=request_raw, decision_raw=decision_raw,
    )
    return {
        "active_authority_sha256": sha256_bytes(final_authority_raw),
        "integrity_sha256": sha256_bytes(receipts[f"{_EXPERIMENT_PREFIX}/receipts/integrity-receipt-v14.json"]),
        "status": "accepted_v6_state_chain_verified",
    }


def verify_accepted_v6_receipts(
    repository: Path, *, authority_pre_state_raw: bytes, request_raw: bytes, decision_raw: bytes,
) -> dict[str, object]:
    values = build_pending_source_cutover_v13(
        repository, authority_pre_state_raw=authority_pre_state_raw,
        request_raw=request_raw, decision_raw=decision_raw,
    )
    pending_raw = _canonical_bytes(values["pending"])
    transition_raw = _canonical_bytes(values["transition"])
    readiness_raw = _canonical_bytes(values["readiness"])
    final_authority = _accepted_v6_final_authority(values["pending"], transition_raw, decision_raw)
    final_authority_raw = _canonical_bytes(final_authority)
    identity = values["pending"]["accepted_identity"]
    assert isinstance(identity, Mapping)
    expected = _accepted_v6_receipts(
        pre_state_raw=authority_pre_state_raw, pending_raw=pending_raw,
        transition_raw=transition_raw, readiness_raw=readiness_raw,
        final_authority_raw=final_authority_raw, request_raw=request_raw,
        decision_raw=decision_raw, accepted_identity=identity,
    )
    if (repository / _AUTHORITY_RELATIVE).read_bytes() != final_authority_raw:
        raise SuccessorProtocolError("V13_AUTHORITY_HEAD_DIVERGED")
    for relative, raw in expected.items():
        if (repository / relative).read_bytes() != raw:
            raise SuccessorProtocolError("ACCEPTED_V6_RECEIPT_MISMATCH")
    return {"authority_sha256": sha256_bytes(final_authority_raw), "status": "accepted_v6_state_chain_verified"}
