# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require "open3"
require "tmpdir"

module Idl
  # Formats IDL source strings using the Topiary formatter (same tool as
  # bin/idl-format), with optional line-length reflow for narrow outputs
  # such as documentation PDFs.
  #
  # Formatting is a 1- or 3-pass pipeline:
  #   1. topiary format   — canonical spacing/indentation
  #   2. node reflow.js   — break long lines at semantic break points (only
  #                         when column_width: is given)
  #   3. topiary format   — re-indent after reflow (only when reflow ran)
  #
  # All passes use stdin→stdout so no temp files are needed.
  #
  # Path resolution mirrors TsParser: checks the installed gem's lib/idlc/
  # first (where the platform gem bundles the artifacts), then falls back to
  # the in-repo tree-sitter-idl/idl-reflow trees for dev-mode use.
  module Formatter
    # Grammar .so — same search order as TsParser::LIB_PATH.
    _gem_so = Gem.loaded_specs["idlc"]&.full_gem_path&.then do |p|
      File.join(p, "lib/idlc/libtree-sitter-idl.so")
    end
    _repo_so = File.expand_path(
      "../../../../../tools/node/tree-sitter-idl/libtree-sitter-idl.so",
      __dir__
    )
    GRAMMAR_SO = [_gem_so, _repo_so].compact.find { |p| File.exist?(p) }

    # Topiary queries directory (contains idl.scm).
    _gem_queries = Gem.loaded_specs["idlc"]&.full_gem_path&.then do |p|
      File.join(p, "lib/idlc/queries")
    end
    _repo_queries = File.expand_path(
      "../../../../../tools/node/tree-sitter-idl/queries",
      __dir__
    )
    QUERY_DIR = [_gem_queries, _repo_queries].compact.find { |p| File.exist?(p) }

    # Reflow script — bundled in gem at lib/idlc/idl-reflow/index.js,
    # or found in the repo's tools/node/idl-reflow/ tree for dev mode.
    _gem_reflow = Gem.loaded_specs["idlc"]&.full_gem_path&.then do |p|
      File.join(p, "lib/idlc/idl-reflow/index.js")
    end
    _repo_reflow = File.expand_path(
      "../../../../../tools/node/idl-reflow/index.js",
      __dir__
    )
    REFLOW_JS = [_gem_reflow, _repo_reflow].compact.find { |p| File.exist?(p) }

    # Node.js binary.  Prefer the repo's bin/node (mise-managed) in dev mode;
    # fall back to bare "node" in PATH for gem release contexts.
    _repo_node = File.expand_path("../../../../../bin/node", __dir__)
    NODE_BIN = File.exist?(_repo_node) ? _repo_node : "node"

    class << self
      # Format an IDL source string.
      #
      # @param idl_source [String]  raw IDL (e.g. from AstNode#to_idl)
      # @param column_width [Integer, nil]  when set, runs the reflow pass to
      #   break lines longer than this many columns at semantic break points,
      #   followed by a second topiary pass to re-indent.  Nil skips reflow.
      # @return [String] formatted IDL, or the original string on failure
      def format(idl_source, column_width: nil)
        return idl_source if idl_source.strip.empty?
        return idl_source if GRAMMAR_SO.nil? || QUERY_DIR.nil?

        config_path = topiary_config_path
        return idl_source if config_path.nil?

        # Topiary requires a trailing newline to emit formatted output correctly.
        input = idl_source.end_with?("\n") ? idl_source : "#{idl_source}\n"

        env = { "TOPIARY_LANGUAGE_DIR" => QUERY_DIR.to_s }
        topiary_cmd = ["topiary", "--configuration", config_path, "format", "--language", "idl"]

        # Pass 1: canonical spacing/indentation.
        # Capture stderr to suppress topiary parse-error noise on input it can't
        # fully parse (e.g., CSR method-call syntax not yet in the grammar).
        # Fallback to the original string on any error; the caller still gets
        # syntactically valid IDL — just unformatted.
        pass1, _err, status = Open3.capture3(env, *topiary_cmd, stdin_data: input)
        return idl_source unless status.success?

        if column_width && REFLOW_JS
          unless node_available?
            hint = NODE_BIN == "node" ? "install Node.js to enable line reflow" \
                                      : "run `bin/mise install` to enable line reflow"
            warn "idl-format: 'node' not found — #{hint}; falling back to unflowed output"
            return pass1.rstrip
          end

          # Pass 2: break long lines at semantic break points
          pass2, status = Open3.capture2(NODE_BIN, REFLOW_JS, column_width.to_s,
                                         stdin_data: pass1)
          return pass1.rstrip unless status.success?

          # Pass 3: re-indent after reflow (stderr suppressed, same fallback policy)
          pass3, _err, status = Open3.capture3(env, *topiary_cmd, stdin_data: pass2)
          return pass2.rstrip unless status.success?

          pass3.rstrip
        else
          pass1.rstrip
        end
      rescue Errno::ENOENT
        idl_source
      end

      private

      def node_available?
        return @node_available unless @node_available.nil?

        @node_available = system(NODE_BIN, "--version", out: File::NULL, err: File::NULL)
      rescue Errno::ENOENT
        @node_available = false
      end

      def topiary_config_path
        @topiary_config_path ||= begin
          return nil if GRAMMAR_SO.nil?

          path = File.join(Dir.tmpdir, "topiary-idl-#{Process.pid}.ncl")
          File.write(path, <<~NCL)
            {
              languages = {
                idl = {
                  extensions | default = ["idl", "isa"],
                  indent | default = "  ",
                  grammar.source | default = {
                    path = "#{GRAMMAR_SO}",
                  },
                },
              },
            }
          NCL
          at_exit { File.delete(path) rescue nil }
          path
        end
      end
    end
  end
end
