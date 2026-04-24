#!/usr/bin/env python3
import argparse
import sys
import json
import yaml
from pathlib import Path

yamls = []
instructions = {}
operand_list = []


def parse_args():
    parser = argparse.ArgumentParser(description="Process RISC-V instruction definitions")
    parser.add_argument("--assembly", type=str, help="Assembly language file to process")
    parser.add_argument(
        "--xlen",
        type=int,
        choices=[32, 64],
        default=64,
        help="RISC-V architecture width (32 or 64 bits, default: 64)",
    )
    parser.add_argument(
        "dirs", nargs="*", default=["."], help="Directories to search for YAML files"
    )
    return parser.parse_args()


def find_and_load_yamls(path, kind=None):
    p = Path(path)
    for file in p.rglob("*.yaml"):
        with open(file) as f:
            y = yaml.safe_load(f)
            if "kind" in y:
                if y["kind"] == kind:
                    y["file"] = file
                    yamls.append(y)
            else:
                print(f"No 'kind' field in {file}")


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


def parse_value_range(range_str):
    """Parse a numeric range string like '0-31', '-4096-4095', or '5' into (min_val, max_val)."""
    s = str(range_str).strip()
    try:
        if "-" in s:
            # Split at the last '-' to preserve a leading minus on the start
            # Note: this does not well handle a -X..-Y range
            idx = s.rfind("-")
            start_str = s[:idx]
            end_str = s[idx + 1 :]
            start = int(start_str)
            end = int(end_str)
            return (start, end)
        else:
            val = int(s)
            return (val, val)
    except ValueError as e:
        raise ValueError(f"Invalid range string: {range_str}") from e


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
    with open(filepath, "r") as f:
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

    print(
        f"#    Setting bits at positions {positions} to value {value} (field width {field_w}) in binary string: {binary_str}"
    )
    # Convert binary string to list for easier manipulation
    binary_list = list(binary_str)
    print(f"#    Initial binary list: {binary_list}")

    # Ensure value fits within the specified field width
    value = (value & ((1 << field_w) - 1)) if field_w > 0 else 0

    positions_rev = list(positions)[::-1]  # LSB of value goes to the last position

    # Set bits at specified positions
    for i, pos in enumerate(positions_rev):
        if i >= field_w:
            break
        bit_value = (value >> i) & 1
        print(f"#    Setting bit at position {pos} to {bit_value} (bit {i} of value)")

        # Convert bit position to string index (MSB at index 0)
        idx = instruction_width - pos - 1
        if idx < 0 or idx >= instruction_width:
            print(
                f"#    ERROR: Bit position {pos} out of range for instruction width {instruction_width}"
            )
            continue
        binary_list[idx] = "1" if bit_value else "0"
        print(f"#    binary list after setting bits: {binary_list}")

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
        if "optional" in operand_def and operand_def["optional"]:
            optional_operands += 1
    # print(f"possible operands = {len(instruction_operands)}; Optional operands = {optional_operands}; provided arguments = {len(arguments)}")

    optional_operands_to_keep = optional_operands - (len(instruction_operands) - len(arguments))
    # print(f"optional_operands_to_keep = {optional_operands_to_keep}")
    if optional_operands < optional_operands_to_keep:
        print(
            f"#    ERROR: insufficient arguments for instruction; got {len(arguments)} ({arguments}) needed at least {len(instruction_operands) - optional_operands}"
        )
        return {}

    # Map assembly arguments to instruction operands definition
    operand_values = {}
    argi = 0
    for i, operand_def in enumerate(instruction_operands):
        print(f'# operand {i}: "{operand_def}"; {len(arguments)}')
        operand_name = operand_def.get("name", f"op{i}")
        # print(operand_def)
        # print(optional_operands_to_keep)
        if "optional" in operand_def and operand_def["optional"]:
            if optional_operands_to_keep > 0:
                optional_operands_to_keep -= 1
            else:
                print(f'# Skipping optional operand "{operand_name}"')
                continue

        print(f"#    Creating operand '{operand_name}' ({operand_def['type']})")
        if operand_def["type"] in ["register", "register_pair"]:
            if "offset" in operand_def:
                print(f'#    memory argument with offset "{arguments[argi]}"')

                # Memory operand like "offset(rs1)"
                offset_part = arguments[argi].split("(")[0].strip()
                if offset_part == "":
                    offset_part = "0"
                reg_index = int(arguments[argi].split("(")[1].split(")")[0].strip())
                print(f"#    Extracted offset: {offset_part}, register: {reg_index}")

                # print(f"#{instruction_operands[i]}")
                operand_values[instruction_operands[i]["offset"]["name"]] = int(offset_part)

                if "length" in instruction_operands[i]["offset"]:
                    encoded_value = int(offset_part)
                    if "left_shifted" in instruction_operands[i]["offset"]:
                        encoded_value = (
                            encoded_value >> instruction_operands[i]["offset"]["left_shifted"]
                        )
                        if encoded_value << instruction_operands[i]["offset"][
                            "left_shifted"
                        ] != int(offset_part):
                            print(
                                f"#    ERROR: Offset value {offset_part} cannot be fully represented given the required shift"
                            )
                            return None
                    if encoded_value >> instruction_operands[i]["offset"]["length"] != 0:
                        print(
                            f"#    ERROR: Offset value {offset_part} exceeds the maximum representable value for {instruction_operands[i]['offset']['length']} bits"
                        )
                        return None

            else:
                print(f"#    Detected register argument: {arguments[i]}")
                reg_index = int(arguments[argi])

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
                        min_val, max_val = parse_value_range(operand_def["possible_values"])
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

            operand_values[instruction_operands[i]["name"]] = reg_index
            print(f"#    Final value for '{operand_name}': {reg_index}")
            operand_values[instruction_operands[i]["name"]] = int(reg_index)

        elif operand_def["type"] == "immediate":
            print(f'#    immediate argument: "{arguments[argi]}"')
            imm_value = int(arguments[argi])
            if "possible_values" in operand_def:
                if isinstance(
                    operand_def["possible_values"], list
                ) and imm_value not in operand_def.get("possible_values", []):
                    print(
                        f"#    ERROR: Immediate value {imm_value} is not valid, must be {operand_def.get('possible_values', [])}"
                    )
                    return None
                elif isinstance(operand_def["possible_values"], str):
                    try:
                        min_val, max_val = parse_value_range(operand_def["possible_values"])
                    except ValueError:
                        print(
                            f"#    ERROR: Invalid possible_values range for '{operand_name}': {operand_def['possible_values']}"
                        )
                        return None
                    if imm_value < min_val or imm_value > max_val:
                        print(
                            f"#    ERROR: Immediate value {imm_value} is out of range, must be between {min_val} and {max_val}"
                        )
                        return None

            operand_values[instruction_operands[i]["name"]] = imm_value
            print(f"#    Final value for '{operand_name}': {imm_value}")

        elif operand_def["type"] == "fence_scope":
            print(f"#    Detected fence_scope argument: {arguments[argi]}")

            operand_values[instruction_operands[i]["name"]] = arguments[i]
            print(f"#    Final value for '{operand_name}': {arguments[argi]}")

        elif operand_def["type"] == "rounding_mode":
            print(f"#    Detected rounding_mode argument: {arguments[argi]}")

            operand_values[instruction_operands[i]["name"]] = arguments[i]
            print(f"#    Final value for '{operand_name}': {arguments[argi]}")

        elif operand_def["type"] == "reg_range":
            print(f"#    Detected reg_range argument: {arguments[argi]}")

            operand_values[instruction_operands[i]["name"]] = arguments[i]
            print(f"#    Final value for '{operand_name}': {arguments[argi]}")

        # consume argument
        argi += 1

    print(f"#    Parsed operand values: {operand_values}")
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

    print(f"#  Parsed assembly operands: {assembly_operands}")

    encoded = match_pattern

    # Process each variable
    for variable in variables:
        var_name = variable["name"]
        location = variable["location"]

        print(f'# Fill in "{var_name}"')

        # Find the operand value from assembly operands
        operand_value = 0  # Default value

        # Try to find the operand value based on the variable name
        if var_name not in assembly_operands:
            if "encode(operands)" in variable:
                if "return 1;" in variable["encode(operands)"]:  # vector mask
                    operand_value = 1
                elif "return 0;" in variable["encode(operands)"]:
                    operand_value = 0
                elif "reg_list" in variable["encode(operands)"]:
                    operand_value = builtin_encode_reg_list(assembly_operands)
                elif "stack_adj" in variable["encode(operands)"]:  # stack_adj
                    operand_value = builtin_encode_stack_adj(assembly_operands, xlen)
                else:
                    print(f"#  ERROR: unsupported variable encoding")
                    return None
            else:
                print(f"#  ERROR: unknown variable encoding")
                return None
        else:
            print(
                f"#  Found direct match for variable '{var_name}' in assembly operands {assembly_operands[var_name]}"
            )
            if "encode(operands)" in variable and "iorw" in variable["encode(operands)"]:
                operand_value = builtin_encode_fence_scope(assembly_operands[var_name])
                if operand_value is None:
                    return None
            elif "encode(operands)" in variable and "rtz" in variable["encode(operands)"]:
                operand_value = builtin_encode_rounding_mode(assembly_operands[var_name])
                if operand_value is None:
                    return None
            elif "encode(operands)" in variable and (
                "r1s" in variable["encode(operands)"] or "r2s" in variable["encode(operands)"]
            ):
                operand_value = builtin_encode_sreg(assembly_operands[var_name])
            else:
                operand_value = assembly_operands[var_name]

        print(f"#  Variable '{var_name}' value: {operand_value}")

        # Parse the location string to get bit positions
        bit_positions = parse_location(location)

        # Apply any shifts specified in the variable
        if "left_shift" in variable:
            operand_value = operand_value >> variable["left_shift"]
            print(f"#  Unapplied left shift {variable['left_shift']}, new value: {operand_value}")

        print(f"#  Variable '{var_name}': {variable}")
        enc_ops = variable.get("encode(operands)")
        if enc_ops and "reg2creg" in enc_ops:
            operand_value = operand_value - 8
            print(f"#        Applied reg2creg transformation, new value: {operand_value}")

        # Set the bits in the binary match string
        encoded = set_bits(encoded, bit_positions, operand_value)

    return encoded


def encode(assembly, xlen=64):
    # This function will take an assembly instruction and encode it into binary
    # For now, it's a placeholder that just prints the assembly instruction
    print(f"#Encoding assembly instruction: {assembly} with xlen={xlen}")

    mnemonic = extract_mnemonic(assembly)
    if not mnemonic:
        return None

    print(f"#mnemonic: {mnemonic}")
    if mnemonic not in instructions:
        print(f"# ERROR: Instruction '{mnemonic}' not found in YAML definitions")
        return None

    inst = instructions[mnemonic]

    filled_match = fill_in_variables(inst, assembly, xlen)

    print(f"#  Filled match pattern:  {filled_match}")
    return filled_match


def main():
    args = parse_args()

    # Validate xlen parameter
    xlen = args.xlen
    if xlen not in [32, 64]:
        print(f"# ERROR: xlen must be either 32 or 64, got {xlen}")
        sys.exit(1)
    print(f"# Using RISC-V {xlen}-bit architecture (xlen={xlen})")

    for path in args.dirs:
        find_and_load_yamls(path, kind="instruction")

    # Create a dictionary mapping instruction mnemonics to their definitions
    for instruction in yamls:
        instructions[instruction["name"]] = instruction

    assembly_lines = []
    if args.assembly:
        assembly_lines = read_assembly_file(args.assembly)

    # Process assembly lines and print mnemonics
    if assembly_lines:
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
