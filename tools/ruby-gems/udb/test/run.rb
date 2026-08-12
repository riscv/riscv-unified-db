# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

require_relative "test_helper"

# Load every test file in this directory. Enumerating them by hand meant a new
# test file silently never ran here until someone remembered to add it.
Dir.children(__dir__).grep(/\Atest_.+\.rb\z/).sort.each do |test_file|
  next if test_file == "test_helper.rb"

  require_relative test_file
end
