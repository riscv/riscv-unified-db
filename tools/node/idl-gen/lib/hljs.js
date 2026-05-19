// Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
// SPDX-License-Identifier: BSD-3-Clause-Clear
//
// Generates backends/cfg_html_doc/ui/idl-hljs-lang.js from the
// tree-sitter IDL grammar (grammar.json + highlights.scm).

'use strict';

const path = require('path');
const fs   = require('fs');

const ROOT     = path.resolve(__dirname, '..', '..', '..', '..');
const OUT_PATH = path.join(ROOT, 'backends', 'cfg_html_doc', 'ui', 'idl-hljs-lang.js');

function generate(grammarData) {
  const { keywords, specialKeywords, builtinPattern, typeIdentifierPattern } = grammarData;

  const allKeywords    = [...keywords, ...specialKeywords].join(' ');
  const builtinPat     = builtinPattern        || '\\$[a-zA-Z_][a-zA-Z0-9_?]*';
  const typeIdPat      = typeIdentifierPattern || '[A-Z][A-Za-z0-9_]*';

  // Escape a string for use inside a JS template literal / single-quoted string in the output
  function esc(s) { return s.replace(/\\/g, '\\\\').replace(/'/g, "\\'"); }

  const content = `// AUTO-GENERATED — do not edit by hand.
// Source: tools/node/tree-sitter-idl/grammar.json + queries/highlights.scm
// Regenerate: bin/chore gen idl-highlight
// Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
// SPDX-License-Identifier: BSD-3-Clause-Clear

(function() {
  'use strict';

  function idl(hljs) {
    var KEYWORDS = {
      keyword: '${esc(allKeywords)}',
      literal: 'true false'
    };

    var COMMENT = hljs.COMMENT('#', '$');

    var STRING = {
      className: 'string',
      begin: '"', end: '"'
    };

    var VERILOG_NUMBER = {
      className: 'number',
      begin: /\\b(?:\\d+|MXLEN)'s?[bBoOdDhH][0-9a-fA-F_]+\\b/
    };

    var HEX_NUMBER = {
      className: 'number',
      begin: /\\b0x[0-9a-fA-F_]+\\b/
    };

    var BINARY_NUMBER = {
      className: 'number',
      begin: /\\b0b[01_]+\\b/
    };

    var NUMBER = hljs.NUMBER_MODE;

    var BUILTIN = {
      className: 'built_in',
      begin: /${builtinPat}\\b/
    };

    var TYPE = {
      className: 'type',
      begin: /\\b${typeIdPat}\\b/
    };

    var FUNCTION_CALL = {
      className: 'title',
      begin: /\\b([a-z][a-zA-Z0-9_]*\\??)\\s*(?:<[^>]*>\\s*)?\\(/,
      returnBegin: true,
      contains: [{
        className: 'title',
        begin: /[a-z][a-zA-Z0-9_]*\\??/
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
`;

  fs.mkdirSync(path.dirname(OUT_PATH), { recursive: true });
  fs.writeFileSync(OUT_PATH, content);
  console.log(`Written: ${path.relative(ROOT, OUT_PATH)}`);
}

module.exports = { generate };
