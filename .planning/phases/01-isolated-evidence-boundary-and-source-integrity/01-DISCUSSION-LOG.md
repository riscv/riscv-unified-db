# Phase 1: Isolated Evidence Boundary and Source Integrity - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-30
**Phase:** 1-Isolated Evidence Boundary and Source Integrity
**Areas discussed:** Snapshot custody and offline replay, Manifest granularity and trust chain, Environment decision and fallback evidence, Boundary guard and integrity receipt

---

## Snapshot Custody and Offline Replay

### Committed source material

| Option | Description | Selected |
|--------|-------------|----------|
| Hybrid evidence bundle | Commit exact consumed files, hashes, and provenance without unrelated snapshot contents. | ✓ |
| Manifest only | Commit pins, paths, and hashes; fetch public commits during reproduction. | |
| Full snapshot copies | Vendor the relevant PR trees for complete offline independence. | |

**User's choice:** Hybrid evidence bundle.
**Notes:** The experiment keeps exact consumed files and their pinned-commit provenance while avoiding unrelated snapshot duplication.

### Offline sufficiency

| Option | Description | Selected |
|--------|-------------|----------|
| Bundle alone | Verification and downstream stages require neither network nor local Git objects. | ✓ |
| Bundle plus local Git objects | Replay is network-free but requires the pinned commits locally. | |
| Online source recheck | Recheck public sources during every verification run. | |

**User's choice:** Bundle alone.
**Notes:** Git is used only to build, independently audit, or refresh a bundle.

### Refresh behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Immutable generations | Every refresh creates a new content-addressed generation and root. | ✓ |
| Replace until freeze | Permit replacement before Phase 1 approval. | |
| Mutable with audit log | Update in place while recording changes. | |

**User's choice:** Immutable generations.
**Notes:** Existing generations are never overwritten. Downstream artifacts record the exact generation, root SHA-256, and manifest SHA-256 consumed.

### Authoritative bytes

| Option | Description | Selected |
|--------|-------------|----------|
| Raw bytes plus explicit derived views | Preserve exact upstream bytes and record transformation lineage for every derived artifact. | ✓ |
| Raw bytes only | Normalize only in memory and never persist derived views. | |
| Canonicalized bundle files | Treat LF/NFC-normalized bytes as authoritative. | |

**User's choice:** Raw bytes plus explicit derived views.
**Notes:** Every derived view records the raw source hash, transformation name/version and parameters, and its own hash. Canonicalized views never replace authoritative raw bytes.

---

## Manifest Granularity and Trust Chain

### Manifest boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Two-level manifest | Bind snapshot identity and an explicit consumed-file inventory. | ✓ |
| Consumed-file inventory only | Pin commit and files without commit-tree identity. | |
| Whole snapshot tree | Inventory and hash every file in every pinned commit. | |

**User's choice:** Two-level manifest.
**Notes:** Snapshot identity records repository, PR, pinned commit, tree, generation, and root. Each consumed file records upstream/local paths, role, raw hash, length, and derived lineage.

### PR-to-commit proof

| Option | Description | Selected |
|--------|-------------|----------|
| Git-native PR reachability plus captured metadata | Verify PR-ref reachability and local commit/tree objects; retain deterministic supporting metadata. | ✓ |
| Commit existence only | Verify the commit exists without proving PR association. | |
| Hosting-API proof only | Trust captured hosting API metadata. | |

**User's choice:** Git-native PR reachability plus captured metadata.
**Notes:** The pinned commit must equal or be reachable as an ancestor of the PR head. Git-object proof is authoritative; API metadata is supplementary.

### Construction failure

| Option | Description | Selected |
|--------|-------------|----------|
| Fail closed without publishing a generation | Preserve a failed-attempt receipt but create no accepted generation or eligible root. | ✓ |
| Publish a quarantined generation | Give failed content an inspectable but blocked generation ID. | |
| Publish with warnings | Permit downstream use despite mismatches. | |

**User's choice:** Fail closed without publishing a generation.
**Notes:** Reachability, object, path, length, hash, linkage, and manifest failures abort. Failed receipts retain stable codes, expected/observed values, tool versions, and non-canonical timestamps.

### Bundle root meaning

| Option | Description | Selected |
|--------|-------------|----------|
| Canonical content tree | Hash sorted logical artifact identities and the canonical manifest, independent of packaging. | ✓ |
| Deterministic archive bytes | Make canonical archive bytes the identity. | |
| Manifest bytes only | Reuse the manifest hash as the bundle root. | |

**User's choice:** Canonical content tree.
**Notes:** Repacking, compression, timestamps, ownership metadata, and archive format do not change `root_sha256`.

---

## Environment Decision and Fallback Evidence

### Default route

| Option | Description | Selected |
|--------|-------------|----------|
| Standalone-first | Use Python standard library and construction-only Git; defer the full UDB toolchain. | ✓ |
| Full UDB setup first | Attempt `bin/setup`/`bin/doctor` before falling back. | |
| Support both immediately | Implement and validate both routes from the start. | |

**User's choice:** Standalone-first.
**Notes:** Phase 1 does not require UDB resolution, generators, Ruby, IDL, C++, Node, or root setup. Verification and downstream replay use only Python standard library plus offline bundle access.

### Frozen fallback status

| Option | Description | Selected |
|--------|-------------|----------|
| Proactive environment decision | Record standalone-first as primary and leave the 90-minute fail-safe dormant. | ✓ |
| Immediate fallback | Mark standalone as a fallback at time zero. | |
| Probe full setup | Run `bin/doctor` only to populate fallback status. | |

**User's choice:** Proactive environment decision.
**Notes:** Record `fallback_triggered: false`, `full_udb_setup_attempted: false`, and `fallback_ceiling_status: not_started`. Do not probe an unnecessary environment.

### Incident timing

| Option | Description | Selected |
|--------|-------------|----------|
| Cumulative wall-clock incident | One timer starts at the first concrete dependency failure and never pauses or resets. | ✓ |
| Active troubleshooting time | Exclude downloads, builds, and unattended waits. | |
| Per-attempt timer | Give each setup approach a separate 90 minutes. | |

**User's choice:** Cumulative wall-clock incident.
**Notes:** Retries and approach changes do not reset the clock. At the ceiling, stop environment expansion and use the smaller workaround or document the Red blocker.

### Canonical versus audit evidence

| Option | Description | Selected |
|--------|-------------|----------|
| Canonical decision plus separate audit receipt | Hash stable environment identity and keep machine-specific operational evidence separate. | ✓ |
| Single complete receipt | Mix timestamps, paths, commands, and stable identity in one artifact. | |
| Minimal decision only | Omit command-level incident evidence. | |

**User's choice:** Canonical decision plus separate audit receipt.
**Notes:** The audit receipt references the canonical decision hash. The canonical identity does not hash the audit receipt, so timestamps, paths, platform data, and sanitized output cannot change experiment identity.

---

## Boundary Guard and Integrity Receipt

### Worktree baseline

| Option | Description | Selected |
|--------|-------------|----------|
| Phase-start delta with explicit allowlist | Attribute only post-baseline changes and allow only the experiment root plus exact control files. | ✓ |
| Completely clean worktree | Block until every tracked and untracked difference is removed. | |
| Tracked files only | Ignore all untracked files. | |

**User's choice:** Phase-start delta with explicit allowlist.
**Notes:** Pre-existing `.DS_Store` files remain visible and unattributed. New, modified, or deleted paths outside the narrow allowlist fail; broad roots and wildcard allowlists are prohibited.

### Baseline integrity

| Option | Description | Selected |
|--------|-------------|----------|
| Canonical hashed baseline | Hash repository-relative start state and exact allowlist before implementation. | ✓ |
| Non-canonical audit snapshot | Preserve initial status without stable identity. | |
| Recompute from Git history | Infer the baseline later. | |

**User's choice:** Canonical hashed baseline.
**Notes:** The record includes HEAD, index/worktree/untracked state, byte lengths and hashes, deleted paths, file kinds, symlink targets, and allowlist. A defective baseline requires a new generation and phase restart rather than an in-place edit.

### File-kind containment

| Option | Description | Selected |
|--------|-------------|----------|
| Regular files and directories only | Reject links, special files, mount points, and path escapes. | ✓ |
| Internal symlinks allowed | Permit only normalized in-bundle symlink targets. | |
| Record but allow links | Preserve link metadata without blocking. | |

**User's choice:** Regular files and directories only.
**Notes:** Each file path must be independently readable and verified. Suggested stable diagnostics include `SPECIAL_FILE_KIND_REJECTED`, `SYMLINK_REJECTED`, and `PATH_ESCAPE_DETECTED`.

### Reviewer receipt

| Option | Description | Selected |
|--------|-------------|----------|
| Canonical JSON plus derived Markdown | Use hashed JSON for gating and generate a deterministic human report from it. | ✓ |
| Canonical JSON only | Keep only the machine-readable artifact. | |
| Markdown with embedded evidence | Make the human report authoritative. | |

**User's choice:** Canonical JSON plus derived Markdown.
**Notes:** Markdown contains no independently computed facts. Blocking violations or JSON-generation failure produce nonzero exit. Markdown-generation failure leaves valid JSON intact but makes the reviewer package incomplete.

---

## the agent's Discretion

- Exact internal module names, schema decomposition, command names, and accepted-bundle directory names within the frozen experiment boundary.
- Additional stable diagnostic codes consistent with the fail-closed contracts.

## Deferred Ideas

None — discussion stayed within Phase 1.
