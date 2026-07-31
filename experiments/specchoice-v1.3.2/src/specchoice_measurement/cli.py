# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Command boundary for deterministic measurement artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from specchoice_evidence.canonical import canonical_json_bytes

from .adapter import AdapterError, build_pr2164_adapter_batch
from .attempts import AttemptError, run_measurement_attempt, validate_measurement_attempt
from .preflight import preflight_prediction_batch
from .scoring import score_prediction_batch


def command_adapt_pr2164(args: argparse.Namespace) -> int:
    if args.output.exists():
        raise AdapterError("ADAPTER_OUTPUT_ALREADY_EXISTS")
    batch = build_pr2164_adapter_batch(
        authority_path=args.authority,
        bundle_root=args.bundle,
        rules_path=args.rules,
    )
    if not batch.valid:
        raise AdapterError("ADAPTER_BATCH_NOT_SCORE_ELIGIBLE")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_json_bytes(batch.as_dict()))
    sys.stdout.buffer.write(canonical_json_bytes({"adapter_batch_sha256": batch.adapter_batch_sha256, "status": "written"}))
    return 0


def command_run_formal_measurement(args: argparse.Namespace) -> int:
    """Publish only the exact all-11, accepted-v2 golden measurement attempt."""
    raw_predictions = args.predictions.read_bytes()
    batch = build_pr2164_adapter_batch(
        authority_path=args.authority,
        bundle_root=args.bundle,
        rules_path=args.rules,
    )
    if not batch.valid:
        raise AdapterError("ADAPTER_BATCH_NOT_SCORE_ELIGIBLE")
    preflight = preflight_prediction_batch(raw=raw_predictions, adapter_batch=batch, ingress="current-v1")
    score = score_prediction_batch(adapter_batch=batch, preflight=preflight, mode="formal")
    result = run_measurement_attempt(
        mode="formal",
        attempt_id=args.attempt_id,
        attempt_root=args.attempt_root,
        inputs={
            "adapter_batch": batch,
            "ingress": "current-v1",
            "preflight": preflight,
            "raw_predictions": raw_predictions,
            "score_result": score,
            "schema_path": args.schema,
        },
    )
    if result["status"] != "completed":
        raise AttemptError("FORMAL_MEASUREMENT_NOT_CLEAN")
    validated = validate_measurement_attempt(attempt_root=args.attempt_root / args.attempt_id)
    if validated != result:
        raise AttemptError("FORMAL_ATTEMPT_VALIDATION_MISMATCH")
    sys.stdout.buffer.write(canonical_json_bytes(result))
    return 0


def command_validate_attempt(args: argparse.Namespace) -> int:
    sys.stdout.buffer.write(canonical_json_bytes(validate_measurement_attempt(attempt_root=args.attempt)))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="specchoice-measurement")
    commands = parser.add_subparsers(dest="command", required=True)
    adapter = commands.add_parser("adapt-pr2164")
    adapter.add_argument("--authority", type=Path, required=True)
    adapter.add_argument("--bundle", type=Path, required=True)
    adapter.add_argument("--rules", type=Path, required=True)
    adapter.add_argument("--output", type=Path, required=True)
    adapter.set_defaults(handler=command_adapt_pr2164)
    formal = commands.add_parser("run-formal-measurement")
    formal.add_argument("--authority", type=Path, required=True)
    formal.add_argument("--bundle", type=Path, required=True)
    formal.add_argument("--rules", type=Path, required=True)
    formal.add_argument("--schema", type=Path, required=True)
    formal.add_argument("--predictions", type=Path, required=True)
    formal.add_argument("--attempt-root", type=Path, required=True)
    formal.add_argument("--attempt-id", required=True)
    formal.set_defaults(handler=command_run_formal_measurement)
    validate_attempt = commands.add_parser("validate-attempt")
    validate_attempt.add_argument("--attempt", type=Path, required=True)
    validate_attempt.set_defaults(handler=command_validate_attempt)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.handler(args)
    except (AdapterError, AttemptError, OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
