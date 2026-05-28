# AUTO-GENERATED — do not edit by hand.
# Source: tools/node/tree-sitter-idl/grammar.json + queries/highlights.scm
# Regenerate: bin/chore gen idl-highlight
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: ignore
# frozen_string_literal: true

require "rouge"

module Rouge
  module Lexers
    class Idl < RegexLexer
      tag "idl"
      filenames "idl", "isa"

      title "IDL"
      desc "ISA Description Language"

      ws = /[ \n]+/
      id = /[A-Za-z][A-Za-z0-9_]*/

      def self.keywords
        return @keywords unless @keywords.nil?

        @keywords = Set.new %w[
          if else for return returns arguments body description function enum bitfield struct builtin generated external fetch include const
        ]
      end

      def self.keywords_type
        @keywords_type ||= Set.new %w[
          Bits XReg U32 U64 String Boolean
        ]
      end

      state :root do
        rule ws, Text::Whitespace
        rule %r{#.*}, Comment::Single
        rule %r{"[^"]*"}, Str::Double
        # Verilog integer literals must precede the constant/identifier rules so
        # that width prefixes like MXLEN are consumed as part of the literal.
        # 1) Explicit-base Verilog with width:  32'b1010  MXLEN'hff  8'sd42
        rule %r{(?:[0-9]+|MXLEN)'s?[bBoOdDhH][0-9_a-fA-FxXzZ]+}, Num
        # 2) Implicit-decimal Verilog with width:  MXLEN'1  32'0
        rule %r{(?:[0-9]+|MXLEN)'s?[0-9_]+}, Num
        # 3) Bare Verilog (no width prefix):  'b1010  'hff  '0
        rule %r{'s?[bBoOdDhH][0-9_a-fA-FxXzZ]+}, Num
        # C-style and plain numeric literals
        rule %r/0[bB][01_]+s?/, Num::Bin
        rule %r/0x[0-9a-f]+[lu]*/i, Num::Hex
        rule %r/0[0-7]+[lu]*/i, Num::Oct
        rule %r{\d+s?}, Num::Integer
        rule %r{[A-Z][A-Za-z0-9_]*}, Name::Constant
        rule %r{\$[a-zA-Z_][a-zA-Z0-9_?]*\b}, Name::Builtin
        rule %r{[.,;:\[\]\(\)\}\{]}, Punctuation
        rule %r([~!%^&*+=\|?:<>/`-]), Operator
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
