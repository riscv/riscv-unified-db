# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Accepted-v2-only bounded PR #2164 fixture adapter."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from specchoice_evidence.canonical import canonical_json_bytes, require_byte_length, require_sha256, sha256_bytes
from specchoice_evidence.filesystem import FilesystemPolicyError, inspect_authoritative_path, require_relative_posix_path
from specchoice_evidence.verify import verify_accepted_bundle

from .domain import AdapterBatch, CanonicalFixtureRecord, Diagnostic, RawFileIdentity


class AdapterError(ValueError):
    """Stable error for bounded score-bearing fixture syntax."""


def _load_canonical_json(path: Path, code: str) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AdapterError(code) from error
    if not isinstance(payload, dict) or canonical_json_bytes(payload) != raw:
        raise AdapterError(code)
    return payload, raw


def _validate_phase2_authority(authority_path: Path, bundle_root: Path) -> None:
    """Use Phase 1's public CLI boundary rather than copying its authority policy."""
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
        cwd=authority_path.parent.parent,
        text=True,
    )
    if completed.returncode != 0:
        raise AdapterError("PHASE2_SOURCE_AUTHORITY_INVALID")


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
        evidence = inspect_authoritative_path(bundle_root, path)
        expected_length = require_byte_length(declared.get("raw_byte_length"))
        expected_hash = require_sha256(declared.get("raw_sha256"))
    except (FilesystemPolicyError, ValueError, TypeError) as error:
        raise AdapterError("RAW_PATH_OR_IDENTITY_INVALID") from error
    if evidence.file_kind != "regular_file" or evidence.byte_length != expected_length or evidence.sha256 != expected_hash:
        raise AdapterError("RAW_IDENTITY_MISMATCH")
    raw = (bundle_root / path).read_bytes()
    if len(raw) != expected_length or sha256_bytes(raw) != expected_hash:
        raise AdapterError("RAW_IDENTITY_CHANGED_DURING_READ")
    return RawFileIdentity(path=path, role=str(declared["role"]), byte_length=expected_length, sha256=expected_hash), raw


def _record_from_fixture(
    fixture: dict[str, Any], *, bundle_root: Path, source_identity: dict[str, str], adapter_version: str, rule_sha256: str
) -> CanonicalFixtureRecord:
    fixture_id = fixture.get("fixture_id")
    category = fixture.get("fixture_class")
    if not isinstance(fixture_id, str) or category not in {"positive", "negative", "candidate"}:
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
    if expected.get("id") != fixture_id or not isinstance(expected.get("expect_extract"), bool):
        raise AdapterError("EXPECTED_SCORE_FIELDS_INVALID")
    expect_extract = expected["expect_extract"]
    expected_count = 1 if category == "positive" else expected.get("expect_params")
    if not isinstance(expected_count, int):
        raise AdapterError("EXPECTED_SCORE_FIELDS_INVALID")
    if expected_count < 0:
        raise AdapterError("EXPECTED_PARAMETER_COUNT_INVALID")
    evidence_required = expected.get("must_have_excerpt") is True
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
            raise AdapterError("GOLD_NAME_MISMATCH")
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


def build_pr2164_adapter_batch(*, authority_path: Path, bundle_root: Path, rules_path: Path) -> AdapterBatch:
    """Build the sole score-eligible adapter batch from the active accepted v2 source."""
    _validate_phase2_authority(authority_path, bundle_root)
    authority, _ = _load_canonical_json(authority_path, "PHASE2_SOURCE_AUTHORITY_INVALID")
    verified = verify_accepted_bundle(bundle_root)
    source_identity = _source_identity(authority, verified)
    rules, rules_raw = _load_canonical_json(rules_path, "ADAPTER_RULES_NOT_CANONICAL")
    if rules.get("schema_version") != "1" or rules.get("adapter_version") != "pr2164-adapter-v1":
        raise AdapterError("ADAPTER_RULES_INVALID")
    rule_sha256 = sha256_bytes(rules_raw)
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
            adapter_version=rules["adapter_version"], rule_sha256=rule_sha256,
        )
        for fixture in fixtures
        if isinstance(fixture, dict)
    )
    if len(records) != 11 or len({record.fixture_id for record in records}) != 11 or sum(len(record.raw_files) for record in records) != 28:
        raise AdapterError("ADAPTER_COMPLETE_BATCH_REQUIRED")
    return AdapterBatch.from_parts(
        adapter_version=rules["adapter_version"], rule_sha256=rule_sha256, source_identity=source_identity,
        records=records, diagnostics=(),
    )
