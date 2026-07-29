# SpecChoice v1.3.2 — DelegationFrame + Axis-Contrastive Retrieval Feasibility Spike

## What This Is

SpecChoice v1.3.2 is a three-day, controlled feasibility experiment inside the RISC-V Unified Database repository. It tests whether extracting a minimal three-axis DelegationFrame and then retrieving axis-contrastive demonstration pairs improves architectural-parameter adjudication over the public Part I fixed-demonstration baseline.

The project is an evaluation-first research prototype for a human RISC-V reviewer and the developers or maintainers who will inspect its evidence. It is not a production extraction pipeline, a repository-wide schema change, or an automatic UnifiedDB parameter emitter.

## Core Value

Produce a reproducible, leakage-safe, falsifiable A/B/C result—positive, negative, or Red-path infeasible—without weakening gold semantics, deterministic measurement, or human control of RISC-V judgments.

## Requirements

### Validated

- ✓ UnifiedDB provides versioned, declarative RISC-V source data and JSON Schema contracts under `spec/` — existing upstream capability.
- ✓ UnifiedDB resolves standard and custom overlays into deterministic configured architecture views through `Udb::Resolver` and `Udb::Yaml::Resolver` — existing upstream capability.
- ✓ UnifiedDB exposes behavior-rich configured architecture and parameter objects through the Ruby domain/query layer — existing upstream capability.
- ✓ UnifiedDB compiles and validates embedded architectural behavior through its IDL compiler and constraint tooling — existing upstream capability.
- ✓ UnifiedDB supports repository-local generation backends, command wrappers, and reproducible generated-artifact boundaries under `gen/` — existing upstream capability.
- ✓ UnifiedDB already has multi-language validation infrastructure, including Minitest, pytest, CTest/Catch2, regression manifests, and GitHub Actions — existing upstream capability.
- ✓ Public PR snapshots provide the Part I prompts, taxonomy, fixtures, extraction artifacts, and emitter context needed for a pinned feasibility study — frozen baseline input.

### Active

- [ ] Pin and verify all public source snapshots named by the v1.3.2 frozen baseline.
- [ ] Build a dependency-light, self-contained prototype at `experiments/specchoice-v1.3.2/`.
- [ ] Implement a versioned PR #2164 fixture adapter and minimal v1.2.1 deterministic measurement runner.
- [ ] Enforce the canonical `surfaced` plus nullable `parameter_status` adjudication representation and stable diagnostic codes.
- [ ] Score surfacing, disposition, identity, evidence integrity, and candidate behavior independently.
- [ ] Produce byte-stable canonical JSON reports for equivalent inputs.
- [ ] Curate and human-review a prototype bank of explicit axis-contrastive pairs with provenance.
- [ ] Freeze a primary-family registry, leakage-safe split manifest, and preregistered pair-relevance registry.
- [ ] Create a strict family-disjoint held-out core and keep any example-disjoint auxiliary set separate.
- [ ] Implement exactly the three required DelegationFrame axes and non-blocking frame-combination advisory diagnostics.
- [ ] Assemble treatment-controlled A/B/C prompts with equal demonstration counts and no neutral-text token padding.
- [ ] Implement deterministic complete-pair retrieval using TF-IDF, cosine similarity, and stable tie-breaking.
- [ ] Run the preregistered A/B/C experiment only after the human-reviewed Green or Yellow gate authorizes model calls.
- [ ] Implement four human-reviewed metamorphic minimal pairs and evaluate directional consistency.
- [ ] Generate case-level metrics, failure taxonomy, reproducibility evidence, limitations, and a defensible feasibility conclusion.
- [ ] Treat a Red gate as a successful feasibility assessment only when its independent auditability and reproducibility criteria pass.
- [ ] Keep discovery, maintainer communication, and upstream contribution work optional and strictly downstream of required deliverables.

### Out of Scope

- Generic RAG or vector-database infrastructure — the experiment tests one small retrieval treatment.
- Embedding comparisons, learned retrievers, or learned rerankers — retrieval is frozen to TF-IDF and cosine similarity.
- Knowledge graphs or multi-agent extraction orchestration — neither is part of the falsifiable hypothesis.
- Prompt optimization loops such as GEPA or DSPy — they would confound the controlled comparison.
- Fuzzy identity matching or generic semantic-entailment validation — naming and evidence auditing have narrower preregistered meanings.
- UDB YAML emission, taxonomy redesign, or complete `definedBy` inference — the spike adjudicates candidates only.
- Repository-wide prediction schemas or a full-corpus extraction benchmark — the prototype is isolated and small.
- Claims of statistical significance, full-corpus recall gains, private-pipeline superiority, or confirmed new parameters — the experiment cannot support them.
- Automatic Issues, comments, branches, pull requests, or other upstream writes — every public action requires human approval.
- Optional discovery or top-10 review dossiers before all required Green/Yellow work passes — optional scope is cut first.

## Context

- The working repository is the user's fork, `DengZhiyuan-math/riscv-unified-db`, with `origin` pointing to the fork and `upstream` pointing to `riscv/riscv-unified-db`.
- Local initialization started from upstream/fork commit `eb60a2f1ae968d2dceb91c338e0b34b64904822f`.
- The execution contract is `/Users/zhdeng/Downloads/LFX_RISCV_SpecChoice_v1.3.2_frozen_execution_baseline.md`.
- The baseline pins public snapshots from PRs #1765, #1766, #2097, #2164, #2192, and #1831. These are public research inputs, not assumed accepted interfaces.
- UnifiedDB is a large, data-centric generation system. Canonical YAML and IDL live under `spec/`; Ruby resolution/query libraries live under `tools/ruby-gems/`; generators live under `backends/` and `tools/ruby-gems/udb-gen/`; derived artifacts live under `gen/`.
- The prototype should minimize coupling to the Ruby generation pipeline. It may consume pinned public fixtures or snapshots, but its measurement, data, prompts, runs, and reports remain self-contained.
- The primary ablation is `B - A`: fixed demonstrations with a DelegationFrame versus direct fixed-demonstration adjudication.
- The secondary ablation is `C - B`: retrieved contrastive demonstrations versus fixed contrastive demonstrations with the same DelegationFrame.
- The human reviewer retains authority over architectural-parameter semantics, labels, dataset membership, primary families, contrastive axes, pair relevance, fallback state, and public communication.
- Known specification ambiguities must be resolved conservatively and logged:
  - `expect_params` in the skeptical-review prompt conflicts with canonical fixture field names.
  - Prompt-level `not_surfaced` must serialize as `surfaced: false`, never as a `parameter_status`.
  - Retrieval allows top one or two pairs generally, while the controlled experiment requires exactly two demonstration pairs.

## Constraints

- **Timeline**: Target three focused days, approximately 18–24 hours — remove work from the right side of the execution priority when constrained.
- **Placement**: Start at `experiments/specchoice-v1.3.2/` — the prototype must be self-contained and must not presume a final upstream location.
- **Measurement**: The minimal v1.2.1-compatible runner is the measurement spine — all 11 pinned fixtures must score from golden predictions before innovation work proceeds.
- **Schema**: Require exactly `authority`, `choice_object`, and `choice_space_origin` — optional metadata cannot become part of the primary hypothesis.
- **Adjudication**: `surfaced=false` has one canonical nullable representation — `parameter_status: not_surfaced` is invalid.
- **Semantics**: Naming is independent from accept/classify-out disposition — missing names warn but do not rewrite semantic outcomes.
- **Evidence**: Surfaced findings require verbatim evidence spans — span presence is auditing, not proof of entailment.
- **Data**: Prototype and held-out examples must be disjoint; the strict core must also be primary-family-disjoint — no leakage exceptions.
- **Preregistration**: Families, assignments, pairs, relevance judgments, gold, prompts, model settings, and fallback configuration must be frozen and hashed before retrieval or model execution.
- **Retrieval**: Use deterministic TF-IDF and cosine similarity over complete contrastive pairs — no embeddings or learned ranking.
- **Treatment Isolation**: A/B/C share cases, model snapshot, sampling, context, decision space, evidence rules, demonstration count, and repeat count — natural frame-related token differences are measured, not padded.
- **Determinism**: Core reports use UTF-8/LF, NFC normalization, stable sorting, canonical JSON, no absolute paths or timestamps, and content hashes.
- **Human Gate**: No real model experiment may start before labels, families, pairs, relevance judgments, and the Green/Yellow fallback decision receive human review.
- **Upstream Safety**: No public Issue or PR during the spike without explicit human approval and satisfaction of the frozen upstream criteria.
- **Environment**: If repository/toolchain setup blocks progress for 90 minutes, fall back to a dependency-light standalone implementation rather than expanding setup work.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Work from `DengZhiyuan-math/riscv-unified-db` with separate `origin` and `upstream` remotes | Preserves a clean contribution path while keeping the authoritative project visible | ✓ Good |
| Place the prototype under `experiments/specchoice-v1.3.2/` | Matches the frozen baseline and isolates research code from core UDB schemas and generators | — Pending |
| Preserve the frozen v1.3.2 document as the execution contract | Prevents scope drift and post-hoc changes to hypotheses or success criteria | — Pending |
| Build measurement before data retrieval or model calls | Invalid measurement would make every later comparison uninterpretable | — Pending |
| Use a three-axis DelegationFrame only | Keeps the intermediate representation small enough for a controlled falsifiable test | — Pending |
| Retrieve complete contrastive pairs with deterministic TF-IDF | Isolates the proposed boundary-example treatment without introducing embedding or learning confounds | — Pending |
| Separate surfacing, disposition, identity, evidence, frame, and retrieval metrics | A single score would conceal materially different failure modes | — Pending |
| Require strict family-disjoint evaluation and preregistered relevance | Prevents example/family leakage and post-hoc retrieval-quality claims | — Pending |
| Treat Green, Yellow, and Red as explicit Day 1 gates | Prevents unreliable gold or insufficient data from being replaced by unjustified model runs | — Pending |
| Accept controlled negative results as valid outcomes | The project tests feasibility rather than optimizing toward a preferred conclusion | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-30 after initialization*
