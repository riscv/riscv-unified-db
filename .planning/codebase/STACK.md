# Technology Stack

**Analysis Date:** 2026-07-30

## Languages

**Primary:**
- YAML (version not pinned) - Normative RISC-V data is stored as schema-tagged YAML under `spec/std/isa/`, custom data under `spec/custom/isa/`, and selectable architecture configurations under `cfgs/`.
- Ruby 3.4.10 for the repository toolchain, with published gems declaring Ruby `~> 3.2` - Core resolution, object models, the IDL compiler, generators, Rake tasks, and command-line tools live in `tools/ruby-gems/`, `backends/`, and `Rakefile`; the runtime pin is in `.mise.toml`.
- JSON / JSON Schema Draft 7 - Data contracts live in `spec/schemas/*.json`; for example, `spec/schemas/inst_schema.json` identifies Draft 7 and carries its own independent `$id` version.
- ISA Description Language (IDL), an in-repository DSL - Instruction behavior is embedded in fields such as `operation()` in `spec/std/isa/inst/I/add.yaml`, while shared IDL source lives in `spec/std/isa/isa/*.idl` and `spec/std/isa/isa/globals.isa`.

**Secondary:**
- Python 3.14.6 (project pin), compatible with Python `>=3.12` - Schema tooling, profile/report scripts, LLVM cross-validation, and the stdio MCP server live in `tools/scripts/*.py`, `tools/python/`, `tools/ruby-gems/udb/python/`, and `tools/mcp_gen_server/server.py`; pins are in `.python-version` and `pyproject.toml`.
- TypeScript 7.0.2 and JavaScript - The Docusaurus documentation site is in `doc/`, the VS Code client is in `tools/eclipse/udb-vscode/`, and TextMate grammar tooling/extensions are in `tools/node/` and `tools/vscode/`.
- React 19.2.8 / MDX - Interactive documentation pages and theme components are rooted at `doc/src/` and `doc/docs/`, with resolved versions in `package-lock.json`.
- C++23 and C - The generated instruction-set simulator, hart library, GDB server, and tests are under `backends/cpp_hart_gen/`; the required C++ feature level is enforced by `.toolchain/check_cxx.cmake`.
- Java 21, Java 17, Xtend, and Xtext - The Eclipse/Xtext workspace targets Java 21 in `tools/eclipse/dev/org.xtext.udb.parent/pom.xml`; the standalone Gradle language-server launcher uses a Java 17 toolchain in `tools/eclipse/udb-ls/build.gradle`.
- Bash / POSIX shell - Developer entry points and tool wrappers are in `bin/`, native dependency build scripts are in `tools/scripts/`, and the toolchain wrapper is `bin/.toolchain.sh`.
- ERB and AsciiDoc - Generator templates are spread across `backends/*/templates/` and `tools/ruby-gems/udb-gen/templates/`; source documentation lives in `doc/*.adoc` and generated/manual pipelines are registered in `backends/*/tasks.rake`.
- C# - The optional Renode integration is implemented in `backends/cpp_hart_gen/renode/UdbCpu.cs`.
- Go, C headers, and SystemVerilog are generated output targets, not primary implementation languages; their task definitions are in `backends/generators/tasks.rake`.

## Runtime

**Environment:**
- mise-managed native development environment - `.mise.toml` pins Ruby 3.4.10, Node.js 24.18.0, uv 0.11.31, CMake 4.4.0, GNU Make 4.4.1, ShellCheck 0.11.0, GitHub CLI 2.96.0, and prek 0.4.10.
- uv-managed Python 3.14.6 - `.python-version` selects the interpreter and `bin/setup` runs `bin/uv sync` to create the in-tree `.venv`.
- Node.js 24.18.0 - `.mise.toml` supplies Node for Antora, Docusaurus, Prettier, grammar generation, and VS Code tooling configured by `package.json`, `doc/package.json`, and `tools/eclipse/udb-vscode/package.json`.
- Java 21 (CI Xtext builds) and Java 17 (Gradle language-server toolchain) - `.github/workflows/regress.yml`, `tools/eclipse/dev/org.xtext.udb.parent/pom.xml`, and `tools/eclipse/udb-ls/build.gradle` define these separate requirements.
- C++23 host or container toolchain - `.toolchain/check_cxx.cmake` requires concepts and `constexpr from_chars`; `.toolchain/Dockerfile` supplies AlmaLinux 8, GCC Toolset 14, and RISC-V GNU Toolchain 2026.07.12.
- Local command wrappers are the supported invocation layer - `do`, `bin/regress`, `bin/generate`, and the generated wrappers in `bin/` execute tools through `bin/mise`.

**Package Manager:**
- Bundler 4.0.17 - Ruby dependencies are declared in `Gemfile` and the local gemspecs under `tools/ruby-gems/`; lockfile `Gemfile.lock` is present and `.default-gems` installs the matching Bundler release.
- uv 0.11.31 - Python dependencies are declared in `pyproject.toml`; lockfile `uv.lock` is present.
- npm with lockfile format 3 - JavaScript dependencies and the `doc` workspace are declared in `package.json` and `doc/package.json`; root lockfile `package-lock.json` is present. npm itself is supplied with Node and is not separately pinned.
- npm for the VS Code client - `tools/eclipse/udb-vscode/package.json` has its own `tools/eclipse/udb-vscode/package-lock.json`.
- Gradle Wrapper 9.6.1 - The standalone Xtext language server is built via `tools/eclipse/udb-ls/gradle/wrapper/gradle-wrapper.properties`; no dependency lockfile is detected in `tools/eclipse/udb-ls/`.
- Maven/Tycho - The Eclipse plug-in workspace is rooted at `tools/eclipse/dev/org.xtext.udb.parent/pom.xml`; Maven itself is not pinned by a checked-in wrapper.
- CMake FetchContent / ExternalProject - Native dependencies are pinned by tag, commit, or hash in `backends/cpp_hart_gen/CMakeLists.txt`; no CMake package lockfile is used.

## Frameworks

**Core:**
- UDB 0.1.14 - The main Ruby database API and resolver live in `tools/ruby-gems/udb/lib/udb/`, with the version defined in `tools/ruby-gems/udb/lib/udb/version.rb`.
- IDLC 0.1.5 - The Treetop-based IDL compiler, AST, type checker, and passes live in `tools/ruby-gems/idlc/lib/idlc/`, with its grammar in `tools/ruby-gems/idlc/lib/idlc/idl.treetop`.
- UDB Gen 0.1.13 - Generator CLI and backend implementations live in `tools/ruby-gems/udb-gen/lib/udb-gen/` and use templates in `tools/ruby-gems/udb-gen/templates/`.
- UDB Helpers 0.1.3 - Shared documentation and generator helpers live in `tools/ruby-gems/udb_helpers/lib/udb_helpers/`.
- Rake 13.4.2 - `Rakefile` discovers `backends/*/tasks.rake` and `tools/*/tasks.rake`; the exact version is locked in `Gemfile.lock`.
- Sorbet 0.6.13363 - Runtime and static typing are used throughout typed Ruby sources such as `Rakefile` and `tools/ruby-gems/udb/lib/udb/`; configuration and RBIs live in `sorbet/`.
- Docusaurus 3.10.2 with React 19.2.8 - The new static documentation site is configured by `doc/docusaurus.config.ts`, `doc/sidebars.ts`, and `doc/package.json`; resolved versions are in `package-lock.json`.
- Antora 3.1.15 with Lunr, Asciidoctor tabs, MathJax, and Kroki extensions - Configuration is generated by `backends/cfg_html_doc/html_gen.rake`, and packages are declared in `package.json`.
- Asciidoctor 2.0.26, Asciidoctor PDF 2.3.24, and Asciidoctor Diagram 3.2.1 - Ruby documentation generation dependencies are locked in `Gemfile.lock` and declared by `tools/ruby-gems/udb-gen/udb-gen.gemspec`.
- Eclipse Xtext 2.43.0 and Tycho 5.0.3 - Grammar and Eclipse language tooling live under `tools/eclipse/dev/org.xtext.udb.parent/`; versions are centralized in `tools/eclipse/dev/org.xtext.udb.parent/pom.xml`.
- Model Context Protocol Python SDK (`mcp[cli]`, version not pinned) - The low-level stdio server is `tools/mcp_gen_server/server.py`; installation is documented separately in `tools/mcp_gen_server/README.md` and is not part of `pyproject.toml` or `uv.lock`.

**Testing:**
- Minitest 6.0.6 and Mocha 3.1.0 - Ruby unit and integration tests live under `tools/ruby-gems/*/test/`; versions are locked in `Gemfile.lock`.
- SimpleCov 1.0.3 with simplecov-cobertura 4.0.0 - Ruby coverage is initialized by `tools/ruby-gems/udb/test/test_helper.rb` and uploaded by `.github/workflows/regress.yml`.
- pytest 9.1.1 - Python tests such as `tools/python/auto-inst/test_parsing.py` use the dev dependency pinned in `pyproject.toml` and `uv.lock`.
- Catch2 3.15.2 / CTest - C++ tests are declared in `backends/cpp_hart_gen/CMakeLists.txt` and implemented in `backends/cpp_hart_gen/cpp/test/`.
- Mocha 11.7.6 and `@vscode/test-electron` 3.1.0 - VS Code extension tests are configured in `tools/eclipse/udb-vscode/package.json` and locked in `tools/eclipse/udb-vscode/package-lock.json`.
- Xtext/Tycho test modules - Java tests are organized in `tools/eclipse/dev/org.xtext.udb.parent/org.xtext.udb.tests/` and `tools/eclipse/dev/org.xtext.udb.parent/org.xtext.udb.ui.tests/`, and run with Java 21 in `.github/workflows/regress.yml`.
- Repository regression harness - Test metadata and tags are authored in `tools/test/regress-tests.yaml`, rendered into `.github/workflows/regress.yml`, and executed locally by `bin/regress`.

**Build/Dev:**
- mise bootstrap 2026.7.5 locally and mise action 2026.7.11 in CI - `bin/mise` bootstraps the local binary, while `.github/actions/mise-setup/action.yml` installs the CI environment.
- `bin/setup` and `bin/doctor` - `bin/setup` installs all managed tools and dependencies, downloads native UDB dependencies, and chooses a C++ toolchain; `bin/doctor` validates the resulting environment.
- CMake 4.4.0 and GNU Make 4.4.1 - Versions are pinned in `.mise.toml`; the ISS build is defined in `backends/cpp_hart_gen/CMakeLists.txt`.
- Prek 0.4.10 - The Rust-native pre-commit runner is pinned in `.mise.toml`; hook definitions and tool versions are in `.pre-commit-config.yaml`.
- Ruff 0.16.0, RuboCop 1.88.2, Prettier 3.9.6, clang-format 22.1.8 hook, ShellCheck 0.11.0, and shfmt 3.11.0-1 hook - Configuration lives in `pyproject.toml`, `.rubocop.yml`, `.prettierrc`, `.clang-format`, `.shellcheckrc`, and `.pre-commit-config.yaml`.
- Renovate - Dependency update policy, custom regex managers, vulnerability alerts, and grouping rules live in `renovate.json`.
- Repository-local agent automation - `.agents/skills/extract-instructions-from-subsection/SKILL.md` defines an AsciiDoc-to-YAML instruction extraction workflow; it is developer automation and not a runtime dependency.

## Key Dependencies

**Critical:**
- `json_schemer` 2.5.0 - Ruby-side JSON Schema validation and reference resolution are implemented in `tools/ruby-gems/udb/lib/udb/obj/database_obj.rb`; the version is locked in `Gemfile.lock`.
- `ruamel-yaml` 0.19.1 and `jsonschema` 4.26.0 - Python-side YAML preservation and schema validation are declared in `pyproject.toml` and locked in `uv.lock`.
- Treetop 1.6.12 - IDL parsing is declared in `tools/ruby-gems/idlc/idlc.gemspec` and locked in `Gemfile.lock`.
- Z3 Ruby binding 0.0.20260727 plus native Z3 `z3-5.0.0` - Constraint solving is loaded by `tools/ruby-gems/udb/lib/udb/z3_loader.rb`; Ruby and native versions are recorded in `Gemfile.lock` and `tools/ruby-gems/udb/lib/udb/Z3_VERSION`.
- Espresso `espresso-18f59c7`, Eqntott `eqntott-392759e`, and Must `must-17fa9f9` - Boolean minimization/logic binaries are versioned by `tools/ruby-gems/udb/lib/udb/ESPRESSO_VERSION`, `tools/ruby-gems/udb/lib/udb/EQNTOTT_VERSION`, and `tools/ruby-gems/udb/lib/udb/MUST_VERSION`.
- ActiveSupport 8.1.3, concurrent-ruby 1.3.8, and Sorbet Runtime 0.6.13363 - Shared Ruby runtime facilities are declared by `tools/ruby-gems/idlc/idlc.gemspec` and `tools/ruby-gems/udb/udb.gemspec`, with versions in `Gemfile.lock`.
- `write_xlsx` 1.15.0 - ISA Explorer spreadsheet output is declared in `tools/ruby-gems/udb-gen/udb-gen.gemspec` and locked in `Gemfile.lock`.
- `deepmerge` 2.1.0 and `tqdm` 4.70.0 - Python configuration merging and progress reporting are declared in `pyproject.toml` and resolved in `uv.lock`.

**Infrastructure:**
- fmt 12.2.0, yaml-cpp 0.9.0, CLI11 2.6.2, Catch2 3.15.2, nlohmann/json 3.11.3, JSON Schema Validator 2.4.0, and CTRE 3.11.0 - CMake fetches these pinned sources in `backends/cpp_hart_gen/CMakeLists.txt`.
- Berkeley SoftFloat commit `a0c6494…` and elfutils/libelf 0.195 with a SHA-256-pinned archive - Native floating-point and ELF support are built by `backends/cpp_hart_gen/CMakeLists.txt`.
- AlmaLinux 8 and GCC Toolset 14 - The reproducible cross-toolchain image is defined in `.toolchain/Dockerfile`; its RISC-V GNU toolchain is pinned to 2026.07.12.
- Gradle 9.6.1, Xtext 2.43.0, ClassGraph 4.8.184, and Shadow 8.1.1 - The standalone Java language server is configured by `tools/eclipse/udb-ls/gradle/wrapper/gradle-wrapper.properties` and `tools/eclipse/udb-ls/build.gradle`.
- Git submodules - Upstream validation and documentation sources are pinned in `.gitmodules`: riscv-opcodes, docs-resources, riscv-isa-manual, LLVM, riscv-tests, and rbi-central.

## Configuration

**Environment:**
- Tool and runtime versions must be changed in `.mise.toml`, `.python-version`, and `.default-gems`; run `bin/setup` after changes so `Gemfile.lock`, `uv.lock`, and `package-lock.json` are installed consistently.
- Architecture behavior must be selected through YAML configurations in `cfgs/`; `_` is the unconfigured architecture used by resolver flows in `Rakefile` and `tools/ruby-gems/udb/lib/udb/resolver.rb`.
- Local C++ toolchain selection is written to the gitignored `.toolchain-local` by `bin/setup` or `bin/.toolchain.sh`; supported switches are `UDB_TOOLCHAIN_CONTAINER` and `UDB_TOOLCHAIN_NONE`.
- Core path/cache overrides are `UDB_ROOT`, `XDG_DATA_HOME`, and `XDG_CACHE_HOME`, consumed by `tools/ruby-gems/udb/lib/udb/paths.rb`, `tools/ruby-gems/udb/lib/udb/dep_paths.rb`, and `tools/ruby-gems/udb/lib/udb/z3_loader.rb`.
- Documentation deployment overrides are `DOCUSAURUS_URL` and `DOCUSAURUS_BASE_URL` in `doc/docusaurus.config.ts`.
- Task-level inputs include `CFG`, `CONFIG`, `JOBS`, `BUILD_TYPE`, `IGNOREUNDEFINED`, and output overrides; representative consumers are `Rakefile`, `backends/cpp_hart_gen/tasks.rake`, and `backends/generators/tasks.rake`.
- No checked-in `.env` or `.env.*` file is present; local setup uses explicit files and environment variables documented by `bin/setup`, `.mise.toml`, and `doc/docusaurus.config.ts`.

**Build:**
- `Rakefile` is the main task graph; new backend tasks are registered in `backends/<backend>/tasks.rake` and tool tasks in `tools/<tool>/tasks.rake`.
- `do` is the supported Rake launcher, while `bin/generate`, `bin/regress`, and `bin/chore` provide stable user-facing command surfaces.
- `backends/cpp_hart_gen/CMakeLists.txt` and `.toolchain/check_cxx.cmake` define the C++ build; `.toolchain/Dockerfile` and `bin/.toolchain.sh` define the optional container execution path.
- `package.json` defines the npm workspace and Antora toolchain; `doc/package.json`, `doc/docusaurus.config.ts`, and `doc/tsconfig.json` define the Docusaurus build.
- `tools/eclipse/dev/org.xtext.udb.parent/pom.xml` defines the Maven/Tycho Eclipse build; `tools/eclipse/udb-ls/build.gradle` and its Gradle wrapper define the shaded stdio language-server build.
- `.pre-commit-config.yaml`, `pyproject.toml`, `.rubocop.yml`, `.prettierrc`, `.clang-format`, and `.shellcheckrc` are the formatting, linting, schema-validation, and license-compliance configuration set.
- `tools/test/regress-tests.yaml` is the source of CI test definitions; `.github/workflows/regress.yml` is generated and must be refreshed through `bin/chore gen regress`.

## Platform Requirements

**Development:**
- macOS or Linux on x86_64/arm64 is the primary native setup path exposed by `bin/mise`; `bin/setup` additionally requires Git, GnuPG, and internet access for first-time tool/dependency installation.
- Core Ruby, Python, Node, schema, and document workflows run natively through mise according to `README.adoc` and `bin/setup`.
- C++/ISS work requires a compiler satisfying `.toolchain/check_cxx.cmake` (effectively GCC 14+ or a compatible Clang with C++23 `constexpr from_chars`) plus RISC-V cross-compilers, or Docker/Podman using the image wired by `bin/.toolchain.sh`.
- Native dependency binaries currently support x64 and arm64 host CPUs, enforced by `tools/ruby-gems/udb/ext/udb_download/extconf.rb` and `tools/ruby-gems/udb/lib/udb/dep_paths.rb`.
- Java language-tooling work requires Java 21 for the Maven/Tycho workspace in `tools/eclipse/dev/org.xtext.udb.parent/` and Java 17+ for `tools/eclipse/udb-ls/`.
- Run `bin/setup` once and `bin/doctor` to verify the complete environment; both scripts are authoritative for local prerequisites.

**Production:**
- This repository does not define a long-running production application; its distributable outputs are static documentation/data, Ruby gems, schema/native release assets, and a C++ toolchain image produced by `.github/workflows/pages.yml`, `.github/workflows/release_gems.yml`, `.github/workflows/schema-release.yml`, `.github/workflows/release_udb_deps.yml`, and `.github/workflows/toolchain-container.yml`.
- Static outputs are hosted on GitHub Pages, configured by `.github/workflows/pages.yml` and `doc/docusaurus.config.ts`.
- Published Ruby libraries target Ruby `~> 3.2` as declared in `tools/ruby-gems/*/*.gemspec`; repository development itself uses the newer Ruby pin in `.mise.toml`.
- The toolchain container targets Linux amd64 and arm64 and is published as `ghcr.io/riscv/udb-toolchain`, as configured by `.github/workflows/toolchain-container.yml` and `bin/.toolchain.sh`.

---

*Stack analysis: 2026-07-30*
