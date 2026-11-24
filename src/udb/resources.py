# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

"""Locate UDB data in a source checkout or an installed wheel."""

from __future__ import annotations

from importlib import metadata, resources
from pathlib import Path
from typing import Any

_CHECKOUT = Path(__file__).resolve().parents[2]


def package_data_root() -> Any:
    """Return the root that holds repository-relative data such as ``spec/std/isa``.

    A wheel holds a copy of the data in ``udb/_data``. A source checkout, including an
    editable install, uses the repository files directly.
    """

    bundled = resources.files("udb").joinpath("_data")
    if bundled.is_dir():
        return bundled
    if (_CHECKOUT / "pyproject.toml").is_file() and (_CHECKOUT / "spec/std/isa").is_dir():
        return _CHECKOUT
    raise metadata.PackageNotFoundError("udb data")
