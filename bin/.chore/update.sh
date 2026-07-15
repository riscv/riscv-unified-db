#!/bin/bash

# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# Update operations for bin/chore
# This file contains all update-related subcommands

#
# Update Ruby gems
# Returns: 0 on success, exits with 1 on error
#
do_update_gems() {
  # first, update Gemfile.lock files and sorbet definitions.
  # Delete all lockfiles first so --update resolves fresh, then re-lock root
  # before per-gem files so they are derived from the same resolved graph.
  rm "${UDB_ROOT}"/Gemfile.lock
  rm "${UDB_ROOT}"/tools/ruby-gems/idlc/Gemfile.lock
  rm "${UDB_ROOT}"/tools/ruby-gems/udb/Gemfile.lock
  rm "${UDB_ROOT}"/tools/ruby-gems/udb-gen/Gemfile.lock
  rm "${UDB_ROOT}"/tools/ruby-gems/udb_helpers/Gemfile.lock
  do_lock_all_gemfiles --update --bundler

  "${UDB_ROOT}"/bin/bundle exec bundle install
  do_ruby_type_def idlc
  do_ruby_type_def udb
  do_ruby_type_def udb-gen
}

# Read a git-pinned binary dependency version from its *_VERSION file.
# Args: $1 - tool/release prefix, e.g. "espresso"
#       $2 - version file path
#       $3 - output variable for the full version string
#       $4 - output variable for the git commit portion
read_git_pinned_tool_version() {
  local tool=$1
  local version_file=$2
  local version_var=$3
  local commit_var=$4
  local version
  local commit

  version=$(<"${version_file}") || {
    echo "ERROR: Could not read ${version_file}" >&2
    exit 1
  }

  if [[ "${version}" != "${tool}-"* ]]; then
    echo "ERROR: Invalid ${version_file}: expected ${tool}-<git-commit>, got '${version}'" >&2
    exit 1
  fi

  commit="${version#${tool}-}"
  if [[ ! "${commit}" =~ ^[a-f0-9]{7,40}$ ]]; then
    echo "ERROR: Invalid ${version_file}: expected ${tool}-<7-to-40-char-hex-commit>, got '${version}'" >&2
    exit 1
  fi

  printf -v "${version_var}" "%s" "${version}"
  printf -v "${commit_var}" "%s" "${commit}"
}

#
# Update espresso binary
# Args: $1 - native_only ("yes" to build only for native platform, "no" for both x64 and arm64)
#       $2 - force ("yes" to force rebuild even if release exists, "no" otherwise)
# Returns: 0 on success, exits with 1 on error
#
do_update_espresso() {
  local native_only=$1
  local force=${2:-no}

  # Requires: docker (for build_espresso_with_docker.sh) and gh (GitHub CLI, authenticated)
  if ! command -v gh &>/dev/null; then
    echo "ERROR: 'gh' CLI is required for 'chore update espresso'. Install from https://cli.github.com" >&2
    exit 1
  fi

  # ESPRESSO_VERSION is the source of truth for both the release tag and git commit.
  local espresso_version_file="${UDB_ROOT}/tools/ruby-gems/udb/lib/udb/ESPRESSO_VERSION"
  local espresso_version
  local espresso_commit
  read_git_pinned_tool_version espresso "${espresso_version_file}" espresso_version espresso_commit
  echo "==> Building espresso version: ${espresso_version} (commit: ${espresso_commit})"

  # Check if the GitHub Release exists
  local release_exists=no
  if gh release view "${espresso_version}" --repo riscv/riscv-unified-db &>/dev/null; then
    release_exists=yes
  fi

  # Handle based on force flag and release existence
  if [ "${force}" != "yes" ] && [ "${release_exists}" = "yes" ]; then
    echo "==> GitHub Release ${espresso_version} already exists. Nothing to do."
    echo "    Use -f flag to force rebuild."
    return 0
  fi

  if [ "${force}" = "yes" ] && [ "${release_exists}" = "yes" ]; then
    echo "==> Force rebuild enabled..."
    # Only delete the release if we're building both architectures (not native_only)
    # For native_only builds, we'll use --clobber to replace individual assets
    if [ "${native_only}" != "yes" ]; then
      echo "==> Deleting existing GitHub Release ${espresso_version}..."
      gh release delete "${espresso_version}" --repo riscv/riscv-unified-db --yes
    else
      echo "==> Will replace existing assets with --clobber"
    fi
  fi

  echo "==> Building espresso ${espresso_version}..."

  local orig_dir="${PWD}"
  local work_dir
  work_dir=$(mktemp -d --tmpdir="$PWD" build-espresso.XXXXXX)

  if [ "${native_only}" = "yes" ]; then
    # Detect native architecture
    local native_arch
    case "$(uname -m)" in
      x86_64)
        native_arch="x64"
        ;;
      aarch64)
        native_arch="arm64"
        ;;
      *)
        echo "ERROR: Unsupported architecture: $(uname -m)" >&2
        exit 1
        ;;
    esac
    echo "==> Building espresso for native platform (${native_arch})..."
    "${UDB_ROOT}"/tools/scripts/build_espresso_with_docker.sh "${work_dir}/espresso-build" "${native_arch}" || exit 1

    # Move the binary to the asset name expected by the gem
    mv "${work_dir}/espresso-build/espresso" "${work_dir}/espresso-${native_arch}"

    # Generate checksum
    echo "==> Generating checksum..."
    (cd "${work_dir}" && sha256sum "espresso-${native_arch}" | awk '{print "sha256:" $1}' > "espresso-${native_arch}.checksum")
    echo "  ${native_arch}: $(cat "${work_dir}/espresso-${native_arch}.checksum")"
  else
    # Build for both architectures
    echo "==> Building espresso for x64..."
    "${UDB_ROOT}"/tools/scripts/build_espresso_with_docker.sh "${work_dir}/espresso-x64-out" x64 || exit 1

    echo "==> Building espresso for arm64..."
    "${UDB_ROOT}"/tools/scripts/build_espresso_with_docker.sh "${work_dir}/espresso-arm64-out" arm64 || exit 1

    # Rename the binaries to the asset names expected by the gem
    mv "${work_dir}/espresso-x64-out/espresso" "${work_dir}/espresso-x64"
    mv "${work_dir}/espresso-arm64-out/espresso" "${work_dir}/espresso-arm64"

    # Generate checksums
    echo "==> Generating checksums..."
    (cd "${work_dir}" && sha256sum espresso-x64 | awk '{print "sha256:" $1}' > espresso-x64.checksum)
    (cd "${work_dir}" && sha256sum espresso-arm64 | awk '{print "sha256:" $1}' > espresso-arm64.checksum)
    echo "  x64:   $(cat "${work_dir}/espresso-x64.checksum")"
    echo "  arm64: $(cat "${work_dir}/espresso-arm64.checksum")"
  fi

  # Create the GitHub Release and upload assets (or upload to existing release if native_only)
  local release_tag="${espresso_version}"
  if [ "${native_only}" = "yes" ]; then
    # Detect native architecture
    local native_arch
    case "$(uname -m)" in
      x86_64)
        native_arch="x64"
        ;;
      aarch64)
        native_arch="arm64"
        ;;
    esac
    echo "==> Uploading ${native_arch} assets to GitHub Release ${release_tag}..."
    # Try to upload; if release doesn't exist, create it first (for parallel CI builds)
    if ! gh release upload "${release_tag}" \
      --repo riscv/riscv-unified-db \
      --clobber \
      "${work_dir}/espresso-${native_arch}" \
      "${work_dir}/espresso-${native_arch}.checksum" 2>/dev/null; then
      echo "==> Release doesn't exist yet, creating it..."
      gh release create "${release_tag}" \
        --repo riscv/riscv-unified-db \
        --title "Espresso binaries ${espresso_version}" \
        --notes "Pre-built espresso binaries for the udb gem (Linux x64 and arm64, built on AlmaLinux 8). Commit: ${espresso_commit}" \
        "${work_dir}/espresso-${native_arch}" \
        "${work_dir}/espresso-${native_arch}.checksum"
    fi
  else
    echo "==> Creating GitHub Release ${release_tag}..."
    gh release create "${release_tag}" \
      --repo riscv/riscv-unified-db \
      --title "Espresso binaries ${espresso_version}" \
      --notes "Pre-built espresso binaries for the udb gem (Linux x64 and arm64, built on AlmaLinux 8). Commit: ${espresso_commit}" \
      "${work_dir}/espresso-x64" \
      "${work_dir}/espresso-arm64" \
      "${work_dir}/espresso-x64.checksum" \
      "${work_dir}/espresso-arm64.checksum"
  fi

  cd "${orig_dir}" || exit 1
  rm -rf "${work_dir}"

  echo ""
  echo "Done. GitHub Release ${espresso_version} created on riscv/riscv-unified-db."
}

#
# Update must binary
# Args: $1 - native_only ("yes" to build only for native platform, "no" for both x64 and arm64)
#       $2 - force ("yes" to force rebuild even if release exists, "no" otherwise)
# Returns: 0 on success, exits with 1 on error
#
do_update_must() {
  local native_only=$1
  local force=${2:-no}

  # Requires: docker (for build_must_with_docker.sh) and gh (GitHub CLI, authenticated)
  if ! command -v gh &>/dev/null; then
    echo "ERROR: 'gh' CLI is required for 'chore update must'. Install from https://cli.github.com" >&2
    exit 1
  fi

  # MUST_VERSION is the source of truth for both the release tag and git commit.
  local must_version_file="${UDB_ROOT}/tools/ruby-gems/udb/lib/udb/MUST_VERSION"
  local must_version
  local must_commit
  read_git_pinned_tool_version must "${must_version_file}" must_version must_commit
  echo "==> Building must version: ${must_version} (commit: ${must_commit})"

  # Check if the GitHub Release exists
  local release_exists=no
  if gh release view "${must_version}" --repo riscv/riscv-unified-db &>/dev/null; then
    release_exists=yes
  fi

  # Handle based on force flag and release existence
  if [ "${force}" != "yes" ] && [ "${release_exists}" = "yes" ]; then
    echo "==> GitHub Release ${must_version} already exists. Nothing to do."
    echo "    Use -f flag to force rebuild."
    return 0
  fi

  if [ "${force}" = "yes" ] && [ "${release_exists}" = "yes" ]; then
    echo "==> Force rebuild enabled..."
    # Only delete the release if we're building both architectures (not native_only)
    # For native_only builds, we'll use --clobber to replace individual assets
    if [ "${native_only}" != "yes" ]; then
      echo "==> Deleting existing GitHub Release ${must_version}..."
      gh release delete "${must_version}" --repo riscv/riscv-unified-db --yes
    else
      echo "==> Will replace existing assets with --clobber"
    fi
  fi

  echo "==> Building must ${must_version}..."

  local orig_dir="${PWD}"
  local work_dir
  work_dir=$(mktemp -d --tmpdir="$PWD" build-must.XXXXXX)

  if [ "${native_only}" = "yes" ]; then
    # Detect native architecture
    local native_arch
    case "$(uname -m)" in
      x86_64)
        native_arch="x64"
        ;;
      aarch64)
        native_arch="arm64"
        ;;
      *)
        echo "ERROR: Unsupported architecture: $(uname -m)" >&2
        exit 1
        ;;
    esac
    echo "==> Building must for native platform (${native_arch})..."
    "${UDB_ROOT}"/tools/scripts/build_must_with_docker.sh "${work_dir}/must-build" "${native_arch}" || exit 1

    # Move the binary to the asset name expected by the gem
    mv "${work_dir}/must-build/must" "${work_dir}/must-${native_arch}"

    # Generate checksum
    echo "==> Generating checksum..."
    (cd "${work_dir}" && sha256sum "must-${native_arch}" | awk '{print "sha256:" $1}' > "must-${native_arch}.checksum")
    echo "  ${native_arch}: $(cat "${work_dir}/must-${native_arch}.checksum")"
  else
    # Build for both architectures
    echo "==> Building must for x64..."
    "${UDB_ROOT}"/tools/scripts/build_must_with_docker.sh "${work_dir}/must-x64-out" x64 || exit 1

    echo "==> Building must for arm64..."
    "${UDB_ROOT}"/tools/scripts/build_must_with_docker.sh "${work_dir}/must-arm64-out" arm64 || exit 1

    # Rename the binaries to the asset names expected by the gem
    mv "${work_dir}/must-x64-out/must" "${work_dir}/must-x64"
    mv "${work_dir}/must-arm64-out/must" "${work_dir}/must-arm64"

    # Generate checksums
    echo "==> Generating checksums..."
    (cd "${work_dir}" && sha256sum must-x64 | awk '{print "sha256:" $1}' > must-x64.checksum)
    (cd "${work_dir}" && sha256sum must-arm64 | awk '{print "sha256:" $1}' > must-arm64.checksum)
    echo "  x64:   $(cat "${work_dir}/must-x64.checksum")"
    echo "  arm64: $(cat "${work_dir}/must-arm64.checksum")"
  fi

  # Create the GitHub Release and upload assets
  local release_tag="${must_version}"
  if [ "${native_only}" = "yes" ]; then
    # Detect native architecture
    local native_arch
    case "$(uname -m)" in
      x86_64)
        native_arch="x64"
        ;;
      aarch64)
        native_arch="arm64"
        ;;
    esac
    echo "==> Uploading ${native_arch} assets to GitHub Release ${release_tag}..."
    # Try to upload; if release doesn't exist, create it first (for parallel CI builds)
    if ! gh release upload "${release_tag}" \
      --repo riscv/riscv-unified-db \
      --clobber \
      "${work_dir}/must-${native_arch}" \
      "${work_dir}/must-${native_arch}.checksum" 2>/dev/null; then
      echo "==> Release doesn't exist yet, creating it..."
      gh release create "${release_tag}" \
        --repo riscv/riscv-unified-db \
        --title "Must binaries ${must_version}" \
        --notes "Pre-built must (mustool) binaries for the udb gem (Linux x64 and arm64, built on AlmaLinux 8). Commit: ${must_commit}" \
        "${work_dir}/must-${native_arch}" \
        "${work_dir}/must-${native_arch}.checksum"
    fi
  else
    echo "==> Creating GitHub Release ${release_tag}..."
    gh release create "${release_tag}" \
      --repo riscv/riscv-unified-db \
      --title "Must binaries ${must_version}" \
      --notes "Pre-built must (mustool) binaries for the udb gem (Linux x64 and arm64, built on AlmaLinux 8). Commit: ${must_commit}" \
      "${work_dir}/must-x64" \
      "${work_dir}/must-arm64" \
      "${work_dir}/must-x64.checksum" \
      "${work_dir}/must-arm64.checksum"
  fi

  cd "${orig_dir}" || exit 1
  rm -rf "${work_dir}"

  echo ""
  echo "Done. GitHub Release ${must_version} created on riscv/riscv-unified-db."
}

#
# Update eqntott binary
# Args: $1 - native_only ("yes" to build only for native platform, "no" for both x64 and arm64)
#       $2 - force ("yes" to force rebuild even if release exists, "no" otherwise)
# Returns: 0 on success, exits with 1 on error
#
do_update_eqntott() {
  local native_only=$1
  local force=${2:-no}

  # Requires: docker (for build_eqntott_with_docker.sh) and gh (GitHub CLI, authenticated)
  if ! command -v gh &>/dev/null; then
    echo "ERROR: 'gh' CLI is required for 'chore update eqntott'. Install from https://cli.github.com" >&2
    exit 1
  fi

  # EQNTOTT_VERSION is the source of truth for both the release tag and git commit.
  local eqntott_version_file="${UDB_ROOT}/tools/ruby-gems/udb/lib/udb/EQNTOTT_VERSION"
  local eqntott_version
  local eqntott_commit
  read_git_pinned_tool_version eqntott "${eqntott_version_file}" eqntott_version eqntott_commit
  echo "==> Building eqntott version: ${eqntott_version} (commit: ${eqntott_commit})"

  # Check if the GitHub Release exists
  local release_exists=no
  if gh release view "${eqntott_version}" --repo riscv/riscv-unified-db &>/dev/null; then
    release_exists=yes
  fi

  # Handle based on force flag and release existence
  if [ "${force}" != "yes" ] && [ "${release_exists}" = "yes" ]; then
    echo "==> GitHub Release ${eqntott_version} already exists. Nothing to do."
    echo "    Use -f flag to force rebuild."
    return 0
  fi

  if [ "${force}" = "yes" ] && [ "${release_exists}" = "yes" ]; then
    echo "==> Force rebuild enabled..."
    # Only delete the release if we're building both architectures (not native_only)
    # For native_only builds, we'll use --clobber to replace individual assets
    if [ "${native_only}" != "yes" ]; then
      echo "==> Deleting existing GitHub Release ${eqntott_version}..."
      gh release delete "${eqntott_version}" --repo riscv/riscv-unified-db --yes
    else
      echo "==> Will replace existing assets with --clobber"
    fi
  fi

  echo "==> Building eqntott ${eqntott_version}..."

  local orig_dir="${PWD}"
  local work_dir
  work_dir=$(mktemp -d --tmpdir="$PWD" build-eqntott.XXXXXX)

  if [ "${native_only}" = "yes" ]; then
    # Detect native architecture
    local native_arch
    case "$(uname -m)" in
      x86_64)
        native_arch="x64"
        ;;
      aarch64)
        native_arch="arm64"
        ;;
      *)
        echo "ERROR: Unsupported architecture: $(uname -m)" >&2
        exit 1
        ;;
    esac
    echo "==> Building eqntott for native platform (${native_arch})..."
    "${UDB_ROOT}"/tools/scripts/build_eqntott_with_docker.sh "${work_dir}/eqntott-build" "${native_arch}" || exit 1

    # Move the binary to the asset name expected by the gem
    mv "${work_dir}/eqntott-build/eqntott" "${work_dir}/eqntott-${native_arch}"

    # Generate checksum
    echo "==> Generating checksum..."
    (cd "${work_dir}" && sha256sum "eqntott-${native_arch}" | awk '{print "sha256:" $1}' > "eqntott-${native_arch}.checksum")
    echo "  ${native_arch}: $(cat "${work_dir}/eqntott-${native_arch}.checksum")"
  else
    # Build for both architectures
    echo "==> Building eqntott for x64..."
    "${UDB_ROOT}"/tools/scripts/build_eqntott_with_docker.sh "${work_dir}/eqntott-x64-out" x64 || exit 1

    echo "==> Building eqntott for arm64..."
    "${UDB_ROOT}"/tools/scripts/build_eqntott_with_docker.sh "${work_dir}/eqntott-arm64-out" arm64 || exit 1

    # Rename the binaries to the asset names expected by the gem
    mv "${work_dir}/eqntott-x64-out/eqntott" "${work_dir}/eqntott-x64"
    mv "${work_dir}/eqntott-arm64-out/eqntott" "${work_dir}/eqntott-arm64"

    # Generate checksums
    echo "==> Generating checksums..."
    (cd "${work_dir}" && sha256sum eqntott-x64 | awk '{print "sha256:" $1}' > eqntott-x64.checksum)
    (cd "${work_dir}" && sha256sum eqntott-arm64 | awk '{print "sha256:" $1}' > eqntott-arm64.checksum)
    echo "  x64:   $(cat "${work_dir}/eqntott-x64.checksum")"
    echo "  arm64: $(cat "${work_dir}/eqntott-arm64.checksum")"
  fi

  # Create the GitHub Release and upload assets
  local release_tag="${eqntott_version}"
  if [ "${native_only}" = "yes" ]; then
    # Detect native architecture
    local native_arch
    case "$(uname -m)" in
      x86_64)
        native_arch="x64"
        ;;
      aarch64)
        native_arch="arm64"
        ;;
    esac
    echo "==> Uploading ${native_arch} assets to GitHub Release ${release_tag}..."
    # Try to upload; if release doesn't exist, create it first (for parallel CI builds)
    if ! gh release upload "${release_tag}" \
      --repo riscv/riscv-unified-db \
      --clobber \
      "${work_dir}/eqntott-${native_arch}" \
      "${work_dir}/eqntott-${native_arch}.checksum" 2>/dev/null; then
      echo "==> Release doesn't exist yet, creating it..."
      gh release create "${release_tag}" \
        --repo riscv/riscv-unified-db \
        --title "eqntott binaries ${eqntott_version}" \
        --notes "Pre-built eqntott binaries for the udb gem (Linux x64 and arm64, built on AlmaLinux 8). Commit: ${eqntott_commit}" \
        "${work_dir}/eqntott-${native_arch}" \
        "${work_dir}/eqntott-${native_arch}.checksum"
    fi
  else
    echo "==> Creating GitHub Release ${release_tag}..."
    gh release create "${release_tag}" \
      --repo riscv/riscv-unified-db \
      --title "eqntott binaries ${eqntott_version}" \
      --notes "Pre-built eqntott binaries for the udb gem (Linux x64 and arm64, built on AlmaLinux 8). Commit: ${eqntott_commit}" \
      "${work_dir}/eqntott-x64" \
      "${work_dir}/eqntott-arm64" \
      "${work_dir}/eqntott-x64.checksum" \
      "${work_dir}/eqntott-arm64.checksum"
  fi

  cd "${orig_dir}" || exit 1
  rm -rf "${work_dir}"

  echo ""
  echo "Done. GitHub Release ${eqntott_version} created on riscv/riscv-unified-db."
}

#
# Update Z3 shared library
# Args: $1 - native_only ("yes" to build only for native platform, "no" for both x64 and arm64)
#       $2 - force ("yes" to force rebuild even if release exists, "no" otherwise)
# Returns: 0 on success, exits with 1 on error
#
do_update_z3() {
  local native_only=$1
  local force=${2:-no}

  # Requires: docker (for build_z3_with_docker.sh) and gh (GitHub CLI, authenticated)
  if ! command -v gh &>/dev/null; then
    echo "ERROR: 'gh' CLI is required for 'chore update z3'. Install from https://cli.github.com" >&2
    exit 1
  fi

  # Z3_VERSION is the source of truth for the release tag and upstream version.
  local z3_version_file="${UDB_ROOT}/tools/ruby-gems/udb/lib/udb/Z3_VERSION"
  local z3_version
  z3_version=$(<"${z3_version_file}") || {
    echo "ERROR: Could not read ${z3_version_file}" >&2
    exit 1
  }

  if [[ ! "${z3_version}" =~ ^z3-[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "ERROR: Invalid ${z3_version_file}: expected z3-<major>.<minor>.<patch>, got '${z3_version}'" >&2
    exit 1
  fi

  echo "==> Building Z3 version: ${z3_version}"

  # Check if the GitHub Release exists
  local release_exists=no
  if gh release view "${z3_version}" --repo riscv/riscv-unified-db &>/dev/null; then
    release_exists=yes
  fi

  # Handle based on force flag and release existence
  if [ "${force}" != "yes" ] && [ "${release_exists}" = "yes" ]; then
    echo "==> GitHub Release ${z3_version} already exists. Nothing to do."
    echo "    Use -f flag to force rebuild."
    return 0
  fi

  if [ "${force}" = "yes" ] && [ "${release_exists}" = "yes" ]; then
    echo "==> Force rebuild enabled..."
    # Only delete the release if we're building both architectures (not native_only)
    # For native_only builds, we'll use --clobber to replace individual assets
    if [ "${native_only}" != "yes" ]; then
      echo "==> Deleting existing GitHub Release ${z3_version}..."
      gh release delete "${z3_version}" --repo riscv/riscv-unified-db --yes
    else
      echo "==> Will replace existing assets with --clobber"
    fi
  fi

  echo "==> Building Z3 ${z3_version}..."

  local orig_dir="${PWD}"
  local work_dir
  work_dir=$(mktemp -d --tmpdir="$PWD" build-z3.XXXXXX)

  if [ "${native_only}" = "yes" ]; then
    # Detect native architecture
    local native_arch
    case "$(uname -m)" in
      x86_64)
        native_arch="x64"
        ;;
      aarch64)
        native_arch="arm64"
        ;;
      *)
        echo "ERROR: Unsupported architecture: $(uname -m)" >&2
        exit 1
        ;;
    esac
    echo "==> Building Z3 for native platform (${native_arch})..."
    "${UDB_ROOT}"/tools/scripts/build_z3_with_docker.sh "${work_dir}/z3-${native_arch}" Release "${native_arch}" || exit 1

    local built_version
    built_version=$(cat "${work_dir}/z3-${native_arch}/VERSION")
    if [ "${built_version}" != "${z3_version}" ]; then
      echo "ERROR: Built Z3 version ${built_version} does not match ${z3_version}" >&2
      exit 1
    fi

    # Rename the .so file to the asset name expected by extconf.rb / setup_z3
    cp "${work_dir}/z3-${native_arch}/lib/libz3.so" "${work_dir}/libz3-${native_arch}.so"
  else
    # Build for both architectures
    echo "==> Building Z3 for x64..."
    "${UDB_ROOT}"/tools/scripts/build_z3_with_docker.sh "${work_dir}/z3-x64" Release x64 || exit 1

    echo "==> Building Z3 for arm64..."
    "${UDB_ROOT}"/tools/scripts/build_z3_with_docker.sh "${work_dir}/z3-arm64" Release arm64 || exit 1

    local built_version
    built_version=$(cat "${work_dir}/z3-x64/VERSION")
    if [ "${built_version}" != "${z3_version}" ]; then
      echo "ERROR: Built Z3 version ${built_version} does not match ${z3_version}" >&2
      exit 1
    fi

    # Rename the .so files to the asset names expected by extconf.rb / setup_z3
    cp "${work_dir}/z3-x64/lib/libz3.so"   "${work_dir}/libz3-x64.so"
    cp "${work_dir}/z3-arm64/lib/libz3.so" "${work_dir}/libz3-arm64.so"
  fi

  # Generate checksum files
  echo "==> Generating checksums..."
  if [ "${native_only}" = "yes" ]; then
    # Detect native architecture
    local native_arch
    case "$(uname -m)" in
      x86_64)
        native_arch="x64"
        ;;
      aarch64)
        native_arch="arm64"
        ;;
    esac
    (cd "${work_dir}" && sha256sum "libz3-${native_arch}.so" | awk '{print "sha256:" $1}' > "libz3-${native_arch}.checksum")
    echo "  ${native_arch}: $(cat "${work_dir}/libz3-${native_arch}.checksum")"
  else
    (cd "${work_dir}" && sha256sum libz3-x64.so | awk '{print "sha256:" $1}' > libz3-x64.checksum)
    (cd "${work_dir}" && sha256sum libz3-arm64.so | awk '{print "sha256:" $1}' > libz3-arm64.checksum)
    echo "  x64:   $(cat "${work_dir}/libz3-x64.checksum")"
    echo "  arm64: $(cat "${work_dir}/libz3-arm64.checksum")"
  fi

  # Create the GitHub Release and upload assets (or upload to existing release if native_only)
  local release_tag="${z3_version}"
  if [ "${native_only}" = "yes" ]; then
    # Detect native architecture
    local native_arch
    case "$(uname -m)" in
      x86_64)
        native_arch="x64"
        ;;
      aarch64)
        native_arch="arm64"
        ;;
    esac
    echo "==> Uploading ${native_arch} assets to GitHub Release ${release_tag}..."
    # Try to upload; if release doesn't exist, create it first (for parallel CI builds)
    if ! gh release upload "${release_tag}" \
      --repo riscv/riscv-unified-db \
      --clobber \
      "${work_dir}/libz3-${native_arch}.so" \
      "${work_dir}/libz3-${native_arch}.checksum" 2>/dev/null; then
      echo "==> Release doesn't exist yet, creating it..."
      gh release create "${release_tag}" \
        --repo riscv/riscv-unified-db \
        --title "Z3 binaries ${z3_version}" \
        --notes "Pre-built Z3 shared libraries for the udb gem (Linux x64 and arm64, built on AlmaLinux 8)." \
        "${work_dir}/libz3-${native_arch}.so" \
        "${work_dir}/libz3-${native_arch}.checksum"
    fi
  else
    echo "==> Creating GitHub Release ${release_tag}..."
    gh release create "${release_tag}" \
      --repo riscv/riscv-unified-db \
      --title "Z3 binaries ${z3_version}" \
      --notes "Pre-built Z3 shared libraries for the udb gem (Linux x64 and arm64, built on AlmaLinux 8)." \
      "${work_dir}/libz3-x64.so" \
      "${work_dir}/libz3-arm64.so" \
      "${work_dir}/libz3-x64.checksum" \
      "${work_dir}/libz3-arm64.checksum"
  fi

  cd "${orig_dir}" || exit 1
  rm -rf "${work_dir}"

  echo ""
  echo "Done. GitHub Release ${z3_version} created on riscv/riscv-unified-db."
}

# Portable sha256 of a single file, printing just the hex digest.
_chore_sha256() {
  if command -v sha256sum &>/dev/null; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

#
# Build and publish the prebuilt tree-sitter IDL grammar shared library.
#
# Unlike z3/espresso/eqntott/must (built for several Linux arches via Docker on
# one runner), the grammar is a native shared object that must be built on the
# matching OS, so this always builds for the *native* (OS, CPU) only. The
# release_udb_deps.yml workflow fans out across linux/macos x64/arm64 runners,
# each uploading its own asset to the shared release with --clobber.
#
# Args: $1 - native_only (accepted for interface symmetry; always native)
#       $2 - force ("yes" to re-upload even if the asset already exists)
# Returns: 0 on success, exits with 1 on error
#
do_update_tree_sitter_idl() {
  local force=${2:-no}

  if ! command -v gh &>/dev/null; then
    echo "ERROR: 'gh' CLI is required for 'chore update tree-sitter-idl'. Install from https://cli.github.com" >&2
    exit 1
  fi

  local grammar_dir="${UDB_ROOT}/tools/node/tree-sitter-idl"
  local version_file="${grammar_dir}/TS_IDL_VERSION"
  local version
  version=$(tr -d '[:space:]' < "${version_file}") || {
    echo "ERROR: Could not read ${version_file}" >&2
    exit 1
  }
  local release_tag="tree-sitter-idl-${version}"
  echo "==> tree-sitter-idl version: ${version} (release tag ${release_tag})"

  # Detect native OS + CPU and the matching shared-object extension.
  local os ext
  case "$(uname -s)" in
    Darwin) os=macos; ext=dylib ;;
    Linux)  os=linux; ext=so ;;
    *) echo "ERROR: Unsupported OS: $(uname -s)" >&2; exit 1 ;;
  esac
  local cpu
  case "$(uname -m)" in
    x86_64)        cpu=x64 ;;
    arm64|aarch64) cpu=arm64 ;;
    *) echo "ERROR: Unsupported architecture: $(uname -m)" >&2; exit 1 ;;
  esac
  local asset="libtree-sitter-idl-${os}-${cpu}.${ext}"

  # If the asset already exists in the release and we're not forcing, skip.
  if [ "${force}" != "yes" ] && gh release view "${release_tag}" --repo riscv/riscv-unified-db &>/dev/null; then
    if gh release view "${release_tag}" --repo riscv/riscv-unified-db --json assets \
         --jq '.assets[].name' 2>/dev/null | grep -qx "${asset}"; then
      echo "==> ${asset} already present in ${release_tag}. Nothing to do (use -f to rebuild)."
      return 0
    fi
  fi

  echo "==> Building ${asset}..."
  # parser.c is committed but generated from grammar.json; touch it so make does
  # not try to regenerate it (which would require the tree-sitter CLI).
  [ -f "${grammar_dir}/src/parser.c" ] && touch "${grammar_dir}/src/parser.c"
  if ! make -C "${grammar_dir}" "libtree-sitter-idl.${ext}"; then
    echo "ERROR: Failed to build libtree-sitter-idl.${ext}. Ensure a C compiler is installed." >&2
    exit 1
  fi

  local orig_dir="${PWD}"
  local work_dir
  work_dir=$(mktemp -d "${PWD}/build-ts-idl.XXXXXX") || {
    echo "ERROR: Could not create work directory" >&2
    exit 1
  }
  cp "${grammar_dir}/libtree-sitter-idl.${ext}" "${work_dir}/${asset}"

  echo "==> Generating checksum..."
  ( cd "${work_dir}" && echo "sha256:$(_chore_sha256 "${asset}")" > "${asset}.checksum" )
  echo "  $(cat "${work_dir}/${asset}.checksum")"

  echo "==> Uploading ${asset} to GitHub Release ${release_tag}..."
  # Upload to the existing release; create it first if it doesn't exist yet
  # (handles parallel CI matrix builds racing to create the release).
  if ! gh release upload "${release_tag}" \
    --repo riscv/riscv-unified-db \
    --clobber \
    "${work_dir}/${asset}" \
    "${work_dir}/${asset}.checksum" 2>/dev/null; then
    echo "==> Release doesn't exist yet, creating it..."
    gh release create "${release_tag}" \
      --repo riscv/riscv-unified-db \
      --title "tree-sitter-idl grammar ${version}" \
      --notes "Pre-built tree-sitter IDL grammar shared libraries for the idlc/udb gems (linux & macos, x64 & arm64)." \
      "${work_dir}/${asset}" \
      "${work_dir}/${asset}.checksum"
  fi

  cd "${orig_dir}" || exit 1
  rm -rf "${work_dir}"

  echo ""
  echo "Done. ${asset} uploaded to GitHub Release ${release_tag} on riscv/riscv-unified-db."
}
