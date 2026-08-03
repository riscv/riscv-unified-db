# SPDX-License-Identifier: BSD-3-Clause-Clear
"""End-to-end and fail-closed tests for the frozen PR #2164 adapter."""

from __future__ import annotations

import json
import os
import subprocess
import shutil
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from specchoice_evidence.canonical import canonical_json_bytes, sha256_bytes
from specchoice_evidence import filesystem
from specchoice_evidence.filesystem import FilesystemPolicyError, read_authoritative_file
from specchoice_evidence.verify import verify_accepted_bundle
from specchoice_measurement import adapter
from specchoice_measurement.adapter import AdapterError, build_pr2164_adapter_batch, validate_complete_adapter_batch


class MeasurementAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.experiment_root = Path(__file__).parents[1]
        # Legacy/pending rehearsal coverage needs an isolated pre-cutover root;
        # the live authority and revocation are intentionally active-v3.
        self._legacy_root = tempfile.TemporaryDirectory()
        self.addCleanup(self._legacy_root.cleanup)
        source_root = Path(self._legacy_root.name)
        (source_root / "phase2").mkdir()
        (source_root / "receipts/pending").mkdir(parents=True)
        shutil.copy2(self.experiment_root / "phase2/source-authority-v9-historical.json", source_root / "phase2/source-authority.json")
        shutil.copy2(self.experiment_root / "phase2/source-authority-v10-pending.json", source_root / "phase2/source-authority-v10-pending.json")
        shutil.copy2(self.experiment_root / "receipts/pending/fixture-closure-transition-v2-to-v3.json", source_root / "receipts/pending/fixture-closure-transition-v2-to-v3.json")
        shutil.copy2(self.experiment_root / "receipts/fixture-closure-acceptance-audit-v3.json", source_root / "receipts/fixture-closure-acceptance-audit-v3.json")
        self.authority = source_root / "phase2/source-authority.json"
        self.active_authority = self.experiment_root / "phase2/source-authority.json"
        self.revocation = self.experiment_root / "receipts/fixture-closure-revocation-v2.json"
        self.bundle = (
            self.experiment_root
            / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"
        )
        self.rules = self.experiment_root / "config/measurement/pr2164-adapter-rules-v1.json"
        self.pending_authority = source_root / "phase2/source-authority-v10-pending.json"
        self.transition = source_root / "receipts/pending/fixture-closure-transition-v2-to-v3.json"
        self.pending_bundle = (
            self.experiment_root
            / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v3"
        )

    def build(self):
        return build_pr2164_adapter_batch(
            authority_path=self.authority,
            bundle_root=self.bundle,
            rules_path=self.rules,
        )

    def test_exact_eleven_case_metric_population_contract(self) -> None:
        contract = json.loads((self.experiment_root / "config/measurement/pr2164-semantic-gold-contract-v1.json").read_text())
        golden = json.loads((self.experiment_root / "fixtures/measurement/golden-predictions-v3.json").read_text())
        outcomes = {outcome["fixture_id"]: outcome for outcome in golden["outcomes"]}
        self.assertEqual(len(outcomes), 11)
        self.assertEqual({key for key, value in outcomes.items() if value["surfaced"]}, set(contract["surfaced_ids"]))
        self.assertEqual({key for key, value in outcomes.items() if not value["surfaced"]}, set(contract["negative_ids"]))
        self.assertEqual([outcomes[key]["proposed_name"] for key in outcomes if outcomes[key]["parameter_status"] == "accept"], contract["identity_names"])
        self.assertEqual(golden["score_bearing_span_count"], 8)

    def build_pending(self):
        return build_pr2164_adapter_batch(
            authority_path=self.authority,
            bundle_root=self.pending_bundle,
            rules_path=self.rules,
            pending_authority_path=self.pending_authority,
            transition_path=self.transition,
        )

    def build_active(self):
        return build_pr2164_adapter_batch(
            authority_path=self.active_authority,
            bundle_root=self.pending_bundle,
            rules_path=self.rules,
            revocation_path=self.revocation,
        )

    def source_environment(self) -> dict[str, str]:
        return {**os.environ, "PYTHONPATH": str(self.experiment_root / "src")}

    def test_explicit_pending_v3_builds_the_complete_canonical_partition(self) -> None:
        batch = self.build_pending()

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

        with self.subTest(mode="active-v3"):
            active = self.build_active()
            self.assertTrue(active.valid)
            self.assertEqual(len(active.records), 11)
            self.assertEqual(sum(len(record.raw_files) for record in active.records), 28)
            self.assertEqual(
                {category: sum(record.category == category for record in active.records)
                 for category in ("positive", "negative", "candidate")},
                {"positive": 6, "negative": 4, "candidate": 1},
            )

        for mode, inputs in {
            "pending-only": {"pending_authority_path": self.pending_authority},
            "transition-only": {"transition_path": self.transition},
            "revocation-with-pending": {
                "pending_authority_path": self.pending_authority,
                "transition_path": self.transition,
                "revocation_path": self.revocation,
            },
            "revocation-with-transition": {
                "transition_path": self.transition,
                "revocation_path": self.revocation,
            },
        }.items():
            with self.subTest(mode=mode):
                invalid = build_pr2164_adapter_batch(
                    authority_path=self.active_authority,
                    bundle_root=self.pending_bundle,
                    rules_path=self.rules,
                    **inputs,
                )
                self.assertFalse(invalid.valid)
                self.assertEqual(invalid.records, ())

    def test_cli_writes_identical_new_canonical_batches(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first.json"
            second = root / "second.json"
            command = [
                sys.executable, "-m", "specchoice_measurement.cli", "adapt-pr2164",
                "--authority", self.authority.as_posix(),
                "--bundle", self.pending_bundle.as_posix(),
                "--rules", self.rules.as_posix(),
                "--pending-authority", self.pending_authority.as_posix(),
                "--transition", self.transition.as_posix(),
            ]
            subprocess.run(
                [*command, "--output", first.as_posix()],
                check=True,
                cwd=self.experiment_root,
                env=self.source_environment(),
            )
            subprocess.run(
                [*command, "--output", second.as_posix()],
                check=True,
                cwd=self.experiment_root,
                env=self.source_environment(),
            )

            self.assertEqual(first.read_bytes(), second.read_bytes())
            emitted = json.loads(first.read_text(encoding="utf-8"))
            self.assertEqual(emitted["adapter_batch_sha256"], self.build_pending().adapter_batch_sha256)

            active_command = [
                sys.executable, "-m", "specchoice_measurement.cli", "adapt-pr2164",
                "--authority", self.active_authority.as_posix(),
                "--bundle", self.pending_bundle.as_posix(),
                "--rules", self.rules.as_posix(),
                "--revocation", self.revocation.as_posix(),
            ]
            active = root / "active-v3.json"
            subprocess.run(
                [*active_command, "--output", active.as_posix()],
                check=True,
                cwd=self.experiment_root,
                env=self.source_environment(),
            )
            self.assertEqual(
                json.loads(active.read_text(encoding="utf-8"))["adapter_batch_sha256"],
                self.build_active().adapter_batch_sha256,
            )

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

        with self.subTest(mode="revocation-appears-during-legacy-validation"):
            original_run = adapter.subprocess.run
            revocation = self.authority.parent.parent / "receipts/fixture-closure-revocation-v2.json"

            def validate_then_create_revocation(*args, **kwargs):
                result = original_run(*args, **kwargs)
                revocation.write_bytes(self.revocation.read_bytes())
                return result

            with mock.patch("specchoice_measurement.adapter.subprocess.run", side_effect=validate_then_create_revocation):
                rejected = build_pr2164_adapter_batch(
                    authority_path=self.authority,
                    bundle_root=self.bundle,
                    rules_path=self.rules,
                )
            self.assertFalse(rejected.valid)
            self.assertEqual(rejected.records, ())

        with self.subTest(mode="revoked-v2-historical"):
            rejected = build_pr2164_adapter_batch(
                authority_path=self.experiment_root / "phase2/source-authority-v9-historical.json",
                bundle_root=self.bundle,
                rules_path=self.rules,
            )
            self.assertFalse(rejected.valid)
            self.assertEqual(rejected.records, ())

    def test_rules_require_a_versioned_identifier(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "rules.json"
            rules = json.loads(self.rules.read_text(encoding="utf-8"))
            rules["adapter_version"] = "pr2164-adapter-v0"
            path.write_bytes(canonical_json_bytes(rules))
            with self.assertRaisesRegex(AdapterError, "ADAPTER_RULES_INVALID"):
                build_pr2164_adapter_batch(authority_path=self.authority, bundle_root=self.bundle, rules_path=path)

    def test_rules_require_the_exact_expected_fields_mapping(self) -> None:
        required = {
            "candidate_or_negative": ["expect_extract", "expect_params", "id"],
            "positive": ["class", "expect_extract", "expect_status", "gold_name", "id", "must_have_excerpt"],
        }
        variants = {
            "empty": {"candidate_or_negative": [], "positive": []},
            "missing": {"positive": required["positive"]},
            "reordered": {"candidate_or_negative": list(reversed(required["candidate_or_negative"])), "positive": required["positive"]},
            "non-string": {"candidate_or_negative": ["expect_extract", 1, "id"], "positive": required["positive"]},
        }
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "rules.json"
            for variant, expected_fields in variants.items():
                with self.subTest(variant=variant):
                    rules = json.loads(self.rules.read_text(encoding="utf-8"))
                    rules["expected_fields"] = expected_fields
                    path.write_bytes(canonical_json_bytes(rules))
                    with self.assertRaisesRegex(AdapterError, "ADAPTER_RULES_INVALID"):
                        build_pr2164_adapter_batch(
                            authority_path=self.authority, bundle_root=self.bundle, rules_path=path
                        )

    def test_adapter_preserves_authoritative_bytes_and_refuses_output_overwrite(self) -> None:
        raw_before = {
            path.relative_to(self.bundle).as_posix(): sha256_bytes(path.read_bytes())
            for path in sorted((self.bundle / "raw").rglob("*"))
            if path.is_file()
        }
        self.build()
        raw_after = {
            path.relative_to(self.bundle).as_posix(): sha256_bytes(path.read_bytes())
            for path in sorted((self.bundle / "raw").rglob("*"))
            if path.is_file()
        }
        self.assertEqual(raw_after, raw_before)

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "immutable.json"
            output.write_text("preserve me", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable, "-m", "specchoice_measurement.cli", "adapt-pr2164",
                    "--authority", self.authority.as_posix(), "--bundle", self.bundle.as_posix(),
                    "--rules", self.rules.as_posix(), "--output", output.as_posix(),
                ],
                cwd=self.experiment_root,
                env=self.source_environment(),
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ADAPTER_OUTPUT_ALREADY_EXISTS", result.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), "preserve me")
            broken = Path(temporary) / "broken.json"
            broken.symlink_to(Path(temporary) / "missing-target")
            result = subprocess.run(
                [*result.args[:-1], broken.as_posix()], cwd=self.experiment_root,
                env=self.source_environment(),
                check=False, capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(broken.is_symlink())

    def test_public_builder_preserves_conflict_provenance(self) -> None:
        valid = self.build()
        record = next(item for item in valid.records if item.fixture_id == "POS_CSR_RW_MTVEC_ACCESS")
        hashes = {
            item.role: item.sha256
            for item in record.raw_files
            if item.role in {"fixture_expected", "fixture_gold"}
        }
        original = adapter._bounded_yaml_fields

        def conflicting_gold(raw: bytes, *, source: str) -> dict[str, object]:
            fields = original(raw, source=source)
            if source == "POS_CSR_RW_MTVEC_ACCESS:gold":
                return {**fields, "name": "FORGED_MTVEC_ACCESS"}
            return fields

        with mock.patch("specchoice_measurement.adapter._bounded_yaml_fields", side_effect=conflicting_gold):
            invalid = self.build()

        self.assertFalse(invalid.valid)
        self.assertEqual(invalid.records, ())
        self.assertEqual(invalid.source_identity, valid.source_identity)
        self.assertEqual(
            invalid.diagnostics[0].as_dict(),
            {
                "code": "GOLD_NAME_MISMATCH",
                "expected": record.original_score_bearing["gold_name"],
                "field": "gold_name",
                "fixture_id": "POS_CSR_RW_MTVEC_ACCESS",
                "observed": "FORGED_MTVEC_ACCESS",
                "severity": "blocker",
                "source_hashes": hashes,
            },
        )

    def test_public_builder_rejects_swapped_raw_leaf_and_fifo_without_consuming_or_blocking(self) -> None:
        """The public builder must consume only bytes returned by the custody helper."""
        real_open = filesystem.os.open
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            leaf = root / "raw.yaml"
            external = root / "external.yaml"
            external.write_text("sentinel: external\n", encoding="utf-8")
            for kind in ("symlink", "fifo"):
                with self.subTest(kind=kind):
                    leaf.write_text("safe: raw\n", encoding="utf-8")
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

        with mock.patch(
            "specchoice_measurement.adapter.read_authoritative_file",
            side_effect=lambda root, relative: (
                (_ for _ in ()).throw(FilesystemPolicyError("SPECIAL_FILE_KIND_REJECTED"))
                if relative.startswith("raw/")
                else read_authoritative_file(root, relative)
            ),
            create=True,
        ):
            invalid = self.build()
        self.assertFalse(invalid.valid)
        self.assertEqual(invalid.records, ())
        self.assertEqual(invalid.diagnostics[0].code, "RAW_PATH_OR_IDENTITY_INVALID")

    def test_public_builder_binds_complete_validator_receipt_and_rejects_post_validation_authority_replacement(self) -> None:
        original_run = adapter.subprocess.run
        replacement = json.loads(self.pending_authority.read_text(encoding="utf-8"))
        replacement["root_sha256"] = "0" * 64
        verified = verify_accepted_bundle(self.pending_bundle)
        expected_provenance = {
            "generation": verified["generation"],
            "manifest_sha256": verified["manifest_sha256"],
            "root_sha256": verified["root_sha256"],
        }

        with tempfile.TemporaryDirectory() as temporary:
            pending = Path(temporary) / "source-authority-v10-pending.json"
            pending.write_bytes(self.pending_authority.read_bytes())
            def validate_then_replace(*args, **kwargs):
                result = original_run(*args, **kwargs)
                pending.write_bytes(canonical_json_bytes(replacement))
                return result
            with mock.patch("specchoice_measurement.adapter.subprocess.run", side_effect=validate_then_replace):
                invalid = build_pr2164_adapter_batch(
                    authority_path=self.authority,
                    bundle_root=self.pending_bundle,
                    rules_path=self.rules,
                    pending_authority_path=pending,
                    transition_path=self.transition,
                )
        self.assertFalse(invalid.valid)
        self.assertEqual(invalid.records, ())
        self.assertEqual(invalid.source_identity, expected_provenance)

        with tempfile.TemporaryDirectory() as temporary:
            revocation = Path(temporary) / "fixture-closure-revocation-v2.json"
            revocation.write_bytes(self.revocation.read_bytes())

            def validate_then_replace_revocation(*args, **kwargs):
                result = original_run(*args, **kwargs)
                revocation.write_bytes(canonical_json_bytes(replacement))
                return result

            with mock.patch("specchoice_measurement.adapter.subprocess.run", side_effect=validate_then_replace_revocation):
                invalid = build_pr2164_adapter_batch(
                    authority_path=self.active_authority,
                    bundle_root=self.pending_bundle,
                    rules_path=self.rules,
                    revocation_path=revocation,
                )
        self.assertFalse(invalid.valid)
        self.assertEqual(invalid.records, ())
        self.assertEqual(invalid.source_identity, expected_provenance)

        with tempfile.TemporaryDirectory() as temporary:
            active = Path(temporary) / "source-authority.json"
            active.write_bytes(self.active_authority.read_bytes())

            def validate_then_replace_active(*args, **kwargs):
                result = original_run(*args, **kwargs)
                active.write_bytes(canonical_json_bytes(replacement))
                return result

            with mock.patch("specchoice_measurement.adapter.subprocess.run", side_effect=validate_then_replace_active):
                invalid = build_pr2164_adapter_batch(
                    authority_path=active,
                    bundle_root=self.pending_bundle,
                    rules_path=self.rules,
                    revocation_path=self.revocation,
                )
        self.assertFalse(invalid.valid)
        self.assertEqual(invalid.records, ())
        self.assertEqual(invalid.source_identity, expected_provenance)

        mutations = {
            "external_publication_authorized": lambda payload: payload.__setitem__("external_publication_authorized", True),
            "local_only": lambda payload: payload.__setitem__("local_only", False),
            "decision_sha256": lambda payload: payload.__setitem__("decision_sha256", "0" * 64),
            "request_sha256": lambda payload: payload.__setitem__("request_sha256", "0" * 64),
            "extra_key": lambda payload: payload.__setitem__("unexpected", True),
        }
        for mutation, apply_mutation in mutations.items():
            with self.subTest(mutation=mutation):
                with tempfile.TemporaryDirectory() as temporary:
                    active = Path(temporary) / "source-authority.json"
                    active.write_bytes(self.active_authority.read_bytes())
                    replacement = json.loads(active.read_text(encoding="utf-8"))
                    apply_mutation(replacement)

                    def validate_then_replace_active(*args, **kwargs):
                        result = original_run(*args, **kwargs)
                        active.write_bytes(canonical_json_bytes(replacement))
                        return result

                    with mock.patch("specchoice_measurement.adapter.subprocess.run", side_effect=validate_then_replace_active):
                        invalid = build_pr2164_adapter_batch(
                            authority_path=active,
                            bundle_root=self.pending_bundle,
                            rules_path=self.rules,
                            revocation_path=self.revocation,
                        )
                self.assertFalse(invalid.valid)
                self.assertEqual(invalid.records, ())
                self.assertEqual(invalid.source_identity, expected_provenance)

        for receipt_variant in ("missing-final-newline", "crlf"):
            with self.subTest(receipt_variant=receipt_variant):
                def validate_with_noncanonical_stdout(*args, **kwargs):
                    result = original_run(*args, **kwargs)
                    if receipt_variant == "missing-final-newline":
                        stdout = result.stdout.rstrip("\n")
                    else:
                        stdout = result.stdout.replace("\n", "\r\n")
                    return subprocess.CompletedProcess(result.args, result.returncode, stdout, result.stderr)

                with mock.patch("specchoice_measurement.adapter.subprocess.run", side_effect=validate_with_noncanonical_stdout):
                    invalid = self.build_active()
                self.assertFalse(invalid.valid)
                self.assertEqual(invalid.records, ())
                self.assertEqual(invalid.source_identity, expected_provenance)

        for descriptor in ("snapshot-manifest.json", "fixture-registry-pr2164-v1.json"):
            with self.subTest(descriptor=descriptor):
                with tempfile.TemporaryDirectory() as temporary:
                    bundle = Path(temporary) / self.pending_bundle.name
                    shutil.copytree(self.pending_bundle, bundle)
                    descriptor_path = bundle / descriptor

                    def validate_then_replace_descriptor(*args, **kwargs):
                        result = original_run(*args, **kwargs)
                        replacement = json.loads(descriptor_path.read_text(encoding="utf-8"))
                        replacement["unexpected"] = True
                        if descriptor == "snapshot-manifest.json":
                            replacement["snapshot_manifest_sha256"] = sha256_bytes(
                                canonical_json_bytes(
                                    {key: value for key, value in replacement.items() if key != "snapshot_manifest_sha256"}
                                )
                            )
                        descriptor_path.write_bytes(canonical_json_bytes(replacement))
                        return result

                    with mock.patch("specchoice_measurement.adapter.subprocess.run", side_effect=validate_then_replace_descriptor):
                        invalid = build_pr2164_adapter_batch(
                            authority_path=self.active_authority,
                            bundle_root=bundle,
                            rules_path=self.rules,
                            revocation_path=self.revocation,
                        )
                self.assertFalse(invalid.valid)
                self.assertEqual(invalid.records, ())
                self.assertEqual(invalid.source_identity, expected_provenance)
                self.assertEqual(invalid.diagnostics[0].code, "ACTIVE_SOURCE_CUTOVER_DESCRIPTOR_CHANGED_DURING_VALIDATION")

        with self.subTest(descriptor="authority-revocation-pair-swap"):
            with tempfile.TemporaryDirectory() as temporary:
                authority = Path(temporary) / "source-authority.json"
                revocation = Path(temporary) / "fixture-closure-revocation-v2.json"
                authority.write_bytes(self.active_authority.read_bytes())
                revocation.write_bytes(self.revocation.read_bytes())
                authority_raw = authority.read_bytes()
                revocation_raw = revocation.read_bytes()

                def validate_then_swap_descriptors(*args, **kwargs):
                    result = original_run(*args, **kwargs)
                    authority.write_bytes(revocation_raw)
                    revocation.write_bytes(authority_raw)
                    return result

                with mock.patch("specchoice_measurement.adapter.subprocess.run", side_effect=validate_then_swap_descriptors):
                    invalid = build_pr2164_adapter_batch(
                        authority_path=authority,
                        bundle_root=self.pending_bundle,
                        rules_path=self.rules,
                        revocation_path=revocation,
                    )
            self.assertFalse(invalid.valid)
            self.assertEqual(invalid.records, ())
            self.assertEqual(invalid.source_identity, expected_provenance)
            self.assertEqual(invalid.diagnostics[0].code, "ACTIVE_SOURCE_CUTOVER_DESCRIPTOR_CHANGED_DURING_VALIDATION")

    def test_public_builder_rejects_rebound_rules_authority_and_registry_roles(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            copied_rules = root / "rules.json"
            copied_rules.write_bytes(self.rules.read_bytes())
            rebound = build_pr2164_adapter_batch(
                authority_path=self.authority,
                bundle_root=self.pending_bundle,
                rules_path=copied_rules,
                pending_authority_path=self.pending_authority,
                transition_path=self.transition,
            )
            self.assertTrue(rebound.valid)
            rules = json.loads(copied_rules.read_text(encoding="utf-8"))
            rules["fixture_count"] = 10
            copied_rules.write_bytes(canonical_json_bytes(rules))
            with self.assertRaisesRegex(AdapterError, "ADAPTER_RULES_INVALID"):
                build_pr2164_adapter_batch(
                    authority_path=self.authority,
                    bundle_root=self.pending_bundle,
                    rules_path=copied_rules,
                    pending_authority_path=self.pending_authority,
                    transition_path=self.transition,
                )


if __name__ == "__main__":
    unittest.main()
