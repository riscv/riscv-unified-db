#!/usr/bin/env python3
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

"""Publish resolved schema files as GitHub release assets."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GEN_SCHEMAS_DIR = ROOT / "gen" / "schemas"
SCHEMA_PAGES_URL = "https://riscv.github.io/riscv-unified-db/schemas"


def schema_versions(schemas_dir: Path) -> Iterator[tuple[str, str, Path]]:
    for schema_dir in sorted(path for path in schemas_dir.iterdir() if path.is_dir()):
        for version_dir in sorted(path for path in schema_dir.iterdir() if path.is_dir()):
            yield schema_dir.name, version_dir.name, version_dir


def release_exists(tag: str) -> bool:
    return (
        subprocess.run(
            ["gh", "release", "view", tag],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )


def create_release(schema_name: str, version: str, tag: str) -> None:
    published_url = f"{SCHEMA_PAGES_URL}/{schema_name}/{version}/{schema_name}"
    notes = (
        f"{schema_name} version {version} for riscv-unified-db.\n\nPublished at:\n{published_url}"
    )

    print(f"  Creating release {tag}...")
    subprocess.run(
        [
            "gh",
            "release",
            "create",
            tag,
            "--title",
            f"{schema_name} {version}",
            "--notes",
            notes,
            "--latest=false",
        ],
        check=True,
    )


def asset_content(tag: str, asset_name: str) -> str | None:
    result = subprocess.run(
        ["gh", "release", "download", tag, "--pattern", asset_name, "--output", "-"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout if result.returncode == 0 else None


def publish_asset(tag: str, schema_file: Path) -> None:
    asset_name = schema_file.name
    local_content = schema_file.read_text(encoding="utf-8").strip()
    remote_content = asset_content(tag, asset_name)

    if remote_content is not None and remote_content.strip() == local_content:
        print(f"  Unchanged: {asset_name}")
        return

    action = "Uploading new" if remote_content is None else "Updating changed"
    print(f"  {action} asset: {asset_name}")
    subprocess.run(["gh", "release", "upload", tag, str(schema_file), "--clobber"], check=True)


def main() -> None:
    if not GEN_SCHEMAS_DIR.is_dir():
        sys.exit("gen/schemas does not exist; run './do gen:schemas' first")

    for schema_name, version, version_dir in schema_versions(GEN_SCHEMAS_DIR):
        tag = f"schemas/{schema_name}/{version}"
        print(f"Processing {schema_name} {version}")

        if not release_exists(tag):
            create_release(schema_name, version, tag)

        for schema_file in sorted(version_dir.glob("*.json")):
            publish_asset(tag, schema_file)

    print("Schema release publishing complete.")


if __name__ == "__main__":
    main()
