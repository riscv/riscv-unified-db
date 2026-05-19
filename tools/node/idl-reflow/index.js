#!/usr/bin/env node
// Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
// SPDX-License-Identifier: BSD-3-Clause-Clear
//
// idl-reflow — reflow long IDL lines to fit a target column width.
//
// Uses the tree-sitter IDL grammar to find semantically appropriate break
// points (logical operators, commas) on lines that exceed the target width,
// inserts line breaks at those points, then re-runs topiary to clean up
// indentation.  Intended as a pre-processing step for narrow-column output
// (e.g., documentation PDFs).
//
// Usage:
//   node tools/node/idl-reflow/index.js <width> [files...]
//   node tools/node/idl-reflow/index.js 60 file.idl          # in-place
//   echo 'IDL source' | node tools/node/idl-reflow/index.js 60   # stdin→stdout

'use strict';

const path   = require('path');
const fs     = require('fs');

// Resolve tree-sitter and the IDL language from the sibling tree-sitter-idl
// package, which is already built and has its own node_modules.
const TREE_SITTER_IDL_DIR = path.join(__dirname, '..', 'tree-sitter-idl');
const Parser = require(path.join(TREE_SITTER_IDL_DIR, 'node_modules', 'tree-sitter'));
const IDL    = require(path.join(TREE_SITTER_IDL_DIR, 'bindings', 'node'));

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
// Tree-sitter helpers
// ---------------------------------------------------------------------------

const _parser = new Parser();
_parser.setLanguage(IDL);

function parse(source) {
  return _parser.parse(source);
}

// Collect all potential break-point tokens on `targetRow` (0-indexed).
// Returns an array of { node, priority, breakPos, breakCol } sorted left-to-right
// by breakCol.  breakPos/breakCol reflect whether the break is before or after the token.
function breakCandidates(rootNode, targetRow) {
  const results = [];

  function visit(n) {
    if (n.endPosition.row   < targetRow) return;
    if (n.startPosition.row > targetRow) return;

    if (n.childCount === 0 && n.startPosition.row === targetRow) {
      const afterPri = BREAK_AFTER[n.type];
      if (afterPri !== undefined) {
        results.push({ node: n, priority: afterPri,
          breakPos: n.endIndex, breakCol: n.endPosition.column, breakBefore: false });
      }
      const beforePri = BREAK_BEFORE[n.type];
      if (beforePri !== undefined) {
        results.push({ node: n, priority: beforePri,
          breakPos: n.startIndex, breakCol: n.startPosition.column, breakBefore: true });
      }
    }

    for (let i = 0; i < n.childCount; i++) visit(n.child(i));
  }

  visit(rootNode);
  results.sort((a, b) => a.breakCol - b.breakCol);
  return results;
}

// Pick the best break point for a line exceeding maxWidth.
//
// Strategy: prefer the RIGHTMOST candidate whose end-column is ≤ maxWidth
// (the left part of the line fits).  If no candidate fits within the limit,
// fall back to the leftmost available candidate (at least make some progress).
// When multiple candidates share the same position, prefer higher priority.
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

// Insert a newline after byte offset `pos` in `source`.
// `indent` is the whitespace string placed at the start of the continuation.
function insertBreak(source, pos, indent) {
  return source.slice(0, pos) + '\n' + indent + source.slice(pos);
}

// Derive the indentation string for a continuation line.
// We keep the same leading whitespace as the current line.  Topiary will
// re-indent properly on its second formatting pass; this just ensures
// the continuation isn't at column 0.
function continuationIndent(line) {
  return (line.match(/^(\s*)/) || ['', ''])[1];
}

// Given a ternary '?' or ':' node, return all '?' and ':' direct children of
// its parent ternary_expression (i.e. the sibling operators including itself).
// Returns null if the parent is not a ternary_expression.
function ternaryPairedOps(node) {
  const parent = node.parent;
  if (!parent || parent.type !== 'ternary_expression') return null;
  const ops = [];
  for (let i = 0; i < parent.childCount; i++) {
    const child = parent.child(i);
    if (child.type === '?' || child.type === ':') ops.push(child);
  }
  return ops;
}

// True if byte offset `index` in `source` is preceded only by whitespace
// since the last newline (i.e. the token is already at a line start).
function alreadyAtLineStart(source, index) {
  const lineStart = source.lastIndexOf('\n', index - 1) + 1;
  return source.slice(lineStart, index).trim() === '';
}

// Reflow `source` so that no line exceeds `maxWidth` columns.
// Returns the modified source string.
function reflow(source, maxWidth) {
  const MAX_ITERS = source.split('\n').length * 4;  // generous safety cap
  let current = source;
  // Row indices (0-based) where we found no break candidates — skip these
  // when searching for the next long line to avoid an infinite loop.
  const skipRows = new Set();

  for (let iter = 0; iter < MAX_ITERS; iter++) {
    const lines = current.split('\n');

    // Find the first long line that isn't stuck.
    let longRow = -1;
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].length > maxWidth && !skipRows.has(i)) { longRow = i; break; }
    }
    if (longRow === -1) break;  // no more breakable long lines — done

    const tree = parse(current);
    const candidates = breakCandidates(tree.rootNode, longRow);
    const bp = candidates.length > 0 ? bestBreakPoint(candidates, maxWidth) : null;

    if (!bp) {
      // No break point found on this line; mark it as stuck and try the next.
      skipRows.add(longRow);
      continue;
    }

    // For ternary operators, break before all ? and : of the same ternary
    // expression at once so the result is always:
    //   condition
    //     ? consequence
    //     : alternative
    const indent = continuationIndent(lines[longRow]);
    let breakPositions;
    if (bp.breakBefore && (bp.node.type === '?' || bp.node.type === ':')) {
      const paired = ternaryPairedOps(bp.node);
      if (paired) {
        breakPositions = paired
          .filter(op => op.startPosition.row === longRow &&
                        !alreadyAtLineStart(current, op.startIndex))
          .map(op => op.startIndex)
          .sort((a, b) => b - a);  // right-to-left preserves earlier positions
      }
    }
    if (!breakPositions || breakPositions.length === 0) {
      breakPositions = [bp.breakPos];
    }

    for (const pos of breakPositions) {
      current = insertBreak(current, pos, indent);
    }

    // Each insertion adds a new line after longRow, so skipRow indices
    // greater than longRow shift up by the number of breaks inserted.
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
