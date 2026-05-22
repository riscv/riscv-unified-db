#!/usr/bin/env python3
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
import argparse
import sys

import idl

import spec

instruction_by_match = {}
debug = False
quiet = False


def parse_args():
    parser = argparse.ArgumentParser(description="Decode RISC-V opcodes to assembly instructions")
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
        help="RISC-V architecture width (32 or 64 bits)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress warning and information-only messages"
    )
    parser.add_argument(
        "--abi-names",
        action="store_true",
        help="Emit ABI register names when available (e.g. ra/sp/a0)",
    )
    parser.add_argument(
        "opcode_files",
        nargs="*",
        help="Opcode input files to process (reads stdin if omitted)",
    )
    return parser.parse_args()


def dprint(s):
    if debug:
        print(s)


def qprint(s):
    if not quiet:
        print(s)


def register_name_for_index(reg_file_name, reg_index, abi_names=False):
    if abi_names:
        abi_map = spec.register_abi_name_by_index.get(reg_file_name, {})
        if reg_index in abi_map:
            return abi_map[reg_index]

    canonical_map = spec.register_name_by_index.get(reg_file_name, {})
    if reg_index in canonical_map:
        return canonical_map[reg_index]

    return str(reg_index)


def read_opcodes(f):
    """Read file containing opcodes and return its contents as an array of strings"""
    return [line.strip() for line in f.readlines() if line.strip()]


def parse_location(location):
    """Parse location string into a list of bit positions"""
    dprint(f"# Parsing location: {location}")
    bit_positions = []

    # Handle concatenated locations (separated by '|')
    if "|" in location:
        segments = location.split("|")
        for segment in segments:
            bit_positions.extend(parse_location(segment))
        dprint(f"# Parsed concatenated location '{location}' into bit positions: {bit_positions}")
        return bit_positions

    # Handle range locations (e.g., '31-25')
    if "-" in location:
        start, end = location.split("-")
        start, end = int(start), int(end)
        for bit in range(start, end - 1, -1):
            bit_positions.append(bit)
    else:
        # Single bit location
        bit_positions.append(int(location))

    dprint(f"# Parsed location '{location}' into bit positions: {bit_positions}")
    return bit_positions


def extract_bits(binary_str, positions):
    """Extract bits from specified positions in the binary string"""
    result = 0

    # Convert binary string to list for easier manipulation
    binary_list = list(binary_str)

    # Extract bits from specified positions
    dprint(f"# Extracting bits from binary string '{binary_str}' at positions {positions}")
    for pos in positions:
        dprint(f"# Processing bit position {pos}")
        idx = len(binary_list) - 1 - pos  # Calculate index from the right
        bit_value = 1 if binary_str[idx] == "1" else 0
        result = (result << 1) | bit_value
        dprint(f"# Bit at position {pos} is '{binary_str[idx]}' result {result}")

    return result


def matches_pattern(opcode, pattern):
    """Check if opcode matches the pattern (considering '-' as wildcards)"""
    if len(opcode) != len(pattern):
        return False

    return all((pattern[i] == "-" or opcode[i] == pattern[i]) for i in range(len(opcode)))


def find_matching_instructions(opcode, xlen=64):
    """Find all instructions that match the given opcode."""
    matches = []

    for instruction in spec.instructions:
        match_pattern = (
            spec.get_stanza(spec.instructions[instruction].get("encoding"), xlen) or {}
        ).get("match") or ""

        if matches_pattern(opcode, match_pattern):
            matches.append(spec.instructions[instruction])

    return matches


def extract_variable_values(opcode, instruction, xlen=64):
    """Extract variable values from opcode based on instruction definition"""

    variables = spec.get_stanza(instruction.get("encoding"), xlen).get("variables") or []

    variable_values = {}

    # Process each variable
    for variable in variables:
        var_name = variable["name"]
        location = variable["location"]

        # Parse the location string to get bit positions
        bit_positions = parse_location(location)
        dprint(f"# Variable '{var_name}' is located at bits {bit_positions} in the opcode")

        # Extract the value from the opcode
        value = extract_bits(opcode, bit_positions)
        dprint(
            f"# Extracted raw value for variable '{var_name}': {value} from bits {bit_positions}"
        )

        # Apply any transformations

        if variable.get("sign_extend"):
            sign_bit = 1 << (len(bit_positions) - 1)
            if value & sign_bit:
                value -= 1 << len(bit_positions)
            dprint(f"# Value after sign extension for variable '{var_name}': {value}")

        variable_values[var_name] = value

    return variable_values


def operand_has_default(operand):
    return "default" in operand


def append_assembly_operand(assembly_parts, operand, value):
    if operand_has_default(operand) and value == operand["default"]:
        return
    assembly_parts.append(str(value))


def append_decoded_operand(assembly_parts, operand, value, abi_names=False):
    if operand.get("type") in ["register", "register_pair"] and isinstance(value, int):
        value = register_name_for_index(operand.get("reg_file"), value, abi_names)
    append_assembly_operand(assembly_parts, operand, value)


def decode_operand_offset(operand, variable_values, xlen=64):
    offset = operand.get("offset")
    if not offset:
        return None

    offset_name = offset.get("name")
    if offset_name == "":
        return ""
    if offset_name not in variable_values:
        return None

    decode_expr = offset.get("decode()")
    if decode_expr:
        return idl.execute(decode_expr, xlen, variables=variable_values)

    return variable_values[offset_name]


def format_assembly(instruction, variable_values, xlen=64, abi_names=False):
    """Format assembly instruction based on instruction definition and variable values"""
    mnemonic = instruction["name"]

    operands = spec.get_stanza(instruction.get("operands"), xlen) or []

    assembly_parts = []

    # For regular instructions with operands
    for operand in operands:
        if operand.get("implicit"):
            continue

        operand_name = operand["name"]

        dprint(f"# Processing operand '{operand_name}' ({operand['type']})")

        decode_expr = operand.get("decode()")
        if decode_expr:
            try:
                value = idl.execute(decode_expr, xlen, variables=variable_values)
            except idl.IdlExecutionError as exc:
                print(f"# ERROR: IDL decode failed for operand '{operand['name']}': {exc}")
                return None

            offset = operand.get("offset")
            if offset:
                try:
                    offset_value = decode_operand_offset(operand, variable_values, xlen)
                except idl.IdlExecutionError as exc:
                    print(
                        f"# ERROR: IDL decode failed for offset '{offset.get('name', '')}': {exc}"
                    )
                    return None
                reg_name = register_name_for_index(operand.get("reg_file"), value, abi_names)
                assembly_parts.append(f"{offset_value}({reg_name})")
            else:
                append_decoded_operand(assembly_parts, operand, value, abi_names)
            continue

        elif operand.get("offset"):
            value = variable_values[operand_name]

            dprint(f"# Handling offset for operand '{operand_name}' with value {value}")
            try:
                offset_value = decode_operand_offset(operand, variable_values, xlen)
            except idl.IdlExecutionError as exc:
                print(
                    f"# ERROR: IDL decode failed for offset '{operand['offset'].get('name', '')}': {exc}"
                )
                return None
            reg_name = register_name_for_index(operand.get("reg_file"), value, abi_names)
            assembly_parts.append(f"{offset_value}({reg_name})")

        elif operand_has_default(operand):
            value = variable_values[operand_name]
            if operand_name == "vm" and operand.get("type") == "register":
                if value == 0:
                    append_assembly_operand(assembly_parts, operand, "v0.t")
            else:
                append_assembly_operand(assembly_parts, operand, value)

        else:
            value = variable_values[operand_name]
            dprint(f"# map {operand_name} {value}")
            if operand["type"] in ["register", "register_pair"]:
                append_assembly_operand(
                    assembly_parts,
                    operand,
                    register_name_for_index(operand.get("reg_file"), value, abi_names),
                )
            else:
                append_assembly_operand(assembly_parts, operand, value)

    if assembly_parts:
        return f"{mnemonic} {', '.join(assembly_parts)}"

    # Default case: just return the mnemonic
    return mnemonic


def decode(opcode, xlen=64, abi_names=False):
    """Decode an opcode into an assembly instruction"""
    dprint(f"# Decoding opcode: {opcode} with xlen={xlen}")

    # Find matching instructions and try each one until formatting succeeds.
    matching_instructions = find_matching_instructions(opcode, xlen)
    if not matching_instructions:
        print(f"# ERROR: No matching instruction found for opcode: {opcode}")
        return None

    for instruction in matching_instructions:
        dprint(f"# Found matching instruction candidate: {instruction['name']}")

        # Extract variable values from opcode
        variable_values = extract_variable_values(opcode, instruction, xlen)
        dprint(f"# Extracted variable values: {variable_values}")

        # Format assembly instruction
        assembly = format_assembly(instruction, variable_values, xlen, abi_names=abi_names)
        dprint(f"# Formatted assembly: {assembly}")
        if assembly is not None:
            return assembly

    print("# ERROR: No matching instruction candidate produced a decodable assembly string")
    return None


def main():
    global debug
    global quiet

    args = parse_args()
    debug = args.debug
    quiet = args.quiet

    # Validate xlen parameter
    xlen = args.xlen
    if xlen not in [32, 64]:
        print(f"ERROR: xlen must be either 32 or 64, got {xlen}")
        sys.exit(1)
    qprint(f"# Using RISC-V {xlen}-bit architecture (xlen={xlen})")

    spec.initialize_spec(args.spec, quiet=quiet)

    if args.opcode_files:
        opcodes = []
        for opcode_file in args.opcode_files:
            with open(opcode_file) as f:
                opcodes.extend(read_opcodes(f))
    else:
        opcodes = read_opcodes(sys.stdin)

    # Process opcodes and print assembly instructions
    for opcode in opcodes:
        opcode = opcode.split("#")[0].strip()  # Remove comments and whitespace
        if not opcode:
            continue  # Skip empty lines
        assembly = decode(opcode, xlen, abi_names=args.abi_names)
        if assembly:
            print(f"{assembly}")
        else:
            print(f"ERROR: Failed to decode '{opcode}'")


if __name__ == "__main__":
    main()
