# SPDX-License-Identifier: BSD-3-Clause-Clear
"""No-replace rendering for successor reports from frozen canonical inputs."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from specchoice_evidence.canonical import canonical_json_bytes, require_sha256, sha256_bytes
from specchoice_evidence.filesystem import write_new_descriptor_file


class FinalReportError(ValueError):
    """Stable failure for a stale report input or incomplete evidence set."""


def validate_final_report_inputs(root: Path, bindings: object, receipts: object, *, human_disposition: str) -> None:
    """Reject report creation unless all hash-bound inputs and human evidence are complete."""
    if human_disposition != "approved" or not isinstance(bindings, Mapping) or not isinstance(receipts, Mapping):
        raise FinalReportError("FINAL_REPORT_NOT_APPROVED")
    if not bindings or not receipts or any(value is not True for value in receipts.values()):
        raise FinalReportError("FINAL_REPORT_RECEIPTS_INCOMPLETE")
    for path, digest in bindings.items():
        if not isinstance(path, str):
            raise FinalReportError("FINAL_REPORT_BINDING_INVALID")
        try:
            expected = require_sha256(digest)
            current = (root / path).read_bytes()
        except (OSError, ValueError) as error:
            raise FinalReportError("FINAL_REPORT_BINDING_INVALID") from error
        if sha256_bytes(current) != expected:
            raise FinalReportError("FINAL_REPORT_INPUT_DRIFT")


def write_successor_reports(
    root: Path, bindings: object, receipts: object, *, human_disposition: str, reports: Mapping[str, Mapping[str, object]],
) -> dict[str, str]:
    """Write a finite, deterministic report batch only after all inputs have validated."""
    validate_final_report_inputs(root, bindings, receipts, human_disposition=human_disposition)
    if len(reports) != 4 or list(reports) != sorted(reports):
        raise FinalReportError("FINAL_REPORT_SET_INVALID")
    payloads: dict[str, bytes] = {}
    for path, report in reports.items():
        if not isinstance(path, str) or not isinstance(report, Mapping):
            raise FinalReportError("FINAL_REPORT_SET_INVALID")
        payloads[path] = canonical_json_bytes(dict(report))
    for path in payloads:
        target = root / path
        write_new_descriptor_file(target.parent, target.name, payloads[path])
    return {path: sha256_bytes(payloads[path]) for path in sorted(payloads)}
