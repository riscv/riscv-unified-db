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

# test IDL arrays
class TestArrays < Minitest::Test
  include TestMixin

  def test_element_access
    idl = "ary[0]"

    symtab = Idl::SymbolTable.new(
      possible_xlens_cb: proc { [32, 64] }
    )
    @compiler.parser.set_input_file(idl, 0)
    m = @compiler.parser.parse(idl, root: :ary_access)
    refute_nil m
  end

  def test_element_access_var_index
    idl = "ary[var]"

    symtab = Idl::SymbolTable.new(
      possible_xlens_cb: proc { [32, 64] }
    )
    @compiler.parser.set_input_file(idl, 0)
    m = @compiler.parser.parse(idl, root: :ary_access)
    refute_nil m
  end

  def test_range_access
    idl = "ary[0:1]"

    symtab = Idl::SymbolTable.new(
      possible_xlens_cb: proc { [32, 64] }
    )
    @compiler.parser.set_input_file(idl, 0)
    m = @compiler.parser.parse(idl, root: :ary_access)
    refute_nil m
  end

  def test_range_access_var_range
    idl = "ary[var1:var2]"

    symtab = Idl::SymbolTable.new(
      possible_xlens_cb: proc { [32, 64] }
    )
    @compiler.parser.set_input_file(idl, 0)
    m = @compiler.parser.parse(idl, root: :ary_access)
    refute_nil m
  end

  def test_range_access_mixed_range
    idl = "ary[0:var2]"

    symtab = Idl::SymbolTable.new(
      possible_xlens_cb: proc { [32, 64] }
    )
    @compiler.parser.set_input_file(idl, 0)
    m = @compiler.parser.parse(idl, root: :ary_access)
    refute_nil m
  end

  def test_range_access_mixed_range
    idl = "ary[var1:3]"

    symtab = Idl::SymbolTable.new(
      possible_xlens_cb: proc { [32, 64] }
    )
    @compiler.parser.set_input_file(idl, 0)
    m = @compiler.parser.parse(idl, root: :ary_access)
    refute_nil m
  end

  def test_nested_element_access
    idl = "ary[0][1]"

    symtab = Idl::SymbolTable.new(
      possible_xlens_cb: proc { [32, 64] }
    )
    @compiler.parser.set_input_file(idl, 0)
    m = @compiler.parser.parse(idl, root: :ary_access)
    refute_nil m
  end

  def test_nested_element_access_var
    idl = "ary[0][var]"

    symtab = Idl::SymbolTable.new(
      possible_xlens_cb: proc { [32, 64] }
    )
    @compiler.parser.set_input_file(idl, 0)
    m = @compiler.parser.parse(idl, root: :ary_access)
    refute_nil m
  end

  def test_nested_element_range_access_var
    idl = "ary[0][0:var]"

    symtab = Idl::SymbolTable.new(
      possible_xlens_cb: proc { [32, 64] }
    )
    @compiler.parser.set_input_file(idl, 0)
    m = @compiler.parser.parse(idl, root: :ary_access)
    refute_nil m
    assert_instance_of Idl::AryRangeAccessAst, m.to_ast
  end

  def test_element_assignment
    idl = "ary[0] = 5"

    symtab = Idl::SymbolTable.new(
      possible_xlens_cb: proc { [32, 64] }
    )
    @compiler.parser.set_input_file(idl, 0)
    m = @compiler.parser.parse(idl, root: :assignment)
    refute_nil m
    assert_instance_of Idl::AryElementAssignmentAst, m.to_ast
  end

  def test_range_assignment
    idl = "ary[0:1] = 5"

    symtab = Idl::SymbolTable.new(
      possible_xlens_cb: proc { [32, 64] }
    )
    @compiler.parser.set_input_file(idl, 0)
    m = @compiler.parser.parse(idl, root: :assignment)
    refute_nil m
    assert_instance_of Idl::AryRangeAssignmentAst, m.to_ast
  end

  def test_nested_element_assignment
    idl = "ary[0][1] = 5"

    symtab = Idl::SymbolTable.new(
      possible_xlens_cb: proc { [32, 64] }
    )
    @compiler.parser.set_input_file(idl, 0)
    m = @compiler.parser.parse(idl, root: :assignment)
    refute_nil m
    assert_instance_of Idl::AryElementAssignmentAst, m.to_ast
  end

  def test_nested_element_range_assignment
    idl = "ary[0][0:1] = 5"

    symtab = Idl::SymbolTable.new(
      possible_xlens_cb: proc { [32, 64] }
    )
    @compiler.parser.set_input_file(idl, 0)
    m = @compiler.parser.parse(idl, root: :assignment)
    refute_nil m
    assert_instance_of Idl::AryRangeAssignmentAst, m.to_ast
  end

  def test_nested_range_element_assignment
    idl = "ary[0:1][0] = 5"

    symtab = Idl::SymbolTable.new(
      possible_xlens_cb: proc { [32, 64] }
    )
    @compiler.parser.set_input_file(idl, 0)
    m = @compiler.parser.parse(idl, root: :assignment)
    refute_nil m
    assert_instance_of Idl::AryElementAssignmentAst, m.to_ast
  end
end
