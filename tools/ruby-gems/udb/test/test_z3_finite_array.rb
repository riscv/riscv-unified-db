# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require_relative "test_helper"
require_relative "../lib/udb/z3"

class TestZ3FiniteArray < Minitest::Test
  def setup
    @solver = Udb::Z3Solver.new
  end

  # Basic initialization tests
  def test_finite_array_initialization_with_max_size
    constraints = Udb::ArrayConstraints.new(max_size: 10)
    array = Udb::Z3FiniteArray.new(@solver, "test_array", Z3::IntSort, constraints)

    assert_equal 10, array.max_size
  end

  def test_finite_array_initialization_without_max_size
    constraints = Udb::ArrayConstraints.new
    array = Udb::Z3FiniteArray.new(@solver, "test_array", Z3::IntSort, constraints)

    # Should default to 64
    assert_nil array.max_size
  end

  def test_finite_array_initialization_with_large_max_size
    constraints = Udb::ArrayConstraints.new(max_size: 100)
    array = Udb::Z3FiniteArray.new(@solver, "test_array", Z3::IntSort, constraints)

    assert_equal 100, array.max_size
  end

  def test_finite_array_with_min_size
    constraints = Udb::ArrayConstraints.new(min_size: 3, max_size: 10)
    array = Udb::Z3FiniteArray.new(@solver, "sized_array", Z3::IntSort, constraints)

    assert @solver.satisfiable?
  end

  # Element access tests
  def test_element_access_returns_correct_type_int
    constraints = Udb::ArrayConstraints.new(max_size: 5)
    array = Udb::Z3FiniteArray.new(@solver, "int_array", Z3::IntSort, constraints)

    elem = array[0]
    assert_instance_of Z3::IntExpr, elem
  end

  def test_element_access_returns_correct_type_bool
    constraints = Udb::ArrayConstraints.new(max_size: 5)
    array = Udb::Z3FiniteArray.new(@solver, "bool_array", Z3::BoolSort, constraints)

    elem = array[0]
    assert_instance_of Z3::BoolExpr, elem
  end

  def test_element_access_returns_correct_type_bitvec
    constraints = Udb::ArrayConstraints.new(max_size: 5)
    array = Udb::Z3FiniteArray.new(@solver, "bv_array", Z3::BitvecSort, constraints, bitvec_width: 32)

    elem = array[0]
    assert_instance_of Z3::BitvecExpr, elem
  end

  def test_element_access_different_indices
    constraints = Udb::ArrayConstraints.new(max_size: 5)
    array = Udb::Z3FiniteArray.new(@solver, "test_array", Z3::IntSort, constraints)

    elem0 = array[0]
    elem1 = array[1]
    elem2 = array[2]

    # Each element should be a different variable
    refute_equal elem0.object_id, elem1.object_id
    refute_equal elem1.object_id, elem2.object_id
    refute_equal elem0.object_id, elem2.object_id
  end

  def test_element_access_out_of_bounds
    constraints = Udb::ArrayConstraints.new(max_size: 5)
    array = Udb::Z3FiniteArray.new(@solver, "test_array", Z3::IntSort, constraints)

    assert_raises(RuntimeError) do
      array[65]  # Beyond the 64-element limit
    end
  end

  # constrain_element tests
  def test_constrain_element_with_item_by_idx
    type_constraint = Udb::TypeConstraint.new(
      mthd: Udb::Z3ParameterTerm.method(:constrain_int),
      schema: { "type" => "integer", "const" => 42 }
    )
    constraints = Udb::ArrayConstraints.new(max_size: 5)
    constraints.item_by_idx[0] = type_constraint

    array = Udb::Z3FiniteArray.new(@solver, "constrained_array", Z3::BitvecSort, constraints, bitvec_width: 64)

    assert @solver.satisfiable?
  end

  def test_constrain_element_with_item_rest
    type_constraint = Udb::TypeConstraint.new(
      mthd: Udb::Z3ParameterTerm.method(:constrain_int),
      schema: { "type" => "integer", "minimum" => 0, "maximum" => 100 }
    )
    constraints = Udb::ArrayConstraints.new(max_size: 5)
    constraints.item_rest = type_constraint

    array = Udb::Z3FiniteArray.new(@solver, "constrained_array", Z3::BitvecSort, constraints, bitvec_width: 64)

    assert @solver.satisfiable?
  end

  def test_constrain_element_tuple_style
    type_constraint_1 = Udb::TypeConstraint.new(
      mthd: Udb::Z3ParameterTerm.method(:constrain_int),
      schema: { "type" => "integer", "const" => 1 }
    )
    type_constraint_2 = Udb::TypeConstraint.new(
      mthd: Udb::Z3ParameterTerm.method(:constrain_int),
      schema: { "type" => "integer", "const" => 2 }
    )
    type_constraint_rest = Udb::TypeConstraint.new(
      mthd: Udb::Z3ParameterTerm.method(:constrain_int),
      schema: { "type" => "integer", "minimum" => 10 }
    )

    constraints = Udb::ArrayConstraints.new(max_size: 5)
    constraints.item_by_idx[0] = type_constraint_1
    constraints.item_by_idx[1] = type_constraint_2
    constraints.item_rest = type_constraint_rest

    array = Udb::Z3FiniteArray.new(@solver, "tuple_array", Z3::BitvecSort, constraints, bitvec_width: 64)

    assert @solver.satisfiable?
  end

  # has_value? tests
  def test_has_value_with_integer
    constraints = Udb::ArrayConstraints.new(max_size: 5)
    array = Udb::Z3FiniteArray.new(@solver, "int_array", Z3::IntSort, constraints)

    @solver.push
    @solver.assert(array.has_value?(42))
    assert @solver.satisfiable?
    @solver.pop
  end

  def test_has_value_with_boolean
    constraints = Udb::ArrayConstraints.new(max_size: 5)
    array = Udb::Z3FiniteArray.new(@solver, "bool_array", Z3::BoolSort, constraints)

    @solver.push
    @solver.assert(array.has_value?(true))
    assert @solver.satisfiable?
    @solver.pop
  end

  def test_has_value_with_string
    constraints = Udb::ArrayConstraints.new(max_size: 5)
    array = Udb::Z3FiniteArray.new(@solver, "string_array", Z3::IntSort, constraints)

    # Strings are compared via hash
    @solver.push
    @solver.assert(array.has_value?("test_string"))
    assert @solver.satisfiable?
    @solver.pop
  end

  def test_has_value_respects_size
    constraints = Udb::ArrayConstraints.new(max_size: 5)
    array = Udb::Z3FiniteArray.new(@solver, "sized_array", Z3::IntSort, constraints)

    # Set size to 2
    @solver.assert(array.size_term == 2)

    # Value should only be found within the first 2 elements
    @solver.push
    @solver.assert(array[0] == 10)
    @solver.assert(array[1] == 20)
    @solver.assert(array.has_value?(10))
    assert @solver.satisfiable?
    @solver.pop

    # Value beyond size should not be found
    @solver.push
    @solver.assert(array[0] == 10)
    @solver.assert(array[1] == 20)
    @solver.assert(array[2] == 30)
    @solver.assert(~array.has_value?(30))
    assert @solver.satisfiable?
    @solver.pop
  end

  # Array equality tests
  def test_array_equality_empty_array
    constraints = Udb::ArrayConstraints.new(max_size: 5)
    array = Udb::Z3FiniteArray.new(@solver, "test_array", Z3::IntSort, constraints)

    @solver.push
    @solver.assert(array == [])
    assert @solver.satisfiable?
    @solver.pop
  end

  def test_array_equality_single_element
    constraints = Udb::ArrayConstraints.new(max_size: 5)
    array = Udb::Z3FiniteArray.new(@solver, "test_array", Z3::IntSort, constraints)

    @solver.push
    @solver.assert(array == [42])
    assert @solver.satisfiable?
    @solver.pop
  end

  def test_array_equality_multiple_elements
    constraints = Udb::ArrayConstraints.new(max_size: 5)
    array = Udb::Z3FiniteArray.new(@solver, "test_array", Z3::IntSort, constraints)

    @solver.push
    @solver.assert(array == [1, 2, 3, 4, 5])
    assert @solver.satisfiable?
    @solver.pop
  end

  def test_array_equality_with_strings
    constraints = Udb::ArrayConstraints.new(max_size: 3)
    array = Udb::Z3FiniteArray.new(@solver, "string_array", Z3::IntSort, constraints)

    @solver.push
    @solver.assert(array == ["a", "b", "c"])
    assert @solver.satisfiable?
    @solver.pop
  end

  def test_array_equality_with_booleans
    constraints = Udb::ArrayConstraints.new(max_size: 3)
    array = Udb::Z3FiniteArray.new(@solver, "bool_array", Z3::BoolSort, constraints)

    @solver.push
    @solver.assert(array == [true, false, true])
    assert @solver.satisfiable?
    @solver.pop
  end

  def test_array_inequality
    constraints = Udb::ArrayConstraints.new(max_size: 5)
    array = Udb::Z3FiniteArray.new(@solver, "test_array", Z3::IntSort, constraints)

    @solver.push
    @solver.assert(array != [1, 2, 3])
    assert @solver.satisfiable?
    @solver.pop
  end

  def test_array_equality_size_mismatch_smaller
    constraints = Udb::ArrayConstraints.new(min_size: 3, max_size: 5)
    array = Udb::Z3FiniteArray.new(@solver, "test_array", Z3::IntSort, constraints)

    # Array smaller than min_size should return false
    @solver.push
    @solver.assert(array == [1, 2])
    refute @solver.satisfiable?
    @solver.pop
  end

  def test_array_equality_oversized_within_schema
    constraints = Udb::ArrayConstraints.new(max_size: 3)
    array = Udb::Z3FiniteArray.new(@solver, "test_array", Z3::IntSort, constraints)

    # Array larger than max_size should be unsatisfiable
    @solver.push
    @solver.assert(array == [1, 2, 3, 4])
    refute @solver.satisfiable?
    @solver.pop
  end

  def test_array_equality_oversized_beyond_limit
    constraints = Udb::ArrayConstraints.new
    array = Udb::Z3FiniteArray.new(@solver, "test_array", Z3::IntSort, constraints)

    # Array larger than 64-element limit should raise error
    large_array = Array.new(65) { |i| i }
    assert_raises(RuntimeError) do
      array == large_array
    end
  end

  # Size term tests
  def test_size_term_returns_int_expr
    constraints = Udb::ArrayConstraints.new(max_size: 5)
    array = Udb::Z3FiniteArray.new(@solver, "test_array", Z3::IntSort, constraints)

    size = array.size_term
    assert_instance_of Z3::IntExpr, size
  end

  def test_size_term_respects_min_constraint
    constraints = Udb::ArrayConstraints.new(min_size: 3, max_size: 10)
    array = Udb::Z3FiniteArray.new(@solver, "test_array", Z3::IntSort, constraints)

    @solver.push
    @solver.assert(array.size_term < 3)
    refute @solver.satisfiable?
    @solver.pop
  end

  def test_size_term_respects_max_constraint
    constraints = Udb::ArrayConstraints.new(min_size: 2, max_size: 5)
    array = Udb::Z3FiniteArray.new(@solver, "test_array", Z3::IntSort, constraints)

    @solver.push
    @solver.assert(array.size_term > 5)
    refute @solver.satisfiable?
    @solver.pop
  end

  # Contains constraint tests
  def test_contains_constraint
    type_constraint = Udb::TypeConstraint.new(
      mthd: Udb::Z3ParameterTerm.method(:constrain_int),
      schema: { "type" => "integer", "const" => 42 }
    )
    constraints = Udb::ArrayConstraints.new(max_size: 5)
    constraints.contains = type_constraint

    array = Udb::Z3FiniteArray.new(@solver, "contains_array", Z3::BitvecSort, constraints, bitvec_width: 64)

    # Array must contain 42
    assert @solver.satisfiable?
  end

  # Unique items constraint tests
  def test_unique_items_constraint
    constraints = Udb::ArrayConstraints.new(max_size: 5)
    constraints.unique = true

    array = Udb::Z3FiniteArray.new(@solver, "unique_array", Z3::IntSort, constraints)

    # All elements must be distinct
    assert @solver.satisfiable?
  end

  def test_unique_items_prevents_duplicates
    constraints = Udb::ArrayConstraints.new(max_size: 3)
    constraints.unique = true

    array = Udb::Z3FiniteArray.new(@solver, "unique_array", Z3::IntSort, constraints)

    # Try to create array with duplicates
    @solver.push
    @solver.assert(array[0] == 1)
    @solver.assert(array[1] == 1)  # Duplicate
    @solver.assert(array.size_term == 2)
    refute @solver.satisfiable?
    @solver.pop
  end

  # Complex constraint combinations
  def test_array_with_multiple_constraints
    type_constraint = Udb::TypeConstraint.new(
      mthd: Udb::Z3ParameterTerm.method(:constrain_int),
      schema: { "type" => "integer", "minimum" => 0, "maximum" => 10 }
    )
    constraints = Udb::ArrayConstraints.new(min_size: 2, max_size: 5)
    constraints.item_rest = type_constraint
    constraints.unique = true

    array = Udb::Z3FiniteArray.new(@solver, "complex_array", Z3::BitvecSort, constraints, bitvec_width: 64)

    assert @solver.satisfiable?
  end

  def test_array_with_tuple_and_rest_constraints
    type_constraint_0 = Udb::TypeConstraint.new(
      mthd: Udb::Z3ParameterTerm.method(:constrain_int),
      schema: { "type" => "integer", "const" => 0 }
    )
    type_constraint_rest = Udb::TypeConstraint.new(
      mthd: Udb::Z3ParameterTerm.method(:constrain_int),
      schema: { "type" => "integer", "minimum" => 1, "maximum" => 100 }
    )
    constraints = Udb::ArrayConstraints.new(min_size: 3, max_size: 5)
    constraints.item_by_idx[0] = type_constraint_0
    constraints.item_rest = type_constraint_rest

    array = Udb::Z3FiniteArray.new(@solver, "mixed_array", Z3::BitvecSort, constraints, bitvec_width: 64)

    assert @solver.satisfiable?
  end

  # Edge cases
  def test_array_with_zero_max_size
    constraints = Udb::ArrayConstraints.new(max_size: 0)
    array = Udb::Z3FiniteArray.new(@solver, "empty_array", Z3::IntSort, constraints)

    # Should only be satisfiable with empty array
    @solver.push
    @solver.assert(array == [])
    assert @solver.satisfiable?
    @solver.pop
  end

  def test_array_with_conflicting_size_constraints
    constraints = Udb::ArrayConstraints.new(min_size: 5, max_size: 3)
    array = Udb::Z3FiniteArray.new(@solver, "conflict_array", Z3::IntSort, constraints)

    # min > max should be unsatisfiable
    refute @solver.satisfiable?
  end

  def test_bitvec_array_with_different_widths
    constraints_32 = Udb::ArrayConstraints.new(max_size: 3)
    array_32 = Udb::Z3FiniteArray.new(@solver, "bv32_array", Z3::BitvecSort, constraints_32, bitvec_width: 32)

    constraints_64 = Udb::ArrayConstraints.new(max_size: 3)
    array_64 = Udb::Z3FiniteArray.new(@solver, "bv64_array", Z3::BitvecSort, constraints_64, bitvec_width: 64)

    elem_32 = array_32[0]
    elem_64 = array_64[0]

    assert_instance_of Z3::BitvecExpr, elem_32
    assert_instance_of Z3::BitvecExpr, elem_64
  end

  def test_array_operations_with_solver_push_pop
    constraints = Udb::ArrayConstraints.new(max_size: 5)
    array = Udb::Z3FiniteArray.new(@solver, "test_array", Z3::IntSort, constraints)

    # First context: array = [1, 2, 3]
    @solver.push
    @solver.assert(array == [1, 2, 3])
    assert @solver.satisfiable?

    # Nested context: also require has_value?(2)
    @solver.push
    @solver.assert(array.has_value?(2))
    assert @solver.satisfiable?
    @solver.pop

    # Back to first context
    assert @solver.satisfiable?
    @solver.pop

    # Base context: different constraint
    @solver.push
    @solver.assert(array == [4, 5, 6])
    assert @solver.satisfiable?
    @solver.pop
  end
end
