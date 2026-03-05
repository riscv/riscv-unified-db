# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require_relative "content_descriptor"

module Udb
  module OpenRpc
    # Typed wrapper for a single method entry in the OpenRPC spec
    class MethodSpec
      extend T::Sig

      sig { returns(String) }
      attr_reader :name

      sig { returns(String) }
      attr_reader :summary

      sig { returns(T.nilable(String)) }
      attr_reader :description

      sig { returns(T::Array[ContentDescriptor]) }
      attr_reader :params

      sig { returns(ContentDescriptor) }
      attr_reader :result

      sig { returns(T::Array[T::Hash[String, T.untyped]]) }
      attr_reader :errors

      # Convention: "list_extensions" -> "handle_list_extensions"
      # Dots replaced with underscores for methods like "rpc.discover"
      sig { returns(String) }
      def handler_method_name
        "handle_#{@name.gsub(".", "_")}"
      end

      sig { params(data: T::Hash[String, T.untyped]).void }
      def initialize(data)
        @name = T.let(data.fetch("name"), String)
        @summary = T.let(data.fetch("summary"), String)
        @description = T.let(data["description"], T.nilable(String))
        @params = T.let(
          (data["params"] || []).map { |p| ContentDescriptor.new(p) },
          T::Array[ContentDescriptor]
        )
        @result = T.let(ContentDescriptor.new(data.fetch("result")), ContentDescriptor)
        @errors = T.let(data["errors"] || [], T::Array[T::Hash[String, T.untyped]])
      end

      sig { returns(T::Hash[String, T.untyped]) }
      def to_h
        h = T.let(
          {
            "name" => @name,
            "summary" => @summary,
            "params" => @params.map(&:to_h),
            "result" => @result.to_h
          },
          T::Hash[String, T.untyped]
        )
        h["description"] = @description if @description
        h["errors"] = @errors unless @errors.empty?
        h
      end
    end
  end
end
