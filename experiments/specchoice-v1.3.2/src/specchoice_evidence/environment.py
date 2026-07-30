# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Standalone-first environment identity and non-canonical audit evidence."""

from __future__ import annotations

import datetime as datetime_module
import os
import platform
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .canonical import canonical_json_bytes, sha256_bytes


class EnvironmentError(ValueError):
    """A stable failure while observing the dependency-light environment."""


@dataclass(frozen=True)
class EnvironmentObservation:
    """Stable tool identity fields allowed in the canonical decision."""

    python_implementation: str
    python_version: str
    git_implementation: str
    git_version: str


_GIT_VERSION_RE = re.compile(r"^git version ([0-9]+(?:\.[0-9]+)+(?:[A-Za-z0-9.+-]*)?)$")
_SENSITIVE_KEY_RE = re.compile(r"(?:credential|password|secret|token)", re.IGNORECASE)
_SENSITIVE_ARGUMENT_RE = re.compile(r"(?i)(--(?:credential|password|secret|token)(?:=|\s+))\S+")


def observe_environment() -> EnvironmentObservation:
    """Observe only CPython and Git CLI identities; never probe the UDB toolchain."""
    completed = subprocess.run(
        ["git", "--version"],
        check=False,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    match = _GIT_VERSION_RE.fullmatch(completed.stdout.strip())
    if completed.returncode != 0 or match is None:
        raise EnvironmentError("GIT_VERSION_OBSERVATION_FAILED")
    return EnvironmentObservation(
        python_implementation=platform.python_implementation(),
        python_version=".".join(str(component) for component in sys.version_info[:3]),
        git_implementation="git",
        git_version=match.group(1),
    )


def build_environment_decision(observation: EnvironmentObservation) -> dict[str, Any]:
    """Return the versioned, stable canonical projection for a normal success route."""
    if observation.python_implementation != "CPython":
        raise EnvironmentError("UNSUPPORTED_PYTHON_IMPLEMENTATION")
    if observation.git_implementation != "git":
        raise EnvironmentError("UNSUPPORTED_GIT_IMPLEMENTATION")
    return {
        "capabilities": {
            "construction": ["git_cli_for_construction", "python_standard_library"],
            "downstream": ["offline_bundle_access", "python_standard_library"],
        },
        "fallback_ceiling_status": "not_started",
        "fallback_policy": {
            "ceiling_minutes": 90,
            "retries_reset_clock": False,
            "timing_mode": "cumulative_wall_clock",
            "waits_pause_clock": False,
        },
        "fallback_triggered": False,
        "full_udb_setup": {"attempted": False, "required": False},
        "incident": {"error_codes": [], "outcome": "not_triggered", "triggered": False},
        "outcome": "success",
        "route": "standalone_first",
        "schema_version": "1",
        "tools": {
            "git_cli": {"implementation": observation.git_implementation, "version": observation.git_version},
            "python": {"implementation": observation.python_implementation, "version": observation.python_version},
        },
    }


def build_default_decision(observation: EnvironmentObservation | None = None) -> dict[str, Any]:
    """Build the normal route decision without treating it as a fallback."""
    return build_environment_decision(observation or observe_environment())


def _sanitize_audit_value(value: Any) -> Any:
    if isinstance(value, str):
        sanitized = _SENSITIVE_ARGUMENT_RE.sub(r"\1<redacted>", value)
        return "<absolute-path>" if os.path.isabs(sanitized) else sanitized
    if isinstance(value, list):
        return [_sanitize_audit_value(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _sanitize_audit_value(item)
            for key, item in value.items()
            if _SENSITIVE_KEY_RE.search(str(key)) is None
        }
    return value


def build_audit_receipt(
    canonical_decision_sha256: str,
    observation: EnvironmentObservation,
    audit_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return non-canonical operational evidence with a one-way decision reference."""
    metadata = _sanitize_audit_value(dict(audit_metadata or {}))
    return {
        "audit": metadata,
        "canonical_environment_decision_sha256": canonical_decision_sha256,
        "observed_tools": {
            "git_cli": {"implementation": observation.git_implementation, "version": observation.git_version},
            "python": {"implementation": observation.python_implementation, "version": observation.python_version},
        },
        "schema_version": "1",
    }


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)


def write_environment_artifacts(
    decision_path: Path,
    audit_path: Path,
    observation: EnvironmentObservation | None = None,
    audit_metadata: Mapping[str, Any] | None = None,
) -> str:
    """Write the decision before its audit receipt and return the decision digest."""
    current_observation = observation or observe_environment()
    decision_bytes = canonical_json_bytes(build_default_decision(current_observation))
    digest = sha256_bytes(decision_bytes)
    _atomic_write(decision_path, decision_bytes)
    receipt = build_audit_receipt(digest, current_observation, audit_metadata)
    _atomic_write(audit_path, canonical_json_bytes(receipt))
    return digest


def default_audit_metadata(command: str) -> dict[str, Any]:
    """Capture machine-local details solely for the non-canonical audit receipt."""
    return {
        "command": command,
        "hostname": platform.node(),
        "platform": platform.platform(),
        "timestamp": datetime_module.datetime.now(datetime_module.timezone.utc).isoformat(),
        "working_directory": str(Path.cwd()),
    }
