# External Integrations

**Analysis Date:** 2026-07-30

## APIs & External Services

**GitHub Platform:**
- GitHub repository API - Release publication, release-asset download, pull-request creation/comments, tag checks, and repository queries are performed from `tools/scripts/publish_schemas.py`, `tools/scripts/download_schema_releases.py`, `bin/.chore/update.sh`, `.github/workflows/gem_bump.yml`, and `.github/workflows/autofix-comment.yml`.
  - SDK/Client: GitHub CLI 2.96.0 from `.mise.toml`; `actions/github-script` is used by `.github/workflows/dco_check.yml`.
  - Auth: `GH_TOKEN`, `GITHUB_TOKEN`, or the workflow-provided `github.token`, wired in `.github/workflows/*.yml`.
- GitHub Actions - CI, generated-artifact builds, dependency releases, gem publication, autofix, DCO checks, and Pages deployment are defined in `.github/workflows/`; the main generated pipeline is `.github/workflows/regress.yml`.
  - SDK/Client: Pinned GitHub Actions plus the repository composite action `.github/actions/mise-setup/action.yml`.
  - Auth: Job-scoped GitHub permissions and `secrets.GITHUB_TOKEN` / `github.token` in `.github/workflows/*.yml`.
- Git submodules - RISC-V opcodes, documentation assets, ISA manual sources, LLVM, RISC-V tests, and RBI definitions are fetched from upstream GitHub repositories listed in `.gitmodules`.
  - SDK/Client: Git CLI invoked by `bin/setup`, `backends/cpp_hart_gen/tasks.rake`, and `.github/workflows/regress.yml`.
  - Auth: Public clone by default; private/fork credentials are supplied by the caller's Git configuration, not repository code.

**Artifact Distribution:**
- GitHub Releases - Versioned JSON schemas and prebuilt Z3, Espresso, Eqntott, and Must binaries are published and consumed as release assets by `tools/scripts/publish_schemas.py`, `tools/scripts/download_schema_releases.py`, `tools/ruby-gems/udb/ext/udb_download/extconf.rb`, and `tools/ruby-gems/udb/lib/udb/dep_paths.rb`.
  - SDK/Client: GitHub CLI for publication; Ruby `Net::HTTP` for public binary downloads.
  - Auth: `GH_TOKEN`, `GITHUB_TOKEN`, and the custom workflow secret `TOKEN` in `.github/workflows/schema-release.yml` and `.github/workflows/release_udb_deps.yml`; public install-time downloads require no token.
- GitHub Container Registry (GHCR) - The multi-architecture RISC-V C++ toolchain image `ghcr.io/riscv/udb-toolchain` is built and published by `.github/workflows/toolchain-container.yml` and pulled or locally built by `bin/.toolchain.sh`.
  - SDK/Client: Docker/Podman locally; Docker Buildx, login, and build-push actions in `.github/workflows/toolchain-container.yml` and `.github/actions/mise-setup/action.yml`.
  - Auth: Workflow `github.token` / `secrets.GITHUB_TOKEN`; public pulls in `bin/.toolchain.sh` do not configure repository-held credentials.
- RubyGems.org - The `idlc`, `udb`, `udb-gen`, and `udb_helpers` gems are built and pushed by `.github/workflows/release_gems.yml`; package metadata and dependencies live in `tools/ruby-gems/*/*.gemspec`.
  - SDK/Client: RubyGems `gem build` / `gem push`, with Bundler using the registry declared in `Gemfile`.
  - Auth: `GEM_HOST_API_KEY` populated from `secrets.RUBYGEM_API_KEY` in `.github/workflows/release_gems.yml`.

**Published Documentation and Schemas:**
- GitHub Pages - Generated manuals, ISA Explorer artifacts, API docs, Docusaurus docs, schema downloads, and PDFs are assembled and deployed by `.github/workflows/pages.yml`; the site root is `https://riscv.github.io/riscv-unified-db`.
  - SDK/Client: `actions/configure-pages`, `actions/upload-pages-artifact`, and `actions/deploy-pages` in `.github/workflows/pages.yml`.
  - Auth: GitHub Actions `pages: write` plus OIDC `id-token: write` permissions in `.github/workflows/pages.yml`.
- Docusaurus preview Pages - The `doc_next` branch is configured for a fork preview by `.github/workflows/docs-preview.yml`, with URL/base-path overrides consumed by `doc/docusaurus.config.ts`.
  - SDK/Client: Docusaurus 3.10.2 and GitHub Pages actions.
  - Auth: GitHub Actions Pages/OIDC permissions in `.github/workflows/docs-preview.yml`.
- Published schema URLs - `tools/ruby-gems/udb/lib/udb/resolver.rb` rewrites resolved schema `$id` values to `https://riscv.github.io/riscv-unified-db/schemas/...`; `tools/scripts/check_schema_versions.py` reads those URLs to enforce immutable published versions.
  - SDK/Client: Python `urllib.request` in `tools/scripts/check_schema_versions.py`.
  - Auth: None; schemas are public.

**Coverage and Dependency Automation:**
- Codecov - Ruby Cobertura coverage for `udb` and `idlc` is uploaded from `.github/workflows/regress.yml`, with policy configured in `codecov.yml`.
  - SDK/Client: `codecov/codecov-action` v7 pinned in `.github/workflows/regress.yml`.
  - Auth: `secrets.CODECOV_TOKEN`.
- Renovate - Automated registry, GitHub release, submodule, action, pre-commit, Maven, RubyGems, npm, PyPI, Docker, and custom CMake dependency updates are configured in `renovate.json`.
  - SDK/Client: Renovate GitHub integration; local configuration validation is registered in `.pre-commit-config.yaml`.
  - Auth: Managed outside the repository by the installed Renovate integration; no Renovate credential file is present.
- autofix.ci - Generated files and formatter changes are handed to `autofix-ci/action` in `.github/workflows/autofix.yaml`; failures that involve workflow generation are reported through `.github/workflows/autofix-comment.yml`.
  - SDK/Client: `autofix-ci/action` plus GitHub CLI.
  - Auth: GitHub workflow token in `.github/workflows/autofix-comment.yml`.

**Build-Time Content and Dependency Sources:**
- RubyGems, npm Registry, and PyPI - Dependency sources are declared by `Gemfile`, `package-lock.json`, and `uv.lock`; installs are coordinated by `bin/setup`.
  - SDK/Client: Bundler, npm, and uv wrappers under `bin/`.
  - Auth: None for public packages; no checked-in package-manager credential files are used.
- Maven Central and Gradle Plugin Portal - Xtext and language-server dependencies are resolved by `tools/eclipse/dev/org.xtext.udb.parent/pom.xml` and `tools/eclipse/udb-ls/build.gradle`; Gradle itself is downloaded from the URL in `tools/eclipse/udb-ls/gradle/wrapper/gradle-wrapper.properties`.
  - SDK/Client: Maven/Tycho and Gradle Wrapper.
  - Auth: None for public artifacts.
- CMake source dependencies - fmt, yaml-cpp, CLI11, Catch2, nlohmann/json, JSON Schema Validator, CTRE, Berkeley SoftFloat, and elfutils are fetched from GitHub or Sourceware by `backends/cpp_hart_gen/CMakeLists.txt`.
  - SDK/Client: CMake `FetchContent` and `ExternalProject`.
  - Auth: None for public source repositories/archives.
- RISC-V GNU Toolchain sources - `.toolchain/Dockerfile` clones the pinned riscv-collab toolchain release and its submodules when the GHCR image is built.
  - SDK/Client: Git inside the container build.
  - Auth: None for public source.
- Antora UI bundle - Config-specific HTML documentation downloads the default Antora UI artifact from GitLab through the playbook generated by `backends/cfg_html_doc/html_gen.rake`.
  - SDK/Client: Antora 3.1.15.
  - Auth: None.
- Kroki diagrams - The Antora/Asciidoctor pipeline loads `asciidoctor-kroki` in `backends/cfg_html_doc/html_gen.rake`; no server override or credential is configured in the repository, so the extension's configured/default endpoint governs diagram requests.
  - SDK/Client: `asciidoctor-kroki` 0.18.1 from `package.json`.
  - Auth: Not configured.
- Creative Commons license text - Profile-family license bodies are fetched from `creativecommons.org` when `Udb::License#text` resolves `text_url`, implemented by `tools/ruby-gems/udb/lib/udb/obj/database_obj.rb` and referenced by `spec/std/isa/profile_family/RVI.yaml`, `spec/std/isa/profile_family/RVA.yaml`, and `spec/std/isa/profile_family/RVB.yaml`.
  - SDK/Client: Ruby `Net::HTTP`.
  - Auth: None.
- Remote JSON Schema references - `TopLevelDatabaseObject.create_json_schemer_resolver` can retrieve an HTTP(S) `$ref` using Ruby `Net::HTTP` in `tools/ruby-gems/udb/lib/udb/obj/database_obj.rb`; ordinary repository schema references resolve locally from `spec/schemas/`.
  - SDK/Client: Ruby `Net::HTTP` and `json_schemer`.
  - Auth: None.

**Developer Protocols:**
- Model Context Protocol (MCP) - `tools/mcp_gen_server/server.py` exposes generated instruction, CSR, extension, and IDL queries over stdio using the Python MCP SDK; setup is documented in `tools/mcp_gen_server/README.md`.
  - SDK/Client: Python `mcp[cli]` plus `ruamel.yaml`.
  - Auth: None; transport is local stdio, not an HTTP listener.
- Language Server Protocol (LSP) - The VS Code extension `tools/eclipse/udb-vscode/src/extension.ts` spawns the shaded Java server from `tools/eclipse/udb-vscode/server/udb-ls-all.jar` and communicates over stdin/stdout.
  - SDK/Client: `vscode-languageclient` 10.1.0, configured in `tools/eclipse/udb-vscode/package.json`.
  - Auth: None; local process transport.
- GDB and Renode integration - The generated ISS contains a GDB remote server in `backends/cpp_hart_gen/cpp/src/GDBServer.cpp`, and the Renode bridge loads the generated hart shared library through `backends/cpp_hart_gen/renode/UdbCpu.cs`.
  - SDK/Client: GDB remote protocol and Renode's C# peripheral API.
  - Auth: No authentication layer is defined in `backends/cpp_hart_gen/cpp/src/GDBServer.cpp` or `backends/cpp_hart_gen/renode/UdbCpu.cs`.

## Data Storage

**Databases:**
- No database server, ORM, or SQL schema is detected in `Gemfile`, `pyproject.toml`, `package.json`, or `tools/eclipse/udb-ls/build.gradle`.
  - Connection: Not applicable.
  - Client: Repository YAML/JSON loaders in `tools/ruby-gems/udb/lib/udb/` and `tools/ruby-gems/udb/python/yaml_resolver.py`.
- The source of truth is the Git working tree: standard/custom architecture data is under `spec/`, configurations are under `cfgs/`, and schemas are under `spec/schemas/`.
  - Connection: Filesystem paths resolved by `tools/ruby-gems/udb/lib/udb/resolver.rb`.
  - Client: Ruby UDB APIs and Python YAML/JSON tooling in `tools/ruby-gems/udb/`.

**File Storage:**
- Local generated output is written under the gitignored `gen/` directory by `Rakefile`, `backends/*/tasks.rake`, and `tools/ruby-gems/udb/lib/udb/resolver.rb`.
- CI build outputs use GitHub Actions artifacts in `.github/workflows/regress.yml`, then `.github/workflows/pages.yml` assembles selected artifacts into `_site/`.
- Immutable schemas and native binary bundles use GitHub Release assets via `tools/scripts/publish_schemas.py` and `bin/.chore/update.sh`.
- Published static content uses GitHub Pages through `.github/workflows/pages.yml`; published gems use RubyGems through `.github/workflows/release_gems.yml`.

**Caching:**
- Native UDB dependencies are cached under `${XDG_CACHE_HOME:-~/.cache}/udb` by `tools/ruby-gems/udb/ext/udb_download/extconf.rb`, `tools/ruby-gems/udb/lib/udb/dep_paths.rb`, and `tools/ruby-gems/udb/lib/udb/z3_loader.rb`.
- Developer package caches use uv and npm default caches, with CI cache keys defined in `.github/actions/mise-setup/action.yml`.
- GitHub Actions caches the LLVM-derived RISC-V JSON and package/native downloads in `.github/workflows/regress.yml` and `.github/actions/mise-setup/action.yml`.
- No network cache service such as Redis or Memcached is configured in `Gemfile`, `pyproject.toml`, or `package.json`.

## Authentication & Identity

**Auth Provider:**
- No end-user authentication or identity provider exists because the repository delivers local CLIs/libraries and static artifacts; entry points `do`, `bin/generate`, `bin/regress`, and `tools/mcp_gen_server/server.py` do not implement user sessions.
  - Implementation: Not applicable for local tools and public static output.
- CI service authentication uses GitHub Actions tokens and scoped job permissions in `.github/workflows/*.yml`.
  - Implementation: `GITHUB_TOKEN` / `GH_TOKEN` for GitHub API and releases, OIDC `id-token: write` for Pages, `CODECOV_TOKEN` for Codecov, `RUBYGEM_API_KEY` for RubyGems, and `TOKEN` for the native dependency release workflow.

## Monitoring & Observability

**Error Tracking:**
- No hosted error-tracking or application-performance-monitoring SDK is declared in `Gemfile`, `pyproject.toml`, `package.json`, or `doc/package.json`.
- Code coverage is tracked by Codecov using `.github/workflows/regress.yml` and `codecov.yml`; this is quality reporting rather than runtime error monitoring.

**Logs:**
- Ruby tooling logs to stdout/stderr through `Logger` in `Rakefile` and `TTY::Logger` dependencies declared in `tools/ruby-gems/udb/udb.gemspec`.
- CI logs and annotations are retained by GitHub Actions workflows under `.github/workflows/`; artifacts and coverage reports are uploaded explicitly by `.github/workflows/regress.yml`.
- The VS Code language client sends Java server stderr and process lifecycle messages to an output channel in `tools/eclipse/udb-vscode/src/extension.ts`.

## CI/CD & Deployment

**Hosting:**
- GitHub Pages hosts generated project artifacts and the Docusaurus site through `.github/workflows/pages.yml`; `doc/docusaurus.config.ts` defines the canonical project URL and base path.
- GitHub Pages also hosts the temporary `doc_next` preview configured by `.github/workflows/docs-preview.yml`.
- GHCR hosts the RISC-V toolchain container configured by `.github/workflows/toolchain-container.yml`.
- RubyGems.org hosts the published gems configured by `.github/workflows/release_gems.yml`.
- GitHub Releases host versioned schemas and native dependency binaries configured by `.github/workflows/schema-release.yml` and `.github/workflows/release_udb_deps.yml`.

**CI Pipeline:**
- GitHub Actions is the sole CI/CD platform detected; the main PR/main pipeline is generated at `.github/workflows/regress.yml` from `tools/test/regress-tests.yaml` and `tools/test/regress-gh-template.yaml`.
- Pull requests run regression, schema, type, generator, language-server, and C++ checks in `.github/workflows/regress.yml`, DCO enforcement in `.github/workflows/dco_check.yml`, and formatting regeneration through `.github/workflows/autofix.yaml`.
- Successful main-branch CI feeds Pages deployment in `.github/workflows/pages.yml` and schema publication in `.github/workflows/schema-release.yml`.
- Separate workflows publish gems and the toolchain image from `.github/workflows/release_gems.yml` and `.github/workflows/toolchain-container.yml`; `.github/workflows/gem_bump.yml` creates scheduled version-bump PRs.

## Environment Configuration

**Required env vars:**
- Core local workflows have defaults and require no secret environment variables; path/cache overrides `UDB_ROOT`, `XDG_DATA_HOME`, and `XDG_CACHE_HOME` are read by `tools/ruby-gems/udb/lib/udb/paths.rb`, `tools/ruby-gems/udb/lib/udb/dep_paths.rb`, and `tools/ruby-gems/udb/lib/udb/z3_loader.rb`.
- C++ toolchain selection uses `UDB_TOOLCHAIN_CONTAINER`, `UDB_TOOLCHAIN_NONE`, `DOCKER`, and `PODMAN` in `bin/setup` and `bin/.toolchain.sh`.
- Documentation deployment can set `DOCUSAURUS_URL` and `DOCUSAURUS_BASE_URL` as defined by `doc/docusaurus.config.ts`.
- CI publication uses `GITHUB_TOKEN`/`GH_TOKEN`, `CODECOV_TOKEN`, `RUBYGEM_API_KEY`, and `TOKEN` as referenced by `.github/workflows/*.yml`.
- Build/task parameters such as `CFG`, `CONFIG`, `JOBS`, `BUILD_TYPE`, and `IGNOREUNDEFINED` are consumed by `Rakefile` and `backends/cpp_hart_gen/tasks.rake`; they are command inputs, not credentials.

**Secrets location:**
- CI secrets are expected in GitHub Actions repository/environment secrets and are referenced symbolically from `.github/workflows/regress.yml`, `.github/workflows/release_gems.yml`, `.github/workflows/release_udb_deps.yml`, and `.github/workflows/toolchain-container.yml`.
- No checked-in `.env` or `.env.*` file is present; local `.toolchain-local` is gitignored by `.gitignore` and stores only toolchain selection written by `bin/setup`.
- Package-manager authentication files are not part of the repository; public registries are configured by `Gemfile`, `package-lock.json`, `uv.lock`, and `tools/eclipse/udb-ls/build.gradle`.

## Webhooks & Callbacks

**Incoming:**
- No application webhook endpoint or HTTP server route is defined in the Ruby/Python entry points under `tools/ruby-gems/`, `tools/python/`, or `tools/mcp_gen_server/server.py`.
- GitHub repository events trigger automation directly: pull requests, pushes, merge groups, schedules, manual dispatches, and completed workflow runs are declared in `.github/workflows/*.yml`.
- MCP and the Java language server accept local stdio protocol requests in `tools/mcp_gen_server/server.py` and `tools/eclipse/udb-vscode/src/extension.ts`; these are not webhooks.
- The optional ISS GDB server accepts debugger protocol connections in `backends/cpp_hart_gen/cpp/src/GDBServer.cpp`; it is not an HTTP callback endpoint.

**Outgoing:**
- GitHub API/release calls originate from `tools/scripts/publish_schemas.py`, `tools/scripts/download_schema_releases.py`, `bin/.chore/update.sh`, and `.github/workflows/autofix-comment.yml`.
- Public HTTP fetches originate from `tools/ruby-gems/udb/ext/udb_download/extconf.rb` for native binaries, `tools/scripts/check_schema_versions.py` for published schemas, and `tools/ruby-gems/udb/lib/udb/obj/database_obj.rb` for remote schema/license content.
- Build and publication traffic targets RubyGems, npm, PyPI, Maven Central/Gradle services, GitHub source repositories/releases, Sourceware, GitLab Antora UI artifacts, Kroki, Codecov, GHCR, and GitHub Pages, as configured by `Gemfile`, `package-lock.json`, `uv.lock`, `tools/eclipse/udb-ls/build.gradle`, `backends/cpp_hart_gen/CMakeLists.txt`, `backends/cfg_html_doc/html_gen.rake`, and `.github/workflows/`.

---

*Integration audit: 2026-07-30*
