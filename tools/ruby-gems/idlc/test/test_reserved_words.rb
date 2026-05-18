# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require "minitest/autorun"

require "idlc"
require_relative "helpers"

$root ||= (Pathname.new(__FILE__) / ".." / ".." / ".." / "..").realpath

# Test that reserved words (keywords and builtin type names) are properly rejected
# in contexts where user-defined identifiers are expected
class TestReservedWords < Minitest::Test
  include TestMixin

  # All builtin type names that should be reserved
  BUILTIN_TYPES = %w[XReg Boolean String U64 U32 Bits]

  # All keywords that should be reserved
  KEYWORDS = %w[
    if else for return returns arguments description body
    function builtin generated enum bitfield CSR true false
  ]

  # Test that reserved words cannot be used as function names
  def test_keywords_rejected_as_function_names
    KEYWORDS.each do |keyword|
      idl = "%version: 0.11\nfunction #{keyword} { description { test } body { return; } }"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl)

      refute_nil result, "Keyword '#{keyword}' should parse"

      error = assert_raises(Idl::AstNode::TypeError) do
        ast = result.to_ast
        symtab = Idl::SymbolTable.new
        ast.add_global_symbols(symtab)
      end

      assert_match(/Cannot use reserved word '#{keyword}' as function name/, error.message)
    end
  end

  def test_builtin_types_rejected_as_function_names
    BUILTIN_TYPES.each do |typename|
      idl = "%version: 0.11\nfunction #{typename} { description { test } body { return; } }"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl)

      refute_nil result, "Builtin type '#{typename}' should parse"

      error = assert_raises(Idl::AstNode::TypeError) do
        ast = result.to_ast
        symtab = Idl::SymbolTable.new
        ast.add_global_symbols(symtab)
      end

      assert_match(/Cannot use reserved word '#{typename}' as function name/, error.message)
    end
  end

  # Test that reserved words cannot be used as variable names (id)
  def test_keywords_rejected_as_variable_names
    # Note: "true" and "false" are expressions, not valid variable names in any context
    # Note: "CSR" is uppercase so can't be used as a variable name (variables must start lowercase)
    keywords_to_test = KEYWORDS.reject { |k| %w[true false CSR].include?(k) }

    keywords_to_test.each do |keyword|
      idl = "%version: 0.11\nfunction testFunc { description { test } body { Bits<32> #{keyword}; } }"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl)

      refute_nil result, "Keyword '#{keyword}' should parse"

      error = assert_raises(Idl::AstNode::TypeError) do
        ast = result.to_ast
        ast.type_check(Idl::SymbolTable.new, strict: false)
      end

      assert_match(/Cannot use reserved word '#{keyword}' as variable name/, error.message)
    end
  end

  # Test that reserved words cannot be used as user-defined type names
  def test_keywords_rejected_as_type_names
    # For enum names (which use user_type_name rule), only uppercase keywords can be tested
    # since enum names must start with uppercase
    keywords_to_test = KEYWORDS.select { |k| k[0] == k[0].upcase }

    keywords_to_test.each do |keyword|
      idl = "enum #{keyword} { Value0 }"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl, root: :enum_definition)

      refute_nil result, "Keyword '#{keyword}' should parse"

      error = assert_raises(Idl::AstNode::TypeError) do
        ast = result.to_ast
        symtab = Idl::SymbolTable.new
        ast.type_check(symtab, strict: false)
      end

      assert_match(/Cannot use reserved word '#{keyword}' as user-defined type name/, error.message)
    end
  end

  def test_builtin_types_rejected_as_type_names
    BUILTIN_TYPES.each do |typename|
      idl = "enum #{typename} { Value0 }"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl, root: :enum_definition)

      # Some builtin types (like "XReg", "Bits", etc.) may parse as builtin type names rather than user type names
      # In this case, we get a different error (TypeError from sorbet validation)
      # Either way, the reserved word is rejected
      if result.nil?
        # If it doesn't parse, that's also acceptable - the reserved word is rejected
        next
      end

      error = assert_raises(StandardError) do
        ast = result.to_ast
        symtab = Idl::SymbolTable.new
        ast.type_check(symtab, strict: false)
      end

      # Accept any error that prevents using the reserved word
      assert(
        error.is_a?(Idl::AstNode::TypeError) || error.is_a?(TypeError),
        "Expected TypeError, got: #{error.class} - #{error.message}"
      )
    end
  end

  # Test that non-reserved words ARE allowed
  def test_valid_function_names_accepted
    valid_names = %w[myFunc getValue]

    valid_names.each do |name|
      # Parse as function call expression
      idl = "#{name}()"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl, root: :expression)

      refute_nil result, "Valid function name '#{name}' should be accepted"
    end
  end

  def test_valid_variable_names_accepted
    valid_names = %w[myVar my_var var123 counter value]

    valid_names.each do |name|
      idl = "Bits<32> #{name}"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl, root: :single_declaration)

      refute_nil result, "Valid variable name '#{name}' should be accepted"
    end
  end

  def test_valid_type_names_accepted
    valid_names = %w[MyType MyEnum Status CustomType]

    valid_names.each do |name|
      idl = "enum #{name} { Value0 }"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl, root: :enum_definition)

      refute_nil result, "Valid type name '#{name}' should be accepted"
    end
  end

  # Test that reserved words with additional characters are allowed
  # (e.g., "iffy" contains "if" but should be allowed)
  def test_names_containing_keywords_accepted
    names_with_keywords = %w[iffy forLoop returning bitfieldValue]

    names_with_keywords.each do |name|
      # Parse as function call
      idl = "#{name}()"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl, root: :expression)

      refute_nil result, "Name '#{name}' containing keyword substring should be accepted"
    end
  end

  # Test case sensitivity - keywords are lowercase, so uppercase versions should work
  def test_uppercase_keywords_accepted_as_type_names
    uppercase_keywords = %w[If Else For Return Function]

    uppercase_keywords.each do |name|
      idl = "enum #{name} { Value0 }"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl, root: :enum_definition)

      refute_nil result, "Uppercase keyword '#{name}' should be accepted as type name"
    end
  end

  # Edge case: function names can end with '?'
  def test_function_names_with_question_mark
    # Parse as a function call expression instead
    idl = "isValid?()"

    compiler = Idl::Compiler.new
    result = compiler.parser.parse(idl, root: :expression)

    refute_nil result, "Function names with '?' should be accepted"
  end

  ##########################################
  # Comprehensive tests for all declaration rules
  ##########################################

  # Test that reserved words are rejected in bitfield definitions (bitfield name)
  def test_keywords_rejected_as_bitfield_names
    keywords_to_test = KEYWORDS.select { |k| k[0] == k[0].upcase }

    keywords_to_test.each do |keyword|
      idl = "bitfield(32) #{keyword} { field 0 }"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl, root: :bitfield_definition)

      refute_nil result, "Keyword '#{keyword}' should parse as bitfield name"

      error = assert_raises(Idl::AstNode::TypeError) do
        ast = result.to_ast
        symtab = Idl::SymbolTable.new
        ast.type_check(symtab, strict: false)
      end

      assert_match(/Cannot use reserved word '#{keyword}' as user-defined type name/, error.message)
    end
  end

  def test_builtin_types_rejected_as_bitfield_names
    BUILTIN_TYPES.each do |typename|
      idl = "bitfield(32) #{typename} { field 0 }"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl, root: :bitfield_definition)

      refute_nil result, "Builtin type '#{typename}' should parse as bitfield name"

      # Accept either TypeError (reserved word check) or DuplicateSymError (builtin already defined)
      begin
        ast = result.to_ast
        symtab = Idl::SymbolTable.new
        ast.type_check(symtab, strict: false)
        flunk("Builtin type '#{typename}' was not rejected - type check passed")
      rescue StandardError => error
        assert(
          error.is_a?(Idl::AstNode::TypeError) || error.is_a?(Idl::SymbolTable::DuplicateSymError),
          "Expected TypeError or DuplicateSymError for '#{typename}', got: #{error.class} - #{error.message}"
        )
      end
    end
  end

  # Test that reserved words are rejected in struct definitions (struct name)
  def test_keywords_rejected_as_struct_names
    keywords_to_test = KEYWORDS.select { |k| k[0] == k[0].upcase }

    keywords_to_test.each do |keyword|
      idl = "struct #{keyword} { U32 field; }"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl, root: :struct_definition)

      refute_nil result, "Keyword '#{keyword}' should parse as struct name"

      error = assert_raises(Idl::AstNode::TypeError) do
        ast = result.to_ast
        symtab = Idl::SymbolTable.new
        ast.type_check(symtab, strict: false)
      end

      assert_match(/Cannot use reserved word '#{keyword}' as user-defined type name/, error.message)
    end
  end

  def test_builtin_types_rejected_as_struct_names
    BUILTIN_TYPES.each do |typename|
      idl = "struct #{typename} { U32 field; }"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl, root: :struct_definition)

      refute_nil result, "Builtin type '#{typename}' should parse as struct name"

      error = assert_raises(Idl::AstNode::TypeError) do
        ast = result.to_ast
        symtab = Idl::SymbolTable.new
        ast.type_check(symtab, strict: false)
      end

      assert_match(/Cannot use reserved word '#{typename}' as user-defined type name/, error.message)
    end
  end

  # Test that reserved words are rejected as struct member names
  def test_keywords_rejected_as_struct_member_names
    # Filter to lowercase keywords that can be used as variable names
    keywords_to_test = KEYWORDS.reject { |k| %w[true false CSR].include?(k) }

    keywords_to_test.each do |keyword|
      idl = "struct MyStruct { U32 #{keyword}; }"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl, root: :struct_definition)

      refute_nil result, "Keyword '#{keyword}' should parse as struct member name"

      error = assert_raises(Idl::AstNode::TypeError) do
        ast = result.to_ast
        symtab = Idl::SymbolTable.new
        ast.type_check(symtab, strict: false)
      end

      assert_match(/Cannot use reserved word '#{keyword}' as variable name/, error.message)
    end
  end

  # Test that reserved words are rejected as function parameter names
  def test_keywords_rejected_as_function_parameter_names
    keywords_to_test = KEYWORDS.reject { |k| %w[true false CSR].include?(k) }

    keywords_to_test.each do |keyword|
      idl = "%version: 0.11\nfunction testFunc { arguments U32 #{keyword} description { test } body { return; } }"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl)

      refute_nil result, "Keyword '#{keyword}' should parse as function parameter name"

      error = assert_raises(Idl::AstNode::TypeError) do
        ast = result.to_ast
        ast.type_check(Idl::SymbolTable.new, strict: false)
      end

      assert_match(/Cannot use reserved word '#{keyword}' as variable name/, error.message)
    end
  end

  def test_builtin_types_rejected_as_function_parameter_names
    # Builtin type names are uppercase, but variable names starting with uppercase
    # are treated as constants and get different validation errors.
    # The important thing is that they are rejected.
    BUILTIN_TYPES.each do |typename|
      # Skip if the typename starts with lowercase (there are none currently, but for safety)
      next if typename[0] == typename[0].downcase

      idl = "%version: 0.11\nfunction testFunc { arguments U32 #{typename} description { test } body { return; } }"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl)

      # This won't parse correctly because function parameters must be lowercase identifiers
      # If it does parse, it should fail type check with some error
      if result.nil?
        # Parse failure is acceptable - it prevents using the reserved word
        next
      end

      # If it does parse, it should fail type check with either:
      # - "Constants must be initialized" (uppercase = constant)
      # - "Cannot use reserved word" (explicit check)
      error = assert_raises(Idl::AstNode::TypeError) do
        ast = result.to_ast
        ast.type_check(Idl::SymbolTable.new, strict: false)
      end

      # Accept either error message - both prevent using the reserved word
      assert(
        error.message.match?(/Constants must be initialized|Cannot use reserved word/),
        "Expected constant or reserved word error, got: #{error.message}"
      )
    end
  end

  # Test that reserved words are rejected in global variable declarations
  def test_keywords_rejected_as_global_variable_names
    keywords_to_test = KEYWORDS.reject { |k| %w[true false CSR].include?(k) }

    keywords_to_test.each do |keyword|
      idl = "%version: 0.11\nU32 #{keyword};"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl)

      refute_nil result, "Keyword '#{keyword}' should parse as global variable name"

      error = assert_raises(Idl::AstNode::TypeError) do
        ast = result.to_ast
        ast.type_check(Idl::SymbolTable.new, strict: false)
      end

      assert_match(/Cannot use reserved word '#{keyword}' as variable name/, error.message)
    end
  end

  # Test that reserved words are rejected in const global variable declarations
  def test_keywords_rejected_as_const_global_variable_names
    keywords_to_test = KEYWORDS.reject { |k| %w[true false CSR].include?(k) }

    keywords_to_test.each do |keyword|
      idl = "%version: 0.11\nconst U32 #{keyword} = 42;"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl)

      refute_nil result, "Keyword '#{keyword}' should parse as const global variable name"

      error = assert_raises(Idl::AstNode::TypeError) do
        ast = result.to_ast
        ast.type_check(Idl::SymbolTable.new, strict: false)
      end

      assert_match(/Cannot use reserved word '#{keyword}' as variable name/, error.message)
    end
  end

  # Test that reserved words are rejected in for loop iteration variables
  def test_keywords_rejected_as_for_loop_variables
    keywords_to_test = KEYWORDS.reject { |k| %w[true false CSR].include?(k) }

    keywords_to_test.each do |keyword|
      idl = "%version: 0.11\nfunction testFunc { description { test } body { for (U32 #{keyword} = 0; #{keyword} < 10; #{keyword}++) { return; } } }"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl)

      refute_nil result, "Keyword '#{keyword}' should parse as for loop variable"

      error = assert_raises(Idl::AstNode::TypeError) do
        ast = result.to_ast
        ast.type_check(Idl::SymbolTable.new, strict: false)
      end

      assert_match(/Cannot use reserved word '#{keyword}' as variable name/, error.message)
    end
  end

  # Test that reserved words are rejected as enum member names
  def test_keywords_rejected_as_enum_member_names
    # Only uppercase keywords can be enum members
    keywords_to_test = KEYWORDS.select { |k| k[0] == k[0].upcase }

    keywords_to_test.each do |keyword|
      idl = "enum MyEnum { #{keyword} }"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl, root: :enum_definition)

      refute_nil result, "Keyword '#{keyword}' should parse as enum member"

      error = assert_raises(Idl::AstNode::TypeError) do
        ast = result.to_ast
        symtab = Idl::SymbolTable.new
        ast.type_check(symtab, strict: false)
      end

      assert_match(/Cannot use reserved word '#{keyword}' as enum member/, error.message)
    end
  end

  def test_builtin_types_rejected_as_enum_member_names
    BUILTIN_TYPES.each do |typename|
      idl = "enum MyEnum { #{typename} }"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl, root: :enum_definition)

      refute_nil result, "Builtin type '#{typename}' should parse as enum member"

      error = assert_raises(Idl::AstNode::TypeError) do
        ast = result.to_ast
        symtab = Idl::SymbolTable.new
        ast.type_check(symtab, strict: false)
      end

      assert_match(/Cannot use reserved word '#{typename}' as enum member/, error.message)
    end
  end

  # Test builtin function definitions
  def test_keywords_rejected_as_builtin_function_names
    KEYWORDS.each do |keyword|
      idl = "%version: 0.11\nbuiltin function #{keyword} { description { test } }"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl)

      refute_nil result, "Keyword '#{keyword}' should parse as builtin function name"

      error = assert_raises(Idl::AstNode::TypeError) do
        ast = result.to_ast
        symtab = Idl::SymbolTable.new
        ast.add_global_symbols(symtab)
      end

      assert_match(/Cannot use reserved word '#{keyword}' as function name/, error.message)
    end
  end

  def test_builtin_types_rejected_as_builtin_function_names
    BUILTIN_TYPES.each do |typename|
      idl = "%version: 0.11\nbuiltin function #{typename} { description { test } }"

      compiler = Idl::Compiler.new
      result = compiler.parser.parse(idl)

      refute_nil result, "Builtin type '#{typename}' should parse as builtin function name"

      error = assert_raises(Idl::AstNode::TypeError) do
        ast = result.to_ast
        symtab = Idl::SymbolTable.new
        ast.add_global_symbols(symtab)
      end

      assert_match(/Cannot use reserved word '#{typename}' as function name/, error.message)
    end
  end
end
