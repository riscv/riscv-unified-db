# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Command boundary for deterministic measurement artifacts."""

from __future__ import annotations

import argparse
import base64
import json
import sys
import tempfile
from copy import deepcopy
from pathlib import Path

from specchoice_evidence.bundle import _sync_directory, _write_exact
from specchoice_evidence.canonical import canonical_json_bytes, sha256_bytes

from .adapter import AdapterError, build_pr2164_adapter_batch
from .attempts import AttemptError, run_measurement_attempt, validate_measurement_attempt
from .h1 import H1Error, build_h1_packet, validate_h1_decision, validate_h1_packet
from .preflight import _source_bytes_by_fixture, preflight_prediction_batch
from .scoring import score_prediction_batch


def command_adapt_pr2164(args: argparse.Namespace) -> int:
    if args.output.exists():
        raise AdapterError("ADAPTER_OUTPUT_ALREADY_EXISTS")
    batch = build_pr2164_adapter_batch(
        authority_path=args.authority,
        bundle_root=args.bundle,
        rules_path=args.rules,
    )
    if not batch.valid:
        raise AdapterError("ADAPTER_BATCH_NOT_SCORE_ELIGIBLE")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_json_bytes(batch.as_dict()))
    sys.stdout.buffer.write(canonical_json_bytes({"adapter_batch_sha256": batch.adapter_batch_sha256, "status": "written"}))
    return 0


def command_run_formal_measurement(args: argparse.Namespace) -> int:
    """Publish only the exact all-11, accepted-v2 golden measurement attempt."""
    raw_predictions = args.predictions.read_bytes()
    batch = build_pr2164_adapter_batch(
        authority_path=args.authority,
        bundle_root=args.bundle,
        rules_path=args.rules,
    )
    if not batch.valid:
        raise AdapterError("ADAPTER_BATCH_NOT_SCORE_ELIGIBLE")
    preflight = preflight_prediction_batch(raw=raw_predictions, adapter_batch=batch, ingress="current-v1")
    score = score_prediction_batch(adapter_batch=batch, preflight=preflight, mode="formal")
    result = run_measurement_attempt(
        mode="formal",
        attempt_id=args.attempt_id,
        attempt_root=args.attempt_root,
        inputs={
            "adapter_batch": batch,
            "ingress": "current-v1",
            "preflight": preflight,
            "raw_predictions": raw_predictions,
            "score_result": score,
            "schema_path": args.schema,
        },
    )
    if result["status"] != "completed":
        raise AttemptError("FORMAL_MEASUREMENT_NOT_CLEAN")
    validated = validate_measurement_attempt(attempt_root=args.attempt_root / args.attempt_id)
    if validated != result:
        raise AttemptError("FORMAL_ATTEMPT_VALIDATION_MISMATCH")
    sys.stdout.buffer.write(canonical_json_bytes(result))
    return 0


def command_validate_attempt(args: argparse.Namespace) -> int:
    sys.stdout.buffer.write(canonical_json_bytes(validate_measurement_attempt(attempt_root=args.attempt)))
    return 0


def _fixture_span(batch: object, fixture_id: str) -> dict[str, object]:
    values = _source_bytes_by_fixture(batch).get(fixture_id, {})
    for digest, raw in values.items():
        for end in range(1, min(len(raw), 4) + 1):
            try:
                text = raw[:end].decode("utf-8")
            except UnicodeDecodeError:
                continue
            return {"source_sha256": digest, "start_byte": 0, "end_byte": end, "text": text}
    raise AttemptError("ADVERSARIAL_INPUT_INVALID")


def _mutate_adversarial_payload(payload: dict[str, object], oracle_id: str, *, negative_span: dict[str, object] | None = None) -> None:
    predictions = payload.get("predictions")
    if not isinstance(predictions, list):
        raise AttemptError("ADVERSARIAL_INPUT_INVALID")
    by_fixture = {item.get("fixture_id"): item for item in predictions if isinstance(item, dict)}
    try:
        positive = by_fixture["POS_CSR_RW_MTVEC_ACCESS"]
        candidate = by_fixture["CAND_WARL_FIXED_LEGAL_SET"]
        negative = by_fixture["NEG_EXT_GATED_PBMTE"]
        positive_adjudication = positive["adjudication"]
        candidate_adjudication = candidate["adjudication"]
        negative_adjudication = negative["adjudication"]
        span = positive_adjudication["evidence_spans"][0]
    except (KeyError, IndexError, TypeError) as error:
        raise AttemptError("ADVERSARIAL_INPUT_INVALID") from error
    if not all(isinstance(item, dict) for item in (positive_adjudication, candidate_adjudication, negative_adjudication, span)):
        raise AttemptError("ADVERSARIAL_INPUT_INVALID")
    mutations = {
        "accepted-parameter-name-missing": lambda: positive_adjudication.update(proposed_name=None),
        "candidate-not-surfaced": lambda: candidate_adjudication.update(surfaced=False, parameter_status=None, evidence_spans=[]),
        "candidate-accepted": lambda: candidate_adjudication.update(parameter_status="accept"),
        "candidate-review": lambda: candidate_adjudication.update(parameter_status="review"),
        "positive-not-surfaced": lambda: positive_adjudication.update(
            surfaced=False, parameter_status=None, proposed_name=None, evidence_spans=[]
        ),
        "positive-classified-out": lambda: positive_adjudication.update(parameter_status="classify_out"),
        "negative-accepted": lambda: negative_adjudication.update(
            surfaced=True, parameter_status="accept", proposed_name="PBMTE", evidence_spans=[deepcopy(negative_span)]
        ),
        "negative-review": lambda: negative_adjudication.update(
            surfaced=True, parameter_status="review", proposed_name=None, evidence_spans=[deepcopy(negative_span)]
        ),
        "evidence-empty": lambda: positive_adjudication.update(evidence_spans=[]),
        "evidence-source-changed": lambda: span.update(source_sha256="0" * 64),
        "evidence-empty-range": lambda: span.update(end_byte=0),
        "evidence-text-mismatch": lambda: span.update(text="changed"),
    }
    try:
        mutations[oracle_id]()
    except KeyError as error:
        raise AttemptError("ADVERSARIAL_ORACLE_UNKNOWN") from error


def _canonical_object(path: Path, code: str) -> tuple[dict[str, object], bytes]:
    try:
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AttemptError(code) from error
    if not isinstance(payload, dict) or canonical_json_bytes(payload) != raw:
        raise AttemptError(code)
    return payload, raw


def _adversarial_bindings(*, batch: object, schema: Path, golden_raw: bytes, formal_attempt_sha256: str) -> dict[str, object]:
    return {
        "adapter_batch_sha256": getattr(batch, "adapter_batch_sha256", None),
        "formal_attempt_sha256": formal_attempt_sha256,
        "golden_predictions_sha256": sha256_bytes(golden_raw),
        "rule_sha256": getattr(batch, "rule_sha256", None),
        "schema_sha256": sha256_bytes(schema.read_bytes()),
        "source_identity": getattr(batch, "source_identity", None),
    }


def command_run_adversarial_oracles(args: argparse.Namespace) -> int:
    """Prove frozen diagnostics in diagnostic-only custody, without formal metrics."""
    formal = validate_measurement_attempt(attempt_root=args.formal_attempt)
    if (formal["role"], formal["status"]) != ("formal", "completed"):
        raise AttemptError("FORMAL_ATTEMPT_NOT_CLEAN")
    oracle, oracle_raw = _canonical_object(args.oracle, "ADVERSARIAL_ORACLE_INVALID")
    entries = oracle.get("oracles")
    if oracle.get("schema_version") != "required-diagnostics-v1" or not isinstance(entries, list) or not entries:
        raise AttemptError("ADVERSARIAL_ORACLE_INVALID")
    golden, golden_raw = _canonical_object(args.predictions, "ADVERSARIAL_INPUT_INVALID")
    batch = build_pr2164_adapter_batch(authority_path=args.authority, bundle_root=args.bundle, rules_path=args.rules)
    if not batch.valid:
        raise AdapterError("ADAPTER_BATCH_NOT_SCORE_ELIGIBLE")
    negative_span = _fixture_span(batch, "NEG_EXT_GATED_PBMTE")
    attempt_root = args.report.parent / f"{args.report.stem}-attempts"
    if args.report.exists() or args.report.is_symlink() or attempt_root.exists() or attempt_root.is_symlink():
        raise AttemptError("ADVERSARIAL_REPORT_EXISTS")
    cases: list[dict[str, object]] = []
    for index, entry in enumerate(entries, start=1):
            if not isinstance(entry, dict) or not isinstance(entry.get("id"), str) or not isinstance(entry.get("expected_diagnostics"), list):
                raise AttemptError("ADVERSARIAL_ORACLE_INVALID")
            payload = deepcopy(golden)
            _mutate_adversarial_payload(payload, entry["id"], negative_span=negative_span)
            raw_predictions = canonical_json_bytes(payload)
            preflight = preflight_prediction_batch(raw=raw_predictions, adapter_batch=batch, ingress="current-v1")
            score = score_prediction_batch(adapter_batch=batch, preflight=preflight, mode="formal")
            observed = [item.as_dict() for item in (preflight.diagnostics if preflight.status == "invalid_preflight" else score.diagnostics)]
            expected = entry["expected_diagnostics"]
            if observed != expected:
                raise AttemptError("ADVERSARIAL_ORACLE_MISMATCH")
            attempt = run_measurement_attempt(
                mode="diagnostic_only",
                attempt_id=f"oracle-{index:02d}",
                attempt_root=attempt_root,
                inputs={
                    "adapter_batch": batch,
                    "ingress": "current-v1",
                    "preflight": preflight,
                    "raw_predictions": raw_predictions,
                    "score_result": score,
                    "schema_path": args.schema,
                },
            )
            if validate_measurement_attempt(attempt_root=attempt_root / f"oracle-{index:02d}") != attempt:
                raise AttemptError("ADVERSARIAL_ATTEMPT_VALIDATION_MISMATCH")
            cases.append({
                "attempt_id": f"oracle-{index:02d}",
                "attempt_sha256": attempt["attempt_sha256"],
                "expected_diagnostics": expected,
                "id": entry["id"],
                "matched": True,
                "observed_diagnostics": observed,
                "raw_predictions_sha256": sha256_bytes(raw_predictions),
                "role": attempt["role"],
                "status": attempt["status"],
            })
    report = {
        "bindings": _adversarial_bindings(
            batch=batch, schema=args.schema, golden_raw=golden_raw, formal_attempt_sha256=str(formal["attempt_sha256"])
        ),
        "cases": cases,
        "oracle_sha256": sha256_bytes(oracle_raw),
        "schema_version": "adversarial-oracle-results-v2",
        "status": "diagnostic_only",
    }
    if args.report.exists() or args.report.is_symlink():
        raise AttemptError("ADVERSARIAL_REPORT_EXISTS")
    try:
        _write_exact(args.report, canonical_json_bytes(report))
        _sync_directory(args.report.parent)
    except FileExistsError as error:
        raise AttemptError("ADVERSARIAL_REPORT_EXISTS") from error
    validate_adversarial_report(report_path=args.report)
    sys.stdout.buffer.write(canonical_json_bytes({"oracle_sha256": report["oracle_sha256"], "status": report["status"]}))
    return 0


def validate_adversarial_report(*, report_path: Path) -> dict[str, object]:
    """Validate the closed, canonical diagnostic-only report against the frozen oracle."""
    report, _ = _canonical_object(report_path, "ADVERSARIAL_REPORT_INVALID")
    expected_keys = {"bindings", "cases", "oracle_sha256", "schema_version", "status"}
    if set(report) != expected_keys or report.get("schema_version") != "adversarial-oracle-results-v2" or report.get("status") != "diagnostic_only":
        raise AttemptError("ADVERSARIAL_REPORT_INVALID")
    experiment_root = Path(__file__).parents[2]
    oracle, oracle_raw = _canonical_object(
        experiment_root / "fixtures/measurement/adversarial/required-diagnostics-v1.json", "ADVERSARIAL_REPORT_INVALID"
    )
    golden_path = experiment_root / "fixtures/measurement/golden-predictions-v1.json"
    schema_path = experiment_root / "config/measurement/canonical-adjudication-schema-v1.json"
    golden, golden_raw = _canonical_object(golden_path, "ADVERSARIAL_REPORT_INVALID")
    batch = build_pr2164_adapter_batch(
        authority_path=experiment_root / "phase2/source-authority.json",
        bundle_root=experiment_root / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2",
        rules_path=experiment_root / "config/measurement/pr2164-adapter-rules-v1.json",
    )
    bindings = report.get("bindings")
    if not batch.valid or not isinstance(bindings, dict) or bindings != _adversarial_bindings(
        batch=batch, schema=schema_path, golden_raw=golden_raw, formal_attempt_sha256=str(bindings.get("formal_attempt_sha256"))
    ):
        raise AttemptError("ADVERSARIAL_REPORT_INVALID")
    expected_entries = oracle.get("oracles")
    cases = report.get("cases")
    if report.get("oracle_sha256") != sha256_bytes(oracle_raw) or not isinstance(expected_entries, list) or not isinstance(cases, list) or len(cases) != len(expected_entries):
        raise AttemptError("ADVERSARIAL_REPORT_INVALID")
    attempt_root = report_path.parent / f"{report_path.stem}-attempts"
    if not attempt_root.is_dir() or attempt_root.is_symlink():
        raise AttemptError("ADVERSARIAL_REPORT_INVALID")
    for entry, case in zip(expected_entries, cases, strict=True):
        if not isinstance(entry, dict) or not isinstance(case, dict) or set(case) != {
            "attempt_id", "attempt_sha256", "expected_diagnostics", "id", "matched", "observed_diagnostics", "raw_predictions_sha256", "role", "status"
        } or case.get("id") != entry.get("id") or case.get("expected_diagnostics") != entry.get("expected_diagnostics") or case.get("observed_diagnostics") != entry.get("expected_diagnostics") or case.get("matched") is not True or (case.get("role"), case.get("status")) != ("diagnostic_only", "diagnostic_only") or not isinstance(case.get("attempt_id"), str) or not isinstance(case.get("attempt_sha256"), str) or len(case["attempt_sha256"]) != 64 or not isinstance(case.get("raw_predictions_sha256"), str) or len(case["raw_predictions_sha256"]) != 64:
            raise AttemptError("ADVERSARIAL_REPORT_INVALID")
        attempt_path = attempt_root / case["attempt_id"]
        validated = validate_measurement_attempt(attempt_root=attempt_path)
        if validated != {"attempt_sha256": case["attempt_sha256"], "role": "diagnostic_only", "status": "diagnostic_only"}:
            raise AttemptError("ADVERSARIAL_REPORT_INVALID")
        manifest, _ = _canonical_object(attempt_path / "attempt.json", "ADVERSARIAL_REPORT_INVALID")
        try:
            raw = base64.b64decode(manifest["raw_predictions_base64"], validate=True)
        except (KeyError, TypeError, ValueError) as error:
            raise AttemptError("ADVERSARIAL_REPORT_INVALID") from error
        payload = deepcopy(golden)
        _mutate_adversarial_payload(payload, str(case["id"]), negative_span=_fixture_span(batch, "NEG_EXT_GATED_PBMTE"))
        if raw != canonical_json_bytes(payload) or sha256_bytes(raw) != case["raw_predictions_sha256"]:
            raise AttemptError("ADVERSARIAL_REPORT_INVALID")
        preflight = preflight_prediction_batch(raw=raw, adapter_batch=batch, ingress="current-v1")
        score = score_prediction_batch(adapter_batch=batch, preflight=preflight, mode="formal")
        observed = [item.as_dict() for item in (preflight.diagnostics if preflight.status == "invalid_preflight" else score.diagnostics)]
        if observed != entry["expected_diagnostics"]:
            raise AttemptError("ADVERSARIAL_REPORT_INVALID")
    return report


def command_validate_adversarial_report(args: argparse.Namespace) -> int:
    sys.stdout.buffer.write(canonical_json_bytes(validate_adversarial_report(report_path=args.report)))
    return 0


def command_build_h1_packet(args: argparse.Namespace) -> int:
    packet = build_h1_packet(
        formal_attempt=args.formal_attempt,
        adversarial_report=args.adversarial_report,
        output_json=args.output,
        output_markdown=args.markdown,
    )
    sys.stdout.buffer.write(canonical_json_bytes({"packet_sha256": packet["packet_sha256"], "status": "written"}))
    return 0


def command_validate_h1_packet(args: argparse.Namespace) -> int:
    sys.stdout.buffer.write(canonical_json_bytes(validate_h1_packet(packet=args.packet, markdown=args.markdown)))
    return 0


def command_validate_h1_decision(args: argparse.Namespace) -> int:
    sys.stdout.buffer.write(canonical_json_bytes(validate_h1_decision(packet=args.packet, decision=args.decision)))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="specchoice-measurement")
    commands = parser.add_subparsers(dest="command", required=True)
    adapter = commands.add_parser("adapt-pr2164")
    adapter.add_argument("--authority", type=Path, required=True)
    adapter.add_argument("--bundle", type=Path, required=True)
    adapter.add_argument("--rules", type=Path, required=True)
    adapter.add_argument("--output", type=Path, required=True)
    adapter.set_defaults(handler=command_adapt_pr2164)
    formal = commands.add_parser("run-formal-measurement")
    formal.add_argument("--authority", type=Path, required=True)
    formal.add_argument("--bundle", type=Path, required=True)
    formal.add_argument("--rules", type=Path, required=True)
    formal.add_argument("--schema", type=Path, required=True)
    formal.add_argument("--predictions", type=Path, required=True)
    formal.add_argument("--attempt-root", type=Path, required=True)
    formal.add_argument("--attempt-id", required=True)
    formal.set_defaults(handler=command_run_formal_measurement)
    validate_attempt = commands.add_parser("validate-attempt")
    validate_attempt.add_argument("--attempt", type=Path, required=True)
    validate_attempt.set_defaults(handler=command_validate_attempt)
    adversarial = commands.add_parser("run-adversarial-oracles")
    adversarial.add_argument("--authority", type=Path, required=True)
    adversarial.add_argument("--bundle", type=Path, required=True)
    adversarial.add_argument("--rules", type=Path, required=True)
    adversarial.add_argument("--schema", type=Path, required=True)
    adversarial.add_argument("--predictions", type=Path, required=True)
    adversarial.add_argument("--oracle", type=Path, required=True)
    adversarial.add_argument("--formal-attempt", type=Path, required=True)
    adversarial.add_argument("--report", type=Path, required=True)
    adversarial.set_defaults(handler=command_run_adversarial_oracles)
    validate_adversarial = commands.add_parser("validate-adversarial-report")
    validate_adversarial.add_argument("--report", type=Path, required=True)
    validate_adversarial.set_defaults(handler=command_validate_adversarial_report)
    h1_build = commands.add_parser("build-h1-packet")
    h1_build.add_argument("--formal-attempt", type=Path, required=True)
    h1_build.add_argument("--adversarial-report", type=Path, required=True)
    h1_build.add_argument("--output", type=Path, required=True)
    h1_build.add_argument("--markdown", type=Path, required=True)
    h1_build.set_defaults(handler=command_build_h1_packet)
    h1_packet = commands.add_parser("validate-h1-packet")
    h1_packet.add_argument("--packet", type=Path, required=True)
    h1_packet.add_argument("--markdown", type=Path, required=True)
    h1_packet.set_defaults(handler=command_validate_h1_packet)
    h1_decision = commands.add_parser("validate-h1-decision")
    h1_decision.add_argument("--packet", type=Path, required=True)
    h1_decision.add_argument("--decision", type=Path, required=True)
    h1_decision.set_defaults(handler=command_validate_h1_decision)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.handler(args)
    except (AdapterError, AttemptError, H1Error, OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
