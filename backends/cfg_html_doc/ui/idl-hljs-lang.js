// AUTO-GENERATED — do not edit by hand.
// Source: tools/node/tree-sitter-idl/grammar.json + queries/highlights.scm
// Regenerate: bin/chore gen idl-highlight
// Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
// SPDX-License-Identifier: BSD-3-Clause-Clear

(function() {
  'use strict';

  function idl(hljs) {
    var KEYWORDS = {
      keyword: 'if else for return returns arguments body description function enum bitfield struct builtin generated external fetch include const CSR',
      literal: 'true false'
    };

    var COMMENT = hljs.COMMENT('#', '$');

    var STRING = {
      className: 'string',
      begin: '"', end: '"'
    };

    var VERILOG_NUMBER = {
      className: 'number',
      begin: /\b(?:\d+|MXLEN)'s?[bBoOdDhH][0-9a-fA-F_]+\b/
    };

    var HEX_NUMBER = {
      className: 'number',
      begin: /\b0x[0-9a-fA-F_]+\b/
    };

    var BINARY_NUMBER = {
      className: 'number',
      begin: /\b0b[01_]+\b/
    };

    var NUMBER = hljs.NUMBER_MODE;

    var BUILTIN = {
      className: 'built_in',
      begin: /\$[a-zA-Z_][a-zA-Z0-9_?]*\b/
    };

    var TYPE = {
      className: 'type',
      begin: /\b[A-Z][A-Za-z0-9_]*\b/
    };

    var FUNCTION_CALL = {
      className: 'title',
      begin: /\b([a-z][a-zA-Z0-9_]*\??)\s*(?:<[^>]*>\s*)?\(/,
      returnBegin: true,
      contains: [{
        className: 'title',
        begin: /[a-z][a-zA-Z0-9_]*\??/
      }]
    };

    return {
      name: 'IDL',
      aliases: ['idl'],
      keywords: KEYWORDS,
      contains: [
        COMMENT,
        STRING,
        VERILOG_NUMBER,
        HEX_NUMBER,
        BINARY_NUMBER,
        NUMBER,
        BUILTIN,
        FUNCTION_CALL,
        TYPE
      ]
    };
  }

  // Register with highlight.js if available, otherwise export for module use.
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = idl;
  } else if (typeof hljs !== 'undefined') {
    hljs.registerLanguage('idl', idl);
  } else {
    // Defer registration until hljs is available.
    document.addEventListener('DOMContentLoaded', function() {
      if (typeof hljs !== 'undefined') hljs.registerLanguage('idl', idl);
    });
  }
}());
