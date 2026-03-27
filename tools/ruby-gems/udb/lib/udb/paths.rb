# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "pathname"
require "sorbet-runtime"

require_relative "version"

module Udb
  extend T::Sig

  sig { returns(Pathname) }
  def self.gem_path
    @gem_path ||= Pathname.new(Gem::Specification.find_by_name("udb").full_gem_path)
  end

  sig { params(from_dir: Pathname).returns(T.nilable(Pathname)) }
  def self.find_udb_root(from_dir)
    if from_dir.root?
      nil
    elsif (from_dir / "do").executable? && (from_dir / "spec").directory?
      from_dir
    else
      find_udb_root(from_dir.dirname)
    end
  end
  private_class_method :find_udb_root

  sig { returns(T.nilable(Pathname)) }
  def self.repo_root
    @root ||=
      if ENV.key?("UDB_ROOT")
        Pathname.new(ENV["UDB_ROOT"])
      else
        find_udb_root(Pathname.new(__dir__))
      end
  end

  sig { returns(Pathname) }
  def self.default_std_isa_path
    if repo_root.nil?
      # not in the udb repo. try for a copy of the database stored with the gem
      gem_path / ".data" / "spec" / "std" / "isa"
    else
      T.must(repo_root) / "spec" / "std" / "isa"
    end
  end

  sig { returns(Pathname) }
  def self.default_custom_isa_path
    if repo_root.nil?
      # not in the udb repo. try for a copy of the database stored with the gem
      gem_path / ".data" / "spec" / "custom" / "isa"
    else
      T.must(repo_root) / "spec" / "custom" / "isa"
    end
  end

  sig { returns(Pathname) }
  def self.default_schemas_path
    if repo_root.nil?
      # not in the udb repo. try for a copy of the database stored with the gem
      gem_path / ".data" / "spec" / "schemas"
    else
      T.must(repo_root) / "spec" / "schemas"
    end
  end

  sig { returns(Pathname) }
  def self.default_gen_path
    if repo_root.nil?
      # not in the udb repo. use XDG path
      data_home = Pathname.new(ENV.fetch("XDG_DATA_HOME", "#{ENV["HOME"]}/.local/share"))
      data_home / "udb" / Udb.version / "gen"
    else
      T.must(repo_root) / "gen"
    end
  end

  sig { returns(Pathname) }
  def self.default_cfgs_path
    if repo_root.nil?
      gem_path / ".data" / "cfgs"
    else
      T.must(repo_root) / "cfgs"
    end
  end
end
