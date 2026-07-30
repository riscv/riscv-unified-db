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


def _default_capture_baseline() -> Path:
    return Path("baselines/phase-start-v1.json")


def _default_active_baseline() -> Path:
    """Use the latest D-15 successor when a restart has been recorded."""
    successor = Path("baselines/phase-start-v2.json")
    return successor if successor.exists() else _default_capture_baseline()


def _default_policy_override() -> Path:
    return Path("baselines/ds-store-policy-override-v1.json")


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
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.handler(args)
    except (BaselineError, ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
