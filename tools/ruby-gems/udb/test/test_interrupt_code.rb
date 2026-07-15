# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require_relative "test_helper"

require "udb/obj/exception_code"

# ---------------------------------------------------------------------------
# Regression tests for InterruptCode#<=> and InterruptCode#hash.
#
# Both methods had copy-paste errors where they referenced ExceptionCode
# instead of InterruptCode:
#
#   - InterruptCode#<=>  always returned nil because the type guard
#     `is_a?(ExceptionCode)` never matched an InterruptCode argument.
#     This broke Array#sort, Array#min, Array#max, and all Comparable
#     methods on collections of InterruptCode objects.
#
#   - InterruptCode#hash used [ExceptionCode, num].hash, producing the
#     same hash value as an ExceptionCode with the same num. This caused
#     false Hash collisions and incorrect Set membership between the
#     two unrelated types.
#
# See: https://github.com/riscv/riscv-unified-db/issues/1979
# ---------------------------------------------------------------------------
class TestInterruptCodeComparable < Minitest::Test

  # Build lightweight InterruptCode and ExceptionCode doubles that satisfy
  # the `num` interface without requiring a live Resolver or Z3.
  # The #<=> and #hash methods under test only call `num` and `is_a?`, so
  # this is sufficient to exercise the corrected behaviour.
  def make_interrupt(n)
    obj = Udb::InterruptCode.allocate
    obj.define_singleton_method(:num) { n }
    obj
  end

  def make_exception(n)
    obj = Udb::ExceptionCode.allocate
    obj.define_singleton_method(:num) { n }
    obj
  end

  def setup
    @int1 = make_interrupt(1)
    @int2 = make_interrupt(2)
    @exc1 = make_exception(1)   # same num as @int1 — used to test hash isolation
  end

  # -------------------------------------------------------------------------
  # InterruptCode#<=>
  # -------------------------------------------------------------------------

  def test_less_than
    result = @int1 <=> @int2
    refute_nil result, "InterruptCode#<=> must not return nil for two InterruptCode objects"
    assert_operator result, :<, 0, "num=1 must compare less than num=2"
  end

  def test_greater_than
    result = @int2 <=> @int1
    refute_nil result, "InterruptCode#<=> must not return nil for two InterruptCode objects"
    assert_operator result, :>, 0, "num=2 must compare greater than num=1"
  end

  def test_equal_to_self
    assert_equal 0, (@int1 <=> @int1), "InterruptCode compared with itself must return 0"
  end

  def test_returns_nil_for_incompatible_type_exception_code
    assert_nil @int1 <=> @exc1,
      "InterruptCode <=> ExceptionCode must return nil (incompatible types)"
  end

  def test_returns_nil_for_incompatible_type_string
    assert_nil @int1 <=> "not an interrupt code",
      "InterruptCode <=> String must return nil"
  end

  def test_sortable
    sorted = [@int2, @int1].sort
    assert_equal [@int1, @int2], sorted,
      "InterruptCode objects must be sortable by num"
  end

  def test_min
    assert_equal @int1, [@int2, @int1].min
  end

  def test_max
    assert_equal @int2, [@int2, @int1].max
  end

  def test_comparable_less_than_operator
    assert @int1 < @int2
  end

  def test_comparable_greater_than_operator
    assert @int2 > @int1
  end

  # -------------------------------------------------------------------------
  # InterruptCode#hash
  # -------------------------------------------------------------------------

  def test_hash_is_stable
    assert_equal @int1.hash, @int1.hash,
      "InterruptCode#hash must return the same value on successive calls"
  end

  def test_hash_differs_for_different_nums
    refute_equal @int1.hash, @int2.hash,
      "InterruptCode objects with different nums must produce different hashes"
  end

  def test_hash_isolated_from_exception_code_with_same_num
    # Before the fix, [ExceptionCode, 1].hash == [ExceptionCode, 1].hash meant
    # an InterruptCode(1) and ExceptionCode(1) shared the same hash bucket,
    # causing subtle Set/Hash key collisions.
    refute_equal @int1.hash, @exc1.hash,
      "InterruptCode and ExceptionCode sharing the same num must not share a hash"
  end

  def test_usable_as_hash_key
    h = { @int1 => "interrupt_1", @int2 => "interrupt_2" }
    assert_equal "interrupt_1", h[@int1]
    assert_equal "interrupt_2", h[@int2]
  end

  def test_usable_in_set
    require "set"
    s = Set.new([@int1, @int2])
    assert s.include?(@int1)
    assert s.include?(@int2)
    assert_equal 2, s.size,
      "Set must not collapse two distinct InterruptCode objects"
  end

  # -------------------------------------------------------------------------
  # ExceptionCode is unchanged — verify it still works correctly
  # -------------------------------------------------------------------------

  def test_exception_code_spaceship_still_correct
    exc2 = make_exception(2)
    result = @exc1 <=> exc2
    refute_nil result, "ExceptionCode#<=> must still work after the fix"
    assert_operator result, :<, 0
  end

  def test_exception_code_hash_still_correct
    exc2 = make_exception(2)
    refute_equal @exc1.hash, exc2.hash
  end
end
