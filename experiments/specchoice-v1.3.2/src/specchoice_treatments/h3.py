# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Decision-free H3 Red readiness for the closed offline treatment boundary."""

from __future__ import annotations

import argparse
import ast
import contextlib
import io
from collections.abc import Mapping
from pathlib import Path

from specchoice_data.h2 import (
    H2ValidationError,
    audit_phase3_counts_v1,
    derive_data_eligibility_v1,
    validate_phase3_chain_v1,
    validate_phase3_data_authority_v1,
)
from specchoice_data.schema import DataSchemaError, require_canonical_utc
from specchoice_evidence.canonical import canonical_json_bytes, sha256_bytes
from specchoice_evidence.filesystem import (
    FilesystemPolicyError,
    enumerate_authoritative_files,
    read_authoritative_file,
    write_exact_descriptor_files,
)
from specchoice_measurement.strict_json import decode_strict_json


class H3ValidationError(ValueError):
    """Stable failure for the H3 decision-free Red readiness boundary."""


_ACKNOWLEDGMENTS = (
    "phase3_red_authority",
    "offline_treatment_bundle",
    "test_only_retrieval_contract",
    "red_counts",
    "no_model_reachability",
    "h4_not_applicable",
    "change_control",
)
_FORBIDDEN_IMPORT_ROOTS = frozenset({
    "http", "urllib", "socket", "requests", "httpx", "openai", "anthropic",
    "google", "boto3", "keyring", "dotenv",
})
_MACHINE_ONLY_FIELDS = frozenset({
    "aggregate_disposition", "reviewer_id", "attestation", "signature", "rationale", "timestamp_utc",
})
_PHASE3_ROOTS = (
    "phase3/data-authority-v1.json",
    "reports/h2/data-eligibility-v1.json",
    "reports/h2/h2-data-review-v1/review-packet.json",
    "receipts/h2-data-review-readiness-v1.json",
    "reviews/h2-data-decision-v1.json",
)
_TREATMENT_CONFIGS = (
    "config/treatments/delegation-frame-contract-v1.json",
    "config/treatments/frame-advisory-patterns-v1.json",
    "config/treatments/lexical-retrieval-contract-v1.json",
    "config/treatments/prompt-contract-v1.json",
)
_TREATMENT_FIXTURES = (
    "fixtures/treatments/contract-response-a-v1.json",
    "fixtures/treatments/contract-response-b-v1.json",
    "fixtures/treatments/contract-response-c-v1.json",
    "fixtures/treatments/frame-response-adversarial-v1.json",
    "fixtures/treatments/frame-response-b-valid-v1.json",
    "fixtures/treatments/frame-source-v1.txt",
    "fixtures/treatments/synthetic-complete-pairs-v1.json",
    "fixtures/treatments/synthetic-retrieval-receipt-v1.json",
    "fixtures/treatments/synthetic-target-v1.json",
)
_TREATMENT_PROMPTS = (
    "prompts/treatments/prompt-bundle-manifest-v1.json",
    "prompts/treatments/system-a-v1.txt",
    "prompts/treatments/system-b-v1.txt",
    "prompts/treatments/system-c-v1.txt",
)
_TREATMENT_SOURCES = (
    "src/specchoice_treatments/__init__.py",
    "src/specchoice_treatments/cli.py",
    "src/specchoice_treatments/h3.py",
    "src/specchoice_treatments/prompts.py",
    "src/specchoice_treatments/retrieval.py",
    "src/specchoice_treatments/schema.py",
)
_TREATMENT_TESTS = (
    "tests/test_treatments_frame.py",
    "tests/test_treatments_h3.py",
    "tests/test_treatments_prompts.py",
    "tests/test_treatments_retrieval.py",
)
_FROZEN_PATHS = tuple(sorted({
    *_PHASE3_ROOTS,
    *_TREATMENT_CONFIGS,
    *_TREATMENT_FIXTURES,
    *_TREATMENT_PROMPTS,
    *_TREATMENT_SOURCES,
    *_TREATMENT_TESTS,
    "reports/h3/test-only-retrieval-contract-v1.json",
}))


def _self_hash_valid(value: object, field: str) -> bool:
    return isinstance(value, Mapping) and value.get(field) == sha256_bytes(
        canonical_json_bytes({key: item for key, item in value.items() if key != field})
    )


def _load_canonical(root: Path, relative: str) -> tuple[dict[str, object], bytes]:
    try:
        _, raw = read_authoritative_file(root, relative)
        value = decode_strict_json(raw)
    except (FilesystemPolicyError, OSError, UnicodeDecodeError, ValueError) as error:
        raise H3ValidationError("H3_CHAIN_INPUT_INVALID") from error
    if not isinstance(value, dict) or canonical_json_bytes(value) != raw:
        raise H3ValidationError("H3_CHAIN_INPUT_INVALID")
    return value, raw


def _inventory(root: Path) -> tuple[list[dict[str, object]], dict[str, bytes]]:
    try:
        observations = {
            path: read_authoritative_file(root, path) for path in _FROZEN_PATHS
        }
    except (FilesystemPolicyError, OSError) as error:
        raise H3ValidationError("H3_FREEZE_INVENTORY_INVALID") from error
    records: list[dict[str, object]] = []
    raw_by_path: dict[str, bytes] = {}
    for path in _FROZEN_PATHS:
        evidence, raw = observations[path]
        if evidence.file_kind != "regular_file" or evidence.hardlink_count != 1 or evidence.sha256 is None:
            raise H3ValidationError("H3_FREEZE_INVENTORY_INVALID")
        records.append({
            "byte_length": evidence.byte_length,
            "kind": evidence.file_kind,
            "path": evidence.path,
            "sha256": evidence.sha256,
        })
        raw_by_path[path] = raw
    if [record["path"] for record in records] != sorted(record["path"] for record in records):
        raise H3ValidationError("H3_FREEZE_INVENTORY_INVALID")
    return records, raw_by_path


def _require_phase3_red(
    *, chain: Mapping[str, object], authority: Mapping[str, object], eligibility: Mapping[str, object],
    decision: Mapping[str, object], raw_by_path: Mapping[str, bytes],
) -> dict[str, object]:
    try:
        audit = audit_phase3_counts_v1(chain)
        derived = derive_data_eligibility_v1(audit)
        if eligibility != derived:
            raise H3ValidationError("H3_PHASE3_RED_REQUIRED")
        validate_phase3_data_authority_v1(
            authority=authority, chain=chain, decision=decision, eligibility=eligibility,
        )
    except (H2ValidationError, KeyError, TypeError) as error:
        raise H3ValidationError("H3_PHASE3_RED_REQUIRED") from error
    required_false = (
        "retrieval_authorized", "model_execution_authorized", "external_publication_authorized",
    )
    if (
        eligibility.get("eligibility_status") != "red_required"
        or eligibility.get("qualifying_pair_count") != 1
        or eligibility.get("strict_case_count") != 0
        or eligibility.get("qualifying_pair_ids") != ["WARL_IMPLEMENTATION_SELECTED_VS_ISA_FIXED"]
        or eligibility.get("strict_case_ids") != []
        or any(eligibility.get(field) is not False for field in (
            "retrieval_authorized", "model_experiment_authorized", "external_publication_authorized",
        ))
        or authority.get("eligibility_status") != "red_required"
        or any(authority.get(field) is not False for field in required_false)
        or authority.get("phase4_decision_required") is not True
    ):
        raise H3ValidationError("H3_PHASE3_RED_REQUIRED")
    if not all(raw_by_path[path] for path in _PHASE3_ROOTS):
        raise H3ValidationError("H3_CHAIN_INPUT_INVALID")
    return {
        "h2_decision_sha256": str(authority["h2_decision_sha256"]),
        "h2_packet_sha256": str(decision["packet_sha256"]),
        "h2_readiness_sha256": str(decision["readiness_sha256"]),
        "phase3_authority_sha256": str(authority["authority_sha256"]),
        "phase3_chain_sha256": str(chain["bindings"]["phase3_chain_sha256"]),
        "phase3_eligibility_report_sha256": str(eligibility["report_sha256"]),
    }


def load_phase4_freeze_inputs_v1(*, experiment_root: Path | None = None) -> dict[str, object]:
    """Reopen the full predecessor Red chain and every frozen treatment input."""
    root = experiment_root or Path(__file__).resolve().parents[2]
    inventory, raw_by_path = _inventory(root)
    try:
        chain = validate_phase3_chain_v1(experiment_root=root)
        authority, _ = _load_canonical(root, "phase3/data-authority-v1.json")
        eligibility, _ = _load_canonical(root, "reports/h2/data-eligibility-v1.json")
        _, decision_raw = _load_canonical(root, "reviews/h2-data-decision-v1.json")
        decision = decode_strict_json(decision_raw)
        if not isinstance(decision, dict):
            raise H3ValidationError("H3_CHAIN_INPUT_INVALID")
        phase3_bindings = _require_phase3_red(
            chain=chain, authority=authority, eligibility=eligibility, decision=decision, raw_by_path=raw_by_path,
        )
    except H3ValidationError:
        raise
    except (H2ValidationError, KeyError, TypeError, ValueError) as error:
        raise H3ValidationError("H3_CHAIN_INPUT_INVALID") from error
    inventory_hash = sha256_bytes(canonical_json_bytes(inventory))
    return {
        "phase3_bindings": phase3_bindings,
        "phase3_chain": chain,
        "phase3_authority": authority,
        "phase3_eligibility": eligibility,
        "phase4_freeze_inventory": inventory,
        "freeze_inventory_sha256": inventory_hash,
        "_experiment_root": root,
        "raw_by_path": raw_by_path,
    }


def _forbidden_imports(raw: bytes, path: str) -> None:
    try:
        tree = ast.parse(raw.decode("utf-8"), filename=path)
    except (SyntaxError, UnicodeDecodeError) as error:
        raise H3ValidationError("H3_FORBIDDEN_IMPORT") from error
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [item.name for item in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            names = [node.module]
        for name in names:
            if name.split(".", 1)[0] in _FORBIDDEN_IMPORT_ROOTS:
                raise H3ValidationError("H3_FORBIDDEN_IMPORT")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {"__import__", "eval", "exec"}:
                raise H3ValidationError("H3_FORBIDDEN_IMPORT")
            if isinstance(node.func, ast.Attribute) and node.func.attr in {"import_module", "reload"}:
                raise H3ValidationError("H3_FORBIDDEN_IMPORT")


def audit_no_model_reachability_v1(freeze_inputs: Mapping[str, object]) -> dict[str, object]:
    """Prove the treatment package has only its singleton offline verifier surface."""
    inventory = freeze_inputs.get("phase4_freeze_inventory")
    raw_by_path = freeze_inputs.get("raw_by_path")
    root = freeze_inputs.get("_experiment_root")
    if not isinstance(inventory, list) or not isinstance(raw_by_path, Mapping) or not isinstance(root, Path):
        raise H3ValidationError("H3_FREEZE_INVENTORY_INVALID")
    paths = [entry.get("path") for entry in inventory if isinstance(entry, Mapping)]
    if paths != sorted(_FROZEN_PATHS) or set(paths) != set(_FROZEN_PATHS):
        raise H3ValidationError("H3_FREEZE_INVENTORY_INVALID")
    for path in _TREATMENT_SOURCES:
        raw = raw_by_path.get(path)
        if not isinstance(raw, bytes):
            raise H3ValidationError("H3_FREEZE_INVENTORY_INVALID")
        _forbidden_imports(raw, path)
    from . import cli

    parser = cli.build_parser()
    commands = sorted(
        action.dest for action in parser._actions if isinstance(action, argparse._SubParsersAction) for _ in action.choices
    )
    command_names = sorted(
        name for action in parser._actions if isinstance(action, argparse._SubParsersAction) for name in action.choices
    )
    if commands != ["command"] or command_names != ["verify-retrieval-contract"]:
        raise H3ValidationError("H3_CLI_SURFACE_INVALID")
    parser.parse_args([
        "verify-retrieval-contract", "--target", "fixtures/treatments/synthetic-target-v1.json",
        "--corpus", "fixtures/treatments/synthetic-complete-pairs-v1.json",
        "--config", "config/treatments/lexical-retrieval-contract-v1.json",
        "--prompt-manifest", "prompts/treatments/prompt-bundle-manifest-v1.json",
    ])
    with contextlib.redirect_stderr(io.StringIO()):
        if cli.main(["model-run"]) != 2:
            raise H3ValidationError("H3_NETWORK_REACHABILITY_INVALID")
    try:
        all_paths = enumerate_authoritative_files(root)
    except (FilesystemPolicyError, OSError) as error:
        raise H3ValidationError("H3_FREEZE_INVENTORY_INVALID") from error
    if any("h4" in path.lower() for path in all_paths):
        raise H3ValidationError("H3_H4_ARTIFACT_FORBIDDEN")
    treatment_paths = [
        path for path in all_paths
        if path.startswith(("config/treatments/", "fixtures/treatments/", "prompts/treatments/", "src/specchoice_treatments/"))
    ]
    if any(any(token in path.lower() for token in ("credential", "secret", "provider", "model", ".env")) for path in treatment_paths):
        raise H3ValidationError("H3_CREDENTIAL_PATH_FORBIDDEN")
    payload = {
        "checks": {
            "cli_singleton": True,
            "forbidden_imports_absent": True,
            "h4_artifacts_absent": True,
            "runtime_success_parser_no_network": True,
            "runtime_unknown_command_no_network": True,
            "unsafe_config_and_credential_paths_absent": True,
        },
        "cli_commands": command_names,
        "forbidden_import_roots": sorted(_FORBIDDEN_IMPORT_ROOTS),
        "inspected_output_paths": [
            "reports/h3/h3-red-review-v1/review-packet.json",
            "reports/h3/h3-red-review-v1/review-packet.md",
            "receipts/h3-branch-readiness-v1.json",
        ],
        "schema_version": "h3-no-model-reachability-v1",
    }
    return {**payload, "no_model_reachability_sha256": sha256_bytes(canonical_json_bytes(payload))}


def build_h3_red_review_packet_v1(freeze_inputs: Mapping[str, object]) -> dict[str, object]:
    """Build the canonical decision-free H3 Red review packet."""
    bindings = freeze_inputs.get("phase3_bindings")
    inventory = freeze_inputs.get("phase4_freeze_inventory")
    inventory_hash = freeze_inputs.get("freeze_inventory_sha256")
    raw_by_path = freeze_inputs.get("raw_by_path")
    if not isinstance(bindings, Mapping) or not isinstance(inventory, list) or not isinstance(inventory_hash, str) or not isinstance(raw_by_path, Mapping):
        raise H3ValidationError("H3_CHAIN_INPUT_INVALID")
    no_model = audit_no_model_reachability_v1(freeze_inputs)
    prompt_raw = raw_by_path.get("prompts/treatments/prompt-bundle-manifest-v1.json")
    retrieval_raw = raw_by_path.get("reports/h3/test-only-retrieval-contract-v1.json")
    if not isinstance(prompt_raw, bytes) or not isinstance(retrieval_raw, bytes):
        raise H3ValidationError("H3_FREEZE_INVENTORY_INVALID")
    payload = {
        "N_strict": 0,
        "branch": "red",
        "credentials_boundary": "not_applicable_red",
        "external_calls_authorized": False,
        "freeze_inventory_sha256": inventory_hash,
        "h4_reason": "not_applicable_red",
        "h4_required": False,
        "model_execution_authorized": False,
        "model_snapshot": "not_applicable_red",
        "no_model_reachability": no_model,
        "no_model_reachability_sha256": no_model["no_model_reachability_sha256"],
        "phase3_bindings": dict(bindings),
        "phase4_freeze_inventory": inventory,
        "production_retrieval_authorized": False,
        "prompt_bundle_manifest_sha256": sha256_bytes(prompt_raw),
        "provider_config_present": False,
        "repeat_count": 0,
        "required_acknowledgment_categories": list(_ACKNOWLEDGMENTS),
        "retrieval_contract_report_sha256": sha256_bytes(retrieval_raw),
        "recovery_contract": {
            "disputed": "corrected upstream input requires a versioned regenerated successor chain",
            "incomplete": "a new immutable decision may bind unchanged readiness",
            "missing": "machine readiness is not branch authority",
        },
        "schema_version": "h3-red-review-packet-v1",
        "warning": "MACHINE READINESS ONLY; NOT BRANCH AUTHORITY",
    }
    return {**payload, "packet_sha256": sha256_bytes(canonical_json_bytes(payload))}


def render_h3_red_review_markdown_v1(packet: Mapping[str, object]) -> bytes:
    """Render Markdown exclusively from canonical packet JSON."""
    if not _self_hash_valid(packet, "packet_sha256"):
        raise H3ValidationError("H3_READINESS_INVALID")
    return (
        "# Phase 4 H3 Red Review\n\n"
        "**MACHINE READINESS ONLY; NOT BRANCH AUTHORITY**\n\n"
        "## Canonical packet\n\n```json\n"
    ).encode("utf-8") + canonical_json_bytes(dict(packet)) + b"```\n"


def build_h3_red_readiness_v1(packet: Mapping[str, object], markdown: bytes | None = None) -> dict[str, object]:
    """Bind only decision-free H3 machine products and their exact roots."""
    rendered = render_h3_red_review_markdown_v1(packet)
    if markdown is None:
        markdown = rendered
    required = {
        "N_strict", "branch", "credentials_boundary", "external_calls_authorized", "freeze_inventory_sha256",
        "h4_reason", "h4_required", "markdown_sha256", "model_execution_authorized", "model_snapshot",
        "no_model_reachability_sha256", "packet_sha256", "phase3_authority_sha256", "production_retrieval_authorized",
        "provider_config_present", "readiness_sha256", "repeat_count", "schema_version", "status",
    }
    if (
        not _self_hash_valid(packet, "packet_sha256")
        or markdown != rendered
        or any(field in packet for field in _MACHINE_ONLY_FIELDS)
        or packet.get("branch") != "red"
        or packet.get("N_strict") != 0 or isinstance(packet.get("N_strict"), bool)
        or packet.get("repeat_count") != 0 or isinstance(packet.get("repeat_count"), bool)
        or packet.get("h4_required") is not False or packet.get("h4_reason") != "not_applicable_red"
        or any(packet.get(field) is not False for field in (
            "provider_config_present", "external_calls_authorized", "production_retrieval_authorized", "model_execution_authorized",
        ))
        or packet.get("model_snapshot") != "not_applicable_red"
        or packet.get("credentials_boundary") != "not_applicable_red"
    ):
        raise H3ValidationError("H3_READINESS_INVALID")
    bindings = packet.get("phase3_bindings")
    if not isinstance(bindings, Mapping):
        raise H3ValidationError("H3_READINESS_INVALID")
    payload = {
        "N_strict": 0,
        "branch": "red",
        "credentials_boundary": "not_applicable_red",
        "external_calls_authorized": False,
        "freeze_inventory_sha256": packet["freeze_inventory_sha256"],
        "h4_reason": "not_applicable_red",
        "h4_required": False,
        "markdown_sha256": sha256_bytes(markdown),
        "model_execution_authorized": False,
        "model_snapshot": "not_applicable_red",
        "no_model_reachability_sha256": packet["no_model_reachability_sha256"],
        "packet_sha256": packet["packet_sha256"],
        "phase3_authority_sha256": bindings["phase3_authority_sha256"],
        "production_retrieval_authorized": False,
        "provider_config_present": False,
        "repeat_count": 0,
        "schema_version": "h3-branch-readiness-v1",
        "status": "ready_for_human",
    }
    if set({**payload, "readiness_sha256": ""}) != required:
        raise H3ValidationError("H3_READINESS_INVALID")
    return {**payload, "readiness_sha256": sha256_bytes(canonical_json_bytes(payload))}


def write_h3_red_readiness_v1(*, experiment_root: Path, packet: Mapping[str, object], markdown: bytes, readiness: Mapping[str, object]) -> None:
    """Publish only exact-resume machine outputs; human decision and authority stay absent."""
    expected = build_h3_red_readiness_v1(packet, markdown)
    if dict(readiness) != expected or not _self_hash_valid(readiness, "readiness_sha256"):
        raise H3ValidationError("H3_READINESS_INVALID")
    try:
        write_exact_descriptor_files(experiment_root, {
            "receipts/h3-branch-readiness-v1.json": canonical_json_bytes(readiness),
            "reports/h3/h3-red-review-v1/review-packet.json": canonical_json_bytes(packet),
            "reports/h3/h3-red-review-v1/review-packet.md": markdown,
        })
    except (FilesystemPolicyError, OSError) as error:
        raise H3ValidationError("H3_READINESS_INVALID") from error


_V2_MACHINE_ONLY_FIELDS = _MACHINE_ONLY_FIELDS | frozenset({"acknowledgments"})


def _load_h3_v1_predecessor(*, root: Path) -> dict[str, object]:
    """Bind the immutable v1 decision as history, never as v2 authority."""
    packet, _ = _load_canonical(root, "reports/h3/h3-red-review-v1/review-packet.json")
    readiness, _ = _load_canonical(root, "receipts/h3-branch-readiness-v1.json")
    decision, _ = _load_canonical(root, "reviews/h3-branch-decision-v1.json")
    if (
        packet.get("schema_version") != "h3-red-review-packet-v1"
        or readiness.get("schema_version") != "h3-branch-readiness-v1"
        or decision.get("schema_version") != "h3-branch-decision-v1"
        or not _self_hash_valid(packet, "packet_sha256")
        or not _self_hash_valid(readiness, "readiness_sha256")
        or not _self_hash_valid(decision, "decision_sha256")
        or decision.get("packet_sha256") != packet.get("packet_sha256")
        or decision.get("readiness_sha256") != readiness.get("readiness_sha256")
    ):
        raise H3ValidationError("H3_CHAIN_INPUT_INVALID")
    return {
        "decision_sha256": decision["decision_sha256"],
        "packet_sha256": packet["packet_sha256"],
        "readiness_sha256": readiness["readiness_sha256"],
        "status": "historical_predecessor_not_authority",
    }


def load_phase4_freeze_inputs_v2(*, experiment_root: Path | None = None) -> dict[str, object]:
    """Recompute the successor freeze from completed authority code and tests."""
    inputs = load_phase4_freeze_inputs_v1(experiment_root=experiment_root)
    root = inputs.get("_experiment_root")
    if not isinstance(root, Path):
        raise H3ValidationError("H3_FREEZE_INVENTORY_INVALID")
    return {**inputs, "predecessor_v1": _load_h3_v1_predecessor(root=root)}


def audit_no_model_reachability_v2(freeze_inputs: Mapping[str, object]) -> dict[str, object]:
    """Version the closed no-model audit with the successor output inventory."""
    audit = audit_no_model_reachability_v1(freeze_inputs)
    payload = {
        **{key: value for key, value in audit.items() if key != "no_model_reachability_sha256"},
        "inspected_output_paths": [
            "reports/h3/h3-red-review-v2/review-packet.json",
            "reports/h3/h3-red-review-v2/review-packet.md",
            "receipts/h3-branch-readiness-v2.json",
        ],
        "schema_version": "h3-no-model-reachability-v2",
    }
    return {**payload, "no_model_reachability_sha256": sha256_bytes(canonical_json_bytes(payload))}


def build_h3_red_review_packet_v2(freeze_inputs: Mapping[str, object]) -> dict[str, object]:
    """Build a decision-free v2 packet that explains why v1 cannot authorize it."""
    predecessor = freeze_inputs.get("predecessor_v1")
    if not isinstance(predecessor, Mapping) or predecessor.get("status") != "historical_predecessor_not_authority":
        raise H3ValidationError("H3_CHAIN_INPUT_INVALID")
    v1_packet = build_h3_red_review_packet_v1(freeze_inputs)
    no_model = audit_no_model_reachability_v2(freeze_inputs)
    payload = {
        **{key: value for key, value in v1_packet.items() if key not in {"no_model_reachability", "no_model_reachability_sha256", "packet_sha256", "schema_version"}},
        "no_model_reachability": no_model,
        "no_model_reachability_sha256": no_model["no_model_reachability_sha256"],
        "predecessor_v1": dict(predecessor),
        "schema_version": "h3-red-review-packet-v2",
        "successor_rationale": (
            "v2 successor rationale: ordering conflict discovered because v1 readiness froze h3.py and "
            "tests before authority implementation and adversarial tests existed; v1 remains valid historical "
            "decision but cannot generate authority, while v2 freezes the completed implementation and tests "
            "before a new human decision."
        ),
    }
    return {**payload, "packet_sha256": sha256_bytes(canonical_json_bytes(payload))}


def render_h3_red_review_markdown_v2(packet: Mapping[str, object]) -> bytes:
    """Render the successor review projection only from its canonical packet."""
    if not _self_hash_valid(packet, "packet_sha256") or packet.get("schema_version") != "h3-red-review-packet-v2":
        raise H3ValidationError("H3_READINESS_INVALID")
    return (
        "# Phase 4 H3 Red Successor Review v2\n\n"
        "**MACHINE READINESS ONLY; NOT BRANCH AUTHORITY**\n\n"
        "## Canonical packet\n\n```json\n"
    ).encode("utf-8") + canonical_json_bytes(dict(packet)) + b"```\n"


def build_h3_red_readiness_v2(packet: Mapping[str, object], markdown: bytes | None = None) -> dict[str, object]:
    """Bind a machine-only v2 readiness root without reviewer-owned fields."""
    rendered = render_h3_red_review_markdown_v2(packet)
    if markdown is None:
        markdown = rendered
    if (
        markdown != rendered
        or any(field in packet for field in _V2_MACHINE_ONLY_FIELDS)
        or packet.get("branch") != "red"
        or isinstance(packet.get("N_strict"), bool) or packet.get("N_strict") != 0
        or isinstance(packet.get("repeat_count"), bool) or packet.get("repeat_count") != 0
        or packet.get("h4_required") is not False or packet.get("h4_reason") != "not_applicable_red"
        or any(packet.get(field) is not False for field in (
            "provider_config_present", "external_calls_authorized", "production_retrieval_authorized", "model_execution_authorized",
        ))
        or packet.get("model_snapshot") != "not_applicable_red"
        or packet.get("credentials_boundary") != "not_applicable_red"
        or not isinstance(packet.get("phase3_bindings"), Mapping)
        or not isinstance(packet.get("predecessor_v1"), Mapping)
    ):
        raise H3ValidationError("H3_READINESS_INVALID")
    payload = {
        "N_strict": 0,
        "branch": "red",
        "credentials_boundary": "not_applicable_red",
        "external_calls_authorized": False,
        "freeze_inventory_sha256": packet["freeze_inventory_sha256"],
        "h4_reason": "not_applicable_red",
        "h4_required": False,
        "markdown_sha256": sha256_bytes(markdown),
        "model_execution_authorized": False,
        "model_snapshot": "not_applicable_red",
        "no_model_reachability_sha256": packet["no_model_reachability_sha256"],
        "packet_sha256": packet["packet_sha256"],
        "phase3_authority_sha256": packet["phase3_bindings"]["phase3_authority_sha256"],
        "predecessor_v1_decision_sha256": packet["predecessor_v1"]["decision_sha256"],
        "production_retrieval_authorized": False,
        "provider_config_present": False,
        "repeat_count": 0,
        "schema_version": "h3-branch-readiness-v2",
        "status": "ready_for_human",
    }
    return {**payload, "readiness_sha256": sha256_bytes(canonical_json_bytes(payload))}


def validate_h3_red_decision_v2(
    *, decision: object, packet: Mapping[str, object], readiness: Mapping[str, object],
) -> dict[str, object]:
    """Validate a future v2 human decision without treating v1 as interchangeable."""
    required = {
        "acknowledgments", "aggregate_disposition", "aggregate_rationale", "attestation", "decision_sha256",
        "packet_sha256", "readiness_sha256", "reviewer_id", "schema_version", "signature", "timestamp_utc",
    }
    if (
        not isinstance(decision, dict) or set(decision) != required
        or decision.get("schema_version") != "h3-branch-decision-v2"
    ):
        raise H3ValidationError("H3_DECISION_INCOMPLETE")
    if decision.get("packet_sha256") != packet.get("packet_sha256") or decision.get("readiness_sha256") != readiness.get("readiness_sha256"):
        raise H3ValidationError("H3_DECISION_BINDING_INVALID")
    if not _self_hash_valid(decision, "decision_sha256"):
        raise H3ValidationError("H3_DECISION_HASH_INVALID")
    for field in ("aggregate_rationale", "attestation", "reviewer_id", "signature"):
        if not isinstance(decision.get(field), str) or not decision[field].strip():
            raise H3ValidationError("H3_DECISION_INCOMPLETE")
    try:
        require_canonical_utc(decision.get("timestamp_utc"), "H3_DECISION_INCOMPLETE")
    except DataSchemaError as error:
        raise H3ValidationError(str(error)) from error
    aggregate = decision.get("aggregate_disposition")
    if aggregate not in {"approved_red", "disputed", "incomplete"}:
        raise H3ValidationError("H3_DECISION_INCOMPLETE")
    acknowledgments = decision.get("acknowledgments")
    expected = packet.get("required_acknowledgment_categories")
    if not isinstance(acknowledgments, list) or [item.get("category") if isinstance(item, Mapping) else None for item in acknowledgments] != expected:
        raise H3ValidationError("H3_DECISION_INCOMPLETE")
    for item in acknowledgments:
        if (
            not isinstance(item, Mapping) or set(item) != {"category", "disposition", "rationale"}
            or item.get("disposition") not in {"approved", "disputed", "incomplete"}
            or not isinstance(item.get("rationale"), str) or not item["rationale"].strip()
        ):
            raise H3ValidationError("H3_DECISION_INCOMPLETE")
    if aggregate == "approved_red" and any(item["disposition"] != "approved" for item in acknowledgments):
        raise H3ValidationError("H3_DECISION_INCONSISTENT")
    return decision


def _require_current_v2_inputs(freeze_inputs: Mapping[str, object]) -> dict[str, object]:
    root = freeze_inputs.get("_experiment_root")
    if not isinstance(root, Path):
        raise H3ValidationError("H3_FREEZE_INVENTORY_INVALID")
    current = load_phase4_freeze_inputs_v2(experiment_root=root)
    for field in ("phase3_bindings", "phase4_freeze_inventory", "freeze_inventory_sha256", "predecessor_v1", "raw_by_path"):
        if freeze_inputs.get(field) != current.get(field):
            raise H3ValidationError("FROZEN_INPUT_CHANGE_REQUIRES_NEW_EXPERIMENT_VERSION")
    return current


def _freeze_root_v2(*, packet: Mapping[str, object], readiness: Mapping[str, object], decision: Mapping[str, object]) -> str:
    return sha256_bytes(canonical_json_bytes({
        "decision_sha256": decision["decision_sha256"],
        "freeze_inventory_sha256": packet["freeze_inventory_sha256"],
        "no_model_reachability_sha256": packet["no_model_reachability_sha256"],
        "packet_sha256": packet["packet_sha256"],
        "phase3_authority_sha256": readiness["phase3_authority_sha256"],
        "readiness_sha256": readiness["readiness_sha256"],
    }))


def build_h3_red_authority_v2(
    *, freeze_inputs: Mapping[str, object], packet: Mapping[str, object], readiness: Mapping[str, object], decision: object,
) -> dict[str, object]:
    """Construct, but do not publish, authority from one exact fresh v2 approval."""
    current = _require_current_v2_inputs(freeze_inputs)
    expected_packet = build_h3_red_review_packet_v2(current)
    expected_readiness = build_h3_red_readiness_v2(expected_packet)
    if dict(packet) != expected_packet or dict(readiness) != expected_readiness:
        raise H3ValidationError("FROZEN_INPUT_CHANGE_REQUIRES_NEW_EXPERIMENT_VERSION")
    validated_decision = validate_h3_red_decision_v2(decision=decision, packet=packet, readiness=readiness)
    if validated_decision.get("aggregate_disposition") != "approved_red":
        raise H3ValidationError("H3_APPROVED_RED_REQUIRED")
    payload = {
        "N_strict": 0,
        "branch": "red",
        "credentials_boundary": "not_applicable_red",
        "decision_sha256": validated_decision["decision_sha256"],
        "external_calls_authorized": False,
        "freeze_root_sha256": _freeze_root_v2(packet=packet, readiness=readiness, decision=validated_decision),
        "h4_reason": "not_applicable_red",
        "h4_required": False,
        "model_execution_authorized": False,
        "model_snapshot": "not_applicable_red",
        "packet_sha256": packet["packet_sha256"],
        "phase3_authority_sha256": readiness["phase3_authority_sha256"],
        "predecessor_v1_decision_sha256": readiness["predecessor_v1_decision_sha256"],
        "production_retrieval_authorized": False,
        "provider_config_present": False,
        "readiness_sha256": readiness["readiness_sha256"],
        "repeat_count": 0,
        "schema_version": "phase4-branch-authority-v2",
    }
    return {**payload, "authority_sha256": sha256_bytes(canonical_json_bytes(payload))}


def validate_h3_red_authority_v2(
    *, authority: object, packet: Mapping[str, object], readiness: Mapping[str, object], decision: Mapping[str, object],
) -> dict[str, object]:
    """Validate a constructed v2 authority against the exact v2 decision chain."""
    required = {
        "N_strict", "authority_sha256", "branch", "credentials_boundary", "decision_sha256",
        "external_calls_authorized", "freeze_root_sha256", "h4_reason", "h4_required", "model_execution_authorized",
        "model_snapshot", "packet_sha256", "phase3_authority_sha256", "predecessor_v1_decision_sha256",
        "production_retrieval_authorized", "provider_config_present", "readiness_sha256", "repeat_count", "schema_version",
    }
    if (
        not isinstance(authority, dict) or set(authority) != required
        or authority.get("schema_version") != "phase4-branch-authority-v2"
        or not _self_hash_valid(authority, "authority_sha256")
    ):
        raise H3ValidationError("H3_AUTHORITY_INVALID")
    if (
        authority.get("branch") != "red"
        or isinstance(authority.get("N_strict"), bool) or authority.get("N_strict") != 0
        or isinstance(authority.get("repeat_count"), bool) or authority.get("repeat_count") != 0
        or authority.get("h4_required") is not False or authority.get("h4_reason") != "not_applicable_red"
        or any(authority.get(field) is not False for field in (
            "provider_config_present", "external_calls_authorized", "production_retrieval_authorized", "model_execution_authorized",
        ))
        or authority.get("model_snapshot") != "not_applicable_red"
        or authority.get("credentials_boundary") != "not_applicable_red"
        or authority.get("packet_sha256") != packet.get("packet_sha256")
        or authority.get("readiness_sha256") != readiness.get("readiness_sha256")
        or authority.get("decision_sha256") != decision.get("decision_sha256")
        or authority.get("phase3_authority_sha256") != readiness.get("phase3_authority_sha256")
        or authority.get("predecessor_v1_decision_sha256") != readiness.get("predecessor_v1_decision_sha256")
        or authority.get("freeze_root_sha256") != _freeze_root_v2(packet=packet, readiness=readiness, decision=decision)
    ):
        raise H3ValidationError("H3_AUTHORITY_INVALID")
    return authority


def write_h3_red_authority_v2(
    *, output_root: Path, freeze_inputs: Mapping[str, object], packet: Mapping[str, object],
    readiness: Mapping[str, object], decision: object,
) -> dict[str, object]:
    """Publish v2 authority only after exact fresh approved_red validation."""
    authority = build_h3_red_authority_v2(
        freeze_inputs=freeze_inputs, packet=packet, readiness=readiness, decision=decision,
    )
    validate_h3_red_authority_v2(authority=authority, packet=packet, readiness=readiness, decision=decision)
    try:
        write_exact_descriptor_files(output_root, {
            "phase4/branch-authority-v2.json": canonical_json_bytes(authority),
        })
    except (FilesystemPolicyError, OSError) as error:
        raise H3ValidationError("H3_AUTHORITY_WRITE_INVALID") from error
    return authority
