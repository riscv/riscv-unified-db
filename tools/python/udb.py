#!/usr/bin/env python3
# Copyright (c) Ventana Micro Systems
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Python utilities for using UDB"""

from collections.abc import Iterable
from pathlib import Path

from ruamel.yaml import YAML

YAML_SAFE = YAML(typ="safe")


def find_and_load_yaml(path: str | Path, kinds: Iterable[str] | None = None) -> list[dict]:
    """Load the YAML files in a directory hierarchy into an array of dictionaries.

    Optionally, restrict to specific "kinds" of YAML files.
    """
    database = []

    kinds_set = set(kinds) if kinds else None

    p = Path(path)
    for file in p.rglob("*.yaml"):
        with file.open(encoding="utf-8") as f:
            y = YAML_SAFE.load(f)
            if (
                isinstance(y, dict)
                and "kind" in y
                and (kinds_set is None or y["kind"] in kinds_set)
            ):
                y["file"] = file
                database.append(y)
    return database
