# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require "minitest/autorun"

require_relative "helpers"
require "idlc"

class TestStrictnessAndUnknowns < Minitest::Test
  include TestMixin

  def test_range_operator_strictness
    @symtab.add!("a", Idl::Var.new("a", Idl::Type.new(:bits, width: 8), 0))
    ast = @compiler.compile_expression("a[9:0]", @symtab)

    assert_raises(Idl::AstNode::TypeError) do
      ast.type_check(@symtab, strict: true)
    end

    ast.type_check(@symtab, strict: false)
  end

  def test_enum_ref_memoizes_per_symtab
    symtab1 = Idl::SymbolTable.new
    symtab1.add!("E", Idl::EnumerationType.new("E", ["A"], [0]))

    symtab2 = Idl::SymbolTable.new
    symtab2.add!("E", Idl::EnumerationType.new("E", ["A"], [1]))

    ast = Idl::EnumRefAst.new(nil, nil, "E", "A")

    ast.type_check(symtab1, strict: false)
    assert_equal 0, ast.value(symtab1)

    ast.type_check(symtab2, strict: false)
    assert_equal 1, ast.value(symtab2)
  end

  def test_concat_unknown_literal_propagates
    unknown = Idl::IntLiteralAst.new(nil, nil, "1'bx")
    zero = Idl::IntLiteralAst.new(nil, nil, "1'b0")

    ast = Idl::ConcatenationExpressionAst.new(nil, nil, [zero, unknown])
    ast.type_check(@symtab, strict: false)
    value = ast.value(@symtab)

    assert_kind_of Idl::UnknownLiteral, value
    refute value.unknown_mask.zero?
  end

  def test_replication_unknown_literal_propagates
    n = Idl::IntLiteralAst.new(nil, nil, "2")
    unknown = Idl::IntLiteralAst.new(nil, nil, "1'bx")

    ast = Idl::ReplicationExpressionAst.new(nil, nil, n, unknown)
    ast.type_check(@symtab, strict: false)
    value = ast.value(@symtab)

    assert_kind_of Idl::UnknownLiteral, value
    refute value.unknown_mask.zero?
  end
end
