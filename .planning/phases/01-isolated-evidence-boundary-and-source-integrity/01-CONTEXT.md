# Phase 1: Isolated Evidence Boundary and Source Integrity - Context

**Gathered:** 2026-07-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 establishes a dependency-light workspace under `experiments/specchoice-v1.3.2/`, constructs and verifies immutable source-bundle generations for the six frozen public PR snapshots, records the standalone environment decision, and produces a reviewer-facing boundary and source-integrity receipt. It does not implement the PR #2164 measurement adapter, adjudication semantics, data preregistration, retrieval, prompts, or model execution.

</domain>

<decisions>
## Implementation Decisions

### Snapshot Custody and Offline Replay

- **D-01:** Commit a hybrid evidence bundle containing every exact source file consumed by the experiment, its hash, and pinned-commit provenance. Do not vendor unrelated snapshot contents.
- **D-02:** After construction, the bundle alone must support verification and every downstream experiment stage without network access or local Git objects. Git is permitted only to construct, independently audit, or refresh a bundle.
- **D-03:** Every refresh creates a new immutable, content-addressed generation. Existing generations are never modified or overwritten, and every downstream artifact records the exact generation, `root_sha256`, and `manifest_sha256` it consumed.
- **D-04:** Exact upstream bytes are authoritative and are stored and hashed unchanged. LF/NFC-normalized text, parsed representations, and extracted subsections are separate derived artifacts that record the raw source SHA-256, transformation name and version, transformation parameters, and derived-file SHA-256. A derived view never replaces or redefines the authoritative raw bytes.

### Manifest Granularity and Trust Chain

- **D-05:** Use a two-level manifest. Snapshot identity records canonical repository identity, PR number, pinned commit SHA, commit tree SHA, bundle generation, and root hash. The consumed-file inventory records upstream path, local bundle path, experimental role, authoritative raw SHA-256, byte length, derived-artifact links, transformation identifiers, and derived hashes.
- **D-06:** Bundle construction must fetch the canonical repository's PR head ref, prove that the pinned commit equals or is an ancestor of the resolved PR head, and verify the commit and tree objects locally. Git-object proof is authoritative; deterministic hosting metadata is supplementary. The audit receipt records the PR ref, resolved head SHA, pinned commit SHA, tree SHA, result, and tool versions.
- **D-07:** Any PR-reachability, Git-object, path-resolution, byte-length, raw-hash, derived-linkage, or manifest-consistency failure aborts construction. Preserve a deterministic failed-attempt receipt with stable error code and expected/observed values, but assign no accepted generation ID or downstream-eligible root. Downstream tools may consume only explicitly `accepted` generations.
- **D-08:** `root_sha256` identifies a versioned canonical content tree rather than archive bytes. Canonically serialize a deterministically sorted sequence covering every bundle-relative path, artifact kind, byte length, authoritative SHA-256, raw/derived relationship, and canonical manifest SHA-256. Compression, timestamps, ownership, repacking, and archive format do not affect the root.

### Environment Decision and Fallback Evidence

- **D-09:** Phase 1 is standalone-first. Construction uses the Python standard library and Git CLI, with a hosting metadata client optional and supplementary. Accepted-bundle verification and all downstream replay use the Python standard library only, without network access or local Git objects. Do not require or probe the full UDB toolchain merely to populate an environment flag.
- **D-10:** Record standalone-first as the selected primary route, not a fallback: `fallback_triggered: false`, `full_udb_setup_attempted: false`, and `fallback_ceiling_status: not_started`. Retain the frozen 90-minute ceiling only as a fail-safe if an unexpected Phase 1 dependency appears.
- **D-11:** An unexpected dependency starts one cumulative wall-clock incident at the first concrete failed capability check or setup action. Retries, alternative approaches, downloads, builds, and unattended waits neither pause nor reset the timer. At 90 minutes, stop expanding the environment and use the predefined smaller workaround or record the applicable Red blocker.
- **D-12:** Include a canonical environment decision in reproducible experiment identity. It records stable capabilities, tool identities and versions, route, outcome, UDB setup status, fallback policy, incident outcome, and stable error codes, while excluding timestamps, usernames, hostnames, absolute paths, raw command output, platform-specific error text, network addresses, and credentials.
- **D-13:** Store operational details in a separate non-canonical audit receipt: sanitized commands and output, platform data, start/end times, elapsed time, failures, workaround, and Red-blocker status. The audit receipt references the canonical environment-decision SHA-256; the canonical decision does not hash or otherwise depend on the audit receipt.

### Boundary Guard and Integrity Receipt

- **D-14:** Capture a Phase 1 start state and evaluate only the later worktree delta. Allow changes beneath `experiments/specchoice-v1.3.2/` plus exact, narrowly scoped GSD planning/control files. Pre-existing differences such as `.DS_Store` remain visible as `preexisting_unrelated` with `attributed_to_phase: false`; they neither block Phase 1 nor disappear from the receipt. Any new, modified, or deleted out-of-boundary path fails.
- **D-15:** Before any implementation change, canonically serialize and hash the phase-start baseline. It records repository HEAD, staged paths, tracked changes, untracked files, relevant byte lengths and SHA-256 values, deleted paths, file kinds, symlink targets, and the exact allowlist using repository-relative POSIX paths and deterministic ordering. Every later receipt references `phase_start_baseline_sha256`. An incorrect baseline is never edited in place; restart Phase 1 with a new baseline generation and record the reason.
- **D-16:** Authoritative contents under `experiments/specchoice-v1.3.2/` and in every accepted source-bundle generation may contain only independent regular files and directories. Reject symlinks, hardlink-dependent layouts, sockets, FIFOs, block or character devices, mount points, path escapes, and other special kinds. Each file path must be independently readable and verified by its own bytes, length, and SHA-256.
- **D-17:** Use canonical JSON as the authoritative hashed integrity-gating artifact. It contains a stable schema version, phase-start baseline hash, bundle generation and root hash, boundary classifications, blocking and non-blocking diagnostics, final pass/fail status, and receipt SHA-256.
- **D-18:** Generate the Markdown reviewer report deterministically from the canonical JSON, with no independently calculated facts. Exit zero only when all gating checks and authoritative receipt generation pass. A Markdown-generation failure does not invalidate valid JSON, but the reviewer package remains incomplete until the Markdown is regenerated.

### the agent's Discretion

The planner may choose exact internal module names, schema file decomposition, command names, and accepted-bundle directory names within `experiments/specchoice-v1.3.2/`, provided the frozen custody, hashing, offline, boundary, and receipt contracts above remain intact. Stable diagnostic codes beyond the user-specified examples may also be defined during planning.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Frozen Execution Contract

- `../../Downloads/LFX_RISCV_SpecChoice_v1.3.2_frozen_execution_baseline.md` §§0, 3, 4, 14–16, 23–25 — Frozen project scope, six public snapshot pins, repository layout, determinism rules, Day 1 timebox, and change-control policy.

### Project and Phase Contract

- `.planning/PROJECT.md` — Project boundary, active constraints, source-snapshot list, experiment placement, and the standalone fallback requirement.
- `.planning/REQUIREMENTS.md` — Phase 1 requirements TS-01 and TS-02 and the all-path reproducibility and human-control contract.
- `.planning/ROADMAP.md` — Phase 1 goal, success criteria, human checkpoint, and the three planned vertical increments.

### Repository Context

- `.planning/codebase/STACK.md` — Root toolchain breadth and pinned runtimes that motivate the standalone Phase 1 boundary.
- `.planning/codebase/ARCHITECTURE.md` — Authoritative source/derived-artifact boundaries and repository integration patterns.
- `.planning/codebase/CONCERNS.md` — Absence of an existing SpecChoice module, schema/API churn, setup fragility, and the recommendation to isolate the prototype from core UDB internals.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- Python standard library (`hashlib`, `json`, `pathlib`, `subprocess`, Unicode normalization, and deterministic sorting): sufficient for bundle construction support, canonical serialization, hashing, verification, and receipts.
- Git CLI and the canonical `upstream` remote: construction-only source for PR refs, commits, trees, and exact file bytes.
- Existing repository command and test conventions: useful as references, but Phase 1 must not add root dependencies or require `bin/setup`, `bin/doctor`, Ruby, IDL, C++, or Node.

### Established Patterns

- Canonical source data lives under `spec/`, while derived repository artifacts normally live under `gen/`; Phase 1 deliberately establishes a separate research boundary under `experiments/specchoice-v1.3.2/`.
- Repository schemas and APIs change rapidly, so the experiment must pin exact public commits and preserve raw source bytes rather than depending on current core interfaces.
- The worktree contains pre-existing untracked `.DS_Store` files. Boundary verification must use the immutable phase-start delta model rather than requiring or fabricating a clean worktree.

### Integration Points

- New Phase 1 implementation belongs entirely under `experiments/specchoice-v1.3.2/`.
- Named GSD artifacts under `.planning/phases/01-isolated-evidence-boundary-and-source-integrity/` are control-plane exceptions and must be exact-file allowlisted.
- Later phases consume only an accepted bundle generation through its canonical manifest, generation identifier, manifest hash, and content-tree root; they must not refetch or inspect Git objects.
- There is no existing `experiments/` tree or SpecChoice implementation to extend, so the phase is a small greenfield package rather than a core UDB modification.

</code_context>

<specifics>
## Specific Ideas

- Preferred source identity fields: `generation`, `root_sha256`, and `manifest_sha256`.
- Preferred canonical environment route fields include `route: standalone_first`, `fallback_triggered: false`, `full_udb_setup_attempted: false`, and `fallback_ceiling_minutes: 90`.
- Preferred baseline identity: `phase_start_baseline_sha256 = SHA256(canonical_baseline_bytes)`.
- Preferred stable file-kind diagnostics include `SPECIAL_FILE_KIND_REJECTED`, `SYMLINK_REJECTED`, and `PATH_ESCAPE_DETECTED`.
- Preferred reviewer contract names are `integrity-receipt.json` as authoritative and `integrity-receipt.md` as its deterministic derivative.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1-Isolated Evidence Boundary and Source Integrity*
*Context gathered: 2026-07-30*
