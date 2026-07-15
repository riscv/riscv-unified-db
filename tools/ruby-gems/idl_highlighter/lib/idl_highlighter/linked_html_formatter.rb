# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: ignore
# frozen_string_literal: true

require "rouge"
require "cgi"
require "idl_highlighter"

module IdlHighlighter
  # Formats IDL source as syntax-highlighted HTML, with optional hyperlinks on
  # identifiers.  Unlike a plain Rouge HTML formatter, this lets callsites
  # embed <a href> elements inside the highlighted code block so that both
  # highlighting and cross-references work simultaneously.
  module LinkedHtmlFormatter
    # @param idl_source [String] IDL source code
    # @param link_map [Hash{String => String}] maps identifier name to href string;
    #   identifiers found in the map are wrapped in <a href> elements
    # @return [String] complete highlighted HTML fragment, ready for ++++  passthrough
    def self.format(idl_source, link_map = {})
      lexer = Rouge::Lexers::Idl.new
      inner = lexer.lex(idl_source).map do |token, chunk|
        escaped = CGI.escapeHTML(chunk)
        css_class = token.shortname

        if token == Rouge::Token::Tokens::Name && (href = link_map[chunk])
          %(<a href="#{href}"><span class="#{css_class}">#{escaped}</span></a>)
        elsif css_class.empty?
          escaped
        else
          %(<span class="#{css_class}">#{escaped}</span>)
        end
      end.join

      %(<pre class="rouge highlight"><code class="language-idl hljs">#{inner}</code></pre>)
    end
  end
end
