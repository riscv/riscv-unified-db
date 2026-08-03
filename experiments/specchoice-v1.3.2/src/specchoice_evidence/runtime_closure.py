# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Deterministic, local-only byte custody for executable closure receipts."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path

from .canonical import canonical_json_bytes, require_byte_length, require_sha256, sha256_bytes
from .filesystem import require_relative_posix_path


class RuntimeClosureError(ValueError):
    """Stable failure for an executable closure mismatch."""


_EXPERIMENT_PREFIX = "experiments/specchoice-v1.3.2"
_ACCEPTED_V3 = (
    f"{_EXPERIMENT_PREFIX}/bundles/accepted/"
    "source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v3"
)
_REGISTRY_V6 = f"{_EXPERIMENT_PREFIX}/config/fixture-registry-pr2164-v6.json"
_REPAIR_MANIFEST_V5 = (
    f"{_EXPERIMENT_PREFIX}/config/fixture-repairs/"
    "pr2164-semantic-gold-v5/repair-manifest.json"
)

# This is intentionally code authority, not proposal authority.  A proposal can
# repeat this inventory but cannot add, remove, reorder, or relabel one target.
_FUTURE_TARGETS_V6: tuple[tuple[str, str], ...] = (
    ("construction_decision", f"{_EXPERIMENT_PREFIX}/receipts/source-contract-construction-decision-v6-pr2164-semantic-gold-executable-closure-verifier-rooted-v6.json"),
    ("candidate", f"{_EXPERIMENT_PREFIX}/bundles/candidates/source-contract-v6-pr2164-semantic-gold-executable-closure-verifier-rooted-v6"),
    ("candidate_audit", f"{_EXPERIMENT_PREFIX}/receipts/source-contract-v6-pr2164-semantic-gold-executable-closure-verifier-rooted-v6/candidate-audit-v6.json"),
    ("acceptance_request", f"{_EXPERIMENT_PREFIX}/receipts/local-acceptance-request-v13.json"),
    ("acceptance_decision", f"{_EXPERIMENT_PREFIX}/receipts/local-acceptance-decision-v13.json"),
    ("accepted_bundle", f"{_EXPERIMENT_PREFIX}/bundles/accepted/source-contract-v6-pr2164-semantic-gold-executable-closure-verifier-rooted-v6"),
    ("historical_authority", f"{_EXPERIMENT_PREFIX}/phase2/source-authority-v13-historical.json"),
    ("pending_authority", f"{_EXPERIMENT_PREFIX}/phase2/source-authority-v13-pending.json"),
    ("transition", f"{_EXPERIMENT_PREFIX}/receipts/pending/fixture-closure-transition-v3-to-v6.json"),
    ("readiness", f"{_EXPERIMENT_PREFIX}/receipts/pending/source-cutover-readiness-v13.json"),
    ("revocation", f"{_EXPERIMENT_PREFIX}/receipts/fixture-closure-revocation-v3-to-v6.json"),
    ("acceptance_audit", f"{_EXPERIMENT_PREFIX}/receipts/fixture-closure-acceptance-audit-v6.json"),
    ("offline_replay", f"{_EXPERIMENT_PREFIX}/receipts/fixture-closure-offline-replay-v6.json"),
    ("integrity", f"{_EXPERIMENT_PREFIX}/receipts/integrity-receipt-v14.json"),
    ("adapter_batch", f"{_EXPERIMENT_PREFIX}/reports/h1/adapter-batch-pr2164-v5.json"),
    ("formal_attempt", f"{_EXPERIMENT_PREFIX}/runs/measurement-attempts/formal-golden-pr2164-v5"),
    ("adversarial", f"{_EXPERIMENT_PREFIX}/reports/h1/adversarial-oracle-results-v6.json"),
    ("h1_packet", f"{_EXPERIMENT_PREFIX}/reports/h1/h1-source-gold-review-v6"),
    ("h1_readiness", f"{_EXPERIMENT_PREFIX}/receipts/h1-review-readiness-v6.json"),
    ("h1_decision", f"{_EXPERIMENT_PREFIX}/reviews/h1-source-gold-decision-v5.json"),
    ("phase1_verification", ".planning/phases/01-isolated-evidence-boundary-and-source-integrity/01-VERIFICATION-02-19.md"),
    ("phase1_review", ".planning/phases/01-isolated-evidence-boundary-and-source-integrity/01-REVIEW-02-19.md"),
    ("phase2_verification", ".planning/phases/02-deterministic-measurement-spine/02-VERIFICATION-02-19.md"),
    ("phase2_review", ".planning/phases/02-deterministic-measurement-spine/02-REVIEW-02-19.md"),
    ("summary", ".planning/phases/02-deterministic-measurement-spine/02-19-SUMMARY.md"),
)

_KNOWN_RUNTIME_PATHS_V2 = (
    # Evidence and measurement implementation.
    *(
        f"{_EXPERIMENT_PREFIX}/src/{package}/{name}.py"
        for package, names in (
            ("specchoice_evidence", ("__init__", "baseline", "bundle", "canonical", "cli", "environment", "filesystem", "git_proof", "receipt", "runtime_closure", "source_contract", "successor", "verify")),
            ("specchoice_measurement", ("__init__", "adapter", "attempts", "cli", "diagnostics", "domain", "final_reports", "h1", "preflight", "scoring", "strict_json")),
        )
        for name in names
    ),
    # Every focused test and both the historical and successor exact oracle.
    *(
        f"{_EXPERIMENT_PREFIX}/tests/{name}"
        for name in (
            "test_source_contract.py", "test_fixture_closure.py", "test_filesystem_boundary.py",
            "test_measurement_adapter.py", "test_measurement_scoring.py", "test_measurement_parsing.py",
            "test_measurement_attempts.py", "test_measurement_h1.py",
            "phase1_expected_red_oracle.py", "phase1_expected_red_oracle_v2.py",
        )
    ),
    _REGISTRY_V6,
    _REPAIR_MANIFEST_V5,
    f"{_EXPERIMENT_PREFIX}/reviews/h1-source-gold-ontology-decision-v1.json",
    f"{_EXPERIMENT_PREFIX}/config/measurement/pr2164-semantic-gold-contract-v2.json",
    f"{_EXPERIMENT_PREFIX}/config/measurement/pr2164-adapter-rules-v3.json",
    f"{_EXPERIMENT_PREFIX}/config/measurement/canonical-adjudication-schema-v3.json",
    f"{_EXPERIMENT_PREFIX}/config/measurement/h1-semantic-review-questions-v2.json",
    f"{_EXPERIMENT_PREFIX}/config/measurement/h1-review-schema-v4.json",
    f"{_EXPERIMENT_PREFIX}/fixtures/measurement/golden-predictions-v4.json",
    f"{_EXPERIMENT_PREFIX}/fixtures/measurement/adversarial/required-diagnostics-v4.json",
    f"{_EXPERIMENT_PREFIX}/receipts/source-contract-construction-authorization-v4-non-executable-supersession-v1.json",
    f"{_EXPERIMENT_PREFIX}/receipts/runtime-executable-closure-v1.json",
    f"{_EXPERIMENT_PREFIX}/receipts/source-contract-proposal-v5-pr2164-semantic-gold-executable-closure-verifier-rooted-v5.json",
    f"{_EXPERIMENT_PREFIX}/receipts/source-contract-construction-proposal-v5-supersession-v4.json",
    f"{_EXPERIMENT_PREFIX}/receipts/source-contract-construction-proposal-v5-non-executable-supersession-v1.json",
    f"{_ACCEPTED_V3}/snapshot-manifest.json",
    ".planning/ROADMAP.md",
    ".planning/REQUIREMENTS.md",
    ".planning/phases/01-isolated-evidence-boundary-and-source-integrity/01-VERIFICATION.md",
    ".planning/phases/01-isolated-evidence-boundary-and-source-integrity/01-REVIEW.md",
    ".planning/phases/02-deterministic-measurement-spine/02-VERIFICATION.md",
    ".planning/phases/02-deterministic-measurement-spine/02-REVIEW.md",
    ".planning/phases/02-deterministic-measurement-spine/02-19-PLAN.md",
)

_DYNAMIC_IMPORTS = (
    "specchoice_evidence.bundle", "specchoice_evidence.cli", "specchoice_evidence.runtime_closure",
    "specchoice_evidence.source_contract", "specchoice_evidence.successor",
    "specchoice_measurement.adapter", "specchoice_measurement.attempts", "specchoice_measurement.cli",
    "specchoice_measurement.final_reports", "specchoice_measurement.h1", "specchoice_measurement.scoring",
)

_FORBIDDEN_AMBIENT_TOOL_ENV = ("GIT_OPTIONAL_LOCKS", "RUBYOPT", "RUBYLIB")


def _require_clean_tool_environment() -> dict[str, str]:
    """Reject ambient Git/Ruby injection before constructing or checking custody."""
    projection = {name: os.environ.get(name, "") for name in _FORBIDDEN_AMBIENT_TOOL_ENV}
    if any(projection.values()):
        raise RuntimeClosureError("RUNTIME_CLOSURE_TOOL_ENVIRONMENT_DIRTY")
    return projection


def _git_environment() -> dict[str, str]:
    return {
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
    }


def _ruby_environment() -> dict[str, str]:
    return {
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "RUBYLIB": "",
        "RUBYOPT": "",
    }


def future_target_inventory_v6() -> list[dict[str, str]]:
    """Return the typed, canonical future target inventory reconstructed from code."""
    return [
        {"kind": kind, "path": path}
        for kind, path in sorted(_FUTURE_TARGETS_V6, key=lambda item: item[1])
    ]


def closure_entry(root: Path, relative_path: str) -> dict[str, object]:
    """Capture one existing ordinary file using an experiment-relative path."""
    try:
        normalized = str(require_relative_posix_path(relative_path))
        candidate = (root / normalized).resolve(strict=True)
        root_real = root.resolve(strict=True)
    except (OSError, ValueError) as error:
        raise RuntimeClosureError("RUNTIME_CLOSURE_PATH_INVALID") from error
    if candidate == root_real or root_real not in candidate.parents or not candidate.is_file():
        raise RuntimeClosureError("RUNTIME_CLOSURE_PATH_INVALID")
    raw = candidate.read_bytes()
    return {"byte_length": len(raw), "path": normalized, "sha256": sha256_bytes(raw)}


def build_runtime_closure(root: Path, relative_paths: list[str]) -> dict[str, object]:
    """Freeze an exact, sorted finite file inventory for later no-write preflight."""
    if not isinstance(relative_paths, list) or not relative_paths:
        raise RuntimeClosureError("RUNTIME_CLOSURE_INPUT_INVALID")
    try:
        normalized = sorted(str(require_relative_posix_path(path)) for path in relative_paths)
    except (TypeError, ValueError) as error:
        raise RuntimeClosureError("RUNTIME_CLOSURE_INPUT_INVALID") from error
    if len(set(normalized)) != len(normalized):
        raise RuntimeClosureError("RUNTIME_CLOSURE_INPUT_INVALID")
    return {
        "entries": [closure_entry(root, path) for path in normalized],
        "schema_version": "runtime-executable-closure-v1",
    }


def verify_runtime_closure(closure: object, root: Path) -> dict[str, object]:
    """Prove every bound entry still has exactly the frozen bytes before mutation."""
    if not isinstance(closure, Mapping) or closure.get("schema_version") != "runtime-executable-closure-v1":
        raise RuntimeClosureError("RUNTIME_CLOSURE_INVALID")
    entries = closure.get("entries")
    if not isinstance(entries, list) or not entries:
        raise RuntimeClosureError("RUNTIME_CLOSURE_INVALID")
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, Mapping) or set(entry) != {"byte_length", "path", "sha256"}:
            raise RuntimeClosureError("RUNTIME_CLOSURE_ENTRY_INVALID")
        try:
            path = str(require_relative_posix_path(entry["path"]))
            length = require_byte_length(entry["byte_length"])
            digest = require_sha256(entry["sha256"])
        except (KeyError, ValueError) as error:
            raise RuntimeClosureError("RUNTIME_CLOSURE_ENTRY_INVALID") from error
        if path in seen:
            raise RuntimeClosureError("RUNTIME_CLOSURE_ENTRY_INVALID")
        seen.add(path)
        current = closure_entry(root, path)
        if current["byte_length"] != length or current["sha256"] != digest:
            raise RuntimeClosureError("RUNTIME_CLOSURE_ENTRY_MISMATCH")
    return dict(closure)


def validate_v6_preflight_inventory(
    *, root: Path, input_paths: list[str], target_paths: list[str],
) -> dict[str, object]:
    """Read every frozen input and prove every future target is absent.

    This is deliberately independent of a proposal's self-declared ``targets``
    field: callers supply the inventory reconstructed from frozen config/code.
    It is used by every v6/v13 preflight before a writer is allowed to open a
    candidate, receipt, authority, or report target.
    """
    if not isinstance(input_paths, list) or not input_paths or not isinstance(target_paths, list) or not target_paths:
        raise RuntimeClosureError("RUNTIME_CLOSURE_INVENTORY_INVALID")
    try:
        inputs = sorted(str(require_relative_posix_path(path)) for path in input_paths)
        targets = sorted(str(require_relative_posix_path(path)) for path in target_paths)
    except (TypeError, ValueError) as error:
        raise RuntimeClosureError("RUNTIME_CLOSURE_INVENTORY_INVALID") from error
    if len(inputs) != len(set(inputs)) or len(targets) != len(set(targets)) or set(inputs) & set(targets):
        raise RuntimeClosureError("RUNTIME_CLOSURE_INVENTORY_INVALID")
    # ``closure_entry`` consumes and hashes the current bytes; callers retain
    # the returned evidence in their decision/proposal validator.
    evidence = [closure_entry(root, path) for path in inputs]
    root_real = root.resolve(strict=True)
    for path in targets:
        candidate = root_real / path
        if candidate.exists() or candidate.is_symlink():
            raise RuntimeClosureError("RUNTIME_CLOSURE_TARGET_OCCUPIED")
    return {"inputs": evidence, "targets": targets}


def no_user_site_environment() -> dict[str, str]:
    """Return the only environment projection accepted by closure preflights."""
    return {
        "PYTHONDONTWRITEBYTECODE": os.environ.get("PYTHONDONTWRITEBYTECODE", ""),
        "PYTHONNOUSERSITE": os.environ.get("PYTHONNOUSERSITE", ""),
        "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
    }


def _canonical_object(path: Path, diagnostic: str) -> dict[str, object]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeClosureError(diagnostic) from error
    if not isinstance(value, dict) or canonical_json_bytes(value) != raw:
        raise RuntimeClosureError(diagnostic)
    return value


def _repository_relative(repository: Path, path: Path) -> str:
    try:
        return path.resolve(strict=True).relative_to(repository.resolve(strict=True)).as_posix()
    except (OSError, ValueError) as error:
        raise RuntimeClosureError("RUNTIME_CLOSURE_PATH_INVALID") from error


def _run(command: list[str], *, cwd: Path, env: Mapping[str, str] | None = None) -> bytes:
    try:
        completed = subprocess.run(
            command, cwd=cwd, env=dict(env) if env is not None else None,
            check=False, capture_output=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeClosureError("RUNTIME_CLOSURE_TOOL_UNAVAILABLE") from error
    if completed.returncode != 0 or len(completed.stdout) > 4 * 1024 * 1024 or len(completed.stderr) > 64 * 1024:
        raise RuntimeClosureError("RUNTIME_CLOSURE_TOOL_UNAVAILABLE")
    return completed.stdout


def _file_identity(path: Path) -> dict[str, object]:
    try:
        resolved = path.resolve(strict=True)
        if not resolved.is_file():
            raise OSError
        raw = resolved.read_bytes()
    except OSError as error:
        raise RuntimeClosureError("RUNTIME_CLOSURE_TOOL_UNAVAILABLE") from error
    return {"byte_length": len(raw), "path": os.fspath(resolved), "sha256": sha256_bytes(raw)}


def _fresh_python_discovery(experiment: Path) -> dict[str, object]:
    script = (
        "import importlib,json,sys\n"
        f"names={list(_DYNAMIC_IMPORTS)!r}\n"
        "[importlib.import_module(name) for name in names]\n"
        "items=[]\n"
        "for name,module in sorted(sys.modules.items()):\n"
        " p=getattr(module,'__file__',None)\n"
        " if isinstance(p,str): items.append({'module':name,'origin':p})\n"
        "print(json.dumps(items,sort_keys=True,separators=(',',':')))\n"
    )
    environment = {
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTHONPATH": os.fspath((experiment / "src").resolve(strict=True)),
    }
    argv = [os.fspath(Path(sys.executable).resolve(strict=True)), "-B", "-c", script]
    raw = _run(argv, cwd=experiment, env=environment)
    try:
        discovered = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeClosureError("RUNTIME_CLOSURE_PYTHON_DISCOVERY_INVALID") from error
    if not isinstance(discovered, list):
        raise RuntimeClosureError("RUNTIME_CLOSURE_PYTHON_DISCOVERY_INVALID")
    origins: list[dict[str, object]] = []
    for item in discovered:
        if not isinstance(item, dict) or set(item) != {"module", "origin"}:
            raise RuntimeClosureError("RUNTIME_CLOSURE_PYTHON_DISCOVERY_INVALID")
        origin = Path(str(item["origin"]))
        if not origin.exists() or not origin.is_file():
            continue
        identity = _file_identity(origin)
        origins.append({"module": item["module"], **identity})
    origins.sort(key=lambda item: (str(item["path"]), str(item["module"])))
    return {
        "discovery_argv": argv,
        "discovery_environment": environment,
        "module_origins": origins,
    }


def _tool_identities(repository: Path, experiment: Path) -> dict[str, object]:
    _require_clean_tool_environment()
    python = _file_identity(Path(sys.executable))
    python.update({
        "cache_tag": sys.implementation.cache_tag,
        "implementation": sys.implementation.name,
        "version": platform.python_version(),
        "version_info": list(sys.version_info[:5]),
        **_fresh_python_discovery(experiment),
    })

    git_name = shutil.which("git")
    ruby_name = shutil.which("ruby")
    if git_name is None or ruby_name is None:
        raise RuntimeClosureError("RUNTIME_CLOSURE_TOOL_UNAVAILABLE")
    git_path = Path(git_name).resolve(strict=True)
    git_argv = [os.fspath(git_path), "--version"]
    git = {
        **_file_identity(git_path),
        "argv": git_argv,
        "environment": _git_environment(),
        "version_output": _run(
            git_argv, cwd=repository, env=_git_environment()
        ).decode("utf-8", "strict").rstrip("\n"),
    }

    ruby_path = Path(ruby_name).resolve(strict=True)
    ruby_script = (
        "require 'json'; require 'psych'; "
        "puts JSON.generate({'ruby_version'=>RUBY_VERSION,'ruby_description'=>RUBY_DESCRIPTION,"
        "'psych_version'=>Psych::VERSION,'loaded_features'=>$LOADED_FEATURES.select{|p| File.file?(p)}.sort})"
    )
    ruby_argv = [os.fspath(ruby_path), "-e", ruby_script]
    try:
        ruby_projection = json.loads(
            _run(ruby_argv, cwd=repository, env=_ruby_environment()).decode("utf-8")
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeClosureError("RUNTIME_CLOSURE_RUBY_DISCOVERY_INVALID") from error
    if not isinstance(ruby_projection, dict) or not isinstance(ruby_projection.get("loaded_features"), list):
        raise RuntimeClosureError("RUNTIME_CLOSURE_RUBY_DISCOVERY_INVALID")
    libraries = [_file_identity(Path(path)) for path in ruby_projection["loaded_features"]]
    libraries.sort(key=lambda item: str(item["path"]))
    ruby = {
        **_file_identity(ruby_path),
        "argv": ruby_argv,
        "environment": _ruby_environment(),
        "loaded_libraries": libraries,
        "psych_version": ruby_projection.get("psych_version"),
        "ruby_description": ruby_projection.get("ruby_description"),
        "ruby_version": ruby_projection.get("ruby_version"),
    }
    return {"git": git, "python": python, "ruby_psych": ruby}


def _git(repository: Path, *arguments: str) -> bytes:
    git_name = shutil.which("git")
    if git_name is None:
        raise RuntimeClosureError("RUNTIME_CLOSURE_TOOL_UNAVAILABLE")
    return _run(
        [os.fspath(Path(git_name).resolve(strict=True)), "-C", os.fspath(repository), *arguments],
        cwd=repository,
        env=_git_environment(),
    )


def _referenced_runtime_paths_v2(repository: Path) -> dict[str, set[str]]:
    """Reconstruct every path from accepted-v3 and registry-v6 independently."""
    classes: dict[str, set[str]] = {}

    def add(path: str, kind: str) -> None:
        try:
            normalized = require_relative_posix_path(path).as_posix()
        except ValueError as error:
            raise RuntimeClosureError("RUNTIME_CLOSURE_PATH_INVALID") from error
        classes.setdefault(normalized, set()).add(kind)

    for path in _KNOWN_RUNTIME_PATHS_V2:
        add(path, "known_mandatory")

    accepted_root = repository / _ACCEPTED_V3
    snapshot = _canonical_object(accepted_root / "snapshot-manifest.json", "RUNTIME_CLOSURE_ACCEPTED_V3_INVALID")
    core = snapshot.get("content_manifest_core")
    if not isinstance(core, dict):
        raise RuntimeClosureError("RUNTIME_CLOSURE_ACCEPTED_V3_INVALID")
    referenced: list[str] = []
    snapshots = core.get("snapshots")
    artifacts = core.get("bundle_artifacts")
    if not isinstance(snapshots, list) or not isinstance(artifacts, list):
        raise RuntimeClosureError("RUNTIME_CLOSURE_ACCEPTED_V3_INVALID")
    for item in snapshots:
        if not isinstance(item, dict) or not isinstance(item.get("consumed_files"), list):
            raise RuntimeClosureError("RUNTIME_CLOSURE_ACCEPTED_V3_INVALID")
        for entry in item["consumed_files"]:
            if not isinstance(entry, dict) or not isinstance(entry.get("local_bundle_path"), str):
                raise RuntimeClosureError("RUNTIME_CLOSURE_ACCEPTED_V3_INVALID")
            referenced.append(entry["local_bundle_path"])
    for entry in artifacts:
        if not isinstance(entry, dict) or not isinstance(entry.get("local_bundle_path"), str):
            raise RuntimeClosureError("RUNTIME_CLOSURE_ACCEPTED_V3_INVALID")
        referenced.append(entry["local_bundle_path"])
    if len(referenced) != 34 or len(set(referenced)) != 34:
        raise RuntimeClosureError("RUNTIME_CLOSURE_ACCEPTED_V3_INVENTORY_INVALID")
    for relative in referenced:
        add(f"{_ACCEPTED_V3}/{require_relative_posix_path(relative).as_posix()}", "accepted_v3_referenced_file")

    registry = _canonical_object(repository / _REGISTRY_V6, "RUNTIME_CLOSURE_REGISTRY_V6_INVALID")
    entries = registry.get("file_entries")
    if registry.get("raw_file_count") != 29 or not isinstance(entries, list) or len(entries) != 29:
        raise RuntimeClosureError("RUNTIME_CLOSURE_REGISTRY_V6_INVALID")
    registry_paths: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("origin") not in {"accepted-v3", "repair-v5"} or not isinstance(entry.get("path"), str):
            raise RuntimeClosureError("RUNTIME_CLOSURE_REGISTRY_V6_INVALID")
        source = (
            f"{_ACCEPTED_V3}/{entry['path']}"
            if entry["origin"] == "accepted-v3"
            else f"{_EXPERIMENT_PREFIX}/{entry['path']}"
        )
        add(source, "registry_v6_raw_input")
        registry_paths.add(source)
    if len(registry_paths) != 29:
        raise RuntimeClosureError("RUNTIME_CLOSURE_REGISTRY_V6_INVALID")

    repair = _canonical_object(repository / _REPAIR_MANIFEST_V5, "RUNTIME_CLOSURE_REPAIR_MANIFEST_INVALID")
    payloads = repair.get("payloads")
    if repair.get("payload_count") != 9 or not isinstance(payloads, list) or len(payloads) != 9:
        raise RuntimeClosureError("RUNTIME_CLOSURE_REPAIR_MANIFEST_INVALID")
    for item in payloads:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise RuntimeClosureError("RUNTIME_CLOSURE_REPAIR_MANIFEST_INVALID")
        add(f"{_EXPERIMENT_PREFIX}/{item['path']}", "repair_v5_payload")

    return classes


def _git_bound_entry(repository: Path, freeze_commit: str, relative_path: str, kinds: set[str]) -> dict[str, object]:
    entry = closure_entry(repository, relative_path)
    try:
        blob_oid = _git(repository, "rev-parse", f"{freeze_commit}:{relative_path}").decode("ascii").strip()
        if len(blob_oid) not in {40, 64}:
            raise ValueError
        int(blob_oid, 16)
        committed = _git(repository, "cat-file", "blob", blob_oid)
    except RuntimeClosureError as error:
        raise RuntimeClosureError("RUNTIME_CLOSURE_UNCOMMITTED_INPUT") from error
    except (UnicodeDecodeError, ValueError) as error:
        raise RuntimeClosureError("RUNTIME_CLOSURE_GIT_BLOB_OID_INVALID") from error
    if committed != (repository / relative_path).read_bytes():
        raise RuntimeClosureError("RUNTIME_CLOSURE_UNCOMMITTED_INPUT")
    return {**entry, "classes": sorted(kinds), "git_blob_oid": blob_oid}


def build_runtime_closure_v2(repository: Path, *, freeze_commit: str | None = None) -> dict[str, object]:
    """Build the transitive, tool-bound successor closure from code authority."""
    ambient_tool_environment = _require_clean_tool_environment()
    repository = repository.resolve(strict=True)
    experiment = repository / _EXPERIMENT_PREFIX
    if freeze_commit is None:
        freeze_commit = _git(repository, "rev-parse", "HEAD").decode("ascii").strip()
    if not isinstance(freeze_commit, str) or len(freeze_commit) != 40:
        raise RuntimeClosureError("RUNTIME_CLOSURE_FREEZE_COMMIT_INVALID")
    try:
        int(freeze_commit, 16)
    except ValueError as error:
        raise RuntimeClosureError("RUNTIME_CLOSURE_FREEZE_COMMIT_INVALID") from error
    _git(repository, "cat-file", "-e", f"{freeze_commit}^{{commit}}")

    classes = _referenced_runtime_paths_v2(repository)
    discovery = _fresh_python_discovery(experiment)
    for origin in discovery["module_origins"]:
        assert isinstance(origin, dict)
        try:
            relative = Path(str(origin["path"])).resolve(strict=True).relative_to(repository).as_posix()
        except ValueError:
            continue
        classes.setdefault(relative, set()).add("dynamic_python_module")
    entries = [_git_bound_entry(repository, freeze_commit, path, kinds) for path, kinds in sorted(classes.items())]
    return {
        "entries": entries,
        "freeze_commit": freeze_commit,
        "future_targets": future_target_inventory_v6(),
        "roots": {
            "experiment": _repository_relative(repository, experiment),
            "repository": os.fspath(repository),
        },
        "ambient_tool_environment": ambient_tool_environment,
        "schema_version": "runtime-executable-closure-v2",
        "tools": _tool_identities(repository, experiment),
    }


def verify_runtime_closure_v2(closure: object, repository: Path) -> dict[str, object]:
    """Rebuild the complete closure and reject any file, tool, env, or target drift."""
    if not isinstance(closure, Mapping) or closure.get("schema_version") != "runtime-executable-closure-v2":
        raise RuntimeClosureError("RUNTIME_CLOSURE_V2_INVALID")
    freeze_commit = closure.get("freeze_commit")
    if not isinstance(freeze_commit, str):
        raise RuntimeClosureError("RUNTIME_CLOSURE_V2_INVALID")
    rebuilt = build_runtime_closure_v2(repository, freeze_commit=freeze_commit)
    if dict(closure) != rebuilt:
        raise RuntimeClosureError("RUNTIME_CLOSURE_V2_MISMATCH")
    return rebuilt


def validate_future_target_occupancy_v6(
    repository: Path, *, allowed_existing: set[str] | frozenset[str] = frozenset(),
) -> list[dict[str, str]]:
    """Reject occupied, missing-from-code, or caller-invented future outputs."""
    expected = future_target_inventory_v6()
    expected_paths = {entry["path"] for entry in expected}
    if not isinstance(allowed_existing, (set, frozenset)) or not allowed_existing <= expected_paths:
        raise RuntimeClosureError("V6_TARGET_OCCUPANCY_ALLOWLIST_INVALID")
    for entry in expected:
        path = entry["path"]
        occupied = (repository / path).exists() or (repository / path).is_symlink()
        if occupied != (path in allowed_existing):
            raise RuntimeClosureError("V6_TARGET_OCCUPANCY_MISMATCH")
    return expected
