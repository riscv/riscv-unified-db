# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Phase-aware oracle: retain the legacy red cohort and require successor green."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import phase1_expected_red_oracle as legacy


SUCCESSOR_IDS = {
    "tests.test_fixture_closure.FixtureClosureTests.test_v5_executable_closure_and_candidate_entrypoints",
    "tests.test_fixture_closure.FixtureClosureTests.test_runtime_closure_builder_is_sorted_and_rejects_any_one_byte_drift",
    "tests.test_fixture_closure.FixtureClosureTests.test_v5_construction_decision_rejects_every_transitive_one_byte_drift_before_write",
    "tests.test_fixture_closure.FixtureClosureTests.test_v12_acceptance_and_cutover_entrypoints",
    "tests.test_fixture_closure.FixtureClosureTests.test_v5_registry_manifest_and_every_repair_payload_are_pre_freeze_committed_inputs",
    "tests.test_fixture_closure.FixtureClosureTests.test_v6_preflight_reconstructs_target_inventory_before_any_write",
    "tests.test_measurement_adapter.MeasurementAdapterTests.test_exact_eleven_case_metric_population_contract",
    "tests.test_measurement_adapter.MeasurementAdapterTests.test_v5_outcome_contract_rejects_candidate_identity_leakage",
    "tests.test_measurement_scoring.MeasurementScoringTests.test_v5_span_population_is_frozen",
    "tests.test_measurement_h1.H1PublicContractTests.test_v5_h1_question_contract_is_exactly_seven_questions",
    "tests.test_measurement_h1.H1PacketTests.test_seven_question_h1_and_four_report_pipeline",
    "tests.test_measurement_h1.H1PacketTests.test_report_generation_rejects_one_byte_planning_or_predecessor_report_drift_before_write",
}


def main() -> int:
    loader = unittest.defaultTestLoader
    discovered = [test for test in legacy._flatten(loader.discover("tests", top_level_dir=".")) if test.id() not in SUCCESSOR_IDS]
    focused = [test for test in legacy._flatten(unittest.TestSuite(loader.loadTestsFromName(name) for name in legacy.FOCUSED_MODULES)) if test.id() not in SUCCESSOR_IDS]
    if len(discovered) != 150 or len(focused) != 72:
        raise SystemExit("ORACLE_LEGACY_COHORT_CHANGED")
    green = [test for test in discovered if test.id() not in legacy.RED_IDS]
    result, _ = legacy._run(green)
    if result["tests_run"] != 145 or result["failures"] or result["errors"] or result["skipped"]:
        raise SystemExit("ORACLE_LEGACY_GREEN_CHANGED")
    red, _ = legacy._run([test for test in discovered if test.id() in legacy.RED_IDS])
    if legacy._normalized_outcomes(red) is None:
        raise SystemExit("ORACLE_LEGACY_RED_CHANGED")
    suite = unittest.defaultTestLoader.loadTestsFromNames(tuple(sorted(SUCCESSOR_IDS)))
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
