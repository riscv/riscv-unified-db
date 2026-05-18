# typed: false
# frozen_string_literal: true

# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

require_relative "helpers"
require "yaml"
require "minitest/autorun"
require "idlc"

# Test class for control flow type checking using data-driven approach
class TestControlFlow < Minitest::Test
  TEST_DATA_FILE = File.join(__dir__, "data", "control_flow_tests.yaml")

  def setup
    @test_data = YAML.load_file(TEST_DATA_FILE)
  end

  # Dynamically generate test methods for each test case
  @test_data = YAML.load_file(File.join(__dir__, "data", "control_flow_tests.yaml"))
  @test_data.each do |category, tests|
    tests.each do |test_case|
      test_name = "test_#{category}_#{test_case['name']}"

      define_method(test_name) do
        run_test_case(test_case, category)
      end
    end
  end

  private

  def run_test_case(test_case, category)
    idl_code = test_case["idl"]
    should_pass = test_case["should_pass"]
    expected_error = test_case["expected_error"]
    description = test_case["description"]
    context = test_case["context"]

    if should_pass
      # Test should pass - no exception expected
      begin
        compile_idl_block(idl_code, context)
      rescue => e
        flunk("#{category}/#{test_case['name']}: #{description}: Expected to pass but got error: #{e.class}: #{e.message}")
      end
    else
      # Test should fail - expect specific exception
      assert_raises(eval(expected_error), "#{category}/#{test_case['name']}: #{description}: Expected #{expected_error}") do
        compile_idl_block(idl_code, context)
      end
    end
  end

  def compile_idl_block(idl_code, context)
    # Parse and type-check the IDL code block
    # Control flow constructs must be in a function body context
    full_idl =
      if context == "root"
        <<~IDL
          %version: 1.0

          #{idl_code}
        IDL
      elsif context == "body"
        <<~IDL
          %version: 1.0

          function test_function {
            returns Bits<32>
            description {
              Test function for control flow type checking
            }
            body {
              #{idl_code}
              return 32'd0;
            }
          }
        IDL
      else
        raise "unhandled context #{context}"
      end

    begin
      compiler = Idl::Compiler.new
      m = compiler.parser.parse(full_idl, root: :isa)
      raise "#{compiler.parser.failure_reason}" if m.nil?

      ast = m.to_ast

      # Create a symbol table and type-check
      symtab = Idl::SymbolTable.new
      ast.type_check(symtab, strict: false)
    rescue Idl::AstNode::TypeError, Idl::AstNode::ValueError => e
      # Re-raise type/value errors for test assertions
      raise e
    rescue => e
      # Wrap other errors with context
      raise RuntimeError, "Failed to parse IDL: #{idl_code.strip}\nReason: #{e.message}"
    end
  end
end
