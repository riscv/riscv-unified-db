# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Fail-closed validation tests for pending source-contract corrections."""

from __future__ import annotations

import copy
import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path

from specchoice_evidence.source_contract import (
    SourceContractProposalError,
    validate_source_contract_proposal,
    verify_source_contract_proposal_git,
)


def git(*arguments: str, cwd: Path | None = None) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def proposal_for(raw: bytes, commit: str, tree: str) -> dict[str, object]:
    return {
        "schema_version": "1",
        "status": "pending_reviewer_approval",
        "proposed_contract_version": "2",
        "requested_generation_label": "candidate-v2",
        "base_frozen_contract": {"path": "config/source_snapshots.json", "sha256": "a" * 64},
        "historical_rejected_receipt": {"path": "bundles/rejected/receipt.json", "sha256": "b" * 64},
        "snapshots": [
            {
                "snapshot_id": "fixture",
                "repository": "example/repository",
                "pull_request": 7,
                "pinned_commit_sha": commit,
                "pinned_tree_sha": tree,
                "canonical_pr_head_sha": commit,
                "reachability": "equal_head",
                "change_control": "versioned_correction",
            }
        ],
        "consumed_files": [
            {
                "snapshot_id": "fixture",
                "upstream_path": "fixture.txt",
                "local_bundle_path": "raw/fixture.txt",
                "experimental_role": "test fixture",
                "why_consumed": "Proves exact byte custody.",
                "raw_authoritative": True,
                "raw_byte_length": len(raw),
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "declared_transforms": [],
            }
        ],
    }


class SourceContractProposalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.audit = self.root / "audit.git"
        git("init", "-q", self.source.as_posix())
        git("config", "user.email", "test@example.invalid", cwd=self.source)
        git("config", "user.name", "SpecChoice test", cwd=self.source)
        self.raw = b"fixture\r\n"
        (self.source / "fixture.txt").write_bytes(self.raw)
        git("add", "fixture.txt", cwd=self.source)
        git("commit", "-qm", "fixture", cwd=self.source)
        self.commit = git("rev-parse", "HEAD", cwd=self.source)
        self.tree = git("rev-parse", "HEAD^{tree}", cwd=self.source)
        git("clone", "--bare", "-q", self.source.as_posix(), self.audit.as_posix())
        git("--git-dir", self.audit.as_posix(), "update-ref", "refs/specchoice/pr/7", self.commit)
        self.proposal = proposal_for(self.raw, self.commit, self.tree)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_complete_pending_proposal_has_local_git_proof(self) -> None:
        validate_source_contract_proposal(self.proposal)
        verify_source_contract_proposal_git(self.proposal, self.audit)

    def test_missing_required_file_fields_fail_closed(self) -> None:
        for field in (
            "upstream_path",
            "local_bundle_path",
            "experimental_role",
            "raw_sha256",
            "raw_byte_length",
            "declared_transforms",
        ):
            invalid = copy.deepcopy(self.proposal)
            del invalid["consumed_files"][0][field]
            with self.subTest(field=field), self.assertRaises(SourceContractProposalError):
                validate_source_contract_proposal(invalid)

    def test_missing_role_or_transform_details_fail_closed(self) -> None:
        invalid = copy.deepcopy(self.proposal)
        invalid["consumed_files"][0]["declared_transforms"] = [{"name": "normalize"}]
        with self.assertRaisesRegex(SourceContractProposalError, "TRANSFORM_PARAMETERS_MISSING"):
            validate_source_contract_proposal(invalid)

    def test_git_proof_rejects_tampered_raw_hash_or_non_blob_path(self) -> None:
        tampered_hash = copy.deepcopy(self.proposal)
        tampered_hash["consumed_files"][0]["raw_sha256"] = "0" * 64
        with self.assertRaisesRegex(SourceContractProposalError, "RAW_SHA256_MISMATCH"):
            verify_source_contract_proposal_git(tampered_hash, self.audit)

        directory_path = copy.deepcopy(self.proposal)
        directory_path["consumed_files"][0]["upstream_path"] = "."
        with self.assertRaises(SourceContractProposalError):
            verify_source_contract_proposal_git(directory_path, self.audit)


if __name__ == "__main__":
    unittest.main()
