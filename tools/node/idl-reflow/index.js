#!/usr/bin/env node
// Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
// SPDX-License-Identifier: BSD-3-Clause-Clear
//
// idl-reflow — reflow long IDL lines to fit a target column width.
//
// Scans each line for semantically appropriate break points (logical operators,
// commas) on lines that exceed the target width, inserts line breaks at those
// points, then re-runs topiary to clean up indentation.  Intended as a
// pre-processing step for narrow-column output (e.g., documentation PDFs).
//
// Usage:
//   node tools/node/idl-reflow/index.js <width> [files...]
//   node tools/node/idl-reflow/index.js 60 file.idl          # in-place
//   echo 'IDL source' | node tools/node/idl-reflow/index.js 60   # stdin→stdout

'use strict';

const fs = require('fs');

// ---------------------------------------------------------------------------
// Break-point configuration
// ---------------------------------------------------------------------------

// Tokens where we break AFTER (operator stays at end of line), by priority (2 = highest).
const BREAK_AFTER = {
  '||': 2, '&&': 2,
  ',':  2,
  '+': 1, '`+': 1,
  '-': 1, '`-': 1,
  '*': 1, '`*': 1,
  '|': 1, '&': 1, '^': 1,
};

// Tokens where we break BEFORE (operator starts the next line), by priority.
const BREAK_BEFORE = {
  '?': 2,
  ':': 2,
};

// ---------------------------------------------------------------------------
// Pure-JS lexer: find break candidates on a single source line
// ---------------------------------------------------------------------------
//
// Scans the line character-by-character, skipping:
//   - string literals  "..." and '...'
//   - backtick-prefixed operators like `+ `- (treated as a single token)
//   - line comments //...
// Returns the same { priority, breakPos, breakCol, breakBefore } shape as
// the old tree-sitter version (breakPos = byte offset from start of `source`).

function breakCandidatesForLine(source, lineStart, lineLen) {
  const results = [];
  const end = lineStart + lineLen;
  let i = lineStart;

  while (i < end) {
    const ch = source[i];

    // Skip string literals
    if (ch === '"' || ch === "'") {
      const quote = ch;
      i++;
      while (i < end && source[i] !== quote) {
        if (source[i] === '\\') i++; // skip escaped char
        i++;
      }
      i++; // closing quote
      continue;
    }

    // Line comments — nothing useful after this
    if (ch === '#') break;
    if (ch === '/' && source[i + 1] === '/') break;

    // Two-character operators first
    const two = source.slice(i, i + 2);
    if (BREAK_AFTER[two] !== undefined) {
      const col = i - lineStart;
      results.push({ priority: BREAK_AFTER[two], breakPos: i + 2, breakCol: col + 2, breakBefore: false });
      i += 2;
      continue;
    }

    // Backtick operators: `+ `- `*
    if (ch === '`') {
      const tok = source.slice(i, i + 2);
      if (BREAK_AFTER[tok] !== undefined) {
        const col = i - lineStart;
        results.push({ priority: BREAK_AFTER[tok], breakPos: i + 2, breakCol: col + 2, breakBefore: false });
        i += 2;
        continue;
      }
      i++;
      continue;
    }

    // Single-character break-after operators (but not when part of && || already consumed)
    if (BREAK_AFTER[ch] !== undefined) {
      const col = i - lineStart;
      results.push({ priority: BREAK_AFTER[ch], breakPos: i + 1, breakCol: col + 1, breakBefore: false });
      i++;
      continue;
    }

    // Single-character break-before operators
    if (BREAK_BEFORE[ch] !== undefined) {
      // Skip '::' — scope resolution operator is not a break point
      if (ch === ':' && source[i + 1] === ':') { i += 2; continue; }
      // Skip '?' when preceded by a word character — it's part of a predicate
      // function name (e.g. implemented_version?) not a ternary operator
      if (ch === '?' && i > lineStart && /\w/.test(source[i - 1])) { i++; continue; }
      const col = i - lineStart;
      results.push({ priority: BREAK_BEFORE[ch], breakPos: i, breakCol: col, breakBefore: true });
      i++;
      continue;
    }

    i++;
  }

  results.sort((a, b) => a.breakCol - b.breakCol);
  return results;
}

// ---------------------------------------------------------------------------
// Break-point selection (unchanged from original)
// ---------------------------------------------------------------------------

function bestBreakPoint(candidates, maxWidth) {
  let best = null;

  for (const c of candidates) {          // left-to-right
    if (c.breakCol <= maxWidth) {
      if (
        !best ||
        c.breakCol > best.breakCol ||
        (c.breakCol === best.breakCol && c.priority > best.priority)
      ) {
        best = c;
      }
    }
  }

  // Nothing fits within maxWidth — take the leftmost candidate so we at
  // least make progress on shortening the line.
  if (!best && candidates.length > 0) best = candidates[0];
  return best;
}

// ---------------------------------------------------------------------------
// Core reflow logic
// ---------------------------------------------------------------------------

function insertBreak(source, pos, indent) {
  return source.slice(0, pos) + '\n' + indent + source.slice(pos);
}

function continuationIndent(line) {
  return (line.match(/^(\s*)/) || ['', ''])[1];
}

function alreadyAtLineStart(source, index) {
  const lineStart = source.lastIndexOf('\n', index - 1) + 1;
  return source.slice(lineStart, index).trim() === '';
}

// Find all '?' and ':' positions on the same row as `breakPos` for ternary grouping.
// Pure-JS version: scans the line for ? and : at the top nesting level.
function ternaryPairedPositions(source, lineStart, lineLen, isBefore) {
  const end = lineStart + lineLen;
  const positions = [];
  let i = lineStart;
  let depth = 0;

  while (i < end) {
    const ch = source[i];
    if (ch === '(' || ch === '[' || ch === '{') { depth++; i++; continue; }
    if (ch === ')' || ch === ']' || ch === '}') { depth--; i++; continue; }
    if (depth === 0 && (ch === '?' || ch === ':')) {
      // Skip '::' — scope-resolution operator is not a ternary operator
      if (ch === ':' && source[i + 1] === ':') { i += 2; continue; }
      // Skip '?' when preceded by a word character — predicate function name, not ternary
      if (ch === '?' && i > lineStart && /\w/.test(source[i - 1])) { i++; continue; }
      positions.push(i);
    }
    i++;
  }
  return positions;
}

function reflow(source, maxWidth) {
  // Each break inserts a newline, and the shortest breakable token span is 2 chars
  // (e.g. "||"), so at most ceil(sourceLength / 2) breaks are ever needed.
  // The old `lines * 4` was too small when a single very long line arrived (e.g.
  // when topiary failed on pass 1 and the formatter fell back to an unformatted
  // one-liner containing many chained operators).
  const MAX_ITERS = Math.ceil(source.length / 2);
  let current = source;
  const skipRows = new Set();

  for (let iter = 0; iter < MAX_ITERS; iter++) {
    const lines = current.split('\n');

    let longRow = -1;
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].length > maxWidth && !skipRows.has(i)) { longRow = i; break; }
    }
    if (longRow === -1) break;

    // Compute byte offset of the start of longRow in current
    let lineStart = 0;
    for (let r = 0; r < longRow; r++) lineStart += lines[r].length + 1;

    const lineLen = lines[longRow].length;
    const candidates = breakCandidatesForLine(current, lineStart, lineLen);
    const bp = candidates.length > 0 ? bestBreakPoint(candidates, maxWidth) : null;

    if (!bp) {
      skipRows.add(longRow);
      continue;
    }

    const indent = continuationIndent(lines[longRow]);
    let breakPositions;

    // For ternary operators, break before all ? and : on the line at once
    if (bp.breakBefore && (current[bp.breakPos] === '?' || current[bp.breakPos] === ':')) {
      const paired = ternaryPairedPositions(current, lineStart, lineLen);
      if (paired.length > 1) {
        breakPositions = paired
          .filter(pos => !alreadyAtLineStart(current, pos))
          .sort((a, b) => b - a); // right-to-left
      }
    }

    if (!breakPositions || breakPositions.length === 0) {
      breakPositions = [bp.breakPos];
    }

    for (const pos of breakPositions) {
      current = insertBreak(current, pos, indent);
    }

    const numInserted = breakPositions.length;
    const shifted = new Set();
    for (const r of skipRows) shifted.add(r > longRow ? r + numInserted : r);
    skipRows.clear();
    for (const r of shifted) skipRows.add(r);
  }

  return current;
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

const args = process.argv.slice(2);

if (args.length === 0) {
  process.stderr.write(
    'usage: idl-reflow <max-width> [files...]\n' +
    '       echo IDL | idl-reflow <max-width>\n'
  );
  process.exit(1);
}

const maxWidth = parseInt(args[0], 10);
if (isNaN(maxWidth) || maxWidth < 1) {
  process.stderr.write(`idl-reflow: invalid width: ${args[0]}\n`);
  process.exit(1);
}

const files = args.slice(1);

if (files.length === 0) {
  // Stdin → stdout mode
  let data = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => { data += chunk; });
  process.stdin.on('end', () => {
    process.stdout.write(reflow(data, maxWidth));
    process.exit(0);
  });
} else {
  // In-place mode
  let exitCode = 0;
  for (const file of files) {
    try {
      const source   = fs.readFileSync(file, 'utf8');
      const reflowed = reflow(source, maxWidth);
      if (reflowed !== source) fs.writeFileSync(file, reflowed, 'utf8');
    } catch (err) {
      process.stderr.write(`idl-reflow: ${file}: ${err.message}\n`);
      exitCode = 1;
    }
  }
  process.exit(exitCode);
}
