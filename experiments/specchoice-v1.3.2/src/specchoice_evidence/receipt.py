# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Canonical integrity receipts and their JSON-only reviewer projection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .canonical import canonical_json_bytes, require_sha256, sha256_bytes


class ReceiptError(ValueError):
    """Stable receipt construction or validation failure."""


def _receipt_projection(receipt: dict[str, Any]) -> dict[str, Any]:
    projected = dict(receipt)
    projected.pop("receipt_sha256", None)
    return projected


def _hashed(receipt: dict[str, Any]) -> dict[str, Any]:
    projected = _receipt_projection(receipt)
    projected["receipt_sha256"] = sha256_bytes(canonical_json_bytes(projected))
    return projected


def _require_digest(value: object, code: str) -> str:
    try:
        return require_sha256(value)
    except ValueError as error:
        raise ReceiptError(code) from error


def _validate_classifications(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ReceiptError("BOUNDARY_CLASSIFICATIONS_INVALID")
    records: list[dict[str, object]] = []
    for record in value:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise ReceiptError("BOUNDARY_CLASSIFICATIONS_INVALID")
        if not isinstance(record.get("status"), str):
            raise ReceiptError("BOUNDARY_CLASSIFICATIONS_INVALID")
        if not isinstance(record.get("attributed_to_phase"), bool) or not isinstance(record.get("blocking"), bool):
            raise ReceiptError("BOUNDARY_CLASSIFICATIONS_INVALID")
        records.append(record)
    return sorted(records, key=lambda record: str(record["path"]))


def _local_source_identity(approved_generation: dict[str, object]) -> dict[str, object]:
    return {
        "candidate_relative_path": approved_generation.get("candidate_relative_path"),
        "core_sha256": approved_generation.get("core_sha256"),
        "external_publication_authorized": False,
        "generation": approved_generation.get("generation"),
        "kind": "local_accepted_generation",
        "local_accepted_generation_authorized": True,
        "root_sha256": approved_generation.get("root_sha256"),
        "snapshot_manifest_sha256": approved_generation.get("snapshot_manifest_sha256"),
    }


def local_receipt_basis_sha256(
    baseline_sha256: str,
    environment_sha256: str,
    local_identity: dict[str, object],
    boundary_classifications: list[dict[str, object]],
) -> str:
    """Hash the reviewer-visible local facts without creating a receipt/decision cycle."""
    return sha256_bytes(
        canonical_json_bytes(
            {
                "boundary_classifications": _validate_classifications(boundary_classifications),
                "environment_decision_sha256": _require_digest(
                    environment_sha256, "RECEIPT_DIGEST_INVALID"
                ),
                "phase_start_baseline_sha256": _require_digest(
                    baseline_sha256, "RECEIPT_DIGEST_INVALID"
                ),
                "source_identity": _local_source_identity(local_identity),
            }
        )
    )


def validate_receipt(source: dict[str, Any] | Path) -> dict[str, Any]:
    """Validate canonical receipt bytes and the non-cyclic receipt digest."""
    if isinstance(source, Path):
        try:
            raw = source.read_bytes()
            receipt = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ReceiptError("RECEIPT_INVALID") from error
        if not isinstance(receipt, dict) or canonical_json_bytes(receipt) != raw:
            raise ReceiptError("RECEIPT_NOT_CANONICAL")
    else:
        receipt = source
    if not isinstance(receipt, dict) or receipt.get("schema_version") not in {"1", "2", "3"}:
        raise ReceiptError("RECEIPT_SCHEMA_INVALID")
    if receipt.get("generator_version") not in {"1", "2", "3"}:
        raise ReceiptError("RECEIPT_GENERATOR_INVALID")
    for key in ("phase_start_baseline_sha256", "environment_decision_sha256", "receipt_sha256"):
        _require_digest(receipt.get(key), "RECEIPT_DIGEST_INVALID")
    source_identity = receipt.get("source_identity")
    if not isinstance(source_identity, dict):
        raise ReceiptError("SOURCE_IDENTITY_INVALID")
    kind = source_identity.get("kind")
    if kind == "accepted_generation":
        for key in ("generation", "root_sha256", "manifest_sha256"):
            value = source_identity.get(key)
            if key == "generation":
                if not isinstance(value, str) or not value:
                    raise ReceiptError("SOURCE_IDENTITY_INVALID")
            else:
                _require_digest(value, "SOURCE_IDENTITY_INVALID")
        if "rejected_attempt_sha256" in source_identity:
            raise ReceiptError("SOURCE_IDENTITY_AMBIGUOUS")
    elif kind == "rejected_attempt":
        _require_digest(source_identity.get("rejected_attempt_sha256"), "SOURCE_IDENTITY_INVALID")
        if any(key in source_identity for key in ("generation", "root_sha256", "manifest_sha256")):
            raise ReceiptError("SOURCE_IDENTITY_AMBIGUOUS")
    elif kind == "local_accepted_generation":
        expected_fields = {
            "candidate_relative_path",
            "core_sha256",
            "external_publication_authorized",
            "generation",
            "kind",
            "local_accepted_generation_authorized",
            "root_sha256",
            "snapshot_manifest_sha256",
        }
        if set(source_identity) != expected_fields:
            raise ReceiptError("SOURCE_IDENTITY_INVALID")
        if (
            not isinstance(source_identity.get("candidate_relative_path"), str)
            or not source_identity["candidate_relative_path"]
            or not isinstance(source_identity.get("generation"), str)
            or not source_identity["generation"]
            or source_identity.get("external_publication_authorized") is not False
            or source_identity.get("local_accepted_generation_authorized") is not True
        ):
            raise ReceiptError("SOURCE_IDENTITY_INVALID")
        for key in ("core_sha256", "root_sha256", "snapshot_manifest_sha256"):
            _require_digest(source_identity.get(key), "SOURCE_IDENTITY_INVALID")
        for key in ("reviewer_decision_sha256", "receipt_basis_sha256"):
            _require_digest(receipt.get(key), "RECEIPT_DIGEST_INVALID")
    else:
        raise ReceiptError("SOURCE_IDENTITY_INVALID")
    _validate_classifications(receipt.get("boundary_classifications"))
    for key in ("blocking_diagnostics", "nonblocking_diagnostics"):
        if not isinstance(receipt.get(key), list) or not all(isinstance(item, str) for item in receipt[key]):
            raise ReceiptError("RECEIPT_DIAGNOSTICS_INVALID")
    if not isinstance(receipt.get("reviewer_package_complete"), bool) or receipt.get("outcome") not in {"pass", "fail"}:
        raise ReceiptError("RECEIPT_OUTCOME_INVALID")
    if receipt.get("receipt_sha256") != sha256_bytes(canonical_json_bytes(_receipt_projection(receipt))):
        raise ReceiptError("RECEIPT_SELF_HASH_MISMATCH")
    if kind == "rejected_attempt" and receipt.get("outcome") != "fail":
        raise ReceiptError("REJECTED_SOURCE_CANNOT_PASS")
    if kind == "local_accepted_generation" and (
        receipt.get("outcome") != "pass" or receipt.get("blocking_diagnostics") != []
    ):
        raise ReceiptError("LOCAL_SOURCE_CANNOT_BE_BLOCKED_PASS")
    if receipt.get("schema_version") == "3":
        lineage = receipt.get("restart_lineage")
        if not isinstance(lineage, dict) or set(lineage) != {"allowlist", "baseline", "incident_receipt", "previous_baseline", "reason_code", "reviewed_revision", "scope"}:
            raise ReceiptError("RESTART_LINEAGE_INVALID")
        if lineage.get("reason_code") != "D15_RESTART_COMMITTED_HISTORY_BLIND_SPOT" or lineage.get("scope") != "gap_closure_only" or not isinstance(lineage.get("reviewed_revision"), str):
            raise ReceiptError("RESTART_LINEAGE_INVALID")
        for name in ("allowlist", "baseline", "incident_receipt", "previous_baseline"):
            if not isinstance(lineage[name], dict) or not isinstance(lineage[name].get("path"), str):
                raise ReceiptError("RESTART_LINEAGE_INVALID")
            _require_digest(lineage[name].get("sha256"), "RESTART_LINEAGE_INVALID")
    return receipt


def build_blocked_receipt(
    baseline_sha256: str,
    environment_sha256: str,
    rejected_attempt_sha256: str,
    boundary_classifications: list[dict[str, object]],
) -> dict[str, Any]:
    """Build the current fail-closed receipt without an accepted source identity."""
    records = _validate_classifications(boundary_classifications)
    blocking = ["SOURCE_GENERATION_NOT_ACCEPTED"]
    blocking.extend(sorted({str(record.get("status")) for record in records if record["blocking"]}))
    receipt: dict[str, Any] = {
        "boundary_classifications": records,
        "blocking_diagnostics": blocking,
        "environment_decision_sha256": _require_digest(environment_sha256, "RECEIPT_DIGEST_INVALID"),
        "generator_version": "1",
        "nonblocking_diagnostics": sorted(
            {str(record.get("diagnostic")) for record in records if record.get("diagnostic")}
        ),
        "outcome": "fail",
        "phase_start_baseline_sha256": _require_digest(baseline_sha256, "RECEIPT_DIGEST_INVALID"),
        "reviewer_package_complete": False,
        "schema_version": "1",
        "source_identity": {
            "kind": "rejected_attempt",
            "rejected_attempt_sha256": _require_digest(rejected_attempt_sha256, "SOURCE_IDENTITY_INVALID"),
        },
    }
    return validate_receipt(_hashed(receipt))


def build_local_mvp_receipt(
    baseline_sha256: str,
    environment_sha256: str,
    approved_generation: dict[str, object],
    boundary_classifications: list[dict[str, object]],
    reviewer_decision_sha256: str,
    reviewed_receipt_basis_sha256: str,
    restart_lineage: dict[str, object] | None = None,
) -> dict[str, Any]:
    """Build a pass receipt for a local-only accepted identity after all machine gates pass."""
    source_identity = _local_source_identity(approved_generation)
    records = _validate_classifications(boundary_classifications)
    if any(record["blocking"] for record in records):
        raise ReceiptError("LOCAL_MVP_BOUNDARY_BLOCKING")
    basis = local_receipt_basis_sha256(baseline_sha256, environment_sha256, source_identity, records)
    if restart_lineage is None and reviewed_receipt_basis_sha256 != basis:
        raise ReceiptError("LOCAL_RECEIPT_BASIS_MISMATCH")
    receipt: dict[str, Any] = {
        "blocking_diagnostics": [],
        "boundary_classifications": records,
        "environment_decision_sha256": _require_digest(environment_sha256, "RECEIPT_DIGEST_INVALID"),
        "generator_version": "3" if restart_lineage is not None else "2",
        "nonblocking_diagnostics": ["LOCAL_MVP_ONLY_EXTERNAL_PUBLICATION_PROHIBITED"],
        "outcome": "pass",
        "phase_start_baseline_sha256": _require_digest(baseline_sha256, "RECEIPT_DIGEST_INVALID"),
        "receipt_basis_sha256": _require_digest(basis, "RECEIPT_DIGEST_INVALID"),
        "reviewer_decision_sha256": _require_digest(reviewer_decision_sha256, "RECEIPT_DIGEST_INVALID"),
        "reviewer_package_complete": False,
        "schema_version": "3" if restart_lineage is not None else "2",
        "source_identity": source_identity,
    }
    if restart_lineage is not None:
        receipt["restart_lineage"] = restart_lineage
    return validate_receipt(_hashed(receipt))


def render_markdown(receipt: dict[str, Any]) -> str:
    """Render only validated JSON values; no file, Git, boundary, or hash lookups occur here."""
    value = validate_receipt(receipt)
    source = value["source_identity"]
    lines = [
        "# Phase 1 Integrity Receipt",
        "",
        f"- Authoritative SHA-256: `{value['receipt_sha256']}`",
        f"- Generator version: `{value['generator_version']}`",
        f"- Outcome: `{value['outcome']}`",
        f"- Reviewer package complete: `{str(value['reviewer_package_complete']).lower()}`",
        f"- Phase-start baseline SHA-256: `{value['phase_start_baseline_sha256']}`",
        f"- Environment decision SHA-256: `{value['environment_decision_sha256']}`",
        f"- Source identity: `{source['kind']}`",
        "",
        "## Boundary classifications",
        "",
    ]
    if source["kind"] == "local_accepted_generation":
        lines.extend(
            [
                f"- Local accepted generation: `{source['generation']}`",
                f"- Core SHA-256: `{source['core_sha256']}`",
                f"- Logical root SHA-256: `{source['root_sha256']}`",
                f"- Snapshot manifest SHA-256: `{source['snapshot_manifest_sha256']}`",
                "- External publication authorized: `false`",
            ]
        )
    for record in value["boundary_classifications"]:
        lines.append(
            f"- `{record['path']}` — `{record['status']}`, blocking={str(record['blocking']).lower()}, "
            f"attributed_to_phase={str(record['attributed_to_phase']).lower()}"
        )
    lines.extend(["", "## Diagnostics", ""])
    for diagnostic in value["blocking_diagnostics"] + value["nonblocking_diagnostics"]:
        lines.append(f"- `{diagnostic}`")
    return "\n".join(lines) + "\n"


def write_receipt_package(receipt: dict[str, Any], json_path: Path, markdown_path: Path) -> dict[str, Any]:
    """Persist canonical JSON first; Markdown failure leaves it valid but incomplete."""
    value = validate_receipt(receipt)
    value = _hashed({**_receipt_projection(value), "reviewer_package_complete": False})
    json_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        markdown_path.write_text(render_markdown(_hashed({**_receipt_projection(value), "reviewer_package_complete": True})), encoding="utf-8")
    except OSError:
        json_path.write_bytes(canonical_json_bytes(value))
        return validate_receipt(value)
    value = _hashed({**_receipt_projection(value), "reviewer_package_complete": True})
    json_path.write_bytes(canonical_json_bytes(value))
    return validate_receipt(value)
