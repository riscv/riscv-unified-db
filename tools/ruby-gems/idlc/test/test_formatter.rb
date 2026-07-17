# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/idlc/formatter"

class TestFormatter < Minitest::Test
  # Topiary (and the compiled grammar) are needed to actually format. They are
  # available in CI and dev (via mise); skip the format-dependent cases when
  # they are not, so the suite still runs in a degraded environment.
  def formatting_available?
    !Idl::Formatter::GRAMMAR_SO.nil? && !Idl::Formatter::QUERY_DIR.nil?
  end

  def reflow_available?
    formatting_available? && !Idl::Formatter::REFLOW_JS.nil?
  end

  def test_blank_input_is_returned_unchanged
    assert_equal "", Idl::Formatter.format("")
    assert_equal "   \n", Idl::Formatter.format("   \n")
  end

  def test_applies_canonical_spacing_and_indentation
    skip "topiary grammar unavailable" unless formatting_available?
    assert_equal "if (x == 0) {\n  return 0;\n}",
                 Idl::Formatter.format("if (x == 0){return 0;}")
  end

  def test_format_is_idempotent
    skip "topiary grammar unavailable" unless formatting_available?
    once = Idl::Formatter.format("if (x == 0){return 0;}")
    assert_equal once, Idl::Formatter.format(once)
  end

  def test_without_column_width_does_not_reflow
    skip "topiary grammar unavailable" unless formatting_available?
    long = "x = aaaaaaaa && bbbbbbbb && cccccccc && dddddddd && eeeeeeee;"
    # Pass 1 (topiary) only adjusts spacing/indent; it must not wrap.
    assert_equal long, Idl::Formatter.format(long)
  end

  def test_column_width_wraps_long_lines
    skip "topiary/node reflow unavailable" unless reflow_available?
    long = "x = aaaaaaaa && bbbbbbbb && cccccccc && dddddddd && eeeeeeee;"
    wide   = Idl::Formatter.format(long)
    narrow = Idl::Formatter.format(long, column_width: 30)
    refute_equal wide, narrow
    assert_operator narrow.count("\n"), :>, wide.count("\n")
    assert_includes narrow, "&&"
  end
end
