#!/usr/bin/env python3
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
import argparse
import sys

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
        if "encoding" in spec.instructions[instruction]:
            encoding = spec.instructions[instruction]["encoding"]
            match_pattern = None

            # Extract match pattern based on encoding format and xlen
            if f"RV{xlen}" in encoding and "match" in encoding[f"RV{xlen}"]:
                match_pattern = encoding[f"RV{xlen}"]["match"]
            elif "match" in encoding:
                match_pattern = encoding["match"]
            elif "RV32" in encoding and "match" in encoding["RV32"] and xlen == 32:
                match_pattern = encoding["RV32"]["match"]
            elif "RV64" in encoding and "match" in encoding["RV64"] and xlen == 64:
                match_pattern = encoding["RV64"]["match"]

            if match_pattern and matches_pattern(opcode, match_pattern):
                matches.append(spec.instructions[instruction])

    return matches


def extract_variable_values(opcode, instruction, xlen=64):
    """Extract variable values from opcode based on instruction definition"""
    encoding = instruction["encoding"]
    variables = []

    # Extract variables based on encoding format and xlen
    if f"RV{xlen}" in encoding and "variables" in encoding[f"RV{xlen}"]:
        variables = encoding[f"RV{xlen}"]["variables"]
    elif "variables" in encoding:
        variables = encoding["variables"]
    elif "RV32" in encoding and "variables" in encoding["RV32"] and xlen == 32:
        variables = encoding["RV32"]["variables"]
    elif "RV64" in encoding and "variables" in encoding["RV64"] and xlen == 64:
        variables = encoding["RV64"]["variables"]

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

        if "sign_extend" in variable:
            sign_bit = 1 << (len(bit_positions) - 1)
            if value & sign_bit:
                value -= 1 << len(bit_positions)
            dprint(f"# Value after sign extension for variable '{var_name}': {value}")
        if "left_shift" in variable:
            value = value << variable["left_shift"]
            dprint(f"# Value after left shift for variable '{var_name}': {value}")

        variable_values[var_name] = value

    return variable_values


def decoded_reg_list_value(rlist, abi_names=False):
    """Return decoded reg_list text for PUSH/POP style instructions."""
    reg_list_map = {
        4: "{x1}",
        5: "{x1,x8}",
        6: "{x1,x8-x9}",
        7: "{x1,x8-x9,x18}",
        8: "{x1,x8-x9,x18-x19}",
        9: "{x1,x8-x9,x18-x20}",
        10: "{x1,x8-x9,x18-x21}",
        11: "{x1,x8-x9,x18-x22}",
        12: "{x1,x8-x9,x18-x23}",
        13: "{x1,x8-x9,x18-x24}",
        14: "{x1,x8-x9,x18-x25}",
        15: "{x1,x8-x9,x18-x27}",
    }
    reg_list_map_abi = {
        4: "{ra}",
        5: "{ra,s0}",
        6: "{ra,s0-s1}",
        7: "{ra,s0-s2}",
        8: "{ra,s0-s3}",
        9: "{ra,s0-s4}",
        10: "{ra,s0-s5}",
        11: "{ra,s0-s6}",
        12: "{ra,s0-s7}",
        13: "{ra,s0-s8}",
        14: "{ra,s0-s9}",
        15: "{ra,s0-s11}",
    }
    if abi_names:
        return reg_list_map_abi.get(rlist)
    else:
        return reg_list_map.get(rlist)


def operand_has_default(operand):
    return "default" in operand


def append_assembly_operand(assembly_parts, operand, value):
    if operand_has_default(operand) and value == operand["default"]:
        return
    assembly_parts.append(str(value))


def variable_by_name(variables, name):
    for variable in variables or []:
        if variable.get("name") == name:
            return variable
    return None


def format_assembly(instruction, variable_values, xlen=64, abi_names=False):
    """Format assembly instruction based on instruction definition and variable values"""
    mnemonic = instruction["name"]

    operands = []
    if "operands" in instruction:
        if "RV32" in instruction["operands"] and xlen == 32:
            operands = instruction["operands"]["RV32"]
        elif "RV64" in instruction["operands"] and xlen == 64:
            operands = instruction["operands"]["RV64"]
        else:
            operands = instruction["operands"]

    if "RV32" in instruction["encoding"] and xlen == 32:
        variables = instruction["encoding"]["RV32"].get("variables")
    elif "RV64" in instruction["encoding"] and xlen == 64:
        variables = instruction["encoding"]["RV64"].get("variables")
    else:
        variables = instruction["encoding"].get("variables")

    assembly_parts = []

    # For regular instructions with operands
    for operand in operands:
        if operand.get("implicit"):
            continue

        operand_name = operand["name"]

        dprint(f"# Processing operand '{operand_name}' ({operand['type']})")

        if operand["type"] == "fence_scope":
            scope_map = {
                0b1111: "iorw",
                0b1110: "ior",
                0b1101: "iow",
                0b1011: "irw",
                0b0111: "orw",
                0b1100: "io",
                0b1010: "ir",
                0b1001: "iw",
                0b0110: "or",
                0b0101: "ow",
                0b0011: "rw",
                0b1000: "i",
                0b0100: "o",
                0b0010: "r",
                0b0001: "w",
            }

            value = variable_values[operand_name]
            if value not in scope_map:
                print(f"# ERROR: unknown fence scope {value}")
                continue
            append_assembly_operand(assembly_parts, operand, scope_map[value])

        elif operand["type"] == "rounding_mode":
            rm_map = {
                0b000: "rne",
                0b001: "rtz",
                0b010: "rdn",
                0b011: "rup",
                0b100: "rmm",
                0b111: "dyn",
            }

            value = variable_values[operand_name]
            if value not in rm_map:
                print(f"# ERROR: unknown rounding mode {value}")
                continue
            append_assembly_operand(assembly_parts, operand, rm_map[value])

        elif operand.get("offset"):
            value = variable_values[operand_name]
            variable = variable_by_name(variables, operand_name)
            if variable and "decode()" in variable and "creg2reg" in variable["decode()"]:
                value += 8
                dprint(
                    f"# Value after creg2reg transformation for variable '{variable['name']}': {value}"
                )

            dprint(f"# Handling offset for operand '{operand_name}' with value {value}")
            if operand["offset"]["name"] == "":
                offset_value = ""
            else:
                offset_value = variable_values[operand["offset"]["name"]]
                if "left_shift" in operand["offset"]:
                    offset_value = offset_value << operand["offset"]["left_shift"]
            reg_name = register_name_for_index(operand.get("reg_file"), value, abi_names)
            assembly_parts.append(f"{offset_value}({reg_name})")

        elif operand["type"] == "reg_list":
            reg_list = decoded_reg_list_value(variable_values["rlist"], abi_names)
            if reg_list is None:
                print(f"# ERROR: unknown reg_list encoding {variable_values['rlist']}")
                continue
            possible_values = operand.get("possible_values")
            if isinstance(possible_values, list) and reg_list not in possible_values:
                dprint(
                    f"# reg_list '{reg_list}' not valid for this xlen/instruction variant: {possible_values}"
                )
                return None
            append_assembly_operand(assembly_parts, operand, reg_list)

        elif operand_has_default(operand):
            value = variable_values[operand_name]
            if operand_name == "vm" and operand.get("type") == "register":
                if value == 0:
                    append_assembly_operand(assembly_parts, operand, "v0.t")
            else:
                append_assembly_operand(assembly_parts, operand, value)

        elif operand_name == "stack_adj":
            dprint("# Handling stack_adj")
            registers = 13 if variable_values["rlist"] == 15 else (variable_values["rlist"] - 3)
            register_space = registers * int(xlen / 8)
            register_space_aligned = int((register_space + 15) / 16) * 16
            extra_space = variable_values["spimm"] * 16
            total_space = register_space_aligned + extra_space
            append_assembly_operand(assembly_parts, operand, -total_space)

        elif operand["type"] == "float_immediate":
            if variable_values["xs1"] == 0:
                value = "-1.0"
            elif variable_values["xs1"] == 1:
                value = "min"
            elif variable_values["xs1"] == 2:
                value = "0.0000152587890625"
            elif variable_values["xs1"] == 3:
                value = "0.000030517578125"
            elif variable_values["xs1"] == 4:
                value = "0.00390625"
            elif variable_values["xs1"] == 5:
                value = "0.0078125"
            elif variable_values["xs1"] == 6:
                value = "0.0625"
            elif variable_values["xs1"] == 7:
                value = "0.125"
            elif variable_values["xs1"] == 8:
                value = "0.25"
            elif variable_values["xs1"] == 9:
                value = "0.3125"
            elif variable_values["xs1"] == 10:
                value = "0.375"
            elif variable_values["xs1"] == 11:
                value = "0.4375"
            elif variable_values["xs1"] == 12:
                value = "0.5"
            elif variable_values["xs1"] == 13:
                value = "0.625"
            elif variable_values["xs1"] == 14:
                value = "0.75"
            elif variable_values["xs1"] == 15:
                value = "0.875"
            elif variable_values["xs1"] == 16:
                value = "1.0"
            elif variable_values["xs1"] == 17:
                value = "1.25"
            elif variable_values["xs1"] == 18:
                value = "1.5"
            elif variable_values["xs1"] == 19:
                value = "1.75"
            elif variable_values["xs1"] == 20:
                value = "2.0"
            elif variable_values["xs1"] == 21:
                value = "2.5"
            elif variable_values["xs1"] == 22:
                value = "3"
            elif variable_values["xs1"] == 23:
                value = "4"
            elif variable_values["xs1"] == 24:
                value = "8"
            elif variable_values["xs1"] == 25:
                value = "16"
            elif variable_values["xs1"] == 26:
                value = "128"
            elif variable_values["xs1"] == 27:
                value = "256"
            elif variable_values["xs1"] == 28:
                value = "32768"
            elif variable_values["xs1"] == 29:
                value = "65536"
            elif variable_values["xs1"] == 30:
                value = "inf"
            elif variable_values["xs1"] == 31:
                value = "nan"
            append_assembly_operand(assembly_parts, operand, value)

        else:
            value = variable_values[operand_name]
            for variable in variables:
                if variable["name"] == operand_name:
                    if "decode()" in variable:
                        if "creg2reg" in variable["decode()"]:
                            value += 8
                            dprint(
                                f"# Value after creg2reg transformation for variable '{variable['name']}': {value}"
                            )

                        elif "r1s" in variable["decode()"] or "r2s" in variable["decode()"]:
                            value = value + 8 + 8 * ((value + 6) // 8)
                    break
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
