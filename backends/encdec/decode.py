#!/usr/bin/env python3
import argparse
import sys
import json
import yaml
from pathlib import Path

yamls = []
instructions = {}
instruction_by_match = {}

def parse_args():
    parser = argparse.ArgumentParser(description='Decode RISC-V opcodes to assembly instructions')
    parser.add_argument('--opcodes', type=str, help='File containing opcodes to decode')
    parser.add_argument('--xlen', type=int, choices=[32, 64], default=64, help='RISC-V architecture width (32 or 64 bits)')
    parser.add_argument('dirs', nargs='*', default=["."], help='Directories to search for YAML files')
    return parser.parse_args()

def find_and_load_yamls(path, kind=None):
    p = Path(path)
    for file in p.rglob('*.yaml'):
        with open(file) as f:
            y = yaml.safe_load(f)
            if 'kind' in y:
                if y['kind'] == kind:
                    y['file'] = file
                    yamls.append(y)
            else:
                print(f"No 'kind' field in {file}")

def read_opcodes(f):
    """Read file containing opcodes and return its contents as an array of strings"""
    return [line.strip() for line in f.readlines() if line.strip()]

def parse_location(location):
    """Parse location string into a list of bit positions"""
    print(f"# Parsing location: {location}")
    bit_positions = []

    # Handle concatenated locations (separated by '|')
    if '|' in location:
        segments = location.split('|')
        for segment in segments:
            bit_positions.extend(parse_location(segment))
        print(f"# Parsed concatenated location '{location}' into bit positions: {bit_positions}")
        return bit_positions

    # Handle range locations (e.g., '31-25')
    if '-' in location:
        start, end = location.split('-')
        start, end = int(start), int(end)
        for bit in range(start, end - 1, -1):
            bit_positions.append(bit)
    else:
        # Single bit location
        bit_positions.append(int(location))

    print(f"# Parsed location '{location}' into bit positions: {bit_positions}")
    return bit_positions

def extract_bits(binary_str, positions):
    """Extract bits from specified positions in the binary string"""
    width = len(positions)
    result = 0

    # Convert binary string to list for easier manipulation
    binary_list = list(binary_str)

    # Extract bits from specified positions
    print(f"# Extracting bits from binary string '{binary_str}' at positions {positions}")
    for pos in positions:
        print(f"# Processing bit position {pos}")
        idx = len(binary_list) - 1 - pos  # Calculate index from the right
        bit_value = 1 if binary_str[idx] == '1' else 0
        result = (result << 1) | bit_value
        print(f"# Bit at position {pos} is '{binary_str[idx]}' result {result}")

    return result

def matches_pattern(opcode, pattern):
    """Check if opcode matches the pattern (considering '-' as wildcards)"""
    if len(opcode) != len(pattern):
        return False

    for i in range(len(opcode)):
        if pattern[i] != '-' and opcode[i] != pattern[i]:
            return False

    return True

def find_matching_instruction(opcode, xlen=64):
    """Find instruction that matches the given opcode"""
    for name, instruction in instructions.items():
        if 'encoding' in instruction:
            encoding = instruction['encoding']
            match_pattern = None

            # Extract match pattern based on encoding format and xlen
            if f'RV{xlen}' in encoding and 'match' in encoding[f'RV{xlen}']:
                match_pattern = encoding[f'RV{xlen}']['match']
            elif 'match' in encoding:
                match_pattern = encoding['match']
            elif 'RV32' in encoding and 'match' in encoding['RV32'] and xlen == 32:
                match_pattern = encoding['RV32']['match']
            elif 'RV64' in encoding and 'match' in encoding['RV64'] and xlen == 64:
                match_pattern = encoding['RV64']['match']

            if match_pattern and matches_pattern(opcode, match_pattern):
                return instruction

    return None

def extract_variable_values(opcode, instruction, xlen=64):
    """Extract variable values from opcode based on instruction definition"""
    encoding = instruction['encoding']
    variables = []

    # Extract variables based on encoding format and xlen
    if f'RV{xlen}' in encoding and 'variables' in encoding[f'RV{xlen}']:
        variables = encoding[f'RV{xlen}']['variables']
    elif 'variables' in encoding:
        variables = encoding['variables']
    elif 'RV32' in encoding and 'variables' in encoding['RV32'] and xlen == 32:
        variables = encoding['RV32']['variables']
    elif 'RV64' in encoding and 'variables' in encoding['RV64'] and xlen == 64:
        variables = encoding['RV64']['variables']

    variable_values = {}

    # Process each variable
    for variable in variables:
        var_name = variable['name']
        location = variable['location']

        # Parse the location string to get bit positions
        bit_positions = parse_location(location)
        print(f"# Variable '{var_name}' is located at bits {bit_positions} in the opcode")

        # Extract the value from the opcode
        value = extract_bits(opcode, bit_positions)
        print(f"# Extracted raw value for variable '{var_name}': {value} from bits {bit_positions}")

        # Apply any transformations

        if 'sign_extend' in variable:
            sign_bit = 1 << (len(bit_positions) - 1)
            if value & sign_bit:
                value -= (1 << len(bit_positions))
            print(f"# Value after sign extension for variable '{var_name}': {value}")
        if 'left_shift' in variable:
            value = value << variable['left_shift']
            print(f"# Value after left shift for variable '{var_name}': {value}")

        if 'decode()' in variable and 'creg2reg' in variable['decode()']:
            value += 8
            print(f"# Value after creg2reg transformation for variable '{var_name}': {value}")

        variable_values[var_name] = value

    return variable_values

def format_assembly(instruction, variable_values, xlen=64):
    """Format assembly instruction based on instruction definition and variable values"""
    mnemonic = instruction['name']

    if 'operands' not in instruction:
        print(f"# INFO: No operands defined for instruction '{mnemonic}'")
        return None

    if 'RV32' in instruction['operands'] and xlen == 32:
        operands = instruction['operands']['RV32']
    elif 'RV64' in instruction['operands'] and xlen == 64:
        operands = instruction['operands']['RV64']
    else:
        operands = instruction['operands']

    if 'RV32' in instruction['encoding']['variables'] and xlen == 32:
        variables = instruction['encoding']['variables']['RV32']
    elif 'RV64' in instruction['encoding']['variables'] and xlen == 64:
        variables = instruction['encoding']['variables']['RV64']
    else:
        variables = instruction['encoding']['variables']

    assembly_parts = []

    # For regular instructions with operands
    for i, operand in enumerate(operands):
        operand_name = operand['name']

        print(f"# Processing operand '{operand_name}' ({operand['type']})")

        if operand['type'] == 'fence_scope':
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
                0b0001: "w"
            }

            value = variable_values[operand_name]
            if value not in scope_map:
                print(f"# ERROR: unknown fence scope {value}")
                continue
            assembly_parts.append(scope_map[value])

        elif operand['type'] == 'rounding_mode':
            rm_map = {
                0b000: "rne",
                0b001: "rtz",
                0b010: "rdn",
                0b011: "rup",
                0b100: "rmm",
                0b111: "dyn"
            }

            value = variable_values[operand_name]
            if value not in rm_map:
                print(f"# ERROR: unknown rounding mode {value}")
                continue
            assembly_parts.append(rm_map[value])

        elif 'offset' in operand:
            value = variable_values[operand_name]
            print(f"# Handling offset for operand '{operand_name}' with value {value}")
            if operand['offset']['name'] == '':
                offset_value = ''
            else:
                offset_value = variable_values[operand['offset']['name']]
                if 'left_shift' in operand['offset']:
                    offset_value = offset_value << operand['offset']['left_shift']
            assembly_parts.append(f"{offset_value}({value})")

        elif operand['type'] == 'reg_range':
            print(f"# Handling reg_range \"{operand}\" {variable_values}")
            which_reg_range = 0;
            opi = i-1
            while opi >= 0:
                if operands[opi]['type'] != 'reg_range':
                    break
                opi -= 1
                which_reg_range += 1
            if which_reg_range == 0:
                if variable_values['rlist'] >= 4:
                    assembly_parts.append('x1') # use ABI names?
            elif which_reg_range == 1:
                if variable_values['rlist'] == 5:
                    assembly_parts.append('x8')
                elif variable_values['rlist'] >= 6:
                    assembly_parts.append('x8-x9')
            elif which_reg_range == 2:
                if variable_values['rlist'] == 7:
                    assembly_parts.append('x18')
                elif variable_values['rlist'] == 8:
                    assembly_parts.append('x18-x19')
                elif variable_values['rlist'] == 9:
                    assembly_parts.append('x18-x20')
                elif variable_values['rlist'] == 10:
                    assembly_parts.append('x18-x21')
                elif variable_values['rlist'] == 11:
                    assembly_parts.append('x18-x22')
                elif variable_values['rlist'] == 12:
                    assembly_parts.append('x18-x23')
                elif variable_values['rlist'] == 13:
                    assembly_parts.append('x18-x24')
                elif variable_values['rlist'] == 14:
                    assembly_parts.append('x18-x25')
                elif variable_values['rlist'] == 15:
                    assembly_parts.append('x18-x27')

        elif 'optional' in operand:
            value = variable_values[operand_name]
            if value == 0: # vector mask
                assembly_parts.append(f"v0.t")

        elif operand_name == "stack_adj":
            print("# Handling stack_adj")
            registers = variable_values['rlist'] - 3
            register_space = registers * int(xlen/8)
            register_space_aligned = int((register_space + 15) / 16) * 16
            extra_space = variable_values['spimm'] * 16
            total_space = register_space_aligned + extra_space
            assembly_parts.append(str(-total_space))

        else:
            value = variable_values[operand_name]
            for variable in variables:
                if variable['name'] == operand_name:
                    if 'decode()' in variable:
                        if 'r1s' in variable['decode()'] or 'r2s' in variable['decode()']:
                            value = value + 8 + 8 * ((value + 6) // 8)
                    break
            print(f"# map {operand_name} {value}")
            assembly_parts.append(str(value))

    if assembly_parts:
        return f"{mnemonic} {', '.join(assembly_parts)}"

    # Default case: just return the mnemonic
    return mnemonic

def decode(opcode, xlen=64):
    """Decode an opcode into an assembly instruction"""
    print(f"# Decoding opcode: {opcode} with xlen={xlen}")

    # Find matching instruction
    instruction = find_matching_instruction(opcode, xlen)
    if not instruction:
        print(f"# No matching instruction found for opcode: {opcode}")
        return None

    print(f"# Found matching instruction: {instruction['name']}")

    # Extract variable values from opcode
    variable_values = extract_variable_values(opcode, instruction, xlen)
    print(f"# Extracted variable values: {variable_values}")

    # Format assembly instruction
    assembly = format_assembly(instruction, variable_values, xlen)
    print(f"# Formatted assembly: {assembly}")

    return assembly

def main():
    args = parse_args()

    # Validate xlen parameter
    xlen = args.xlen
    if xlen not in [32, 64]:
        print(f"Error: xlen must be either 32 or 64, got {xlen}")
        sys.exit(1)
    print(f"# Using RISC-V {xlen}-bit architecture (xlen={xlen})")

    for path in args.dirs:
        find_and_load_yamls(path, kind="instruction")

    # Create a dictionary mapping instruction mnemonics to their definitions
    for instruction in yamls:
        instructions[instruction['name']] = instruction

    opcodes = []
    f = sys.stdin
    if args.opcodes:
        f = open(filepath, 'r')
    opcodes = read_opcodes(f)

    # Process opcodes and print assembly instructions
    if opcodes:
        for opcode in opcodes:
            opcode = opcode.split('#')[0].strip()  # Remove comments and whitespace
            if not opcode:
                continue  # Skip empty lines
            assembly = decode(opcode, xlen)
            if assembly:
                print(f"{assembly}")
            else:
                print(f"Failed to decode '{opcode}'")

if __name__ == "__main__":
    main()
