# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "sorbet-runtime"

module UdbGen
  module AdocHelpers
    extend T::Sig
    include Kernel

    # Returns the :revmark: attribute value for the given ExtensionVersion.
    sig { params(version: Udb::ExtensionVersion).returns(String) }
    def state_revmark(version)
      case version.state
      when "ratified"
        <<~STATE
          This document is in the http://riscv.org/spec-state[Ratified state] + \\
          + \\
          No changes are allowed. + \\
          Any desired or needed changes can be the subject of a follow-on new extension. + \\
          Ratified extensions are never revised. + \\
        STATE
      when "frozen"
        <<~STATE
          This document is in the http://riscv.org/spec-state[Frozen state]. + \\
          + \\
          Change is extremely unlikely. + \\
          A high threshold will be used, and a change will only occur because of some truly + \\
          critical issue being identified during the public review cycle. + \\
          Any other desired or needed changes can be the subject of a follow-on new extension. + \\
        STATE
      when "development"
        <<~STATE
          This document is in the http://riscv.org/spec-state[Development state]. + \\
          + \\
          Change should be expected + \\
        STATE
      else
        raise "Unknown state: #{version.state}"
      end
    end

    # Returns the preamble [WARNING] admonition block for the given ExtensionVersion.
    sig { params(version: Udb::ExtensionVersion).returns(String) }
    def state_preamble_adoc(version)
      case version.state
      when "ratified"
        <<~ADOC
          [WARNING]
          .This document is in the link:http://riscv.org/spec-state[Ratified state]
          ====
          No changes are allowed. Any desired or needed changes can be the subject of a
          follow-on new extension. Ratified extensions are never revised
          ====
        ADOC
      when "frozen"
        <<~ADOC
          [WARNING]
          This document is in the http://riscv.org/spec-state[Frozen state].
          ====
          Change is extremely unlikely.
          A high threshold will be used, and a change will only occur because of some truly
          critical issue being identified during the public review cycle.
          Any other desired or needed changes can be the subject of a follow-on new extension.
          ====
        ADOC
      when "development"
        <<~ADOC
          [WARNING]
          This document is in the http://riscv.org/spec-state[Development state].
          ====
          Change should be expected
          ====
        ADOC
      else
        raise "Unknown state: #{version.state}"
      end
    end

    sig { params(cfg_arch: Udb::ConfiguredArchitecture, adoc: String).returns(String) }
    def convert_monospace_to_links(cfg_arch, adoc)
      adoc.gsub(/`([\\w.]+)`/) do |match|
        name = Regexp.last_match(1)
        csr_name, field_name = T.must(name).split(".")
        csr = cfg_arch.not_prohibited_csrs.find { |c| c.name == csr_name }
        if !field_name.nil? && !csr.nil? && csr.field?(field_name)
          link_to(csr.field(field_name), match)
        elsif !csr.nil?
          link_to(csr, match)
        elsif cfg_arch.not_prohibited_instructions.any? { |inst| inst.name == name }
          link_to(cfg_arch.instruction(name), match)
        elsif cfg_arch.not_prohibited_extensions.any? { |ext| ext.name == name }
          link_to(cfg_arch.extension(name), match)
        else
          match
        end
      end
    end

    sig { params(cfg_arch: Udb::ConfiguredArchitecture, adoc: String).returns(String) }
    def resolve_intermediate_links(cfg_arch, adoc)
      adoc.gsub(/%%UDB_DOC_LINK%([^;%]+)\s*;\s*([^;%]+)\s*;\s*([^%]+)%%/) do |match|
        type = T.must(Regexp.last_match(1))
        name = T.must(Regexp.last_match(2))
        link_text = T.must(Regexp.last_match(3))

        case type
        when "ext"
          ext = cfg_arch.extension(name)
          if ext
            link_to(cfg_arch.extension(name), link_text)
          else
            Udb.logger.warn "Attempted link to undefined extension: #{name}"
            match
          end
        when "ext_param"
          param = cfg_arch.param(name)
          if param
            link_to(param, link_text)
          else
            Udb.logger.warn "Attempted link to undefined parameter: #{name}"
            match
          end
        when "inst"
          inst = cfg_arch.instruction(name)
          if inst
            link_to(inst, link_text)
          else
            Udb.logger.warn "Attempted link to undefined instruction: #{name}"
            match
          end
        when "csr"
          csr = cfg_arch.csr(name)
          if csr
            link_to(cfg_arch.csr(name), link_text)
          else
            Udb.logger.warn "Attempted link to undefined CSR: #{name}"
            match
          end
        when "csr_field"
          csr_name, field_name = name.split("*")
          csr = cfg_arch.csr(csr_name)
          if csr
            csr_field = csr.field(field_name)
            if csr_field
              link_to(csr_field, link_text)
            else
              Udb.logger.warn "Attempted link to undefined CSR field: #{name}"
              match
            end
          else
            Udb.logger.warn "Attempted link to undefined CSR: #{csr_name}"
            match
          end
        when "func"
          func = cfg_arch.function(name)
          if func
            link_to(func, link_text)
          else
            Udb.logger.warn "Attempted link to undefined function: #{name}"
            match
          end
        else
          raise "Unhandled link type of '#{type}' for '#{name}' with link_text '#{link_text}'"
        end
      end
    end
  end
end
