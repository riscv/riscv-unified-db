# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require "idlc"
require "idlc/ast"
require "minitest/autorun"
require_relative "helpers"

class TestTypeEquality < Minitest::Test
  def test_void_equality
    t1 = Idl::Type.new(:void)
    t2 = Idl::Type.new(:void)
    assert_equal t1, t2
  end

  def test_boolean_equality
    t1 = Idl::Type.new(:boolean)
    t2 = Idl::Type.new(:boolean)
    assert_equal t1, t2
  end

  def test_bits_equality
    t1 = Idl::Type.new(:bits, width: 32)
    t2 = Idl::Type.new(:bits, width: 32)
    t3 = Idl::Type.new(:bits, width: 64)
    assert_equal t1, t2
    refute_equal t1, t3
  end

  def test_array_equality
    bits32 = Idl::Type.new(:bits, width: 32)
    bits64 = Idl::Type.new(:bits, width: 64)

    t1 = Idl::Type.new(:array, width: 4, sub_type: bits32)
    t2 = Idl::Type.new(:array, width: 4, sub_type: bits32)
    t3 = Idl::Type.new(:array, width: 8, sub_type: bits32)
    t4 = Idl::Type.new(:array, width: 4, sub_type: bits64)

    assert_equal t1, t2
    refute_equal t1, t3
    refute_equal t1, t4
  end

  def test_struct_equality
    t1 = Idl::StructType.new("MyStruct", [], [])
    t2 = Idl::StructType.new("MyStruct", [], [])
    t3 = Idl::StructType.new("OtherStruct", [], [])

    assert_equal t1, t2
    refute_equal t1, t3
  end

  def test_tuple_equality
    bits32 = Idl::Type.new(:bits, width: 32)
    bits64 = Idl::Type.new(:bits, width: 64)

    t1 = Idl::Type.new(:tuple, tuple_types: [bits32, bits64])
    t2 = Idl::Type.new(:tuple, tuple_types: [bits32, bits64])
    t3 = Idl::Type.new(:tuple, tuple_types: [bits64, bits32])

    assert_equal t1, t2
    refute_equal t1, t3
  end
  def test_cross_kind_inequality
    t_void = Idl::Type.new(:void)
    t_bool = Idl::Type.new(:boolean)
    t_bits = Idl::Type.new(:bits, width: 32)

    refute_equal t_void, t_bool
    refute_equal t_bool, t_bits
  end
end
