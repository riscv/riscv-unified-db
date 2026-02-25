<!-- Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries. -->
<!-- SPDX-License-Identifier: BSD-3-Clause-Clear -->

# Building must (mustool) from Source with Docker

This script builds the `must` MUS enumerator from source using Docker and
AlmaLinux 8, producing a statically-linked binary for maximum portability
(glibc 2.28+, same baseline as the Z3 builds).

The build is pinned to a specific commit of
[jar-ben/mustool](https://github.com/jar-ben/mustool) that matches
`lib/udb/MUST_VERSION` in the udb gem.

## Script: `build_must_with_docker.sh`

### Prerequisites

- Docker installed and running
- For cross-architecture builds (e.g. ARM64 on x64), QEMU support in Docker
  (usually available by default on Docker Desktop and modern Docker on Linux)

### Usage

```bash
./build_must_with_docker.sh [output_dir] [architecture]
```

#### Arguments

- **output_dir** (optional): Directory where the binary will be placed
  - Default: `./must-build`
- **architecture** (optional): Target architecture
  - Options: `x64`, `amd64`, `x86_64`, `arm64`, `aarch64`
  - Default: `x64`

### Examples

```bash
# Build x64 binary to ./must-build
./build_must_with_docker.sh

# Build arm64 binary to ./must-arm64
./build_must_with_docker.sh ./must-arm64 arm64
```

### Output

A single statically-linked executable named `must` in the output directory.

### Integration with the udb gem

The `udb` gem downloads prebuilt `must` binaries from GitHub releases at
`gem install` time. Use this script to build new binaries when the pinned
commit needs to change:

1. Update `MUST_COMMIT` in `build_must_with_docker.sh` to the new commit hash.
2. Build for both architectures:
   ```bash
   ./build_must_with_docker.sh ./out x64
   ./build_must_with_docker.sh ./out arm64
   ```
3. Create a new GitHub release tag matching the new `lib/udb/MUST_VERSION`
   (e.g. `must-<short-sha>`).
4. Run the `release_tools` GitHub Actions workflow with `tool=must` and the
   matching tag, or upload the binaries manually as release assets named
   `must-x64` and `must-arm64`.
5. Update `lib/udb/MUST_VERSION` to the new tag.
