# Phase 3: Human-Reviewed Data Preregistration - Research

**Researched:** 2026-08-03
**Scope:** TS-08, TS-09, H2-01
**Mode:** MVP, tracer-first

## Summary

Phase 3 should be implemented as a local, dependency-free evidence pipeline under `experiments/specchoice-v1.3.2/`. The pipeline must consume the exact active Phase 2 source authority and approved H1 decision, freeze a complete candidate inventory before semantic review, admit only structurally valid candidates to human review, and publish no count-bearing data root until all dependent human decisions are complete and consistent.

The smallest mature design is a new `specchoice_data` package that reuses the existing canonical JSON, SHA-256, descriptor-bound filesystem, strict JSON, deterministic diagnostic, immutable-write, and human decision patterns. A separate package is justified because Phase 3 validates curated data and review state rather than model predictions or Phase 2 measurements. It should remain standard-library-only and expose a local `python -m specchoice_data.cli` interface; no core UDB schema, generated data, database, network service, model call, or external API is needed.

Phase 3 planning is valid now, but execution must fail closed until Phase 2 is lifecycle-closed and the exact successor verification/review/H1 authority referenced by `03-CONTEXT.md` is available as committed local evidence.

## Source Contract

### Required upstream authority

Every Phase 3 readiness or decision artifact must bind:

- `experiments/specchoice-v1.3.2/phase2/source-authority.json` canonical bytes and SHA-256;
- `experiments/specchoice-v1.3.2/reviews/h1-source-gold-decision-v6.json` canonical bytes, approved disposition, and exact packet/readiness bindings;
- the accepted source generation/core/root/snapshot identities already carried by that Phase 2 chain;
- the Phase 3 schema, candidate inventory, family registry, and every dependent review decision by version and content hash.

Historical, candidate, repair, or predecessor generations are audit evidence only. There is no fallback search for a different authority if the active path or hash fails.

### Frozen baseline constraints

The frozen baseline requires complete contrastive pairs, a frozen family registry, a strict family-disjoint core, separately reported example-disjoint auxiliary cases, preregistered relevance, four metamorphic directions, and deterministic Green/Yellow/Red thresholds. `03-CONTEXT.md` tightens this contract with explicit invalid/disputed/excluded states, inventory freeze before review, no threshold backfill, exact claim-to-span mappings, directed pair semantics, explicit `no_relevant_pair`, registry-change invalidation, and H2's limited authority over `green_eligible`, `yellow_eligible`, or `red_required`.

## Recommended Architecture

### Authoritative representation

Use canonical JSON as the sole machine authority. Reviewer-facing Markdown is a one-way projection whose hash is bound by its packet. This avoids adding YAML parsing dependencies and directly reuses `canonical_json_bytes`, `decode_strict_json`, and existing exact-resume writers.

Recommended stable files:

- `config/data/phase3-data-schema-v1.json` — closed versions, enums, required field sets, four metamorphic direction IDs, and fixed eligibility thresholds.
- `data/preregistration/candidates-v1/candidate-inventory.json` — complete, sorted, pre-review inventory with every candidate path, kind, byte length, and SHA-256.
- `data/preregistration/candidates-v1/pairs/*.json` — pair candidates with independently reviewable sides and relationship fields.
- `data/preregistration/candidates-v1/held-out/*.json` — held-out case candidates.
- `data/preregistration/candidates-v1/metamorphic/*.json` — exactly one candidate for each required direction; synthetic sides are explicitly typed and excluded from dataset counts.
- `data/preregistration/family-registry-v1.json` — closed definition-first registry.
- `data/preregistration/split-manifest-v1.json` — deterministic prototype, strict-core, and auxiliary membership.
- `data/preregistration/pair-relevance-registry-v1.json` — complete strict-core coverage with non-empty pair IDs or explicit `no_relevant_pair`.
- `reports/h2/*-review-v1/` — canonical packet JSON plus Markdown projection for each review stage.
- `receipts/*-readiness-v1.json` — decision-free machine readiness artifacts.
- `reviews/*-decision-v1.json` — human-authored decisions with exact packet/readiness hashes.
- `phase3/data-authority-v1.json` — approved data root, audited counts, and exactly one eligibility status; not the final Phase 4 Green/Yellow/Red authorization.

### Module responsibilities

- `specchoice_data/schema.py`: exact-key, enum, identifier, evidence-span, registry-version, and canonical-input validation.
- `specchoice_data/admission.py`: active Phase 2 authority gate, inventory freeze, descriptor-bound source-span verification, structural admission, and stable diagnostics.
- `specchoice_data/review.py`: review packet/readiness/decision construction and validation with no semantic inference.
- `specchoice_data/splits.py`: family-registry validation, deterministic strict/auxiliary assignment, example/span reuse checks, and registry invalidation checks.
- `specchoice_data/relevance.py`: complete relevance coverage and four-direction metamorphic validation.
- `specchoice_data/h2.py`: whole-chain H2 readiness, decision validation, approved-only data-root publication, count audit, and eligibility calculation.
- `specchoice_data/cli.py`: thin argparse routes only; domain logic remains in the modules above.

This decomposition is small enough to test independently but keeps each trust boundary explicit. Do not copy canonicalization or filesystem code into the new package.

## Tracer-First Implementation Path

1. Build one production-quality pair admission and review slice using real accepted Phase 2 source bytes. It must freeze an inventory, validate two independent sides and one directed relationship, render a packet, and accept an explicit human approved/disputed/excluded decision without inferring semantics.
2. Expand the same schemas and review mechanics to the full candidate inventory, then freeze and approve the family registry and deterministic strict/auxiliary split.
3. Add complete strict-core relevance and the four human-reviewed metamorphic directions, keeping synthetic material typed and non-counting.
4. Run whole-chain validation, collect H2, and publish the approved-only data root and one deterministic eligibility status. Red must remain a successful, auditable outcome when thresholds cannot be met.

The first slice proves every layer from accepted source bytes to a human decision. Later work expands data coverage and cross-record invariants rather than replacing the architecture.

## Detailed Validation Rules

### Structural admission

Machine admission must reject before semantic review when any of these are false:

- exact closed schema and supported version;
- candidate is listed in the frozen inventory with matching path/hash/length/kind;
- every source path is relative, under the active accepted authority, and read through descriptor-held boundaries;
- every claim-to-span mapping has a declared claim ID, non-empty exact byte range, matching text, and accepted source SHA-256;
- primary family exists in the exact registry version where required;
- pair sides have distinct example IDs and the directed pair declares shared structure, discriminating axes, expected frame/status delta, and presentation order;
- synthetic metamorphic material contains an exact edit record and never declares itself authoritative or count-eligible.

Structural failures emit sorted stable diagnostics, retain audit custody, and never appear in a human semantic review queue or eligibility count.

### Human semantic review

Each item carries exactly `approved`, `disputed`, or `excluded`; structurally invalid candidates remain `invalid` and cannot receive an approval that bypasses admission. Pair sides are reviewed independently before the relationship. A rejected relationship does not rewrite side semantics. Any modified bytes create a new version and invalidate the decision.

Family definitions, inclusion criteria, and exclusion criteria are approved before assignments. Every eligible item has exactly one unambiguous primary family. Ambiguity produces `disputed`, not an `ambiguous` family value.

### Leakage and split rules

- An approved count-eligible prototype pair cannot reuse an authoritative example ID or source-span identity used by another count-eligible pair.
- Prototype and all held-out examples are example-disjoint.
- Strict-core primary families are disjoint from prototype primary families.
- Example-disjoint held-out cases with family overlap are auxiliary only.
- No held-out passage identity may appear in any declared fixed or retrieval demonstration material.
- Auxiliary cases and approved-but-auxiliary state are reported separately and never counted as strict core.

### Relevance and metamorphic rules

Every strict-core case has exactly one relevance disposition: a non-empty list of approved pair IDs or `no_relevant_pair` with a non-empty rationale. Pair relevance requires shared key structure and at least one preregistered decisive axis; it never stores or implies ranking. PairHit denominators later include only non-empty relevant-pair cases.

The metamorphic registry contains the four exact direction IDs:

- `choice_space_origin`;
- `warl_fixed_legal_set`;
- `hardware_software_authority`;
- `normative_note_example`.

Each freezes source A, source B, expected frame/status delta, provenance, and human approval. Synthetic variants are visibly typed, contain exact edits, are not model generated, and contribute zero prototype or held-out count.

### H2 eligibility

Only an approved H2 decision can publish `phase3/data-authority-v1.json`. Counts derive from approved, structurally valid, mutually consistent records only. The deterministic result is:

- `green_eligible`: at least 6 approved qualifying pairs and at least 10 approved strict-core cases, with registry, relevance, metamorphic, and all invariant checks green;
- `yellow_eligible`: otherwise at least 4 approved qualifying pairs and at least 6 approved strict-core cases, with the same non-count invariants green;
- `red_required`: every other structurally complete reviewed outcome, including insufficient counts or material disputes.

No quota filling or candidate replacement occurs after inventory freeze. H2 does not write Phase 4's final execution decision.

## Failure Modes and Prevention

| Failure mode | Prevention |
|---|---|
| Candidate list changes after seeing review results | Inventory canonical bytes and hash precede all review packets; decisions bind that hash. |
| Human dispute silently becomes machine exclusion or relabel | Distinct invalid/disputed/excluded states and exact human payload validation. |
| Multiple variants inflate pair counts | Global example-ID and source-span uniqueness across approved count-eligible pairs. |
| Family definitions drift during assignment | Closed registry approval precedes assignments; any content change invalidates all dependent artifacts. |
| Helpful cases are moved into strict core | Split membership is a deterministic function of approved example and primary-family identities. |
| Missing relevance is treated as negative relevance | Explicit `no_relevant_pair` with rationale; absence is invalid. |
| Synthetic metamorphic text is mistaken for source text | Required `source_kind=human_synthetic`, exact edit record, human approval, zero count eligibility. |
| Machine readiness is mistaken for human approval | Separate readiness and decision artifacts; data root writer requires approved H2. |
| Red is hidden by partial approved data | Whole-inventory counts include all invalid/disputed/excluded states and deterministically select `red_required`. |
| Phase 3 executes on unfinished Phase 2 | Every command gates on lifecycle-closed Phase 2 evidence and exact approved H1 authority before writing. |

## Security and Trust Boundaries

Security enforcement is active at ASVS L1 with high severity blocking. Relevant threats are integrity and authority escalation rather than web attacks:

- pathname or symlink substitution of accepted source bytes;
- stale or mixed registry/candidate/review versions;
- forged reviewer identity or inferred human fields;
- post-freeze mutation or replacement of immutable artifacts;
- count inflation through reused examples/spans or synthetic data;
- eligibility status being misrepresented as final execution authority;
- accidental network/model/publication behavior.

Mitigations are descriptor-bound reads, canonical hash bindings, closed schemas, no-replace exact-resume writes, explicit human checkpoints, deterministic whole-chain recomputation, and local-only CLI routes.

## Validation Architecture

Use the existing `unittest` infrastructure. Add focused tests under `experiments/specchoice-v1.3.2/tests/` and run with `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m unittest`.

### Fast feedback suites

- `tests.test_data_admission` — inventory, provenance, exact spans, pair admission, invalid-state diagnostics.
- `tests.test_data_splits` — family registry, primary assignment, example/span reuse, strict/aux split, held-out demonstration leakage.
- `tests.test_data_relevance` — complete relevance and four metamorphic directions.
- `tests.test_data_h2` — readiness, three-state human decisions, count audit, eligibility, stale binding rejection, approved-only data root.

Each plan runs its focused module after every task and the cumulative four-module suite after its wave. Existing canonical/filesystem tests run in the final wave to prove reused custody behavior was not weakened.

### Manual-only gates

Automation cannot approve semantic labels, family definitions/assignments, pair axes, relevance, metamorphic expectations, or H2. Each checkpoint must display exact recomputed upstream hashes and the complete review set, then accept a structurally complete human response. Tests cover the state machine and reject inferred/defaulted/missing human fields; they do not impersonate the reviewer for production artifacts.

### Expected feedback latency

Focused suites should remain under 10 seconds because they use temporary local fixtures and standard-library code. The cumulative Phase 3 suite plus canonical/filesystem regressions should remain under 30 seconds.

## Planning Implications

- Keep the roadmap's four capability plans, but make every plan detailed and checkpoint-aware.
- Use serial waves because each review decision is an authority input to the next layer.
- Mark all four plans `autonomous: false` because each contains a genuine human semantic checkpoint.
- Put one `type="tracer"` task first in 03-01; subsequent tasks expand real coverage and adversarial validation.
- Include concrete artifacts/symbols and exact verification commands in every task.
- Include a threat model in every plan and block high-severity integrity or authority threats.
- Preserve Phase 2 untracked successor evidence; Phase 3 planning must not stage or modify it.

## No External API Declaration

This phase integrates no external API, SDK, service, database, or model. It consumes local content-addressed files and emits local canonical evidence only, so no API capability matrix is required.
