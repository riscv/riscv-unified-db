# Feature Research

**Domain:** Controlled LLM extraction feasibility experiment for RISC-V architectural-parameter adjudication  
**Project:** SpecChoice v1.3.2 — DelegationFrame + Axis-Contrastive Retrieval Feasibility Spike  
**Researched:** 2026-07-30  
**Confidence:** HIGH for the frozen feature contract; MEDIUM for supporting cross-domain evaluation guidance

## Scope Interpretation

For this milestone, a “feature” is a reviewer-observable experimental capability or control: a fixture adapter, schema invariant, split check, human gate, treatment isolation rule, trace artifact, metric, or fail-safe outcome. It is not a production UI or a general extraction-platform feature.

Path notation used below:

- **ALL** — mandatory for every defensible outcome, including Red.
- **G/Y** — mandatory only after a human-reviewed Green or Yellow gate authorizes model execution.
- **G** — Green threshold or deliverable.
- **Y** — Yellow threshold or deliverable.
- **R** — Red feasibility deliverable; model execution is prohibited.
- **OPT** — optional only after every required G/Y deliverable passes; cut first when constrained.

The frozen baseline is the authority for scope. General AI-evaluation guidance reinforces its emphasis on repeatable measurement, fixed harnesses, documented test sets and tools, explicit claim limits, expert oversight, and reproducibility artifacts; it does not justify adding new scope.

## Feature Landscape

### Table Stakes (A Defensible Spike Requires These)

These capabilities do not test either innovation hypothesis by themselves. They make any Green, Yellow, or Red conclusion reviewable and falsifiable.

| ID | Capability | Path | Why Expected | Complexity | Frozen Requirement and Reviewer-Observable Acceptance |
|----|------------|------|--------------|------------|-------------------------------------------------------|
| TS-01 | Self-contained, dependency-light experiment boundary | ALL | A three-day spike must be inspectable without coupling experimental logic to unstable UDB schemas, generators, the heuristic MCP search service, or incomplete solver paths. | LOW | Baseline §§14, 16 and project constraints. All prototype code, data, prompts, runs, reports, and notes live under `experiments/specchoice-v1.3.2/`; generated artifacts stay out of core UDB data. After 90 minutes of environment blockage, the recorded fallback is a standalone implementation rather than more setup work. |
| TS-02 | Pinned public-source snapshot manifest and integrity checks | ALL | A result cannot be reproduced or audited if the public PR inputs drift. | LOW | Baseline §§3, 15, 19, 25. `config/source_snapshots.yaml` records every named PR and commit; source-integrity tests detect a missing or mismatched snapshot; reports repeat the exact commits. Public PR designs are described as snapshots, never accepted upstream interfaces. |
| TS-03 | Versioned PR #2164 fixture adapter plus minimal v1.2.1 measurement runner | ALL | Measurement validity must be established before innovation or model calls. | HIGH | Baseline §§4.1, 6, 16, 17. A named adapter version normalizes `expect_extract`, `expected_parameter_count`, and expected names. Golden predictions score all 11 pinned fixtures. The candidate fixture is surfaced and then `classify_out`, not accepted and not treated as absent. |
| TS-04 | Canonical adjudication schema and strict parser | ALL | Ambiguous no-finding or rejection states would make cross-system scores incomparable. | MEDIUM | Baseline §§6.2–6.3, 11.3, 23. `surfaced=false` permits only `parameter_status=null`, `proposed_name=null`, and empty evidence; `parameter_status:not_surfaced` is rejected. Strict mode rejects unknown top-level keys and invalid enums. Invalid decisions are never silently repaired; raw output and parser diagnostics remain visible. |
| TS-05 | Stable, structured diagnostics | ALL | Reviewers and tests need machine-stable failure identities rather than prose matching. | MEDIUM | Baseline §6.3. Tests assert all required diagnostic codes and structured fields, including missing/extra findings, candidate errors, evidence failures, duplicate/conflicting predictions, and missing accepted names. `ACCEPTED_PARAMETER_NAME_MISSING` remains an identity warning and cannot rewrite disposition. |
| TS-06 | Orthogonal outcome measurement | ALL | A single score would hide whether a system failed to surface a case, disposed it incorrectly, named it incorrectly, or quoted invalid evidence. | HIGH | Baseline §13. Reports separate SurfacingRecall, DispositionAccuracy, ExactIdentityAccuracy with `exact/incorrect/missing`, ClassifyOutAccuracy, and EvidenceSpanIntegrity. `review` is reported separately, identity is evaluated only after a correct positive acceptance, and evidence presence is never described as semantic entailment. G/Y additionally report each frame axis and retrieval separately. |
| TS-07 | Verbatim evidence audit with raw-output preservation | ALL | Expert reviewers must be able to trace every surfaced finding back to source text and distinguish parsing from semantic correctness. | MEDIUM | Baseline §§6.3, 7.3, 11.3, 13.1, 16. Every surfaced finding has at least one non-empty span found verbatim in the source; absent or fabricated spans receive stable diagnostics. Raw model responses, parsed outputs, and parser diagnostics are separate artifacts. |
| TS-08 | Leakage-safe, provenance-rich data manifests | ALL | Prototype/evaluation overlap or post-hoc family definitions would invalidate both ablations. | HIGH | Baseline §§8–9, 16, 25. Every item has provenance and one registered `primary_family`; prototype and held-out example IDs are disjoint; the strict core is also primary-family-disjoint. Tests fail on example overlap, strict-family overlap, unknown families, registry-version mismatch, or a held-out passage appearing in a prompt demonstration. Auxiliary data, if needed, is reported separately and never merged into the headline result. |
| TS-09 | Human authority and preregistered change control | ALL | RISC-V semantics, gold, family boundaries, contrastive axes, and useful-pair judgments are expert judgments, not model-generated truth. | MEDIUM | Baseline §§0, 8.4, 9.3, 16, 25. A human reviews labels, dataset membership, primary families, pairs, axes, relevance judgments, metamorphic transformations, fallback state, and any public communication. Required registries, gold, prompts, settings, and configuration are frozen and hashed before retrieval or model execution. Any later change stops the run, enters the decision log, increments the experiment version, and reruns affected systems. |
| TS-10 | Explicit Green / Yellow / Red gate with fail-safe behavior | ALL | A model run on disputed gold or an inadequate strict core produces a misleading answer, not useful evidence. | MEDIUM | Baseline §§16–17, 24. The gate emits one human-approved state plus `N_strict` and repeat count. Green requires all 11 fixtures, at least 6 verified pairs, frozen families and relevance, at least 10 strict cases, and parseable schemas. Yellow requires all fixtures, at least 4 pairs, at least 6 strict cases, and reviewed labels/families. A scoring gap already covered, fewer than 4 pairs, no strict core, inconsistent axes, or disputed gold selects Red and blocks real model calls. |
| TS-11 | Controlled A/B/C execution harness | G/Y | Without treatment isolation, `B-A` and `C-B` cannot be attributed to the proposed interventions. | HIGH | Baseline §§10–11, 16. Every strict-core case runs under A, B, and C with the same model snapshot, sampling, target context, guidelines, decision space, evidence rules, exactly two demonstration pairs, and preregistered repeat count. A/B share fixed pairs; B/C share frame and adjudication instructions; only C’s pair-selection method differs. Natural frame-related token differences are recorded, never padded. |
| TS-12 | Call-level accounting and complete case coverage | G/Y | Hidden retries, truncation, or missing cases can bias a tiny experiment. | MEDIUM | Baseline §§10.4, 13.4, 16. Each call records prompt hash, actual input/output tokens, maximum-output setting, model snapshot, sampling settings, raw response, parse result, truncation, and retry/failure state. A/B/C must complete on every preregistered strict-core case; otherwise optional work stops. |
| TS-13 | Four human-reviewed metamorphic minimal pairs | G/Y | A small held-out set needs directional checks that directly perturb the hypothesized semantic boundaries. | HIGH | Baseline §12. The artifact contains the four required transformations: implementation-selected/ISA-fixed, true WARL/fixed legal set, hardware choice/software advice, and normative/NOTE-example. Each pair has human-reviewed expected axis and decision direction; reports show per-pair outputs, evidence integrity, and MetamorphicConsistency. |
| TS-14 | Case-level reporting, failure taxonomy, and bounded claims | ALL | Aggregate scores alone cannot support skeptical review of a small, non-significance-seeking spike. | MEDIUM | Baseline §§13, 16–17, 19, 21. G/Y reports include paired A/B/C case rows, split counts, fallback state, retrieved pair IDs, axis metrics, repeat disagreements, metamorphic results, diagnostics, limitations, hashes, and positive or negative conclusions. Red reports the runner, public scoring-gap assessment, auditable data-construction attempt, explicit blocker, ambiguity report, and reproducible revised feasibility conclusion. No path claims statistical significance, full-corpus gains, confirmed parameters, or private-pipeline superiority. |
| TS-15 | Byte-stable reproducibility package | ALL | An independent reviewer must be able to distinguish a changed experiment from nondeterministic serialization. | MEDIUM | Baseline §§15, 19, 25. Equivalent inputs produce byte-identical canonical JSON using UTF-8/LF, NFC, stable sorting, sorted keys, and no timestamps or absolute paths in core reports. Separate manifests hold runtime metadata. Inputs, prompts, prototypes, gold, predictions, and reports carry content hashes; `reports/reproducibility.md` gives exact commands and expected outputs. |

### Differentiators (The Two Hypotheses Under Test)

These are scientific differentiators, not optional product enhancements. They are required in Green/Yellow because they constitute the intervention; Red stops before claiming to test them.

#### H1 — Does a Minimal DelegationFrame Reduce Shortcut Errors?

| ID | Capability | Path | Value Proposition | Complexity | Frozen Requirement and Reviewer-Observable Acceptance |
|----|------------|------|-------------------|------------|-------------------------------------------------------|
| H1-01 | Exactly three required frame axes with per-axis evidence | G/Y | Forces the model to expose who controls the choice, what is selected, and where the choice space originates before adjudicating. | MEDIUM | Baseline §7. Outputs require only `authority`, `choice_object`, and `choice_space_origin`, each using the frozen enums and a verbatim evidence span. Optional normativity, scope, and source metadata never enter the primary hypothesis; `scope` is not required. |
| H1-02 | Direct-fixed vs frame-fixed ablation (`B-A`) | G/Y | Isolates the effect of structured frame extraction from final-label prediction while keeping demonstrations fixed. | HIGH | Baseline §§2.1, 10.1–10.2, 16. Systems A and B use the same two fixed contrastive pairs and all shared controls; A returns adjudication only, B returns the three-axis frame plus the identical adjudication contract. The case-level report computes paired `B-A` outcomes without post-hoc prompt changes. |
| H1-03 | Independent axis scoring plus advisory frame-combination review | G/Y | Shows whether one axis is useful even if the full frame is not, while flagging suspicious combinations without turning a heuristic into gold. | MEDIUM | Baseline §§7.5, 13.2. Authority, choice object, and choice-space origin accuracies are reported separately. `FRAME_COMBINATION_REQUIRES_REVIEW` is generated only from a frozen advisory-pattern file, is non-blocking, and cannot change axis or disposition correctness. |
| H1-04 | Shortcut-family and directional failure evidence | G/Y | Makes the primary hypothesis falsifiable against the named errors: fixed ISA rules, extension gates, WARL false positives, software advice, and true positives classified out. | MEDIUM | Baseline §§2.1, 12, 16. Failure rows use the frozen taxonomy; metamorphic pairs expose the expected direction. Strong success may be two corrected shortcut errors across different families or at least three of four directional changes, but the experiment is not optimized after seeing labels to reach those thresholds. |

#### H2 — Do Retrieved Axis-Contrastive Pairs Improve Boundary Adjudication?

| ID | Capability | Path | Value Proposition | Complexity | Frozen Requirement and Reviewer-Observable Acceptance |
|----|------------|------|-------------------|------------|-------------------------------------------------------|
| H2-01 | Explicit, complete contrastive-pair bank | G/Y | Presents a shared technical structure together with the decisive semantic difference instead of treating unrelated positive and negative examples as interchangeable. | HIGH | Baseline §8. Each pair stores positive and contrast passages together with shared structure, frames, final statuses, discriminating axes, evidence, source provenance, and manual verification. Green targets 6–8 high-quality pairs with at least 6 acceptable; Yellow permits at least 4. No pair is fabricated to reach a quota. |
| H2-02 | Deterministic pair-level TF-IDF retrieval | G/Y | Tests one small, interpretable retrieval treatment without embedding or learned-ranking confounds. | MEDIUM | Baseline §§8.3, 16. Retrieval scores complete pairs using TF-IDF and cosine similarity, returns exactly two pairs for the controlled experiment, and uses stable tie-breaking. Tests show target-dependent selection, deterministic ties, no retrievable held-out examples, and no embedding model or learned reranker. |
| H2-03 | Preregistered useful-pair judgments and `PairHit@K` | G/Y | Separates retrieval quality from outcome quality and prevents pair relevance from being declared after ranks or model outputs are known. | MEDIUM | Baseline §§8.4, 13.3, 25. A human-reviewed relevance registry is versioned and hashed before retrieval. `PairHit@K` includes only cases with preregistered judgments, and every case reports retrieved pair IDs. Relevance changes require a new experiment version. |
| H2-04 | Frame-fixed vs frame-retrieved ablation (`C-B`) | G/Y | Isolates pair selection as the only difference after holding the frame schema and adjudication task constant. | HIGH | Baseline §§2.2, 10.2–10.3, 16. B uses frozen fixed pairs; C retrieves pairs per target. Both have identical frame/adjudication instructions, decision schema, evidence rules, context, model settings, count of two pairs, and repeat count. The report gives paired `C-B` outcomes and allows a valid negative result when retrieval is unhelpful. |

### Anti-Features (Explicitly Excluded)

| Anti-Feature | Why It May Be Requested | Why It Is Problematic Here | Required Alternative |
|--------------|-------------------------|----------------------------|----------------------|
| Generic RAG or vector-database infrastructure | Looks reusable and scalable. | It adds indexing, storage, and retrieval choices unrelated to the frozen pair-selection hypothesis and cannot be justified in three days. | Load the small frozen pair bank directly and use deterministic TF-IDF/cosine retrieval. |
| Embeddings, embedding comparisons, learned retrievers, or rerankers | May improve semantic retrieval. | They add model and optimization confounds, weaken interpretability, and violate the frozen secondary hypothesis. | Use the one preregistered TF-IDF pair representation and stable tie-breaking. |
| Multi-agent extraction orchestration or knowledge graphs | May appear to improve reasoning and coverage. | They create unmeasured interventions, broader data models, and new failure surfaces unrelated to `B-A` or `C-B`. | Use one controlled model interface and the three-axis frame. |
| More required frame axes, required `scope`, or a general ontology | Extra structure may seem more expressive. | It changes H1, increases annotation burden, and makes a small experiment harder to label consistently. | Require exactly the three frozen axes; keep allowed metadata optional and outside primary metrics. |
| Full-corpus extraction or a repository-wide benchmark | Produces a larger-looking result. | The timeline, gold coverage, family isolation, and reviewer capacity cannot support full-corpus recall or significance claims. | Use the small preregistered strict core; keep discovery to one optional qualitative slice. |
| UDB YAML emitter, taxonomy redesign, complete `definedBy` inference, or fuzzy identity matching | Converts predictions into apparent production value. | It conflates adjudication with alignment and emission, touches unstable repository contracts, and creates false confidence in merge-ready results. | Score surfacing, disposition, identity, and evidence separately; leave UDB changes to later maintainer-led work. |
| Candidate discovery combined with demonstration retrieval | Reuses one score and reduces implementation. | Hard-negative similarity is useful for boundary review but must not suppress discovery; combining tasks destroys the meaning of retrieval metrics. | Keep optional candidate ranking separate and retrieve complete contrastive pairs only for adjudication context. |
| Prompt optimization loops, adaptive pair tuning, or post-hoc settings changes | Could raise scores within the spike. | Optimization after seeing held-out outcomes invalidates the controlled comparison and encourages benchmark overfitting. | Freeze prompts, pair IDs/representation, settings, `N_strict`, and repeats before execution; version and rerun after any change. |
| Post-hoc relabeling, family reassignment, pair edits, or relevance edits | Can resolve inconvenient disagreements. | It leaks results into gold and makes `PairHit@K`, split isolation, and ablation claims circular. | Preserve the observed result; log the issue; start a new version only after human review. |
| LLM-generated gold, pair labels, relevance judgments, or unreviewed metamorphic transformations | Saves scarce expert time. | The model would define the target it is evaluated against, erasing independent semantic review. | Human RISC-V review remains the authority; Red is preferable to unreliable labels. |
| Silent output repair or tolerant schema coercion | Increases parse rate. | It hides instruction-following failures and can change decisions. | Preserve raw output, reject invalid strict outputs, and report structured parser diagnostics. Only the documented external `reject` to `classify_out` normalization may occur before strict validation. |
| Semantic-entailment claims from evidence-span presence | Evidence looks like an explanation. | A verbatim span proves only source occurrence, not that the decision follows from it. | Report EvidenceSpanIntegrity as an audit metric and leave semantic judgment to case-level human review. |
| Neutral-text token padding or unequal examples | Appears to equalize prompt length or compensate for A. | Padding is itself an intervention; unequal demonstrations confound treatment effects. | Keep exactly two pairs and shared context/rules; record natural token differences and preregister any necessary output-budget difference. |
| One aggregate score or statistical-significance claim | Simplifies the headline. | It hides distinct failure modes and overstates what 6–12 strict cases can establish. | Report case-level paired outcomes and separate surfacing, disposition, identity, evidence, axes, retrieval, stability, and metamorphic metrics. |
| Production service, UI, persistence, authentication, or core UDB integration | Makes the spike look deployable. | The repository has no SpecChoice product boundary, its reusable MCP path is heuristic and under-tested, and production controls would consume the spike. | Deliver a self-contained command-line research artifact and reproducibility package. |
| Automatic Issues, comments, branches, pull requests, or other upstream writes | Speeds contribution. | Public action is outside the experiment and requires maintainer context plus human approval. | Draft privately only after required work; publish nothing without explicit approval and all frozen upstream criteria. |
| Optional discovery, top-10 dossiers, external repository, or maintainer outreach before controlled work passes | Provides visible findings early. | It displaces the measurement spine and can bias the controlled study. | Remove optional work first; attempt one discovery slice only after every required G/Y deliverable is complete. |

## Fallback Deliverable Matrix

| Capability / Artifact | Green | Yellow | Red |
|-----------------------|-------|--------|-----|
| Pinned snapshots and 11-fixture deterministic runner | Required | Required | Required |
| Canonical adjudication, stable diagnostics, decomposed metrics, evidence audit | Required | Required | Required |
| Human-reviewed prototype bank | At least 6 defensible pairs; target 6–8 | At least 4 defensible pairs | Attempt and audit; fewer than 4 is an explicit Red reason |
| Strict family-disjoint core | At least 10 adjudicated cases | At least 6 adjudicated cases | Formation attempt and blocker are documented |
| Frozen family, split, gold, pair, relevance, prompt, model, and fallback artifacts | Required before retrieval/model calls | Required before retrieval/model calls | Record what could and could not be frozen; no unreliable gold is used for calls |
| A/B/C on every preregistered strict case | Required; normally 10–12 cases, one or two repeats | Required; 6–9 cases, one or two repeats | **Prohibited** |
| Three-axis and pair-retrieval metrics | Required | Required | Not claimed |
| Four metamorphic model evaluations | Required | Required | Not run when their labels/axes are unreliable |
| Headline outcome | Controlled positive or negative experiment result | Reduced controlled positive or negative experiment result; auxiliary separate | Reproducible feasibility assessment, explicitly not extraction-experiment success |
| Optional discovery and top-10 dossiers | Only after all required work passes | Skip by default; only after all required work passes | Not attempted |
| Upstream communication | Private draft at most; publication requires explicit human approval and upstream criteria | Same | None |

## Feature Dependencies

```text
[Pinned source snapshots]
    └──requires──> [Versioned PR #2164 adapter]
                       └──requires──> [11-fixture golden runner]
                                          ├──requires──> [Canonical schema + diagnostics]
                                          └──enables────> [Decomposed deterministic scoring]

[Human-reviewed family registry]
    ├──requires──> [Prototype pair assignments]
    └──requires──> [Held-out primary-family assignments]
                       └──enables────> [Strict family-disjoint split checks]

[Human-reviewed pair bank]
    ├──requires──> [Pair provenance + discriminating axes]
    └──requires──> [Preregistered pair relevance registry]
                       └──enables────> [Deterministic complete-pair retrieval]

[Golden runner + valid strict split + reviewed pairs + frozen registries]
    └──requires──> [Human Green/Yellow/Red gate]
                       ├──Green/Yellow──> [Frozen A/B/C prompts and settings]
                       │                     ├──A/B──> [H1 B-A ablation]
                       │                     └──B/C──> [H2 C-B ablation]
                       │
                       └──Red──────────> [No model calls]
                                            └──> [Runner + data audit + ambiguity report
                                                  + reproducible feasibility conclusion]

[Exactly three frame axes]
    ├──enables──> [System B]
    ├──enables──> [System C]
    ├──enables──> [Per-axis metrics and advisory warnings]
    └──enables──> [Four directional metamorphic pairs]

[Complete G/Y controlled result]
    └──may-enable──> [Optional discovery slice]
                         └──may-enable──> [Top-10 private review dossiers]
                                              └──requires explicit approval──> [Public communication]
```

### Dependency Notes

- **Measurement precedes innovation:** The runner must score all 11 golden fixtures before retrieval, prompt execution, or interpretation. Otherwise later results have no trusted measurement spine.
- **Human-reviewed data precedes the gate:** Labels, family assignments, pair definitions, discriminating axes, and relevance judgments must be reviewed before Green or Yellow can authorize calls.
- **Family registry precedes split validation:** “Family” cannot be chosen opportunistically after seeing overlap or results. Only `primary_family` determines strict isolation; secondary tags may overlap.
- **Pair bank precedes retrieval:** Retrieval operates on complete, manually verified units. It must never synthesize or pair independent examples at query time.
- **A/B control precedes H1 interpretation:** `B-A` is meaningful only when the same fixed pairs and shared harness are used.
- **B/C control precedes H2 interpretation:** `C-B` is meaningful only when pair selection is the sole changed intervention.
- **Red conflicts with real model execution:** Once Red is selected, model calls cannot be used to compensate for weak gold or insufficient data.
- **Optional work depends on a finished controlled result:** Discovery, dossiers, external packaging, and outreach cannot run in parallel with unfinished required work.

## MVP Definition

“MVP” here means the smallest artifact package that can answer the feasibility question defensibly. It does not mean a deployable product.

### Launch With — Mandatory Foundation for Every Path

- [ ] **Pinned-source manifest and isolated experiment skeleton** — fixes the evidence boundary and prevents coupling to unstable UDB internals.
- [ ] **Versioned PR #2164 adapter and 11-fixture golden runner** — proves the measurement spine before innovation.
- [ ] **Canonical adjudication parser, stable diagnostics, and orthogonal metrics** — makes outputs comparable and failures testable.
- [ ] **Verbatim evidence checks, raw-output retention, canonical reports, and hashes** — makes every score independently auditable.
- [ ] **Human-reviewed family/split/pair data audit and explicit fallback decision** — selects Green, Yellow, or Red without substituting model output for gold quality.

### Launch With — Green or Yellow Controlled Experiment

- [ ] **Threshold-satisfying pair bank and strict family-disjoint core** — Green uses at least 6 pairs and 10 strict cases; Yellow uses at least 4 pairs and 6 strict cases.
- [ ] **Exactly three required DelegationFrame axes** — no ontology expansion.
- [ ] **Deterministic complete-pair TF-IDF retrieval with preregistered relevance** — tests H2 without learned retrieval.
- [ ] **Frozen, treatment-controlled A/B/C harness** — exactly two demonstration pairs and shared cases/settings/rules.
- [ ] **Complete strict-core execution plus four human-reviewed metamorphic pairs** — no missing A/B/C cells.
- [ ] **Case-level positive or negative report and exact rerun instructions** — reports `B-A` and `C-B` without significance claims.

### Launch With — Red Feasibility Assessment

- [ ] **No real model experiment** — fail closed when gold, axes, pairs, or strict isolation are inadequate.
- [ ] **Documented public scoring-gap assessment and auditable construction attempt** — preserves what was learned.
- [ ] **Explicit Red trigger and ambiguity report** — shows why the experiment was not defensible.
- [ ] **Reproducible revised feasibility conclusion** — distinguishes successful feasibility assessment from extraction-experiment success.

### Add Only After Required G/Y Validation (Optional)

- [ ] **One controlled discovery slice of approximately 30–80 paragraphs** — only when required work is complete; no benchmark or recall claim.
- [ ] **Top-10 private review dossiers** — only for human inspection; no “new parameter” claim without maintainer adjudication.
- [ ] **Small external prototype repository or maintainer comment draft** — only after the controlled package passes and a human approves.
- [ ] **Issue or PR-ready branch** — only when all frozen upstream criteria are satisfied and maintainers confirm a useful gap.

### Future Consideration

No post-spike product capability is committed by the frozen baseline. Generic RAG, multi-agent extraction, full-corpus benchmarking, UDB emission, taxonomy redesign, and production service work remain out of scope unless a later milestone is separately scoped from new evidence.

## Feature Prioritization Matrix

| Capability Group | Reviewer Value | Implementation Cost | Priority | Path |
|------------------|----------------|---------------------|----------|------|
| Snapshot pinning and isolated boundary | HIGH | LOW | P1 | ALL |
| Fixture adapter and golden measurement runner | HIGH | HIGH | P1 | ALL |
| Canonical schema, diagnostics, evidence audit | HIGH | MEDIUM | P1 | ALL |
| Decomposed metrics and deterministic reproducibility | HIGH | HIGH | P1 | ALL |
| Provenance, family registry, strict split, relevance preregistration | HIGH | HIGH | P1 | ALL |
| Human review and Green/Yellow/Red change-control gate | HIGH | MEDIUM | P1 | ALL |
| Three-axis frame and `B-A` ablation | HIGH | HIGH | P1 | G/Y |
| Contrastive pair bank, deterministic retrieval, and `C-B` ablation | HIGH | HIGH | P1 | G/Y |
| Complete A/B/C call trace and four metamorphic pairs | HIGH | HIGH | P1 | G/Y |
| Red audit and revised feasibility conclusion | HIGH | MEDIUM | P1 | R |
| Optional discovery slice and dossiers | LOW | MEDIUM | P2 | OPT |
| External packaging or private maintainer draft | LOW | MEDIUM | P2 | OPT |
| Public Issue/PR-ready work | LOW during spike | HIGH | P3, approval-gated | OPT |

**Priority key:**

- **P1:** Required for the applicable outcome path.
- **P2:** Optional only after all P1 G/Y work passes; remove first when time is constrained.
- **P3:** Downstream contribution work, not part of feasibility success and never automatic.

## Treatment Capability Matrix

This matrix replaces a generic competitor comparison. The credible comparison is between the three frozen treatments.

| Controlled Capability | A — Direct-fixed | B — Frame-fixed | C — Frame-axis-retrieved |
|-----------------------|------------------|-----------------|--------------------------|
| Same held-out cases and target context | Yes | Yes | Yes |
| Same model snapshot, sampling, repeats, shared guidance, evidence rules, and final decision space | Yes | Yes | Yes |
| Exactly two complete contrastive demonstration pairs | Yes, fixed | Yes, same fixed pairs as A | Yes, retrieved per target |
| Required three-axis DelegationFrame | No | Yes | Yes, identical to B |
| Adjudication schema | Canonical shared schema | Canonical shared schema | Identical to B |
| Primary comparison enabled | Baseline | `B-A` tests H1 | `C-B` tests H2 |
| Natural frame-related token difference | Recorded, not padded | Recorded, not padded | Recorded, not padded |

## What a Reviewer Must Be Able to Observe

A requirement is complete only when a reviewer can verify it from committed experiment artifacts or deterministic command output:

1. Every source, case, family, pair, prompt, model setting, and prediction has a stable identity and provenance or hash.
2. Automated tests demonstrate fixture compatibility, canonical state enforcement, evidence matching, split isolation, retrieval determinism, prompt controls, and byte stability.
3. Human approvals and unresolved ambiguities are explicit records, not inferred from file presence.
4. Green/Yellow reports contain a complete case-by-system grid; Red reports contain no model outputs presented as experimental evidence.
5. Every aggregate metric can be traced to case-level outcomes and raw responses.
6. Optional and upstream artifacts are visibly separated from required feasibility deliverables.

## Sources

### Project-Authoritative

- [SpecChoice v1.3.2 frozen execution baseline](/Users/zhdeng/Downloads/LFX_RISCV_SpecChoice_v1.3.2_frozen_execution_baseline.md) — **HIGH confidence** for scope, thresholds, schemas, treatments, and path-specific deliverables; this is the execution contract.
- [Project definition](/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/.planning/PROJECT.md) — **HIGH confidence**; distilled milestone scope and constraints.
- [Codebase concerns audit](/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/.planning/codebase/CONCERNS.md) — **HIGH confidence** for the need to isolate the prototype from heuristic MCP search, unstable schemas, generated trees, and incomplete production controls.

### Supporting Primary Guidance

- [NIST AI Risk Management Framework Core](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/) — **MEDIUM confidence** after cross-checking; supports documented experimental design, repeatable TEVV, test-set/tool documentation, limitations, independent/domain-expert review, and human oversight.
- [OpenAI: A shared playbook for trustworthy third-party evaluations](https://openai.com/index/trustworthy-third-party-evaluations-foundations/) — **MEDIUM confidence** after cross-checking; supports consistent harnesses, explicit claim scope, contamination/shortcut checks, case review, and reporting of model, budget, tools, harness, and validity checks.
- [CDC: Considerations for Disclosing Generative AI Use in Scientific Work](https://www.cdc.gov/ai/resources/considerations-for-generative-ai-use-in-scientific-work.html) — **MEDIUM confidence** after cross-checking; supports recording model/version, prompts, settings, inputs, validation, and extent of human oversight, with humans retaining accountability.

---
*Feature research for: SpecChoice v1.3.2 controlled extraction feasibility spike*  
*Researched: 2026-07-30*
