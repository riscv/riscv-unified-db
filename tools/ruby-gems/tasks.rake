# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# frozen_string_literal: true

require "pathname"
require "fileutils"

# Release tasks and gem-specific chore/test tasks for tools/ruby-gems/*.
# $root is the project root, already set by the top-level Rakefile.

# ── idlc ──────────────────────────────────────────────────────────────────

namespace :release do
  namespace :idlc do
    desc "Prepare a copy of the idlc gem for release under gen/idlc_gem (or IDLC_GEM_GEN_DIR)"
    task :prepare do
      src = $root / "tools/ruby-gems/idlc"
      dst = Pathname.new(ENV.fetch("IDLC_GEM_GEN_DIR", ($root / "gen" / "idlc_gem").to_s))

      puts "Preparing idlc gem release copy at #{dst}"
      FileUtils.rm_rf(dst)

      symlink_targets = {}
      src.children.select(&:symlink?).each { |s| symlink_targets[s.basename.to_s] = s.realpath }

      FileUtils.mkdir_p(dst)
      FileUtils.cp_r(src.children.map(&:to_s), dst.to_s)
      FileUtils.rm_f(dst / "Gemfile")
      FileUtils.rm_f(dst / "Gemfile.lock")

      symlink_targets.each do |name, target|
        entry = dst / name
        FileUtils.rm_rf(entry)
        next unless target.exist?
        target.directory? ? FileUtils.cp_r(target, entry) : FileUtils.cp(target, entry)
      end

      puts "idlc gem release copy ready at #{dst}"
    end
  end
end

namespace :test do
  namespace :idlc do
    task :ruby do
      Dir.chdir($root / "tools/ruby-gems/idlc") do
        sh "ruby -Ilib:test test/test_*.rb"
      end
    end

    task :sorbet_coverage do
      Bundler.with_unbundled_env do
        Dir.chdir($root / "tools/ruby-gems/idlc") do
          sh "BUNDLE_GEMFILE=#{$root}/Gemfile BUNDLE_FROZEN=1 bundle exec spoom srb coverage"
        end
      end
    end

    desc "Run all idlc unit tests"
    task :unit do
      Dir.chdir($root / "tools/ruby-gems/idlc") do
        sh "bundle exec ruby test/run.rb"
      end
    end
  end
end

# ── udb ───────────────────────────────────────────────────────────────────

namespace :release do
  namespace :udb do
    desc "Prepare a copy of the udb gem for release under gen/udb_gem (or UDB_GEM_GEN_DIR)"
    task :prepare do
      src = $root / "tools/ruby-gems/udb"
      dst = Pathname.new(ENV.fetch("UDB_GEM_GEN_DIR", ($root / "gen" / "udb_gem").to_s))

      puts "Preparing udb gem release copy at #{dst}"
      FileUtils.rm_rf(dst)

      symlink_targets = {}
      src.children.select(&:symlink?).each { |s| symlink_targets[s.basename.to_s] = s.realpath }

      FileUtils.mkdir_p(dst)
      FileUtils.cp_r(src.children.map(&:to_s), dst.to_s)
      FileUtils.rm_f(dst / "Gemfile")
      FileUtils.rm_f(dst / "Gemfile.lock")

      symlink_targets.each do |name, target|
        entry = dst / name
        FileUtils.rm_rf(entry)
        next unless target.exist?
        next if name == "schemas"  # symlink to spec/schemas; not needed in gem copy
        target.directory? ? FileUtils.cp_r(target, entry) : FileUtils.cp(target, entry)
      end

      # Populate .data/ with required data files from the monorepo
      data_dir = dst / ".data"
      {
        ($root / "spec" / "std" / "isa")    => (data_dir / "spec" / "std" / "isa"),
        ($root / "spec" / "custom" / "isa") => (data_dir / "spec" / "custom" / "isa"),
        ($root / "spec" / "schemas")        => (data_dir / "spec" / "schemas"),
        ($root / "cfgs")                    => (data_dir / "cfgs")
      }.each do |from, to|
        FileUtils.mkdir_p(to.dirname)
        FileUtils.cp_r(from, to)
      end

      puts "udb gem release copy ready at #{dst}"
    end
  end
end

namespace :gen do
  namespace :udb do
    desc "Generate the UDB Ruby API documentation"
    task "ruby-doc" do
      Dir.chdir($root / "tools/ruby-gems/udb") do
        sh "bundle exec yard doc"
      end
    end

    task :api_doc do
      Dir.chdir($root / "tools/ruby-gems/udb") do
        FileUtils.rm_rf $root / "gen" / "udb_api_doc"
        sh "bundle exec yard --plugin sorbet lib --no-save --embed-mixins --hide-void-return -o #{$root}/gen/udb_api_doc"
      end
    end
  end
end

namespace :chore do
  namespace :udb do
    task :lsp do
      Bundler.with_unbundled_env do
        Dir.chdir($root) do
          sh "BUNDLE_GEMFILE=#{$root}/Gemfile BUNDLE_FROZEN=1 bundle exec srb tc --lsp --disable-watchman"
        end
      end
    end

    task :collate_cov, [:cov_dir] do |_t, args|
      require "simplecov"
      require "simplecov-cobertura"

      if args[:cov_dir].nil?
        Udb.logger.error "Missing required argument: cov_dir"
        exit 1
      end

      SimpleCov.collate Dir["#{args[:cov_dir]}/*.resultset.json"] do
        coverage_dir(($root / "tools/ruby-gems/udb/coverage").to_s)
        formatter SimpleCov::Formatter::MultiFormatter.new([
          SimpleCov::Formatter::CoberturaFormatter,
          SimpleCov::Formatter::HTMLFormatter,
        ])
      end
    end
  end
end

namespace :test do
  namespace :udb do
    desc "Run unit tests for the udb gem"
    task :unit do
      Dir.chdir($root / "tools/ruby-gems/udb") do
        sh "ruby -Ilib:test test/run.rb"
      end
    end
  end
end

# ── udb_helpers ───────────────────────────────────────────────────────────

namespace :release do
  namespace :udb_helpers do
    desc "Prepare a copy of the udb_helpers gem for release under gen/udb_helpers_gem (or UDB_HELPERS_GEM_GEN_DIR)"
    task :prepare do
      src = $root / "tools/ruby-gems/udb_helpers"
      dst = Pathname.new(ENV.fetch("UDB_HELPERS_GEM_GEN_DIR", ($root / "gen" / "udb_helpers_gem").to_s))

      puts "Preparing udb_helpers gem release copy at #{dst}"
      FileUtils.rm_rf(dst)

      symlink_targets = {}
      src.children.select(&:symlink?).each { |s| symlink_targets[s.basename.to_s] = s.realpath }

      FileUtils.mkdir_p(dst)
      FileUtils.cp_r(src.children.map(&:to_s), dst.to_s)
      FileUtils.rm_f(dst / "Gemfile")
      FileUtils.rm_f(dst / "Gemfile.lock")

      symlink_targets.each do |name, target|
        entry = dst / name
        FileUtils.rm_rf(entry)
        next unless target.exist?
        target.directory? ? FileUtils.cp_r(target, entry) : FileUtils.cp(target, entry)
      end

      puts "udb_helpers gem release copy ready at #{dst}"
    end
  end
end

namespace :test do
  namespace :udb_helpers do
    desc "Run unit tests for the udb_helpers gem"
    task :unit do
      Dir.chdir($root / "tools/ruby-gems/udb_helpers") do
        sh "ruby -Ilib:test test/run.rb"
      end
    end
  end
end

# ── udb-gen ───────────────────────────────────────────────────────────────

namespace :release do
  namespace :udb_gen do
    desc "Prepare a copy of the udb-gen gem for release under gen/udb_gen_gem (or UDB_GEN_GEM_GEN_DIR)"
    task :prepare do
      src = $root / "tools/ruby-gems/udb-gen"
      dst = Pathname.new(ENV.fetch("UDB_GEN_GEM_GEN_DIR", ($root / "gen" / "udb_gen_gem").to_s))

      puts "Preparing udb-gen gem release copy at #{dst}"
      FileUtils.rm_rf(dst)

      symlink_targets = {}
      src.children.select(&:symlink?).each { |s| symlink_targets[s.basename.to_s] = s.realpath }

      FileUtils.mkdir_p(dst)
      FileUtils.cp_r(src.children.map(&:to_s), dst.to_s)
      FileUtils.rm_f(dst / "Gemfile")
      FileUtils.rm_f(dst / "Gemfile.lock")

      symlink_targets.each do |name, target|
        entry = dst / name
        FileUtils.rm_rf(entry)
        next unless target.exist?
        target.directory? ? FileUtils.cp_r(target, entry) : FileUtils.cp(target, entry)
      end

      puts "udb-gen gem release copy ready at #{dst}"
    end
  end
end
