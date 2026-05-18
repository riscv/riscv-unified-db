# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require "ostruct"

# Minimal mock register entry
MockRegEntry = Struct.new(:name)

# Minimal mock register file that satisfies SymbolTable's register_files interface.
# Used to provide X (and other) register files in test symtab setup.
class MockRegFile
  attr_reader :name, :register_length, :registers

  def initialize(name, register_length_idl, count)
    @name = name
    @register_length = register_length_idl
    @registers = Array.new(count) { |i| MockRegEntry.new("#{name.downcase}#{i}") }
  end
end

DEFAULT_X_REGISTER_FILE = MockRegFile.new("X", "return MXLEN;", 32)

# Extension mock that returns an extension name
class Xmockension
  attr_reader :name
  def initialize(name)
    @name = name
  end
end

XmockensionParameter = Struct.new(:name, :desc, :schema, :extra_validation, :exts, :type)
XmockensionParameterWithValue = Struct.new(:name, :desc, :schema, :extra_validation, :exts, :value)

# ConfiguredArchitecture mock that knows about XLEN and extensions
class MockConfiguredArchitecture
  def param_values = { "XLEN" => 32 }
  def params_with_value = [XmockensionParameterWithValue.new("XLEN", "mxlen", { "type" => "integer", "enum" => [32, 64] }, nil, nil, 32)]
  def params_without_value = []
  def params = []
  def extensions = [Xmockension.new("I")]
  def mxlen = 64
  def exception_codes = [OpenStruct.new(var: "ACode", num: 0), OpenStruct.new(var: "BCode", num: 1)]
  def interrupt_codes = [OpenStruct.new(var: "CoolInterrupt", num: 1)]

  def fully_configured? = false
  def partially_configured? = true
  def unconfigured? = false

  def name = "mock"

  attr_accessor :global_ast
end

module TestMixin
  def param_syms
    {
      "XLEN" => Idl::Var.new("XLEN", Idl::Type.new(:bits, width: 8), 32)
    }
  end
  class MockCsrFieldClass
    require "idlc/interfaces"
    include Idl::CsrField
    def initialize(name, val, loc)
      @name = name
      @val = val
      @loc = loc
    end
    attr_reader :name
    def defined_in_all_bases? = true
    def defined_in_base32? = true
    def defined_in_base64? = true
    def base64_only? = false
    def base32_only? = false
    def location(_) = @loc
    def width(_) = 32
    def type(_) = @val.nil? ? "RW" : "RO"
    def exists? = true
    def reset_value = @val.nil? ? "UNDEFINED_LEGAL" : @val
  end
  def setup
    @symtab = Idl::SymbolTable.new(register_files: [DEFAULT_X_REGISTER_FILE])
    @compiler = Idl::Compiler.new
    @mock_csr_field_class = MockCsrFieldClass
  end
end
