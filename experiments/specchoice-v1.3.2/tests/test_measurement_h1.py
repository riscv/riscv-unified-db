"""H1 packet and human-decision boundary tests."""

import json
import os
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest import mock

from specchoice_evidence.canonical import canonical_json_bytes, sha256_bytes
from specchoice_evidence import filesystem
from specchoice_evidence.filesystem import FilesystemPolicyError, read_authoritative_file
from specchoice_measurement import h1
from specchoice_measurement.h1 import H1Error, build_h1_packet, render_h1_markdown, validate_h1_decision, validate_h1_packet


class H1PublicContractTests(unittest.TestCase):
    def test_h1_exposes_only_packet_and_existing_decision_validation(self) -> None:
        from specchoice_measurement.h1 import (  # noqa: PLC0415
            build_h1_packet,
            render_h1_markdown,
            validate_h1_decision,
            validate_h1_packet,
        )

        self.assertTrue(callable(build_h1_packet))
        self.assertTrue(callable(render_h1_markdown))
        self.assertTrue(callable(validate_h1_packet))
        self.assertTrue(callable(validate_h1_decision))


class H1PacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).parents[1]
        self.formal = self.root / "runs/measurement-attempts/formal-golden-pr2164-v1"
        self.adversarial = self.root / "reports/h1/adversarial-oracle-results-v2.json"

    def _build(self, directory: Path) -> tuple[Path, Path, dict[str, object]]:
        packet_path = directory / "packet" / "packet.json"
        markdown_path = directory / "packet" / "packet.md"
        packet = build_h1_packet(
            formal_attempt=self.formal,
            adversarial_report=self.adversarial,
            output_json=packet_path,
            output_markdown=markdown_path,
        )
        return packet_path, markdown_path, packet

    @staticmethod
    def _decision(packet: dict[str, object], *, disposition: str = "approved") -> dict[str, object]:
        packet_reviews = packet["fixture_reviews"]
        assert isinstance(packet_reviews, list)
        reviews = []
        for review in packet_reviews:
            assert isinstance(review, dict)
            reviews.append({
                "disposition": "approved",
                "fixture_id": review["fixture_id"],
                "reviewed_semantics": {key: value for key, value in review.items() if key != "signature_slot"},
                "reviewer": "independent-human-reviewer",
                "signature": f"signed:{review['fixture_id']}",
            })
        decision: dict[str, object] = {
            "aggregate_disposition": disposition,
            "bindings": {"packet_bindings": packet["bindings"], "packet_sha256": packet["packet_sha256"]},
            "external_publication_authorized": False,
            "fixture_reviews": reviews,
            "schema_version": "h1-source-gold-decision-v1",
        }
        decision["decision_sha256"] = sha256_bytes(canonical_json_bytes(decision))
        return decision

    def test_packet_is_complete_clean_and_markdown_is_a_pure_projection(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            packet_path, markdown_path, packet = self._build(Path(directory))
            validated = validate_h1_packet(packet=packet_path, markdown=markdown_path)
            self.assertEqual(validated, packet)
            self.assertEqual(len(packet["fixture_reviews"]), 11)
            self.assertFalse(packet["external_publication_authorized"])
            self.assertEqual(markdown_path.read_text(encoding="utf-8"), render_h1_markdown(packet))
            self.assertNotIn("approved", markdown_path.read_text(encoding="utf-8").lower())

    def test_any_packet_binding_or_markdown_mutation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            packet_path, markdown_path, packet = self._build(Path(directory))
            changed = deepcopy(packet)
            assert isinstance(changed["bindings"], dict)
            changed["bindings"]["golden_predictions_sha256"] = "0" * 64
            changed["packet_sha256"] = sha256_bytes(canonical_json_bytes({key: value for key, value in changed.items() if key != "packet_sha256"}))
            packet_path.write_bytes(canonical_json_bytes(changed))
            with self.assertRaisesRegex(H1Error, "H1_BINDINGS_INVALID"):
                validate_h1_packet(packet=packet_path, markdown=markdown_path)

            packet_path.write_bytes(canonical_json_bytes(packet))
            markdown_path.write_text("not a projection\n", encoding="utf-8")
            with self.assertRaisesRegex(H1Error, "H1_MARKDOWN_INVALID"):
                validate_h1_packet(packet=packet_path, markdown=markdown_path)

    def test_existing_signed_human_decision_is_validated_without_repair_or_upgrade(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            root = Path(directory)
            packet_path, _, packet = self._build(root)
            decision_path = root / "decision.json"
            decision = self._decision(packet)
            decision_path.write_bytes(canonical_json_bytes(decision))
            with self.assertRaisesRegex(H1Error, "H1_MANUAL_AUTHORIZATION_REQUIRED"):
                validate_h1_decision(packet=packet_path, decision=decision_path)

            changed = deepcopy(decision)
            assert isinstance(changed["fixture_reviews"], list)
            assert isinstance(changed["fixture_reviews"][0], dict)
            changed["fixture_reviews"][0]["signature"] = ""
            changed["decision_sha256"] = sha256_bytes(canonical_json_bytes({key: value for key, value in changed.items() if key != "decision_sha256"}))
            decision_path.write_bytes(canonical_json_bytes(changed))
            with self.assertRaisesRegex(H1Error, "H1_DECISION_REVIEW_INVALID"):
                validate_h1_decision(packet=packet_path, decision=decision_path)

    def test_disputed_item_forces_disputed_aggregate(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            root = Path(directory)
            packet_path, _, packet = self._build(root)
            decision_path = root / "decision.json"
            decision = self._decision(packet)
            assert isinstance(decision["fixture_reviews"], list)
            assert isinstance(decision["fixture_reviews"][0], dict)
            decision["fixture_reviews"][0]["disposition"] = "disputed"
            decision["decision_sha256"] = sha256_bytes(canonical_json_bytes({key: value for key, value in decision.items() if key != "decision_sha256"}))
            decision_path.write_bytes(canonical_json_bytes(decision))
            with self.assertRaisesRegex(H1Error, "H1_DISPUTE_AGGREGATION_INVALID"):
                validate_h1_decision(packet=packet_path, decision=decision_path)

    def test_human_can_sign_each_exact_packet_semantics_hash(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            root = Path(directory)
            packet_path, _, packet = self._build(root)
            decision_path = root / "decision.json"
            decision = self._decision(packet)
            reviews = decision["fixture_reviews"]
            assert isinstance(reviews, list)
            for review in reviews:
                assert isinstance(review, dict)
                semantics = review.pop("reviewed_semantics")
                review["reviewed_semantics_sha256"] = sha256_bytes(canonical_json_bytes(semantics))
            decision["decision_sha256"] = sha256_bytes(canonical_json_bytes({key: value for key, value in decision.items() if key != "decision_sha256"}))
            decision_path.write_bytes(canonical_json_bytes(decision))
            with self.assertRaisesRegex(H1Error, "H1_MANUAL_AUTHORIZATION_REQUIRED"):
                validate_h1_decision(packet=packet_path, decision=decision_path)

    def test_public_h1_validators_reject_swapped_packet_markdown_and_decision_leaves_and_fifos_without_consuming_or_blocking(self) -> None:
        """All public H1 authority leaves must pass through the descriptor-bound seam."""
        real_open = filesystem.os.open
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            root = Path(directory)
            packet_path, markdown_path, packet = self._build(root)
            decision_path = root / "decision.json"
            decision_path.write_bytes(canonical_json_bytes(self._decision(packet)))
            schema = root / "canonical-adjudication-v1.json"
            h1_schema = root / "h1-source-gold-review-v1.json"
            schema.write_bytes(h1._SCHEMA.read_bytes())
            h1_schema.write_bytes(h1._H1_SCHEMA.read_bytes())
            external = root / "external.json"
            external.write_text('{"sentinel":"external"}\n', encoding="utf-8")

            for leaf, code, validator in (
                (packet_path, "H1_PACKET_INVALID", lambda: validate_h1_packet(packet=packet_path, markdown=markdown_path)),
                (markdown_path, "H1_MARKDOWN_INVALID", lambda: validate_h1_packet(packet=packet_path, markdown=markdown_path)),
                (decision_path, "H1_DECISION_INVALID", lambda: validate_h1_decision(packet=packet_path, decision=decision_path)),
                (schema, "H1_BINDINGS_INVALID", lambda: validate_h1_packet(packet=packet_path, markdown=markdown_path)),
                (h1_schema, "H1_BINDINGS_INVALID", lambda: validate_h1_packet(packet=packet_path, markdown=markdown_path)),
            ):
                with self.subTest(leaf=leaf.name):
                    relative = leaf.relative_to(self.root).as_posix()

                    def reject_target(root: Path, candidate: str):
                        if candidate == relative:
                            raise FilesystemPolicyError("SPECIAL_FILE_KIND_REJECTED")
                        return read_authoritative_file(root, candidate)

                    with mock.patch.object(h1, "_SCHEMA", schema), mock.patch.object(h1, "_H1_SCHEMA", h1_schema), mock.patch(
                        "specchoice_measurement.h1.read_authoritative_file", side_effect=reject_target, create=True
                    ):
                        with self.assertRaisesRegex(H1Error, code):
                            validator()

            leaf = root / "race-leaf.json"
            for kind in ("symlink", "fifo"):
                with self.subTest(kind=kind):
                    leaf.write_bytes(b"{}")
                    opened = False

                    def guarded_open(path, flags, *args, **kwargs):
                        nonlocal opened
                        if path != leaf.name or "dir_fd" not in kwargs:
                            return real_open(path, flags, *args, **kwargs)
                        opened = True
                        if kind == "symlink":
                            leaf.unlink()
                            leaf.symlink_to(external)
                            return real_open(path, flags, *args, **kwargs)
                        self.fail("FIFO target reached os.open")

                    if kind == "fifo":
                        leaf.unlink()
                        os.mkfifo(leaf)
                    with mock.patch("specchoice_evidence.filesystem.os.open", side_effect=guarded_open):
                        with self.assertRaises((FilesystemPolicyError, OSError)):
                            read_authoritative_file(root, leaf.name)
                    self.assertEqual(opened, kind == "symlink")
                    if leaf.is_symlink() or leaf.exists():
                        leaf.unlink()


if __name__ == "__main__":
    unittest.main()
