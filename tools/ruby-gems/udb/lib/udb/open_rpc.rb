# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

require_relative "open_rpc/content_descriptor"
require_relative "open_rpc/method_spec"
require_relative "open_rpc/spec"
require_relative "open_rpc/dispatcher"

module Udb
  # OpenRPC support: spec loading, method descriptors, and request dispatching.
  # The openrpc.yaml file is the source of truth for the JSON-RPC API.
  module OpenRpc
    # All submodules loaded above
  end
end
