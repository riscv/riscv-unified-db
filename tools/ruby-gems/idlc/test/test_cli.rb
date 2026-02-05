# typed: false
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require "open3"

require "idlc/cli"
require "minitest/autorun"

class CliTest < Minitest::Test
  CommandResult = Struct.new(:status, :out, :err)

  def result
    @result ||= CommandResult.new
  end

  def run_cmd(cmd)
    puts "> #{cmd}"
    result.out, result.err, result.status = Open3.capture3(cmd)
  end
end

# Test Command Line Interface
class TestCli < CliTest
  def test_eval_addition
    run_cmd("idlc eval -DA=5 -DB=10 A+B")
    assert_equal 0, result.status
    assert_empty result.err, "nothing should be written to STDERR"
    assert_equal 15, eval(result.out)
  end

  def test_operation_tc
    Tempfile.open("idl") do |f|
      f.write <<~YAML
        operation(): |
          XReg src1 = X[xs1];
          XReg src2 = X[xs2];

          X[xd] = src1 + src2;
      YAML
      f.flush

      run_cmd("idlc tc inst -k 'operation()' -d xs1=5 -d xs2=5 -d xd=5 #{f.path}")
      assert_equal 0, result.status
      assert_empty result.err, "nothing should be written to STDERR"
      assert_empty result.out, "nothing should be written to STDOUT"
    end
  end

  # recursively remove key from hash
  def remove(data, keys_to_remove)
    case data
    when Hash
      data.delete_if do |k, v|
        # Delete if the current key is in the list to remove
        is_key_to_remove = Array(keys_to_remove).include?(k)

        # Recurse on the value if it's not being deleted
        remove(v, keys_to_remove) unless is_key_to_remove

        is_key_to_remove
      end
    when Array
      data.each do |item|
        remove(item, keys_to_remove)
      end
    end
    data
  end

  def test_compile
    Tempfile.open("idl") do |f|
      idl = <<~YAML
          XReg src1 = X[xs1];
          XReg src2 = X[xs2];

          X[xd] = src1 + src2;
      YAML
      f.write idl
      f.flush

      compiler = Idl::Compiler.new
      m = compiler.parser.parse(idl, root: :instruction_operation)
      refute_nil m
      ast = m.to_ast
      refute_nil ast

      run_cmd("idlc compile -f yaml -r instruction_operation #{f.path}")
      assert_equal 0, result.status
      assert_equal remove(ast.to_h, "source"), remove(YAML::load(result.out), "source")

      o = Tempfile.create("idl")
      run_cmd("idlc compile -f yaml -r instruction_operation #{f.path} -o #{o.path}")
      assert_equal 0, result.status
      assert_equal remove(ast.to_h, "source"), remove(YAML::load_file(o.path), "source")

      run_cmd("idlc compile")
      refute_equal 0, result.status

      run_cmd("idlc compile arg1 arg2")
      refute_equal 0, result.status

      run_cmd("idlc compile -f bad -r instruction_operation #{f.path}")
      refute_equal 0, result.status

    end
  end
end
