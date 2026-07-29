# Codebase Structure

**Analysis Date:** 2026-07-30

## Directory Layout

```text
LFX_RISCV_SpecChoice/
├── .agents/skills/          # Repository-specific agent workflows
├── .github/                 # CI workflows, composite actions, issue templates
├── .toolchain/              # C++/RISC-V toolchain container definition and checks
├── .vscode/                 # Repository workspace settings
├── backends/                # Rake-discovered artifact generators
│   ├── cfg_html_doc/        # Per-configuration Antora/HTML documentation
│   ├── cpp_hart_gen/        # Generated C++ instruction-set simulator
│   ├── generators/          # Python Go/C/SystemVerilog exporters
│   ├── instructions_appendix/
│   ├── portfolio/           # Shared portfolio/profile document support
│   ├── prm_pdf/             # Processor requirements manual generator
│   └── profile/             # Profile release document generator
├── bin/                     # mise-aware command and tool wrappers
├── cfgs/                    # Architecture configurations and generated profile configs
│   └── profile/
├── doc/                     # Docusaurus project docs plus design/reference prose
│   ├── docs/
│   ├── src/
│   └── static/
├── ext/                     # Pinned external Git submodules
├── sorbet/                  # Ruby static-type configuration and RBI interfaces
├── spec/                    # Authoritative UDB data and schemas
│   ├── schemas/
│   ├── std/
│   │   ├── isa/
│   │   └── non_isa/
│   └── custom/
│       ├── isa/
│       └── non_isa/
├── tests/                   # Repository-level ISA data, fixtures, and golden outputs
├── tools/                   # Libraries, test runner, utilities, IDE and service tooling
│   ├── common/
│   ├── eclipse/
│   ├── internal-gems/
│   ├── mcp_gen_server/
│   ├── node/
│   ├── python/
│   ├── ruby-gems/
│   │   ├── idl_highlighter/
│   │   ├── idlc/
│   │   ├── udb/
│   │   ├── udb-gen/
│   │   └── udb_helpers/
│   ├── scripts/
│   ├── test/
│   └── vscode/
├── gen/                     # Gitignored resolved data and generated artifacts
├── do                       # Rake facade
├── Rakefile                 # Root task graph and backend discovery
├── Gemfile                  # Ruby workspace
├── pyproject.toml           # Python workspace
├── package.json             # Node/Antora workspace
└── .mise.toml               # Pinned development tool versions
```

## Directory Purposes

**`spec/`:**
- Purpose: Store the canonical architecture database, non-ISA specifications, custom overlays, and structural contracts.
- Contains: YAML records in `spec/std/isa/` and `spec/custom/isa/`, non-ISA YAML in `spec/std/non_isa/` and `spec/custom/non_isa/`, and JSON Schema files in `spec/schemas/`.
- Key files: `spec/std/isa/ext/M.yaml`, `spec/std/isa/inst/M/mul.yaml`, `spec/std/isa/csr/misa.yaml`, `spec/schemas/inst_schema.json`

**`spec/std/isa/`:**
- Purpose: Organize standard RISC-V objects by schema kind.
- Contains: `ext/`, `inst/`, `csr/`, `param/`, `profile/`, `profile_family/`, `profile_release/`, `manual/`, `manual_version/`, `register_file/`, instruction metadata directories, exception/interrupt codes, `prose/`, and global IDL in `isa/`.
- Key files: `spec/std/isa/isa/globals.isa`, `spec/std/isa/manual/isa.yaml`, `spec/std/isa/profile/RVA23U64.yaml`, `spec/std/isa/README.adoc`

**`spec/custom/isa/`:**
- Purpose: Overlay or extend the standard architecture for a named custom implementation.
- Contains: One subtree per overlay, mirroring standard object directories such as `ext/`, `inst/`, `csr/`, `exception_code/`, and `isa/`.
- Key files: `spec/custom/isa/example/ext/Xcustom.yaml`, `spec/custom/isa/qc_iu/isa/globals.isa`, `cfgs/example_rv64_with_overlay.yaml`, `cfgs/qc_iu.yaml`

**`spec/schemas/`:**
- Purpose: Define the JSON Schema contract for every YAML object/config kind.
- Contains: `*_schema.json` files, shared definitions in `schema_defs.json`, and the bundled JSON Schema draft in `json-schema-draft-07.json`.
- Key files: `spec/schemas/config_schema.json`, `spec/schemas/ext_schema.json`, `spec/schemas/inst_schema.json`, `spec/schemas/csr_schema.json`

**`cfgs/`:**
- Purpose: Select configuration type, extension/version requirements, parameter values, compatibility, and optional custom overlay.
- Contains: Root configs such as `cfgs/_.yaml`, `cfgs/rv32.yaml`, `cfgs/rv64.yaml`, custom configs, and strict profile-derived configs under `cfgs/profile/`.
- Key files: `cfgs/_.yaml`, `cfgs/rv64.yaml`, `cfgs/example_rv64_with_overlay.yaml`, `cfgs/profile/RVA23U64.yaml`

**`tools/ruby-gems/`:**
- Purpose: House the reusable Ruby implementation as a multi-gem workspace.
- Contains: Core database gem `tools/ruby-gems/udb/`, IDL compiler `tools/ruby-gems/idlc/`, generator CLI `tools/ruby-gems/udb-gen/`, shared helpers `tools/ruby-gems/udb_helpers/`, and AsciiDoc highlighting `tools/ruby-gems/idl_highlighter/`.
- Key files: `tools/ruby-gems/udb/lib/udb/resolver.rb`, `tools/ruby-gems/idlc/lib/idlc.rb`, `tools/ruby-gems/udb-gen/bin/udb-gen`, `tools/ruby-gems/tasks.rake`

**`tools/ruby-gems/udb/lib/udb/`:**
- Purpose: Implement config resolution, the configured architecture API, domain objects, schema validation, conditions, and solver integration.
- Contains: Core classes at the directory root, YAML resolution helpers in `yaml/`, embedded-IDL adapters in `idl/`, and domain models in `obj/`.
- Key files: `tools/ruby-gems/udb/lib/udb/resolver.rb`, `tools/ruby-gems/udb/lib/udb/cfg_arch.rb`, `tools/ruby-gems/udb/lib/udb/architecture.rb`, `tools/ruby-gems/udb/lib/udb/obj/database_obj.rb`

**`tools/ruby-gems/idlc/`:**
- Purpose: Implement the ISA Description Language compiler.
- Contains: Grammar/parser, syntax nodes, AST, symbol table, type system, CLI, analysis/rendering passes, tests, and the `idlc` executable.
- Key files: `tools/ruby-gems/idlc/lib/idlc/idl.treetop`, `tools/ruby-gems/idlc/lib/idlc.rb`, `tools/ruby-gems/idlc/lib/idlc/ast.rb`, `tools/ruby-gems/idlc/lib/idlc/passes/`

**`tools/ruby-gems/udb-gen/`:**
- Purpose: Provide user-facing, auto-discovered generator subcommands.
- Contains: Shared command/options code in `lib/udb-gen/`, generator implementations in `lib/udb-gen/generators/`, and adjacent templates/assets/themes.
- Key files: `tools/ruby-gems/udb-gen/bin/udb-gen`, `tools/ruby-gems/udb-gen/lib/udb-gen/common_opts.rb`, `tools/ruby-gems/udb-gen/lib/udb-gen/generators/manual/generator.rb`

**`backends/`:**
- Purpose: Contain repository-local, dependency-aware artifact pipelines loaded by `Rakefile`.
- Contains: A `tasks.rake` contract per backend, backend-specific Ruby/Python/C++ helpers, and ERB/AsciiDoc/C++ templates.
- Key files: `backends/cpp_hart_gen/tasks.rake`, `backends/cfg_html_doc/tasks.rake`, `backends/prm_pdf/tasks.rake`, `backends/generators/tasks.rake`

**`bin/`:**
- Purpose: Keep user commands inside the pinned mise environment and hide language/tool invocation details.
- Contains: Hand-written facades such as `bin/setup`, `bin/doctor`, `bin/generate`, `bin/regress`, and `bin/chore`, plus direct wrappers such as `bin/ruby`, `bin/uv`, `bin/npm`, `bin/udb`, and `bin/idlc`.
- Key files: `bin/setup`, `bin/doctor`, `bin/generate`, `bin/regress`, `bin/mise`

**`tools/test/` and `tests/`:**
- Purpose: Define and execute repository-wide regression jobs and store cross-component fixtures/golden data.
- Contains: The runner and test schema in `tools/test/`, plus ISA assembly, input data, and golden output in `tests/`.
- Key files: `tools/test/regress-cli.rb`, `tools/test/regress-tests.yaml`, `tools/test/tests-schema.json`, `tests/golden/all_instructions.golden.adoc`

**`tools/`:**
- Purpose: Hold tooling not owned by the core published gems or artifact backends.
- Contains: Python readers/scripts in `tools/python/`, maintenance utilities in `tools/scripts/`, schema documentation gem in `tools/internal-gems/`, MCP service in `tools/mcp_gen_server/`, grammar helpers in `tools/node/`, and IDE support in `tools/eclipse/` and `tools/vscode/`.
- Key files: `tools/python/udb.py`, `tools/mcp_gen_server/server.py`, `tools/internal-gems/schema_doc_gen/lib/schema_doc_gen.rb`, `tools/eclipse/dev/org.xtext.udb.parent/`

**`doc/`:**
- Purpose: Build the project/developer documentation website and retain source/reference prose.
- Contains: Docusaurus Markdown/MDX in `doc/docs/`, React/custom theme code in `doc/src/`, images in `doc/static/`, and standalone AsciiDoc references at `doc/*.adoc`.
- Key files: `doc/package.json`, `doc/docusaurus.config.ts`, `doc/sidebars.ts`, `doc/docs/developer/tools-overview.mdx`

**`ext/`:**
- Purpose: Pin upstream manuals, test suites, opcode data, documentation resources, LLVM, and Ruby type data.
- Contains: Git submodules declared in `.gitmodules`.
- Key files: `.gitmodules`, `ext/riscv-isa-manual/`, `ext/riscv-tests/`, `ext/docs-resources/`, `ext/riscv-opcodes/`

**`sorbet/`:**
- Purpose: Configure Sorbet and retain generated/handwritten RBI interfaces for Ruby static typing.
- Contains: `sorbet/config`, gem annotations in `sorbet/rbi/annotations/`, generated gem RBIs in `sorbet/rbi/gems/`, and architecture DSL RBI in `sorbet/rbi/dsl/`.
- Key files: `sorbet/config`, `sorbet/rbi/dsl/udb/architecture.rbi`, `sorbet/tapioca/config.yml`

**`.github/` and `.toolchain/`:**
- Purpose: Define CI/release automation and the optional containerized C++/RISC-V build environment.
- Contains: Workflows and composite setup actions in `.github/`, plus container/CMake checks in `.toolchain/`.
- Key files: `.github/workflows/regress.yml`, `.github/actions/mise-setup/action.yml`, `.toolchain/Dockerfile`, `.toolchain/check_cxx.cmake`

**`.agents/skills/`:**
- Purpose: Store repository-specific agent procedures.
- Contains: One skill directory with a complete `SKILL.md` contract per procedure.
- Key files: `.agents/skills/extract-instructions-from-subsection/SKILL.md`

## Key File Locations

**Entry Points:**
- `do`: Primary facade for Rake tasks.
- `bin/generate`: Language-neutral artifact generator dispatcher.
- `bin/udb`: Core database validation/query CLI wrapper.
- `bin/idlc`: IDL compiler CLI wrapper.
- `bin/regress`: Local regression runner wrapper.
- `bin/setup`: One-command environment bootstrap.
- `tools/mcp_gen_server/server.py`: Generated-database MCP stdio server.
- `doc/src/pages/index.tsx`: Docusaurus documentation home page.
- `backends/cpp_hart_gen/cpp/src/iss.cpp`: Generated hart simulator executable source entry.

**Configuration:**
- `.mise.toml`: Tool versions and repository environment.
- `Gemfile`: Local Ruby gem workspace and external gems.
- `pyproject.toml`: Python project, dependency groups, and Ruff settings.
- `package.json`: Root Node/Antora dependencies and `doc` workspace.
- `doc/package.json`: Docusaurus scripts and dependencies.
- `cfgs/*.yaml`: Architecture configurations.
- `spec/schemas/*.json`: Data contracts.
- `.pre-commit-config.yaml`: Repository pre-commit checks.
- `sorbet/config`: Ruby type-check inputs.

**Core Logic:**
- `tools/ruby-gems/udb/lib/udb/resolver.rb`: Config-to-resolved-spec orchestration.
- `tools/ruby-gems/udb/lib/udb/yaml/yaml_resolver.rb`: Overlay/inheritance/schema transformation.
- `tools/ruby-gems/udb/lib/udb/cfg_arch.rb`: Configured query model.
- `tools/ruby-gems/udb/lib/udb/architecture.rb`: Top-level object catalog.
- `tools/ruby-gems/udb/lib/udb/obj/`: Domain behavior by record kind.
- `tools/ruby-gems/udb/lib/udb/condition.rb`: Configuration conditions.
- `tools/ruby-gems/udb/lib/udb/z3.rb`: SMT constraint integration.
- `tools/ruby-gems/idlc/lib/idlc.rb`: IDL compiler facade.
- `tools/ruby-gems/idlc/lib/idlc/passes/`: Semantic analysis and rendering passes.

**Testing:**
- `tools/test/regress-tests.yaml`: Canonical regression catalog.
- `tools/test/regress-cli.rb`: Local job/matrix runner.
- `tools/ruby-gems/udb/test/`: Core database unit tests and mock specs/configs.
- `tools/ruby-gems/idlc/test/`: IDL compiler tests and fixtures.
- `tools/ruby-gems/udb-gen/test/`: Generator unit/integration tests.
- `backends/cpp_hart_gen/cpp/test/`: C++ simulator tests.
- `tests/`: Repository-wide golden and ISA inputs.

**Templates and Generated Outputs:**
- `tools/ruby-gems/udb-gen/templates/`: Templates shipped with generator commands.
- `backends/*/templates/`: Backend-local templates.
- `spec/std/isa/**/*.layout`: Sources for generated architecture YAML families.
- `gen/spec/`: Merged standard/custom snapshots.
- `gen/resolved_spec/`: Inheritance-resolved, schema-versioned snapshots.
- `gen/<backend>/`: Backend-specific artifacts and build trees.

## Naming Conventions

**Files:**
- Standard extensions use their architectural case in `spec/std/isa/ext/<Name>.yaml`, for example `spec/std/isa/ext/M.yaml`.
- Instructions use lowercase mnemonics, including dots where architectural names require them, under `spec/std/isa/inst/<Extension>/<mnemonic>.yaml`, for example `spec/std/isa/inst/M/mul.yaml`.
- CSRs use lowercase architectural names under either `spec/std/isa/csr/<name>.yaml` or `spec/std/isa/csr/<Extension>/<name>.yaml`, for example `spec/std/isa/csr/misa.yaml`.
- Profiles/releases/families retain published uppercase names in `spec/std/isa/profile/`, `spec/std/isa/profile_release/`, and `spec/std/isa/profile_family/`, for example `spec/std/isa/profile/RVA23U64.yaml`.
- Parameters use uppercase architectural identifiers under `spec/std/isa/param/`, for example `spec/std/isa/param/MXLEN.yaml`.
- Schemas use snake_case with `_schema.json` in `spec/schemas/`, for example `spec/schemas/profile_schema.json`.
- Ruby implementation files use snake_case in conventional gem paths such as `tools/ruby-gems/udb/lib/udb/portfolio_design.rb`; Ruby classes/modules use CamelCase inside those files.
- Backend task registration is always `tasks.rake`, as in `backends/cpp_hart_gen/tasks.rake`; split task fragments use intent names such as `backends/cfg_html_doc/adoc_gen.rake`.
- Templates append the target syntax before `.erb`, such as `backends/cpp_hart_gen/templates/hart.hxx.erb` and `tools/ruby-gems/udb-gen/templates/manual/instruction.adoc.erb`.
- Unit tests use `test_*.rb` in each gem's `test/` directory; repository regression names use the `regress-` prefix in `tools/test/regress-tests.yaml`.
- Parameterized architecture sources capitalize placeholders in `.layout` names, such as `spec/std/isa/inst/Zaamo/amoadd.SIZE.AQRL.layout`.

**Directories:**
- Backend and Ruby module directories use snake_case, for example `backends/cpp_hart_gen/` and `tools/ruby-gems/udb_helpers/`.
- Standard instruction/CSR subdirectories use defining extension names with architectural capitalization, for example `spec/std/isa/inst/Zicsr/` and `spec/std/isa/csr/Smcsrind/`.
- Custom overlays use the `arch_overlay` value as the subtree name under `spec/custom/isa/`, for example `spec/custom/isa/qc_iu/`.
- Generator command implementations use `tools/ruby-gems/udb-gen/lib/udb-gen/generators/<command>/generator.rb`.
- Derived output directories mirror the generator/backend purpose under `gen/`, for example `gen/manual/`, `gen/cpp_hart_gen/`, and `gen/cfg_html_doc/`.

## Where to Add New Code

**New Standard Architecture Object:**
- Extension: `spec/std/isa/ext/<Name>.yaml`
- Instruction: `spec/std/isa/inst/<DefiningExtension>/<mnemonic>.yaml`
- CSR: `spec/std/isa/csr/[<DefiningExtension>/]<csr-name>.yaml`
- Parameter/profile/manual or other kind: the matching object directory declared by `Architecture::OBJS` in `tools/ruby-gems/udb/lib/udb/architecture.rb`
- Validation updates: the matching schema in `spec/schemas/`
- Tests: schema/domain coverage in `tools/ruby-gems/udb/test/` and regression registration in `tools/test/regress-tests.yaml`

**New Custom Architecture Behavior:**
- Overlay records: `spec/custom/isa/<overlay>/`, mirroring the relative path under `spec/std/isa/`
- Custom global IDL: `spec/custom/isa/<overlay>/isa/globals.isa`
- Selecting config: `cfgs/<config>.yaml` with `arch_overlay: <overlay>`
- Tests: a config-specific case in `tools/test/regress-tests.yaml` and mock/unit data in `tools/ruby-gems/udb/test/` when isolated coverage is appropriate

**New Domain Object or Query:**
- Shared base behavior: `tools/ruby-gems/udb/lib/udb/obj/database_obj.rb`
- Kind-specific behavior: `tools/ruby-gems/udb/lib/udb/obj/<kind>.rb`
- Top-level registration: `Architecture::OBJS` in `tools/ruby-gems/udb/lib/udb/architecture.rb`
- Config-aware aggregation/filtering: `tools/ruby-gems/udb/lib/udb/cfg_arch.rb`
- Tests: `tools/ruby-gems/udb/test/test_<area>.rb`

**New IDL Syntax or Analysis:**
- Grammar: `tools/ruby-gems/idlc/lib/idlc/idl.treetop`
- AST/type/symbol behavior: `tools/ruby-gems/idlc/lib/idlc/ast.rb`, `tools/ruby-gems/idlc/lib/idlc/type.rb`, or `tools/ruby-gems/idlc/lib/idlc/symbol_table.rb`
- New analysis/rendering pass: `tools/ruby-gems/idlc/lib/idlc/passes/<pass>.rb`
- Tests and IDL fixtures: `tools/ruby-gems/idlc/test/`

**New User-Facing Generator:**
- Command implementation: `tools/ruby-gems/udb-gen/lib/udb-gen/generators/<name>/generator.rb`
- Command templates/assets: `tools/ruby-gems/udb-gen/templates/<name>/` or `tools/ruby-gems/udb-gen/assets/`
- Facade exposure: add the subcommand routing/help entry to `bin/generate` when it belongs in the language-neutral facade
- Tests: `tools/ruby-gems/udb-gen/test/unit/` and `tools/ruby-gems/udb-gen/test/integration/`

**New Repository Backend:**
- Task registration: `backends/<name>/tasks.rake`
- Implementation/helpers: `backends/<name>/lib/` or language-appropriate files inside `backends/<name>/`
- Templates: `backends/<name>/templates/`
- Output: `gen/<name>/`
- Regression coverage: `tools/test/regress-tests.yaml`

**New Utility or Service:**
- Shared Ruby helper: `tools/ruby-gems/udb_helpers/lib/udb_helpers/`
- Repository maintenance utility: `tools/scripts/`
- Python data consumer: `tools/python/`
- Generated-data MCP query: `tools/mcp_gen_server/server.py`
- IDE grammar/editor support: `tools/vscode/` or `tools/eclipse/`

**New Documentation:**
- Docusaurus content: `doc/docs/<topic>/`
- Docusaurus UI/component: `doc/src/components/`, `doc/src/pages/`, or `doc/src/theme/`
- Generator-specific prose/template: keep it with its owner in `tools/ruby-gems/udb-gen/templates/` or `backends/<name>/templates/`
- Repository agent procedure: `.agents/skills/<skill-name>/SKILL.md`

## Special Directories

**`gen/`:**
- Purpose: Holds merged/resolved specs, generated artifacts, build trees, and published inputs.
- Generated: Yes, by `tools/ruby-gems/udb/lib/udb/resolver.rb`, `tools/ruby-gems/udb-gen/`, and `backends/`.
- Committed: No; ignored by `.gitignore`.

**`ext/`:**
- Purpose: Holds pinned upstream repositories used by manuals, documentation, validation, and simulator tests.
- Generated: No; populated through Git submodule initialization declared in `.gitmodules`.
- Committed: Gitlink revisions are committed; submodule working-tree contents are not part of the main repository tree.

**`spec/std/isa/**/*.layout` and expanded YAML peers:**
- Purpose: Define families of repetitive CSR/instruction YAML records through ERB-like layout sources.
- Generated: `.layout` files are source; matching expanded `.yaml` files are generated by `./do gen:arch` in `Rakefile`.
- Committed: Both layout sources and expanded YAML are committed; edit the `.layout` source for managed families.

**`.stamps/`:**
- Purpose: Cache Rake completion/dependency state for expensive generation stages.
- Generated: Yes, by `Rakefile` and backend tasks such as `backends/cfg_html_doc/adoc_gen.rake`.
- Committed: No; ignored by `.gitignore`.

**`.venv/` and `node_modules/`:**
- Purpose: Hold local Python and Node dependencies installed by `bin/setup`.
- Generated: Yes, from `pyproject.toml`/`uv.lock` and `package.json`/`package-lock.json`.
- Committed: No; ignored by `.gitignore`.

**`sorbet/rbi/`:**
- Purpose: Provide type interfaces for dependencies and metaprogrammed UDB APIs.
- Generated: Mixed; gem/DSL RBI content is managed through Tapioca tasks in `tools/ruby-gems/tasks.rake`, while annotations are repository-maintained.
- Committed: Yes.

**`tests/golden/`:**
- Purpose: Store expected generated output for regression comparisons.
- Generated: Updated only through explicit maintenance tasks such as `chore:update_golden_appendix` in `Rakefile`.
- Committed: Yes.

**`.agents/skills/`:**
- Purpose: Store project-specific instructions for agent-executed repository workflows.
- Generated: No.
- Committed: Yes, including `.agents/skills/extract-instructions-from-subsection/SKILL.md`.

---

*Structure analysis: 2026-07-30*
