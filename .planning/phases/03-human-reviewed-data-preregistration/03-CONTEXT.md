# Phase 3: Human-Reviewed Data Preregistration - Context

**Gathered:** 2026-08-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 delivers an immutable, human-reviewed data preregistration package before retrieval ranks or model outputs can influence semantic decisions. It freezes a provenance-rich prototype pair bank, held-out strict/auxiliary assignments, a versioned primary-family registry, complete strict-core relevance judgments, the four required metamorphic directions, deterministic leakage/provenance validation, and an H2 packet that binds every human disposition and audited branch-eligibility count. It does not implement retrieval ranking, prompt assembly, model calls, final Green/Yellow/Red execution authorization, aggregate experiment metrics, discovery, or external publication.

Phase 3 may be planned only against the exact locally approved Phase 2/H1 authority. Phase 2 lifecycle state and its currently untracked successor evidence must be closed and made available before Phase 3 execution is treated as authorized.

</domain>

<decisions>
## Implementation Decisions

### Data Admission and Dispute Handling

- **D-01:** H2 may approve the stable subset. Every candidate receives an explicit human `approved`, `disputed`, or `excluded` disposition. Only approved items enter eligibility counts and the frozen corpus; disputed and excluded items remain auditable but quarantined. Modifying an item creates a new version and requires review again.
- **D-02:** Machine structural admission precedes human semantic review. Provenance, exact evidence spans, required fields, registered primary family, version compatibility, and fail-closed filesystem boundaries must pass before a candidate reaches semantic review. Structural failures are `invalid`; semantic disagreements are `disputed`. Neither participates in eligibility counts.
- **D-03:** An authoritative `example_id` or source span may belong to at most one count-eligible approved prototype pair. Cross-references may be retained for audit, but reused or lightly varied material cannot increase pair counts.
- **D-04:** Freeze and hash the complete candidate inventory before human review begins. Invalid, disputed, and excluded candidates are not replaced to reach Green or Yellow thresholds. An insufficient approved subset is preserved as auditable Yellow or Red evidence without quota filling.

### Primary-Family and Strict/Auxiliary Assignment

- **D-05:** Use a closed, definition-first family registry. Human reviewers approve every family's semantic definition, inclusion criteria, and exclusion criteria before any example or case is assigned. Each eligible item has exactly one `primary_family`; the registry cannot expand or change during review.
- **D-06:** If reviewers cannot assign one unambiguous primary family, mark the item `disputed` and exclude it from prototype, strict-core, auxiliary, and threshold counts. Overlapping descriptive concepts may remain as `secondary_tags`; an `ambiguous` primary family is not permitted as a bypass.
- **D-07:** Split membership is deterministic after the prototype bank is frozen. Held-out cases that are both example-disjoint and primary-family-disjoint from prototypes are strict-core candidates. Example-disjoint cases with primary-family overlap are auxiliary only. Human review approves semantics but cannot move cases between splits based on expected usefulness or results.
- **D-08:** Every item, pair, split assignment, and relevance judgment binds the family-registry version and content hash. Any change to a family definition, membership, or primary assignment creates a new registry version and invalidates the complete dependent approval chain for full validation and human review again.

### Contrastive Pair Review Standard

- **D-09:** An approved pair is a controlled minimal contrast. Its two sides share the technical object, normative context, and all material semantic structure except one discriminating axis or an explicitly inseparable coupled set of axes. Any additional factor that could independently explain the final-disposition difference makes the pair disputed.
- **D-10:** Use explicit claim-to-span mappings. Every frame axis, final status, and discriminating-axis rationale on each side references at least one exact, non-empty authoritative source span. One span may support multiple claims, but every claim-to-span relationship is declared separately.
- **D-11:** Review both sides independently before reviewing the pair relationship. Each side's frame, final status, evidence, and provenance must be approved before shared structure and discriminating axes are assessed. Rejecting the relationship cannot rewrite previously approved item semantics.
- **D-12:** Every pair is directed and freezes its positive side, contrast side, expected frame/status delta, and presentation order. Swapping sides creates a new pair version and never counts as an additional qualifying pair.

### Relevance, Metamorphic, and H2 Approval Packet

- **D-13:** The relevance registry covers every strict-core case. Each case carries either an approved, non-empty `relevant_pair_ids` list or an explicit `no_relevant_pair` disposition with rationale; silent missing judgments are invalid. `PairHit@K` includes only cases with at least one preregistered relevant pair. Auxiliary relevance is registered and reported separately.
- **D-14:** Before retrieval, freeze each target case's choice object and decisive axes. A prototype pair is relevant only when it shares the key structure and exposes at least one preregistered decisive axis. Multiple pairs may be relevant, but relevance judgments do not preregister a ranking among them.
- **D-15:** Prefer accepted authoritative passages for both sides of each required metamorphic pair. If a true minimal contrast is unavailable, a clearly marked human-authored synthetic variant is allowed only with an exact edit record, expected semantic delta, and explicit human approval. Synthetic text cannot masquerade as specification text, enter prototype/held-out counts, or be generated by a model.
- **D-16:** H2 approves the exact data root, per-item decisions, quarantined disputes, and audited counts as trustworthy. Deterministic threshold evaluation reports exactly one of `green_eligible`, `yellow_eligible`, or `red_required`; Phase 4 retains authority for the final human-signed Green/Yellow/Red execution decision.

### the agent's Discretion

The planner may choose internal module names, schema decomposition, CLI command names, immutable generation-directory names, review-packet layout, and additional stable structural diagnostic codes. Those choices must reuse the existing canonical JSON, hashing, descriptor-bound filesystem, strict parsing, immutable-attempt, and human-decision patterns without weakening the decisions above. The planner may choose a YAML authoring format with canonical JSON projections, or canonical JSON directly, provided one representation is unambiguously authoritative and byte-stable.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Frozen Project and Data Contract

- `.planning/PROJECT.md` — Defines the evaluation-first scope, strict/auxiliary separation, human authority, preregistration boundary, and prohibited model-driven semantic changes.
- `.planning/REQUIREMENTS.md` — Defines Phase 3 requirements TS-08, TS-09, and H2-01 plus Green, Yellow, Red, every-path, and human-control acceptance criteria.
- `.planning/ROADMAP.md` — Defines Phase 3's goal, four capability increments, success criteria, H2 checkpoint, and dependency on Phase 2.
- `../../Downloads/LFX_RISCV_SpecChoice_v1.3.2_frozen_execution_baseline.md` §§8, 9, 12, 15, 17, 18.3, 24, 25 — Defines prototype-pair fields, family/split/relevance registries, four metamorphic directions, fallback thresholds, validation instructions, and frozen-input change control.

### Accepted Source and Semantic Authority

- `.planning/phases/01-isolated-evidence-boundary-and-source-integrity/01-CONTEXT.md` — Locks offline accepted-bundle custody, raw-byte authority, derived lineage, immutable generations, and fail-closed filesystem rules inherited by all Phase 3 data.
- `.planning/phases/02-deterministic-measurement-spine/02-CONTEXT.md` — Locks canonical adjudication, evidence occurrence preservation, versioned normalization, immutable attempts, and the H1 semantic review boundary.
- `.planning/phases/02-deterministic-measurement-spine/02-VERIFICATION-02-22.md` — Latest local successor verification projection for the exact approved Phase 2 evidence chain; must be lifecycle-closed before Phase 3 execution.
- `.planning/phases/02-deterministic-measurement-spine/02-REVIEW-02-22.md` — Latest local successor review projection and exact Phase 2 source-identity bindings.
- `experiments/specchoice-v1.3.2/phase2/source-authority.json` — Active accepted source authority that downstream data must bind rather than rediscover or silently replace.
- `experiments/specchoice-v1.3.2/reviews/h1-source-gold-decision-v6.json` — Human-approved eleven-fixture semantics and exact decision/readiness/packet hashes; authorizes local Phase 3 progression only.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `experiments/specchoice-v1.3.2/src/specchoice_evidence/canonical.py`: Existing standard-library canonical JSON and SHA-256 primitives for stable registry, manifest, packet, and decision identities.
- `experiments/specchoice-v1.3.2/src/specchoice_evidence/filesystem.py`: Existing descriptor-bound, fail-closed authoritative-leaf and filesystem-kind validation for provenance material.
- `experiments/specchoice-v1.3.2/src/specchoice_measurement/strict_json.py`: Existing closed-schema and duplicate-key rejection patterns suitable for Phase 3 machine admission.
- `experiments/specchoice-v1.3.2/src/specchoice_measurement/diagnostics.py`: Existing stable structured diagnostic representation and deterministic ordering conventions.
- `experiments/specchoice-v1.3.2/src/specchoice_measurement/h1.py`: Existing readiness-packet and human-decision validation pattern that can be reused structurally for H2 without copying H1 semantics.
- `experiments/specchoice-v1.3.2/src/specchoice_measurement/final_reports.py`: Existing canonical-evidence-to-deterministic-Markdown projection pattern for reviewer-facing packets.

### Established Patterns

- Immutable candidate, accepted, attempt, readiness, and decision artifacts replace in-place mutation; historical failures remain evidence but never become authority implicitly.
- Raw authoritative source bytes, parsed semantic records, canonical machine evidence, and human-readable projections are separate one-way layers connected by exact hashes.
- Human decisions bind a closed packet/readiness identity, are local-only unless separately authorized, and cannot be inferred from machine readiness.
- Complete-batch preflight emits deterministic diagnostics and withholds score- or eligibility-bearing outputs on structural failure.
- The prototype remains standalone-first under `experiments/specchoice-v1.3.2/` and does not require core UDB schema or generated-data changes.

### Integration Points

- Phase 3 data, registries, schemas, validators, tests, review packets, and decisions belong under `experiments/specchoice-v1.3.2/` using the frozen `data/`, `config/`, `src/`, `tests/`, `reports/`, `reviews/`, and `receipts/` boundaries.
- Phase 3 must consume the exact active Phase 2 source authority and approved H1 decision; it must not fall back to historical candidate or accepted generations.
- The H2 packet feeds Phase 4 only through a content-bound approved data root plus deterministic eligibility status. It must not create retrieval ranks, model evidence, or final execution authority.

</code_context>

<specifics>
## Specific Ideas

- Preserve four distinct non-eligible states in the reviewer packet: structurally `invalid`, semantically `disputed`, human `excluded`, and approved-but-auxiliary. Never collapse them into one rejection count.
- Show pair count and unique example/source-span count together so the no-reuse rule remains independently auditable.
- Keep `no_relevant_pair` explicit rather than treating absence as a judgment, while excluding those cases from the `PairHit@K` denominator.
- Report eligibility as a deterministic consequence of approved counts, never as a machine recommendation that can override human dispositions.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 3 scope.

</deferred>

---

*Phase: 3-human-reviewed-data-preregistration*
*Context gathered: 2026-08-03*
