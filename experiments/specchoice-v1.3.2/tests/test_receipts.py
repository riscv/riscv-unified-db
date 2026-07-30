# SPDX-License-Identifier: BSD-3-Clause-Clear
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from specchoice_evidence.canonical import canonical_json_bytes, sha256_bytes
from specchoice_evidence.receipt import (
    ReceiptError,
    build_local_mvp_receipt,
    build_blocked_receipt,
    local_receipt_basis_sha256,
    render_markdown,
    validate_receipt,
    write_receipt_package,
)


class IntegrityReceiptTests(unittest.TestCase):
    def test_rejected_source_receipt_is_canonical_and_markdown_is_json_only(self) -> None:
        receipt = build_blocked_receipt(
            baseline_sha256="a" * 64,
            environment_sha256="b" * 64,
            rejected_attempt_sha256="c" * 64,
            boundary_classifications=[
                {"path": ".DS_Store", "status": "preexisting_unrelated", "attributed_to_phase": False,
                 "blocking": False, "diagnostic": "DS_STORE_IGNORED_OS_METADATA"}
            ],
        )
        validated = validate_receipt(receipt)
        self.assertEqual(validated["outcome"], "fail")
        self.assertFalse(validated["reviewer_package_complete"])
        self.assertIn("SOURCE_GENERATION_NOT_ACCEPTED", validated["blocking_diagnostics"])
        markdown = render_markdown(validated)
        self.assertEqual(markdown, render_markdown(validated))
        self.assertIn(validated["receipt_sha256"], markdown)

    def test_receipt_hash_and_markdown_failure_do_not_invalidate_json_authority(self) -> None:
        receipt = build_blocked_receipt("a" * 64, "b" * 64, "c" * 64, [])
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "integrity-receipt.json"
            markdown = Path(directory) / "missing" / "integrity-receipt.md"
            result = write_receipt_package(receipt, destination, markdown)
            self.assertEqual(result["receipt_sha256"], receipt["receipt_sha256"])
            self.assertFalse(result["reviewer_package_complete"])
            self.assertEqual(destination.read_bytes(), canonical_json_bytes(result))
            validate_receipt(destination)
        broken = dict(receipt)
        broken["receipt_sha256"] = "0" * 64
        with self.assertRaisesRegex(ReceiptError, "RECEIPT_SELF_HASH_MISMATCH"):
            validate_receipt(broken)

    def test_local_mvp_receipt_is_pass_only_for_local_identity_with_external_publication_false(self) -> None:
        identity = {
            "candidate_relative_path": "bundles/candidates/fixture",
            "core_sha256": "c" * 64,
            "generation": "fixture",
            "root_sha256": "d" * 64,
            "snapshot_manifest_sha256": "e" * 64,
        }
        classifications = [{
            "path": ".DS_Store", "status": "preexisting_unrelated", "attributed_to_phase": False,
            "blocking": False, "diagnostic": "DS_STORE_IGNORED_OS_METADATA",
        }]
        basis = local_receipt_basis_sha256("a" * 64, "b" * 64, identity, classifications)
        receipt = build_local_mvp_receipt(
            "a" * 64, "b" * 64, identity, classifications, "f" * 64, basis
        )
        self.assertEqual(receipt["outcome"], "pass")
        self.assertEqual(receipt["source_identity"]["kind"], "local_accepted_generation")
        self.assertFalse(receipt["source_identity"]["external_publication_authorized"])
        self.assertEqual(render_markdown(receipt), render_markdown(receipt))


if __name__ == "__main__":
    unittest.main()
