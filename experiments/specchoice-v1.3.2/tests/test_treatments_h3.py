"""Contract tests for the decision-free H3 Red readiness tracer."""

from __future__ import annotations

import json
import tempfile
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
    build_h3_red_readiness_v3,
    build_h3_red_review_packet_v2,
    build_h3_red_review_packet_v3,
    load_phase4_freeze_inputs_v1,
    load_phase4_freeze_inputs_v2,
    load_phase4_freeze_inputs_v3,
    render_h3_red_review_markdown_v2,
    render_h3_red_review_markdown_v3,
    validate_h3_red_authority_v2,
    validate_h3_red_decision_v2,
    write_h3_red_readiness_v2,
    write_h3_red_readiness_v3,
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

    def test_v2_machine_products_publish_only_exact_packet_and_readiness(self) -> None:
        """The successor packet writer has no decision or authority output path."""
        _, packet, readiness = self._v2_packet_readiness()
        markdown = render_h3_red_review_markdown_v2(packet)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_h3_red_readiness_v2(experiment_root=root, packet=packet, markdown=markdown, readiness=readiness)
            write_h3_red_readiness_v2(experiment_root=root, packet=packet, markdown=markdown, readiness=readiness)
            self.assertEqual(canonical_json_bytes(packet), (root / "reports/h3/h3-red-review-v2/review-packet.json").read_bytes())
            self.assertEqual(canonical_json_bytes(readiness), (root / "receipts/h3-branch-readiness-v2.json").read_bytes())
            self.assertFalse((root / "reviews/h3-branch-decision-v2.json").exists())
            self.assertFalse((root / "phase4/branch-authority-v2.json").exists())

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

    def test_v2_authority_requires_exact_fresh_approved_red_before_publication(self) -> None:
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

    def test_v2_published_authority_is_present_self_validating_and_content_bound(self) -> None:
        """The post-publication state is valid evidence, not a stale pre-publication fixture."""
        packet = json.loads((self.experiment / "reports/h3/h3-red-review-v2/review-packet.json").read_text())
        readiness = json.loads((self.experiment / "receipts/h3-branch-readiness-v2.json").read_text())
        decision_path = self.experiment / "reviews/h3-branch-decision-v2.json"
        authority_path = self.experiment / "phase4/branch-authority-v2.json"
        decision = json.loads(decision_path.read_text())
        authority = json.loads(authority_path.read_text())

        self.assertTrue(decision_path.is_file())
        self.assertTrue(authority_path.is_file())
        self.assertEqual(canonical_json_bytes(decision), decision_path.read_bytes())
        self.assertEqual(canonical_json_bytes(authority), authority_path.read_bytes())
        self.assertEqual(decision, validate_h3_red_decision_v2(decision=decision, packet=packet, readiness=readiness))
        self.assertEqual(
            authority,
            validate_h3_red_authority_v2(authority=authority, packet=packet, readiness=readiness, decision=decision),
        )
        self.assertEqual(decision["packet_sha256"], authority["packet_sha256"])
        self.assertEqual(decision["readiness_sha256"], authority["readiness_sha256"])
        self.assertEqual(decision["decision_sha256"], authority["decision_sha256"])

    def test_v3_binds_v1_v2_history_and_publishes_no_decision_or_authority(self) -> None:
        """v3 freezes the lifecycle fix and must await a new human decision before any authority."""
        freeze_inputs = load_phase4_freeze_inputs_v3(experiment_root=self.experiment)
        packet = build_h3_red_review_packet_v3(freeze_inputs)
        readiness = build_h3_red_readiness_v3(packet)
        markdown = render_h3_red_review_markdown_v3(packet)

        self.assertEqual("historical_predecessor_not_current_authority", packet["predecessor_v1"]["status"])
        self.assertEqual("historical_predecessor_not_current_authority", packet["predecessor_v2"]["status"])
        self.assertEqual(
            sha256_bytes((self.experiment / "reviews/h3-branch-decision-v1.json").read_bytes()),
            packet["predecessor_v1"]["decision"]["raw_sha256"],
        )
        self.assertEqual(
            sha256_bytes((self.experiment / "reviews/h3-branch-decision-v2.json").read_bytes()),
            packet["predecessor_v2"]["decision"]["raw_sha256"],
        )
        self.assertEqual(
            sha256_bytes((self.experiment / "phase4/branch-authority-v2.json").read_bytes()),
            packet["predecessor_v2"]["authority"]["raw_sha256"],
        )
        self.assertIn("lifecycle tests and static checking", packet["successor_rationale"])
        self.assertEqual(packet["predecessor_v2"], readiness["historical_predecessors"]["v2"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_h3_red_readiness_v3(experiment_root=root, packet=packet, markdown=markdown, readiness=readiness)
            self.assertTrue((root / "receipts/h3-branch-readiness-v3.json").is_file())
            self.assertFalse((root / "reviews/h3-branch-decision-v3.json").exists())
            self.assertFalse((root / "phase4/branch-authority-v3.json").exists())


if __name__ == "__main__":
    unittest.main()
