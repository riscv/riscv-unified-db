# SPDX-License-Identifier: BSD-3-Clause-Clear
"""TDD contract for isolated Phase 2 scoring semantics."""

from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from specchoice_evidence.canonical import canonical_json_bytes
from specchoice_measurement.adapter import build_pr2164_adapter_batch
from specchoice_measurement.preflight import preflight_prediction_batch
from specchoice_measurement.scoring import score_prediction_batch


class MeasurementScoringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.experiment_root = Path(__file__).parents[1]
        self.bundle = self.experiment_root / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"
        self.batch = build_pr2164_adapter_batch(
            authority_path=self.experiment_root / "phase2/source-authority.json",
            bundle_root=self.bundle,
            rules_path=self.experiment_root / "config/measurement/pr2164-adapter-rules-v1.json",
        )
        self.assertTrue(self.batch.valid)
        self.golden_path = self.experiment_root / "fixtures/measurement/golden-predictions-v1.json"

    def golden_payload(self) -> dict[str, object]:
        raw = self.golden_path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
        self.assertEqual(raw, canonical_json_bytes(payload))
        return payload

    def preflight(self, payload: object):
        return preflight_prediction_batch(
            raw=canonical_json_bytes(payload), adapter_batch=self.batch, ingress="current-v1"
        )

    def test_exact_all_eleven_golden_outcomes_keep_dimensions_independent(self) -> None:
        preflight = self.preflight(self.golden_payload())
        result = score_prediction_batch(adapter_batch=self.batch, preflight=preflight, mode="formal")

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.diagnostics, ())
        self.assertEqual(len(result.case_outcomes), 11)
        self.assertEqual(result.metrics.as_dict(), {
            "disposition": {"denominator": 7, "numerator": 7},
            "evidence_integrity": {"denominator": 7, "numerator": 7},
            "identity": {"denominator": 6, "numerator": 6},
            "surfacing": {"denominator": 7, "numerator": 7},
        })
        outcomes = {item.fixture_id: item for item in result.case_outcomes}
        self.assertTrue(all(outcomes[record.fixture_id].surfacing_correct for record in self.batch.records))
        self.assertTrue(all(outcomes[record.fixture_id].disposition_correct for record in self.batch.records))
        self.assertTrue(all(outcomes[record.fixture_id].evidence_integrity for record in self.batch.records))
        for record in self.batch.records:
            if record.category == "positive":
                self.assertEqual(outcomes[record.fixture_id].identity_outcome, "exact")
        candidate = outcomes["CAND_WARL_FIXED_LEGAL_SET"]
        self.assertEqual(candidate.actual_status, "classify_out")
        self.assertIsNone(candidate.proposed_name)
        self.assertTrue(candidate.disposition_correct)

    def test_candidate_must_surface_then_classify_out(self) -> None:
        variants = (
            (False, None, "CANDIDATE_NOT_SURFACED"),
            (True, "accept", "CANDIDATE_ACCEPTED_AS_PARAMETER"),
            (True, "review", "CANDIDATE_LEFT_UNRESOLVED"),
        )
        for surfaced, status, code in variants:
            payload = self.golden_payload()
            candidate = next(item for item in payload["predictions"] if item["fixture_id"] == "CAND_WARL_FIXED_LEGAL_SET")
            candidate["adjudication"]["surfaced"] = surfaced
            candidate["adjudication"]["parameter_status"] = status
            if not surfaced:
                candidate["adjudication"]["evidence_spans"] = []
            with self.subTest(code=code):
                result = score_prediction_batch(adapter_batch=self.batch, preflight=self.preflight(payload), mode="formal")
                self.assertIn(code, {item.code for item in result.diagnostics})
                self.assertEqual(result.metrics, None)

    def test_invalid_or_diagnostic_only_preflight_never_emits_formal_metrics(self) -> None:
        payload = self.golden_payload()
        payload["predictions"] = payload["predictions"][:-1]
        invalid = score_prediction_batch(adapter_batch=self.batch, preflight=self.preflight(payload), mode="formal")
        diagnostic = score_prediction_batch(adapter_batch=self.batch, preflight=self.preflight(self.golden_payload()), mode="diagnostic_only")

        self.assertEqual((invalid.status, invalid.metrics), ("invalid_preflight", None))
        self.assertEqual((diagnostic.status, diagnostic.metrics), ("diagnostic_only", None))


if __name__ == "__main__":
    unittest.main()
