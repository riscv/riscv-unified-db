# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require "minitest/autorun"

require "idlc"
require_relative "helpers"

# Tests for Idl::Type#to_idl rendering.
class TestTypeToIdl < Minitest::Test
  def test_bits_to_idl_has_closing_angle_bracket
    assert_equal "Bits<32>", Idl::Type.new(:bits, width: 32).to_idl
  end

  def test_string_to_idl_returns_string_name
    assert_equal "String", Idl::Type.new(:string, width: 8).to_idl
  end

  def test_boolean_to_idl
    assert_equal "Boolean", Idl::Type.new(:boolean).to_idl
  end

  def test_void_to_idl
    assert_equal "void", Idl::Type.new(:void).to_idl
  end

  def test_array_to_idl_fixed_width
    sub = Idl::Type.new(:boolean)
    t = Idl::Type.new(:array, width: 32, sub_type: sub)
    assert_equal "Boolean[32]", t.to_idl
  end

  def test_array_to_idl_unknown_width
    sub = Idl::Type.new(:bits, width: 16)
    t = Idl::Type.new(:array, width: :unknown, sub_type: sub)
    assert_equal "array of Bits<16>", t.to_idl
  end

  def test_tuple_to_idl
    t1 = Idl::Type.new(:boolean)
    t2 = Idl::Type.new(:bits, width: 8)
    t = Idl::Type.new(:tuple, tuple_types: [t1, t2])
    assert_equal "(Boolean, Bits<8>)", t.to_idl
  end

  def test_struct_to_idl
    t = Idl::StructType.new("MyStruct", [Idl::Type.new(:boolean)], ["field1"])
    assert_equal "MyStruct", t.to_idl
  end

  def test_enum_to_idl
    t = Idl::Type.new(:enum, width: 2, name: "SatpMode")
    assert_equal "SatpMode", t.to_idl
  end

  def test_unknown_width_bits_raises
    t = Idl::Type.new(:bits, width: :unknown)
    assert_raises RuntimeError do
      t.to_idl
    end
  end
end
