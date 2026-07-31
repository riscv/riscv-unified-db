# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Command boundary for deterministic measurement artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from specchoice_evidence.canonical import canonical_json_bytes

from .adapter import AdapterError, build_pr2164_adapter_batch


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="specchoice-measurement")
    commands = parser.add_subparsers(dest="command", required=True)
    adapter = commands.add_parser("adapt-pr2164")
    adapter.add_argument("--authority", type=Path, required=True)
    adapter.add_argument("--bundle", type=Path, required=True)
    adapter.add_argument("--rules", type=Path, required=True)
    adapter.add_argument("--output", type=Path, required=True)
    adapter.set_defaults(handler=command_adapt_pr2164)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.handler(args)
    except (AdapterError, OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
