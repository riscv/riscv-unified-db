# SPDX-License-Identifier: BSD-3-Clause-Clear
# SPDX-FileCopyrightText: Copyright (c) Charlie Jenkins

# typed: true
# frozen_string_literal: true

require "tty-exit"

require_relative "../../common_opts"
require_relative "../../defines"
require_relative "../../template_helpers"
require_relative "table_builder"

require "udb/obj/extension"

module UdbGen
  class InstTableOptions < SubcommandWithCommonOptions
    include TTY::Exit

    NAME = "inst-table"

    sig { void }
    def initialize
      super(name: NAME, desc: "Generate an instruction table")
    end

    usage \
      command: NAME,
      desc:   "Generate an instruction table for extensions defined in UDB",
      example: <<~EXAMPLE
        Generate an instruction table for all extensions, printed to stdout
          $ #{File.basename($PROGRAM_NAME)} #{NAME}

        Generate an instruction table for all extensions, written to a file
          $ #{File.basename($PROGRAM_NAME)} #{NAME} -o inst_table.txt
      EXAMPLE

    option :output_file do
      T.bind(self, TTY::Option::Parameter::Option)
      short "-o"
      long "--out=file"
      desc "Output file (default: stdout)"
      convert :path
    end

    sig { void }
    def gen_inst_table
      target_file = params[:output_file]
      builder = InstTable::TableBuilder.new(cfg_arch, target_file&.basename&.to_s)

      if target_file.nil?
        $stdout.write(builder.generate)
      else
        File.write(target_file, builder.generate)
      end
    end

    sig { override.params(argv: T::Array[String]).returns(T.noreturn) }
    def run(argv)
      parse(argv)

      if params[:help]
        print help
        exit_with(:success)
      end

      if params.errors.any?
        exit_with(:usage_error, "#{params.errors.summary}\n\n#{help}")
      end

      unless params.remaining.empty?
        exit_with(:usage_error, "Unknown arguments: #{params.remaining}\n")
      end

      gen_inst_table

      exit_with(:success)
    end

  end
end
