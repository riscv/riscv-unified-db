# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require "pathname"
require "tree_sitter"

module Idl
  module TsParser
    # Absolute path to the compiled IDL language shared library.
    #
    # Search order:
    #   1. lib/idlc/ within the installed gem (platform gem bundles it there;
    #      source gem's extconf.rb compiles it there at install time)
    #   2. Repo dev mode fallback: the Node project's pre-compiled .so, reached
    #      via __dir__ when loaded via `gemspec path:` in the repo Gemfile
    _gem_lib_so = Gem.loaded_specs["idlc"]&.full_gem_path&.then do |p|
      File.join(p, "lib/idlc/libtree-sitter-idl.so")
    end
    _repo_so = File.expand_path(
      "../../../../../tools/node/tree-sitter-idl/libtree-sitter-idl.so",
      __dir__
    )
    LIB_PATH = [_gem_lib_so, _repo_so].compact.find { |p| File.exist?(p) }.freeze
    raise "Cannot find libtree-sitter-idl.so (searched: #{[_gem_lib_so, _repo_so].compact.join(", ")})" if LIB_PATH.nil?

    @language = nil
    @language_mutex = Mutex.new

    def self.language
      @language_mutex.synchronize do
        @language ||= TreeSitter::Language.load("idl", LIB_PATH.to_s)
      end
    end

    # Returns an array of error records for any ERROR or MISSING nodes found
    # in the parse tree. Returns an empty array when the source is valid.
    #
    # Each record is a Hash with:
    #   :type        => :error | :missing
    #   :line        => Integer (1-based)
    #   :col         => Integer (1-based)
    #   :end_line    => Integer (1-based)
    #   :end_col     => Integer (1-based)
    #   :token_type  => String  (tree-sitter node type; for :missing, names expected token)
    #   :parent_type => String  (parent node type; context for :error nodes)
    def self.check_errors(source, root: :auto)
      parser = TreeSitter::Parser.new
      parser.language = language
      tree = parser.parse_string(nil, source)
      collect_errors(tree.root_node, [])
    end

    # Formats an error-record array into a multi-line CLI message.
    #
    # @param source       [String]  the source string that was parsed
    # @param errors       [Array]   records returned by check_errors
    # @param filename     [String]  file path shown in the message header
    # @param starting_line [Integer] 0-based line offset for embedded snippets
    #                               (e.g. 10 means source line 1 maps to file line 11)
    # @return [String]
    def self.format_errors(source, errors, filename:, starting_line: 0)
      lines = source.lines
      errors.map do |err|
        absolute_line = err[:line] + starting_line
        header = "#{filename}:#{absolute_line}:#{err[:col]}"
        detail = if err[:type] == :missing
          "expected #{err[:token_type]}"
        else
          "unexpected token in #{err[:parent_type] || "unknown context"}"
        end
        context = source_context(lines, err[:line] - 1, err[:col] - 1)
        "#{header}: #{detail}\n#{context}"
      end.join("\n")
    end

    def self.collect_errors(node, errors)
      return errors if node.nil? || node.null?

      if node.missing?
        errors << build_record(node, :missing)
      elsif node.error?
        errors << build_record(node, :error)
      end

      node.child_count.times do |i|
        collect_errors(node.child(i), errors)
      end

      errors
    end

    CONTEXT_RADIUS = 2

    def self.source_context(lines, error_row, error_col)
      first = [error_row - CONTEXT_RADIUS, 0].max
      last  = [error_row + CONTEXT_RADIUS, lines.size - 1].min
      result = (first..last).map do |i|
        prefix = i == error_row ? ">" : " "
        "#{prefix} #{i + 1} | #{lines[i].chomp}"
      end
      result << "  #{" " * (error_col + 4)}^"
      result.join("\n")
    end

    def self.build_record(node, type)
      sp = node.start_point
      ep = node.end_point
      parent_type = (!node.parent.nil? && !node.parent.null?) ? node.parent.type : nil
      {
        type:        type,
        line:        sp.row + 1,
        col:         sp.column + 1,
        end_line:    ep.row + 1,
        end_col:     ep.column + 1,
        token_type:  node.type,
        parent_type: parent_type
      }
    end
  end
end
