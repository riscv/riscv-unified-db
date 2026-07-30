# Phase 1: Isolated Evidence Boundary and Source Integrity - Research

**Researched:** 2026-07-30
**Domain:** Offline-verifiable evidence bundles, Git provenance, canonical integrity receipts, and worktree-boundary enforcement
**Confidence:** MEDIUM

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

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

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TS-01 | The operator can work entirely within a dependency-light `experiments/specchoice-v1.3.2/` boundary containing the prototype's code, configuration, data, prompts, tests, runs, reports, and notes, without modifying core UDB schemas or generated data. | Isolated stdlib-only package, immutable phase-start baseline, exact allowlist, file-kind validation, and a JSON-first integrity receipt. |
| TS-02 | The operator can verify a source manifest that pins every named public PR snapshot to its frozen commit and records stable hashes for every consumed source file. | Git-native PR-head/reachability/object/tree proof, two-level content manifest, raw-byte file inventory, offline verifier, and current PR #2192 rejected-attempt evidence. |
</phase_requirements>

## Project Constraints (from AGENTS.md)

- The UDB schemas and APIs change rapidly; Phase 1 must not depend on live core interfaces. [VERIFIED: codebase grep]
- Keep all implementation under `experiments/specchoice-v1.3.2/`; do not modify `spec/`, `cfgs/`, generated architecture data, root dependency manifests, or UDB generators. [VERIFIED: codebase grep]
- Do not edit generated YAML directly; where repository work would affect generated data, the owning `.layout` is authoritative and `./do gen:arch` is required. This is out of Phase 1 scope. [VERIFIED: codebase grep]
- New Python follows the repository's Ruff conventions: 100-column format, standard-library imports first, `snake_case` functions/locals, PascalCase classes, typed public structures, LF endings, final newline, and SPDX/REUSE-compatible file metadata. [VERIFIED: codebase grep]
- Repository PRs must ultimately pass `./bin/regress --all`; Phase 1's own verification must not require `bin/setup`, `bin/doctor`, Ruby, Node, Java, C++, or containers. [VERIFIED: codebase grep]

## Summary

Phase 1 should be a small, self-contained Python standard-library program whose only construction-time external capability is the Git CLI. It should capture the worktree baseline before adding the experiment directory, construct a staged source bundle from exact Git object bytes, validate the whole custody chain, and publish only a complete, accepted immutable generation. Offline verification must operate only on the committed bundle and Python standard library. [VERIFIED: codebase grep] [CITED: https://git-scm.com/docs/git-cat-file] [CITED: https://docs.python.org/3/library/hashlib.html]

The current source audit finds that five frozen commits equal their current canonical `refs/pull/<PR>/head` values, while PR #2192 has advanced from frozen commit `4bdaa4be1a404f78ff5b2841edd535afb637566b` to `f44a21144f603ce5d60b9b3af5605e820597b320`; the frozen commit exists but is not an ancestor of that head. A builder conforming to D-06/D-07 must emit `PR_PIN_NOT_REACHABLE` (or equivalent), preserve a rejected attempt receipt, and publish no accepted generation. It must not silently use `f44a…` or weaken the proof. [CITED: https://docs.github.com/en/pull-requests/reference/pull-requests] [CITED: https://git-scm.com/docs/git-merge-base] [CITED: https://api.github.com/repos/riscv/riscv-unified-db/commits/4bdaa4be1a404f78ff5b2841edd535afb637566b]

**Primary recommendation:** Plan three increments: (1) baseline, isolated stdlib package, canonical serialization, and environment decision; (2) staged Git construction plus immutable source-bundle manifests; (3) offline verification, boundary enforcement, canonical JSON receipt, and deterministic Markdown—making the #2192 fail-closed receipt a required tested path before any acceptance claim.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Phase-start baseline and allowlist evaluation | Local CLI / filesystem | Git index and worktree | The boundary is a repository-local state assertion, so the CLI owns deterministic capture and delta classification. [VERIFIED: codebase grep] |
| Source PR identity proof | Construction-time Git CLI | Canonical GitHub PR refs | Local Git object and ancestry checks are authoritative; hosting metadata only identifies the canonical ref. [CITED: https://docs.github.com/en/pull-requests/reference/pull-requests] [CITED: https://git-scm.com/docs/git-merge-base] |
| Raw file acquisition | Construction-time Git object database | Bundle storage | `git show <commit>:<path>`/object reads provide exact committed bytes before the bundle stores and hashes them. [CITED: https://git-scm.com/docs/git-show] |
| Manifest/root construction | Local Python stdlib | — | Canonical JSON, NFC normalization where permitted, and SHA-256 are deterministic local transformations. [CITED: https://docs.python.org/3/library/json.html] [CITED: https://docs.python.org/3/library/hashlib.html] [CITED: https://docs.python.org/3/library/unicodedata.html] |
| Accepted-bundle verification | Offline local Python stdlib | Bundle storage | Downstream replay cannot require network or local Git objects under D-02/D-09. [VERIFIED: codebase grep] |
| Reviewer-facing receipt | Local Python stdlib | Markdown file | Canonical JSON is gating authority; Markdown is a deterministic rendering with no independently computed facts. [VERIFIED: codebase grep] |

## Standard Stack

### Core

| Library / tool | Version observed | Purpose | Why Standard |
|----------------|------------------|---------|--------------|
| Python standard library (`argparse`, `dataclasses`, `hashlib`, `json`, `pathlib`, `stat`, `subprocess`, `unicodedata`, `unittest`) | Python 3.14.5 | Construction orchestration, canonical serialization, raw-byte hashing, filesystem validation, receipt generation, and offline verification | It satisfies the locked standalone-first contract without a project or root dependency change. [VERIFIED: codebase grep] [CITED: https://docs.python.org/3/library/hashlib.html] |
| Git CLI | 2.54.0 | Fetch exact PR refs, inspect commit/tree objects, prove ancestry, and materialize exact file bytes during construction only | GitHub exposes PR-head refs; Git supplies object and ancestor checks without treating mutable hosting metadata as authority. [CITED: https://docs.github.com/en/pull-requests/reference/pull-requests] [CITED: https://git-scm.com/docs/git-merge-base] |

### Supporting

| Library / tool | Version | Purpose | When to Use |
|----------------|---------|---------|-------------|
| GitHub metadata endpoint or `git ls-remote` | none required | Capture supplementary canonical-repository/PR-ref facts | Construction/audit only; never needed by the accepted-bundle verifier. [CITED: https://docs.github.com/en/pull-requests/reference/pull-requests] |
| Markdown renderer implemented in local Python | project-owned | Render `integrity-receipt.md` from validated JSON | Run only after canonical JSON receipt succeeds; it cannot alter receipt facts. [VERIFIED: codebase grep] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Stdlib-only verifier | Root `uv` environment, `jsonschema`, or UDB resolver | Contradicts standalone-first verification and introduces root/toolchain coupling without adding integrity authority. [VERIFIED: codebase grep] |
| Git-object evidence | GitHub REST/HTML metadata alone | Hosting metadata can supplement a receipt but cannot prove the pinned object is in the current PR-head ancestry. [CITED: https://git-scm.com/docs/git-merge-base] |
| Canonical content-tree root | Archive/tarball SHA-256 | Archive hashes vary with packaging metadata and cannot honor D-08's repackaging independence. [VERIFIED: codebase grep] |

**Installation:** None. Phase 1 must not install external packages or modify the root dependency state. [VERIFIED: codebase grep]

## Architecture Patterns

### System Architecture Diagram

```text
canonical upstream remote
  │ refs/pull/<pr>/head
  ▼
construction-only Git sandbox
  ├─ fetch PR head + pinned commit
  ├─ verify commit objects / commit trees
  ├─ merge-base --is-ancestor(pin, head)
  └─ read allowlisted <commit>:<path> bytes
              │
              ├─ failure ─► rejected-attempt receipt ─► no generation / non-zero
              │
              ▼
staged bundle (regular files only)
  ├─ raw bytes + raw SHA-256 / byte length
  ├─ explicit derived views + lineage
  └─ core two-level manifest
              │
              ▼
canonical root preimage ─► root_sha256 ─► immutable accepted generation
              │                                      │
              ▼                                      ▼
phase-start baseline + later worktree delta ─► canonical integrity-receipt.json
                                                       │
                                                       ▼
                                      deterministic integrity-receipt.md
                                                       │
                                                       ▼
                            offline stdlib verifier / later phases (no Git/network)
```

The construction path and the offline verification path must be separate commands/modules. The verifier accepts a selected generation directory plus manifest/receipt bytes; it must neither invoke `git` nor read the repository's `.git` directory. [VERIFIED: codebase grep]

### Recommended Project Structure

```text
experiments/specchoice-v1.3.2/
├── README.md                         # boundary, offline replay, and non-goals
├── src/specchoice_evidence/
│   ├── canonical.py                  # NFC/LF/canonical JSON/SHA-256 primitives
│   ├── filesystem.py                 # lstat containment and regular-file checks
│   ├── baseline.py                   # immutable phase-start capture and delta logic
│   ├── git_proof.py                  # construction-only Git subprocess wrapper
│   ├── bundle.py                     # staged construction and accepted publication
│   ├── verify.py                     # offline bundle verifier
│   ├── receipt.py                    # canonical JSON and Markdown derivation
│   └── cli.py                        # capture-baseline/build/verify/receipt commands
├── config/
│   ├── source_snapshots.json         # six pinned PR identities; exact path/role requests
│   └── boundary_allowlist.json       # experiment root plus exact GSD control files
├── bundles/
│   ├── accepted/<generation>/         # immutable, downstream-eligible only
│   └── rejected/<attempt-id>/         # evidence only; no generation/root eligibility
├── receipts/
│   ├── environment-decision.json      # canonical identity
│   ├── environment-audit.json         # non-canonical operational details
│   ├── integrity-receipt.json         # authoritative phase receipt
│   └── integrity-receipt.md           # deterministic derivative
├── tests/
│   ├── test_canonical.py
│   ├── test_filesystem_boundary.py
│   ├── test_git_proof.py
│   ├── test_bundle_verifier.py
│   └── test_receipts.py
└── notes/
    └── source-integrity-blockers.md   # reviewer decision only; never changes a pin
```

The exact names are discretionary; the separation between construction-only Git, accepted bundles, rejected attempts, and offline verification is not. [VERIFIED: codebase grep]

### Pattern 1: Canonical serialization is one owned primitive

**What:** Centralize recursive NFC normalization for canonical textual fields, LF normalization for canonical text outputs, semantic list ordering, `json.dumps(..., ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n"`, UTF-8 encoding, and SHA-256 over those exact bytes. Raw source files bypass all normalization and are hashed directly as bytes. [CITED: https://docs.python.org/3/library/json.html] [CITED: https://docs.python.org/3/library/hashlib.html] [CITED: https://docs.python.org/3/library/unicodedata.html]

**When to use:** Every canonical baseline, manifest core, root preimage, environment decision, and integrity receipt. Do not use it to rewrite source bytes. [VERIFIED: codebase grep]

**Example:**

```python
import hashlib
import json
import unicodedata


def canonical_json_bytes(value: object) -> bytes:
    normalized = normalize_nfc(value)
    payload = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        allow_nan=False,
        separators=(",", ":"),
    ) + "\n"
    return payload.encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def normalize_nfc(value: object) -> object:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value).replace("\r\n", "\n").replace("\r", "\n")
    if isinstance(value, list):
        return [normalize_nfc(item) for item in value]
    if isinstance(value, dict):
        return {normalize_nfc(key): normalize_nfc(item) for key, item in value.items()}
    return value
```

Source: adapted only from documented Python standard-library APIs. [CITED: https://docs.python.org/3/library/json.html] [CITED: https://docs.python.org/3/library/hashlib.html] [CITED: https://docs.python.org/3/library/unicodedata.html]

### Pattern 2: Git-native proof before bytes enter the bundle

**What:** Fetch the canonical `refs/pull/<number>/head` into a disposable Git directory, resolve the head SHA, verify pinned SHA and its `^{tree}`, run `git merge-base --is-ancestor <pin> <head>`, then retrieve only requested `pin:path` bytes. `--is-ancestor` succeeds only when the first commit is an ancestor of the second. [CITED: https://docs.github.com/en/pull-requests/reference/pull-requests] [CITED: https://git-scm.com/docs/git-merge-base] [CITED: https://git-scm.com/docs/git-cat-file]

**When to use:** Construction or independent online audit only. A nonzero result, missing object, invalid tree, or path absence is a deterministic construction failure. [VERIFIED: codebase grep]

**Example:**

```text
git -C <scratch-bare-repo> fetch --no-tags <canonical-upstream-url> \
  refs/pull/2164/head:refs/specchoice/pr/2164
head_sha=$(git -C <scratch-bare-repo> rev-parse refs/specchoice/pr/2164)
git -C <scratch-bare-repo> cat-file -e 22e84458c87a7ccf4c07034de1eb6d0bf9764144^{commit}
tree_sha=$(git -C <scratch-bare-repo> rev-parse 22e84458c87a7ccf4c07034de1eb6d0bf9764144^{tree})
git -C <scratch-bare-repo> merge-base --is-ancestor \
  22e84458c87a7ccf4c07034de1eb6d0bf9764144 "$head_sha"
git -C <scratch-bare-repo> show 22e84458c87a7ccf4c07034de1eb6d0bf9764144:<allowlisted-path>
```

Source: command composition based on official Git/GitHub documentation. [CITED: https://git-scm.com/docs/git-merge-base] [CITED: https://git-scm.com/docs/git-show] [CITED: https://docs.github.com/en/pull-requests/reference/pull-requests]

### Pattern 3: Publish accepted and rejected states separately

**What:** Build all candidate content in a staging location, validate every file/manifest/root property, then publish a new accepted directory only after all gates pass. On failure, write a stable rejected-attempt record containing no accepted generation ID and no usable root. [VERIFIED: codebase grep]

**When to use:** Every refresh and every deliberate negative test. The accepted verifier must reject anything not explicitly marked `accepted`. [VERIFIED: codebase grep]

### Pattern 4: Break root/manifest self-reference explicitly

**What:** Define a non-self-referential `content_manifest` canonical projection containing the two-level snapshot/inventory data. Hash it as `manifest_sha256`; calculate `root_sha256` from the sorted logical artifact records plus that hash; write computed `generation`, `root_sha256`, and `manifest_sha256` in a separate accepted identity/receipt object. [VERIFIED: codebase grep]

**When to use:** Before schemas or paths are frozen. The full reviewer-visible snapshot identity can record the root, but the bytes that define `manifest_sha256` cannot themselves include a value derived from that hash/root. This removes an otherwise impossible hash cycle while preserving D-05 and D-08. [VERIFIED: codebase grep]

### Anti-Patterns to Avoid

- **Manifest-only replay:** Re-fetching commits for verification violates offline sufficiency and makes later evidence sensitive to retention/ref changes. [VERIFIED: codebase grep]
- **Commit-exists proof:** A commit object existing is not proof it belongs to the named PR; require the canonical PR-head ancestry proof. [CITED: https://git-scm.com/docs/git-merge-base]
- **Raw-text normalization before hashing:** It redefines upstream authority and loses byte-level reproducibility. [VERIFIED: codebase grep]
- **Archive as root:** Tar/zip bytes import metadata and packaging differences that D-08 excludes. [VERIFIED: codebase grep]
- **Rewriting a baseline after a surprise:** It hides attribution drift; create a new baseline generation and record why. [VERIFIED: codebase grep]
- **`Path.resolve()` as the only containment defense:** Resolve can follow a symlink before it is rejected. Inspect with `lstat`, reject every link/special type, and then perform containment checks. [CITED: https://docs.python.org/3/library/pathlib.html]
- **A human-friendly Markdown report with extra calculations:** It becomes a second authority. Render only values already present in canonical JSON. [VERIFIED: codebase grep]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SHA-256 | Custom digest implementation | `hashlib.sha256` | Correct byte hashing is a standard-library concern with no experiment value in reimplementation. [CITED: https://docs.python.org/3/library/hashlib.html] |
| JSON encoding | String concatenation or ad hoc key sorting | `json.dumps` with all canonical options centralized | Handles escaping and valid JSON; the project-owned layer supplies ordering/normalization policy. [CITED: https://docs.python.org/3/library/json.html] |
| Git object/reachability proof | HTTP scraping of PR HTML or API-only checks | `git cat-file`, `git rev-parse`, `git merge-base --is-ancestor`, `git show` | Git objects and ancestry are the locked authority; metadata remains supplemental. [CITED: https://git-scm.com/docs/git-cat-file] [CITED: https://git-scm.com/docs/git-merge-base] |
| Path/file-kind classification | String-prefix containment checks | `os.lstat`, `stat.S_ISREG`, `stat.S_ISDIR`, explicit relative-path validation | Prefix checks and automatic link following miss escape/special-file cases. [CITED: https://docs.python.org/3/library/pathlib.html] |
| Unit-test runner | New testing dependency | `unittest` | Phase 1 needs no third-party test framework and must remain replayable from a plain Python installation. [VERIFIED: codebase grep] |

**Key insight:** The specialized logic is the custody policy—canonical projections, exact allowlist, state transitions, and stable diagnostics—not cryptography, JSON parsing, or Git graph traversal. [VERIFIED: codebase grep]

## Current Frozen-Source Audit

The construction-time audit used the canonical upstream remote, fetched each PR head into disposable bare repositories, inspected local Git objects, and applied the required ancestor check. It found the following state on 2026-07-30. [CITED: https://docs.github.com/en/pull-requests/reference/pull-requests] [CITED: https://git-scm.com/docs/git-merge-base]

| PR | Frozen pin | Resolved current PR head | Pinned tree | Ancestor proof | Planning consequence |
|----|------------|--------------------------|-------------|----------------|----------------------|
| 1765 | `8117d9a24e276e5ae21423dea2640b78db5924fe` | same | `f138e70ad60d56484781cf1a234baefe9c283886` | PASS | Normal construction test fixture. [CITED: https://api.github.com/repos/riscv/riscv-unified-db/pulls/1765] |
| 1766 | `3d03d48bde785e81220a2db3932b811422377ecf` | same | `760ca2e4c1faf181d7c1bd1d0e9cd9e8adcb88d4` | PASS | Normal construction test fixture. [CITED: https://api.github.com/repos/riscv/riscv-unified-db/pulls/1766] |
| 2097 | `72d18f75f5875f2d7b01027c6e2765084ac38283` | same | `f100c5c14f4ff2e51609b9d671b6281af4a4b013` | PASS | Normal construction test fixture. [CITED: https://api.github.com/repos/riscv/riscv-unified-db/pulls/2097] |
| 2164 | `22e84458c87a7ccf4c07034de1eb6d0bf9764144` | same | `af003b427c66bd8ac9803a91b3bf363a1b1304d9` | PASS | Normal construction test fixture. [CITED: https://api.github.com/repos/riscv/riscv-unified-db/pulls/2164] |
| 2192 | `4bdaa4be1a404f78ff5b2841edd535afb637566b` | `f44a21144f603ce5d60b9b3af5605e820597b320` | `de6ff1cf69d4585bc7078ffab5c1888b71830ba9` | **FAIL** | Required rejected-attempt fixture and human decision checkpoint; no accepted six-snapshot generation may be published. [CITED: https://api.github.com/repos/riscv/riscv-unified-db/commits/4bdaa4be1a404f78ff5b2841edd535afb637566b] [CITED: https://api.github.com/repos/riscv/riscv-unified-db/pulls/2192] |
| 1831 | `e9f6b9a9d0094cbbf3b99bb24a1ca578a364aff6` | same | `e86c12405136954868cb9ed7aaa124b9b847cf90` | PASS | Normal construction test fixture. [CITED: https://api.github.com/repos/riscv/riscv-unified-db/pulls/1831] |

The frozen contract does not enumerate the eventual exact consumed file paths. The plan must therefore make `source_snapshots.json` an explicit, versioned request inventory with each path and experiment role, reject an empty/duplicate/path-escaping inventory, and copy no file that is not requested. Later phases may add a new generation only through the same construction protocol. [VERIFIED: codebase grep]

## Common Pitfalls

### Pitfall 1: Treating a changed PR head as an allowed refresh

**What goes wrong:** The builder replaces an unreached pin with the PR's current head and still reports success.

**Why it happens:** Both identifiers look related in hosting metadata, but the frozen experiment identity is the pinned commit, not the mutable head.

**How to avoid:** Make equality/ancestor proof a gate before file extraction; emit `PR_PIN_NOT_REACHABLE` with PR, ref, pinned SHA, observed head SHA, and tree data; set `accepted: false`; omit generation/root eligibility. [CITED: https://git-scm.com/docs/git-merge-base]

**Warning signs:** The source receipt shows a different resolved head and pin, or `git merge-base --is-ancestor` exits 1. [CITED: https://git-scm.com/docs/git-merge-base]

### Pitfall 2: Hashing canonicalized bytes as if they were source bytes

**What goes wrong:** LF/NFC conversion changes a file but the manifest calls the converted file authoritative.

**Why it happens:** Canonical JSON policy is mistakenly applied to arbitrary upstream files.

**How to avoid:** Always hash/store raw bytes first. Derived text must record the raw SHA, transformation identifier/version/parameters, and its own SHA. [VERIFIED: codebase grep]

**Warning signs:** A raw file's byte length changes after a “normalization” step, or a derived artifact lacks a raw parent hash. [VERIFIED: codebase grep]

### Pitfall 3: A cyclic root/manifest design

**What goes wrong:** `manifest_sha256` includes `root_sha256`, while the root preimage includes `manifest_sha256`; different reruns cannot converge without an invalid fixed-point scheme.

**Why it happens:** The review-facing identity and the content manifest are treated as one byte object.

**How to avoid:** Freeze and hash a core canonical manifest projection without computed identity fields; root the logical tree against that hash; write a separate identity/receipt projection. Unit-test that recomputation from stored core bytes produces exactly the published hashes. [VERIFIED: codebase grep]

**Warning signs:** Serializer code adds computed root fields before calculating the manifest hash, or root changes on an otherwise identical recomputation. [VERIFIED: codebase grep]

### Pitfall 4: A baseline that assumes a clean worktree

**What goes wrong:** Existing `.DS_Store` artifacts are removed, hidden, or reported as Phase 1 violations.

**Why it happens:** The guard compares only current status to an ideal clean repository rather than to the immutable start state.

**How to avoid:** Capture tracked/index/untracked/deleted state and hashes before any Phase 1 implementation write. Classify existing deviations as `preexisting_unrelated`, never omit them, and fail only on later out-of-allowlist changes. [VERIFIED: codebase grep]

**Warning signs:** The receipt cannot identify when a difference first appeared, or it has no `phase_start_baseline_sha256`. [VERIFIED: codebase grep]

### Pitfall 5: Link-following verifier

**What goes wrong:** A symlink or mount point makes a bundle path read bytes outside its accepted tree.

**Why it happens:** High-level path APIs are used before file-kind checks.

**How to avoid:** Validate normalized relative paths before joining; walk with `lstat`; allow only directories and regular files; reject symlinks, other special modes, non-independent hardlink layouts, and device-boundary/mount-point conditions before opening files. [CITED: https://docs.python.org/3/library/pathlib.html]

**Warning signs:** Any `st_mode` is not a regular file/directory, `st_nlink > 1` is relied upon, a resolved path leaves the root, or an unexpected device ID appears under the bundle root. [ASSUMED]

### Pitfall 6: Markdown becomes an independent receipt

**What goes wrong:** JSON says one status while Markdown recalculates or rounds another.

**Why it happens:** Separate report code performs its own filesystem/Git calculations.

**How to avoid:** Validate canonical JSON, pass it as the only data model to Markdown generation, and test deterministic re-rendering. A Markdown failure is package-incomplete but does not rewrite valid JSON. [VERIFIED: codebase grep]

**Warning signs:** Markdown rendering imports bundle/Git modules, or `markdown -> JSON` round trips are treated as authoritative. [VERIFIED: codebase grep]

## Code Examples

Verified patterns from official sources:

### Offline raw-file verification

```python
from pathlib import Path
import hashlib
import os
import stat


def verify_regular_raw_file(bundle_root: Path, relative_path: str, expected_size: int, expected_sha256: str) -> None:
    candidate = bundle_root / relative_path
    if candidate.is_absolute() or ".." in Path(relative_path).parts:
        raise ValueError("PATH_ESCAPE_DETECTED")

    metadata = os.lstat(candidate)
    if stat.S_ISLNK(metadata.st_mode):
        raise ValueError("SYMLINK_REJECTED")
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError("SPECIAL_FILE_KIND_REJECTED")

    raw = candidate.read_bytes()
    if len(raw) != expected_size:
        raise ValueError("RAW_BYTE_LENGTH_MISMATCH")
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("RAW_SHA256_MISMATCH")
```

Source: adapted only from documented Python path and hashing APIs. [CITED: https://docs.python.org/3/library/pathlib.html] [CITED: https://docs.python.org/3/library/hashlib.html]

### Receipt-state gate

```python
def require_accepted_generation(identity: dict[str, object]) -> None:
    if identity.get("status") != "accepted":
        raise ValueError("GENERATION_NOT_ACCEPTED")
    if not identity.get("generation") or not identity.get("root_sha256"):
        raise ValueError("ACCEPTED_IDENTITY_INCOMPLETE")
```

This gate makes rejected construction evidence inspectable but impossible for downstream phases to consume as a generation. [VERIFIED: codebase grep]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Re-fetch or clone an upstream revision at each experiment run | Commit a minimal raw-byte evidence bundle and verify it offline | Locked Phase 1 decision D-02 | Replay survives absent Git objects, network loss, and mutable PR refs. [VERIFIED: codebase grep] |
| PR page/API says a commit is related | Fetch canonical PR head and prove pin ancestry with local Git objects | Locked D-06 | Source identity is graph-verifiable rather than metadata-dependent. [CITED: https://git-scm.com/docs/git-merge-base] |
| Hash an archive | Hash a canonical logical content tree | Locked D-08 | Root identity ignores repackaging metadata. [VERIFIED: codebase grep] |
| Treat Markdown as the primary reviewer artifact | Canonical JSON gates; Markdown derives from it | Locked D-17/D-18 | Humans and tools see one authority. [VERIFIED: codebase grep] |

**Deprecated/outdated:** Full-UDB setup as a Phase 1 prerequisite is incompatible with the locked standalone-first route. Do not run `bin/setup` or `bin/doctor` merely to populate an environment flag. [VERIFIED: codebase grep]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Mount-point/device-boundary detection can safely use device-ID comparison in the target macOS/Linux environment once the exact implementation policy is selected. | Common Pitfalls | A verifier could under- or over-reject a directory boundary; use explicit test fixtures and document platform behavior before locking implementation. |

## Open Questions

1. **Frozen PR #2192 pin is not reachable from its current canonical PR head.**
   - What we know: The exact frozen commit exists and has tree `de6ff1cf69d4585bc7078ffab5c1888b71830ba9`, but `git merge-base --is-ancestor 4bdaa… f44a…` fails. [CITED: https://api.github.com/repos/riscv/riscv-unified-db/commits/4bdaa4be1a404f78ff5b2841edd535afb637566b] [CITED: https://api.github.com/repos/riscv/riscv-unified-db/pulls/2192]
   - What's unclear: Whether the frozen execution contract intended a prior PR head that was later force-pushed, or contains an incorrect PR/pin association.
   - Recommendation: Implement and demonstrate the rejected-attempt path now; preserve its exact receipt. Before accepting a six-snapshot generation or advancing on a source-integrity success claim, obtain human authorization to revise the frozen contract or to record a formal Red/blocker outcome. Do not change the pin unilaterally. [VERIFIED: codebase grep]

2. **Exact consumed-file inventory is not yet frozen.**
   - What we know: D-01 requires every consumed file but forbids vendoring unrelated snapshot content.
   - What's unclear: The minimum exact path/role set needed by all later stages.
   - Recommendation: Add a versioned source-request inventory in this phase; it is the sole construction input. Require every named PR to have an explicit justified entry, and add future files only in a new accepted generation. [VERIFIED: codebase grep]

## Environment Availability

| Dependency | Required By | Available | Version / status | Fallback |
|------------|-------------|-----------|------------------|----------|
| `python3` standard library | Construction, offline verifier, receipts, tests | ✓ | Python 3.14.5 | — |
| Git CLI | Construction-time canonical PR/object proof | ✓ | Git 2.54.0 | No equivalent; failure produces rejected attempt / documented blocker. |
| Canonical upstream network access | Construction or independent audit only | ✓ during research audit | Six PR refs and exact pin fetches succeeded from a disposable bare repo | Accepted-bundle verifier remains offline; network loss prevents only new construction/refresh. |
| Local Git objects for frozen pins | Current repository construction starting point | ✗ | None of the six pins existed locally before the disposable audit | Fetch into a disposable Git directory; never require them for accepted verification. |
| Full UDB setup/toolchain | Phase 1 | Intentionally unprobed | D-09 prohibits probing it merely for a flag | Standalone-first is the selected route. [VERIFIED: codebase grep] |

**Missing dependencies with no fallback:** None for the standalone/offline verifier. A new source-bundle construction requires Git plus canonical-remote access; without them it must emit an explicit rejected attempt rather than substitute data. [VERIFIED: codebase grep]

**Missing dependencies with fallback:** No Phase 1 dependency requires a third-party package or root environment setup. [VERIFIED: codebase grep]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Python standard-library `unittest` |
| Config file | none — tests discover from the experiment-local `tests/` directory |
| Quick run command | `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -v` |
| Full suite command | `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -v` |

No SpecChoice tests or experiment directory currently exist, so Wave 0 establishes the local test harness without adding root dependencies. [VERIFIED: codebase grep]

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TS-01 | Capture immutable baseline; classify pre-existing `.DS_Store` as non-blocking; fail later out-of-allowlist create/modify/delete actions | unit + filesystem integration | `PYTHONPATH=src python3 -m unittest tests.test_filesystem_boundary -v` | ❌ Wave 0 |
| TS-01 | Reject symlink, special file, path escape, and hardlink-dependent accepted content | unit | `PYTHONPATH=src python3 -m unittest tests.test_filesystem_boundary -v` | ❌ Wave 0 |
| TS-01 | Canonical environment decision excludes noncanonical audit data and carries standalone-first fields | unit | `PYTHONPATH=src python3 -m unittest tests.test_canonical -v` | ❌ Wave 0 |
| TS-02 | Verify each valid pin's commit object, tree, PR-head equality/ancestry, and exact requested raw bytes | Git integration (disposable repo) | `PYTHONPATH=src python3 -m unittest tests.test_git_proof -v` | ❌ Wave 0 |
| TS-02 | Current #2192 pin creates deterministic rejected receipt without accepted generation/root | Git integration | `PYTHONPATH=src python3 -m unittest tests.test_git_proof -v` | ❌ Wave 0 |
| TS-02 | Offline verifier recomputes raw bytes, derived lineage, manifest hash, root, and receipt independently with no `git` call | unit + process isolation | `PYTHONPATH=src python3 -m unittest tests.test_bundle_verifier -v` | ❌ Wave 0 |
| TS-01, TS-02 | Canonical JSON and Markdown receipts are byte-stable; Markdown facts equal JSON facts | golden / determinism | `PYTHONPATH=src python3 -m unittest tests.test_receipts -v` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py' -v`
- **Per wave merge:** Run the same suite plus one deliberate offline replay in a copied accepted bundle directory with `PATH` excluding Git.
- **Phase gate:** Full suite green, accepted/rejected state tests green, baseline receipt clean for the permitted delta, and reviewer checkpoint resolves the #2192 evidence before claiming a six-snapshot accepted source generation.

### Wave 0 Gaps

- [ ] `experiments/specchoice-v1.3.2/tests/test_canonical.py` — canonical bytes, hash, ordering, and no-computed-field cycle tests.
- [ ] `experiments/specchoice-v1.3.2/tests/test_filesystem_boundary.py` — baseline delta, allowlist, lstat, symlink, special-file, hardlink, and escape tests.
- [ ] `experiments/specchoice-v1.3.2/tests/test_git_proof.py` — isolated bare-repo success and PR #2192 failure fixtures.
- [ ] `experiments/specchoice-v1.3.2/tests/test_bundle_verifier.py` — offline verification without Git/network.
- [ ] `experiments/specchoice-v1.3.2/tests/test_receipts.py` — canonical JSON/derived Markdown determinism and no independent facts.
- [ ] `experiments/specchoice-v1.3.2/tests/__init__.py` — local test package marker.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V1 Architecture, Design and Threat Modeling | yes | Explicit construction/verification trust boundary, accepted/rejected state machine, and threat tests. [VERIFIED: codebase grep] |
| V5 Input Validation | yes | Strict schema-like field validation, relative POSIX path rules, canonical JSON validation, exact expected/observed diagnostics, and no implicit defaults. [VERIFIED: codebase grep] |
| V8 Data Protection | yes | Preserve authoritative raw bytes; SHA-256 detects integrity drift but does not claim authenticity beyond the captured Git proof. [CITED: https://docs.python.org/3/library/hashlib.html] |
| V10 Malicious Code | yes | Do not execute bundled source; treat it as bytes/text, and permit only regular files/directories. [VERIFIED: codebase grep] |
| V12 File and Resource Security | yes | `lstat` before read, reject symlinks/special files/path escape/mount-like boundaries, and independently verify each file. [CITED: https://docs.python.org/3/library/pathlib.html] |
| V14 Configuration | yes | Exact source pins, immutable generation identity, canonical environment decision, and narrow boundary allowlist. [VERIFIED: codebase grep] |

### Known Threat Patterns for the evidence stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| PR head moves or is force-pushed | Tampering | Capture resolved ref and require pin equality/ancestry; reject failure without publishing an accepted root. [CITED: https://git-scm.com/docs/git-merge-base] |
| Commit exists but is unrelated to the named PR | Spoofing | Require local Git graph proof, not API/HTML association alone. [CITED: https://git-scm.com/docs/git-merge-base] |
| Symlink/path escape reads outside bundle | Elevation of Privilege / Information Disclosure | Validate relative POSIX path, `lstat` every component/file, reject links and special kinds before reading. [CITED: https://docs.python.org/3/library/pathlib.html] |
| Derived artifact substituted for raw authority | Tampering | Raw bytes/hash remain authoritative; derived files require explicit parent hash and transform lineage. [VERIFIED: codebase grep] |
| Receipt mismatch or nondeterministic report | Repudiation / Tampering | One canonical JSON authority with self-hash; Markdown derives only from validated JSON. [VERIFIED: codebase grep] |
| Quiet out-of-boundary worktree change | Tampering | Immutable phase-start baseline plus exact later-delta allowlist and nonzero gate. [VERIFIED: codebase grep] |

## Sources

### Primary (HIGH confidence)

- None. The research-plan confidence seam classified the available documentation providers as MEDIUM, so this document does not elevate them to HIGH.

### Secondary (MEDIUM confidence)

- [Git `merge-base` documentation](https://git-scm.com/docs/git-merge-base) — `--is-ancestor` semantics and exit-status proof.
- [Git `cat-file` documentation](https://git-scm.com/docs/git-cat-file) and [Git `show` documentation](https://git-scm.com/docs/git-show) — local object inspection and committed-content access.
- [GitHub pull-request reference](https://docs.github.com/en/pull-requests/reference/pull-requests) — PR-head ref behavior.
- [Python `json` documentation](https://docs.python.org/3/library/json.html), [hashlib documentation](https://docs.python.org/3/library/hashlib.html), [unicodedata documentation](https://docs.python.org/3/library/unicodedata.html), and [pathlib documentation](https://docs.python.org/3/library/pathlib.html) — canonical JSON primitives, SHA-256, NFC normalization, and path APIs.
- [Canonical PR #2192 commit](https://api.github.com/repos/riscv/riscv-unified-db/commits/4bdaa4be1a404f78ff5b2841edd535afb637566b) and [current PR #2192 metadata](https://api.github.com/repos/riscv/riscv-unified-db/pulls/2192) — current existence/head evidence, cross-checked by disposable Git-object audit.

### Tertiary (LOW confidence)

- Device-ID mount-boundary heuristic in the Assumptions Log; it is deliberately marked for implementation-time validation.

## Metadata

**Confidence breakdown:**

- Standard stack: MEDIUM — locked project evidence plus official standard-library/Git documentation; no external package recommendation.
- Architecture: MEDIUM — directly constrained by locked decisions, with Git/Python mechanics supported by official documentation.
- Pitfalls: MEDIUM — most arise directly from frozen custody/boundary rules; mount/device detection remains an explicit assumption.

**Research date:** 2026-07-30
**Valid until:** 2026-08-06 for live PR-head observations; the frozen contract itself remains authoritative until changed by an authorized decision.
