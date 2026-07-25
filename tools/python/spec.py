# SPDX-FileCopyrightText: Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

yamls: list[dict] = []
instructions: dict[str, dict] = {}
register_files: dict[str, dict] = {}

# Shared derived maps built during initialize_spec().
register_name_to_index: dict[str, dict[str, int]] = {}
register_name_by_index: dict[str, dict[int, str]] = {}
register_abi_name_by_index: dict[str, dict[int, str]] = {}


def _qprint(message: str, quiet: bool) -> None:
    if not quiet:
        print(message)


def _register_abi_name(register_entry: dict) -> str | None:
    abi_name = register_entry.get("abi_name")
    if isinstance(abi_name, str):
        return abi_name

    abi_mnemonics = register_entry.get("abi_mnemonics", [])
    if isinstance(abi_mnemonics, list):
        for value in abi_mnemonics:
            return value
    return None


def get_stanza(block, xlen):
    rvtag = f"RV{xlen}"
    if not block or rvtag not in block:
        return block
    return block[rvtag]


def initialize_spec(spec_dir: str, quiet: bool = False) -> None:
    """
    Load all relevant YAML objects and build shared lookup maps.
    """
    yaml = YAML(typ="safe")
    yamls.clear()
    instructions.clear()
    register_files.clear()
    register_name_to_index.clear()
    register_name_by_index.clear()
    register_abi_name_by_index.clear()

    root_path = Path(spec_dir)
    for yaml_path in root_path.rglob("*.yaml"):
        try:
            with yaml_path.open(encoding="utf-8") as handle:
                data = yaml.load(handle)
        except (OSError, yaml.YAMLError):
            print(f'# ERROR: Failed to load "{yaml_path}".')
            continue

        if not isinstance(data, dict):
            _qprint(f'# WARNING: Unexpected data in "{yaml_path}".', quiet)
            continue

        kind = data.get("kind")
        if not isinstance(kind, str):
            _qprint(f"# WARNING: No 'kind' field in {yaml_path}", quiet)
            continue

        name = data.get("name")
        if not isinstance(name, str) or not name:
            _qprint(f'# WARNING: Unexpected data in "{yaml_path}".', quiet)
            continue

        data["file"] = yaml_path
        yamls.append(data)

        if kind == "instruction":
            # Keep only instructions with "operand" data, or no variables
            if "operands" in data:
                instructions[name] = data
                continue
            encoding = data.get("encoding")
            if encoding is None:
                # no "operands" or "encoding", must be "format": skip for now
                continue
            if "RV64" in encoding:
                # XLEN-specific encoding: just pick one for now
                encoding = encoding.get("RV64")
            match = encoding.get("match")
            if "-" in match:
                # variables, but no operands: skip for now
                continue
            instructions[name] = data
        elif kind == "register_file":
            register_files[name] = data

    for regfile_name, regfile_data in register_files.items():
        registers = regfile_data.get("registers", [])
        if not isinstance(registers, list):
            continue

        idx_to_name: dict[int, str] = {}
        name_to_idx: dict[str, int] = {}
        idx_to_abi: dict[int, str] = {}

        for index, register_entry in enumerate(registers):
            if not isinstance(register_entry, dict):
                continue

            reg_name = register_entry.get("name")
            if isinstance(reg_name, str):
                idx_to_name[index] = reg_name
                name_to_idx[reg_name.lower()] = index

            abi_mnemonics = register_entry.get("abi_mnemonics", [])
            if isinstance(abi_mnemonics, list):
                for abi_name in abi_mnemonics:
                    if isinstance(abi_name, str):
                        name_to_idx[abi_name.lower()] = index

            abi_name = _register_abi_name(register_entry)
            if isinstance(abi_name, str):
                idx_to_abi[index] = abi_name

        register_name_to_index[regfile_name] = name_to_idx
        register_name_by_index[regfile_name] = idx_to_name
        register_abi_name_by_index[regfile_name] = idx_to_abi
