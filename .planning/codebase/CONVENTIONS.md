# Coding Conventions

**Analysis Date:** 2026-07-30

## Naming Patterns

**Files:**
- Use `snake_case.rb` for Ruby implementation and test files, with tests named `test_<subject>.rb`; examples are `tools/ruby-gems/udb/lib/udb/yaml/yaml_resolver.rb` and `tools/ruby-gems/udb/test/test_yaml_resolver.rb`.
- Keep each Ruby gem's public loader at `lib/<gem-name>.rb` and place implementation below a matching namespace directory; examples are `tools/ruby-gems/udb/lib/udb.rb`, `tools/ruby-gems/idlc/lib/idlc.rb`, and `tools/ruby-gems/udb-gen/lib/udb-gen.rb`.
- Use `snake_case.py` for Python modules and `test_<subject>.py` for pytest modules; examples are `tools/python/auto-inst/parsing.py` and `tools/python/auto-inst/test_parsing.py`.
- Use `.hpp` for C++ public headers, `.cpp` for implementations/tests, and `test_<subject>.cpp` for Catch2 tests; examples are `backends/cpp_hart_gen/cpp/include/udb/bits.hpp`, `backends/cpp_hart_gen/cpp/src/hart.cpp`, and `backends/cpp_hart_gen/cpp/test/test_regfile.cpp`.
- Use `index.tsx` inside PascalCase React component directories and lowercase page entry files; examples are `doc/src/components/HomepageFeatures/index.tsx` and `doc/src/pages/index.tsx`.
- Use `*.test.ts` for VS Code/Mocha tests; the active suite is `tools/eclipse/udb-vscode/src/test/suite/basic.test.ts`.
- Name specification YAML by the database object's canonical name and nest instructions by extension; examples are `spec/std/isa/inst/I/add.yaml`, `spec/std/isa/inst/Zaamo/amoadd.w.yaml`, and `spec/std/isa/csr/mstatus.yaml`.
- Use descriptive placeholder tokens in `.layout` template names when one template emits a family, as in `spec/std/isa/inst/Zaamo/amoadd.SIZE.AQRL.layout` and `spec/std/isa/csr/I/pmpaddrN.layout`.
- Name repository-local agent skills with a kebab-case directory and a `SKILL.md` entrypoint; the active example is `.agents/skills/extract-instructions-from-subsection/SKILL.md`.

**Functions:**
- Use `snake_case` for Ruby and Python methods/functions; examples include `Udb::Resolver#cfg_arch_for` in `tools/ruby-gems/udb/lib/udb/resolver.rb` and `_levenshtein_distance` in `tools/mcp_gen_server/server.py`.
- Use a trailing `?` for Ruby predicates and a trailing `=` for writers; examples include `Instruction#has_type?` in `tools/ruby-gems/udb/lib/udb/obj/instruction.rb` and `Udb.log_level=` in `tools/ruby-gems/udb/lib/udb/log.rb`.
- Use `test_<behavior>` for Minitest methods and readable behavior phrases for Catch2/Mocha cases; examples are `test_cfg_c_header_matches_golden` in `tools/ruby-gems/udb-gen/test/test_cfg_headers.rb`, `TEST_CASE("freg round-trips a written value", "[regfile]")` in `backends/cpp_hart_gen/cpp/test/test_regfile.cpp`, and `test('completion after a keyword ...')` in `tools/eclipse/udb-vscode/src/test/suite/basic.test.ts`.
- Use lower snake case for C++ free functions and methods in the ISS code, while generated architecture types retain their generated names; examples are `parse_rounding_mode` in `backends/cpp_hart_gen/cpp/test/test_softfloat_fp.cpp` and `Rv64_Hart` included by that file.

**Variables:**
- Use `snake_case` for Ruby/Python locals and instance variables; examples are `@arch_dir` in `tools/ruby-gems/udb/lib/udb/architecture.rb` and `yaml_instructions` in `tools/python/auto-inst/test_parsing.py`.
- Prefix intentionally unused Ruby bindings with `_`, as in `_out` and `_err` in `tools/ruby-gems/udb/test/test_cli.rb`.
- Prefix private Python helpers with `_`, as in `_ensure_in_gen` and `_try_load_yaml` in `tools/mcp_gen_server/server.py`.
- Use lower camel case for TypeScript locals/functions and PascalCase for imported or declared types; examples are `extensionDevelopmentPath` in `tools/eclipse/udb-vscode/src/test/runTests.ts` and `Config` in `doc/docusaurus.config.ts`.
- Use uppercase snake case for constants in Ruby/Python and CamelCase constants where the C++ type API makes the value type-like; examples are `UDB_ROOT` in `tools/ruby-gems/udb/test/test_helper.rb`, `GEN_DIR` in `tools/mcp_gen_server/server.py`, and `InfinitePrecision` in `backends/cpp_hart_gen/cpp/test/test_bits_directed.cpp`.

**Types:**
- Use PascalCase Ruby classes/modules under the owning namespace: `Udb::Architecture` in `tools/ruby-gems/udb/lib/udb/architecture.rb`, `Idl::Compiler` in `tools/ruby-gems/idlc/lib/idlc.rb`, and `UdbGen::Subcommand` in `tools/ruby-gems/udb-gen/lib/udb-gen/subcommand.rb`.
- Use `T::Struct` and `T::Enum` for closed, typed Ruby value models; examples are `Instruction::MemoizedState` in `tools/ruby-gems/udb/lib/udb/obj/instruction.rb` and `Udb::LogLevel` in `tools/ruby-gems/udb/lib/udb/log.rb`.
- Use PascalCase for Python classes and typed container annotations in modules that expose structured APIs; examples are `TestInstructionEncoding` in `tools/python/auto-inst/test_parsing.py` and `list[str]`/`dict | None` annotations in `tools/mcp_gen_server/server.py`.
- Keep IDL type names in their language-defined casing (`Bits<N>`, `XReg`, `Boolean`, enum names); examples are embedded under `operation():` and `type():` in `spec/std/isa/inst/I/add.yaml` and `spec/std/isa/csr/mstatus.yaml`.

## Code Style

**Formatting:**
- Format Ruby according to RuboCop's GitHub base rules and repository overrides in `.rubocop.yml`; use double-quoted string literals, and target the syntax accepted by Ruby 3.2.3 for linting.
- Start Ruby source with the applicable SPDX copyright/license lines, a `# typed: ...` sigil when the file is in Sorbet's scope, and `# frozen_string_literal: true`; representative ordering appears in `tools/ruby-gems/udb/lib/udb/architecture.rb` and `tools/ruby-gems/idlc/lib/idlc.rb`.
- Use two-space indentation for Ruby, YAML, and shell. Ruby examples appear in `tools/ruby-gems/udb/lib/udb/config.rb`; shell formatting is enforced with `shfmt --indent 2 --case-indent` in `.pre-commit-config.yaml`.
- Format Python with Ruff at a 100-character line length; the settings and selected lint rules are in `pyproject.toml`, and both `ruff-format` and `ruff-check --fix` are pre-commit hooks in `.pre-commit-config.yaml`.
- Format JSON, TOML, YAML, and YML with Prettier's defaults because `.prettierrc` is `{}`; the file filters and exclusions are in `.pre-commit-config.yaml` and `.prettierignore`.
- Format C/C++ using the Google base style, two-space indentation, a 100-column limit, namespace indentation, and fixed namespace comments from `.clang-format`.
- Treat C++ formatting as a manual responsibility for `backends/cpp_hart_gen/`: the clang-format pre-commit hook excludes that subtree in `.pre-commit-config.yaml`, even though `.clang-format` defines the intended style.
- Follow the local TypeScript style in each subtree: Docusaurus source uses single quotes and compact object literals in `doc/docusaurus.config.ts`, while the VS Code extension uses semicolons and single quotes in `tools/eclipse/udb-vscode/src/test/runTests.ts`.
- Use LF line endings, one final newline, and no trailing whitespace; the built-in fixer hooks and their generated/golden exclusions are defined in `.pre-commit-config.yaml`.
- Add REUSE-compatible SPDX metadata to new files; `reuse-lint-file` enforces this in `.pre-commit-config.yaml`, with examples in `tools/test/gen_regress.py`, `spec/std/isa/inst/I/add.yaml`, and `backends/cpp_hart_gen/cpp/test/test_regfile.cpp`.

**Linting:**
- Run repository hooks through `./bin/pre-commit`; `.pre-commit-config.yaml` covers whitespace, syntax checks, Prettier, Ruff, shfmt, shellcheck, JSON Schema validation, REUSE, Renovate configuration, and regression-workflow regeneration.
- Run Ruby linting with `./bin/bundle exec rubocop`; `.rubocop.yml` loads `rubocop-minitest`, `rubocop-performance`, and `rubocop-sorbet` plus `rubocop-github` defaults.
- Do not rely on RuboCop for size limits: block length, class length counting exceptions, method length, ABC size, cyclomatic complexity, perceived complexity, and block nesting are relaxed in `.rubocop.yml`; keep new functions cohesive by matching focused neighbors such as `UdbGen::SubcommandWithCommonOptions#resolve_cfg_arg` in `tools/ruby-gems/udb-gen/lib/udb-gen/common_opts.rb`.
- Prefer keyword arguments for multi-parameter Ruby APIs; `Metrics/ParameterLists` ignores keyword arguments in `.rubocop.yml`, and `Udb::Resolver.new(..., gen_path_override:)` is used in `tools/ruby-gems/udb/test/test_cfg.rb`.
- Run Sorbet with `./do test:sorbet`; its checked directories and exclusions are in `sorbet/config`, and production APIs use `extend T::Sig` plus `sig` blocks in `tools/ruby-gems/udb/lib/udb/architecture.rb`.
- Run shellcheck at error severity and use Bash semantics; `.shellcheckrc` declares `shell=bash`, while `.pre-commit-config.yaml` invokes `shellcheck --severity=error`.
- Validate data changes against their schemas through the pre-commit JSON Schema hooks in `.pre-commit-config.yaml` and the full repository task `./do test:schema` registered from `Rakefile`.

## Import Organization

**Order:**
1. Put language/runtime standard-library imports first; examples are `json`, `os`, and `Path` in `tools/mcp_gen_server/server.py`, and `pathname`, `json`, and `yaml` in `tools/ruby-gems/udb/lib/udb/architecture.rb`.
2. Put third-party imports next; examples are `pytest` in `tools/python/auto-inst/test_parsing.py`, `sorbet-runtime` in `tools/ruby-gems/idlc/lib/idlc.rb`, and Catch2/fmt headers in `backends/cpp_hart_gen/cpp/test/test_bits_directed.cpp`.
3. Put repository-local or relative imports last; examples are `from parsing import ...` in `tools/python/auto-inst/test_parsing.py`, `require_relative "obj/csr"` in `tools/ruby-gems/udb/lib/udb/architecture.rb`, and `<udb/bits.hpp>` in `backends/cpp_hart_gen/cpp/test/test_bits_directed.cpp`.
4. Separate import groups with a blank line when the file has more than one group; examples are `tools/mcp_gen_server/server.py` and `tools/ruby-gems/udb/lib/udb/architecture.rb`.
5. In TypeScript, place external/type imports before local style modules; examples are `doc/docusaurus.config.ts` and `doc/src/pages/index.tsx`.

**Path Aliases:**
- Ruby code uses gem load paths for cross-gem imports (`require "udb/..."`, `require "idlc/..."`) and `require_relative` within a gem; examples are `tools/ruby-gems/udb/lib/udb/cfg_arch.rb` and `tools/ruby-gems/idlc/lib/idlc.rb`.
- Python code uses direct sibling imports in script-oriented directories rather than a configured alias; `tools/python/auto-inst/test_parsing.py` imports `parsing` from `tools/python/auto-inst/parsing.py`.
- TypeScript has no repository-defined path alias in `tools/eclipse/udb-vscode/tsconfig.json` or `doc/tsconfig.json`; use package imports and relative imports as demonstrated in `tools/eclipse/udb-vscode/src/test/suite/basic.test.ts`.
- C++ includes public project headers through the `udb/` include prefix configured by `backends/cpp_hart_gen/CMakeLists.txt`; examples are `<udb/bits.hpp>` and `<udb/csr.hpp>` in `backends/cpp_hart_gen/cpp/test/test_softfloat_fp.cpp`.

## Error Handling

**Patterns:**
- Validate public Ruby arguments at the boundary and raise `ArgumentError` with the received value/type; examples are `Udb::Architecture#ref` in `tools/ruby-gems/udb/lib/udb/architecture.rb` and template validation in `tools/ruby-gems/udb_helpers/lib/udb_helpers/backend_helpers.rb`.
- Use a domain-specific exception when callers need to distinguish a failure category; examples are `Udb::ConfigNotFoundError` in `tools/ruby-gems/udb/lib/udb/resolver.rb`, `Udb::PrmGenerator::GenerationError` in `tools/ruby-gems/udb/lib/udb/prm_generator.rb`, and `Idl::AstNode::TypeError` in `tools/ruby-gems/idlc/lib/idlc/ast.rb`.
- Preserve context when translating parser/compiler failures: include the source file, line, reason, or offending value in messages as done by `Idl::Compiler` in `tools/ruby-gems/idlc/lib/idlc.rb`.
- Rescue only expected exceptions in reusable code, then re-raise or translate them with context; examples are the typed IDL error branches in `tools/ruby-gems/idlc/lib/idlc.rb` and YAML parse handling in `backends/generators/generator.py`.
- Use `ensure`/`teardown` for resources that must be released; examples are tempfile deletion in `tools/ruby-gems/udb-gen/test/unit/test_inst_table.rb` and temporary directory cleanup in `tools/ruby-gems/udb/test/test_cfg.rb`.
- In Python, raise built-in typed exceptions such as `ValueError`, `FileNotFoundError`, and `RuntimeError`, including the bad path/value in the message; examples are `_ensure_in_gen` in `tools/mcp_gen_server/server.py` and schema-release checks in `tools/scripts/download_schema_releases.py`.
- In CLI/task code, log a concise actionable message and return a nonzero status; examples are `tools/test/regress-cli.rb`, `backends/generators/Go/go_generator.py`, and golden-diff failures in `backends/instructions_appendix/tasks.rake`.
- In C++, use `std::runtime_error`, `std::out_of_range`, or project exception types for invalid runtime state and assert the exact type in tests; examples are `parse_hex_u64` and `REQUIRE_THROWS_AS` in `backends/cpp_hart_gen/cpp/test/test_softfloat_fp.cpp` and `backends/cpp_hart_gen/cpp/test/test_regfile.cpp`.

## Logging

**Framework:** `TTY::Logger`/Ruby `Logger` for Ruby, standard `logging` for Python, and direct console output at CLI/test boundaries.

**Patterns:**
- Use `Udb.logger` rather than ad hoc `puts` in UDB library and backend code; log-level selection and injection are centralized in `tools/ruby-gems/udb/lib/udb/log.rb`.
- Use `Idl.logger` for IDL compiler diagnostics that are not raised errors; the injectable logger is defined in `tools/ruby-gems/idlc/lib/idlc/log.rb`.
- Use `TTY::Logger` and `TTY::Command` for interactive command status and subprocess output; the regression runner's live-streaming printer is in `tools/test/regress-cli.rb`.
- Define a module logger with `logging.getLogger(__name__)` in Python modules and configure the process at the CLI boundary; examples are `backends/generators/generator.py` and `backends/generators/c_header/generate_encoding.py`.
- Reserve `puts`, `warn`, `print`, and `console.*` for command output, progress, generated diagnostics, or tests; examples are `Rakefile`, `tools/ruby-gems/idlc/lib/idlc.rb`, and `tools/eclipse/udb-vscode/src/test/runTests.ts`.
- Never log secret values; environment-driven logging in `tools/ruby-gems/udb/lib/udb/log.rb` reads only the `LOG` level selector.

## Comments

**When to Comment:**
- Explain non-obvious invariants, generated-code constraints, concurrency, or protocol decisions; examples are the parse-cache thread-safety comment in `tools/ruby-gems/idlc/lib/idlc.rb` and regression printer contract in `tools/test/regress-cli.rb`.
- Keep schema/data comments adjacent to the affected field or IDL block; examples are `spec/std/isa/csr/mstatus.yaml` and `spec/std/isa/inst/Zaamo/amoadd.w.yaml`.
- Mark generated outputs prominently and edit their source templates; `spec/std/isa/inst/Zaamo/amoadd.w.yaml` points to `spec/std/isa/inst/Zaamo/amoadd.SIZE.AQRL.layout`, and `spec/std/isa/csr/I/pmpaddr0.yaml` points to `spec/std/isa/csr/I/pmpaddrN.layout`.
- Use `TODO` only for a concrete follow-up at the relevant location; examples are CSR/field support notes in `tools/ruby-gems/udb_helpers/lib/udb_helpers/backend_helpers.rb` and the broken-link policy note in `doc/docusaurus.config.ts`.
- Keep procedural agent instructions explicit and ordered in `SKILL.md`; `.agents/skills/extract-instructions-from-subsection/SKILL.md` demonstrates arguments, steps, exclusions, output format, and an example.

**JSDoc/TSDoc:**
- Ruby public APIs primarily use YARD tags (`@param`, `@return`, `@raise`, `@example`) immediately above the method; examples are `tools/ruby-gems/udb/lib/udb/architecture.rb`, `tools/ruby-gems/udb_helpers/lib/udb_helpers/backend_helpers.rb`, and `tools/ruby-gems/idlc/lib/idlc.rb`.
- Python functions use concise docstrings for purpose and structured `Args`/`Returns` sections where behavior is nontrivial; examples are `_fuzzy_match` in `tools/mcp_gen_server/server.py` and helpers in `tools/python/auto-inst/test_parsing.py`.
- TypeScript uses short comments for test orchestration rather than repository-wide TSDoc; examples are `tools/eclipse/udb-vscode/src/test/suite/basic.test.ts` and `tools/eclipse/udb-vscode/src/test/runTests.ts`.

## Function Design

**Size:** No hard Ruby method-size or complexity threshold is enabled in `.rubocop.yml`; keep new methods centered on one operation and extract named helpers following `resolve_cfg_arg` in `tools/ruby-gems/udb-gen/lib/udb-gen/common_opts.rb` and `_load_yaml` in `tools/mcp_gen_server/server.py`.

**Parameters:** Prefer keyword arguments for Ruby APIs with multiple optional inputs and annotate them in one multiline `sig`; examples are `Udb::Resolver#initialize` in `tools/ruby-gems/udb/lib/udb/resolver.rb` and test construction in `tools/ruby-gems/udb/test/test_cfg.rb`.

**Return Values:** Make return contracts explicit with Sorbet in production Ruby (`sig { returns(...) }`) as in `tools/ruby-gems/udb/lib/udb/architecture.rb`; use Python annotations in typed service code as in `tools/mcp_gen_server/server.py`; return domain objects rather than loosely structured output where an abstraction exists.

**Guard Clauses:**
- Use early returns/raises for invalid or already-computed states; examples are memoized accessors in `tools/ruby-gems/udb/lib/udb/architecture.rb` and path validation in `tools/mcp_gen_server/server.py`.
- Keep fallback values explicit when absence is valid; examples are `YAML_SAFE.load(fh) or {}` in `tools/mcp_gen_server/server.py` and `@objects = Concurrent::Hash.new` initialization in `tools/ruby-gems/udb/lib/udb/architecture.rb`.

**Mutation:**
- Freeze Ruby constants and memoized collections that represent completed read models; examples are `Architecture::OBJS` and cached extension lists in `tools/ruby-gems/udb/lib/udb/architecture.rb`.
- Confine mutable global/module state to documented service-level caches or command configuration; examples are the mutex-protected parse cache in `tools/ruby-gems/idlc/lib/idlc.rb` and logger state in `tools/ruby-gems/udb/lib/udb/log.rb`.

## Module Design

**Exports:** Keep implementation under the owning namespace (`Udb`, `Idl`, `UdbGen`) and expose it through the gem entrypoint; examples are `tools/ruby-gems/udb/lib/udb.rb`, `tools/ruby-gems/idlc/lib/idlc.rb`, and `tools/ruby-gems/udb-gen/lib/udb-gen.rb`.

**Barrel Files:** Ruby entrypoint files serve as explicit barrels and list their `require_relative` dependencies; do not add wildcard loading when extending `tools/ruby-gems/udb/lib/udb.rb` or `tools/ruby-gems/idlc/lib/idlc.rb`.

**Boundaries:**
- Put database models under `tools/ruby-gems/udb/lib/udb/obj/`, compiler passes under `tools/ruby-gems/idlc/lib/idlc/passes/`, generator implementations under `tools/ruby-gems/udb-gen/lib/udb-gen/generators/`, and shared presentation helpers under `tools/ruby-gems/udb_helpers/lib/udb_helpers/`.
- Register artifact backends through a local `tasks.rake`; the root `Rakefile` loads `backends/*/tasks.rake`, with examples in `backends/cfg_html_doc/tasks.rake` and `backends/cpp_hart_gen/tasks.rake`.
- Keep generated artifacts out of source modules and write them under `gen/`; generation tasks in `Rakefile` and `backends/cpp_hart_gen/tasks.rake` use that boundary.
- Put reusable agent workflows in `.agents/skills/<name>/SKILL.md` with YAML frontmatter (`name`, `description`, optional `argument-hint`, `allowed-tools`); use `.agents/skills/extract-instructions-from-subsection/SKILL.md` as the repository pattern.

## Data and Schema Conventions

**Specification YAML:**
- Begin object files with a YAML language-server schema comment, then `$schema`, `kind`, and `name`; `spec/std/isa/inst/I/add.yaml` and `spec/std/isa/csr/mstatus.yaml` are canonical examples.
- Express provenance/availability through `definedBy` and structured `extension`, `xlen`, `param`, `allOf`, or `anyOf` conditions; examples are `spec/std/isa/inst/I/add.yaml` and `spec/std/isa/csr/mstatus.yaml`.
- Use literal YAML blocks for prose and multi-line IDL, and use function-shaped keys such as `operation():`, `type():`, and `reset_value():`; examples are `spec/std/isa/inst/Zaamo/amoadd.w.yaml` and `spec/std/isa/csr/mstatus.yaml`.
- Use `$ref` for references between database objects rather than duplicating the target data; hint references in `spec/std/isa/inst/I/add.yaml` show the pattern.
- Edit a `.layout` template, then run `./do gen:arch`, when the target YAML carries an auto-generated warning; examples pair `spec/std/isa/inst/Zaamo/amoadd.SIZE.AQRL.layout` with `spec/std/isa/inst/Zaamo/amoadd.w.yaml`.

**Regression YAML:**
- Define locally runnable tests under `tests:` in `tools/test/regress-tests.yaml`, with required `ci_stage` and `test` fields validated by `tools/test/tests-schema.json`.
- Use `tags` for `smoke`, `unit`, or `integration` selection and a `strategy.matrix` for variants; examples are `regress-idlc-unit` and `regress-udb-unit-test` in `tools/test/regress-tests.yaml`.
- Keep GitHub-only setup/upload steps in `gh_pre` and `gh_post`; examples are submodule checkout and Codecov upload in `tools/test/regress-tests.yaml`.
- Regenerate `.github/workflows/regress.yml` through `./bin/chore gen regress` after changing `tools/test/regress-tests.yaml` or `tools/test/regress-gh-template.yaml`; enforcement is configured in `.pre-commit-config.yaml`.

---

*Convention analysis: 2026-07-30*
