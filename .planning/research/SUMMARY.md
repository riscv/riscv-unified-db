# Project Research Summary

**Project:** SpecChoice v1.3.2 — DelegationFrame + Axis-Contrastive Retrieval Feasibility Spike  
**Domain:** Controlled, reproducible LLM evaluation inside the RISC-V Unified Database repository  
**Researched:** 2026-07-30  
**Confidence:** HIGH for scope, controls, and roadmap ordering; MEDIUM for the unfrozen model-provider integration

## Executive Summary

SpecChoice v1.3.2 is a three-day feasibility experiment, not a production extraction system. Its purpose is to determine whether a minimal three-axis DelegationFrame improves architectural-parameter adjudication over direct fixed-demonstration prompting (`B-A`), and whether deterministic retrieval of complete axis-contrastive pairs adds value over the same frame with fixed pairs (`C-B`). Experts would build this as a small, file-backed, one-way evidence pipeline: pin the public inputs, prove the scorer on all 11 fixtures, curate and review the data, freeze every treatment-affecting artifact, obtain human authorization, then execute and report the controlled comparison.

The recommended implementation is an isolated Python 3.14 package under `experiments/specchoice-v1.3.2/`. Reuse UnifiedDB's pinned `uv`, `jsonschema`, `ruamel.yaml`, `pytest`, and Ruff tooling; add only `scikit-learn` for explicit TF-IDF and cosine similarity. Keep model access behind one narrow synchronous adapter selected and locked only after the provider is frozen. Do not integrate with UDB's Ruby resolver/generator layers, alter UDB schemas, write to `spec/` or `gen/`, or add a database, orchestration framework, vector store, UI, or service.

The dominant risks are invalid measurement, model-influenced gold, family or relevance leakage, treatment confounds, silent output repair, and artifact drift. Prevent them structurally: use exact snapshot SHAs and hashes; preserve the canonical two-stage adjudication semantics; separate surfacing, disposition, identity, evidence, frame, and retrieval metrics; preregister human-reviewed families, pairs, relevance, and metamorphic expectations; hash the complete run contract; preserve raw responses before strict parsing; and keep strict, auxiliary, metamorphic, and discovery results separate. Green and Yellow authorize full or reduced controlled model execution. Red prohibits real model calls and instead delivers a reproducible measurement-and-data feasibility assessment; it is a valid outcome when its audit criteria pass.

## Key Findings

### Recommended Stack

The smallest reliable stack is a standalone Python batch application with local, reviewable artifacts. The detailed rationale and compatibility notes are in [STACK.md](STACK.md).

**Core technologies:**

- **CPython 3.14.6:** runner, schemas, retrieval, scoring, hashing, reporting, and CLI; reuse the repository pin.
- **uv 0.11.31:** isolated environment and experiment-local `uv.lock`; audited commands run with `--locked` and do not modify the root lockfile.
- **JSON Schema Draft 2020-12 with `jsonschema==4.26.0`:** authoritative validation for fixtures, predictions, frames, pairs, splits, manifests, and reports.
- **`ruamel.yaml==0.19.1`:** safe loading of human-authored frozen YAML only; normalize to plain values and validate before use.
- **`scikit-learn==1.9.0`:** the sole new core dependency, used only for explicitly configured `TfidfVectorizer` and cosine similarity.
- **`pytest==9.1.1` and Ruff 0.16.0:** deterministic golden, adversarial, leakage, treatment-isolation, retrieval, and byte-stability tests using repository conventions.
- **Standard-library `argparse`, `json`, `hashlib`, `unicodedata`, `statistics`, and filesystem APIs:** CLI, canonical reports, hashes, and small-scale aggregation without extra frameworks.
- **One optional official provider SDK:** place it in a non-default dependency group only after the exact provider and immutable model snapshot are human-approved and locked.

**Critical implementation requirements:**

- Parse model output as size-capped JSON; reject duplicate keys, non-finite numbers, unknown fields, invalid enums, and noncanonical no-finding states.
- Preserve the raw provider response before parsing. Never repair, default, re-ask, or retry silently.
- Freeze every TF-IDF parameter, sort prototype pairs by `pair_id`, fit only on complete prototype-pair documents, and rank by `(-score, pair_id)`.
- Canonical core JSON uses NFC-normalized strings, LF line endings, explicitly sorted arrays, sorted object keys, UTF-8, one trailing newline, and SHA-256 of the final bytes.
- Keep timestamps, absolute paths, request IDs, latency, and other volatile metadata in separate run manifests, not canonical score reports.

### Expected Features

The feature contract is an experimental-control contract rather than a product feature list. Full acceptance detail is in [FEATURES.md](FEATURES.md).

**Must have for every defensible Green, Yellow, or Red outcome:**

- Isolated `experiments/specchoice-v1.3.2/` boundary and a pinned manifest for all named public PR snapshots.
- Versioned PR #2164 adapter and minimal v1.2.1-compatible runner that scores golden predictions for all 11 fixtures before innovation work.
- Canonical `surfaced` plus nullable `parameter_status` schema, strict parsing, stable diagnostic codes, and immutable raw-output lineage.
- Independent measurement of surfacing, disposition, identity, classify-out behavior, evidence-span integrity, and candidate behavior.
- Byte-stable canonical reports and hashes for equivalent captured inputs.
- Provenance-rich, human-reviewed family, split, pair, gold, relevance, and metamorphic registries with strict example and primary-family isolation.
- Machine-evaluated Green/Yellow/Red thresholds plus recorded human approval; no model execution before the gate and freeze manifest pass.
- Case-level reporting, explicit limitations, failure taxonomy, reproducibility commands, and bounded claims.

**Hypothesis-specific differentiators required on Green/Yellow:**

- Exactly three DelegationFrame axes—`authority`, `choice_object`, and `choice_space_origin`—with per-axis verbatim evidence and `unknown` allowed.
- `B-A` ablation using the same two fixed complete contrastive pairs, target context, final decision schema, model settings, and repeats.
- Human-reviewed complete contrastive-pair bank with provenance, shared structure, discriminating axes, frames, final decisions, and evidence.
- Deterministic TF-IDF retrieval of exactly two complete pairs, preregistered useful-pair judgments, and separate `PairHit@K`.
- `C-B` ablation in which pair-selection method is the only treatment difference.
- Complete A/B/C coverage for every preregistered strict case, all call-level accounting, and four frozen human-reviewed metamorphic minimal pairs.

**Conditional only after all required Green/Yellow work passes:**

- One small qualitative discovery slice and private top-10 review dossiers.
- A private external-package or maintainer-communication draft.
- Any public Issue, comment, branch, or PR only after a separate human approval and the frozen upstream criteria are satisfied.

### Explicit Anti-Features

Do not add these to the v1.3.2 roadmap:

- Generic RAG, embeddings, vector databases, learned retrieval, learned reranking, or query expansion.
- LangChain-style orchestration, multi-agent extraction, knowledge graphs, prompt search, DSPy/GEPA, or adaptive pair tuning.
- More required frame axes, required `scope`, a general ontology, or advisory rules that rewrite correctness.
- Full-corpus extraction, a repository-wide benchmark, UDB YAML emission, taxonomy redesign, complete `definedBy` inference, or fuzzy identity matching.
- Semantic-entailment automation; verbatim evidence presence is an auditability check, not proof of support.
- A production API, service, database, UI, authentication, tracking server, or core UDB backend integration.
- Silent schema coercion, tolerant parsing, hidden retries, neutral-text token padding, unequal demonstrations, or one blended headline score.
- Statistical-significance, full-corpus recall, private-pipeline superiority, confirmed-parameter, or merge-readiness claims.
- Automatic upstream writes or optional discovery before the controlled work is complete.

### Architecture Approach

Use the one-way, file-backed artifact architecture defined in [ARCHITECTURE.md](ARCHITECTURE.md):

```text
pinned snapshots
  → versioned fixture adapter
  → deterministic measurement spine
  → human-curated data and registries
  → validation, freeze manifest, and human branch gate
  → offline complete-pair retrieval and A/B/C prompt plan
  → authorized model boundary
  → immutable raw responses
  → strict parsing
  → partition-aware scoring
  → canonical reports
```

**Major components:**

1. **Snapshot importer and PR #2164 adapter** — resolve only exact SHAs, record provenance, and isolate external fixture-shape knowledge.
2. **Pure domain models and canonical artifact service** — enforce the adjudication/frame contracts and provide the single NFC/LF/JSON/SHA-256 implementation.
3. **Measurement spine** — score golden and adversarial predictions with stable diagnostics and independent denominators.
4. **Registry, split, and freeze controllers** — validate human-authored data without rewriting it, hash the controlled inputs, and fail closed on drift.
5. **Gate evaluator** — compute Green/Yellow/Red eligibility and require recorded human selection of the state, `N_strict`, and repeats.
6. **Prototype loader, retriever, and prompt assembler** — retrieve complete pair units, expose no gold or relevance to retrieval, and render treatment-controlled prompt bytes.
7. **Narrow model client and immutable executor** — execute a stable call plan only when authorized, save prompts first, and preserve raw responses before any parse.
8. **Strict parser, metrics engine, and report builder** — join gold only after execution and emit separate strict, auxiliary, metamorphic, and optional discovery artifacts.

**Non-negotiable architectural patterns:**

- Retrieval and prompt code receive target-only views; gold and pair relevance become visible only to scoring.
- Every stage reads only artifacts to its left. Reports and prior runs never influence same-version prompts, retrieval, or gold.
- A completed call directory is immutable and content-addressed by experiment, manifest, case, system, repeat, model-config, and prompt identities.
- Any frozen-input change stops the run, records a decision, increments the experiment version, refreezes, and reruns affected systems symmetrically.
- Strict-family-disjoint results are the only headline. Auxiliary, metamorphic, and discovery evidence have separate IDs, denominators, files, and conclusions.

### Human Approval Gates

| Gate | Human-owned decision | Machine prerequisite | Failure behavior |
|------|----------------------|----------------------|------------------|
| H1 — Source/gold review | Fixture interpretation and candidate semantics | Snapshot hashes and adapter audit | Measurement may continue; innovation does not |
| H2 — Data review | Labels, membership, primary families, pair axes, relevance, and metamorphic directions | Provenance, evidence, and split checks pass | Return inconsistencies; never auto-edit |
| H3 — Freeze/branch | Approve the manifest and select Green, Yellow, or Red, `N_strict`, and repeats | All 11 fixtures score and gate counts are computed | No production retrieval or model calls |
| H4 — Model authorization | Approve the exact provider/model settings and external calls | Green/Yellow freeze root verifies | Fail closed; Red cannot be overridden |
| H5 — Interpretation | Accept the failure taxonomy, limitations, and feasibility conclusion | Canonical reports and raw evidence exist | Record disputes without same-version relabeling |
| H6 — Upstream action | Approve any public communication or repository change | Required work and upstream criteria pass | Local draft only |

### Green / Yellow / Red Branch Contract

| Branch | Minimum entry state | Authorized execution | Required conclusion package |
|--------|---------------------|----------------------|-----------------------------|
| **Green** | 11 fixtures pass; at least 6 reviewed pairs; frozen families and relevance; at least 10 strict cases; parseable schemas | Full strict-core A/B/C with preregistered repeats; optional work only after required work | Raw and parsed calls, strict and metamorphic reports, case-level `B-A`/`C-B`, reproducibility package |
| **Yellow** | 11 fixtures pass; at least 4 reviewed pairs; reviewed labels/families; at least 6 strict cases | Reduced frozen A/B/C; auxiliary remains separate; optional discovery skipped by default | Same controlled evidence with smaller denominators and explicit Yellow limits |
| **Red** | Any frozen Red trigger, including fewer than 4 defensible pairs, no strict core, inconsistent axes, disputed gold, or an already-covered scoring gap | **No real model calls and no production ablation** | Runner, construction and split audit, ambiguity report, blocker evidence, and deterministic revised feasibility conclusion |

### Critical Pitfalls

The full risk catalog and recovery rules are in [PITFALLS.md](PITFALLS.md). The roadmap must prevent these early:

1. **Moving inputs or a faulty measurement contract** — pin exact PR commits and consumed-file hashes; fail on fixture-version mismatch; prove all 11 golden fixtures before retrieval or model work.
2. **Collapsed semantics or silent output repair** — keep surfacing, disposition, identity, evidence, candidate behavior, and frames independent; preserve raw output and expose strict-parser failures.
3. **Model-curated gold, family leakage, or post-hoc relevance** — keep humans authoritative, freeze one primary family per item and relevance judgments before retrieval, and select Red when defensible thresholds cannot be met.
4. **Frame creep or prompt confounds** — require exactly three axes, use shared prompt components and exactly two complete pairs, record natural token differences, and change only the intended `B-A` or `C-B` treatment.
5. **Gate abuse, mid-run drift, or hidden API nondeterminism** — encode the branch thresholds, verify the full manifest before calls, pin model/settings, preserve every repeat, and never splice changed artifacts into one result.
6. **Mixed partitions or overclaimed conclusions** — keep strict, auxiliary, metamorphic, and discovery results separate; lead with case-level evidence and accept negative ablations or Red as legitimate bounded outcomes.
7. **Premature optional or upstream work** — cut work from the right of the priority chain and require H6 before any public action.

## Implications for Roadmap

Use six dependency-ordered implementation phases. Do not schedule optional discovery or upstream contribution as a required v1.3.2 phase.

### Phase 1: Isolated Evidence Boundary and Source Integrity

**Rationale:** Every later artifact depends on immutable public inputs and an experiment-owned boundary. Establishing this first prevents live PR drift and accidental coupling to unstable UDB internals.  
**Delivers:** `experiments/specchoice-v1.3.2/` skeleton, nested Python project and lockfile, source-snapshot manifest, verified exact SHAs and file hashes, fixture import path, and versioned PR #2164 adapter shell.  
**Addresses:** TS-01, TS-02, the source-identity portion of TS-03.  
**Exit gate:** Every named source resolves to the frozen commit and every consumed file has reproducible provenance. If environment setup consumes 90 minutes, record and use the standalone dependency-light path.  
**Avoids:** Moving PR heads, generated-tree ambiguity, root dependency changes, and premature UDB integration.

### Phase 2: Deterministic Measurement Spine

**Rationale:** The experiment cannot interpret either hypothesis until the evaluator's semantics are independently proven.  
**Delivers:** canonical domain values; strict adjudication parser; candidate semantics; stable diagnostics; evidence-span checks; separate surfacing/disposition/identity/classify-out metrics; canonical serialization/hashing; golden and adversarial tests.  
**Addresses:** TS-03 through TS-07 and TS-15.  
**Exit gate:** Golden predictions score all 11 pinned fixtures, including the surfaced-then-classified-out candidate; invalid states remain visible; equivalent inputs produce byte-identical core JSON. No innovation or model work proceeds without this gate.  
**Avoids:** Measurement collapse, identity-as-disposition, silent repair, evidence overclaiming, and irreproducible reports.

### Phase 3: Human-Reviewed Data Preregistration

**Rationale:** Pair quality, family isolation, relevance, gold, and metamorphic directions are semantic judgments and must be frozen before ranks or outputs can bias them.  
**Delivers:** provenance-rich complete-pair bank; held-out cases and gold; primary-family registry; strict and auxiliary split manifests; preregistered pair-relevance registry; four required metamorphic minimal pairs; automated overlap, version, provenance, and evidence checks.  
**Addresses:** TS-08, TS-09, TS-13 data preparation, H2-01, and H2-03.  
**Human gate:** H2 reviews every label, membership decision, family, pair axis, relevance judgment, and expected metamorphic direction. Machines report inconsistencies but never repair them.  
**Exit gate:** The audited data either meets a possible Green/Yellow threshold or records the specific evidence for Red.  
**Avoids:** Model-generated gold, fabricated quota-filling pairs, example or family leakage, post-hoc relevance, and metamorphic tuning.

### Phase 4: Offline Treatments, Retrieval, Freeze, and Branch Gate

**Rationale:** Implement and mechanically compare all treatment-affecting artifacts before any real call; then freeze the exact experiment and choose the only authorized branch.  
**Delivers:** exactly three frame axes; non-blocking advisory patterns; shared pair/target serializers; A/B/C prompt templates and schemas; fixed A/B pair IDs; deterministic pair-level TF-IDF retrieval with stable ties; target-only interfaces; replay/fake model client; prompt structural-diff and budget tests; complete freeze manifest and root hash.  
**Addresses:** TS-10, TS-11 controls, H1-01 through H1-03, H2-02, H2-04 controls, and TS-15 freeze behavior.  
**Human gates:** H3 approves Green/Yellow/Red, `N_strict`, repeats, and the freeze manifest. H4 separately approves the exact provider, immutable model snapshot, sampling/output settings, cost, and real external calls.  
**Exit gate:** Exactly one verified branch is frozen. Green/Yellow may reach execution; Red is technically unable to reach the model adapter.  
**Avoids:** Frame/schema creep, gold-aware retrieval, independent-example retrieval, prompt/token confounds, gate-as-schedule-label behavior, and mid-run drift.

### Phase 5: Branch-Specific Execution and Immutable Evidence

**Rationale:** Execution must honor the frozen branch rather than assume that a model experiment is always feasible.  
**Delivers on Green/Yellow:** stable case/system/repeat plan; exact prompt bytes and hashes; exactly two pairs per condition; model calls with explicit settings and retries disabled; immutable raw envelopes and outputs; usage, finish, refusal, truncation, and failure metadata; strict parsed outputs and diagnostics.  
**Delivers on Red:** no real model calls; deterministic measurement, data/split construction audit, ambiguity record, and documented Red trigger.  
**Addresses:** TS-11, TS-12, the execution portion of TS-13, H1-02/H1-04, and H2-04.  
**Exit gate:** Every preregistered strict A/B/C cell and repeat is present, or execution stops and the gap remains explicit. Raw artifacts exist before parsing and can be replayed offline.  
**Avoids:** Unauthorized calls, asymmetric retries, moving model aliases, best-repeat selection, lost raw evidence, and partial favorable-subset comparisons.

### Phase 6: Partition-Aware Evaluation and Feasibility Report

**Rationale:** The final value is a bounded, auditable answer—not a preferred positive result. Scoring and interpretation must preserve every experimental distinction established upstream.  
**Delivers on Green/Yellow:** case-level A/B/C grid; descriptive `B-A` and `C-B`; separate frame-axis metrics; `PairHit@K` only where preregistered; repeat disagreements; four directional metamorphic results; strict-only headline; separate auxiliary outputs; failure taxonomy; canonical JSON, Markdown, hashes, exact rerun instructions, limitations, and positive or negative conclusion.  
**Delivers on Red:** deterministic feasibility report demonstrating the runner, audited construction attempt, blocker, ambiguity, and revised next-step conclusion without presenting model outputs as experimental evidence.  
**Addresses:** TS-06, TS-13, TS-14, TS-15, H1-03/H1-04, and H2-03/H2-04 reporting.  
**Human gates:** H5 approves semantic interpretation and claim bounds. H6 is required for any later public communication.  
**Exit gate:** Every aggregate traces to cases and raw evidence; strict and auxiliary denominators remain separate; no prohibited claim appears. Required v1.3.2 work ends here.  
**Avoids:** One-score reporting, strict/auxiliary pooling, evidence-as-entailment language, small-sample overclaiming, negative-result suppression, and premature upstream action.

### Phase Ordering Rationale

- Source identity precedes adaptation; adaptation and canonical semantics precede every score.
- The 11-fixture runner is the measurement spine and must pass before data, retrieval, or model results can be interpreted.
- Human-reviewed gold, families, pairs, relevance, and metamorphic directions precede retrieval and the branch gate.
- Treatment code is tested offline before the freeze so prompt differences, leakage, and parser behavior are inspectable without spending calls.
- The freeze and H3/H4 approvals are executable dependencies, not documentation afterthoughts.
- Scoring joins predictions with gold only after execution, and optional discovery remains downstream of a complete Green/Yellow package.
- Under time pressure, remove optional work first. Never weaken Phases 2, 3, or 4 to reach model execution.

### Research Flags

**Phases likely needing targeted research during planning:**

- **Phase 3:** HIGH domain uncertainty. The existence of enough defensible pairs, strict-family-disjoint cases, relevance judgments, and consistently labelable axes cannot be established by software research. Use pinned-source investigation plus named human RISC-V review; do not let `$gsd-plan-phase --research-phase 3` substitute for approval.
- **Phase 4:** MEDIUM runtime uncertainty. The exact model provider and snapshot are not frozen, and the local Python 3.14/scikit-learn lock resolution was not completed in the research sandbox. Research only the chosen provider's official structured-output, retry, raw-response, usage, refusal, and snapshot contracts; validate the nested lock in the connected environment.

**Phases with sufficiently documented patterns (skip research-phase):**

- **Phase 1:** repository layout, exact snapshot discipline, and isolated packaging are fully specified.
- **Phase 2:** schema, parser, measurement, diagnostics, and canonical byte contracts are explicit and testable.
- **Phase 5:** once the provider contract is frozen in Phase 4, the stable call plan and immutable artifact pattern are straightforward.
- **Phase 6:** metric ownership, partition separation, report contents, and claim bounds are already defined.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | HIGH confidence in repository-pinned Python/uv/jsonschema/ruamel/pytest/Ruff reuse and the minimal dependency boundary; MEDIUM confidence in scikit-learn/provider compatibility until local lock resolution and provider selection complete |
| Features | HIGH | The frozen project contract precisely defines table stakes, differentiators, thresholds, anti-features, and branch-specific deliverables |
| Architecture | HIGH | Isolation, one-way artifact flow, gold separation, freeze behavior, human gates, and build ordering follow directly from the frozen constraints; provider-specific transport details remain MEDIUM |
| Pitfalls | HIGH | Project-specific failure modes and recoveries are concrete and consistently reinforced across the feature and architecture research |

**Overall confidence:** HIGH for requirements and roadmap creation; MEDIUM for whether human-reviewed data will qualify for Green, Yellow, or Red and for the final provider adapter.

### Gaps to Address

- **Provider and immutable model snapshot are unfrozen:** select exactly one provider only after H3 prerequisites are known, then pin the SDK, model snapshot, parameters, retry policy, output limit, timeout, and credential boundary before H4.
- **Local dependency resolution is unverified:** run `bin/doctor`, create the nested lockfile, and verify Python 3.14/scikit-learn wheels early in Phase 1. Invoke the 90-minute standalone fallback rather than expanding setup scope.
- **Green/Yellow data sufficiency is unknown:** do not forecast a successful model run. Phase 3 must measure whether reviewed pairs and the strict core meet the frozen thresholds; choose Red when they do not.
- **Human semantic consistency is the limiting resource:** primary-family assignments, contrastive axes, evidence, relevance, and metamorphic directions require explicit reviewer records and may legitimately produce Red.
- **Known field and representation ambiguities require versioned decisions:** resolve `expect_params` versus canonical fixture fields inside the PR #2164 adapter; serialize prompt-level `not_surfaced` only as `surfaced=false`; use exactly two retrieved pairs in the controlled experiment.
- **Remote generation is not deterministic:** reproducibility means frozen requests, immutable raw responses, complete repeats, and byte-stable downstream reports—not a promise that future provider calls return identical text.

## Sources

### Primary (HIGH confidence)

- [Project definition](../PROJECT.md) — frozen milestone objective, active constraints, branch policy, human authority, and explicit out-of-scope boundaries.
- [Feature research](FEATURES.md) — table stakes, hypothesis-specific differentiators, thresholds, anti-features, and fallback deliverables.
- [Architecture research](ARCHITECTURE.md) — component boundaries, one-way data flow, human gates, branch behavior, and build order.
- [Pitfalls research](PITFALLS.md) — project-specific failure modes, warning signs, phase prevention, and recovery rules.
- [Stack research](STACK.md) — minimal dependency set, versions, parser/retrieval/report contracts, and compatibility caveats.
- SpecChoice v1.3.2 frozen execution baseline — authoritative contract cited and reconciled by all four research reports.
- Frozen UnifiedDB public snapshots for PRs #1765, #1766, #2097, #2164, #2192, and #1831 — experiment inputs identified by exact commits in the research.

### Secondary (MEDIUM confidence)

- Official Python documentation — JSON serialization, Unicode NFC normalization, SHA-256 hashing, and Python runtime behavior.
- Official scikit-learn documentation and package metadata — TF-IDF, cosine similarity, dependencies, and Python 3.14 wheel availability.
- Official `jsonschema`, `ruamel.yaml`, pytest, uv, and selected-provider documentation — validation, locking, compatibility, and provider-boundary behavior.
- NIST AI RMF, OSF/APS preregistration guidance, contamination research, and evaluation-quality guidance — supporting rationale for preregistration, leakage controls, human review, and bounded claims.

---
*Research completed: 2026-07-30*  
*Ready for roadmap: yes*
