"""Public H1 packet, readiness, and human-decision contracts."""

from __future__ import annotations

import json
import os
import shutil
import stat
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from specchoice_evidence.canonical import canonical_json_bytes, sha256_bytes
from specchoice_measurement import h1
from specchoice_measurement.h1 import H1Error


class H1PublicContractTests(unittest.TestCase):
    def test_v5_h1_question_contract_is_exactly_seven_questions(self) -> None:
        root = Path(__file__).parents[1]
        value = json.loads((root / "config/measurement/h1-semantic-review-questions-v1.json").read_text())
        h1.validate_v5_h1_question_contract(value)
        value["question_ids"] = value["question_ids"][:-1]
        with self.assertRaisesRegex(H1Error, "V5_H1_QUESTION_CONTRACT_INVALID"):
            h1.validate_v5_h1_question_contract(value)

        questions = root / "config/measurement/h1-semantic-review-questions-v2.json"
        schema = root / "config/measurement/h1-review-schema-v4.json"
        bundle = root / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v3"
        result = h1.validate_h1_semantic_questions_v2(
            questions=questions, bundle_root=bundle
        )
        self.assertEqual(result["question_count"], 7)
        self.assertEqual(result["question_ids"], list(h1._SUCCESSOR_QUESTION_IDS))
        schema_result = h1.validate_h1_review_schema_v4(
            schema=schema, questions=questions, bundle_root=bundle
        )
        self.assertEqual(schema_result["questions_sha256"], result["questions_sha256"])
        complete = json.loads(questions.read_text(encoding="utf-8"))
        self.assertEqual(
            {fixture for question in complete["questions"] for fixture in question["fixture_ids"]},
            set(h1._SUCCESSOR_FIXTURE_IDS),
        )
        self.assertEqual(
            {policy for question in complete["questions"] for policy in question["policy_ids"]},
            {"CACHE", "PBMTE"},
        )
        self.assertTrue(all(len(question["evidence"]) == len(question["fixture_ids"]) for question in complete["questions"]))
        self.assertFalse(any(
            forbidden in question
            for question in complete["questions"]
            for forbidden in ("reviewer", "reviewer_identity", "signature", "timestamp", "choice")
        ))
        with tempfile.TemporaryDirectory(dir=root) as directory:
            temporary = Path(directory)
            unknown = deepcopy(complete)
            unknown["questions"][0]["unexpected"] = True
            unknown["canonical_semantic_content_sha256"] = sha256_bytes(canonical_json_bytes({
                key: item for key, item in unknown.items() if key != "canonical_semantic_content_sha256"
            }))
            unknown_path = temporary / "unknown.json"
            unknown_path.write_bytes(canonical_json_bytes(unknown))
            with self.assertRaisesRegex(H1Error, "H1_SEMANTIC_QUESTION_INVALID"):
                h1.validate_h1_semantic_questions_v2(questions=unknown_path)

            drifted = deepcopy(complete)
            drifted["questions"][0]["prompt"] += " drift"
            drifted_path = temporary / "drifted.json"
            drifted_path.write_bytes(canonical_json_bytes(drifted))
            with self.assertRaisesRegex(H1Error, "H1_SEMANTIC_QUESTIONS_HASH_INVALID"):
                h1.validate_h1_semantic_questions_v2(questions=drifted_path)

    def test_h1_v3_exposes_readiness_and_v2_decision_validation_without_human_writers(self) -> None:
        from specchoice_measurement.h1 import (  # noqa: PLC0415
            build_h1_packet,
            render_h1_markdown,
            validate_h1_decision_v2,
            validate_h1_ontology_decision_v1,
            validate_h1_ontology_options_v1,
            validate_h1_packet,
            validate_h1_readiness_v3,
            validate_h1_route_supersession_v1,
            write_h1_readiness_v3,
            write_h1_ontology_options_v1,
        )

        for value in (
            build_h1_packet,
            render_h1_markdown,
            validate_h1_packet,
            write_h1_readiness_v3,
            validate_h1_readiness_v3,
            validate_h1_decision_v2,
            validate_h1_ontology_decision_v1,
            validate_h1_route_supersession_v1,
            validate_h1_ontology_options_v1,
            write_h1_ontology_options_v1,
        ):
            self.assertTrue(callable(value))
        self.assertFalse(any("decision" in name and "validate" not in name for name in dir(h1)))
        from specchoice_measurement.cli import build_parser  # noqa: PLC0415

        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args([
                "build-h1-packet", "--formal-attempt", "formal", "--adversarial-report", "adversarial",
                "--schema", "schema", "--output", "packet", "--markdown", "markdown",
            ])
        with self.assertRaises(SystemExit):
            parser.parse_args([
                "write-h1-readiness-v3", "--formal-attempt", "formal", "--adversarial-result", "adversarial",
                "--packet", "packet", "--markdown", "markdown", "--schema", "schema",
                "--source-authority", "authority", "--canonical-revocation", "revocation", "--bundle", "bundle",
                "--rules", "rules", "--predictions", "predictions", "--oracle", "oracle",
                "--offline-replay", "replay", "--plan-summary", "/summary", "--output", "readiness",
            ])
        command_args = {
            "validate-h1-route-supersession-v1": [
                "--supersession", "supersession", "--schema", "schema", "--packet", "packet",
                "--markdown", "markdown", "--readiness", "readiness",
            ],
            "validate-h1-ontology-options-v1": ["--options", "options"],
        }
        for command, arguments in command_args.items():
            with self.subTest(command=command):
                self.assertEqual(parser.parse_args([command, *arguments]).command, command)
        root = Path(__file__).parents[1]
        options_path = root / "config/measurement/h1-ontology-policy-options-v1.json"
        supersession_path = root / "receipts/h1-review-route-supersession-v1.json"
        self.assertEqual(validate_h1_ontology_options_v1(options=options_path)["schema_version"], "h1-ontology-policy-options-v1")
        packet_path = root / "reports/h1/h1-source-gold-review-v3/h1-source-gold-review-v3.json"
        readiness_path = root / "receipts/h1-review-readiness-v3.json"
        with tempfile.TemporaryDirectory(dir=root) as directory:
            temporary = Path(directory)
            options_value = json.loads(options_path.read_text(encoding="utf-8"))
            supersession_value = json.loads(supersession_path.read_text(encoding="utf-8"))

            def with_self_hash(value: dict[str, object], field: str) -> dict[str, object]:
                value[field] = sha256_bytes(canonical_json_bytes({
                    key: item for key, item in value.items() if key != field
                }))
                return value

            def ontology_decision() -> dict[str, object]:
                value: dict[str, object] = {
                    "bindings": {
                        "options_sha256": options_value["options_sha256"],
                        "supersession_sha256": supersession_value["supersession_sha256"],
                    },
                    "cache_policy": {
                        "rationale": "Keep the cache identity unified.",
                        "selection": "unified_cache_block_identity",
                    },
                    "external_publication_authorized": False,
                    "pbmte_policy": {
                        "rationale": "PBMTE is absent from discovery.",
                        "selection": "excluded_from_discovery",
                    },
                    "reviewer": "independent-human-reviewer",
                    "schema_version": "h1-source-gold-ontology-decision-v1",
                    "signature": "signed:ontology-policy",
                    "timestamp": "2026-08-02T00:00:00Z",
                }
                return with_self_hash(value, "decision_sha256")

            def validate_ontology(
                decision: Path, *, options: Path = options_path, supersession: Path = supersession_path,
            ) -> dict[str, object]:
                with patch.object(
                    h1,
                    "validate_h1_route_supersession_v1",
                    side_effect=AssertionError("ontology validation must not replay historical H1"),
                ):
                    return validate_h1_ontology_decision_v1(
                        options=options, supersession=supersession, decision=decision,
                    )

            valid_decision = ontology_decision()
            valid_decision_path = temporary / "ontology-decision.json"
            valid_decision_path.write_bytes(canonical_json_bytes(valid_decision))
            self.assertEqual(
                validate_ontology(valid_decision_path),
                {
                    "artifact_sha256": sha256_bytes(valid_decision_path.read_bytes()),
                    "decision_sha256": valid_decision["decision_sha256"],
                    "selected_policy": {
                        "cache": "unified_cache_block_identity",
                        "pbmte": "excluded_from_discovery",
                    },
                    "valid": True,
                },
            )
            invalid_decision_path = temporary / "invalid-ontology-decision.json"
            for timestamp in (
                "", "   ", "not-a-timestamp", "2026-08-02T00:00:00",
                "2026-08-02T02:00:00+02:00", "2026-02-30T00:00:00Z", "2026-08-02T24:00:00Z",
            ):
                with self.subTest(ontology_timestamp=timestamp):
                    invalid = ontology_decision()
                    invalid["timestamp"] = timestamp
                    invalid_decision_path.write_bytes(canonical_json_bytes(with_self_hash(invalid, "decision_sha256")))
                    with self.assertRaisesRegex(H1Error, "H1_ONTOLOGY_DECISION_INVALID"):
                        validate_ontology(invalid_decision_path)
            for field in ("reviewer", "signature"):
                with self.subTest(ontology_human_field=field):
                    invalid = ontology_decision()
                    invalid[field] = " \t "
                    invalid_decision_path.write_bytes(canonical_json_bytes(with_self_hash(invalid, "decision_sha256")))
                    with self.assertRaisesRegex(H1Error, "H1_ONTOLOGY_DECISION_INVALID"):
                        validate_ontology(invalid_decision_path)
            for policy_name in ("pbmte_policy", "cache_policy"):
                with self.subTest(ontology_rationale=policy_name):
                    invalid = ontology_decision()
                    assert isinstance(invalid[policy_name], dict)
                    invalid[policy_name]["rationale"] = " \t "
                    invalid_decision_path.write_bytes(canonical_json_bytes(with_self_hash(invalid, "decision_sha256")))
                    with self.assertRaisesRegex(H1Error, "H1_ONTOLOGY_DECISION_INVALID"):
                        validate_ontology(invalid_decision_path)
            route_bindings = supersession_value["bindings"]
            self.assertIsInstance(route_bindings, dict)
            self.assertEqual(len(route_bindings), 8)
            for binding in sorted(route_bindings):
                with self.subTest(supersession_binding=binding):
                    invalid_supersession = deepcopy(supersession_value)
                    invalid_supersession["bindings"][binding] = "0" * 64
                    with_self_hash(invalid_supersession, "supersession_sha256")
                    invalid_supersession_path = temporary / f"supersession-{binding}.json"
                    invalid_supersession_path.write_bytes(canonical_json_bytes(invalid_supersession))
                    with self.assertRaisesRegex(H1Error, "H1_ROUTE_SUPERSESSION_INVALID"):
                        validate_ontology(valid_decision_path, supersession=invalid_supersession_path)

            unknown_id = deepcopy(options_value)
            unknown_id["pbmte_choices"][0]["id"] = "unknown_policy"
            changed_consequence = deepcopy(options_value)
            changed_consequence["cache_choices"][0]["consequences"]["scope"] = "changed"
            changed_order = deepcopy(options_value)
            changed_order["pbmte_choices"].reverse()
            forbidden_selection = deepcopy(options_value)
            forbidden_selection["selection"] = "excluded_from_discovery"
            forbidden_human_field = deepcopy(options_value)
            forbidden_human_field["reviewer"] = "test-only-reviewer"
            invalid_options_path = temporary / "invalid-options.json"
            for attack, invalid_options in (
                ("unknown_id", unknown_id),
                ("changed_consequence", changed_consequence),
                ("changed_order", changed_order),
                ("forbidden_selection", forbidden_selection),
                ("forbidden_human_field", forbidden_human_field),
            ):
                with self.subTest(options_attack=attack):
                    invalid_options_path.write_bytes(canonical_json_bytes(
                        with_self_hash(invalid_options, "options_sha256")
                    ))
                    with self.assertRaisesRegex(H1Error, "H1_ONTOLOGY_OPTIONS_INVALID"):
                        validate_h1_ontology_options_v1(options=invalid_options_path)

            missing_options_path = temporary / "missing-options.json"
            noncanonical_options_path = temporary / "noncanonical-options.json"
            noncanonical_options_path.write_text(json.dumps(options_value, indent=2), encoding="utf-8")
            symlink_options_path = temporary / "symlink-options.json"
            symlink_options_path.symlink_to(options_path)
            fifo_options_path = temporary / "fifo-options.json"
            os.mkfifo(fifo_options_path)
            for attack, invalid_path in (
                ("missing", missing_options_path),
                ("noncanonical", noncanonical_options_path),
                ("symlink", symlink_options_path),
                ("fifo", fifo_options_path),
            ):
                with self.subTest(options_path_attack=attack):
                    with self.assertRaisesRegex(H1Error, "H1_ONTOLOGY_OPTIONS_INVALID"):
                        validate_h1_ontology_options_v1(options=invalid_path)

            generated_options_path = temporary / "generated-options.json"
            self.assertEqual(write_h1_ontology_options_v1(output=generated_options_path), options_value)
            generated_options_raw = generated_options_path.read_bytes()
            with self.assertRaisesRegex(H1Error, "H1_ONTOLOGY_OPTIONS_OUTPUT_INVALID"):
                write_h1_ontology_options_v1(output=generated_options_path)
            self.assertEqual(generated_options_path.read_bytes(), generated_options_raw)

            preexisting_options_path = temporary / "preexisting-options.json"
            preexisting_options_path.write_bytes(b"preexisting options\n")
            with self.assertRaisesRegex(H1Error, "H1_ONTOLOGY_OPTIONS_OUTPUT_INVALID"):
                write_h1_ontology_options_v1(output=preexisting_options_path)
            self.assertEqual(preexisting_options_path.read_bytes(), b"preexisting options\n")

            writer_symlink_target = temporary / "writer-symlink-target.json"
            writer_symlink_target.write_bytes(b"symlink target\n")
            writer_symlink_path = temporary / "writer-symlink-options.json"
            writer_symlink_path.symlink_to(writer_symlink_target)
            with self.assertRaisesRegex(H1Error, "H1_ONTOLOGY_OPTIONS_OUTPUT_INVALID"):
                write_h1_ontology_options_v1(output=writer_symlink_path)
            self.assertTrue(writer_symlink_path.is_symlink())
            self.assertEqual(writer_symlink_target.read_bytes(), b"symlink target\n")

            writer_fifo_path = temporary / "writer-fifo-options.json"
            os.mkfifo(writer_fifo_path)
            with self.assertRaisesRegex(H1Error, "H1_ONTOLOGY_OPTIONS_OUTPUT_INVALID"):
                write_h1_ontology_options_v1(output=writer_fifo_path)
            self.assertTrue(stat.S_ISFIFO(os.lstat(writer_fifo_path).st_mode))

            legacy_decision = H1PacketTests._decision(
                json.loads(packet_path.read_text(encoding="utf-8")),
                json.loads(readiness_path.read_text(encoding="utf-8")),
            )
            legacy_decision_path = temporary / "legacy-decision.json"
            legacy_decision_path.write_bytes(canonical_json_bytes(legacy_decision))

            def validate_legacy_with_supersession(path: Path) -> dict[str, object]:
                with patch.object(h1, "_ROUTE_SUPERSESSION", path):
                    return validate_h1_decision_v2(
                        schema=root / "config/measurement/h1-review-schema-v2.json", packet=packet_path,
                        readiness=readiness_path, decision=legacy_decision_path,
                    )

            with self.assertRaisesRegex(H1Error, "H1_LEGACY_ROUTE_SUPERSEDED"):
                validate_legacy_with_supersession(supersession_path)

            missing_supersession_path = temporary / "missing-supersession.json"
            tampered_supersession = deepcopy(supersession_value)
            tampered_supersession["status"] = "reviewed"
            tampered_supersession_path = temporary / "tampered-supersession.json"
            tampered_supersession_path.write_bytes(canonical_json_bytes(
                with_self_hash(tampered_supersession, "supersession_sha256")
            ))
            symlink_supersession_path = temporary / "symlink-supersession.json"
            symlink_supersession_path.symlink_to(supersession_path)
            fifo_supersession_path = temporary / "fifo-supersession.json"
            os.mkfifo(fifo_supersession_path)
            for attack, invalid_path in (
                ("missing", missing_supersession_path),
                ("tampered", tampered_supersession_path),
                ("symlink", symlink_supersession_path),
                ("fifo", fifo_supersession_path),
            ):
                with self.subTest(legacy_supersession_attack=attack):
                    with self.assertRaisesRegex(H1Error, "H1_ROUTE_SUPERSESSION_INVALID"):
                        validate_legacy_with_supersession(invalid_path)


class H1PacketTests(unittest.TestCase):
    semantic_ids = (
        "ts03_adjacency",
        "ts03_empty_null_single_element",
        "ts03_equal_element_stable_order",
        "ts04_unclassified_manual_review",
        "ts05_adjacency",
        "ts05_empty_null_single_element",
        "ts05_equal_element_stable_order",
    )

    def setUp(self) -> None:
        self.root = Path(__file__).parents[1]
        self.formal = self.root / "runs/measurement-attempts/formal-golden-pr2164-v1"
        self.adversarial = self.root / "reports/h1/adversarial-oracle-results-v2.json"
        self.active_formal = self.root / "runs/measurement-attempts/formal-golden-pr2164-v2"
        self.active_adversarial = self.root / "reports/h1/adversarial-oracle-results-v3.json"
        self.schema = self.root / "config/measurement/h1-review-schema-v2.json"
        self.bundle = self.root / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2"
        self.active_bundle = self.root / "bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v3"
        self.rules = self.root / "config/measurement/pr2164-adapter-rules-v1.json"
        self.predictions = self.root / "fixtures/measurement/golden-predictions-v1.json"
        self.oracle = self.root / "fixtures/measurement/adversarial/required-diagnostics-v1.json"
        self.revocation = self.root / "receipts/fixture-closure-revocation-v1.json"
        self.replay = self.root / "receipts/fixture-closure-offline-replay-v3.json"
        self.cutover = self.root / "receipts/source-cutover-readiness-v10.json"

    def test_seven_question_h1_and_four_report_pipeline(self) -> None:
        value = json.loads((self.root / "config/measurement/h1-semantic-review-questions-v1.json").read_text())
        h1.validate_v5_h1_question_contract(value)
        self.assertEqual(value["question_ids"], list(self.semantic_ids))
        questions = self.root / "config/measurement/h1-semantic-review-questions-v2.json"
        schema = self.root / "config/measurement/h1-review-schema-v4.json"
        result = h1.validate_h1_semantic_questions_v2(
            questions=questions,
            bundle_root=self.active_bundle,
        )
        self.assertEqual(result["question_ids"], list(self.semantic_ids))
        self.assertEqual(
            h1.validate_h1_review_schema_v4(
                schema=schema, questions=questions, bundle_root=self.active_bundle
            )["question_count"],
            7,
        )
        from specchoice_measurement.cli import build_parser  # noqa: PLC0415

        parser = build_parser()
        for command in (
            "run-adversarial-semantic-suite-v6",
            "validate-adversarial-semantic-result-v6",
            "build-h1-semantic-packet-v6",
            "validate-h1-semantic-packet-v6",
            "write-h1-semantic-readiness-v6",
            "validate-h1-semantic-readiness",
            "validate-h1-semantic-review-decision",
            "write-final-successor-reports",
            "verify-final-successor-reports",
        ):
            self.assertIn(command, parser._subparsers._group_actions[0].choices)

    def test_report_generation_rejects_one_byte_planning_or_predecessor_report_drift_before_write(self) -> None:
        from specchoice_measurement import final_reports  # noqa: PLC0415
        from specchoice_measurement.final_reports import FinalReportError, validate_final_report_inputs  # noqa: PLC0415
        repository = self.root.parents[1]
        source = repository / ".planning" / "ROADMAP.md"
        self.assertTrue(source.is_file())
        frozen = sha256_bytes(source.read_bytes())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "input.txt").write_bytes(b"frozen\n")
            validate_final_report_inputs(root, {"input.txt": sha256_bytes(b"frozen\n")}, {"all": True}, human_disposition="approved")
            (root / "input.txt").write_bytes(b"drifted\n")
            with self.assertRaisesRegex(FinalReportError, "FINAL_REPORT_INPUT_DRIFT"):
                validate_final_report_inputs(root, {"input.txt": sha256_bytes(b"frozen\n")}, {"all": True}, human_disposition="approved")
        self.assertNotEqual(frozen, sha256_bytes(source.read_bytes() + b"\n"))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = []
            for role in final_reports._FINAL_BINDING_ROLES:
                path = f"inputs/{role}.json" if role in final_reports._CANONICAL_JSON_BINDINGS else f"inputs/{role}.md"
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                raw = canonical_json_bytes({}) if role in final_reports._CANONICAL_JSON_BINDINGS else b"frozen\n"
                target.write_bytes(raw)
                records.append({
                    "byte_length": len(raw),
                    "path": path,
                    "role": role,
                    "sha256": sha256_bytes(raw),
                })
            validated, _ = final_reports._validate_final_binding_set(root, records)
            self.assertEqual(tuple(item["role"] for item in validated), final_reports._FINAL_BINDING_ROLES)
            roadmap = root / str(records[0]["path"])
            roadmap.write_bytes(b"drifted\n")
            with self.assertRaisesRegex(FinalReportError, "FINAL_REPORT_INPUT_DRIFT"):
                final_reports._validate_final_binding_set(root, records)
            roadmap.write_bytes(b"frozen\n")
            for malformed in (
                records[:-1],
                [records[1], records[0], *records[2:]],
                [*records, {**records[-1], "role": "extra"}],
            ):
                with self.assertRaisesRegex(FinalReportError, "FINAL_REPORT_BINDING"):
                    final_reports._validate_final_binding_set(root, malformed)

            for relative in final_reports.FINAL_SUCCESSOR_TARGETS:
                (root / relative).parent.mkdir(parents=True, exist_ok=True)
            evidence = {
                "adversarial": {"case_count": 17, "matched": 17, "status": "diagnostic_only"},
                "audited_commit": "a" * 40,
                "bindings": records,
                "decision": {"aggregate_disposition": "approved", "open_semantic_ids": [], "question_count": 7},
                "external_publication_authorized": False,
                "formal": {"case_count": 11, "evidence_span_population": 10, "metrics": {}, "negative_no_surface": {"denominator": 3, "numerator": 3}},
                "schema_version": "final-successor-evidence-v1",
            }
            with patch("specchoice_measurement.final_reports._final_evidence", return_value=evidence):
                for targets in (
                    final_reports.FINAL_SUCCESSOR_TARGETS[:-1],
                    (*final_reports.FINAL_SUCCESSOR_TARGETS, "extra.md"),
                    (
                        final_reports.FINAL_SUCCESSOR_TARGETS[1],
                        final_reports.FINAL_SUCCESSOR_TARGETS[0],
                        *final_reports.FINAL_SUCCESSOR_TARGETS[2:],
                    ),
                ):
                    with self.assertRaisesRegex(FinalReportError, "FINAL_REPORT_TARGET_INVENTORY_INVALID"):
                        final_reports.write_final_successor_reports(
                            root,
                            audited_commit="a" * 40,
                            bindings=records,
                            targets=targets,
                        )
                original_link = final_reports._link_no_replace
                last = root / final_reports.FINAL_SUCCESSOR_TARGETS[-1]

                def collide_on_last(staged: Path, target: Path) -> None:
                    if target == last:
                        target.write_bytes(b"racer\n")
                    original_link(staged, target)

                with patch("specchoice_measurement.final_reports._link_no_replace", side_effect=collide_on_last):
                    with self.assertRaisesRegex(FinalReportError, "FINAL_REPORT_ATOMIC_PUBLISH_FAILED"):
                        final_reports.write_final_successor_reports(
                            root,
                            audited_commit="a" * 40,
                            bindings=records,
                            targets=final_reports.FINAL_SUCCESSOR_TARGETS,
                        )
                self.assertTrue(all(
                    not (root / relative).exists()
                    for relative in final_reports.FINAL_SUCCESSOR_TARGETS[:-1]
                ))
                self.assertEqual(last.read_bytes(), b"racer\n")

    def _legacy_context(self, directory: Path) -> dict[str, Path | None]:
        source_root = directory / "pre-cutover"
        authority = source_root / "phase2/source-authority.json"
        authority.parent.mkdir(parents=True, exist_ok=True)
        if not authority.exists():
            shutil.copy2(self.root / "phase2/source-authority-v9-historical.json", authority)
        return {
            "authority": authority,
            "bundle": self.bundle,
            "rules": self.rules,
            "predictions": self.predictions,
            "oracle": self.oracle,
            "pending_authority": None,
            "transition": None,
            "revocation": None,
        }

    def _active_context(self) -> dict[str, Path | None]:
        return {
            "authority": self.root / "phase2/source-authority.json",
            "bundle": self.active_bundle,
            "rules": self.rules,
            "predictions": self.root / "fixtures/measurement/golden-predictions-v2.json",
            "oracle": self.root / "fixtures/measurement/adversarial/required-diagnostics-v2.json",
            "pending_authority": None,
            "transition": None,
            "revocation": self.root / "receipts/fixture-closure-revocation-v2.json",
        }

    def _active_evidence(self, directory: Path) -> tuple[Path, Path]:
        from specchoice_measurement.cli import (  # noqa: PLC0415
            command_run_adversarial_oracles,
            command_run_formal_measurement,
        )

        formal = directory / "formal-golden-pr2164-v2"
        report = directory / "adversarial-oracle-results-v3.json"
        if not formal.exists():
            context = self._active_context()
            formal_args = SimpleNamespace(
                authority=context["authority"], bundle=context["bundle"], rules=context["rules"],
                schema=self.root / "config/measurement/canonical-adjudication-schema-v1.json",
                predictions=context["predictions"], pending_authority=None, transition=None,
                revocation=context["revocation"], attempt_root=directory, attempt_id=formal.name,
            )
            self.assertEqual(command_run_formal_measurement(formal_args), 0)
            self.assertEqual(command_run_adversarial_oracles(SimpleNamespace(
                authority=context["authority"], bundle=context["bundle"], rules=context["rules"],
                schema=formal_args.schema, predictions=context["predictions"], oracle=context["oracle"],
                pending_authority=None, transition=None, revocation=context["revocation"],
                formal_attempt=formal, report=report,
            )), 0)
        return formal, report

    def _build(self, directory: Path) -> tuple[Path, Path, dict[str, object]]:
        formal, adversarial = self._active_evidence(directory)
        packet_path = directory / "packet" / "packet.json"
        markdown_path = directory / "packet" / "packet.md"
        packet = h1.build_h1_packet(
            formal_attempt=formal,
            adversarial_report=adversarial,
            output_json=packet_path,
            output_markdown=markdown_path,
            schema=self.schema,
            **self._active_context(),
        )
        return packet_path, markdown_path, packet

    def _readiness(self, directory: Path, packet: Path, markdown: Path) -> Path:
        summary = directory / "02-16-SUMMARY-fixture.md"
        summary.write_text("# disposable normalized projection\n", encoding="utf-8")
        readiness = directory / "h1-review-readiness-v3.json"
        h1.write_h1_readiness_v3(
            output=readiness,
            formal_attempt=self._active_evidence(directory)[0],
            adversarial_result=self._active_evidence(directory)[1],
            packet=packet,
            markdown=markdown,
            schema=self.schema,
            source_authority=self._active_context()["authority"],
            canonical_revocation=self._active_context()["revocation"],
            bundle=self.active_bundle,
            rules=self.rules,
            predictions=self._active_context()["predictions"],
            oracle=self._active_context()["oracle"],
            offline_replay=self.replay,
            phase_gate=self.cutover.read_bytes(),
            plan_summary=summary,
        )
        return readiness

    @staticmethod
    def _decision(packet: dict[str, object], readiness: dict[str, object], *, disposition: str = "approved") -> dict[str, object]:
        reviews = []
        for review in packet["fixture_reviews"]:
            assert isinstance(review, dict)
            semantics = {key: value for key, value in review.items() if key != "signature_slot"}
            reviews.append({
                "disposition": "approved",
                "fixture_id": review["fixture_id"],
                "reviewed_semantics_sha256": sha256_bytes(canonical_json_bytes(semantics)),
                "reviewer": "independent-human-reviewer",
                "signature": f"signed:{review['fixture_id']}",
            })
        decision: dict[str, object] = {
            "aggregate_disposition": disposition,
            "bindings": {
                "packet_sha256": packet["packet_sha256"],
                "phase_gate_sha256": readiness["bindings"]["phase_gate_sha256"],
                "readiness_sha256": readiness["readiness_sha256"],
                "schema_sha256": readiness["bindings"]["schema_sha256"],
            },
            "external_publication_authorized": False,
            "fixture_reviews": reviews,
            "reviewer": "independent-human-reviewer",
            "rationale": "independent review completed",
            "semantic_responses": {
                identifier: {"disposition": "approved", "response": "reviewed"}
                for identifier in H1PacketTests.semantic_ids
            },
            "timestamp": "2026-08-02T00:00:00Z",
            "schema_version": "h1-source-gold-decision-v2",
        }
        decision["decision_sha256"] = sha256_bytes(canonical_json_bytes(decision))
        return decision

    def test_packet_is_complete_clean_and_markdown_is_a_pure_projection(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            packet_path, markdown_path, packet = self._build(Path(directory))
            validated = h1.validate_h1_packet(
                packet=packet_path, markdown=markdown_path, schema=self.schema,
                formal_attempt=self._active_evidence(Path(directory))[0],
                adversarial_report=self._active_evidence(Path(directory))[1], **self._active_context(),
            )
            self.assertEqual(validated, packet)
            self.assertEqual(len(packet["fixture_reviews"]), 11)
            self.assertFalse(packet["external_publication_authorized"])
            self.assertEqual(markdown_path.read_text(encoding="utf-8"), h1.render_h1_markdown(packet))

    def test_any_packet_binding_or_markdown_mutation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            root = Path(directory)
            packet_path, markdown_path, packet = self._build(root)
            changed = deepcopy(packet)
            assert isinstance(changed["bindings"], dict)
            changed["bindings"]["golden_predictions_sha256"] = "0" * 64
            changed["packet_sha256"] = sha256_bytes(canonical_json_bytes({key: value for key, value in changed.items() if key != "packet_sha256"}))
            packet_path.write_bytes(canonical_json_bytes(changed))
            with self.assertRaisesRegex(H1Error, "H1_BINDINGS_INVALID"):
                h1.validate_h1_packet(
                    packet=packet_path, markdown=markdown_path, schema=self.schema,
                    formal_attempt=self._active_evidence(root)[0], adversarial_report=self._active_evidence(root)[1],
                    **self._active_context(),
                )
            packet_path.write_bytes(canonical_json_bytes(packet))
            markdown_path.write_text("not a projection\n", encoding="utf-8")
            with self.assertRaisesRegex(H1Error, "H1_MARKDOWN_INVALID"):
                h1.validate_h1_packet(
                    packet=packet_path, markdown=markdown_path, schema=self.schema,
                    formal_attempt=self._active_evidence(root)[0], adversarial_report=self._active_evidence(root)[1],
                    **self._active_context(),
                )

    def test_readiness_is_one_time_and_validator_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            root = Path(directory)
            packet, markdown, _ = self._build(root)
            readiness = self._readiness(root, packet, markdown)
            before = readiness.read_bytes()
            phase_gate = self.cutover.read_bytes()
            self.assertEqual(
                h1.validate_h1_readiness_v3(
                    readiness=readiness, formal_attempt=self._active_evidence(root)[0], adversarial_result=self._active_evidence(root)[1],
                    packet=packet, markdown=markdown, schema=self.schema, source_authority=self._active_context()["authority"],
                    canonical_revocation=self._active_context()["revocation"], offline_replay=self.replay, phase_gate=phase_gate,
                    plan_summary=root / "02-16-SUMMARY-fixture.md", bundle=self.active_bundle, rules=self.rules,
                    predictions=self._active_context()["predictions"], oracle=self._active_context()["oracle"],
                )["readiness_sha256"],
                json.loads(before)["readiness_sha256"],
            )
            self.assertEqual(readiness.read_bytes(), before)
            with self.assertRaisesRegex(H1Error, "H1_READINESS_EXISTS"):
                self._readiness(root, packet, markdown)

    def test_v2_decision_validator_checks_closed_human_contract_without_authoring(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            root = Path(directory)
            packet_path, markdown_path, packet = self._build(root)
            readiness_path = self._readiness(root, packet_path, markdown_path)
            readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
            decision = self._decision(packet, readiness)
            decision_path = root / "decision.json"
            decision_path.write_bytes(canonical_json_bytes(decision))
            receipt = h1.validate_h1_decision_v2(
                schema=self.schema, packet=packet_path, readiness=readiness_path, decision=decision_path
            )
            self.assertEqual(receipt["fixture_count"], 11)
            self.assertEqual(receipt["aggregate_disposition"], "approved")
            self.assertFalse(receipt["external_publication_authorized"])

            for binding in ("packet_sha256", "schema_sha256"):
                with self.subTest(binding=binding):
                    detached_readiness = deepcopy(readiness)
                    assert isinstance(detached_readiness["bindings"], dict)
                    detached_readiness["bindings"][binding] = "0" * 64
                    detached_readiness["readiness_sha256"] = sha256_bytes(canonical_json_bytes({
                        key: value for key, value in detached_readiness.items() if key != "readiness_sha256"
                    }))
                    detached_decision = deepcopy(decision)
                    assert isinstance(detached_decision["bindings"], dict)
                    detached_decision["bindings"]["readiness_sha256"] = detached_readiness["readiness_sha256"]
                    detached_decision["decision_sha256"] = sha256_bytes(canonical_json_bytes({
                        key: value for key, value in detached_decision.items() if key != "decision_sha256"
                    }))
                    readiness_path.write_bytes(canonical_json_bytes(detached_readiness))
                    decision_path.write_bytes(canonical_json_bytes(detached_decision))
                    with self.assertRaisesRegex(H1Error, "H1_READINESS_BINDINGS_INVALID"):
                        h1.validate_h1_decision_v2(
                            schema=self.schema, packet=packet_path, readiness=readiness_path, decision=decision_path
                        )

            questions_path = self.root / "config/measurement/h1-semantic-review-questions-v2.json"
            schema_v4 = self.root / "config/measurement/h1-review-schema-v4.json"
            questions = json.loads(questions_path.read_text(encoding="utf-8"))
            golden = json.loads((self.root / "fixtures/measurement/golden-predictions-v4.json").read_text(encoding="utf-8"))
            successor_packet: dict[str, object] = {
                "bindings": {},
                "external_publication_authorized": False,
                "fixture_reviews": h1._successor_fixture_reviews(golden),
                "schema_version": "h1-source-gold-review-v6",
                "semantic_questions": questions["questions"],
            }
            successor_packet["packet_sha256"] = sha256_bytes(canonical_json_bytes(successor_packet))
            successor_packet_path = root / "successor-packet.json"
            successor_packet_path.write_bytes(canonical_json_bytes(successor_packet))
            successor_readiness: dict[str, object] = {
                "bindings": {"packet_file_sha256": sha256_bytes(successor_packet_path.read_bytes())},
                "external_publication_authorized": False,
                "schema_version": "h1-semantic-readiness-v6",
            }
            successor_readiness["readiness_sha256"] = sha256_bytes(canonical_json_bytes(successor_readiness))
            successor_readiness_path = root / "successor-readiness.json"
            successor_readiness_path.write_bytes(canonical_json_bytes(successor_readiness))
            schema_result = h1.validate_h1_review_schema_v4(
                schema=schema_v4, questions=questions_path
            )
            successor_decision: dict[str, object] = {
                "aggregate_disposition": "approved",
                "bindings": {
                    "packet_sha256": successor_packet["packet_sha256"],
                    "questions_sha256": schema_result["questions_sha256"],
                    "readiness_sha256": successor_readiness["readiness_sha256"],
                    "schema_sha256": schema_result["schema_sha256"],
                },
                "external_publication_authorized": False,
                "fixture_reviews": [
                    {
                        "disposition": "approved",
                        "fixture_id": review["fixture_id"],
                        "rationale": "I reviewed this fixture's frozen semantics.",
                        "reviewed_semantics_sha256": review["reviewed_semantics_sha256"],
                        "signature": f"human:{review['fixture_id']}",
                    }
                    for review in successor_packet["fixture_reviews"]
                ],
                "rationale": "I reviewed all fixture and question semantics.",
                "responses": [
                    {
                        "disposition": "approved",
                        "fixture_signoffs": [
                            {"disposition": "approved", "fixture_id": fixture_id, "signature": f"human:{question['id']}:{fixture_id}"}
                            for fixture_id in question["fixture_ids"]
                        ],
                        "question_id": question["id"],
                        "rationale": "The expected semantics and machine assertions are correct.",
                        "response": "approve_expected_semantics",
                    }
                    for question in successor_packet["semantic_questions"]
                ],
                "reviewer_identity": "independent-human-reviewer",
                "schema_version": "h1-source-gold-decision-v5",
                "signature": "human:all-seven-questions",
                "timestamp": "2026-08-03T00:00:00Z",
            }
            successor_decision["decision_sha256"] = sha256_bytes(canonical_json_bytes(successor_decision))
            successor_decision_path = root / "successor-decision.json"
            successor_decision_path.write_bytes(canonical_json_bytes(successor_decision))
            self.assertEqual(
                h1.validate_h1_semantic_review_decision(
                    schema=schema_v4,
                    questions=questions_path,
                    packet=successor_packet_path,
                    readiness=successor_readiness_path,
                    decision=successor_decision_path,
                )["questions"],
                7,
            )
            placeholder = deepcopy(successor_decision)
            placeholder["responses"][0]["response"] = "reviewed"
            placeholder["decision_sha256"] = sha256_bytes(canonical_json_bytes({
                key: item for key, item in placeholder.items() if key != "decision_sha256"
            }))
            successor_decision_path.write_bytes(canonical_json_bytes(placeholder))
            with self.assertRaisesRegex(H1Error, "H1_SEMANTIC_RESPONSES_INVALID"):
                h1.validate_h1_semantic_review_decision(
                    schema=schema_v4, questions=questions_path, packet=successor_packet_path,
                    readiness=successor_readiness_path, decision=successor_decision_path,
                )
            inconsistent = deepcopy(successor_decision)
            inconsistent["responses"][0]["response"] = "reject_expected_semantics"
            inconsistent["responses"][0]["disposition"] = "disputed"
            for signoff in inconsistent["responses"][0]["fixture_signoffs"]:
                signoff["disposition"] = "disputed"
            inconsistent["decision_sha256"] = sha256_bytes(canonical_json_bytes({
                key: item for key, item in inconsistent.items() if key != "decision_sha256"
            }))
            successor_decision_path.write_bytes(canonical_json_bytes(inconsistent))
            with self.assertRaisesRegex(H1Error, "H1_DISPUTE_AGGREGATION_INVALID"):
                h1.validate_h1_semantic_review_decision(
                    schema=schema_v4, questions=questions_path, packet=successor_packet_path,
                    readiness=successor_readiness_path, decision=successor_decision_path,
                )
            with self.assertRaisesRegex(H1Error, "H1_REVIEW_SCHEMA_V4_INVALID"):
                h1.validate_h1_semantic_review_decision(
                    schema=self.root / "config/measurement/h1-review-schema-v3.json",
                    questions=questions_path, packet=successor_packet_path,
                    readiness=successor_readiness_path, decision=successor_decision_path,
                )

    def test_incomplete_or_disputed_leaf_must_match_aggregate(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            root = Path(directory)
            packet_path, markdown_path, packet = self._build(root)
            readiness_path = self._readiness(root, packet_path, markdown_path)
            readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
            decision = self._decision(packet, readiness)
            assert isinstance(decision["fixture_reviews"], list)
            assert isinstance(decision["fixture_reviews"][0], dict)
            decision["fixture_reviews"][0]["disposition"] = "disputed"
            decision["decision_sha256"] = sha256_bytes(canonical_json_bytes({key: value for key, value in decision.items() if key != "decision_sha256"}))
            decision_path = root / "decision.json"
            decision_path.write_bytes(canonical_json_bytes(decision))
            with self.assertRaisesRegex(H1Error, "H1_DISPUTE_AGGREGATION_INVALID"):
                h1.validate_h1_decision_v2(schema=self.schema, packet=packet_path, readiness=readiness_path, decision=decision_path)

    def test_public_h1_validators_cover_packet_markdown_readiness_decision_schema_and_retained_roles(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            root = Path(directory)
            packet_path, markdown_path, packet = self._build(root)
            readiness_path = self._readiness(root, packet_path, markdown_path)
            readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
            decision_path = root / "decision.json"
            decision_path.write_bytes(canonical_json_bytes(self._decision(packet, readiness)))
            self.assertEqual(
                h1.validate_h1_decision_v2(schema=self.schema, packet=packet_path, readiness=readiness_path, decision=decision_path)["valid"],
                True,
            )
            for path in (packet_path, markdown_path, readiness_path, decision_path, self.schema, self.formal / "attempt.json", self.adversarial):
                self.assertTrue(path.is_file(), path)

    def test_public_h1_reuses_validated_attempt_and_adversarial_objects_without_reopen(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.root) as directory:
            root = Path(directory)
            packet_path, markdown_path, packet = self._build(root)
            self.assertEqual(
                h1.validate_h1_packet(
                    packet=packet_path, markdown=markdown_path, schema=self.schema,
                    formal_attempt=self._active_evidence(root)[0], adversarial_report=self._active_evidence(root)[1],
                    **self._active_context(),
                )["bindings"],
                packet["bindings"],
            )
            legacy = h1.build_h1_packet(
                formal_attempt=self.formal,
                adversarial_report=self.adversarial,
                output_json=root / "legacy" / "packet.json",
                output_markdown=root / "legacy" / "packet.md",
                schema=self.schema,
                **self._legacy_context(root),
            )
            self.assertEqual(legacy["bindings"]["formal_attempt_sha256"], json.loads(
                (self.formal / "attempt.json").read_text(encoding="utf-8")
            )["attempt_sha256"])


if __name__ == "__main__":
    unittest.main()
