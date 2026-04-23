#!/bin/bash

# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# Container operations for bin/chore

#
# Build the container image
# Args: $1 - force flag ("yes" to force rebuild, "no" otherwise)
#
do_container_build() {
  local force=$1

  local runtime
  runtime=$(get_container_runtime)
  if [ -z "$runtime" ]; then
    echo "Error: No container runtime (docker/podman) found" >&2
    exit 1
  fi

  local tag image dockerfile context
  tag=$(compute_toolchain_hash)
  image="ghcr.io/riscv/udb-toolchain:${tag}"
  dockerfile="${UDB_ROOT}/.toolchain/Dockerfile"
  context="${UDB_ROOT}/.toolchain"

  if [ "$force" != "yes" ]; then
    if $runtime images --format "{{.Repository}}:{{.Tag}}" 2>/dev/null | grep -qF "${image}"; then
      echo "Container image ${image} already exists."
      echo "Use 'chore container build -f' to force rebuild."
      exit 0
    fi
  fi

  echo "Building container image ${image}..."
  $runtime build -t "${image}" -f "${dockerfile}" "${context}"
}

#
# Pull the container image from registry
# Args: $1 - force flag ("yes" to force pull, "no" otherwise)
#
do_container_pull() {
  local force=$1

  local runtime
  runtime=$(get_container_runtime)
  if [ -z "$runtime" ]; then
    echo "Error: No container runtime (docker/podman) found" >&2
    exit 1
  fi

  local tag image
  tag=$(compute_toolchain_hash)
  image="ghcr.io/riscv/udb-toolchain:${tag}"

  if [ "$force" != "yes" ]; then
    if $runtime images --format "{{.Repository}}:{{.Tag}}" 2>/dev/null | grep -qF "${image}"; then
      echo "Container image ${image} already exists locally."
      echo "Use 'chore container pull -f' to force pull."
      exit 0
    fi
  fi

  echo "Pulling container image ${image}..."
  $runtime pull "${image}"
}

#
# Remove the container image
#
do_container_remove() {
  local runtime
  runtime=$(get_container_runtime)
  if [ -z "$runtime" ]; then
    echo "Error: No container runtime (docker/podman) found" >&2
    exit 1
  fi

  local tag image
  tag=$(compute_toolchain_hash)
  image="ghcr.io/riscv/udb-toolchain:${tag}"

  if ! $runtime images --format "{{.Repository}}:{{.Tag}}" 2>/dev/null | grep -qF "${image}"; then
    echo "Container image ${image} does not exist locally."
    exit 0
  fi

  echo "Removing container image ${image}..."
  $runtime rmi "${image}"
}
