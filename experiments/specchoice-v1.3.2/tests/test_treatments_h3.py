"""Contract tests for the decision-free H3 Red readiness tracer."""

from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from specchoice_evidence.canonical import canonical_json_bytes, sha256_bytes
from specchoice_treatments.h3 import (
    audit_no_model_reachability_v1,
    build_h3_red_authority_v2,
    build_h3_red_readiness_v1,
    build_h3_red_review_packet_v1,
    build_h3_red_readiness_v2,
    build_h3_red_review_packet_v2,
    load_phase4_freeze_inputs_v1,
    load_phase4_freeze_inputs_v2,
    validate_h3_red_authority_v2,
    validate_h3_red_decision_v2,
)


class H3ContractTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.experiment = Path(__file__).parents[1]

    @staticmethod
    def _hash(value: dict[str, object], field: str) -> dict[str, object]:
        payload = {key: item for key, item in value.items() if key != field}
        return {**payload, field: sha256_bytes(canonical_json_bytes(payload))}

    def _v2_packet_readiness(self) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        freeze_inputs = load_phase4_freeze_inputs_v2(experiment_root=self.experiment)
        packet = build_h3_red_review_packet_v2(freeze_inputs)
        readiness = build_h3_red_readiness_v2(packet)
        return freeze_inputs, packet, readiness

    def _v2_decision(
        self, packet: dict[str, object], readiness: dict[str, object], *, aggregate: str = "approved_red",
    ) -> dict[str, object]:
        acknowledgment_disposition = "approved" if aggregate == "approved_red" else aggregate
        payload = {
            "acknowledgments": [
                {
                    "category": category,
                    "disposition": acknowledgment_disposition,
                    "rationale": "Reviewed against the exact v2 packet and readiness root.",
                }
                for category in packet["required_acknowledgment_categories"]
            ],
            "aggregate_disposition": aggregate,
            "aggregate_rationale": "This record is a future v2-only human decision.",
            "attestation": "I personally reviewed the exact v2 inputs and authorize no broader surface.",
            "packet_sha256": packet["packet_sha256"],
            "readiness_sha256": readiness["readiness_sha256"],
            "reviewer_id": "future-human-reviewer",
            "schema_version": "h3-branch-decision-v2",
            "signature": "Future Human Reviewer",
            "timestamp_utc": "2026-08-04T15:00:00Z",
        }
        return self._hash(payload, "decision_sha256")

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

    def test_v2_packet_and_readiness_remain_decision_free_and_bind_v1_predecessor(self) -> None:
        """v2 preserves v1 history but treats it as non-authorizing predecessor evidence."""
        _, packet, readiness = self._v2_packet_readiness()

        self.assertEqual("h3-red-review-packet-v2", packet["schema_version"])
        self.assertEqual("h3-branch-readiness-v2", readiness["schema_version"])
        self.assertEqual("historical_predecessor_not_authority", packet["predecessor_v1"]["status"])
        self.assertIn("ordering conflict", packet["successor_rationale"])
        self.assertFalse(
            {"aggregate_disposition", "reviewer_id", "attestation", "signature", "rationale", "timestamp_utc"}
            & packet.keys()
        )
        self.assertFalse(
            {"aggregate_disposition", "reviewer_id", "attestation", "signature", "rationale", "timestamp_utc"}
            & readiness.keys()
        )

    def test_v1_decision_cannot_authorize_v2_authority(self) -> None:
        """A valid v1 human decision cannot cross the v2 successor boundary."""
        freeze_inputs, packet, readiness = self._v2_packet_readiness()
        v1_decision = json.loads((self.experiment / "reviews/h3-branch-decision-v1.json").read_text())

        with self.assertRaisesRegex(Exception, "H3_DECISION_INCOMPLETE"):
            validate_h3_red_decision_v2(decision=v1_decision, packet=packet, readiness=readiness)
        with self.assertRaisesRegex(Exception, "H3_DECISION_INCOMPLETE"):
            build_h3_red_authority_v2(
                freeze_inputs=freeze_inputs, packet=packet, readiness=readiness, decision=v1_decision,
            )

    def test_v2_authority_requires_exact_fresh_approved_red_and_never_writes(self) -> None:
        """Construction is authorization-gated, content-bound, and has no publication side effect."""
        freeze_inputs, packet, readiness = self._v2_packet_readiness()
        decision = self._v2_decision(packet, readiness)
        authority = build_h3_red_authority_v2(
            freeze_inputs=freeze_inputs, packet=packet, readiness=readiness, decision=decision,
        )

        self.assertEqual(authority, validate_h3_red_authority_v2(
            authority=authority, packet=packet, readiness=readiness, decision=decision,
        ))
        self.assertEqual("red", authority["branch"])
        self.assertEqual(0, authority["N_strict"])
        self.assertFalse((self.experiment / "phase4/branch-authority-v2.json").exists())
        rejected = self._v2_decision(packet, readiness, aggregate="incomplete")
        with self.assertRaisesRegex(Exception, "H3_APPROVED_RED_REQUIRED"):
            build_h3_red_authority_v2(
                freeze_inputs=freeze_inputs, packet=packet, readiness=readiness, decision=rejected,
            )

    def test_v2_authority_rejects_tampered_freeze_bytes_before_construction(self) -> None:
        """A stale caller-side input cannot bypass the fresh descriptor-bound v2 recomputation."""
        freeze_inputs, packet, readiness = self._v2_packet_readiness()
        decision = self._v2_decision(packet, readiness)
        tampered = deepcopy(freeze_inputs)
        tampered["raw_by_path"]["src/specchoice_treatments/h3.py"] += b"# drift\n"

        with self.assertRaisesRegex(Exception, "FROZEN_INPUT_CHANGE_REQUIRES_NEW_EXPERIMENT_VERSION"):
            build_h3_red_authority_v2(
                freeze_inputs=tampered, packet=packet, readiness=readiness, decision=decision,
            )
        self.assertFalse((self.experiment / "phase4/branch-authority-v2.json").exists())


if __name__ == "__main__":
    unittest.main()
