# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "yaml"
require "pathname"
require_relative "method_spec"

module Udb
  module OpenRpc
    # Loads and parses the OpenRPC YAML spec file.
    # The spec file is the source of truth for the JSON-RPC API.
    class Spec
      extend T::Sig

      SPEC_PATH = T.let(
        Pathname.new(__dir__).parent.join("openrpc.yaml").freeze,
        Pathname
      )

      sig { returns(String) }
      attr_reader :openrpc_version

      sig { returns(T::Hash[String, T.untyped]) }
      attr_reader :info

      sig { returns(T::Array[MethodSpec]) }
      attr_reader :methods

      sig { void }
      def initialize
        raw = YAML.safe_load_file(SPEC_PATH)
        @openrpc_version = T.let(raw.fetch("openrpc"), String)
        @info = T.let(raw.fetch("info"), T::Hash[String, T.untyped])
        @methods = T.let(
          raw.fetch("methods").map { |m| MethodSpec.new(m) },
          T::Array[MethodSpec]
        )
        @method_index = T.let(
          @methods.each_with_object({}) { |m, h| h[m.name] = m },
          T::Hash[String, MethodSpec]
        )
      end

      sig { params(name: String).returns(T.nilable(MethodSpec)) }
      def method_spec(name)
        @method_index[name]
      end

      sig { returns(T::Array[String]) }
      def method_names
        @methods.map(&:name)
      end

      sig { returns(T::Hash[String, T.untyped]) }
      def to_h
        {
          "openrpc" => @openrpc_version,
          "info" => @info,
          "methods" => @methods.map(&:to_h)
        }
      end
    end
  end
end
