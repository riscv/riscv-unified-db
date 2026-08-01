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

Scope and known limits
----------------------
* Parameter enums are loaded with ruamel YAML (typ=safe) from
  ``spec/std/isa/param/*.yaml``.
* Call sites are scanned under the entire ``spec/`` tree, restricted to ordinary
  files whose names contain a dot (e.g. ``foo.yaml``), so extension-less junk is
  skipped.
* Comparisons are matched only in the form ``PARAM op "literal"`` or
  ``PARAM op 'literal'`` (parameter name on the left). The reverse form
  ``"literal" op PARAM`` is legal IDL but is not checked; it is expected to be
  rare or absent in this tree. Extend COMPARE_RE if that form appears.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

ROOT = Path(__file__).resolve().parents[2]
PARAM_DIR = ROOT / "spec" / "std" / "isa" / "param"
SPEC_ROOT = ROOT / "spec"

# Safe loader shared with other UDB Python tooling (see tools/python/udb.py).
YAML_SAFE = YAML(typ="safe")


def repo_paths(root: Path) -> tuple[Path, Path]:
    """Return (param_dir, spec_root) for a repository root.

    Uses module globals PARAM_DIR / SPEC_ROOT when ``root`` is this checkout,
    so the default path is not re-derived by string concatenation in main().
    """
    root = root.resolve()
    if root == ROOT:
        return PARAM_DIR, SPEC_ROOT
    return root / "spec" / "std" / "isa" / "param", root / "spec"


# PARAM == "literal" or PARAM != 'literal'
# group(1) = parameter name
# group(2) = operator (== or !=)
# group(3) = literal when double-quoted
# group(4) = literal when single-quoted
# (Only one of group(3)/group(4) is set per match.)
#
# Robustness: does not match "literal" == PARAM (parameter on the right).
COMPARE_RE = re.compile(r"""\b([A-Z][A-Z0-9_]*)\s*(==|!=)\s*(?:"([^"]*)"|'([^']*)')""")


def load_param_string_enums(param_dir: Path) -> dict[str, set[str]]:
    """Map parameter name -> set of schema.enum string values (ruamel YAML)."""
    enums: dict[str, set[str]] = {}
    if not param_dir.is_dir():
        return enums

    for path in sorted(param_dir.glob("*.yaml")):
        try:
            with path.open(encoding="utf-8") as handle:
                doc = YAML_SAFE.load(handle)
        except (OSError, YAMLError) as exc:
            print(f"ERROR: could not load {path}: {exc}", file=sys.stderr)
            continue

        if not isinstance(doc, dict):
            continue

        # Only true parameter objects (defensive; param/ should be all kind: parameter).
        if doc.get("kind") != "parameter":
            continue

        name = doc.get("name")
        schema = doc.get("schema")
        if not isinstance(name, str) or not isinstance(schema, dict):
            continue

        enum_vals = schema.get("enum")
        if not isinstance(enum_vals, list):
            continue

        # Only string members matter for string-literal compares in IDL.
        # Include even when schema.type is missing (some params only set enum).
        values = {v for v in enum_vals if isinstance(v, str)}
        if values:
            enums[name] = values

    return enums


def iter_scan_files(spec_root: Path) -> list[Path]:
    """All files under spec/ whose basename contains a '.' (has an extension)."""
    files: list[Path] = []
    if not spec_root.is_dir():
        return files

    for path in spec_root.rglob("*"):
        if not path.is_file():
            continue
        # ?*.?* style: require a dot in the filename so we skip extension-less paths.
        if "." not in path.name:
            continue
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
        except (OSError, UnicodeDecodeError) as exc:
            # Skip unreadable / binary-ish files under spec/.
            print(f"WARNING: could not read {path}: {exc}", file=sys.stderr)
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            for match in COMPARE_RE.finditer(line):
                param = match.group(1)
                if param not in enums:
                    continue
                op = match.group(2)
                # group(3) = double-quoted literal; group(4) = single-quoted.
                literal = match.group(3) if match.group(3) is not None else match.group(4)
                assert literal is not None
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

    param_dir, spec_root = repo_paths(root)

    if not param_dir.is_dir():
        print(f"ERROR: param directory not found: {param_dir}", file=sys.stderr)
        return 2

    if not spec_root.is_dir():
        print(f"ERROR: spec directory not found: {spec_root}", file=sys.stderr)
        return 2

    enums = load_param_string_enums(param_dir)
    files = iter_scan_files(spec_root)
    bad = find_invalid_compares(enums, files)

    print(
        f"Checked {len(enums)} string-enum parameters across {len(files)} files under "
        f"spec/; found {len(bad)} invalid literal comparison(s)."
    )

    if not bad:
        print("OK: every PARAM ==/!= string literal is a member of that parameter's schema.enum.")
        return 0

    print("ERROR: string literal is not in the parameter's schema.enum:", file=sys.stderr)
    for path, line_no, param, op, literal, line in bad:
        try:
            rel = path.relative_to(root)
        except ValueError:
            rel = path
        allowed = ", ".join(repr(v) for v in sorted(enums[param]))
        print(f"  {rel}:{line_no}: {param} {op} {literal!r}", file=sys.stderr)
        print(f"    allowed: [{allowed}]", file=sys.stderr)
        print(f"    line: {line}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
