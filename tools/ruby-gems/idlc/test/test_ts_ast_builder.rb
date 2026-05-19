# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require "minitest/autorun"
require "tree_sitter"
require_relative "../lib/idlc/ts_parser"
require_relative "../lib/idlc/ts_ast_builder"

class TestTsAstBuilder < Minitest::Test
  LABEL = "[TEST]"

  def ts_ast(source, root: :expression, starting_line: 0)
    parser = TreeSitter::Parser.new
    parser.language = Idl::TsParser.language
    tree = parser.parse_string(nil, source)
    ast = Idl::TsAstBuilder.new(source).build(tree.root_node)
    ast.set_input_file(LABEL, starting_line)
    ast
  end

  # ---------------------------------------------------------------------------
  # Literals
  # ---------------------------------------------------------------------------

  def test_true_literal
    assert_instance_of Idl::TrueExpressionAst, ts_ast("true")
  end

  def test_false_literal
    assert_instance_of Idl::FalseExpressionAst, ts_ast("false")
  end

  def test_int_literal_decimal
    assert_instance_of Idl::IntLiteralAst, ts_ast("42")
  end

  def test_int_literal_hex
    assert_instance_of Idl::IntLiteralAst, ts_ast("0xff")
  end

  def test_int_literal_verilog
    assert_instance_of Idl::IntLiteralAst, ts_ast("8'hAB")
  end

  def test_identifier
    assert_instance_of Idl::IdAst, ts_ast("xlen")
  end

  def test_binary_expression_add
    assert_instance_of Idl::BinaryExpressionAst, ts_ast("1 + 2")
  end

  def test_binary_expression_shift
    assert_instance_of Idl::BinaryExpressionAst, ts_ast("x >> 2")
  end

  def test_binary_expression_chained
    assert_instance_of Idl::BinaryExpressionAst, ts_ast("1 + 2 + 3")
  end

  def test_unary_expression
    assert_instance_of Idl::UnaryOperatorExpressionAst, ts_ast("~x")
  end

  def test_unary_negative
    assert_instance_of Idl::UnaryOperatorExpressionAst, ts_ast("-1")
  end

  def test_ternary_expression
    assert_instance_of Idl::TernaryOperatorExpressionAst, ts_ast("x ? 1 : 2")
  end

  def test_paren_expression
    assert_instance_of Idl::ParenExpressionAst, ts_ast("(1 + 2)")
  end

  # ---------------------------------------------------------------------------
  # Function bodies
  # ---------------------------------------------------------------------------

  def test_function_body_assignment
    ast = ts_ast("x = 1;", root: :function_body)
    assert_instance_of Idl::FunctionBodyAst, ast
    assert_equal 1, ast.stmts.length
  end

  def test_function_body_return
    ast = ts_ast("return x;", root: :function_body)
    assert_instance_of Idl::FunctionBodyAst, ast
    assert_instance_of Idl::ReturnStatementAst, ast.stmts.first
  end

  def test_function_body_multi_statement
    ast = ts_ast("x = 1;\nreturn x;", root: :function_body)
    assert_instance_of Idl::FunctionBodyAst, ast
    assert_equal 2, ast.stmts.length
  end

  # ---------------------------------------------------------------------------
  # Type names
  # ---------------------------------------------------------------------------

  def test_bits_type_name_in_decl
    ast = ts_ast("Bits<32> x;", root: :function_body)
    assert_instance_of Idl::FunctionBodyAst, ast
    stmt = ast.stmts.first
    decl = stmt.respond_to?(:action) ? stmt.action : stmt
    assert_instance_of Idl::VariableDeclarationAst, decl
  end

  def test_decl_with_initialization
    ast = ts_ast("Bits<32> x = 42;", root: :function_body)
    assert_instance_of Idl::FunctionBodyAst, ast
    stmt = ast.stmts.first
    decl = stmt.respond_to?(:action) ? stmt.action : stmt
    assert_instance_of Idl::VariableDeclarationWithInitializationAst, decl
  end

  # ---------------------------------------------------------------------------
  # Post-increment / decrement
  # ---------------------------------------------------------------------------

  def test_post_increment
    assert_instance_of Idl::PostIncrementExpressionAst, ts_ast("x++")
  end

  def test_post_decrement
    assert_instance_of Idl::PostDecrementExpressionAst, ts_ast("x--")
  end

  # ---------------------------------------------------------------------------
  # Array/subscript access
  # ---------------------------------------------------------------------------

  def test_element_access
    assert_instance_of Idl::AryElementAccessAst, ts_ast("arr[2]")
  end

  def test_range_access
    assert_instance_of Idl::AryRangeAccessAst, ts_ast("arr[3:0]")
  end

  # ---------------------------------------------------------------------------
  # Conditional statement / return
  # ---------------------------------------------------------------------------

  def test_conditional_statement
    ast = ts_ast("x = 1 if y > 0;", root: :function_body)
    assert_instance_of Idl::FunctionBodyAst, ast
    assert_instance_of Idl::ConditionalStatementAst, ast.stmts.first
  end

  def test_conditional_return
    ast = ts_ast("return x if y > 0;", root: :function_body)
    assert_instance_of Idl::FunctionBodyAst, ast
    assert_instance_of Idl::ConditionalReturnStatementAst, ast.stmts.first
  end

  # ---------------------------------------------------------------------------
  # If statements
  # ---------------------------------------------------------------------------

  def test_if_statement
    ast = ts_ast("if (x > 0) { y = 1; }", root: :function_body)
    assert_instance_of Idl::FunctionBodyAst, ast
    assert_instance_of Idl::IfAst, ast.stmts.first
  end

  def test_if_else_statement
    ast = ts_ast("if (x > 0) { y = 1; } else { y = 2; }", root: :function_body)
    assert_instance_of Idl::FunctionBodyAst, ast
    assert_instance_of Idl::IfAst, ast.stmts.first
  end

  # ---------------------------------------------------------------------------
  # For loop
  # ---------------------------------------------------------------------------

  def test_for_loop
    ast = ts_ast("for (Bits<5> i = 0; i < 8; i++) { x = x + 1; }", root: :function_body)
    assert_instance_of Idl::FunctionBodyAst, ast
    assert_instance_of Idl::ForLoopAst, ast.stmts.first
  end

  # ---------------------------------------------------------------------------
  # Compound expressions
  # ---------------------------------------------------------------------------

  def test_concatenation_expression
    assert_instance_of Idl::ConcatenationExpressionAst, ts_ast("{a, b, c}")
  end

  def test_replication_expression
    assert_instance_of Idl::ReplicationExpressionAst, ts_ast("{4{x}}")
  end

  def test_array_literal
    assert_instance_of Idl::ArrayLiteralAst, ts_ast("[1, 2, 3]")
  end

  def test_field_access_expression
    assert_instance_of Idl::FieldAccessExpressionAst, ts_ast("obj.field")
  end

  def test_enum_ref
    assert_instance_of Idl::EnumRefAst, ts_ast("MyEnum::VALUE")
  end

  def test_function_call_no_args
    assert_instance_of Idl::FunctionCallExpressionAst, ts_ast("foo()")
  end

  def test_function_call_with_args
    assert_instance_of Idl::FunctionCallExpressionAst, ts_ast("foo(1, 2)")
  end

  def test_builtin_variable
    assert_instance_of Idl::BuiltinVariableAst, ts_ast("$pc")
  end

  def test_dollar_signed_cast
    assert_instance_of Idl::SignCastAst, ts_ast("$signed(x)")
  end

  # ---------------------------------------------------------------------------
  # CSR access
  # ---------------------------------------------------------------------------

  def test_csr_field_read
    assert_instance_of Idl::CsrFieldReadExpressionAst, ts_ast("CSR[mstatus].MIE")
  end

  def test_csr_field_assignment
    ast = ts_ast("CSR[mstatus].MIE = 1;", root: :function_body)
    assert_instance_of Idl::FunctionBodyAst, ast
    stmt = ast.stmts.first
    action = stmt.respond_to?(:action) ? stmt.action : stmt
    assert_instance_of Idl::CsrFieldAssignmentAst, action
  end

  # ---------------------------------------------------------------------------
  # More assignments
  # ---------------------------------------------------------------------------

  def test_array_element_assignment
    ast = ts_ast("arr[0] = 1;", root: :function_body)
    assert_instance_of Idl::FunctionBodyAst, ast
    stmt = ast.stmts.first
    action = stmt.respond_to?(:action) ? stmt.action : stmt
    assert_instance_of Idl::AryElementAssignmentAst, action
  end

  def test_field_assignment
    ast = ts_ast("obj.f = 1;", root: :function_body)
    assert_instance_of Idl::FunctionBodyAst, ast
    stmt = ast.stmts.first
    action = stmt.respond_to?(:action) ? stmt.action : stmt
    assert_instance_of Idl::FieldAssignmentAst, action
  end

  def test_pc_assignment
    ast = ts_ast("$pc = 0x1000;", root: :function_body)
    assert_instance_of Idl::FunctionBodyAst, ast
    stmt = ast.stmts.first
    action = stmt.respond_to?(:action) ? stmt.action : stmt
    assert_instance_of Idl::PcAssignmentAst, action
  end

  def test_array_declaration
    ast = ts_ast("Bits<8> arr[4];", root: :function_body)
    assert_instance_of Idl::FunctionBodyAst, ast
    stmt = ast.stmts.first
    decl = stmt.respond_to?(:action) ? stmt.action : stmt
    assert_instance_of Idl::VariableDeclarationAst, decl
  end

  # ---------------------------------------------------------------------------
  # ISA file level
  # ---------------------------------------------------------------------------

  ISA_ENUM = <<~IDL
    %version: 1.0
    enum Color { Red Green Blue }
  IDL

  ISA_BITFIELD = <<~IDL
    %version: 1.0
    bitfield (32) Status { IE 0 MPIE 3 }
  IDL

  ISA_BITFIELD_RANGE = <<~IDL
    %version: 1.0
    bitfield (32) Status { FIELD 5-0 BIT 7 }
  IDL

  ISA_STRUCT = <<~IDL
    %version: 1.0
    struct Point { Bits<32> x; Bits<32> y; }
  IDL

  ISA_GLOBAL_CONST = <<~IDL
    %version: 1.0
    const Bits<32> MAX = 100;
  IDL

  ISA_GLOBAL_DECL = <<~IDL
    %version: 1.0
    Bits<32> counter;
  IDL

  ISA_FUNCTION = <<~IDL
    %version: 1.0
    function foo? {
      returns Boolean
      arguments Bits<32> x
      description { Returns true if positive. }
      body {
        return x > 0;
      }
    }
  IDL

  ISA_BUILTIN = <<~IDL
    %version: 1.0
    builtin function clz? {
      returns Bits<6>
      arguments Bits<32> x
      description { Count leading zeros. }
    }
  IDL

  ISA_MULTI_RETURN = <<~IDL
    %version: 1.0
    function foo {
      returns Bits<32>, Bits<32>
      description { Returns two values. }
      body {
        return 1;
      }
    }
  IDL

  def test_isa_enum
    ast = ts_ast(ISA_ENUM, root: :isa)
    assert_instance_of Idl::IsaAst, ast
    assert_instance_of Idl::EnumDefinitionAst, ast.definitions.first
  end

  def test_isa_bitfield_single_bits
    ast = ts_ast(ISA_BITFIELD, root: :isa)
    assert_instance_of Idl::IsaAst, ast
    assert_instance_of Idl::BitfieldDefinitionAst, ast.definitions.first
  end

  def test_isa_bitfield_range
    ast = ts_ast(ISA_BITFIELD_RANGE, root: :isa)
    assert_instance_of Idl::IsaAst, ast
    assert_instance_of Idl::BitfieldDefinitionAst, ast.definitions.first
  end

  def test_isa_struct
    ast = ts_ast(ISA_STRUCT, root: :isa)
    assert_instance_of Idl::IsaAst, ast
    assert_instance_of Idl::StructDefinitionAst, ast.definitions.first
  end

  def test_isa_global_const
    ast = ts_ast(ISA_GLOBAL_CONST, root: :isa)
    assert_instance_of Idl::IsaAst, ast
    assert_instance_of Idl::GlobalWithInitializationAst, ast.definitions.first
  end

  def test_isa_global_decl
    ast = ts_ast(ISA_GLOBAL_DECL, root: :isa)
    assert_instance_of Idl::IsaAst, ast
    assert_instance_of Idl::GlobalAst, ast.definitions.first
  end

  def test_isa_function
    ast = ts_ast(ISA_FUNCTION, root: :isa)
    assert_instance_of Idl::IsaAst, ast
    assert_instance_of Idl::FunctionDefAst, ast.definitions.first
  end

  def test_isa_builtin_function
    ast = ts_ast(ISA_BUILTIN, root: :isa)
    assert_instance_of Idl::IsaAst, ast
    assert_instance_of Idl::FunctionDefAst, ast.definitions.first
  end

  def test_isa_function_multi_return
    ast = ts_ast(ISA_MULTI_RETURN, root: :isa)
    assert_instance_of Idl::IsaAst, ast
    assert_instance_of Idl::FunctionDefAst, ast.definitions.first
  end

  # ---------------------------------------------------------------------------
  # Remaining expression / statement types
  # ---------------------------------------------------------------------------

  def test_string_literal
    assert_instance_of Idl::StringLiteralAst, ts_ast("\"hello\"")
  end

  def test_bits_dollar_cast
    assert_instance_of Idl::BitsCastAst, ts_ast("$bits(x)")
  end

  def test_csr_function_call_no_args
    ast = ts_ast("CSR[mstatus].mret();", root: :function_body)
    assert_instance_of Idl::FunctionBodyAst, ast
    stmt = ast.stmts.first
    action = stmt.respond_to?(:action) ? stmt.action : stmt
    assert_instance_of Idl::CsrFunctionCallAst, action
  end

  def test_csr_function_call_with_args
    ast = ts_ast("CSR[mstatus].foo(1, 2);", root: :function_body)
    assert_instance_of Idl::FunctionBodyAst, ast
    stmt = ast.stmts.first
    action = stmt.respond_to?(:action) ? stmt.action : stmt
    assert_instance_of Idl::CsrFunctionCallAst, action
  end

  def test_array_range_assignment
    ast = ts_ast("arr[3:0] = 1;", root: :function_body)
    assert_instance_of Idl::FunctionBodyAst, ast
    stmt = ast.stmts.first
    action = stmt.respond_to?(:action) ? stmt.action : stmt
    assert_instance_of Idl::AryRangeAssignmentAst, action
  end

  def test_widening_operator
    assert_instance_of Idl::BinaryExpressionAst, ts_ast("x " + "`+ y")
  end
end
