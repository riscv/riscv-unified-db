<!-- Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries. -->
<!-- SPDX-License-Identifier: BSD-3-Clause-Clear -->

# Building Z3 from Source with Docker

This directory contains a script to build Z3 from source using Docker and AlmaLinux 8.

## Script: `build_z3_with_docker.sh`

### Overview

The `build_z3_with_docker.sh` script automates the process of:
1. Downloading the latest Z3 release from GitHub
2. Compiling it inside a Docker container using AlmaLinux 8
3. Extracting the compiled binaries and libraries to your host system

### Prerequisites

- Docker installed and running
- Either `curl` or `wget` installed
- Internet connection to download Z3 source and Docker images
- **Optional**: `GITHUB_TOKEN` environment variable for authenticated GitHub API requests (helps avoid rate limits)
- **For cross-architecture builds** (e.g., building ARM64 on x64):
  - **Docker Desktop**: Multi-platform support with QEMU is enabled by default - no additional setup required
  - **Docker on Linux**: QEMU support is usually available automatically. If cross-architecture builds fail with platform errors, install `qemu-user-static`:
    ```bash
    # On Debian/Ubuntu
    sudo apt-get install qemu-user-static binfmt-support
    ```
  - **Note**: Most modern Docker installations already have QEMU support. Try running the build first before installing additional packages.

### Usage

```bash
./build_z3_with_docker.sh [output_dir] [build_type] [architecture]
```

#### Arguments

- **output_dir** (optional): Directory where Z3 will be installed
  - Default: `./z3-build` in the current directory

- **build_type** (optional): CMake build configuration
  - Options: `Release`, `Debug`, `RelWithDebInfo`, `MinSizeRel`
  - Default: `Release`

- **architecture** (optional): Target architecture for the build
  - Options: `x64`, `amd64`, `x86_64`, `arm64`, `aarch64`
  - Default: `x64`

### Environment Variables

- **GITHUB_TOKEN** (optional): GitHub personal access token for authenticated API requests
  - Helps avoid GitHub API rate limits (60 requests/hour unauthenticated vs 5000/hour authenticated)
  - The script will automatically use this token if set
  - Example: `export GITHUB_TOKEN=ghp_your_token_here`

### Examples

#### Basic usage (default settings)
```bash
./build_z3_with_docker.sh
```
This builds Z3 in Release mode and installs to `./z3-build`

#### Specify output directory
```bash
./build_z3_with_docker.sh /opt/z3
```
This builds Z3 in Release mode and installs to `/opt/z3`

#### Debug build
```bash
./build_z3_with_docker.sh ./z3-debug Debug
```
This builds Z3 in Debug mode and installs to `./z3-debug`

#### ARM64 build
```bash
./build_z3_with_docker.sh ./z3-arm64 Release arm64
```
This builds Z3 for ARM64 architecture in Release mode and installs to `./z3-arm64`

#### Explicit x64 build
```bash
./build_z3_with_docker.sh ./z3-x64 Release x64
```
This builds Z3 for x64 architecture in Release mode and installs to `./z3-x64`

#### Using GitHub authentication to avoid rate limits
```bash
export GITHUB_TOKEN=ghp_your_token_here
./build_z3_with_docker.sh
```
This uses your GitHub token for authenticated API requests

### Output Structure

After successful build, the output directory will contain:

```
output_dir/
├── bin/           # Z3 executable and tools
├── lib/           # Shared and static libraries
├── include/       # Header files
└── VERSION        # File containing the Z3 version
```

### Using as a Bash Function

You can also source the script to use the `build_z3_with_docker` function directly:

```bash
source ./build_z3_with_docker.sh
build_z3_with_docker /custom/path Release x64
```

### Build Process Details

The script performs the following steps:

1. **Fetch Latest Release**: Queries GitHub API for the latest Z3 release
2. **Download Source**: Downloads the source tarball
3. **Create Dockerfile**: Generates a Dockerfile with AlmaLinux 8 base image
4. **Install Dependencies**: Installs gcc, g++, cmake, make, python3, and git
5. **Build Z3**: Uses Z3's `mk_make.py` script to configure and build
6. **Extract Files**: Copies the installation from the container to the host
7. **Cleanup**: Removes temporary Docker images and containers

### Build Configuration

The script builds Z3 with the following options:
- Static library support (`--staticlib`)
- Installation prefix: `/opt/z3` (inside container)
- Parallel compilation using all available CPU cores

### Troubleshooting

#### Docker not found
```
ERROR: Docker is not installed or not in PATH
```
Install Docker and ensure it's in your PATH.

#### Download fails
```
ERROR: Failed to download Z3 source
```
Check your internet connection and GitHub availability.

#### Build fails
```
ERROR: Z3 build failed - BUILD_SUCCESS marker not found
```
The compilation failed inside the container. Check Docker logs for details.

### Integration with UDB

This script can be used to build Z3 for use with the UDB project. The compiled libraries are compatible with the `z3_loader.rb` module in `tools/ruby-gems/udb/lib/udb/z3_loader.rb`.

To use the built Z3 with UDB:

1. Build Z3 to a specific location:
   ```bash
   ./build_z3_with_docker.sh ~/.local/share/udb/z3/4.16.0
   ```

2. The z3_loader.rb will automatically detect and use the libraries from this location.

### Notes

- The script uses AlmaLinux 8, which provides glibc 2.28 compatibility
- Build artifacts are extracted from the container, so no persistent containers remain
- Temporary files are automatically cleaned up on exit
- The script is safe to run multiple times; each run uses unique container names
- **Cross-architecture builds**: When building for a different architecture than your host (e.g., ARM64 on x64), Docker uses QEMU emulation which will be significantly slower than native builds. Expect build times of 30+ minutes for cross-architecture builds.

### License

Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
SPDX-License-Identifier: BSD-3-Clause-Clear
