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
# Compute devcontainer image tag as first 16 chars of SHA256 of all devcontainer-affecting files
# Returns: 16-char hex string
#
compute_devcontainer_hash() {
  local files=()
  files+=(
    "${UDB_ROOT}/.devcontainer/Dockerfile"
    "${UDB_ROOT}/.mise.toml"
    "${UDB_ROOT}/pyproject.toml"
    "${UDB_ROOT}/uv.lock"
    "${UDB_ROOT}/package.json"
    "${UDB_ROOT}/package-lock.json"
    "${UDB_ROOT}/Gemfile"
    "${UDB_ROOT}/Gemfile.lock"
  )
  # Add per-gem files
  for gem_dir in "${UDB_ROOT}"/tools/ruby-gems/*/; do
    local gem_name
    gem_name=$(basename "$gem_dir")
    [ -f "${gem_dir}/Gemfile" ]      && files+=("${gem_dir}/Gemfile")
    [ -f "${gem_dir}/Gemfile.lock" ] && files+=("${gem_dir}/Gemfile.lock")
    # gemspec: named after the gem directory
    [ -f "${gem_dir}/${gem_name}.gemspec" ] && files+=("${gem_dir}/${gem_name}.gemspec")
    # version.rb files
    for vf in "${gem_dir}"/lib/*/version.rb; do
      [ -f "$vf" ] && files+=("$vf")
    done
  done
  sha256sum "${files[@]}" | sha256sum | cut -c1-16
}

#
# Compute toolchain container image tag as first 16 chars of SHA256 of .toolchain/Dockerfile
# Returns: 16-char hex string
#
compute_toolchain_hash() {
  sha256sum "${UDB_ROOT}/.toolchain/Dockerfile" | cut -c1-16
}
