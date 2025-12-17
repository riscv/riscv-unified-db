# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "sorbet-runtime"

require_relative "database_obj"
require_relative "../fields"

module Udb

  class InstructionOpcode < TopLevelDatabaseObject
    sig { returns(String) }
    def display_name = @data.fetch("displayName")

    sig { returns(Integer) }
    def value = @data.fetch("value")
  end

end
