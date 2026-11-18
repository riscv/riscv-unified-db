# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require_relative "test_helper"

require "fileutils"
require "tmpdir"
require "yaml"

require "udb/logic"
require "udb/cfg_arch"
require "udb/resolver"

class TestCfg < Minitest::Test
  include Udb

  def setup
    @gen_dir = Dir.mktmpdir
    @resolver = Udb::Resolver.new(
      Udb.repo_root,
      gen_path_override: Pathname.new(@gen_dir)
    )
  end

  def teardown
    FileUtils.rm_rf @gen_dir
  end

  # make sure all the configs in the repo are valid
  Dir[Udb.repo_root / "cfgs" / "*.yaml"].each do |cfg_path|
    define_method "test_cfg_#{File.basename(cfg_path, ".yaml")}_valid" do
      cfg_arch = @resolver.cfg_arch_for(Pathname.new cfg_path)
      result = cfg_arch.valid?
      assert result.valid, <<~MSG
        Config '#{File.basename(cfg_path, ".yaml")}' is not valid.
        To see why, run `./bin/udb validate cfg #{cfg_path}`
      MSG
    end
  end

  # make sure all the profile configs in the repo are valid
  Dir[Udb.repo_root / "cfgs" / "profile" / "*.yaml"].each do |cfg_path|
    define_method "test_cfg_profile_#{File.basename(cfg_path, ".yaml")}_valid" do
      cfg_arch = @resolver.cfg_arch_for(Pathname.new cfg_path)
      result = cfg_arch.valid?
      assert result.valid, <<~MSG
        Config '#{File.basename(cfg_path, ".yaml")}' is not valid.
        To see why, run `./bin/udb validate cfg #{cfg_path}`
      MSG
    end
  end

  # Full rv64 config that also implements Sdext, with the given DCSR_*_TYPE values
  def dcsr_cfg_arch(name, params)
    data = YAML.load_file(Udb.repo_root / "cfgs" / "rv64-riscv-tests.yaml")
    data["name"] = name
    data["implemented_extensions"] << ["Sdext", "1.0.0"]
    data["params"].merge!(params)
    path = Pathname.new(@gen_dir) / "#{name}.yaml"
    File.write(path, YAML.dump(data))
    @resolver.cfg_arch_for(path)
  end

  def test_dcsr_rw_fields_are_rw
    dcsr = dcsr_cfg_arch(
      "dcsr_rw",
      "DCSR_MPRVEN_TYPE" => "rw",
      "DCSR_STEPIE_TYPE" => "rw",
      "DCSR_STOPCOUNT_TYPE" => "rw",
      "DCSR_STOPTIME_TYPE" => "rw"
    ).csr("dcsr")
    %w[MPRVEN STEPIE STOPCOUNT STOPTIME].each do |field|
      assert_equal "RW", dcsr.field(field).type(64), "dcsr.#{field}"
    end
    assert_equal 0, dcsr.field("STEPIE").reset_value
  end

  def test_dcsr_read_only_fields_are_ro
    dcsr = dcsr_cfg_arch(
      "dcsr_ro",
      "DCSR_MPRVEN_TYPE" => "read-only-1",
      "DCSR_STEPIE_TYPE" => "read-only-0",
      "DCSR_STOPCOUNT_TYPE" => "read-only-0",
      "DCSR_STOPTIME_TYPE" => "read-only-1"
    ).csr("dcsr")
    %w[MPRVEN STEPIE STOPCOUNT STOPTIME].each do |field|
      assert_equal "RO", dcsr.field(field).type(64), "dcsr.#{field}"
    end
    assert_equal 1, dcsr.field("MPRVEN").reset_value
    assert_equal 0, dcsr.field("STEPIE").reset_value
    assert_equal 0, dcsr.field("STOPCOUNT").reset_value
    assert_equal 1, dcsr.field("STOPTIME").reset_value
  end
end
