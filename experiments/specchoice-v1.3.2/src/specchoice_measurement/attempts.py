# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Immutable terminal custody for deterministic Phase 2 measurement attempts."""

from __future__ import annotations

import base64
import json
import shutil
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from specchoice_evidence.bundle import BundleError, _publish_directory_no_replace, _sync_directory, _write_exact
from specchoice_evidence.canonical import canonical_json_bytes, sha256_bytes
from specchoice_evidence.filesystem import FilesystemPolicyError, read_authoritative_file

from .adapter import build_pr2164_adapter_batch
from .preflight import preflight_prediction_batch
from .scoring import score_prediction_batch


class AttemptError(ValueError):
    """Stable custody or validation diagnostic for a terminal attempt."""


_ATTEMPT_KEYS = frozenset({
    "artifacts", "attempt_id", "attempt_sha256", "bindings", "raw_predictions_base64",
    "raw_predictions_sha256", "role", "schema_version", "status",
})
_SCORE_ARTIFACTS = ("case-outcomes.json", "metrics.json", "report.json")
_BASE_ARTIFACTS = ("diagnostics.json", "parsed-predictions.json")
_VALID_ROLES = frozenset({"formal", "diagnostic_only", "invalid_preflight", "completed_with_warnings"})
_ROOT = Path(__file__).parents[2]
_BUNDLE = _ROOT / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"
_AUTHORITY = _ROOT / "phase2/source-authority.json"
_RULES = _ROOT / "config/measurement/pr2164-adapter-rules-v1.json"
_SCHEMA = _ROOT / "config/measurement/canonical-adjudication-schema-v1.json"


def _attempt_target(attempt_root: Path, attempt_id: str) -> Path:
    if not attempt_id or "/" in attempt_id or "\\" in attempt_id or attempt_id in {".", ".."}:
        raise AttemptError("ATTEMPT_ID_INVALID")
    target = attempt_root / attempt_id
    if target.exists() or target.is_symlink():
        raise AttemptError("ATTEMPT_TARGET_EXISTS")
    return target


def _as_dict(value: object, code: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise AttemptError(code)
    return dict(value)


def _artifact_payloads(*, inputs: Mapping[str, object], role: str, status: str) -> dict[str, object]:
    preflight = inputs.get("preflight")
    score = inputs.get("score_result")
    if preflight is None or score is None:
        raise AttemptError("ATTEMPT_INPUTS_INCOMPLETE")
    parsed = {
        "parsed_predictions": list(getattr(preflight, "parsed_predictions", ())),
        "raw_prediction_sha256": getattr(preflight, "raw_prediction_sha256", None),
        "status": getattr(preflight, "status", None),
    }
    payloads: dict[str, object] = {
        "diagnostics.json": [item.as_dict() for item in getattr(score, "diagnostics", ())],
        "parsed-predictions.json": parsed,
    }
    if role in {"formal", "completed_with_warnings"}:
        payloads["case-outcomes.json"] = [item.as_dict() for item in getattr(score, "case_outcomes", ())]
        metrics = getattr(score, "metrics", None)
        if metrics is None:
            raise AttemptError("ATTEMPT_SCORE_ARTIFACTS_FORBIDDEN")
        payloads["metrics.json"] = metrics.as_dict()
        payloads["report.json"] = {
            "case_outcomes": payloads["case-outcomes.json"],
            "diagnostics": payloads["diagnostics.json"],
            "metrics": payloads["metrics.json"],
            "role": role,
            "status": status,
        }
    return payloads


def _schema_bytes(inputs: Mapping[str, object]) -> bytes:
    schema_raw = inputs.get("schema_raw")
    if isinstance(schema_raw, bytes):
        return schema_raw
    schema_path = inputs.get("schema_path")
    if not isinstance(schema_path, Path):
        raise AttemptError("ATTEMPT_INPUTS_INCOMPLETE")
    try:
        _, schema_raw = read_authoritative_file(schema_path.parent, schema_path.name)
        return schema_raw
    except (OSError, FilesystemPolicyError) as error:
        raise AttemptError("ATTEMPT_SCHEMA_UNREADABLE") from error


def _bindings(inputs: Mapping[str, object], raw_predictions: bytes) -> dict[str, object]:
    batch = inputs.get("adapter_batch")
    if batch is None:
        raise AttemptError("ATTEMPT_INPUTS_INCOMPLETE")
    schema_raw = _schema_bytes(inputs)
    source_identity = getattr(batch, "source_identity", None)
    if not isinstance(source_identity, dict):
        raise AttemptError("ATTEMPT_SOURCE_IDENTITY_INVALID")
    adapter_sha = getattr(batch, "adapter_batch_sha256", None)
    if not isinstance(adapter_sha, str):
        raise AttemptError("ATTEMPT_ADAPTER_IDENTITY_INVALID")
    return {
        "adapter_batch_sha256": adapter_sha,
        "adapter_version": getattr(batch, "adapter_version", None),
        "ingress": inputs.get("ingress"),
        "raw_predictions_byte_length": len(raw_predictions),
        "raw_predictions_sha256": sha256_bytes(raw_predictions),
        "rule_sha256": getattr(batch, "rule_sha256", None),
        "schema_sha256": sha256_bytes(schema_raw),
        "source_identity": source_identity,
    }


def _terminal_role(*, mode: str, score: object) -> tuple[str, str]:
    status = getattr(score, "status", None)
    if mode == "diagnostic_only":
        return "diagnostic_only", "diagnostic_only"
    if mode != "formal":
        raise AttemptError("ATTEMPT_MODE_INVALID")
    if status == "completed":
        return "formal", "completed"
    if status == "completed_with_warnings":
        return "completed_with_warnings", "completed_with_warnings"
    return "invalid_preflight", "invalid_preflight"


def _manifest(*, attempt_id: str, role: str, status: str, raw_predictions: bytes, bindings: dict[str, object], artifacts: dict[str, dict[str, object]]) -> dict[str, object]:
    payload: dict[str, object] = {
        "artifacts": artifacts,
        "attempt_id": attempt_id,
        "bindings": bindings,
        "raw_predictions_base64": base64.b64encode(raw_predictions).decode("ascii"),
        "raw_predictions_sha256": sha256_bytes(raw_predictions),
        "role": role,
        "schema_version": "measurement-attempt-v1",
        "status": status,
    }
    payload["attempt_sha256"] = sha256_bytes(canonical_json_bytes(payload))
    return payload


def run_measurement_attempt(*, mode: str, attempt_id: str, attempt_root: Path, inputs: object) -> dict[str, object]:
    """Stage, self-validate, and publish exactly one closed terminal attempt."""
    values = _as_dict(inputs, "ATTEMPT_INPUTS_INVALID")
    raw_predictions = values.get("raw_predictions")
    if not isinstance(raw_predictions, bytes):
        raise AttemptError("ATTEMPT_RAW_PREDICTIONS_INVALID")
    target = _attempt_target(attempt_root, attempt_id)
    score = values.get("score_result")
    role, status = _terminal_role(mode=mode, score=score)
    bindings = _bindings(values, raw_predictions)
    attempt_root.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{attempt_id}.staging-", dir=attempt_root))
    try:
        artifacts: dict[str, dict[str, object]] = {}
        for name, payload in _artifact_payloads(inputs=values, role=role, status=status).items():
            content = canonical_json_bytes(payload)
            _write_exact(temporary / name, content)
            artifacts[name] = {"sha256": sha256_bytes(content), "byte_length": len(content)}
        manifest = _manifest(
            attempt_id=attempt_id, role=role, status=status, raw_predictions=raw_predictions,
            bindings=bindings, artifacts=artifacts,
        )
        _write_exact(temporary / "attempt.json", canonical_json_bytes(manifest))
        validate_measurement_attempt(
            attempt_root=temporary,
            adapter_batch=values.get("adapter_batch"),
            schema_raw=_schema_bytes(values),
        )
        _sync_directory(temporary)
        _sync_directory(attempt_root)
        try:
            _publish_directory_no_replace(temporary, target, "ATTEMPT_TARGET_EXISTS")
        except BundleError as error:
            raise AttemptError(str(error)) from error
        _sync_directory(attempt_root)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
    return {"attempt_sha256": manifest["attempt_sha256"], "role": role, "status": status}


def _read_attempt_file(*, attempt_root: Path, name: str, code: str) -> bytes:
    """Read one report-owned attempt leaf from its checked no-follow descriptor."""
    try:
        evidence, content = read_authoritative_file(attempt_root, name)
        if evidence.file_kind != "regular_file":
            raise FilesystemPolicyError("SPECIAL_FILE_KIND_REJECTED")
        return content
    except (OSError, FilesystemPolicyError) as error:
        raise AttemptError(code) from error


def load_measurement_attempt_manifest(*, attempt_root: Path) -> dict[str, object]:
    """Load a canonical attempt manifest only from its report-owned directory."""
    try:
        raw = _read_attempt_file(
            attempt_root=attempt_root, name="attempt.json", code="ATTEMPT_MANIFEST_INVALID"
        )
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AttemptError("ATTEMPT_MANIFEST_INVALID") from error
    if not isinstance(manifest, dict) or canonical_json_bytes(manifest) != raw or set(manifest) != _ATTEMPT_KEYS:
        raise AttemptError("ATTEMPT_MANIFEST_INVALID")
    return manifest


def _verify_replay(
    *,
    manifest: dict[str, object],
    artifact_bytes: Mapping[str, bytes],
    raw: bytes,
    adapter_batch: object | None = None,
    schema_raw: bytes | None = None,
) -> None:
    """Derive every terminal artifact from the bound raw input and current custody roots."""
    batch = adapter_batch or build_pr2164_adapter_batch(
        authority_path=_AUTHORITY, bundle_root=_BUNDLE, rules_path=_RULES
    )
    if not batch.valid:
        raise AttemptError("ATTEMPT_REPLAY_ADAPTER_INVALID")
    bindings = manifest["bindings"]
    assert isinstance(bindings, dict)
    ingress = bindings.get("ingress")
    if not isinstance(ingress, str):
        raise AttemptError("ATTEMPT_BINDINGS_INVALID")
    expected_bindings = _bindings(
        {
            "adapter_batch": batch,
            "schema_path": _SCHEMA,
            "schema_raw": schema_raw,
            "ingress": ingress,
        },
        raw,
    )
    if bindings != expected_bindings:
        raise AttemptError("ATTEMPT_BINDINGS_INVALID")
    preflight = preflight_prediction_batch(raw=raw, adapter_batch=batch, ingress=ingress)
    score = score_prediction_batch(adapter_batch=batch, preflight=preflight, mode="formal")
    mode = "diagnostic_only" if manifest["role"] == "diagnostic_only" else "formal"
    role, status = _terminal_role(mode=mode, score=score)
    if (role, status) != (manifest["role"], manifest["status"]):
        raise AttemptError("ATTEMPT_REPLAY_TERMINAL_MISMATCH")
    expected_payloads = _artifact_payloads(
        inputs={"preflight": preflight, "score_result": score}, role=role, status=status
    )
    for name, payload in expected_payloads.items():
        if artifact_bytes[name] != canonical_json_bytes(payload):
            raise AttemptError("ATTEMPT_REPLAY_ARTIFACT_MISMATCH")


def validate_measurement_attempt(
    *,
    attempt_root: Path,
    adapter_batch: object | None = None,
    schema_raw: bytes | None = None,
) -> dict[str, object]:
    """Validate raw-byte recovery, non-cyclic manifest digest, and every sibling binding."""
    manifest = load_measurement_attempt_manifest(attempt_root=attempt_root)
    role, status = manifest.get("role"), manifest.get("status")
    if role not in _VALID_ROLES or not isinstance(status, str):
        raise AttemptError("ATTEMPT_ROLE_INVALID")
    if (role == "formal") != (status == "completed") or (role == "completed_with_warnings") != (status == "completed_with_warnings"):
        raise AttemptError("ATTEMPT_ROLE_STATUS_INVALID")
    try:
        raw = base64.b64decode(manifest["raw_predictions_base64"], validate=True)
    except (KeyError, TypeError, ValueError) as error:
        raise AttemptError("ATTEMPT_RAW_PREDICTIONS_INVALID") from error
    if manifest.get("raw_predictions_sha256") != sha256_bytes(raw):
        raise AttemptError("ATTEMPT_RAW_PREDICTIONS_HASH_MISMATCH")
    projection = {key: value for key, value in manifest.items() if key != "attempt_sha256"}
    if manifest.get("attempt_sha256") != sha256_bytes(canonical_json_bytes(projection)):
        raise AttemptError("ATTEMPT_DIGEST_MISMATCH")
    bindings = manifest.get("bindings")
    if not isinstance(bindings, dict) or bindings.get("raw_predictions_sha256") != manifest["raw_predictions_sha256"]:
        raise AttemptError("ATTEMPT_BINDINGS_INVALID")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        raise AttemptError("ATTEMPT_ARTIFACTS_INVALID")
    expected = set(_BASE_ARTIFACTS)
    if role in {"formal", "completed_with_warnings"}:
        expected.update(_SCORE_ARTIFACTS)
    if set(artifacts) != expected:
        raise AttemptError("ATTEMPT_ARTIFACT_SET_INVALID")
    artifact_bytes: dict[str, bytes] = {}
    for name, identity in artifacts.items():
        if not isinstance(identity, dict) or set(identity) != {"sha256", "byte_length"}:
            raise AttemptError("ATTEMPT_ARTIFACTS_INVALID")
        try:
            content = _read_attempt_file(
                attempt_root=attempt_root, name=name, code="ATTEMPT_ARTIFACT_INVALID"
            )
            parsed = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise AttemptError("ATTEMPT_ARTIFACT_INVALID") from error
        if canonical_json_bytes(parsed) != content or identity.get("sha256") != sha256_bytes(content) or identity.get("byte_length") != len(content):
            raise AttemptError("ATTEMPT_ARTIFACT_HASH_MISMATCH")
        artifact_bytes[name] = content
    _verify_replay(
        manifest=manifest,
        artifact_bytes=artifact_bytes,
        raw=raw,
        adapter_batch=adapter_batch,
        schema_raw=schema_raw,
    )
    return {"attempt_sha256": manifest["attempt_sha256"], "role": role, "status": status}
