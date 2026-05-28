# Copyright (c) Jordan Carlin, Harvey Mudd College.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "sorbet-runtime"
require "tty-exit"

require_relative "../../common_opts"
require_relative "../../defines"
require_relative "../../cfg_header_base"

module UdbGen
  class GenCfgSvhHeaderOptions < SubcommandWithCommonOptions
    include TTY::Exit
    include CfgHeaderBase

    NAME = "cfg-svh-header"

    sig { void }
    def initialize
      super(name: NAME, desc: "Generate a SystemVerilog header with `define directives from a fully configured UDB config")
    end

    usage \
      command: NAME,
      desc: "Generate a SystemVerilog header file with `define directives derived from a fully configured UDB YAML config",
      example: <<~EXAMPLE
        Generate a SystemVerilog header for the rv64 config, printed to stdout
          $ #{File.basename($PROGRAM_NAME)} #{NAME} -c rv64

        Generate a SystemVerilog header for the rv64 config, written to a file
          $ #{File.basename($PROGRAM_NAME)} #{NAME} -c rv64 -o config.svh

        Generate a SystemVerilog header for a custom config file
          $ #{File.basename($PROGRAM_NAME)} #{NAME} -c /path/to/my_config.yaml
      EXAMPLE

    option :output do
      T.bind(self, TTY::Option::Parameter::Option)
      short "-o"
      long "--output=file"
      desc "Output file path (default: stdout)"
      convert :path
    end

    sig { override.returns(String) }
    def define_directive = "`define"

    sig { override.returns(String) }
    def command_name = NAME

    sig { override.params(guard_name: String).returns(String) }
    def guard_begin(guard_name) = "`ifndef #{guard_name}"

    sig { override.params(guard_name: String).returns(String) }
    def guard_end(guard_name) = "`endif // #{guard_name}"

    sig { override.returns(String) }
    def guard_suffix = "_SVH"

    sig { override.params(text: String).returns(String) }
    def section_comment(text) = "// #{text}"

    sig { override.params(text_lines: T::Array[String]).returns(T::Array[String]) }
    def header_comment(text_lines)
      text_lines.map { |line| line.empty? ? "//" : "// #{line}" }
    end

    sig { override.returns(String) }
    def file_type_name = "SystemVerilog header"

    # Emit sized hex literals so large unsigned values are not misinterpreted
    sig { override.params(value: Integer).returns(String) }
    def format_integer(value)
      bits = [32, value.bit_length].max
      width = ((bits + 31) / 32) * 32
      "#{width}'h#{value.to_s(16).upcase}"
    end

    sig { override.params(argv: T::Array[String]).returns(T.noreturn) }
    def run(argv)
      run_generator(argv)
    end
  end
end
