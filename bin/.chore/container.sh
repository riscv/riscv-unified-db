#!/bin/bash

# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# Container operations for bin/chore

#
# Build the container image
# Args: $1 - force flag ("yes" to force rebuild, "no" otherwise)
#       $2 - target ("devcontainer" or "toolchain"; default: "devcontainer")
#
do_container_build() {
  local force=$1
  local target=${2:-devcontainer}

  local runtime
  runtime=$(get_container_runtime)
  if [ -z "$runtime" ]; then
    echo "Error: No container runtime (docker/podman) found" >&2
    exit 1
  fi

  local tag image dockerfile context
  if [ "$target" = "devcontainer" ]; then
    tag=$(compute_devcontainer_hash)
    image="ghcr.io/riscv/udb:${tag}"
    dockerfile="${UDB_ROOT}/.devcontainer/Dockerfile"
    context="${UDB_ROOT}"
  elif [ "$target" = "toolchain" ]; then
    tag=$(compute_toolchain_hash)
    image="ghcr.io/riscv/udb-toolchain:${tag}"
    dockerfile="${UDB_ROOT}/.toolchain/Dockerfile"
    context="${UDB_ROOT}/.toolchain"
  else
    echo "Error: Unknown target '${target}'. Must be 'devcontainer' or 'toolchain'." >&2
    exit 1
  fi

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
#       $2 - target ("devcontainer" or "toolchain"; default: "devcontainer")
#
do_container_pull() {
  local force=$1
  local target=${2:-devcontainer}

  local runtime
  runtime=$(get_container_runtime)
  if [ -z "$runtime" ]; then
    echo "Error: No container runtime (docker/podman) found" >&2
    exit 1
  fi

  local tag image
  if [ "$target" = "devcontainer" ]; then
    tag=$(compute_devcontainer_hash)
    image="ghcr.io/riscv/udb:${tag}"
  elif [ "$target" = "toolchain" ]; then
    tag=$(compute_toolchain_hash)
    image="ghcr.io/riscv/udb-toolchain:${tag}"
  else
    echo "Error: Unknown target '${target}'. Must be 'devcontainer' or 'toolchain'." >&2
    exit 1
  fi

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
# Args: $1 - target ("devcontainer" or "toolchain"; default: "devcontainer")
#
do_container_remove() {
  local target=${1:-devcontainer}

  local runtime
  runtime=$(get_container_runtime)
  if [ -z "$runtime" ]; then
    echo "Error: No container runtime (docker/podman) found" >&2
    exit 1
  fi

  local tag image
  if [ "$target" = "devcontainer" ]; then
    tag=$(compute_devcontainer_hash)
    image="ghcr.io/riscv/udb:${tag}"
  elif [ "$target" = "toolchain" ]; then
    tag=$(compute_toolchain_hash)
    image="ghcr.io/riscv/udb-toolchain:${tag}"
  else
    echo "Error: Unknown target '${target}'. Must be 'devcontainer' or 'toolchain'." >&2
    exit 1
  fi

  if ! $runtime images --format "{{.Repository}}:{{.Tag}}" 2>/dev/null | grep -qF "${image}"; then
    echo "Container image ${image} does not exist locally."
    exit 0
  fi

  echo "Removing container image ${image}..."
  $runtime rmi "${image}"
}
