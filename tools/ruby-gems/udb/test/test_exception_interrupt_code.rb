# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require_relative "test_helper"
require "tmpdir"
require "fileutils"

require "udb/resolver"

class TestExceptionInterruptCode < Minitest::Test
  include Udb

  def setup
    @gen_dir = Dir.mktmpdir
    @resolver = Resolver.new(
      Udb.repo_root,
      gen_path_override: Pathname.new(@gen_dir)
    )
    @arch = @resolver.cfg_arch_for("_")
  end

  def teardown
    FileUtils.rm_rf @gen_dir
  end

  def test_exception_code_comparisons
    exceptions = @arch.exception_codes.to_a
    assert_operator exceptions.size, :>, 1

    # Test sorting
    sorted = exceptions.sort
    assert_equal exceptions.map(&:num).sort, sorted.map(&:num)

    # Test eql? and hash contract
    exc1 = exceptions.find { |e| e.num == 1 }
    exc2 = exceptions.find { |e| e.num == 1 }
    exc3 = exceptions.find { |e| e.num != 1 }

    assert_equal exc1, exc2
    assert exc1.eql?(exc2)
    assert_equal exc1.hash, exc2.hash

    if exc3
      refute_equal exc1, exc3
      refute exc1.eql?(exc3)
      refute_equal exc1.hash, exc3.hash
    end
  end

  def test_interrupt_code_comparisons
    interrupts = @arch.interrupt_codes.to_a
    assert_operator interrupts.size, :>, 1

    # Test sorting
    sorted = interrupts.sort
    assert_equal interrupts.map(&:num).sort, sorted.map(&:num)

    # Test eql? and hash contract
    int1 = interrupts.find { |i| i.num == 1 }
    int2 = interrupts.find { |i| i.num == 1 }
    int3 = interrupts.find { |i| i.num != 1 }

    assert_equal int1, int2
    assert int1.eql?(int2)
    assert_equal int1.hash, int2.hash

    if int3
      refute_equal int1, int3
      refute int1.eql?(int3)
      refute_equal int1.hash, int3.hash
    end
  end

  def test_cross_type_comparisons
    exc = @arch.exception_codes.find { |e| e.num == 1 }
    int = @arch.interrupt_codes.find { |i| i.num == 1 }

    # If both num=1 exist, ensure they do not equal or collide in hash
    if exc && int
      assert_nil exc <=> int
      assert_nil int <=> exc

      refute_equal exc, int
      refute exc.eql?(int)
      refute_equal exc.hash, int.hash
    end
  end
end
