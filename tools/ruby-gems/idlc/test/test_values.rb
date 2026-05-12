# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require "idlc"
require "idlc/ast"
require_relative "helpers"
require "minitest/autorun"

$root ||= (Pathname.new(__FILE__) / ".." / ".." / ".." / "..").realpath

require_relative "helpers"

# test IDL variables
class TestValues < Minitest::Test
  include TestMixin

  def test_unimplemented_csr_field
    $mock_csr_field_class = Class.new do
      include Idl::CsrField
      def initialize(name, val, loc, impl)
        @name = name
        @val = val
        @loc = loc
        @impl = impl
      end
      attr_reader :name
      def type(_) = @val.nil? ? "RW" : "RO"
      def exists? = @impl
    end
    mock_csr_class = Class.new do
      include Idl::Csr
      def name = "mockcsr"
      def max_length = 32
      def length(_) = 32
      def dynamic_length? = false
      def value = nil
      def fields = [
        $mock_csr_field_class.new("ONE", 1, 0..15, false)
      ]
    end

    symtab = Idl::SymbolTable.new(
      csrs: [mock_csr_class.new],
      possible_xlens_cb: proc { [32, 64] }
    )

    idl = "CSR[mockcsr].ONE"
    @compiler.parser.set_input_file("", 0)
    m = @compiler.parser.parse(idl, root: :csr_field_access_expression)
    refute_nil m
    ast = m.to_ast
    refute_nil ast
    ast.freeze_tree(symtab)
    assert_equal 0, ast.value(symtab)
  end
end

# test UnknownLiteral
class TestUnknownLiteral < Minitest::Test
  def test_to_s
    tmp = Idl::UnknownLiteral.new(5, 4)
    assert_equal "3'bx01", tmp.to_s

    tmp = Idl::UnknownLiteral.new(0x7fff_ffff, 0b1000_0000_0000)
    assert_equal "31'b1111111111111111111x11111111111", tmp.to_s
  end
end

# Tests for TernaryOperatorExpressionAst#max_value and #min_value.
# These support the max-register-width derivation used when removing
# the max_register_length: field from register file YAML.
class TestTernaryMaxMinValue < Minitest::Test
  def setup
    @compiler = Idl::Compiler.new
    # Symtab with a boolean variable that has no compile-time value, so ternary
    # conditions referencing it will be unknown at compile time.
    @symtab = Idl::SymbolTable.new(
      register_files: [DEFAULT_X_REGISTER_FILE],
      builtin_global_vars: [
        Idl::Var.new("flag", Idl::Type.new(:boolean))
      ]
    )
  end

  def compile(expr)
    @compiler.compile_expression(expr, @symtab, pass_error: true)
  end

  # Unknown condition → max_value returns the larger of the two literal branches
  def test_max_value_unknown_condition
    ast = compile("flag ? 64 : 32")
    assert_equal 64, ast.max_value(@symtab)
  end

  # Unknown condition → min_value returns the smaller branch
  def test_min_value_unknown_condition
    ast = compile("flag ? 64 : 32")
    assert_equal 32, ast.min_value(@symtab)
  end

  # Known-true condition → max_value follows the true branch only
  def test_max_value_known_true_condition
    ast = compile("true ? 32 : 64")
    assert_equal 32, ast.max_value(@symtab)
  end

  # Known-false condition → max_value follows the false branch only
  def test_max_value_known_false_condition
    ast = compile("false ? 32 : 64")
    assert_equal 64, ast.max_value(@symtab)
  end
end
