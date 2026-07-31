# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Hash-bound H1 review material and validation of existing human decisions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from specchoice_evidence.bundle import _sync_directory, _write_exact
from specchoice_evidence.canonical import canonical_json_bytes, require_sha256, sha256_bytes
from specchoice_evidence.filesystem import FilesystemPolicyError, inspect_authoritative_path

from .adapter import build_pr2164_adapter_batch
from .attempts import AttemptError, validate_measurement_attempt


class H1Error(ValueError):
    """Stable H1 packet or decision validation diagnostic."""


_ROOT = Path(__file__).parents[2]
_BUNDLE = _ROOT / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"
_AUTHORITY = _ROOT / "phase2/source-authority.json"
_RULES = _ROOT / "config/measurement/pr2164-adapter-rules-v1.json"
_SCHEMA = _ROOT / "config/measurement/canonical-adjudication-schema-v1.json"
_H1_SCHEMA = _ROOT / "config/measurement/h1-review-schema-v1.json"
_GOLDEN = _ROOT / "fixtures/measurement/golden-predictions-v1.json"


def _relative(path: Path, code: str) -> str:
    try:
        return path.absolute().relative_to(_ROOT.absolute()).as_posix()
    except ValueError as error:
        raise H1Error(code) from error


def _read_canonical_value(path: Path, code: str) -> tuple[Any, bytes]:
    try:
        evidence = inspect_authoritative_path(_ROOT, _relative(path, code))
        if evidence.file_kind != "regular_file":
            raise H1Error(code)
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (FilesystemPolicyError, OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise H1Error(code) from error
    if canonical_json_bytes(value) != raw:
        raise H1Error(code)
    return value, raw


def _read_canonical(path: Path, code: str) -> tuple[dict[str, Any], bytes]:
    value, raw = _read_canonical_value(path, code)
    if not isinstance(value, dict):
        raise H1Error(code)
    return value, raw


def _require_digest(value: object, code: str) -> str:
    try:
        return require_sha256(value)
    except ValueError as error:
        raise H1Error(code) from error


def _packet_projection(packet: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in packet.items() if key != "packet_sha256"}


def _decision_projection(decision: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in decision.items() if key != "decision_sha256"}


def _batch() -> object:
    batch = build_pr2164_adapter_batch(authority_path=_AUTHORITY, bundle_root=_BUNDLE, rules_path=_RULES)
    if not batch.valid:
        raise H1Error("H1_ADAPTER_NOT_ELIGIBLE")
    return batch


def _review_items(batch: object) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for record in getattr(batch, "records", ()):
        category = getattr(record, "category")
        items.append({
            "adapter_lineage": {
                "adapter_batch_sha256": getattr(batch, "adapter_batch_sha256"),
                "adapter_version": getattr(record, "adapter_version"),
                "rule_sha256": getattr(record, "rule_sha256"),
            },
            "candidate_surfaced_then_classify_out": category == "candidate",
            "category": category,
            "evidence": [raw.as_dict() for raw in getattr(record, "raw_files", ())],
            "expect_extract": getattr(record, "expect_extract"),
            "expected_parameter_count": getattr(record, "expected_parameter_count"),
            "expected_parameter_names": list(getattr(record, "expected_parameter_names")),
            "fixture_id": getattr(record, "fixture_id"),
            "signature_slot": {"reviewer": None, "signature": None},
        })
    if len(items) != 11 or [item["fixture_id"] for item in items] != sorted(item["fixture_id"] for item in items):
        raise H1Error("H1_FIXTURE_SET_INVALID")
    return items


def _expected_bindings(*, formal_attempt: Path, adversarial_report: Path) -> dict[str, Any]:
    from .cli import validate_adversarial_report

    try:
        formal_summary = validate_measurement_attempt(attempt_root=formal_attempt)
        formal, _ = _read_canonical(formal_attempt / "attempt.json", "H1_FORMAL_ATTEMPT_INVALID")
        adversarial = validate_adversarial_report(report_path=adversarial_report)
    except (AttemptError, ValueError, OSError) as error:
        raise H1Error("H1_EVIDENCE_INVALID") from error
    if (formal_summary.get("role"), formal_summary.get("status")) != ("formal", "completed") or (
        formal.get("role"), formal.get("status")
    ) != ("formal", "completed"):
        raise H1Error("H1_FORMAL_ATTEMPT_NOT_CLEAN")
    bindings = formal.get("bindings")
    artifacts = formal.get("artifacts")
    if not isinstance(bindings, dict) or not isinstance(artifacts, dict):
        raise H1Error("H1_FORMAL_ATTEMPT_INVALID")
    diagnostics = formal_attempt / "diagnostics.json"
    diagnostics_value, diagnostics_raw = _read_canonical_value(diagnostics, "H1_FORMAL_DIAGNOSTICS_INVALID")
    if diagnostics_value != []:
        raise H1Error("H1_FORMAL_DIAGNOSTICS_NOT_CLEAN")
    diagnostic_entry = artifacts.get("diagnostics.json")
    if not isinstance(diagnostic_entry, dict) or diagnostic_entry != {
        "byte_length": len(diagnostics_raw), "sha256": sha256_bytes(diagnostics_raw)
    }:
        raise H1Error("H1_FORMAL_DIAGNOSTICS_INVALID")
    batch = _batch()
    adversarial_bindings = adversarial.get("bindings")
    expected_source = getattr(batch, "source_identity")
    if (
        not isinstance(adversarial_bindings, dict)
        or bindings.get("adapter_batch_sha256") != getattr(batch, "adapter_batch_sha256")
        or bindings.get("adapter_version") != getattr(batch, "adapter_version")
        or bindings.get("rule_sha256") != getattr(batch, "rule_sha256")
        or bindings.get("schema_sha256") != sha256_bytes(_SCHEMA.read_bytes())
        or bindings.get("source_identity") != expected_source
        or adversarial_bindings.get("formal_attempt_sha256") != formal.get("attempt_sha256")
        or adversarial_bindings.get("adapter_batch_sha256") != getattr(batch, "adapter_batch_sha256")
        or adversarial_bindings.get("rule_sha256") != getattr(batch, "rule_sha256")
        or adversarial_bindings.get("schema_sha256") != sha256_bytes(_SCHEMA.read_bytes())
        or adversarial_bindings.get("golden_predictions_sha256") != bindings.get("raw_predictions_sha256")
        or adversarial_bindings.get("source_identity") != expected_source
    ):
        raise H1Error("H1_BINDINGS_INVALID")
    _, adversarial_raw = _read_canonical(adversarial_report, "H1_ADVERSARIAL_REPORT_INVALID")
    return {
        "adapter_batch_sha256": getattr(batch, "adapter_batch_sha256"),
        "adapter_version": getattr(batch, "adapter_version"),
        "adversarial_report_sha256": sha256_bytes(adversarial_raw),
        "formal_attempt_sha256": formal.get("attempt_sha256"),
        "formal_diagnostics_sha256": sha256_bytes(diagnostics_raw),
        "golden_predictions_sha256": bindings.get("raw_predictions_sha256"),
        "h1_review_schema_sha256": sha256_bytes(_H1_SCHEMA.read_bytes()),
        "rule_sha256": getattr(batch, "rule_sha256"),
        "schema_sha256": sha256_bytes(_SCHEMA.read_bytes()),
        "source_identity": expected_source,
    }


def _validate_packet_value(packet: object, *, expected: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(packet, dict) or set(packet) != {
        "bindings", "external_publication_authorized", "fixture_reviews", "packet_sha256", "schema_version"
    }:
        raise H1Error("H1_PACKET_INVALID")
    if packet.get("schema_version") != "h1-source-gold-review-v1" or packet.get("external_publication_authorized") is not False:
        raise H1Error("H1_PACKET_INVALID")
    if packet.get("packet_sha256") != sha256_bytes(canonical_json_bytes(_packet_projection(packet))):
        raise H1Error("H1_PACKET_HASH_INVALID")
    bindings = packet.get("bindings")
    if not isinstance(bindings, dict) or expected is not None and bindings != expected:
        raise H1Error("H1_BINDINGS_INVALID")
    reviews = packet.get("fixture_reviews")
    if not isinstance(reviews, list) or len(reviews) != 11:
        raise H1Error("H1_FIXTURE_SET_INVALID")
    identifiers = [item.get("fixture_id") for item in reviews if isinstance(item, dict)]
    if len(identifiers) != 11 or identifiers != sorted(identifiers) or len(set(identifiers)) != 11:
        raise H1Error("H1_FIXTURE_SET_INVALID")
    for item in reviews:
        if not isinstance(item, dict) or set(item) != {
            "adapter_lineage", "candidate_surfaced_then_classify_out", "category", "evidence", "expect_extract",
            "expected_parameter_count", "expected_parameter_names", "fixture_id", "signature_slot"
        } or item.get("signature_slot") != {"reviewer": None, "signature": None}:
            raise H1Error("H1_REVIEW_ITEM_INVALID")
    return packet


def render_h1_markdown(packet: object) -> str:
    """Project validated JSON only; this function neither reads evidence nor decides H1."""
    value = _validate_packet_value(packet)
    lines = [
        "# H1 Source/Gold Review Packet",
        "",
        f"- Packet SHA-256: `{value['packet_sha256']}`",
        "- External publication authorized: `false`",
        "- Aggregate disposition: human decision required (not present in this packet)",
        "",
        "## Immutable bindings",
        "",
    ]
    for key, binding in value["bindings"].items():
        lines.append(f"- `{key}`: `{canonical_json_bytes(binding).decode('utf-8').rstrip() if isinstance(binding, dict) else binding}`")
    lines.extend(["", "## Fixture review items", ""])
    for review in value["fixture_reviews"]:
        lines.extend([
            f"### {review['fixture_id']}",
            "",
            f"- Category: `{review['category']}`",
            f"- expect_extract: `{str(review['expect_extract']).lower()}`",
            f"- Expected parameter count: `{review['expected_parameter_count']}`",
            f"- Expected parameter names: `{', '.join(review['expected_parameter_names'])}`",
            f"- Candidate surfaced then classify_out: `{str(review['candidate_surfaced_then_classify_out']).lower()}`",
            f"- Adapter lineage: `{canonical_json_bytes(review['adapter_lineage']).decode('utf-8').rstrip()}`",
            "- Signature slot: reviewer/signature intentionally blank pending independent human review",
            "",
        ])
    return "\n".join(lines)


def _write_new(path: Path, data: bytes) -> None:
    parent_relative = _relative(path.parent, "H1_OUTPUT_PATH_INVALID")
    try:
        parent = inspect_authoritative_path(_ROOT, parent_relative)
    except FilesystemPolicyError as error:
        raise H1Error("H1_OUTPUT_PATH_INVALID") from error
    if parent.file_kind != "directory" or path.exists() or path.is_symlink():
        raise H1Error("H1_OUTPUT_EXISTS")
    try:
        _write_exact(path, data)
        _sync_directory(path.parent)
    except (FileExistsError, OSError) as error:
        raise H1Error("H1_OUTPUT_EXISTS") from error


def build_h1_packet(*, formal_attempt: Path, adversarial_report: Path, output_json: Path, output_markdown: Path) -> dict[str, Any]:
    """Build an immutable packet from validated evidence; it never creates a decision."""
    expected = _expected_bindings(formal_attempt=formal_attempt, adversarial_report=adversarial_report)
    packet: dict[str, Any] = {
        "bindings": expected,
        "external_publication_authorized": False,
        "fixture_reviews": _review_items(_batch()),
        "schema_version": "h1-source-gold-review-v1",
    }
    packet["packet_sha256"] = sha256_bytes(canonical_json_bytes(packet))
    _validate_packet_value(packet, expected=expected)
    _write_new(output_json, canonical_json_bytes(packet))
    _write_new(output_markdown, render_h1_markdown(packet).encode("utf-8"))
    return packet


def validate_h1_packet(*, packet: Path, markdown: Path) -> dict[str, Any]:
    """Recompute every current H1 binding and reject non-projection Markdown."""
    value, _ = _read_canonical(packet, "H1_PACKET_INVALID")
    expected = _expected_bindings(
        formal_attempt=_ROOT / "runs/measurement-attempts/formal-golden-pr2164-v1",
        adversarial_report=_ROOT / "reports/h1/adversarial-oracle-results-v1.json",
    )
    value = _validate_packet_value(value, expected=expected)
    if value.get("fixture_reviews") != _review_items(_batch()):
        raise H1Error("H1_REVIEW_ITEM_INVALID")
    try:
        inspect_authoritative_path(_ROOT, _relative(markdown, "H1_MARKDOWN_INVALID"))
        markdown_bytes = markdown.read_bytes()
    except (FilesystemPolicyError, OSError) as error:
        raise H1Error("H1_MARKDOWN_INVALID") from error
    if markdown_bytes != render_h1_markdown(value).encode("utf-8"):
        raise H1Error("H1_MARKDOWN_INVALID")
    return value


def validate_h1_decision(*, packet: Path, decision: Path) -> dict[str, Any]:
    """Validate, but never create or repair, an independently authored H1 decision."""
    packet_value = validate_h1_packet(packet=packet, markdown=packet.with_suffix(".md"))
    value, _ = _read_canonical(decision, "H1_DECISION_INVALID")
    if not isinstance(value, dict) or set(value) != {
        "aggregate_disposition", "bindings", "decision_sha256", "external_publication_authorized",
        "fixture_reviews", "schema_version"
    } or value.get("schema_version") != "h1-source-gold-decision-v1" or value.get("external_publication_authorized") is not False:
        raise H1Error("H1_DECISION_INVALID")
    disposition = value.get("aggregate_disposition")
    if disposition not in {"approved", "disputed", "incomplete"}:
        raise H1Error("H1_DECISION_INVALID")
    if value.get("decision_sha256") != sha256_bytes(canonical_json_bytes(_decision_projection(value))):
        raise H1Error("H1_DECISION_HASH_INVALID")
    if value.get("bindings") != {"packet_sha256": packet_value["packet_sha256"], "packet_bindings": packet_value["bindings"]}:
        raise H1Error("H1_DECISION_BINDINGS_INVALID")
    reviews = value.get("fixture_reviews")
    expected_reviews = packet_value["fixture_reviews"]
    if not isinstance(reviews, list) or len(reviews) != 11:
        raise H1Error("H1_DECISION_REVIEW_SET_INVALID")
    disputed = False
    for expected_review, review in zip(expected_reviews, reviews, strict=True):
        if not isinstance(review, dict) or set(review) != {"disposition", "fixture_id", "reviewed_semantics", "reviewer", "signature"}:
            raise H1Error("H1_DECISION_REVIEW_INVALID")
        if review.get("fixture_id") != expected_review["fixture_id"] or review.get("reviewed_semantics") != {
            key: item for key, item in expected_review.items() if key != "signature_slot"
        } or not isinstance(review.get("reviewer"), str) or not review["reviewer"] or not isinstance(review.get("signature"), str) or not review["signature"]:
            raise H1Error("H1_DECISION_REVIEW_INVALID")
        if review.get("disposition") not in {"approved", "disputed", "incomplete"}:
            raise H1Error("H1_DECISION_REVIEW_INVALID")
        disputed = disputed or review["disposition"] == "disputed"
    if disputed and disposition != "disputed":
        raise H1Error("H1_DISPUTE_AGGREGATION_INVALID")
    if disposition == "approved" and any(review["disposition"] != "approved" for review in reviews):
        raise H1Error("H1_APPROVAL_REQUIRES_ALL_ITEMS")
    return value
