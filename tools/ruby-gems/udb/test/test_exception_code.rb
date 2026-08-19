# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require_relative "test_helper"

require "pathname"
require "concurrent"
require "sorbet-runtime"
require "udb/cfg_arch"
require "udb/obj/exception_code"

# Tests for Udb::InterruptCode comparison/hashing.
#
# InterruptCode was copy-pasted from ExceptionCode and two references were left
# pointing at ExceptionCode instead of InterruptCode, which broke sorting (<=>
# always returned nil) and caused hash collisions with the same-num ExceptionCode.
# See https://github.com/riscv/riscv-unified-db/issues/1979
class TestExceptionCode < Minitest::Test
  include Udb

  # Build a genuine ConfiguredArchitecture (Sorbet passes) with minimal state,
  # mirroring test_register_file_obj.rb.
  def make_arch
    arch = Udb::ConfiguredArchitecture.allocate
    arch.instance_variable_set(:@objects, Concurrent::Hash.new)
    arch.instance_variable_set(:@object_hashes, Concurrent::Hash.new)
    arch
  end

  def make_code(klass, arch, name, num)
    data = {
      "kind" => klass == Udb::InterruptCode ? "interrupt_code" : "exception_code",
      "name" => name,
      "num" => num,
      "display_name" => name
    }
    klass.new(data, Pathname.new("/mock/#{name}.yaml"), arch)
  end

  def test_interrupt_code_compare
    arch = make_arch
    low = make_code(Udb::InterruptCode, arch, "Interrupt1", 1)
    high = make_code(Udb::InterruptCode, arch, "Interrupt2", 2)

    assert_equal(-1, low <=> high,
      "InterruptCode#<=> must compare by num, not return nil for two InterruptCodes")
    assert_equal(1, high <=> low)
    assert_equal(0, low <=> make_code(Udb::InterruptCode, arch, "Other", 1))
  end

  def test_interrupt_code_sort
    arch = make_arch
    two = make_code(Udb::InterruptCode, arch, "Interrupt2", 2)
    one = make_code(Udb::InterruptCode, arch, "Interrupt1", 1)
    three = make_code(Udb::InterruptCode, arch, "Interrupt3", 3)

    assert_equal [one, two, three], [three, one, two].sort,
      "InterruptCode must be sortable by num"
  end

  def test_interrupt_code_hash_does_not_collide_with_exception_code
    arch = make_arch
    interrupt = make_code(Udb::InterruptCode, arch, "Interrupt1", 1)
    exception = make_code(Udb::ExceptionCode, arch, "Exception1", 1)

    refute_equal interrupt.hash, exception.hash,
      "InterruptCode#hash must not collide with an ExceptionCode of the same num"
    refute interrupt.eql?(exception),
      "InterruptCode must not be eql? to an ExceptionCode of the same num"
  end

  def test_interrupt_code_eql
    arch = make_arch
    a = make_code(Udb::InterruptCode, arch, "Interrupt1", 1)
    b = make_code(Udb::InterruptCode, arch, "Interrupt2", 2)

    assert a.eql?(make_code(Udb::InterruptCode, arch, "SameNum", 1)),
      "InterruptCodes with the same num must be eql?"
    refute a.eql?(b),
      "InterruptCodes with different nums must not be eql?"
  end
end
