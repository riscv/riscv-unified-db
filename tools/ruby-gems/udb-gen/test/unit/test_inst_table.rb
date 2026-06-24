# SPDX-License-Identifier: BSD-3-Clause-Clear
# SPDX-FileCopyrightText: Copyright (c) Charlie Jenkins

# typed: false
# frozen_string_literal: true
require_relative "test_helper"
require "tempfile"
require "pathname"

require "udb-gen/generators/inst_table/generator"
require "udb-gen/generators/inst_table/table_builder"

module UdbGen
  class InstTableTest < Minitest::Test
    def mock_instruction(name, ops, vars, supported_32, supported_64)
      inst = mock("#{name}_inst")
      inst.stubs(:name).returns(name)

      ops = ops.map do |ops_data|
        o = mock("op_#{ops_data[:name]}")
        o.stubs(:name).returns(ops_data[:name])
        o.stubs(:range).returns(ops_data[:range])
        o
      end

      enc_obj = mock("#{name}_enc")
      enc_obj.stubs(:opcode_fields).returns(ops)

      vars = vars.map do |v_data|
        v = mock("var_#{v_data[:name]}")
        v.stubs(:name).returns(v_data[:name])
        v.stubs(:location).returns(v_data[:location])
        v.stubs(:sext?).returns(v_data[:sext])
        v.stubs(:excludes).returns(v_data[:excludes])
        v.stubs(:left_shift).returns(v_data[:left_shift])
        v
      end

      inst.stubs(:defined_in_base?).with(32).returns(supported_32)
      inst.stubs(:defined_in_base?).with(64).returns(supported_64)
      inst.stubs(:encoding).returns(enc_obj)
      inst.stubs(:decode_variables).returns(vars)

      inst
    end

    def setup
      @mock_arch = mock("udb_architecture")
      @one = mock_instruction("one", [
        { name: "0100000", range: 31..25 },
        { name: "111", range: 14..12 },
        { name: "0110011", range: 6..0 }
      ], [
        { name: "xs2", location: "24-20", sext: false, excludes: [], left_shift: 0 },
        { name: "xs1", location: "19-15", sext: false, excludes: [], left_shift: 0 },
        { name: "xd",  location: "11-7" , sext: false, excludes: [], left_shift: 0 }
      ], true, true)

      @two = mock_instruction("two", [
        { name: "1100011", range: 6..0 },
        { name: "101", range: 14..12 }
      ], [
        { name: "imm", location: "31|7|30-25|11-8", sext: true, excludes: [], left_shift: 1 },
        { name: "xs2", location: "24-20", sext: false, excludes: [], left_shift: 0 },
        { name: "xs1",  location: "19-15" , sext: false, excludes: [], left_shift: 0 }
      ], true, false)

      @three = mock_instruction("three", [
        { name: "1100011", range: 6..0 },
        { name: "101", range: 14..12 }
      ], [
        { name: "imm", location: "31-25|11-7", sext: false, excludes: [], left_shift: 0 },
        { name: "xs2", location: "24-20", sext: false, excludes: [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31], left_shift: 0 },
        { name: "xs1",  location: "19-15" , sext: false, excludes: [], left_shift: 0 }
      ], false, true)

      @mock_arch.stubs(:instructions).returns([@one, @two, @three])

      mock_ext = mock("ext")
      mock_ext.stubs(:name).returns("ext")
      @mock_arch.stubs(:extensions).returns([mock_ext])
    end

    def test_builder_generation
      builder = InstTable::TableBuilder.new(@mock_arch, "test_table.txt")

      actual_output = builder.generate

      fixture_path = File.expand_path("fixtures/inst_table/expected.txt", __dir__)

      if ENV["UPDATE_FIXTURES"]
        File.write(fixture_path, actual_output)
      end

      assert_equal File.read(fixture_path), actual_output, "***Maybe you need to regenerate? ./do chore:udb_gen:update_fixtures***"
    end

    def test_generator_writes_file_to_disk
      temp_out = Tempfile.new(["inst_table", ".txt"])
      temp_path = Pathname.new(temp_out.path)
      temp_out.close

      options_cmd = UdbGen::InstTableOptions.new

      options_cmd.stubs(:cfg_arch).returns(@mock_arch)

      options_cmd.stubs(:params).returns({ output_file: temp_path })

      options_cmd.gen_inst_table

      assert File.exist?(temp_path), "The generator should create the output file"
      refute_empty File.read(temp_path), "The output file should not be empty"
    ensure
      File.delete(temp_path) if File.exist?(temp_path)
    end
  end
end
