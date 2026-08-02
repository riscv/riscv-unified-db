# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Hash-bound H1 review material and validation of existing human decisions."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from specchoice_evidence.bundle import BundleError, _publish_directory_no_replace, _sync_directory, _write_exact
from specchoice_evidence.canonical import canonical_json_bytes, require_sha256, sha256_bytes
from specchoice_evidence.filesystem import (
    FilesystemPolicyError,
    inspect_authoritative_path,
    read_authoritative_file,
    write_new_descriptor_file,
)

from .adapter import build_pr2164_adapter_batch
from .attempts import AttemptError, validate_measurement_attempt


class H1Error(ValueError):
    """Stable H1 packet or decision validation diagnostic."""


_ROOT = Path(__file__).parents[2]
_SCHEMA = _ROOT / "config/measurement/canonical-adjudication-schema-v1.json"
_H1_V2_SCHEMA = _ROOT / "config/measurement/h1-review-schema-v2.json"
_H1_V3_PACKET = _ROOT / "reports/h1/h1-source-gold-review-v3/h1-source-gold-review-v3.json"
_H1_V3_MARKDOWN = _ROOT / "reports/h1/h1-source-gold-review-v3/h1-source-gold-review-v3.md"
_H1_V3_READINESS = _ROOT / "receipts/h1-review-readiness-v3.json"
_H1_V2_FORMAL = _ROOT / "runs/measurement-attempts/formal-golden-pr2164-v2/attempt.json"
_H1_V3_ADVERSARIAL = _ROOT / "reports/h1/adversarial-oracle-results-v3.json"
_ACTIVE_AUTHORITY = _ROOT / "phase2/source-authority.json"
_REVOCATION_V2 = _ROOT / "receipts/fixture-closure-revocation-v2.json"
_ROUTE_SUPERSESSION = _ROOT / "receipts/h1-review-route-supersession-v1.json"
_H1_V3_BUNDLE = _ROOT / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v3"
_H1_V1_RULES = _ROOT / "config/measurement/pr2164-adapter-rules-v1.json"
_H1_V2_PREDICTIONS = _ROOT / "fixtures/measurement/golden-predictions-v2.json"
_H1_V2_ORACLE = _ROOT / "fixtures/measurement/adversarial/required-diagnostics-v2.json"
_H1_V3_REPLAY = _ROOT / "receipts/fixture-closure-offline-replay-v3.json"
_H1_V2_SUMMARY = _ROOT.parents[1] / ".planning/phases/02-deterministic-measurement-spine/02-16-SUMMARY.md"

_ROUTE_BINDING_PATHS = {
    "active_authority_sha256": _ACTIVE_AUTHORITY,
    "adversarial_v3_sha256": _H1_V3_ADVERSARIAL,
    "formal_v2_sha256": _H1_V2_FORMAL,
    "h1_review_schema_v2_sha256": _H1_V2_SCHEMA,
    "packet_v3_json_sha256": _H1_V3_PACKET,
    "packet_v3_markdown_sha256": _H1_V3_MARKDOWN,
    "readiness_v3_sha256": _H1_V3_READINESS,
    "revocation_v2_sha256": _REVOCATION_V2,
}

_ONTOLOGY_OPTIONS = {
    "cache_choices": [
        {
            "consequences": {
                "management_prefetch_identity": "CACHE_BLOCK_SIZE",
                "scope": "unified",
                "zero_block_identity": "CACHE_BLOCK_SIZE",
            },
            "id": "unified_cache_block_identity",
        },
        {
            "consequences": {
                "management_prefetch_identity": "CACHE_BLOCK_SIZE.management_prefetch",
                "scope": "scoped",
                "zero_block_identity": "CACHE_BLOCK_SIZE.zero_block",
            },
            "id": "scoped_cache_block_identities",
        },
    ],
    "external_publication_authorized": False,
    "local_only": True,
    "pbmte_choices": [
        {
            "consequences": {
                "discovery_surfaced": False,
                "exclusion_reason": "excluded_from_discovery",
                "final_included": False,
                "fixture_class": "absent",
                "parameter_identity": None,
            },
            "id": "excluded_from_discovery",
        },
        {
            "consequences": {
                "discovery_surfaced": True,
                "exclusion_reason": "surfaced_classified_out",
                "final_included": False,
                "fixture_class": "candidate",
                "parameter_identity": None,
            },
            "id": "surfaced_classified_out",
        },
        {
            "consequences": {
                "discovery_surfaced": True,
                "exclusion_reason": None,
                "final_included": True,
                "fixture_class": "positive",
                "parameter_identity": "PBMTE",
            },
            "id": "included_capability_parameter",
        },
    ],
    "schema_version": "h1-ontology-policy-options-v1",
}


def _relative(path: Path, code: str) -> str:
    try:
        return path.absolute().relative_to(_ROOT.absolute()).as_posix()
    except ValueError as error:
        raise H1Error(code) from error


def _read_canonical_value(path: Path, code: str) -> tuple[Any, bytes]:
    try:
        evidence, raw = read_authoritative_file(_ROOT, _relative(path, code))
        if evidence.file_kind != "regular_file":
            raise H1Error(code)
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


def _batch(
    *, authority: Path, bundle: Path, rules: Path, pending_authority: Path | None,
    transition: Path | None, revocation: Path | None,
) -> object:
    batch = build_pr2164_adapter_batch(
        authority_path=authority,
        bundle_root=bundle,
        rules_path=rules,
        pending_authority_path=pending_authority,
        transition_path=transition,
        revocation_path=revocation,
    )
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


def _expected_bindings(
    *, formal_attempt: Path, adversarial_report: Path, h1_schema: Path, authority: Path, bundle: Path,
    rules: Path, predictions: Path, oracle: Path, pending_authority: Path | None, transition: Path | None,
    revocation: Path | None, batch: object,
) -> dict[str, Any]:
    from .cli import validate_adversarial_report

    try:
        _, schema_raw = _read_canonical(_SCHEMA, "H1_BINDINGS_INVALID")
        formal_summary = validate_measurement_attempt(
            attempt_root=formal_attempt, adapter_batch=batch, schema_raw=schema_raw
        )
        formal, _ = _read_canonical(formal_attempt / "attempt.json", "H1_FORMAL_ATTEMPT_INVALID")
        adversarial = validate_adversarial_report(
            report_path=adversarial_report,
            formal_attempt=formal_attempt,
            authority=authority,
            bundle=bundle,
            rules=rules,
            schema=_SCHEMA,
            predictions=predictions,
            oracle=oracle,
            pending_authority=pending_authority,
            transition=transition,
            revocation=revocation,
        )
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
    adversarial_bindings = adversarial.get("bindings")
    expected_source = getattr(batch, "source_identity")
    try:
        _, h1_schema_raw = read_authoritative_file(h1_schema.parent, h1_schema.name)
    except (FilesystemPolicyError, OSError) as error:
        raise H1Error("H1_BINDINGS_INVALID") from error
    schema_sha256 = sha256_bytes(schema_raw)
    h1_schema_sha256 = sha256_bytes(h1_schema_raw)
    if (
        not isinstance(adversarial_bindings, dict)
        or bindings.get("adapter_batch_sha256") != getattr(batch, "adapter_batch_sha256")
        or bindings.get("adapter_version") != getattr(batch, "adapter_version")
        or bindings.get("rule_sha256") != getattr(batch, "rule_sha256")
        or bindings.get("schema_sha256") != schema_sha256
        or bindings.get("source_identity") != expected_source
        or adversarial_bindings.get("formal_attempt_sha256") != formal.get("attempt_sha256")
        or adversarial_bindings.get("adapter_batch_sha256") != getattr(batch, "adapter_batch_sha256")
        or adversarial_bindings.get("rule_sha256") != getattr(batch, "rule_sha256")
        or adversarial_bindings.get("schema_sha256") != schema_sha256
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
        "h1_review_schema_sha256": h1_schema_sha256,
        "rule_sha256": getattr(batch, "rule_sha256"),
        "schema_sha256": schema_sha256,
        "source_identity": expected_source,
    }


def _validate_packet_value(packet: object, *, expected: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(packet, dict) or set(packet) != {
        "bindings", "external_publication_authorized", "fixture_reviews", "packet_sha256", "schema_version"
    }:
        raise H1Error("H1_PACKET_INVALID")
    if packet.get("schema_version") != "h1-source-gold-review-v2" or packet.get("external_publication_authorized") is not False:
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


def _publish_packet_pair(*, output_json: Path, output_markdown: Path, json_bytes: bytes, markdown_bytes: bytes) -> None:
    if output_json == output_markdown or output_json.parent != output_markdown.parent:
        raise H1Error("H1_OUTPUT_PATH_INVALID")
    target = output_json.parent
    parent = target.parent
    try:
        evidence = inspect_authoritative_path(_ROOT, _relative(parent, "H1_OUTPUT_PATH_INVALID"))
    except FilesystemPolicyError as error:
        raise H1Error("H1_OUTPUT_PATH_INVALID") from error
    if evidence.file_kind != "directory" or target.exists() or target.is_symlink():
        raise H1Error("H1_OUTPUT_EXISTS")
    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.staging-", dir=parent))
    try:
        _write_exact(staging / output_json.name, json_bytes)
        _write_exact(staging / output_markdown.name, markdown_bytes)
        _sync_directory(staging)
        _publish_directory_no_replace(staging, target, "H1_OUTPUT_EXISTS")
        _sync_directory(parent)
    except (BundleError, FileExistsError, OSError) as error:
        if staging.exists():
            shutil.rmtree(staging)
        raise H1Error("H1_OUTPUT_EXISTS") from error


def _read_canonical_external(path: Path, code: str) -> tuple[dict[str, Any], bytes]:
    try:
        _, raw = read_authoritative_file(path.parent, path.name)
        value = json.loads(raw.decode("utf-8"))
    except (FilesystemPolicyError, OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise H1Error(code) from error
    if not isinstance(value, dict) or canonical_json_bytes(value) != raw:
        raise H1Error(code)
    return value, raw


def _validate_v2_schema(schema: Path) -> bytes:
    value, raw = _read_canonical_external(schema, "H1_SCHEMA_INVALID")
    required = {
        "schema_version": "h1-review-schema-v2",
        "packet": {
            "additional_properties": False,
            "external_publication_authorized": False,
            "fixture_reviews": 11,
            "schema_version": "h1-source-gold-review-v2",
        },
        "readiness": {"additional_properties": False, "external_publication_authorized": False},
        "decision": {
            "additional_properties": False,
            "aggregate_disposition": ["approved", "disputed", "incomplete"],
            "external_publication_authorized": False,
            "fixture_reviews": 11,
            "human_authored": True,
            "semantic_response_ids": [
                "ts03_adjacency",
                "ts03_empty_null_single_element",
                "ts03_equal_element_stable_order",
                "ts04_unclassified_manual_review",
                "ts05_adjacency",
                "ts05_empty_null_single_element",
                "ts05_equal_element_stable_order",
            ],
        },
    }
    if value != required:
        raise H1Error("H1_SCHEMA_INVALID")
    return raw


def _canonical_digest(path: Path, code: str) -> str:
    if path == _H1_V3_MARKDOWN:
        try:
            _, raw = read_authoritative_file(path.parent, path.name)
        except (FilesystemPolicyError, OSError) as error:
            raise H1Error(code) from error
        return sha256_bytes(raw)
    _, raw = _read_canonical_external(path, code)
    return sha256_bytes(raw)


def _route_bindings() -> dict[str, str]:
    return {
        name: _canonical_digest(path, "H1_ROUTE_SUPERSESSION_INPUT_INVALID")
        for name, path in _ROUTE_BINDING_PATHS.items()
    }


def _historical_phase_gate() -> bytes:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(_ROOT / "src")
    try:
        completed = subprocess.run(
            [
                sys.executable,
                "tests/phase1_expected_red_oracle.py",
                "--expected-focused", "72",
                "--expected-discovered", "150",
                "--expected-green", "145",
            ],
            cwd=_ROOT,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=120,
        )
    except subprocess.TimeoutExpired as error:
        raise H1Error("H1_ROUTE_SUPERSESSION_INPUT_INVALID") from error
    if completed.returncode != 0:
        raise H1Error("H1_ROUTE_SUPERSESSION_INPUT_INVALID")
    return completed.stdout


def _validate_v3_route_inputs(*, schema: Path, packet: Path, markdown: Path, readiness: Path) -> dict[str, str]:
    expected_paths = {
        "schema": _H1_V2_SCHEMA,
        "packet": _H1_V3_PACKET,
        "markdown": _H1_V3_MARKDOWN,
        "readiness": _H1_V3_READINESS,
    }
    supplied_paths = {"schema": schema, "packet": packet, "markdown": markdown, "readiness": readiness}
    for name, expected in expected_paths.items():
        if supplied_paths[name].absolute() != expected.absolute():
            raise H1Error("H1_ROUTE_SUPERSESSION_INPUT_INVALID")
    schema_raw = _validate_v2_schema(schema)
    packet_value, packet_raw = _read_canonical_external(packet, "H1_ROUTE_SUPERSESSION_INPUT_INVALID")
    _validate_packet_value(packet_value)
    try:
        _, markdown_raw = read_authoritative_file(markdown.parent, markdown.name)
    except (FilesystemPolicyError, OSError) as error:
        raise H1Error("H1_ROUTE_SUPERSESSION_INPUT_INVALID") from error
    if markdown_raw != render_h1_markdown(packet_value).encode("utf-8"):
        raise H1Error("H1_ROUTE_SUPERSESSION_INPUT_INVALID")
    readiness_value, readiness_raw = _read_canonical_external(readiness, "H1_ROUTE_SUPERSESSION_INPUT_INVALID")
    if (
        set(readiness_value) != {"bindings", "external_publication_authorized", "readiness_sha256", "schema_version"}
        or readiness_value.get("schema_version") != "h1-review-readiness-v3"
        or readiness_value.get("external_publication_authorized") is not False
        or readiness_value.get("readiness_sha256") != sha256_bytes(canonical_json_bytes({
            key: value for key, value in readiness_value.items() if key != "readiness_sha256"
        }))
    ):
        raise H1Error("H1_ROUTE_SUPERSESSION_INPUT_INVALID")
    bindings = readiness_value.get("bindings")
    if not isinstance(bindings, dict) or bindings.get("packet_sha256") != sha256_bytes(packet_raw) or (
        bindings.get("schema_sha256") != sha256_bytes(schema_raw)
    ):
        raise H1Error("H1_ROUTE_SUPERSESSION_INPUT_INVALID")
    validate_h1_readiness_v3(
        readiness=readiness,
        formal_attempt=_H1_V2_FORMAL.parent,
        adversarial_result=_H1_V3_ADVERSARIAL,
        packet=packet,
        markdown=markdown,
        schema=schema,
        source_authority=_ACTIVE_AUTHORITY,
        canonical_revocation=_REVOCATION_V2,
        bundle=_H1_V3_BUNDLE,
        rules=_H1_V1_RULES,
        predictions=_H1_V2_PREDICTIONS,
        oracle=_H1_V2_ORACLE,
        offline_replay=_H1_V3_REPLAY,
        phase_gate=_historical_phase_gate(),
        plan_summary=_H1_V2_SUMMARY,
    )
    return {
        "h1_review_schema_v2_sha256": sha256_bytes(schema_raw),
        "packet_v3_json_sha256": sha256_bytes(packet_raw),
        "packet_v3_markdown_sha256": sha256_bytes(markdown_raw),
        "readiness_v3_sha256": sha256_bytes(readiness_raw),
    }


def _route_supersession_value(bindings: dict[str, str]) -> dict[str, Any]:
    value: dict[str, Any] = {
        "bindings": bindings,
        "external_publication_authorized": False,
        "local_only": True,
        "schema_version": "h1-review-route-supersession-v1",
        "status": "insufficient_for_decision",
    }
    value["supersession_sha256"] = sha256_bytes(canonical_json_bytes(value))
    return value


def _validate_route_supersession_receipt(supersession: Path) -> dict[str, Any]:
    """Strictly validate the published refusal receipt without replaying history."""
    value, _ = _read_canonical_external(supersession, "H1_ROUTE_SUPERSESSION_INVALID")
    expected = _route_supersession_value(_route_bindings())
    if value != expected:
        raise H1Error("H1_ROUTE_SUPERSESSION_INVALID")
    return value


def write_h1_route_supersession_v1(
    *, output: Path, schema: Path, packet: Path, markdown: Path, readiness: Path,
) -> dict[str, Any]:
    """Write the one immutable refusal receipt for the historical H1 route."""
    direct = _validate_v3_route_inputs(schema=schema, packet=packet, markdown=markdown, readiness=readiness)
    bindings = _route_bindings()
    if any(bindings[name] != value for name, value in direct.items()):
        raise H1Error("H1_ROUTE_SUPERSESSION_INPUT_INVALID")
    value = _route_supersession_value(bindings)
    try:
        write_new_descriptor_file(_ROOT, _relative(output, "H1_ROUTE_SUPERSESSION_OUTPUT_INVALID"), canonical_json_bytes(value))
    except FilesystemPolicyError as error:
        raise H1Error("H1_ROUTE_SUPERSESSION_OUTPUT_INVALID") from error
    return value


def validate_h1_route_supersession_v1(
    *, supersession: Path, schema: Path, packet: Path, markdown: Path, readiness: Path,
) -> dict[str, Any]:
    """Validate that the fixed v3 route remains historical evidence only."""
    direct = _validate_v3_route_inputs(schema=schema, packet=packet, markdown=markdown, readiness=readiness)
    bindings = _route_bindings()
    if any(bindings[name] != value for name, value in direct.items()):
        raise H1Error("H1_ROUTE_SUPERSESSION_INPUT_INVALID")
    return _validate_route_supersession_receipt(supersession)


def _ontology_options_value() -> dict[str, Any]:
    value = dict(_ONTOLOGY_OPTIONS)
    value["options_sha256"] = sha256_bytes(canonical_json_bytes(value))
    return value


def write_h1_ontology_options_v1(*, output: Path) -> dict[str, Any]:
    """Write the closed, decision-free H1 ontology policy request once."""
    value = _ontology_options_value()
    try:
        write_new_descriptor_file(_ROOT, _relative(output, "H1_ONTOLOGY_OPTIONS_OUTPUT_INVALID"), canonical_json_bytes(value))
    except FilesystemPolicyError as error:
        raise H1Error("H1_ONTOLOGY_OPTIONS_OUTPUT_INVALID") from error
    return value


def validate_h1_ontology_options_v1(*, options: Path) -> dict[str, Any]:
    """Require the exact closed PBMTE and cache choice request."""
    value, _ = _read_canonical_external(options, "H1_ONTOLOGY_OPTIONS_INVALID")
    if value != _ontology_options_value():
        raise H1Error("H1_ONTOLOGY_OPTIONS_INVALID")
    return value


def validate_h1_ontology_decision_v1(*, options: Path, supersession: Path, decision: Path) -> dict[str, Any]:
    """Validate a human-authored closed selection without supplying any human field."""
    options_value = validate_h1_ontology_options_v1(options=options)
    supersession_value = validate_h1_route_supersession_v1(
        supersession=supersession, schema=_H1_V2_SCHEMA, packet=_H1_V3_PACKET,
        markdown=_H1_V3_MARKDOWN, readiness=_H1_V3_READINESS,
    )
    value, _ = _read_canonical_external(decision, "H1_ONTOLOGY_DECISION_INVALID")
    required = {
        "bindings", "cache_policy", "decision_sha256", "external_publication_authorized", "pbmte_policy",
        "reviewer", "schema_version", "signature", "timestamp",
    }
    if set(value) != required or value.get("schema_version") != "h1-source-gold-ontology-decision-v1" or (
        value.get("external_publication_authorized") is not False
    ):
        raise H1Error("H1_ONTOLOGY_DECISION_INVALID")
    if value.get("decision_sha256") != sha256_bytes(canonical_json_bytes({
        key: item for key, item in value.items() if key != "decision_sha256"
    })):
        raise H1Error("H1_ONTOLOGY_DECISION_INVALID")
    if value.get("bindings") != {
        "options_sha256": options_value["options_sha256"],
        "supersession_sha256": supersession_value["supersession_sha256"],
    }:
        raise H1Error("H1_ONTOLOGY_DECISION_INVALID")
    for key, choices in (("pbmte_policy", options_value["pbmte_choices"]), ("cache_policy", options_value["cache_choices"])):
        policy = value.get(key)
        if not isinstance(policy, dict) or set(policy) != {"rationale", "selection"} or not isinstance(policy.get("rationale"), str) or not policy["rationale"]:
            raise H1Error("H1_ONTOLOGY_DECISION_INVALID")
        if policy.get("selection") not in {choice["id"] for choice in choices}:
            raise H1Error("H1_ONTOLOGY_DECISION_INVALID")
    if not all(isinstance(value.get(key), str) and value[key] for key in ("reviewer", "signature", "timestamp")):
        raise H1Error("H1_ONTOLOGY_DECISION_INVALID")
    return {"decision_sha256": value["decision_sha256"], "valid": True}


def build_h1_packet(
    *, formal_attempt: Path, adversarial_report: Path, output_json: Path, output_markdown: Path, schema: Path,
    authority: Path, bundle: Path, rules: Path, predictions: Path, oracle: Path,
    pending_authority: Path | None = None, transition: Path | None = None, revocation: Path | None = None,
) -> dict[str, Any]:
    """Build an immutable packet from validated evidence; it never creates a decision."""
    _validate_v2_schema(schema)
    batch = _batch(
        authority=authority, bundle=bundle, rules=rules, pending_authority=pending_authority,
        transition=transition, revocation=revocation,
    )
    expected = _expected_bindings(
        formal_attempt=formal_attempt, adversarial_report=adversarial_report, h1_schema=schema,
        authority=authority, bundle=bundle, rules=rules, predictions=predictions, oracle=oracle,
        pending_authority=pending_authority, transition=transition, revocation=revocation, batch=batch,
    )
    packet: dict[str, Any] = {
        "bindings": expected,
        "external_publication_authorized": False,
        "fixture_reviews": _review_items(batch),
        "schema_version": "h1-source-gold-review-v2",
    }
    packet["packet_sha256"] = sha256_bytes(canonical_json_bytes(packet))
    _validate_packet_value(packet, expected=expected)
    _publish_packet_pair(
        output_json=output_json,
        output_markdown=output_markdown,
        json_bytes=canonical_json_bytes(packet),
        markdown_bytes=render_h1_markdown(packet).encode("utf-8"),
    )
    return packet


def validate_h1_packet(
    *, packet: Path, markdown: Path, schema: Path, formal_attempt: Path, adversarial_report: Path,
    authority: Path, bundle: Path, rules: Path, predictions: Path, oracle: Path,
    pending_authority: Path | None = None, transition: Path | None = None, revocation: Path | None = None,
) -> dict[str, Any]:
    """Recompute every current H1 binding and reject non-projection Markdown."""
    _validate_v2_schema(schema)
    value, _ = _read_canonical(packet, "H1_PACKET_INVALID")
    batch = _batch(
        authority=authority, bundle=bundle, rules=rules, pending_authority=pending_authority,
        transition=transition, revocation=revocation,
    )
    expected = _expected_bindings(
        formal_attempt=formal_attempt, adversarial_report=adversarial_report, h1_schema=schema,
        authority=authority, bundle=bundle, rules=rules, predictions=predictions, oracle=oracle,
        pending_authority=pending_authority, transition=transition, revocation=revocation, batch=batch,
    )
    value = _validate_packet_value(value, expected=expected)
    if value.get("fixture_reviews") != _review_items(batch):
        raise H1Error("H1_REVIEW_ITEM_INVALID")
    try:
        _, markdown_bytes = read_authoritative_file(_ROOT, _relative(markdown, "H1_MARKDOWN_INVALID"))
    except (FilesystemPolicyError, OSError) as error:
        raise H1Error("H1_MARKDOWN_INVALID") from error
    if markdown_bytes != render_h1_markdown(value).encode("utf-8"):
        raise H1Error("H1_MARKDOWN_INVALID")
    return value


def _readiness_bindings(
    *, formal_attempt: Path, adversarial_result: Path, packet: Path, markdown: Path, schema: Path,
    source_authority: Path, canonical_revocation: Path, bundle: Path, rules: Path, predictions: Path, oracle: Path,
    offline_replay: Path, phase_gate: bytes,
    plan_summary: Path,
) -> dict[str, str]:
    if not plan_summary.is_absolute() or ".." in plan_summary.parts:
        raise H1Error("H1_PLAN_SUMMARY_PATH_INVALID")
    _validate_v2_schema(schema)
    validate_h1_packet(
        packet=packet, markdown=markdown, schema=schema, formal_attempt=formal_attempt,
        adversarial_report=adversarial_result, authority=source_authority, bundle=bundle, rules=rules,
        predictions=predictions, oracle=oracle, revocation=canonical_revocation,
    )
    _, formal_raw = _read_canonical_external(formal_attempt / "attempt.json", "H1_FORMAL_ATTEMPT_INVALID")
    _, adversarial_raw = _read_canonical_external(adversarial_result, "H1_ADVERSARIAL_REPORT_INVALID")
    _, packet_raw = _read_canonical_external(packet, "H1_PACKET_INVALID")
    try:
        _, markdown_raw = read_authoritative_file(markdown.parent, markdown.name)
        _, authority_raw = _read_canonical_external(source_authority, "H1_SOURCE_AUTHORITY_INVALID")
        _, revocation_raw = _read_canonical_external(canonical_revocation, "H1_REVOCATION_INVALID")
        _, replay_raw = _read_canonical_external(offline_replay, "H1_OFFLINE_REPLAY_INVALID")
        _, summary_raw = read_authoritative_file(plan_summary.parent, plan_summary.name)
        phase_gate_value = json.loads(phase_gate.decode("utf-8"))
    except (FilesystemPolicyError, OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise H1Error("H1_READINESS_INPUT_INVALID") from error
    if canonical_json_bytes(phase_gate_value) != phase_gate:
        raise H1Error("H1_PHASE_GATE_INVALID")
    return {
        "adversarial_result_sha256": sha256_bytes(adversarial_raw),
        "canonical_revocation_sha256": sha256_bytes(revocation_raw),
        "formal_attempt_sha256": sha256_bytes(formal_raw),
        "markdown_sha256": sha256_bytes(markdown_raw),
        "offline_replay_sha256": sha256_bytes(replay_raw),
        "packet_sha256": sha256_bytes(packet_raw),
        "phase_gate_sha256": sha256_bytes(phase_gate),
        "plan_summary_sha256": sha256_bytes(summary_raw),
        "schema_sha256": sha256_bytes(_validate_v2_schema(schema)),
        "source_authority_sha256": sha256_bytes(authority_raw),
    }


def _readiness_value(bindings: dict[str, str]) -> dict[str, Any]:
    value: dict[str, Any] = {
        "bindings": bindings,
        "external_publication_authorized": False,
        "schema_version": "h1-review-readiness-v3",
    }
    value["readiness_sha256"] = sha256_bytes(canonical_json_bytes(value))
    return value


def write_h1_readiness_v3(
    *, output: Path, formal_attempt: Path, adversarial_result: Path, packet: Path, markdown: Path, schema: Path,
    source_authority: Path, canonical_revocation: Path, bundle: Path, rules: Path, predictions: Path, oracle: Path,
    offline_replay: Path, phase_gate: bytes, plan_summary: Path,
) -> dict[str, Any]:
    """Create one descriptor-checked readiness receipt; never creates a human decision."""
    if output.exists() or output.is_symlink() or not output.parent.is_dir() or output.parent.is_symlink():
        raise H1Error("H1_READINESS_EXISTS")
    value = _readiness_value(_readiness_bindings(
        formal_attempt=formal_attempt, adversarial_result=adversarial_result, packet=packet, markdown=markdown,
        schema=schema, source_authority=source_authority, canonical_revocation=canonical_revocation,
        bundle=bundle, rules=rules, predictions=predictions, oracle=oracle,
        offline_replay=offline_replay, phase_gate=phase_gate, plan_summary=plan_summary,
    ))
    try:
        _write_exact(output, canonical_json_bytes(value))
        _sync_directory(output.parent)
    except (FileExistsError, OSError) as error:
        raise H1Error("H1_READINESS_EXISTS") from error
    return value


def validate_h1_readiness_v3(
    *, readiness: Path, formal_attempt: Path, adversarial_result: Path, packet: Path, markdown: Path, schema: Path,
    source_authority: Path, canonical_revocation: Path, bundle: Path, rules: Path, predictions: Path, oracle: Path,
    offline_replay: Path, phase_gate: bytes, plan_summary: Path,
) -> dict[str, Any]:
    """Compare a pre-existing readiness receipt with fresh held inputs without rewriting it."""
    value, _ = _read_canonical_external(readiness, "H1_READINESS_INVALID")
    expected = _readiness_value(_readiness_bindings(
        formal_attempt=formal_attempt, adversarial_result=adversarial_result, packet=packet, markdown=markdown,
        schema=schema, source_authority=source_authority, canonical_revocation=canonical_revocation,
        bundle=bundle, rules=rules, predictions=predictions, oracle=oracle,
        offline_replay=offline_replay, phase_gate=phase_gate, plan_summary=plan_summary,
    ))
    if value != expected:
        raise H1Error("H1_READINESS_BINDINGS_INVALID")
    return value


_SEMANTIC_RESPONSE_IDS = (
    "ts03_adjacency", "ts03_empty_null_single_element", "ts03_equal_element_stable_order",
    "ts04_unclassified_manual_review", "ts05_adjacency", "ts05_empty_null_single_element",
    "ts05_equal_element_stable_order",
)


def validate_h1_decision_v2(*, schema: Path, packet: Path, readiness: Path, decision: Path) -> dict[str, Any]:
    """Validate a fully human-authored successor decision without authoring or inferring one."""
    schema_raw = _validate_v2_schema(schema)
    packet_value, packet_raw = _read_canonical_external(packet, "H1_PACKET_INVALID")
    packet_value = _validate_packet_value(packet_value)
    readiness_value, readiness_raw = _read_canonical_external(readiness, "H1_READINESS_INVALID")
    if (
        set(readiness_value) != {"bindings", "external_publication_authorized", "readiness_sha256", "schema_version"}
        or readiness_value.get("schema_version") != "h1-review-readiness-v3"
        or readiness_value.get("external_publication_authorized") is not False
    ):
        raise H1Error("H1_READINESS_INVALID")
    readiness_bindings = readiness_value.get("bindings")
    required_readiness_bindings = {
        "adversarial_result_sha256", "canonical_revocation_sha256", "formal_attempt_sha256", "markdown_sha256",
        "offline_replay_sha256", "packet_sha256", "phase_gate_sha256", "plan_summary_sha256", "schema_sha256",
        "source_authority_sha256",
    }
    if not isinstance(readiness_bindings, dict) or set(readiness_bindings) != required_readiness_bindings:
        raise H1Error("H1_READINESS_INVALID")
    for binding in readiness_bindings.values():
        _require_digest(binding, "H1_READINESS_INVALID")
    _require_digest(readiness_value.get("readiness_sha256"), "H1_READINESS_INVALID")
    if readiness_value.get("readiness_sha256") != sha256_bytes(canonical_json_bytes({
        key: value for key, value in readiness_value.items() if key != "readiness_sha256"
    })):
        raise H1Error("H1_READINESS_INVALID")
    if (
        readiness_bindings["packet_sha256"] != sha256_bytes(packet_raw)
        or readiness_bindings["schema_sha256"] != sha256_bytes(schema_raw)
    ):
        raise H1Error("H1_READINESS_BINDINGS_INVALID")
    value, _ = _read_canonical_external(decision, "H1_DECISION_INVALID")
    required = {
        "aggregate_disposition", "bindings", "decision_sha256", "external_publication_authorized", "fixture_reviews",
        "rationale", "reviewer", "schema_version", "semantic_responses", "timestamp",
    }
    if set(value) != required or value.get("schema_version") != "h1-source-gold-decision-v2" or value.get("external_publication_authorized") is not False:
        raise H1Error("H1_DECISION_INVALID")
    if value.get("decision_sha256") != sha256_bytes(canonical_json_bytes({key: item for key, item in value.items() if key != "decision_sha256"})):
        raise H1Error("H1_DECISION_HASH_INVALID")
    if not all(isinstance(value.get(key), str) and value[key] for key in ("reviewer", "timestamp", "rationale")):
        raise H1Error("H1_DECISION_INVALID")
    expected_bindings = {
        "packet_sha256": packet_value["packet_sha256"],
        "phase_gate_sha256": readiness_value.get("bindings", {}).get("phase_gate_sha256"),
        "readiness_sha256": readiness_value.get("readiness_sha256"),
        "schema_sha256": sha256_bytes(schema_raw),
    }
    if value.get("bindings") != expected_bindings:
        raise H1Error("H1_DECISION_BINDINGS_INVALID")
    reviews = value.get("fixture_reviews")
    packet_reviews = packet_value.get("fixture_reviews")
    if not isinstance(reviews, list) or not isinstance(packet_reviews, list) or len(reviews) != 11:
        raise H1Error("H1_DECISION_REVIEW_SET_INVALID")
    expected_by_id = {review["fixture_id"]: review for review in packet_reviews if isinstance(review, dict)}
    if len(expected_by_id) != 11 or {review.get("fixture_id") for review in reviews if isinstance(review, dict)} != set(expected_by_id):
        raise H1Error("H1_DECISION_REVIEW_SET_INVALID")
    dispositions: list[str] = []
    for review in reviews:
        if not isinstance(review, dict) or set(review) != {"disposition", "fixture_id", "reviewed_semantics_sha256", "reviewer", "signature"}:
            raise H1Error("H1_DECISION_REVIEW_INVALID")
        expected_review = expected_by_id.get(review.get("fixture_id"))
        if expected_review is None or review.get("reviewed_semantics_sha256") != sha256_bytes(canonical_json_bytes({
            key: item for key, item in expected_review.items() if key != "signature_slot"
        })) or not isinstance(review.get("reviewer"), str) or not review["reviewer"]:
            raise H1Error("H1_DECISION_REVIEW_INVALID")
        disposition = review.get("disposition")
        signature = review.get("signature")
        if disposition not in {"approved", "disputed", "incomplete"} or (disposition == "incomplete" and signature is not None) or (disposition != "incomplete" and (not isinstance(signature, str) or not signature)):
            raise H1Error("H1_DECISION_REVIEW_INVALID")
        dispositions.append(disposition)
    responses = value.get("semantic_responses")
    if not isinstance(responses, dict) or set(responses) != set(_SEMANTIC_RESPONSE_IDS):
        raise H1Error("H1_SEMANTIC_RESPONSES_INVALID")
    for identifier in _SEMANTIC_RESPONSE_IDS:
        response = responses[identifier]
        if not isinstance(response, dict) or set(response) != {"disposition", "response"}:
            raise H1Error("H1_SEMANTIC_RESPONSES_INVALID")
        disposition = response.get("disposition")
        answer = response.get("response")
        if disposition not in {"approved", "disputed", "incomplete"} or (disposition == "incomplete" and answer is not None) or (disposition != "incomplete" and (not isinstance(answer, str) or not answer)):
            raise H1Error("H1_SEMANTIC_RESPONSES_INVALID")
        dispositions.append(disposition)
    aggregate = value.get("aggregate_disposition")
    expected_aggregate = "incomplete" if "incomplete" in dispositions else "disputed" if "disputed" in dispositions else "approved"
    if aggregate != expected_aggregate:
        raise H1Error("H1_DISPUTE_AGGREGATION_INVALID")
    supersession = _validate_route_supersession_receipt(_ROUTE_SUPERSESSION)
    route_bindings = supersession["bindings"]
    if (
        sha256_bytes(packet_raw) == route_bindings["packet_v3_json_sha256"]
        and sha256_bytes(readiness_raw) == route_bindings["readiness_v3_sha256"]
    ):
        raise H1Error("H1_LEGACY_ROUTE_SUPERSEDED")
    return {
        "aggregate_disposition": aggregate,
        "decision_sha256": value["decision_sha256"],
        "external_publication_authorized": False,
        "fixture_count": 11,
        "semantic_response_ids": sorted(_SEMANTIC_RESPONSE_IDS),
        "valid": True,
    }
