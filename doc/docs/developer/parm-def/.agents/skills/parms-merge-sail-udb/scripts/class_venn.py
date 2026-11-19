#!/usr/bin/env python3
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Plot three-source parameter class counts from summary.json."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import warnings
from pathlib import Path
from typing import Any

CLASS_FILENAMES = {
    "0b000": "none.md",
    "0b001": "only-spec.md",
    "0b010": "only-udb.md",
    "0b011": "no-sail.md",
    "0b100": "only-sail.md",
    "0b101": "no-udb.md",
    "0b110": "no-spec.md",
    "0b111": "all.md",
}
SET_BITS = {"Spec": 0b001, "UDB": 0b010, "Sail": 0b100}
VENN_SET_ORDER = ("Spec", "UDB", "Sail")

# matplotlib-venn orders regions as A only, B only, A+B, C only,
# A+C, B+C, and A+B+C. The sets below are A=Spec, B=UDB, C=Sail.
VENN_REGIONS = (
    ("100", "0b001"),
    ("010", "0b010"),
    ("110", "0b011"),
    ("001", "0b100"),
    ("101", "0b101"),
    ("011", "0b110"),
    ("111", "0b111"),
)


def load_summary(
    summary_path: Path,
) -> tuple[dict[str, int], dict[str, str], dict[str, int]]:
    """Read class counts, report links, and validated source-set sizes."""
    try:
        data: Any = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read valid JSON from {summary_path}: {exc}") from exc

    if not isinstance(data, dict) or set(data) != {"sets", "classes"}:
        raise ValueError("summary.json must contain exactly 'sets' and 'classes'")
    if not isinstance(data["classes"], list):
        raise TypeError("summary.json 'classes' must be an array of class records")
    if not isinstance(data["sets"], list):
        raise TypeError("summary.json 'sets' must be an array of name/size records")

    set_sizes: dict[str, int] = {}
    for index, item in enumerate(data["sets"]):
        if not isinstance(item, dict) or set(item) != {"name", "size"}:
            raise ValueError(f"Set entry {index} must contain exactly name and size")
        name, size = item["name"], item["size"]
        if not isinstance(name, str) or name not in SET_BITS:
            raise ValueError(f"Set entry {index} has an unknown set name: {name!r}")
        if name in set_sizes:
            raise ValueError(f"Duplicate set entry: {name}")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise ValueError(f"Size for {name} must be a non-negative integer")
        set_sizes[name] = size
    if set(set_sizes) != set(SET_BITS):
        raise ValueError("summary.json must define Spec, Sail, and UDB set sizes")

    counts = {class_code: 0 for class_code in CLASS_FILENAMES}
    filenames: dict[str, str] = {}
    seen: set[str] = set()
    for index, item in enumerate(data["classes"]):
        if not isinstance(item, dict) or set(item) != {"class", "count", "filename"}:
            raise ValueError(f"Entry {index} must contain exactly class, count, and filename")

        class_code = item["class"]
        count = item["count"]
        filename = item["filename"]
        if not isinstance(class_code, str) or class_code not in CLASS_FILENAMES:
            raise ValueError(f"Entry {index} has an invalid three-bit class: {class_code!r}")
        if class_code in seen:
            raise ValueError(f"Duplicate class entry: {class_code}")
        seen.add(class_code)

        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError(f"Count for {class_code} must be a non-negative integer")
        if filename != CLASS_FILENAMES[class_code]:
            raise ValueError(
                f"{class_code} must use {CLASS_FILENAMES[class_code]!r}, not {filename!r}"
            )
        counts[class_code] = count
        filenames[class_code] = filename

    if "0b000" in seen:
        warnings.warn(
            "Alert: summary.json contains class 0b000 (no source contains the parameter).",
            stacklevel=2,
        )
        if counts["0b000"]:
            raise ValueError(
                "Class 0b000 has entries outside all three circles; "
                "resolve the unexpected class before plotting."
            )

    if sum(counts.values()) == 0:
        raise ValueError("All class counts are zero; there is nothing to plot")

    for name, bit in SET_BITS.items():
        expected_size = sum(
            count for class_code, count in counts.items() if int(class_code, 2) & bit
        )
        if set_sizes[name] != expected_size:
            raise ValueError(
                f"Size for {name} is {set_sizes[name]}, but class counts imply {expected_size}"
            )
    return counts, filenames, set_sizes


def load_class_counts(summary_path: Path) -> dict[str, int]:
    """Read validated counts (kept as a small helper for callers and tests)."""
    return load_summary(summary_path)[0]


def create_diagram(
    counts: dict[str, int],
    filenames: dict[str, str],
    set_sizes: dict[str, int],
    summary_path: Path,
    output_path: Path,
    overwrite: bool = False,
) -> None:
    """Write an SVG whose region counts link to their class reports."""
    try:
        import matplotlib.pyplot as plt
        from matplotlib_venn import venn3
    except ImportError as exc:
        raise RuntimeError(
            "This script requires matplotlib and matplotlib-venn in the selected "
            "Python environment; no packages were installed automatically."
        ) from exc

    output_path = output_path.expanduser().resolve()
    summary_path = summary_path.expanduser().resolve()
    if output_path.suffix.lower() != ".svg":
        raise ValueError("The output path must end in .svg")
    if not output_path.parent.is_dir():
        raise ValueError(f"Output directory does not exist: {output_path.parent}")
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"Output already exists: {output_path} (choose another path or pass --force)"
        )

    subset_sizes = tuple(counts[class_code] for _, class_code in VENN_REGIONS)
    figure, axis = plt.subplots(figsize=(8, 7))
    diagram = venn3(
        subsets=subset_sizes,
        set_labels=tuple(f"{name} ({set_sizes[name]})" for name in VENN_SET_ORDER),
        set_colors=("#4C78A8", "#F58518", "#54A24B"),
        alpha=0.55,
        ax=axis,
    )
    if diagram is None:
        plt.close(figure)
        raise RuntimeError("matplotlib-venn could not construct the diagram")

    for region_id, class_code in VENN_REGIONS:
        label = diagram.get_label_by_id(region_id)
        if label is not None:
            label.set_ha("left")
            filename = filenames.get(class_code)
            count_label = str(counts[class_code])
            if filename is not None:
                label.set_text(f"{count_label} [{filename}]")
            else:
                label.set_text(count_label)
            if filename is not None:
                report_path = (summary_path.parent / filename).resolve()
                relative_url = os.path.relpath(report_path, output_path.parent)
                label.set_url(urllib.parse.quote(relative_url.replace(os.sep, "/")))

    axis.set_title("Parameter counts by source class")
    figure.tight_layout()
    with plt.rc_context({"svg.fonttype": "none"}):
        figure.savefig(output_path, format="svg", bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create an SVG of summary.json counts as Spec/UDB/Sail Venn regions. "
            "Region areas use class counts and each count links to its class report."
        )
    )
    parser.add_argument("summary_json", type=Path, help="path to summary.json")
    parser.add_argument(
        "--output",
        type=Path,
        help="SVG output path (default: class-venn.svg next to summary.json)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace the output SVG if it already exists",
    )
    args = parser.parse_args()

    try:
        counts, filenames, set_sizes = load_summary(args.summary_json)
        output_path = args.output or args.summary_json.parent / "class-venn.svg"
        create_diagram(
            counts,
            filenames,
            set_sizes,
            args.summary_json,
            output_path,
            args.force,
        )
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote Venn diagram to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
