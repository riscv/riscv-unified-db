# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require_relative "test_helper"

require "ostruct"
require "concurrent"
require "sorbet-runtime"
require "udb/obj/csr"
require "udb/cfg_arch"

# Tests for Csr#dynamic_length? in the "XLEN" case.
#
# An XLEN-length CSR is dynamic when ANY of the following independently holds:
#   - MXLEN is unknown, OR
#   - S-mode is possible and SXLEN is unknown/mutable, OR
#   - H-mode is possible and VSXLEN is unknown/mutable.
# i.e. the intent is a disjunction of three independent terms (A || B || C), as
# documented by the method's own comments and mirrored by the sibling
# "SXLEN" / "VSXLEN" branches (each of which independently signals dynamic).
class TestCsr < Minitest::Test
  include Udb

  # Build a genuine ConfiguredArchitecture (so Sorbet sig checks pass) with just
  # enough state injected to exercise Csr#dynamic_length?. Mirrors the approach in
  # test_register_file_obj.rb (allocate + define_singleton_method).
  def make_cfg_arch(mxlen:, exts:, param_values:)
    arch = Udb::ConfiguredArchitecture.allocate
    arch.instance_variable_set(:@objects, Concurrent::Hash.new)
    arch.instance_variable_set(:@object_hashes, Concurrent::Hash.new)
    ext_objs = exts.map { |name| OpenStruct.new(name: name) }
    arch.define_singleton_method(:mxlen) { mxlen }
    arch.define_singleton_method(:possible_extensions) { ext_objs }
    arch.define_singleton_method(:param_values) { param_values }
    arch
  end

  # Build a real Csr with the given length. base is seeded to nil (CSR defined in
  # all bases) so dynamic_length? reaches the length-based branches without invoking
  # the SAT/logic-tree machinery, which would require the full architecture database.
  def make_csr(arch, length:)
    data = {
      "$schema" => "csr_schema.json#",
      "kind" => "csr",
      "name" => "xtest",
      "long_name" => "Test CSR",
      "length" => length,
      "description" => "A test CSR."
    }
    csr = Csr.new(data, Pathname.new("/mock/csr/xtest.yaml"), arch)
    csr.instance_variable_set(:@base, nil)
    csr
  end

  # M + S, MXLEN known, SXLEN mutable, NO H extension.
  # S-mode alone makes the effective XLEN variable, so the CSR IS dynamic.
  # (Regression pin: the buggy `A || B && C` precedence returns false here.)
  def test_xlen_dynamic_when_only_sxlen_mutable
    arch = make_cfg_arch(mxlen: 32, exts: %w[A S], param_values: { "SXLEN" => [32, 64] })
    csr = make_csr(arch, length: "XLEN")
    assert csr.dynamic_length?,
      "XLEN CSR must be dynamic when S-mode is possible and SXLEN is mutable, even without H"
  end

  # M + H, MXLEN known, VSXLEN mutable, NO S extension.
  # H-mode alone makes the effective XLEN variable, so the CSR IS dynamic.
  def test_xlen_dynamic_when_only_vsxlen_mutable
    arch = make_cfg_arch(mxlen: 32, exts: %w[A H], param_values: { "VSXLEN" => [32, 64] })
    csr = make_csr(arch, length: "XLEN")
    assert csr.dynamic_length?,
      "XLEN CSR must be dynamic when H-mode is possible and VSXLEN is mutable, even without S"
  end

  # Both S and H conditions dynamic -> still dynamic (already true before the fix).
  def test_xlen_dynamic_when_both_conditions_hold
    arch = make_cfg_arch(
      mxlen: 32, exts: %w[A S H],
      param_values: { "SXLEN" => [32, 64], "VSXLEN" => [32, 64] }
    )
    csr = make_csr(arch, length: "XLEN")
    assert csr.dynamic_length?,
      "XLEN CSR must be dynamic when both SXLEN and VSXLEN are mutable"
  end

  # MXLEN unknown -> dynamic regardless of S/H.
  def test_xlen_dynamic_when_mxlen_unknown
    arch = make_cfg_arch(mxlen: nil, exts: %w[A], param_values: {})
    csr = make_csr(arch, length: "XLEN")
    assert csr.dynamic_length?,
      "XLEN CSR must be dynamic when MXLEN is unknown"
  end

  # MXLEN known, S-mode possible but SXLEN fixed, no H -> NOT dynamic.
  # Guards against an over-broad fix that makes everything dynamic.
  def test_xlen_not_dynamic_when_fully_pinned
    arch = make_cfg_arch(mxlen: 32, exts: %w[A S], param_values: { "SXLEN" => [32] })
    csr = make_csr(arch, length: "XLEN")
    refute csr.dynamic_length?,
      "XLEN CSR must not be dynamic when MXLEN is known and SXLEN is fixed with no H"
  end
end
