# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require "idlc"
require "idlc/passes/prune"
require_relative "helpers"
require "minitest/autorun"

$root ||= (Pathname.new(__FILE__) / ".." / ".." / ".." / "..").realpath

require_relative "helpers"

# test IDL variables
class TestVariables < Minitest::Test
  include TestMixin

  def test_prune_forced_type
    orig_idl = "true ? 4'b0 : 5'b1"

    expected_idl = "5'd0"

    symtab = Idl::SymbolTable.new
    m = @compiler.parser.parse(orig_idl, root: :expression)
    refute_nil m

    ast = m.to_ast
    assert_instance_of Idl::TernaryOperatorExpressionAst, ast

    pruned = ast.prune(symtab)
    assert_instance_of Idl::IntLiteralAst, pruned

    assert_equal expected_idl, pruned.to_idl
  end

  def test_prune_forced_type_nested
    orig_idl = "true ? 4'b0 : (5'b1 * 1)"

    expected_idl = "5'd0"

    symtab = Idl::SymbolTable.new
    m = @compiler.parser.parse(orig_idl, root: :expression)
    refute_nil m

    ast = m.to_ast
    assert_instance_of Idl::TernaryOperatorExpressionAst, ast

    pruned = ast.prune(symtab)
    assert_instance_of Idl::IntLiteralAst, pruned

    assert_equal expected_idl, pruned.to_idl
  end

  def test_prune_forced_type_nested_2
    ops = ["*", "/", "+", "-", "&", "|"]
    ops.each do |op|
      orig_idl = "false ? 5'b0 : 4'b1 #{op} 1"

      expected_idl = "5'#{eval "1 #{op} 1"}"

      symtab = Idl::SymbolTable.new
      m = @compiler.parser.parse(orig_idl, root: :expression)
      refute_nil m

      ast = m.to_ast
      assert_instance_of Idl::TernaryOperatorExpressionAst, ast

      pruned = ast.prune(symtab)
      assert_instance_of Idl::IntLiteralAst, pruned

      assert_equal expected_idl, pruned.to_idl
    end
  end

  def test_ternary_prune
    orig_idl = "(true) ? {1'b1, {31{1'b0}}} : {1'b1, {63{1'b0}}}"
    expected_idl = "64'h80000000"

    symtab = Idl::SymbolTable.new
    m = @compiler.parser.parse(orig_idl, root: :expression)
    refute_nil m

    ast = m.to_ast
    assert_instance_of Idl::TernaryOperatorExpressionAst, ast

    pruned = ast.prune(symtab)
    assert_instance_of Idl::IntLiteralAst, pruned

    assert_equal expected_idl, pruned.to_idl
  end

  def test_ternary_prune_2
    orig_idl = "(true) ? {1'b1, {31{1'bx}}} : {1'b1, {63{1'b0}}}"
    expected_idl = "{32'0,1'b1,{31{1'bx}}}"

    symtab = Idl::SymbolTable.new
    m = @compiler.parser.parse(orig_idl, root: :expression)
    refute_nil m

    ast = m.to_ast
    assert_instance_of Idl::TernaryOperatorExpressionAst, ast

    pruned = ast.prune(symtab)
    assert_instance_of Idl::ConcatenationExpressionAst, pruned

    assert_equal expected_idl, pruned.to_idl
  end

  def test_prune_nested_ternary_with_type_coercion
    orig_idl = "true ? (false ? 8'b0 : 16'b1) : 32'd2"
    expected_idl = "32'd1"

    symtab = Idl::SymbolTable.new
    m = @compiler.parser.parse(orig_idl, root: :expression)
    refute_nil m, proc { @compiler.parser.failure_reason }

    ast = m.to_ast
    pruned = ast.prune(symtab)

    assert_equal expected_idl, pruned.to_idl
  end

  def test_prune_complex_concatenation
    orig_idl = "true ? {1'b1, {7{1'b0}}} : {1'b0, {15{1'b1}}}"
    expected_idl = "16'128"

    symtab = Idl::SymbolTable.new
    m = @compiler.parser.parse(orig_idl, root: :expression)
    refute_nil m

    ast = m.to_ast
    pruned = ast.prune(symtab)

    assert_equal expected_idl, pruned.to_idl
  end

  def test_prune_arithmetic_with_known_values
    orig_idl = "true ? (5 `+ 3) : (10 - 2)"
    expected_idl = "4'8"

    symtab = Idl::SymbolTable.new
    m = @compiler.parser.parse(orig_idl, root: :expression)
    refute_nil m

    ast = m.to_ast
    pruned = ast.prune(symtab)

    assert_equal expected_idl, pruned.to_idl
  end

  def test_prune_logical_operations
    orig_idl = "true ? (true && false) : (true || false)"
    expected_idl = "false"

    symtab = Idl::SymbolTable.new
    m = @compiler.parser.parse(orig_idl, root: :expression)
    refute_nil m

    ast = m.to_ast
    pruned = ast.prune(symtab)

    assert_equal expected_idl, pruned.to_idl
  end

  def test_prune_bitwise_operations
    orig_idl = "true ? (8'hFF & 8'h0F) : (8'hAA | 8'h55)"
    expected_idl = "8'15"

    symtab = Idl::SymbolTable.new
    m = @compiler.parser.parse(orig_idl, root: :expression)
    refute_nil m

    ast = m.to_ast
    pruned = ast.prune(symtab)

    assert_equal expected_idl, pruned.to_idl
  end

  def test_prune_shift_operations
    orig_idl = "true ? (8'h01 << 3) : (8'h80 >> 3)"
    expected_idl = "8'8"

    symtab = Idl::SymbolTable.new
    m = @compiler.parser.parse(orig_idl, root: :expression)
    refute_nil m

    ast = m.to_ast
    pruned = ast.prune(symtab)

    assert_equal expected_idl, pruned.to_idl
  end

  def test_prune_comparison_operations
    orig_idl = "true ? (5 > 3) : (2 < 1)"
    expected_idl = "true"

    symtab = Idl::SymbolTable.new
    m = @compiler.parser.parse(orig_idl, root: :expression)
    refute_nil m

    ast = m.to_ast
    pruned = ast.prune(symtab)

    assert_equal expected_idl, pruned.to_idl
  end

  def test_prune_nested_if_statements
    orig_idl = <<~IDL
      if (true) {
        if (false) {
          return 1;
        } else {
          return 2;
        }
      }
    IDL
    expected_idl = <<~IDL
      return 2;
    IDL

    symtab = Idl::SymbolTable.new
    ast = @compiler.compile_func_body(
      orig_idl,
      return_type: Idl::Type.new(:bits, width: 32),
      symtab:,
      input_file: "temp"
    )
    refute_nil ast

    pruned = ast.prune(symtab)
    assert_equal expected_idl.strip, pruned.to_idl.strip
  end

  def test_prune_unknown_condition_preserved
    orig_idl = "unknown_var ? 1 : 2"

    symtab = Idl::SymbolTable.new
    symtab.add("unknown_var", Idl::Var.new("unknown_var", Idl::Type.new(:bits, width: :unknown)))
    # Don't define unknown_var, so it remains unknown
    m = @compiler.parser.parse(orig_idl, root: :expression)
    refute_nil m

    ast = m.to_ast
    pruned = ast.prune(symtab)

    # Should preserve the ternary since condition is unknown
    assert_instance_of Idl::TernaryOperatorExpressionAst, pruned
  end

  def test_prune_csr_value
    orig_idl = <<~IDL
      if (CSR[mockcsr].ONE == 1) {
        return 1;
      }
    IDL
    expected_idl = <<~IDL
      return 1;
    IDL

    mock_csr_class = Class.new do
      include Idl::Csr
      def name = "mockcsr"
      def max_length = 32
      def length(_) = 32
      def dynamic_length? = false
      def value = nil
      def fields = [
        MockCsrFieldClass.new("ONE", 1, 0..15),
        MockCsrFieldClass.new("UNKNOWN", nil, 16..31)
      ]
    end
    mock_csr_class2 = Class.new do
      include Idl::Csr
      def name = "mockcsr2"
      def max_length = 32
      def length(_) = 32
      def dynamic_length? = false
      def value = 1
      def fields = [
        MockCsrFieldClass.new("ONE", 1, 0..31)
      ]
    end
    symtab = Idl::SymbolTable.new(
      csrs: [mock_csr_class.new, mock_csr_class2.new],
      possible_xlens_cb: proc { [32, 64] }
    )
    ast =
      @compiler.compile_func_body(
        orig_idl,
        return_type: Idl::Type.new(:bits, width: 32),
        symtab:,
        input_file: "temp"
      )
    refute_nil(ast)
    pruned_ast = ast.prune(symtab)
    expected_ast =
      @compiler.compile_func_body(
        expected_idl,
        return_type: Idl::Type.new(:bits, width: 32),
        symtab:,
        input_file: "temp"
      )
    refute_nil(expected_ast)
    assert_equal expected_ast.to_idl, pruned_ast.to_idl

    orig_idl = <<~IDL
      if (CSR[mockcsr].UNKNOWN == 1) {
        return 1;
      }
    IDL
    expected_idl = <<~IDL
      if (CSR[mockcsr].UNKNOWN == 1) {
        return 1;
      }
    IDL
    ast =
          @compiler.compile_func_body(
            orig_idl,
            return_type: Idl::Type.new(:bits, width: 32),
            symtab:,
            input_file: "temp"
          )
    refute_nil(ast)
    pruned_ast = ast.prune(symtab)
    expected_ast =
      @compiler.compile_func_body(
        expected_idl,
        return_type: Idl::Type.new(:bits, width: 32),
        symtab:,
        input_file: "temp"
      )
    refute_nil(expected_ast)
    assert_equal expected_ast.to_idl, pruned_ast.to_idl

    orig_idl = <<~IDL
      CSR[mockcsr].UNKNOWN = CSR[mockcsr].ONE;
    IDL
    expected_idl = <<~IDL
      CSR[mockcsr].UNKNOWN = 32'1;
    IDL
    ast =
          @compiler.compile_func_body(
            orig_idl,
            return_type: Idl::Type.new(:bits, width: 32),
            symtab:,
            input_file: "temp"
          )
    refute_nil(ast)
    pruned_ast = ast.prune(symtab)
    expected_ast =
      @compiler.compile_func_body(
        expected_idl,
        return_type: Idl::Type.new(:bits, width: 32),
        symtab:,
        input_file: "temp"
      )
    refute_nil(expected_ast)
    assert_equal expected_ast.to_idl, pruned_ast.to_idl

    orig_idl = <<~IDL
      Bits<32> tmp = $bits(CSR[mockcsr]);
    IDL
    expected_idl = <<~IDL
      Bits<32> tmp = $bits(CSR[mockcsr]);
    IDL
    ast =
          @compiler.compile_func_body(
            orig_idl,
            return_type: Idl::Type.new(:bits, width: 32),
            symtab:,
            input_file: "temp"
          )
    refute_nil(ast)
    pruned_ast = ast.prune(symtab)
    expected_ast =
      @compiler.compile_func_body(
        expected_idl,
        return_type: Idl::Type.new(:bits, width: 32),
        symtab:,
        input_file: "temp"
      )
    refute_nil(expected_ast)
    assert_equal expected_ast.to_idl, pruned_ast.to_idl

    orig_idl = <<~IDL
      Bits<32> tmp = $bits(CSR[mockcsr2]);
    IDL
    expected_idl = <<~IDL
      Bits<32> tmp = 32'1;
    IDL
    ast =
          @compiler.compile_func_body(
            orig_idl,
            return_type: Idl::Type.new(:bits, width: 32),
            symtab:,
            input_file: "temp"
          )
    refute_nil(ast)
    ast.freeze_tree(symtab)
    pruned_ast = ast.prune(symtab)
    expected_ast =
      @compiler.compile_func_body(
        expected_idl,
        return_type: Idl::Type.new(:bits, width: 32),
        symtab:,
        input_file: "temp"
      )
    refute_nil(expected_ast)
    assert_equal expected_ast.to_idl, pruned_ast.to_idl
  end

  def test_prune_csr_field_with_multiple_fields
    mock_csr_class = Class.new do
      include Idl::Csr
      def name = "testcsr"
      def max_length = 32
      def length(_) = 32
      def dynamic_length? = false
      def value = nil
      def fields = [
        MockCsrFieldClass.new("FIELD1", 1, 0..7),
        MockCsrFieldClass.new("FIELD2", 2, 8..15),
        MockCsrFieldClass.new("FIELD3", nil, 16..31)
      ]
    end

    symtab = Idl::SymbolTable.new(
      csrs: [mock_csr_class.new],
      possible_xlens_cb: proc { [32, 64] }
    )

    orig_idl = <<~IDL
      if (CSR[testcsr].FIELD1 == 1 && CSR[testcsr].FIELD2 == 2) {
        return 1;
      }
    IDL
    expected_idl = <<~IDL
      return 1;
    IDL

    ast = @compiler.compile_func_body(
      orig_idl,
      return_type: Idl::Type.new(:bits, width: 32),
      symtab:,
      input_file: "temp"
    )
    refute_nil ast

    pruned = ast.prune(symtab)
    expected_ast = @compiler.compile_func_body(
      expected_idl,
      return_type: Idl::Type.new(:bits, width: 32),
      symtab:,
      input_file: "temp"
    )

    assert_equal expected_ast.to_idl, pruned.to_idl
  end

  def test_prune_preserves_unknown_csr_field
    mock_csr_class = Class.new do
      include Idl::Csr
      def name = "testcsr"
      def max_length = 32
      def length(_) = 32
      def dynamic_length? = false
      def value = nil
      def fields = [
        MockCsrFieldClass.new("UNKNOWN", nil, 0..31)
      ]
    end

    symtab = Idl::SymbolTable.new(
      csrs: [mock_csr_class.new],
      possible_xlens_cb: proc { [32, 64] }
    )

    orig_idl = <<~IDL
      if (CSR[testcsr].UNKNOWN == 1) {
        return 1;
      }
    IDL

    ast = @compiler.compile_func_body(
      orig_idl,
      return_type: Idl::Type.new(:bits, width: 32),
      symtab:,
      input_file: "temp"
    )
    refute_nil ast

    pruned = ast.prune(symtab)

    # Should preserve the if statement since field value is unknown
    assert_instance_of Idl::FunctionBodyAst, pruned
    assert_includes pruned.to_idl, "if"
  end

  def test_prune_with_type_width_mismatch
    orig_idl = "true ? 4'b1111 : 8'b00000000"
    expected_idl = "8'd15"

    symtab = Idl::SymbolTable.new
    m = @compiler.parser.parse(orig_idl, root: :expression)
    refute_nil m

    ast = m.to_ast
    pruned = ast.prune(symtab)

    assert_equal expected_idl, pruned.to_idl
  end

  def test_prune_complex_expression_tree
    orig_idl = "true ? (false ? 1 : (true ? 2 : 3)) : 4"
    expected_idl = "3'd2"

    symtab = Idl::SymbolTable.new
    m = @compiler.parser.parse(orig_idl, root: :expression)
    refute_nil m

    ast = m.to_ast
    pruned = ast.prune(symtab)

    assert_equal expected_idl, pruned.to_idl
  end
end
