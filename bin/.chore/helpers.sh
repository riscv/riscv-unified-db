#!/bin/bash

# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# Helper functions for bin/chore

#
# Get container runtime (docker or podman)
# Prefers docker; falls back to podman; respects DOCKER/PODMAN env vars
# Returns: "docker", "podman", or "" (if neither found)
#
get_container_runtime() {
  if [ -v DOCKER ] || command -v docker &>/dev/null; then
    echo "docker"
  elif [ -v PODMAN ] || command -v podman &>/dev/null; then
    echo "podman"
  else
    echo ""
  fi
}

#
# Compute toolchain container image tag as first 16 chars of SHA256 of .toolchain/Dockerfile
# Returns: 16-char hex string
#
compute_toolchain_hash() {
  sha256sum "${UDB_ROOT}/.toolchain/Dockerfile" | cut -c1-16
}
