# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require "idlc"
require "idlc/ast"
require_relative "helpers"
require "minitest/autorun"
require "yaml"

$root ||= (Pathname.new(__FILE__) / ".." / ".." / ".." / "..").realpath

# Data-driven type checking tests
# Test cases are loaded from YAML files in test/data/
class TestTypeCheckingDataDriven < Minitest::Test
  include TestMixin

  # Load test data from YAML file
  TEST_DATA_FILE = File.join(__dir__, "data", "type_checking_tests.yaml")
  TEST_DATA = YAML.load_file(TEST_DATA_FILE)

  def setup
    @symtab = Idl::SymbolTable.new(
      possible_xlens_cb: proc { [32, 64] }
    )
    @compiler = Idl::Compiler.new
  end

  # Dynamically generate test methods from YAML data
  TEST_DATA.each do |category, test_cases|
    test_cases.each_with_index do |test_case, index|
      test_name = "test_#{category}_#{test_case['name']}"

      define_method(test_name) do
        run_test_case(test_case, category)
      end
    end
  end

  private

  def run_test_case(test_case, category)
    # Add context to assertion messages
    context = "#{category}/#{test_case['name']}: #{test_case['description']}"

    if test_case["should_pass"]
      # Positive test case - should compile and type check successfully
      ast = compile_idl(test_case["idl"], test_case["test_type"])

      # Get the type to check
      type = if test_case["test_type"] == "initialization"
        # For statements, check the LHS type
               ast.lhs.type(@symtab)
      else
        # For expressions, check the expression type
        ast.type(@symtab)
      end

      # Verify expected type properties
      expected = test_case["expected_type"]
      assert_equal expected["kind"].to_sym, type.kind,
        "#{context}: Expected kind :#{expected['kind']}, got :#{type.kind}"

      if expected["width"]
        assert_equal expected["width"], type.width,
          "#{context}: Expected width #{expected['width']}, got #{type.width}"
      elsif expected["width"].nil? && expected.key?("width")
        # width: null means MXLEN-dependent
        # Check max_width constraint if specified in test data
        if expected.key?("max_width")
          max_width = expected["max_width"]
          # type.width might be a Symbol like :MXLEN, :XLEN, :unknown or a number
          if type.width.is_a?(Integer)
            assert type.width <= max_width,
              "#{context}: Width should be at most #{max_width}, got #{type.width}"
          else
            # If it's a symbol like :MXLEN or :unknown, we can't check the exact value
            # but we validate it's an expected symbol
            assert [:MXLEN, :XLEN, :unknown].include?(type.width) || type.width.is_a?(Integer),
              "#{context}: Expected MXLEN-dependent width (symbol or <=#{max_width}), got #{type.width}"
          end
        end
      end

      if expected.key?("signed")
        if expected["signed"]
          assert type.signed?, "#{context}: Expected signed type"
        else
          refute type.signed?, "#{context}: Expected unsigned type"
        end
      end
    else
      # Negative test case - should raise an error
      error_class = Object.const_get(test_case["expected_error"])

      assert_raises(error_class, "#{context}: Expected #{test_case['expected_error']}") do
        compile_idl(test_case["idl"], test_case["test_type"])
      end
    end
  end

  def compile_idl(idl, test_type)
    root = test_type == "initialization" ? :assignment : :expression

    @compiler.parser.set_input_file("", 0)
    m = @compiler.parser.parse(idl, root: root)

    unless m
      raise "Failed to parse IDL: #{idl}\nReason: #{@compiler.parser.failure_reason}"
    end

    ast = m.to_ast
    raise "Failed to convert to AST" unless ast

    ast.freeze_tree(@symtab)
    ast.type_check(@symtab, strict: false)
    ast
  end
end
