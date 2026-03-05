# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

module Udb
  module OpenRpc
    # Typed wrapper for a content descriptor (parameter or result) in the OpenRPC spec
    class ContentDescriptor
      extend T::Sig

      sig { returns(String) }
      attr_reader :name

      sig { returns(T.nilable(String)) }
      attr_reader :description

      sig { returns(T.nilable(T::Hash[String, T.untyped])) }
      attr_reader :schema

      sig { returns(T::Boolean) }
      def required?
        @required
      end

      sig { params(data: T::Hash[String, T.untyped]).void }
      def initialize(data)
        @name = T.let(data.fetch("name"), String)
        @description = T.let(data["description"], T.nilable(String))
        @schema = T.let(data["schema"], T.nilable(T::Hash[String, T.untyped]))
        @required = T.let(data.fetch("required", true), T::Boolean)
      end

      sig { returns(T::Hash[String, T.untyped]) }
      def to_h
        h = T.let({ "name" => @name }, T::Hash[String, T.untyped])
        h["description"] = @description if @description
        h["schema"] = @schema if @schema
        h["required"] = @required
        h
      end
    end
  end
end
