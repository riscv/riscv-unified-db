# SPDX-FileCopyrightText: 2026 Contributors to the RISCV UnifiedDB <https://github.com/riscv/riscv-unified-db>
# SPDX-License-Identifier: BSD-3-Clause-Clear

import importlib.util
from pathlib import Path

from udb import Database
from udb.cpp_hart.resources import RUNTIME_SOURCE, RuntimeResources
from udb.resources import package_data_root

REPOSITORY_ROOT = Path(__file__).parents[2]
BUILD_HOOK_SPEC = importlib.util.spec_from_file_location(
    "hatch_build", REPOSITORY_ROOT / "hatch_build.py"
)
assert BUILD_HOOK_SPEC is not None and BUILD_HOOK_SPEC.loader is not None
BUILD_HOOK = importlib.util.module_from_spec(BUILD_HOOK_SPEC)
BUILD_HOOK_SPEC.loader.exec_module(BUILD_HOOK)
DATA_PATHS = BUILD_HOOK.DATA_PATHS


def test_checkout_reads_repository_data_directly() -> None:
    assert package_data_root() == REPOSITORY_ROOT
    database = Database.bundled()
    assert database.isa_root == REPOSITORY_ROOT / "spec/std/isa"
    assert database.extension("Zvkg").name == "Zvkg"


def test_wheel_data_paths_exist() -> None:
    assert all((REPOSITORY_ROOT / path).exists() for path in DATA_PATHS)
    assert "spec/custom/isa/qc_iu" in DATA_PATHS


def test_wheel_data_paths_cover_runtime_resources_without_tests() -> None:
    def shipped(source: str) -> bool:
        return any(source == path or source.startswith(f"{path}/") for path in DATA_PATHS)

    sources = [str(origin) for *_, origin in RuntimeResources.from_path(REPOSITORY_ROOT).files()]
    tests = (str(RUNTIME_SOURCE / "cpp/test/"), "tests/", "cfgs/rv64-riscv-tests.yaml")
    assert all(shipped(source) for source in sources if not source.startswith(tests))
    assert not any(shipped(source) for source in sources if source.startswith(tests))
