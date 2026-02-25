<!-- Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries. -->
<!-- SPDX-License-Identifier: BSD-3-Clause-Clear -->

# Building espresso from Source with Docker

This script builds the `espresso` logic minimizer from source using Docker and
AlmaLinux 8, producing a statically-linked binary for maximum portability
(glibc 2.28+, same baseline as the Z3 builds).

## Script: `build_espresso_with_docker.sh`

### Prerequisites

- Docker installed and running
- For cross-architecture builds (e.g. ARM64 on x64), QEMU support in Docker
  (usually available by default on Docker Desktop and modern Docker on Linux)

### Usage

```bash
./build_espresso_with_docker.sh [output_dir] [architecture]
```

#### Arguments

- **output_dir** (optional): Directory where the binary will be placed
  - Default: `./espresso-build`
- **architecture** (optional): Target architecture
  - Options: `x64`, `amd64`, `x86_64`, `arm64`, `aarch64`
  - Default: `x64`

### Examples

```bash
# Build x64 binary to ./espresso-build
./build_espresso_with_docker.sh

# Build arm64 binary to ./espresso-arm64
./build_espresso_with_docker.sh ./espresso-arm64 arm64
```

### Output

A single statically-linked executable named `espresso` in the output directory.

### Integration with the udb gem

The `udb` gem downloads prebuilt `espresso` binaries from GitHub releases at
`gem install` time. Use this script to build new binaries when the upstream
source changes:

1. Build for both architectures:
   ```bash
   ./build_espresso_with_docker.sh ./out x64
   ./build_espresso_with_docker.sh ./out arm64
   ```
2. Create a new GitHub release tag matching `lib/udb/ESPRESSO_VERSION`
   (e.g. `espresso-1.0`).
3. Run the `release_tools` GitHub Actions workflow with `tool=espresso` and
   the matching tag, or upload the binaries manually as release assets named
   `espresso-x64` and `espresso-arm64`.
4. Update `lib/udb/ESPRESSO_VERSION` if the version changed.
