# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# typed: true
# frozen_string_literal: true

module Udb
  # Z3 version to use for the udb gem
  # This is the single source of truth for which Z3 version should be downloaded
  Z3_VERSION = "4.16.0"
  Z3_CHECKSUM = {
    "arm64-glibc-2.39" => "sha256:87fcd963d3eecb0f12cf1c3ef0ad74e84a3a7bd3caed5d94445645ef94ae6274",
    "x64-glibc-2.39" => "sha256:7288c49a5bd6dbafd7b0b0d1f65956b91672da24b08f09242919af159be3418e"
  }
end
