# Copyright (c) AINEKKO.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require_relative "test_helper"

require "json"
require "json_schemer"
require "yaml"

class TestMmrSchema < Minitest::Test
  SCHEMA_DIR = (Pathname.new(__dir__) / ".." / ".." / ".." / ".." / "spec" / "schemas").realpath
  SCHEMA_PATH = SCHEMA_DIR / "mmr_schema.json"

  def setup
    schema_json = JSON.parse(File.read(SCHEMA_PATH))
    @schemer = JSONSchemer.schema(
      schema_json,
      ref_resolver: proc { |uri|
        path = SCHEMA_DIR / File.basename(uri.path)
        data = JSON.parse(File.read(path))
        # json_schemer 2.x enforces Draft-07 strictly: $defs is not recognised
        # (Draft-07 uses "definitions"). Copy $defs so both keywords work.
        data["definitions"] = data["$defs"] if data["$defs"] && !data.key?("definitions")
        data
      }
    )
  end

  # ── helpers ──

  def valid_mmr
    {
      "$schema" => "mmr_schema.json#",
      "kind" => "mmr",
      "name" => "example_reg0",
      "long_name" => "Example Register 0",
      "length" => 32,
      "description" => "A simple test register for unit testing.",
      "writable" => true,
      "physical_address" => 0x1000,
      "definedBy" => { "extension" => { "name" => "Xexample" } }
    }
  end

  def assert_valid(data, msg = nil)
    errors = @schemer.validate(data).to_a
    assert errors.empty?, "Expected VALID but got errors#{msg ? " (#{msg})" : ""}:\n#{errors.map { |e| "  #{e["data_pointer"]}: #{e["type"]}" }.join("\n")}"
  end

  def assert_invalid(data, msg = nil)
    errors = @schemer.validate(data).to_a
    refute errors.empty?, "Expected INVALID but schema passed#{msg ? " (#{msg})" : ""}"
  end

  # ════════════════════════════════════════════════════════════════════
  # TESTS THAT SHOULD PASS (valid MMR definitions)
  # ════════════════════════════════════════════════════════════════════

  # SHOULD PASS: minimal valid MMR with all required fields
  def test_valid_minimal_mmr
    assert_valid(valid_mmr, "minimal valid MMR with all required fields")
  end

  # SHOULD PASS: valid MMR with 64-bit length
  def test_valid_mmr_64bit
    data = valid_mmr.merge("length" => 64)
    assert_valid(data, "64-bit MMR")
  end

  # SHOULD PASS: valid read-only MMR
  def test_valid_readonly_mmr
    data = valid_mmr.merge("writable" => false)
    assert_valid(data, "read-only MMR")
  end

  # SHOULD PASS: valid MMR with fields
  def test_valid_mmr_with_fields
    data = valid_mmr.merge(
      "fields" => {
        "EN" => {
          "location" => 0,
          "description" => "Enable bit",
          "type" => "RW",
          "reset_value" => 0
        }
      }
    )
    assert_valid(data, "MMR with fields")
  end

  # SHOULD PASS: valid MMR with zero physical address
  def test_valid_mmr_zero_address
    data = valid_mmr.merge("physical_address" => 0)
    assert_valid(data, "MMR with physical_address 0")
  end

  # SHOULD PASS: valid MMR with large physical address
  def test_valid_mmr_large_address
    data = valid_mmr.merge("physical_address" => 0xFFFF_FFFF)
    assert_valid(data, "MMR with large physical_address")
  end

  # SHOULD PASS: valid MMR with definedBy as allOf-style
  def test_valid_mmr_defined_by_complex
    data = valid_mmr.merge(
      "definedBy" => {
        "allOf" => [
          { "extension" => { "name" => "Xext1" } },
          { "extension" => { "name" => "Xext2" } }
        ]
      }
    )
    assert_valid(data, "MMR with complex definedBy")
  end

  # ════════════════════════════════════════════════════════════════════
  # TESTS THAT SHOULD FAIL (invalid MMR definitions)
  # ════════════════════════════════════════════════════════════════════

  # SHOULD FAIL: missing $schema
  def test_invalid_missing_schema
    data = valid_mmr.tap { |d| d.delete("$schema") }
    assert_invalid(data, "missing $schema")
  end

  # SHOULD FAIL: missing kind
  def test_invalid_missing_kind
    data = valid_mmr.tap { |d| d.delete("kind") }
    assert_invalid(data, "missing kind")
  end

  # SHOULD FAIL: wrong kind value
  def test_invalid_wrong_kind
    data = valid_mmr.merge("kind" => "csr")
    assert_invalid(data, "kind is 'csr' instead of 'mmr'")
  end

  # SHOULD FAIL: missing name
  def test_invalid_missing_name
    data = valid_mmr.tap { |d| d.delete("name") }
    assert_invalid(data, "missing name")
  end

  # SHOULD FAIL: name with uppercase letters (must match ^[a-z][a-z0-9_.]+$)
  def test_invalid_name_uppercase
    data = valid_mmr.merge("name" => "MyRegister")
    assert_invalid(data, "name with uppercase")
  end

  # SHOULD FAIL: name starting with digit
  def test_invalid_name_starts_with_digit
    data = valid_mmr.merge("name" => "0reg")
    assert_invalid(data, "name starting with digit")
  end

  # SHOULD FAIL: single-char name (pattern requires 2+ chars)
  def test_invalid_name_single_char
    data = valid_mmr.merge("name" => "x")
    assert_invalid(data, "single character name")
  end

  # SHOULD FAIL: missing long_name
  def test_invalid_missing_long_name
    data = valid_mmr.tap { |d| d.delete("long_name") }
    assert_invalid(data, "missing long_name")
  end

  # SHOULD FAIL: missing length
  def test_invalid_missing_length
    data = valid_mmr.tap { |d| d.delete("length") }
    assert_invalid(data, "missing length")
  end

  # SHOULD PASS: valid MMR with 8-bit length
  def test_valid_mmr_8bit
    data = valid_mmr.merge("length" => 8)
    assert_valid(data, "8-bit MMR")
  end

  # SHOULD PASS: valid MMR with 16-bit length
  def test_valid_mmr_16bit
    data = valid_mmr.merge("length" => 16)
    assert_valid(data, "16-bit MMR")
  end

  # SHOULD PASS: valid MMR with 128-bit length
  def test_valid_mmr_128bit
    data = valid_mmr.merge("length" => 128)
    assert_valid(data, "128-bit MMR")
  end

  # SHOULD FAIL: length is 256 (must be 8, 16, 32, 64, or 128)
  def test_invalid_length_256
    data = valid_mmr.merge("length" => 256)
    assert_invalid(data, "length is 256")
  end

  # SHOULD FAIL: length is a string
  def test_invalid_length_string
    data = valid_mmr.merge("length" => "MXLEN")
    assert_invalid(data, "length is string 'MXLEN', MMRs must be a fixed integer")
  end

  # SHOULD FAIL: missing description
  def test_invalid_missing_description
    data = valid_mmr.tap { |d| d.delete("description") }
    assert_invalid(data, "missing description")
  end

  # SHOULD FAIL: missing writable
  def test_invalid_missing_writable
    data = valid_mmr.tap { |d| d.delete("writable") }
    assert_invalid(data, "missing writable")
  end

  # SHOULD FAIL: writable is a string instead of boolean
  def test_invalid_writable_string
    data = valid_mmr.merge("writable" => "yes")
    assert_invalid(data, "writable is string instead of boolean")
  end

  # SHOULD FAIL: missing physical_address
  def test_invalid_missing_physical_address
    data = valid_mmr.tap { |d| d.delete("physical_address") }
    assert_invalid(data, "missing physical_address")
  end

  # SHOULD FAIL: negative physical_address
  def test_invalid_negative_physical_address
    data = valid_mmr.merge("physical_address" => -1)
    assert_invalid(data, "negative physical_address")
  end

  # SHOULD FAIL: physical_address is string
  def test_invalid_physical_address_string
    data = valid_mmr.merge("physical_address" => "0x1000")
    assert_invalid(data, "physical_address is string instead of integer")
  end

  # SHOULD FAIL: missing definedBy
  def test_invalid_missing_defined_by
    data = valid_mmr.tap { |d| d.delete("definedBy") }
    assert_invalid(data, "missing definedBy")
  end

  # SHOULD FAIL: wrong $schema value
  def test_invalid_wrong_schema_value
    data = valid_mmr.merge("$schema" => "csr_schema.json#")
    assert_invalid(data, "wrong $schema reference")
  end

  # SHOULD FAIL: additional unknown property
  def test_invalid_additional_property
    data = valid_mmr.merge("unknown_field" => "surprise")
    assert_invalid(data, "unknown additional property")
  end
end
