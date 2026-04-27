# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "sorbet-runtime"
require "tty-progressbar"

module UdbGen
  module IsaExplorer
    class TableBuilder
      extend T::Sig

      sig { params(arch: Udb::ConfiguredArchitecture, skip: Integer).void }
      def initialize(arch, skip)
        @arch = arch
        @skip = skip
      end

      # @return Extension table data
      sig { returns(T::Hash[String, T::Array[T.untyped]]) }
      def ext_table
        sorted_releases = sorted_profile_releases

        table = {
          # Array of hashes
          "columns" => [
            { name: "Extension Name", formatter: "link", sorter: "alphanum", headerFilter: true, frozen: true, formatterParams:
              {
              labelField: "Extension Name",
              urlPrefix: "https://riscv.github.io/riscv-unified-db/manual/html/isa/isa_20240411/exts/"
              }
            },
            { name: "Description", formatter: "textarea", sorter: "alphanum", headerFilter: true },
            { name: "IC", formatter: "textarea", sorter: "alphanum", headerFilter: true },
            { name: "Requires\n(Exts)", formatter: "textarea", sorter: "alphanum" },
            { name: "Transitive Requires\n(Ext)", formatter: "textarea", sorter: "alphanum" },
            { name: "Incompatible\n(Ext Reqs)", formatter: "textarea", sorter: "alphanum" },
            { name: "Ratified", formatter: "textarea", sorter: "boolean", headerFilter: true },
            { name: "Ratification\nDate", formatter: "textarea", sorter: "alphanum", headerFilter: true },
            sorted_releases.map do |pr|
              { name: "#{pr.name}", formatter: "textarea", sorter: "alphanum", headerFilter: true }
            end
          ].flatten,

          # Will eventually be an array containing arrays.
          "rows" => []
          }

        pb = Udb.create_progressbar(
          "Analyzing extensions [:bar] :current/:total",
          total: @arch.extensions.size,
          clear: true
        )

        @arch.extensions.sort_by!(&:name).each_with_index do |ext, idx|
          pb.advance

          if @skip != 0
            next unless (idx % @skip) == 0
          end

          row = [
            ext.name,           # Name
            ext.long_name,      # Description
            ext.compact_priv_type,  # IC
            ext.max_version.ext_requirements(expand: false).map do |cond_ext_req|
              if cond_ext_req.cond.empty?
                cond_ext_req.ext_req.name
              else
                "#{cond_ext_req.ext_req.name} if #{cond_ext_req.cond}"
              end
            end.uniq,  # Requires
            ext.max_version.ext_requirements(expand: true).map do |cond_ext_req|
              if cond_ext_req.cond.empty?
                cond_ext_req.ext_req.name
              else
                "#{cond_ext_req.ext_req.name} if #{cond_ext_req.cond}"
              end
            end.uniq,  # Transitive Requires
            ext.conflicting_extensions.map(&:name),
            ext.ratified,
            if ext.ratified
              rat_date = T.must(ext.min_ratified_version).ratification_date
              if rat_date.nil? || rat_date.empty?
                "UDB MISSING"
              else
                rat_date
              end
            else
              ""
            end
          ]

          sorted_releases.each do |pr|
            row.append(presence2char(pr.extension_presence(ext.name)))
          end

          table["rows"].append(row)
        end

        table
      end

      # @return Instruction table data
      sig { returns(T::Hash[String, T::Array[T.untyped]]) }
      def inst_table
        sorted_releases = sorted_profile_releases

        table = {
          # Array of hashes
          "columns" => [
            { name: "Instruction Name", formatter: "link", sorter: "alphanum", headerFilter: true, frozen: true, formatterParams:
              {
              labelField: "Instruction Name",
              urlPrefix: "https://riscv.github.io/riscv-unified-db/manual/html/isa/isa_20240411/insts/"
              }
            },
            { name: "Description", formatter: "textarea", sorter: "alphanum", headerFilter: true },
            { name: "Assembly", formatter: "textarea", sorter: "alphanum", headerFilter: true },
            sorted_releases.map do |pr|
              { name: "#{pr.name}", formatter: "textarea", sorter: "alphanum", headerFilter: true }
            end
          ].flatten,

          # Will eventually be an array containing arrays.
          "rows" => []
          }

        insts = @arch.instructions.sort_by!(&:name)
        progressbar = TTY::ProgressBar.new("Instruction Table [:bar] :current/:total", total: insts.size, output: $stdout)

        insts.each_with_index do |inst, idx|
          progressbar.advance
          if @skip != 0
            next unless (idx % @skip) == 0
          end

          row = [
            inst.name,
            inst.long_name,
            inst.name + " " + inst.assembly.gsub("x", "r")
          ]

          sorted_releases.each do |pr|
            row.append(presence2char(pr.instruction_presence(inst.name)))
          end

          table["rows"].append(row)
        end

        table
      end

      # @return CSR table data
      sig { returns(T::Hash[String, T::Array[T.untyped]]) }
      def csr_table
        sorted_releases = sorted_profile_releases

        table = {
          # Array of hashes
          "columns" => [
            { name: "CSR Name", formatter: "link", sorter: "alphanum", headerFilter: true, frozen: true, formatterParams:
              {
              labelField: "CSR Name",
              urlPrefix: "https://riscv.github.io/riscv-unified-db/manual/html/isa/isa_20240411/csrs/"
              }
            },
            { name: "Address", formatter: "textarea", sorter: "number", headerFilter: true },
            { name: "Description", formatter: "textarea", sorter: "alphanum", headerFilter: true },
            sorted_releases.map do |pr|
              { name: "#{pr.name}", formatter: "textarea", sorter: "alphanum", headerFilter: true }
            end
          ].flatten,

          # Will eventually be an array containing arrays.
          "rows" => []
          }

        csrs = @arch.csrs.sort_by!(&:name)
        progressbar = TTY::ProgressBar.new("CSR Table [:bar]", total: csrs.size, output: $stdout)

        csrs.each_with_index do |csr, idx|
          progressbar.advance

          if @skip != 0
            next unless (idx % @skip) == 0
          end

          raise "Indirect CSRs not yet supported for CSR #{csr.name}" if csr.address.nil?

          row = [
            csr.name,
            csr.address,
            csr.long_name,
          ]

          sorted_releases.each do |pr|
            row.append(presence2char(pr.csr_presence(csr.name)))
          end

          table["rows"].append(row)
        end

        table
      end

      private

      # return Nice list of profile release to use in a nice order
      sig { returns(T::Array[Udb::ProfileRelease]) }
      def sorted_profile_releases
        # Get array of profile releases and sort by name
        sorted = @arch.profile_releases.sort_by(&:name)

        # Move RVI20 to the beginning of the array if it exists.
        if sorted.any? { |pr| pr.name == "RVI20" }
          sorted.delete_if { |pr| pr.name == "RVI20" }
          sorted.unshift(T.must(@arch.profile_release("RVI20")))
        end

        sorted
      end

      # @param presence [String] Can be nil
      # @return [String] m=mandatory, o=optional, n=not present
      sig { params(presence: String).returns(String) }
      def presence2char(presence)
        if presence == "mandatory"
          "m"
        elsif presence == "optional"
          "o"
        elsif presence == "-"
          "n"
        else
          raise ArgumentError, "Unknown presence of #{presence}"
        end
      end
    end
  end
end
