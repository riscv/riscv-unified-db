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
from .filesystem import FilesystemPolicyError, read_authoritative_file, read_authoritative_files, read_closed_authoritative_tree, replace_descriptor_file, require_relative_posix_path, write_exact_descriptor_files, write_new_descriptor_file
from .receipt import (
    ReceiptError,
    build_blocked_receipt,
    build_accepted_v3_receipts,
    build_local_mvp_receipt,
    local_receipt_basis_sha256,
    render_markdown,
    validate_receipt,
    write_accepted_v3_receipts,
    write_receipt_package,
)
from .bundle import (
    accept_local_candidate,
    accept_fixture_closure_candidate,
    accept_fixture_closure_candidate_v10,
    build_local_acceptance_request_v10,
    construct_candidate,
    construct_fixture_closure_candidate,
    construct_fixture_construction_candidate_v3,
    fixture_construction_candidate_audit,
    publish_accepted,
    verify_candidate,
)
from .verify import BundleVerificationError, _load_canonical, verify_accepted_bundle, verify_accepted_bundle_material
from .canonical import canonical_json_bytes, require_byte_length, require_sha256, sha256_bytes
from .environment import default_audit_metadata, write_environment_artifacts
from .git_proof import GitProofError, audit_snapshots, validate_consumed_file_request
from .source_contract import (
    _EXPECTED_FIXTURES,
    SourceContractProposalError,
    validate_fixture_construction_decision,
    validate_fixture_construction_proposal,
    validate_fixture_construction_proposal_v4,
    validate_fixture_construction_decision_v4,
    validate_local_acceptance_decision_v10,
    validate_local_acceptance_request_v10,
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


def _load_canonical_fixture_construction_payload(path: Path, error_code: str) -> object:
    """Load one closed v3 governance object while rejecting duplicate keys."""
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise SourceContractProposalError(error_code)
            result[key] = value
        return result

    raw = path.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError, SourceContractProposalError) as error:
        raise SourceContractProposalError(error_code) from error
    if canonical_json_bytes(payload) != raw:
        raise SourceContractProposalError(error_code)
    return payload


def command_validate_fixture_construction_decision_v3(args: argparse.Namespace) -> int:
    """Validate only one closed human construction disposition for verifier-rooted-v3."""
    proposal_raw = args.proposal.read_bytes()
    proposal = _load_canonical_fixture_construction_payload(
        args.proposal, "FIXTURE_CONSTRUCTION_PROPOSAL_NOT_CANONICAL"
    )
    decision = _load_canonical_fixture_construction_payload(
        args.decision, "FIXTURE_CONSTRUCTION_DECISION_NOT_CANONICAL"
    )
    validate_fixture_construction_proposal(proposal)
    validated = validate_fixture_construction_decision(
        decision,
        proposal,
        proposal_path=args.proposal.as_posix(),
        proposal_sha256=sha256_bytes(proposal_raw),
    )
    _print_json(
        {
            "construction_authorized": validated["decision"] == "authorize",
            "decision": validated["decision"],
            "fixed_source_commit": validated["fixed_source_commit"],
            "generation": proposal["generation"],
            "proposal_sha256": sha256_bytes(proposal_raw),
            "status": "decision_valid",
        }
    )
    return 0


def _validated_v4_inputs(args: argparse.Namespace) -> dict[str, object]:
    """Read and fully validate each v4 input once for all non-authoring commands."""
    from specchoice_measurement.h1 import validate_h1_ontology_decision_v1

    proposal, proposal_raw = _load_authoritative_canonical_v4(args.proposal, "FIXTURE_CONSTRUCTION_V4_PROPOSAL_NOT_CANONICAL")
    repair_manifest, repair_manifest_raw = _load_authoritative_canonical_v4(
        args.repair_manifest, "FIXTURE_CONSTRUCTION_V4_REPAIR_MANIFEST_NOT_CANONICAL"
    )
    registry, registry_raw = _load_authoritative_canonical_v4(args.registry, "FIXTURE_CONSTRUCTION_V4_REGISTRY_NOT_CANONICAL")
    supersession, supersession_raw = _load_authoritative_canonical_v4(
        args.supersession, "FIXTURE_CONSTRUCTION_V4_SUPERSESSION_NOT_CANONICAL"
    )
    _, legacy_proposal_raw = _load_authoritative_canonical_v4(
        _experiment_root() / "receipts/source-contract-proposal-v4-pr2164-semantic-gold-closure-verifier-rooted-v3.json",
        "FIXTURE_CONSTRUCTION_V4_SUPERSESSION_INVALID",
    )
    _, legacy_manifest_raw = _load_authoritative_canonical_v4(
        _experiment_root() / "config/fixture-repairs/pr2164-semantic-gold-v2/repair-manifest.json",
        "FIXTURE_CONSTRUCTION_V4_SUPERSESSION_INVALID",
    )
    _, legacy_registry_raw = _load_authoritative_canonical_v4(
        _experiment_root() / "config/fixture-registry-pr2164-v3.json",
        "FIXTURE_CONSTRUCTION_V4_SUPERSESSION_INVALID",
    )
    previous_supersession, previous_supersession_raw = _load_authoritative_canonical_v4(
        _experiment_root() / "receipts/source-contract-construction-proposal-v4-supersession-v2.json",
        "FIXTURE_CONSTRUCTION_V4_SUPERSESSION_INVALID",
    )
    _, previous_legacy_proposal_raw = _load_authoritative_canonical_v4(
        _experiment_root() / "receipts/source-contract-proposal-v4-pr2164-semantic-gold-closure-verifier-rooted-v2.json",
        "FIXTURE_CONSTRUCTION_V4_SUPERSESSION_INVALID",
    )
    previous_legacy_manifest_raw = legacy_manifest_raw
    previous_legacy_registry_raw = legacy_registry_raw
    prior_supersession, prior_supersession_raw = _load_authoritative_canonical_v4(
        _experiment_root() / "receipts/source-contract-construction-proposal-v4-supersession-v1.json",
        "FIXTURE_CONSTRUCTION_V4_SUPERSESSION_INVALID",
    )
    _, prior_legacy_proposal_raw = _load_authoritative_canonical_v4(
        _experiment_root() / "receipts/source-contract-proposal-v4-pr2164-semantic-gold-closure-verifier-rooted-v1.json",
        "FIXTURE_CONSTRUCTION_V4_SUPERSESSION_INVALID",
    )
    _, prior_legacy_manifest_raw = _load_authoritative_canonical_v4(
        _experiment_root() / "config/fixture-repairs/pr2164-semantic-gold-v1/repair-manifest.json",
        "FIXTURE_CONSTRUCTION_V4_SUPERSESSION_INVALID",
    )
    _, prior_legacy_registry_raw = _load_authoritative_canonical_v4(
        _experiment_root() / "config/fixture-registry-pr2164-v2.json",
        "FIXTURE_CONSTRUCTION_V4_SUPERSESSION_INVALID",
    )
    ontology = validate_h1_ontology_decision_v1(
        options=_experiment_root() / "config/measurement/h1-ontology-policy-options-v1.json",
        supersession=_experiment_root() / "receipts/h1-review-route-supersession-v1.json",
        decision=args.ontology_decision,
    )
    authority, authority_raw = _load_authoritative_canonical_v4(
        args.active_authority, "FIXTURE_CONSTRUCTION_V4_AUTHORITY_INVALID"
    )
    historical, historical_raw = _load_authoritative_canonical_v4(
        args.historical_authority, "FIXTURE_CONSTRUCTION_V4_AUTHORITY_INVALID"
    )
    revocation, revocation_raw = _load_authoritative_canonical_v4(
        args.revocation, "FIXTURE_CONSTRUCTION_V4_REVOCATION_INVALID"
    )
    predecessor = _v4_predecessor_material(args.predecessor)
    _validate_pending_source_cutover_v10(
        authority, authority_raw, revocation, revocation_raw, historical, historical_raw, args.predecessor,
        accepted_material=predecessor,
    )
    repair_payloads = _v4_repair_payloads(repair_manifest, args.staging_root)
    validated = validate_fixture_construction_proposal_v4(
        proposal=proposal,
        repair_manifest=repair_manifest,
        registry=registry,
        ontology=ontology,
        predecessor_identity=predecessor["identity"],
        predecessor_manifest_sha256=predecessor["manifest_sha256"],
        predecessor_registry_sha256=predecessor["registry_sha256"],
        predecessor_files=predecessor["files"],
        predecessor_classes=predecessor["classes"],
        authority_sha256=sha256_bytes(authority_raw),
        revocation_sha256=sha256_bytes(revocation_raw),
        repair_payloads=repair_payloads,
        supersession=supersession,
        supersession_sha256=sha256_bytes(supersession_raw),
        legacy_proposal_sha256=sha256_bytes(legacy_proposal_raw),
        legacy_manifest_sha256=sha256_bytes(legacy_manifest_raw),
        legacy_registry_sha256=sha256_bytes(legacy_registry_raw),
        previous_supersession=previous_supersession,
        previous_supersession_sha256=sha256_bytes(previous_supersession_raw),
        previous_legacy_proposal_sha256=sha256_bytes(previous_legacy_proposal_raw),
        previous_legacy_manifest_sha256=sha256_bytes(previous_legacy_manifest_raw),
        previous_legacy_registry_sha256=sha256_bytes(previous_legacy_registry_raw),
        prior_supersession=prior_supersession,
        prior_supersession_sha256=sha256_bytes(prior_supersession_raw),
        prior_legacy_proposal_sha256=sha256_bytes(prior_legacy_proposal_raw),
        prior_legacy_manifest_sha256=sha256_bytes(prior_legacy_manifest_raw),
        prior_legacy_registry_sha256=sha256_bytes(prior_legacy_registry_raw),
        repository_root=_experiment_root().parents[1],
    )
    return {
        "authority_raw": authority_raw, "ontology": ontology, "proposal": validated, "proposal_raw": proposal_raw,
        "registry_raw": registry_raw, "repair_manifest": repair_manifest, "repair_manifest_raw": repair_manifest_raw,
        "repair_payloads": repair_payloads, "supersession_raw": supersession_raw,
    }


def command_validate_fixture_construction_proposal_v4(args: argparse.Namespace) -> int:
    """Validate one decision-free semantic-gold construction proposal."""
    validated = _validated_v4_inputs(args)
    _print_json({"ontology_decision_sha256": validated["ontology"]["artifact_sha256"], "proposal_sha256": sha256_bytes(validated["proposal_raw"]), "status": validated["proposal"]["status"], "valid": True})
    return 0


def command_validate_fixture_construction_decision_v4(args: argparse.Namespace) -> int:
    """Revalidate all v4 inputs before validating an externally authored decision."""
    inputs = _validated_v4_inputs(args)
    proposal = inputs["proposal"]
    proposal_raw = inputs["proposal_raw"]
    decision, _ = _load_authoritative_canonical_v4(args.decision, "FIXTURE_CONSTRUCTION_V4_DECISION_NOT_CANONICAL")
    validated = validate_fixture_construction_decision_v4(decision, proposal=proposal, proposal_sha256=sha256_bytes(proposal_raw), supersession_sha256=sha256_bytes(inputs["supersession_raw"]), ontology_sha256=str(inputs["ontology"]["artifact_sha256"]), authority_sha256=sha256_bytes(inputs["authority_raw"]))
    _print_json({"construction_authorized": validated["decision"] == "authorize", "decision": validated["decision"], "status": "decision_valid"})
    return 0


def _write_v4_no_replace(output_root: Path, payloads: dict[str, bytes]) -> None:
    """Bind the complete no-replace batch to one descriptor-rooted transaction."""
    try:
        write_exact_descriptor_files(output_root, payloads)
    except FilesystemPolicyError as error:
        if str(error) == "AUTHORITATIVE_DESTINATION_COLLISION":
            raise SourceContractProposalError("FIXTURE_CONSTRUCTION_V4_WRITE_COLLISION") from error
        raise SourceContractProposalError("FIXTURE_CONSTRUCTION_V4_WRITE_INVALID") from error


def command_write_fixture_construction_proposal_v4(args: argparse.Namespace) -> int:
    """Materialize only fully revalidated v4 staging bytes, never replacing a target."""
    inputs = _validated_v4_inputs(args)
    repairs = {
        item["target_path"]: item
        for item in inputs["repair_manifest"]["repairs"]
    }
    payloads = {
        "config/fixture-repairs/pr2164-semantic-gold-v3/POS_DIRECT_CACHE_BLOCK/gold.yaml": inputs["repair_payloads"][repairs["raw/evaluation_fixtures/POS_DIRECT_CACHE_BLOCK/gold.yaml"]["payload_path"]],
        "config/fixture-repairs/pr2164-semantic-gold-v3/POS_RECALL_COUNT_GEILEN/expected.yaml": inputs["repair_payloads"][repairs["raw/evaluation_fixtures/POS_RECALL_COUNT_GEILEN/expected.yaml"]["payload_path"]],
        "config/fixture-repairs/pr2164-semantic-gold-v3/repair-manifest.json": inputs["repair_manifest_raw"],
        "config/fixture-registry-pr2164-v4.json": inputs["registry_raw"],
        "receipts/source-contract-proposal-v4-pr2164-semantic-gold-closure-verifier-rooted-v4.json": inputs["proposal_raw"],
        "receipts/source-contract-construction-proposal-v4-supersession-v3.json": inputs["supersession_raw"],
    }
    _write_v4_no_replace(args.output_root, payloads)
    _print_json({"status": "materialized", "targets": sorted(payloads)})
    return 0


def _load_authoritative_canonical_v4(path: Path, code: str) -> tuple[dict[str, object], bytes]:
    """Read exactly one regular canonical JSON input without path reopening."""
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        value: dict[str, object] = {}
        for key, item in pairs:
            if key in value:
                raise SourceContractProposalError(code)
            value[key] = item
        return value

    try:
        _, raw = read_authoritative_file(path.parent, path.name)
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicates)
    except (FilesystemPolicyError, OSError, UnicodeDecodeError, json.JSONDecodeError, SourceContractProposalError) as error:
        raise SourceContractProposalError(code) from error
    if not isinstance(payload, dict) or canonical_json_bytes(payload) != raw:
        raise SourceContractProposalError(code)
    return payload, raw


def _v4_predecessor_material(predecessor: Path) -> dict[str, object]:
    """Hold and validate every predecessor registry leaf once before comparison."""
    try:
        held = read_closed_authoritative_tree(predecessor)
        identity = verify_accepted_bundle_material(held)

        def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
            result: dict[str, object] = {}
            for key, value in pairs:
                if key in result:
                    raise SourceContractProposalError("FIXTURE_CONSTRUCTION_V4_PREDECESSOR_INVALID")
                result[key] = value
            return result

        manifest_raw = held["snapshot-manifest.json"][1]
        registry_raw = held["fixture-registry-pr2164-v1.json"][1]
        manifest = json.loads(manifest_raw.decode("utf-8"), object_pairs_hook=reject_duplicates)
        registry = json.loads(registry_raw.decode("utf-8"), object_pairs_hook=reject_duplicates)
    except (BundleVerificationError, FilesystemPolicyError, UnicodeDecodeError, json.JSONDecodeError, SourceContractProposalError, KeyError) as error:
        raise SourceContractProposalError("FIXTURE_CONSTRUCTION_V4_PREDECESSOR_INVALID") from error
    if not isinstance(manifest, dict) or not isinstance(registry, dict) or canonical_json_bytes(manifest) != manifest_raw or canonical_json_bytes(registry) != registry_raw or any(
        manifest.get(key) != identity.get(key) for key in ("generation", "manifest_sha256", "root_sha256")
    ):
        raise SourceContractProposalError("FIXTURE_CONSTRUCTION_V4_PREDECESSOR_INVALID")
    fixtures = registry.get("fixtures")
    if not isinstance(fixtures, list):
        raise SourceContractProposalError("FIXTURE_CONSTRUCTION_V4_PREDECESSOR_INVALID")
    files: dict[str, dict[str, object]] = {}
    classes: dict[str, str] = {}
    for fixture in fixtures:
        if not isinstance(fixture, dict) or not isinstance(fixture.get("fixture_id"), str) or not isinstance(fixture.get("fixture_class"), str) or not isinstance(fixture.get("files"), list):
            raise SourceContractProposalError("FIXTURE_CONSTRUCTION_V4_PREDECESSOR_INVALID")
        fixture_id = fixture["fixture_id"]
        if fixture_id in classes:
            raise SourceContractProposalError("FIXTURE_CONSTRUCTION_V4_PREDECESSOR_INVALID")
        classes[fixture_id] = fixture["fixture_class"]
        for file in fixture["files"]:
            if not isinstance(file, dict):
                raise SourceContractProposalError("FIXTURE_CONSTRUCTION_V4_PREDECESSOR_INVALID")
            try:
                relative = require_relative_posix_path(str(file["local_bundle_path"])).as_posix()
                role = str(file["role"])
                length = require_byte_length(file["raw_byte_length"])
                digest = require_sha256(file["raw_sha256"])
                evidence, _ = held[relative]
            except (KeyError, FilesystemPolicyError, ValueError) as error:
                raise SourceContractProposalError("FIXTURE_CONSTRUCTION_V4_PREDECESSOR_INVALID") from error
            if relative in files or evidence.byte_length != length or evidence.sha256 != digest:
                raise SourceContractProposalError("FIXTURE_CONSTRUCTION_V4_PREDECESSOR_INVALID")
            files[relative] = {"byte_length": length, "fixture_id": fixture_id, "role": role, "sha256": digest}
    if len(files) != 28 or manifest.get("snapshot_manifest_sha256") is None:
        raise SourceContractProposalError("FIXTURE_CONSTRUCTION_V4_PREDECESSOR_INVALID")
    return {
        "classes": classes,
        "files": files,
        "identity": identity,
        "manifest": manifest,
        "manifest_sha256": manifest["snapshot_manifest_sha256"],
        "registry_raw": registry_raw,
        "registry_sha256": sha256_bytes(registry_raw),
    }


_V4_STAGED_REPAIR_PAYLOADS = frozenset({
    "config/fixture-repairs/pr2164-semantic-gold-v3/POS_DIRECT_CACHE_BLOCK/gold.yaml",
    "config/fixture-repairs/pr2164-semantic-gold-v3/POS_RECALL_COUNT_GEILEN/expected.yaml",
})
_V4_REUSED_REPAIR_PAYLOADS = frozenset({
    "config/fixture-repairs/pr2164-semantic-gold-v2/CAND_WARL_FIXED_LEGAL_SET/expected.yaml",
    "config/fixture-repairs/pr2164-semantic-gold-v2/NEG_EXT_GATED_PBMTE/expected.yaml",
    "config/fixture-repairs/pr2164-semantic-gold-v2/NEG_EXT_GATED_PBMTE/gold.yaml",
    "config/fixture-repairs/pr2164-semantic-gold-v2/POS_DIRECT_NUM_PMP/gold.yaml",
    "config/fixture-repairs/pr2164-semantic-gold-v2/POS_RECALL_COUNT_GEILEN/gold.yaml",
    "config/fixture-repairs/pr2164-semantic-gold-v2/POS_WARL_ASID_WIDTH/expected.yaml",
    "config/fixture-repairs/pr2164-semantic-gold-v2/POS_WARL_ASID_WIDTH/gold.yaml",
})
_V4_REPAIR_PAYLOAD_MAX_BYTES = 64 * 1024


def _v4_repair_payloads(manifest: dict[str, object], payload_root: Path) -> dict[str, bytes]:
    repairs = manifest.get("repairs")
    if not isinstance(repairs, list):
        raise SourceContractProposalError("FIXTURE_CONSTRUCTION_V4_REPAIR_MANIFEST_INVALID")
    paths: list[str] = []
    for repair in repairs:
        if not isinstance(repair, dict) or not isinstance(repair.get("payload_path"), str):
            raise SourceContractProposalError("FIXTURE_CONSTRUCTION_V4_REPAIR_MANIFEST_INVALID")
        try:
            paths.append(require_relative_posix_path(repair["payload_path"]).as_posix())
        except FilesystemPolicyError as error:
            raise SourceContractProposalError("FIXTURE_CONSTRUCTION_V4_REPAIR_MANIFEST_INVALID") from error
    expected_paths = _V4_STAGED_REPAIR_PAYLOADS | _V4_REUSED_REPAIR_PAYLOADS
    if len(paths) != len(expected_paths) or len(paths) != len(set(paths)) or set(paths) != expected_paths:
        raise SourceContractProposalError("FIXTURE_CONSTRUCTION_V4_REPAIR_MANIFEST_INVALID")
    try:
        reused = read_authoritative_files(
            _experiment_root(), sorted(_V4_REUSED_REPAIR_PAYLOADS), max_bytes=_V4_REPAIR_PAYLOAD_MAX_BYTES,
        )
        staged = read_authoritative_files(
            payload_root, sorted(_V4_STAGED_REPAIR_PAYLOADS), max_bytes=_V4_REPAIR_PAYLOAD_MAX_BYTES,
        )
    except (FilesystemPolicyError, OSError) as error:
        raise SourceContractProposalError("FIXTURE_CONSTRUCTION_V4_REPAIR_PAYLOAD_INVALID") from error
    held = reused | staged
    if any(evidence.hardlink_count != 1 for evidence, _ in held.values()):
        raise SourceContractProposalError("FIXTURE_CONSTRUCTION_V4_REPAIR_PAYLOAD_INVALID")
    return {path: held[path][1] for path in sorted(expected_paths)}


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


def command_build_fixture_construction_candidate_v3(args: argparse.Namespace) -> int:
    """Construct the exact authorized v3 candidate and its closed machine audit."""
    proposal = _load_canonical_fixture_construction_payload(
        args.proposal, "FIXTURE_CONSTRUCTION_PROPOSAL_NOT_CANONICAL"
    )
    decision = _load_canonical_fixture_construction_payload(
        args.decision, "FIXTURE_CONSTRUCTION_DECISION_NOT_CANONICAL"
    )
    result = construct_fixture_construction_candidate_v3(
        decision, proposal, args.proposal.as_posix(), args.predecessor, args.candidates_directory
    )
    audit = fixture_construction_candidate_audit(
        decision, proposal, args.proposal.as_posix(), args.decision.as_posix(),
        args.candidates_directory / result["generation"],
    )
    if args.audit.exists() or args.audit.is_symlink():
        raise ReceiptError("FIXTURE_CONSTRUCTION_AUDIT_EXISTS")
    args.audit.write_bytes(canonical_json_bytes(audit))
    _print_json({"audit_sha256": sha256_bytes(canonical_json_bytes(audit)), **result})
    return 0


def command_validate_fixture_candidate_v3(args: argparse.Namespace) -> int:
    """Verify the candidate and its exact proposal/decision-bound audit."""
    experiment = args.candidate.resolve().parents[2]
    proposal_path = experiment / "receipts/source-contract-proposal-v3-pr2164-fixture-closure-verifier-rooted-v3.json"
    decision_path = experiment / "receipts/source-contract-decision-v3-pr2164-fixture-closure-verifier-rooted-v3.json"
    proposal = _load_canonical_fixture_construction_payload(
        proposal_path, "FIXTURE_CONSTRUCTION_PROPOSAL_NOT_CANONICAL"
    )
    decision = _load_canonical_fixture_construction_payload(
        decision_path, "FIXTURE_CONSTRUCTION_DECISION_NOT_CANONICAL"
    )
    audit = _load_canonical_fixture_construction_payload(args.audit, "FIXTURE_CONSTRUCTION_AUDIT_NOT_CANONICAL")
    expected = fixture_construction_candidate_audit(
        decision, proposal,
        proposal_path.relative_to(experiment).as_posix(),
        decision_path.relative_to(experiment).as_posix(),
        args.candidate,
    )
    if audit != expected:
        raise ReceiptError("FIXTURE_CONSTRUCTION_AUDIT_MISMATCH")
    _print_json({"generation": expected["candidate"]["generation"], "status": "candidate_valid"})
    return 0


def command_publish_accepted(args: argparse.Namespace) -> int:
    """Reject accepted publication until a later, offline-proven Plan 04 gate exists."""
    decision = json.loads(args.decision.read_bytes().decode("utf-8"))
    publish_accepted(decision)
    return 0


def command_accept_fixture_closure_local(args: argparse.Namespace) -> int:
    """Accept only through the library's canonical current-v7 gate."""
    _print_json(accept_fixture_closure_candidate(
        args.candidate_directory, args.accepted_directory, args.decision
    ))
    return 0


def command_verify_accepted(args: argparse.Namespace) -> int:
    _print_json(verify_accepted_bundle(args.bundle))
    return 0


def command_validate_phase2_source_authority(args: argparse.Namespace) -> int:
    """Fail closed unless the Phase 2 pin matches the accepted v3 registry exactly."""
    authority, raw = _load_authoritative_canonical(args.authority, "PHASE2_SOURCE_AUTHORITY_INVALID")
    if args.authority_mode is not None and args.revocation is None:
        raise ReceiptError("SOURCE_AUTHORITY_REVOCATION_REQUIRED")
    revocation_raw = _optional_canonical_bytes(args.revocation) if args.revocation is not None else None
    _print_json(_validate_phase2_source_authority(authority, raw, args.bundle, revocation_raw, args.authority_mode))
    return 0


def _validate_phase2_source_authority(
    authority: dict[str, object], raw: bytes, bundle: Path, revocation_raw: bytes | None, authority_mode: str | None,
) -> dict[str, object]:
    """Validate held authority bytes without reopening any mutable authority leaf."""
    verified = verify_accepted_bundle(bundle)
    manifest, _ = _load_canonical(bundle, "snapshot-manifest.json", "SNAPSHOT_MANIFEST_INVALID")
    _, registry_raw = _load_canonical(bundle, "fixture-registry-pr2164-v1.json", "FIXTURE_REGISTRY_INVALID")
    registry_sha256 = sha256_bytes(registry_raw)
    snapshot = manifest["content_manifest_core"]["snapshots"][0]
    expected = {
        "fixture_count": 11, "generation": verified["generation"], "manifest_sha256": manifest["snapshot_manifest_sha256"],
        "pinned_commit_sha": snapshot["pinned_commit_sha"], "pinned_tree_sha": snapshot["pinned_tree_sha"],
        "raw_file_count": 28, "registry_sha256": registry_sha256, "root_sha256": verified["root_sha256"],
    }
    if authority_mode is None:
        if authority.get("schema_version") != "1" or authority.get("external_publication_authorized") is not False or authority.get("local_only") is not True or any(authority.get(key) != value for key, value in expected.items()):
            raise ReceiptError("PHASE2_SOURCE_AUTHORITY_MISMATCH")
        return {"status": "valid", **expected}
    if authority.get("schema_version") == "1":
        if authority.get("external_publication_authorized") is not False or authority.get("local_only") is not True or any(authority.get(key) != value for key, value in expected.items()):
            raise ReceiptError("PHASE2_SOURCE_AUTHORITY_MISMATCH")
        if authority_mode == "active" and revocation_raw is not None:
            raise ReceiptError("SOURCE_AUTHORITY_V2_REVOKED")
        return {"eligible": False, "status": "historical_valid", **expected} if authority_mode == "historical-inspection" else {"eligible": True, "status": "valid", **expected}
    _validate_v10_authority(authority, raw, verified, manifest, registry_sha256, revocation_raw)
    if authority_mode != "active":
        return {"eligible": False, "status": "historical_valid", **expected}
    return {"eligible": True, "status": "valid", **expected}


def _optional_canonical_bytes(path: Path) -> bytes | None:
    try:
        _, raw = _load_authoritative_canonical(path, "SOURCE_AUTHORITY_REVOCATION_INVALID")
    except ReceiptError as error:
        if str(error) == "AUTHORITATIVE_FILE_MISSING":
            return None
        raise
    return raw


def _load_authoritative_canonical(path: Path, code: str) -> tuple[dict[str, object], bytes]:
    """Read one canonical control leaf exactly once through descriptor custody."""
    try:
        _, raw = read_authoritative_file(path.parent, path.name)
        value = json.loads(raw.decode("utf-8"))
    except FilesystemPolicyError as error:
        if str(error) == "AUTHORITATIVE_FILE_MISSING":
            raise ReceiptError("AUTHORITATIVE_FILE_MISSING") from error
        raise ReceiptError(code) from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReceiptError(code) from error
    if not isinstance(value, dict) or canonical_json_bytes(value) != raw:
        raise ReceiptError(code)
    return value, raw


def _v10_identity(verified: dict[str, object], manifest: dict[str, object]) -> dict[str, object]:
    return {
        "core_sha256": verified["manifest_sha256"], "generation": verified["generation"],
        "root_sha256": verified["root_sha256"], "snapshot_manifest_sha256": manifest["snapshot_manifest_sha256"],
    }


def _validate_v10_authority(
    authority: dict[str, object], raw: bytes, verified: dict[str, object], manifest: dict[str, object],
    registry_sha256: str, revocation_raw: bytes | None,
) -> None:
    required = {
        "accepted_identity", "decision_sha256", "external_publication_authorized", "fixture_count", "generation",
        "local_only", "manifest_sha256", "pinned_commit_sha", "pinned_tree_sha", "raw_file_count",
        "registry_sha256", "request_sha256", "root_sha256", "schema_version", "status", "transition_sha256",
    }
    if set(authority) != required or authority.get("schema_version") != "10" or authority.get("status") != "pending_cutover_v10":
        raise ReceiptError("SOURCE_CUTOVER_PENDING_INVALID")
    snapshot = manifest["content_manifest_core"]["snapshots"][0]
    expected = {
        "fixture_count": 11, "generation": verified["generation"], "manifest_sha256": manifest["snapshot_manifest_sha256"],
        "pinned_commit_sha": snapshot["pinned_commit_sha"], "pinned_tree_sha": snapshot["pinned_tree_sha"],
        "raw_file_count": 28, "registry_sha256": registry_sha256, "root_sha256": verified["root_sha256"],
    }
    if authority.get("external_publication_authorized") is not False or authority.get("local_only") is not True or any(authority.get(key) != value for key, value in expected.items()) or authority.get("accepted_identity") != _v10_identity(verified, manifest):
        raise ReceiptError("SOURCE_CUTOVER_PENDING_INVALID")
    if revocation_raw is None or sha256_bytes(revocation_raw) != authority.get("transition_sha256"):
        raise ReceiptError("SOURCE_CUTOVER_REVOCATION_MISMATCH")


def command_write_local_acceptance_request_v10(args: argparse.Namespace) -> int:
    request = build_local_acceptance_request_v10(args.candidate, args.audit, args.construction_decision, args.proposal, args.active_authority)
    args.request.parent.mkdir(parents=True, exist_ok=True)
    with args.request.open("xb") as stream:
        stream.write(canonical_json_bytes(request))
        stream.flush()
        __import__("os").fsync(stream.fileno())
    _print_json({"request_sha256": sha256_bytes(args.request.read_bytes()), "status": "pending_independent_local_acceptance"})
    return 0


def command_validate_local_acceptance_decision_v10(args: argparse.Namespace) -> int:
    """Validate one canonical, hash-bound local acceptance disposition without writing state."""
    request_raw = args.request.read_bytes()
    request = _load_canonical_fixture_construction_payload(
        args.request, "LOCAL_ACCEPTANCE_REQUEST_V10_NOT_CANONICAL"
    )
    decision = _load_canonical_fixture_construction_payload(
        args.decision, "LOCAL_ACCEPTANCE_DECISION_V10_NOT_CANONICAL"
    )
    validated = validate_local_acceptance_decision_v10(
        decision, request, sha256_bytes(request_raw)
    )
    _print_json(
        {
            "decision": validated["decision"],
            "request_sha256": sha256_bytes(request_raw),
            "status": "local_acceptance_decision_valid",
        }
    )
    return 0


def command_accept_fixture_closure_local_v10(args: argparse.Namespace) -> int:
    _print_json(accept_fixture_closure_candidate_v10(args.request, args.decision, args.candidate, args.accepted_directory))
    return 0


def command_prepare_pending_source_cutover_v10(args: argparse.Namespace) -> int:
    request_raw = args.request.read_bytes()
    decision_raw = args.decision.read_bytes()
    request = json.loads(request_raw.decode("utf-8"))
    decision = json.loads(decision_raw.decode("utf-8"))
    validate_local_acceptance_decision_v10(decision, request, sha256_bytes(request_raw))
    if decision.get("decision") != "accept":
        raise ReceiptError("SOURCE_CUTOVER_REJECTED")
    verified = verify_accepted_bundle(args.accepted_bundle)
    manifest, _ = _load_canonical(args.accepted_bundle, "snapshot-manifest.json", "SNAPSHOT_MANIFEST_INVALID")
    _, registry_raw = _load_canonical(args.accepted_bundle, "fixture-registry-pr2164-v1.json", "FIXTURE_REGISTRY_INVALID")
    snapshot = manifest["content_manifest_core"]["snapshots"][0]
    base = {
        "accepted_identity": _v10_identity(verified, manifest), "decision_sha256": sha256_bytes(decision_raw),
        "external_publication_authorized": False, "fixture_count": 11, "generation": verified["generation"],
        "local_only": True, "manifest_sha256": manifest["snapshot_manifest_sha256"], "pinned_commit_sha": snapshot["pinned_commit_sha"],
        "pinned_tree_sha": snapshot["pinned_tree_sha"], "raw_file_count": 28, "registry_sha256": sha256_bytes(registry_raw),
        "request_sha256": sha256_bytes(request_raw), "root_sha256": verified["root_sha256"], "schema_version": "10", "status": "pending_cutover_v10",
    }
    old_raw = args.old_authority.read_bytes()
    transition = {
        "accepted_identity": base["accepted_identity"], "decision_sha256": base["decision_sha256"],
        "new_authority_projection_sha256": sha256_bytes(canonical_json_bytes(base)),
        "old_authority_sha256": sha256_bytes(old_raw), "request_sha256": base["request_sha256"], "schema_version": "2",
    }
    transition_raw = canonical_json_bytes(transition)
    pending = {**base, "transition_sha256": sha256_bytes(transition_raw)}
    for path, content in ((args.transition, transition_raw), (args.pending_authority, canonical_json_bytes(pending))):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(content)
            stream.flush()
            __import__("os").fsync(stream.fileno())
    _print_json({"pending_sha256": sha256_bytes(args.pending_authority.read_bytes()), "status": "pending_cutover_prepared", "transition_sha256": sha256_bytes(transition_raw)})
    return 0


def command_validate_pending_source_cutover_v10(args: argparse.Namespace) -> int:
    """Validate reviewed future bytes while proving current v2 remains active."""
    pending, pending_raw = _load_authoritative_canonical(args.pending_authority, "SOURCE_CUTOVER_PENDING_INVALID")
    transition, transition_raw = _load_authoritative_canonical(args.transition, "SOURCE_CUTOVER_TRANSITION_INVALID")
    active, active_raw = _load_authoritative_canonical(args.active_authority, "PHASE2_SOURCE_AUTHORITY_INVALID")
    _validate_pending_source_cutover_v10(
        pending, pending_raw, transition, transition_raw, active, active_raw, args.accepted_bundle,
    )
    canonical_revocation = args.active_authority.parents[1] / "receipts/fixture-closure-revocation-v2.json"
    if _optional_canonical_bytes(canonical_revocation) is not None:
        raise ReceiptError("SOURCE_CUTOVER_ALREADY_EFFECTIVE")
    _print_json(
        {
            "active_authority_sha256": sha256_bytes(active_raw),
            "eligible": False,
            "pending_authority_sha256": sha256_bytes(pending_raw),
            "status": "pending_cutover_valid_non_effective",
            "transition_sha256": sha256_bytes(transition_raw),
        }
    )
    return 0


def _validate_pending_source_cutover_v10(
    pending: dict[str, object], pending_raw: bytes, transition: dict[str, object], transition_raw: bytes,
    active: dict[str, object], active_raw: bytes, accepted_bundle: Path,
    *, accepted_material: dict[str, object] | None = None,
) -> None:
    """Validate held pending transition bytes against one held active-v2 authority."""
    if accepted_material is None:
        verified = verify_accepted_bundle(accepted_bundle)
        manifest, _ = _load_canonical(accepted_bundle, "snapshot-manifest.json", "SNAPSHOT_MANIFEST_INVALID")
        _, registry_raw = _load_canonical(accepted_bundle, "fixture-registry-pr2164-v1.json", "FIXTURE_REGISTRY_INVALID")
    else:
        verified = accepted_material["identity"]
        manifest = accepted_material["manifest"]
        registry_raw = accepted_material["registry_raw"]
        if not isinstance(verified, dict) or not isinstance(manifest, dict) or not isinstance(registry_raw, bytes):
            raise ReceiptError("SOURCE_CUTOVER_TRANSITION_INVALID")
    _validate_v10_authority(pending, pending_raw, verified, manifest, sha256_bytes(registry_raw), transition_raw)
    if set(transition) != {
        "accepted_identity", "decision_sha256", "new_authority_projection_sha256",
        "old_authority_sha256", "request_sha256", "schema_version",
    } or transition.get("schema_version") != "2":
        raise ReceiptError("SOURCE_CUTOVER_TRANSITION_INVALID")
    projection = dict(pending)
    projection.pop("transition_sha256", None)
    if (
        transition.get("accepted_identity") != pending.get("accepted_identity")
        or transition.get("decision_sha256") != pending.get("decision_sha256")
        or transition.get("request_sha256") != pending.get("request_sha256")
        or transition.get("new_authority_projection_sha256") != sha256_bytes(canonical_json_bytes(projection))
        or transition.get("old_authority_sha256") != sha256_bytes(active_raw)
    ):
        raise ReceiptError("SOURCE_CUTOVER_TRANSITION_INVALID")
    if active.get("schema_version") != "1" or active.get("external_publication_authorized") is not False or active.get("local_only") is not True:
        raise ReceiptError("PHASE2_SOURCE_AUTHORITY_MISMATCH")


_SOURCE_CUTOVER_READINESS_V10_SHA256 = "24dc6bbfc56c1fbcdc856015673b109987b2e7683465f57d6bd20225689bbdc5"


def _validate_source_cutover_readiness_v10(
    readiness: dict[str, object], readiness_raw: bytes, pending: dict[str, object], pending_raw: bytes,
    transition: dict[str, object], transition_raw: bytes, accepted_bundle: Path,
) -> None:
    """Authorize cutover only from the one reviewed, non-effective readiness receipt."""
    required = {
        "accepted_identity", "active_authority_sha256", "adapter_batch_sha256", "adapter_version",
        "cutover_effective", "external_publication_authorized", "fixture_count", "kind", "local_only",
        "pending_authority_sha256", "pending_v3_adapter_preflight_rehearsal", "preflight_status",
        "raw_file_count", "registry_sha256", "schema_version", "status", "transition_sha256", "validator_receipt",
    }
    if (
        sha256_bytes(readiness_raw) != _SOURCE_CUTOVER_READINESS_V10_SHA256
        or set(readiness) != required
        or readiness.get("schema_version") != "10"
        or readiness.get("kind") != "source_cutover_readiness_v10"
        or readiness.get("status") != "pending_v3_adapter_preflight_ready_non_effective"
        or readiness.get("cutover_effective") is not False
        or readiness.get("external_publication_authorized") is not False
        or readiness.get("local_only") is not True
        or readiness.get("pending_v3_adapter_preflight_rehearsal") is not True
        or readiness.get("preflight_status") != "valid_preflight"
        or readiness.get("adapter_version") != "pr2164-adapter-v1"
        or readiness.get("pending_authority_sha256") != sha256_bytes(pending_raw)
        or readiness.get("transition_sha256") != sha256_bytes(transition_raw)
    ):
        raise ReceiptError("SOURCE_CUTOVER_READINESS_INVALID")
    verified = verify_accepted_bundle(accepted_bundle)
    manifest, _ = _load_canonical(accepted_bundle, "snapshot-manifest.json", "SNAPSHOT_MANIFEST_INVALID")
    _, registry_raw = _load_canonical(accepted_bundle, "fixture-registry-pr2164-v1.json", "FIXTURE_REGISTRY_INVALID")
    if (
        readiness.get("accepted_identity") != _v10_identity(verified, manifest)
        or readiness.get("registry_sha256") != sha256_bytes(registry_raw)
        or readiness.get("fixture_count") != 11
        or readiness.get("raw_file_count") != 28
        or transition.get("old_authority_sha256") != readiness.get("active_authority_sha256")
        or readiness.get("validator_receipt") != {
            "active_authority_sha256": readiness["active_authority_sha256"],
            "eligible": False,
            "pending_authority_sha256": readiness["pending_authority_sha256"],
            "status": "pending_cutover_valid_non_effective",
            "transition_sha256": readiness["transition_sha256"],
        }
    ):
        raise ReceiptError("SOURCE_CUTOVER_READINESS_INVALID")


def command_activate_pending_source_cutover_v10(args: argparse.Namespace) -> int:
    readiness, readiness_raw = _load_authoritative_canonical(args.readiness, "SOURCE_CUTOVER_READINESS_INVALID")
    pending, pending_raw = _load_authoritative_canonical(args.pending_authority, "SOURCE_CUTOVER_PENDING_INVALID")
    transition, transition_raw = _load_authoritative_canonical(args.transition, "SOURCE_CUTOVER_TRANSITION_INVALID")
    active, active_raw = _load_authoritative_canonical(args.active_authority, "PHASE2_SOURCE_AUTHORITY_INVALID")
    revocation_raw = _optional_canonical_bytes(args.canonical_revocation)
    _validate_source_cutover_readiness_v10(
        readiness, readiness_raw, pending, pending_raw, transition, transition_raw, args.accepted_bundle,
    )
    if active_raw == pending_raw and revocation_raw == transition_raw:
        _validate_phase2_source_authority(active, active_raw, args.accepted_bundle, revocation_raw, "active")
        _print_json({"status": "already_activated"})
        return 0
    if active.get("schema_version") != "1":
        raise ReceiptError("SOURCE_CUTOVER_STATE_MISMATCH")
    _validate_pending_source_cutover_v10(
        pending, pending_raw, transition, transition_raw, active, active_raw, args.accepted_bundle,
    )
    if revocation_raw is None:
        try:
            write_new_descriptor_file(args.canonical_revocation.parent, args.canonical_revocation.name, transition_raw)
        except FilesystemPolicyError as error:
            raise ReceiptError("SOURCE_CUTOVER_REVOCATION_WRITE_INVALID") from error
        _, revocation_raw = _load_authoritative_canonical(args.canonical_revocation, "SOURCE_CUTOVER_REVOCATION_INVALID")
    if revocation_raw != transition_raw:
        raise ReceiptError("SOURCE_CUTOVER_STATE_MISMATCH")
    try:
        replace_descriptor_file(args.active_authority.parent, args.active_authority.name, pending_raw, active_raw)
    except FilesystemPolicyError as error:
        raise ReceiptError("SOURCE_CUTOVER_AUTHORITY_WRITE_INVALID") from error
    active, active_raw = _load_authoritative_canonical(args.active_authority, "PHASE2_SOURCE_AUTHORITY_INVALID")
    _, revocation_raw = _load_authoritative_canonical(args.canonical_revocation, "SOURCE_CUTOVER_REVOCATION_INVALID")
    if active_raw != pending_raw or revocation_raw != transition_raw:
        raise ReceiptError("SOURCE_CUTOVER_STATE_MISMATCH")
    _validate_phase2_source_authority(active, active_raw, args.accepted_bundle, revocation_raw, "active")
    _print_json({"status": "activated"})
    return 0


def command_write_accepted_v3_receipts(args: argparse.Namespace) -> int:
    """Write only the immutable accepted-v3 custody receipts; never activate the pending authority."""
    receipts = build_accepted_v3_receipts(
        args.request, args.decision, args.candidate_audit, args.pending_authority, args.transition,
        args.active_authority, args.historical_authority, args.accepted_bundle,
    )
    written = write_accepted_v3_receipts(args.receipt_directory, receipts)
    _print_json({"status": "accepted_v3_receipts_written", "written": sorted(written)})
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
    fixture_construction_decision = commands.add_parser("validate-fixture-construction-decision-v3")
    fixture_construction_decision.add_argument("--proposal", type=Path, required=True)
    fixture_construction_decision.add_argument("--decision", type=Path, required=True)
    fixture_construction_decision.set_defaults(handler=command_validate_fixture_construction_decision_v3)
    fixture_construction_proposal_v4 = commands.add_parser("validate-fixture-construction-proposal-v4")
    fixture_construction_proposal_v4.add_argument("--proposal", type=Path, required=True)
    fixture_construction_proposal_v4.add_argument("--predecessor", type=Path, required=True)
    fixture_construction_proposal_v4.add_argument("--active-authority", type=Path, required=True)
    fixture_construction_proposal_v4.add_argument("--historical-authority", type=Path, required=True)
    fixture_construction_proposal_v4.add_argument("--revocation", type=Path, required=True)
    fixture_construction_proposal_v4.add_argument("--ontology-decision", type=Path, required=True)
    fixture_construction_proposal_v4.add_argument("--repair-manifest", type=Path, required=True)
    fixture_construction_proposal_v4.add_argument("--registry", type=Path, required=True)
    fixture_construction_proposal_v4.add_argument("--supersession", type=Path, required=True)
    fixture_construction_proposal_v4.add_argument("--staging-root", type=Path, default=_experiment_root())
    fixture_construction_proposal_v4.set_defaults(handler=command_validate_fixture_construction_proposal_v4)
    fixture_construction_decision_v4 = commands.add_parser("validate-fixture-construction-decision-v4")
    for option in ("proposal", "predecessor", "active_authority", "historical_authority", "revocation", "ontology_decision", "repair_manifest", "registry", "supersession"):
        fixture_construction_decision_v4.add_argument("--" + option.replace("_", "-"), type=Path, required=True)
    fixture_construction_decision_v4.add_argument("--decision", type=Path, required=True)
    fixture_construction_decision_v4.add_argument("--staging-root", type=Path, default=_experiment_root())
    fixture_construction_decision_v4.set_defaults(handler=command_validate_fixture_construction_decision_v4)
    fixture_construction_write_v4 = commands.add_parser("write-fixture-construction-proposal-v4")
    for option in ("proposal", "predecessor", "active_authority", "historical_authority", "revocation", "ontology_decision", "repair_manifest", "registry", "supersession"):
        fixture_construction_write_v4.add_argument("--" + option.replace("_", "-"), type=Path, required=True)
    fixture_construction_write_v4.add_argument("--output-root", type=Path, required=True)
    fixture_construction_write_v4.add_argument("--staging-root", type=Path, default=_experiment_root())
    fixture_construction_write_v4.set_defaults(handler=command_write_fixture_construction_proposal_v4)
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
    fixture_construction_candidate = commands.add_parser("build-fixture-construction-candidate-v3")
    fixture_construction_candidate.add_argument("--proposal", type=Path, required=True)
    fixture_construction_candidate.add_argument("--decision", type=Path, required=True)
    fixture_construction_candidate.add_argument("--predecessor", type=Path, required=True)
    fixture_construction_candidate.add_argument("--audit", type=Path, required=True)
    fixture_construction_candidate.add_argument("--candidates-directory", type=Path, default=Path("bundles/candidates"))
    fixture_construction_candidate.set_defaults(handler=command_build_fixture_construction_candidate_v3)
    fixture_candidate_v3 = commands.add_parser("validate-fixture-candidate-v3")
    fixture_candidate_v3.add_argument("--candidate", type=Path, required=True)
    fixture_candidate_v3.add_argument("--audit", type=Path, required=True)
    fixture_candidate_v3.set_defaults(handler=command_validate_fixture_candidate_v3)
    verify_candidate_parser = commands.add_parser("verify-candidate")
    verify_candidate_parser.add_argument("candidate_directory", type=Path)
    verify_candidate_parser.set_defaults(handler=command_verify_candidate)
    verify_accepted_parser = commands.add_parser("verify-accepted")
    verify_accepted_parser.add_argument("--bundle", type=Path, required=True)
    verify_accepted_parser.set_defaults(handler=command_verify_accepted)
    fixture_accept = commands.add_parser("accept-fixture-closure-local")
    fixture_accept.add_argument("--decision", type=Path, required=True)
    fixture_accept.add_argument("--candidate-directory", type=Path, required=True)
    fixture_accept.add_argument("--accepted-directory", type=Path, default=Path("bundles/accepted"))
    fixture_accept.set_defaults(handler=command_accept_fixture_closure_local)
    authority = commands.add_parser("validate-phase2-source-authority")
    authority.add_argument("--authority", type=Path, required=True)
    authority.add_argument("--bundle", type=Path, required=True)
    authority.add_argument("--revocation", type=Path)
    authority.add_argument("--authority-mode", choices=("active", "historical-inspection"))
    authority.set_defaults(handler=command_validate_phase2_source_authority)
    request_v10 = commands.add_parser("write-local-acceptance-request-v10")
    request_v10.add_argument("--candidate", type=Path, required=True)
    request_v10.add_argument("--audit", type=Path, required=True)
    request_v10.add_argument("--construction-decision", type=Path, required=True)
    request_v10.add_argument("--proposal", type=Path, required=True)
    request_v10.add_argument("--active-authority", type=Path, required=True)
    request_v10.add_argument("--request", type=Path, required=True)
    request_v10.set_defaults(handler=command_write_local_acceptance_request_v10)
    validate_local_acceptance_v10 = commands.add_parser("validate-local-acceptance-decision-v10")
    validate_local_acceptance_v10.add_argument("--request", type=Path, required=True)
    validate_local_acceptance_v10.add_argument("--decision", type=Path, required=True)
    validate_local_acceptance_v10.set_defaults(handler=command_validate_local_acceptance_decision_v10)
    accept_v10 = commands.add_parser("accept-fixture-closure-local-v10")
    accept_v10.add_argument("--request", type=Path, required=True)
    accept_v10.add_argument("--decision", type=Path, required=True)
    accept_v10.add_argument("--candidate", type=Path, required=True)
    accept_v10.add_argument("--accepted-directory", type=Path, required=True)
    accept_v10.set_defaults(handler=command_accept_fixture_closure_local_v10)
    pending_v10 = commands.add_parser("prepare-pending-source-cutover-v10")
    pending_v10.add_argument("--request", type=Path, required=True)
    pending_v10.add_argument("--decision", type=Path, required=True)
    pending_v10.add_argument("--old-authority", type=Path, required=True)
    pending_v10.add_argument("--accepted-bundle", type=Path, required=True)
    pending_v10.add_argument("--pending-authority", type=Path, required=True)
    pending_v10.add_argument("--transition", type=Path, required=True)
    pending_v10.add_argument("--revocation", type=Path, required=True)
    pending_v10.set_defaults(handler=command_prepare_pending_source_cutover_v10)
    validate_pending_v10 = commands.add_parser("validate-pending-source-cutover-v10")
    validate_pending_v10.add_argument("--pending-authority", type=Path, required=True)
    validate_pending_v10.add_argument("--transition", type=Path, required=True)
    validate_pending_v10.add_argument("--active-authority", type=Path, required=True)
    validate_pending_v10.add_argument("--accepted-bundle", type=Path, required=True)
    validate_pending_v10.set_defaults(handler=command_validate_pending_source_cutover_v10)
    cutover_v10 = commands.add_parser("activate-pending-source-cutover-v10")
    cutover_v10.add_argument("--pending-authority", type=Path, required=True)
    cutover_v10.add_argument("--transition", type=Path, required=True)
    cutover_v10.add_argument("--readiness", type=Path, required=True)
    cutover_v10.add_argument("--canonical-revocation", type=Path, required=True)
    cutover_v10.add_argument("--active-authority", type=Path, required=True)
    cutover_v10.add_argument("--accepted-bundle", type=Path, required=True)
    cutover_v10.set_defaults(handler=command_activate_pending_source_cutover_v10)
    accepted_v3_receipts = commands.add_parser("write-accepted-v3-receipts")
    accepted_v3_receipts.add_argument("--request", type=Path, required=True)
    accepted_v3_receipts.add_argument("--decision", type=Path, required=True)
    accepted_v3_receipts.add_argument("--candidate-audit", type=Path, required=True)
    accepted_v3_receipts.add_argument("--pending-authority", type=Path, required=True)
    accepted_v3_receipts.add_argument("--transition", type=Path, required=True)
    accepted_v3_receipts.add_argument("--active-authority", type=Path, required=True)
    accepted_v3_receipts.add_argument("--historical-authority", type=Path, required=True)
    accepted_v3_receipts.add_argument("--accepted-bundle", type=Path, required=True)
    accepted_v3_receipts.add_argument("--receipt-directory", type=Path, required=True)
    accepted_v3_receipts.set_defaults(handler=command_write_accepted_v3_receipts)
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
