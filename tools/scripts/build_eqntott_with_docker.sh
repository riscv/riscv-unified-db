#!/usr/bin/env bash
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# Build eqntott from source using Docker and AlmaLinux 8.
# Produces a statically-linked binary for maximum portability (musl 1.2.5).
#
# Usage: build_eqntott_with_docker.sh [output_dir] [architecture]
#   output_dir   - where to place the binary (default: ./eqntott-build)
#   architecture - x64 or arm64 (default: x64)
#
# The pinned commit matches EQNTOTT_VERSION in the udb gem.
# To update: change EQNTOTT_COMMIT below and update lib/udb/EQNTOTT_VERSION accordingly.

set -euo pipefail

error() { echo "ERROR: $*" >&2; exit 1; }
info()  { echo "INFO: $*"  >&2; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

# Pinned commit - must match lib/udb/EQNTOTT_VERSION
EQNTOTT_COMMIT="392759e6493a46f1d1ed7d9fb1c7c31197b0f6a8"

build_eqntott_with_docker() {
    local output_dir="${1:-./eqntott-build}"
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

    info "Building eqntott (commit $EQNTOTT_COMMIT)"
    info "Output directory: $output_dir"
    info "Architecture: $architecture ($docker_platform)"

    command_exists docker || error "Docker is not installed or not in PATH"

    local temp_dir
    temp_dir=$(mktemp -d -t eqntott-build-XXXXXX)
    trap "rm -rf '$temp_dir'" EXIT

    info "Using temporary directory: $temp_dir"

    # Write Dockerfile - EQNTOTT_COMMIT is baked in at image-build time via ARG
    cat > "$temp_dir/Dockerfile" << 'EOF'
FROM almalinux:8

RUN dnf install -y \
    gcc-toolset-12 \
    make \
    git \
    autoconf \
    automake \
    curl \
    && dnf clean all

ENV PATH=/opt/rh/gcc-toolset-12/root/usr/bin:$PATH \
    LD_LIBRARY_PATH=/opt/rh/gcc-toolset-12/root/usr/lib64

ARG EQNTOTT_COMMIT
WORKDIR /build

RUN curl -L -o musl-1.2.5.tar.gz https://musl.libc.org/releases/musl-1.2.5.tar.gz \
  && tar -xf musl-1.2.5.tar.gz \
  && cd musl-1.2.5 \
  && ./configure && make && make install

RUN git clone https://github.com/TheProjecter/eqntott.git eqntott && \
    cd eqntott && \
    git checkout ${EQNTOTT_COMMIT}

WORKDIR /build/eqntott

# Configure and build with static linking
RUN ./configure CC="/usr/local/musl/bin/musl-gcc" LDFLAGS="-static" && \
    make -j$(nproc) && \
    strip src/eqntott

RUN touch /build/BUILD_SUCCESS
EOF

    local image_name="eqntott-builder-$$"
    info "Building Docker image for $docker_platform..."
    docker build \
        --platform="$docker_platform" \
        --build-arg "EQNTOTT_COMMIT=$EQNTOTT_COMMIT" \
        -t "$image_name" \
        -f "$temp_dir/Dockerfile" \
        "$temp_dir" \
        || error "Docker build failed"

    local container_name="eqntott-extract-$$"
    docker create --name "$container_name" "$image_name" || error "Failed to create container"

    if ! docker cp "$container_name:/build/BUILD_SUCCESS" "$temp_dir/" 2>/dev/null; then
        docker rm "$container_name" >/dev/null 2>&1 || true
        docker rmi "$image_name" >/dev/null 2>&1 || true
        error "eqntott build failed - BUILD_SUCCESS marker not found"
    fi

    mkdir -p "$output_dir"
    docker cp "$container_name:/build/eqntott/src/eqntott" "$output_dir/eqntott" \
        || error "Failed to extract eqntott binary"
    chmod +x "$output_dir/eqntott"

    docker rm "$container_name" >/dev/null 2>&1 || true
    docker rmi "$image_name" >/dev/null 2>&1 || true

    info "Build completed successfully!"
    info "Binary: $output_dir/eqntott"
    ls -lh "$output_dir/eqntott"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ $# -gt 0 ]] && [[ "$1" == "-h" || "$1" == "--help" ]]; then
        echo "Usage: $0 [output_dir] [architecture]" >&2
        echo "  output_dir   - where to place the binary (default: ./eqntott-build)" >&2
        echo "  architecture - x64 or arm64 (default: x64)" >&2
        exit 0
    fi
    build_eqntott_with_docker "${1:-./eqntott-build}" "${2:-x64}"
fi
