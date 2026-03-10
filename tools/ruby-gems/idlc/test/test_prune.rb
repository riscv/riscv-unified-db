# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require "idlc"
require "idlc/passes/prune"
require_relative "helpers"
require "minitest/autorun"

$root ||= (Pathname.new(__FILE__) / ".." / ".." / ".." / "..").realpath

require_relative "helpers"

# test IDL variables
class TestVariables < Minitest::Test
  include TestMixin

  def test_prune_csr_value
    orig_idl = <<~IDL
      if (CSR[mockcsr].ONE == 1) {
        return 1;
      }
    IDL
    expected_idl = <<~IDL
      return 1;
    IDL

    $mock_csr_field_class = Class.new do
      include Idl::CsrField
      def initialize(name, val, loc)
        @name = name
        @val = val
        @loc = loc
      end
      attr_reader :name
      def defined_in_all_bases? = true
      def defined_in_base32? = true
      def defined_in_base64? = true
      def base64_only? = false
      def base32_only? = false
      def location(_) = @loc
      def width(_) = 32
      def type(_) = @val.nil? ? "RW" : "RO"
      def exists? = true
      def reset_value = @val.nil? ? "UNDEFINED_LEGAL" : @val
    end
    mock_csr_class = Class.new do
      include Idl::Csr
      def name = "mockcsr"
      def max_length = 32
      def length(_) = 32
      def dynamic_length? = false
      def value = nil
      def fields = [
        $mock_csr_field_class.new("ONE", 1, 0..15),
        $mock_csr_field_class.new("UNKNOWN", nil, 16..31)
      ]
    end
    mock_csr_class2 = Class.new do
      include Idl::Csr
      def name = "mockcsr2"
      def max_length = 32
      def length(_) = 32
      def dynamic_length? = false
      def value = 1
      def fields = [
        $mock_csr_field_class.new("ONE", 1, 0..31)
      ]
    end
    symtab = Idl::SymbolTable.new(
      csrs: [mock_csr_class.new, mock_csr_class2.new],
      possible_xlens_cb: proc { [32, 64] }
    )
    ast =
      @compiler.compile_func_body(
        orig_idl,
        return_type: Idl::Type.new(:bits, width: 32),
        symtab:,
        input_file: "temp"
      )
    refute_nil(ast)
    pruned_ast = ast.prune(symtab)
    expected_ast =
      @compiler.compile_func_body(
        expected_idl,
        return_type: Idl::Type.new(:bits, width: 32),
        symtab:,
        input_file: "temp"
      )
    refute_nil(expected_ast)
    assert_equal expected_ast.to_idl, pruned_ast.to_idl

    orig_idl = <<~IDL
      if (CSR[mockcsr].UNKNOWN == 1) {
        return 1;
      }
    IDL
    expected_idl = <<~IDL
      if (CSR[mockcsr].UNKNOWN == 1) {
        return 1;
      }
    IDL
    ast =
          @compiler.compile_func_body(
            orig_idl,
            return_type: Idl::Type.new(:bits, width: 32),
            symtab:,
            input_file: "temp"
          )
    refute_nil(ast)
    pruned_ast = ast.prune(symtab)
    expected_ast =
      @compiler.compile_func_body(
        expected_idl,
        return_type: Idl::Type.new(:bits, width: 32),
        symtab:,
        input_file: "temp"
      )
    refute_nil(expected_ast)
    assert_equal expected_ast.to_idl, pruned_ast.to_idl

    orig_idl = <<~IDL
      CSR[mockcsr].UNKNOWN = CSR[mockcsr].ONE;
    IDL
    expected_idl = <<~IDL
      CSR[mockcsr].UNKNOWN = 1;
    IDL
    ast =
          @compiler.compile_func_body(
            orig_idl,
            return_type: Idl::Type.new(:bits, width: 32),
            symtab:,
            input_file: "temp"
          )
    refute_nil(ast)
    pruned_ast = ast.prune(symtab)
    expected_ast =
      @compiler.compile_func_body(
        expected_idl,
        return_type: Idl::Type.new(:bits, width: 32),
        symtab:,
        input_file: "temp"
      )
    refute_nil(expected_ast)
    assert_equal expected_ast.to_idl, pruned_ast.to_idl

    orig_idl = <<~IDL
      Bits<32> tmp = $bits(CSR[mockcsr]);
    IDL
    expected_idl = <<~IDL
      Bits<32> tmp = $bits(CSR[mockcsr]);
    IDL
    ast =
          @compiler.compile_func_body(
            orig_idl,
            return_type: Idl::Type.new(:bits, width: 32),
            symtab:,
            input_file: "temp"
          )
    refute_nil(ast)
    pruned_ast = ast.prune(symtab)
    expected_ast =
      @compiler.compile_func_body(
        expected_idl,
        return_type: Idl::Type.new(:bits, width: 32),
        symtab:,
        input_file: "temp"
      )
    refute_nil(expected_ast)
    assert_equal expected_ast.to_idl, pruned_ast.to_idl

    orig_idl = <<~IDL
      Bits<32> tmp = $bits(CSR[mockcsr2]);
    IDL
    expected_idl = <<~IDL
      Bits<32> tmp = 1;
    IDL
    ast =
          @compiler.compile_func_body(
            orig_idl,
            return_type: Idl::Type.new(:bits, width: 32),
            symtab:,
            input_file: "temp"
          )
    refute_nil(ast)
    ast.freeze_tree(symtab)
    pruned_ast = ast.prune(symtab)
    expected_ast =
      @compiler.compile_func_body(
        expected_idl,
        return_type: Idl::Type.new(:bits, width: 32),
        symtab:,
        input_file: "temp"
      )
    refute_nil(expected_ast)
    assert_equal expected_ast.to_idl, pruned_ast.to_idl
  end

  def test_if_body_does_not_leak_assignments
    # 'a' is assigned inside an if with unknown condition.
    # After the if, 'a' should be unknown, so 'result = a' must NOT be folded to a constant.
    orig_idl = <<~IDL
      Bits<32> a = 10;
      if (CSR[mockcsr].UNKNOWN == 1) {
        a = 0xdeadbeef;
      }
      Bits<32> result = a;
    IDL
    expected_idl = <<~IDL
      Bits<32> a = 10;
      if (CSR[mockcsr].UNKNOWN == 1) {
        a = 0xdeadbeef;
      }
      Bits<32> result = a;
    IDL

    $mock_csr_field_class2 = Class.new do
      include Idl::CsrField
      def initialize(name, val, loc)
        @name = name
        @val = val
        @loc = loc
      end
      attr_reader :name
      def defined_in_all_bases? = true
      def defined_in_base32? = true
      def defined_in_base64? = true
      def base64_only? = false
      def base32_only? = false
      def location(_) = @loc
      def width(_) = 32
      def type(_) = @val.nil? ? "RW" : "RO"
      def exists? = true
      def reset_value = @val.nil? ? "UNDEFINED_LEGAL" : @val
    end
    leak_csr_class = Class.new do
      include Idl::Csr
      def name = "mockcsr"
      def max_length = 32
      def length(_) = 32
      def dynamic_length? = false
      def value = nil
      def fields = [
        $mock_csr_field_class2.new("UNKNOWN", nil, 0..31)
      ]
    end
    symtab = Idl::SymbolTable.new(
      csrs: [leak_csr_class.new],
      possible_xlens_cb: proc { [32, 64] }
    )
    ast =
      @compiler.compile_func_body(
        orig_idl,
        return_type: Idl::Type.new(:bits, width: 32),
        symtab:,
        input_file: "temp"
      )
    refute_nil(ast)
    pruned_ast = ast.prune(symtab)
    expected_ast =
      @compiler.compile_func_body(
        expected_idl,
        return_type: Idl::Type.new(:bits, width: 32),
        symtab:,
        input_file: "temp"
      )
    refute_nil(expected_ast)
    assert_equal expected_ast.to_idl, pruned_ast.to_idl
  end

  # Helper to build a symtab with mockcsr having ONE (known=1) and UNKNOWN (unknown) fields
  def build_mock_symtab
    mock_field_class = Class.new do
      include Idl::CsrField
      def initialize(name, val, loc)
        @name = name
        @val = val
        @loc = loc
      end
      attr_reader :name
      def defined_in_all_bases? = true
      def defined_in_base32? = true
      def defined_in_base64? = true
      def base64_only? = false
      def base32_only? = false
      def location(_) = @loc
      def width(_) = 32
      def type(_) = @val.nil? ? "RW" : "RO"
      def exists? = true
      def reset_value = @val.nil? ? "UNDEFINED_LEGAL" : @val
    end
    $mock_field_class_for_prune = mock_field_class
    mock_csr = Class.new do
      include Idl::Csr
      def name = "mockcsr"
      def max_length = 32
      def length(_) = 32
      def dynamic_length? = false
      def value = nil
      def fields = [
        $mock_field_class_for_prune.new("ONE", 1, 0..15),
        $mock_field_class_for_prune.new("UNKNOWN", nil, 16..31)
      ]
    end
    Idl::SymbolTable.new(
      csrs: [mock_csr.new],
      possible_xlens_cb: proc { [32, 64] }
    )
  end

  def compile_and_prune(idl, symtab)
    ast = @compiler.compile_func_body(
      idl,
      return_type: Idl::Type.new(:bits, width: 32),
      symtab:,
      input_file: "temp"
    )
    refute_nil(ast)
    ast.prune(symtab)
  end

  def test_conditional_statement_does_not_leak_assignment
    # a = 0xdeadbeef if (CSR[mockcsr].UNKNOWN == 1);
    # After pruning, 'a' should be unknown (nil), not 0xdeadbeef
    orig_idl = <<~IDL
      Bits<32> a = 10;
      a = 0xdeadbeef if (CSR[mockcsr].UNKNOWN == 1);
      Bits<32> result = a;
    IDL
    expected_idl = <<~IDL
      Bits<32> a = 10;
      a = 0xdeadbeef if (CSR[mockcsr].UNKNOWN == 1);
      Bits<32> result = a;
    IDL
    symtab = build_mock_symtab
    pruned_ast = compile_and_prune(orig_idl, symtab)
    expected_ast = @compiler.compile_func_body(
      expected_idl,
      return_type: Idl::Type.new(:bits, width: 32),
      symtab:,
      input_file: "temp"
    )
    refute_nil(expected_ast)
    assert_equal expected_ast.to_idl, pruned_ast.to_idl
  end

  def test_for_loop_does_not_leak_assignments
    # 'a' is assigned inside a for loop body.
    # After the loop, 'a' should be unknown (nil).
    orig_idl = <<~IDL
      Bits<32> a = 10;
      for (Bits<8> i = 0; i < 4; i++) {
        a = i;
      }
      Bits<32> result = a;
    IDL
    expected_idl = <<~IDL
      Bits<32> a = 10;
      for (Bits<8> i = 0; i < 4; i++) {
        a = i;
      }
      Bits<32> result = a;
    IDL
    symtab = build_mock_symtab
    pruned_ast = compile_and_prune(orig_idl, symtab)
    expected_ast = @compiler.compile_func_body(
      expected_idl,
      return_type: Idl::Type.new(:bits, width: 32),
      symtab:,
      input_file: "temp"
    )
    refute_nil(expected_ast)
    assert_equal expected_ast.to_idl, pruned_ast.to_idl
  end

  def test_ary_range_assignment_does_not_leak
    # vec[7:0] = 0xff inside unknown if; after if, vec should be unknown
    orig_idl = <<~IDL
      Bits<32> vec = 0;
      if (CSR[mockcsr].UNKNOWN == 1) {
        vec[7:0] = 0xff;
      }
      Bits<32> result = vec;
    IDL
    expected_idl = <<~IDL
      Bits<32> vec = 0;
      if (CSR[mockcsr].UNKNOWN == 1) {
        vec[7:0] = 0xff;
      }
      Bits<32> result = vec;
    IDL
    symtab = build_mock_symtab
    pruned_ast = compile_and_prune(orig_idl, symtab)
    expected_ast = @compiler.compile_func_body(
      expected_idl,
      return_type: Idl::Type.new(:bits, width: 32),
      symtab:,
      input_file: "temp"
    )
    refute_nil(expected_ast)
    assert_equal expected_ast.to_idl, pruned_ast.to_idl
  end

  def test_ary_range_assignment_execute_updates_value
    # vec[7:0] = 0xab with known condition (ONE == 1); result should fold to the updated value.
    # Uses vec + 0 to force folding of the variable reference.
    orig_idl = <<~IDL
      Bits<32> vec = 0x12340000;
      if (CSR[mockcsr].ONE == 1) {
        vec[7:0] = 0xab;
      }
      Bits<32> result = vec + 0;
    IDL
    expected_idl = <<~IDL
      Bits<32> vec = 0x12340000;
      vec[7:0] = 0xab;
      Bits<32> result = 0x123400ab;
    IDL
    symtab = build_mock_symtab
    pruned_ast = compile_and_prune(orig_idl, symtab)
    expected_ast = @compiler.compile_func_body(
      expected_idl,
      return_type: Idl::Type.new(:bits, width: 32),
      symtab:,
      input_file: "temp"
    )
    refute_nil(expected_ast)
    assert_equal expected_ast.to_idl, pruned_ast.to_idl
  end
end
