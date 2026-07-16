# Copyright (c) Jordan Carlin, Harvey Mudd College.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require "pathname"

SIMPLECOV_AVAILABLE = begin
  require "simplecov"
  require "simplecov-cobertura"
  true
rescue LoadError
  false
end

UDB_GEN_ROOT = (Pathname.new(__dir__) / "..").realpath

if SIMPLECOV_AVAILABLE && !SimpleCov.active_session? && ENV["COVERAGE"] != "0"
  SimpleCov.start do
    enable_coverage :branch, :eval
    skip "/test/"
    root UDB_GEN_ROOT.to_s
    coverage_dir (UDB_GEN_ROOT / "coverage").to_s
    formatter SimpleCov::Formatter::MultiFormatter.new([
      SimpleCov::Formatter::CoberturaFormatter,
      SimpleCov::Formatter::HTMLFormatter,
    ])
  end

  puts "[SimpleCov] Coverage started."
end

require "minitest/autorun"
