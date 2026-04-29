# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require "minitest/autorun"

require "idlc"
require "idlc/passes/find_src_registers"
require_relative "helpers"

$root ||= (Pathname.new(__FILE__) / ".." / ".." / ".." / "..").realpath

# Minimal mock register entry for testing
MockRegisterEntry = Struct.new(:name)

# Minimal mock register file for testing
class MockRegisterFile
  attr_reader :name, :register_length

  def initialize(name, register_length_idl, count)
    @name = name
    @register_length = register_length_idl
    @registers = Array.new(count) { |i| MockRegisterEntry.new("#{name.downcase}#{i}") }
  end

  def registers = @registers
end

# Tests for register file generalization in the IDL symbol table and type system.
#
# These tests drive the implementation of:
#   - Idl::RegFileElementType (replaces XregType, generalized for any register file)
#   - SymbolTable.new(register_files: [...]) parameter
#   - find_src_registers / find_dst_registers returning [rf_name, index] pairs
class TestRegisterFiles < Minitest::Test
  def setup
    @mock_f_rf = MockRegisterFile.new("F", "return 64;", 32)
    @mock_v_rf = MockRegisterFile.new("V", "return VLEN;", 32)
    @compiler = Idl::Compiler.new
  end

  # Verify that SymbolTable.new(register_files: [...]) registers:
  #   - "F" as a global array var whose sub_type is a RegFileElementType named "F"
  #   - "FReg" as a RegFileElementType
  def test_regfile_globals_registered
    symtab = Idl::SymbolTable.new(register_files: [@mock_f_rf])

    f_var = symtab.get("F")
    refute_nil f_var, "Expected 'F' to be defined in symtab"
    assert_equal :array, f_var.type.kind
    assert_equal 32, f_var.type.width
    assert f_var.type.qualifiers.include?(:global), "Expected :global qualifier on F"

    sub = f_var.type.sub_type
    assert_instance_of Idl::RegFileElementType, sub, "Expected sub_type to be RegFileElementType"
    assert_equal "F", sub.name
    assert_equal 64, sub.width

    freg_type = symtab.get("FReg")
    refute_nil freg_type, "Expected 'FReg' to be defined in symtab"
    assert_instance_of Idl::RegFileElementType, freg_type
  end

  # Verify that IDL code `FReg v = F[rs1];` type-checks when F is registered.
  def test_regfile_element_access_typechecks
    symtab = Idl::SymbolTable.new(
      register_files: [@mock_f_rf],
      builtin_global_vars: [
        Idl::Var.new("rs1", Idl::Type.new(:bits, width: 5))
      ]
    )

    ast = @compiler.compile_func_body(
      "FReg v = F[rs1]; return v;",
      symtab:,
      return_type: Idl::Type.new(:bits, width: 64),
      no_rescue: true,
      input_file: ""
    )
    refute_nil ast
  end

  # Verify that IDL code `F[rd] = v;` type-checks when F is registered.
  def test_regfile_element_write_typechecks
    symtab = Idl::SymbolTable.new(
      register_files: [@mock_f_rf],
      builtin_global_vars: [
        Idl::Var.new("rd", Idl::Type.new(:bits, width: 5)),
        Idl::Var.new("v", Idl::Type.new(:bits, width: 64))
      ]
    )

    ast = @compiler.compile_func_body(
      "F[rd] = v;",
      symtab:,
      return_type: Idl::VoidType,
      no_rescue: true,
      input_file: ""
    )
    refute_nil ast
  end

  # Verify that F[0] is not a compile-time constant (register reads are runtime-only).
  def test_regfile_not_const_eval
    symtab = Idl::SymbolTable.new(register_files: [@mock_f_rf])

    m = @compiler.parser.parse("F[0]", root: :expression)
    refute_nil m
    ast = m.to_ast

    refute ast.const_eval?(symtab), "F[0] should not be compile-time-evaluable"
  end

  # Verify find_src_registers returns [[rf_name, index]] pairs for F register reads.
  def test_regfile_find_src_registers
    symtab = Idl::SymbolTable.new(
      register_files: [@mock_f_rf],
      builtin_global_vars: [
        Idl::Var.new("rs1", Idl::Type.new(:bits, width: 5), 3),
        Idl::Var.new("rd", Idl::Type.new(:bits, width: 5), 7)
      ]
    )

    m = @compiler.parser.parse("F[rs1]", root: :expression)
    refute_nil m
    ast = m.to_ast

    srcs = ast.find_src_registers(symtab)
    assert_equal [["F", 3]], srcs, "Expected find_src_registers to return [[\"F\", 3]]"
  end

  # Verify find_dst_registers returns [[rf_name, index]] pairs for F register writes.
  def test_regfile_find_dst_registers
    # Need a statement context for assignment
    symtab = Idl::SymbolTable.new(
      register_files: [@mock_f_rf],
      builtin_global_vars: [
        Idl::Var.new("rd", Idl::Type.new(:bits, width: 5), 7),
        Idl::Var.new("v", Idl::Type.new(:bits, width: 64))
      ]
    )

    m = @compiler.parser.parse("F[rd] = v;", root: :statement)
    refute_nil m
    ast = m.to_ast

    dsts = ast.find_dst_registers(symtab)
    assert_equal [["F", 7]], dsts, "Expected find_dst_registers to return [[\"F\", 7]]"
  end

  # Regression test: X register file still works after generalization.
  def test_x_register_still_works
    # X is populated via register_files: in the new implementation,
    # but still appears as a global array of XReg (now RegFileElementType named "X")
    mock_x_rf = MockRegisterFile.new("X", "return MXLEN;", 32)
    symtab = Idl::SymbolTable.new(mxlen: 64, register_files: [mock_x_rf])

    x_var = symtab.get("X")
    refute_nil x_var, "X should still be in symtab"
    assert_equal :array, x_var.type.kind
    assert_equal 32, x_var.type.width
    assert x_var.type.qualifiers.include?(:global)

    sub = x_var.type.sub_type
    assert_instance_of Idl::RegFileElementType, sub
    assert_equal "X", sub.name
    assert_equal 64, sub.width

    # Check that XReg type alias still exists
    xreg_type = symtab.get("XReg")
    refute_nil xreg_type
    assert_instance_of Idl::RegFileElementType, xreg_type
  end
end
