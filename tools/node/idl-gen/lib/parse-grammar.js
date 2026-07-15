// Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
// SPDX-License-Identifier: BSD-3-Clause-Clear
//
// Loads the tree-sitter IDL grammar data used by all three generators.

'use strict';

const path = require('path');
const fs   = require('fs');

const ROOT           = path.resolve(__dirname, '..', '..', '..', '..');
const GRAMMAR_JSON   = path.join(ROOT, 'tools', 'node', 'tree-sitter-idl', 'src', 'grammar.json');
const HIGHLIGHTS_SCM = path.join(ROOT, 'tools', 'node', 'tree-sitter-idl', 'queries', 'highlights.scm');

// ---------------------------------------------------------------------------
// Parse highlights.scm for string-literal → capture mappings.
// Lines starting with ';' are comments. The relevant patterns look like:
//   "word1" "word2" ... @capture_name
// (possibly spanning multiple lines before the @ token)
// ---------------------------------------------------------------------------
function parseHighlights(src) {
  // Strip comment lines.
  const text = src.split('\n').filter(l => !l.trimStart().startsWith(';')).join('\n');

  const keywords = [];
  const specialKeywords = [];

  // Match one or more quoted strings followed by a @capture on the same "logical" line.
  // The regex handles multi-word groups split across visual lines but in the same text block.
  const re = /((?:\s*"[^"]+")+)\s*@([\w.]+)/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    const words = Array.from(m[1].matchAll(/"([^"]+)"/g), w => w[1]);
    const capture = m[2];
    if (capture === 'keyword')         keywords.push(...words);
    else if (capture === 'keyword.special') specialKeywords.push(...words);
  }

  return { keywords, specialKeywords };
}

// ---------------------------------------------------------------------------
// Extract the first PATTERN value from a grammar.json rule by name.
// ---------------------------------------------------------------------------
function extractPattern(rules, ruleName) {
  const rule = rules[ruleName];
  if (!rule) return null;

  function find(node) {
    if (!node) return null;
    if (node.type === 'PATTERN') return node.value;
    if (node.content) return find(node.content);
    if (node.members) {
      for (const child of node.members) {
        const found = find(child);
        if (found) return found;
      }
    }
    return null;
  }

  return find(rule);
}

// ---------------------------------------------------------------------------
// Public: load and return all grammar data needed by the generators.
// ---------------------------------------------------------------------------
function loadGrammarData() {
  const grammarJson    = JSON.parse(fs.readFileSync(GRAMMAR_JSON, 'utf8'));
  const highlightsSrc  = fs.readFileSync(HIGHLIGHTS_SCM, 'utf8');

  const { keywords, specialKeywords } = parseHighlights(highlightsSrc);

  const rules = grammarJson.rules;

  return {
    // From highlights.scm
    keywords,           // e.g. ['if', 'else', 'for', ...]
    specialKeywords,    // e.g. ['CSR']

    // From grammar.json — raw regex strings (no delimiters)
    identifierPattern:     extractPattern(rules, 'identifier'),      // [A-Za-z][A-Za-z0-9_]*
    typeIdentifierPattern: extractPattern(rules, 'type_identifier'), // [A-Z][A-Za-z0-9_]*
    builtinPattern:        extractPattern(rules, 'dollar_variable'), // \$[a-zA-Z_][a-zA-Z0-9_?]*
  };
}

module.exports = { loadGrammarData };
