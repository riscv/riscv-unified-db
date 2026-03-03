#!/usr/bin/env bash

# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear

# Update operations for bin/chore
# This file contains all update-related subcommands

#
# Update Ruby gems and optionally update container tag
# Args: $1 - update_tag ("yes" to increment container tag, "no" otherwise)
# Returns: 0 on success, exits with 1 on error
#
do_update_gems() {
  local update_tag=$1
  source "$UDB_ROOT"/bin/setup

  # first, update Gemfile.lock files
  # and sorbet definitions
  rm "${UDB_ROOT}"/tools/ruby-gems/idlc/Gemfile.lock
  $RUN bundle exec bundle lock --gemfile "${UDB_ROOT}"/tools/ruby-gems/idlc/Gemfile --lockfile "${UDB_ROOT}"/tools/ruby-gems/idlc/Gemfile.lock --update --bundler --add-platform x86_64-linux aarch64-linux
  rm "${UDB_ROOT}"/tools/ruby-gems/udb/Gemfile.lock
  $RUN bundle exec bundle lock --gemfile "${UDB_ROOT}"/tools/ruby-gems/udb/Gemfile --lockfile "${UDB_ROOT}"/tools/ruby-gems/udb/Gemfile.lock --update --bundler --add-platform x86_64-linux aarch64-linux
  rm "${UDB_ROOT}"/tools/ruby-gems/udb-gen/Gemfile.lock
  $RUN bundle exec bundle lock --gemfile "${UDB_ROOT}"/tools/ruby-gems/udb-gen/Gemfile --lockfile "${UDB_ROOT}"/tools/ruby-gems/udb-gen/Gemfile.lock --update --bundler --add-platform x86_64-linux aarch64-linux
  rm "${UDB_ROOT}"/Gemfile.lock
  $RUN bundle exec bundle lock --gemfile "${UDB_ROOT}"/Gemfile --lockfile "${UDB_ROOT}"/Gemfile.lock --update --bundler --add-platform x86_64-linux aarch64-linux

  # increment container-tag
  if [ "$update_tag" == "yes" ]; then
    new_version=$(increment_minor_version "$(cat bin/.container-tag)")
    echo "$new_version" > bin/.container-tag
  fi

  if [ "$CONTAINER_TYPE" == "native" ]; then
    bundle exec bundle install
    do_ruby_type_def idlc
    do_ruby_type_def udb
    do_ruby_type_def udb-gen
  else
    # rebuild the container
    build_container "${UDB_ROOT}"

    # need to run as a seperate process to pick up the new container
    # since we bumped the container tag, this will also cause the container to rebuild
    ./bin/chore gen ruby-type-def
  fi
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

  # For espresso, we use a fixed version since it builds from a fixed git repo
  local espresso_version="espresso-1.0"
  echo "==> Building espresso version: ${espresso_version}"

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
  else
    # Build for both architectures
    echo "==> Building espresso for x64..."
    "${UDB_ROOT}"/tools/scripts/build_espresso_with_docker.sh "${work_dir}/espresso-x64-out" x64 || exit 1

    echo "==> Building espresso for arm64..."
    "${UDB_ROOT}"/tools/scripts/build_espresso_with_docker.sh "${work_dir}/espresso-arm64-out" arm64 || exit 1

    # Rename the binaries to the asset names expected by the gem
    mv "${work_dir}/espresso-x64-out/espresso" "${work_dir}/espresso-x64"
    mv "${work_dir}/espresso-arm64-out/espresso" "${work_dir}/espresso-arm64"
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
      "${work_dir}/espresso-${native_arch}" 2>/dev/null; then
      echo "==> Release doesn't exist yet, creating it..."
      gh release create "${release_tag}" \
        --repo riscv/riscv-unified-db \
        --title "Espresso binaries ${espresso_version}" \
        --notes "Pre-built espresso binaries for the udb gem (Linux x64 and arm64, built on AlmaLinux 8)." \
        "${work_dir}/espresso-${native_arch}"
    fi
  else
    echo "==> Creating GitHub Release ${release_tag}..."
    gh release create "${release_tag}" \
      --repo riscv/riscv-unified-db \
      --title "Espresso binaries ${espresso_version}" \
      --notes "Pre-built espresso binaries for the udb gem (Linux x64 and arm64, built on AlmaLinux 8)." \
      "${work_dir}/espresso-x64" \
      "${work_dir}/espresso-arm64"
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

  # Read the commit hash from the build script
  local must_commit
  must_commit=$(grep '^MUST_COMMIT=' "${UDB_ROOT}/tools/scripts/build_must_with_docker.sh" | cut -d'"' -f2)
  if [ -z "$must_commit" ]; then
    echo "ERROR: Could not read MUST_COMMIT from build_must_with_docker.sh" >&2
    exit 1
  fi

  # Use short commit hash for the version tag
  local must_version="must-${must_commit:0:7}"
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
  else
    # Build for both architectures
    echo "==> Building must for x64..."
    "${UDB_ROOT}"/tools/scripts/build_must_with_docker.sh "${work_dir}/must-x64-out" x64 || exit 1

    echo "==> Building must for arm64..."
    "${UDB_ROOT}"/tools/scripts/build_must_with_docker.sh "${work_dir}/must-arm64-out" arm64 || exit 1

    # Rename the binaries to the asset names expected by the gem
    mv "${work_dir}/must-x64-out/must" "${work_dir}/must-x64"
    mv "${work_dir}/must-arm64-out/must" "${work_dir}/must-arm64"
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
      "${work_dir}/must-${native_arch}" 2>/dev/null; then
      echo "==> Release doesn't exist yet, creating it..."
      gh release create "${release_tag}" \
        --repo riscv/riscv-unified-db \
        --title "Must binaries ${must_version}" \
        --notes "Pre-built must (mustool) binaries for the udb gem (Linux x64 and arm64, built on AlmaLinux 8). Commit: ${must_commit}" \
        "${work_dir}/must-${native_arch}"
    fi
  else
    echo "==> Creating GitHub Release ${release_tag}..."
    gh release create "${release_tag}" \
      --repo riscv/riscv-unified-db \
      --title "Must binaries ${must_version}" \
      --notes "Pre-built must (mustool) binaries for the udb gem (Linux x64 and arm64, built on AlmaLinux 8). Commit: ${must_commit}" \
      "${work_dir}/must-x64" \
      "${work_dir}/must-arm64"
  fi

  cd "${orig_dir}" || exit 1
  rm -rf "${work_dir}"

  echo ""
  echo "Done. GitHub Release ${must_version} created on riscv/riscv-unified-db."
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

  # Read the version currently tracked in z3_version.rb
  local z3_version_rb="${UDB_ROOT}/tools/ruby-gems/udb/lib/udb/z3_version.rb"
  local current_version
  current_version=$(ruby -e "load '${z3_version_rb}'; puts Udb::Z3_VERSION" 2>/dev/null) || {
    echo "ERROR: Could not read current Z3 version from ${z3_version_rb}" >&2
    exit 1
  }
  echo "==> Current Z3 version in z3_version.rb: ${current_version}"

  # Query the latest Z3 release tag from upstream (Z3Prover/z3)
  local latest_version
  latest_version=$(gh release list --repo Z3Prover/z3 --limit 50 --json tagName \
    --jq '[.[] | select(.tagName | test("^z3-[0-9]+\\.[0-9]+\\.[0-9]+$"))] | .[0].tagName' 2>/dev/null) || {
    echo "ERROR: Could not query latest Z3 release from Z3Prover/z3. Check gh authentication." >&2
    exit 1
  }
  echo "==> Latest upstream Z3 release: ${latest_version}"

  # Compare versions: strip "z3-" prefix and use sort -V to determine which is newer
  local current_ver="${current_version#z3-}"
  local latest_ver="${latest_version#z3-}"
  local newest
  newest=$(printf '%s\n%s\n' "${current_ver}" "${latest_ver}" | sort -V | tail -1)

  # Determine the target version to build/release
  local target_version
  if [ "${latest_ver}" = "${current_ver}" ]; then
    echo "==> Z3 is already up to date (${current_version})."
    target_version="${current_version}"
  elif [ "${newest}" != "${latest_ver}" ]; then
    echo "==> Current version (${current_version}) is already newer than upstream (${latest_version})."
    target_version="${current_version}"
  else
    echo "==> New Z3 version available: ${latest_version} (current: ${current_version})."
    target_version="${latest_version}"
  fi

  # Check if the GitHub Release exists
  local release_exists=no
  if gh release view "${target_version}" --repo riscv/riscv-unified-db &>/dev/null; then
    release_exists=yes
  fi

  # Handle based on force flag and release existence
  if [ "${force}" != "yes" ] && [ "${release_exists}" = "yes" ]; then
    echo "==> GitHub Release ${target_version} already exists. Nothing to do."
    echo "    Use -f flag to force rebuild."
    return 0
  fi

  if [ "${force}" = "yes" ] && [ "${release_exists}" = "yes" ]; then
    echo "==> Force rebuild enabled..."
    # Only delete the release if we're building both architectures (not native_only)
    # For native_only builds, we'll use --clobber to replace individual assets
    if [ "${native_only}" != "yes" ]; then
      echo "==> Deleting existing GitHub Release ${target_version}..."
      gh release delete "${target_version}" --repo riscv/riscv-unified-db --yes
    else
      echo "==> Will replace existing assets with --clobber"
    fi
  fi

  echo "==> Building Z3 ${target_version}..."

  local orig_dir="${PWD}"
  local work_dir
  work_dir=$(mktemp -d --tmpdir="$PWD" build-z3.XXXXXX)

  local z3_version
  if [ "${target_version}" != "${current_version}" ]; then
    # New upstream version: build from source
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

      # Read the version produced by the build
      z3_version=$(cat "${work_dir}/z3-${native_arch}/VERSION")
      echo "==> Built Z3 version: ${z3_version}"

      # Rename the .so file to the asset name expected by extconf.rb / setup_z3
      cp "${work_dir}/z3-${native_arch}/lib/libz3.so" "${work_dir}/libz3-${native_arch}.so"
    else
      # Build for both architectures
      echo "==> Building Z3 for x64..."
      "${UDB_ROOT}"/tools/scripts/build_z3_with_docker.sh "${work_dir}/z3-x64" Release x64 || exit 1

      echo "==> Building Z3 for arm64..."
      "${UDB_ROOT}"/tools/scripts/build_z3_with_docker.sh "${work_dir}/z3-arm64" Release arm64 || exit 1

      # Read the version produced by the build
      z3_version=$(cat "${work_dir}/z3-x64/VERSION")
      echo "==> Built Z3 version: ${z3_version}"

      # Rename the .so files to the asset names expected by extconf.rb / setup_z3
      cp "${work_dir}/z3-x64/lib/libz3.so"   "${work_dir}/libz3-x64.so"
      cp "${work_dir}/z3-arm64/lib/libz3.so" "${work_dir}/libz3-arm64.so"
    fi
  else
    # Version unchanged: use the already-installed libraries from the XDG cache
    z3_version="${current_version}"
    local xdg_cache="${XDG_CACHE_HOME:-${HOME}/.cache}"

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
      local cache_native="${xdg_cache}/udb/z3/${current_version}/${native_arch}/libz3.so"
      if [ ! -f "${cache_native}" ]; then
        echo "ERROR: Cached Z3 library not found. Run 'bin/setup' first to download it." >&2
        echo "  Expected: ${cache_native}" >&2
        exit 1
      fi
      cp "${cache_native}" "${work_dir}/libz3-${native_arch}.so"
      echo "==> Using cached Z3 library for ${z3_version} (${native_arch})"
    else
      local cache_x64="${xdg_cache}/udb/z3/${current_version}/x64/libz3.so"
      local cache_arm64="${xdg_cache}/udb/z3/${current_version}/arm64/libz3.so"
      if [ ! -f "${cache_x64}" ] || [ ! -f "${cache_arm64}" ]; then
        echo "ERROR: Cached Z3 libraries not found. Run 'bin/setup' first to download them." >&2
        echo "  Expected: ${cache_x64}" >&2
        echo "  Expected: ${cache_arm64}" >&2
        exit 1
      fi
      cp "${cache_x64}"   "${work_dir}/libz3-x64.so"
      cp "${cache_arm64}" "${work_dir}/libz3-arm64.so"
      echo "==> Using cached Z3 libraries for ${z3_version}"
    fi
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

  if [ "${target_version}" != "${current_version}" ]; then
    # Update z3_version.rb so the gem knows which release to download
    # z3_version_rb already declared above
    echo -n "${z3_version}" > "${UDB_ROOT}/tools/ruby-gems/udb/lib/udb/Z3_VERSION"
    echo "==> Updated ${z3_version_rb}"
  fi

  cd "${orig_dir}" || exit 1
  rm -rf "${work_dir}"

  echo ""
  if [ "${target_version}" != "${current_version}" ]; then
    echo "Done. Next steps:"
    echo "  1. git add tools/ruby-gems/udb/lib/udb/z3_version.rb"
    echo "  2. git commit -m 'chore: update Z3 to ${z3_version}'"
    echo "  3. Open a PR"
  else
    echo "Done. GitHub Release ${z3_version} created on riscv/riscv-unified-db."
  fi
}
