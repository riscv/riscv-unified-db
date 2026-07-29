# Architecture Research

**Domain:** Controlled, file-backed LLM evaluation experiment inside the RISC-V UnifiedDB repository  
**Project:** SpecChoice v1.3.2 — DelegationFrame + Axis-Contrastive Retrieval Feasibility Spike  
**Researched:** 2026-07-30  
**Confidence:** HIGH for project boundaries and sequencing fixed by the execution baseline; MEDIUM for library-level implementation details verified through official documentation

## Executive Recommendation

Implement SpecChoice as an independent Python batch application rooted at
`experiments/specchoice-v1.3.2/`. Treat UnifiedDB and the pinned public PR snapshots as
read-only source inputs, not runtime frameworks. Do not register a UDB backend, extend a UDB
schema, import the Ruby domain layer, write beneath `gen/`, or add a service/database.

The experiment should be a one-way artifact pipeline:

```text
pinned snapshots
    → versioned fixture adapter
    → deterministic measurement spine
    → human-curated datasets and registries
    → validation + freeze manifest + human fallback gate
    → deterministic pair retrieval
    → treatment-controlled A/B/C prompts
    → model-call boundary
    → immutable raw responses
    → strict parsing
    → partition-aware scoring
    → canonical reports
```

The central architectural rule is that every stage may read only artifacts to its left.
Gold, relevance judgments, and reports must never flow backward into retrieval, prompt
assembly, or model execution. Any change to a frozen artifact creates a new experiment
version and invalidates affected downstream artifacts.

## Standard Architecture

### System Overview

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Read-only external inputs                                                    │
│ UDB checkout + PR snapshots pinned by commit SHA                             │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ one-way import / adaptation
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ Experiment-owned reviewed inputs                                             │
│ config/ + data/ + prompts/ + schemas/model settings                          │
│ families, split, gold, pairs, relevance, advisory patterns, A/B/C templates  │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ validate, canonicalize, hash, approve
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ Deterministic offline core                                                   │
│ adapter → measurement → split checks → freeze/gate → retrieval → prompts     │
│ parsing → metrics → canonical reporting                                      │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ only authorized side-effect boundary
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ Model execution boundary                                                     │
│ deterministic call plan → provider request → immutable raw run bundle        │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │ replayable without network access
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ Derived evidence                                                             │
│ runs/<version>/parsed + diagnostics; reports/strict, auxiliary, metamorphic  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Dependency Direction

```text
models + canonical serialization
    ├── adapters ──→ measurement ──→ metrics ──→ reports
    ├── dataset loaders ──→ invariant validation ──→ freeze/gate
    ├── prototype loader ──→ retrieval ──→ context/prompt assembly
    ├── prompt assembly ──→ experiment plan ──→ model adapter
    └── parsing ──→ diagnostics ──→ metrics
```

Required negative dependencies:

- `retrieval.py` must not import or load held-out gold or
  `pair_relevance_registry.yaml`; relevance is a scoring-only input.
- `prompts.py`, `context.py`, and the model adapter must receive a target-only view that
  cannot expose gold labels, expected names, or expected frames.
- `measurement.py`, `metrics.py`, and `report.py` must not call a model provider.
- `src/specchoice/` must not import UDB Ruby code, read `gen/`, or mutate `spec/`.
- `reports/` and prior `runs/` must never be inputs to a new run of the same experiment
  version.

### Component Responsibilities

| Component | Owns | Inputs | Outputs | Boundary / rule |
|---|---|---|---|---|
| Snapshot manifest and importer | Pinned repository/PR identities and copied fixture provenance | Exact commit SHAs | Validated experiment-local source artifacts | Never resolves a moving branch or live PR head |
| PR #2164 adapter | Version-specific fixture shape normalization | Pinned fixture files | Internal `CaseGold` values | Only place allowed to understand PR-specific field names |
| Domain models | DelegationFrame, adjudication, diagnostics, pair/case/run records | Primitive values | Strict typed values | No file or network I/O |
| Canonical artifact service | NFC/LF/UTF-8 normalization, ordering, JSON serialization, SHA-256 | Validated values/files | Canonical bytes and hashes | One implementation used by freeze, run IDs, and reports |
| Measurement spine | Surfacing, disposition, identity, evidence, candidate behavior | Normalized gold + predictions | Stable diagnostics and case scores | Must work on all 11 pinned fixtures before innovation work |
| Registry and split validator | Family, split, pair, relevance, provenance invariants | Human-curated YAML/text | Validation result | Reports inconsistencies; never changes human labels |
| Freeze controller | Reviewed input inventory, code/environment identity, fallback decision | Validated artifacts | Canonical freeze manifest and root hash | Production retrieval/model execution fail closed without it |
| Gate evaluator | Green/Yellow/Red criteria and approval record | Frozen counts and review state | Authorized branch, `N_strict`, repeats | Cannot silently downgrade Green to Yellow or Red |
| Prototype loader | Complete positive/contrast pair units | Frozen prototype files | Ordered pair records/documents | Never exposes individual examples as separately retrievable units |
| Pair retriever | Frozen TF-IDF configuration and prototype bank | Pair documents + target text | Ordered pair IDs and scores | Fits on prototype bank only; relevance registry is inaccessible |
| Context and prompt assembler | Shared pair serializer, target packet, three treatment templates | Frozen pairs/prompts and target-only case | Exact prompt bytes + prompt hash | Exactly two complete pairs and stable section order |
| Model adapter | One provider-specific request/response boundary | Frozen model config + prompt | Raw response and operational metadata | No parsing, scoring, retries that change treatment, or access to gold |
| Experiment planner/executor | Stable case/system/repeat call plan | Gate authorization + prompt hashes | Immutable run bundles | Uses content-derived call IDs and supports exact crash replay |
| Strict parser | JSON/YAML decoding and schema enforcement | Preserved raw response | Parsed output or diagnostics | No silent semantic repair; raw response remains authoritative |
| Metrics engine | Partition-aware case and aggregate metrics | Parsed outputs + gold + relevance | Strict/auxiliary/metamorphic metric records | No blended headline metric |
| Report builder | Canonical machine report and narrative projections | Sorted metric records + manifests | `results.json`, Markdown, reproducibility evidence | Volatile metadata is kept outside canonical core reports |

## Recommended Project Structure

Preserve the frozen baseline layout and add only the small modules needed to make the
boundaries executable:

```text
experiments/specchoice-v1.3.2/
├── README.md
├── pyproject.toml
├── config/
│   ├── source_snapshots.yaml       # source identity; human-reviewed
│   ├── experiment.yaml             # fixed pairs, K=2, repeats, fallback inputs
│   ├── frame_advisory_patterns.yaml
│   └── model.example.yaml          # settings shape only; never credentials
├── data/
│   ├── family_registry.yaml
│   ├── split_manifest.yaml
│   ├── pair_relevance_registry.yaml
│   ├── prototypes/                 # one complete pair per file
│   ├── held_out/                   # source.txt and gold.yaml kept adjacent
│   ├── metamorphic/
│   └── discovery/                  # optional and excluded from headline metrics
├── prompts/
│   ├── shared_guidelines.md
│   ├── system_a_direct_fixed.md
│   ├── system_b_frame_fixed.md
│   └── system_c_frame_retrieved.md
├── src/specchoice/
│   ├── models.py                   # pure values and enums
│   ├── canonical.py                # NFC/LF/JSON/hash contract
│   ├── adapters/pr2164_v0_1.py
│   ├── measurement.py
│   ├── evidence.py
│   ├── validation.py               # registry/split/provenance invariants
│   ├── freeze.py                   # manifest and human-gate checks
│   ├── gates.py                    # Green/Yellow/Red state machine
│   ├── prototypes.py
│   ├── retrieval.py
│   ├── context.py
│   ├── prompts.py
│   ├── model.py                    # narrow provider boundary
│   ├── parsing.py
│   ├── experiment.py
│   ├── metrics.py
│   ├── report.py
│   └── cli.py
├── tests/
├── runs/
│   └── <experiment-version>/
│       ├── freeze_manifest.json
│       ├── run_manifest.json       # timestamps/provider metadata; non-canonical
│       └── calls/<call-id>/
│           ├── prompt.txt
│           ├── request.json
│           ├── raw_response.txt
│           ├── call_metadata.json
│           ├── parsed.json
│           └── diagnostics.json
├── reports/
│   ├── results.json                # canonical index and strict-core headline
│   ├── strict_core.json
│   ├── auxiliary.json              # only when auxiliary set exists
│   ├── metamorphic.json
│   ├── results.md
│   └── reproducibility.md
└── notes/
    ├── open_questions.md
    └── decision_log.md
```

`runs/` is evidence, not a cache to overwrite. `reports/` is reproducible derived output.
Human-authored inputs remain in `config/`, `data/`, and `prompts/`; code must never rewrite
them during validation or execution.

## Deterministic Artifact Contract

### Canonical Bytes

Use one canonical byte function everywhere:

1. Validate text as UTF-8.
2. normalize every string to Unicode NFC;
3. normalize line endings to LF and reject/normalize nonconforming frozen inputs before
   approval;
4. sort domain collections explicitly (`case_id`, `pair_id`, finding identity, diagnostic
   identity)—`sort_keys=True` does not sort arrays;
5. serialize JSON with fixed settings, `ensure_ascii=False`, `allow_nan=False`,
   `sort_keys=True`, two-space indentation, and exactly one trailing LF;
6. encode to UTF-8 and hash the exact bytes with SHA-256.

The Python documentation confirms that JSON key sorting is explicit, JSON serialization
returns text rather than bytes, NFC is an explicit Unicode normalization form, and SHA-256
hashes bytes. These implementation details are MEDIUM confidence because the documentation
provider seam fell back to official web sources.

### Freeze Manifest

Generate a canonical `freeze_manifest.json` containing:

- experiment version and frozen baseline name;
- repository commit and source snapshot SHAs;
- repo-relative path plus SHA-256 for every family/split/relevance registry, prototype,
  held-out gold, metamorphic pair, prompt, advisory-pattern file, adjudication schema, and
  model/sampling configuration;
- fixed pair IDs for A/B, retrieval `K=2`, strict case IDs, `N_strict`, repeat count, and
  Green/Yellow/Red state;
- dependency lock hash and measurement-code commit;
- human approval identifiers or an explicit reviewed-status record.

Paths are repository-relative and sorted. Do not include timestamps, usernames, absolute
paths, API keys, or host-specific data in the canonical freeze manifest.

Before production retrieval and before every model call, recompute the root hash and fail
closed on mismatch. A changed frozen input requires:

```text
stop current run
→ append rationale to notes/decision_log.md
→ increment experiment version
→ regenerate and approve freeze manifest
→ rerun every affected system from the beginning
```

### Run Identity and Immutability

Derive `call_id` from canonical values such as:

```text
experiment version + freeze root hash + dataset partition + case_id
+ system_id + repeat index + model-config hash + prompt hash
```

Write the prompt before making the request and preserve the provider response byte-for-byte
before parsing. A completed call directory is immutable. An interrupted executor may reuse an
already complete call with the same `call_id`, but it must not overwrite it or mix responses
from different prompt/model hashes.

## Data Flow

### End-to-End Flow

1. **Import:** Resolve only pinned commit SHAs and copy/read the required public artifacts.
   Record provenance; runtime execution never fetches a moving source.
2. **Adapt:** The PR #2164 adapter converts external fixture fields into the canonical
   positive/negative/candidate semantics.
3. **Measure first:** Golden and adversarial predictions exercise surfacing, disposition,
   identity, evidence, candidate behavior, diagnostics, and canonical JSON across all 11
   fixtures.
4. **Curate:** Humans author families, primary-family assignments, contrastive pairs, gold,
   metamorphic expectations, and pair relevance judgments.
5. **Validate:** Automated checks reject example overlap, strict primary-family overlap,
   unknown families, version mismatch, missing provenance/evidence, and held-out text in
   demonstrations. They never repair labels.
6. **Freeze and gate:** Hash the complete controlled input set, record `N_strict` and repeats,
   obtain human approval, and select Green, Yellow, or Red.
7. **Retrieve:** For C only, transform the target against the frozen prototype-bank TF-IDF
   space and select two complete pairs. Persist all scores and selected pair IDs.
8. **Assemble:** Serialize demonstrations once with a shared serializer, add the identical
   target and shared rules, then add the treatment-specific task/output fragment.
9. **Execute:** Enumerate calls in a stable case/system/repeat order and cross the model
   boundary only for an authorized Green/Yellow run.
10. **Parse:** Preserve raw output, then apply strict schema validation and stable diagnostics.
11. **Score:** Join parsed outputs to gold only after execution. Join retrieval rankings to
    preregistered relevance only inside retrieval-metric calculation.
12. **Report:** Sort all case-level records and emit partition-specific canonical artifacts,
    then render human-readable results from those artifacts.

### Gold Isolation

Use two distinct internal values:

- `TargetCase`: case ID, source text, allowed source metadata;
- `CaseGold`: expected surfacing/disposition/name/frame/evidence and primary family.

Prompt and model components accept only `TargetCase`. The metrics component is the first
place where `TargetCase`, prediction, and `CaseGold` are joined. Apply the same separation to
`RetrievalRanking` and `PairRelevanceJudgment`.

## Treatment Isolation

| Property | A — Direct-fixed | B — Frame-fixed | C — Frame-retrieved |
|---|---|---|---|
| Demonstration count | 2 complete pairs | Same 2 complete pairs as A | 2 complete retrieved pairs |
| Pair serializer | Shared | Shared | Shared |
| Target context | Identical | Identical | Identical |
| Shared guidelines/evidence rules | Identical | Identical | Identical |
| Decision space | Identical adjudication | Same adjudication | Same adjudication |
| DelegationFrame instructions/output | Absent | Present | Identical to B |
| Pair selection | Frozen fixed IDs | Same frozen fixed IDs | Deterministic TF-IDF |
| Model/sampling/repeats | Identical | Identical | Identical |

Prompt assembly should use ordered sections with no timestamps or environment-derived text.
Do not pad A with neutral text. Record actual input/output tokens, maximum output settings,
and truncation events in call metadata. Demonstration text and target text hashes make
treatment-isolation tests mechanical rather than visual.

## Pair Retrieval Boundary

Represent each prototype as one document containing its shared structure, positive text,
contrast text, and discriminating-axis labels. Sort pair records by `pair_id` before fitting.
Fit `TfidfVectorizer` only on the frozen prototype documents, transform targets separately,
compute cosine similarity, and rank by a total order:

```text
similarity descending, then pair_id ascending
```

Freeze every vectorizer parameter and the scikit-learn version. Persist the full ranking,
scores, bank hash, target hash, and selected two pair IDs. Scikit-learn officially documents
TF-IDF document vectors, L2 normalization, and cosine similarity; the application-owned
stable tie-break is still required. This library-level recommendation is MEDIUM confidence.

The retriever must not:

- read held-out gold, family labels used only for evaluation, or relevance judgments;
- retrieve a positive and contrast independently;
- include held-out cases while fitting IDF;
- use embeddings, a learned reranker, or model-generated query expansion;
- suppress a target because it resembles a hard negative.

## Model Execution and Parsing

Keep model access deliberately narrow: one adapter for the selected provider and one replay
path that consumes existing raw responses. Do not build a generic provider framework.
Credentials come from the environment and are never serialized.

Per-call state moves forward only:

```text
PLANNED → PROMPT_SAVED → RAW_SAVED → PARSED | PARSE_FAILED → SCORED
```

The parser may perform only explicitly versioned compatibility normalization, such as the
permitted external `reject` → `classify_out` mapping before strict validation. It must reject
unknown top-level keys, invalid enums, `parameter_status: not_surfaced`, noncanonical
`surfaced=false`, and empty evidence for surfaced findings. It must not infer missing
decisions or rewrite semantic content.

## Scoring and Reporting Separation

### Metric Ownership

- Surfacing, disposition, identity, evidence, candidate behavior, and classify-out behavior
  remain separate case fields and aggregates.
- Frame axes are scored separately for B/C; A records them as not applicable, never zero.
- `FRAME_COMBINATION_REQUIRES_REVIEW` is advisory and cannot alter axis or disposition
  correctness.
- `ACCEPTED_PARAMETER_NAME_MISSING` affects identity coverage only.
- `PairHit@K` is computed only for cases with frozen relevance judgments.
- Metamorphic consistency is a separate relation metric, not merged with held-out accuracy.

### Dataset Partitions

| Partition | Role | Report behavior |
|---|---|---|
| `strict_family_disjoint_core` | Primary controlled evaluation | Only source of headline A/B/C and ablation results |
| `example_disjoint_auxiliary` | Fallback supplementary evidence | Separate file/table/aggregates; never pooled with strict core |
| `metamorphic` | Directional consistency | Separate report and denominator |
| `discovery` | Optional qualitative review | Dossiers only; excluded from benchmark metrics |

`reports/results.json` should be a canonical index whose headline points only to
`strict_core.json`. If an auxiliary set exists, its counts and metrics live in
`auxiliary.json` and a separately labeled Markdown section. No code path should offer a
combined strict-plus-auxiliary aggregate.

Keep volatile execution metadata—timestamps, provider request IDs, latency, host, retry
history—in `run_manifest.json` and per-call metadata, outside canonical score reports.

## Human Approval Checkpoints

| Checkpoint | Human-owned decision | Machine prerequisite | Failure behavior |
|---|---|---|---|
| H1 — Source/gold review | Fixture interpretation and candidate semantics | Snapshot hashes and adapter audit | Measurement work may continue; innovation work does not |
| H2 — Data review | Labels, primary families, pair membership, discriminating axes, relevance, metamorphic expectations | Provenance/evidence and split validation pass | Return inconsistencies; never auto-edit data |
| H3 — Freeze and fallback | Approve manifest; choose Green/Yellow/Red, `N_strict`, repeats | Measurement scores 11 fixtures and all gate counts are computed | No production retrieval or model calls |
| H4 — Model authorization | Approve real external calls/cost with frozen model settings | Green or Yellow manifest hash matches | Fail closed; Red can never be overridden by executor flag |
| H5 — Interpretation | Accept failure taxonomy and feasibility conclusion | Canonical reports and raw evidence available | Record disputes without changing same-version gold |
| H6 — Upstream action | Approve any maintainer comment, Issue, branch, or PR | Required deliverables complete and upstream criteria met | Produce local draft only |

## Green / Yellow / Red Branch Behavior

| State | Entry criteria | Authorized work | Required outputs |
|---|---|---|---|
| Green | All 11 fixtures score; ≥6 reviewed pairs; frozen registry; strict core ≥10; frozen relevance; parseable A/B/C schemas | Full strict-core A/B/C with preregistered repeats; optional work only after required work | Raw/parsed calls, strict report, metamorphic report, reproducibility package |
| Yellow | All 11 fixtures score; ≥4 reviewed pairs; strict core ≥6; labels/families reviewed | Reduced A/B/C on frozen strict core; lower preregistered repeats allowed | Same controlled evidence; auxiliary separate; skip optional discovery |
| Red | Any frozen Red trigger, including inadequate pairs/core/labels or a covered scoring gap | No real model calls and no production ablation | Runner, data/split audit, ambiguity report, deterministic Red feasibility report |

Red is a successful feasibility assessment only when its independent auditability criteria
pass. It is not an experimental extraction result. The CLI should expose branch-specific
commands or checks so a Red manifest cannot accidentally reach the model adapter.

## Suggested Build Order

1. **Isolated skeleton and snapshot pins**
   - Create only the experiment directory, local package entry point, source manifest, and
     pinned fixture import path.
   - Dependency: none.

2. **Canonical values and measurement spine**
   - Implement models, canonical serialization/hashing, PR #2164 adapter, strict
     adjudication parser, evidence checks, stable diagnostics, and golden/adversarial tests.
   - Exit gate: all 11 pinned fixtures score from golden predictions and canonical reports
     are byte-stable.

3. **Human-curated data and invariant validators**
   - Add prototype pairs, held-out cases, family/split/relevance registries, and metamorphic
     pairs; implement overlap/version/provenance/evidence tests.
   - Dependency: canonical models; no retriever or model calls.
   - Exit gate: H2 human review complete.

4. **Prompt treatments and offline retrieval implementation**
   - Implement shared pair/context serialization, A/B/C templates, strict schemas,
     TF-IDF/cosine retrieval, stable ties, and prompt-budget/treatment-isolation tests.
   - Use synthetic/unit data while registries remain under review; do not run retrieval over
     the production held-out set yet.

5. **Freeze controller and Day 1 branch gate**
   - Hash every controlled artifact, record repository/dependency identity, freeze fixed
     pairs, `N_strict`, repeats, and model settings; obtain H3/H4 approval.
   - Exit is exactly one of Green, Yellow, or Red.

6. **Branch execution**
   - Green/Yellow: run frozen retrieval, generate the stable call plan, save prompts, execute
     model calls, preserve raw outputs, then parse.
   - Red: bypass retrieval/model execution and build the feasibility package from measurement
     and audit artifacts.

7. **Partition-aware scoring and reports**
   - Produce case-level tables, B−A and C−B comparisons, strict-only headline aggregates,
     auxiliary results separately, retrieval metrics, repeat disagreement, failures, and
     canonical hashes.

8. **Metamorphic evaluation, interpretation, then optional work**
   - Run the four reviewed minimal pairs, finalize limitations and reproducibility, and only
     then consider discovery or upstream communication.

This order makes the deterministic runner, reviewed data, and freeze gate structural
dependencies rather than checklist promises. If time is constrained, cut phases from step 8
backward; do not weaken steps 2, 3, or 5.

## Integration Points

### Allowed

| Boundary | Communication | Notes |
|---|---|---|
| Pinned UDB/PR snapshots → adapter | Read-only files identified by SHA | One-way import with provenance |
| Experiment CLI → model API | Narrow request/response adapter | Only external runtime side effect |
| Experiment tests → repository tooling | Optional invocation through existing Python/pytest environment | Keep experiment package independently runnable |
| Final evidence → human reviewer | Canonical JSON, Markdown, raw call bundles | Human retains semantic and upstream authority |

### Explicitly Deferred

- No Rake backend or `udb-gen` subcommand.
- No `tools/ruby-gems/udb` dependency.
- No UDB schema, taxonomy, parameter, or YAML emission changes.
- No writes to `spec/`, `cfgs/`, `backends/`, or `gen/`.
- No database, vector service, MLflow server, job queue, or web UI.
- No repository-wide regression entry until the experiment proves useful and maintainers
  invite integration.

## Anti-Patterns

### Coupling the spike to UDB resolution

**Failure:** Importing UDB internals or registering a generator makes an experimental
measurement change depend on a rapidly changing production API.  
**Instead:** Use pinned, copied public artifacts through one versioned adapter.

### One mutable “experiment state” file

**Failure:** Curated inputs, live execution metadata, and results overwrite one another,
destroying preregistration evidence.  
**Instead:** Separate human-authored frozen inputs, immutable run bundles, volatile manifests,
and reproducible canonical reports.

### Gold-aware retrieval or prompting

**Failure:** Relevance judgments, primary-family labels, or expected decisions influence pair
selection or model context.  
**Instead:** Enforce target-only and ranking-only value types; join gold only in metrics.

### Parsing during model transport

**Failure:** An invalid response is silently repaired or raw evidence is lost.  
**Instead:** Persist raw bytes first, then run a separately testable strict parser.

### Blending strict and auxiliary outcomes

**Failure:** A larger example-disjoint set masks family leakage in the headline metric.  
**Instead:** Separate files, denominators, tables, and narrative conclusions.

### Freeze-by-convention

**Failure:** Files are described as frozen but code does not check their hashes before
retrieval/model execution.  
**Instead:** Make manifest verification a required executable precondition.

### Premature experiment infrastructure

**Failure:** A provider framework, tracking server, vector database, or workflow engine
consumes the three-day spike and introduces confounds.  
**Instead:** Use a synchronous CLI, local files, one provider adapter, and deterministic replay.

## Scaling Considerations

| Scale | Recommendation |
|---|---|
| Current 18–72 strict-core calls | Sequential or narrowly bounded batch execution; one immutable directory per call |
| Hundreds of replayed calls | Keep the same call-ID/artifact contract; parallelize independent calls but assemble reports in sorted order |
| Larger future benchmark | Reassess storage/concurrency only after the experiment earns continuation; do not pre-build it now |

The first bottleneck is external model latency/rate limiting, not local TF-IDF or scoring.
The second is human semantic review. Neither is improved by coupling the spike to UDB's
generation architecture.

## Confidence Assessment

| Area | Confidence | Basis |
|---|---|---|
| Isolation from UDB production layers | HIGH | Frozen project contract plus mapped UDB architecture and directory responsibilities |
| Build order and Green/Yellow/Red behavior | HIGH | Directly specified by the frozen v1.3.2 execution baseline |
| Artifact ownership, gold isolation, and replay boundaries | HIGH | Required determinism, leakage, raw-output, and human-gate invariants imply these boundaries |
| Canonical JSON/NFC/SHA-256 implementation | MEDIUM | Verified against official Python documentation via web fallback |
| TF-IDF/cosine component design | MEDIUM | Verified against official scikit-learn documentation via web fallback; stable ranking remains application-owned |
| Preregistration-style immutable freeze model | MEDIUM | Consistent with the frozen baseline and official OSF registration guidance |

## Sources

- SpecChoice v1.3.2 frozen execution baseline:
  `/Users/zhdeng/Downloads/LFX_RISCV_SpecChoice_v1.3.2_frozen_execution_baseline.md`
- [Project definition](../PROJECT.md)
- [Mapped UnifiedDB architecture](../codebase/ARCHITECTURE.md)
- [Mapped UnifiedDB structure](../codebase/STRUCTURE.md)
- [Python `json` documentation](https://docs.python.org/3/library/json.html)
- [Python `unicodedata` documentation](https://docs.python.org/3/library/unicodedata.html)
- [Python `hashlib` documentation](https://docs.python.org/3/library/hashlib.html)
- [scikit-learn `TfidfVectorizer` documentation](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
- [scikit-learn cosine-similarity documentation](https://scikit-learn.org/stable/modules/metrics.html#cosine-similarity)
- [OSF registrations and preregistrations guidance](https://help.osf.io/article/330-welcome-to-registrations)

---
*Architecture research for SpecChoice v1.3.2*
*Researched: 2026-07-30*
