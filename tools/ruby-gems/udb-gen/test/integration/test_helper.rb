# SPDX-License-Identifier: BSD-3-Clause-Clear
# SPDX-FileCopyrightText: Copyright (c) Charlie Jenkins

# typed: false
# frozen_string_literal: true
require "sorbet-runtime"
T::Configuration.default_checked_level = :never
require "minitest/autorun"
require "mocha/minitest"

$LOAD_PATH.unshift File.expand_path("../lib", __dir__)
require "udb-gen"

module TestHelpers
  def fixture_path(path)
    File.join(__dir__, "fixtures", path)
  end

  def read_fixture(path)
    File.read(File.expand_path("fixtures/#{path}", __dir__))
  end
end

Minitest::Test.include TestHelpers
