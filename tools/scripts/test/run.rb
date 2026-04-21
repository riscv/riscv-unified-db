# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require "minitest/autorun"
require "pathname"
require "tmpdir"
require "fileutils"

# Load parse_gem_metadata without running the main block.
# gen_gem_versions.rb guards its main block with `if __FILE__ == $PROGRAM_NAME`,
# so requiring it here is safe.
require_relative "../gen_gem_versions"

UDB_ROOT_REAL = Pathname.new(__FILE__).dirname.parent.parent.parent.realpath

# ---------------------------------------------------------------------------
# Helpers to build a minimal fake gem tree inside a tmpdir
# ---------------------------------------------------------------------------
module FakeGemTree
  # Build a fake gem directory with a .gemspec (Gemfile is no longer required for discovery).
  # deps is a hash of { gem_name => version_constraint_string }
  def self.make_gem(root, name:, version: "1.0.0", deps: {}, has_spec_dir: false)
    dir = root / "tools" / "ruby-gems" / name
    FileUtils.mkdir_p(dir / "lib" / name)

    # version.rb
    File.write(dir / "lib" / name / "version.rb", <<~RUBY)
      # frozen_string_literal: true
      module #{name.gsub("-", "_").split("_").map(&:capitalize).join}
        VERSION = "#{version}"
        def self.version = VERSION
      end
    RUBY

    # gemspec
    File.write(dir / "#{name}.gemspec", <<~RUBY)
      # frozen_string_literal: true
      require_relative "lib/#{name}/version"
      Gem::Specification.new do |s|
        s.name    = "#{name}"
        s.version = #{name.gsub("-", "_").split("_").map(&:capitalize).join}.version
        s.summary = "fake #{name}"
        s.required_ruby_version = ">= 3.0"
        #{deps.map { |dep, constraint| "s.add_dependency \"#{dep}\", \"#{constraint}\"" }.join("\n  ")}
      end
    RUBY

    FileUtils.mkdir_p(dir / "spec") if has_spec_dir

    dir
  end
end

# ---------------------------------------------------------------------------
# Tests for parse_gem_metadata
# ---------------------------------------------------------------------------
class TestParseGemMetadata < Minitest::Test
  # ------------------------------------------------------------------
  # Test against the real repo so we catch regressions against actual gemspecs
  # ------------------------------------------------------------------

  def test_real_repo_gem_names
    metadata = parse_gem_metadata(UDB_ROOT_REAL)
    names = metadata[:gems].map { |g| g[:name] }.sort
    assert_equal %w[idl_highlighter idlc udb udb-gen udb_helpers], names
  end

  def test_real_repo_includes_idl_highlighter
    # idl_highlighter has a gemspec but no Gemfile; it must now be included
    # since gem discovery is driven by gemspecs, not Gemfiles.
    metadata = parse_gem_metadata(UDB_ROOT_REAL)
    names = metadata[:gems].map { |g| g[:name] }
    assert_includes names, "idl_highlighter"
  end

  def test_real_repo_gem_dirs
    metadata = parse_gem_metadata(UDB_ROOT_REAL)
    dirs = metadata[:gems].map { |g| g[:dir] }.sort
    assert_equal [
      "tools/ruby-gems/idl_highlighter",
      "tools/ruby-gems/idlc",
      "tools/ruby-gems/udb",
      "tools/ruby-gems/udb-gen",
      "tools/ruby-gems/udb_helpers"
    ], dirs
  end

  def test_real_repo_version_files
    metadata = parse_gem_metadata(UDB_ROOT_REAL)
    by_name = metadata[:gems].each_with_object({}) { |g, h| h[g[:name]] = g[:version_file] }
    assert_equal "tools/ruby-gems/idlc/lib/idlc/version.rb",           by_name["idlc"]
    assert_equal "tools/ruby-gems/udb/lib/udb/version.rb",             by_name["udb"]
    assert_equal "tools/ruby-gems/udb-gen/lib/udb-gen/version.rb",     by_name["udb-gen"]
    assert_equal "tools/ruby-gems/udb_helpers/lib/udb_helpers/version.rb", by_name["udb_helpers"]
  end

  def test_real_repo_dependents
    metadata = parse_gem_metadata(UDB_ROOT_REAL)
    deps = metadata[:dependents]
    # idlc and udb_helpers are depended on by udb
    assert_includes deps["idlc"],        "udb"
    assert_includes deps["udb_helpers"], "udb"
    # udb is depended on by udb-gen
    assert_includes deps["udb"], "udb-gen"
    # udb-gen has no dependents
    assert_empty deps["udb-gen"]
  end

  def test_real_repo_gemspec_pins
    metadata = parse_gem_metadata(UDB_ROOT_REAL)
    pins = metadata[:gemspec_pins]
    pin_pairs = pins.map { |p| [p[:gemspec], p[:dep_name]] }.sort
    assert_includes pin_pairs, ["tools/ruby-gems/udb/udb.gemspec",         "idlc"]
    assert_includes pin_pairs, ["tools/ruby-gems/udb/udb.gemspec",         "udb_helpers"]
    assert_includes pin_pairs, ["tools/ruby-gems/udb-gen/udb-gen.gemspec", "udb"]
  end

  def test_real_repo_gemfiles_single_root
    metadata = parse_gem_metadata(UDB_ROOT_REAL)
    gemfiles = metadata[:gemfiles]
    # With a single root Gemfile, there is exactly one entry: the root Gemfile
    assert_equal ["Gemfile"], gemfiles
  end

  def test_real_repo_gems_have_no_gemspec_path_key
    # The public :gems array must not expose :gemspec_path (internal detail)
    metadata = parse_gem_metadata(UDB_ROOT_REAL)
    metadata[:gems].each do |g|
      refute g.key?(:gemspec_path), "gem #{g[:name]} should not expose :gemspec_path"
    end
  end

  # ------------------------------------------------------------------
  # Synthetic tests using a fake gem tree in a tmpdir
  # ------------------------------------------------------------------

  def setup
    @tmpdir = Pathname.new(Dir.mktmpdir("gen_gem_versions_test"))
    FileUtils.mkdir_p(@tmpdir / "tools" / "ruby-gems")
  end

  def teardown
    FileUtils.remove_entry(@tmpdir)
  end

  def test_single_gem_no_deps
    FakeGemTree.make_gem(@tmpdir, name: "alpha")
    metadata = parse_gem_metadata(@tmpdir)

    assert_equal 1, metadata[:gems].size
    gem = metadata[:gems].first
    assert_equal "alpha",                                    gem[:name]
    assert_equal "tools/ruby-gems/alpha",                   gem[:dir]
    assert_equal "tools/ruby-gems/alpha/lib/alpha/version.rb", gem[:version_file]
    assert_equal [],                                         gem[:additional_dirs]
    assert_empty metadata[:dependents]["alpha"]
    assert_empty metadata[:gemspec_pins]
    assert_equal ["Gemfile"], metadata[:gemfiles]
  end

  def test_spec_dir_sets_additional_dirs
    FakeGemTree.make_gem(@tmpdir, name: "beta", has_spec_dir: true)
    metadata = parse_gem_metadata(@tmpdir)
    gem = metadata[:gems].find { |g| g[:name] == "beta" }
    # additional_dirs must be repo-root-relative so they can be matched directly
    # against paths from `git diff --name-only`
    assert_equal ["tools/ruby-gems/beta/spec"], gem[:additional_dirs]
  end

  def test_no_spec_dir_gives_empty_additional_dirs
    FakeGemTree.make_gem(@tmpdir, name: "gamma")
    metadata = parse_gem_metadata(@tmpdir)
    gem = metadata[:gems].find { |g| g[:name] == "gamma" }
    assert_equal [], gem[:additional_dirs]
  end

  def test_local_dependency_builds_dependents_and_pins
    FakeGemTree.make_gem(@tmpdir, name: "base")
    FakeGemTree.make_gem(@tmpdir, name: "consumer", deps: { "base" => "= 1.0.0" })

    metadata = parse_gem_metadata(@tmpdir)

    # dependents: base is depended on by consumer
    assert_includes metadata[:dependents]["base"], "consumer"
    assert_empty    metadata[:dependents]["consumer"]

    # gemspec_pins: one pin entry for consumer -> base
    assert_equal 1, metadata[:gemspec_pins].size
    pin = metadata[:gemspec_pins].first
    assert_equal "tools/ruby-gems/consumer/consumer.gemspec", pin[:gemspec]
    assert_equal "base",                                       pin[:dep_name]
    assert_equal "base",                                       pin[:version_gem]
  end

  def test_external_dependency_not_in_pins
    FakeGemTree.make_gem(@tmpdir, name: "solo", deps: { "activesupport" => ">= 6" })
    metadata = parse_gem_metadata(@tmpdir)
    assert_empty metadata[:gemspec_pins]
    assert_empty metadata[:dependents]["solo"]
  end

  def test_gemfiles_topological_order_chain
    # chain: leaf -> middle -> top
    FakeGemTree.make_gem(@tmpdir, name: "leaf")
    FakeGemTree.make_gem(@tmpdir, name: "middle", deps: { "leaf" => "= 1.0.0" })
    FakeGemTree.make_gem(@tmpdir, name: "top",    deps: { "middle" => "= 1.0.0" })

    metadata = parse_gem_metadata(@tmpdir)
    # With a single root Gemfile, gemfiles is always just ["Gemfile"]
    assert_equal ["Gemfile"], metadata[:gemfiles]
  end

  def test_gemfiles_root_always_last
    FakeGemTree.make_gem(@tmpdir, name: "x")
    FakeGemTree.make_gem(@tmpdir, name: "y")
    metadata = parse_gem_metadata(@tmpdir)
    assert_equal "Gemfile", metadata[:gemfiles].last
  end

  def test_diamond_dependency
    # diamond: a and b both depend on base; top depends on a and b
    FakeGemTree.make_gem(@tmpdir, name: "base")
    FakeGemTree.make_gem(@tmpdir, name: "a",   deps: { "base" => "= 1.0.0" })
    FakeGemTree.make_gem(@tmpdir, name: "b",   deps: { "base" => "= 1.0.0" })
    FakeGemTree.make_gem(@tmpdir, name: "top", deps: { "a" => "= 1.0.0", "b" => "= 1.0.0" })

    metadata = parse_gem_metadata(@tmpdir)

    # With a single root Gemfile, gemfiles is always just ["Gemfile"]
    assert_equal ["Gemfile"], metadata[:gemfiles]

    # dependents of base includes both a and b
    assert_includes metadata[:dependents]["base"], "a"
    assert_includes metadata[:dependents]["base"], "b"
  end

  def test_gems_array_does_not_expose_gemspec_path
    FakeGemTree.make_gem(@tmpdir, name: "hidden")
    metadata = parse_gem_metadata(@tmpdir)
    metadata[:gems].each do |g|
      refute g.key?(:gemspec_path), "gems array must not expose :gemspec_path"
    end
  end
end
