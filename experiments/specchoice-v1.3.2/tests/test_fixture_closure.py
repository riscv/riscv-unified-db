# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Exact-set guards for the frozen PR #2164 fixture custody input."""

from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from specchoice_evidence.bundle import (
    BundleError,
    accept_fixture_closure_candidate,
    construct_fixture_closure_candidate,
    fixture_construction_candidate_audit,
    verify_candidate,
)
from specchoice_evidence.canonical import canonical_json_bytes, sha256_bytes
from specchoice_evidence.verify import _bundle_artifacts, _raw_artifacts, _root_digest, verify_accepted_bundle
from specchoice_evidence.source_contract import (
    FixtureRegistryError,
    SourceContractProposalError,
    require_fixture_closure_local_acceptance_authorization,
    validate_fixture_registry,
    verify_fixture_registry_git,
)


class FixtureClosureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.experiment = Path(__file__).resolve().parents[1]
        self.registry = json.loads(
            (self.experiment / "config/fixture-registry-pr2164-v1.json").read_text(encoding="utf-8")
        )
        self.repository = self.experiment.parents[1]

    def test_frozen_registry_proves_exactly_eleven_fixtures_and_twenty_eight_blobs(self) -> None:
        normalized = validate_fixture_registry(self.registry)
        self.assertEqual(normalized["fixture_count"], 11)
        self.assertEqual(normalized["raw_file_count"], 28)
        self.assertEqual(
            [entry["fixture_id"] for entry in normalized["fixtures"]],
            sorted(entry["fixture_id"] for entry in normalized["fixtures"]),
        )
        verify_fixture_registry_git(self.registry, self.repository)

    def test_registry_fails_closed_for_empty_missing_extra_duplicate_and_bad_role(self) -> None:
        for mutation, code in (
            (lambda value: value.update({"fixtures": []}), "FIXTURE_REGISTRY_EMPTY"),
            (lambda value: value["fixtures"].pop(), "FIXTURE_SET_MISMATCH"),
            (lambda value: value["fixtures"].append(copy.deepcopy(value["fixtures"][0])), "FIXTURE_DUPLICATE"),
            (lambda value: value["fixtures"][0]["files"].pop(), "FIXTURE_FILE_SET_MISMATCH"),
            (lambda value: value["fixtures"][0]["files"][0].update({"role": "gold"}), "FIXTURE_ROLE_MISMATCH"),
        ):
            invalid = copy.deepcopy(self.registry)
            mutation(invalid)
            with self.subTest(code=code), self.assertRaisesRegex(FixtureRegistryError, code):
                validate_fixture_registry(invalid)

    def test_registry_fails_closed_for_escape_and_git_byte_drift(self) -> None:
        invalid = copy.deepcopy(self.registry)
        invalid["fixtures"][0]["files"][0]["upstream_path"] = "../escape.txt"
        with self.assertRaisesRegex(FixtureRegistryError, "PATH_ESCAPE_DETECTED"):
            validate_fixture_registry(invalid)

        invalid = copy.deepcopy(self.registry)
        invalid["fixtures"][0]["files"][0]["raw_sha256"] = "0" * 64
        with self.assertRaisesRegex(FixtureRegistryError, "FIXTURE_RAW_SHA256_MISMATCH"):
            verify_fixture_registry_git(invalid, self.repository)


class FixtureClosureCandidateTests(unittest.TestCase):

    def _public_command(self, experiment: Path, *arguments: str) -> dict[str, object]:
        result = subprocess.run(
            [sys.executable, "-m", "specchoice_evidence.cli", *arguments],
            cwd=experiment,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_v3_local_acceptance_prepares_pending_cutover_without_switching_v2(self) -> None:
        """The public v10 flow is disposable, forward-only, and leaves v2 alone until cutover."""
        experiment = Path(__file__).resolve().parents[1]
        candidate = experiment / "bundles/candidates/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v3"
        active_v2 = experiment / "phase2/source-authority.json"
        audit = experiment / "receipts/fixture-closure-candidate-audit-v3.json"
        construction = experiment / "receipts/source-contract-decision-v3-pr2164-fixture-closure-verifier-rooted-v3.json"
        proposal = experiment / "receipts/source-contract-proposal-v3-pr2164-fixture-closure-verifier-rooted-v3.json"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = root / "local-acceptance-request-v10.json"
            self._public_command(
                experiment,
                "write-local-acceptance-request-v10", "--candidate", str(candidate), "--audit", str(audit),
                "--construction-decision", str(construction), "--proposal", str(proposal),
                "--active-authority", str(active_v2), "--request", str(request),
            )
            request_payload = json.loads(request.read_text(encoding="utf-8"))
            self.assertNotIn("reviewer_identity", request_payload)
            decision = {
                "candidate": request_payload["candidate"], "decision": "accept",
                "external_publication_authorized": False,
                "projected_accepted": request_payload["projected_accepted"],
                "rationale": "disposable public test", "request_sha256": sha256_bytes(request.read_bytes()),
                "reviewer_identity": "test-reviewer", "reviewed_at": "2026-08-02T00:00:00Z",
                "schema_version": "10", "verifier_artifacts": request_payload["verifier_artifacts"],
            }
            decision_path = root / "decision.json"
            decision_path.write_bytes(canonical_json_bytes(decision))
            accepted_root = root / "accepted"
            accepted = self._public_command(
                experiment,
                "accept-fixture-closure-local-v10", "--request", str(request), "--decision", str(decision_path),
                "--candidate", str(candidate), "--accepted-directory", str(accepted_root),
            )
            accepted_bundle = accepted_root / str(accepted["generation"])
            active = root / "source-authority.json"
            shutil.copyfile(active_v2, active)
            revocation = root / "fixture-closure-revocation-v2.json"
            self._public_command(
                experiment,
                "validate-phase2-source-authority", "--authority", str(active),
                "--bundle", str(experiment / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"),
                "--revocation", str(revocation), "--authority-mode", "active",
            )
            historical = root / "source-authority-v9-historical.json"
            shutil.copyfile(active, historical)
            pending = root / "source-authority-v10-pending.json"
            transition = root / "fixture-closure-transition-v2-to-v3.json"
            self._public_command(
                experiment,
                "prepare-pending-source-cutover-v10", "--request", str(request), "--decision", str(decision_path),
                "--old-authority", str(active), "--accepted-bundle", str(accepted_bundle),
                "--pending-authority", str(pending), "--transition", str(transition), "--revocation", str(revocation),
            )
            revocation.write_bytes(transition.read_bytes())
            failed_v2 = subprocess.run(
                [
                    sys.executable, "-m", "specchoice_evidence.cli", "validate-phase2-source-authority",
                    "--authority", str(active),
                    "--bundle", str(experiment / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"),
                    "--revocation", str(revocation), "--authority-mode", "active",
                ], cwd=experiment, check=False, capture_output=True, text=True,
            )
            self.assertNotEqual(failed_v2.returncode, 0)
            revocation.unlink()
            self._public_command(
                experiment,
                "validate-phase2-source-authority", "--authority", str(historical),
                "--bundle", str(experiment / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"),
                "--revocation", str(revocation), "--authority-mode", "historical-inspection",
            )
            self.assertFalse(self._public_command(
                experiment,
                "validate-phase2-source-authority", "--authority", str(historical),
                "--bundle", str(experiment / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"),
                "--revocation", str(revocation), "--authority-mode", "historical-inspection",
            )["eligible"])
            self.assertEqual(active.read_bytes(), active_v2.read_bytes())
            self.assertFalse(revocation.exists())
            self._public_command(
                experiment,
                "activate-pending-source-cutover-v10", "--pending-authority", str(pending), "--transition", str(transition),
                "--canonical-revocation", str(revocation), "--active-authority", str(active), "--accepted-bundle", str(accepted_bundle),
            )
            self.assertNotEqual(active.read_bytes(), active_v2.read_bytes())
            self.assertTrue(revocation.exists())
            self._public_command(
                experiment,
                "validate-phase2-source-authority", "--authority", str(active), "--bundle", str(accepted_bundle),
                "--revocation", str(revocation), "--authority-mode", "active",
            )
            self.assertEqual(
                self._public_command(
                    experiment,
                    "activate-pending-source-cutover-v10", "--pending-authority", str(pending), "--transition", str(transition),
                    "--canonical-revocation", str(revocation), "--active-authority", str(active), "--accepted-bundle", str(accepted_bundle),
                )["status"],
                "already_activated",
            )
            before = active.read_bytes()
            invalid_pending = root / "invalid-pending.json"
            invalid_pending.write_bytes(canonical_json_bytes({"schema_version": "10"}))
            with self.assertRaisesRegex(AssertionError, "SOURCE_CUTOVER"):
                self._public_command(
                    experiment,
                    "activate-pending-source-cutover-v10", "--pending-authority", str(invalid_pending),
                    "--transition", str(transition), "--canonical-revocation", str(revocation),
                    "--active-authority", str(active), "--accepted-bundle", str(accepted_bundle),
                )
            self.assertEqual(active.read_bytes(), before)

    def test_v3_copied_offline_replay_uses_embedded_hardened_verifier(self) -> None:
        """The v10 accepted successor verifies with only its embedded verifier."""
        experiment = Path(__file__).resolve().parents[1]
        candidate = experiment / "bundles/candidates/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v3"
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "candidate"
            shutil.copytree(candidate, copied)
            result = subprocess.run(
                [sys.executable, "verify_bundle.py"], cwd=copied,
                env={"PATH": "/nonexistent", "PYTHONDONTWRITEBYTECODE": "1"},
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_source_authority_and_bundle_consumers_reuse_descriptor_bound_canonical_bytes(self) -> None:
        """The public authority receipt is assembled from descriptor-read bundle leaves."""
        experiment = Path(__file__).resolve().parents[1]
        accepted = experiment / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"
        command = [
            sys.executable, "-m", "specchoice_evidence.cli", "validate-phase2-source-authority",
            "--authority", "phase2/source-authority.json", "--bundle", str(accepted),
        ]
        result = subprocess.run(command, cwd=experiment, check=False, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertEqual(result.stdout, canonical_json_bytes(json.loads(result.stdout.decode("utf-8"))))
        receipt = json.loads(result.stdout.decode("utf-8"))
        self.assertEqual(receipt["status"], "valid")
        self.assertEqual(set(receipt), {
            "fixture_count", "generation", "manifest_sha256", "pinned_commit_sha",
            "pinned_tree_sha", "raw_file_count", "registry_sha256", "root_sha256", "status",
        })

    def test_public_candidate_and_acceptance_paths_reject_rebound_control_leaves(self) -> None:
        """Public consumers fail closed before a special control leaf can be consumed."""
        experiment = Path(__file__).resolve().parents[1]
        candidate = experiment / "bundles/candidates/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "candidate"
            shutil.copytree(candidate, copied)
            registry = copied / "fixture-registry-pr2164-v1.json"
            registry.unlink()
            os.mkfifo(registry)
            with self.assertRaisesRegex(BundleError, "VERIFIER_ARTIFACT_INVALID|SPECIAL_FILE_KIND_REJECTED|STAGED_RAW_CUSTODY_MISMATCH"):
                verify_candidate(copied)

    def test_fixture_candidate_publish_rejects_racing_empty_target_without_overwrite(self) -> None:
        experiment = Path(__file__).resolve().parents[1]
        original = __import__("specchoice_evidence.bundle", fromlist=["_native_publish_no_replace"])._native_publish_no_replace

        def attacker(source: Path, target: Path) -> None:
            target.mkdir()
            original(source, target)

        with tempfile.TemporaryDirectory() as directory:
            candidates = Path(directory) / "candidates"
            target = candidates / "source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"
            with mock.patch("specchoice_evidence.bundle._native_publish_no_replace", side_effect=attacker):
                with self.assertRaisesRegex(BundleError, "CANDIDATE_TARGET_EXISTS"):
                    construct_fixture_closure_candidate(
                        json.loads((experiment / "receipts/source-contract-decision-v3-pr2164-fixture-closure-v2.json").read_text()),
                        json.loads((experiment / "receipts/source-contract-proposal-v3-pr2164-fixture-closure-v2.json").read_text()),
                        experiment / "config/fixture-registry-pr2164-v1.json",
                        experiment.parents[1],
                        candidates,
                    )
            self.assertTrue(target.is_dir())
            self.assertEqual(list(target.iterdir()), [])

    def test_fixture_accept_publish_rejects_racing_empty_target_without_overwrite(self) -> None:
        experiment = Path(__file__).resolve().parents[1]
        candidate = experiment / "bundles/candidates/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"
        original = __import__("specchoice_evidence.bundle", fromlist=["_native_publish_no_replace"])._native_publish_no_replace

        def attacker(source: Path, target: Path) -> None:
            target.mkdir()
            original(source, target)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            decision = self._write_fixture_acceptance_decision(
                root / "decision.json", self._current_fixture_acceptance_decision(experiment)
            )
            target = root / "accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"
            with mock.patch("specchoice_evidence.bundle._native_publish_no_replace", side_effect=attacker):
                with self.assertRaisesRegex(BundleError, "LOCAL_ACCEPTED_TARGET_EXISTS"):
                    accept_fixture_closure_candidate(candidate, root / "accepted", decision)
            self.assertTrue(target.is_dir())
            self.assertEqual(list(target.iterdir()), [])

    def test_fixture_candidate_publish_preserves_racing_nonempty_target(self) -> None:
        experiment = Path(__file__).resolve().parents[1]
        original = __import__("specchoice_evidence.bundle", fromlist=["_native_publish_no_replace"])._native_publish_no_replace

        def attacker(source: Path, target: Path) -> None:
            target.mkdir()
            (target / "attacker.txt").write_text("do not overwrite", encoding="utf-8")
            original(source, target)

        with tempfile.TemporaryDirectory() as directory:
            candidates = Path(directory) / "candidates"
            target = candidates / "source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"
            with mock.patch("specchoice_evidence.bundle._native_publish_no_replace", side_effect=attacker):
                with self.assertRaisesRegex(BundleError, "CANDIDATE_TARGET_EXISTS"):
                    construct_fixture_closure_candidate(
                        json.loads((experiment / "receipts/source-contract-decision-v3-pr2164-fixture-closure-v2.json").read_text()),
                        json.loads((experiment / "receipts/source-contract-proposal-v3-pr2164-fixture-closure-v2.json").read_text()),
                        experiment / "config/fixture-registry-pr2164-v1.json",
                        experiment.parents[1],
                        candidates,
                    )
            self.assertEqual((target / "attacker.txt").read_text(encoding="utf-8"), "do not overwrite")

    def test_fixture_publish_fails_closed_when_no_replace_primitive_is_unavailable(self) -> None:
        experiment = Path(__file__).resolve().parents[1]
        candidate = experiment / "bundles/candidates/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            decision = self._write_fixture_acceptance_decision(
                root / "decision.json", self._current_fixture_acceptance_decision(experiment)
            )
            with mock.patch("specchoice_evidence.bundle._native_publish_no_replace", side_effect=NotImplementedError):
                with self.assertRaisesRegex(BundleError, "ATOMIC_NO_REPLACE_UNAVAILABLE"):
                    accept_fixture_closure_candidate(candidate, root / "accepted", decision)

    def _current_fixture_acceptance_decision(self, experiment: Path) -> dict[str, object]:
        decision = json.loads((experiment / "receipts/local-acceptance-v9.json").read_text(encoding="utf-8"))
        decision["v7_basis"]["reviewed_revision"] = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=experiment.parents[1], check=True,
            capture_output=True, text=True,
        ).stdout.strip()
        return decision

    def _write_fixture_acceptance_decision(self, path: Path, decision: dict[str, object]) -> Path:
        path.write_bytes(canonical_json_bytes(decision))
        return path

    def test_public_fixture_acceptance_resolves_its_own_current_v7_basis(self) -> None:
        experiment = Path(__file__).resolve().parents[1]
        candidate = experiment / "bundles/candidates/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"
        decision = self._current_fixture_acceptance_decision(experiment)
        with tempfile.TemporaryDirectory() as directory:
            accepted_root = Path(directory) / "accepted"
            decision_path = self._write_fixture_acceptance_decision(Path(directory) / "decision.json", decision)
            result = accept_fixture_closure_candidate(candidate, accepted_root, decision_path)
            self.assertEqual(result["status"], "accepted")
            self.assertTrue((accepted_root / result["generation"]).is_dir())

    def test_public_fixture_acceptance_rejects_missing_mismatched_and_stale_authority(self) -> None:
        experiment = Path(__file__).resolve().parents[1]
        candidate = experiment / "bundles/candidates/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"
        decision = self._current_fixture_acceptance_decision(experiment)
        variants = (
            (None, "FIXTURE_CLOSURE_ACCEPTANCE_DECISION_INVALID"),
            ({**decision, "fixture_registry_sha256": "0" * 64}, "FIXTURE_CLOSURE_ACCEPTANCE_REGISTRY_MISMATCH"),
            ({**decision, "v7_basis": {**decision["v7_basis"], "reviewed_revision": "0" * 40}}, "FIXTURE_CLOSURE_ACCEPTANCE_BASIS_MISMATCH"),
        )
        for authority, code in variants:
            with self.subTest(code=code), tempfile.TemporaryDirectory() as directory:
                accepted_root = Path(directory) / "accepted"
                decision_path = (
                    None if authority is None
                    else self._write_fixture_acceptance_decision(Path(directory) / "decision.json", authority)
                )
                with self.assertRaisesRegex(BundleError, code):
                    accept_fixture_closure_candidate(candidate, accepted_root, decision_path)
                self.assertFalse(accepted_root.exists())

    def test_public_fixture_acceptance_rejects_current_boundary_violation(self) -> None:
        experiment = Path(__file__).resolve().parents[1]
        repository = experiment.parents[1]
        candidate = experiment / "bundles/candidates/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"
        violation = repository / "fixture-closure-boundary-violation.tmp"
        violation.write_text("must block acceptance", encoding="utf-8")
        try:
            with tempfile.TemporaryDirectory() as directory:
                decision_path = self._write_fixture_acceptance_decision(
                    Path(directory) / "decision.json", self._current_fixture_acceptance_decision(experiment)
                )
                with self.assertRaisesRegex(BundleError, "FIXTURE_CLOSURE_ACCEPTANCE_BOUNDARY_BLOCKING"):
                    accept_fixture_closure_candidate(
                        candidate, Path(directory) / "accepted", decision_path
                    )
        finally:
            violation.unlink()

    def test_local_acceptance_authority_is_bound_to_identity_registry_and_v7_basis(self) -> None:
        experiment = Path(__file__).resolve().parents[1]
        candidate = experiment / "bundles/candidates/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v1"
        identity = verify_candidate(candidate)
        final = json.loads((candidate / "snapshot-manifest.json").read_text(encoding="utf-8"))
        registry_sha256 = sha256_bytes((candidate / "fixture-registry-pr2164-v1.json").read_bytes())
        v7_basis = {
            "allowlist_sha256": "a" * 64,
            "baseline_sha256": "b" * 64,
            "restart_receipt_sha256": "c" * 64,
            "reviewed_revision": "d" * 40,
        }
        decision = {
            "approval_scope": "fixture_closure_local_acceptance_only",
            "approved_generation": {
                "candidate_relative_path": "bundles/candidates/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v1",
                "core_sha256": identity["manifest_sha256"],
                "generation": identity["generation"],
                "root_sha256": identity["root_sha256"],
                "snapshot_manifest_sha256": final["snapshot_manifest_sha256"],
            },
            "authorization": {
                "external_publication_authorized": False,
                "fixture_closure_local_acceptance_authorized": True,
            },
            "fixture_registry_sha256": registry_sha256,
            "reviewer": {"disposition": "approved_local_only"},
            "schema_version": "1",
            "state": "fixture_closure_local_acceptance_authorized",
            "v7_basis": v7_basis,
        }
        require_fixture_closure_local_acceptance_authorization(
            decision, identity, final["snapshot_manifest_sha256"], registry_sha256, v7_basis
        )
        for changed, code in (
            (None, "FIXTURE_CLOSURE_ACCEPTANCE_DECISION_INVALID"),
            ({**decision, "fixture_registry_sha256": "0" * 64}, "FIXTURE_CLOSURE_ACCEPTANCE_REGISTRY_MISMATCH"),
            ({**decision, "v7_basis": {**v7_basis, "reviewed_revision": "e" * 40}}, "FIXTURE_CLOSURE_ACCEPTANCE_BASIS_MISMATCH"),
        ):
            with self.subTest(code=code), self.assertRaisesRegex(SourceContractProposalError, code):
                require_fixture_closure_local_acceptance_authorization(
                    changed, identity, final["snapshot_manifest_sha256"], registry_sha256, v7_basis
                )

    def test_recanonicalized_subset_fails_embedded_fixture_closure(self) -> None:
        experiment = Path(__file__).resolve().parents[1]
        accepted = experiment / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "accepted"
            shutil.copytree(accepted, copied)
            core_path = copied / "content-manifest-core.json"
            core = json.loads(core_path.read_text(encoding="utf-8"))
            files = core["snapshots"][0]["consumed_files"]
            keep = files[:1]
            for entry in files[1:]:
                (copied / entry["local_bundle_path"]).unlink()
            core["snapshots"][0]["consumed_files"] = keep
            core_bytes = canonical_json_bytes(core)
            core_path.write_bytes(core_bytes)
            manifest_sha256 = sha256_bytes(core_bytes)
            artifacts = _raw_artifacts(core, copied) + _bundle_artifacts(core, copied)
            root_sha256 = _root_digest(manifest_sha256, artifacts)
            final_path = copied / "snapshot-manifest.json"
            final = json.loads(final_path.read_text(encoding="utf-8"))
            final["content_manifest_core"] = core
            final["manifest_sha256"] = manifest_sha256
            final["root_sha256"] = root_sha256
            final["snapshots"] = [
                {
                    **snapshot,
                    "generation": final["generation"],
                    "manifest_sha256": manifest_sha256,
                    "root_sha256": root_sha256,
                }
                for snapshot in core["snapshots"]
            ]
            final.pop("snapshot_manifest_sha256")
            final["snapshot_manifest_sha256"] = sha256_bytes(canonical_json_bytes(final))
            final_path.write_bytes(canonical_json_bytes(final))
            with self.assertRaisesRegex(Exception, "FIXTURE_CLOSURE_CORE_REGISTRY_MISMATCH"):
                verify_accepted_bundle(copied)

    def test_verifier_rooted_v3_candidate_has_fresh_root_and_unchanged_source_hashes(self) -> None:
        experiment = Path(__file__).resolve().parents[1]
        candidate = experiment / (
            "bundles/candidates/source-contract-v3-pr2164-fixture-closure-"
            "22e84458-verifier-rooted-v3"
        )
        identity = verify_candidate(candidate)
        self.assertEqual(identity["status"], "candidate")
        manifest = json.loads((candidate / "snapshot-manifest.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["downstream_eligible"])
        self.assertFalse(manifest["external_publication_authorized"])
        self.assertEqual(
            sum(len(snapshot["consumed_files"]) for snapshot in manifest["snapshots"]), 28
        )
        core = json.loads((candidate / "content-manifest-core.json").read_text(encoding="utf-8"))
        self.assertEqual(core["fixture_closure"]["fixture_count"], 11)
        self.assertEqual(core["fixture_closure"]["raw_file_count"], 28)
        self.assertEqual(len(core["bundle_artifacts"]), 6)
        self.assertEqual(
            [artifact["local_bundle_path"] for artifact in core["bundle_artifacts"] if artifact["kind"] == "verifier"],
            [
                "verifier/specchoice_evidence/__init__.py",
                "verifier/specchoice_evidence/canonical.py",
                "verifier/specchoice_evidence/filesystem.py",
                "verifier/specchoice_evidence/verify.py",
                "verify_bundle.py",
            ],
        )
        accepted = experiment / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"
        accepted_core = json.loads((accepted / "content-manifest-core.json").read_text(encoding="utf-8"))
        self.assertNotEqual(identity["manifest_sha256"], sha256_bytes((accepted / "content-manifest-core.json").read_bytes()))
        self.assertEqual(
            sorted(entry["raw_sha256"] for entry in core["snapshots"][0]["consumed_files"]),
            sorted(entry["raw_sha256"] for entry in accepted_core["snapshots"][0]["consumed_files"]),
        )
        proposal = json.loads((experiment / "receipts/source-contract-proposal-v3-pr2164-fixture-closure-verifier-rooted-v3.json").read_text())
        decision = json.loads((experiment / "receipts/source-contract-decision-v3-pr2164-fixture-closure-verifier-rooted-v3.json").read_text())
        audit = fixture_construction_candidate_audit(
            decision, proposal,
            "receipts/source-contract-proposal-v3-pr2164-fixture-closure-verifier-rooted-v3.json",
            "receipts/source-contract-decision-v3-pr2164-fixture-closure-verifier-rooted-v3.json",
            candidate,
        )
        self.assertEqual(audit["copied_isolation_replay"]["result"], "passed")

        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "candidate"
            shutil.copytree(candidate, copied)
            (copied / "raw/evaluation_fixtures/unexpected.txt").write_text("extra", encoding="utf-8")
            with self.assertRaisesRegex(BundleError, "BUNDLE_EXTRA_FILE"):
                verify_candidate(copied)
            (copied / "raw/evaluation_fixtures/unexpected.txt").unlink()
            (copied / "raw/evaluation_fixtures/POS_WARL_MTVEC_MODES/gold.yaml").unlink()
            with self.assertRaisesRegex(BundleError, "STAGED_RAW_CUSTODY_MISMATCH"):
                verify_candidate(copied)

    def test_accepted_v3_is_distinct_and_downstream_eligible(self) -> None:
        experiment = Path(__file__).resolve().parents[1]
        candidate = experiment / "bundles/candidates/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v1"
        accepted = experiment / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v1"
        self.assertEqual(verify_candidate(candidate)["status"], "candidate")
        verified = verify_accepted_bundle(accepted)
        self.assertEqual(verified["status"], "accepted")
        manifest = json.loads((accepted / "snapshot-manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(manifest["downstream_eligible"])
        self.assertTrue(manifest["offline_replay_proven"])
        self.assertFalse(manifest["external_publication_authorized"])

    def test_phase2_authority_requires_the_accepted_registry_digest(self) -> None:
        experiment = Path(__file__).resolve().parents[1]
        accepted = experiment / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"
        command = [
            sys.executable, "-m", "specchoice_evidence.cli", "validate-phase2-source-authority",
            "--authority", "phase2/source-authority.json", "--bundle", str(accepted),
        ]
        result = subprocess.run(command, cwd=experiment, check=False, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        authority = json.loads((experiment / "phase2/source-authority.json").read_text(encoding="utf-8"))
        authority["registry_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            invalid = Path(directory) / "source-authority.json"
            invalid.write_text(json.dumps(authority, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
            command[command.index("phase2/source-authority.json")] = str(invalid)
            result = subprocess.run(command, cwd=experiment, check=False, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
