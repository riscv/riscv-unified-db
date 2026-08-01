#!/usr/bin/env python3
# Copyright (c) 2026 titoatwork
# SPDX-License-Identifier: BSD-3-Clause-Clear

"""Unit tests for check_param_enum_literals.py"""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

SCRIPT = Path(__file__).resolve().parents[1] / "check_param_enum_literals.py"

PARAM_YAML = dedent(
    """\
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
    """
)


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

    def _write_fixture(self, root: Path, compare_body: str, param_yaml: str = PARAM_YAML) -> None:
        """Minimal tree: one param + one file under spec/ with the compare."""
        param_dir = root / "spec" / "std" / "isa" / "param"
        other = root / "spec" / "std" / "isa" / "csr"
        param_dir.mkdir(parents=True)
        other.mkdir(parents=True)
        (param_dir / "DEMO_ENUM.yaml").write_text(param_yaml, encoding="utf-8")
        (other / "demo.yaml").write_text(
            dedent(
                f"""\
                kind: csr
                name: demo
                fields:
                  X:
                    type(): |
                {compare_body}
                """
            ),
            encoding="utf-8",
        )

    def test_valid_literal_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_fixture(
                root,
                compare_body='      if (DEMO_ENUM != "always zero") {\n'
                "        return CsrFieldType::RO;\n"
                "      }\n"
                "      return CsrFieldType::RW;\n",
            )
            self.assertEqual(self.mod.main(["--root", str(root)]), 0)

    def test_invalid_literal_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_fixture(
                root,
                compare_body='      if (DEMO_ENUM != "always_zero") {\n'
                "        return CsrFieldType::RO;\n"
                "      }\n"
                "      return CsrFieldType::RW;\n",
            )
            self.assertEqual(self.mod.main(["--root", str(root)]), 1)

    def test_unknown_param_name_ignored(self):
        """Comparisons of non-parameter identifiers are out of scope."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_fixture(
                root,
                compare_body='      if (NOT_A_PARAM != "always_zero") {\n'
                "        return CsrFieldType::RO;\n"
                "      }\n"
                "      return CsrFieldType::RW;\n",
            )
            self.assertEqual(self.mod.main(["--root", str(root)]), 0)

    def test_single_quoted_literal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_fixture(
                root,
                compare_body="      if (DEMO_ENUM != 'always zero') {\n"
                "        return CsrFieldType::RO;\n"
                "      }\n"
                "      return CsrFieldType::RW;\n",
            )
            self.assertEqual(self.mod.main(["--root", str(root)]), 0)

    def test_ruamel_loads_multiword_enum_members(self):
        """Enums with spaces (always zero) must load via ruamel, not only simple tokens."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            param_dir = root / "spec" / "std" / "isa" / "param"
            param_dir.mkdir(parents=True)
            (param_dir / "DEMO_ENUM.yaml").write_text(PARAM_YAML, encoding="utf-8")
            enums = self.mod.load_param_string_enums(param_dir)
            self.assertIn("DEMO_ENUM", enums)
            self.assertEqual(enums["DEMO_ENUM"], {"always zero", "custom"})

    def test_enum_without_type_field_still_loaded(self):
        """Some real params set schema.enum without schema.type (e.g. MTVEC_ILLEGAL_WRITE_BEHAVIOR)."""
        yaml = dedent(
            """\
            kind: parameter
            name: DEMO_NO_TYPE
            description: demo
            long_name: demo
            schema:
              enum:
                - retain
                - custom
            definedBy:
              extension:
                name: Sm
            """
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            param_dir = root / "spec" / "std" / "isa" / "param"
            param_dir.mkdir(parents=True)
            (param_dir / "DEMO_NO_TYPE.yaml").write_text(yaml, encoding="utf-8")
            enums = self.mod.load_param_string_enums(param_dir)
            self.assertEqual(enums.get("DEMO_NO_TYPE"), {"retain", "custom"})

    def test_non_parameter_kind_ignored(self):
        yaml = dedent(
            """\
            kind: csr
            name: DEMO_ENUM
            schema:
              type: string
              enum:
                - always zero
            """
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            param_dir = root / "spec" / "std" / "isa" / "param"
            param_dir.mkdir(parents=True)
            (param_dir / "DEMO_ENUM.yaml").write_text(yaml, encoding="utf-8")
            enums = self.mod.load_param_string_enums(param_dir)
            self.assertNotIn("DEMO_ENUM", enums)

    def test_missing_param_dir_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "spec").mkdir()
            self.assertEqual(self.mod.main(["--root", str(root)]), 2)

    def test_missing_spec_dir_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # param path missing too → still 2 (param checked first)
            self.assertEqual(self.mod.main(["--root", str(root)]), 2)


if __name__ == "__main__":
    unittest.main()
