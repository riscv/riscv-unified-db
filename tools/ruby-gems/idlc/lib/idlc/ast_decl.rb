# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

# this file exists to get around a bug in tapioca/sorbet that thinks AstNode is declared
# abstract twice when the abstract! definition is in ast.rb
#
# This started when tapioca upgraded from 0.16.11
#
# I'm not sure why, but this fixes it

require "sorbet-runtime"

module Idl
  class AstNode
    extend T::Sig
    extend T::Helpers
    abstract!
  end
end
