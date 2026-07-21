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
end
