# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "sorbet-runtime"

module Udb
  class GlobalOptions < T::Struct
    # when true, set Z3's parallel.enable param to true
    prop :parallel_z3, T::Boolean, default: true
  end

  def self.global_options
    @global_options ||= GlobalOptions.new
  end
end
