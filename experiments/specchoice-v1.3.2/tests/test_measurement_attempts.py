# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Immutable, role-separated custody contracts for Phase 2 attempts."""

from __future__ import annotations

import base64
import hashlib
import json
import shutil
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from specchoice_evidence.canonical import canonical_json_bytes, sha256_bytes
from specchoice_measurement.adapter import build_pr2164_adapter_batch
from specchoice_measurement.attempts import AttemptError, run_measurement_attempt, validate_measurement_attempt
from specchoice_measurement.cli import (
    command_run_adversarial_oracles,
    command_run_formal_measurement,
    validate_adversarial_report,
)
from specchoice_measurement.preflight import preflight_prediction_batch
from specchoice_measurement.scoring import score_prediction_batch


class MeasurementAttemptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.experiment_root = Path(__file__).parents[1]
        self.bundle = self.experiment_root / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"
        self.batch = build_pr2164_adapter_batch(
            authority_path=self.experiment_root / "phase2/source-authority.json",
            bundle_root=self.bundle,
            rules_path=self.experiment_root / "config/measurement/pr2164-adapter-rules-v1.json",
        )
        self.raw = (self.experiment_root / "fixtures/measurement/golden-predictions-v1.json").read_bytes()

    def _inputs(self, *, raw: bytes | None = None, mode: str = "formal") -> dict[str, object]:
        prediction_bytes = self.raw if raw is None else raw
        preflight = preflight_prediction_batch(raw=prediction_bytes, adapter_batch=self.batch, ingress="current-v1")
        score = score_prediction_batch(adapter_batch=self.batch, preflight=preflight, mode=mode)
        return {
            "adapter_batch": self.batch,
            "ingress": "current-v1",
            "preflight": preflight,
            "raw_predictions": prediction_bytes,
            "score_result": score,
            "schema_path": self.experiment_root / "config/measurement/canonical-adjudication-schema-v1.json",
        }

    def test_complete_formal_attempt_preserves_raw_bytes_and_binds_siblings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            attempt = run_measurement_attempt(
                mode="formal", attempt_id="complete", attempt_root=Path(directory), inputs=self._inputs()
            )
            target = Path(directory) / "complete"
            manifest = json.loads((target / "attempt.json").read_text(encoding="utf-8"))

            self.assertEqual(attempt["status"], "completed")
            self.assertEqual(manifest["role"], "formal")
            decoded = base64.b64decode(manifest["raw_predictions_base64"], validate=True)
            self.assertEqual(decoded, self.raw)
            self.assertEqual(manifest["raw_predictions_sha256"], sha256_bytes(self.raw))
            self.assertEqual(manifest["attempt_sha256"], sha256_bytes(canonical_json_bytes({
                key: value for key, value in manifest.items() if key != "attempt_sha256"
            })))
            self.assertEqual(set(manifest["artifacts"]), {
                "case-outcomes.json", "diagnostics.json", "metrics.json", "parsed-predictions.json", "report.json"
            })
            self.assertEqual(validate_measurement_attempt(attempt_root=target)["status"], "completed")

    def test_blocking_preflight_is_immutable_but_has_no_score_artifacts(self) -> None:
        invalid = json.loads(self.raw.decode("utf-8"))
        invalid["predictions"] = invalid["predictions"][:-1]
        raw = json.dumps(invalid, separators=(",", ":")).encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            result = run_measurement_attempt(
                mode="formal", attempt_id="invalid", attempt_root=Path(directory), inputs=self._inputs(raw=raw)
            )
            target = Path(directory) / "invalid"
            manifest = json.loads((target / "attempt.json").read_text(encoding="utf-8"))

            self.assertEqual((result["status"], manifest["role"]), ("invalid_preflight", "invalid_preflight"))
            self.assertTrue((target / "parsed-predictions.json").is_file())
            self.assertTrue((target / "diagnostics.json").is_file())
            self.assertFalse((target / "case-outcomes.json").exists())
            self.assertFalse((target / "metrics.json").exists())
            self.assertFalse((target / "report.json").exists())

    def test_diagnostic_only_is_not_promotable_and_targets_are_never_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            diagnostic = run_measurement_attempt(
                mode="diagnostic_only", attempt_id="diagnostic", attempt_root=root, inputs=self._inputs(mode="diagnostic_only")
            )
            self.assertEqual((diagnostic["role"], diagnostic["status"]), ("diagnostic_only", "diagnostic_only"))
            self.assertFalse((root / "diagnostic" / "metrics.json").exists())

            target = root / "collision"
            target.mkdir()
            (target / "sentinel").write_bytes(b"original")
            with self.assertRaisesRegex(AttemptError, "ATTEMPT_TARGET_EXISTS"):
                run_measurement_attempt(mode="formal", attempt_id="collision", attempt_root=root, inputs=self._inputs())
            self.assertEqual((target / "sentinel").read_bytes(), b"original")

    def test_race_and_tampering_are_rejected_without_mutating_existing_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            from specchoice_measurement import attempts

            original = attempts._publish_directory_no_replace

            def race(source: Path, target: Path, collision_code: str) -> None:
                target.mkdir()
                (target / "sentinel").write_bytes(b"racer")
                original(source, target, collision_code)

            with patch("specchoice_measurement.attempts._publish_directory_no_replace", side_effect=race):
                with self.assertRaisesRegex(AttemptError, "ATTEMPT_TARGET_EXISTS"):
                    run_measurement_attempt(mode="formal", attempt_id="race", attempt_root=root, inputs=self._inputs())
            self.assertEqual((root / "race" / "sentinel").read_bytes(), b"racer")

            run_measurement_attempt(mode="formal", attempt_id="tamper", attempt_root=root, inputs=self._inputs())
            (root / "tamper" / "metrics.json").write_bytes(b"{}\n")
            with self.assertRaisesRegex(AttemptError, "ATTEMPT_ARTIFACT_HASH_MISMATCH"):
                validate_measurement_attempt(attempt_root=root / "tamper")

    def test_self_consistent_forged_derived_artifacts_fail_replay(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_measurement_attempt(mode="formal", attempt_id="forged", attempt_root=root, inputs=self._inputs())
            target = root / "forged"
            forged = {"disposition": {"denominator": 7, "numerator": 0}}
            forged_raw = canonical_json_bytes(forged)
            (target / "metrics.json").write_bytes(forged_raw)
            manifest = json.loads((target / "attempt.json").read_text(encoding="utf-8"))
            manifest["artifacts"]["metrics.json"] = {
                "byte_length": len(forged_raw), "sha256": sha256_bytes(forged_raw)
            }
            manifest["attempt_sha256"] = sha256_bytes(canonical_json_bytes({
                key: value for key, value in manifest.items() if key != "attempt_sha256"
            }))
            (target / "attempt.json").write_bytes(canonical_json_bytes(manifest))

            with self.assertRaisesRegex(AttemptError, "ATTEMPT_REPLAY_ARTIFACT_MISMATCH"):
                validate_measurement_attempt(attempt_root=target)

    def test_attempt_validation_rejects_symlinked_manifest_and_all_retained_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_measurement_attempt(mode="formal", attempt_id="linked", attempt_root=root, inputs=self._inputs())
            target = root / "linked"
            manifest = json.loads((target / "attempt.json").read_text(encoding="utf-8"))
            outside = root / "outside"
            outside.mkdir()

            for name in ("attempt.json", *manifest["artifacts"]):
                owned = target / name
                external = outside / name
                shutil.copy2(owned, external)
                owned.unlink()
                owned.symlink_to(external)
                code = "ATTEMPT_MANIFEST_INVALID" if name == "attempt.json" else "ATTEMPT_ARTIFACT_INVALID"
                with self.assertRaisesRegex(AttemptError, code):
                    validate_measurement_attempt(attempt_root=target)
                owned.unlink()
                shutil.copy2(external, owned)

    def test_formal_cli_writes_one_clean_all_eleven_attempt_and_refuses_regeneration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = SimpleNamespace(
                authority=self.experiment_root / "phase2/source-authority.json",
                bundle=self.bundle,
                rules=self.experiment_root / "config/measurement/pr2164-adapter-rules-v1.json",
                schema=self.experiment_root / "config/measurement/canonical-adjudication-schema-v1.json",
                predictions=self.experiment_root / "fixtures/measurement/golden-predictions-v1.json",
                attempt_root=root,
                attempt_id="formal-golden",
            )
            self.assertEqual(command_run_formal_measurement(args), 0)
            target = root / "formal-golden"
            manifest = json.loads((target / "attempt.json").read_text(encoding="utf-8"))
            self.assertEqual((manifest["role"], manifest["status"]), ("formal", "completed"))
            self.assertEqual(json.loads((target / "diagnostics.json").read_text(encoding="utf-8")), [])
            self.assertEqual(len(json.loads((target / "case-outcomes.json").read_text(encoding="utf-8"))), 11)
            self.assertEqual(
                json.loads((target / "metrics.json").read_text(encoding="utf-8")),
                {"disposition": {"denominator": 7, "numerator": 7}, "evidence_integrity": {"denominator": 7, "numerator": 7}, "identity": {"denominator": 6, "numerator": 6}, "surfacing": {"denominator": 7, "numerator": 7}},
            )
            for name in manifest["artifacts"]:
                content = (target / name).read_bytes()
                self.assertEqual(manifest["artifacts"][name], {"byte_length": len(content), "sha256": sha256_bytes(content)})
            original = (target / "attempt.json").read_bytes()
            with self.assertRaisesRegex(AttemptError, "ATTEMPT_TARGET_EXISTS"):
                command_run_formal_measurement(args)
            self.assertEqual((target / "attempt.json").read_bytes(), original)

    def test_adversarial_cli_is_diagnostic_only_and_matches_every_frozen_oracle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            formal_args = SimpleNamespace(
                authority=self.experiment_root / "phase2/source-authority.json",
                bundle=self.bundle,
                rules=self.experiment_root / "config/measurement/pr2164-adapter-rules-v1.json",
                schema=self.experiment_root / "config/measurement/canonical-adjudication-schema-v1.json",
                predictions=self.experiment_root / "fixtures/measurement/golden-predictions-v1.json",
                attempt_root=root / "attempts",
                attempt_id="formal",
            )
            self.assertEqual(command_run_formal_measurement(formal_args), 0)
            report = root / "adversarial.json"
            args = SimpleNamespace(
                authority=formal_args.authority,
                bundle=formal_args.bundle,
                rules=formal_args.rules,
                schema=formal_args.schema,
                predictions=formal_args.predictions,
                oracle=self.experiment_root / "fixtures/measurement/adversarial/required-diagnostics-v1.json",
                formal_attempt=root / "attempts/formal",
                report=report,
            )
            self.assertEqual(command_run_adversarial_oracles(args), 0)
            payload = validate_adversarial_report(report_path=report)
            self.assertEqual(payload["status"], "diagnostic_only")
            self.assertEqual(len(payload["cases"]), 12)
            self.assertTrue(all(case["role"] == "diagnostic_only" and case["matched"] for case in payload["cases"]))
            attempt_root = root / "adversarial-attempts"
            self.assertTrue(all((attempt_root / case["attempt_id"] / "attempt.json").is_file() for case in payload["cases"]))
            self.assertNotIn("metrics", payload)
            original_payload = deepcopy(payload)

            def assert_invalid_attempt_id(attempt_id: str) -> None:
                tampered = deepcopy(original_payload)
                tampered["cases"][0]["attempt_id"] = attempt_id
                report.write_bytes(canonical_json_bytes(tampered))
                with self.assertRaisesRegex(AttemptError, "ADVERSARIAL_REPORT_INVALID"):
                    validate_adversarial_report(report_path=report)

            assert_invalid_attempt_id(str((attempt_root / "oracle-01").resolve()))

            outside = root / "outside"
            outside.mkdir()
            shutil.copytree(attempt_root / "oracle-01", outside / "oracle-01")
            assert_invalid_attempt_id("../outside/oracle-01")

            for name in ("attempt.json", "diagnostics.json", "parsed-predictions.json"):
                owned = attempt_root / "oracle-01" / name
                external = outside / name
                shutil.copy2(owned, external)
                owned.unlink()
                owned.symlink_to(external)
                report.write_bytes(canonical_json_bytes(original_payload))
                with self.assertRaisesRegex(AttemptError, "ADVERSARIAL_REPORT_INVALID"):
                    validate_adversarial_report(report_path=report)
                owned.unlink()
                shutil.copy2(external, owned)

            shutil.rmtree(attempt_root / "oracle-01")
            (attempt_root / "oracle-01").symlink_to(outside / "oracle-01", target_is_directory=True)
            report.write_bytes(canonical_json_bytes(original_payload))
            with self.assertRaisesRegex(AttemptError, "ADVERSARIAL_REPORT_INVALID"):
                validate_adversarial_report(report_path=report)

            with self.assertRaisesRegex(AttemptError, "ADVERSARIAL_REPORT_INVALID"):
                report.write_bytes(canonical_json_bytes({"status": "formal"}))
                validate_adversarial_report(report_path=report)


if __name__ == "__main__":
    unittest.main()
