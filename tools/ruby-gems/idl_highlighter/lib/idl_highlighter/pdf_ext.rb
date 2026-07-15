# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: ignore
# frozen_string_literal: true

# Extended asciidoctor-pdf converter that renders [source,idl,idl-links="..."]
# code blocks with simultaneous syntax highlighting and hyperlinks.
#
# For blocks without the idl-links attribute, delegates to super unchanged.
# For blocks with idl-links, patches the Rouge Prawn formatter on the current
# call to inject :anchor keys into fragments for identifiers in the link map,
# then calls super so all whitespace handling, padding, and layout remain
# identical to the standard code block rendering.
#
# Load with: asciidoctor-pdf -r idl_highlighter/pdf_ext ...

require "rouge"
require "idl_highlighter"

class IdlPdfConverter < (Asciidoctor::Converter.for "pdf")
  register_for "pdf"

  def convert_code(node)
    idl_links = node.attr("idl-links")
    return super unless node.attr("language") == "idl" && idl_links && !idl_links.empty?

    link_map = idl_links.split(",").each_with_object({}) do |pair, h|
      name, anchor = pair.split("=", 2)
      h[name.strip] = anchor.strip if name && anchor
    end

    require "asciidoctor/pdf/ext/rouge/formatters/prawn" unless defined?(Rouge::Formatters::Prawn)

    # Ensure the formatter is initialized so we can patch it before super runs.
    @rouge_formatter ||= Rouge::Formatters::Prawn.new(
      theme: (node.document.attr "rouge-style"),
      line_gap: @theme.code_line_gap,
      highlight_background_color: @theme.code_highlight_background_color
    )

    formatter = @rouge_formatter
    original_format = formatter.method(:format)

    # Temporarily replace format on this formatter instance to inject :anchor
    # keys into fragments for identifiers listed in the link map.
    formatter.define_singleton_method(:format) do |token_enum, opts = {}|
      original_format.call(token_enum, opts).tap do |frags|
        frags.each do |frag|
          next unless frag[:text] && (anchor = link_map[frag[:text]])
          frag[:anchor] = anchor
        end
      end
    end

    super
  ensure
    formatter&.singleton_class&.remove_method(:format) rescue nil
  end
end
