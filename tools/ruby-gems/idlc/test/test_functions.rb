# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require "minitest/autorun"

require "idlc"
require "idlc/passes/reachable_exceptions"
require "idlc/passes/reachable_functions"
require_relative "helpers"

$root ||= (Pathname.new(__FILE__) / ".." / ".." / ".." / "..").realpath

require_relative "helpers"

# test IDL Functions
class TestFunctions < Minitest::Test
  include TestMixin

  def test_that_reachable_raise_analysis_respects_transitive_known_values
    idl = <<~IDL.strip
      %version: 1.0
      enum Choice {
        A 0
        B 1
      }

      enum ExceptionCode {
        ACode 0
        BCode 1
      }

      builtin function raise {
        arguments ExceptionCode code
        description { raise an exception}
      }

      function nested_choose {
        arguments Choice choice
        description {
          Chooses A or B
        }
        body {
          if (choice == Choice::A) {
            raise(ExceptionCode::ACode);
          } else {
            raise(ExceptionCode::BCode);
          }
        }
      }

      function choose {
        arguments Choice choice
        description {
          Chooses A or B
        }
        body {
          nested_choose(choice);
        }
      }

      function test {
        description {
          run the test
        }
        body {
          choose(Choice::B);
        }
      }

    IDL

    t = Tempfile.new("idl")
    t.write idl
    t.close

    path = Pathname.new(t.path)

    ast = @compiler.compile_file(path)
    ast.add_global_symbols(@symtab)
    @symtab.deep_freeze
    ast.freeze_tree(@symtab)

    test_ast = ast.functions.find { |f| f.name == "test" }

    # should return (1 << BCode), also known as 2
    assert_equal (1 << 1), test_ast.body.prune(@symtab.deep_clone).reachable_exceptions(@symtab.deep_clone)
  end

  def test_that_reachable_raise_analysis_respects_known_paths_down_an_unknown_path
    idl = <<~IDL.strip
      %version: 1.0
      enum Choice {
        A 0
        B 1
      }

      enum ExceptionCode {
        ACode 0
        BCode 1
      }

      Bits<64> unknown;

      builtin function raise {
        arguments ExceptionCode code
        description { raise and exception}
      }

      function choose {
        arguments Choice choice
        description {
          Chooses A or B
        }
        body {
          if (unknown == 1) {
            if (choice == Choice::A) {
              raise(ExceptionCode::ACode);
            } else {
              raise(ExceptionCode::BCode);
            }
          }
        }
      }

      function test {
        description {
          run the test
        }
        body {
          choose(Choice::B);
        }
      }

    IDL

    t = Tempfile.new("idl")
    t.write idl
    t.close

    path = Pathname.new(t.path)

    ast = @compiler.compile_file(path)
    ast.add_global_symbols(@symtab)
    @symtab.deep_freeze
    ast.freeze_tree(@symtab)

    test_ast = ast.functions.find { |f| f.name == "test" }
    pruned_test_ast = test_ast.body.prune(@symtab.deep_clone)
    assert_equal (1 << 1), pruned_test_ast.reachable_exceptions(@symtab.deep_clone)
  end
end

# Helper to compile an IDL string and return a frozen (symtab, ast) pair.
# Used by TestReachableFunctions to avoid repeating boilerplate.
module IdlCompileHelper
  def compile_idl(idl_str)
    t = Tempfile.new("idl")
    t.write idl_str
    t.close
    path = Pathname.new(t.path)
    ast = @compiler.compile_file(path)
    ast.add_global_symbols(@symtab)
    @symtab.deep_freeze
    ast.freeze_tree(@symtab)
    ast
  end

  def reachable_names(func_name, ast, cache: {})
    fn_ast = ast.functions.find { |f| f.name == func_name }
    fn_ast.body.reachable_functions(@symtab.deep_clone, cache).map(&:name)
  end
end

# Tests for reachable_functions — behavioral contract, not implementation details.
class TestReachableFunctions < Minitest::Test
  include TestMixin
  include IdlCompileHelper

  # A calls B directly; B must appear in A's reachable set.
  def test_direct_call_returns_callee
    ast = compile_idl(<<~IDL)
      %version: 1.0
      function b {
        description { b }
        body { }
      }
      function a {
        description { calls b }
        body { b(); }
      }
    IDL

    assert_includes reachable_names("a", ast), "b"
  end

  # A→B→C→D: all three callees must appear in A's reachable set.
  def test_transitive_closure
    ast = compile_idl(<<~IDL)
      %version: 1.0
      function d {
        description { d }
        body { }
      }
      function c {
        description { c calls d }
        body { d(); }
      }
      function b {
        description { b calls c }
        body { c(); }
      }
      function a {
        description { a calls b }
        body { b(); }
      }
    IDL

    names = reachable_names("a", ast)
    assert_includes names, "b", "a should reach b"
    assert_includes names, "c", "a should reach c (transitive)"
    assert_includes names, "d", "a should reach d (transitive)"
  end

  # Diamond: A calls B and C; both B and C call D.
  # D must appear exactly once in A's reachable set.
  def test_diamond_no_duplicates
    ast = compile_idl(<<~IDL)
      %version: 1.0
      function d {
        description { d }
        body { }
      }
      function b {
        description { b calls d }
        body { d(); }
      }
      function c {
        description { c calls d }
        body { d(); }
      }
      function a {
        description { a calls b and c }
        body { b(); c(); }
      }
    IDL

    names = reachable_names("a", ast)
    assert_includes names, "b"
    assert_includes names, "c"
    assert_includes names, "d"
    assert_equal 1, names.count("d"), "d should appear exactly once"
  end

  # A calls B; C exists but is never called from A.
  # C must NOT appear in A's reachable set.
  def test_function_not_called_is_not_reachable
    ast = compile_idl(<<~IDL)
      %version: 1.0
      function b {
        description { b }
        body { }
      }
      function c {
        description { c is never called }
        body { }
      }
      function a {
        description { a calls only b }
        body { b(); }
      }
    IDL

    names = reachable_names("a", ast)
    assert_includes names, "b"
    refute_includes names, "c", "c is unreachable from a"
  end

  # A function with an empty body has no reachable functions.
  def test_empty_function_body_has_no_reachable_functions
    ast = compile_idl(<<~IDL)
      %version: 1.0
      function empty_fn {
        description { empty }
        body { }
      }
    IDL

    assert_empty reachable_names("empty_fn", ast),
                 "empty body should have no reachable functions"
  end

  # When a function is called with a known argument value, only the branch
  # that is actually taken should contribute reachable functions.
  def test_conditional_known_value_only_taken_branch
    ast = compile_idl(<<~IDL)
      %version: 1.0
      enum Branch {
        Left 0
        Right 1
      }
      function go_left {
        description { left }
        body { }
      }
      function go_right {
        description { right }
        body { }
      }
      function dispatcher {
        arguments Branch branch
        description { dispatches }
        body {
          if (branch == Branch::Left) {
            go_left();
          } else {
            go_right();
          }
        }
      }
      function entry {
        description { calls dispatcher with Left }
        body {
          dispatcher(Branch::Left);
        }
      }
    IDL

    names = reachable_names("entry", ast)
    assert_includes names, "dispatcher", "entry should reach dispatcher"
    assert_includes names, "go_left",    "entry should reach go_left (taken branch)"
    refute_includes names, "go_right",   "entry should NOT reach go_right (not-taken branch)"
  end

  # When a condition depends on an unknown runtime value, both branches
  # are conservatively considered reachable.
  def test_conditional_unknown_value_includes_both_branches
    ast = compile_idl(<<~IDL)
      %version: 1.0
      Bits<64> unknown_val;
      function go_left {
        description { left }
        body { }
      }
      function go_right {
        description { right }
        body { }
      }
      function dispatcher {
        description { dispatches on unknown }
        body {
          if (unknown_val == 1) {
            go_left();
          } else {
            go_right();
          }
        }
      }
    IDL

    names = reachable_names("dispatcher", ast)
    assert_includes names, "go_left",  "go_left is reachable (condition unknown)"
    assert_includes names, "go_right", "go_right is reachable (condition unknown)"
  end

  # A builtin function that is called must appear in the reachable set
  # (even though its body is not traversed).
  def test_builtin_function_included
    ast = compile_idl(<<~IDL)
      %version: 1.0
      builtin function my_builtin {
        description { a builtin }
      }
      function caller {
        description { calls my_builtin }
        body {
          my_builtin();
        }
      }
    IDL

    assert_includes reachable_names("caller", ast), "my_builtin",
                    "builtin functions should appear in the reachable set"
  end

  # Verify that when two callers share a cache and both call the same intermediate
  # function, the second caller still receives the complete transitive closure of
  # reachable functions (not just the direct callee).
  #
  # Call graph:
  #   caller1 -> middle -> leaf
  #   caller2 -> middle -> leaf
  def test_shared_cache_propagates_transitive_callees
    ast = compile_idl(<<~IDL)
      %version: 1.0
      function leaf {
        description { leaf function }
        body { }
      }
      function middle {
        description { calls leaf }
        body { leaf(); }
      }
      function caller1 {
        description { calls middle }
        body { middle(); }
      }
      function caller2 {
        description { also calls middle }
        body { middle(); }
      }
    IDL

    shared_cache = {}
    fn_names1 = reachable_names("caller1", ast, cache: shared_cache)
    fn_names2 = reachable_names("caller2", ast, cache: shared_cache)

    assert_includes fn_names1, "middle", "caller1 should reach middle"
    assert_includes fn_names1, "leaf",   "caller1 should reach leaf (transitive)"
    assert_includes fn_names2, "middle", "caller2 should reach middle"
    # Key assertion: with the old cache bug, caller2 returned only ["middle"],
    # silently dropping "leaf" because the cache hit skipped fns.concat.
    assert_includes fn_names2, "leaf",   "caller2 should reach leaf via shared cache (transitive)"
  end
end
