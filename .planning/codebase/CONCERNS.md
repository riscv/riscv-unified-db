# Codebase Concerns

**Analysis Date:** 2026-07-30

## Tech Debt

**SpecChoice has no implementation boundary:**
- Issue: No package, backend, route, data model, configuration, or test mentions `SpecChoice`, `Spec Choice`, or `spec_choice`. The closest reusable query surface is a standalone MCP script that reads pre-generated data.
- Files: `tools/mcp_gen_server/server.py`, `tools/mcp_gen_server/README.md`, `tools/ruby-gems/udb/lib/udb/resolver.rb`, `doc/src/pages/index.tsx`
- Impact: A v1.3.2 prototype cannot be added by extending an established feature module. Product behavior, persistence, API contracts, and UI placement all require explicit ownership decisions.
- Fix approach: Put the prototype behind a clearly named top-level module with its own tests and dependency declaration. Reuse `Udb::Resolver`/`Udb::ConfiguredArchitecture` for authoritative architecture semantics; do not treat MCP search heuristics as the selection engine.

**Incomplete configuration reasoning:**
- Issue: Z3 parameter translation explicitly raises for JSON Schema `anyOf`, `oneOf`, `noneOf`, and `if`/`then`/`else` across integer, boolean, string, and array parameters. Extension requirement conversion also raises for multi-clause and non-contiguous version sets.
- Files: `tools/ruby-gems/udb/lib/udb/z3.rb`, `tools/ruby-gems/udb/lib/udb/obj/extension.rb`
- Impact: SpecChoice can fail at runtime for valid parameter schemas or extension-version choices that need disjunctions, conditional schemas, or complex version sets.
- Fix approach: Inventory the schema constructs used by the prototype's supported extensions, implement the missing solver translations before exposing them, and return typed unsupported-choice errors rather than raw `raise "TODO"` failures.

**Large, high-coupling compiler and logic modules:**
- Issue: Core behavior is concentrated in `ast.rb` (about 9,800 lines), `logic.rb` (about 3,600 lines), `condition.rb` (about 2,200 lines), and `cfg_arch.rb` (about 1,850 lines). The generated IDL parser adds about 14,700 lines.
- Files: `tools/ruby-gems/idlc/lib/idlc/ast.rb`, `tools/ruby-gems/idlc/lib/idlc/idl_parser.rb`, `tools/ruby-gems/udb/lib/udb/logic.rb`, `tools/ruby-gems/udb/lib/udb/condition.rb`, `tools/ruby-gems/udb/lib/udb/cfg_arch.rb`
- Impact: Small semantic changes have a broad regression surface, and unfamiliar call paths are difficult to isolate during prototype work.
- Fix approach: Keep SpecChoice orchestration outside these modules. Add narrow adapters around public resolver/configuration APIs and characterize any required core behavior with tests before modifying compiler internals.

**Legacy parallel YAML resolver:**
- Issue: Architecture resolution uses the Ruby resolver, while a separate approximately 790-line Python resolver remains in the tree without regression-test references.
- Files: `tools/ruby-gems/udb/lib/udb/resolver.rb`, `tools/ruby-gems/udb/lib/udb/yaml/yaml_resolver.rb`, `tools/ruby-gems/udb/python/yaml_resolver.py`, `tools/test/regress-tests.yaml`
- Impact: Two implementations can drift, and prototype developers may choose the untested Python path because it appears easier to integrate with a web service.
- Fix approach: Use the Ruby resolver as the source of truth. Either delete/deprecate the Python implementation or add parity tests and document its supported contract before using it.

**C++ hart backend contains deliberate failure paths:**
- Issue: Memory defaults assert “not implemented,” generator branches raise `TODO`, register access in the Renode bridge asserts, and GDB feature handling is incomplete.
- Files: `backends/cpp_hart_gen/cpp/include/udb/memory.hpp`, `backends/cpp_hart_gen/lib/gen_cpp.rb`, `backends/cpp_hart_gen/lib/template_helpers.rb`, `backends/cpp_hart_gen/cpp/src/libhart_renode.cpp`, `backends/cpp_hart_gen/cpp/src/GDBServer.cpp`
- Impact: A SpecChoice flow that promises simulator generation can accept a choice that later aborts during generation or execution.
- Fix approach: Keep simulator generation outside the v1.3.2 prototype contract unless the chosen configuration is covered by a named C++ backend regression. Convert reachable `TODO` raises to capability checks with actionable errors.

## Known Bugs

**MCP path containment accepts sibling prefixes:**
- Symptoms: `_ensure_in_gen` accepts any resolved path whose string begins with the `gen` path. A sibling such as `gen_backup/file.yaml` passes the prefix test even though it is outside `gen/`.
- Files: `tools/mcp_gen_server/server.py`
- Trigger: Call `read_gen_yaml` with an existing YAML path under a repository sibling whose name starts with `gen`.
- Workaround: Do not expose `read_gen_yaml` to untrusted callers. Replace the string comparison with `Path.is_relative_to(GEN_DIR.resolve())` and test symlinks plus prefix-collision directories.

**MCP searches mix generated configurations:**
- Symptoms: Instruction, CSR, and extension iterators walk all of `gen/`, including merged and resolved trees for multiple configurations. Instruction and CSR results are not de-duplicated or tagged with a selected architecture.
- Files: `tools/mcp_gen_server/server.py`, `tools/mcp_gen_server/README.md`, `tools/ruby-gems/udb/lib/udb/resolver.rb`
- Trigger: Generate more than one configuration, then search for an object present in multiple `gen/spec/**` or `gen/resolved_spec/**` trees.
- Workaround: Query a single explicit configuration directory or use a `ConfiguredArchitecture` object. Add a required configuration/source parameter and include it in every result identity.

**XLEN filtering is heuristic rather than architectural:**
- Symptoms: Missing XLEN evidence defaults to both 32 and 64, while arbitrary `"32"`/`"64"` substrings in names, defining extensions, or encoding text are treated as evidence.
- Files: `tools/mcp_gen_server/server.py`, `tools/ruby-gems/udb/lib/udb/obj/instruction.rb`, `tools/ruby-gems/udb/lib/udb/obj/csr.rb`
- Trigger: Search with the MCP `xlen` filter for YAML without a top-level `base` value or with numeric substrings unrelated to architectural availability.
- Workaround: Derive availability from `Instruction#rv32?`/`rv64?`, CSR base/conditions, and the selected `ConfiguredArchitecture`; do not use MCP XLEN results as validation.

**Fuzzy search truncates before ranking:**
- Symptoms: Matching stops as soon as `limit` filesystem-order entries are collected, and only that subset is sorted by fuzzy score. Better matches later in the walk are omitted.
- Files: `tools/mcp_gen_server/server.py`
- Trigger: Run a fuzzy instruction or CSR search with a result set larger than `limit`.
- Workaround: Score the complete candidate set, then select the top `limit`, or query a prebuilt index with top-k ranking.

**Architecture YAML cache can serve stale data:**
- Symptoms: Raw YAML is held in a class-level cache keyed by resolved directory and has no mtime, content hash, or explicit invalidation. Regenerating the same path in a long-lived process leaves subsequent architecture objects on old contents.
- Files: `tools/ruby-gems/udb/lib/udb/cfg_arch.rb`, `tools/ruby-gems/udb/lib/udb/resolver.rb`
- Trigger: Load an object category, regenerate that resolved architecture path, then create or query another configured architecture in the same Ruby process.
- Workaround: Restart the process after regeneration. For a server, version cache keys by generation stamp/content digest and invalidate atomically after resolution.

## Security Considerations

**Untrusted path and regex input:**
- Risk: The MCP server accepts caller-controlled file paths and regular expressions. The path-prefix bug permits reads outside `gen/`, and catastrophic regexes can monopolize the synchronous event loop.
- Files: `tools/mcp_gen_server/server.py`
- Current mitigation: YAML extensions and file existence are checked; invalid regex syntax is rejected. The server uses stdio rather than a network listener.
- Recommendations: Enforce real path containment, reject symlink escapes, cap pattern length, prefer escaped substring search, and put regex evaluation behind time/resource limits before adapting this server for a web API.

**Remote-content and local-include trust boundary:**
- Risk: Database objects can fetch schema/license URLs, and external documentation include resolution reads relative paths without proving they remain under the repository root. Untrusted overlays can therefore create SSRF or local-file disclosure behavior when these methods are exposed by a service.
- Files: `tools/ruby-gems/udb/lib/udb/obj/database_obj.rb`, `tools/ruby-gems/udb/lib/udb/external_documentation_renderer.rb`, `tools/ruby-gems/udb/lib/udb/resolver.rb`
- Current mitigation: Standard repository data and schemas are expected to be trusted; absolute include paths and URL includes are left unresolved by the documentation renderer.
- Recommendations: Treat custom YAML/overlays as untrusted input, allowlist remote hosts and schemes, disable remote fetches by default, and enforce `realpath` containment for recursive includes.

**Shell command construction:**
- Risk: PDF generation joins an argument array into a single shell command, and PDF viewing interpolates paths into `system` strings. Metacharacters in caller-controlled names or paths can become shell syntax.
- Files: `tools/ruby-gems/udb/lib/udb/prm_generator.rb`, `backends/prm_pdf/tasks.rake`
- Current mitigation: Normal repository task names and generated paths are trusted.
- Recommendations: Pass executable and arguments separately to `Open3.popen3`/`system`, validate artifact identifiers, and never expose these tasks directly through a SpecChoice request handler.

**Downloaded native binaries lack integrity verification:**
- Risk: Espresso, eqntott, and must are downloaded after redirects, written executable, and then invoked without a checksum or signature check.
- Files: `tools/ruby-gems/udb/lib/udb/dep_paths.rb`, `tools/ruby-gems/udb/lib/udb/logic.rb`, `tools/ruby-gems/udb/lib/udb/dep_versions.rb`
- Current mitigation: The source URL is constructed for a pinned GitHub repository release and HTTPS is enabled for the initial URL.
- Recommendations: Pin and verify SHA-256 digests per version/platform, constrain redirect hosts and HTTPS, download atomically, and fail closed on verification errors.

## Performance Bottlenecks

**MCP reparses the database for every request:**
- Problem: Each query recursively walks `gen/` and parses candidate YAML files. Combined search repeats separate scans, fuzzy matching additionally runs pure-Python Levenshtein calculations, and all work executes synchronously inside async handlers.
- Files: `tools/mcp_gen_server/server.py`
- Cause: No startup index, per-file cache, configuration partition, background worker, or invalidation strategy exists.
- Improvement path: Build a configuration-scoped immutable index at startup, cache parsed documents by mtime/digest, precompute normalized searchable fields, and move expensive rebuilds off the event loop.

**Configuration resolution repeatedly scans and copies whole trees:**
- Problem: Freshness checks enumerate every standard/merged YAML file, and resolution copies the standard ISA tree into each resolved configuration.
- Files: `tools/ruby-gems/udb/lib/udb/resolver.rb`, `tools/ruby-gems/udb/lib/udb/yaml/yaml_resolver.rb`
- Cause: Dependency tracking is directory-wide and based on mtimes rather than a manifest/content graph.
- Improvement path: Resolve configurations outside request latency, publish versioned snapshots, and use a content manifest to rebuild only affected objects.

**Unbounded process-level caches:**
- Problem: Parsed IDL syntax and raw YAML contents live in class-level caches for the lifetime of the process with no eviction.
- Files: `tools/ruby-gems/idlc/lib/idlc.rb`, `tools/ruby-gems/udb/lib/udb/cfg_arch.rb`
- Cause: Caches optimize repeated generation jobs and assume a short-lived process with stable files.
- Improvement path: Bound caches by snapshot/configuration, expose invalidation, and monitor memory before using the libraries in a long-running prototype service.

## Fragile Areas

**Schema and API churn:**
- Files: `README.adoc`, `spec/schemas/`, `tools/ruby-gems/udb/lib/udb/resolver.rb`, `tools/ruby-gems/udb/lib/udb/cfg_arch.rb`
- Why fragile: The repository explicitly marks schemas, APIs, and `spec/` data as rapidly changing and potentially incorrect. Only instruction encodings plus instruction names/assembly formats are identified as third-party validated.
- Safe modification: Pin the exact UDB commit and schema version used by SpecChoice v1.3.2, preserve `$schema` metadata, validate every loaded snapshot, and present provenance/“unofficial” status in the prototype.
- Test coverage: Schema resolution has unit coverage, but no SpecChoice contract tests freeze the fields the prototype needs.

**Generated architecture sources:**
- Files: `spec/std/isa/csr/I/pmpaddrN.layout`, `spec/std/isa/csr/I/pmpcfgN.layout`, `spec/std/isa/inst/Zaamo/amoadd.SIZE.AQRL.layout`, `spec/std/isa/csr/I/pmpaddr0.yaml`, `spec/std/isa/inst/Zaamo/amoadd.w.yaml`
- Why fragile: Many checked-in YAML files are generated from `.layout` ERB templates and marked read-only/auto-generated.
- Safe modification: Edit the owning `.layout`, run `./do gen:arch`, and review the full generated diff; never patch generated YAML variants individually.
- Test coverage: `./do test:schema` and encoding regressions catch structure/conflicts, but product-level selection behavior still needs dedicated tests.

**Resolver concurrency and mutable generated output:**
- Files: `tools/ruby-gems/udb/lib/udb/resolver.rb`, `tools/ruby-gems/udb/lib/udb/cfg_arch.rb`, `gen/`
- Why fragile: Resolution serializes through an in-process mutex plus file locks while mutating shared gitignored directories; readers also maintain process-global caches.
- Safe modification: Generate into a versioned temporary snapshot, validate it, then atomically switch readers. Do not let requests resolve into a shared live directory.
- Test coverage: Resolver unit tests cover merge/resolve behavior, but no test exercises concurrent readers across regeneration and cache invalidation.

**Multi-toolchain setup and submodules:**
- Files: `.mise.toml`, `.gitmodules`, `bin/setup`, `bin/doctor`, `Gemfile.lock`, `uv.lock`, `package-lock.json`
- Why fragile: Ruby, Python, Node, native tools, downloaded solver helpers, and six pinned submodules must align. A partial setup can support documentation while failing architecture or simulator workflows.
- Safe modification: Run through repository wrappers, make `bin/doctor` a prototype prerequisite, and keep SpecChoice's minimal runtime dependency set separate from simulator/document-generation extras.
- Test coverage: Regression definitions cover repository tasks, but no single smoke test proves a clean setup can launch and query SpecChoice.

## Scaling Limits

**Search service:**
- Current capacity: One stdio MCP process; the repository contains more than 2,500 YAML files before generated per-configuration duplicates, and each search scans eligible files.
- Limit: Latency grows with every generated configuration; synchronous YAML parsing/fuzzy matching blocks other tool calls, and results can mix configurations.
- Scaling path: Index one immutable architecture snapshot per configuration, add pagination and deterministic sorting, use worker processes for rebuilds, and expose metrics for scan/index time.
- Files: `tools/mcp_gen_server/server.py`, `spec/`, `cfgs/`, `gen/`

**Configuration generation:**
- Current capacity: One resolver instance serializes merge/resolve work with a mutex and file locks; generated outputs share `gen/`.
- Limit: Concurrent interactive users queue behind full-tree work, while process-global caches make in-place regeneration unsafe.
- Scaling path: Precompute popular configurations, deduplicate snapshots by content hash, isolate per-job workspaces, and atomically publish read-only results.
- Files: `tools/ruby-gems/udb/lib/udb/resolver.rb`, `tools/ruby-gems/udb/lib/udb/cfg_arch.rb`

## Dependencies at Risk

**MCP runtime is outside managed dependencies:**
- Risk: `mcp[cli]` is imported by the server but is absent from `pyproject.toml` and `uv.lock`; the README instructs an unpinned manual `pip install` into a separate environment and claims Python 3.10+ while the project declares Python 3.12+.
- Impact: Standard `bin/setup`/`uv sync` does not establish a reproducible MCP runtime, and upstream API changes can break the only reusable query service.
- Migration plan: Add a pinned MCP dependency to the managed Python project or create a separately locked service package; align its Python requirement and add a launch smoke test.
- Files: `tools/mcp_gen_server/server.py`, `tools/mcp_gen_server/README.md`, `pyproject.toml`, `uv.lock`, `.python-version`

**Pre-release documentation dependencies:**
- Risk: Search/navigation relies on alpha/beta packages.
- Impact: A prototype embedded in the documentation site can inherit unstable build or browser behavior.
- Migration plan: Isolate SpecChoice from Antora/Docusaurus internals, pin exact versions, and add browser-level tests before integrating with the published site.
- Files: `package.json`, `package-lock.json`, `doc/package.json`

## Missing Critical Features

**SpecChoice v1.3.2 feature surface:**
- Problem: There is no SpecChoice version marker, selection model, API, UI, persistence format, compatibility explanation, or artifact export flow.
- Blocks: The repository cannot launch, exercise, or validate the requested prototype.
- Files: `README.adoc`, `cfgs/`, `doc/src/`, `tools/mcp_gen_server/`, `tools/ruby-gems/udb/lib/udb/`

**Configuration-scoped read API:**
- Problem: The standalone MCP API reads generated files across all configurations and approximates architectural metadata instead of querying `ConfiguredArchitecture`.
- Blocks: A user cannot reliably ask “what is selectable for this architecture?” or receive authoritative dependency/conflict reasons.
- Files: `tools/mcp_gen_server/server.py`, `tools/ruby-gems/udb/lib/udb/cfg_arch.rb`, `tools/ruby-gems/udb/lib/udb/condition.rb`, `tools/ruby-gems/udb/lib/udb/obj/extension.rb`

**Service lifecycle and production controls:**
- Problem: The MCP server has no managed dependency, health/readiness signal, snapshot version, cache rebuild protocol, authentication/authorization boundary, observability, or deployment configuration.
- Blocks: It is suitable as a local stdio utility, not as the backend of a multi-user prototype.
- Files: `tools/mcp_gen_server/server.py`, `tools/mcp_gen_server/README.md`, `pyproject.toml`, `.github/workflows/`

## Test Coverage Gaps

**MCP query server:**
- What's not tested: Path containment, symlink escape, configuration isolation, duplicate handling, XLEN accuracy, fuzzy top-k correctness, malformed YAML, regex resource limits, and startup with managed dependencies.
- Files: `tools/mcp_gen_server/server.py`, `tools/mcp_gen_server/README.md`, `tools/test/regress-tests.yaml`
- Risk: The query layer most likely to be reused by SpecChoice can return misleading results or expose files without CI detecting it.
- Priority: High

**SpecChoice behavior:**
- What's not tested: No requirements, fixtures, unit tests, integration tests, or end-to-end flows exist for SpecChoice v1.3.2.
- Files: `tests/`, `tools/test/regress-tests.yaml`, `doc/src/`, `cfgs/`
- Risk: Extension dependency/conflict handling, version selection, parameter choices, and generated output can regress without a release gate.
- Priority: High

**Long-lived resolver lifecycle:**
- What's not tested: Regeneration under active readers, class-cache invalidation, concurrent configuration builds, and atomic publication of generated data.
- Files: `tools/ruby-gems/udb/lib/udb/resolver.rb`, `tools/ruby-gems/udb/lib/udb/cfg_arch.rb`, `tools/ruby-gems/udb/test/test_cfg_arch.rb`, `tools/ruby-gems/udb/test/test_yaml_resolver.rb`
- Risk: A prototype server can serve stale or partially regenerated architecture data.
- Priority: High

**Unsupported solver branches:**
- What's not tested: End-to-end user choices that reach unsupported JSON Schema composition or complex extension-version requirement conversion.
- Files: `tools/ruby-gems/udb/lib/udb/z3.rb`, `tools/ruby-gems/udb/lib/udb/obj/extension.rb`, `tools/ruby-gems/udb/test/test_z3_parameter_constraints.rb`, `tools/ruby-gems/udb/test/test_z3_extensions.rb`
- Risk: Valid choice sets fail with internal `TODO` exceptions rather than a domain-level explanation.
- Priority: High

---

*Concerns audit: 2026-07-30*
