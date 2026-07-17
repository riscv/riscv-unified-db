# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require "idlc"
require "minitest/autorun"

# Exercises Idl::Type utility methods (to_s and convertable_to?) across kinds.
class TestType < Minitest::Test
  Ty = Idl::Type

  def bits(w) = Ty.new(:bits, width: w)

  # --- to_s ------------------------------------------------------------------

  def test_to_s_bits
    assert_equal "Bits<8>", bits(8).to_s
  end

  def test_to_s_boolean
    assert_equal "Boolean", Ty.new(:boolean).to_s
  end

  def test_to_s_void
    assert_equal "void", Ty.new(:void).to_s
  end

  def test_to_s_string
    assert_equal "string", Ty.new(:string, width: 4).to_s
  end

  def test_to_s_array
    assert_equal "array of Bits<8>", Ty.new(:array, width: 4, sub_type: bits(8)).to_s
  end

  def test_to_s_tuple
    assert_equal "(Bits<8>,Boolean)",
                 Ty.new(:tuple, tuple_types: [bits(8), Ty.new(:boolean)]).to_s
  end

  def test_to_s_bitfield
    assert_equal "bitfield Foo", Ty.new(:bitfield, name: "Foo", width: 32).to_s
  end

  def test_to_s_with_qualifier
    t = bits(8).make_const
    assert_includes t.to_s, "Bits<8>"
    assert_includes t.to_s, "const"
  end

  # --- convertable_to? -------------------------------------------------------

  def test_void_convertable_to_void
    assert Ty.new(:void).convertable_to?(Ty.new(:void))
  end

  def test_string_convertable_to_string
    assert Ty.new(:string, width: 4).convertable_to?(Ty.new(:string, width: 8))
  end

  def test_string_not_convertable_to_bits
    refute Ty.new(:string, width: 4).convertable_to?(bits(8))
  end

  def test_tuple_same_shape_convertable
    a = Ty.new(:tuple, tuple_types: [bits(8), Ty.new(:boolean)])
    b = Ty.new(:tuple, tuple_types: [bits(8), Ty.new(:boolean)])
    assert a.convertable_to?(b)
  end

  def test_tuple_different_size_not_convertable
    a = Ty.new(:tuple, tuple_types: [bits(8), Ty.new(:boolean)])
    b = Ty.new(:tuple, tuple_types: [bits(8)])
    refute a.convertable_to?(b)
  end

  def test_array_same_shape_convertable
    a = Ty.new(:array, width: 4, sub_type: bits(8))
    b = Ty.new(:array, width: 4, sub_type: bits(8))
    assert a.convertable_to?(b)
  end

  def test_array_different_width_not_convertable
    a = Ty.new(:array, width: 4, sub_type: bits(8))
    b = Ty.new(:array, width: 8, sub_type: bits(8))
    refute a.convertable_to?(b)
  end
end
