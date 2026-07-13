#!/usr/bin/env python3
# Copyright (c) 2026 Contributors to the RISCV UnifiedDB <https://github.com/riscv/riscv-unified-db>
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""
Phase 8: Insert ``[#param:NAME]`` tags into the riscv-isa-manual spec.

For every row in the Phase 7 spreadsheet, locate the verbatim excerpt in the
matching ``.adoc`` file and wrap it with ``[#param:NAME]#excerpt#`` — following
the existing ``[#norm:NAME]#text#`` convention already used ~1,361 times in
the upstream spec.

LLM-reported line numbers are advisory only (LLMs notoriously mis-count
lines); the matcher works on whitespace-normalized text across the whole
file and uses the line number purely as a proximity tiebreaker.

Edge cases handled:
  - Excerpt is already wrapped in a ``[#norm:NAME]#...#`` block      →
      emit a bare ``[#param:NAME]`` anchor on the preceding line so the
      anchor still attaches to the same paragraph without breaking the
      existing inline norm wrap.
  - Excerpt spans multiple source lines                              →
      wrap the entire span (joined by the original whitespace).
  - Multiple parameters on the same line                             →
      processed in left-to-right offset order, with offsets adjusted
      after each insertion.
  - Excerpt cannot be located                                        →
      logged and emitted to ``unmatched.csv`` for manual review; the
      ``.adoc`` file is not modified.

Modes:
  run     - tag every matchable row, write a per-file diff summary
  dry-run - same matching, but no files are modified (default)
  verify  - run asciidoctor on every modified file and check for errors

Inputs (defaults; configurable via CLI):
  - param_extraction/data/parameters.csv        (Phase 7 spreadsheet)
  - ext/riscv-isa-manual/src/*.adoc             (target files)

Outputs:
  - Modified .adoc files (in-place, under ext/riscv-isa-manual/src/)
  - param_extraction/data/tagging_report.txt    (per-file statistics)
  - param_extraction/data/tagging_unmatched.csv (rows that could not be located)
"""

from __future__ import annotations

import argparse
import csv
import logging
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
REPO_ROOT = PROJECT_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
DEFAULT_SPEC_DIR = REPO_ROOT / "ext" / "riscv-isa-manual" / "src"

logger = logging.getLogger("phase8")

# Matches an existing inline reference tag: [#prefix:NAME]#...#
INLINE_TAG_RE = re.compile(r"\[#(?P<prefix>norm|param):[A-Za-z0-9_\-]+\]#")

# Confidence ordering for cross-row tie-breaking (more confident first).
CONFIDENCE_RANK = {"high": 3, "medium": 2, "low": 1}


# ── Data structures ───────────────────────────────────────────────────────


@dataclass
class TagRequest:
    adoc_file: str
    line_number: int
    excerpt: str
    parameter_name: str
    named: str
    cls: str
    confidence: str


@dataclass
class TagResult:
    request: TagRequest
    matched: bool
    start_offset: int = -1  # char offset in the (joined) source text
    end_offset: int = -1
    overlap_with_norm: bool = False
    anchor_offset: int = -1  # offset where a bare anchor should attach (for overlap case)
    reason: str = ""


@dataclass
class FileStats:
    file: str
    requested: int = 0
    inserted: int = 0
    bare_anchors: int = 0
    unmatched: int = 0
    overlaps: int = 0
    failures: list[str] = field(default_factory=list)


# ── CSV loader ────────────────────────────────────────────────────────────


def load_requests(csv_path: Path, min_confidence: str = "medium") -> list[TagRequest]:
    min_rank = CONFIDENCE_RANK[min_confidence]
    requests: list[TagRequest] = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            conf = (row.get("confidence") or "low").lower()
            if CONFIDENCE_RANK.get(conf, 0) < min_rank:
                continue
            try:
                line_number = int(row["line_number"])
            except (KeyError, ValueError):
                continue
            requests.append(
                TagRequest(
                    adoc_file=row["adoc_file"].strip(),
                    line_number=line_number,
                    excerpt=row["excerpt"].strip(),
                    parameter_name=row["parameter_name"].strip(),
                    named=row.get("named", "no"),
                    cls=row.get("class", ""),
                    confidence=conf,
                )
            )
    logger.info("Loaded %d tag requests (confidence ≥ %s)", len(requests), min_confidence)
    return requests


# ── Whitespace-normalized fuzzy matcher ───────────────────────────────────


# Common AsciiDoc attribute refs that the LLM renders as their unicode form.
ASCIIDOC_UNICODE_MAP = {
    "≥": " ",
    "≤": " ",
    "≠": " ",
    "→": " ",
    "←": " ",
    "\u2014": "-",  # em dash
    "\u2013": "-",  # en dash
    "`": " ",
    "*": " ",
    "_": " ",
}

ASCIIDOC_ATTR_REFS = re.compile(r"\{(?:ge|le|ne|gt|lt|to|from|leftarrow|rightarrow|times|nbsp)\}")


def _normalize(
    text: str,
    inline_spans: list[tuple[int, int]] | None = None,
) -> tuple[str, list[int]]:
    """Collapse whitespace and AsciiDoc markup; return (normalized, src_index_map).

    The normalized text:
      - drops ``[#prefix:NAME]#`` openers and the matching closing ``#`` of every
        inline tag span (if ``inline_spans`` is provided);
      - replaces AsciiDoc attribute refs (``{ge}``, ``{le}`` …) with a single
        space, since the LLM excerpts use the rendered unicode characters;
      - replaces common rendered unicode characters (``≥``, ``≤`` …) with a
        single space — they match either form via whitespace collapse;
      - drops backticks, asterisks and underscores (asciidoc inline markup);
      - collapses whitespace runs to a single space.

    ``src_index_map[i]`` is the index in ``text`` corresponding to the *i*-th
    character of the normalized string. Lets us project a match back to
    original-text offsets.
    """
    spans = inline_spans or []
    # Build a quick "skip mask": chars that should not appear in the
    # normalized output. We use a sparse set of (start, end) skip ranges so
    # the per-char loop stays O(N).
    skip_ranges: list[tuple[int, int]] = []
    for s, e in spans:
        # Opener: from '[' to and including the '#' after ']'.
        m = INLINE_TAG_RE.match(text, s)
        if m:
            skip_ranges.append((m.start(), m.end()))
        # Closer: the single '#' character at position e-1.
        if e - 1 >= 0 and e - 1 < len(text) and text[e - 1] == "#":
            skip_ranges.append((e - 1, e))
    # Replace asciidoc attribute refs with spaces.
    for m in ASCIIDOC_ATTR_REFS.finditer(text):
        skip_ranges.append((m.start(), m.end()))
    skip_ranges.sort()
    skip_iter = iter(skip_ranges)
    next_skip = next(skip_iter, None)

    out_chars: list[str] = []
    out_map: list[int] = []
    in_ws = False
    i = 0
    while i < len(text):
        if next_skip and i >= next_skip[0] and i < next_skip[1]:
            i = next_skip[1]
            next_skip = next(skip_iter, None)
            # Treat the skipped region as whitespace.
            if not in_ws and out_chars:
                out_chars.append(" ")
                out_map.append(i)
            in_ws = True
            continue
        ch = text[i]
        if ch in ASCIIDOC_UNICODE_MAP:
            ch = ASCIIDOC_UNICODE_MAP[ch]
        if ch.isspace():
            if not in_ws and out_chars:
                out_chars.append(" ")
                out_map.append(i)
            in_ws = True
        else:
            out_chars.append(ch.lower())
            out_map.append(i)
            in_ws = False
        i += 1
    return "".join(out_chars), out_map


def _strip_excerpt(excerpt: str) -> str:
    """Strip leading bullets and collapse whitespace."""
    s = excerpt.strip()
    s = re.sub(r"^[-*•]+\s*", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def compute_inline_tag_spans(file_text: str) -> list[tuple[int, int]]:
    """Return [(start, end), ...] for every existing ``[#prefix:NAME]#text#`` span.

    Implementation: find every ``[#prefix:NAME]#`` opener via the regex, then
    scan forward for the matching closing ``#``. The closer is the next ``#``
    that is not part of another opener.
    """
    spans: list[tuple[int, int]] = []
    for m in INLINE_TAG_RE.finditer(file_text):
        start = m.start()
        cursor = m.end()  # position just after the opening "]#"
        while cursor < len(file_text):
            nxt = file_text.find("#", cursor)
            if nxt < 0:
                break
            # If this '#' starts a new opener `[#prefix:...`, skip past it.
            inner = INLINE_TAG_RE.match(file_text, nxt - 1)
            if inner and inner.start() == nxt - 1:
                cursor = inner.end()
                continue
            spans.append((start, nxt + 1))
            break
    return spans


def _span_containing(spans: list[tuple[int, int]], offset: int) -> tuple[int, int] | None:
    for s, e in spans:
        if s <= offset < e:
            return (s, e)
        if s > offset:
            break
    return None


def find_excerpt(
    file_text: str,
    line_starts: list[int],
    request: TagRequest,
    inline_spans: list[tuple[int, int]] | None = None,
) -> TagResult:
    """Locate the excerpt in ``file_text``; return char offsets on success."""
    needle_raw = _strip_excerpt(request.excerpt)
    norm_text, idx_map = _normalize(file_text, inline_spans=inline_spans)
    norm_needle, _ = _normalize(needle_raw, inline_spans=[])

    if not norm_needle:
        return TagResult(request, matched=False, reason="empty excerpt")

    # Find all occurrences and pick the one closest to the LLM-reported line.
    occurrences: list[int] = []
    start = 0
    while True:
        pos = norm_text.find(norm_needle, start)
        if pos < 0:
            break
        occurrences.append(pos)
        start = pos + 1

    if not occurrences:
        return TagResult(request, matched=False, reason="excerpt not found")

    target_offset = (
        line_starts[request.line_number - 1]
        if 0 < request.line_number <= len(line_starts)
        else 0
    )

    # Project each normalized-index occurrence back to the source-text offset
    # then pick the one closest to the LLM-reported line.
    def src_offset(norm_pos: int) -> int:
        return idx_map[norm_pos] if norm_pos < len(idx_map) else len(file_text)

    best = min(occurrences, key=lambda p: abs(src_offset(p) - target_offset))
    start_src = src_offset(best)
    end_norm = best + len(norm_needle) - 1
    end_src = src_offset(end_norm) + 1

    # Overlap with an existing [#norm:...] / [#param:...] inline tag span?
    if inline_spans is None:
        inline_spans = compute_inline_tag_spans(file_text)
    enclosing = _span_containing(inline_spans, start_src)
    overlap = enclosing is not None or any(
        s < end_src and e > start_src for (s, e) in inline_spans if s != start_src
    )
    # For overlap cases the anchor should attach to the line where the
    # *enclosing* norm tag opens, not where the match itself sits (which may
    # be several lines deep inside the norm span).
    anchor_offset = enclosing[0] if enclosing else start_src

    return TagResult(
        request,
        matched=True,
        start_offset=start_src,
        end_offset=end_src,
        overlap_with_norm=overlap,
        anchor_offset=anchor_offset,
    )


# ── File-level tagger ─────────────────────────────────────────────────────


def _line_starts(text: str) -> list[int]:
    starts = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            starts.append(i + 1)
    return starts


def _offset_to_line(line_starts: list[int], offset: int) -> int:
    # Binary search would be faster; linear is fine for our file sizes.
    lo, hi = 0, len(line_starts) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if line_starts[mid] <= offset:
            lo = mid
        else:
            hi = mid - 1
    return lo + 1  # 1-indexed


def tag_file(
    src_path: Path,
    requests: list[TagRequest],
    apply: bool = False,
) -> tuple[FileStats, str, list[TagResult]]:
    """Apply all tag requests for one file. Returns (stats, new_text, results)."""
    text = src_path.read_text(encoding="utf-8")
    starts = _line_starts(text)
    stats = FileStats(file=str(src_path.relative_to(REPO_ROOT)), requested=len(requests))
    inline_spans = compute_inline_tag_spans(text)

    results = [find_excerpt(text, starts, r, inline_spans=inline_spans) for r in requests]

    # Drop unmatched / collect failure reasons
    matched_results = [r for r in results if r.matched]
    for r in results:
        if not r.matched:
            stats.unmatched += 1
            stats.failures.append(f"  ✗ {r.request.parameter_name}: {r.reason}")

    # De-duplicate same-name same-offset requests (defensive: shouldn't happen
    # in Phase 7 output but cheap to guard against).
    seen_keys: set[tuple[str, int]] = set()
    unique_results: list[TagResult] = []
    for r in matched_results:
        key = (r.request.parameter_name, r.start_offset)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        unique_results.append(r)

    # Sort by descending start offset so insertions don't perturb earlier offsets.
    unique_results.sort(key=lambda r: r.start_offset, reverse=True)

    new_text = text
    for r in unique_results:
        name = r.request.parameter_name
        original = new_text[r.start_offset : r.end_offset]

        if r.overlap_with_norm or INLINE_TAG_RE.search(original):
            # Place a bare AsciiDoc inline anchor immediately before the
            # enclosing norm tag's opener (or, if there is no enclosing tag,
            # before the start of the match). Using ``anchor:NAME[]`` is the
            # standard inline anchor form and never disrupts paragraph flow.
            attach_offset = r.anchor_offset if r.anchor_offset >= 0 else r.start_offset
            anchor = f"[#param:{name}]##"
            new_text = new_text[:attach_offset] + anchor + new_text[attach_offset:]
            stats.bare_anchors += 1
            stats.overlaps += 1
            stats.inserted += 1
            continue

        wrapped = f"[#param:{name}]#{original}#"
        new_text = new_text[: r.start_offset] + wrapped + new_text[r.end_offset :]
        stats.inserted += 1

    if apply and new_text != text:
        src_path.write_text(new_text, encoding="utf-8")
        logger.info("Updated %s (+%d tags)", stats.file, stats.inserted)

    return stats, new_text, results


# ── AsciiDoc validation ───────────────────────────────────────────────────


def validate_asciidoc(files: list[Path]) -> dict[str, str]:
    """Run asciidoctor on each file (if available) and return file → error."""
    if not shutil.which("asciidoctor"):
        logger.warning("asciidoctor not on PATH; skipping AsciiDoc validation")
        return {}
    errors: dict[str, str] = {}
    for f in files:
        try:
            proc = subprocess.run(
                [
                    "asciidoctor",
                    "--no-header-footer",
                    "--failure-level=ERROR",
                    "-o",
                    "/dev/null",
                    str(f),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if proc.returncode != 0:
                errors[str(f)] = proc.stderr.strip() or "non-zero exit"
        except Exception as e:
            errors[str(f)] = f"validation error: {e}"
    return errors


# ── CLI ───────────────────────────────────────────────────────────────────


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "mode",
        choices=["run", "dry-run", "verify"],
        nargs="?",
        default="dry-run",
        help="run = write tags into .adoc files; dry-run = match only; verify = asciidoctor",
    )
    p.add_argument(
        "--csv",
        type=Path,
        default=DATA_DIR / "parameters.csv",
        help="Phase 7 spreadsheet",
    )
    p.add_argument(
        "--spec-dir",
        type=Path,
        default=DEFAULT_SPEC_DIR,
        help="Directory containing the .adoc files",
    )
    p.add_argument(
        "--report",
        type=Path,
        default=DATA_DIR / "tagging_report.txt",
        help="Human-readable per-file report",
    )
    p.add_argument(
        "--unmatched",
        type=Path,
        default=DATA_DIR / "tagging_unmatched.csv",
        help="CSV of rows that could not be located",
    )
    p.add_argument(
        "--min-confidence",
        choices=["low", "medium", "high"],
        default="medium",
    )
    p.add_argument(
        "--only",
        action="append",
        default=None,
        help="Restrict to specific .adoc filenames (repeatable)",
    )
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    if not args.csv.exists():
        logger.error("Missing spreadsheet: %s", args.csv)
        return 2
    if not args.spec_dir.exists():
        logger.error(
            "Missing spec dir: %s. Run `git submodule update --init ext/riscv-isa-manual`",
            args.spec_dir,
        )
        return 2

    requests = load_requests(args.csv, min_confidence=args.min_confidence)
    if args.only:
        only_set = set(args.only)
        requests = [r for r in requests if r.adoc_file in only_set]
        logger.info("Filtered to %d requests across %s", len(requests), sorted(only_set))

    by_file: dict[str, list[TagRequest]] = defaultdict(list)
    for r in requests:
        by_file[r.adoc_file].append(r)

    all_stats: list[FileStats] = []
    all_unmatched: list[TagResult] = []
    apply = args.mode == "run"
    touched_files: list[Path] = []

    for fname, file_requests in sorted(by_file.items()):
        path = args.spec_dir / fname
        if not path.exists():
            logger.warning("Spec file not present, skipping: %s", path)
            continue
        stats, _new, results = tag_file(path, file_requests, apply=apply)
        all_stats.append(stats)
        all_unmatched.extend(r for r in results if not r.matched)
        if stats.inserted > 0 and (apply or args.mode == "verify"):
            touched_files.append(path)

    # Write report
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with open(args.report, "w", encoding="utf-8") as f:
        f.write("Phase 8 — Parameter Tag Insertion Report\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Mode             : {args.mode}\n")
        f.write(f"Spec directory   : {args.spec_dir}\n")
        f.write(f"Spreadsheet      : {args.csv}\n")
        f.write(f"Min confidence   : {args.min_confidence}\n\n")
        total_req = sum(s.requested for s in all_stats)
        total_ins = sum(s.inserted for s in all_stats)
        total_un = sum(s.unmatched for s in all_stats)
        total_ov = sum(s.overlaps for s in all_stats)
        total_ba = sum(s.bare_anchors for s in all_stats)
        f.write(f"Requests         : {total_req}\n")
        f.write(f"Tags inserted    : {total_ins}\n")
        f.write(f"  inline wraps   : {total_ins - total_ba}\n")
        f.write(f"  bare anchors   : {total_ba}\n")
        f.write(f"Overlaps w/ norm : {total_ov}\n")
        f.write(f"Unmatched rows   : {total_un}\n\n")

        f.write("Per-file breakdown:\n")
        for s in sorted(all_stats, key=lambda x: -x.inserted):
            f.write(
                f"  {s.file:60s}  req={s.requested:3d}  "
                f"ins={s.inserted:3d}  bare={s.bare_anchors:2d}  "
                f"unmatched={s.unmatched:2d}\n"
            )
        f.write("\nFailures:\n")
        for s in all_stats:
            for fail in s.failures:
                f.write(f"  [{s.file}]\n{fail}\n")
    logger.info("Wrote %s", args.report)

    # Write unmatched CSV
    if all_unmatched:
        with open(args.unmatched, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(
                [
                    "adoc_file",
                    "line_number",
                    "parameter_name",
                    "class",
                    "confidence",
                    "reason",
                    "excerpt",
                ]
            )
            for r in all_unmatched:
                w.writerow(
                    [
                        r.request.adoc_file,
                        r.request.line_number,
                        r.request.parameter_name,
                        r.request.cls,
                        r.request.confidence,
                        r.reason,
                        r.request.excerpt,
                    ]
                )
        logger.info("Wrote %s (%d rows)", args.unmatched, len(all_unmatched))

    if args.mode == "verify" and touched_files:
        errors = validate_asciidoc(touched_files)
        if errors:
            logger.error("AsciiDoc validation found %d error(s):", len(errors))
            for path, err in errors.items():
                logger.error("  %s\n    %s", path, err)
            return 1
        logger.info("AsciiDoc validation passed on %d files", len(touched_files))

    return 0


if __name__ == "__main__":
    sys.exit(main())
