# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require "minitest/autorun"
require_relative "../lib/idl_highlighter/linked_html_formatter"

class TestLinkedHtmlFormatter < Minitest::Test
  def fmt(source, link_map = {})
    IdlHighlighter::LinkedHtmlFormatter.format(source, link_map)
  end

  def test_wraps_in_pre_code
    result = fmt("x")
    assert_match(/<pre class="rouge highlight"><code class="language-idl hljs">/, result)
    assert_match(/<\/code><\/pre>$/, result)
  end

  def test_keyword_gets_span
    result = fmt("if")
    assert_includes result, '<span class="k">if</span>'
  end

  def test_name_gets_span
    result = fmt("my_func")
    assert_includes result, '<span class="n">my_func</span>'
  end

  def test_whitespace_is_included
    result = fmt("x y")
    assert_includes result, "x"
    assert_includes result, "y"
  end

  def test_html_escapes_special_chars
    result = fmt("x < y")
    assert_includes result, "&lt;"
    refute_includes result, " < "
  end

  def test_linked_name_wraps_in_anchor
    link_map = { "raise_Illegal_Instruction" => "../funcs/funcs.html#udb:doc:func:raise_Illegal_Instruction" }
    result = fmt("raise_Illegal_Instruction(0);", link_map)
    assert_includes result, '<a href="../funcs/funcs.html#udb:doc:func:raise_Illegal_Instruction"><span class="n">raise_Illegal_Instruction</span></a>'
  end

  def test_linked_name_still_highlights_surrounding_tokens
    link_map = { "foo" => "#foo-anchor" }
    result = fmt("if (foo) {", link_map)
    assert_includes result, '<span class="k">if</span>'
    assert_includes result, '<a href="#foo-anchor"><span class="n">foo</span></a>'
  end

  def test_unlinked_name_not_wrapped_in_anchor
    link_map = { "other" => "#other-anchor" }
    result = fmt("my_func()", link_map)
    assert_includes result, '<span class="n">my_func</span>'
    refute_includes result, "<a href"
  end

  def test_empty_link_map_no_anchors
    result = fmt("return x + 1;")
    refute_includes result, "<a href"
  end

  def test_uppercase_name_gets_no_span
    # Identifiers starting with uppercase match Name::Constant (no) per the IDL lexer
    result = fmt("Bits")
    assert_includes result, '<span class="no">Bits</span>'
  end

  def test_number_gets_span
    result = fmt("42")
    assert_includes result, '<span class="mi">42</span>'
  end
end
