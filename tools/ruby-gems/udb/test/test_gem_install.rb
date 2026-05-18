# typed: false
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require_relative "test_helper"

require "fileutils"
require "open3"
require "tmpdir"
require "pathname"

# Tests that the udb gem can be built with bundled data and installed in a
# sandbox outside the monorepo, and that the CLI still works correctly.
class TestGemInstall < Minitest::Test
  UDB_GEM_DIR = (Pathname.new(__dir__) / "..").realpath
  REPO_ROOT = (UDB_GEM_DIR / ".." / ".." / "..").realpath

  # Replicate the logic of the release:udb:prepare Rake task directly in Ruby
  # so we don't need to spawn a subprocess (which would fight with bundler).
  def prepare_gem_staging(staging)
    staging = Pathname.new(staging)
    udb_gem_src = UDB_GEM_DIR

    # Before copying, record the realpath of each top-level symlink in the source
    # so we can resolve them after the copy (the symlinks point into the monorepo
    # and would be broken at a different directory depth).
    symlink_targets = {}
    udb_gem_src.children.select(&:symlink?).each do |s|
      symlink_targets[s.basename.to_s] = s.realpath
    end

    # Copy the gem source directory contents into staging (symlinks are copied as symlinks).
    # We copy children individually so the contents land directly in staging/
    # rather than in staging/udb/ (which is what cp_r does when dst already exists).
    FileUtils.cp_r(udb_gem_src.children.map(&:to_s), staging.to_s)

    # Remove Gemfile and Gemfile.lock from the staging directory.
    # These reference local gem paths (../idlc, ../udb_helpers) that only
    # exist inside the monorepo and would cause `gem build` to fail elsewhere.
    FileUtils.rm_f(staging / "Gemfile")
    FileUtils.rm_f(staging / "Gemfile.lock")

    # Resolve (or remove) each top-level symlink in the copy
    symlink_targets.each do |name, target|
      dst_entry = staging / name
      FileUtils.rm_rf(dst_entry)
      # Skip entries whose target doesn't exist (e.g. ext/rbi-central when
      # the submodule isn't checked out) and the schemas symlink (not needed
      # in the gem; data is under .data/ instead)
      next unless target.exist?
      next if name == "schemas"

      if target.directory?
        FileUtils.cp_r(target, dst_entry)
      else
        FileUtils.cp(target, dst_entry)
      end
    end

    # Populate .data/ with the required data files from the monorepo
    data_dir = staging / ".data"
    {
      (REPO_ROOT / "spec" / "std" / "isa")    => (data_dir / "spec" / "std" / "isa"),
      (REPO_ROOT / "spec" / "custom" / "isa") => (data_dir / "spec" / "custom" / "isa"),
      (REPO_ROOT / "spec" / "schemas")        => (data_dir / "spec" / "schemas"),
      (REPO_ROOT / "cfgs")                    => (data_dir / "cfgs")
    }.each do |src, dst|
      FileUtils.mkdir_p(dst.dirname)
      FileUtils.cp_r(src, dst)
    end
  end

  # Prepare a staging copy of the gem, build it, install it into a temporary
  # sandbox, and verify that `udb list extensions` produces expected output.
  def test_list_extensions_from_installed_gem
    Dir.mktmpdir("udb_gem_install_test") do |sandbox_dir|
      sandbox = Pathname.new(sandbox_dir)

      Dir.mktmpdir("udb_gem_staging") do |staging_dir|
        staging = Pathname.new(staging_dir)

        # Populate the staging directory with the gem source + .data/
        prepare_gem_staging(staging)

        # Verify the .data directory was populated
        assert (staging / ".data" / "spec" / "std" / "isa").directory?,
          "Expected .data/spec/std/isa to exist in the staging gem"
        assert (staging / ".data" / "spec" / "custom" / "isa").directory?,
          "Expected .data/spec/custom/isa to exist in the staging gem"
        assert (staging / ".data" / "spec" / "schemas").directory?,
          "Expected .data/spec/schemas to exist in the staging gem"
        assert (staging / ".data" / "cfgs").directory?,
          "Expected .data/cfgs to exist in the staging gem"

        # Build the gem from the staging directory.
        # Unset BUNDLE_GEMFILE so bundler doesn't interfere with gem build.
        build_out, build_err, build_status = Open3.capture3(
          { "BUNDLE_GEMFILE" => nil },
          "gem", "build", "udb.gemspec",
          chdir: staging.to_s
        )
        assert build_status.success?,
          "gem build failed:\nSTDOUT: #{build_out}\nSTDERR: #{build_err}"

        gem_filename = build_out.match(/File: (.+\.gem)/)[1]
        gem_file = staging / gem_filename

        # Install the gem into the sandbox (without dependencies — they are
        # available via GEM_PATH from the current Ruby environment).
        # Unset BUNDLE_GEMFILE so bundler doesn't interfere with gem install.
        install_out, install_err, install_status = Open3.capture3(
          { "BUNDLE_GEMFILE" => nil },
          "gem", "install", gem_file.to_s,
          "--install-dir", sandbox.to_s,
          "--no-document",
          "--ignore-dependencies"
        )
        assert install_status.success?,
          "gem install failed:\nSTDOUT: #{install_out}\nSTDERR: #{install_err}"

        # Run `udb list extensions` from the sandbox.
        # GEM_HOME=sandbox  → the udb gem (with .data/) is loaded from the sandbox
        # GEM_PATH=sandbox:...current paths  → dependencies are found in the current env
        # UDB_ROOT is intentionally NOT set so the gem uses .data/ for its paths
        # BUNDLE_GEMFILE is unset so bundler doesn't interfere
        env = {
          "GEM_HOME" => sandbox.to_s,
          "GEM_PATH" => ([sandbox.to_s] + Gem.path).join(File::PATH_SEPARATOR),
          "BUNDLE_GEMFILE" => nil
        }
        udb_bin = sandbox / "bin" / "udb"
        stdout, stderr, status = Open3.capture3(env, udb_bin.to_s, "list", "extensions")

        assert status.success?,
          "udb list extensions failed:\nSTDOUT: #{stdout}\nSTDERR: #{stderr}"
        assert_match(/Zvkg/, stdout,
          "Expected 'Zvkg' in output of `udb list extensions`")
      end
    end
  end
end
