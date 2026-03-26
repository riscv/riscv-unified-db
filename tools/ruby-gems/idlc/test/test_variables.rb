# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require "minitest/autorun"

require "idlc"
require_relative "helpers"

$root ||= (Pathname.new(__FILE__) / ".." / ".." / ".." / "..").realpath

require_relative "helpers"

# test IDL variables
class TestVariables < Minitest::Test
  include TestMixin

  def test_array_decl
    idl = "XReg ary [8]"

    compiler = Idl::Compiler.new
    symtab = Idl::SymbolTable.new

    m = compiler.parser.parse(idl, root: :single_declaration)
    refute_nil m

    ast = m.to_ast
    assert_instance_of Idl::VariableDeclarationAst, ast

    assert_equal :array, ast.type(symtab).kind
    assert_equal :bits, ast.type(symtab).sub_type.kind
  end

  def test_ternary_max_size
    idl = "true ? 5'b0 : 'b0"

    compiler = Idl::Compiler.new
    symtab = Idl::SymbolTable.new

    m = compiler.parser.parse(idl, root: :expression)
    refute_nil m

    ast = m.to_ast
    assert_instance_of Idl::TernaryOperatorExpressionAst, ast

    assert_equal :bits, ast.type(symtab).kind
    assert_equal :unknown, ast.type(symtab).width
    assert_equal 64, ast.type(symtab).max_width
  end

  def test_that_constants_are_read_only
    idl = <<~IDL.strip
      XReg MyConstant = 15;
      MyContant = 0;
    IDL

    assert_raises(Idl::AstNode::TypeError) do
      @compiler.compile_func_body(idl, symtab: @symtab, no_rescue: true, input_file: "")
    end
  end
end
