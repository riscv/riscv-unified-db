# frozen_string_literal: true

require_relative "test_helper"
require_relative "../../../backends/cpp_hart_gen/lib/gen_cpp"

class TestGenC < Minitest::Test
  def test_array_decl_gen_c
    idl = "U32 foo [ 32 ]"
    compiler = Idl::Compiler.new
    symtab = Idl::SymbolTable.new

    m = compiler.parser.parse(idl, root: :single_declaration)
    refute_nil m

    ast = m.to_ast
    assert_instance_of Idl::VariableDeclarationAst, ast

    # Verify that the C generation correctly formats the array size 
    # instead of crashing with "TODO"
    c_code = ast.gen_c(symtab)
    assert_equal "uint32_t foo[32]", c_code
  end

  def test_array_decl_gen_c_with_expression
    idl = "U32 bar [ VLEN ]"
    compiler = Idl::Compiler.new
    symtab = Idl::SymbolTable.new

    m = compiler.parser.parse(idl, root: :single_declaration)
    refute_nil m

    ast = m.to_ast
    
    # In C, it should fallback to the raw text_value because we can't emit C++ type wrappers
    c_code = ast.gen_c(symtab)
    assert_equal "uint32_t bar[VLEN]", c_code
  end
end
