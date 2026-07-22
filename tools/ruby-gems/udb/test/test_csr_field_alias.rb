# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require_relative "test_helper"

require "udb/obj/csr_field"

class TestCsrFieldAlias < Minitest::Test
  StubField = Struct.new(:name, :location)

  class StubCsr
    def initialize(fields)
      @fields = fields
    end

    def field(name)
      @fields.fetch(name)
    end
  end

  class StubCfgArch
    def initialize(csrs)
      @csrs = csrs
    end

    def csr(name)
      @csrs[name]
    end
  end

  def build_field(alias_str, cfg_arch)
    field = Udb::CsrField.allocate
    field.instance_variable_set(:@data, { "alias" => alias_str })
    field.define_singleton_method(:cfg_arch) { cfg_arch }
    field
  end

  def cfg_arch_with(csr_name, field_name, location)
    target = StubField.new(field_name, location)
    StubCfgArch.new(csr_name => StubCsr.new(field_name => target))
  end

  def test_alias_without_range_uses_target_field_location
    cfg_arch = cfg_arch_with("sstatus", "SPP", (8..8))
    result = build_field("sstatus.SPP", cfg_arch).alias

    refute_nil result
    assert_equal "SPP", result.field.name
    assert_equal 8, result.range.begin
    assert_equal 8, result.range.end
  end

  def test_alias_single_bit_range
    cfg_arch = cfg_arch_with("mstatus", "SIE", (1..1))
    result = build_field("mstatus.SIE[1]", cfg_arch).alias

    assert_equal "SIE", result.field.name
    assert_equal 1, result.range.begin
    assert_equal 1, result.range.end
  end

  def test_alias_multi_bit_range_captures_csr_field_and_bounds
    cfg_arch = cfg_arch_with("mstatus", "MPP", (11..12))
    result = build_field("mstatus.MPP[12:11]", cfg_arch).alias

    assert_equal "MPP", result.field.name
    assert_equal 12, result.range.begin
    assert_equal 11, result.range.end
  end

  def test_alias_rejects_unparseable_string
    cfg_arch = cfg_arch_with("mstatus", "MPP", (11..12))
    assert_raises(RuntimeError) { build_field("not a valid alias", cfg_arch).alias }
  end
end
