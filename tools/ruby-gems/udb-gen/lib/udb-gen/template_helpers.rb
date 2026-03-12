# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "sorbet-runtime"

require_relative "adoc_helpers"

module UdbGen
  module TemplateHelpers
    extend T::Sig
    include Kernel
    include AdocHelpers

    sig { params(template_pname: String, inputs: T::Hash[Symbol, T.untyped]).returns(String) }
    def partial(template_pname, inputs = {})
      template_path = Pathname.new(__dir__) / ".." / ".." / "templates" / template_pname
      raise ArgumentError, "Template '#{template_path} not found" unless template_path.exist?

      erb = ERB.new(template_path.read, trim_mode: "-")
      erb.filename = template_path.realpath.to_s

      context = OpenStruct.new(inputs)
      context.singleton_class.include(TemplateHelpers)
      erb.result(context.instance_eval { binding })
    end

    LinkableObj = T.type_alias { T.any(Udb::Instruction, Udb::Csr, Udb::CsrField, Idl::FunctionDefAst) }

    # return an asciidoc link to obj, with text "text"
    sig { params(obj: LinkableObj, text: String).returns(String) }
    def link_to(obj, text = obj.name)
      # link on the same page
      "xref:##{link_name(obj)}[#{text}]"
    end

    # return an asciidoc anchor for obj
    sig { params(obj: LinkableObj).returns(String) }
    def anchor_for(obj)
      "[##{link_name(obj)}]"
    end

    # return an asciidoc link to obj, with text "text"
    sig { params(obj: LinkableObj).returns(String) }
    def link_name(obj)
      case obj
      when Udb::Instruction
        "udb-insn-#{obj.name.gsub(".", "_")}"
      when Udb::Csr
        "udb-csr-#{obj.name.gsub(".", "_")}"
      when Udb::CsrField
        "udb-csrfield-#{obj.parent.name.gsub(".", "_")}-#{obj.name.gsub(".", "_")}"
      when Idl::FunctionDefAst
        "udb-function-#{obj.name.gsub(".", "_")}"
      else
        T.absurd(obj)
      end
    end
  end
end
