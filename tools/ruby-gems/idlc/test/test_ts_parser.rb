# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/idlc/ts_parser"

class TestTsParser < Minitest::Test
  # ---------------------------------------------------------------------------
  # format_errors
  # ---------------------------------------------------------------------------

  def test_format_errors_includes_filename_and_line
    errors = Idl::TsParser.check_errors("1 +")
    msg = Idl::TsParser.format_errors("1 +", errors, filename: "foo.idl")
    assert_includes msg, "foo.idl"
    assert_includes msg, "1:"
  end

  def test_format_errors_includes_source_context
    source = "x = 1;\n1 +\ny = 2;"
    errors = Idl::TsParser.check_errors(source)
    msg = Idl::TsParser.format_errors(source, errors, filename: "foo.idl")
    assert_includes msg, "1 +"
  end

  def test_format_errors_missing_says_expected
    errors = Idl::TsParser.check_errors("1 +")
    msg = Idl::TsParser.format_errors("1 +", errors, filename: "foo.idl")
    assert_includes msg, "expected"
  end

  def test_format_errors_starting_line_offset
    errors = Idl::TsParser.check_errors("1 +")
    msg = Idl::TsParser.format_errors("1 +", errors, filename: "foo.idl", starting_line: 10)
    assert_includes msg, "11:"
  end

  def test_valid_expression_has_no_errors
    assert_empty Idl::TsParser.check_errors("1 + 2")
  end

  def test_incomplete_expression_returns_errors
    errors = Idl::TsParser.check_errors("1 +")
    refute_empty errors
  end

  def test_missing_node_has_type_missing
    errors = Idl::TsParser.check_errors("1 +")
    assert errors.any? { |e| e[:type] == :missing }
  end

  def test_missing_node_has_location
    errors = Idl::TsParser.check_errors("1 +")
    missing = errors.find { |e| e[:type] == :missing }
    assert_equal 1, missing[:line]
    assert_equal 4, missing[:col]
  end
end
