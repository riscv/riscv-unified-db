#!/usr/bin/env bash

# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# Container operations for bin/chore
# This file contains all container-related subcommands

#
# Build the container image
# Args: $1 - force flag ("yes" to force rebuild, "no" otherwise)
# Returns: 0 on success, exits with 1 on error
#
do_container_build() {
  local force=$1

  setup_container_vars || exit 1

  # Check if container already exists
  if [ "$force" != "yes" ]; then
    if container_exists; then
      echo "Container image $REGISTRY/$OWNER/udb:${CONTAINER_TAG} already exists."
      echo "Use 'chore container build -f' to force rebuild."
      exit 0
    fi
  fi

  echo "Building container image $REGISTRY/$OWNER/udb:${CONTAINER_TAG}..."
  build_container "${UDB_ROOT}"
}

#
# Pull the container image from registry
# Args: $1 - force flag ("yes" to force pull, "no" otherwise)
# Returns: 0 on success, exits with 1 on error
#
do_container_pull() {
  local force=$1

  setup_container_vars || exit 1

  # Check if container already exists
  if [ "$force" != "yes" ]; then
    if container_exists; then
      echo "Container image $REGISTRY/$OWNER/udb:${CONTAINER_TAG} already exists locally."
      echo "Use 'chore container pull -f' to force pull."
      exit 0
    fi
  fi

  echo "Pulling container image $REGISTRY/$OWNER/udb:${CONTAINER_TAG}..."
  ${CONTAINER_TYPE} pull "$REGISTRY/$OWNER/udb:${CONTAINER_TAG}"
}

#
# Remove the container image
# Returns: 0 on success, exits with 1 on error
#
do_container_remove() {
  setup_container_vars || exit 1

  # Check if container exists
  if ! container_exists; then
    echo "Container image $REGISTRY/$OWNER/udb:${CONTAINER_TAG} does not exist locally."
    exit 0
  fi

  echo "Removing container image $REGISTRY/$OWNER/udb:${CONTAINER_TAG}..."
  ${CONTAINER_TYPE} rmi "$REGISTRY/$OWNER/udb:${CONTAINER_TAG}"
}
