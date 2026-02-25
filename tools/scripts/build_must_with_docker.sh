#!/usr/bin/env bash
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# Build must (mustool) from source using Docker and AlmaLinux 8.
# Produces a statically-linked binary for maximum portability (glibc 2.28+).
#
# Usage: build_must_with_docker.sh [output_dir] [architecture]
#   output_dir   - where to place the binary (default: ./must-build)
#   architecture - x64 or arm64 (default: x64)
#
# The pinned commit matches MUST_VERSION in the udb gem.
# To update: change MUST_COMMIT below and update lib/udb/MUST_VERSION accordingly.

set -euo pipefail

error() { echo "ERROR: $*" >&2; exit 1; }
info()  { echo "INFO: $*"  >&2; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

# Pinned commit - must match lib/udb/MUST_VERSION
MUST_COMMIT="17fa9f9542a9ce05328dfccd1cd410f05f741ab3"

build_must_with_docker() {
    local output_dir="${1:-./must-build}"
    local architecture="${2:-x64}"

    case "${architecture,,}" in
        x64|amd64|x86_64)
            architecture="x64"
            local docker_platform="linux/amd64"
            ;;
        arm64|aarch64)
            architecture="arm64"
            local docker_platform="linux/arm64"
            ;;
        *)
            error "Invalid architecture: $architecture. Must be x64 or arm64"
            ;;
    esac

    info "Building must (mustool @ $MUST_COMMIT)"
    info "Output directory: $output_dir"
    info "Architecture: $architecture ($docker_platform)"

    command_exists docker || error "Docker is not installed or not in PATH"

    local temp_dir
    temp_dir=$(mktemp -d -t must-build-XXXXXX)
    trap "rm -rf '$temp_dir'" EXIT

    info "Using temporary directory: $temp_dir"

    # Write Dockerfile - MUST_COMMIT is baked in at image-build time via ARG
    cat > "$temp_dir/Dockerfile" << 'EOF'
FROM almalinux:8

RUN dnf install -y \
    gcc-toolset-14 \
    make \
    git \
    zlib-static \
    glibc-static \
    libstdc++-static \
    && dnf clean all

ENV PATH=/opt/rh/gcc-toolset-14/root/usr/bin:$PATH \
    LD_LIBRARY_PATH=/opt/rh/gcc-toolset-14/root/usr/lib64:$LD_LIBRARY_PATH

ARG MUST_COMMIT
WORKDIR /build

RUN git clone https://github.com/jar-ben/mustool.git must && \
    cd must && \
    git checkout ${MUST_COMMIT}

WORKDIR /build/must

# Apply the missing #include <cstdio> patch
RUN sed -i -e 's/#include <signal.h>/#include <signal.h>\n#include <cstdio>/' \
    mcsmus/mcsmus/control.cc

# Build; link statically where possible
RUN make -j$(nproc) LDFLAGS="-static" && \
    strip must

RUN touch /build/BUILD_SUCCESS
EOF

    local image_name="must-builder-$$"
    info "Building Docker image for $docker_platform..."
    docker build \
        --platform="$docker_platform" \
        --build-arg "MUST_COMMIT=$MUST_COMMIT" \
        -t "$image_name" \
        -f "$temp_dir/Dockerfile" \
        "$temp_dir" \
        || error "Docker build failed"

    local container_name="must-extract-$$"
    docker create --name "$container_name" "$image_name" || error "Failed to create container"

    if ! docker cp "$container_name:/build/BUILD_SUCCESS" "$temp_dir/" 2>/dev/null; then
        docker rm "$container_name" >/dev/null 2>&1 || true
        docker rmi "$image_name" >/dev/null 2>&1 || true
        error "must build failed - BUILD_SUCCESS marker not found"
    fi

    mkdir -p "$output_dir"
    docker cp "$container_name:/build/must/must" "$output_dir/must" \
        || error "Failed to extract must binary"
    chmod +x "$output_dir/must"

    docker rm "$container_name" >/dev/null 2>&1 || true
    docker rmi "$image_name" >/dev/null 2>&1 || true

    info "Build completed successfully!"
    info "Binary: $output_dir/must"
    ls -lh "$output_dir/must"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ $# -gt 0 ]] && [[ "$1" == "-h" || "$1" == "--help" ]]; then
        echo "Usage: $0 [output_dir] [architecture]" >&2
        echo "  output_dir   - where to place the binary (default: ./must-build)" >&2
        echo "  architecture - x64 or arm64 (default: x64)" >&2
        exit 0
    fi
    build_must_with_docker "${1:-./must-build}" "${2:-x64}"
fi
