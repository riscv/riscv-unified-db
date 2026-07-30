# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Byte-custody and non-accepted candidate bundle tests."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from specchoice_evidence.bundle import BundleError, construct_candidate, publish_accepted, verify_candidate
from specchoice_evidence.canonical import canonical_json_bytes, sha256_bytes
from specchoice_evidence.source_contract import (
    SourceContractProposalError,
    require_accepted_publication_authorization,
    validate_source_publication_decision,
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
        "snapshots": [{
            "snapshot_id": "fixture",
            "repository": "example/repository",
            "pull_request": 7,
            "pinned_commit_sha": commit,
            "pinned_tree_sha": tree,
            "canonical_pr_head_sha": commit,
            "reachability": "equal_head",
            "change_control": "versioned_correction",
        }],
        "consumed_files": [{
            "snapshot_id": "fixture",
            "upstream_path": "fixture.txt",
            "local_bundle_path": "raw/fixture.txt",
            "experimental_role": "test fixture",
            "why_consumed": "Proves byte custody.",
            "raw_authoritative": True,
            "raw_byte_length": len(raw),
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "declared_transforms": [],
        }],
    }


def candidate_decision_for(proposal: dict[str, object]) -> dict[str, object]:
    return {
        "approval_scope": "candidate_construction_only",
        "approved_contract": {
            "base_frozen_contract": proposal["base_frozen_contract"],
            "consumed_files": proposal["consumed_files"],
            "historical_rejected_receipt": proposal["historical_rejected_receipt"],
            "proposed_contract_version": proposal["proposed_contract_version"],
            "requested_generation_label": proposal["requested_generation_label"],
            "snapshots": proposal["snapshots"],
        },
        "authorization": {
            "accepted_publication_authorized": False,
            "candidate_construction_authorized": True,
            "source_extraction_authorized": True,
        },
        "proposal": {
            "path": "receipts/source-contract-correction-proposal-v2.json",
            "sha256": sha256_bytes(canonical_json_bytes(proposal)),
        },
        "reviewer": {"approval_token": "authorize-candidate-construction-only"},
        "schema_version": "1",
        "state": "candidate_construction_authorized",
    }


class CandidateBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.audit = self.root / "audit.git"
        git("init", "-q", self.source.as_posix())
        git("config", "user.email", "test@example.invalid", cwd=self.source)
        git("config", "user.name", "SpecChoice test", cwd=self.source)
        self.raw = "decomposed-e\u0301\r\n".encode("utf-8")
        (self.source / "fixture.txt").write_bytes(self.raw)
        git("add", "fixture.txt", cwd=self.source)
        git("commit", "-qm", "fixture", cwd=self.source)
        self.commit = git("rev-parse", "HEAD", cwd=self.source)
        self.tree = git("rev-parse", "HEAD^{tree}", cwd=self.source)
        git("clone", "--bare", "-q", self.source.as_posix(), self.audit.as_posix())
        git("--git-dir", self.audit.as_posix(), "update-ref", "refs/specchoice/pr/7", self.commit)
        self.proposal = proposal_for(self.raw, self.commit, self.tree)
        self.decision = candidate_decision_for(self.proposal)
        self.candidates = self.root / "bundles" / "candidates"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_candidate_copies_exact_git_blob_and_has_deterministic_noncyclic_binding(self) -> None:
        result = construct_candidate(self.decision, self.proposal, self.audit, self.candidates)
        candidate = self.candidates / "candidate-v2"
        self.assertEqual(result["status"], "candidate")
        self.assertEqual((candidate / "raw/fixture.txt").read_bytes(), self.raw)
        self.assertEqual(verify_candidate(candidate)["root_sha256"], result["root_sha256"])
        self.assertFalse((self.root / "bundles" / "accepted").exists())
        with self.assertRaisesRegex(BundleError, "CANDIDATE_TARGET_EXISTS"):
            construct_candidate(self.decision, self.proposal, self.audit, self.candidates)

    def test_tampered_final_bindings_and_raw_bytes_fail_closed(self) -> None:
        construct_candidate(self.decision, self.proposal, self.audit, self.candidates)
        candidate = self.candidates / "candidate-v2"
        manifest_path = candidate / "snapshot-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["snapshots"][0]["root_sha256"] = "0" * 64
        manifest_path.write_bytes(canonical_json_bytes(manifest))
        with self.assertRaisesRegex(BundleError, "SNAPSHOT_MANIFEST_SELF_DIGEST_MISMATCH"):
            verify_candidate(candidate)

    def test_recomputed_top_level_and_per_snapshot_binding_tampering_rejects(self) -> None:
        construct_candidate(self.decision, self.proposal, self.audit, self.candidates)
        candidate = self.candidates / "candidate-v2"
        manifest_path = candidate / "snapshot-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["generation"] = "other"
        without_self = dict(manifest)
        without_self.pop("snapshot_manifest_sha256")
        manifest["snapshot_manifest_sha256"] = sha256_bytes(canonical_json_bytes(without_self))
        manifest_path.write_bytes(canonical_json_bytes(manifest))
        with self.assertRaisesRegex(BundleError, "SNAPSHOT_BINDING_MISMATCH"):
            verify_candidate(candidate)

        construct_candidate(self.decision, self.proposal, self.audit, self.candidates / "second")
        candidate = self.candidates / "second" / "candidate-v2"
        manifest_path = candidate / "snapshot-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["snapshots"][0]["manifest_sha256"] = "0" * 64
        without_self = dict(manifest)
        without_self.pop("snapshot_manifest_sha256")
        manifest["snapshot_manifest_sha256"] = sha256_bytes(canonical_json_bytes(without_self))
        manifest_path.write_bytes(canonical_json_bytes(manifest))
        with self.assertRaisesRegex(BundleError, "SNAPSHOT_BINDING_MISMATCH"):
            verify_candidate(candidate)

    def test_interruption_alias_special_file_and_accepted_publication_all_fail_closed(self) -> None:
        invalid = copy.deepcopy(self.proposal)
        invalid["consumed_files"][0]["raw_sha256"] = "0" * 64
        with self.assertRaisesRegex(BundleError, "RAW_SHA256_MISMATCH"):
            construct_candidate(candidate_decision_for(invalid), invalid, self.audit, self.candidates)
        self.assertEqual(list(self.candidates.glob(".candidate-v2.staging-*")), [])
        self.assertFalse((self.root / "bundles" / "accepted").exists())

        construct_candidate(self.decision, self.proposal, self.audit, self.candidates)
        raw_path = self.candidates / "candidate-v2" / "raw" / "fixture.txt"
        raw_path.unlink()
        raw_path.symlink_to("missing-target")
        with self.assertRaisesRegex(BundleError, "SYMLINK_REJECTED"):
            verify_candidate(self.candidates / "candidate-v2")
        with self.assertRaisesRegex(BundleError, "ACCEPTED_PUBLICATION_NOT_AUTHORIZED"):
            publish_accepted(self.decision)

    def test_inventory_collision_and_accepted_scope_escalation_reject(self) -> None:
        invalid = copy.deepcopy(self.proposal)
        duplicate = copy.deepcopy(invalid["consumed_files"][0])
        duplicate["upstream_path"] = "nested.txt"
        duplicate["local_bundle_path"] = "raw/fixture.txt/child.txt"
        invalid["consumed_files"].append(duplicate)
        with self.assertRaisesRegex(BundleError, "LOCAL_PATH_COLLISION"):
            construct_candidate(candidate_decision_for(invalid), invalid, self.audit, self.candidates)

        decision = candidate_decision_for(self.proposal)
        decision["authorization"]["accepted_publication_authorized"] = True
        with self.assertRaisesRegex(SourceContractProposalError, "AUTHORIZATION_INVALID"):
            validate_source_publication_decision(
                decision,
                self.proposal,
                proposal_path="receipts/source-contract-correction-proposal-v2.json",
                proposal_sha256=sha256_bytes(canonical_json_bytes(self.proposal)),
            )
        with self.assertRaisesRegex(SourceContractProposalError, "ACCEPTED_PUBLICATION_NOT_AUTHORIZED"):
            require_accepted_publication_authorization(self.decision)


if __name__ == "__main__":
    unittest.main()
