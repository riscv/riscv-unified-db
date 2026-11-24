# SPDX-FileCopyrightText: 2026 Contributors to the RISCV UnifiedDB <https://github.com/riscv/riscv-unified-db>
# SPDX-License-Identifier: BSD-3-Clause-Clear

"""Add repository data to the sdist and to standard wheels.

The sdist keeps the repository paths. The wheel puts them under ``udb/_data``.
Editable installs get no copy; they read the checkout directly.
"""

from __future__ import annotations

from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

# Repository-relative files and directories. The wheel keeps the same relative paths.
DATA_PATHS = (
    "spec/std/isa",
    "spec/schemas",
    "spec/custom/isa/qc_iu",
    "cfgs/_.yaml",
    "cfgs/rv32.yaml",
    "cfgs/rv64.yaml",
    "src/udb/cpp_hart/runtime/CMakeLists.txt",
    "src/udb/cpp_hart/runtime/c",
    "src/udb/cpp_hart/runtime/cpp/include",
    "src/udb/cpp_hart/runtime/cpp/src",
    "src/udb/cpp_hart/runtime/gdb",
    "src/udb/cpp_hart/runtime/renode",
    ".toolchain/check_cxx.cmake",
    ".toolchain/.build-elfutils.sh",
    "LICENSE-BSD-3-Clause-Clear.txt",
    "LICENSE-CC-BY.txt",
    "LICENSE-MIT.txt",
    "LICENSES/BSD-2-Clause.txt",
    "NOTICE",
)


class CustomBuildHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        if version == "editable":
            return
        prefix = "udb/_data/" if self.target_name == "wheel" else ""
        force_include = build_data.setdefault("force_include", {})
        for path in DATA_PATHS:
            force_include[path] = prefix + path
