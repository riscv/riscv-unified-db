#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

from __future__ import annotations

import argparse
import itertools
import re

import spec

RANGE_PATTERN = re.compile(r"^(-?\d+)(?:-(-?\d+))?$")


def _extract_possible_values(possible_values: object) -> list[object]:
    if isinstance(possible_values, list):
        return possible_values
    if possible_values is None:
        return []
    return [possible_values]


def _range_endpoints(raw_value: str) -> list[int] | None:
    match = RANGE_PATTERN.fullmatch(raw_value.strip())
    if not match:
        return None

    start = int(match.group(1))
    end = int(match.group(2)) if match.group(2) is not None else start
    if start == end:
        return [start]
    return [start, end]


def load_yaml_objects(spec_dir: str) -> dict[str, dict[str, dict]]:
    """Load supported YAML objects from spec_dir and return instruction/register-file maps."""
    spec.initialize_spec(spec_dir)
    return {"instructions": spec.instructions, "register_files": spec.register_files}


def _register_names_for_operand(operand: dict, operand_name: str) -> list[object]:
    reg_file_name = operand.get("reg_file")
    if not isinstance(reg_file_name, str):
        raise ValueError(f"Register operand is missing 'reg_file': {operand}")

    index_to_name = spec.register_name_by_index.get(reg_file_name)
    if not index_to_name:
        return [f"<{operand_name}>"]

    possible_values = _extract_possible_values(operand.get("possible_values"))
    if not possible_values:
        return [index_to_name[idx] for idx in sorted(index_to_name)]

    resolved_names: list[object] = []
    for value in possible_values:
        if isinstance(value, int):
            if value in index_to_name:
                resolved_names.append(index_to_name[value])
            else:
                resolved_names.append(str(value))
        elif isinstance(value, str):
            endpoints = _range_endpoints(value)
            if endpoints is None:
                resolved_names.append(value)
                continue
            for reg_index in endpoints:
                if reg_index in index_to_name:
                    resolved_names.append(index_to_name[reg_index])
        else:
            resolved_names.append(value)

    return resolved_names or [f"<{operand_name}>"]


def _non_register_values_for_operand(operand: dict, operand_name: str) -> list[object]:
    possible_values = _extract_possible_values(operand.get("possible_values"))
    if possible_values:
        expanded_values: list[object] = []
        for value in possible_values:
            if isinstance(value, str):
                endpoints = _range_endpoints(value)
                if endpoints is not None:
                    expanded_values.extend(endpoints)
                    continue
            expanded_values.append(value)
        return expanded_values

    return [f"<{operand_name}>"]


def _operand_values(operand: dict, operand_name: str) -> list[object]:
    operand_type = operand.get("type")
    if operand_type in ["register", "register_pair"]:
        values = _register_names_for_operand(operand, operand_name)
    else:
        values = _non_register_values_for_operand(operand, operand_name)

    if operand.get("optional"):
        return ["", *values]
    return values


def _extract_operand_list(instruction: dict) -> list[dict]:
    """Extract a concrete operand list from instruction['operands']."""
    operands = instruction.get("operands")
    if isinstance(operands, list):
        return operands

    # Some instructions carry xlen-specific operand variants.
    if isinstance(operands, dict):
        for preferred_key in ("RV64", "RV32"):
            preferred = operands.get(preferred_key)
            if isinstance(preferred, list):
                return preferred
        for value in operands.values():
            if isinstance(value, list):
                return value

    raise ValueError(f"Instruction '{instruction.get('name', '<unknown>')}' has no operand list")


def list_instruction_operand_combinations(instruction_name: str) -> list[dict[str, object]]:
    """Return all instruction+operand combinations for one instruction."""
    instruction = spec.instructions.get(instruction_name)
    if not isinstance(instruction, dict):
        raise KeyError(f"Instruction '{instruction_name}' not found")

    operands = _extract_operand_list(instruction)

    operand_names: list[str] = []
    operand_values: list[list[object]] = []

    for operand in operands:
        if not isinstance(operand, dict):
            continue
        operand_name = operand.get("name")
        if not isinstance(operand_name, str):
            continue

        values = _operand_values(operand, operand_name)
        operand_names.append(operand_name)
        operand_values.append(values)

        offset = operand.get("offset")
        if isinstance(offset, dict):
            offset_name = offset.get("name")
            if isinstance(offset_name, str) and offset_name and offset_name not in operand_names:
                operand_names.append(offset_name)
                operand_values.append(_non_register_values_for_operand(offset, offset_name))

    combinations: list[dict[str, object]] = []
    for value_tuple in itertools.product(*operand_values):
        combinations.append(
            {
                "instruction": instruction_name,
                "operands": dict(zip(operand_names, value_tuple, strict=True)),
            }
        )

    return combinations


def render_instruction_combination(combo: dict[str, object]) -> str:
    """Render one instruction+operands combination using assembly-like operand formatting."""
    instruction_name = combo["instruction"]
    instruction = spec.instructions.get(instruction_name)
    if not isinstance(instruction, dict):
        raise KeyError(f"Instruction '{instruction_name}' not found")

    operand_map = combo["operands"]
    if not isinstance(operand_map, dict):
        raise ValueError("Combination is missing operand mapping")

    operands = _extract_operand_list(instruction)
    rendered_operands: list[str] = []
    consumed_offset_names: set[str] = set()

    for operand in operands:
        if not isinstance(operand, dict):
            continue

        operand_name = operand.get("name")
        if not isinstance(operand_name, str):
            continue

        value = operand_map.get(operand_name, "")
        if value == "":
            # Optional operands are omitted when empty.
            continue

        offset = operand.get("offset")
        if isinstance(offset, dict):
            offset_name = offset.get("name")
            if isinstance(offset_name, str) and offset_name:
                offset_value = operand_map.get(offset_name, "")
                consumed_offset_names.add(offset_name)
                rendered_operands.append(f"{offset_value}({value})")
            else:
                rendered_operands.append(f"({value})")
            continue

        rendered_operands.append(str(value))

    # Include stand-alone operands that were not part of the primary operand list render.
    for name, value in operand_map.items():
        if name in consumed_offset_names:
            continue
        if value == "":
            continue
        if any(isinstance(op, dict) and op.get("name") == name for op in operands):
            continue
        rendered_operands.append(str(value))

    if rendered_operands:
        return f"{instruction_name} " + ", ".join(rendered_operands)
    return instruction_name


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List instruction/operand combinations from resolved YAML objects."
    )
    parser.add_argument(
        "--spec",
        required=True,
        help="Root directory to recursively scan for YAML files",
    )
    parser.add_argument("instructions", nargs="*", help="Instruction names to generate")
    args = parser.parse_args()

    spec.initialize_spec(args.spec)
    instruction_names = args.instructions or sorted(spec.instructions)

    had_error = False
    try:
        for instruction_name in instruction_names:
            try:
                combos = list_instruction_operand_combinations(instruction_name)
            except KeyError:
                print(f"# ERROR: Instruction '{instruction_name}' not found")
                had_error = True
                continue

            for combo in combos:
                print(render_instruction_combination(combo))
    except BrokenPipeError:
        return 0

    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
