#!/usr/bin/env python3
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
import argparse
import re
import sys

import idl

import spec

operand_list = []
debug = False
quiet = False


def parse_args():
    parser = argparse.ArgumentParser(description="Process RISC-V instruction definitions")
    parser.add_argument(
        "--spec",
        required=True,
        help="Root directory to recursively scan for YAML files",
    )
    parser.add_argument(
        "--xlen",
        type=int,
        choices=[32, 64],
        default=64,
        help="RISC-V architecture width (32 or 64 bits, default: 64)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress warnings and informational-only output"
    )
    parser.add_argument(
        "assembly_files",
        nargs="*",
        help="Assembly input files to process (reads stdin if omitted)",
    )
    return parser.parse_args()


def dprint(s):
    if debug:
        print(s)


def qprint(s):
    if not quiet:
        print(s)


def parse_register_value(reg_operand, operand_def):
    reg_text = str(reg_operand).strip()

    try:
        return int(reg_text, 0)
    except ValueError:
        pass

    reg_file = operand_def.get("reg_file")
    if not isinstance(reg_file, str):
        print(
            f"#    ERROR: Invalid register '{reg_text}' for operand without register-file metadata"
        )
        return None
    reg_file = reg_file.strip()

    reg_names = spec.register_name_to_index.get(reg_file)
    if reg_names is None:
        print(f"#    ERROR: Unknown register file '{reg_file}' while parsing register '{reg_text}'")
        return None

    reg_idx = reg_names.get(reg_text.lower())
    if reg_idx is None:
        print(f"#    ERROR: Unknown register name '{reg_text}' for register file '{reg_file}'")
        return None

    return reg_idx


def field_width(s):
    """Return the width in bits of a field location string.
    Supports:
      - single bit index: '5' -> 1
      - range: '31-25' -> 7, '0-3' -> 4
      - concatenation: '31-25|11-7|14' -> sum of each segment
    """
    if isinstance(s, int):
        return s
    s = str(s).strip()
    if "|" in s:
        return sum(field_width(seg.strip()) for seg in s.split("|"))
    if "-" in s:
        first, last = s.split("-")
        return abs(int(first) - int(last)) + 1
    return 1


pattern = re.compile(r"^(-?\d+)(?:-(-?\d+))?$")


def parse_range(s: str) -> tuple[int, int]:
    """
    Parse strings like:
      '5-10', '-5--10', '0', '800', '-42'
    Return values (single element ranges like "x" return "x, x"):
      (start, end)
    """
    match = pattern.fullmatch(s)
    if not match:
        raise ValueError(f"Invalid input: {s}")

    start = int(match.group(1))
    end = int(match.group(2)) if match.group(2) is not None else start

    return start, end


def extract_mnemonic(line):
    """Extract the instruction mnemonic from an assembly line"""
    # Remove comments
    line = line.split("#")[0].strip()
    if not line:
        return None
    # Extract the first word (mnemonic)
    parts = line.split()
    if parts:
        # Remove any trailing colon (for labels)
        mnemonic = parts[0]
        if mnemonic.endswith(":"):
            # This is a label, not an instruction
            if len(parts) > 1:
                # Return the next word after the label
                return parts[1]
            return None
        return mnemonic
    return None


def read_assembly_file(filepath):
    """Read assembly file and return its contents as an array of strings"""
    with open(filepath) as f:
        return f.readlines()


def parse_location(location):
    """Parse location string into list of bit positions (e.g., '31-25', '0-3', '7|11|30')"""
    bit_positions = []

    # Handle concatenated locations (separated by '|')
    if "|" in location:
        segments = location.split("|")
        for segment in segments:
            bit_positions.extend(parse_location(segment.strip()))
        return bit_positions

    # Handle range locations (e.g., '31-25', '0-3') or single bit
    try:
        if "-" in location:
            first, last = location.split("-")
            start = int(first)
            end = int(last)
            step = -1 if start > end else 1
            for bit in range(start, end + step, step):
                bit_positions.append(bit)
        else:
            bit_positions.append(int(location))
    except ValueError:
        print(f"# ERROR: Invalid location format: {location}")
        return []

    return bit_positions


def set_bits(binary_str, positions, value):
    """Set bits at specified positions to the bits from value"""
    instruction_width = len(binary_str)
    field_w = len(positions)

    dprint(
        f"#    Setting bits at positions {positions} to value {value} (field width {field_w}) in binary string: {binary_str}"
    )
    binary_list = list(binary_str)
    dprint(f"#    Initial binary list: {binary_list}")

    # Ensure value fits within the specified field width
    value = (value & ((1 << field_w) - 1)) if field_w > 0 else 0

    positions_rev = list(positions)[::-1]  # LSB of value goes to the last position

    # Set bits at specified positions
    for i, pos in enumerate(positions_rev):
        if i >= field_w:
            break
        bit_value = (value >> i) & 1
        dprint(f"#    Setting bit at position {pos} to {bit_value} (bit {i} of value)")

        # Convert bit position to string index (MSB at index 0)
        idx = instruction_width - pos - 1
        if idx < 0 or idx >= instruction_width:
            print(
                f"#    ERROR: Bit position {pos} out of range for instruction width {instruction_width}"
            )
            continue
        binary_list[idx] = "1" if bit_value else "0"
        dprint(f"#    binary list after setting bits: {binary_list}")

    return "".join(binary_list)


def split_assembly_arguments(arguments_str):
    """Split operand text on commas, ignoring commas inside {} groups."""
    arguments = []
    current = []
    brace_depth = 0

    for char in arguments_str:
        if char == "," and brace_depth == 0:
            arguments.append("".join(current).strip())
            current = []
            continue

        if char == "{":
            brace_depth += 1
        elif char == "}" and brace_depth > 0:
            brace_depth -= 1

        current.append(char)

    if current:
        arguments.append("".join(current).strip())

    return arguments


def operand_has_default(operand_def):
    return "default" in operand_def


def operand_default_value(operand_def):
    return operand_def["default"]


def operand_def_by_name(instruction_operands, operand_name):
    for operand_def in instruction_operands:
        if operand_def.get("name") == operand_name:
            return operand_def
    return None


def parse_assembly_arguments(line, instruction_operands):
    """Parse assembly line arguments to extract operands based on instruction definition"""
    # Remove comments and leading/trailing whitespace
    line = line.split("#")[0].strip()
    if " " in line:
        # Extract arguments (everything after mnemonic, comma separated)
        arguments_str = "".join(line.split()[1:])  # Skip the mnemonic
        arguments = split_assembly_arguments(arguments_str)
    else:
        arguments = []

    explicit_operands = [
        operand_def for operand_def in instruction_operands if not operand_def.get("implicit")
    ]

    optional_operands = 0
    for operand_def in explicit_operands:
        if operand_has_default(operand_def):
            optional_operands += 1

    min_arguments = len(explicit_operands) - optional_operands
    if len(arguments) < min_arguments or len(arguments) > len(explicit_operands):
        print(
            f"#    ERROR: invalid argument count for instruction; got {len(arguments)} ({arguments}) needed between {min_arguments} and {len(explicit_operands)}"
        )
        return {}

    optional_operands_to_keep = len(arguments) - min_arguments

    # Map assembly arguments to instruction operands definition
    operand_values = {}
    argi = 0
    for i, operand_def in enumerate(explicit_operands):
        dprint(f'# operand {i}: "{operand_def}"; {len(arguments)}')
        operand_name = operand_def.get("name", f"op{i}")
        if operand_has_default(operand_def):
            if optional_operands_to_keep > 0:
                optional_operands_to_keep -= 1
            else:
                operand_values[operand_name] = operand_default_value(operand_def)
                dprint(
                    f'# Using default value "{operand_values[operand_name]}" for operand "{operand_name}"'
                )
                continue

        dprint(f"#    Creating operand '{operand_name}' ({operand_def['type']})")
        if operand_def["type"] in ["register", "register_pair"]:
            if operand_def.get("offset"):
                dprint(f'#    memory argument with offset "{arguments[argi]}"')

                # Memory operand like "offset(rs1)"
                offset_part = arguments[argi].split("(")[0].strip()
                if offset_part == "":
                    offset_part = "0"
                reg_text = arguments[argi].split("(")[1].split(")")[0].strip()
                reg_index = parse_register_value(reg_text, operand_def)
                if reg_index is None:
                    print(f"# ERROR: Unknown register name {reg_text}")
                    return None
                dprint(f"#    Extracted offset: {offset_part}, register: {reg_index}")

                operand_values[operand_def["offset"]["name"]] = int(offset_part)

                if "possible_values" in operand_def["offset"]:
                    if not operand_def["offset"]["possible_values"]:
                        if arguments[argi].split("(")[0].strip() != "":
                            print("#    ERROR: Register offset not permitted.")
                    else:
                        is_possible = False
                        for possible in operand_def["offset"]["possible_values"]:
                            min_val, max_val = parse_range(str(possible))
                            if int(offset_part) >= min_val and int(offset_part) <= max_val:
                                is_possible = True
                        if not is_possible:
                            print("#    ERROR: Register offset is invalid.")

                if "left_shifted" in operand_def["offset"]:
                    encoded_value = int(offset_part)
                    shift = operand_def["offset"]["left_shifted"]
                    if ((encoded_value >> shift) << shift) != encoded_value:
                        print(
                            f"#    ERROR: Offset value {offset_part} cannot be fully represented given the required shift"
                        )
                        return None

            else:
                dprint(f"#    Detected register argument: {arguments[argi]}")
                reg_index = parse_register_value(arguments[argi], operand_def)
                if reg_index is None:
                    print(f"# ERROR: Unknown register name {arguments[argi]}")
                    return None

            # Validate register range against possible_values
            if "possible_values" in operand_def:
                if isinstance(
                    operand_def["possible_values"], list
                ) and reg_index not in operand_def.get("possible_values", []):
                    print(
                        f"#    ERROR: Register index {reg_index} is not valid, must be {operand_def.get('possible_values', [])}"
                    )
                    return None
                elif isinstance(operand_def["possible_values"], str):
                    try:
                        min_val, max_val = parse_range(operand_def["possible_values"])
                    except ValueError:
                        print(
                            f"#    ERROR: Invalid possible_values range for '{operand_name}': {operand_def['possible_values']}"
                        )
                        return None
                    if reg_index < min_val or reg_index > max_val:
                        print(
                            f"#    ERROR: Register index {reg_index} is out of range, must be between {min_val} and {max_val}"
                        )
                        return None

            dprint(f"#    Final value for '{operand_name}': {reg_index}")
            operand_values[operand_def["name"]] = int(reg_index)

        elif operand_def["type"] == "csr":
            dprint(f"#    Detected register argument: {arguments[argi]}")
            reg_index = parse_register_value(arguments[argi], operand_def)
            if reg_index is None:
                print(f"# ERROR: Unknown register name {arguments[argi]}")
                return None

            # Validate register range against possible_values
            if "possible_values" in operand_def:
                for possible in operand_def["possible_values"]:
                    min_val, max_val = parse_range(str(possible))
                    if reg_index < min_val or reg_index > max_val:
                        print(
                            f"#    ERROR: Register index {reg_index} is out of range, must be between {min_val} and {max_val}"
                        )
                        return None

            dprint(f"#    Final value for '{operand_name}': {reg_index}")
            operand_values[operand_def["name"]] = int(reg_index)

        elif operand_def["type"] == "immediate":
            dprint(f'#    immediate argument: "{arguments[argi]}"')
            imm_value = int(arguments[argi])
            if "possible_values" in operand_def:
                is_possible = False
                for possible in operand_def["possible_values"]:
                    min_val, max_val = parse_range(str(possible))
                    if int(imm_value) >= min_val and int(imm_value) <= max_val:
                        is_possible = True
                if not is_possible:
                    print("#    ERROR: Register offset is invalid.")

            operand_values[operand_def["name"]] = imm_value
            dprint(f"#    Final value for '{operand_name}': {imm_value}")

        elif operand_def["type"] == "fence_scope":
            dprint(f"#    Detected fence_scope argument: {arguments[argi]}")

            operand_values[operand_def["name"]] = arguments[argi]
            dprint(f"#    Final value for '{operand_name}': {arguments[argi]}")

        elif operand_def["type"] == "rounding_mode":
            dprint(f"#    Detected rounding_mode argument: {arguments[argi]}")

            operand_values[operand_def["name"]] = arguments[argi]
            dprint(f"#    Final value for '{operand_name}': {arguments[argi]}")

        elif operand_def["type"] == "reg_list":
            dprint(f"#    Detected reg_list argument: {arguments[argi]}")
            reg_list = arguments[argi].strip().replace(" ", "")

            if "possible_values" in operand_def:
                possible_values = operand_def.get("possible_values", [])
                if reg_list not in possible_values:
                    print(
                        f"#    ERROR: reg_list '{reg_list}' is not valid, must be one of {possible_values}"
                    )
                    return None

            operand_values[operand_def["name"]] = reg_list
            dprint(f"#    Final value for '{operand_name}': {reg_list}")

        elif operand_def["type"] == "float_immediate":
            dprint(f"#    Detected float_immediate argument: {arguments[argi]}")

            operand_values[operand_def["name"]] = arguments[argi]
            dprint(f"#    Final value for '{operand_name}': {arguments[argi]}")

        # consume argument
        argi += 1

    dprint(f"#    Parsed operand values: {operand_values}")
    return operand_values


def fill_in_variables(instruction, assembly, xlen=64):
    """Fill in variables in the match pattern based on the instruction's operands"""

    match_pattern = (spec.get_stanza(instruction.get("encoding"), xlen) or {}).get("match") or ""
    instruction_operands = spec.get_stanza(instruction.get("operands"), xlen) or []

    if not instruction_operands:
        return match_pattern

    variables = spec.get_stanza(instruction.get("encoding"), xlen).get("variables") or []

    assembly_operands = parse_assembly_arguments(assembly, instruction_operands)
    if assembly_operands is None:
        print(f"#  ERROR: Failed to parse assembly operands for '{assembly}'")
        return None

    dprint(f"#  Parsed assembly operands: {assembly_operands}")

    encoded = match_pattern

    for variable in variables:
        var_name = variable["name"]
        location = variable["location"]

        dprint(f'# Fill in "{var_name}"')

        # Find the operand value from assembly operands
        operand_value = 0  # Default value

        if "encode(operands)" in variable:
            try:
                operand_value = idl.execute(
                    variable["encode(operands)"],
                    xlen,
                    operands=assembly_operands,
                    instruction_operands=instruction_operands,
                )
            except idl.IdlExecutionError as exc:
                print(f"#  ERROR: IDL encode failed: {exc}")
                return None
        elif var_name in assembly_operands:
            dprint(
                f"#  Found direct match for variable '{var_name}' in assembly operands {assembly_operands[var_name]}"
            )
            operand_value = assembly_operands[var_name]
            if operand_value is None:
                print("#  ERROR: unsupported variable encoding")
                return None
        else:
            print("#  ERROR: unknown variable encoding")
            return None

        dprint(f"#  Variable '{var_name}' value: {operand_value}")

        bit_positions = parse_location(location)

        if "left_shift" in variable:
            operand_value = operand_value >> variable["left_shift"]
            dprint(f"#  Unapplied left shift {variable['left_shift']}, new value: {operand_value}")

        encoded = set_bits(encoded, bit_positions, operand_value)

    return encoded


def encode(assembly, xlen=64):
    dprint(f"#Encoding assembly instruction: {assembly} with xlen={xlen}")

    mnemonic = extract_mnemonic(assembly)
    if not mnemonic:
        return None

    dprint(f"#mnemonic: {mnemonic}")
    if mnemonic not in spec.instructions:
        print(f"# ERROR: Instruction '{mnemonic}' not found in YAML definitions")
        return None

    inst = spec.instructions[mnemonic]

    filled_match = fill_in_variables(inst, assembly, xlen)

    dprint(f"#  Filled match pattern:  {filled_match}")
    return filled_match


def main():
    global debug
    global quiet

    args = parse_args()
    debug = args.debug
    quiet = args.quiet
    xlen = args.xlen

    qprint(f"# Using RISC-V {xlen}-bit architecture")

    spec.initialize_spec(args.spec, quiet=quiet)

    if args.assembly_files:
        assembly_lines = []
        for assembly_file in args.assembly_files:
            assembly_lines.extend(read_assembly_file(assembly_file))
    else:
        assembly_lines = sys.stdin.read().splitlines()

    for line in assembly_lines:
        line = line.split("#")[0].strip()  # Remove comments and whitespace
        if not line:
            continue  # Skip empty lines
        encoded = encode(line.strip(), xlen)
        if encoded:
            print(f"{encoded}")
        else:
            print(f"# ERROR: Failed to encode '{line.strip()}'")


if __name__ == "__main__":
    main()
