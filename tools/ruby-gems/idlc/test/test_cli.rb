# typed: false
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require "stringio"
require "tempfile"
require "tty-progressbar"

require "idlc/cli"
require "minitest/autorun"

class CliTest < Minitest::Test
  CommandResult = Struct.new(:status, :out, :err)

  # Drive the CLI in-process (rather than shelling out to the `idlc` binary)
  # so the command code in lib/idlc/cli.rb runs under the test process and is
  # captured by SimpleCov. Returns the captured stdout/stderr and exit status.
  def run_cli(*argv)
    out = StringIO.new
    err = StringIO.new
    orig_out = $stdout
    orig_err = $stderr
    $stdout = out
    $stderr = err
    status = 0
    begin
      Idl::Cli.new(argv).run
    rescue SystemExit => e
      status = e.status
    rescue StandardError => e
      # Commander normally rescues and exits non-zero; if an error escapes,
      # treat it as a failed invocation.
      err << e.message
      status = 1
    ensure
      $stdout = orig_out
      $stderr = orig_err
    end
    CommandResult.new(status, out.string, err.string)
  end
end

# Test Command Line Interface
class TestCli < CliTest
  def test_eval_addition_to_stdout
    result = run_cli("eval", "-DA=5", "-DB=10", "A+B")
    assert_equal 0, result.status
    assert_equal 15, eval(result.out.strip)
  end

  def test_eval_to_output_file
    out = Tempfile.create("idl-eval-out")
    result = run_cli("eval", "-DA=5", "-DB=10", "-o", out.path, "A+B")
    assert_equal 0, result.status
    assert_equal 15, eval(File.read(out.path).strip)
  end

  def test_eval_missing_expression_fails
    result = run_cli("eval")
    refute_equal 0, result.status
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

      result = run_cli("tc", "inst", "-k", "operation()", "-d", "xs1=5", "-d", "xs2=5", "-d", "xd=5", f.path)
      assert_equal 0, result.status
    end
  end

  def test_operation_tc_undefined_vars_fails
    Tempfile.open("idl") do |f|
      f.write <<~YAML
        operation(): |
          X[xd] = X[xs1] + X[xs2];
      YAML
      f.flush

      # No -d decode vars defined, so type checking must fail.
      result = run_cli("tc", "inst", "-k", "operation()", "-s", f.path)
      refute_equal 0, result.status
    end
  end

  # recursively remove key from hash
  def remove(data, keys_to_remove)
    case data
    when Hash
      data.delete_if do |k, v|
        is_key_to_remove = Array(keys_to_remove).include?(k)
        remove(v, keys_to_remove) unless is_key_to_remove
        is_key_to_remove
      end
    when Array
      data.each { |item| remove(item, keys_to_remove) }
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
      compiler.pb = TTY::ProgressBar.new("compiling [:bar]")
      ast = compiler.build_ast(idl, root: :instruction_operation)
      refute_nil ast
      ast.set_input_file(__FILE__)

      result = run_cli("compile", "-f", "yaml", "-r", "instruction_operation", f.path)
      assert_equal 0, result.status
      assert_equal remove(ast.to_h, "source"), remove(YAML.load(result.out), "source")

      o = Tempfile.create("idl")
      result = run_cli("compile", "-f", "yaml", "-r", "instruction_operation", f.path, "-o", o.path)
      assert_equal 0, result.status
      assert_equal remove(ast.to_h, "source"), remove(YAML.load_file(o.path), "source")
    end
  end

  def test_compile_missing_file_fails
    result = run_cli("compile")
    refute_equal 0, result.status
  end

  def test_compile_extra_args_fails
    result = run_cli("compile", "arg1", "arg2")
    refute_equal 0, result.status
  end

  def test_compile_bad_format_fails
    Tempfile.open("idl") do |f|
      f.write "X[xd] = 1;\n"
      f.flush
      result = run_cli("compile", "-f", "bad", "-r", "instruction_operation", f.path)
      refute_equal 0, result.status
    end
  end
end
