#!/usr/bin/env python3
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
import argparse
import re
import sys

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
    # Convert binary string to list for easier manipulation
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


def parse_assembly_arguments(line, instruction_operands):
    """Parse assembly line arguments to extract operands based on instruction definition"""
    # Remove comments and leading/trailing whitespace
    line = line.split("#")[0].strip()
    if " " not in line:
        return {}

    # Extract arguments (everything after mnemonic, comma separated)
    arguments_str = "".join(line.split()[1:])  # Skip the mnemonic
    arguments = [argument.strip() for argument in arguments_str.split(",")]

    optional_operands = 0
    for operand_def in instruction_operands:
        if operand_def.get("optional"):
            optional_operands += 1

    optional_operands_to_keep = optional_operands - (len(instruction_operands) - len(arguments))
    if optional_operands < optional_operands_to_keep:
        print(
            f"#    ERROR: insufficient arguments for instruction; got {len(arguments)} ({arguments}) needed at least {len(instruction_operands) - optional_operands}"
        )
        return {}

    # Map assembly arguments to instruction operands definition
    operand_values = {}
    argi = 0
    for i, operand_def in enumerate(instruction_operands):
        dprint(f'# operand {i}: "{operand_def}"; {len(arguments)}')
        operand_name = operand_def.get("name", f"op{i}")
        if operand_def.get("optional"):
            if optional_operands_to_keep > 0:
                optional_operands_to_keep -= 1
            else:
                dprint(f'# Skipping optional operand "{operand_name}"')
                continue

        dprint(f"#    Creating operand '{operand_name}' ({operand_def['type']})")
        if operand_def["type"] in ["register", "register_pair"]:
            if "offset" in operand_def:
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

                # print(f"#{instruction_operands[i]}")
                operand_values[instruction_operands[i]["offset"]["name"]] = int(offset_part)

                if "possible_values" in instruction_operands[i]["offset"]:
                    if not instruction_operands[i]["offset"]["possible_values"]:
                        if arguments[argi].split("(")[0].strip() != "":
                            print("#    ERROR: Register offset not permitted.")
                    else:
                        is_possible = False
                        for possible in instruction_operands[i]["offset"]["possible_values"]:
                            min_val, max_val = parse_range(str(possible))
                            if int(offset_part) >= min_val and int(offset_part) <= max_val:
                                is_possible = True
                        if not is_possible:
                            print("#    ERROR: Register offset is invalid.")

                if "left_shifted" in instruction_operands[i]["offset"]:
                    encoded_value = int(offset_part)
                    shift = instruction_operands[i]["offset"]["left_shifted"]
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
            operand_values[instruction_operands[i]["name"]] = int(reg_index)

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
            operand_values[instruction_operands[i]["name"]] = int(reg_index)

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

            operand_values[instruction_operands[i]["name"]] = imm_value
            dprint(f"#    Final value for '{operand_name}': {imm_value}")

        elif operand_def["type"] == "fence_scope":
            dprint(f"#    Detected fence_scope argument: {arguments[argi]}")

            operand_values[instruction_operands[i]["name"]] = arguments[i]
            dprint(f"#    Final value for '{operand_name}': {arguments[argi]}")

        elif operand_def["type"] == "rounding_mode":
            dprint(f"#    Detected rounding_mode argument: {arguments[argi]}")

            operand_values[instruction_operands[i]["name"]] = arguments[i]
            dprint(f"#    Final value for '{operand_name}': {arguments[argi]}")

        elif operand_def["type"] == "reg_range":
            dprint(f"#    Detected reg_range argument: {arguments[argi]}")

            operand_values[instruction_operands[i]["name"]] = arguments[i]
            dprint(f"#    Final value for '{operand_name}': {arguments[argi]}")

        elif operand_def["type"] == "float_immediate":
            dprint(f"#    Detected float_immediate argument: {arguments[argi]}")

            operand_values[instruction_operands[i]["name"]] = arguments[i]
            dprint(f"#    Final value for '{operand_name}': {arguments[argi]}")

        # consume argument
        argi += 1

    dprint(f"#    Parsed operand values: {operand_values}")
    return operand_values


def builtin_encode_fence_scope(scope):
    scope_map = {
        "i": 0b1000,
        "o": 0b0100,
        "r": 0b0010,
        "w": 0b0001,
        "io": 0b1100,
        "ir": 0b1010,
        "iw": 0b1001,
        "or": 0b0110,
        "ow": 0b0101,
        "rw": 0b0011,
        "ior": 0b1110,
        "iow": 0b1101,
        "irw": 0b1011,
        "orw": 0b0111,
        "iorw": 0b1111,
    }
    if scope in scope_map:
        return scope_map[scope]
    print(f'# ERROR: invalid fence scope "{scope}"')
    return None


def builtin_encode_rounding_mode(rm):
    rm_map = {"rne": 0b000, "rtz": 0b001, "rdn": 0b010, "rup": 0b011, "rmm": 0b100, "dyn": 0b111}
    if rm in rm_map:
        return rm_map[rm]
    print(f'# ERROR: invalid rounding mode "{rm}"')
    return None


def builtin_encode_reg_list(ops):
    args = ""
    if "reg_range0" in ops:
        args += ops["reg_range0"]
        if "reg_range1" in ops:
            args += "," + ops["reg_range1"]
            if "reg_range2" in ops:
                args += "," + ops["reg_range2"]
    if args in ["ra", "x1"]:
        return 4
    if args in ["ra,s0", "x1,x8"]:
        return 5
    if args in ["ra,s0-s1", "x1,x8-x9"]:
        return 6
    if args in ["ra,s0-s2", "x1,x8-x9,x18"]:
        return 7
    if args in ["ra,s0-s3", "x1,x8-x9,x18-x19"]:
        return 8
    if args in ["ra,s0-s4", "x1,x8-x9,x18-x20"]:
        return 9
    if args in ["ra,s0-s5", "x1,x8-x9,x18-x21"]:
        return 10
    if args in ["ra,s0-s6", "x1,x8-x9,x18-x22"]:
        return 11
    if args in ["ra,s0-s7", "x1,x8-x9,x18-x23"]:
        return 12
    if args in ["ra,s0-s8", "x1,x8-x9,x18-x24"]:
        return 13
    if args in ["ra,s0-s9", "x1,x8-x9,x18-x25"]:
        return 14
    if args in ["ra,s0-s11", "x1,x8-x9,x18-x27"]:
        return 15


def builtin_encode_stack_adj(ops, xlen):
    registers = builtin_encode_reg_list(ops) - 3
    registers_space = registers * int(xlen / 8)
    registers_space_aligned = int((registers_space + 15) / 16) * 16
    extra_space = (-ops["stack_adj"]) - registers_space_aligned
    return extra_space >> 4


def builtin_encode_sreg(reg):
    return (reg - 8) - 8 * ((reg - 8) // 10)


def builtin_encode_float_immediate(value):
    if value == "-1.0":
        return 0b00000
    if value == "min":
        return 0b00001
    if value == "0.0000152587890625":
        return 0b00010
    if value == "0.000030517578125":
        return 0b00011
    if value == "0.00390625":
        return 0b00100
    if value == "0.0078125":
        return 0b00101
    if value == "0.0625":
        return 0b00110
    if value == "0.125":
        return 0b00111
    if value == "0.25":
        return 0b01000
    if value == "0.3125":
        return 0b01001
    if value == "0.375":
        return 0b01010
    if value == "0.4375":
        return 0b01011
    if value == "0.5":
        return 0b01100
    if value == "0.625":
        return 0b01101
    if value == "0.75":
        return 0b01110
    if value == "0.875":
        return 0b01111
    if value == "1.0":
        return 0b10000
    if value == "1.25":
        return 0b10001
    if value == "1.5":
        return 0b10010
    if value == "1.75":
        return 0b10011
    if value == "2.0":
        return 0b10100
    if value == "2.5":
        return 0b10101
    if value == "3":
        return 0b10110
    if value == "4":
        return 0b10111
    if value == "8":
        return 0b11000
    if value == "16":
        return 0b11001
    if value == "128":
        return 0b11010
    if value == "256":
        return 0b11011
    if value == "32768":
        return 0b11100
    if value == "65536":
        return 0b11101
    if value == "inf":
        return 0b11110
    if value == "nan":
        return 0b11111
    print(f'# ERROR: Unrecognized floating point immediate: "{value}"')
    return None


def UDB_invoke_IDL(idl, operands, xlen):
    if "operands[vm]" in idl:
        if "vm" in operands:
            return 0
        return 1
    if "return 1;" in idl:  # vector mask
        return 1
    if "return 0;" in idl:
        return 0
    if "reg_list" in idl:
        return builtin_encode_reg_list(operands)
    if "stack_adj" in idl:
        return builtin_encode_stack_adj(operands, xlen)
    if "iorw" in idl:
        if "pred" in idl:
            return builtin_encode_fence_scope(operands["pred"])
        elif "succ" in idl:
            return builtin_encode_fence_scope(operands["succ"])
    if "rtz" in idl:
        return builtin_encode_rounding_mode(operands["rm"])
    if "r1s" in idl:
        return builtin_encode_sreg(operands["r1s"])
    if "r2s" in idl:
        return builtin_encode_sreg(operands["r2s"])
    if ".offset" in idl:
        return operands["imm"]
    if "reg2creg" in idl:
        if "xd" in idl:
            return operands["xd"] - 8
        if "xs1" in idl:
            return operands["xs1"] - 8
    if "nan" in idl and "min" in idl and "inf" in idl:
        return builtin_encode_float_immediate(operands["xs1"])
    return None


def fill_in_variables(inst, assembly, xlen=64):
    """Fill in variables in the match pattern based on the instruction's operands"""
    # Initialize variables
    match_pattern = ""
    variables = []

    if "encoding" not in inst:
        print(f"  ERROR: No encoding information found for {inst.get('name', '<unknown>')}")
        return None

    encoding = inst["encoding"]

    # Extract match pattern and variables based on encoding format and xlen
    if f"RV{xlen}" in encoding and "match" in encoding[f"RV{xlen}"]:
        match_pattern = encoding[f"RV{xlen}"]["match"]
        variables = encoding[f"RV{xlen}"].get("variables", [])
    elif "match" in encoding:
        match_pattern = encoding["match"]
        variables = encoding.get("variables", [])
    elif "RV32" in encoding and "match" in encoding["RV32"] and xlen == 32:
        match_pattern = encoding["RV32"]["match"]
        variables = encoding["RV32"].get("variables", [])
    elif "RV64" in encoding and "match" in encoding["RV64"] and xlen == 64:
        match_pattern = encoding["RV64"]["match"]
        variables = encoding["RV64"].get("variables", [])
    else:
        print("# ERROR: No match pattern found in encoding")
        return None

    # Get operands based on xlen
    if f"RV{xlen}" in inst["operands"]:
        instruction_operands = inst["operands"][f"RV{xlen}"]
    elif "RV32" in inst["operands"] and xlen == 32:
        instruction_operands = inst["operands"]["RV32"]
    elif "RV64" in inst["operands"] and xlen == 64:
        instruction_operands = inst["operands"]["RV64"]
    else:
        instruction_operands = inst["operands"]

    # Parse assembly line to extract operands
    assembly_operands = parse_assembly_arguments(assembly, instruction_operands)
    if assembly_operands is None:
        print(f"#  ERROR: Failed to parse assembly operands for '{assembly}'")
        return None

    dprint(f"#  Parsed assembly operands: {assembly_operands}")

    encoded = match_pattern

    # Process each variable
    for variable in variables:
        var_name = variable["name"]
        location = variable["location"]

        dprint(f'# Fill in "{var_name}"')

        # Find the operand value from assembly operands
        operand_value = 0  # Default value

        if "encode(operands)" in variable:
            operand_value = UDB_invoke_IDL(variable["encode(operands)"], assembly_operands, xlen)
            if operand_value is None:
                print("#  ERROR: unsupported variable encoding")
                return None
        elif var_name in assembly_operands:
            dprint(
                f"#  Found direct match for variable '{var_name}' in assembly operands {assembly_operands[var_name]}"
            )
            operand_value = assembly_operands[var_name]
        else:
            print("#  ERROR: unknown variable encoding")
            return None

        dprint(f"#  Variable '{var_name}' value: {operand_value}")

        # Parse the location string to get bit positions
        bit_positions = parse_location(location)

        # Apply any shifts specified in the variable
        if "left_shift" in variable:
            operand_value = operand_value >> variable["left_shift"]
            dprint(f"#  Unapplied left shift {variable['left_shift']}, new value: {operand_value}")

        dprint(f"#  Variable '{var_name}': {variable}")
        enc_ops = variable.get("encode(operands)")
        if enc_ops and "reg2creg" in enc_ops:
            operand_value = operand_value - 8
            dprint(f"#        Applied reg2creg transformation, new value: {operand_value}")

        # Set the bits in the binary match string
        encoded = set_bits(encoded, bit_positions, operand_value)

    return encoded


def encode(assembly, xlen=64):
    # This function will take an assembly instruction and encode it into binary
    # For now, it's a placeholder that just prints the assembly instruction
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

    # Process assembly lines and print mnemonics
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
