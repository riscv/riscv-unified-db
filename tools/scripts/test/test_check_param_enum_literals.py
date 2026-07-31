#!/usr/bin/env python3
# Copyright (c) 2026 titoatwork
# SPDX-License-Identifier: BSD-3-Clause-Clear

"""Unit tests for check_param_enum_literals.py"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "check_param_enum_literals.py"


def load_module():
    spec = importlib.util.spec_from_file_location("check_param_enum_literals", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestCheckParamEnumLiterals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module()

    def _write_tree(self, root: Path, param_yaml: str, csr_yaml: str) -> None:
        param_dir = root / "spec" / "std" / "isa" / "param"
        csr_dir = root / "spec" / "std" / "isa" / "csr" / "H"
        param_dir.mkdir(parents=True)
        csr_dir.mkdir(parents=True)
        (root / "spec" / "std" / "isa" / "isa").mkdir(parents=True)
        (root / "spec" / "std" / "isa" / "inst").mkdir(parents=True)
        (param_dir / "DEMO_ENUM.yaml").write_text(param_yaml, encoding="utf-8")
        (csr_dir / "demo.yaml").write_text(csr_yaml, encoding="utf-8")

    def test_valid_literal_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_tree(
                root,
                param_yaml="""\
$schema: param_schema.json#
kind: parameter
name: DEMO_ENUM
description: demo
long_name: demo
schema:
  type: string
  enum:
    - always zero
    - custom
definedBy:
  extension:
    name: H
""",
                csr_yaml="""\
kind: csr
name: demo
fields:
  X:
    type(): |
      if (DEMO_ENUM != "always zero") {
        return CsrFieldType::RO;
      }
      return CsrFieldType::RW;
""",
            )
            self.assertEqual(self.mod.main(["--root", str(root)]), 0)

    def test_invalid_literal_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_tree(
                root,
                param_yaml="""\
$schema: param_schema.json#
kind: parameter
name: DEMO_ENUM
description: demo
long_name: demo
schema:
  type: string
  enum:
    - always zero
    - custom
definedBy:
  extension:
    name: H
""",
                csr_yaml="""\
kind: csr
name: demo
fields:
  X:
    type(): |
      if (DEMO_ENUM != "always_zero") {
        return CsrFieldType::RO;
      }
      return CsrFieldType::RW;
""",
            )
            self.assertEqual(self.mod.main(["--root", str(root)]), 1)

    def test_unknown_param_name_ignored(self):
        """Comparisons of non-parameter identifiers are out of scope."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_tree(
                root,
                param_yaml="""\
$schema: param_schema.json#
kind: parameter
name: DEMO_ENUM
description: demo
long_name: demo
schema:
  type: string
  enum:
    - always zero
definedBy:
  extension:
    name: H
""",
                csr_yaml="""\
kind: csr
name: demo
fields:
  X:
    type(): |
      if (NOT_A_PARAM != "always_zero") {
        return CsrFieldType::RO;
      }
      return CsrFieldType::RW;
""",
            )
            self.assertEqual(self.mod.main(["--root", str(root)]), 0)


if __name__ == "__main__":
    unittest.main()
