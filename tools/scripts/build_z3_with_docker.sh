#!/usr/bin/env bash
# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# Build Z3 from source using Docker and AlmaLinux 8
# This script downloads the latest Z3 release, compiles it in a Docker container,
# and extracts the installation files to the host.

set -euo pipefail

# Function to print error messages
error() {
    echo "ERROR: $*" >&2
    exit 1
}

# Function to print info messages
info() {
    echo "INFO: $*" >&2
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main function to build Z3
build_z3_with_docker() {
    local output_dir="${1:-./z3-build}"
    local build_type="${2:-Release}"
    local architecture="${3:-x64}"

    # Validate build type
    if [[ ! "$build_type" =~ ^(Release|Debug|RelWithDebInfo|MinSizeRel)$ ]]; then
        error "Invalid build type: $build_type. Must be Release, Debug, RelWithDebInfo, or MinSizeRel"
    fi

    # Validate and normalize architecture
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

    info "Starting Z3 build process"
    info "Output directory: $output_dir"
    info "Build type: $build_type"
    info "Architecture: $architecture ($docker_platform)"

    # Check for Docker
    if ! command_exists docker; then
        error "Docker is not installed or not in PATH"
    fi

    # Check for curl or wget
    if ! command_exists curl && ! command_exists wget; then
        error "Neither curl nor wget is installed"
    fi

    # Create temporary directory for build
    local temp_dir
    temp_dir=$(mktemp -d -t z3-build-XXXXXX)
    trap "rm -rf '$temp_dir'" EXIT

    info "Using temporary directory: $temp_dir"

    # Get latest Z3 release version from GitHub API
    info "Fetching latest Z3 release information from GitHub..."
    local latest_release

    # Check for GitHub token for authentication (helps avoid rate limits)
    local auth_header=""
    if [[ -n "${GITHUB_TOKEN:-}" ]]; then
        auth_header="Authorization: Bearer $GITHUB_TOKEN"
        info "Using GitHub authentication token"
    fi

    if command_exists curl; then
        if [[ -n "$auth_header" ]]; then
            latest_release=$(curl -s -H "$auth_header" https://api.github.com/repos/Z3Prover/z3/releases/latest)
        else
            latest_release=$(curl -s https://api.github.com/repos/Z3Prover/z3/releases/latest)
        fi
    else
        if [[ -n "$auth_header" ]]; then
            latest_release=$(wget -qO- --header="$auth_header" https://api.github.com/repos/Z3Prover/z3/releases/latest)
        else
            latest_release=$(wget -qO- https://api.github.com/repos/Z3Prover/z3/releases/latest)
        fi
    fi

    local version
    version=$(echo "$latest_release" | grep -o '"tag_name": *"[^"]*"' | sed 's/"tag_name": *"\(.*\)"/\1/')

    if [[ -z "$version" ]]; then
        # Check if we hit rate limit
        if echo "$latest_release" | grep -q "rate limit"; then
            error "GitHub API rate limit exceeded. Please set GITHUB_TOKEN environment variable or try again later."
        fi
        error "Failed to fetch latest Z3 version from GitHub. Response: $(echo "$latest_release" | head -c 200)"
    fi

    info "Latest Z3 version: $version"

    # Download source tarball
    local tarball_url="http://github.com/Z3Prover/z3/archive/refs/tags/${version}.tar.gz"
    local tarball_path="$temp_dir/z3-${version}.tar.gz"

    info "Downloading Z3 source from: $tarball_url"
    if command_exists curl; then
        if [[ -n "$auth_header" ]]; then
            curl -L -H "$auth_header" -o "$tarball_path" "$tarball_url" || error "Failed to download Z3 source"
        else
            curl -L -o "$tarball_path" "$tarball_url" || error "Failed to download Z3 source"
        fi
    else
        if [[ -n "$auth_header" ]]; then
            wget --header="$auth_header" -O "$tarball_path" "$tarball_url" || error "Failed to download Z3 source"
        else
            wget -O "$tarball_path" "$tarball_url" || error "Failed to download Z3 source"
        fi
    fi

    # Verify the downloaded file is actually a gzip file
    if ! file "$tarball_path" | grep -q "gzip compressed"; then
        info "Downloaded file is not a gzip archive. First 500 bytes:"
        head -c 500 "$tarball_path" >&2
        error "Downloaded file is not in gzip format. This may indicate a rate limit or download error."
    fi

    # Extract tarball
    info "Extracting source tarball..."
    tar -xzf "$tarball_path" -C "$temp_dir" || error "Failed to extract tarball"

    # Find extracted directory (should be z3-<version> without the 'z3-' prefix in tag)
    local source_dir
    source_dir=$(find "$temp_dir" -maxdepth 1 -type d -name "z3-*" ! -path "$temp_dir" | head -n 1)

    if [[ -z "$source_dir" ]]; then
        error "Could not find extracted Z3 source directory"
    fi

    info "Source directory: $source_dir"

    # Create Dockerfile for building Z3
    local dockerfile="$temp_dir/Dockerfile"
    cat > "$dockerfile" << 'EOF'
FROM almalinux:8

# Install build dependencies
RUN dnf install -y \
    gcc-toolset-14 \
    cmake \
    make \
    python3 \
    git \
    && dnf clean all

# Enable GCC 14 toolset
ENV PATH=/opt/rh/gcc-toolset-14/root/usr/bin:$PATH \
    LD_LIBRARY_PATH=/opt/rh/gcc-toolset-14/root/usr/lib64:$LD_LIBRARY_PATH

# Set working directory
WORKDIR /build

# Copy source code
COPY z3-source /build/z3

# Build Z3
WORKDIR /build/z3
RUN python3 scripts/mk_make.py \
    --prefix=/opt/z3 \
    --staticlib \
    --build=BUILD_TYPE_PLACEHOLDER && \
    cd BUILD_TYPE_PLACEHOLDER && \
    make -j$(nproc) && \
    make install

# Create a marker file to indicate successful build
RUN touch /opt/z3/BUILD_SUCCESS
EOF

    # Replace build type placeholder
    sed -i "s/BUILD_TYPE_PLACEHOLDER/$build_type/g" "$dockerfile"

    # Copy source to build context
    cp -r "$source_dir" "$temp_dir/z3-source"

    # Build Docker image with platform specification
    local image_name="z3-builder-$$"
    info "Building Docker image for $docker_platform..."
    docker build --platform="$docker_platform" -t "$image_name" -f "$dockerfile" "$temp_dir" || error "Docker build failed"

    # Create container to extract files
    info "Creating container to extract build artifacts..."
    local container_name="z3-extract-$$"
    docker create --name "$container_name" "$image_name" || error "Failed to create container"

    # Check if build was successful
    if ! docker cp "$container_name:/opt/z3/BUILD_SUCCESS" "$temp_dir/" 2>/dev/null; then
        docker rm "$container_name" >/dev/null 2>&1 || true
        docker rmi "$image_name" >/dev/null 2>&1 || true
        error "Z3 build failed - BUILD_SUCCESS marker not found"
    fi

    # Create output directory
    mkdir -p "$output_dir"

    # Extract installation files
    info "Extracting installation files to: $output_dir"
    docker cp "$container_name:/opt/z3/." "$output_dir/" || error "Failed to extract files from container"

    # Clean up Docker resources
    info "Cleaning up Docker resources..."
    docker rm "$container_name" >/dev/null 2>&1 || true
    docker rmi "$image_name" >/dev/null 2>&1 || true

    # Remove BUILD_SUCCESS marker from output
    rm -f "$output_dir/BUILD_SUCCESS"

    # Create version file
    echo "$version" > "$output_dir/VERSION"

    # Display summary
    info "Build completed successfully!"
    info "Z3 version: $version"
    info "Build type: $build_type"
    info "Installation directory: $(cd "$output_dir" && pwd)"
    info ""
    info "Contents:"
    ls -lh "$output_dir"

    # Display library information
    if [[ -d "$output_dir/lib" ]]; then
        info ""
        info "Libraries:"
        ls -lh "$output_dir/lib"
    fi

    if [[ -d "$output_dir/bin" ]]; then
        info ""
        info "Binaries:"
        ls -lh "$output_dir/bin"
    fi
}

# Run the function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Check for help flag
    if [[ $# -gt 0 ]] && [[ "$1" == "-h" || "$1" == "--help" || "$1" == "help" ]]; then
        echo "Usage: $0 [output_dir] [build_type] [architecture]" >&2
        echo "" >&2
        echo "Arguments:" >&2
        echo "  output_dir    - Directory to extract Z3 installation (default: ./z3-build)" >&2
        echo "  build_type    - CMake build type: Release, Debug, RelWithDebInfo, or MinSizeRel (default: Release)" >&2
        echo "  architecture  - Target architecture: x64, amd64, x86_64, arm64, or aarch64 (default: x64)" >&2
        echo "" >&2
        echo "Examples:" >&2
        echo "  $0                              # Build x64 to ./z3-build with Release configuration" >&2
        echo "  $0 /opt/z3                      # Build x64 to /opt/z3 with Release configuration" >&2
        echo "  $0 ./z3-debug Debug             # Build x64 to ./z3-debug with Debug configuration" >&2
        echo "  $0 ./z3-arm64 Release arm64     # Build arm64 to ./z3-arm64 with Release configuration" >&2
        echo "  $0 ./z3-x64 Release x64         # Build x64 to ./z3-x64 with Release configuration" >&2
        exit 0
    fi

    if [[ $# -eq 0 ]]; then
        build_z3_with_docker
    elif [[ $# -eq 1 ]]; then
        build_z3_with_docker "$1"
    elif [[ $# -eq 2 ]]; then
        build_z3_with_docker "$1" "$2"
    elif [[ $# -eq 3 ]]; then
        build_z3_with_docker "$1" "$2" "$3"
    else
        echo "Usage: $0 [output_dir] [build_type] [architecture]" >&2
        echo "" >&2
        echo "Too many arguments provided." >&2
        echo "Run '$0 --help' for usage information." >&2
        exit 1
    fi
fi
