# SPDX-License-Identifier: BSD-3-Clause-Clear
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from specchoice_evidence.canonical import canonical_json_bytes, sha256_bytes
from specchoice_evidence.environment import (
    EnvironmentObservation,
    build_default_decision,
    build_environment_decision,
    write_environment_artifacts,
)


class EnvironmentDecisionTests(unittest.TestCase):
    def test_equivalent_stable_observations_have_identical_canonical_bytes(self) -> None:
        observation = EnvironmentObservation(
            python_implementation="CPython",
            python_version="3.14.0",
            git_implementation="git",
            git_version="2.50.1",
        )
        first = canonical_json_bytes(build_environment_decision(observation))
        second = canonical_json_bytes(build_environment_decision(observation))
        self.assertEqual(first, second)
        self.assertEqual(sha256_bytes(first), sha256_bytes(second))
        self.assertNotIn(b"hostname", first)
        self.assertNotIn(b"working_directory", first)
        self.assertNotIn(b"command", first)

    def test_default_decision_selects_standalone_first_without_udb_probe(self) -> None:
        decision = build_default_decision(
            EnvironmentObservation(
                python_implementation="CPython",
                python_version="3.14.0",
                git_implementation="git",
                git_version="2.50.1",
            )
        )
        self.assertEqual(decision["route"], "standalone_first")
        self.assertEqual(decision["outcome"], "success")
        self.assertFalse(decision["fallback_triggered"])
        self.assertEqual(decision["fallback_ceiling_status"], "not_started")
        self.assertEqual(decision["full_udb_setup"], {"attempted": False, "required": False})
        self.assertEqual(decision["incident"], {"error_codes": [], "outcome": "not_triggered", "triggered": False})
        self.assertEqual(
            decision["capabilities"]["construction"],
            ["git_cli_for_construction", "python_standard_library"],
        )
        self.assertEqual(
            decision["capabilities"]["downstream"],
            ["offline_bundle_access", "python_standard_library"],
        )

    def test_audit_receipt_has_one_way_canonical_digest_reference(self) -> None:
        observation = EnvironmentObservation(
            python_implementation="CPython",
            python_version="3.14.0",
            git_implementation="git",
            git_version="2.50.1",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            decision_path = root / "environment-decision.json"
            audit_path = root / "environment-receipt.json"
            digest = write_environment_artifacts(
                decision_path,
                audit_path,
                observation,
                audit_metadata={
                    "command": "python3 -m specchoice_evidence.cli record-environment --token secret",
                    "hostname": "build-host",
                    "timestamp": "2026-07-30T14:30:00Z",
                    "working_directory": "/private/tmp/specchoice",
                },
            )
            decision_bytes = decision_path.read_bytes()
            receipt_bytes = audit_path.read_bytes()
            receipt = json.loads(receipt_bytes.decode("utf-8"))
        self.assertEqual(digest, sha256_bytes(decision_bytes))
        self.assertEqual(receipt["canonical_environment_decision_sha256"], digest)
        self.assertNotIn("audit", json.loads(decision_bytes.decode("utf-8")))
        self.assertNotIn(b"build-host", decision_bytes)
        self.assertNotIn(b"secret", receipt_bytes)

    def test_audit_only_metadata_cannot_change_canonical_decision_bytes(self) -> None:
        observation = EnvironmentObservation(
            python_implementation="CPython",
            python_version="3.14.0",
            git_implementation="git",
            git_version="2.50.1",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first_decision = root / "first-decision.json"
            second_decision = root / "second-decision.json"
            first_digest = write_environment_artifacts(
                first_decision,
                root / "first-audit.json",
                observation,
                audit_metadata={"hostname": "first-host", "timestamp": "2026-07-30T00:00:00Z"},
            )
            second_digest = write_environment_artifacts(
                second_decision,
                root / "second-audit.json",
                observation,
                audit_metadata={"hostname": "second-host", "timestamp": "2026-07-31T00:00:00Z"},
            )
            self.assertEqual(first_decision.read_bytes(), second_decision.read_bytes())
        self.assertEqual(first_digest, second_digest)


if __name__ == "__main__":
    unittest.main()
