# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require "idlc"
require "minitest/autorun"

# Exercises Idl::Type.from_json_schema (and, through it, the scalar and array
# schema-to-Type conversion helpers).
class TestTypeFromJsonSchema < Minitest::Test
  def conv(schema) = Idl::Type.from_json_schema(schema)

  # --- scalar: type keyword --------------------------------------------------

  def test_integer_default_width_is_128
    t = conv("type" => "integer")
    assert_equal :bits, t.kind
    assert_equal 128, t.width
  end

  def test_integer_with_maximum
    t = conv("type" => "integer", "maximum" => 255)
    assert_equal :bits, t.kind
    assert_equal 8, t.width
  end

  def test_integer_with_enum
    t = conv("type" => "integer", "enum" => [1, 2, 8])
    assert_equal :bits, t.kind
    assert_equal 4, t.width
  end

  def test_string_default_width
    t = conv("type" => "string")
    assert_equal :string, t.kind
    assert_equal 4096, t.width
  end

  def test_string_with_enum_uses_longest
    t = conv("type" => "string", "enum" => ["ab", "cdef"])
    assert_equal :string, t.kind
    assert_equal 4, t.width
  end

  def test_unhandled_type_raises
    assert_raises(RuntimeError) { conv("type" => "number") }
  end

  # --- scalar: const ---------------------------------------------------------

  def test_const_integer
    t = conv("const" => 5)
    assert_equal :bits, t.kind
    assert_equal 3, t.width
  end

  def test_const_string
    t = conv("const" => "hello")
    assert_equal :string, t.kind
    assert_equal 5, t.width
  end

  def test_const_float_raises
    assert_raises(RuntimeError) { conv("const" => 1.5) }
  end

  # --- scalar: enum ----------------------------------------------------------

  def test_enum_integers
    t = conv("enum" => [1, 2, 255])
    assert_equal :bits, t.kind
    assert_equal 8, t.width
  end

  def test_enum_strings
    t = conv("enum" => ["a", "bb"])
    assert_equal :string, t.kind
    assert_equal 2, t.width
  end

  def test_enum_mixed_types_raises
    assert_raises(RuntimeError) { conv("enum" => [1, "a"]) }
  end

  def test_enum_unhandled_element_type_raises
    assert_raises(RuntimeError) { conv("enum" => [[1], [2]]) }
  end

  # --- scalar: allOf ---------------------------------------------------------

  def test_allof_integers_takes_widest
    t = conv("allOf" => [
      { "type" => "integer", "maximum" => 15 },
      { "type" => "integer", "maximum" => 255 }
    ])
    assert_equal :bits, t.kind
    assert_equal 8, t.width
  end

  def test_allof_strings
    t = conv("allOf" => [{ "type" => "string" }, { "type" => "string" }])
    assert_equal :string, t.kind
  end

  def test_allof_disagreeing_types_raises
    assert_raises(RuntimeError) do
      conv("allOf" => [{ "type" => "string" }, { "type" => "integer" }])
    end
  end

  # --- scalar: $ref ----------------------------------------------------------

  def test_ref_uint32
    t = conv("$ref" => "schema_defs.json#/$defs/uint32")
    assert_equal :bits, t.kind
    assert_equal 32, t.width
  end

  def test_ref_uint64
    t = conv("$ref" => "schema_defs.json#/$defs/uint64")
    assert_equal :bits, t.kind
    assert_equal 64, t.width
  end

  def test_ref_unknown_raises
    assert_raises(RuntimeError) { conv("$ref" => "schema_defs.json#/$defs/other") }
  end

  # --- scalar: not / unhandled ----------------------------------------------

  def test_not_schema_is_nil
    assert_nil conv("not" => { "type" => "string" })
  end

  def test_unhandled_scalar_schema_raises
    assert_raises(RuntimeError) { conv({}) }
  end

  # --- array -----------------------------------------------------------------

  def test_array_fixed_size_known_width
    t = conv("type" => "array",
             "items" => { "type" => "integer", "maximum" => 255 },
             "minItems" => 4, "maxItems" => 4)
    assert_equal :array, t.kind
    assert_equal 4, t.width
    assert_equal :bits, t.sub_type.kind
  end

  def test_array_without_bounds_is_unknown_width
    t = conv("type" => "array", "items" => { "type" => "boolean" })
    assert_equal :array, t.kind
    assert_equal :unknown, t.width
  end

  def test_array_per_element_items
    t = conv("type" => "array",
             "items" => [
               { "type" => "integer", "maximum" => 255 },
               { "type" => "integer", "maximum" => 255 }
             ])
    assert_equal :array, t.kind
    assert_equal :bits, t.sub_type.kind
  end

  def test_array_mismatched_elements_raises
    assert_raises(RuntimeError) do
      conv("type" => "array",
           "items" => [{ "type" => "integer", "maximum" => 255 }, { "type" => "string" }])
    end
  end

  # --- from_json_schema dispatch --------------------------------------------

  def test_dispatch_unexpected_type_raises
    assert_raises(RuntimeError) { conv("type" => "object") }
  end

  def test_boolean_type
    assert_equal :boolean, conv("type" => "boolean").kind
  end

  def test_const_boolean
    assert_equal :boolean, conv("const" => true).kind
  end
end
