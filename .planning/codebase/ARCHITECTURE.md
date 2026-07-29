<!-- refreshed: 2026-07-30 -->
# Architecture

**Analysis Date:** 2026-07-30

## System Overview

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Command and automation entry points                                          │
├──────────────────┬──────────────────────┬────────────────────────────────────┤
│ Rake facade      │ Generator / query    │ Regression / auxiliary services    │
│ `do`, `Rakefile` │ `bin/generate`,      │ `bin/regress`,                     │
│                  │ `bin/udb`, `bin/idlc`│ `tools/mcp_gen_server/server.py`    │
└────────┬─────────┴──────────┬───────────┴────────────────┬───────────────────┘
         │                    │                            │
         ▼                    ▼                            │ reads
┌─────────────────────────────────────────────────────────┼────────────────────┐
│ Artifact applications and adapters                      │                    │
│ `backends/*/tasks.rake`, `tools/ruby-gems/udb-gen/`     │                    │
└────────────────────────────┬────────────────────────────┘                    │
                             │ queries / renders                               │
                             ▼                                                  │
┌──────────────────────────────────────────────────────────────────────────────┐
│ Configured domain and semantic layer                                         │
│ `tools/ruby-gems/udb/lib/udb/cfg_arch.rb`                                    │
│ `tools/ruby-gems/udb/lib/udb/obj/`                                           │
│ `tools/ruby-gems/udb/lib/udb/condition.rb` + `tools/ruby-gems/idlc/`          │
└────────────────────────────┬─────────────────────────────────────────────────┘
                             │ built by
                             ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ Merge and resolution pipeline                                                │
│ `tools/ruby-gems/udb/lib/udb/resolver.rb`                                    │
│ `tools/ruby-gems/udb/lib/udb/yaml/yaml_resolver.rb`                          │
└───────────────┬───────────────────────────────────────┬──────────────────────┘
                │ reads                                 │ writes
                ▼                                       ▼
┌───────────────────────────────────────┐   ┌──────────────────────────────────┐
│ Authoritative source data             │   │ Derived filesystem snapshots     │
│ `spec/std/isa/`, `spec/custom/isa/`,  │   │ `gen/spec/`, `gen/resolved_spec/`,│
│ `spec/schemas/`, `cfgs/`              │   │ `gen/<backend>/`                 │
└───────────────────────────────────────┘   └──────────────────────────────────┘
```

The system is a data-centric, configuration-resolved generation pipeline. The authoritative RISC-V model is declarative YAML and embedded IDL under `spec/`; Ruby libraries under `tools/ruby-gems/` resolve that data into a configured object graph; generators under `backends/` and `tools/ruby-gems/udb-gen/` fan the same model out into documents, code, simulators, and indexes under `gen/`.

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Command facade | Runs repository Rake tasks inside the mise/Bundler environment and special-cases clean/clobber | `do` |
| Root task registry | Creates the shared resolver/logger and auto-loads backend and tool task files | `Rakefile` |
| Generator facade | Routes supported generator subcommands to the `udb-gen` executable | `bin/generate` |
| UDB CLI | Exposes validation, listing, and inspection commands over configured architectures | `tools/ruby-gems/udb/lib/udb/cli.rb` |
| Resolver | Locates configs, merges standard/custom data, resolves inheritance, and constructs configured architectures | `tools/ruby-gems/udb/lib/udb/resolver.rb` |
| YAML resolver | Applies JSON Merge Patch overlays, `$inherits`, `$remove`, schema validation, source attribution, and optional embedded-IDL compilation | `tools/ruby-gems/udb/lib/udb/yaml/yaml_resolver.rb` |
| Configuration model | Represents unconfigured, partially configured, and fully configured architecture selections | `tools/ruby-gems/udb/lib/udb/config.rb` |
| Base architecture catalog | Defines supported top-level object kinds and aggregate/ref lookup behavior | `tools/ruby-gems/udb/lib/udb/architecture.rb` |
| Configured query API | Lazily loads resolved YAML objects and computes possible/implemented extensions, instructions, CSRs, parameters, and functions | `tools/ruby-gems/udb/lib/udb/cfg_arch.rb` |
| Domain objects | Wrap YAML records with typed behavior for instructions, CSRs, extensions, profiles, manuals, parameters, and related objects | `tools/ruby-gems/udb/lib/udb/obj/` |
| Constraint engine | Converts extension, XLEN, and parameter conditions to logical forms and Z3 satisfiability checks | `tools/ruby-gems/udb/lib/udb/condition.rb`, `tools/ruby-gems/udb/lib/udb/logic.rb`, `tools/ruby-gems/udb/lib/udb/z3.rb` |
| IDL compiler | Parses IDL, builds ASTs and symbol tables, type-checks behavior, and supplies analysis/code-generation passes | `tools/ruby-gems/idlc/lib/idlc.rb`, `tools/ruby-gems/idlc/lib/idlc/` |
| Generator command registry | Auto-loads generator subclasses and supplies shared `--cfg` resolution | `tools/ruby-gems/udb-gen/bin/udb-gen`, `tools/ruby-gems/udb-gen/lib/udb-gen/common_opts.rb` |
| Rake backends | Render configured data into HTML/PDF/AsciiDoc, C/C++/Go/SystemVerilog, profiles, portfolios, and indexes | `backends/` |
| C++ hart backend | Converts configured objects and typed/pruned IDL into generated C++ ISS sources, then builds/tests them with CMake | `backends/cpp_hart_gen/tasks.rake`, `backends/cpp_hart_gen/lib/`, `backends/cpp_hart_gen/cpp/` |
| Regression orchestrator | Expands YAML test/matrix definitions and runs named or tagged jobs locally, including parallel subprocess execution | `tools/test/regress-cli.rb`, `tools/test/regress-tests.yaml` |
| Generated-data query service | Serves MCP tools over stdio by scanning pre-generated YAML and generated IDL documentation under `gen/` | `tools/mcp_gen_server/server.py` |
| Documentation site | Builds the contributor/tool documentation as a Docusaurus application independently of generated ISA manuals | `doc/package.json`, `doc/docusaurus.config.ts`, `doc/docs/` |
| IDE support | Supplies IDL/YAML/ERB grammars plus an Xtext language server and VS Code clients | `tools/vscode/`, `tools/eclipse/` |

## Pattern Overview

**Overall:** Layered data pipeline with a file-backed repository, a configuration-aware domain model, and plugin-like generation adapters.

**Key Characteristics:**
- Treat YAML under `spec/std/isa/` as the canonical domain records and JSON files under `spec/schemas/` as their structural contracts.
- Treat `cfgs/*.yaml` as architecture views: `Udb::Resolver` materializes a standard/custom merge in `gen/spec/` and a fully inherited/schema-checked snapshot in `gen/resolved_spec/`.
- Query data through `Udb::ConfiguredArchitecture` in `tools/ruby-gems/udb/lib/udb/cfg_arch.rb`; its object collections are lazy and memoized rather than loaded at process start.
- Keep formal behavior in IDL source at `spec/std/isa/isa/` and in YAML function-valued keys such as `operation()` in `spec/std/isa/inst/`; compile it through `tools/ruby-gems/idlc/`.
- Add Rake backends through the discovery contract `backends/<name>/tasks.rake`, loaded by `Rakefile`, and add `udb-gen` commands through `tools/ruby-gems/udb-gen/lib/udb-gen/generators/<name>/generator.rb`, auto-loaded by `tools/ruby-gems/udb-gen/bin/udb-gen`.
- Write all derived snapshots and artifacts beneath `gen/`; `tools/mcp_gen_server/server.py` is deliberately a downstream reader of that generated boundary.

## Layers

**Command and Environment Layer:**
- Purpose: Normalize tool versions, working-directory behavior, Bundler setup, and user-facing command syntax.
- Location: `do`, `bin/`, `.mise.toml`
- Contains: Bash wrappers for Rake, Ruby CLIs, Python/Node tools, setup, diagnostics, generation, regression, and toolchain commands.
- Depends on: mise settings in `.mise.toml`, dependency manifests at `Gemfile`, `pyproject.toml`, and `package.json`.
- Used by: Developers, CI workflows in `.github/workflows/`, and regression steps in `tools/test/regress-tests.yaml`.

**Task Orchestration Layer:**
- Purpose: Register dependency-aware generation, build, validation, and maintenance tasks.
- Location: `Rakefile`, `backends/*/tasks.rake`, `tools/*/tasks.rake`
- Contains: Rake namespaces, file/rule tasks, ERB dependencies, format/build steps, and shared process globals.
- Depends on: `Udb::Resolver` from `tools/ruby-gems/udb/lib/udb/resolver.rb` and backend-specific helpers/templates under `backends/`.
- Used by: The `do` facade and test commands declared in `tools/test/regress-tests.yaml`.

**Authoritative Data Layer:**
- Purpose: Store the generic standard architecture, custom overlays, non-ISA records, and data contracts.
- Location: `spec/std/isa/`, `spec/custom/isa/`, `spec/std/non_isa/`, `spec/custom/non_isa/`, `spec/schemas/`
- Contains: One YAML record per top-level domain object, global/include IDL files, parameterized `.layout` sources, AsciiDoc prose, and JSON schemas.
- Depends on: Schema identifiers in `spec/schemas/` and cross-record references resolved by `tools/ruby-gems/udb/lib/udb/yaml/yaml_resolver.rb`.
- Used by: Config resolution in `tools/ruby-gems/udb/lib/udb/resolver.rb`, source generation in `Rakefile`, and schema publication scripts in `tools/scripts/`.

**Configuration and Resolution Layer:**
- Purpose: Turn a config pointer into a deterministic merged/resolved filesystem view.
- Location: `cfgs/`, `tools/ruby-gems/udb/lib/udb/resolver.rb`, `tools/ruby-gems/udb/lib/udb/yaml/`
- Contains: Config lookup, standard/custom overlay selection, JSON Merge Patch, `$inherits`/`$remove` expansion, source tracking, schema URI versioning, stamps, locks, and output indexes.
- Depends on: `spec/std/isa/`, `spec/custom/isa/`, `spec/schemas/`, and config factories in `tools/ruby-gems/udb/lib/udb/config.rb`.
- Used by: Every config-aware Ruby generator in `tools/ruby-gems/udb-gen/`, Rake backend code in `backends/`, and resolved-YAML consumers in `backends/generators/`.

**Domain Query Layer:**
- Purpose: Expose resolved data as behavior-rich Ruby objects in a selected configuration.
- Location: `tools/ruby-gems/udb/lib/udb/architecture.rb`, `tools/ruby-gems/udb/lib/udb/cfg_arch.rb`, `tools/ruby-gems/udb/lib/udb/obj/`
- Contains: Lazy object loaders, lookup hashes, config filtering, reference traversal, encoding checks, profile/manual relationships, ERB environments, and documentation helpers.
- Depends on: Resolved YAML at `gen/resolved_spec/<config>/`, configuration types in `tools/ruby-gems/udb/lib/udb/config.rb`, and semantic services in `tools/ruby-gems/idlc/` and `tools/ruby-gems/udb/lib/udb/condition.rb`.
- Used by: Generators in `tools/ruby-gems/udb-gen/`, backend task code in `backends/`, and the `udb` CLI at `tools/ruby-gems/udb/lib/udb/cli.rb`.

**Semantic and Constraint Layer:**
- Purpose: Determine whether architecture conditions are satisfiable and whether formal behavior is syntactically and semantically valid.
- Location: `tools/ruby-gems/udb/lib/udb/condition.rb`, `tools/ruby-gems/udb/lib/udb/logic.rb`, `tools/ruby-gems/udb/lib/udb/z3.rb`, `tools/ruby-gems/idlc/lib/idlc/`
- Contains: Extension/version requirements, parameter and XLEN terms, Z3 translation, IDL grammar/parser, AST, symbol table, types, pruning, reachability, and documentation passes.
- Depends on: Parameter schemas and extension relationships exposed through `tools/ruby-gems/udb/lib/udb/cfg_arch.rb`, plus IDL sources in `spec/std/isa/isa/` and YAML function bodies in `spec/std/isa/`.
- Used by: Config validity checks, `./do test:idl`, instruction/CSR object methods, and the C++ backend at `backends/cpp_hart_gen/`.

**Artifact Generation Layer:**
- Purpose: Project the configured model into consumer-specific formats.
- Location: `tools/ruby-gems/udb-gen/`, `backends/`
- Contains: CLI subcommands, ERB/template helpers, Rake file rules, AsciiDoc/Antora rendering, ISA explorer tables, headers, C++ ISS code, profile/portfolio documents, and Python format generators.
- Depends on: `Udb::ConfiguredArchitecture`, IDL passes, templates adjacent to each generator, external content in `ext/`, and render/build tools exposed through `bin/`.
- Used by: CI artifact jobs in `tools/test/regress-tests.yaml`, release workflows in `.github/workflows/`, and local users through `bin/generate` or `do`.

**Generated Artifact and Downstream Consumer Layer:**
- Purpose: Hold reproducible merged specs, resolved specs, documentation, code, and build trees.
- Location: `gen/`
- Contains: `gen/cfgs/`, `gen/spec/`, `gen/resolved_spec/`, `gen/manual/`, `gen/cpp_hart_gen/`, `gen/cfg_html_doc/`, `gen/profile/`, and other backend-specific output directories.
- Depends on: Resolution and generation code under `tools/ruby-gems/` and `backends/`.
- Used by: The MCP server at `tools/mcp_gen_server/server.py`, build/test stages in `backends/cpp_hart_gen/tasks.rake`, and CI publication workflows in `.github/workflows/`.

**Verification Layer:**
- Purpose: Validate data/schema/IDL consistency, domain logic, generated artifacts, and cross-language outputs.
- Location: `tools/test/`, `tools/ruby-gems/*/test/`, `tests/`, `backends/cpp_hart_gen/cpp/test/`, `.github/workflows/`
- Contains: Declarative regression definitions, a local matrix runner, Minitest suites, pytest tests, C++ tests, ISA fixtures, and golden outputs.
- Depends on: Commands in `bin/` and `do`, plus generated data under `gen/`.
- Used by: `bin/regress`, pre-commit configuration at `.pre-commit-config.yaml`, and GitHub Actions.

## Data Flow

### Primary Request Path

1. A user selects a generator through `bin/generate`, which dispatches supported subcommands to `bin/udb-gen` (`bin/generate:51`, `bin/generate:53`).
2. The `udb-gen` executable auto-loads generator subclasses and invokes the selected command; shared options lazily request `resolver.cfg_arch_for(...)` (`tools/ruby-gems/udb-gen/bin/udb-gen:11`, `tools/ruby-gems/udb-gen/bin/udb-gen:56`, `tools/ruby-gems/udb-gen/lib/udb-gen/common_opts.rb:36`).
3. `Udb::Resolver#cfg_arch_for` resolves the config YAML, merges `spec/std/isa/` with any `spec/custom/isa/<overlay>/`, expands/validates the merged data, and constructs `Udb::ConfiguredArchitecture` (`tools/ruby-gems/udb/lib/udb/resolver.rb:335`, `tools/ruby-gems/udb/lib/udb/resolver.rb:341`).
4. `Udb::Yaml::Resolver` applies JSON Merge Patch during merge, expands `$inherits`/`$remove`, validates against `spec/schemas/`, records `$source`, and writes `gen/resolved_spec/<config>/` (`tools/ruby-gems/udb/lib/udb/yaml/yaml_resolver.rb:109`, `tools/ruby-gems/udb/lib/udb/yaml/yaml_resolver.rb:198`, `tools/ruby-gems/udb/lib/udb/yaml/yaml_resolver.rb:301`, `tools/ruby-gems/udb/lib/udb/yaml/yaml_resolver.rb:341`).
5. `Udb::ConfiguredArchitecture` lazily reads the relevant resolved YAML directories into typed objects and lookup hashes (`tools/ruby-gems/udb/lib/udb/cfg_arch.rb:733`, `tools/ruby-gems/udb/lib/udb/cfg_arch.rb:747`, `tools/ruby-gems/udb/lib/udb/cfg_arch.rb:758`).
6. The selected generator queries those objects, evaluates templates, resolves documentation links, and writes a consumer artifact beneath its output directory; the extension document path is representative (`tools/ruby-gems/udb-gen/lib/udb-gen/generators/ext_doc/generator.rb:133`, `tools/ruby-gems/udb-gen/lib/udb-gen/generators/ext_doc/generator.rb:155`, `tools/ruby-gems/udb-gen/lib/udb-gen/generators/ext_doc/generator.rb:162`).

### Rake Backend Flow

1. `do` starts Rake inside the repository tool environment (`do:22`).
2. `Rakefile` creates shared process state and loads every `backends/*/tasks.rake` and `tools/*/tasks.rake` file (`Rakefile:20`, `Rakefile:24`, `Rakefile:43`, `Rakefile:48`).
3. A backend task obtains a configured architecture from the shared resolver and evaluates adjacent templates; C++ generation uses `CppHartGen::TemplateEnv` and places source in `gen/cpp_hart_gen/` (`backends/cpp_hart_gen/tasks.rake:95`, `backends/cpp_hart_gen/tasks.rake:97`, `backends/cpp_hart_gen/tasks.rake:101`).
4. File/rule dependencies trigger formatters, document renderers, compilers, or downstream tests through wrappers in `bin/` (`backends/cpp_hart_gen/tasks.rake:157`, `backends/instructions_appendix/tasks.rake`, `backends/cfg_html_doc/html_gen.rake`).

### IDL Compilation Flow

1. Global definitions and includes live in `spec/std/isa/isa/globals.isa` and `spec/std/isa/isa/*.idl`; instruction and CSR function bodies live in YAML such as `spec/std/isa/inst/M/mul.yaml` and `spec/std/isa/csr/misa.yaml`.
2. `Idl::Compiler` parses files with the Treetop grammar, recursively replaces include nodes, and returns fresh ASTs from a shared parse cache (`tools/ruby-gems/idlc/lib/idlc.rb:34`, `tools/ruby-gems/idlc/lib/idlc.rb:58`, `tools/ruby-gems/idlc/lib/idlc.rb:81`, `tools/ruby-gems/idlc/lib/idlc.rb:133`).
3. `Udb::ConfiguredArchitecture` compiles global IDL and freezes it into a configuration-specific symbol table (`tools/ruby-gems/udb/lib/udb/cfg_arch.rb:202`, `tools/ruby-gems/udb/lib/udb/cfg_arch.rb:234`, `tools/ruby-gems/udb/lib/udb/cfg_arch.rb:248`).
4. Instruction and CSR objects parse/type-check function bodies for the relevant XLEN, then expose pruned/reachable ASTs to generators and validation (`tools/ruby-gems/udb/lib/udb/obj/instruction.rb:1103`, `tools/ruby-gems/udb/lib/udb/obj/instruction.rb:1119`, `tools/ruby-gems/udb/lib/udb/obj/csr.rb`).
5. Passes in `tools/ruby-gems/idlc/lib/idlc/passes/` feed documentation output and the C++ templates/helpers under `backends/cpp_hart_gen/`.

### Regression Flow

1. `bin/regress` starts `tools/test/regress-cli.rb` from the caller's working directory while using repository dependencies (`bin/regress`).
2. The runner loads `tools/test/regress-tests.yaml`, expands matrix combinations, substitutes workspace/matrix variables, and creates ordered jobs (`tools/test/regress-cli.rb:134`, `tools/test/regress-cli.rb:164`).
3. A named job streams its subprocess output; tagged/all jobs use a bounded Ruby thread pool and one subprocess sequence per expanded job (`tools/test/regress-cli.rb:239`, `tools/test/regress-cli.rb:249`, `tools/test/regress-cli.rb:270`).
4. The same declarative definitions are translated into CI context by `tools/test/gen_regress.py` and consumed by `.github/workflows/regress.yml`.

### Generated-Data Query Flow

1. The user first materializes `gen/resolved_spec/` through `do gen:resolved_arch` or another resolver-backed generator (`Rakefile`, `tools/ruby-gems/udb/lib/udb/resolver.rb`).
2. `tools/mcp_gen_server/server.py` walks YAML only under `gen/`, performs instruction/CSR/extension/function searches, and exposes handlers as MCP tools.
3. The MCP server validates direct reads remain inside `gen/` and uses stdio transport rather than an authenticated network listener (`tools/mcp_gen_server/server.py:134`, `tools/mcp_gen_server/server.py:1412`, `tools/mcp_gen_server/server.py:1443`).

**State Management:**
- Persistent source state is file-backed in `spec/` and `cfgs/`; persistent derived state is isolated under `gen/` and Rake stamps under `.stamps/` (`tools/ruby-gems/udb/lib/udb/resolver.rb`, `Rakefile`).
- In-process state is memoized in resolver/configured-architecture hashes, class-level raw-YAML caches, IDL parse caches, schema caches, object-level deferred results, and UDB logger/progress-bar singletons (`tools/ruby-gems/udb/lib/udb/resolver.rb`, `tools/ruby-gems/udb/lib/udb/cfg_arch.rb`, `tools/ruby-gems/idlc/lib/idlc.rb`, `tools/ruby-gems/udb/lib/udb/obj/database_obj.rb`, `tools/ruby-gems/udb/lib/udb/log.rb`).
- There is no database server or application session store in the core architecture; `gen/` is the serialization boundary shared with non-Ruby consumers such as `tools/mcp_gen_server/server.py` and `backends/generators/`.

## Key Abstractions

**`Udb::Resolver`:**
- Purpose: Convert a config name/path into a merged/resolved architecture and configured API object.
- Examples: `tools/ruby-gems/udb/lib/udb/resolver.rb`, `cfgs/_.yaml`, `gen/resolved_spec/_/`
- Pattern: Facade plus filesystem materializer, guarded by mutexes, lock files, stamps, and per-config caches.

**`Udb::Resolver::ConfigInfo`:**
- Purpose: Carry config identity, source/overlay paths, unresolved/resolved YAML, and derived output paths together.
- Examples: `tools/ruby-gems/udb/lib/udb/resolver.rb`
- Pattern: Sorbet `T::Struct` value object shared by resolver and configuration instances.

**`Udb::AbstractConfig`:**
- Purpose: Present one interface across unconfigured, partially configured, fully configured, and portfolio-derived selections.
- Examples: `tools/ruby-gems/udb/lib/udb/config.rb`, `cfgs/_.yaml`, `cfgs/rv64.yaml`, `cfgs/example_rv64_with_overlay.yaml`
- Pattern: Factory-selected strategy subclasses `Udb::UnConfig`, `Udb::PartialConfig`, and `Udb::FullConfig`.

**`Udb::Architecture` / `Udb::ConfiguredArchitecture`:**
- Purpose: Define the catalog of top-level object types and expose a configuration-aware, lazy query surface.
- Examples: `tools/ruby-gems/udb/lib/udb/architecture.rb`, `tools/ruby-gems/udb/lib/udb/cfg_arch.rb`
- Pattern: Base catalog plus configured subclass; metaprogramming creates plural collections, name-indexed hashes, and single-object getters from `Architecture::OBJS`.

**`Udb::DatabaseObject` / `Udb::TopLevelDatabaseObject`:**
- Purpose: Attach source paths, kind/name identity, config context, schema validation, conditions, descriptions, and memoized behavior to YAML records.
- Examples: `tools/ruby-gems/udb/lib/udb/obj/database_obj.rb`, `tools/ruby-gems/udb/lib/udb/obj/instruction.rb`, `tools/ruby-gems/udb/lib/udb/obj/csr.rb`
- Pattern: Domain-object hierarchy with back-reference to `Udb::ConfiguredArchitecture` and specialized subclasses per schema kind.

**Condition and Z3 Model:**
- Purpose: Represent `definedBy`, extension requirements, parameter comparisons, and XLEN constraints, then answer implication/compatibility/satisfiability questions.
- Examples: `tools/ruby-gems/udb/lib/udb/condition.rb`, `tools/ruby-gems/udb/lib/udb/logic.rb`, `tools/ruby-gems/udb/lib/udb/z3.rb`
- Pattern: Composite condition tree translated to a solver-specific intermediate layer with memoized configuration results.

**`Idl::Compiler`, AST, and Symbol Table:**
- Purpose: Compile formal architectural behavior embedded in YAML or global IDL files and make it available to validation and generators.
- Examples: `tools/ruby-gems/idlc/lib/idlc.rb`, `tools/ruby-gems/idlc/lib/idlc/ast.rb`, `tools/ruby-gems/idlc/lib/idlc/symbol_table.rb`, `tools/ruby-gems/idlc/lib/idlc/passes/`
- Pattern: Compiler pipeline: Treetop parse tree → IDL AST → symbol population/type checking → analysis or rendering passes.

**`UdbGen::Subcommand`:**
- Purpose: Standardize generator registration, usage, options, config resolution, and exit behavior.
- Examples: `tools/ruby-gems/udb-gen/lib/udb-gen/subcommand.rb`, `tools/ruby-gems/udb-gen/lib/udb-gen/common_opts.rb`, `tools/ruby-gems/udb-gen/lib/udb-gen/generators/`
- Pattern: Auto-discovered command subclasses with a shared configured-architecture dependency.

**Rake Backend Contract:**
- Purpose: Register repository-local generators/builds that need file dependencies, mixed languages, or multi-step artifact pipelines.
- Examples: `Rakefile`, `backends/cfg_html_doc/tasks.rake`, `backends/cpp_hart_gen/tasks.rake`, `backends/prm_pdf/tasks.rake`
- Pattern: Convention-based plugin discovery by `tasks.rake`, with templates and helpers kept inside each backend directory.

**`Udb::PortfolioDesign`:**
- Purpose: Adapt profile/profile-release data into a configuration-aware document-generation context without creating an object/config construction cycle.
- Examples: `tools/ruby-gems/udb/lib/udb/portfolio_design.rb`, `backends/portfolio/tasks.rake`, `backends/profile/tasks.rake`
- Pattern: Two-stage construction: obtain portfolio objects from the unconfigured architecture, derive a config, then rebuild configured portfolio objects.

## Entry Points

**Rake command facade:**
- Location: `do`
- Triggers: Direct developer/CI invocation such as `./do test:idl CFG=rv64` or `./do gen:arch`.
- Responsibilities: Enter the mise/Bundler environment, load `Rakefile`, and run top-level tasks.

**Artifact generator facade:**
- Location: `bin/generate`, `bin/udb-gen`, `tools/ruby-gems/udb-gen/bin/udb-gen`
- Triggers: `./bin/generate <subcommand>` or `./bin/udb-gen <subcommand>`.
- Responsibilities: Dispatch command plugins, resolve a selected config, and invoke a generator.

**Database CLI:**
- Location: `bin/udb`, `tools/ruby-gems/udb/bin/udb`, `tools/ruby-gems/udb/lib/udb/cli.rb`
- Triggers: `./bin/udb validate ...`, `show ...`, or `list ...`.
- Responsibilities: Validate specs/configs and expose human-readable configured database queries.

**IDL compiler CLI:**
- Location: `bin/idlc`, `tools/ruby-gems/idlc/bin/idlc`, `tools/ruby-gems/idlc/lib/idlc/cli.rb`
- Triggers: Direct IDL compiler invocation and Rake validation/generation.
- Responsibilities: Parse, type-check, and inspect standalone IDL inputs.

**Regression CLI:**
- Location: `bin/regress`, `tools/test/regress-cli.rb`
- Triggers: Named, tagged, matrix-filtered, or full regression requests.
- Responsibilities: Expand `tools/test/regress-tests.yaml` into local jobs and report pass/fail results.

**Environment lifecycle commands:**
- Location: `bin/setup`, `bin/doctor`, `bin/pre-commit`, `bin/chore`
- Triggers: Repository setup, health checks, hook execution, and maintenance commands.
- Responsibilities: Install/verify toolchains and dependencies, run checks, and regenerate managed repository artifacts.

**MCP server:**
- Location: `tools/mcp_gen_server/server.py`
- Triggers: An MCP client starts the Python process over stdio after `gen/` data exists.
- Responsibilities: Search and read generated architecture YAML and IDL function documentation within the `gen/` boundary.

**Documentation web application:**
- Location: `doc/package.json`, `doc/docusaurus.config.ts`, `doc/src/pages/index.tsx`
- Triggers: npm workspace scripts such as `npm --workspace doc run build`.
- Responsibilities: Build the project documentation site from `doc/docs/` and `doc/src/`.

**Generated C++ ISS executable:**
- Location: `backends/cpp_hart_gen/cpp/src/iss.cpp`, `backends/cpp_hart_gen/CMakeLists.txt`
- Triggers: `./do build:cpp_hart CONFIG=<cfg>` and subsequent invocation from generated build output.
- Responsibilities: Execute the generated/configured hart model and support C++ unit/ISA tests.

## Architectural Constraints

- **Threading:** Rake's thread pool is configured by `JOBS` and defaults to one worker in `Rakefile`; the regression runner uses Ruby threads to launch isolated subprocess jobs in `tools/test/regress-cli.rb`; resolver writes use a mutex plus filesystem locks in `tools/ruby-gems/udb/lib/udb/resolver.rb`.
- **Global state:** Repository Rake tasks share `$root`, `$resolver`, `$logger`, `$jobs`, and `$rake_cmd_runner` from `Rakefile`; library-wide caches/singletons exist in `tools/ruby-gems/udb/lib/udb/cfg_arch.rb`, `tools/ruby-gems/idlc/lib/idlc.rb`, `tools/ruby-gems/udb/lib/udb/obj/database_obj.rb`, and `tools/ruby-gems/udb/lib/udb/log.rb`.
- **Circular imports:** Portfolio generation deliberately separates architecture-only portfolio objects from the later configured architecture to avoid a `PortfolioGroup` ↔ `ConfiguredArchitecture` construction cycle; preserve the sequence in `backends/portfolio/tasks.rake` and `backends/profile/tasks.rake`.
- **Filesystem boundary:** Config-aware work must use the materialized `gen/spec/` and `gen/resolved_spec/` paths produced by `tools/ruby-gems/udb/lib/udb/resolver.rb`; downstream Python/MCP consumers at `backends/generators/` and `tools/mcp_gen_server/server.py` depend on that boundary.
- **Plugin discovery:** A repository-local Rake backend is invisible unless it exposes `backends/<name>/tasks.rake`, and a generator CLI command is invisible unless its class lives under `tools/ruby-gems/udb-gen/lib/udb-gen/generators/*/generator.rb`.
- **Source identity:** Top-level YAML filenames must match their `name` field, and resolved records carry `$source`; enforcement is in `tools/ruby-gems/udb/lib/udb/yaml/yaml_resolver.rb`.
- **Generated-source discipline:** Parameterized architecture families originate in `.layout` files under `spec/std/isa/`; expansion and read-only chmod behavior are centralized in `Rakefile` under `gen:arch`.
- **Process model:** Core commands are batch-oriented filesystem processes, while the only query service in `tools/mcp_gen_server/server.py` uses stdio; there is no shared daemon or transactional database in `tools/ruby-gems/udb/`.
- **Platform semantics:** Shell wrappers and IDL progress handling rely on POSIX facilities such as Bash, `realpath`, symlinks, file locking, signals, and `fork` in `bin/`, `tools/ruby-gems/udb/lib/udb/resolver.rb`, and `tools/ruby-gems/idlc/lib/idlc.rb`.

## Anti-Patterns

### Reading Canonical YAML Directly for a Config-Sensitive Backend

**What happens:** A generator reads `spec/std/isa/` and manually filters objects, bypassing overlays, `$inherits`, `$remove`, configuration conditions, and source/schema normalization from `tools/ruby-gems/udb/lib/udb/resolver.rb`.
**Why it's wrong:** The output can disagree with `Udb::ConfiguredArchitecture` and with resolved consumers under `gen/resolved_spec/`, especially for configs such as `cfgs/example_rv64_with_overlay.yaml` and `cfgs/qc_iu.yaml`.
**Do this instead:** Use `resolver.cfg_arch_for(config)` and domain queries as in `tools/ruby-gems/udb-gen/lib/udb-gen/common_opts.rb`; if a Python generator needs raw files, pass `cfg_arch.path` as in `backends/generators/tasks.rake`.

### Editing Derived Architecture or Artifact Files

**What happens:** A change is made directly in `gen/` or in a YAML file expanded from a `.layout` source under `spec/std/isa/`.
**Why it's wrong:** Resolver/backend runs replace `gen/`, while `./do gen:arch` regenerates and chmods managed architecture records according to `Rakefile`.
**Do this instead:** Edit canonical YAML in `spec/std/isa/`, the applicable overlay in `spec/custom/isa/<overlay>/`, or the `.layout` source under `spec/std/isa/`; regenerate through `do` or `bin/generate`.

### Bypassing Generator Discovery Contracts

**What happens:** A standalone script is added without a `backends/<name>/tasks.rake` registration or a `UdbGen::Subcommand` generator under `tools/ruby-gems/udb-gen/lib/udb-gen/generators/`.
**Why it's wrong:** It is absent from `do`/`udb-gen` discovery, does not naturally share config resolution, and is harder to place in `tools/test/regress-tests.yaml`.
**Do this instead:** Use the Rake backend convention in `Rakefile` for multi-step/mixed-language pipelines or the subcommand convention in `tools/ruby-gems/udb-gen/bin/udb-gen` for user-facing generator commands.

### Constructing Configured Portfolio Objects in One Step

**What happens:** Profile/release objects are asked to derive their own `ConfiguredArchitecture` while already requiring configured object behavior.
**Why it's wrong:** It creates the construction dependency explicitly guarded against in `backends/portfolio/tasks.rake`.
**Do this instead:** Follow `pf_create_arch` → derive the `PortfolioGroup` → `pf_create_cfg_arch` → reload configured portfolio objects in `backends/portfolio/tasks.rake` and `backends/profile/tasks.rake`.

## Error Handling

**Strategy:** Fail fast at command boundaries and preserve source-aware diagnostic context through the resolution, schema, configuration, and IDL layers.

**Patterns:**
- Raise path/config errors before resolution in `tools/ruby-gems/udb/lib/udb/resolver.rb` and `tools/ruby-gems/udb/lib/udb/config.rb`.
- Raise structured schema errors with data/schema pointers through `TopLevelDatabaseObject::SchemaValidationError` in `tools/ruby-gems/udb/lib/udb/obj/database_obj.rb`.
- Preserve YAML source paths, source-line metadata, and IDL parser locations through `tools/ruby-gems/udb/lib/udb/yaml/comment_parser.rb`, `tools/ruby-gems/udb/lib/udb/yaml/yaml_resolver.rb`, and `tools/ruby-gems/idlc/lib/idlc.rb`.
- Return explicit usage/data/error exit codes from TTY/Thor CLIs in `tools/ruby-gems/udb-gen/bin/udb-gen`, `tools/ruby-gems/udb/lib/udb/cli.rb`, and `tools/test/regress-cli.rb`.
- Let Rake `sh`/file rules fail the task on non-zero subprocess status in `Rakefile` and `backends/*/tasks.rake`.
- Reject MCP paths outside generated YAML and surface unknown tools as errors in `tools/mcp_gen_server/server.py`.

## Cross-Cutting Concerns

**Logging:** Use `Udb.logger` and progress helpers from `tools/ruby-gems/udb/lib/udb/log.rb` inside libraries/generators; Rake-oriented portfolio/profile code also uses the shared `$logger` from `Rakefile`.

**Validation:** Apply JSON Schema from `spec/schemas/` during YAML resolution and domain-object validation in `tools/ruby-gems/udb/lib/udb/yaml/yaml_resolver.rb` and `tools/ruby-gems/udb/lib/udb/obj/database_obj.rb`; apply config/condition checks in `tools/ruby-gems/udb/lib/udb/cfg_arch.rb`; apply IDL type checking in `tools/ruby-gems/idlc/`.

**Authentication:** Not applicable to the batch-oriented core in `do`, `bin/`, `tools/ruby-gems/`, and `backends/`; the query service in `tools/mcp_gen_server/server.py` is a local stdio MCP process and enforces filesystem scope rather than user identity.

**Caching and Concurrency:** Reuse per-config resolver objects and lock materialization in `tools/ruby-gems/udb/lib/udb/resolver.rb`; reuse raw YAML and IDL parse results in `tools/ruby-gems/udb/lib/udb/cfg_arch.rb` and `tools/ruby-gems/idlc/lib/idlc.rb`; protect shared failure collection in `tools/test/regress-cli.rb`.

**Source and Licensing Metadata:** Preserve `$source` in resolved YAML through `tools/ruby-gems/udb/lib/udb/yaml/yaml_resolver.rb`; retain SPDX headers throughout `spec/`, `tools/`, and `backends/`; repository-wide license checks are configured in `.pre-commit-config.yaml` and `REUSE.toml`.

---

*Architecture analysis: 2026-07-30*
