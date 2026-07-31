# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Stdlib-only command boundary for phase-start evidence operations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .baseline import (
    BaselineError,
    capture_baseline,
    capture_committed_history,
    capture_live_state,
    check_boundary,
    check_current_boundary,
    committed_boundary_projection,
    committed_boundary_projection_sha256,
    create_restart_baseline,
    load_baseline,
    validate_boundary_restart,
    validate_restart_lineage,
)
from .receipt import (
    ReceiptError,
    build_blocked_receipt,
    build_local_mvp_receipt,
    local_receipt_basis_sha256,
    render_markdown,
    validate_receipt,
    write_receipt_package,
)
from .bundle import (
    accept_local_candidate,
    accept_fixture_closure_candidate,
    construct_candidate,
    construct_fixture_closure_candidate,
    publish_accepted,
    verify_candidate,
)
from .verify import verify_accepted_bundle
from .canonical import canonical_json_bytes, require_byte_length, require_sha256, sha256_bytes
from .environment import default_audit_metadata, write_environment_artifacts
from .git_proof import GitProofError, audit_snapshots, validate_consumed_file_request
from .source_contract import (
    SourceContractProposalError,
    validate_source_contract_proposal,
    require_local_accepted_generation_authorization,
    validate_local_accepted_generation_decision,
    validate_source_publication_decision,
    verify_source_contract_proposal_git,
)


def _default_capture_baseline() -> Path:
    return Path("baselines/phase-start-v1.json")


def _default_active_baseline() -> Path:
    """Return the immutable v7 fixture-closure baseline."""
    return _experiment_root() / "baselines/phase-start-v7-fixture-closure.json"


def _experiment_root() -> Path:
    """Locate the experiment from this installed module, not the caller's cwd."""
    return Path(__file__).resolve().parents[2]


def _default_active_restart_receipt() -> Path:
    """Return the restart authority bound to the active v7 baseline."""
    return _experiment_root() / "receipts/boundary-restart-v7-fixture-closure.json"


def _active_previous_baseline() -> Path:
    return _experiment_root() / "baselines/phase-start-v6-fixture-closure.json"


def _active_allowlist() -> Path:
    return _experiment_root() / "config/boundary_allowlist-v7-fixture-closure.json"


def _active_restart_lineage_paths() -> dict[str, str]:
    """Return the immutable experiment-relative paths serialized into schema-4 receipts."""
    return {
        "allowlist": "config/boundary_allowlist-v7-fixture-closure.json",
        "baseline": "baselines/phase-start-v7-fixture-closure.json",
        "incident_receipt": "receipts/boundary-restart-v7-fixture-closure.json",
        "previous_baseline": "baselines/phase-start-v6-fixture-closure.json",
    }


def _canonical_active_restart_lineage(projection: dict[str, object]) -> dict[str, object]:
    """Bind validated restart digests to portable, experiment-relative path spellings."""
    lineage_paths = _active_restart_lineage_paths()
    lineage = {
        name: {"path": path, "sha256": projection[name]["sha256"]}
        for name, path in lineage_paths.items()
    }
    lineage.update(
        {
            "reason_code": projection["reason_code"],
            "reviewed_revision": projection["reviewed_revision"],
            "scope": projection["scope"],
        }
    )
    return lineage


def _default_policy_override() -> Path:
    return Path("baselines/ds-store-policy-override-v1.json")


def _default_allowlist() -> Path:
    return Path("config/boundary_allowlist.json")


def _repository_root(start: Path) -> Path:
    """Find the repository root without invoking Git for offline-compatible reads."""
    for candidate in (start.resolve(), *start.resolve().parents):
        if (candidate / ".git").exists():
            return candidate
    raise BaselineError("REPOSITORY_ROOT_NOT_FOUND")


def _print_json(value: object) -> None:
    sys.stdout.buffer.write(canonical_json_bytes(value))


def _resolve_experiment_path(path: Path) -> Path:
    """Accept explicit paths and make default experiment-relative paths cwd-independent."""
    if path.is_absolute():
        return path
    cwd_path = Path.cwd() / path
    return cwd_path if cwd_path.exists() else _experiment_root() / path


def _canonical_environment_sha256(path: Path) -> str:
    raw = path.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReceiptError("ENVIRONMENT_DECISION_INVALID") from error
    if not isinstance(payload, dict) or canonical_json_bytes(payload) != raw:
        raise ReceiptError("ENVIRONMENT_DECISION_NOT_CANONICAL")
    return sha256_bytes(raw)


def _approved_identity(
    accepted_directory: Path, generation: str, *, candidate_relative_path: str | None = None
) -> dict[str, object]:
    """Verify a concrete accepted generation and return the decision/receipt identity."""
    if not isinstance(generation, str) or not generation or "/" in generation or "\\" in generation:
        raise ReceiptError("APPROVED_GENERATION_INVALID")
    candidate = accepted_directory / generation
    verified = verify_candidate(candidate)
    final = json.loads((candidate / "snapshot-manifest.json").read_text(encoding="utf-8"))
    if not isinstance(final, dict) or not isinstance(final.get("snapshot_manifest_sha256"), str):
        raise ReceiptError("SNAPSHOT_MANIFEST_INVALID")
    if candidate_relative_path is None:
        try:
            relative = candidate.resolve().relative_to(_experiment_root().resolve()).as_posix()
        except ValueError as error:
            raise ReceiptError("APPROVED_GENERATION_PATH_INVALID") from error
    else:
        relative = candidate_relative_path
    return {
        "candidate_relative_path": relative,
        "core_sha256": verified["manifest_sha256"],
        "generation": verified["generation"],
        "root_sha256": verified["root_sha256"],
        "snapshot_manifest_sha256": final["snapshot_manifest_sha256"],
    }


def _committed_basis_material(
    *, root: Path, baseline: Path, environment: Path, approved_generation: dict[str, object], reviewed_revision: object
) -> dict[str, object]:
    """Compute the immutable reviewer proposal before any decision/receipt is written."""
    projection = committed_boundary_projection(root, baseline, reviewed_revision=reviewed_revision)
    projection_sha256 = committed_boundary_projection_sha256(projection)
    environment_sha256 = _canonical_environment_sha256(environment)
    basis = local_receipt_basis_sha256(
        str(projection["phase_start_baseline_sha256"]),
        environment_sha256,
        approved_generation,
        list(projection["boundary_classifications"]),
        reviewed_revision=str(projection["reviewed_revision"]),
        committed_boundary_projection_sha256=projection_sha256,
    )
    return {
        "committed_boundary_projection": projection,
        "committed_boundary_projection_sha256": projection_sha256,
        "environment_decision_sha256": environment_sha256,
        "phase_start_baseline_sha256": projection["phase_start_baseline_sha256"],
        "receipt_basis_sha256": basis,
        "reviewed_revision": projection["reviewed_revision"],
        "source_identity": approved_generation,
    }


def _require_current_boundary_clean(repository: Path, baseline: Path) -> None:
    """Apply the moving, fail-closed issuance/finalization gate after frozen-basis proof."""
    current = check_current_boundary(repository, baseline)
    if current.blocking_violations:
        raise ReceiptError("LOCAL_MVP_CURRENT_BOUNDARY_BLOCKING")


def _repository_relative_posix(repository: Path, path: Path) -> str:
    """Resolve an issuance artifact to one exact repository-relative POSIX path."""
    try:
        relative = path.resolve().relative_to(repository.resolve())
    except ValueError as error:
        raise ReceiptError("LOCAL_RECEIPT_POST_REVIEW_DELTA_BLOCKING") from error
    if not relative.parts:
        raise ReceiptError("LOCAL_RECEIPT_POST_REVIEW_DELTA_BLOCKING")
    return relative.as_posix()


def _post_review_allowed_paths(args: argparse.Namespace, repository: Path) -> set[str]:
    """List the only mutable paths compatible with one active receipt issuance."""
    try:
        issuance_paths = {
            _repository_relative_posix(repository, getattr(args, name))
            for name in ("decision", "receipt", "markdown")
        }
    except (AttributeError, TypeError) as error:
        raise ReceiptError("LOCAL_RECEIPT_POST_REVIEW_DELTA_BLOCKING") from error
    receipts_root = _repository_relative_posix(repository, _experiment_root() / "receipts") + "/"
    if any(not path.startswith(receipts_root) for path in issuance_paths):
        raise ReceiptError("LOCAL_RECEIPT_POST_REVIEW_DELTA_BLOCKING")
    baseline, _ = load_baseline(_default_active_baseline())
    future_controls = baseline.get("future_control_exact_files")
    if not isinstance(future_controls, list) or not all(isinstance(path, str) for path in future_controls):
        raise ReceiptError("LOCAL_RECEIPT_POST_REVIEW_DELTA_BLOCKING")
    return issuance_paths | set(future_controls)


def _require_post_review_delta_clean(
    args: argparse.Namespace, decision: dict[str, object], repository: Path
) -> None:
    """Reject any non-control mutation after the decision's reviewed revision.

    A revision-pinned decision proves its frozen basis only at ``reviewed_revision``.
    Active issuance and finalization therefore permit after-review changes solely for
    the exact invocation artifacts and the baseline's enumerated control files.
    """
    reviewed_revision = decision.get("reviewed_revision")
    if not isinstance(reviewed_revision, str):
        raise ReceiptError("LOCAL_RECEIPT_POST_REVIEW_DELTA_BLOCKING")
    try:
        committed_paths = {
            change.path for change in capture_committed_history(repository, reviewed_revision, "HEAD")
        }
    except BaselineError as error:
        raise ReceiptError("LOCAL_RECEIPT_POST_REVIEW_DELTA_BLOCKING") from error
    changed_paths = committed_paths | set(capture_live_state(repository))
    allowed_paths = _post_review_allowed_paths(args, repository)
    blocking_paths = {
        path for path in changed_paths
        if path.rsplit("/", 1)[-1] != ".DS_Store" and path not in allowed_paths
    }
    if blocking_paths:
        raise ReceiptError("LOCAL_RECEIPT_POST_REVIEW_DELTA_BLOCKING")


def command_capture(args: argparse.Namespace) -> int:
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    baseline_hash = capture_baseline(args.baseline, payload)
    _print_json({"baseline": args.baseline.as_posix(), "phase_start_baseline_sha256": baseline_hash})
    return 0


def command_check(args: argparse.Namespace) -> int:
    root = args.root.resolve() if args.root is not None else _repository_root(Path.cwd())
    baseline = args.baseline.resolve()
    if args.policy_override.exists() and load_baseline(baseline)[0].get("schema_version") == "1":
        policy = json.loads(args.policy_override.read_text(encoding="utf-8"))
        active = policy.get("active_baseline")
        if not isinstance(active, dict) or active.get("sha256") != load_baseline(baseline)[1]:
            raise BaselineError("DS_STORE_POLICY_BASELINE_MISMATCH")
        if policy.get("decision", {}).get("code") != "DS_STORE_IGNORED_OS_METADATA":
            raise BaselineError("INVALID_DS_STORE_POLICY")
    result = check_boundary(root, baseline, reviewed_revision=args.reviewed_revision)
    _print_json({
        "baseline": {"schema_version": "1", "sha256": result.baseline_sha256},
        "blocking_violations": result.blocking_violations,
        "classifications": result.classifications,
        "history_start_commit": result.history_start_commit,
        "reviewed_revision": result.reviewed_revision,
        "unique_changed_path_count": result.unique_changed_path_count,
    })
    return 0 if result.blocking_violations == 0 else 1


def command_compute_local_mvp_receipt_basis(args: argparse.Namespace) -> int:
    """Emit a non-authoritative, revision-pinned receipt-basis proposal.

    The command is intentionally read-only: it never writes a decision, receipt, bundle,
    index entry, or other repository artifact.  Human review remains the only authority
    that can turn this proposal into a schema-3 local acceptance decision.
    """
    repository = args.root.resolve() if args.root is not None else _repository_root(Path.cwd())
    baseline = _resolve_experiment_path(args.baseline).resolve()
    environment = _resolve_experiment_path(args.environment_decision).resolve()
    accepted = _resolve_experiment_path(args.accepted_directory).resolve()
    identity = _approved_identity(
        accepted, args.approved_generation, candidate_relative_path=args.candidate_relative_path
    )
    material = _committed_basis_material(
        root=repository,
        baseline=baseline,
        environment=environment,
        approved_generation=identity,
        reviewed_revision=args.reviewed_revision,
    )
    _print_json({"proposal_only": True, "status": "proposal_only", **material})
    return 0


def command_validate_baseline(args: argparse.Namespace) -> int:
    _, baseline_hash = load_baseline(args.baseline)
    _print_json({"phase_start_baseline_sha256": baseline_hash, "status": "valid"})
    return 0


def command_restart(args: argparse.Namespace) -> int:
    remediation = {
        "removed_byte_length": require_byte_length(args.removed_byte_length),
        "removed_path": args.removed_path,
        "removed_sha256": require_sha256(args.removed_sha256),
    }
    baseline_hash, previous_hash = create_restart_baseline(
        args.previous,
        args.baseline,
        previous_reference=args.previous_reference,
        reason_code=args.reason_code,
        remediation=remediation,
    )
    _print_json(
        {
            "phase_start_baseline_sha256": baseline_hash,
            "previous_phase_start_baseline_sha256": previous_hash,
            "status": "restart_created",
        }
    )
    return 0


def command_validate_restart(args: argparse.Namespace) -> int:
    baseline_hash, previous_hash = validate_restart_lineage(args.baseline, args.previous)
    _print_json(
        {
            "phase_start_baseline_sha256": baseline_hash,
            "previous_phase_start_baseline_sha256": previous_hash,
            "status": "restart_lineage_valid",
        }
    )
    return 0


def command_validate_boundary_restart(args: argparse.Namespace) -> int:
    _print_json(validate_boundary_restart(args.baseline, args.previous_baseline, args.allowlist, args.incident_receipt))
    return 0


def command_validate_control_decision(args: argparse.Namespace) -> int:
    """Validate the reviewer approval that authorizes only GSD control updates."""
    raw = args.decision.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BaselineError("INVALID_CONTROL_DECISION_JSON") from error
    if canonical_json_bytes(payload) != raw:
        raise BaselineError("CONTROL_DECISION_NOT_CANONICAL")
    if not isinstance(payload, dict) or payload.get("schema_version") != "1":
        raise BaselineError("UNSUPPORTED_CONTROL_DECISION_SCHEMA")

    baseline, baseline_sha256 = load_baseline(args.baseline)
    del baseline
    allowlist_sha256 = sha256_bytes(args.allowlist.read_bytes())
    policy_raw = args.policy_override.read_bytes()
    try:
        policy = json.loads(policy_raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BaselineError("INVALID_DS_STORE_POLICY") from error
    if canonical_json_bytes(policy) != policy_raw or policy.get("schema_version") != "1":
        raise BaselineError("INVALID_DS_STORE_POLICY")

    expected = (
        ("baseline", args.baseline, baseline_sha256),
        ("allowlist", args.allowlist, allowlist_sha256),
        ("boundary_policy", args.policy_override, sha256_bytes(policy_raw)),
    )
    for field, path, digest in expected:
        entry = payload.get(field)
        if not isinstance(entry, dict):
            raise BaselineError("CONTROL_DECISION_BINDING_MISSING")
        if entry.get("path") != path.as_posix() or entry.get("sha256") != digest:
            raise BaselineError("CONTROL_DECISION_BINDING_MISMATCH")
        require_sha256(entry.get("sha256"))
    boundary_policy = payload["boundary_policy"]
    if boundary_policy.get("schema_version") != policy["schema_version"]:
        raise BaselineError("CONTROL_DECISION_POLICY_SCHEMA_MISMATCH")
    reviewer = payload.get("reviewer")
    if not isinstance(reviewer, dict) or reviewer.get("disposition") != "approved":
        raise BaselineError("CONTROL_DECISION_NOT_APPROVED")
    if payload.get("disputes") != []:
        raise BaselineError("CONTROL_DECISION_DISPUTES_PRESENT")
    _print_json(
        {
            "allowlist_sha256": allowlist_sha256,
            "boundary_policy_schema_version": policy["schema_version"],
            "phase_start_baseline_sha256": baseline_sha256,
            "status": "control_update_approved",
        }
    )
    return 0


def command_record_environment(args: argparse.Namespace) -> int:
    """Emit the local standalone-first decision and its separate audit evidence."""
    digest = write_environment_artifacts(
        args.decision,
        args.audit_receipt,
        audit_metadata=default_audit_metadata("python3 " + " ".join(sys.argv[1:])),
    )
    _print_json(
        {
            "audit_receipt": args.audit_receipt.as_posix(),
            "canonical_environment_decision_sha256": digest,
            "decision": args.decision.as_posix(),
            "status": "recorded",
        }
    )
    return 0


def command_audit_sources(args: argparse.Namespace) -> int:
    """Run construction-only PR proofs and emit rejected evidence when a gate fails."""
    raw = args.config.read_bytes()
    try:
        config = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GitProofError("INVALID_SOURCE_SNAPSHOTS_CONFIG") from error
    if canonical_json_bytes(config) != raw:
        raise GitProofError("SOURCE_SNAPSHOTS_NOT_CANONICAL")
    if not isinstance(config, dict) or config.get("schema_version") != "1":
        raise GitProofError("INVALID_SOURCE_SNAPSHOTS_CONFIG")
    results, failures = audit_snapshots(config, args.rejected_directory)
    _print_json(
        {"failures": failures, "results": results, "status": "rejected" if failures else "passed"}
    )
    return 1 if failures else 0


def command_validate_source_request(args: argparse.Namespace) -> int:
    """Check that request inventory cannot authorize unreviewed source extraction."""
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise GitProofError("INVALID_SOURCE_SNAPSHOTS_CONFIG")
    entries = validate_consumed_file_request(config.get("consumed_file_request"))
    _print_json({"entry_count": len(entries), "status": "reviewed"})
    return 0


def _load_canonical_source_contract_proposal(path: Path) -> object:
    raw = path.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SourceContractProposalError("INVALID_SOURCE_CONTRACT_PROPOSAL_JSON") from error
    if canonical_json_bytes(payload) != raw:
        raise SourceContractProposalError("SOURCE_CONTRACT_PROPOSAL_NOT_CANONICAL")
    return payload


def command_validate_source_contract_proposal(args: argparse.Namespace) -> int:
    """Validate a pending proposal without treating it as a source decision."""
    payload = _load_canonical_source_contract_proposal(args.proposal)
    normalized = validate_source_contract_proposal(payload)
    _print_json(
        {
            "consumed_file_count": len(normalized["consumed_files"]),
            "snapshot_count": len(normalized["snapshots"]),
            "status": "pending_reviewer_approval",
        }
    )
    return 0


def command_verify_source_contract_proposal_git(args: argparse.Namespace) -> int:
    """Locally prove a pending proposal's exact Git objects and raw bytes."""
    payload = _load_canonical_source_contract_proposal(args.proposal)
    verify_source_contract_proposal_git(payload, args.git_repository)
    _print_json({"status": "git_proof_passed"})
    return 0


def command_validate_source_decision(args: argparse.Namespace) -> int:
    """Validate a hash-bound decision and report its exact limited authority."""
    raw = args.decision.read_bytes()
    try:
        decision = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SourceContractProposalError("INVALID_SOURCE_DECISION_JSON") from error
    if canonical_json_bytes(decision) != raw:
        raise SourceContractProposalError("SOURCE_DECISION_NOT_CANONICAL")
    proposal_raw = args.proposal.read_bytes()
    proposal = _load_canonical_source_contract_proposal(args.proposal)
    validated = validate_source_publication_decision(
        decision,
        proposal,
        proposal_path=args.proposal.as_posix(),
        proposal_sha256=sha256_bytes(proposal_raw),
    )
    contract = validated["approved_contract"]
    assert isinstance(contract, dict)
    consumed_files = contract["consumed_files"]
    snapshots = contract["snapshots"]
    assert isinstance(consumed_files, list)
    assert isinstance(snapshots, list)
    authorization = validated["authorization"]
    assert isinstance(authorization, dict)
    _print_json(
        {
            "accepted_publication_authorized": authorization["accepted_publication_authorized"],
            "candidate_construction_authorized": authorization["candidate_construction_authorized"],
            "consumed_file_count": len(consumed_files),
            "proposal_sha256": sha256_bytes(proposal_raw),
            "snapshot_count": len(snapshots),
            "source_extraction_authorized": authorization["source_extraction_authorized"],
            "state": validated["state"],
        }
    )
    return 0


def command_build_candidate(args: argparse.Namespace) -> int:
    """Build only a non-accepted candidate from exact approved Git blobs."""
    decision = json.loads(args.decision.read_bytes().decode("utf-8"))
    proposal = _load_canonical_source_contract_proposal(args.proposal)
    result = construct_candidate(
        decision,
        proposal,
        args.git_repository,
        args.candidates_directory,
        fixture_registry_path=args.fixture_registry,
    )
    _print_json(result)
    return 0


def command_verify_candidate(args: argparse.Namespace) -> int:
    """Verify an existing non-accepted candidate without network access."""
    _print_json(verify_candidate(args.candidate_directory))
    return 0


def command_build_fixture_closure_candidate(args: argparse.Namespace) -> int:
    """Build the finite PR #2164 candidate from local cached Git objects only."""
    proposal = _load_canonical_source_contract_proposal(args.proposal)
    decision = json.loads(args.decision.read_bytes().decode("utf-8"))
    result = construct_fixture_closure_candidate(
        decision,
        proposal,
        args.fixture_registry,
        args.git_repository,
        args.candidates_directory,
    )
    _print_json(result)
    return 0


def command_publish_accepted(args: argparse.Namespace) -> int:
    """Reject accepted publication until a later, offline-proven Plan 04 gate exists."""
    decision = json.loads(args.decision.read_bytes().decode("utf-8"))
    publish_accepted(decision)
    return 0


def command_accept_fixture_closure_local(args: argparse.Namespace) -> int:
    """Perform the explicit local-only transition for the complete v3 candidate."""
    _print_json(accept_fixture_closure_candidate(args.candidate_directory, args.accepted_directory))
    return 0


def command_verify_accepted(args: argparse.Namespace) -> int:
    _print_json(verify_accepted_bundle(args.bundle))
    return 0


def command_validate_phase2_source_authority(args: argparse.Namespace) -> int:
    """Fail closed unless the Phase 2 pin matches the accepted v3 registry exactly."""
    raw = args.authority.read_bytes()
    authority = json.loads(raw.decode("utf-8"))
    if not isinstance(authority, dict) or canonical_json_bytes(authority) != raw:
        raise ReceiptError("PHASE2_SOURCE_AUTHORITY_NOT_CANONICAL")
    bundle = args.bundle
    verified = verify_accepted_bundle(bundle)
    manifest = json.loads((bundle / "snapshot-manifest.json").read_text(encoding="utf-8"))
    registry = bundle / "fixture-registry-pr2164-v1.json"
    registry_sha256 = sha256_bytes(registry.read_bytes())
    snapshot = manifest["content_manifest_core"]["snapshots"][0]
    expected = {
        "fixture_count": 11, "generation": verified["generation"], "manifest_sha256": manifest["snapshot_manifest_sha256"],
        "pinned_commit_sha": snapshot["pinned_commit_sha"], "pinned_tree_sha": snapshot["pinned_tree_sha"],
        "raw_file_count": 28, "registry_sha256": registry_sha256, "root_sha256": verified["root_sha256"],
    }
    if authority.get("schema_version") != "1" or authority.get("external_publication_authorized") is not False or authority.get("local_only") is not True or any(authority.get(key) != value for key, value in expected.items()):
        raise ReceiptError("PHASE2_SOURCE_AUTHORITY_MISMATCH")
    _print_json({"status": "valid", **expected})
    return 0


def command_write_fixture_closure_receipt(args: argparse.Namespace) -> int:
    """Write the v7-bound JSON-first local closure receipt for accepted v3."""
    decision_raw = args.decision.read_bytes()
    decision = json.loads(decision_raw.decode("utf-8"))
    if not isinstance(decision, dict) or canonical_json_bytes(decision) != decision_raw:
        raise ReceiptError("LOCAL_ACCEPTANCE_DECISION_NOT_CANONICAL")
    verified = verify_accepted_bundle(args.bundle)
    final = json.loads((args.bundle / "snapshot-manifest.json").read_text(encoding="utf-8"))
    repository = _repository_root(_experiment_root())
    boundary = check_boundary(repository, _default_active_baseline())
    if boundary.blocking_violations:
        raise ReceiptError("LOCAL_MVP_CURRENT_BOUNDARY_BLOCKING")
    identity = {
        "candidate_relative_path": "bundles/candidates/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v1",
        "core_sha256": verified["manifest_sha256"], "generation": verified["generation"],
        "root_sha256": verified["root_sha256"], "snapshot_manifest_sha256": final["snapshot_manifest_sha256"],
    }
    environment_sha = _canonical_environment_sha256(_experiment_root() / "receipts/environment-decision.json")
    basis = local_receipt_basis_sha256(boundary.baseline_sha256, environment_sha, identity, boundary.classifications)
    receipt = build_local_mvp_receipt(
        boundary.baseline_sha256, environment_sha, identity, boundary.classifications,
        sha256_bytes(decision_raw), basis,
    )
    result = write_receipt_package(receipt, args.receipt, args.markdown)
    _print_json(result)
    return 0


def command_write_integrity_receipt(args: argparse.Namespace) -> int:
    """Write the canonical fail-closed receipt for the currently rejected source route."""
    repository = _repository_root(Path.cwd())
    baseline = args.baseline if args.baseline.is_absolute() else Path.cwd() / args.baseline
    environment = (
        args.environment_decision
        if args.environment_decision.is_absolute()
        else Path.cwd() / args.environment_decision
    )
    rejected = args.rejected_attempt if args.rejected_attempt.is_absolute() else Path.cwd() / args.rejected_attempt
    boundary = check_boundary(repository, baseline)
    receipt = build_blocked_receipt(
        boundary.baseline_sha256,
        sha256_bytes(environment.read_bytes()),
        sha256_bytes(rejected.read_bytes()),
        boundary.classifications,
    )
    result = write_receipt_package(receipt, args.receipt, args.markdown)
    _print_json(result)
    return 0 if result["outcome"] == "pass" and result["reviewer_package_complete"] else 2


def _load_canonical_local_acceptance_decision(
    path: Path, *, allow_historical: bool = False
) -> dict[str, object]:
    raw = path.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SourceContractProposalError("INVALID_LOCAL_ACCEPTANCE_DECISION_JSON") from error
    if not isinstance(payload, dict) or canonical_json_bytes(payload) != raw:
        raise SourceContractProposalError("LOCAL_ACCEPTANCE_DECISION_NOT_CANONICAL")
    return validate_local_accepted_generation_decision(payload, allow_historical=allow_historical)


def command_accept_local_mvp(args: argparse.Namespace) -> int:
    """Create the exact immutable local accepted copy and canonical local-only receipt."""
    decision_raw = args.decision.read_bytes()
    restart_lineage = _restart_lineage_for_local_mvp_receipt(args)
    decision = _load_canonical_local_acceptance_decision(args.decision, allow_historical=True)
    material = _validate_local_mvp_receipt_basis(args, decision)
    identity = accept_local_candidate(decision, args.candidate_directory, args.accepted_directory)
    result = _write_local_mvp_receipt(args, decision, decision_raw, identity, restart_lineage, material)
    _print_json({**identity, "outcome": result["outcome"], "receipt_sha256": result["receipt_sha256"]})
    return 0 if result["outcome"] == "pass" and result["reviewer_package_complete"] else 2


def _validate_local_mvp_receipt_basis(args: argparse.Namespace, decision: dict[str, object]) -> dict[str, object]:
    """Verify the decision's frozen proposal, then apply an independent live gate."""
    if decision.get("schema_version") != "3":
        # The active v5 route never upgrades historical authority.  It remains readable
        # only so the old decision/receipt pair reaches its established basis failure.
        raise ReceiptError("LOCAL_RECEIPT_BASIS_MISMATCH")
    repository = _repository_root(Path.cwd())
    baseline = _resolve_experiment_path(args.baseline).resolve()
    environment = _resolve_experiment_path(args.environment_decision).resolve()
    approved_generation = decision["approved_generation"]
    assert isinstance(approved_generation, dict)
    material = _committed_basis_material(
        root=repository,
        baseline=baseline,
        environment=environment,
        approved_generation=approved_generation,
        reviewed_revision=decision.get("reviewed_revision"),
    )
    if decision.get("phase_start_baseline_sha256") != material["phase_start_baseline_sha256"]:
        raise ReceiptError("LOCAL_RECEIPT_BASELINE_MISMATCH")
    if decision.get("committed_boundary_projection_sha256") != material["committed_boundary_projection_sha256"]:
        raise ReceiptError("LOCAL_RECEIPT_PROJECTION_MISMATCH")
    if decision.get("reviewed_receipt_basis_sha256") != material["receipt_basis_sha256"]:
        raise ReceiptError("LOCAL_RECEIPT_BASIS_MISMATCH")
    _require_post_review_delta_clean(args, decision, repository)
    _require_current_boundary_clean(repository, baseline)
    return material


def _restart_lineage_for_local_mvp_receipt(args: argparse.Namespace) -> dict[str, object] | None:
    """Validate the selected immutable restart generation without reinterpreting legacy paths."""
    baseline = _resolve_experiment_path(args.baseline).resolve()
    restart_receipt = getattr(args, "restart_receipt", None)
    if restart_receipt is not None:
        restart_receipt = _resolve_experiment_path(restart_receipt).resolve()
    active_baseline = _default_active_baseline().resolve()
    active_restart_receipt = _default_active_restart_receipt().resolve()
    if baseline == active_baseline and restart_receipt is None:
        raise ReceiptError("RESTART_RECEIPT_REQUIRED")
    if baseline != active_baseline and restart_receipt == active_restart_receipt:
        # argparse supplies the active default; an explicit historical baseline opts into
        # schema-2 compatibility unless the caller also supplies a restart authority.
        return None
    if restart_receipt is None:
        return None
    if baseline == active_baseline:
        previous, allowlist = _active_previous_baseline(), _active_allowlist()
    elif baseline == (_experiment_root() / "baselines/phase-start-v5-gap-closure.json").resolve():
        previous = _experiment_root() / "baselines/phase-start-v2.json"
        allowlist = _experiment_root() / "config/boundary_allowlist-v5-gap-closure.json"
    else:
        raise ReceiptError("RESTART_LINEAGE_UNSUPPORTED")
    projection = validate_boundary_restart(
        baseline,
        previous,
        allowlist,
        restart_receipt,
    )
    if baseline == active_baseline:
        return _canonical_active_restart_lineage(projection)
    return {
        name: {"path": value["path"], "sha256": value["sha256"]}
        for name, value in projection.items()
        if name in {"allowlist", "baseline", "incident_receipt", "previous_baseline"}
    } | {name: projection[name] for name in ("reason_code", "reviewed_revision", "scope")}


def _write_local_mvp_receipt(
    args: argparse.Namespace,
    decision: dict[str, object],
    decision_raw: bytes,
    identity: dict[str, object],
    restart_lineage: dict[str, object] | None,
    material: dict[str, object],
) -> dict[str, object]:
    approved_generation = decision["approved_generation"]
    assert isinstance(approved_generation, dict)
    reviewed_basis = decision["reviewed_receipt_basis_sha256"]
    assert isinstance(reviewed_basis, str)
    receipt = build_local_mvp_receipt(
        str(material["phase_start_baseline_sha256"]),
        str(material["environment_decision_sha256"]),
        approved_generation,
        list(material["committed_boundary_projection"]["boundary_classifications"]),
        sha256_bytes(decision_raw),
        reviewed_basis,
        restart_lineage=restart_lineage,
        reviewed_revision=str(material["reviewed_revision"]),
        committed_boundary_projection_sha256=str(material["committed_boundary_projection_sha256"]),
    )
    result = write_receipt_package(receipt, args.receipt, args.markdown)
    return result


def command_write_local_mvp_receipt(args: argparse.Namespace) -> int:
    """Finalize review artifacts for an already-created exact local accepted copy only."""
    restart_lineage = _restart_lineage_for_local_mvp_receipt(args)
    decision_raw = args.decision.read_bytes()
    decision = _load_canonical_local_acceptance_decision(args.decision, allow_historical=True)
    material = _validate_local_mvp_receipt_basis(args, decision)
    generation = decision["approved_generation"]["generation"]
    assert isinstance(generation, str)
    identity = verify_candidate(args.accepted_directory / generation)
    final = json.loads((args.accepted_directory / generation / "snapshot-manifest.json").read_text(encoding="utf-8"))
    if not isinstance(final, dict) or not isinstance(final.get("snapshot_manifest_sha256"), str):
        raise ReceiptError("SNAPSHOT_MANIFEST_INVALID")
    require_local_accepted_generation_authorization(
        decision, identity, final["snapshot_manifest_sha256"]
    )
    result = _write_local_mvp_receipt(args, decision, decision_raw, identity, restart_lineage, material)
    _print_json({**identity, "outcome": result["outcome"], "receipt_sha256": result["receipt_sha256"]})
    return 0 if result["outcome"] == "pass" and result["reviewer_package_complete"] else 2


def command_finalize_review(args: argparse.Namespace) -> int:
    """Finalize only the current, revision-pinned local receipt and decision schemas."""
    receipt = validate_receipt(args.receipt)
    if receipt.get("schema_version") != "4":
        raise ReceiptError("HISTORICAL_RECEIPT_NOT_FINALIZABLE")
    experiment_root = _experiment_root()
    expected_paths = _active_restart_lineage_paths()
    lineage = receipt["restart_lineage"]
    assert isinstance(lineage, dict)
    if any(lineage[name].get("path") != path for name, path in expected_paths.items()):
        raise ReceiptError("RESTART_LINEAGE_PROJECTION_MISMATCH")
    projection = validate_boundary_restart(
        experiment_root / expected_paths["baseline"],
        experiment_root / expected_paths["previous_baseline"],
        experiment_root / expected_paths["allowlist"],
        experiment_root / expected_paths["incident_receipt"],
    )
    expected_lineage = _canonical_active_restart_lineage(projection)
    if lineage != expected_lineage:
        raise ReceiptError("RESTART_LINEAGE_PROJECTION_MISMATCH")
    repository = _repository_root(experiment_root)
    if not args.decision.is_file():
        raise ReceiptError("REVIEW_DECISION_MISSING")
    decision_raw = args.decision.read_bytes()
    decision = json.loads(decision_raw.decode("utf-8"))
    source = receipt["source_identity"]
    if source["kind"] != "local_accepted_generation":
        raise ReceiptError("HISTORICAL_RECEIPT_NOT_FINALIZABLE")
    if canonical_json_bytes(decision) != decision_raw:
        raise ReceiptError("LOCAL_ACCEPTANCE_DECISION_NOT_CANONICAL")
    try:
        local_decision = validate_local_accepted_generation_decision(decision, allow_historical=True)
    except SourceContractProposalError as error:
        raise ReceiptError(str(error)) from error
    if local_decision.get("schema_version") != "3":
        raise ReceiptError("HISTORICAL_RECEIPT_NOT_FINALIZABLE")
    _require_post_review_delta_clean(args, local_decision, repository)
    _require_current_boundary_clean(repository, experiment_root / expected_paths["baseline"])
    if source.get("external_publication_authorized") is not False:
        raise ReceiptError("EXTERNAL_PUBLICATION_NOT_AUTHORIZED")
    if receipt.get("reviewer_decision_sha256") != sha256_bytes(decision_raw):
        raise ReceiptError("REVIEW_DECISION_HASH_MISMATCH")
    if source.get("generation") != local_decision["approved_generation"]["generation"]:
        raise ReceiptError("REVIEW_DECISION_IDENTITY_MISMATCH")
    if receipt.get("receipt_basis_sha256") != local_decision["reviewed_receipt_basis_sha256"]:
        raise ReceiptError("LOCAL_RECEIPT_BASIS_MISMATCH")
    material = _committed_basis_material(
        root=repository,
        baseline=experiment_root / "baselines/phase-start-v7-fixture-closure.json",
        environment=experiment_root / "receipts/environment-decision.json",
        approved_generation=local_decision["approved_generation"],
        reviewed_revision=local_decision.get("reviewed_revision"),
    )
    if receipt.get("reviewed_revision") != material["reviewed_revision"]:
        raise ReceiptError("LOCAL_REVIEWED_REVISION_MISMATCH")
    if receipt.get("phase_start_baseline_sha256") != material["phase_start_baseline_sha256"]:
        raise ReceiptError("LOCAL_RECEIPT_BASELINE_MISMATCH")
    if receipt.get("committed_boundary_projection_sha256") != material["committed_boundary_projection_sha256"]:
        raise ReceiptError("LOCAL_RECEIPT_PROJECTION_MISMATCH")
    if receipt.get("receipt_basis_sha256") != material["receipt_basis_sha256"]:
        raise ReceiptError("LOCAL_RECEIPT_BASIS_MISMATCH")
    if receipt["outcome"] != "pass" or not receipt["reviewer_package_complete"]:
        raise ReceiptError("REVIEW_MACHINE_GATE_NOT_ELIGIBLE")
    if args.markdown.read_text(encoding="utf-8") != render_markdown(receipt):
        raise ReceiptError("REVIEW_MARKDOWN_MISMATCH")
    _print_json({"outcome": "pass", "receipt_sha256": receipt["receipt_sha256"]})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="specchoice-evidence")
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("capture-baseline")
    capture.add_argument("--input", type=Path, required=True)
    capture.add_argument("--baseline", type=Path, default=_default_capture_baseline())
    capture.set_defaults(handler=command_capture)
    boundary = commands.add_parser("check-boundary")
    boundary.add_argument("--root", type=Path)
    boundary.add_argument("--baseline", type=Path, default=_default_active_baseline())
    boundary.add_argument("--policy-override", type=Path, default=_default_policy_override())
    boundary.add_argument("--reviewed-revision", default="HEAD")
    boundary.set_defaults(handler=command_check)
    basis = commands.add_parser("compute-local-mvp-receipt-basis")
    basis.add_argument("--root", type=Path)
    basis.add_argument("--baseline", type=Path, default=_default_active_baseline())
    basis.add_argument("--environment-decision", type=Path, required=True)
    basis.add_argument("--accepted-directory", type=Path, required=True)
    basis.add_argument("--approved-generation", required=True)
    basis.add_argument("--candidate-relative-path")
    basis.add_argument("--reviewed-revision", required=True)
    basis.set_defaults(handler=command_compute_local_mvp_receipt_basis)
    validate = commands.add_parser("validate-baseline")
    validate.add_argument("--baseline", type=Path, default=_default_active_baseline())
    validate.set_defaults(handler=command_validate_baseline)
    restart = commands.add_parser("restart-baseline")
    restart.add_argument("--previous", type=Path, required=True)
    restart.add_argument("--previous-reference", required=True)
    restart.add_argument("--baseline", type=Path, required=True)
    restart.add_argument("--reason-code", required=True)
    restart.add_argument("--removed-path", required=True)
    restart.add_argument("--removed-byte-length", type=int, required=True)
    restart.add_argument("--removed-sha256", required=True)
    restart.set_defaults(handler=command_restart)
    validate_restart = commands.add_parser("validate-restart-lineage")
    validate_restart.add_argument("--previous", type=Path, required=True)
    validate_restart.add_argument("--baseline", type=Path, required=True)
    validate_restart.set_defaults(handler=command_validate_restart)
    boundary_restart = commands.add_parser("validate-boundary-restart")
    boundary_restart.add_argument("--baseline", type=Path, required=True)
    boundary_restart.add_argument("--previous-baseline", type=Path, required=True)
    boundary_restart.add_argument("--allowlist", type=Path, required=True)
    boundary_restart.add_argument("--incident-receipt", type=Path, required=True)
    boundary_restart.set_defaults(handler=command_validate_boundary_restart)
    control_decision = commands.add_parser("validate-control-decision")
    control_decision.add_argument("decision", type=Path)
    control_decision.add_argument("--baseline", type=Path, default=_default_active_baseline())
    control_decision.add_argument("--allowlist", type=Path, default=_default_allowlist())
    control_decision.add_argument("--policy-override", type=Path, default=_default_policy_override())
    control_decision.set_defaults(handler=command_validate_control_decision)
    environment = commands.add_parser("record-environment")
    environment.add_argument("--decision", type=Path, default=Path("receipts/environment-decision.json"))
    environment.add_argument(
        "--audit-receipt",
        type=Path,
        default=Path("audit/environment/environment-receipt-phase-start-001.json"),
    )
    environment.set_defaults(handler=command_record_environment)
    audit_sources = commands.add_parser("audit-sources")
    audit_sources.add_argument(
        "--config", type=Path, default=Path("config/source_snapshots.json")
    )
    audit_sources.add_argument("--rejected-directory", type=Path, default=Path("bundles/rejected"))
    audit_sources.set_defaults(handler=command_audit_sources)
    source_request = commands.add_parser("validate-source-request")
    source_request.add_argument(
        "--config", type=Path, default=Path("config/source_snapshots.json")
    )
    source_request.set_defaults(handler=command_validate_source_request)
    proposal = commands.add_parser("validate-source-contract-proposal")
    proposal.add_argument(
        "proposal",
        type=Path,
        nargs="?",
        default=Path("receipts/source-contract-correction-proposal-v2.json"),
    )
    proposal.set_defaults(handler=command_validate_source_contract_proposal)
    proposal_git = commands.add_parser("verify-source-contract-proposal-git")
    proposal_git.add_argument(
        "proposal",
        type=Path,
        nargs="?",
        default=Path("receipts/source-contract-correction-proposal-v2.json"),
    )
    proposal_git.add_argument("--git-repository", type=Path, required=True)
    proposal_git.set_defaults(handler=command_verify_source_contract_proposal_git)
    source_decision = commands.add_parser("validate-source-decision")
    source_decision.add_argument(
        "decision", type=Path, nargs="?", default=Path("receipts/source-publication-decision.json")
    )
    source_decision.add_argument(
        "--proposal",
        type=Path,
        default=Path("receipts/source-contract-correction-proposal-v2.json"),
    )
    source_decision.set_defaults(handler=command_validate_source_decision)
    candidate = commands.add_parser("build-candidate")
    candidate.add_argument("--decision", type=Path, default=Path("receipts/source-publication-decision.json"))
    candidate.add_argument("--proposal", type=Path, default=Path("receipts/source-contract-correction-proposal-v2.json"))
    candidate.add_argument("--git-repository", type=Path, required=True)
    candidate.add_argument("--candidates-directory", type=Path, default=Path("bundles/candidates"))
    candidate.add_argument("--fixture-registry", type=Path)
    candidate.set_defaults(handler=command_build_candidate)
    fixture_candidate = commands.add_parser("build-fixture-closure-candidate")
    fixture_candidate.add_argument("--decision", type=Path, required=True)
    fixture_candidate.add_argument("--proposal", type=Path, required=True)
    fixture_candidate.add_argument("--fixture-registry", type=Path, required=True)
    fixture_candidate.add_argument("--git-repository", type=Path, required=True)
    fixture_candidate.add_argument("--candidates-directory", type=Path, default=Path("bundles/candidates"))
    fixture_candidate.set_defaults(handler=command_build_fixture_closure_candidate)
    verify_candidate_parser = commands.add_parser("verify-candidate")
    verify_candidate_parser.add_argument("candidate_directory", type=Path)
    verify_candidate_parser.set_defaults(handler=command_verify_candidate)
    verify_accepted_parser = commands.add_parser("verify-accepted")
    verify_accepted_parser.add_argument("--bundle", type=Path, required=True)
    verify_accepted_parser.set_defaults(handler=command_verify_accepted)
    fixture_accept = commands.add_parser("accept-fixture-closure-local")
    fixture_accept.add_argument("--candidate-directory", type=Path, required=True)
    fixture_accept.add_argument("--accepted-directory", type=Path, default=Path("bundles/accepted"))
    fixture_accept.set_defaults(handler=command_accept_fixture_closure_local)
    authority = commands.add_parser("validate-phase2-source-authority")
    authority.add_argument("--authority", type=Path, required=True)
    authority.add_argument("--bundle", type=Path, required=True)
    authority.set_defaults(handler=command_validate_phase2_source_authority)
    closure_receipt = commands.add_parser("write-fixture-closure-receipt")
    closure_receipt.add_argument("--decision", type=Path, required=True)
    closure_receipt.add_argument("--bundle", type=Path, required=True)
    closure_receipt.add_argument("--receipt", type=Path, required=True)
    closure_receipt.add_argument("--markdown", type=Path, required=True)
    closure_receipt.set_defaults(handler=command_write_fixture_closure_receipt)
    publish = commands.add_parser("publish-accepted")
    publish.add_argument("--decision", type=Path, default=Path("receipts/source-publication-decision.json"))
    publish.set_defaults(handler=command_publish_accepted)
    local_accept = commands.add_parser("accept-local-mvp")
    local_accept.add_argument("--decision", type=Path, required=True)
    local_accept.add_argument("--candidate-directory", type=Path, required=True)
    local_accept.add_argument("--accepted-directory", type=Path, default=Path("bundles/accepted"))
    local_accept.add_argument("--baseline", type=Path, default=_default_active_baseline())
    local_accept.add_argument("--environment-decision", type=Path, default=Path("receipts/environment-decision.json"))
    local_accept.add_argument("--receipt", type=Path, default=Path("receipts/integrity-receipt.json"))
    local_accept.add_argument("--markdown", type=Path, default=Path("receipts/integrity-receipt.md"))
    local_accept.add_argument("--restart-receipt", type=Path, default=_default_active_restart_receipt())
    local_accept.set_defaults(handler=command_accept_local_mvp)
    local_receipt = commands.add_parser("write-local-mvp-receipt")
    local_receipt.add_argument("--decision", type=Path, required=True)
    local_receipt.add_argument("--accepted-directory", type=Path, default=Path("bundles/accepted"))
    local_receipt.add_argument("--baseline", type=Path, default=_default_active_baseline())
    local_receipt.add_argument("--environment-decision", type=Path, default=Path("receipts/environment-decision.json"))
    local_receipt.add_argument("--receipt", type=Path, default=Path("receipts/integrity-receipt.json"))
    local_receipt.add_argument("--markdown", type=Path, default=Path("receipts/integrity-receipt.md"))
    local_receipt.add_argument("--restart-receipt", type=Path, default=_default_active_restart_receipt())
    local_receipt.set_defaults(handler=command_write_local_mvp_receipt)
    integrity = commands.add_parser("write-integrity-receipt")
    integrity.add_argument("--baseline", type=Path, default=_default_active_baseline())
    integrity.add_argument("--environment-decision", type=Path, default=Path("receipts/environment-decision.json"))
    integrity.add_argument("--rejected-attempt", type=Path, default=Path("bundles/rejected/pr-2192-current-head/attempt-receipt.json"))
    integrity.add_argument("--receipt", type=Path, default=Path("receipts/integrity-receipt.json"))
    integrity.add_argument("--markdown", type=Path, default=Path("receipts/integrity-receipt.md"))
    integrity.set_defaults(handler=command_write_integrity_receipt)
    finalize = commands.add_parser("finalize-review")
    finalize.add_argument("--decision", type=Path, required=True)
    finalize.add_argument("--receipt", type=Path, required=True)
    finalize.add_argument("--markdown", type=Path, required=True)
    finalize.set_defaults(handler=command_finalize_review)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.handler(args)
    except (BaselineError, GitProofError, SourceContractProposalError, ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
