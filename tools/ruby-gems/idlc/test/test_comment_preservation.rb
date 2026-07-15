# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require "minitest/autorun"
require "tree_sitter"
require_relative "../lib/idlc/ts_parser"
require_relative "../lib/idlc/ts_ast_builder"
require_relative "../lib/idlc/passes/prune"

class TestCommentPreservation < Minitest::Test
  LABEL = "[TEST]"

  def ts_ast(source, root: :statement_list)
    parser = TreeSitter::Parser.new
    parser.language = Idl::TsParser.language
    tree = parser.parse_string(nil, source)
    ast = Idl::TsAstBuilder.new(source).build(tree.root_node)
    ast.set_input_file(LABEL, 0)
    ast
  end

  # ---------------------------------------------------------------------------
  # attach_comments_to_siblings: end-of-line comment
  # ---------------------------------------------------------------------------

  def test_eol_comment_is_trailing_of_preceding_statement
    src = "x = 1; # eol\ny = 2;"
    body = ts_ast(src)
    stmts = body.stmts
    assert_equal 2, stmts.length
    assert_equal 1, stmts[0].trailing_comments.length, "eol comment should be trailing of x=1"
    assert_equal 0, stmts[1].leading_comments.length, "y=2 should have no leading comments"
    assert_includes stmts[0].trailing_comments[0].to_idl, "eol"
  end

  # ---------------------------------------------------------------------------
  # attach_comments_to_siblings: own-line leading comment (no blank line)
  # ---------------------------------------------------------------------------

  def test_own_line_comment_no_blank_is_leading_of_next
    src = "x = 1;\n# leads y\ny = 2;"
    body = ts_ast(src)
    stmts = body.stmts
    assert_equal 2, stmts.length
    assert_equal 0, stmts[0].trailing_comments.length
    assert_equal 1, stmts[1].leading_comments.length, "comment should be leading of y=2"
    assert_includes stmts[1].leading_comments[0].to_idl, "leads y"
  end

  # ---------------------------------------------------------------------------
  # attach_comments_to_siblings: own-line with blank line is trailing
  # ---------------------------------------------------------------------------

  def test_own_line_comment_with_blank_line_is_trailing_of_prev
    src = "x = 1;\n# trails x\n\ny = 2;"
    body = ts_ast(src)
    stmts = body.stmts
    assert_equal 2, stmts.length
    assert_equal 1, stmts[0].trailing_comments.length, "comment should be trailing of x=1"
    assert_equal 0, stmts[1].leading_comments.length
    assert_includes stmts[0].trailing_comments[0].to_idl, "trails x"
  end

  # ---------------------------------------------------------------------------
  # attach_comments_to_siblings: multi-line trailing block (continuation)
  # ---------------------------------------------------------------------------

  def test_multiline_trailing_block_stays_with_preceding
    src = "x = 1;  # first\n         # second\n         # third\ny = 2;"
    body = ts_ast(src)
    stmts = body.stmts
    assert_equal 2, stmts.length
    assert_equal 3, stmts[0].trailing_comments.length, "all 3 comment lines trail x=1"
    assert_equal 0, stmts[1].leading_comments.length
  end

  # ---------------------------------------------------------------------------
  # to_idl_with_comments round-trip
  # ---------------------------------------------------------------------------

  def test_to_idl_with_comments_emits_leading_comment
    src = "x = 1;\n# leads y\ny = 2;"
    body = ts_ast(src)
    output = body.to_idl(include_comments: true)
    assert_includes output, "# leads y"
    assert_includes output, "y = 2"
  end

  def test_to_idl_without_include_comments_omits_comments
    src = "x = 1;\n# leads y\ny = 2;"
    body = ts_ast(src)
    output = body.to_idl
    refute_includes output, "# leads y"
  end

  # ---------------------------------------------------------------------------
  # Prune: comments in kept branch survive, comments in pruned branch drop
  # ---------------------------------------------------------------------------

  def test_prune_keeps_comments_in_live_branch
    require_relative "../lib/idlc/passes/prune"

    # Build a function body with an if/else where XLEN=64 eliminates the else
    src = <<~IDL
      Bits<32> x;
      Bits<32> y;
      if (XLEN == 64) {
        # keep this
        x = 1;
      } else {
        # drop this
        y = 2;
      }
    IDL

    body = ts_ast(src)
    symtab = Idl::SymbolTable.new
    symtab.add("XLEN", Idl::Var.new("XLEN", Idl::AstNode::Bits64Type, 64))

    pruned = body.prune(symtab)
    output = pruned.to_idl(include_comments: true)

    assert_includes output, "# keep this", "comment from live branch should survive"
    refute_includes output, "# drop this", "comment from dead branch should be absent"
  end

  # ---------------------------------------------------------------------------
  # dup preserves comments (used by prune default path)
  # ---------------------------------------------------------------------------

  def test_dup_copies_comments
    src = "# leading\nx = 1;"
    body = ts_ast(src)
    stmt = body.stmts[0]
    assert_equal 1, stmt.leading_comments.length

    duped = stmt.dup
    assert_equal 1, duped.leading_comments.length
    refute_same stmt.leading_comments, duped.leading_comments, "dup should have independent comment array"
  end
end
