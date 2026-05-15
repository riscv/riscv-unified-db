#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

from __future__ import annotations

import argparse
import io
from contextlib import redirect_stdout

import decode
import encode
import gen_asm

import spec


def _silent_invoke(fn, *args, **kwargs):
    """Invoke fn while suppressing its stdout side effects."""
    with io.StringIO() as sink, redirect_stdout(sink):
        return fn(*args, **kwargs)


def _instruction_names(instructions: list[str]) -> list[str]:
    if instructions:
        return instructions
    return sorted(spec.instructions)


def iter_roundtrip_results(spec_dir: str, instructions: list[str], xlen: int = 64):
    """Yield (status_line, is_ok) for generated assembly examples."""
    spec.initialize_spec(spec_dir, quiet=True)

    # Keep imported tool modules quiet: this script emits only round-trip status lines.
    encode.quiet = True
    decode.quiet = True

    for instruction_name in _instruction_names(instructions):
        if instruction_name not in spec.instructions:
            raise KeyError(f"Instruction '{instruction_name}' not found")

        combos = gen_asm.list_instruction_operand_combinations(instruction_name, xlen)
        for combo in combos:
            example = gen_asm.render_instruction_combination(combo, xlen)

            opcode = _silent_invoke(encode.encode, example, xlen)
            if opcode is None:
                yield (f"KO {example}; ERROR", False)
                continue

            decoded = _silent_invoke(decode.decode, opcode, xlen, False)
            if decoded is None:
                yield (f"KO {example}; ERROR", False)
                continue

            if decoded == example:
                yield (f"OK: {example}", True)
            else:
                yield (f"KO {example}; {decoded}", False)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate, encode, decode, and compare RISC-V assembly examples."
    )
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
    parser.add_argument(
        "instructions",
        nargs="*",
        help="Instruction names to process (all loaded instructions if omitted)",
    )
    parser.add_argument(
        "--only-ko",
        action="store_true",
        help="Only print KO lines; suppress OK lines",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    had_error = False
    for line, is_ok in iter_roundtrip_results(args.spec, args.instructions, args.xlen):
        if not (args.only_ko and is_ok):
            print(line)
        if not is_ok:
            had_error = True

    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
