# Phase 2: Deterministic Measurement Spine - Context

**Gathered:** 2026-07-31
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 delivers a dependency-light, deterministic measurement spine for the complete frozen PR #2164 fixture universe. It adapts all 11 fixtures into a versioned canonical adjudication domain, strictly validates predictions without silent repair, scores golden and adversarial inputs with stable structured diagnostics, and produces the hash-bound H1 source/gold review packet. This phase does not implement DelegationFrame extraction, data preregistration, retrieval, prompts, model calls, metamorphic evaluation, or final feasibility claims.

</domain>

<decisions>
## Implementation Decisions

### Adapter Normalization Boundary

- **D-01:** The scorer consumes versioned canonical adapter records only. Authoritative fixture bytes remain unchanged; each canonical record binds the adapter version, raw SHA-256 identities, original fields and values, transformation rule identity, and normalized fields and values.
- **D-02:** Any disagreement among fixture directory identity, registry identity, `expected.yaml`, `gold.yaml`, or other score-bearing sources blocks the complete adapter batch. The failed attempt records a stable diagnostic code, fixture ID, conflicting field, expected and observed values, and source hashes. It emits no score-eligible canonical records and measurement does not start.
- **D-03:** Only an explicit allowlist of fields may affect scoring: case identity, positive/negative/candidate category, `expect_extract`, normalized expected parameter count and names, and evidence requirements. Other upstream fields remain reviewable provenance and cannot alter disposition, denominators, or pass criteria.
- **D-04:** A transformation-rule correction creates a new immutable adapter version and rule hash, then symmetrically rebuilds and retests all 11 fixtures. Old records are never overwritten, adapter versions are never mixed within one measurement run, and every downstream artifact binds one exact adapter version.

### Compatibility Ingress and Strict Validation

- **D-05:** `reject` may normalize to `classify_out` only at an explicitly declared legacy-schema ingress. The raw input and before/after values remain preserved under a stable normalization diagnostic. The current canonical schema rejects `reject` as invalid.
- **D-06:** The complete score-bearing payload uses closed schemas at every level, including top-level, adjudication, and evidence-span objects. Extra provenance may appear only in a separate versioned envelope that cannot affect scoring.
- **D-07:** Canonical no-finding predictions must explicitly encode `surfaced: false`, `parameter_status: null`, `proposed_name: null`, and `evidence_spans: []`. Missing fields are invalid; the parser never supplies default nulls or empty containers.
- **D-08:** The parser never trims, case-folds, fuzzily matches, or rewrites semantic values or evidence. Evidence must match authoritative raw source text. NFC normalization applies only to the post-validation canonical report projection, while raw input remains separately preserved.

### Failure Collection and Exit Behavior

- **D-09:** Before scoring, a side-effect-free preflight validates every fixture and prediction and collects the complete diagnostic set in deterministic order. Any blocking error invalidates the whole batch, yields a nonzero exit, and prevents partial pass rates or formal metrics from being published.
- **D-10:** `ACCEPTED_PARAMETER_NAME_MISSING` remains an identity warning only. A structurally valid run may finish with exit zero and status `completed_with_warnings`; surfacing and disposition stay unchanged, identity coverage decreases independently, and the H1 packet exposes the warning prominently.
- **D-11:** Every invocation becomes an immutable attempt containing input hashes, adapter version, raw predictions, parsed results, separate diagnostics, and terminal status. Failed attempts remain auditable but never become measurement authority. Only attempts that pass preflight may emit canonical metrics and reports.
- **D-12:** Targeted case runs are permitted only as `diagnostic_only` development artifacts. Every formal attempt and H1 report runs all 11 fixtures under one adapter, schema, and prediction-set identity. Formal evidence never splices results from different attempts.

### H1 Review Disposition

- **D-13:** H1 has exactly three formal dispositions: `approved`, `disputed`, and `incomplete`. Only an explicit human `approved` decision permits Phase 3. `disputed` identifies rejected gold or adapter semantics; `incomplete` identifies missing material or signature. Machines cannot override either blocking state.
- **D-14:** The reviewer signs each fixture and its key semantics before issuing the aggregate disposition: category, `expect_extract`, normalized parameter count and names, candidate surfaced-then-`classify_out` semantics, and adapter lineage. Any disputed item makes the overall decision `disputed`.
- **D-15:** The formal golden attempt contains no unexpected warning or error. Adversarial tests may intentionally trigger diagnostics and pass only when code and structured fields exactly match the test oracle. Expected adversarial diagnostics do not block H1; unexpected golden diagnostics do.
- **D-16:** H1 approval is an immutable decision bound to the accepted fixture generation/root, fixture registry, adapter version and rule hash, canonical schema, golden prediction set, formal attempt, diagnostics, and H1 packet. Any bound change invalidates approval and requires a new version and review. H1 authorizes local Phase 3 progression only and never authorizes external publication.

### the agent's Discretion

The planner may choose internal Python module and class names, schema file decomposition, CLI command names, attempt-directory naming, and additional stable diagnostic codes. Those choices must preserve the frozen adapter, validation, attempt, canonicalization, and H1 contracts above. The planner may reuse the existing stdlib canonicalization and filesystem-verification modules or isolate measurement equivalents, provided Phase 1 custody artifacts are not weakened or retroactively modified.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Frozen Product and Measurement Contract

- `.planning/PROJECT.md` — Defines the evaluation-first objective, isolation boundary, active measurement requirements, prohibited scope, and local human authority.
- `.planning/REQUIREMENTS.md` — Defines TS-03, TS-04, and TS-05 plus the every-path acceptance criteria and exact Phase 2 traceability.
- `.planning/ROADMAP.md` — Defines the Phase 2 goal, four planned capability increments, success criteria, and H1 boundary.
- `/Users/zhdeng/Downloads/LFX_RISCV_SpecChoice_v1.3.2_frozen_execution_baseline.md` sections 6.1-6.3, 11.3, 14-16 — External frozen execution contract for PR #2164 semantics, canonical adjudication, required diagnostics, parsing, deterministic artifacts, and the Day 1 measurement spine.

### Accepted Fixture Authority

- `experiments/specchoice-v1.3.2/config/fixture-registry-pr2164-v1.json` — Finite, sorted 11-fixture/28-file registry and authoritative path/hash inventory.
- `experiments/specchoice-v1.3.2/bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2/snapshot-manifest.json` — Active accepted, downstream-eligible, externally unpublished fixture generation and root identity.
- `.planning/phases/01-isolated-evidence-boundary-and-source-integrity/01-CONTEXT.md` — Locks immutable raw-byte custody, offline replay, derived-artifact lineage, canonical receipt, and fail-closed filesystem boundaries.
- `.planning/phases/01-isolated-evidence-boundary-and-source-integrity/01-VERIFICATION.md` — Verifies current 11-directory/28-file closure, bidirectional registry/core/raw enforcement, local Git proof, downstream eligibility, and local-only publication state.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `experiments/specchoice-v1.3.2/src/specchoice_evidence/canonical.py`: Existing canonical JSON and hashing primitives suitable for deterministic identities or as a reference contract.
- `experiments/specchoice-v1.3.2/src/specchoice_evidence/filesystem.py`: Existing fail-closed path and authoritative-file validation patterns.
- `experiments/specchoice-v1.3.2/bundles/accepted/source-contract-v3-pr2164-fixture-closure-22e84458-verifier-rooted-v2/verifier/`: Bundle-local stdlib verifier that already proves fixture registry/core/raw closure offline.
- `experiments/specchoice-v1.3.2/tests/`: Existing stdlib `unittest` organization and negative-test conventions for exact codes and boundary behavior.

### Established Patterns

- Immutable generations and attempts replace in-place mutation; historical failures remain evidence but are never promoted implicitly.
- Canonical JSON is authoritative, while human-readable Markdown is a deterministic projection rather than a second source of truth.
- Raw authoritative bytes and normalized/parsed derivatives are separate artifacts connected by one-way hash lineage.
- The project is standalone-first and isolated under `experiments/specchoice-v1.3.2/`; no core UDB schema, generated data, or root dependency change is needed for Phase 2.

### Integration Points

- New measurement implementation belongs under `experiments/specchoice-v1.3.2/src/` with adjacent schemas/configuration and focused tests under `experiments/specchoice-v1.3.2/tests/`.
- The adapter consumes only the active accepted v2 fixture generation and `fixture-registry-pr2164-v1.json`; historical or revoked generations cannot be fallback inputs.
- H1 output must connect the canonical adapter batch, golden/adversarial attempts, diagnostic projection, reviewer packet, and immutable review decision without creating external-publication authority.

</code_context>

<specifics>
## Specific Ideas

- Treat the candidate fixture as a two-step semantic requirement: it must be surfaced and then classified out; it is neither a negative nor an unresolved discovery finding.
- Keep identity, surfacing, and disposition results independent. A missing accepted parameter name affects identity coverage only.
- Use complete-batch validation and formal 11-case reruns so a convenient subset can never become the Phase 2 authority.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 2 scope.

</deferred>

---

*Phase: 2-deterministic-measurement-spine*
*Context gathered: 2026-07-31*
