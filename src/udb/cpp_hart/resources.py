# SPDX-FileCopyrightText: 2026 Contributors to the RISCV UnifiedDB <https://github.com/riscv/riscv-unified-db>
# SPDX-License-Identifier: BSD-3-Clause-Clear

"""Static C++ runtime resources copied into generated hart builds."""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from udb.resources import package_data_root

from .types import CppGenerationError

__all__ = ["RuntimeResources", "renode_repl", "standalone_cmake"]

RUNTIME_SOURCE = PurePosixPath("src/udb/cpp_hart/runtime")
GROUPS = {
    "cpp/include/udb": ("include/udb", {".hpp"}),
    "c/include/udb": ("include/udb", {".h"}),
    "cpp/src": ("src", {".cpp"}),
    "gdb": ("gdb", {".xml"}),
    "renode": ("renode", {".cs", ".repl", ".resc"}),
}
SUPPORT = (
    "LICENSE-BSD-3-Clause-Clear.txt",
    "LICENSE-MIT.txt",
    "LICENSE-CC-BY.txt",
    "LICENSES/BSD-2-Clause.txt",
    "NOTICE",
    ".toolchain/check_cxx.cmake",
    ".toolchain/.build-elfutils.sh",
)
# Native unit tests exist only in a checkout; the wheel does not ship them.
TEST_GROUP = ("cpp/test", "test", {".cmake", ".cpp", ".hpp"})
TEST_SUPPORT = (
    "cfgs/rv64-riscv-tests.yaml",
    "tests/data/fp/directed/f32_fpgen_expanded.jsonl",
)


def resource_entries(root: Any) -> Iterator[tuple[PurePosixPath, int, PurePosixPath]]:
    """Yield (generated relative path, mode, repository-relative source path)."""
    runtime_root = root.joinpath(*RUNTIME_SOURCE.parts)
    if not runtime_root.joinpath("CMakeLists.txt").is_file():
        raise ValueError(f"Runtime resources lack {RUNTIME_SOURCE}/CMakeLists.txt")
    yield PurePosixPath("CMakeLists.txt"), 0o644, RUNTIME_SOURCE / "CMakeLists.txt"
    groups = [(source, *target) for source, target in GROUPS.items()]
    support = list(SUPPORT)
    if runtime_root.joinpath(TEST_GROUP[0]).is_dir():
        groups.append(TEST_GROUP)
        support.extend(TEST_SUPPORT)
    for source, destination, suffixes in groups:
        directory = runtime_root.joinpath(source)
        if not directory.is_dir():
            raise ValueError(f"Runtime resources lack {RUNTIME_SOURCE / source}")
        for file in sorted(directory.iterdir(), key=lambda file: file.name):
            if file.is_file() and PurePosixPath(file.name).suffix in suffixes:
                yield (
                    PurePosixPath(destination) / file.name,
                    0o644,
                    RUNTIME_SOURCE / source / file.name,
                )
    for source in support:
        if not root.joinpath(source).is_file():
            raise ValueError(f"Runtime resources lack {source}")
        yield (
            PurePosixPath(source),
            0o755 if source.endswith(".sh") else 0o644,
            PurePosixPath(source),
        )


@dataclass(frozen=True)
class RuntimeResources:
    """A root that holds runtime files at repository-relative paths."""

    root: Any

    @classmethod
    def bundled(cls):
        """Use the checkout in-tree, or the copy in an installed wheel."""
        return cls(package_data_root())

    @classmethod
    def from_path(cls, root: str | Path):
        path = Path(root)
        if not path.is_dir():
            raise CppGenerationError(f"Missing explicit runtime resource root: {root}")
        return cls(path)

    def files(self):
        try:
            for output, mode, source in resource_entries(self.root):
                yield output, self.root.joinpath(*source.parts).read_bytes(), mode, source
        except ValueError as error:
            raise CppGenerationError(str(error)) from error


def standalone_cmake(
    content: bytes, config_names: tuple[str, ...], build_type: str = "RelWithDebInfo"
) -> bytes:
    text = content.decode("utf-8")
    old = """if(NOT DEFINED UDB_ROOT OR UDB_ROOT STREQUAL "")
  get_filename_component(UDB_ROOT "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
endif()"""
    new = """if(NOT DEFINED UDB_ROOT OR UDB_ROOT STREQUAL "")
  if(EXISTS "${CMAKE_CURRENT_LIST_DIR}/.toolchain/check_cxx.cmake")
    set(UDB_ROOT "${CMAKE_CURRENT_LIST_DIR}")
  else()
    get_filename_component(UDB_ROOT "${CMAKE_CURRENT_LIST_DIR}/../.." ABSOLUTE)
  endif()
endif()"""
    if old not in text:
        raise CppGenerationError("Unrecognized runtime CMake UDB_ROOT contract")
    text = text.replace(old, new, 1)
    build_default = "SET(CMAKE_BUILD_TYPE RelWithDebInfo"
    if build_default not in text:
        raise CppGenerationError("Unrecognized runtime CMake build-type contract")
    if build_type not in {"Debug", "RelWithDebInfo", "Release", "Asan"}:
        raise CppGenerationError(f"Unsupported runtime CMake build type {build_type!r}")
    text = text.replace(build_default, f"SET(CMAKE_BUILD_TYPE {build_type}", 1)
    configs = ";".join(config_names)
    text = f'if(NOT DEFINED CONFIG_LIST)\n  set(CONFIG_LIST "{configs}")\nendif()\n' + text
    return text.encode("utf-8")


def renode_repl(content: bytes, config: str) -> bytes:
    """Bind the portable Renode example to the first generated model."""
    text = content.decode("utf-8")
    for marker in ("@UDB_MODEL@", "@UDB_CONFIG@"):
        if text.count(marker) != 1:
            raise CppGenerationError(f"Renode platform must contain exactly one {marker}")
        text = text.replace(marker, config)
    return text.encode("utf-8")
