# Walking Skeleton — SpecChoice v1.3.2 Source Custody

**Phase:** 1
**Generated:** 2026-07-30

## Capability Proven End-to-End

An operator can capture an immutable repository baseline, attempt one exact Git-proven
source-bundle generation, and give a reviewer a canonical pass/block receipt that can be
replayed from an accepted bundle using Python standard library only.

The currently frozen source contract exercises the rejected path: PR #2192 pin
`4bdaa4be1a404f78ff5b2841edd535afb637566b` is not reachable from current canonical PR
head `f44a21144f603ce5d60b9b3af5605e820597b320`. The skeleton must preserve the frozen pin,
emit `PR_PIN_NOT_REACHABLE`, publish no accepted generation/root, and stop at the reviewer
source decision. A synthetic disposable-Git fixture proves the accepted/offline path
without misrepresenting the real six-snapshot state.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Runtime | CPython 3.12+-compatible standard library | Verification and downstream replay remain dependency-light and offline |
| Construction authority | Git CLI over the canonical PR head ref | Commit/tree/object/ancestry evidence is authoritative; hosting metadata is supplementary |
| Data layer | Versioned canonical JSON plus immutable regular-file directories | No database is needed; content identity and offline inspection are explicit |
| Source authority | Exact raw Git object bytes | Canonical/parsed views remain derived children and cannot replace upstream bytes |
| Manifest binding | Hashable `content-manifest-core.json`, then logical root, then canonical `snapshot-manifest.json` | Every D-05 snapshot records generation/root/core-manifest identity without a circular hash |
| Publication | Validated sibling staging plus non-replacing atomic rename | A partial, interrupted, or concurrent build cannot become an accepted generation |
| Verification | Bundle-local stdlib verifier rooted with the generation | Bundle alone is sufficient; no network, `.git`, or construction module is required |
| Human control | Source-publication and final boundary checkpoints | Missing path inventory and PR #2192 mismatch cannot be converted into assumptions |
| Auth | Not applicable | Local batch CLI has no account/user boundary |
| External API | None at runtime | Git transport is construction-only; optional hosting metadata is not a runtime/API dependency |
| Deployment | None | This is a local evidence CLI and immutable artifact contract, not a service |
| Directory layout | `experiments/specchoice-v1.3.2/{src,config,baselines,bundles,receipts,audit,tests,notes}` | All implementation stays outside core UDB schema/generated/dependency state |

## Stack Touched in Phase 1

- [ ] First-write phase-start baseline and exact boundary allowlist (Plan 01).
- [ ] Canonical standalone-first environment decision plus one-way audit receipt (Plan 02).
- [ ] `capture-baseline`, `check-boundary`, `record-environment`, `build`, `verify`, and
      `receipt` CLI paths.
- [ ] Construction-only Git proof over six frozen PR identities.
- [ ] Raw/derived core projection, packaging-independent logical root, and final D-05
      snapshot-manifest binding.
- [ ] Immutable accepted/rejected generation state machine with interruption/concurrency tests.
- [ ] Bundle-local offline verifier requiring Python standard library only.
- [ ] Canonical `integrity-receipt.json` and JSON-only `integrity-receipt.md`.
- [ ] Reviewer source/publication and final boundary decisions.

There is intentionally no UI route, database read/write, authentication flow, network
service, or deployment target. The UI planning gate was explicitly skipped by the user,
and these layers are outside TS-01/TS-02.

## End-to-End Paths

### Eligible accepted path

1. Capture/hash the baseline before the first implementation file.
2. Reviewer approves the exact allowlist before GSD state/control updates.
3. Fetch the canonical PR refs; prove every pin's commit/tree and equality/ancestry.
4. Reviewer approves an exact non-empty consumed-file path/role inventory and any versioned
   source-contract correction.
5. Copy exact raw bytes and create explicit derived lineage; hash
   `content-manifest-core.json`, then compute the logical root.
6. Write canonical `snapshot-manifest.json`; every snapshot repeats the exact
   generation/root/core-manifest triple and the final binding has a non-cyclic self-digest.
7. Embed and run the bundle-local offline verifier from a copied, no-Git/no-network tree,
   including top-level and per-snapshot binding recomputation.
8. Atomically expose one new accepted generation; never overwrite an existing one.
9. Recompute the boundary and source chain into canonical JSON, derive Markdown, and obtain
   final reviewer approval before Phase 1 control state advances.

### Current rejected path

1. Complete baseline/environment checks.
2. Fetch/verify the canonical PR #2192 head and frozen commit/tree objects.
3. Observe failed frozen-pin ancestry and emit deterministic `PR_PIN_NOT_REACHABLE`.
4. Preserve rejected attempt/audit evidence with no accepted generation ID or usable root.
5. Emit a canonical blocking integrity receipt and fact-identical Markdown.
6. Reviewer records a Red/blocker disposition or authorizes a new versioned source contract;
   the original config/rejection remains immutable.

## Observability and Receipts

| Artifact | Authority | Included in reproducible identity |
|---|---|---|
| `baselines/phase-start-v1.json` | Canonical start state | Yes, by SHA-256 reference |
| `receipts/environment-decision.json` | Canonical capability/policy decision | Yes |
| `audit/environment/*.json` | Field audit evidence | No; points to canonical decision |
| `bundles/rejected/*/attempt-receipt.json` | Canonical failed-attempt evidence | Referenced by failing receipt, never accepted identity |
| `bundles/accepted/<generation>/content-manifest-core.json` | Hashable stable source/inventory projection | Yes, as `manifest_sha256` in the logical-root preimage |
| `bundles/accepted/<generation>/snapshot-manifest.json` | Sole D-05 final two-level manifest | Yes; every snapshot binds generation/root/core-manifest, carries its full consumed-file inventory, projects back to the core bytes, and self-hashes outside the root preimage |
| `receipts/integrity-receipt.json` | Authoritative Phase 1 gate | Yes |
| `receipts/integrity-receipt.md` | Deterministic JSON-only reviewer view | No independent facts |
| `receipts/reviewer-boundary-decision.json` | Human accept/dispute/block record | Referenced by final receipt |

## Spec-less Edge Coverage

No SPEC-supplied Edge Coverage existed. Every deterministic probe candidate is therefore
resolved here as an explicit acceptance truth with a mechanical backstop.

| Candidate | Resolution statement | Verification backstop | Plan/task |
|---|---|---|---|
| TS-01 boundary | Only the exact experiment root and enumerated control files are allowed; sibling-prefix paths remain outside | `tests.test_filesystem_boundary` prefix/pre-existing/delta cases | 01-01 Task 1 |
| TS-01 precision | Byte lengths are non-negative JSON integers; SHA-256 is lowercase 64-hex; raw lengths/digests use exact bytes and never floats | `tests.test_canonical` plus raw-byte fixtures | 01-01 Task 1; 01-03 Task 3 |
| TS-02 adjacency | Duplicate snapshot/upstream/local identities, path aliases, and file/directory collisions reject | `tests.test_bundle_verifier` inventory-collision cases | 01-03 Task 3 |
| TS-02 empty | Null/empty required snapshot or consumed-file arrays reject; one entry is valid; empty derived lists are valid | `tests.test_bundle_verifier` null/empty/single cases | 01-03 Task 3 |
| TS-02 ordering | Snapshot, inventory, artifact, diagnostic, and boundary arrays have documented stable tuple orders | shuffled-input golden tests in `test_canonical`, `test_bundle_verifier`, and `test_receipts` | 01-01 through 01-04 |
| TS-02 concurrency | At most one same-generation publisher succeeds; interruption/staging never becomes accepted and existing generations never change | concurrent/interrupted publication fixtures in `tests.test_bundle_verifier` | 01-03 Task 3 |

Coverage equality: `6 candidates = 6 resolved + 0 dismissed + 0 unresolved`.

## Spec-less Prohibition Recall and Precision

Stage 1 asked, for each requirement: “What could this feature silently become that the
author would not want, but the specification does not forbid?” Stage 2 removed routine
engineering items, breadcrumbed security canon, and checked each remainder against the
locked context. All bespoke-looking candidates were already explicit prohibitions, so no
new descriptor-less prohibition was minted and all plans correctly carry
`must_haves.prohibitions: []`.

| Requirement | Recall candidate | Precision disposition |
|---|---|---|
| TS-01 | Modify/delete an unrelated path to obtain a clean receipt | Already explicit D-14/D-15 |
| TS-01 | Hide or attribute pre-existing `.DS_Store` files to the phase | Already explicit D-14 |
| TS-01 | Probe/install the full UDB environment merely for evidence | Already explicit D-09/D-10 |
| TS-01 | Put timestamps, host/user paths, raw errors, or credentials in canonical identity | Already explicit D-12/D-13 |
| TS-01 | Follow a traversal/symlink/special file outside the boundary | Security canon; breadcrumb to `$gsd-secure-phase`, with Plan 01 mitigations |
| TS-02 | Replace a frozen pin with the mutable current PR head | Already explicit D-06/D-07 |
| TS-02 | Normalize source text and call it authoritative raw content | Already explicit D-04 |
| TS-02 | Treat a rejected/partial generation as accepted | Already explicit D-03/D-07 |
| TS-02 | Use an archive hash as the logical bundle identity | Already explicit D-08 |
| TS-02 | Require network or local Git objects for downstream verification | Already explicit D-02/D-09 |
| TS-02 | Vendor an entire snapshot instead of exact consumed files | Already explicit D-01 |

No-silent-drop equality:
`11 raw = 10 source-explicit + 1 canon breadcrumb + 0 kept bespoke + 0 dismissed + 0 unresolved`.
Prohibition coverage is `{applicable: 0, resolved: 0, unresolved: 0,
byVerification: {test: 0, judgment: 0}}`.

## Multi-Source Coverage Audit

| Source | ID | Feature/requirement | Plan | Status | Notes |
|---|---|---|---|---|---|
| GOAL | — | Self-contained boundary with independently verifiable public identity | 01-01..04 | COVERED | Full CLI custody chain |
| REQ | TS-01 | Dependency-light isolated experiment boundary | 01-01, 01-02, 01-04 | COVERED | Baseline, environment, guard, receipt |
| REQ | TS-02 | Frozen PR manifest and stable consumed-file hashes | 01-03, 01-04 | COVERED | Git proof, bundle, offline replay |
| RESEARCH | — | Standalone stdlib runtime and Git-only construction | 01-01..04 | COVERED | No installs/full UDB/API |
| RESEARCH | — | Immutable phase-start delta and exact allowlist | 01-01, 01-04 | COVERED | First-write baseline and final receipt |
| RESEARCH | — | `lstat` containment and regular-file policy | 01-01, 01-04 | COVERED | Pre-open checks and offline reuse |
| RESEARCH | — | Local Git commit/tree/ancestry authority | 01-03 | COVERED | Disposable Git proof |
| RESEARCH | — | Non-cyclic manifest/root projections | 01-03, 01-04 | COVERED | Core manifest, root, final snapshot binding |
| RESEARCH | — | Separate accepted/rejected atomic publication | 01-03, 01-04 | COVERED | Staging, reviewer gate, offline gate |
| RESEARCH | — | Current #2192 rejection and human decision | 01-03, 01-04 | COVERED | Never silently repinned |
| RESEARCH | — | Exact consumed inventory is not frozen | 01-03 | COVERED | Explicit blocking checkpoint, not assumption |
| RESEARCH | — | Stdlib `unittest` validation architecture | 01-01..04 | COVERED | No pytest/root dependency |
| RESEARCH | — | Canonical JSON authority and Markdown derivative | 01-04 | COVERED | JSON-only renderer |
| CONTEXT | D-01 | Hybrid exact-consumed-file bundle | 01-03 | COVERED | Reviewer-owned request inventory |
| CONTEXT | D-02 | Bundle-alone offline replay | 01-04 | COVERED | Embedded verifier |
| CONTEXT | D-03 | Immutable content-addressed generations | 01-03, 01-04 | COVERED | Non-replacing publication |
| CONTEXT | D-04 | Raw authority plus explicit derived views | 01-01, 01-03 | COVERED | Separate code paths/lineage |
| CONTEXT | D-05 | Two-level manifest and final snapshot identity | 01-03, 01-04 | COVERED | Core projection then per-snapshot generation/root/manifest binding |
| CONTEXT | D-06 | Git-native PR reachability | 01-03 | COVERED | Authoritative object proof |
| CONTEXT | D-07 | Fail closed/no accepted failure identity | 01-03, 01-04 | COVERED | #2192 real rejected path |
| CONTEXT | D-08 | Canonical logical content root | 01-03, 01-04 | COVERED | Packaging-independent recomputation |
| CONTEXT | D-09 | Standalone-first | 01-02, 01-04 | COVERED | Environment and construction/replay split |
| CONTEXT | D-10 | Proactive environment decision | 01-02 | COVERED | No fallback mislabel |
| CONTEXT | D-11 | Cumulative 90-minute incident | 01-02 | COVERED | No pause/reset |
| CONTEXT | D-12 | Canonical stable environment identity | 01-02 | COVERED | Stable field allowlist |
| CONTEXT | D-13 | Separate non-canonical audit | 01-02 | COVERED | One-way reference |
| CONTEXT | D-14 | Phase-start delta and classifications | 01-01, 01-04 | COVERED | Visible pre-existing files |
| CONTEXT | D-15 | Immutable canonical hashed baseline | 01-01 | COVERED | First write/restart rule |
| CONTEXT | D-16 | Regular files/directories only | 01-01, 01-03, 01-04 | COVERED | Applied at every read/publication |
| CONTEXT | D-17 | Canonical JSON gate | 01-04 | COVERED | Self-hashed projection |
| CONTEXT | D-18 | Derived Markdown | 01-04 | COVERED | JSON-only, incomplete-on-failure |

Audit result: all GOAL, REQ, RESEARCH constraints/features, and D-01 through D-18 are
covered. There are no deferred Phase 1 items and no source-audit gap.

## Out of Scope (Deferred to Later Slices)

- PR #2164 fixture adapter, adjudication schema, measurement, or scoring.
- Data/pair curation, family/split/relevance registries, and metamorphic directions.
- Retrieval, prompt assembly, model configuration, external model calls, or run evidence.
- UDB resolution, Ruby/IDL/C++/Node tooling, `bin/setup`, `bin/doctor`, core schemas, and
  generated architecture data.
- Production API/service, database, UI, authentication, or deployment.
- Optional discovery, packaging, public communication, Issue, comment, or pull request.

## Subsequent Slice Plan

- Phase 2 consumes one exact accepted generation and proves deterministic fixture scoring.
- Phase 3 adds human-reviewed data preregistration without changing source custody.
- Phase 4 roots prompts/retrieval/branch freeze in the same accepted generation identity.
- Phases 5–7 record the consumed generation/root/manifest in every downstream artifact.
