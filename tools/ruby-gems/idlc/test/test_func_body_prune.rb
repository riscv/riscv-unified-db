# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require "idlc"
require "idlc/passes/prune"
require_relative "helpers"
require "minitest/autorun"

# Compiles and prunes whole function bodies that mix control flow, arithmetic,
# bit operations, ternaries and register access, exercising the per-node prune
# and to_idl paths across many AST node types in one pass.
class TestFuncBodyPrune < Minitest::Test
  include TestMixin

  def prune_body(idl)
    ast = @compiler.compile_func_body(
      idl,
      return_type: Idl::Type.new(:bits, width: 32),
      symtab: @symtab,
      input_file: "temp",
      no_rescue: true
    )
    refute_nil ast
    pruned = ast.prune(@symtab)
    refute_nil pruned
    # to_idl of the pruned tree must be non-empty and reparse
    idl_out = pruned.to_idl
    refute_empty idl_out
    idl_out
  end

  def test_for_loop_if_else_ternary_concat
    idl = <<~IDL
      Bits<32> acc = 0;
      for (U32 i = 0; i < 4; i++) {
        acc = acc + i;
      }
      if (acc > 10) {
        acc = acc | 32'h1;
      } else {
        acc = ~acc;
      }
      Bits<32> sel = (acc > 10) ? acc : 32'd0;
      return {16'b0, sel[15:0]};
    IDL
    out = prune_body(idl)
    assert_includes out, "for"
    assert_includes out, "return"
  end

  def test_if_elsif_else_chain
    idl = <<~IDL
      Bits<32> a = 5;
      if (a == 1) {
        a = 32'h1;
      } else if (a == 5) {
        a = 32'h5;
      } else {
        a = 32'd0;
      }
      return a;
    IDL
    out = prune_body(idl)
    assert_includes out, "return"
  end

  def test_register_access_and_shift
    idl = <<~IDL
      Bits<32> v = X[1];
      v = v << 2;
      return v[31:0];
    IDL
    out = prune_body(idl)
    assert_includes out, "return"
  end

  def test_bitwise_identity_folding_in_body
    idl = <<~IDL
      Bits<32> x = X[2];
      Bits<32> y = x & 32'hffffffff;
      Bits<32> z = y | 32'h0;
      return z;
    IDL
    out = prune_body(idl)
    assert_includes out, "return"
  end

  def test_nested_for_loops
    idl = <<~IDL
      Bits<32> s = 0;
      for (U32 a = 0; a < 2; a++) {
        for (U32 b = 0; b < 2; b++) {
          s = s + 1;
        }
      }
      return s;
    IDL
    assert_includes prune_body(idl), "for"
  end

  def test_casts_modulo_and_arithmetic_shift
    idl = <<~IDL
      Bits<32> x = X[3];
      Bits<32> m = x % 7;
      Bits<32> n = $signed(x) >>> 1;
      return m + n;
    IDL
    assert_includes prune_body(idl), "return"
  end

  def test_boolean_short_circuit_operators
    idl = <<~IDL
      Boolean f = (X[1] > 0) && (X[2] < 100) || (X[3] == 0);
      return f ? 32'd1 : 32'd0;
    IDL
    assert_includes prune_body(idl), "return"
  end

  def test_replication_and_or
    idl = <<~IDL
      Bits<32> r = {32{1'b0}};
      return r | X[4];
    IDL
    assert_includes prune_body(idl), "return"
  end

  def test_bit_slice_assignment
    idl = <<~IDL
      Bits<32> v = X[1];
      v[7:0] = 8'hff;
      v[31:16] = 16'h0;
      return v;
    IDL
    assert_includes prune_body(idl), "return"
  end

  def test_register_element_assignment
    idl = <<~IDL
      Bits<32> v = X[1];
      X[2] = v + 1;
      return X[2];
    IDL
    assert_includes prune_body(idl), "return"
  end

  def test_unary_operators
    idl = <<~IDL
      Bits<32> v = X[3];
      Bits<32> a = -v;
      Boolean b = !(v == 0);
      return b ? a : ~v;
    IDL
    assert_includes prune_body(idl), "return"
  end

  def test_compound_arithmetic
    idl = <<~IDL
      Bits<32> v = X[1];
      v = v + 1;
      v = v - 2;
      v = v * 3;
      return v;
    IDL
    assert_includes prune_body(idl), "return"
  end

  def test_nested_ternary
    idl = <<~IDL
      Bits<32> v = X[1];
      return (v > 100) ? 32'd3 : (v > 10) ? 32'd2 : 32'd1;
    IDL
    assert_includes prune_body(idl), "return"
  end
end
