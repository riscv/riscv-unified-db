<!-- Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries. -->
<!-- SPDX-License-Identifier: BSD-3-Clause-Clear -->

# Building UDB Gem Dependencies from Source with Docker

*NOTE* The scripts described here are not intended to be run by many/any developers.
The primary way to update dependencies is to use the "Build and release UDB gem dependencies to
GitHub" action on GitHub.

This directory contains scripts to build the prebuilt binaries and libraries
used by the `udb` gem from source using Docker and AlmaLinux 8. All builds
produce artifacts with glibc 2.28+ compatibility.

| Tool | Script | Output |
|------|--------|--------|
| eqntott | `build_eqntott_with_docker.sh` | `eqntott` (static executable) |
| espresso | `build_espresso_with_docker.sh` | `espresso` (static executable) |
| must (mustool) | `build_must_with_docker.sh` | `must` (static executable) |
| Z3 | `build_z3_with_docker.sh` | `libz3.so` + headers + binaries |

## Prerequisites

- Docker installed and running
- Either `curl` or `wget` installed (Z3 only)
- **For cross-architecture builds** (e.g., ARM64 on x64):
  - **Docker Desktop**: Multi-platform support with QEMU is enabled by default
  - **Docker on Linux**: QEMU support is usually available automatically. If
    cross-architecture builds fail, install `qemu-user-static`:
    ```bash
    # On Debian/Ubuntu
    sudo apt-get install qemu-user-static binfmt-support
    ```

## Updating a Tool (Recommended)

The easiest way to build and release a new version is via `bin/chore`:

```bash
# Build and release for the native platform only (used in CI matrix)
./bin/chore update eqntott -n
./bin/chore update espresso -n
./bin/chore update must -n
./bin/chore update z3 -n

# Build and release for both x64 and arm64 at once
./bin/chore update eqntott
./bin/chore update espresso
./bin/chore update must
./bin/chore update z3

# Force rebuild even if the release already exists
./bin/chore update z3 -f
```

The `chore update` commands handle building, checksum generation, GitHub
release creation, and (for Z3) version file updates automatically.

---

## eqntott

The build is pinned to a specific commit of
[TheProjecter/eqntott](https://github.com/TheProjecter/eqntott) that matches
`lib/udb/EQNTOTT_VERSION` in the udb gem.

### Usage

```bash
./build_eqntott_with_docker.sh [output_dir] [architecture]
```

#### Arguments

- **output_dir** (optional): Directory where the binary will be placed
  - Default: `./eqntott-build`
- **architecture** (optional): Target architecture
  - Options: `x64`, `amd64`, `x86_64`, `arm64`, `aarch64`
  - Default: `x64`

### Examples

```bash
# Build x64 binary to ./eqntott-build
./build_eqntott_with_docker.sh

# Build arm64 binary to ./eqntott-arm64
./build_eqntott_with_docker.sh ./eqntott-arm64 arm64
```

### Output

A single statically-linked executable named `eqntott` in the output directory.

### Releasing a New Version

1. Update `EQNTOTT_COMMIT` in `build_eqntott_with_docker.sh` to the new commit hash.
2. Build for both architectures:
   ```bash
   ./build_eqntott_with_docker.sh ./out x64
   ./build_eqntott_with_docker.sh ./out arm64
   ```
3. Update `lib/udb/EQNTOTT_VERSION` to the new tag (e.g. `eqntott-<short-sha>`).
4. Run `./bin/chore update eqntott` to create the GitHub release and upload the
   binaries and checksums.

---

## espresso

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

### Releasing a New Version

1. Build for both architectures:
   ```bash
   ./build_espresso_with_docker.sh ./out x64
   ./build_espresso_with_docker.sh ./out arm64
   ```
2. Update `lib/udb/ESPRESSO_VERSION` if the version changed.
3. Run `./bin/chore update espresso` to create the GitHub release and upload
   the binaries and checksums.

---

## must (mustool)

The build is pinned to a specific commit of
[jar-ben/mustool](https://github.com/jar-ben/mustool) that matches
`lib/udb/MUST_VERSION` in the udb gem.

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

### Releasing a New Version

1. Update `MUST_COMMIT` in `build_must_with_docker.sh` to the new commit hash.
2. Build for both architectures:
   ```bash
   ./build_must_with_docker.sh ./out x64
   ./build_must_with_docker.sh ./out arm64
   ```
3. Update `lib/udb/MUST_VERSION` to the new tag (e.g. `must-<short-sha>`).
4. Run `./bin/chore update must` to create the GitHub release and upload the
   binaries and checksums.

---

## Z3

### Usage

```bash
./build_z3_with_docker.sh [output_dir] [build_type] [architecture]
```

#### Arguments

- **output_dir** (optional): Directory where Z3 will be installed
  - Default: `./z3-build`
- **build_type** (optional): CMake build configuration
  - Options: `Release`, `Debug`, `RelWithDebInfo`, `MinSizeRel`
  - Default: `Release`
- **architecture** (optional): Target architecture
  - Options: `x64`, `amd64`, `x86_64`, `arm64`, `aarch64`
  - Default: `x64`

### Environment Variables

- **GITHUB_TOKEN** (optional): GitHub personal access token for authenticated
  API requests. Helps avoid rate limits (60 req/hr unauthenticated vs 5000/hr
  authenticated).

### Examples

```bash
# Build x64 Release to ./z3-build
./build_z3_with_docker.sh

# Build arm64 Release to ./z3-arm64
./build_z3_with_docker.sh ./z3-arm64 Release arm64

# Debug build
./build_z3_with_docker.sh ./z3-debug Debug

# With GitHub authentication
export GITHUB_TOKEN=ghp_your_token_here
./build_z3_with_docker.sh
```

### Output Structure

```
output_dir/
├── bin/       # Z3 executable and tools
├── lib/       # Shared and static libraries (includes libz3.so)
├── include/   # Header files
└── VERSION    # File containing the Z3 version string
```

### Releasing a New Version

Run `./bin/chore update z3` — it automatically detects the latest upstream Z3
release, builds it, generates checksums, creates the GitHub release, and
updates `lib/udb/Z3_VERSION`.

### Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `Docker is not installed or not in PATH` | Docker missing | Install Docker |
| `Failed to download Z3 source` | Network issue | Check internet / set `GITHUB_TOKEN` |
| `Z3 build failed - BUILD_SUCCESS marker not found` | Compile error | Check Docker logs |
| GitHub API rate limit exceeded | Too many unauthenticated requests | Set `GITHUB_TOKEN` |
