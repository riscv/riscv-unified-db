# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

import unittest

from backends.generators.generator import parse_extension_requirements


class TestExtensionRequirements(unittest.TestCase):
    def test_parse_extension_requirements(self) -> None:
        req1 = {"extension": {"name": "Zbb"}}
        f1 = parse_extension_requirements(req1)
        self.assertTrue(f1(["Zbb", "I"]))
        self.assertFalse(f1(["I", "M"]))

        req2 = {"allOf": [{"xlen": 64}, {"extension": {"name": "Zbb"}}]}
        f2 = parse_extension_requirements(req2)
        self.assertTrue(f2(["Zbb"]))
        self.assertFalse(f2(["I"]))

        req3 = {"extension": {"anyOf": [{"name": "Zbb"}, {"name": "Zba"}]}}
        f3 = parse_extension_requirements(req3)
        self.assertTrue(f3(["Zba"]))
        self.assertTrue(f3(["Zbb"]))
        self.assertFalse(f3(["M"]))


if __name__ == "__main__":
    unittest.main()
