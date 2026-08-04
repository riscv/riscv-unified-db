# SPDX-License-Identifier: BSD-3-Clause-Clear
from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from specchoice_evidence.canonical import canonical_json_bytes
from specchoice_treatments.schema import parse_treatment_response_v1


class FrameContractTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        experiment = Path(__file__).parents[1]
        self.source_raw = (experiment / "fixtures/treatments/frame-source-v1.txt").read_bytes()
        self.response = json.loads(
            (experiment / "fixtures/treatments/frame-response-b-valid-v1.json").read_text(
                encoding="utf-8"
            )
        )

    def _parse(self, response: object | None = None):
        value = self.response if response is None else response
        return parse_treatment_response_v1(canonical_json_bytes(value), self.source_raw)

    def test_valid_b_response_binds_exact_three_axis_spans(self) -> None:
        parsed = self._parse()

        self.assertTrue(parsed.valid)
        self.assertEqual(parsed.diagnostics, ())
        self.assertEqual(
            tuple(parsed.delegation_frame),
            ("authority", "choice_object", "choice_space_origin"),
        )
        self.assertEqual(len(parsed.adjudication["evidence_spans"]), 1)
        for axis in parsed.delegation_frame.values():
            span = axis["evidence_span"]
            self.assertEqual(
                self.source_raw[span["start_byte"] : span["end_byte"]].decode("utf-8"),
                span["text"],
            )
        self.assertEqual(parsed.canonical_projection, canonical_json_bytes(parsed.as_dict()))

    def test_unknown_and_key_order_are_deterministic(self) -> None:
        response = deepcopy(self.response)
        response["delegation_frame"]["authority"]["value"] = "unknown"
        response["delegation_frame"]["choice_space_origin"]["value"] = "unknown"
        reordered = {
            "adjudication": response["adjudication"],
            "delegation_frame": {
                "choice_space_origin": response["delegation_frame"]["choice_space_origin"],
                "choice_object": response["delegation_frame"]["choice_object"],
                "authority": response["delegation_frame"]["authority"],
            },
            "target_sha256": response["target_sha256"],
            "model_generated": response["model_generated"],
            "origin": response["origin"],
            "system": response["system"],
            "schema_version": response["schema_version"],
        }

        original = self._parse(response)
        reordered_parsed = self._parse(reordered)

        self.assertTrue(original.valid)
        self.assertTrue(reordered_parsed.valid)
        self.assertEqual(original.canonical_projection, reordered_parsed.canonical_projection)
        self.assertEqual(original.diagnostics, reordered_parsed.diagnostics)

    def test_equal_and_adjacent_spans_remain_axis_scoped(self) -> None:
        response = deepcopy(self.response)
        source_sha256 = response["target_sha256"]
        first = response["delegation_frame"]["authority"]["evidence_span"]
        text = self.source_raw.decode("utf-8")
        response["delegation_frame"]["choice_object"]["evidence_span"] = deepcopy(first)
        response["delegation_frame"]["choice_space_origin"]["evidence_span"] = {
            "source_sha256": source_sha256,
            "start_byte": first["end_byte"],
            "end_byte": len(self.source_raw),
            "text": text[first["end_byte"] :],
        }

        parsed = self._parse(response)

        self.assertTrue(parsed.valid)
        axes = parsed.delegation_frame
        self.assertEqual(
            axes["authority"]["evidence_span"],
            axes["choice_object"]["evidence_span"],
        )
        self.assertEqual(
            axes["authority"]["evidence_span"]["end_byte"],
            axes["choice_space_origin"]["evidence_span"]["start_byte"],
        )
        self.assertEqual(len(axes), 3)


if __name__ == "__main__":
    unittest.main()
