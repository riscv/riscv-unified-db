#!/usr/bin/env bash

# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# Helper functions for bin/chore
# This file contains shared utility functions used across chore subcommands

#
# Setup container environment variables
# Sets: CONTAINER_TAG, REGISTRY, OWNER, CONTAINER_TYPE
# Returns: 0 on success, 1 on error
#
setup_container_vars() {
  # Get necessary variables without triggering automatic container build
  CONTAINER_TAG=$(cat "${UDB_ROOT}/bin/.container-tag")
  REGISTRY=${REGISTRY:="ghcr.io"}
  if [ "$REGISTRY" == "ghcr.io" ]; then
    OWNER=riscv
  elif [ "$REGISTRY" == "docker.io" ]; then
    OWNER=riscvintl
  else
    echo "Bad registry: ${REGISTRY}" 1>&2
    return 1
  fi

  # shellcheck source=.functions.sh
  source "${UDB_ROOT}/bin/.functions.sh"

  CONTAINER_TYPE=$(get_container_type)

  if [ "${CONTAINER_TYPE}" != "docker" ] && [ "${CONTAINER_TYPE}" != "podman" ]; then
    echo "Error: Container operations only work with docker or podman, not ${CONTAINER_TYPE}" 1>&2
    return 1
  fi

  echo "Using ${CONTAINER_TYPE} environment"
  return 0
}

#
# Check if a container image exists locally
# Args: None (uses CONTAINER_TYPE, REGISTRY, OWNER, CONTAINER_TAG from environment)
# Returns: 0 if exists, 1 if not
#
container_exists() {
  ${CONTAINER_TYPE} images "$REGISTRY/$OWNER/udb:${CONTAINER_TAG}" --format table | grep -q udb
}

#
# Increment a semantic version's minor number
# Args: $1 - version string (e.g., "1.2")
# Returns: incremented version (e.g., "1.3")
#
increment_minor_version() {
  local version=$1
  # Set Internal Field Separator to '.'
  IFS='.' read -r major minor <<<"$version"

  # Increment the minor version number using arithmetic expansion
  ((minor++))

  # Re-assemble the version string
  local new_version="${major}.${minor}"
  echo "$new_version"
}

#
# Source bin/setup if not already sourced
# Sets: SETUP_SOURCED environment variable
#
source_setup() {
  if [ -z "$SETUP_SOURCED" ]; then
    export SETUP_SOURCED=1
    source "$UDB_ROOT"/bin/setup
  fi
}
