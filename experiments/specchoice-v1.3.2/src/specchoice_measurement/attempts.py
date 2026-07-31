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


class AttemptError(ValueError):
    """Stable custody or validation diagnostic for a terminal attempt."""


_ATTEMPT_KEYS = frozenset({
    "artifacts", "attempt_id", "attempt_sha256", "bindings", "raw_predictions_base64",
    "raw_predictions_sha256", "role", "schema_version", "status",
})
_SCORE_ARTIFACTS = ("case-outcomes.json", "metrics.json", "report.json")
_BASE_ARTIFACTS = ("diagnostics.json", "parsed-predictions.json")
_VALID_ROLES = frozenset({"formal", "diagnostic_only", "invalid_preflight", "completed_with_warnings"})


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


def _bindings(inputs: Mapping[str, object], raw_predictions: bytes) -> dict[str, object]:
    batch = inputs.get("adapter_batch")
    schema_path = inputs.get("schema_path")
    if batch is None or not isinstance(schema_path, Path):
        raise AttemptError("ATTEMPT_INPUTS_INCOMPLETE")
    try:
        schema_raw = schema_path.read_bytes()
    except OSError as error:
        raise AttemptError("ATTEMPT_SCHEMA_UNREADABLE") from error
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
        validate_measurement_attempt(attempt_root=temporary)
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


def _canonical_manifest(path: Path) -> dict[str, object]:
    try:
        raw = path.read_bytes()
        manifest = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AttemptError("ATTEMPT_MANIFEST_INVALID") from error
    if not isinstance(manifest, dict) or canonical_json_bytes(manifest) != raw or set(manifest) != _ATTEMPT_KEYS:
        raise AttemptError("ATTEMPT_MANIFEST_INVALID")
    return manifest


def validate_measurement_attempt(*, attempt_root: Path) -> dict[str, object]:
    """Validate raw-byte recovery, non-cyclic manifest digest, and every sibling binding."""
    manifest = _canonical_manifest(attempt_root / "attempt.json")
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
    for name, identity in artifacts.items():
        if not isinstance(identity, dict) or set(identity) != {"sha256", "byte_length"}:
            raise AttemptError("ATTEMPT_ARTIFACTS_INVALID")
        try:
            content = (attempt_root / name).read_bytes()
            parsed = json.loads(content.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise AttemptError("ATTEMPT_ARTIFACT_INVALID") from error
        if canonical_json_bytes(parsed) != content or identity.get("sha256") != sha256_bytes(content) or identity.get("byte_length") != len(content):
            raise AttemptError("ATTEMPT_ARTIFACT_HASH_MISMATCH")
    return {"attempt_sha256": manifest["attempt_sha256"], "role": role, "status": status}
