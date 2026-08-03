# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Pure, complete-batch scoring for canonical Phase 2 adjudications."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .diagnostics import Diagnostic, ordered_diagnostics
from .preflight import _source_bytes_by_sha256


@dataclass(frozen=True)
class Metric:
    """An independently denominated metric with no blended headline score."""

    numerator: int
    denominator: int

    def as_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class ScoreMetrics:
    surfacing: Metric
    disposition: Metric
    identity: Metric
    evidence_integrity: Metric

    def as_dict(self) -> dict[str, dict[str, int]]:
        return {
            "disposition": self.disposition.as_dict(),
            "evidence_integrity": self.evidence_integrity.as_dict(),
            "identity": self.identity.as_dict(),
            "surfacing": self.surfacing.as_dict(),
        }


@dataclass(frozen=True)
class CaseOutcome:
    """One stable, inspectable outcome for each adapter-bound fixture."""

    fixture_id: str
    finding_id: str
    category: str
    actual_surfaced: bool
    actual_status: str | None
    proposed_name: str | None
    surfacing_correct: bool
    disposition_correct: bool
    identity_outcome: str
    evidence_integrity: bool

    def sort_key(self) -> tuple[str, str, str]:
        return (self.fixture_id, self.finding_id, self.actual_status or "")

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ScoreResult:
    status: str
    case_outcomes: tuple[CaseOutcome, ...]
    metrics: ScoreMetrics | None
    diagnostics: tuple[Diagnostic, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "case_outcomes": [item.as_dict() for item in self.case_outcomes],
            "diagnostics": [item.as_dict() for item in self.diagnostics],
            "metrics": None if self.metrics is None else self.metrics.as_dict(),
            "status": self.status,
        }


def validate_v5_span_population(golden: object) -> int:
    """Require the frozen v5 denominator to match all score-bearing outcomes."""
    if not isinstance(golden, dict) or not isinstance(golden.get("outcomes"), list):
        raise ValueError("V5_SPAN_POPULATION_INVALID")
    count = sum(1 for outcome in golden["outcomes"] if isinstance(outcome, dict) and outcome.get("surfaced") is True)
    if golden.get("score_bearing_span_count") != count:
        raise ValueError("V5_SPAN_POPULATION_INVALID")
    return count


def _score_gate_diagnostics(*, adapter_batch: object, preflight: object) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = list(getattr(preflight, "diagnostics", ()))
    if not getattr(adapter_batch, "valid", False):
        diagnostics.append(Diagnostic("ADAPTER_BATCH_INVALID", "blocker", field="adapter_batch"))
    if getattr(preflight, "status", "") not in {"valid_preflight", "completed_with_warnings"}:
        diagnostics.append(
            Diagnostic(
                "PREFLIGHT_NOT_SCORE_ELIGIBLE",
                "blocker",
                field="preflight.status",
                expected=["valid_preflight", "completed_with_warnings"],
                observed=getattr(preflight, "status", None),
            )
        )
    records = tuple(getattr(adapter_batch, "records", ()))
    predictions = tuple(getattr(preflight, "parsed_predictions", ()))
    expected_ids = {getattr(record, "fixture_id", "") for record in records}
    observed_ids = {
        prediction.get("fixture_id")
        for prediction in predictions
        if isinstance(prediction, dict) and isinstance(prediction.get("fixture_id"), str)
    }
    if len(records) != 11 or len(predictions) != 11 or expected_ids != observed_ids:
        diagnostics.append(
            Diagnostic(
                "FORMAL_COVERAGE_MISMATCH",
                "blocker",
                field="parsed_predictions",
                expected=sorted(expected_ids),
                observed=sorted(item for item in observed_ids if isinstance(item, str)),
            )
        )
    return diagnostics


def _evidence_integrity(
    *, prediction: dict[str, object], fixture_id: str, source_bytes_by_sha256: dict[str, bytes], diagnostics: list[Diagnostic]
) -> bool:
    adjudication = prediction["adjudication"]
    assert isinstance(adjudication, dict)
    if adjudication["surfaced"] is False:
        return True
    spans = adjudication["evidence_spans"]
    assert isinstance(spans, list)
    if not spans:
        diagnostics.append(Diagnostic("EVIDENCE_SPAN_EMPTY", "blocker", fixture_id, "adjudication.evidence_spans", expected="non-empty array", observed=[]))
        return False
    valid = True
    for occurrence, span in enumerate(spans, start=1):
        if not isinstance(span, dict):
            diagnostics.append(Diagnostic("EVIDENCE_SPAN_NOT_FOUND", "blocker", fixture_id, "adjudication.evidence_spans", occurrence=occurrence))
            valid = False
            continue
        source_sha256 = span.get("source_sha256")
        start = span.get("start_byte")
        end = span.get("end_byte")
        text = span.get("text")
        raw = source_bytes_by_sha256.get(source_sha256) if isinstance(source_sha256, str) else None
        if raw is None or not isinstance(start, int) or isinstance(start, bool) or not isinstance(end, int) or isinstance(end, bool) or not isinstance(text, str):
            diagnostics.append(Diagnostic("EVIDENCE_SPAN_NOT_FOUND", "blocker", fixture_id, "adjudication.evidence_spans", occurrence=occurrence, source_sha256=source_sha256 if isinstance(source_sha256, str) else None))
            valid = False
            continue
        if start < 0 or end <= start or end > len(raw):
            diagnostics.append(Diagnostic("EVIDENCE_SPAN_EMPTY", "blocker", fixture_id, "adjudication.evidence_spans", occurrence=occurrence, expected=f"[0,{len(raw)}] non-empty", observed=[start, end], source_sha256=source_sha256))
            valid = False
            continue
        try:
            observed = raw[start:end].decode("utf-8")
        except UnicodeDecodeError:
            observed = None
        if observed != text:
            diagnostics.append(Diagnostic("EVIDENCE_SPAN_NOT_FOUND", "blocker", fixture_id, "adjudication.evidence_spans", occurrence=occurrence, expected=observed, observed=text, source_sha256=source_sha256))
            valid = False
    return valid


def _outcome_for(
    *, record: object, prediction: dict[str, object], source_bytes_by_sha256: dict[str, bytes], diagnostics: list[Diagnostic]
) -> CaseOutcome:
    fixture_id = getattr(record, "fixture_id")
    category = getattr(record, "category")
    adjudication = prediction["adjudication"]
    assert isinstance(adjudication, dict)
    surfaced = adjudication["surfaced"]
    status = adjudication["parameter_status"]
    name = adjudication["proposed_name"]
    assert isinstance(surfaced, bool)
    assert status is None or isinstance(status, str)
    assert name is None or isinstance(name, str)
    finding_id = str(prediction["finding_id"])
    evidence_integrity = _evidence_integrity(
        prediction=prediction, fixture_id=fixture_id, source_bytes_by_sha256=source_bytes_by_sha256, diagnostics=diagnostics
    )
    surfacing_correct = (category != "negative") == surfaced
    disposition_correct = False
    identity_outcome = "not_applicable"

    if category == "positive":
        if not surfaced:
            diagnostics.append(Diagnostic("MISSING_EXPECTED_PARAMETER", "blocker", fixture_id, "adjudication.surfaced", finding_id=finding_id, expected=True, observed=False))
        elif status == "classify_out":
            diagnostics.append(Diagnostic("POSITIVE_CLASSIFIED_OUT", "blocker", fixture_id, "adjudication.parameter_status", finding_id=finding_id, expected="accept", observed=status))
        elif status != "accept":
            diagnostics.append(Diagnostic("MISSING_EXPECTED_PARAMETER", "blocker", fixture_id, "adjudication.parameter_status", finding_id=finding_id, expected="accept", observed=status))
        else:
            disposition_correct = True
            expected_name = getattr(record, "expected_parameter_names")[0]
            if name is None:
                identity_outcome = "missing"
                diagnostics.append(
                    Diagnostic(
                        "ACCEPTED_PARAMETER_NAME_MISSING",
                        "warning",
                        fixture_id,
                        "adjudication.proposed_name",
                        finding_id=str(prediction["finding_id"]),
                        expected=expected_name,
                        observed=None,
                    )
                )
            elif name == expected_name:
                identity_outcome = "exact"
            else:
                identity_outcome = "incorrect"
    elif category == "negative":
        if surfaced:
            code = "UNEXPECTED_ACCEPTED_PARAMETER" if status == "accept" else "NEGATIVE_UNNECESSARILY_SURFACED"
            diagnostics.append(Diagnostic(code, "blocker", fixture_id, "adjudication.parameter_status", finding_id=finding_id, expected=None, observed=status))
        else:
            disposition_correct = True
    else:
        if not surfaced:
            diagnostics.append(Diagnostic("CANDIDATE_NOT_SURFACED", "blocker", fixture_id, "adjudication.surfaced", finding_id=finding_id, expected=True, observed=False))
        elif status == "accept":
            diagnostics.append(Diagnostic("CANDIDATE_ACCEPTED_AS_PARAMETER", "blocker", fixture_id, "adjudication.parameter_status", finding_id=finding_id, expected="classify_out", observed=status))
        elif status == "review":
            diagnostics.append(Diagnostic("CANDIDATE_LEFT_UNRESOLVED", "blocker", fixture_id, "adjudication.parameter_status", finding_id=finding_id, expected="classify_out", observed=status))
        elif status == "classify_out":
            disposition_correct = True
        else:
            diagnostics.append(Diagnostic("CANDIDATE_LEFT_UNRESOLVED", "blocker", fixture_id, "adjudication.parameter_status", finding_id=finding_id, expected="classify_out", observed=status))
    return CaseOutcome(
        fixture_id=fixture_id,
        finding_id=str(prediction["finding_id"]),
        category=category,
        actual_surfaced=surfaced,
        actual_status=status,
        proposed_name=name,
        surfacing_correct=surfacing_correct,
        disposition_correct=disposition_correct,
        identity_outcome=identity_outcome,
        evidence_integrity=evidence_integrity,
    )


def _metrics(outcomes: tuple[CaseOutcome, ...]) -> ScoreMetrics:
    expected_surfaced = tuple(item for item in outcomes if item.category != "negative")
    positive_accepts = tuple(item for item in outcomes if item.category == "positive" and item.disposition_correct)
    surfaced = tuple(item for item in outcomes if item.actual_surfaced)
    return ScoreMetrics(
        surfacing=Metric(sum(item.surfacing_correct for item in expected_surfaced), len(expected_surfaced)),
        disposition=Metric(sum(item.disposition_correct for item in outcomes if item.category != "negative"), len(expected_surfaced)),
        identity=Metric(sum(item.identity_outcome == "exact" for item in positive_accepts), len(positive_accepts)),
        evidence_integrity=Metric(sum(item.evidence_integrity for item in surfaced), len(surfaced)),
    )


def score_prediction_batch(*, adapter_batch: object, preflight: object, mode: str) -> ScoreResult:
    """Score only complete zero-blocker canonical batches; never publish blended metrics."""
    if mode == "diagnostic_only":
        return ScoreResult("diagnostic_only", (), None, ordered_diagnostics(tuple(getattr(preflight, "diagnostics", ()))))
    diagnostics = _score_gate_diagnostics(adapter_batch=adapter_batch, preflight=preflight)
    if mode != "formal":
        diagnostics.append(Diagnostic("SCORE_MODE_INVALID", "blocker", field="mode", expected=["formal", "diagnostic_only"], observed=mode))
    if any(item.severity == "blocker" for item in diagnostics):
        return ScoreResult("invalid_preflight", (), None, ordered_diagnostics(diagnostics))

    predictions = {
        prediction["fixture_id"]: prediction
        for prediction in getattr(preflight, "parsed_predictions")
        if isinstance(prediction, dict)
    }
    source_bytes_by_sha256 = _source_bytes_by_sha256(adapter_batch)
    outcomes = tuple(sorted((
        _outcome_for(record=record, prediction=predictions[record.fixture_id], source_bytes_by_sha256=source_bytes_by_sha256, diagnostics=diagnostics)
        for record in getattr(adapter_batch, "records")
    ), key=CaseOutcome.sort_key))
    ordered = ordered_diagnostics(diagnostics)
    if any(item.severity == "blocker" for item in ordered):
        return ScoreResult("invalid_score", outcomes, None, ordered)
    status = "completed_with_warnings" if ordered else "completed"
    return ScoreResult(status, outcomes, _metrics(outcomes), ordered)
