# typed: false
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require_relative "test_helper"

require "ostruct"

module Udb
  class ConfiguredArchitecture
    def initialize(partially_configured)
      @partially_configured = partially_configured
    end

    def partially_configured?
      @partially_configured
    end
  end

  module SatisfiedResult
    Maybe = :maybe
    No = :no
  end
end

require_relative "../lib/udb/obj/csr"
require_relative "../lib/udb/obj/mmr"
require_relative "../lib/udb/obj/has_fields"

class TestCfgArchCache < Minitest::Test
  include Udb

  class FakeCondition
    def initialize(results_by_cfg)
      @results_by_cfg = results_by_cfg
    end

    def could_be_satisfied_by_cfg_arch?(cfg_arch)
      @results_by_cfg.fetch(cfg_arch)
    end

    def satisfied_by_cfg_arch?(cfg_arch)
      @results_by_cfg.fetch(cfg_arch)
    end

    def empty?
      false
    end
  end

  class OptionalProbe
    include Udb::HasFields

    def initialize(condition)
      @condition = condition
    end

    def defined_by_condition
      @condition
    end

    def exists_in_cfg?(_cfg_arch)
      true
    end
  end

  def make_cfg_arch(partially_configured: true)
    ConfiguredArchitecture.new(partially_configured)
  end

  def make_csr(condition)
    csr = Csr.allocate
    csr.define_singleton_method(:defined_by_condition) { condition }
    csr
  end

  def make_mmr(condition)
    mmr = Mmr.allocate
    mmr.define_singleton_method(:defined_by_condition) { condition }
    mmr
  end

  def test_csr_exists_in_cfg_is_keyed_by_cfg_arch
    cfg_true = make_cfg_arch
    cfg_false = make_cfg_arch
    csr = make_csr(FakeCondition.new(cfg_true => true, cfg_false => false))

    assert_equal true, csr.exists_in_cfg?(cfg_true)
    assert_equal false, csr.exists_in_cfg?(cfg_false)
    assert_equal true, csr.exists_in_cfg?(cfg_true)
  end

  def test_mmr_exists_in_cfg_is_keyed_by_cfg_arch
    cfg_true = make_cfg_arch
    cfg_false = make_cfg_arch
    mmr = make_mmr(FakeCondition.new(cfg_true => true, cfg_false => false))

    assert_equal true, mmr.exists_in_cfg?(cfg_true)
    assert_equal false, mmr.exists_in_cfg?(cfg_false)
    assert_equal true, mmr.exists_in_cfg?(cfg_true)
  end

  def test_optional_in_cfg_is_keyed_by_cfg_arch
    cfg_true = make_cfg_arch(partially_configured: true)
    cfg_false = make_cfg_arch(partially_configured: true)
    probe = OptionalProbe.new(FakeCondition.new(cfg_true => Udb::SatisfiedResult::Maybe, cfg_false => Udb::SatisfiedResult::No))

    assert_equal true, probe.optional_in_cfg?(cfg_true)
    assert_equal false, probe.optional_in_cfg?(cfg_false)
    assert_equal true, probe.optional_in_cfg?(cfg_true)
  end
end
