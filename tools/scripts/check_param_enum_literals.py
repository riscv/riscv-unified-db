#!/usr/bin/env python3
# Copyright (c) 2026 titoatwork
# SPDX-License-Identifier: BSD-3-Clause-Clear

"""Fail if IDL/YAML compares a string-enum parameter to a literal not in its enum.

Parameter files under spec/std/isa/param declare legal string values with
schema.enum. Call sites (CSR type() IDL, globals.isa, etc.) sometimes compare
those parameters to string literals. A typo such as "always_zero" where the
enum only lists "always zero" is silently wrong: the comparison is always true
or always false and no schema check catches it.

See https://github.com/riscv/riscv-unified-db/issues/2285
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARAM_DIR = ROOT / "spec" / "std" / "isa" / "param"
SCAN_ROOTS = [
    ROOT / "spec" / "std" / "isa" / "csr",
    ROOT / "spec" / "std" / "isa" / "isa",
    ROOT / "spec" / "std" / "isa" / "inst",
    ROOT / "spec" / "std" / "isa" / "param",
]
SCAN_SUFFIXES = {".yaml", ".yml", ".isa", ".idl"}

# PARAM == "literal" or PARAM != "literal" (double or single quotes)
COMPARE_RE = re.compile(r"""\b([A-Z][A-Z0-9_]*)\s*(==|!=)\s*(?:"([^"]*)"|'([^']*)')""")


def load_param_string_enums(param_dir: Path) -> dict[str, set[str]]:
    """Map parameter name -> set of schema.enum string values."""
    enums: dict[str, set[str]] = {}
    for path in sorted(param_dir.glob("*.yaml")):
        text = path.read_text(encoding="utf-8")
        name_m = re.search(r"(?m)^name:\s*(\S+)", text)
        if not name_m:
            continue
        name = name_m.group(1)

        schema_m = re.search(r"(?m)^schema:\n((?:  .*\n)*)", text)
        if not schema_m:
            continue
        schema = schema_m.group(1)
        enum_m = re.search(r"(?m)^\s+enum:\n((?:\s+-\s+.+\n)+)", schema)
        if not enum_m:
            continue

        values: set[str] = set()
        for line in enum_m.group(1).splitlines():
            item_m = re.match(r"\s+-\s+(.+)$", line)
            if not item_m:
                continue
            raw = item_m.group(1).strip()
            if (raw.startswith('"') and raw.endswith('"')) or (
                raw.startswith("'") and raw.endswith("'")
            ):
                raw = raw[1:-1]
            values.add(raw)

        if values:
            enums[name] = values
    return enums


def iter_scan_files(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in SCAN_SUFFIXES:
                files.append(path)
    return sorted(files)


def find_invalid_compares(
    enums: dict[str, set[str]], files: list[Path]
) -> list[tuple[Path, int, str, str, str, str]]:
    """Return (path, line_no, param, op, literal, line_text) for bad compares."""
    bad: list[tuple[Path, int, str, str, str, str]] = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"ERROR: could not read {path}: {exc}", file=sys.stderr)
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            for match in COMPARE_RE.finditer(line):
                param = match.group(1)
                if param not in enums:
                    continue
                op = match.group(2)
                literal = match.group(3) if match.group(3) is not None else match.group(4)
                if literal in enums[param]:
                    continue
                bad.append((path, line_no, param, op, literal, line.strip()))
    return bad


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Repository root (default: inferred from script location)",
    )
    args = parser.parse_args(argv)
    root: Path = args.root.resolve()

    param_dir = root / "spec" / "std" / "isa" / "param"
    if not param_dir.is_dir():
        print(f"ERROR: param directory not found: {param_dir}", file=sys.stderr)
        return 2

    enums = load_param_string_enums(param_dir)
    scan_roots = [
        root / "spec" / "std" / "isa" / "csr",
        root / "spec" / "std" / "isa" / "isa",
        root / "spec" / "std" / "isa" / "inst",
        root / "spec" / "std" / "isa" / "param",
    ]
    files = iter_scan_files(scan_roots)
    bad = find_invalid_compares(enums, files)

    print(
        f"Checked {len(enums)} string-enum parameters across {len(files)} files; "
        f"found {len(bad)} invalid literal comparison(s)."
    )

    if not bad:
        print("OK: every PARAM ==/!= string literal is a member of that parameter's schema.enum.")
        return 0

    print("ERROR: string literal is not in the parameter's schema.enum:", file=sys.stderr)
    for path, line_no, param, op, literal, line in bad:
        rel = path.relative_to(root) if path.is_relative_to(root) else path
        allowed = ", ".join(repr(v) for v in sorted(enums[param]))
        print(f"  {rel}:{line_no}: {param} {op} {literal!r}", file=sys.stderr)
        print(f"    allowed: [{allowed}]", file=sys.stderr)
        print(f"    line: {line}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
