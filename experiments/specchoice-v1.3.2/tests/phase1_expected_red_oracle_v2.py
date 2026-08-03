# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Phase-aware oracle: retain the legacy red cohort and require successor green."""

from __future__ import annotations

import subprocess
import sys
import unittest


def main() -> int:
    legacy = subprocess.run(
        [sys.executable, "-B", "tests/phase1_expected_red_oracle.py", "--expected-focused", "72", "--expected-discovered", "150", "--expected-green", "145"],
        check=False,
    )
    if legacy.returncode:
        return legacy.returncode
    suite = unittest.defaultTestLoader.loadTestsFromNames((
        "tests.test_fixture_closure.FixtureClosureTests.test_v6_preflight_reconstructs_target_inventory_before_any_write",
        "tests.test_fixture_closure.FixtureClosureTests.test_v5_executable_closure_and_candidate_entrypoints",
        "tests.test_fixture_closure.FixtureClosureTests.test_v12_acceptance_and_cutover_entrypoints",
    ))
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
