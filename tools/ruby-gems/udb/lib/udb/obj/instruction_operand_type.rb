# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "sorbet-runtime"

require_relative "database_obj"

module Udb
  class InstructionOperandType < TopLevelDatabaseObject

    class Type < T::Enum
      enums do
        Immediate = new("immediate")
        RegisterRefernce = new("register_reference")
        ShiftAmount = new("shift_amount")
      end
    end

    sig { returns(Type) }
    def type
      Type.deserialize(@data.fetch("type"))
    end

    sig { returns(T::Boolean) }
    def signed?
      @data.key?("signed") && @data.fetch("signed") == true
    end
  end
end
