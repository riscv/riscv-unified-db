# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Exact-set guards for the frozen PR #2164 fixture custody input."""

from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from specchoice_evidence.bundle import BundleError, verify_candidate
from specchoice_evidence.source_contract import (
    FixtureRegistryError,
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
    def test_complete_candidate_is_ineligible_and_rejects_extra_or_missing_files(self) -> None:
        experiment = Path(__file__).resolve().parents[1]
        candidate = experiment / (
            "bundles/candidates/source-contract-v3-pr2164-fixture-closure-"
            "22e84458-verifier-rooted-v1"
        )
        identity = verify_candidate(candidate)
        self.assertEqual(identity["status"], "candidate")
        manifest = json.loads((candidate / "snapshot-manifest.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["downstream_eligible"])
        self.assertFalse(manifest["external_publication_authorized"])
        self.assertEqual(
            sum(len(snapshot["consumed_files"]) for snapshot in manifest["snapshots"]), 28
        )

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


if __name__ == "__main__":
    unittest.main()
