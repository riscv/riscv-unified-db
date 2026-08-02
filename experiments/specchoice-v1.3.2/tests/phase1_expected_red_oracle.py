# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Exact, non-discovered semantic gate for the Phase 1 expected-red partition."""

from __future__ import annotations

import argparse
import io
import json
import sys
import tempfile
import unittest

from specchoice_evidence.canonical import canonical_json_bytes


RED_IDS = {
    "tests.test_fixture_closure.FixtureClosureCandidateTests.test_fixture_candidate_publish_rejects_racing_empty_target_without_overwrite",
    "tests.test_fixture_closure.FixtureClosureCandidateTests.test_fixture_publish_fails_closed_when_no_replace_primitive_is_unavailable",
    "tests.test_fixture_closure.FixtureClosureCandidateTests.test_public_fixture_acceptance_rejects_missing_mismatched_and_stale_authority",
    "tests.test_fixture_closure.FixtureClosureCandidateTests.test_public_fixture_acceptance_rejects_current_boundary_violation",
    "tests.test_receipts.IntegrityReceiptTests.test_active_defaults_are_v7_from_experiment_and_repository_roots",
}

FOCUSED_MODULES = (
    "tests.test_measurement_adapter",
    "tests.test_measurement_parsing",
    "tests.test_measurement_scoring",
    "tests.test_measurement_attempts",
    "tests.test_measurement_h1",
    "tests.test_filesystem_boundary",
)


class _Capture:
    def __init__(self) -> None:
        self.binary = tempfile.TemporaryFile(mode="w+b")
        self.text = io.TextIOWrapper(self.binary, encoding="utf-8", newline="\n")

    def close(self) -> str:
        self.text.flush()
        self.binary.seek(0)
        value = self.binary.read().decode("utf-8", "replace")
        self.text.detach()
        self.binary.close()
        return value


def _flatten(suite: unittest.TestSuite) -> list[unittest.TestCase]:
    tests: list[unittest.TestCase] = []
    for item in suite:
        tests.extend(_flatten(item) if isinstance(item, unittest.TestSuite) else [item])
    return tests


def _run(tests: list[unittest.TestCase]) -> tuple[unittest.TestResult, str]:
    capture = _Capture()
    result = unittest.TextTestRunner(stream=capture.text, verbosity=0).run(unittest.TestSuite(tests))
    return result, capture.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-focused", required=True, type=int)
    parser.add_argument("--expected-discovered", required=True, type=int)
    parser.add_argument("--expected-green", required=True, type=int)
    args = parser.parse_args()
    loader = unittest.defaultTestLoader
    discovered = _flatten(loader.discover("tests", top_level_dir="."))
    focused = _flatten(unittest.TestSuite(loader.loadTestsFromName(name) for name in FOCUSED_MODULES))
    ids = {test.id() for test in discovered}
    if len(focused) != args.expected_focused or len(discovered) != args.expected_discovered or RED_IDS - ids or len(RED_IDS) != 5:
        raise SystemExit("ORACLE_DISCOVERY_PARTITION_INVALID")
    green = [test for test in discovered if test.id() not in RED_IDS]
    green_result, green_output = _run(green)
    if green_result.testsRun != args.expected_green or not green_result.wasSuccessful() or green_result.skipped or green_result.expectedFailures or green_result.unexpectedSuccesses:
        print(green_output, file=sys.stderr, end="")
        raise SystemExit("ORACLE_GREEN_PARTITION_INVALID")
    red = [test for test in discovered if test.id() in RED_IDS]
    red_result, red_output = _run(red)
    if red_result.testsRun != 5 or len(red_result.failures) != 5 or len(red_result.errors) != 1 or red_result.skipped or red_result.expectedFailures or red_result.unexpectedSuccesses:
        print(red_output, file=sys.stderr, end="")
        raise SystemExit("ORACLE_RED_OUTCOMES_INVALID")
    sys.stdout.buffer.write(canonical_json_bytes({
        "discovered": len(discovered), "focused": len(focused), "green": len(green),
        "red_ids": sorted(RED_IDS), "status": "phase1_expected_red_oracle_passed",
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
