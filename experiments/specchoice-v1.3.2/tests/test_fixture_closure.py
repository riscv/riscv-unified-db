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
from specchoice_evidence.filesystem import FilesystemPolicyError, read_authoritative_file
from specchoice_evidence.cli import _v4_predecessor_material
from specchoice_evidence.verify import _bundle_artifacts, _raw_artifacts, _root_digest, verify_accepted_bundle
from specchoice_evidence.source_contract import (
    _v4_inventory,
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

    def _assert_canonical_revocation_absent(self, authority_root: Path) -> None:
        with self.assertRaisesRegex(FilesystemPolicyError, "AUTHORITATIVE_FILE_MISSING"):
            read_authoritative_file(authority_root / "receipts", "fixture-closure-revocation-v2.json")

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
        historical_v2 = experiment / "phase2/source-authority-v9-historical.json"
        audit = experiment / "receipts/fixture-closure-candidate-audit-v3.json"
        construction = experiment / "receipts/source-contract-decision-v3-pr2164-fixture-closure-verifier-rooted-v3.json"
        proposal = experiment / "receipts/source-contract-proposal-v3-pr2164-fixture-closure-verifier-rooted-v3.json"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            authority_root = root / "authority-root"
            active_v2 = authority_root / "phase2/source-authority.json"
            active_v2.parent.mkdir(parents=True)
            (authority_root / "receipts").mkdir()
            shutil.copyfile(historical_v2, active_v2)
            self._assert_canonical_revocation_absent(authority_root)
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
            self.assertEqual(
                self._public_command(
                    experiment,
                    "validate-local-acceptance-decision-v10", "--request", str(request),
                    "--decision", str(decision_path),
                ),
                {
                    "decision": "accept",
                    "request_sha256": sha256_bytes(request.read_bytes()),
                    "status": "local_acceptance_decision_valid",
                },
            )
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
            readiness = experiment / "receipts/source-cutover-readiness-v10.json"
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
            self.assertEqual(
                self._public_command(
                    experiment,
                    "validate-pending-source-cutover-v10", "--pending-authority", str(pending),
                    "--transition", str(transition), "--active-authority", str(active),
                    "--accepted-bundle", str(accepted_bundle),
                )["status"],
                "pending_cutover_valid_non_effective",
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
            self._assert_canonical_revocation_absent(authority_root)
            for bundle, expected in (
                (root / "missing-bundle", ""),
                (experiment / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2", ""),
            ):
                with self.subTest(bundle=bundle):
                    result = subprocess.run(
                        [
                            sys.executable, "-m", "specchoice_evidence.cli", "activate-pending-source-cutover-v10",
                            "--pending-authority", str(pending), "--transition", str(transition),
                            "--readiness", str(readiness),
                            "--canonical-revocation", str(revocation), "--active-authority", str(active),
                            "--accepted-bundle", str(bundle),
                        ], cwd=experiment, check=False, capture_output=True, text=True,
                    )
                    self.assertNotEqual(result.returncode, 0, expected)
                    self.assertFalse(revocation.exists())
                    self.assertEqual(active.read_bytes(), active_v2.read_bytes())
            # The public activator only accepts the single reviewed readiness
            # binding; its source inputs must therefore be the canonical pending
            # objects, even though the mutation targets remain disposable.
            pending = experiment / "phase2/source-authority-v10-pending.json"
            transition = experiment / "receipts/pending/fixture-closure-transition-v2-to-v3.json"
            accepted_bundle = experiment / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v3"
            shutil.copyfile(active_v2, active)
            self._public_command(
                experiment,
                "activate-pending-source-cutover-v10", "--pending-authority", str(pending), "--transition", str(transition),
                "--readiness", str(readiness),
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
                    "--readiness", str(readiness),
                    "--canonical-revocation", str(revocation), "--active-authority", str(active), "--accepted-bundle", str(accepted_bundle),
                )["status"],
                "already_activated",
            )
            complete_revocation = revocation.read_bytes()
            complete_active = active.read_bytes()
            alternative_pending_payload = json.loads(pending.read_text(encoding="utf-8"))
            alternative_pending_payload["decision_sha256"] = "0" * 64
            alternative_transition_payload = json.loads(transition.read_text(encoding="utf-8"))
            alternative_transition_payload["decision_sha256"] = "0" * 64
            alternative_projection = dict(alternative_pending_payload)
            alternative_projection.pop("transition_sha256")
            alternative_transition_payload["new_authority_projection_sha256"] = sha256_bytes(
                canonical_json_bytes(alternative_projection)
            )
            alternative_transition = root / "self-consistent-transition.json"
            alternative_transition.write_bytes(canonical_json_bytes(alternative_transition_payload))
            alternative_pending_payload["transition_sha256"] = sha256_bytes(alternative_transition.read_bytes())
            alternative_pending = root / "self-consistent-pending.json"
            alternative_pending.write_bytes(canonical_json_bytes(alternative_pending_payload))
            malformed_readiness = root / "malformed-readiness.json"
            malformed_readiness.write_bytes(canonical_json_bytes({"schema_version": "10"}))
            malformed_transition = root / "malformed-complete-transition.json"
            malformed_transition.write_bytes(canonical_json_bytes({"schema_version": "2"}))
            for supplied_readiness, supplied_pending, supplied_transition in (
                (root / "missing-readiness.json", pending, transition),
                (malformed_readiness, pending, transition),
                (readiness, alternative_pending, alternative_transition),
                (readiness, pending, malformed_transition),
            ):
                with self.subTest(readiness=supplied_readiness.name, pending=supplied_pending.name):
                    result = subprocess.run(
                        [
                            sys.executable, "-m", "specchoice_evidence.cli", "activate-pending-source-cutover-v10",
                            "--pending-authority", str(supplied_pending), "--transition", str(supplied_transition),
                            "--readiness", str(supplied_readiness), "--canonical-revocation", str(revocation),
                            "--active-authority", str(active), "--accepted-bundle", str(accepted_bundle),
                        ], cwd=experiment, check=False, capture_output=True, text=True,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(revocation.read_bytes(), complete_revocation)
                    self.assertEqual(active.read_bytes(), complete_active)
            before = active.read_bytes()
            invalid_pending = root / "invalid-pending.json"
            invalid_pending.write_bytes(canonical_json_bytes({"schema_version": "10"}))
            with self.assertRaisesRegex(AssertionError, "SOURCE_CUTOVER"):
                self._public_command(
                    experiment,
                    "activate-pending-source-cutover-v10", "--pending-authority", str(invalid_pending),
                    "--readiness", str(readiness),
                    "--transition", str(transition), "--canonical-revocation", str(revocation),
                    "--active-authority", str(active), "--accepted-bundle", str(accepted_bundle),
                )
            self.assertEqual(active.read_bytes(), before)

            # Revocation may be durable while the authority replacement has not
            # happened; the public owner resumes only from exact held bytes.
            resume = root / "resume"
            resume.mkdir()
            resume_active = resume / "source-authority.json"
            resume_revocation = resume / "fixture-closure-revocation-v2.json"
            shutil.copyfile(active_v2, resume_active)
            resume_revocation.write_bytes(transition.read_bytes())
            self.assertEqual(
                self._public_command(
                    experiment,
                    "activate-pending-source-cutover-v10", "--pending-authority", str(pending),
                    "--readiness", str(readiness),
                    "--transition", str(transition), "--canonical-revocation", str(resume_revocation),
                    "--active-authority", str(resume_active), "--accepted-bundle", str(accepted_bundle),
                )["status"],
                "activated",
            )
            self.assertEqual(resume_active.read_bytes(), pending.read_bytes())

            for mutation in (
                lambda path: path.write_bytes(canonical_json_bytes({"schema_version": "2"})),
                lambda path: path.write_bytes(canonical_json_bytes({**json.loads(transition.read_text(encoding="utf-8")), "old_authority_sha256": "0" * 64})),
            ):
                with self.subTest(transition_mutation=mutation):
                    invalid_transition = root / "invalid-transition.json"
                    mutation(invalid_transition)
                    before_revocation = revocation.read_bytes()
                    before_active = active.read_bytes()
                    with self.assertRaisesRegex(AssertionError, "SOURCE_CUTOVER"):
                        self._public_command(
                            experiment, "activate-pending-source-cutover-v10", "--pending-authority", str(pending),
                            "--readiness", str(readiness),
                            "--transition", str(invalid_transition), "--canonical-revocation", str(revocation),
                            "--active-authority", str(active), "--accepted-bundle", str(accepted_bundle),
                        )
                    self.assertEqual(revocation.read_bytes(), before_revocation)
                    self.assertEqual(active.read_bytes(), before_active)

            with self.assertRaisesRegex(AssertionError, "SOURCE_CUTOVER"):
                self._public_command(
                    experiment, "activate-pending-source-cutover-v10", "--pending-authority", str(pending),
                    "--readiness", str(readiness),
                    "--transition", str(transition), "--canonical-revocation", str(revocation),
                    "--active-authority", str(active),
                    "--accepted-bundle", str(experiment / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"),
                )

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

    def test_v3_acceptance_receipts_and_copied_replay_bind_same_identity(self) -> None:
        """Public receipt writers bind accepted v3 without activating the pending cutover."""
        experiment = Path(__file__).resolve().parents[1]
        accepted = experiment / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v3"
        historical_v2 = experiment / "phase2/source-authority-v9-historical.json"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            active = root / "authority-root/phase2/source-authority.json"
            active.parent.mkdir(parents=True)
            (root / "authority-root/receipts").mkdir()
            shutil.copyfile(historical_v2, active)
            self._assert_canonical_revocation_absent(root / "authority-root")
            before = active.read_bytes()
            result = self._public_command(
                experiment,
                "write-accepted-v3-receipts",
                "--request", str(experiment / "receipts/local-acceptance-request-v10.json"),
                "--decision", str(experiment / "receipts/local-acceptance-v10.json"),
                "--candidate-audit", str(experiment / "receipts/fixture-closure-candidate-audit-v3.json"),
                "--pending-authority", str(experiment / "phase2/source-authority-v10-pending.json"),
                "--transition", str(experiment / "receipts/pending/fixture-closure-transition-v2-to-v3.json"),
                "--active-authority", str(active),
                "--historical-authority", str(active),
                "--accepted-bundle", str(accepted),
                "--receipt-directory", str(root),
            )
            self.assertEqual(result["status"], "accepted_v3_receipts_written")
            self.assertEqual(result["written"], [
                "fixture-closure-acceptance-audit-v3.json",
                "fixture-closure-acceptance-audit-v3.md",
                "fixture-closure-offline-replay-v3.json",
                "integrity-receipt-v10.json",
                "integrity-receipt-v10.md",
            ])
            audit = json.loads((root / "fixture-closure-acceptance-audit-v3.json").read_text(encoding="utf-8"))
            integrity = json.loads((root / "integrity-receipt-v10.json").read_text(encoding="utf-8"))
            replay = json.loads((root / "fixture-closure-offline-replay-v3.json").read_text(encoding="utf-8"))
            for path in (
                root / "fixture-closure-acceptance-audit-v3.json",
                root / "integrity-receipt-v10.json",
                root / "fixture-closure-offline-replay-v3.json",
            ):
                self.assertEqual(path.read_bytes(), canonical_json_bytes(json.loads(path.read_text(encoding="utf-8"))))
            self.assertEqual(audit["accepted_identity"], integrity["accepted_identity"])
            self.assertEqual(audit["accepted_identity"], replay["accepted_identity"])
            self.assertEqual(audit["local_only"], True)
            self.assertEqual(audit["external_publication_authorized"], False)
            self.assertEqual(len(audit["verifier_artifacts"]), 5)
            self.assertEqual(replay["copied_isolation_replay"], {
                "git_available": False,
                "network_available": False,
                "original_bundle_available": False,
                "repository_modules_available": False,
                "result": "passed",
            })
            self.assertEqual(active.read_bytes(), before)
            self._assert_canonical_revocation_absent(root / "authority-root")

    def test_source_authority_and_bundle_consumers_reuse_descriptor_bound_canonical_bytes(self) -> None:
        """The public authority receipt is assembled from descriptor-read bundle leaves."""
        experiment = Path(__file__).resolve().parents[1]
        accepted = experiment / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v3"
        command = [
            sys.executable, "-m", "specchoice_evidence.cli", "validate-phase2-source-authority",
            "--authority", "phase2/source-authority.json", "--bundle", str(accepted),
            "--revocation", "receipts/fixture-closure-revocation-v2.json", "--authority-mode", "active",
        ]
        result = subprocess.run(command, cwd=experiment, check=False, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertEqual(result.stdout, canonical_json_bytes(json.loads(result.stdout.decode("utf-8"))))
        receipt = json.loads(result.stdout.decode("utf-8"))
        self.assertEqual(receipt["status"], "valid")
        self.assertEqual(set(receipt), {
            "eligible", "fixture_count", "generation", "manifest_sha256", "pinned_commit_sha",
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

        with self.subTest("semantic_gold_v4_proposal_is_closed_over_repairs_and_registry"):
            proposal_v4 = experiment / "receipts/source-contract-proposal-v4-pr2164-semantic-gold-closure-verifier-rooted-v2.json"
            repair_manifest = experiment / "config/fixture-repairs/pr2164-semantic-gold-v2/repair-manifest.json"
            registry_v2 = experiment / "config/fixture-registry-pr2164-v3.json"
            supersession = experiment / "receipts/source-contract-construction-proposal-v4-supersession-v1.json"
            predecessor_v3 = experiment / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v3"
            result = subprocess.run(
                [
                    sys.executable, "-m", "specchoice_evidence.cli", "validate-fixture-construction-proposal-v4",
                    "--proposal", str(proposal_v4),
                    "--predecessor", str(predecessor_v3),
                    "--active-authority", str(experiment / "phase2/source-authority.json"),
                    "--historical-authority", str(experiment / "phase2/source-authority-v9-historical.json"),
                    "--revocation", str(experiment / "receipts/fixture-closure-revocation-v2.json"),
                    "--ontology-decision", str(experiment / "reviews/h1-source-gold-ontology-decision-v1.json"),
                    "--repair-manifest", str(repair_manifest), "--registry", str(registry_v2),
                    "--supersession", str(supersession),
                ],
                cwd=experiment,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            proposal_payload = json.loads(proposal_v4.read_text(encoding="utf-8"))
            supersession_payload = json.loads(supersession.read_text(encoding="utf-8"))
            self.assertEqual(proposal_payload["status"], "awaiting_human_construction_authorization")
            self.assertEqual(proposal_payload["selected_policy"]["pbmte"], "surfaced_classified_out")
            self.assertEqual(proposal_payload["selected_policy"]["cache"], "unified_cache_block_identity")

            cache_gold = (experiment / "config/fixture-repairs/pr2164-semantic-gold-v2/POS_DIRECT_CACHE_BLOCK/gold.yaml").read_text(encoding="utf-8")
            pmp_gold = (experiment / "config/fixture-repairs/pr2164-semantic-gold-v2/POS_DIRECT_NUM_PMP/gold.yaml").read_text(encoding="utf-8")
            geilen_expected = (experiment / "config/fixture-repairs/pr2164-semantic-gold-v2/POS_RECALL_COUNT_GEILEN/expected.yaml").read_text(encoding="utf-8")
            asid_gold = (experiment / "config/fixture-repairs/pr2164-semantic-gold-v2/POS_WARL_ASID_WIDTH/gold.yaml").read_text(encoding="utf-8")
            asid_expected = (experiment / "config/fixture-repairs/pr2164-semantic-gold-v2/POS_WARL_ASID_WIDTH/expected.yaml").read_text(encoding="utf-8")
            self.assertIn("enum:", cache_gold)
            self.assertIn("0x4", cache_gold)
            self.assertNotIn("uniform throughout", cache_gold)
            self.assertIn("- 0", pmp_gold)
            self.assertIn("- 16", pmp_gold)
            self.assertIn("- 64", pmp_gold)
            self.assertIn("existing_alias", geilen_expected)
            self.assertIn("gold_name: GEILEN", geilen_expected)
            self.assertIn("NUM_EXTERNAL_GUEST_INTERRUPTS", geilen_expected)
            self.assertNotIn("versioned_aliases", asid_gold)
            self.assertIn("versioned_aliases", asid_expected)
            legacy_proposal = experiment / "receipts/source-contract-proposal-v4-pr2164-semantic-gold-closure-verifier-rooted-v1.json"
            legacy_manifest = experiment / "config/fixture-repairs/pr2164-semantic-gold-v1/repair-manifest.json"
            legacy_registry = experiment / "config/fixture-registry-pr2164-v2.json"
            self.assertEqual(supersession_payload["legacy"]["proposal"]["sha256"], sha256_bytes(legacy_proposal.read_bytes()))
            self.assertEqual(supersession_payload["legacy"]["repair_manifest"]["sha256"], sha256_bytes(legacy_manifest.read_bytes()))
            self.assertEqual(supersession_payload["legacy"]["registry"]["sha256"], sha256_bytes(legacy_registry.read_bytes()))
            self.assertNotEqual(legacy_manifest.read_bytes(), repair_manifest.read_bytes())

            def run_v4(*, proposal_path: Path = proposal_v4, manifest_path: Path = repair_manifest, registry_path: Path = registry_v2, supersession_path: Path = supersession, decision_path: Path = experiment / "reviews/h1-source-gold-ontology-decision-v1.json") -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [
                        sys.executable, "-m", "specchoice_evidence.cli", "validate-fixture-construction-proposal-v4",
                        "--proposal", str(proposal_path), "--predecessor", str(predecessor_v3),
                        "--active-authority", str(experiment / "phase2/source-authority.json"),
                        "--historical-authority", str(experiment / "phase2/source-authority-v9-historical.json"),
                        "--revocation", str(experiment / "receipts/fixture-closure-revocation-v2.json"),
                        "--ontology-decision", str(decision_path), "--repair-manifest", str(manifest_path),
                        "--registry", str(registry_path), "--supersession", str(supersession_path),
                    ], cwd=experiment, check=False, capture_output=True, text=True,
                )

            with tempfile.TemporaryDirectory() as directory:
                temporary = Path(directory)
                original_proposal = json.loads(proposal_v4.read_text(encoding="utf-8"))
                original_manifest = json.loads(repair_manifest.read_text(encoding="utf-8"))
                original_registry = json.loads(registry_v2.read_text(encoding="utf-8"))
                original_supersession = json.loads(supersession.read_text(encoding="utf-8"))

                def write_payload(name: str, value: object) -> Path:
                    path = temporary / name
                    path.write_bytes(canonical_json_bytes(value))
                    return path

                with self.subTest("v4_rejects_forged_old_hash_and_length"):
                    forged_manifest = copy.deepcopy(original_manifest)
                    forged_manifest["repairs"][0]["old_sha256"] = "0" * 64
                    forged_manifest["repairs"][0]["old_byte_length"] = 0
                    forged_manifest_path = write_payload("forged-manifest.json", forged_manifest)
                    forged_proposal = copy.deepcopy(original_proposal)
                    forged_proposal["repair_manifest"]["sha256"] = sha256_bytes(forged_manifest_path.read_bytes())
                    forged_proposal["replacements"] = forged_manifest["repairs"]
                    self.assertNotEqual(run_v4(proposal_path=write_payload("forged-proposal.json", forged_proposal), manifest_path=forged_manifest_path).returncode, 0)

                with self.subTest("v4_rejects_mislabeled_replace_and_swapped_payload_control"):
                    forged_manifest = copy.deepcopy(original_manifest)
                    replacement = next(item for item in forged_manifest["repairs"] if item["kind"] == "replace")
                    replacement["kind"] = "add"
                    replacement["old_sha256"] = None
                    replacement["old_byte_length"] = None
                    forged_manifest_path = write_payload("mislabeled-manifest.json", forged_manifest)
                    forged_proposal = copy.deepcopy(original_proposal)
                    forged_proposal["repair_manifest"]["sha256"] = sha256_bytes(forged_manifest_path.read_bytes())
                    forged_proposal["replacements"] = forged_manifest["repairs"]
                    self.assertNotEqual(run_v4(proposal_path=write_payload("mislabeled-proposal.json", forged_proposal), manifest_path=forged_manifest_path).returncode, 0)

                    forged_manifest = copy.deepcopy(original_manifest)
                    first, second = forged_manifest["repairs"][:2]
                    first["payload_path"], second["payload_path"] = second["payload_path"], first["payload_path"]
                    first["control"] = "semantic_correction"
                    forged_manifest_path = write_payload("swapped-manifest.json", forged_manifest)
                    forged_proposal = copy.deepcopy(original_proposal)
                    forged_proposal["repair_manifest"]["sha256"] = sha256_bytes(forged_manifest_path.read_bytes())
                    forged_proposal["replacements"] = forged_manifest["repairs"]
                    self.assertNotEqual(run_v4(proposal_path=write_payload("swapped-proposal.json", forged_proposal), manifest_path=forged_manifest_path).returncode, 0)

                with self.subTest("v4_rejects_forged_registry_predecessor_and_reused_leaf"):
                    forged_registry = copy.deepcopy(original_registry)
                    forged_registry["predecessor_registry_sha256"] = "0" * 64
                    forged_registry["fixtures"][0]["files"][0]["role"] = "fixture_gold"
                    forged_registry_path = write_payload("forged-registry.json", forged_registry)
                    forged_proposal = copy.deepcopy(original_proposal)
                    forged_proposal["registry"]["sha256"] = sha256_bytes(forged_registry_path.read_bytes())
                    self.assertNotEqual(run_v4(proposal_path=write_payload("registry-proposal.json", forged_proposal), registry_path=forged_registry_path).returncode, 0)

                with self.subTest("v4_rejects_registry_repair_claimed_as_predecessor"):
                    forged_registry = copy.deepcopy(original_registry)
                    repaired = next(
                        file for fixture in forged_registry["fixtures"] for file in fixture["files"]
                        if file["path"] == "raw/evaluation_fixtures/CAND_WARL_FIXED_LEGAL_SET/expected.yaml"
                    )
                    repaired["origin"] = "predecessor"
                    forged_registry_path = write_payload("origin-registry.json", forged_registry)
                    forged_proposal = copy.deepcopy(original_proposal)
                    forged_proposal["registry"]["sha256"] = sha256_bytes(forged_registry_path.read_bytes())
                    self.assertNotEqual(run_v4(proposal_path=write_payload("origin-proposal.json", forged_proposal), registry_path=forged_registry_path).returncode, 0)

                with self.subTest("v4_rejects_opposite_valid_human_selection"):
                    opposite = json.loads((experiment / "reviews/h1-source-gold-ontology-decision-v1.json").read_text(encoding="utf-8"))
                    opposite["pbmte_policy"]["selection"] = "excluded_from_discovery"
                    opposite.pop("decision_sha256")
                    opposite["decision_sha256"] = sha256_bytes(canonical_json_bytes(opposite))
                    opposite_path = write_payload("opposite-decision.json", opposite)
                    self.assertNotEqual(run_v4(decision_path=opposite_path).returncode, 0)

                with self.subTest("v4_rejects_rebound_opposite_policy_when_payload_consequences_remain_v2"):
                    opposite = json.loads((experiment / "reviews/h1-source-gold-ontology-decision-v1.json").read_text(encoding="utf-8"))
                    opposite["pbmte_policy"]["selection"] = "excluded_from_discovery"
                    opposite.pop("decision_sha256")
                    opposite["decision_sha256"] = sha256_bytes(canonical_json_bytes(opposite))
                    opposite_path = write_payload("rebound-opposite-decision.json", opposite)
                    forged_manifest = copy.deepcopy(original_manifest)
                    forged_manifest["ontology_decision_sha256"] = sha256_bytes(opposite_path.read_bytes())
                    forged_manifest["repairs"] = [
                        repair for repair in forged_manifest["repairs"]
                        if "NEG_EXT_GATED_PBMTE" not in repair["target_path"]
                    ]
                    forged_manifest_path = write_payload("rebound-manifest.json", forged_manifest)
                    forged_registry = copy.deepcopy(original_registry)
                    forged_registry["ontology_decision_sha256"] = sha256_bytes(opposite_path.read_bytes())
                    forged_registry["fixtures"] = [
                        fixture for fixture in forged_registry["fixtures"]
                        if fixture["fixture_id"] != "NEG_EXT_GATED_PBMTE"
                    ]
                    forged_registry["fixture_count"] = 10
                    forged_registry["raw_file_count"] = 26
                    forged_registry_path = write_payload("rebound-registry.json", forged_registry)
                    forged_proposal = copy.deepcopy(original_proposal)
                    forged_proposal["ontology_decision"]["sha256"] = sha256_bytes(opposite_path.read_bytes())
                    forged_proposal["repair_manifest"]["sha256"] = sha256_bytes(forged_manifest_path.read_bytes())
                    forged_proposal["registry"]["sha256"] = sha256_bytes(forged_registry_path.read_bytes())
                    forged_proposal["replacements"] = forged_manifest["repairs"]
                    forged_proposal["selected_policy"]["pbmte"] = "excluded_from_discovery"
                    forged_proposal["successor_inventory"] = {
                        "fixture_count": 10,
                        "partition": {"candidate": 1, "negative": 3, "positive": 6},
                        "raw_file_count": 26,
                    }
                    forged_proposal_path = write_payload("rebound-proposal.json", forged_proposal)
                    forged_supersession = copy.deepcopy(original_supersession)
                    forged_supersession["successor"]["proposal"]["sha256"] = sha256_bytes(forged_proposal_path.read_bytes())
                    forged_supersession["successor"]["repair_manifest"]["sha256"] = sha256_bytes(forged_manifest_path.read_bytes())
                    forged_supersession["successor"]["registry"]["sha256"] = sha256_bytes(forged_registry_path.read_bytes())
                    forged_supersession_path = write_payload("rebound-supersession.json", forged_supersession)
                    predecessor_material = _v4_predecessor_material(predecessor_v3)
                    self.assertEqual(
                        _v4_inventory(
                            predecessor_material["files"], predecessor_material["classes"],
                            "excluded_from_discovery", forged_manifest,
                        ),
                        forged_proposal["successor_inventory"],
                    )
                    self.assertEqual(
                        run_v4(
                            proposal_path=forged_proposal_path, manifest_path=forged_manifest_path,
                            registry_path=forged_registry_path, supersession_path=forged_supersession_path,
                            decision_path=opposite_path,
                        ).returncode,
                        0,
                    )
                    retained_registry = copy.deepcopy(original_registry)
                    retained_registry["ontology_decision_sha256"] = sha256_bytes(opposite_path.read_bytes())
                    retained_registry_path = write_payload("retained-pbmte-registry.json", retained_registry)
                    retained_proposal = copy.deepcopy(forged_proposal)
                    retained_proposal["registry"]["sha256"] = sha256_bytes(retained_registry_path.read_bytes())
                    retained_proposal_path = write_payload("retained-pbmte-proposal.json", retained_proposal)
                    retained_supersession = copy.deepcopy(forged_supersession)
                    retained_supersession["successor"]["proposal"]["sha256"] = sha256_bytes(retained_proposal_path.read_bytes())
                    retained_supersession["successor"]["registry"]["sha256"] = sha256_bytes(retained_registry_path.read_bytes())
                    retained_supersession_path = write_payload("retained-pbmte-supersession.json", retained_supersession)
                    self.assertNotEqual(
                        run_v4(
                            proposal_path=retained_proposal_path, manifest_path=forged_manifest_path,
                            registry_path=retained_registry_path, supersession_path=retained_supersession_path,
                            decision_path=opposite_path,
                        ).returncode,
                        0,
                    )

                with self.subTest("v4_rejects_nonexistent_code_commit"):
                    forged_proposal = copy.deepcopy(original_proposal)
                    forged_proposal["fixed_code_commit"] = "0" * 40
                    self.assertNotEqual(run_v4(proposal_path=write_payload("zero-commit.json", forged_proposal)).returncode, 0)

                with self.subTest("v4_rejects_noncanonical_duplicate_and_symlink_inputs"):
                    noncanonical = temporary / "noncanonical-proposal.json"
                    noncanonical.write_text(json.dumps(original_proposal, indent=2), encoding="utf-8")
                    self.assertNotEqual(run_v4(proposal_path=noncanonical).returncode, 0)
                    duplicate = temporary / "duplicate-proposal.json"
                    duplicate.write_bytes(b'{"schema_version":"fixture-construction-proposal-v4","schema_version":"fixture-construction-proposal-v4"}')
                    self.assertNotEqual(run_v4(proposal_path=duplicate).returncode, 0)
                    symlink = temporary / "proposal-link.json"
                    symlink.symlink_to(proposal_v4)
                    self.assertNotEqual(run_v4(proposal_path=symlink).returncode, 0)

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
        accepted = experiment / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v3"
        command = [
            sys.executable, "-m", "specchoice_evidence.cli", "validate-phase2-source-authority",
            "--authority", "phase2/source-authority.json", "--bundle", str(accepted),
            "--revocation", "receipts/fixture-closure-revocation-v2.json", "--authority-mode", "active",
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
