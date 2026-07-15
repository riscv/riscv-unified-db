// Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
// SPDX-License-Identifier: BSD-3-Clause-Clear
//
// Generates doc/src/prism/idl.js from the tree-sitter IDL grammar.

'use strict';

const path = require('path');
const fs   = require('fs');

const ROOT     = path.resolve(__dirname, '..', '..', '..', '..');
const OUT_DIR  = path.join(ROOT, 'doc', 'src', 'prism');
const OUT_PATH = path.join(OUT_DIR, 'idl.js');

function generate(grammarData) {
  const { keywords, specialKeywords, builtinPattern, typeIdentifierPattern } = grammarData;

  const kwPattern      = [...keywords, ...specialKeywords].join('|');
  const builtinPat     = builtinPattern        || '\\$[a-zA-Z_][a-zA-Z0-9_?]*';
  const typeIdPat      = typeIdentifierPattern || '[A-Z][A-Za-z0-9_]*';

  // Escape a raw regex string so it's safe inside a JS regex literal /…/
  function escRe(s) { return s.replace(/\//g, '\\/'); }

  const content = `// AUTO-GENERATED — do not edit by hand.
// Source: tools/node/tree-sitter-idl/grammar.json + queries/highlights.scm
// Regenerate: bin/chore gen idl-highlight
// Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
// SPDX-License-Identifier: BSD-3-Clause-Clear

module.exports = function (Prism) {
  Prism.languages.idl = {

    // Comments: # to end of line
    comment: {
      pattern: /#.*/,
      greedy: true,
    },

    // description { ... } block — content treated as prose
    description: {
      pattern: /\\bdescription\\s*\\{[^}]*\\}/,
      greedy: true,
      inside: {
        keyword: /\\bdescription\\b/,
        punctuation: /[{}]/,
      },
    },

    // Double-quoted strings
    string: {
      pattern: /"[^"]*"/,
      greedy: true,
    },

    // Verilog-style sized literals: 32'hDEAD, 8'd255, 1'b1, MXLEN'0
    'verilog-literal': {
      pattern: /\\b(?:\\d+|MXLEN)'s?[bBoOdDhH][0-9a-fA-F_xXzZ]*\\b/,
      alias: 'number',
    },

    // C-style hex literals: 0xDEAD
    'hex-literal': {
      pattern: /\\b0x[0-9a-fA-F_]+\\b/,
      alias: 'number',
    },

    // Binary literals: 0b1010
    'binary-literal': {
      pattern: /\\b0b[01_]+\\b/,
      alias: 'number',
    },

    // Decimal integers
    number: /\\b\\d+\\b/,

    // Keywords (from highlights.scm)
    keyword: /\\b(?:${escRe(kwPattern)})\\b/,

    // Builtin variables and cast operators ($ prefix, from grammar.json)
    builtin: /${escRe(builtinPat)}\\b/,

    // Boolean literals
    boolean: /\\b(?:true|false)\\b/,

    // Builtin type names
    'type-alias': {
      pattern: /\\b(?:Bits|XReg|U64|U32|Boolean|String)\\b/,
      alias: 'class-name',
    },

    // Enum/bitfield scope operator: Type::Member
    'scope-resolution': {
      pattern: /\\b(${escRe(typeIdPat)})(::${escRe(typeIdPat)})\\b/,
      inside: {
        'class-name': /^${escRe(typeIdPat)}/,
        punctuation: /::/,
        property: /${escRe(typeIdPat)}$/,
      },
    },

    // Function declarations: function name
    'function-declaration': {
      pattern: /(\\bfunction\\s+)[a-z][a-zA-Z0-9_]*\\??/,
      lookbehind: true,
      alias: 'function',
    },

    // Function calls: name( or name?(
    'function-call': {
      pattern: /\\b([a-z][a-zA-Z0-9_]*\\??)\\s*(?:<[^>]*>\\s*)?\\(/,
      inside: {
        function: /^[a-z][a-zA-Z0-9_]*\\??/,
        punctuation: /[<>(),]/,
      },
    },

    // Constants and type names (uppercase-first identifiers)
    constant: /\\b${escRe(typeIdPat)}\\b/,

    // Widening operators (backtick prefix)
    'widening-operator': {
      pattern: /\`[+\\-*]|\`<</,
      alias: 'operator',
    },

    // Operators
    operator: /->|[+\\-*\\/%&|^~]|<<=?|>>=?|<=?|>=?|[!=]=|&&|\\|\\||[!~]/,

    // Punctuation
    punctuation: /[{}[\\]();,.:]/,
  };
};
`;

  fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.writeFileSync(OUT_PATH, content, 'utf8');
  console.log(`  wrote ${path.relative(ROOT, OUT_PATH)}`);
}

module.exports = { generate };
