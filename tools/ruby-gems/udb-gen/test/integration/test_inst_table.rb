# SPDX-License-Identifier: BSD-3-Clause-Clear
# SPDX-FileCopyrightText: Copyright (c) Charlie Jenkins

# typed: false
# frozen_string_literal: true
require_relative "test_helper"
require "pathname"

require "udb-gen/generators/inst_table/generator"
require "udb-gen/generators/inst_table/table_builder"

module UdbGen
  class InstTableTest < Minitest::Test
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

    def test_builder_generation
      test_cfg = "_"
      cfg_arch = @resolver.cfg_arch_for(test_cfg)

      builder = UdbGen::InstTable::TableBuilder.new(cfg_arch, "test_table.txt")

      actual_output = builder.generate

      fixture_path = File.expand_path("fixtures/inst_table/expected.txt", __dir__)

      if ENV["UPDATE_FIXTURES"]
        File.write(fixture_path, actual_output)
      end

      assert_equal File.read(fixture_path), actual_output, "***Maybe you need to regenerate? ./do chore:udb_gen:update_fixtures***"
    end
  end
end
