# Phase 4: Offline Treatments, Retrieval, and Branch Freeze - Context

**Gathered:** 2026-08-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 delivers a replayable, offline-only A/B/C treatment contract, a strict three-axis DelegationFrame contract, deterministic complete-pair TF-IDF/cosine retrieval contract verification, byte-stable prompt/response fixtures, and an immutable H3 branch freeze. The accepted Phase 3 authority is `red_required` with one qualifying natural pair and zero strict cases, so Phase 4 must freeze Red with `N_strict=0` and `repeat_count=0`. It does not authorize or perform authoritative retrieval, provider selection, credentials handling, external calls, model execution, publication, data replacement, or a Green/Yellow override.

</domain>

<decisions>
## Implementation Decisions

### Red Freeze Contract

- **D-01:** H3 uses the established two-layer pattern: code produces a decision-free readiness packet, then a separate human decision binds its exact hashes. The human decision may be `approved_red`, `disputed`, or `incomplete`; it cannot override the Phase 3 `red_required` result to Green or Yellow. — **Reversibility:** one-way — once an H3 decision is signed against the immutable readiness root, changing the approved branch requires a versioned successor readiness/decision chain rather than mutation.
- **D-02:** The Red execution contract records exactly `N_strict=0` and `repeat_count=0`. It does not retain planned or nominal repeat values that could imply an executable model matrix.
- **D-03:** H3 records `h4_required=false` with reason `not_applicable_red`. No separate H4 decision or N/A artifact is created.
- **D-04:** Both `disputed` and `incomplete` fail closed and create no branch authority. If all bound inputs are unchanged, an incomplete decision may be followed by a new immutable decision against the same readiness. A disputed decision requires corrected upstream inputs, a version increment, and complete regeneration of the readiness and decision chain.

### Two-Pair Retrieval Proof

- **D-05:** Prove top-two retrieval with an isolated test-only corpus containing at least three complete pairs. The corpus exists only to verify TF-IDF, cosine ranking, target dependence, complete-pair atomicity, and deterministic tie-breaking. The authoritative Phase 3 one-pair path must fail closed rather than reuse or duplicate its pair.
- **D-06:** Test corpus content is contract-only synthetic text with no RISC-V research semantics. Every item is explicitly `test_only=true` and `count_eligible=false`; test fixtures cannot enter H2 authority, the experiment freeze root, eligibility counts, or model evidence.
- **D-07:** Retrieval query input is the frozen target source text only. Case identity, gold, DelegationFrame, primary family, decisive axes, relevance judgments, and final disposition are forbidden query inputs.
- **D-08:** With at least two distinct eligible pairs, retrieval always returns exactly two complete pairs even when one or both cosine scores are zero. It introduces no similarity threshold, exposes each score, and orders by cosine score descending then `pair_id` ascending. Fewer than two distinct pairs yields `INSUFFICIENT_RETRIEVAL_PAIRS` and no partial ranking.

### Offline Prompt Contract Fixtures

- **D-09:** Render A/B/C using a dedicated synthetic target marked `test_only=true` and `count_eligible=false`, together with the isolated test-only pair corpus. These artifacts demonstrate prompt and parser contracts only; they are not strict, auxiliary, prototype, discovery, or experiment cases.
- **D-10:** The offline bundle includes exact rendered A/B/C prompt bytes and human-authored contract responses. Every response records `origin=contract_fixture` and `model_generated=false`; contract responses cannot be admitted as raw model responses or run evidence.
- **D-11:** Prompt authority is raw UTF-8/LF text. Responses and the bundle manifest use the existing NFC-normalized, sorted-key canonical JSON and SHA-256 rules. Every prompt and response has its own hash.
- **D-12:** Structural comparison fails closed on any non-treatment difference. A omits DelegationFrame instructions and output while B includes them; B and C have the identical frame/adjudication contract; B and C differ only in fixed versus retrieved pair selection. Demonstration count, target bytes, shared guidance, decision space, evidence rules, and relevant serialization rules remain identical. No neutral-text padding is permitted.
- **D-13:** Red offline accounting records exact UTF-8 byte, Unicode code-point, and line counts plus a deterministic standard-library `offline_lexical_token_count`. Provider token fields are `not_applicable_red`; Phase 4 does not select or install a model tokenizer.

### Red Model and Retrieval Boundary

- **D-14:** Do not implement a provider/model adapter, provider SDK, HTTP client, credentials loader, model CLI, external-call path, or dormant model invocation stub. Phase 4 exposes only offline frame, prompt, retrieval-contract verification, and H3 freeze capabilities.
- **D-15:** Prove model unreachability structurally and at runtime. The CLI allowlist contains no model, provider, or run command; dependency checks reject network, provider-SDK, and credentials imports in the Phase 4 boundary; unknown model commands fail deterministically without network activity.
- **D-16:** The only retrieval CLI surface is `verify-retrieval-contract`, and it accepts only `test_only` corpora. Non-test-only inputs are rejected. No authoritative or production retrieval command exists on the Red branch.
- **D-17:** Create no provider or model configuration file. H3 records `provider_config_present=false`, `model_snapshot=not_applicable_red`, `credentials_boundary=not_applicable_red`, and `external_calls_authorized=false`. The freeze inventory contains no secret, environment-variable, or credentials path.

### the agent's Discretion

The planner may choose internal Python module and schema-file decomposition, additional stable diagnostics, the exact contract-fixture prose, the deterministic standard-library lexical-token rule, and human-readable report layout. Those choices must reuse existing canonical JSON, hashing, strict parsing, immutable-attempt, descriptor-bound filesystem, CLI, and readiness/decision patterns. Do not add a dependency when the standard library or installed project code suffices.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Frozen Project and Treatment Contract

- `.planning/PROJECT.md` — Defines the evaluation-first scope, isolation boundary, treatment controls, Red success path, and prohibited provider/upstream expansion.
- `.planning/REQUIREMENTS.md` — Defines Phase 4 requirements TS-10, H1-01, and H2-02 plus every-path and Green/Yellow/Red acceptance rules.
- `.planning/ROADMAP.md` — Defines the Phase 4 goal, vertical increment, H3/H4 checkpoints, four planned capability increments, and dependency on Phase 3.
- `../../Downloads/LFX_RISCV_SpecChoice_v1.3.2_frozen_execution_baseline.md` §§7, 8.3, 10, 11, 15, 18.4, 24, 25 — Defines the exact three-axis frame, retrieval method, A/B/C isolation, parsing, deterministic artifacts, Phase 4 prompt, fallback policy, and freeze checklist.

### Accepted Phase 3 Authority

- `.planning/phases/03-human-reviewed-data-preregistration/03-CONTEXT.md` — Locks no-quota-filling admission, family/split/relevance boundaries, human authority, immutable review chains, and Phase 4 ownership of the final branch decision.
- `.planning/phases/03-human-reviewed-data-preregistration/03-VERIFICATION.md` — Verifies Phase 3 completion and the accepted Red-path evidence chain.
- `experiments/specchoice-v1.3.2/phase3/data-authority-v1.json` — Exact accepted Phase 3 authority: `red_required`, one qualifying pair, zero strict cases, and no retrieval/model/publication authorization.
- `experiments/specchoice-v1.3.2/reports/h2/data-eligibility-v1.json` — Canonical threshold calculation and audited eligibility status consumed by H3.
- `experiments/specchoice-v1.3.2/reports/h2/h2-data-review-v1/review-packet.json` — Decision-free H2 audit packet with counts, invariants, exclusions, and bindings.
- `experiments/specchoice-v1.3.2/receipts/h2-data-review-readiness-v1.json` — Exact readiness identity approved by the human H2 decision.
- `experiments/specchoice-v1.3.2/reviews/h2-data-decision-v1.json` — Human approval of the data audit and Red conclusion, explicitly not Phase 4 branch authority.

### Frozen Data Inputs

- `experiments/specchoice-v1.3.2/data/preregistration/candidates-v1/candidate-inventory.json` — Frozen candidate inventory; test-only Phase 4 fixtures must never join or replace it.
- `experiments/specchoice-v1.3.2/data/preregistration/split-manifest-v1.json` — Frozen prototype/strict/auxiliary membership, including the empty strict core.
- `experiments/specchoice-v1.3.2/data/preregistration/pair-relevance-registry-v1.json` — Frozen relevance population; retrieval tests must not mutate or infer judgments.
- `experiments/specchoice-v1.3.2/data/preregistration/metamorphic-registry-v1.json` — Frozen unavailable metamorphic directions preserved on Red.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `experiments/specchoice-v1.3.2/src/specchoice_evidence/canonical.py` — Existing standard-library canonical JSON and SHA-256 primitives for prompt, response, manifest, readiness, decision, and freeze identities.
- `experiments/specchoice-v1.3.2/src/specchoice_evidence/filesystem.py` — Existing descriptor-bound, fail-closed authoritative-leaf and filesystem-kind validation.
- `experiments/specchoice-v1.3.2/src/specchoice_measurement/strict_json.py` — Existing duplicate-key rejection, exact-key schemas, enum checks, canonical no-finding representation, and evidence-span validation.
- `experiments/specchoice-v1.3.2/src/specchoice_measurement/diagnostics.py` — Existing stable structured diagnostics and deterministic ordering.
- `experiments/specchoice-v1.3.2/src/specchoice_data/schema.py` — Existing strict frame, pair, provenance, and data-admission schema patterns.
- `experiments/specchoice-v1.3.2/src/specchoice_data/h2.py` — Existing decision-free packet, readiness, human decision, authority, eligibility, and fail-closed publication patterns to reuse for H3.
- `experiments/specchoice-v1.3.2/src/specchoice_data/cli.py` — Existing standalone argparse command registration and immutable artifact publication boundary.

### Established Patterns

- Machine readiness and human approval are separate, content-bound artifacts; approval never emerges from readiness automatically.
- Canonical machine JSON is authoritative and human-readable Markdown is a deterministic projection, never a second source of truth.
- Immutable versioned generations and decisions replace in-place mutation; disputed semantic changes rebuild their dependent chain.
- Strict parsing rejects unknown keys, duplicates, invalid enums, silent coercion, partial authority, and unbound evidence.
- Test/diagnostic-only artifacts are visibly segregated and cannot become score-, eligibility-, or authority-bearing evidence.
- The prototype remains dependency-light and standalone under `experiments/specchoice-v1.3.2/`.

### Integration Points

- New frame, prompt, retrieval-contract, H3, CLI, tests, config, contract fixtures, reports, reviews, and receipts remain inside `experiments/specchoice-v1.3.2/`.
- H3 consumes the exact Phase 3 data authority, data-eligibility report, H2 review packet/readiness, and human H2 decision; it never rediscovers counts or reopens semantics.
- `verify-retrieval-contract` may consume only the new Phase 4 `test_only` corpus and target; the authoritative Phase 3 data root is used only to prove the production path remains unavailable.
- Phase 5 may consume only the approved immutable H3 Red authority and must find no provider/model/H4 execution surface.

</code_context>

<specifics>
## Specific Ideas

- Keep test-only pair and target fixtures obviously synthetic and semantically unrelated to RISC-V so they cannot be mistaken for quota-filling research data.
- Emit `INSUFFICIENT_RETRIEVAL_PAIRS` without a partial ranking when fewer than two distinct eligible pairs exist.
- Store contract responses beside prompts but mark them unambiguously as human-authored, non-model evidence.
- Make the treatment-diff manifest an allowlist: any shared-section byte change outside the intended A-vs-B frame or B-vs-C selection boundary is blocking.
- Treat the absence of provider/model/config/credentials surfaces as positive, machine-verified Red evidence rather than incomplete implementation.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within the frozen Phase 4 scope.

</deferred>

---

*Phase: 4-offline-treatments-retrieval-and-branch-freeze*
*Context gathered: 2026-08-04*
