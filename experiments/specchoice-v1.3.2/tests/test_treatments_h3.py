"""Contract tests for the decision-free H3 Red readiness tracer."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from specchoice_treatments.h3 import (
    audit_no_model_reachability_v1,
    build_h3_red_readiness_v1,
    build_h3_red_review_packet_v1,
    load_phase4_freeze_inputs_v1,
)


class H3ContractTests(unittest.TestCase):
    def test_machine_readiness_recomputes_phase3_and_phase4_roots(self) -> None:
        """The machine tracer binds the Red inputs without human approval fields."""
        freeze_inputs = load_phase4_freeze_inputs_v1()
        packet = build_h3_red_review_packet_v1(freeze_inputs)
        readiness = build_h3_red_readiness_v1(packet)

        self.assertEqual("red", packet["branch"])
        self.assertEqual(0, packet["N_strict"])
        self.assertEqual(0, packet["repeat_count"])
        self.assertFalse(packet["h4_required"])
        self.assertEqual("ready_for_human", readiness["status"])
        self.assertFalse(
            {"aggregate_disposition", "reviewer_id", "attestation", "signature", "rationale", "timestamp_utc"}
            & readiness.keys()
        )

    def test_freeze_inventory_is_complete_sorted_and_content_bound(self) -> None:
        """Every declared treatment input is sorted and bound to immutable bytes."""
        freeze_inputs = load_phase4_freeze_inputs_v1()
        inventory = freeze_inputs["phase4_freeze_inventory"]
        paths = [entry["path"] for entry in inventory]

        self.assertEqual(paths, sorted(paths))
        self.assertIn("src/specchoice_treatments/cli.py", paths)
        self.assertIn("reports/h3/test-only-retrieval-contract-v1.json", paths)
        self.assertEqual(64, len(freeze_inputs["freeze_inventory_sha256"]))

    def test_no_model_reachability_is_static_and_runtime(self) -> None:
        """The only CLI command is the test-only retrieval verifier with no model path."""
        with patch("socket.create_connection", side_effect=AssertionError("network call")) as connection:
            audit = audit_no_model_reachability_v1(load_phase4_freeze_inputs_v1())

        self.assertTrue(all(value is True for value in audit["checks"].values()))
        self.assertEqual("verify-retrieval-contract", audit["cli_commands"][0])
        self.assertEqual(64, len(audit["no_model_reachability_sha256"]))
        connection.assert_not_called()


if __name__ == "__main__":
    unittest.main()
