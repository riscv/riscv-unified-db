# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require "idlc"
require_relative "helpers"
require "minitest/autorun"

# Round-trips a wide variety of IDL expressions through build_ast -> to_idl,
# exercising the to_idl implementations across many AST node types.
class TestToIdlRoundtrip < Minitest::Test
  include TestMixin

  EXPRESSIONS = [
    # literals
    "42", "8'd5", "8'hff", "16'b1010", "32'h1234abcd", "true", "false",
    '"a string"',
    # arithmetic / bitwise / logical
    "1 + 2", "10 - 3", "4 * 5", "20 / 4", "17 % 5",
    "1 << 4", "256 >> 2", "1 & 3", "1 | 2", "5 ^ 6",
    "true && false", "true || false", "!true",
    "~8'h0f", "-5",
    # widening operators
    "8'd200 `+ 8'd100", "8'd1 `- 8'd2", "8'd16 `* 8'd16", "8'd1 `<< 4",
    # comparisons
    "3 < 4", "4 > 3", "3 <= 3", "4 >= 4", "5 == 5", "5 != 6",
    # ternary
    "true ? 1 : 2", "(1 < 2) ? 8'd1 : 8'd2",
    # concatenation and replication
    "{4'h1, 4'h2}", "{8{1'b1}}", "{2'b01, {3{1'b0}}}",
    # bit selection / range
    "8'hff[3:0]", "8'hff[7]", "32'h12345678[15:8]",
    # casts / builtins
    "$signed(8'hff)", "$bits(8'd5)",
    # parens / nesting
    "((1 + 2) * 3)", "(((42)))",
    # array literal
    "[8'd1, 8'd2, 8'd3]"
  ].freeze

  def test_expressions_round_trip_through_to_idl
    EXPRESSIONS.each do |src|
      ast = @compiler.build_ast(src, root: :expression)
      refute_nil ast, "failed to build #{src.inspect}"
      idl = ast.to_idl
      assert_kind_of String, idl
      refute_empty idl, "empty to_idl for #{src.inspect}"
    end
  end

  def test_to_idl_output_reparses
    # The output of to_idl must itself be valid IDL that parses again.
    EXPRESSIONS.each do |src|
      once = @compiler.build_ast(src, root: :expression).to_idl
      reparsed = @compiler.build_ast(once, root: :expression)
      refute_nil reparsed, "to_idl output did not reparse for #{src.inspect}"
      refute_empty reparsed.to_idl
    end
  end
end
