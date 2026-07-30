# SPDX-License-Identifier: BSD-3-Clause-Clear
from __future__ import annotations

import tempfile
import unittest
import json
import shutil
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from specchoice_evidence.baseline import BoundaryResult
from specchoice_evidence.canonical import canonical_json_bytes, sha256_bytes
from specchoice_evidence.cli import (
    _require_current_boundary_clean,
    _restart_lineage_for_local_mvp_receipt,
    build_parser,
)
from specchoice_evidence.receipt import (
    ReceiptError,
    build_local_mvp_receipt,
    build_blocked_receipt,
    local_receipt_basis_sha256,
    render_markdown,
    validate_receipt,
    write_receipt_package,
)
from specchoice_evidence.source_contract import (
    SourceContractProposalError,
    validate_local_accepted_generation_decision,
)


class IntegrityReceiptTests(unittest.TestCase):
    @staticmethod
    def _identity() -> dict[str, object]:
        return {
            "candidate_relative_path": "bundles/candidates/fixture",
            "core_sha256": "c" * 64,
            "generation": "fixture",
            "root_sha256": "d" * 64,
            "snapshot_manifest_sha256": "e" * 64,
        }

    @staticmethod
    def _classifications() -> list[dict[str, object]]:
        return [{
            "path": ".DS_Store", "status": "preexisting_unrelated", "attributed_to_phase": False,
            "blocking": False, "diagnostic": "DS_STORE_IGNORED_OS_METADATA",
        }]

    @staticmethod
    def _restart_lineage(baseline_sha256: str) -> dict[str, object]:
        return {
            "allowlist": {"path": "config/allowlist.json", "sha256": "b" * 64},
            "baseline": {"path": "baselines/phase-start.json", "sha256": baseline_sha256},
            "incident_receipt": {"path": "receipts/restart.json", "sha256": "c" * 64},
            "previous_baseline": {"path": "baselines/phase-start-v1.json", "sha256": "d" * 64},
            "reason_code": "D15_RESTART_COMMITTED_HISTORY_BLIND_SPOT",
            "reviewed_revision": "a" * 40,
            "scope": "gap_closure_only",
        }

    def test_v5_integrity_receipt_binds_restart_and_preserves_accepted_bundle_identity(self) -> None:
        """The v5 receipt is local-only and derives its Markdown solely from canonical JSON."""
        root = Path(__file__).resolve().parents[1]
        receipt_path = root / "receipts/integrity-receipt-v5.json"
        receipt = validate_receipt(receipt_path)
        self.assertEqual(receipt["schema_version"], "3")
        self.assertEqual(receipt["source_identity"]["generation"], "source-contract-v2-pr2192-86a0021b-verifier-rooted-v1")
        self.assertEqual(receipt["source_identity"]["core_sha256"], "6ca1f176c84464d499d6c0e81d03ba3f23fdcdd1b5bd43bc28d9b2153a797495")
        self.assertEqual(receipt["source_identity"]["root_sha256"], "aacdda8218e3779747ae2dec45f9da81822f615ec4b257e55b0766baf8317d5a")
        self.assertEqual(receipt["source_identity"]["snapshot_manifest_sha256"], "1c81f84cf4894a7ecfde4b72e17d6e479a91cb0cfa408258611b00bdf5e2e397")
        self.assertFalse(receipt["source_identity"]["external_publication_authorized"])
        restart = receipt["restart_lineage"]
        self.assertEqual(restart["baseline"]["sha256"], "a0b9f9fdddb42f042bd6dfa8753b012c4514adbb4d8be4ea6faefdcafc402e40")
        self.assertEqual(restart["allowlist"]["sha256"], "8008c839c32f91b2f973f4799ebb27e58e010569057f3f7a4d96c9bcec6d9903")
        self.assertEqual(restart["incident_receipt"]["sha256"], "80b54ba1e45a00d391614cea7e2ffaf53b05ea966a52c1c26f8e0f8bb6ba42fd")
        self.assertEqual(render_markdown(receipt), (root / "receipts/integrity-receipt-v5.md").read_text(encoding="utf-8"))
        self.assertEqual(render_markdown(json.loads(receipt_path.read_text(encoding="utf-8"))), render_markdown(receipt))

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
        identity = self._identity()
        classifications = self._classifications()
        basis = local_receipt_basis_sha256("a" * 64, "b" * 64, identity, classifications)
        receipt = build_local_mvp_receipt(
            "a" * 64, "b" * 64, identity, classifications, "f" * 64, basis
        )
        self.assertEqual(receipt["outcome"], "pass")
        self.assertEqual(receipt["source_identity"]["kind"], "local_accepted_generation")
        self.assertFalse(receipt["source_identity"]["external_publication_authorized"])
        self.assertEqual(render_markdown(receipt), render_markdown(receipt))

    def test_revision_bound_receipt_and_decision_require_projection_binding(self) -> None:
        identity = self._identity()
        classifications = self._classifications()
        revision = "a" * 40
        projection = "b" * 64
        basis = local_receipt_basis_sha256(
            "a" * 64,
            "b" * 64,
            identity,
            classifications,
            reviewed_revision=revision,
            committed_boundary_projection_sha256=projection,
        )
        receipt = build_local_mvp_receipt(
            "a" * 64,
            "b" * 64,
            identity,
            classifications,
            "f" * 64,
            basis,
            restart_lineage=self._restart_lineage("a" * 64),
            reviewed_revision=revision,
            committed_boundary_projection_sha256=projection,
        )
        self.assertEqual(receipt["schema_version"], "4")
        self.assertEqual(receipt["reviewed_revision"], revision)
        self.assertEqual(receipt["committed_boundary_projection_sha256"], projection)
        decision = {
            "approval_scope": "local_accepted_generation_only",
            "approved_generation": identity,
            "authorization": {
                "external_publication_authorized": False,
                "local_accepted_generation_authorized": True,
            },
            "committed_boundary_projection_sha256": projection,
            "phase_start_baseline_sha256": "a" * 64,
            "reviewed_receipt_basis_sha256": basis,
            "reviewed_revision": revision,
            "reviewer": {"disposition": "approved_local_only"},
            "schema_version": "3",
            "state": "local_accepted_generation_authorized",
        }
        self.assertEqual(validate_local_accepted_generation_decision(decision)["schema_version"], "3")
        decision["reviewed_revision"] = "HEAD"
        with self.assertRaisesRegex(SourceContractProposalError, "LOCAL_ACCEPTANCE_REVIEWED_REVISION_INVALID"):
            validate_local_accepted_generation_decision(decision)

    def test_shared_issuance_and_finalization_gate_rejects_current_boundary_violation(self) -> None:
        result = BoundaryResult("a" * 64, [], 1)
        with patch("specchoice_evidence.cli.check_current_boundary", return_value=result):
            with self.assertRaisesRegex(ReceiptError, "LOCAL_MVP_CURRENT_BOUNDARY_BLOCKING"):
                _require_current_boundary_clean(Path("repository"), Path("baseline.json"))

    def test_compute_basis_cli_is_canonical_from_experiment_and_repository_cwds(self) -> None:
        experiment_root = Path(__file__).resolve().parents[1]
        repository_root = experiment_root.parents[1]
        revision = subprocess.run(
            ["git", "-C", os.fspath(repository_root), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        command = [
            sys.executable, "-m", "specchoice_evidence.cli", "compute-local-mvp-receipt-basis",
            "--environment-decision", os.fspath(experiment_root / "receipts/environment-decision.json"),
            "--accepted-directory", os.fspath(experiment_root / "bundles/accepted"),
            "--approved-generation", "source-contract-v2-pr2192-86a0021b-verifier-rooted-v1",
            "--candidate-relative-path", "bundles/candidates/source-contract-v2-pr2192-86a0021b-verifier-rooted-v1",
            "--reviewed-revision", revision,
        ]
        environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": os.fspath(experiment_root / "src")}
        outputs = [
            subprocess.run(command, cwd=cwd, env=environment, check=True, capture_output=True).stdout
            for cwd in (experiment_root, repository_root)
        ]
        self.assertEqual(outputs[0], outputs[1])
        proposal = json.loads(outputs[0])
        self.assertTrue(proposal["proposal_only"])
        self.assertEqual(proposal["status"], "proposal_only")
        self.assertEqual(proposal["reviewed_revision"], revision)
        self.assertEqual(proposal["source_identity"]["candidate_relative_path"], "bundles/candidates/source-contract-v2-pr2192-86a0021b-verifier-rooted-v1")

    def test_local_receipt_basis_mismatch_rejects_schema_two_and_three_construction(self) -> None:
        identity = self._identity()
        classifications = self._classifications()
        for restart_lineage in (None, self._restart_lineage("a" * 64)):
            with self.subTest(schema="3" if restart_lineage else "2"):
                with self.assertRaisesRegex(ReceiptError, "LOCAL_RECEIPT_BASIS_MISMATCH"):
                    build_local_mvp_receipt(
                        "a" * 64,
                        "b" * 64,
                        identity,
                        classifications,
                        "f" * 64,
                        "0" * 64,
                        restart_lineage=restart_lineage,
                    )

    def test_schema_three_lineage_baseline_mismatch_rejects_validation_and_finalization(self) -> None:
        root = Path(__file__).resolve().parents[1]
        receipt = json.loads((root / "receipts/integrity-receipt-v5.json").read_text(encoding="utf-8"))
        receipt["phase_start_baseline_sha256"] = "0" * 64
        projected = dict(receipt)
        projected.pop("receipt_sha256")
        receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(projected))
        with self.assertRaisesRegex(ReceiptError, "RESTART_LINEAGE_BASELINE_MISMATCH"):
            validate_receipt(receipt)
        with tempfile.TemporaryDirectory() as directory:
            receipt_path = Path(directory) / "integrity-receipt.json"
            markdown_path = Path(directory) / "integrity-receipt.md"
            receipt_path.write_bytes(canonical_json_bytes(receipt))
            markdown_path.write_text("not reached\n", encoding="utf-8")
            arguments = build_parser().parse_args(
                [
                    "finalize-review",
                    "--decision", str(root / "receipts/reviewer-boundary-decision.json"),
                    "--receipt", str(receipt_path),
                    "--markdown", str(markdown_path),
                ]
            )
            with self.assertRaisesRegex(ReceiptError, "RESTART_LINEAGE_BASELINE_MISMATCH"):
                arguments.handler(arguments)

    def test_finalization_requires_the_exact_restart_projection(self) -> None:
        root = Path(__file__).resolve().parents[1]
        receipt = json.loads((root / "receipts/integrity-receipt-v5.json").read_text(encoding="utf-8"))
        receipt["restart_lineage"]["reviewed_revision"] = "0" * 40
        projected = dict(receipt)
        projected.pop("receipt_sha256")
        receipt["receipt_sha256"] = sha256_bytes(canonical_json_bytes(projected))
        with tempfile.TemporaryDirectory() as directory:
            fixture_root = Path(directory)
            for relative_path in (
                "baselines/phase-start-v5-gap-closure.json",
                "baselines/phase-start-v2.json",
                "config/boundary_allowlist-v5-gap-closure.json",
                "receipts/boundary-restart-v5.json",
            ):
                destination = fixture_root / relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(root / relative_path, destination)
            receipt_path = fixture_root / "receipts/integrity-receipt.json"
            markdown_path = fixture_root / "receipts/integrity-receipt.md"
            receipt_path.write_bytes(canonical_json_bytes(receipt))
            markdown_path.write_text("not reached\n", encoding="utf-8")
            arguments = build_parser().parse_args(
                [
                    "finalize-review",
                    "--decision", str(root / "receipts/reviewer-boundary-decision.json"),
                    "--receipt", str(receipt_path),
                    "--markdown", str(markdown_path),
                ]
            )
            with self.assertRaisesRegex(ReceiptError, "HISTORICAL_RECEIPT_NOT_FINALIZABLE"):
                arguments.handler(arguments)

    def test_active_defaults_are_v5_from_experiment_and_repository_roots(self) -> None:
        experiment_root = Path(__file__).resolve().parents[1]
        repository_root = experiment_root.parents[1]
        expected_baseline = experiment_root / "baselines/phase-start-v5-gap-closure.json"
        expected_restart = experiment_root / "receipts/boundary-restart-v5.json"
        original_cwd = Path.cwd()
        try:
            for cwd in (experiment_root, repository_root):
                os.chdir(cwd)
                parser = build_parser()
                boundary = parser.parse_args(["check-boundary"])
                receipt = parser.parse_args(["write-local-mvp-receipt", "--decision", "decision.json"])
                self.assertEqual(boundary.baseline, expected_baseline)
                self.assertEqual(receipt.baseline, expected_baseline)
                self.assertEqual(receipt.restart_receipt, expected_restart)
                self.assertEqual(boundary.handler(boundary), 0)
        finally:
            os.chdir(original_cwd)

    def test_v5_write_without_restart_fails_closed_before_receipt_issuance(self) -> None:
        root = Path(__file__).resolve().parents[1]
        arguments = build_parser().parse_args(
            [
                "write-local-mvp-receipt",
                "--decision", str(root / "receipts/reviewer-boundary-decision.json"),
                "--baseline", str(root / "baselines/phase-start-v5-gap-closure.json"),
            ]
        )
        arguments.restart_receipt = None
        with self.assertRaisesRegex(ReceiptError, "RESTART_RECEIPT_REQUIRED"):
            arguments.handler(arguments)

    def test_explicit_historical_baseline_uses_schema_two_compatibility_without_restart(self) -> None:
        root = Path(__file__).resolve().parents[1]
        arguments = build_parser().parse_args(
            [
                "write-local-mvp-receipt",
                "--decision", str(root / "receipts/reviewer-boundary-decision.json"),
                "--baseline", str(root / "baselines/phase-start-v2.json"),
            ]
        )
        self.assertIsNone(_restart_lineage_for_local_mvp_receipt(arguments))

    def test_write_command_rejects_recomputed_basis_that_differs_from_decision(self) -> None:
        root = Path(__file__).resolve().parents[1]
        arguments = build_parser().parse_args(
            [
                "write-local-mvp-receipt",
                "--decision", str(root / "receipts/reviewer-boundary-decision.json"),
                "--accepted-directory", str(root / "bundles/accepted"),
                "--baseline", str(root / "baselines/phase-start-v5-gap-closure.json"),
                "--environment-decision", str(root / "receipts/environment-decision.json"),
                "--receipt", str(root / "receipts/should-not-write.json"),
                "--markdown", str(root / "receipts/should-not-write.md"),
                "--restart-receipt", str(root / "receipts/boundary-restart-v5.json"),
            ]
        )
        with self.assertRaisesRegex(ReceiptError, "LOCAL_RECEIPT_BASIS_MISMATCH"):
            arguments.handler(arguments)

    def test_historical_schema_three_receipt_cannot_finalize(self) -> None:
        root = Path(__file__).resolve().parents[1]
        arguments = build_parser().parse_args(
            [
                "finalize-review",
                "--decision", str(root / "receipts/reviewer-boundary-decision.json"),
                "--receipt", str(root / "receipts/integrity-receipt-v5.json"),
                "--markdown", str(root / "receipts/integrity-receipt-v5.md"),
            ]
        )
        with self.assertRaisesRegex(ReceiptError, "HISTORICAL_RECEIPT_NOT_FINALIZABLE"):
            arguments.handler(arguments)

    def test_historical_schema_two_receipt_cannot_finalize(self) -> None:
        root = Path(__file__).resolve().parents[1]
        arguments = build_parser().parse_args(
            [
                "finalize-review",
                "--decision", str(root / "receipts/reviewer-boundary-decision.json"),
                "--receipt", str(root / "receipts/integrity-receipt.json"),
                "--markdown", str(root / "receipts/integrity-receipt.md"),
            ]
        )
        with self.assertRaisesRegex(ReceiptError, "HISTORICAL_RECEIPT_NOT_FINALIZABLE"):
            arguments.handler(arguments)


if __name__ == "__main__":
    unittest.main()
