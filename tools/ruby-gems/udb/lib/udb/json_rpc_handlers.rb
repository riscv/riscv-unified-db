# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

module Udb
  # Handler implementations for each JSON-RPC method defined in openrpc.yaml.
  # Method naming convention: handle_<rpc_method_name> (dots replaced with underscores).
  # Each method receives a params Hash and returns the result Hash.
  # The @cfg_arch instance variable is available from JsonRpcServer.
  module JsonRpcHandlers
    extend T::Sig

    sig { params(_params: T::Hash[String, T.untyped]).returns(T::Hash[String, T.untyped]) }
    def handle_list_extensions(_params)
      extensions = @cfg_arch.possible_extensions.map do |ext|
        {
          "name" => ext.name,
          "long_name" => ext.long_name,
          "versions" => ext.versions.map(&:version_str),
          "instruction_count" => ext.instructions.count
        }
      end
      { "extensions" => extensions, "count" => extensions.length }
    end
  end
end
