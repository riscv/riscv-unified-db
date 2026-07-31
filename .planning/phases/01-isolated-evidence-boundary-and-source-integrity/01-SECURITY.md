---
phase: 01
slug: isolated-evidence-boundary-and-source-integrity
status: verified
threats_open: 0
asvs_level: 1
created: 2026-07-31
---

# Phase 01 — Security

> ASVS L1 verification of the plan-authored STRIDE register. High-severity threats block advancement.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Git and worktree → custody tools | Repository history and mutable filesystem state enter baseline, proof, and delta classification. | commits, trees, paths, modes, bytes |
| Requested path → filesystem open | Untrusted bundle and inventory paths are resolved before authoritative reads. | relative paths, file kinds, link targets |
| Upstream PR → local source proof | Mutable PR refs are reduced to locally verified commit/tree identities. | PR head, pinned commit, Git objects |
| Candidate → accepted bundle | Verified content enters an immutable local-only accepted namespace. | raw bytes, manifests, rooted verifier |
| Canonical JSON → derived report | Authoritative receipt fields are rendered without independent computation. | hashes, classifications, decision binding |
| Reviewed revision → receipt issuance | Human authority is limited to one revision, projection, basis, and exact post-review delta. | decision, receipt, Markdown, control files |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-01-01 | Tampering | baseline capture | high | mitigate | Exclusive canonical baseline generations; overwrite and canonical-byte regressions. | closed |
| T-01-02 | Tampering / Repudiation | delta classifier | high | mitigate | Per-commit A/M/D/T history plus staged/worktree/untracked merge and explicit classifications. | closed |
| T-01-03 | Elevation / Disclosure | filesystem guard | high | mitigate | Relative-POSIX containment, `lstat`-before-open, path-escape and special-kind rejection tests. | closed |
| T-01-04 | Tampering / Repudiation | environment decision | high | mitigate | Stable canonical field allowlist; audit-only metadata cannot alter decision bytes. | closed |
| T-01-05 | Tampering | incident clock | high | mitigate | First-trigger cumulative wall-clock state cannot reset or pause across retries or waits. | closed |
| T-01-06 | Information Disclosure | environment audit | medium | mitigate | Canonical record excludes host/path/credential data; audit metadata is separate and sanitized. | closed |
| T-01-07 | Denial of Service | unexpected dependency | low | accept | Ninety-minute cumulative ceiling bounds expansion and preserves standalone/Red outcomes. | closed |
| T-01-08 | Spoofing | PR identity | high | mitigate | Local commit/tree/type and equality-or-ancestry proof; unrelated and frozen-PR fixtures reject. | closed |
| T-01-09 | Tampering | raw/derived custody | high | mitigate | Exact Git blob bytes, independent length/hash checks, and explicit derived lineage. | closed |
| T-01-10 | Tampering / Elevation | inventory paths | high | mitigate | Unique relative paths, containment, alias/collision rejection, and adversarial inventory tests. | closed |
| T-01-11 | Tampering / Repudiation | accepted publication | high | mitigate | Verified staging, non-replacing atomic local acceptance, immutable target, and publication authority checks. | closed |
| T-01-12 | Repudiation | snapshot-manifest binding | high | mitigate | Canonical self-digest plus core/root and per-snapshot recomputation with tamper tests. | closed |
| T-01-13 | Denial of Service | construction network | low | accept | Network loss may block refresh but cannot affect an accepted offline generation. | closed |
| T-01-14 | Spoofing / Tampering | offline verifier | high | mitigate | Accepted-state binding, rooted verifier, copied-directory no-Git/no-network replay, and tamper matrix. | closed |
| T-01-15 | Elevation / Disclosure | bundle filesystem | high | mitigate | Every verifier read applies containment and regular-file/directory policy. | closed |
| T-01-16 | Tampering / Repudiation | integrity JSON | high | mitigate | Versioned canonical receipt, non-cyclic self-hash, deterministic validation and rendering. | closed |
| T-01-17 | Tampering / Repudiation | Markdown report | medium | mitigate | JSON-only renderer; exact rerender comparison; Markdown failure cannot change JSON authority. | closed |
| T-01-18 | Tampering | reviewer override | high | mitigate | Active finalization requires schema-4 pass, exact decision hash/basis/projection, clean current boundary, and post-review delta gate. | closed |
| T-01-19 | Denial of Service | Markdown generation | low | accept | JSON remains authoritative while an incomplete reviewer package stays ineligible. | closed |
| T-01-20 | Tampering / Repudiation | committed history | high | mitigate | Full descendant commit walk retains NUL-safe per-commit A/M/D/T events, including add/delete and revert histories. | closed |
| T-01-21 | Tampering | history/live merge | high | mitigate | Canonical path keying retains all committed and live sources without blocker-count dilution. | closed |
| T-01-22 | Spoofing | reviewed revision | high | mitigate | Full immutable commit ID and baseline-ancestor proof; symbolic, missing, and unrelated revisions reject. | closed |
| T-01-23 | Tampering | restart artifacts | high | mitigate | Canonical v5 restart binds predecessor, allowlist, incident receipt, reason, and reviewed revision. | closed |
| T-01-24 | Tampering | `.DS_Store` policy | medium | mitigate | Exact-basename diagnostic remains visible, non-attributed, and nonblocking; ordinary files do not receive the exception. | closed |
| T-01-25 | Tampering / Elevation | accepted bundle during reissue | high | mitigate | v7 re-verifies unchanged accepted identity; copied offline replay passes; external publication remains false. | closed |
| T-01-26 | Repudiation | receipt and downstream reports | high | mitigate | Clean code review, authorized v7 schema-4 receipt, canonical Markdown, security gate, and mandatory independent phase re-verification. | closed |
| T-01-SC | Tampering | package installation | low | accept | Phase uses Python standard library and existing Git CLI; no npm, pip, or cargo install occurs. | closed |

*Status: open · closed · open — below high threshold (non-blocking)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01-01 | T-01-07 | The cumulative ceiling converts unexpected setup dependency into a bounded documented failure rather than weakening evidence. | Phase 01 plan | 2026-07-31 |
| AR-01-02 | T-01-13 | Refresh can wait for network recovery; accepted generations remain fully offline-verifiable. | Phase 01 plan | 2026-07-31 |
| AR-01-03 | T-01-19 | A Markdown failure leaves canonical JSON intact and blocks reviewer-package completion. | Phase 01 plan | 2026-07-31 |
| AR-01-04 | T-01-SC | No package-manager operation or new third-party dependency exists in Phase 01. | Phase 01 plan | 2026-07-31 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-07-31 | 27 | 27 | 0 | Codex / GSD ASVS L1 |
| 2026-07-31 | 10 gap-closure controls | 10 | 0 | Codex / GSD ASVS L1 re-audit |

### Plans 01-06/01-07 gap-closure re-audit

**Verdict:** SECURED. **ASVS level:** 1. **Threats open:** 0.

| Control | Independent evidence | Status |
|---|---|---|
| Exact fixture-set drift | Fixed registry and embedded bidirectional registry/core/raw comparison require exactly 11 fixtures and 28 raw files. | closed |
| Raw-byte substitution | Pinned Git blob length/SHA checks and standalone raw-custody hashing reject drift. | closed |
| Path escape / special files | POSIX containment, no-follow reads, and regular-file policy remain enforced. | closed |
| Concurrent overwrite | Candidate and accepted publication use native atomic no-replace operations; injected empty/nonempty targets are rejected and preserved; unavailable primitives fail `ATOMIC_NO_REPLACE_UNAVAILABLE` without fallback or staging leak. | closed |
| Stale/fake acceptance authority | Public API loads canonical v7 lineage internally and checks the current boundary through resolved `HEAD`; fake basis and committed/live delta bypasses reject before target creation. | closed |
| Candidate/accepted confusion | Candidate stays ineligible; accepted verifier requires accepted status, downstream eligibility, offline replay proof, and publication false. | closed |
| Registry-pin substitution | Active Phase 2 authority binds the v2 generation/root/manifest/registry/commit/tree and exact 11/28 counts. | closed |
| Local versus external publication | Decisions, manifests, receipts, revocation, and authority retain `external_publication_authorized:false`. | closed |
| Offline verifier dependency | Copied v2 accepted bundle verifies using the canonical CPython with Git unavailable and no repository modules. | closed |
| Historical mutation | The no-replace fix changes no generation or receipt bytes; prior v1/v8 and historical v2 manifest hashes remain intact. | closed |

Re-audit validation: 92 stdlib tests passed; deterministic candidate and accepted race
probes rejected; target-specific `os.replace` guard observed zero calls; v7 boundary reported
zero blockers; active v2 authority validated; copied v2 replay passed with
`PATH=/nonexistent`.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-07-31
