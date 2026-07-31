# SPDX-License-Identifier: BSD-3-Clause-Clear
"""End-to-end and fail-closed tests for the frozen PR #2164 adapter."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from specchoice_evidence.canonical import sha256_bytes
from specchoice_measurement.adapter import build_pr2164_adapter_batch, validate_complete_adapter_batch


class MeasurementAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.experiment_root = Path(__file__).parents[1]
        self.authority = self.experiment_root / "phase2/source-authority.json"
        self.bundle = (
            self.experiment_root
            / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"
        )
        self.rules = self.experiment_root / "config/measurement/pr2164-adapter-rules-v1.json"

    def build(self):
        return build_pr2164_adapter_batch(
            authority_path=self.authority,
            bundle_root=self.bundle,
            rules_path=self.rules,
        )

    def test_accepted_v2_builds_the_complete_canonical_partition(self) -> None:
        batch = self.build()

        self.assertTrue(batch.valid)
        self.assertEqual(len(batch.records), 11)
        self.assertEqual(len({record.fixture_id for record in batch.records}), 11)
        self.assertEqual(sum(len(record.raw_files) for record in batch.records), 28)
        self.assertEqual(
            [record.fixture_id for record in batch.records],
            sorted(record.fixture_id for record in batch.records),
        )
        self.assertEqual(
            {category: sum(record.category == category for record in batch.records)
             for category in ("positive", "negative", "candidate")},
            {"positive": 6, "negative": 4, "candidate": 1},
        )
        candidate = next(record for record in batch.records if record.category == "candidate")
        self.assertTrue(candidate.expect_extract)
        self.assertEqual(candidate.expected_parameter_count, 0)
        self.assertEqual(candidate.expected_parameter_names, ())
        self.assertEqual(batch.diagnostics, ())
        self.assertEqual(batch.adapter_version, "pr2164-adapter-v1")
        self.assertEqual(len(batch.rule_sha256), 64)
        self.assertEqual(len(batch.adapter_batch_sha256), 64)

    def test_cli_writes_identical_new_canonical_batches(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first.json"
            second = root / "second.json"
            command = [
                "python3", "-m", "specchoice_measurement.cli", "adapt-pr2164",
                "--authority", self.authority.as_posix(),
                "--bundle", self.bundle.as_posix(),
                "--rules", self.rules.as_posix(),
            ]
            subprocess.run([*command, "--output", first.as_posix()], check=True, cwd=self.experiment_root)
            subprocess.run([*command, "--output", second.as_posix()], check=True, cwd=self.experiment_root)

            self.assertEqual(first.read_bytes(), second.read_bytes())
            emitted = json.loads(first.read_text(encoding="utf-8"))
            self.assertEqual(emitted["adapter_batch_sha256"], self.build().adapter_batch_sha256)

    def test_incomplete_duplicate_reordered_and_mixed_batches_have_all_blockers_and_no_records(self) -> None:
        valid = self.build()
        expected_ids = tuple(record.fixture_id for record in valid.records)
        duplicate = valid.records[0]
        mixed_version = replace(valid.records[1], adapter_version="pr2164-adapter-v2")
        invalid = validate_complete_adapter_batch(
            records=(valid.records[1], duplicate, duplicate, mixed_version),
            expected_fixture_ids=expected_ids,
            expected_raw_file_count=28,
            adapter_version=valid.adapter_version,
            rule_sha256=valid.rule_sha256,
            source_identity=valid.source_identity,
        )

        self.assertFalse(invalid.valid)
        self.assertEqual(invalid.records, ())
        self.assertEqual(
            [item.code for item in invalid.diagnostics],
            sorted([item.code for item in invalid.diagnostics]),
        )
        self.assertTrue({"ADAPTER_FIXTURE_DUPLICATE", "ADAPTER_FIXTURE_SET_MISMATCH", "ADAPTER_ORDER_NONCANONICAL", "ADAPTER_VERSION_MIXED"}.issubset({item.code for item in invalid.diagnostics}))

    def test_candidate_or_historical_source_is_rejected_without_records(self) -> None:
        candidate = self.experiment_root / "bundles/candidates/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v1"
        rejected = build_pr2164_adapter_batch(
            authority_path=self.authority,
            bundle_root=candidate,
            rules_path=self.rules,
        )

        self.assertFalse(rejected.valid)
        self.assertEqual(rejected.records, ())
        self.assertEqual(rejected.diagnostics[0].code, "PHASE2_SOURCE_AUTHORITY_INVALID")


if __name__ == "__main__":
    unittest.main()
