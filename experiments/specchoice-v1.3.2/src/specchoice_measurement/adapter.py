# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Accepted-v2-only bounded PR #2164 fixture adapter."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from specchoice_evidence.canonical import canonical_json_bytes, require_byte_length, require_sha256, sha256_bytes
from specchoice_evidence.filesystem import FilesystemPolicyError, read_authoritative_file, require_relative_posix_path
from specchoice_evidence.verify import verify_accepted_bundle

from .domain import AdapterBatch, CanonicalFixtureRecord, Diagnostic, RawFileIdentity


class AdapterError(ValueError):
    """Stable error for bounded score-bearing fixture syntax."""

    def __init__(self, code: str, *, diagnostic: Diagnostic | None = None) -> None:
        super().__init__(code)
        self.diagnostic = diagnostic


EXPECTED_FIELDS = {
    "candidate_or_negative": ["expect_extract", "expect_params", "id"],
    "positive": ["class", "expect_extract", "expect_status", "gold_name", "id", "must_have_excerpt"],
}

_EXPERIMENT_ROOT = Path(__file__).parents[2]


def _load_canonical_json(path: Path, code: str) -> tuple[dict[str, Any], bytes]:
    try:
        _, raw = read_authoritative_file(path.parent, path.name)
        payload = json.loads(raw.decode("utf-8"))
    except (FilesystemPolicyError, OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AdapterError(code) from error
    if not isinstance(payload, dict) or canonical_json_bytes(payload) != raw:
        raise AdapterError(code)
    return payload, raw


def _validate_phase2_authority(authority_path: Path, bundle_root: Path) -> None:
    """Validate the inspection-only active-v2 mode at the public boundary."""
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "specchoice_evidence.cli",
            "validate-phase2-source-authority",
            "--authority",
            authority_path.as_posix(),
            "--bundle",
            bundle_root.as_posix(),
        ],
        check=False,
        capture_output=True,
        cwd=_EXPERIMENT_ROOT,
        env={**os.environ, "PYTHONPATH": str(_EXPERIMENT_ROOT / "src")},
        text=True,
    )
    if completed.returncode != 0:
        raise AdapterError("PHASE2_SOURCE_AUTHORITY_INVALID")


def _closed_validator_stdout(completed: subprocess.CompletedProcess[str], code: str = "PENDING_SOURCE_CUTOVER_INVALID") -> dict[str, object]:
    """Accept precisely one canonical stdout receipt from the public validator."""
    if completed.returncode != 0 or completed.stderr:
        raise AdapterError(code)
    lines = completed.stdout.splitlines()
    if len(lines) != 1:
        raise AdapterError(f"{code}_STDOUT_INVALID")
    try:
        receipt = json.loads(lines[0])
    except json.JSONDecodeError as error:
        raise AdapterError(f"{code}_STDOUT_INVALID") from error
    if not isinstance(receipt, dict) or canonical_json_bytes(receipt).decode("utf-8") != f"{lines[0]}\n":
        raise AdapterError(f"{code}_STDOUT_INVALID")
    return receipt


def _held_verified_provenance(verified: dict[str, str]) -> dict[str, str]:
    """Retain only verifier-proven identity when a later custody check fails."""
    return {
        "generation": verified["generation"],
        "manifest_sha256": verified["manifest_sha256"],
        "root_sha256": verified["root_sha256"],
    }


def _validate_pending_source_cutover(
    *,
    authority_path: Path,
    bundle_root: Path,
    pending_authority_path: Path,
    transition_path: Path,
) -> dict[str, str]:
    """Bind an explicit pending-v3 rehearsal without making it active authority."""
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "specchoice_evidence.cli",
            "validate-pending-source-cutover-v10",
            "--pending-authority",
            pending_authority_path.as_posix(),
            "--transition",
            transition_path.as_posix(),
            "--active-authority",
            authority_path.as_posix(),
            "--accepted-bundle",
            bundle_root.as_posix(),
        ],
        check=False,
        capture_output=True,
        cwd=_EXPERIMENT_ROOT,
        env={**os.environ, "PYTHONPATH": str(_EXPERIMENT_ROOT / "src")},
        text=True,
    )
    receipt = _closed_validator_stdout(completed)
    pending, pending_raw = _load_canonical_json(pending_authority_path, "PENDING_SOURCE_AUTHORITY_INVALID")
    transition, transition_raw = _load_canonical_json(transition_path, "PENDING_SOURCE_TRANSITION_INVALID")
    active, active_raw = _load_canonical_json(authority_path, "PHASE2_SOURCE_AUTHORITY_INVALID")
    verified = verify_accepted_bundle(bundle_root)
    manifest, _ = _load_canonical_json(bundle_root / "snapshot-manifest.json", "SNAPSHOT_MANIFEST_INVALID")
    registry, registry_raw = _load_canonical_json(bundle_root / "fixture-registry-pr2164-v1.json", "FIXTURE_REGISTRY_INVALID")
    expected_receipt = {
        "active_authority_sha256": sha256_bytes(active_raw),
        "eligible": False,
        "pending_authority_sha256": sha256_bytes(pending_raw),
        "status": "pending_cutover_valid_non_effective",
        "transition_sha256": sha256_bytes(transition_raw),
    }
    if receipt != expected_receipt:
        raise AdapterError("PENDING_SOURCE_CUTOVER_RECEIPT_MISMATCH")
    snapshot = manifest.get("content_manifest_core", {}).get("snapshots", []) if isinstance(manifest.get("content_manifest_core"), dict) else []
    fixtures = registry.get("fixtures") if isinstance(registry, dict) else None
    partition = {
        category: sum(isinstance(item, dict) and item.get("fixture_class") == category for item in fixtures or ())
        for category in ("positive", "negative", "candidate")
    }
    accepted_identity = {
        "core_sha256": verified["manifest_sha256"],
        "generation": verified["generation"],
        "root_sha256": verified["root_sha256"],
        "snapshot_manifest_sha256": manifest.get("snapshot_manifest_sha256"),
    }
    if (
        pending.get("schema_version") != "10"
        or pending.get("status") != "pending_cutover_v10"
        or pending.get("local_only") is not True
        or pending.get("external_publication_authorized") is not False
        or pending.get("accepted_identity") != accepted_identity
        or pending.get("generation") != verified["generation"]
        or pending.get("manifest_sha256") != manifest.get("snapshot_manifest_sha256")
        or pending.get("root_sha256") != verified["root_sha256"]
        or pending.get("registry_sha256") != sha256_bytes(registry_raw)
        or pending.get("fixture_count") != 11
        or pending.get("raw_file_count") != 28
        or not isinstance(snapshot, list)
        or len(snapshot) != 1
        or pending.get("pinned_commit_sha") != snapshot[0].get("pinned_commit_sha")
        or pending.get("pinned_tree_sha") != snapshot[0].get("pinned_tree_sha")
        or partition != {"positive": 6, "negative": 4, "candidate": 1}
        or transition.get("old_authority_sha256") != sha256_bytes(active_raw)
        or transition.get("accepted_identity") != accepted_identity
        or active.get("schema_version") != "1"
        or active.get("local_only") is not True
        or active.get("external_publication_authorized") is not False
    ):
        raise AdapterError("PENDING_SOURCE_CUTOVER_RECEIPT_MISMATCH")
    audit_path = authority_path.parent.parent / "receipts/fixture-closure-acceptance-audit-v3.json"
    audit, audit_raw = _load_canonical_json(audit_path, "PENDING_SOURCE_AUDIT_INVALID")
    inventory = audit.get("fixture_inventory")
    if (
        audit.get("kind") != "fixture_closure_acceptance_audit_v3"
        or audit.get("status") != "accepted_v3_local_only"
        or audit.get("local_only") is not True
        or audit.get("external_publication_authorized") is not False
        or audit.get("accepted_identity") != accepted_identity
        or audit.get("active_authority_sha256") != sha256_bytes(active_raw)
        or audit.get("historical_authority_sha256") != sha256_bytes(active_raw)
        or audit.get("pending_authority_sha256") != sha256_bytes(pending_raw)
        or audit.get("pending_transition_sha256") != sha256_bytes(transition_raw)
        or audit.get("decision_sha256") != pending.get("decision_sha256")
        or audit.get("request_sha256") != pending.get("request_sha256")
        or inventory != {
            "fixture_count": 11,
            "partition": {"candidate": 1, "negative": 4, "positive": 6},
            "raw_file_count": 28,
            "registry_sha256": sha256_bytes(registry_raw),
        }
        or not isinstance(audit.get("verifier_artifacts"), list)
        or len(audit["verifier_artifacts"]) != 5
        or sha256_bytes(canonical_json_bytes({key: value for key, value in audit.items() if key != "receipt_sha256"}))
        != audit.get("receipt_sha256")
    ):
        raise AdapterError("PENDING_SOURCE_AUDIT_MISMATCH")
    return _source_identity(pending, verified)


def _validate_active_source_cutover(
    *, authority_path: Path, bundle_root: Path, revocation_path: Path
) -> dict[str, str]:
    """Bind active-v3 only to one descriptor-rechecked public validator receipt."""
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "specchoice_evidence.cli",
            "validate-phase2-source-authority",
            "--authority",
            authority_path.as_posix(),
            "--bundle",
            bundle_root.as_posix(),
            "--revocation",
            revocation_path.as_posix(),
            "--authority-mode",
            "active",
        ],
        check=False,
        capture_output=True,
        cwd=_EXPERIMENT_ROOT,
        env={**os.environ, "PYTHONPATH": str(_EXPERIMENT_ROOT / "src")},
        text=True,
    )
    receipt = _closed_validator_stdout(completed, "ACTIVE_SOURCE_CUTOVER_INVALID")
    authority, authority_raw = _load_canonical_json(authority_path, "PHASE2_SOURCE_AUTHORITY_INVALID")
    _revocation, revocation_raw = _load_canonical_json(revocation_path, "SOURCE_AUTHORITY_REVOCATION_INVALID")
    verified = verify_accepted_bundle(bundle_root)
    manifest, _ = _load_canonical_json(bundle_root / "snapshot-manifest.json", "SNAPSHOT_MANIFEST_INVALID")
    registry, registry_raw = _load_canonical_json(bundle_root / "fixture-registry-pr2164-v1.json", "FIXTURE_REGISTRY_INVALID")
    fixtures = registry.get("fixtures") if isinstance(registry, dict) else None
    partition = {
        category: sum(isinstance(item, dict) and item.get("fixture_class") == category for item in fixtures or ())
        for category in ("positive", "negative", "candidate")
    }
    expected_receipt = {
        "eligible": True,
        "fixture_count": 11,
        "generation": verified["generation"],
        "manifest_sha256": manifest.get("snapshot_manifest_sha256"),
        "pinned_commit_sha": authority.get("pinned_commit_sha"),
        "pinned_tree_sha": authority.get("pinned_tree_sha"),
        "raw_file_count": 28,
        "registry_sha256": sha256_bytes(registry_raw),
        "root_sha256": verified["root_sha256"],
        "status": "valid",
    }
    accepted_identity = {
        "core_sha256": verified["manifest_sha256"],
        "generation": verified["generation"],
        "root_sha256": verified["root_sha256"],
        "snapshot_manifest_sha256": manifest.get("snapshot_manifest_sha256"),
    }
    if (
        receipt != expected_receipt
        or authority.get("schema_version") != "10"
        or authority.get("status") != "pending_cutover_v10"
        or authority.get("accepted_identity") != accepted_identity
        or authority.get("generation") != verified["generation"]
        or authority.get("manifest_sha256") != manifest.get("snapshot_manifest_sha256")
        or authority.get("root_sha256") != verified["root_sha256"]
        or authority.get("registry_sha256") != sha256_bytes(registry_raw)
        or authority.get("fixture_count") != 11
        or authority.get("raw_file_count") != 28
        or not authority_raw
        or not revocation_raw
        or not isinstance(fixtures, list)
        or len(fixtures) != 11
        or partition != {"positive": 6, "negative": 4, "candidate": 1}
    ):
        raise AdapterError("ACTIVE_SOURCE_CUTOVER_RECEIPT_MISMATCH")
    return _source_identity(authority, verified)


def _bounded_yaml_fields(raw: bytes, *, source: str) -> dict[str, object]:
    """Read only known top-level scalar YAML forms; never become a general YAML parser."""
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise AdapterError("FIXTURE_TEXT_NOT_UTF8") from error
    fields: dict[str, object] = {}
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if not line or line.lstrip().startswith("#") or line.startswith((" ", "\t")):
            continue
        if ":" not in line:
            raise AdapterError(f"UNSUPPORTED_YAML_SYNTAX:{source}")
        key, value = line.split(":", 1)
        if not key or (key != "$schema" and not key.replace("_", "").isalnum()) or key in fields:
            raise AdapterError(f"UNSUPPORTED_YAML_SYNTAX:{source}")
        value = value.strip()
        if value in {">", "|"}:
            block: list[str] = []
            while index < len(lines) and (not lines[index] or lines[index].startswith((" ", "\t"))):
                block.append(lines[index])
                index += 1
            fields[key] = "\n".join(block).strip()
        elif value == "true":
            fields[key] = True
        elif value == "false":
            fields[key] = False
        elif value.isdecimal():
            fields[key] = int(value)
        elif value == "":
            # Nested YAML is provenance-only in this adapter.  Its indented body is
            # deliberately not interpreted, while score-bearing top-level fields stay bounded.
            fields[key] = None
        elif value and not value.startswith(("[", "{", "-")):
            fields[key] = value
        else:
            raise AdapterError(f"UNSUPPORTED_YAML_SYNTAX:{source}")
    return fields


def _source_identity(authority: dict[str, Any], verified: dict[str, str]) -> dict[str, str]:
    fields = (
        "generation", "manifest_sha256", "pinned_commit_sha", "pinned_tree_sha",
        "registry_sha256", "root_sha256",
    )
    identity = {field: str(authority[field]) for field in fields}
    if identity["generation"] != verified["generation"] or identity["root_sha256"] != verified["root_sha256"]:
        raise AdapterError("PHASE2_SOURCE_IDENTITY_MISMATCH")
    return identity


def _raw_identity(bundle_root: Path, declared: dict[str, Any]) -> tuple[RawFileIdentity, bytes]:
    path = declared.get("local_bundle_path")
    try:
        require_relative_posix_path(path)
        evidence, raw = read_authoritative_file(bundle_root, path)
        expected_length = require_byte_length(declared.get("raw_byte_length"))
        expected_hash = require_sha256(declared.get("raw_sha256"))
    except (FilesystemPolicyError, OSError, ValueError, TypeError) as error:
        raise AdapterError("RAW_PATH_OR_IDENTITY_INVALID") from error
    if evidence.file_kind != "regular_file" or evidence.byte_length != expected_length or evidence.sha256 != expected_hash:
        raise AdapterError("RAW_IDENTITY_MISMATCH")
    if len(raw) != expected_length or sha256_bytes(raw) != expected_hash:
        raise AdapterError("RAW_IDENTITY_CHANGED_DURING_READ")
    return RawFileIdentity(path=path, role=str(declared["role"]), byte_length=expected_length, sha256=expected_hash), raw


def _record_from_fixture(
    fixture: dict[str, Any], *, bundle_root: Path, source_identity: dict[str, str], adapter_version: str, rule_sha256: str, rules: dict[str, Any]
) -> CanonicalFixtureRecord:
    fixture_id = fixture.get("fixture_id")
    category = fixture.get("fixture_class")
    if not isinstance(fixture_id, str) or category not in {"positive", "negative", "candidate"} or rules["category_derivation"].get(category) != category:
        raise AdapterError("FIXTURE_DECLARATION_INVALID")
    raw_files: list[RawFileIdentity] = []
    contents: dict[str, bytes] = {}
    for declared in fixture.get("files", []):
        if not isinstance(declared, dict):
            raise AdapterError("FIXTURE_FILE_DECLARATION_INVALID")
        item, raw = _raw_identity(bundle_root, declared)
        if item.role in contents:
            raise AdapterError("RAW_ROLE_DUPLICATE")
        raw_files.append(item)
        contents[item.role] = raw
    expected_raw = contents.get("fixture_expected")
    if expected_raw is None:
        raise AdapterError("EXPECTED_FILE_MISSING")
    expected = _bounded_yaml_fields(expected_raw, source=f"{fixture_id}:expected")
    required_fields = rules["expected_fields"]["positive" if category == "positive" else "candidate_or_negative"]
    if any(field not in expected for field in required_fields):
        raise AdapterError("EXPECTED_SCORE_FIELDS_INVALID")
    if expected.get("id") != fixture_id or not isinstance(expected.get("expect_extract"), bool):
        raise AdapterError("EXPECTED_SCORE_FIELDS_INVALID")
    expect_extract = expected["expect_extract"]
    expected_count = 1 if category == "positive" else expected.get("expect_params")
    if not isinstance(expected_count, int):
        raise AdapterError("EXPECTED_SCORE_FIELDS_INVALID")
    if expected_count < 0:
        raise AdapterError("EXPECTED_PARAMETER_COUNT_INVALID")
    evidence_required = expected.get("must_have_excerpt")
    if category == "positive" and not isinstance(evidence_required, bool):
        raise AdapterError("EVIDENCE_REQUIREMENT_INVALID")
    if category != "positive":
        evidence_required = False
    names: tuple[str, ...] = ()
    score_fields: dict[str, object] = {
        "id": expected["id"], "expect_extract": expect_extract, "expect_params": expected_count,
    }
    if category == "positive":
        gold_raw = contents.get("fixture_gold")
        if gold_raw is None or not isinstance(expected.get("gold_name"), str) or expected_count != 1 or not expect_extract:
            raise AdapterError("POSITIVE_SCORE_FIELDS_INVALID")
        gold = _bounded_yaml_fields(gold_raw, source=f"{fixture_id}:gold")
        if gold.get("name") != expected["gold_name"]:
            raise AdapterError(
                "GOLD_NAME_MISMATCH",
                diagnostic=Diagnostic(
                    code="GOLD_NAME_MISMATCH",
                    severity="blocker",
                    fixture_id=fixture_id,
                    field="gold_name",
                    expected=expected["gold_name"],
                    observed=gold.get("name"),
                    source_hashes={
                        "fixture_expected": next(item.sha256 for item in raw_files if item.role == "fixture_expected"),
                        "fixture_gold": next(item.sha256 for item in raw_files if item.role == "fixture_gold"),
                    },
                ),
            )
        names = (str(gold["name"]),)
        score_fields.update({"gold_name": expected["gold_name"], "gold_name_verified": gold["name"], "must_have_excerpt": evidence_required})
    elif "fixture_gold" in contents or expected_count != 0:
        raise AdapterError("NONPOSITIVE_GOLD_OR_COUNT_INVALID")
    if category == "candidate" and not expect_extract:
        raise AdapterError("CANDIDATE_EXPECT_EXTRACT_INVALID")
    if category == "negative" and expect_extract:
        raise AdapterError("NEGATIVE_EXPECT_EXTRACT_INVALID")
    return CanonicalFixtureRecord(
        fixture_id=fixture_id,
        category=category,
        adapter_version=adapter_version,
        rule_sha256=rule_sha256,
        source_identity=source_identity,
        raw_files=tuple(sorted(raw_files, key=lambda item: (item.path, item.role))),
        original_score_bearing=score_fields,
        expect_extract=expect_extract,
        expected_parameter_count=expected_count,
        expected_parameter_names=names,
        evidence_required=evidence_required,
    )


def validate_complete_adapter_batch(
    *,
    records: tuple[CanonicalFixtureRecord, ...],
    expected_fixture_ids: tuple[str, ...],
    expected_raw_file_count: int,
    adapter_version: str,
    rule_sha256: str,
    source_identity: dict[str, str],
) -> AdapterBatch:
    """Make score eligibility an explicit finite-set and identity gate.

    The function deliberately does not repair, sort, or retain an invalid record set:
    diagnostics are audit material only, while records remain unavailable to a scorer.
    """
    diagnostics: list[Diagnostic] = []
    actual_ids = tuple(record.fixture_id for record in records)
    if actual_ids != tuple(sorted(actual_ids)):
        diagnostics.append(Diagnostic(code="ADAPTER_ORDER_NONCANONICAL", severity="blocker"))
    if set(actual_ids) != set(expected_fixture_ids) or len(actual_ids) != len(expected_fixture_ids):
        diagnostics.append(
            Diagnostic(
                code="ADAPTER_FIXTURE_SET_MISMATCH",
                severity="blocker",
                expected=list(expected_fixture_ids),
                observed=list(actual_ids),
            )
        )
    for occurrence, fixture_id in enumerate(actual_ids):
        if actual_ids.count(fixture_id) > 1:
            diagnostics.append(
                Diagnostic(
                    code="ADAPTER_FIXTURE_DUPLICATE",
                    severity="blocker",
                    fixture_id=fixture_id,
                    occurrence=occurrence + 1,
                )
            )
    raw_file_count = sum(len(record.raw_files) for record in records)
    if raw_file_count != expected_raw_file_count:
        diagnostics.append(
            Diagnostic(
                code="ADAPTER_RAW_FILE_COUNT_MISMATCH",
                severity="blocker",
                expected=expected_raw_file_count,
                observed=raw_file_count,
            )
        )
    for occurrence, record in enumerate(records, start=1):
        if record.adapter_version != adapter_version:
            diagnostics.append(
                Diagnostic(
                    code="ADAPTER_VERSION_MIXED",
                    severity="blocker",
                    fixture_id=record.fixture_id,
                    field="adapter_version",
                    occurrence=occurrence,
                    expected=adapter_version,
                    observed=record.adapter_version,
                )
            )
        if record.rule_sha256 != rule_sha256:
            diagnostics.append(
                Diagnostic(
                    code="ADAPTER_RULE_HASH_MIXED",
                    severity="blocker",
                    fixture_id=record.fixture_id,
                    field="rule_sha256",
                    occurrence=occurrence,
                    expected=rule_sha256,
                    observed=record.rule_sha256,
                )
            )
        if record.source_identity != source_identity:
            diagnostics.append(
                Diagnostic(
                    code="ADAPTER_SOURCE_IDENTITY_MIXED",
                    severity="blocker",
                    fixture_id=record.fixture_id,
                    occurrence=occurrence,
                )
            )
    invalid = any(item.severity == "blocker" for item in diagnostics)
    return AdapterBatch.from_parts(
        adapter_version=adapter_version,
        rule_sha256=rule_sha256,
        source_identity=source_identity,
        records=() if invalid else records,
        diagnostics=tuple(diagnostics),
    )


def _invalid_batch(
    *, adapter_version: str, rule_sha256: str, source_identity: dict[str, str], code: str, diagnostic: Diagnostic | None = None
) -> AdapterBatch:
    return AdapterBatch.from_parts(
        adapter_version=adapter_version,
        rule_sha256=rule_sha256,
        source_identity=source_identity,
        records=(),
        diagnostics=(diagnostic or Diagnostic(code=code, severity="blocker"),),
    )


def build_pr2164_adapter_batch(
    *,
    authority_path: Path,
    bundle_root: Path,
    rules_path: Path,
    pending_authority_path: Path | None = None,
    transition_path: Path | None = None,
    revocation_path: Path | None = None,
) -> AdapterBatch:
    """Build exactly one legacy-v2, pending-v3, or active-v3 source-mode batch."""
    rules, rules_raw = _load_canonical_json(rules_path, "ADAPTER_RULES_NOT_CANONICAL")
    required_rule_keys = {"adapter_version", "category_derivation", "expected_fields", "fixture_count", "fixture_id_sort", "gold_fields", "raw_file_count", "schema_version", "score_bearing_allowlist"}
    if set(rules) != required_rule_keys or rules.get("schema_version") != "1" or not isinstance(rules.get("adapter_version"), str) or not re.fullmatch(r"pr2164-adapter-v[1-9][0-9]*", rules["adapter_version"]):
        raise AdapterError("ADAPTER_RULES_INVALID")
    if rules.get("fixture_count") != 11 or rules.get("raw_file_count") != 28 or rules.get("fixture_id_sort") != "ascending_unicode" or rules.get("score_bearing_allowlist") != ["fixture_id", "category", "expect_extract", "expected_parameter_count", "expected_parameter_names", "evidence_required"] or rules.get("category_derivation") != {"candidate": "candidate", "negative": "negative", "positive": "positive"} or rules.get("gold_fields") != {"positive": ["name"]} or rules.get("expected_fields") != EXPECTED_FIELDS:
        raise AdapterError("ADAPTER_RULES_INVALID")
    adapter_version = rules["adapter_version"]
    rule_sha256 = sha256_bytes(rules_raw)
    source_identity: dict[str, str] = {}
    try:
        if pending_authority_path is None and transition_path is None and revocation_path is None:
            _validate_phase2_authority(authority_path, bundle_root)
            verified = verify_accepted_bundle(bundle_root)
            source_identity = _held_verified_provenance(verified)
            authority, _ = _load_canonical_json(authority_path, "PHASE2_SOURCE_AUTHORITY_INVALID")
            source_identity = _source_identity(authority, verified)
        elif pending_authority_path is not None and transition_path is not None and revocation_path is None:
            verified = verify_accepted_bundle(bundle_root)
            source_identity = _held_verified_provenance(verified)
            source_identity = _validate_pending_source_cutover(
                authority_path=authority_path,
                bundle_root=bundle_root,
                pending_authority_path=pending_authority_path,
                transition_path=transition_path,
            )
        elif pending_authority_path is None and transition_path is None and revocation_path is not None:
            verified = verify_accepted_bundle(bundle_root)
            source_identity = _held_verified_provenance(verified)
            source_identity = _validate_active_source_cutover(
                authority_path=authority_path,
                bundle_root=bundle_root,
                revocation_path=revocation_path,
            )
        else:
            raise AdapterError("SOURCE_CUTOVER_MODE_INVALID")
        registry_path = bundle_root / "fixture-registry-pr2164-v1.json"
        registry, registry_raw = _load_canonical_json(registry_path, "FIXTURE_REGISTRY_NOT_CANONICAL")
        if sha256_bytes(registry_raw) != source_identity["registry_sha256"]:
            raise AdapterError("FIXTURE_REGISTRY_SHA256_MISMATCH")
        fixtures = registry.get("fixtures")
        if not isinstance(fixtures, list) or registry.get("fixture_count") != 11 or registry.get("raw_file_count") != 28:
            raise AdapterError("FIXTURE_REGISTRY_COUNTS_INVALID")
        records = tuple(
            _record_from_fixture(
                fixture, bundle_root=bundle_root, source_identity=source_identity,
                adapter_version=adapter_version, rule_sha256=rule_sha256, rules=rules,
            )
            for fixture in fixtures
            if isinstance(fixture, dict)
        )
    except (AdapterError, OSError, ValueError) as error:
        return _invalid_batch(
            adapter_version=adapter_version,
            rule_sha256=rule_sha256,
            source_identity=source_identity,
            code=str(error).split(":", 1)[0],
            diagnostic=error.diagnostic if isinstance(error, AdapterError) else None,
        )
    return validate_complete_adapter_batch(
        records=records,
        expected_fixture_ids=tuple(str(fixture["fixture_id"]) for fixture in fixtures if isinstance(fixture, dict)),
        expected_raw_file_count=28,
        adapter_version=adapter_version,
        rule_sha256=rule_sha256,
        source_identity=source_identity,
    )
