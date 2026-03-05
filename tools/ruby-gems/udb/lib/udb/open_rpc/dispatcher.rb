# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require "json_schemer"
require_relative "spec"

module Udb
  module OpenRpc
    # Handles routing and parameter validation for JSON-RPC requests.
    # Dynamically builds routing table from the OpenRPC spec at instantiation time.
    # Verifies that all methods in the spec have corresponding handler methods.
    class Dispatcher
      extend T::Sig

      sig { params(spec: Spec, handler_obj: T.untyped).void }
      def initialize(spec, handler_obj)
        @spec = spec
        @handler_obj = handler_obj
        verify_handlers!
      end

      # Dispatch a JSON-RPC request.
      # Returns [status, result_or_error_data] where status is one of:
      # :ok, :not_found, :invalid_params, :internal_error
      sig do
        params(
          method_name: String,
          params: T::Hash[String, T.untyped]
        ).returns([Symbol, T.untyped])
      end
      def dispatch(method_name, params)
        method_spec = @spec.method_spec(method_name)
        return [:not_found, "Unknown method: #{method_name}"] if method_spec.nil?

        errors = validate_params(method_spec, params)
        return [:invalid_params, errors] unless errors.empty?

        result = @handler_obj.public_send(method_spec.handler_method_name, params)
        [:ok, result]
      rescue StandardError => e
        [:internal_error, e.message]
      end

      private

      sig { void }
      def verify_handlers!
        @spec.methods.each do |m|
          next if @handler_obj.respond_to?(m.handler_method_name)

          raise "Missing handler for RPC method '#{m.name}': " \
                "expected method '#{m.handler_method_name}' on #{@handler_obj.class}"
        end
      end

      sig do
        params(
          method_spec: MethodSpec,
          params: T::Hash[String, T.untyped]
        ).returns(T::Array[String])
      end
      def validate_params(method_spec, params)
        errors = T.let([], T::Array[String])
        method_spec.params.each do |p|
          if p.required? && !params.key?(p.name)
            errors << "Missing required parameter: #{p.name}"
            next
          end
          next unless params.key?(p.name) && p.schema

          JSONSchemer.schema(p.schema).validate(params[p.name]).each do |err|
            errors << "Parameter '#{p.name}': #{err["error"]}"
          end
        end
        errors
      end
    end
  end
end
