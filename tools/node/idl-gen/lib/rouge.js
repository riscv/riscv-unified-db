// Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
// SPDX-License-Identifier: BSD-3-Clause-Clear
//
// Generates tools/ruby-gems/idl_highlighter/lib/idl_highlighter.rb from the
// tree-sitter IDL grammar (grammar.json + highlights.scm).

'use strict';

const path = require('path');
const fs   = require('fs');

const ROOT     = path.resolve(__dirname, '..', '..', '..', '..');
const OUT_PATH = path.join(ROOT, 'tools', 'ruby-gems', 'idl_highlighter', 'lib', 'idl_highlighter.rb');

// Built-in type names. These are PascalCase identifiers with special meaning in IDL.
// Not listed explicitly in highlights.scm (they match (type_identifier) @type), but
// kept here to preserve distinct Keyword::Type coloring in Rouge output.
const TYPE_KEYWORDS = ['Bits', 'XReg', 'U32', 'U64', 'String', 'Boolean'];

function generate(grammarData) {
  const { keywords, typeIdentifierPattern, identifierPattern, builtinPattern } = grammarData;
  const keywordList    = keywords.join(' ');
  const typeList       = TYPE_KEYWORDS.join(' ');
  const constantPat    = typeIdentifierPattern || '[A-Z][A-Za-z0-9_]*';
  const idPat          = identifierPattern     || '[A-Za-z][A-Za-z0-9_]*';
  const builtinPat     = builtinPattern        || '\\$[a-zA-Z_][a-zA-Z0-9_?]*';

  const content = `# AUTO-GENERATED — do not edit by hand.
# Source: tools/node/tree-sitter-idl/grammar.json + queries/highlights.scm
# Regenerate: bin/chore gen idl-highlight
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require "rouge"

module Rouge
  module Lexers
    class Idl < RegexLexer
      tag "idl"
      filenames "idl", "isa"

      title "IDL"
      desc "ISA Description Language"

      ws = /[ \\n]+/
      id = /${idPat}/

      def self.keywords
        return @keywords unless @keywords.nil?

        @keywords = Set.new %w[
          ${keywordList}
        ]
      end

      def self.keywords_type
        @keywords_type ||= Set.new %w[
          ${typeList}
        ]
      end

      state :root do
        rule ws, Text::Whitespace
        rule %r{#.*}, Comment::Single
        rule %r{"[^"]*"}, Str::Double
        rule %r{${constantPat}}, Name::Constant
        rule %r{(?:(?:[0-9]+)|(?:MXLEN))?'s?[bBoOdDhH][0-9_a-fA-F]+}, Num
        rule %r/0x[0-9a-f]+[lu]*/i, Num::Hex
        rule %r/0[0-7]+[lu]*/i, Num::Oct
        rule %r{\\d+}, Num::Integer
        rule %r{${builtinPat}\\b}, Name::Builtin
        rule %r{[.,;:\\[\\]\\(\\)\\}\\{]}, Punctuation
        rule %r([~!%^&*+=\\|?:<>/\`-]), Operator
        rule id do |m|
          name = m[0]

          if self.class.keywords.include? name
            token Keyword
          elsif self.class.keywords_type.include? name
            token Keyword::Type
          else
            token Name
          end
        end
      end
    end
  end
end
`;

  fs.mkdirSync(path.dirname(OUT_PATH), { recursive: true });
  fs.writeFileSync(OUT_PATH, content);
  console.log(`Written: ${path.relative(ROOT, OUT_PATH)}`);
}

module.exports = { generate };
