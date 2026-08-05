# typed: false
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require_relative "test_helper"


require "stringio"
require "udb/cli"

# this is needed for tty-progressbar to work with minitest
unless StringIO.method_defined? :ioctl
  class StringIO
    def ioctl(*)
      # :nocov:
      80
      # :nocov:
    end
  end
end

class TestCli < Minitest::Test
  def run_cmd(cmdline)
    Udb::Cli.start(cmdline.split(" "))
  end

  def test_list_extensions
    out, err = capture_io do
      run_cmd("list extensions")
    end
    assert_match %r{Zvkg}, out
  end

  def test_list_qc_iu_extensions
    out, err = capture_io do
      run_cmd("list extensions --config qc_iu")
    end
    assert_match %r{Xqci}, out
  end

  def test_list_params
    out, err = capture_io do
      run_cmd("list parameters")
    end
    assert_match %r{MXLEN}, out
  end

  def test_list_params_filtered
    out, _err = capture_io do
      run_cmd("list parameters -e Sm H")
    end
    assert_match %r{MXLEN}, out
    refute_match %r{MUTABLE_ISA_S}, out
  end

  def test_list_params_yaml
    t = Tempfile.new
    _out, _err = capture_io do
      run_cmd("list parameters -f yaml -o #{t.path}")
    end
    data = YAML.load_file(t.path)
    assert_equal data.any? { |p| p["name"] == "MXLEN" }, true
  end

  def test_disasm
    out, _err = capture_io do
      run_cmd("disasm 0x00000037")
    end

    assert_match "  lui", out
  end

  def test_list_csrs
    num_listed = nil
    _out, _err = capture_io do
      num_listed = run_cmd("list csrs")
    end

    repo_top = Udb.repo_root
    num_csr_yaml_files = `find #{repo_top}/spec/std/isa/csr/ -name '*.yaml' | wc -l`.to_i

    assert_equal num_csr_yaml_files, num_listed
  end

  def test_dummy_progressbar_format
    bar = Udb::DummyProgressBar.new
    bar.format = "Test :bar"
    assert_equal "Test :bar", bar.format
    bar.advance
    bar.finish

    old_level = Udb.log_level
    begin
      Udb.log_level = Udb::LogLevel::Warn
      bar_warn = Udb.create_progressbar("Test :bar")
      assert_instance_of Udb::DummyProgressBar, bar_warn
      bar_warn.format = "New format"
      assert_equal "New format", bar_warn.format

      Udb.log_level = Udb::LogLevel::Warn
      Udb.create_top_level_progressbar(level: Udb::LogLevel::Info)
      sub_bar = Udb.create_progressbar("Sub :bar")
      assert_instance_of Udb::DummyProgressBar, sub_bar
      assert_equal "Sub :bar", sub_bar.format
      sub_bar.format = "Updated sub :bar"
      assert_equal "Updated sub :bar", sub_bar.format
    ensure
      Udb.delete_top_level_progressbar
      Udb.log_level = old_level
    end
  end
end
