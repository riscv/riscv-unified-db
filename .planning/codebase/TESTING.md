# Testing Patterns

**Analysis Date:** 2026-07-30

## Test Framework

**Runner:**
- Minitest 6.0.6 is the primary Ruby unit-test runner; the version is locked in `Gemfile.lock`, test bootstraps require `minitest/autorun` in files such as `tools/ruby-gems/udb/test/test_helper.rb`, and gem tasks are registered in `tools/ruby-gems/tasks.rake`.
- SimpleCov 1.0.3 records Ruby line/branch coverage, with Cobertura output for the `udb`, `idlc`, and `udb-gen` suites; configuration lives in `tools/ruby-gems/udb/test/test_helper.rb`, `tools/ruby-gems/idlc/test/run.rb`, and `tools/ruby-gems/udb-gen/test/test_helper.rb`.
- Mocha 3.1.0 supplies Minitest mocks/stubs for `udb-gen`; it is locked in `Gemfile.lock` and loaded by `tools/ruby-gems/udb-gen/test/unit/test_helper.rb` and `tools/ruby-gems/udb-gen/test/integration/test_helper.rb`.
- pytest 9.1.1 runs the Python/LLVM encoding comparison in `tools/python/auto-inst/test_parsing.py`; the version is pinned in `pyproject.toml`.
- Catch2 3.15.2 runs C++ unit tests under CTest; it is fetched and wired in `backends/cpp_hart_gen/CMakeLists.txt`.
- Mocha 11.7.6 with VS Code's Electron harness runs extension end-to-end tests; dependencies and scripts are in `tools/eclipse/udb-vscode/package.json`, with orchestration in `tools/eclipse/udb-vscode/src/test/runTests.ts`.
- JUnit Jupiter runs Xtext parser tests through Maven; the active test imports `org.junit.jupiter.api.Test` in `tools/eclipse/dev/org.xtext.udb.parent/org.xtext.udb.tests/src/org/xtext/example/udb/tests/UdbParsingTest.xtend`, and CI invokes the reactor from `.github/workflows/regress.yml`.
- `./bin/regress` is the cross-language local orchestrator; its CLI is `tools/test/regress-cli.rb`, test definitions are `tools/test/regress-tests.yaml`, and the generated CI representation is `.github/workflows/regress.yml`.

**Assertion Library:**
- Use Minitest assertions (`assert`, `refute`, `assert_equal`, `assert_raises`, `capture_io`) in Ruby, as demonstrated by `tools/ruby-gems/udb/test/test_cli.rb` and `tools/ruby-gems/udb/test/test_cfg.rb`.
- Use pytest's plain assertions, `pytest.skip`, parameterization, and `pytest.fail` in Python, as demonstrated by `tools/python/auto-inst/test_parsing.py`.
- Use Catch2 `REQUIRE`, `REQUIRE_THROWS_AS`, `static_assert`, generators, and matchers in C++, as demonstrated by `backends/cpp_hart_gen/cpp/test/test_bits_directed.cpp` and `backends/cpp_hart_gen/cpp/test/test_regfile.cpp`.
- Use Node's `assert` inside Mocha TDD suites for the VS Code extension, as demonstrated by `tools/eclipse/udb-vscode/src/test/suite/basic.test.ts`.

**Run Commands:**
```bash
./bin/regress --all                 # Run the full locally available regression suite
./bin/regress --tag smoke           # Run the fast smoke-tagged regressions
./bin/regress --tag unit            # Run regressions tagged as unit tests
./bin/regress -n regress-idlc-unit  # Run one named regression
./do test:idlc:unit                 # Run all IDL compiler Minitest files in its aggregator
./do test:udb:unit                  # Run the UDB gem aggregator
./do test:udb_gen:unit              # Run udb-gen unit tests
./do test:udb_gen:integration       # Run udb-gen integration tests
./do test:cpp_hart CONFIG=rv64 JOBS=4 BUILD_TYPE=debug  # Build/run discovered C++ tests
./bin/pre-commit                    # Run formatting, lint, schema, and generated-file checks
```
These entrypoints are defined in `bin/regress`, `tools/test/regress-cli.rb`, `tools/ruby-gems/tasks.rake`, `backends/cpp_hart_gen/tasks.rake`, and `bin/pre-commit`.

**Watch Mode:**
- No repository-wide watch command is defined in `tools/test/regress-cli.rb` or `tools/ruby-gems/tasks.rake`; run a focused named regression or a single test file while iterating.
- The VS Code package offers TypeScript compilation watch mode with `npm run watch` in `tools/eclipse/udb-vscode/package.json`, but its Mocha suite still runs through `npm test`.

## Test File Organization

**Location:**
- Co-locate Ruby tests with each gem under `tools/ruby-gems/<gem>/test/`; examples include `tools/ruby-gems/udb/test/`, `tools/ruby-gems/idlc/test/`, and `tools/ruby-gems/udb_helpers/test/`.
- Split `udb-gen` tests by boundary under `tools/ruby-gems/udb-gen/test/unit/` and `tools/ruby-gems/udb-gen/test/integration/`.
- Co-locate the only pytest module with its Python implementation at `tools/python/auto-inst/test_parsing.py`.
- Put C++ tests beside the backend under `backends/cpp_hart_gen/cpp/test/` and register targets/discovery in `backends/cpp_hart_gen/CMakeLists.txt`.
- Put repository-wide golden outputs and architecture execution inputs under `tests/golden/`, `tests/data/`, and `tests/isa/`.
- Put VS Code tests under `tools/eclipse/udb-vscode/src/test/` and fixtures under `tools/eclipse/udb-vscode/test-fixtures/`.
- Put Xtext parser tests in the Maven test plugin at `tools/eclipse/dev/org.xtext.udb.parent/org.xtext.udb.tests/`.

**Naming:**
- Name Ruby files `test_<subject>.rb`, classes `Test<Subject>`, and methods `test_<behavior>`; `tools/ruby-gems/udb/test/test_cfg.rb` is the baseline pattern.
- Name Python files `test_<subject>.py`, test classes `Test<Subject>`, and test functions `test_<behavior>`; use `tools/python/auto-inst/test_parsing.py`.
- Name C++ files `test_<subject>.cpp` and give `TEST_CASE` a human-readable behavior plus a subsystem tag; use `backends/cpp_hart_gen/cpp/test/test_regfile.cpp`.
- Name TypeScript test files `*.test.ts`; `tools/eclipse/udb-vscode/src/test/suite/index.ts` discovers compiled `**/*.test.js`.

**Structure:**
```text
tools/ruby-gems/<gem>/
├── lib/...
└── test/
    ├── test_helper.rb       # shared setup/coverage
    ├── run.rb               # explicit suite aggregator
    ├── test_<subject>.rb
    ├── data/                # data-driven cases, when used
    └── fixtures/            # expected output, when used

backends/cpp_hart_gen/cpp/
├── src/
├── include/udb/
└── test/
    └── test_<subject>.cpp
```
This layout is instantiated by `tools/ruby-gems/idlc/test/`, `tools/ruby-gems/udb-gen/test/`, and `backends/cpp_hart_gen/cpp/test/`.

**Discovery Boundaries:**
- Ruby suite loading is explicit, not glob-based: add new files to the appropriate `run.rb`, such as `tools/ruby-gems/udb/test/run.rb`, `tools/ruby-gems/idlc/test/run.rb`, or `tools/ruby-gems/udb-gen/test/unit/run.rb`.
- UDB CI also selects file names through the `regress-udb-unit-test` matrix in `tools/test/regress-tests.yaml`; add a matrix entry when a new UDB test must run as its own CI job.
- C++ execution is explicit in `backends/cpp_hart_gen/CMakeLists.txt`: a source file must have an executable target and `catch_discover_tests(...)` entry (or be included in a discovered target).
- `test_decode`, `test_version`, and `test_csr` are not all in active CTest discovery: commented target/discovery lines in `backends/cpp_hart_gen/CMakeLists.txt` define the actual boundary.
- GitHub-only Xtext and VS Code jobs are authored in `tools/test/regress-gh-template.yaml` and materialized in `.github/workflows/regress.yml`; they are not locally dispatched by `tools/test/regress-cli.rb`.

## Test Structure

**Suite Organization:**
```ruby
class TestCfgHeaders < Minitest::Test
  def setup
    @gen_dir = Dir.mktmpdir
    @resolver = Udb::Resolver.new(
      Udb.repo_root,
      gen_path_override: Pathname.new(@gen_dir)
    )
  end

  def teardown
    FileUtils.rm_rf @gen_dir
  end

  def test_cfg_c_header_matches_golden
    output = generator.generate_header
    golden = File.read(GOLDEN_DIR / "expected.golden.h")
    assert_equal golden, output
  end
end
```
This setup/action/assertion/cleanup shape is taken from `tools/ruby-gems/udb-gen/test/test_cfg_headers.rb`.

**Patterns:**
- Build shared objects in `setup` and release filesystem resources in `teardown` or `ensure`; examples are `tools/ruby-gems/udb/test/test_cfg.rb` and `tools/ruby-gems/udb-gen/test/unit/test_inst_table.rb`.
- Put the behavior under test in a clearly named method and include failure context in assertions; examples are `tools/ruby-gems/udb/test/test_yaml_resolver.rb` and `tools/ruby-gems/idlc/test/test_type_checking_data_driven.rb`.
- Generate repetitive cases from real repository data or YAML tables with `define_method`/pytest parameterization; examples are config validation in `tools/ruby-gems/udb/test/test_cfg.rb`, IDL cases in `tools/ruby-gems/idlc/test/test_control_flow.rb`, and instruction encoding cases in `tools/python/auto-inst/test_parsing.py`.
- Use `skip` only when a declared external prerequisite or unsupported case is absent; examples are missing LLVM data and documented corner cases in `tools/python/auto-inst/test_parsing.py`.
- For CLI tests, capture stdout/stderr and assert the user-visible contract; use `capture_io` as in `tools/ruby-gems/udb/test/test_cli.rb`.

## Mocking

**Framework:** Mocha with Minitest for `udb-gen`; hand-written fakes/test doubles elsewhere.

**Patterns:**
```ruby
inst = mock("add_inst")
inst.stubs(:name).returns("add")
inst.stubs(:defined_in_base?).with(32).returns(true)
inst.stubs(:encoding).returns(encoding)
```
This collaborator-stubbing pattern is used in `tools/ruby-gems/udb-gen/test/unit/test_inst_table.rb` after `mocha/minitest` is loaded by `tools/ruby-gems/udb-gen/test/unit/test_helper.rb`.

**What to Mock:**
- Mock narrow generator collaborators when the test is about formatting/table construction rather than architecture resolution; use `tools/ruby-gems/udb-gen/test/unit/test_inst_table.rb` as the pattern.
- Use small Ruby structs/classes for compiler interfaces with many deterministic accessors; examples are `MockRegFile` and `MockConfiguredArchitecture` in `tools/ruby-gems/idlc/test/helpers.rb`.
- Use a compile-time-compatible C++ fake for the generated hart's environment; `NullSocModel` in `backends/cpp_hart_gen/cpp/test/test_softfloat_fp.cpp` implements the required interface without external devices.

**What NOT to Mock:**
- Exercise the real resolver, schema data, and temporary filesystem in integration tests; examples are `tools/ruby-gems/udb-gen/test/integration/test_inst_table.rb` and `tools/ruby-gems/udb/test/test_yaml_resolver.rb`.
- Exercise the real language server through VS Code Electron for diagnostics/completion/hover; use `tools/eclipse/udb-vscode/src/test/suite/basic.test.ts`.
- Exercise generated ISS binaries against actual RISC-V test programs for execution regressions; orchestration is in `backends/cpp_hart_gen/tasks.rake` and inputs are in `tests/isa/`.
- Prefer deterministic checked-in vectors over mocking numerical reference behavior; `backends/cpp_hart_gen/cpp/test/test_softfloat_fp.cpp` reads `tests/data/fp/directed/f32_fpgen_expanded.jsonl`.

## Fixtures and Factories

**Test Data:**
```yaml
# tools/ruby-gems/idlc/test/data/control_flow_tests.yaml
<category>:
  - name: <case-name>
    idl: |
      <IDL source>
    should_pass: true
    description: <expected behavior>
    context: body
```
The loader and dynamic test generation for this format are in `tools/ruby-gems/idlc/test/test_control_flow.rb`.

**Location:**
- Put isolated UDB configurations and spec objects under `tools/ruby-gems/udb/test/mock_cfgs/` and `tools/ruby-gems/udb/test/mock_spec/`; resolver overrides in `tools/ruby-gems/udb/test/test_conditions.rb` consume them.
- Put IDL data-driven cases under `tools/ruby-gems/idlc/test/data/` and IDL fixture files under `tools/ruby-gems/idlc/test/idl/`.
- Put `udb-gen` expected output beside its unit/integration suite under `tools/ruby-gems/udb-gen/test/unit/fixtures/` and `tools/ruby-gems/udb-gen/test/integration/fixtures/`.
- Put cross-backend golden files under `tests/golden/`; examples are `tests/golden/all_instructions.golden.adoc` and `tests/golden/mc100-32-full-example.golden.h`.
- Update generator fixtures only through the owning chore path; `tools/ruby-gems/tasks.rake` defines `chore:udb_gen:update_fixtures`, while `backends/instructions_appendix/tasks.rake` prints the exact golden update procedure for the appendix.

## Coverage

**Requirements:** No minimum percentage or maximum-drop threshold is configured in the SimpleCov setup files `tools/ruby-gems/udb/test/test_helper.rb`, `tools/ruby-gems/idlc/test/run.rb`, or `tools/ruby-gems/udb-gen/test/test_helper.rb`.

**Collection:**
- UDB and `udb-gen` collect branch plus eval coverage and write HTML/Cobertura reports; see `tools/ruby-gems/udb/test/test_helper.rb` and `tools/ruby-gems/udb-gen/test/test_helper.rb`.
- IDLC and `udb_helpers` collect branch coverage; see `tools/ruby-gems/idlc/test/run.rb` and `tools/ruby-gems/udb_helpers/test/run.rb`.
- UDB matrix jobs save `.resultset.json` artifacts and collate them before Codecov upload; see `tools/test/regress-tests.yaml`, `tools/ruby-gems/tasks.rake`, and `.github/workflows/regress.yml`.
- C++ bit-test executables compile/link with GCC coverage flags and run via `ctest -T coverage -T test`; see `backends/cpp_hart_gen/CMakeLists.txt` and `backends/cpp_hart_gen/tasks.rake`.

**View Coverage:**
```bash
./do test:udb:unit    # Produces tools/ruby-gems/udb/coverage/index.html
./do test:idlc:unit   # Produces tools/ruby-gems/idlc/coverage/index.html
```
The output directories are set in `tools/ruby-gems/udb/test/test_helper.rb` and `tools/ruby-gems/idlc/test/run.rb`.

## Test Types

**Unit Tests:**
- Ruby model/compiler/helper units dominate `tools/ruby-gems/udb/test/`, `tools/ruby-gems/idlc/test/`, `tools/ruby-gems/udb_helpers/test/`, and `tools/ruby-gems/udb-gen/test/unit/`.
- C++ value types, register files, utility behavior, and generated hart floating-point helpers are tested in `backends/cpp_hart_gen/cpp/test/`.
- Parser behavior is unit-tested with JUnit/Xtext in `tools/eclipse/dev/org.xtext.udb.parent/org.xtext.udb.tests/`.

**Integration Tests:**
- Real architecture resolution plus generator output is tested in `tools/ruby-gems/udb-gen/test/integration/test_inst_table.rb`.
- Full YAML resolve/emit/source-map behavior is tested against repository data in `tools/ruby-gems/udb/test/test_yaml_resolver.rb`.
- LLVM/UDB instruction encoding comparison is parameterized across loaded instructions in `tools/python/auto-inst/test_parsing.py`.
- Golden generation checks compare artifacts in `tests/golden/` through tasks such as `backends/instructions_appendix/tasks.rake` and `tools/python/tasks.rake`.

**E2E Tests:**
- VS Code Electron launches the extension and real language server against `tools/eclipse/udb-vscode/test-fixtures/`; orchestration is `tools/eclipse/udb-vscode/src/test/runTests.ts`.
- Generated ISS binaries run upstream and repository vector programs through `backends/cpp_hart_gen/tasks.rake` and `tests/isa/`.
- Full artifact-generation, schema, type-check, packaging, and smoke paths are declared in `tools/test/regress-tests.yaml` and `tools/test/regress-gh-template.yaml`.

## Common Patterns

**Async Testing:**
```typescript
const diags = await waitFor(() => {
  const found = vscode.languages.getDiagnostics(doc.uri);
  return found.length ? found : null;
}, 8000);
assert.ok(diags && diags.length >= 1);
```
Use bounded polling around eventually consistent VS Code APIs as in `tools/eclipse/udb-vscode/src/test/suite/basic.test.ts`; the suite timeout is set in `tools/eclipse/udb-vscode/src/test/suite/index.ts`.

**Error Testing:**
```ruby
assert_raises(ArgumentError) do
  link_to_udb_doc_ext_param("foo", "ba.r", "text")
end
```
Assert the specific error class and the invalid behavior, following `tools/ruby-gems/udb_helpers/test/test_backend_helpers.rb` and typed compiler cases in `tools/ruby-gems/idlc/test/test_control_flow.rb`.

```cpp
REQUIRE_THROWS_AS(hart->set_xreg(32, 0), std::out_of_range);
```
Use the exact exception type for C++ boundary failures, following `backends/cpp_hart_gen/cpp/test/test_regfile.cpp`.

**Golden Testing:**
- Compare complete deterministic output and provide the owning regeneration command in the failure message; examples are `tools/ruby-gems/udb-gen/test/test_cfg_headers.rb` and `backends/instructions_appendix/tasks.rake`.
- Filter only known nondeterministic lines before diffing rather than weakening the whole comparison; the wavedrom-path filter in `backends/instructions_appendix/tasks.rake` is the repository pattern.

**Adding a Regression:**
- Add locally runnable definitions to `tools/test/regress-tests.yaml`, validate against `tools/test/tests-schema.json`, tag the test appropriately, and regenerate `.github/workflows/regress.yml` with `./bin/chore gen regress`.
- Put CI-only orchestration in `tools/test/regress-gh-template.yaml`; `doc/regress-test-infrastructure.adoc` documents the split between local definitions and GitHub-only jobs.
- Verify a new regression locally with `./bin/regress -n <test-name>` and include it in `smoke`, `unit`, or `integration` only when its runtime/scope matches existing definitions in `tools/test/regress-tests.yaml`.

---

*Testing analysis: 2026-07-30*
