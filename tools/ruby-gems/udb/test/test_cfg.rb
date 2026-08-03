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

  # a partially-configured config with no `params:` key at all must still
  # expose a Hash from param_values, not the Array it used to default to
  def test_partial_config_without_params_key_has_hash_param_values
    cfg_path = Pathname.new(@gen_dir) / "no_params.yaml"
    cfg_path.write(<<~YAML)
      $schema: config_schema.json#
      kind: architecture configuration
      type: partially configured
      name: no_params
      description: Partial config with no params key, to check param_values defaults to a Hash
      mandatory_extensions:
        - name: I
          version: ">= 2.1"
    YAML

    cfg_arch = @resolver.cfg_arch_for(cfg_path)

    assert_kind_of Hash, cfg_arch.config.param_values
    refute cfg_arch.config.param_values.key?("SXLEN")
    assert_nil cfg_arch.config.param_values["SXLEN"]
  end
end
