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
    check_boundary,
    create_restart_baseline,
    load_baseline,
    validate_restart_lineage,
)
from .canonical import canonical_json_bytes, require_byte_length, require_sha256, sha256_bytes
from .environment import default_audit_metadata, write_environment_artifacts
from .git_proof import GitProofError, audit_snapshots, validate_consumed_file_request


def _default_capture_baseline() -> Path:
    return Path("baselines/phase-start-v1.json")


def _default_active_baseline() -> Path:
    """Use the latest D-15 successor when a restart has been recorded."""
    successor = Path("baselines/phase-start-v2.json")
    return successor if successor.exists() else _default_capture_baseline()


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


def command_capture(args: argparse.Namespace) -> int:
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    baseline_hash = capture_baseline(args.baseline, payload)
    _print_json({"baseline": args.baseline.as_posix(), "phase_start_baseline_sha256": baseline_hash})
    return 0


def command_check(args: argparse.Namespace) -> int:
    root = args.root.resolve() if args.root is not None else _repository_root(Path.cwd())
    baseline = args.baseline.resolve()
    if args.policy_override.exists():
        policy = json.loads(args.policy_override.read_text(encoding="utf-8"))
        active = policy.get("active_baseline")
        if not isinstance(active, dict) or active.get("sha256") != load_baseline(baseline)[1]:
            raise BaselineError("DS_STORE_POLICY_BASELINE_MISMATCH")
        if policy.get("decision", {}).get("code") != "DS_STORE_IGNORED_OS_METADATA":
            raise BaselineError("INVALID_DS_STORE_POLICY")
    result = check_boundary(root, baseline)
    _print_json({
        "baseline": {"schema_version": "1", "sha256": result.baseline_sha256},
        "blocking_violations": result.blocking_violations,
        "classifications": result.classifications,
    })
    return 0 if result.blocking_violations == 0 else 1


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
    boundary.set_defaults(handler=command_check)
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
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.handler(args)
    except (BaselineError, GitProofError, ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
