# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require_relative "test_helper"
require_relative "../lib/udb/z3"

class TestZ3Solver < Minitest::Test
  def setup
    @solver = Udb::Z3Solver.new
  end

  def test_solver_initialization
    assert_instance_of Udb::Z3Solver, @solver
  end

  def test_xlen_returns_int_expr
    xlen = @solver.xlen
    assert_instance_of Z3::IntExpr, xlen
  end

  def test_xlen_is_constrained_to_32_or_64
    @solver.xlen
    # The solver should have assertions that xlen is either 32 or 64
    assert @solver.satisfiable?

    # Test that xlen can be 32
    @solver.push
    @solver.assert(@solver.xlen == 32)
    assert @solver.satisfiable?
    @solver.pop

    # Test that xlen can be 64
    @solver.push
    @solver.assert(@solver.xlen == 64)
    assert @solver.satisfiable?
    @solver.pop

    # Test that xlen cannot be other values
    @solver.push
    @solver.assert(@solver.xlen == 16)
    refute @solver.satisfiable?
    @solver.pop
  end

  def test_xlen_returns_same_instance
    xlen1 = @solver.xlen
    xlen2 = @solver.xlen
    assert_equal xlen1.object_id, xlen2.object_id
  end

  def test_assert_adds_constraint
    x = Z3.Int("x")
    @solver.assert(x > 0)
    @solver.assert(x < 10)

    assert @solver.satisfiable?
    model = @solver.model
    x_val = model[x].to_i
    assert x_val > 0
    assert x_val < 10
  end

  def test_satisfiable_with_consistent_constraints
    x = Z3.Int("x")
    @solver.assert(x > 5)
    @solver.assert(x < 10)

    assert @solver.satisfiable?
  end

  def test_unsatisfiable_with_inconsistent_constraints
    x = Z3.Int("x")
    @solver.assert(x > 10)
    @solver.assert(x < 5)

    refute @solver.satisfiable?
    assert @solver.unsatisfiable?
  end

  def test_push_and_pop
    x = Z3.Int("x")
    @solver.assert(x > 0)

    @solver.push
    @solver.assert(x < 5)
    assert @solver.satisfiable?

    @solver.pop
    # After pop, the constraint x < 5 should be removed
    @solver.assert(x > 10)
    assert @solver.satisfiable?
  end

  def test_model_returns_satisfying_assignment
    x = Z3.Int("x")
    y = Z3.Int("y")
    @solver.assert(x + y == 10)
    @solver.assert(x > y)

    assert @solver.satisfiable?
    model = @solver.model
    x_val = model[x].to_i
    y_val = model[y].to_i

    assert_equal 10, x_val + y_val
    assert x_val > y_val
  end

  def test_ext_major_creates_int_expr
    major = @solver.ext_major("TestExt")
    assert_instance_of Z3::IntExpr, major
  end

  def test_ext_major_returns_same_instance_for_same_name
    major1 = @solver.ext_major("TestExt")
    major2 = @solver.ext_major("TestExt")
    assert_equal major1.object_id, major2.object_id
  end

  def test_ext_minor_creates_int_expr
    minor = @solver.ext_minor("TestExt")
    assert_instance_of Z3::IntExpr, minor
  end

  def test_ext_patch_creates_int_expr
    patch = @solver.ext_patch("TestExt")
    assert_instance_of Z3::IntExpr, patch
  end

  def test_ext_pre_creates_bool_expr
    pre = @solver.ext_pre("TestExt")
    assert_instance_of Z3::BoolExpr, pre
  end

  def test_assertions_returns_array
    x = Z3.Int("x")
    @solver.assert(x > 0)
    @solver.assert(x < 10)

    assertions = @solver.assertions
    assert_instance_of Array, assertions
    assert_equal 2, assertions.length
  end

  def test_check_returns_symbol
    result = @solver.check
    assert_includes [:sat, :unsat, :unknown], result
  end

  def test_boolean_operations
    a = Z3.Bool("a")
    b = Z3.Bool("b")

    @solver.assert(a | b)  # a OR b
    @solver.assert(!a)     # NOT a

    assert @solver.satisfiable?
    model = @solver.model
    assert_equal false, model[a]
    assert_equal true, model[b]
  end

  def test_distinct_constraint
    x = Z3.Int("x")
    y = Z3.Int("y")
    z = Z3.Int("z")

    @solver.assert(Z3.Distinct(x, y, z))
    @solver.assert(x >= 0)
    @solver.assert(x < 3)
    @solver.assert(y >= 0)
    @solver.assert(y < 3)
    @solver.assert(z >= 0)
    @solver.assert(z < 3)

    assert @solver.satisfiable?
    model = @solver.model
    values = [model[x].to_i, model[y].to_i, model[z].to_i]
    assert_equal values.uniq.length, 3, "All values should be distinct"
  end

  def test_implications
    p = Z3.Bool("p")
    q = Z3.Bool("q")

    @solver.assert(p.implies(q))
    @solver.assert(p)

    assert @solver.satisfiable?
    model = @solver.model
    assert_equal true, model[p]
    assert_equal true, model[q]
  end

  def test_solver_with_multiple_data_types
    int_var = Z3.Int("int_var")
    bool_var = Z3.Bool("bool_var")
    bv_var = Z3.Bitvec("bv_var", 32)

    @solver.assert(int_var > 0)
    @solver.assert(bool_var)
    @solver.assert(bv_var.unsigned_lt(100))

    assert @solver.satisfiable?
  end
end

class TestZ3ParameterTerm < Minitest::Test
  def setup
    @solver = Udb::Z3Solver.new
  end

  def test_detect_type_for_boolean
    schema = { "type" => "boolean" }
    assert_equal :boolean, Udb::Z3ParameterTerm.detect_type(schema)
  end

  def test_detect_type_for_integer
    schema = { "type" => "integer" }
    assert_equal :int, Udb::Z3ParameterTerm.detect_type(schema)
  end

  def test_detect_type_for_string
    schema = { "type" => "string" }
    assert_equal :string, Udb::Z3ParameterTerm.detect_type(schema)
  end

  def test_detect_type_for_array
    schema = { "type" => "array" }
    assert_equal :array, Udb::Z3ParameterTerm.detect_type(schema)
  end

  def test_detect_type_from_const_boolean
    schema = { "const" => true }
    assert_equal :boolean, Udb::Z3ParameterTerm.detect_type(schema)
  end

  def test_detect_type_from_const_integer
    schema = { "const" => 42 }
    assert_equal :int, Udb::Z3ParameterTerm.detect_type(schema)
  end

  def test_detect_type_from_const_string
    schema = { "const" => "test" }
    assert_equal :string, Udb::Z3ParameterTerm.detect_type(schema)
  end

  def test_detect_type_from_enum_integer
    schema = { "enum" => [1, 2, 3] }
    assert_equal :int, Udb::Z3ParameterTerm.detect_type(schema)
  end

  def test_parameter_term_with_const_integer
    schema = { "const" => 42 }
    param = Udb::Z3ParameterTerm.new("test_param", @solver, schema)

    # The parameter should be constrained to equal 42
    assert @solver.satisfiable?
  end

  def test_parameter_term_with_minimum_maximum
    schema = {
      "type" => "integer",
      "minimum" => 10,
      "maximum" => 20
    }
    param = Udb::Z3ParameterTerm.new("test_param", @solver, schema)

    assert @solver.satisfiable?
  end

  def test_parameter_term_with_enum
    schema = {
      "type" => "integer",
      "enum" => [1, 2, 4, 8]
    }
    param = Udb::Z3ParameterTerm.new("test_param", @solver, schema)

    assert @solver.satisfiable?
  end

  def test_parameter_term_boolean_const
    schema = { "const" => true }
    param = Udb::Z3ParameterTerm.new("bool_param", @solver, schema)

    assert @solver.satisfiable?
  end
end

class TestZ3FiniteArray < Minitest::Test
  def setup
    @solver = Udb::Z3Solver.new
  end

  def test_finite_array_initialization
    array = Udb::Z3FiniteArray.new(@solver, "test_array", Z3::IntSort, 5)

    assert_equal 5, array.max_size
  end

  def test_finite_array_element_access
    array = Udb::Z3FiniteArray.new(@solver, "test_array", Z3::IntSort, 5)

    elem0 = array[0]
    elem1 = array[1]

    assert_instance_of Z3::IntExpr, elem0
    assert_instance_of Z3::IntExpr, elem1
  end

  def test_finite_array_with_bitvec
    array = Udb::Z3FiniteArray.new(@solver, "bv_array", Z3::BitvecSort, 3, bitvec_width: 32)

    elem = array[0]
    assert_instance_of Z3::BitvecExpr, elem
  end

  def test_finite_array_with_bool
    array = Udb::Z3FiniteArray.new(@solver, "bool_array", Z3::BoolSort, 3)

    elem = array[0]
    assert_instance_of Z3::BoolExpr, elem
  end

  def test_finite_array_size_term
    array = Udb::Z3FiniteArray.new(@solver, "test_array", Z3::IntSort, 5)

    size = array.size_term
    assert_instance_of Z3::IntExpr, size
  end
end
