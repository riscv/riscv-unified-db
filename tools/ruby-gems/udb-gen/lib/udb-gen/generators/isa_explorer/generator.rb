# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "sorbet-runtime"
require "tty-exit"
require "tty-progressbar"
require "write_xlsx"

require_relative "../../common_opts"
require_relative "../../defines"
require_relative "../../template_helpers"
require_relative "table_builder"
require_relative "js_xlsx_writer"

require "udb/obj/extension"

module UdbGen
  class GenIsaExplorerOptions < SubcommandWithCommonOptions
    include TTY::Exit
    include TemplateHelpers

    NAME = "isa-explorer"

    sig { void }
    def initialize
      super(name: NAME, desc: "Create ISA explorer tables / sites")
    end

    usage \
      command: NAME,
      desc:   "Create static websites and/or spreadsheets populated with helpful ISA information",
      example: <<~EXAMPLE
        Generate a static HTML page with extension information
          $ #{File.basename($PROGRAM_NAME)} #{NAME} -t ext-browser -o gen/isa_explorer

        Generate a static HTML page with instruciton information
          $ #{File.basename($PROGRAM_NAME)} #{NAME} -t inst-browser -o gen/isa_explorer

        Generate a static HTML page with csr information
          $ #{File.basename($PROGRAM_NAME)} #{NAME} -t csr-browser -o gen/isa_explorer

        Generate an Excel spreadsheet with all info
          $ #{File.basename($PROGRAM_NAME)} #{NAME} -t xlsx -o gen/isa_explorer
        EXAMPLE

    option :type do
      T.bind(self, TTY::Option::Parameter::Option)
      short "-t"
      long "--type=type"
      desc "The type of artifact to build"
      permit ["ext-browser", "inst-browser", "csr-browser", "xlsx"]
      required
    end

    option :skip do
      T.bind(self, TTY::Option::Parameter::Option)
      long "--skip=N"
      desc "Only consider every Nth ext/inst/etc. (for testing)"
      convert :integer
      default 0
    end

    option :output_dir do
      T.bind(self, TTY::Option::Parameter::Option)
      required
      short "-o"
      long "--out=directory"
      desc "Output directory"
      convert :path
    end

    option :debug do
      T.bind(self, TTY::Option::Parameter::Option)
      desc "Set debug level"
      long "--debug=level"
      short "-d"
      default "info"
      permit ["debug", "info", "warn", "error", "fatal"]
    end

    sig { void }
    def gen_ext_browser
      FileUtils.mkdir_p params[:output_dir]

      target_html_fn = params[:output_dir] / "ext-explorer.html"

      # Delete target file if already present.
      if target_html_fn.exist?
        begin
          File.delete(target_html_fn)
        rescue StandardError => e
          raise "Can't delete '#{target_html_fn}': #{e.message}"
        end
      end

      builder = IsaExplorer::TableBuilder.new(cfg_arch, params[:skip])
      writer  = IsaExplorer::JsXlsxWriter.new
      js_table = writer.js_table(builder.ext_table, "ext_table")

      template_path = Pathname.new(Gem.loaded_specs["udb-gen"].full_gem_path) / "templates" / "isa_explorer" / "ext-browser.html.erb"

      erb = ERB.new(template_path.read, trim_mode: "-")
      erb.filename = template_path.to_s

      Udb.logger.info "SUCCESS: Writing result to #{target_html_fn}"
      target_html_fn.write erb.result(binding)
    end

    sig { void }
    def gen_inst_browser
      FileUtils.mkdir_p params[:output_dir]

      target_html_fn = params[:output_dir] / "inst-explorer.html"

      # Delete target file if already present.
      if target_html_fn.exist?
        begin
          File.delete(target_html_fn)
        rescue StandardError => e
          raise "Can't delete '#{target_html_fn}': #{e.message}"
        end
      end

      builder = IsaExplorer::TableBuilder.new(cfg_arch, params[:skip])
      writer  = IsaExplorer::JsXlsxWriter.new
      js_table = writer.js_table(builder.inst_table, "inst_table")

      template_path = Pathname.new(Gem.loaded_specs["udb-gen"].full_gem_path) / "templates" / "isa_explorer" / "inst-browser.html.erb"

      erb = ERB.new(template_path.read, trim_mode: "-")
      erb.filename = template_path.to_s

      Udb.logger.info "SUCCESS: Writing result to #{target_html_fn}"
      target_html_fn.write erb.result(binding)
    end

    sig { void }
    def gen_csr_browser
      FileUtils.mkdir_p params[:output_dir]

      target_html_fn = params[:output_dir] / "csr-explorer.html"

      # Delete target file if already present.
      if target_html_fn.exist?
        begin
          File.delete(target_html_fn)
        rescue StandardError => e
          raise "Can't delete '#{target_html_fn}': #{e.message}"
        end
      end

      builder = IsaExplorer::TableBuilder.new(cfg_arch, params[:skip])
      writer  = IsaExplorer::JsXlsxWriter.new
      js_table = writer.js_table(builder.csr_table, "csr_table")

      template_path = Pathname.new(Gem.loaded_specs["udb-gen"].full_gem_path) / "templates" / "isa_explorer" / "csr-browser.html.erb"

      erb = ERB.new(template_path.read, trim_mode: "-")
      erb.filename = template_path.to_s

      Udb.logger.info "SUCCESS: Writing result to #{target_html_fn}"
      target_html_fn.write erb.result(binding)
    end

    sig { void }
    def gen_xlsx
      FileUtils.mkdir_p params[:output_dir]

      target_xlsx_fn = params[:output_dir] / "isa_explorer.xlsx"

      # Delete target file if already present.
      if target_xlsx_fn.exist?
        begin
          File.delete(target_xlsx_fn)
        rescue StandardError => e
          raise "Can't delete '#{target_xlsx_fn}': #{e.message}"
        end
      end

      builder = IsaExplorer::TableBuilder.new(cfg_arch, params[:skip])
      writer  = IsaExplorer::JsXlsxWriter.new

      # Create a new Excel workbook
      Udb.logger.info "Creating Excel workboook #{target_xlsx_fn}"
      workbook = WriteXLSX.new(target_xlsx_fn)

      # Extension worksheet
      Udb.logger.info "Creating extension table data structure"
      ext_worksheet = workbook.add_worksheet("Extensions")
      Udb.logger.info "Adding extension table to worksheet #{ext_worksheet.name}"
      writer.xlsx_table(builder.ext_table, workbook, ext_worksheet)

      # Instruction worksheet
      Udb.logger.info "Creating instruction table data structure"
      inst_worksheet = workbook.add_worksheet("Instructions")
      Udb.logger.info "Adding instruction table to worksheet #{inst_worksheet.name}"
      writer.xlsx_table(builder.inst_table, workbook, inst_worksheet)

      # CSR worksheet
      Udb.logger.info "Creating CSR table data structure"
      csr_worksheet = workbook.add_worksheet("CSRs")
      Udb.logger.info "Adding CSR table to worksheet #{csr_worksheet.name}"
      writer.xlsx_table(builder.csr_table, workbook, csr_worksheet)

      workbook.close

      Udb.logger.info "SUCCESS: Wrote result to #{target_xlsx_fn}"
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

      case params[:type]
      when "ext-browser"
        gen_ext_browser
      when "inst-browser"
        gen_inst_browser
      when "csr-browser"
        gen_csr_browser
      when "xlsx"
        gen_xlsx
      else
        Udb.logger.error "Unknown target type: #{params[:type]}"
      end

      exit_with(:success)
    end

  end
end
