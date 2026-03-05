# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

# Workaround for a tapioca/sorbet bug where, if AstNode#abstract! is defined only in
# ast.rb, tapioca reports that AstNode is declared abstract twice during RBI generation.
#
# This regression was observed immediately after upgrading tapioca from 0.16.11; keep
# this shim file until the duplicate-abstract error no longer occurs with the current
# tapioca/sorbet versions.

require "sorbet-runtime"

module Idl
  class AstNode
    extend T::Sig
    extend T::Helpers
    abstract!
  end
end
