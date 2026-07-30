# Copyright (c) 2026 Hitesh Sai
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require_relative "test_helper"
require_relative "../lib/udb/z3"

# "Unsigned power of two" is defined twice in this repository:
#
#   1. spec/schemas/schema_defs.json, as an explicit enum
#      ($defs/32bit_unsigned_pow2, $defs/64bit_unsigned_pow2)
#   2. Udb::Z3ParameterTerm.constrain_int, which re-derives the same
#      constraint algebraically for the solver
#
# Nothing pins the solver side of that pair, so a change to the assertions in
# constrain_int can alter which values are satisfiable without any test
# noticing. These tests characterise the solver side directly: which values the
# $ref branches accept and reject.
#
# In particular they pin the handling of zero. The bit identity used to detect
# a power of two, v & (v - 1) == 0, is also true for zero, so zero is excluded
# by the strictly-positive lower bound rather than by the identity. A future
# edit that relaxes that bound to unsigned_ge(0), matching the uint32/uint64
# branches directly above, would silently start accepting zero.
class TestZ3Pow2Agreement < Minitest::Test
  POW2_DEFS = {
    "32bit_unsigned_pow2" => 32,
    "64bit_unsigned_pow2" => 64
  }.freeze

  # Ask the solver whether `value` is admitted by the constraints that
  # constrain_int builds for the given $ref. Each query uses a fresh solver so
  # assertions cannot leak between checks.
  def z3_accepts?(def_name, value)
    solver = Udb::Z3Solver.new
    term = Z3.Bitvec("pow2_probe_#{def_name}_#{value}", 64)
    Udb::Z3ParameterTerm.constrain_int(
      solver, term, { "$ref" => "schema_defs.json#/$defs/#{def_name}" }
    )
    solver.assert(term == value)
    solver.satisfiable?
  end

  def test_powers_of_two_in_range_are_accepted
    POW2_DEFS.each_pair do |def_name, bits|
      in_range_powers = (0...bits).map { |i| 1 << i }
      rejected = in_range_powers.reject { |v| z3_accepts?(def_name, v) }
      assert_empty rejected,
                   "#{def_name}: in-range powers of two were rejected: #{rejected.inspect}"
    end
  end

  # Zero satisfies v & (v - 1) == 0 but is not a power of two.
  def test_zero_is_rejected
    POW2_DEFS.each_key do |def_name|
      refute z3_accepts?(def_name, 0),
             "#{def_name}: zero must not be accepted as a power of two"
    end
  end

  # 4095 (0xfff) is the specific non-power-of-two that has historically leaked
  # into power-of-two enums in this repository; see #2137.
  def test_non_powers_of_two_are_rejected
    POW2_DEFS.each_key do |def_name|
      [3, 100, 4095].each do |v|
        refute z3_accepts?(def_name, v),
               "#{def_name}: #{v} is not a power of two and must be rejected"
      end
    end
  end

  # The 32-bit branch bounds values at 2**32 - 1, so 2**32 is out of range even
  # though it is a power of two. The 64-bit branch accepts it.
  def test_upper_bound_is_enforced_for_32bit
    refute z3_accepts?("32bit_unsigned_pow2", 2**32),
           "32bit_unsigned_pow2: 2**32 exceeds the 32-bit bound and must be rejected"
    assert z3_accepts?("64bit_unsigned_pow2", 2**32),
           "64bit_unsigned_pow2: 2**32 is in range and must be accepted"
  end
end
