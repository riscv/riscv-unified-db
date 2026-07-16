#!/usr/bin/env ruby
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

# Smoke test for a *released* idlc/udb install — run this after `gem install`,
# never via bundle/rake, and never from inside a repo checkout that the gem's
# dev-mode fallback paths could see (that would silently mask exactly the bug
# this exists to catch). CI runs it from a container that only has the built
# .gem files installed, no repo checkout of tools/node/.
#
# Exists because idlc.gemspec has two independent ways to package the native
# tree-sitter grammar (see its own comments): a "platform gem" that bundles a
# precompiled libtree-sitter-idl.so directly, and a "source gem" that ships
# ext/idlc/extconf.rb to download or compile it at install time. Both must
# still carry Idl::Formatter's Topiary queries and reflow script and be able
# to parse IDL — nothing here assumes which packaging path installed it.
#
# Usage: ruby gem_install_smoke_test.rb
# Exit status: 0 if every check passes, 1 otherwise.

require "idlc"
require "udb"
require "pathname"

class SkipCheck < StandardError; end

failures = []
skips = []
def check(name)
  yield
  puts "PASS: #{name}"
rescue SkipCheck => e
  puts "SKIP: #{name} — #{e.message}"
  $skips << name
rescue => e
  puts "FAIL: #{name} — #{e.class}: #{e.message}"
  $failures << name
end
$failures = []
$skips = []

check("Idl::Formatter actually reformats IDL (Topiary queries + idl-reflow present)") do
  # Idl::Formatter shells out to bare "topiary" (and, for the reflow pass,
  # bare "node") on PATH — a real dependency any consumer of this gem is
  # expected to provide themselves, not something the gem's packaging
  # controls. If neither is installed on this system, skip rather than fail:
  # the QUERY_DIR check right below already verifies the actual packaging
  # concern (review comment #11) without needing Topiary to be runnable.
  unless system("topiary", "--version", out: File::NULL, err: File::NULL)
    raise SkipCheck, "'topiary' not found on PATH (external dependency, not a packaging issue)"
  end
  unless system("node", "--version", out: File::NULL, err: File::NULL)
    raise SkipCheck, "'node' not found on PATH (needed for the reflow pass; external dependency)"
  end

  # A bare statement, not a full function+%version document — this mirrors
  # Formatter's real input shape (regenerated source from AstNode#to_idl /
  # YAML operation() snippets), which Topiary's "idl" grammar parses as a
  # statement list, not a top-level ISA document.
  unformatted = "if(a){b=1;}else{b=2;}"
  formatted = Idl::Formatter.format(unformatted, column_width: 100)
  raise "output identical to input — formatter silently no-op'd" if formatted == unformatted
  raise "output doesn't look like IDL" unless formatted.include?("if")
  puts "    got:\n#{formatted.gsub(/^/, '    ')}"
end

check("Idl::Formatter::QUERY_DIR resolves inside the installed gem, not a repo checkout") do
  dir = Idl::Formatter::QUERY_DIR
  raise "QUERY_DIR is nil" if dir.nil?
  raise "QUERY_DIR (#{dir}) points at a repo checkout path, not the installed gem" \
    if dir.include?("tools/node") || dir.include?("tools" + File::SEPARATOR + "node")
  puts "    QUERY_DIR = #{dir}"
end

check("idlc's own parser (TsParser/ruby_tree_sitter) works from the installed gem") do
  idl = <<~IDL
    %version: 1.0

    function add_one {
      returns Bits<32>
      arguments Bits<32> a
      description {
        Adds one to a.
      }
      body {
        return a + 1;
      }
    }
  IDL
  path = Pathname.new(File.join(Dir.mktmpdir, "smoke.idl"))
  path.write(idl)
  ast = Idl::Compiler.new.compile_file(path)
  raise "compile_file returned nil" if ast.nil?
  fn = ast.functions.find { |f| f.name == "add_one" }
  raise "function add_one not found in parsed AST" if fn.nil?
end

check("udb loads and exposes a version") do
  raise "Udb.version is blank" if Udb.version.to_s.strip.empty?
  puts "    udb #{Udb.version}"
end

check("udb resolves real bundled configs end-to-end (compile_file cache safety)") do
  # tasks.rake stages spec/std, spec/custom, spec/schemas, cfgs into the gem's
  # own .data/ dir (see release:udb:prepare's after_copy). With no repo
  # checkout reachable, Udb.repo_root is nil and Udb.default_*_path all
  # resolve into that bundled .data/ dir automatically — this uses ONLY what's
  # inside the installed gem.
  require "udb/resolver"
  raise "Udb.repo_root resolved to a real path (#{Udb.repo_root}) — run this " \
        "where no repo checkout is reachable for this check to be meaningful" \
    unless Udb.repo_root.nil?

  resolver = Udb::Resolver.new(nil, quiet: true)
  names = Dir.glob(resolver.cfgs_path / "*.yaml").map { |f| File.basename(f, ".yaml") }
  raise "no bundled configs found under #{resolver.cfgs_path}" if names.empty?
  first, second = names.first(2)
  raise "need at least 2 bundled configs to exercise the shared-cache fix " \
        "(found: #{names.inspect})" if second.nil?

  # Resolve two different configs in-process: Idl::Compiler#compile_file's
  # class-level parse cache must not hand back a shared, already-frozen AST
  # for a globals.isa both configs include unmodified — otherwise the second
  # config would silently inherit the first config's resolved symbol table.
  cfg_arch_1 = resolver.cfg_arch_for(first)
  cfg_arch_2 = resolver.cfg_arch_for(second)
  ast_1 = cfg_arch_1.global_ast
  ast_2 = cfg_arch_2.global_ast
  # Force resolution (this is what would previously freeze a *shared* AST).
  cfg_arch_1.symtab
  cfg_arch_2.symtab
  raise "global_ast was shared across two different configs (#{first}, #{second})" \
    if ast_1.equal?(ast_2)
  puts "    resolved #{first} and #{second} with independent ASTs"
end

unless $skips.empty?
  puts "\n#{$skips.size} CHECK(S) SKIPPED: #{$skips.join(', ')}"
end

if $failures.empty?
  puts "\nALL SMOKE CHECKS PASSED#{" (#{$skips.size} skipped)" unless $skips.empty?}"
  exit 0
else
  puts "\n#{$failures.size} CHECK(S) FAILED: #{$failures.join(', ')}"
  exit 1
end
