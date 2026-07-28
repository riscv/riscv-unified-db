# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

"""Tests for backends/generators/generator.py."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from generator import load_exception_codes


def test_loads_and_sanitizes_codes(tmp_path):
    codes_file = tmp_path / "codes.json"
    codes_file.write_text(
        json.dumps(
            [
                {"num": 9, "name": "Environment Call from HS-mode"},
                {"num": 8, "name": "Environment Call from VU/U-mode"},
                {"num": 8, "name": "Duplicate that should be dropped"},
            ]
        )
    )

    assert load_exception_codes(str(codes_file)) == [
        (8, "environment_call_from_vu_u_mode"),
        (9, "environment_call_from_hs_mode"),
    ]


@pytest.mark.parametrize(
    "make_arg",
    [
        pytest.param(lambda tmp_path: None, id="none"),
        pytest.param(lambda tmp_path: "", id="empty"),
        pytest.param(lambda tmp_path: str(tmp_path / "does_not_exist.json"), id="missing"),
        pytest.param(lambda tmp_path: str(_write(tmp_path / "bad.json", "not json")), id="corrupt"),
    ],
)
def test_raises_instead_of_returning_empty(tmp_path, make_arg):
    """A missing or unparseable file must fail loudly, not yield zero exception codes.

    Returning an empty list here silently generates a header with no CAUSE_* entries.
    """
    with pytest.raises(ValueError):
        load_exception_codes(make_arg(tmp_path))


def _write(path, text):
    path.write_text(text)
    return path
