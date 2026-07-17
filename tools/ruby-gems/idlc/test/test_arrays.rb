# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require "idlc"
require "idlc/ast"
require "idlc/passes/prune"
require_relative "helpers"
require "minitest/autorun"

$root ||= (Pathname.new(__FILE__) / ".." / ".." / ".." / "..").realpath

# test IDL arrays
class TestArrays < Minitest::Test
  include TestMixin

  def test_element_access
    refute_nil @compiler.build_ast("ary[0]", root: :ary_access)
  end

  def test_element_access_var_index
    refute_nil @compiler.build_ast("ary[var]", root: :ary_access)
  end

  def test_range_access
    refute_nil @compiler.build_ast("ary[0:1]", root: :ary_access)
  end

  def test_range_access_var_range
    refute_nil @compiler.build_ast("ary[var1:var2]", root: :ary_access)
  end

  def test_range_access_mixed_range
    refute_nil @compiler.build_ast("ary[0:var2]", root: :ary_access)
  end

  def test_range_access_var_to_const
    refute_nil @compiler.build_ast("ary[var1:3]", root: :ary_access)
  end

  def test_nested_element_access
    refute_nil @compiler.build_ast("ary[0][1]", root: :ary_access)
  end

  def test_nested_element_access_var
    refute_nil @compiler.build_ast("ary[0][var]", root: :ary_access)
  end

  def test_nested_element_range_access_var
    ast = @compiler.build_ast("ary[0][0:var]", root: :ary_access)
    refute_nil ast
    assert_instance_of Idl::AryRangeAccessAst, ast
  end

  def test_element_assignment
    ast = @compiler.build_ast("ary[0] = 5", root: :assignment)
    assert_instance_of Idl::AryElementAssignmentAst, ast
  end

  def test_range_assignment
    ast = @compiler.build_ast("ary[0:1] = 5", root: :assignment)
    assert_instance_of Idl::AryRangeAssignmentAst, ast
  end

  def test_nested_element_assignment
    ast = @compiler.build_ast("ary[0][1] = 5", root: :assignment)
    assert_instance_of Idl::AryElementAssignmentAst, ast
  end

  def test_nested_element_range_assignment
    ast = @compiler.build_ast("ary[0][0:1] = 5", root: :assignment)
    assert_instance_of Idl::AryRangeAssignmentAst, ast
  end

  def test_nested_range_element_assignment
    ast = @compiler.build_ast("ary[0:1][0] = 5", root: :assignment)
    assert_instance_of Idl::AryElementAssignmentAst, ast
  end

  def test_vmv
    ast = @compiler.build_ast("v[vd][end_bit_pos:start_bit_pos] = sext_imm[state.sew-1:0]", root: :assignment)
    assert_instance_of Idl::AryRangeAssignmentAst, ast
  end

  def test_triple_nested_element_assignment
    ast = @compiler.build_ast("ary[0][1][2] = 5", root: :assignment)
    assert_instance_of Idl::AryElementAssignmentAst, ast
    # Verify the lhs is AryElementAccessAst(AryElementAccessAst(ary, 0), 1)
    # The final [2] index is in the assignment itself
    assert_instance_of Idl::AryElementAccessAst, ast.lhs
    assert_instance_of Idl::AryElementAccessAst, ast.lhs.var
    assert_instance_of Idl::IdAst, ast.lhs.var.var
  end

  def test_triple_nested_range_assignment
    ast = @compiler.build_ast("ary[0][1][7:0] = 5", root: :assignment)
    assert_instance_of Idl::AryRangeAssignmentAst, ast
    # Verify the variable is AryElementAccessAst(AryElementAccessAst(ary, 0), 1)
    assert_instance_of Idl::AryElementAccessAst, ast.variable
    assert_instance_of Idl::AryElementAccessAst, ast.variable.var
  end

  def test_deeply_nested_vmv_style
    ast = @compiler.build_ast("matrix[i][j][15:8] = value", root: :assignment)
    assert_instance_of Idl::AryRangeAssignmentAst, ast
  end

  def test_x_register_range_assignment
    ast = @compiler.build_ast("X[rs1][7:0] = value", root: :assignment)
    assert_instance_of Idl::AryRangeAssignmentAst, ast
    # Verify the variable is AryElementAccessAst(X, rs1)
    assert_instance_of Idl::AryElementAccessAst, ast.variable
    assert_instance_of Idl::IdAst, ast.variable.var
    assert_equal "X", ast.variable.var.name
  end

  def test_execute_nested_bits_element_assignment
    # v is an array of 4 x Bits<32>, initially all zeros
    v_type = Idl::Type.new(:array, width: 4, sub_type: Idl::Type.new(:bits, width: 32))
    @symtab.add("v", Idl::Var.new("v", v_type, [0, 0, 0, 0]))

    ast = @compiler.build_ast("v[1][0] = 1", root: :assignment)
    ast.execute(@symtab)

    v_val = @symtab.get("v").value
    assert_kind_of Array, v_val, "v should remain an array after nested bits element assignment"
    assert_equal 1, v_val[1], "bit 0 of v[1] should be set"
    assert_equal 0, v_val[0], "v[0] should be unchanged"
    assert_equal 0, v_val[2], "v[2] should be unchanged"
  end

  def test_nullify_nested_bits_element_assignment
    # v is an array of 4 x Bits<32> with known values
    v_type = Idl::Type.new(:array, width: 4, sub_type: Idl::Type.new(:bits, width: 32))
    @symtab.add("v", Idl::Var.new("v", v_type, [10, 20, 30, 40]))

    ast = @compiler.build_ast("v[1][0] = 1", root: :assignment)
    ast.nullify_assignments(@symtab)

    assert_nil @symtab.get("v").value, "v should be invalidated after nullify_assignments on nested bits element assignment"
  end
end
