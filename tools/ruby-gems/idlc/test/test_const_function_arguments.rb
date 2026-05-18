# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require "minitest/autorun"

require "idlc"
require_relative "helpers"

$root ||= (Pathname.new(__FILE__) / ".." / ".." / ".." / "..").realpath

# Test const function arguments
# Tests the rule: "Function arguments can be constant (by using a capitalized variable name).
# When constant, it is a type error to pass a mutable variable to the argument at the call site."
class TestConstFunctionArguments < Minitest::Test
  include TestMixin

  def test_const_argument_accepts_const_value
    # A function with a const argument (capitalized name) should accept const values
    idl = <<~IDL.strip
      %version: 1.0

      function test_func {
        arguments Bits<32> ConstArg
        description {
          Test function with const argument
        }
        body {
          Bits<32> result = ConstArg + 1;
        }
      }

      function caller {
        description {
          Call test_func with a const value
        }
        body {
          Bits<32> Const = 42;
          test_func(Const);
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

    # Should compile without errors
    refute_nil ast

    ast.type_check(@symtab, strict: false)
  end

  def test_const_argument_accepts_literal
    # A function with a const argument should accept literal values
    idl = <<~IDL.strip
      %version: 1.0

      function test_func {
        arguments Bits<32> ConstArg
        description {
          Test function with const argument
        }
        body {
          Bits<32> result = ConstArg + 1;
        }
      }

      function caller {
        description {
          Call test_func with a literal
        }
        body {
          test_func(42);
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

    # Should compile without errors
    refute_nil ast

    ast.type_check(@symtab, strict: false)
  end

  def test_const_argument_rejects_mutable_variables_with_known_values
    idl = <<~IDL.strip
      %version: 1.0

      function test_func {
        arguments Bits<32> ConstArg
        description {
          Test function with const argument
        }
        body {
          Bits<32> result = ConstArg + 1;
        }
      }

      function caller {
        description {
          Call test_func with a mutable variable
        }
        body {
          Bits<32> mutable_var = 42;
          test_func(mutable_var);
        }
      }
    IDL

    t = Tempfile.new("idl")
    t.write idl
    t.close

    path = Pathname.new(t.path)

    # Should not raise a type error
    ast = @compiler.compile_file(path)
    ast.add_global_symbols(@symtab)
    @symtab.deep_freeze
    ast.freeze_tree(@symtab)
    assert_raises Idl::AstNode::TypeError do
      ast.type_check(@symtab, strict: false)
    end
  end

    def test_const_argument_rejects_mutable_variables
    # A function with a const argument should reject mutable variables
    idl = <<~IDL.strip
      %version: 1.0

      function test_func {
        arguments Bits<32> ConstArg
        description {
          Test function with const argument
        }
        body {
          Bits<32> result = ConstArg + 1;
        }
      }

      function caller {
        description {
          Call test_func with a mutable variable
        }
        body {
          XReg mutable_var = X[1];
          test_func(mutable_var);
        }
      }
    IDL

    t = Tempfile.new("idl")
    t.write idl
    t.close

    path = Pathname.new(t.path)

    # Should not raise a type error
    ast = @compiler.compile_file(path)
    ast.add_global_symbols(@symtab)
    @symtab.deep_freeze
    ast.freeze_tree(@symtab)
    assert_raises Idl::AstNode::TypeError do
      ast.type_check(@symtab, strict: false)
    end
  end

  def test_mutable_argument_accepts_const_value
    # A function with a mutable argument (lowercase name) should accept const values
    idl = <<~IDL.strip
      %version: 1.0

      function test_func {
        arguments Bits<32> mutable_arg
        description {
          Test function with mutable argument
        }
        body {
          Bits<32> result = mutable_arg + 1;
        }
      }

      function caller {
        description {
          Call test_func with a const value
        }
        body {
          Bits<32> Const = 42;
          test_func(Const);
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

    # Should compile without errors
    refute_nil ast

    ast.type_check(@symtab, strict: false)
  end

  def test_mutable_argument_accepts_mutable_variable
    # A function with a mutable argument should accept mutable variables
    idl = <<~IDL.strip
      %version: 1.0

      function test_func {
        arguments Bits<32> mutable_arg
        description {
          Test function with mutable argument
        }
        body {
          Bits<32> result = mutable_arg + 1;
        }
      }

      function caller {
        description {
          Call test_func with a mutable variable
        }
        body {
          Bits<32> mutable_var = 42;
          test_func(mutable_var);
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

    # Should compile without errors
    refute_nil ast

    ast.type_check(@symtab, strict: false)
  end

  def test_multiple_const_arguments
    # Test function with multiple const arguments
    idl = <<~IDL.strip
      %version: 1.0

      function test_func {
        arguments Bits<32> ConstArg1, Bits<32> ConstArg2
        description {
          Test function with multiple const arguments
        }
        body {
          Bits<32> result = ConstArg1 + ConstArg2;
        }
      }

      function caller {
        description {
          Call test_func with const values
        }
        body {
          Bits<32> Const1 = 42;
          Bits<32> Const2 = 10;
          test_func(Const1, Const2);
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

    # Should compile without errors
    refute_nil ast

    ast.type_check(@symtab, strict: false)
  end

  def test_mixed_const_and_mutable_arguments
    # Test function with both const and mutable arguments
    idl = <<~IDL.strip
      %version: 1.0

      function test_func {
        arguments Bits<32> ConstArg, Bits<32> mutable_arg
        description {
          Test function with mixed argument types
        }
        body {
          Bits<32> result = ConstArg + mutable_arg;
        }
      }

      function caller {
        description {
          Call test_func with appropriate values
        }
        body {
          Bits<32> Const = 42;
          Bits<32> mutable_var = 10;
          test_func(Const, mutable_var);
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

    # Should compile without errors
    refute_nil ast

    ast.type_check(@symtab, strict: false)
  end

  def test_const_argument_with_expression
    # Test that const arguments can accept const expressions
    idl = <<~IDL.strip
      %version: 1.0

      function test_func {
        arguments Bits<32> ConstArg
        description {
          Test function with const argument
        }
        body {
          Bits<32> result = ConstArg + 1;
        }
      }

      function caller {
        description {
          Call test_func with a const expression
        }
        body {
          Bits<32> Const1 = 42;
          Bits<32> Const2 = 10;
          test_func(Const1 + Const2);
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

    # Should compile without errors
    refute_nil ast

    ast.type_check(@symtab, strict: false)
  end

  def test_const_argument_rejects_expression_with_mutable_but_known_value
    idl = <<~IDL.strip
      %version: 1.0

      function test_func {
        arguments Bits<32> ConstArg
        description {
          Test function with const argument
        }
        body {
          Bits<32> result = ConstArg + 1;
        }
      }

      function caller {
        description {
          Call test_func with expression containing mutable - should fail
        }
        body {
          Bits<32> Const = 42;
          Bits<32> mutable_var = 10;
          test_func(Const + mutable_var);
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
    assert_raises Idl::AstNode::TypeError do
      ast.type_check(@symtab, strict: false)
    end
  end
end
