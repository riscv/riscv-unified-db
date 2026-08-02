"""Public H1 packet, readiness, and human-decision contracts."""

from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from specchoice_evidence.canonical import canonical_json_bytes, sha256_bytes
from specchoice_measurement import h1
from specchoice_measurement.h1 import H1Error


class H1PublicContractTests(unittest.TestCase):
    def test_h1_v3_exposes_readiness_and_v2_decision_validation_without_human_writers(self) -> None:
        from specchoice_measurement.h1 import (  # noqa: PLC0415
            build_h1_packet,
            render_h1_markdown,
            validate_h1_decision_v2,
            validate_h1_packet,
            validate_h1_readiness_v3,
            write_h1_readiness_v3,
        )

        for value in (
            build_h1_packet,
            render_h1_markdown,
            validate_h1_packet,
            write_h1_readiness_v3,
            validate_h1_readiness_v3,
            validate_h1_decision_v2,
        ):
            self.assertTrue(callable(value))
        self.assertFalse(any("decision" in name and "validate" not in name for name in dir(h1)))


class H1PacketTests(unittest.TestCase):
    semantic_ids = (
        "ts03_adjacency",
        "ts03_empty_null_single_element",
        "ts03_equal_element_stable_order",
        "ts04_unclassified_manual_review",
        "ts05_adjacency",
        "ts05_empty_null_single_element",
        "ts05_equal_element_stable_order",
    )

    def setUp(self) -> None:
        self.root = Path(__file__).parents[1]
        self.formal = self.root / "runs/measurement-attempts/formal-golden-pr2164-v1"
        self.adversarial = self.root / "reports/h1/adversarial-oracle-results-v2.json"
        self.schema = self.root / "config/measurement/h1-review-schema-v2.json"
        self.pending_authority = self.root / "phase2/source-authority-v10-pending.json"
        self.revocation = self.root / "receipts/fixture-closure-revocation-v1.json"
        self.replay = self.root / "receipts/fixture-closure-offline-replay-v3.json"
        self.cutover = self.root / "receipts/source-cutover-readiness-v10.json"

    def _build(self, directory: Path) -> tuple[Path, Path, dict[str, object]]:
        packet_path = directory / "packet" / "packet.json"
        markdown_path = directory / "packet" / "packet.md"
        packet = h1.build_h1_packet(
            formal_attempt=self.formal,
            adversarial_report=self.adversarial,
            output_json=packet_path,
            output_markdown=markdown_path,
            schema=self.schema,
        )
        return packet_path, markdown_path, packet

    def _readiness(self, directory: Path, packet: Path, markdown: Path) -> Path:
        summary = directory / "02-16-SUMMARY-fixture.md"
        summary.write_text("# disposable normalized projection\n", encoding="utf-8")
        readiness = directory / "h1-review-readiness-v3.json"
        h1.write_h1_readiness_v3(
            output=readiness,
            formal_attempt=self.formal,
            adversarial_result=self.adversarial,
            packet=packet,
            markdown=markdown,
            schema=self.schema,
            source_authority=self.pending_authority,
            canonical_revocation=self.revocation,
            offline_replay=self.replay,
            phase_gate=self.cutover.read_bytes(),
            plan_summary=summary,
        )
        return readiness

    @staticmethod
    def _decision(packet: dict[str, object], readiness: dict[str, object], *, disposition: str = "approved") -> dict[str, object]:
        reviews = []
        for review in packet["fixture_reviews"]:
            assert isinstance(review, dict)
            semantics = {key: value for key, value in review.items() if key != "signature_slot"}
            reviews.append({
                "disposition": "approved",
                "fixture_id": review["fixture_id"],
                "reviewed_semantics_sha256": sha256_bytes(canonical_json_bytes(semantics)),
                "reviewer": "independent-human-reviewer",
                "signature": f"signed:{review['fixture_id']}",
            })
        decision: dict[str, object] = {
            "aggregate_disposition": disposition,
            "bindings": {
                "packet_sha256": packet["packet_sha256"],
                "phase_gate_sha256": readiness["bindings"]["phase_gate_sha256"],
                "readiness_sha256": readiness["readiness_sha256"],
                "schema_sha256": readiness["bindings"]["schema_sha256"],
            },
            "external_publication_authorized": False,
            "fixture_reviews": reviews,
            "reviewer": "independent-human-reviewer",
            "rationale": "independent review completed",
            "semantic_responses": {
                identifier: {"disposition": "approved", "response": "reviewed"}
                for identifier in H1PacketTests.semantic_ids
            },
            "timestamp": "2026-08-02T00:00:00Z",
            "schema_version": "h1-source-gold-decision-v2",
        }
        decision["decision_sha256"] = sha256_bytes(canonical_json_bytes(decision))
        return decision

    def test_packet_is_complete_clean_and_markdown_is_a_pure_projection(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            packet_path, markdown_path, packet = self._build(Path(directory))
            validated = h1.validate_h1_packet(packet=packet_path, markdown=markdown_path, schema=self.schema)
            self.assertEqual(validated, packet)
            self.assertEqual(len(packet["fixture_reviews"]), 11)
            self.assertFalse(packet["external_publication_authorized"])
            self.assertEqual(markdown_path.read_text(encoding="utf-8"), h1.render_h1_markdown(packet))

    def test_any_packet_binding_or_markdown_mutation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            packet_path, markdown_path, packet = self._build(Path(directory))
            changed = deepcopy(packet)
            assert isinstance(changed["bindings"], dict)
            changed["bindings"]["golden_predictions_sha256"] = "0" * 64
            changed["packet_sha256"] = sha256_bytes(canonical_json_bytes({key: value for key, value in changed.items() if key != "packet_sha256"}))
            packet_path.write_bytes(canonical_json_bytes(changed))
            with self.assertRaisesRegex(H1Error, "H1_BINDINGS_INVALID"):
                h1.validate_h1_packet(packet=packet_path, markdown=markdown_path, schema=self.schema)
            packet_path.write_bytes(canonical_json_bytes(packet))
            markdown_path.write_text("not a projection\n", encoding="utf-8")
            with self.assertRaisesRegex(H1Error, "H1_MARKDOWN_INVALID"):
                h1.validate_h1_packet(packet=packet_path, markdown=markdown_path, schema=self.schema)

    def test_readiness_is_one_time_and_validator_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            root = Path(directory)
            packet, markdown, _ = self._build(root)
            readiness = self._readiness(root, packet, markdown)
            before = readiness.read_bytes()
            phase_gate = self.cutover.read_bytes()
            self.assertEqual(
                h1.validate_h1_readiness_v3(
                    readiness=readiness, formal_attempt=self.formal, adversarial_result=self.adversarial,
                    packet=packet, markdown=markdown, schema=self.schema, source_authority=self.pending_authority,
                    canonical_revocation=self.revocation, offline_replay=self.replay, phase_gate=phase_gate,
                    plan_summary=root / "02-16-SUMMARY-fixture.md",
                )["readiness_sha256"],
                json.loads(before)["readiness_sha256"],
            )
            self.assertEqual(readiness.read_bytes(), before)
            with self.assertRaisesRegex(H1Error, "H1_READINESS_EXISTS"):
                self._readiness(root, packet, markdown)

    def test_v2_decision_validator_checks_closed_human_contract_without_authoring(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            root = Path(directory)
            packet_path, markdown_path, packet = self._build(root)
            readiness_path = self._readiness(root, packet_path, markdown_path)
            readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
            decision = self._decision(packet, readiness)
            decision_path = root / "decision.json"
            decision_path.write_bytes(canonical_json_bytes(decision))
            receipt = h1.validate_h1_decision_v2(
                schema=self.schema, packet=packet_path, readiness=readiness_path, decision=decision_path
            )
            self.assertEqual(receipt["fixture_count"], 11)
            self.assertEqual(receipt["aggregate_disposition"], "approved")
            self.assertFalse(receipt["external_publication_authorized"])

    def test_incomplete_or_disputed_leaf_must_match_aggregate(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            root = Path(directory)
            packet_path, markdown_path, packet = self._build(root)
            readiness_path = self._readiness(root, packet_path, markdown_path)
            readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
            decision = self._decision(packet, readiness)
            assert isinstance(decision["fixture_reviews"], list)
            assert isinstance(decision["fixture_reviews"][0], dict)
            decision["fixture_reviews"][0]["disposition"] = "disputed"
            decision["decision_sha256"] = sha256_bytes(canonical_json_bytes({key: value for key, value in decision.items() if key != "decision_sha256"}))
            decision_path = root / "decision.json"
            decision_path.write_bytes(canonical_json_bytes(decision))
            with self.assertRaisesRegex(H1Error, "H1_DISPUTE_AGGREGATION_INVALID"):
                h1.validate_h1_decision_v2(schema=self.schema, packet=packet_path, readiness=readiness_path, decision=decision_path)

    def test_public_h1_validators_cover_packet_markdown_readiness_decision_schema_and_retained_roles(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            root = Path(directory)
            packet_path, markdown_path, packet = self._build(root)
            readiness_path = self._readiness(root, packet_path, markdown_path)
            readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
            decision_path = root / "decision.json"
            decision_path.write_bytes(canonical_json_bytes(self._decision(packet, readiness)))
            self.assertEqual(
                h1.validate_h1_decision_v2(schema=self.schema, packet=packet_path, readiness=readiness_path, decision=decision_path)["valid"],
                True,
            )
            for path in (packet_path, markdown_path, readiness_path, decision_path, self.schema, self.formal / "attempt.json", self.adversarial):
                self.assertTrue(path.is_file(), path)


if __name__ == "__main__":
    unittest.main()
