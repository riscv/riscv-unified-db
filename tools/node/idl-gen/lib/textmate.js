// Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
// SPDX-License-Identifier: BSD-3-Clause-Clear
//
// Generates tools/vscode/idl/syntaxes/idl.tmLanguage.json from the
// tree-sitter IDL grammar (grammar.json + highlights.scm).

'use strict';

const path = require('path');
const fs   = require('fs');

const ROOT      = path.resolve(__dirname, '..', '..', '..', '..');
const OUT_PATH  = path.join(ROOT, 'tools', 'vscode', 'idl', 'syntaxes', 'idl.tmLanguage.json');

function generate(grammarData) {
  const { keywords, specialKeywords, builtinPattern } = grammarData;

  // All keywords (control + special) share the same TextMate scope.
  const allKeywords = [...keywords, ...specialKeywords];
  const keywordMatch = `\\b(?:${allKeywords.join('|')})\\b`;

  // Builtin $variables — use the pattern from grammar.json.
  // Anchor with word boundary on the right; $ is already the distinguishing prefix.
  const builtinMatch = builtinPattern
    ? `(?:${builtinPattern.replace(/\\?$/, '')})\\b`
    : `\\$[a-zA-Z_][a-zA-Z0-9_]*\\b`;

  const repository = {
    comment: {
      patterns: [{ name: 'comment.line.number-sign.idl', match: '#.*' }],
    },

    description: {
      patterns: [{
        name: 'meta.description.idl',
        begin: '\\b(description)\\s*(\\{)',
        end: '\\}',
        beginCaptures: {
          '1': { name: 'keyword.control.idl' },
          '2': { name: 'punctuation.idl' },
        },
        endCaptures: {
          '0': { name: 'punctuation.idl' },
        },
        contentName: 'string.other.description.idl',
      }],
    },

    string: {
      patterns: [{ name: 'string.quoted.double.idl', match: '"[^"]*"' }],
    },

    // Verilog-style integer literals: 32'b1010, MXLEN'h3f, 'b1010, etc.
    'verilog-literal': {
      patterns: [{
        name: 'constant.numeric.idl',
        match: "\\b(?:\\d+|MXLEN)'s?[bBoOdDhH][0-9a-fA-F_]+\\b",
      }],
    },

    'hex-literal': {
      patterns: [{ name: 'constant.numeric.idl', match: '\\b0x[0-9a-fA-F_]+\\b' }],
    },

    'binary-literal': {
      patterns: [{ name: 'constant.numeric.idl', match: '\\b0b[01_]+\\b' }],
    },

    number: {
      patterns: [{ name: 'constant.numeric.idl', match: '\\b\\d+\\b' }],
    },

    keyword: {
      patterns: [{ name: 'keyword.control.idl', match: keywordMatch }],
    },

    builtin: {
      patterns: [{ name: 'support.function.builtin.idl', match: builtinMatch }],
    },

    boolean: {
      patterns: [{ name: 'constant.language.idl', match: '\\b(?:true|false)\\b' }],
    },

    // Built-in type names: Bits<N>, XReg, U32, U64, Boolean, String.
    // Also matches any other PascalCase identifier as a type (consistent with
    // tree-sitter's (type_identifier) @type which uses [A-Z][A-Za-z0-9_]*).
    'type-name': {
      patterns: [{ name: 'entity.name.type.idl', match: '\\b[A-Z][a-zA-Z0-9_]*\\b' }],
    },

    // Scope resolution: EnumType::Member
    'scope-resolution': {
      patterns: [{
        match: '\\b([A-Z][a-zA-Z0-9_]*)(::)([A-Za-z][A-Za-z0-9_]*)\\b',
        captures: {
          '1': { name: 'entity.name.type.idl' },
          '2': { name: 'punctuation.idl' },
          '3': { name: 'variable.other.member.idl' },
        },
      }],
    },

    // function name(...) declaration
    'function-declaration': {
      patterns: [{
        match: '(\\bfunction\\s+)[a-z][a-zA-Z0-9_]*\\??',
        captures: {
          '1': { name: 'keyword.control.idl' },
          '2': { name: 'entity.name.function.idl' },
        },
      }],
    },

    // Lowercase identifier immediately followed by optional type params and '('
    'function-call': {
      patterns: [{
        match: '\\b([a-z][a-zA-Z0-9_]*\\??)\\s*(?:<[^>]*>\\s*)?\\(',
        captures: {
          '1': { name: 'entity.name.function.idl' },
        },
      }],
    },

    // Widening arithmetic operators: `+  `-  `*  `<<
    'widening-operator': {
      patterns: [{ name: 'keyword.operator.idl', match: '`[+\\-*]|`<<' }],
    },

    operator: {
      patterns: [{
        name: 'keyword.operator.idl',
        match: '->|[+\\-*/%&|^~]|<<=?|>>=?|<=?|>=?|[!=]=|&&|\\|\\||[!~]',
      }],
    },

    punctuation: {
      patterns: [{ name: 'punctuation.idl', match: '[{}\\[\\]();,.]' }],
    },
  };

  // Pattern ordering matters: more specific rules first.
  const patternOrder = [
    'comment', 'description', 'string',
    'verilog-literal', 'hex-literal', 'binary-literal', 'number',
    'keyword', 'builtin', 'boolean',
    'scope-resolution', 'function-declaration', 'function-call',
    'type-name', 'widening-operator', 'operator', 'punctuation',
  ];

  const tmLanguage = {
    $schema: 'https://raw.githubusercontent.com/martinring/tmlanguage/master/tmlanguage.json',
    name: 'IDL',
    scopeName: 'source.idl',
    // AUTO-GENERATED — do not edit by hand.
    // Source: tools/node/tree-sitter-idl/grammar.json + queries/highlights.scm
    // Regenerate: bin/chore gen idl-highlight
    patterns: patternOrder.map(k => ({ include: `#${k}` })),
    repository,
  };

  fs.mkdirSync(path.dirname(OUT_PATH), { recursive: true });
  fs.writeFileSync(OUT_PATH, JSON.stringify(tmLanguage, null, 2) + '\n');
  console.log(`Written: ${path.relative(ROOT, OUT_PATH)}`);
}

module.exports = { generate };
