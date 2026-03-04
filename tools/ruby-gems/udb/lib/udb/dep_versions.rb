# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: false
# frozen_string_literal: true

module Udb
  EQNTOTT_VERSION  = File.read("#{Kernel.__dir__}/EQNTOTT_VERSION").strip
  ESPRESSO_VERSION = File.read("#{Kernel.__dir__}/ESPRESSO_VERSION").strip
  MUST_VERSION     = File.read("#{Kernel.__dir__}/MUST_VERSION").strip
  Z3_VERSION       = File.read("#{Kernel.__dir__}/Z3_VERSION").strip
end
