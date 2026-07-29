# Pitfalls Research

**Domain:** Controlled LLM extraction feasibility experiments in a standards repository (SpecChoice v1.3.2 / RISC-V UnifiedDB)
**Researched:** 2026-07-30
**Confidence:** HIGH for project-specific requirements; MEDIUM for external methodological generalization

## Roadmap Phase Legend

The phase names below describe the earliest point at which each risk must be prevented:

1. **Source Snapshot and Measurement Contract** — pin public inputs, adapt fixtures, define canonical predictions, and prove deterministic scoring.
2. **Human-Reviewed Data Preregistration** — curate gold, pairs, families, splits, relevance judgments, and metamorphic cases under human authority.
3. **Frame, Retrieval, Parser, and Prompt Treatment** — implement the three-axis frame, complete-pair retrieval, strict parsing, and controlled prompts.
4. **Day-1 Gate and Frozen Run Manifest** — select Green, Yellow, or Red and hash every artifact that can affect a run.
5. **Controlled Model Execution** — execute the preregistered matrix, retain raw artifacts, and expose nondeterminism.
6. **Evaluation and Feasibility Reporting** — report case-level evidence, separate metrics and sets, and bound every conclusion.
7. **Optional Discovery and Upstream Decision** — only after required work; human approval remains mandatory for public action.

## Critical Pitfalls

### Pitfall 1: A Moving PR Head Becomes the Experimental Baseline

**Confidence:** HIGH

**What goes wrong:**
The implementation reads the current branch, current PR head, a merged variant, or locally generated files instead of the six exact public PR commit snapshots frozen by v1.3.2. Fixture counts, field names, prompt examples, or taxonomy then drift without an experiment-version change. Results can no longer be attributed to the stated public Part I baseline, and an open PR is accidentally treated as an accepted UnifiedDB interface.

**Why it happens:**
GitHub URLs and default branches are convenient; open PRs continue to evolve; UnifiedDB schemas and APIs change rapidly; generated files can look authoritative even when they came from a different configuration or commit.

**How to avoid:**
Create `config/source_snapshots.yaml` with repository, PR number, and exact commit SHA for every source. Fetch by commit, verify that each object exists, hash every consumed file, and make the PR #2164 adapter reject unknown fixture versions. Tests must assert the 11 pinned fixtures and their source hashes. Report the public artifacts as research inputs, never as accepted upstream interfaces.

**Warning signs:**
The manifest contains branch names or PR URLs without SHAs; a clean fetch changes a fixture; the adapter accepts multiple undocumented shapes; reports say “current pipeline” rather than “public Part I baseline”; generated files have no configuration/source identity.

**Recovery / change control:**
Quarantine all dependent reports and model outputs. Restore the pinned inputs or intentionally create a new experiment version, update the snapshot manifest and adapter, rerun the measurement spine, then rerun every affected system. Do not compare old and new snapshot results as one experiment.

**Phase to address:**
Phase 1 — Source Snapshot and Measurement Contract.

---

### Pitfall 2: Surfacing, Disposition, Candidate Semantics, and Identity Collapse into One Label

**Confidence:** HIGH

**What goes wrong:**
A single “correct/incorrect” score hides materially different outcomes. The PR #2164 candidate (`expect_extract=true`, count zero) is treated as an ordinary negative, `not_surfaced` is treated as a disposition, a true parameter classified out is confused with a missing finding, or an exact name is allowed to rescue an incorrect semantic decision.

**Why it happens:**
Flat classification metrics are easier to implement than the two-stage task. Legacy fixture fields look like one Boolean target, while the frozen experiment requires independent surfacing, disposition, identity, evidence, frame, and candidate diagnostics.

**How to avoid:**
Normalize fixture gold using `expect_extract`, `expected_parameter_count`, and `expected_parameter_names`. Enforce the canonical external state:

```yaml
surfaced: false
parameter_status: null
proposed_name: null
evidence_spans: []
```

When surfaced, require `accept`, `classify_out`, or `review`. Score SurfacingRecall, DispositionAccuracy, ExactIdentityAccuracy, ClassifyOutAccuracy, EvidenceSpanIntegrity, and frame axes separately. Golden and adversarial tests must assert the required stable diagnostic codes and verify that the candidate is surfaced and then classified out.

**Warning signs:**
One aggregate accuracy is the only output; `parameter_status: not_surfaced` appears; `review` silently counts as correct; candidate cases sit in a negative denominator; an exact name earns credit after the finding was not surfaced.

**Recovery / change control:**
Invalidate aggregate conclusions, repair the measurement contract, and regenerate reports from preserved raw predictions. If the faulty semantics affected prompts, retries, or model selection, increment the experiment version and rerun all systems.

**Phase to address:**
Phase 1 — Source Snapshot and Measurement Contract.

---

### Pitfall 3: Identity Is Used as a Gate on Architectural Disposition

**Confidence:** HIGH

**What goes wrong:**
A correctly accepted parameter with no canonical UDB name is scored as a semantic failure, while a guessed canonical name is treated as proof that the underlying passage is parameter-bearing. This biases the experiment toward known naming patterns and obscures whether DelegationFrame improved adjudication.

**Why it happens:**
Extraction systems often define success as emitting a named record. SpecChoice is narrower: it tests whether a passage should be surfaced and accepted or classified out, not complete UDB alignment.

**How to avoid:**
Permit `accept` with `proposed_name: null`. Emit `ACCEPTED_PARAMETER_NAME_MISSING` as an identity warning only. For correctly accepted positives, classify identity exactly once as `exact`, `incorrect`, or `missing`. Do not evaluate identity when the positive was classified out or not surfaced, and do not let identity change disposition correctness.

**Warning signs:**
Schema validation rejects a null name on `accept`; missing-name cases disappear from disposition denominators; exact-name accuracy uses all positives rather than correctly accepted positives; a known name overrides a wrong frame or disposition.

**Recovery / change control:**
Recompute disposition and identity from raw predictions with separate denominators. If the prompt required a name before `accept`, restore the frozen schema and rerun A/B/C because the treatment decision space was wrong.

**Phase to address:**
Phase 1 — measurement contract, verified again in Phase 3 prompt/schema tests.

---

### Pitfall 4: Silent Schema Repair Turns Model Failures into Apparent Success

**Confidence:** HIGH

**What goes wrong:**
The parser strips unknown keys, invents nulls, maps invalid enums, drops empty evidence, converts `parameter_status: not_surfaced`, or retries privately until one output parses. Schema compliance then looks better than it was, and semantic decisions may be changed by code rather than made by the model.

**Why it happens:**
“Be liberal in what you accept” is useful for product ingestion but invalid for measurement. YAML coercions, convenience defaults, and provider-specific structured-output helpers make repair easy to hide.

**How to avoid:**
Preserve the exact raw response before parsing. In strict mode, reject unknown top-level keys, invalid enums, noncanonical no-finding states, and empty evidence for surfaced findings. Save parser diagnostics separately with stable codes. The only allowed compatibility normalization is the explicitly documented pre-validation mapping from external `reject` to `classify_out`; it must be counted and visible. Do not issue an unplanned corrective retry.

**Warning signs:**
Parsed output cannot be traced to a raw-output hash; schema-invalid count is implausibly zero; parser code contains defaults or broad exception recovery; call counts exceed the preregistered matrix; malformed YAML receives a scored prediction.

**Recovery / change control:**
Restore raw outputs, classify repaired cases as parser failures, and regenerate scores. If repair caused additional model calls or changed prompts, the affected run is invalid: version the parser/prompt contract and rerun the complete A/B/C matrix, not only failed cells.

**Phase to address:**
Phase 1 for parser semantics; Phase 3 for strict model-output integration.

---

### Pitfall 5: Data Curation Is Delegated Back to the Model

**Confidence:** HIGH

**What goes wrong:**
Model output is used to create or “fix” gold labels, fill an eight-pair quota, decide family membership, select evidence, resolve uncertain RISC-V semantics, or manufacture metamorphic transformations. The evaluator and evaluated system then share the same errors, and human review becomes ceremonial.

**Why it happens:**
The three-day window creates pressure to fill the bank quickly. RISC-V passages are technically subtle, and model-generated labels can look polished enough to avoid scrutiny.

**How to avoid:**
Require provenance, source snapshot, verbatim evidence, explicit shared structure, discriminating axes, and `manually_verified: true` for every prototype. Human reviewers own dataset membership, labels, primary family, pair axes, relevance, fallback state, and unresolved decisions. Accept six defensible pairs instead of fabricating eight. Exclude genuinely unresolved discovery items from headline gold.

**Warning signs:**
Every planned pair exists despite weak source material; rationales share model-like phrasing; no reviewer/sign-off record exists; evidence cannot be located verbatim; disputed labels are “resolved” without a named human decision.

**Recovery / change control:**
Quarantine unreviewed items, reconstruct them from pinned source, and repeat human adjudication. Downgrade Green to Yellow or Red when thresholds are no longer met. Never relax the threshold or run the model merely to compensate for weak gold.

**Phase to address:**
Phase 2 — Human-Reviewed Data Preregistration.

---

### Pitfall 6: Example-Disjoint Splits Still Leak the Decisive Family

**Confidence:** HIGH

**What goes wrong:**
Prototype and held-out passages have different IDs but share the same CSR family, wording template, conceptual rule, or near-duplicate technical structure. Retrieval or fixed demonstrations reveal the decisive boundary, inflating apparent generalization. Families are then redefined after outputs to make the overlap disappear.

**Why it happens:**
Exact text overlap is easy to test; semantic-family overlap requires RISC-V judgment. A passage can have several plausible groupings, inviting post-hoc choice of the most favorable one.

**How to avoid:**
Freeze `data/family_registry.yaml` before retrieval. Give each example one preregistered `primary_family`; use only that field for isolation. Secondary tags may overlap but cannot waive the invariant. Automated tests must fail on example overlap, strict primary-family overlap, unregistered families, or registry-version mismatch. Keep the strict family-disjoint core separate from any example-disjoint auxiliary set.

**Warning signs:**
Family definitions reference model behavior; the same semantic rule appears on both sides with different names; assignments change after retrieved ranks are visible; split tests check only hashes or IDs; secondary tags drive exceptions.

**Recovery / change control:**
Stop the run, version the family registry and split manifest, rebuild the strict core, and rerun retrieval and all model systems. If no defensible strict core remains, select Red and deliver the auditable data-quality feasibility result.

**Phase to address:**
Phase 2 — Human-Reviewed Data Preregistration.

---

### Pitfall 7: Retrieval Relevance Is Judged After Seeing the Ranking

**Confidence:** HIGH

**What goes wrong:**
A retrieved pair is added to the relevant set after it ranks highly or improves a model answer. Cases without an obvious relevant pair are quietly omitted. Independent positive and negative examples are retrieved instead of an explicit complete contrastive unit. `PairHit@K` becomes a description of observed ranks rather than an evaluation.

**Why it happens:**
Contrastive relevance is subjective and expensive to label. With few cases, changing one relevance judgment can move the metric sharply.

**How to avoid:**
Human-review and hash `data/pair_relevance_registry.yaml` before running the retriever. Require `judged_before_retrieval: true`, case ID, relevant pair IDs, and rationale. Exclude cases with no preregistered judgment from the PairHit denominator, but still list their retrieved pair IDs. Retrieve complete positive/contrast pairs with deterministic tie-breaking. Keep optional candidate discovery distinct from demonstration retrieval; never suppress a candidate merely because it resembles a hard negative.

**Warning signs:**
Registry timestamps or hashes postdate retrieval; relevance rationales mention rank or output; only successful cases have judgments; positive and contrast examples have different pair IDs; candidate ranking subtracts hard-negative similarity.

**Recovery / change control:**
Invalidate PairHit@K and any C−B explanation based on the contaminated judgments. Freeze a new registry version without access to prior ranks where feasible, then rerun retrieval and C/B. If unbiased re-judgment is no longer credible, report retrieval relevance as unevaluated.

**Phase to address:**
Phase 2 for preregistration; Phase 3 for complete-pair and task-separation tests.

---

### Pitfall 8: The Three-Axis Hypothesis Quietly Expands

**Confidence:** HIGH

**What goes wrong:**
`scope`, `normativity`, confidence, taxonomy alignment, or a generated rationale becomes required input to B/C or part of the headline score. Advisory frame-combination diagnostics change correctness. The experiment no longer isolates the frozen DelegationFrame hypothesis.

**Why it happens:**
Additional metadata appears useful during error analysis, and the temptation is to turn every useful observation into another model requirement.

**How to avoid:**
Require exactly `authority`, `choice_object`, and `choice_space_origin`, each with evidence. Allow `unknown`. Treat all optional metadata as secondary and exclude it from the primary comparison. Generate `FRAME_COMBINATION_REQUIRES_REVIEW` only from the preregistered advisory-pattern file; it is non-blocking and cannot alter axis or disposition scores. Guidance may suggest likely outcomes but code must not hard-code the guidance as gold.

**Warning signs:**
B/C schemas gain required fields; a single averaged frame score hides axes; advisory warnings reduce accuracy; `unknown` is forbidden; a code rule converts a frame directly to `accept`.

**Recovery / change control:**
Restore the minimal schema and regenerate prompts. Because treatment content changed, rerun B and C from the beginning. If reviewers cannot label the required axes consistently, select Red rather than adding substitute axes.

**Phase to address:**
Phase 3 — Frame, Retrieval, Parser, and Prompt Treatment.

---

### Pitfall 9: Prompt or Token Differences Become an Unnamed Second Treatment

**Confidence:** HIGH

**What goes wrong:**
A/B/C differ in demonstration count, example format, target context, shared rules, evidence requirements, decision space, maximum output, repeats, model snapshot, or sampling. System A is padded with “neutral” text to match B, or B/C differ beyond fixed versus retrieved pair selection. An observed delta cannot be attributed to DelegationFrame or retrieval.

**Why it happens:**
Rendered prompts are assembled through separate code paths, token equality looks like fairness, and frame output legitimately needs more space.

**How to avoid:**
Build prompts from shared immutable components and snapshot the fully rendered prompt for every cell. Use exactly two complete contrastive pairs in all systems. A and B use the same fixed pairs; B and C share frame/adjudication instructions and output schema; C differs from B only in pair selection. Keep target context, model snapshot, sampling, evidence rules, and repeats fixed. Record natural input-token differences—do not pad. Use one output cap when safe; otherwise preregister and report the necessary frame-specific cap.

**Warning signs:**
Prompt diffs include unrelated prose; one system has extra examples or reminders; token counts are identical because of filler; truncations cluster in B/C; API defaults are omitted; B and C use different parser settings.

**Recovery / change control:**
Invalidate the affected ablation, fix the shared prompt assembler, refreeze hashes and settings, and rerun every system/case/repeat cell needed for the comparison. Do not patch only the losing condition.

**Phase to address:**
Phase 3, frozen and rechecked in Phase 4.

---

### Pitfall 10: Green/Yellow/Red Is Used as a Schedule Label Rather Than an Evidence Gate

**Confidence:** HIGH

**What goes wrong:**
Green is declared with missing reviews, Yellow is used to authorize a sub-threshold or family-overlapping set, or real model calls continue after a Red trigger. Conversely, Red is described as project failure even when the runner and auditable data assessment satisfy the independent Red success criteria. `N_strict` or repeat count is selected after observing outcomes.

**Why it happens:**
Teams feel pressure to “get to the model,” and traffic-light labels can become subjective status language unless encoded as prerequisites.

**How to avoid:**
Implement a deterministic gate report that checks the exact frozen thresholds. Require human sign-off for labels, family assignments, pairs, relevance, and fallback state. Freeze and hash the selected state, `N_strict`, and repeat count before the first call. Green authorizes the full matrix; Yellow authorizes only the reduced strict core with auxiliary results separate; Red prohibits real model experimentation. Evaluate Red against its own reproducible feasibility-assessment criteria.

**Warning signs:**
The gate exists only in notes; missing pair relevance is waived; model logs predate gate approval; the strict-core size differs across reports; a Red package is called “failed” despite an auditable runner/data conclusion.

**Recovery / change control:**
Stop model calls immediately and quarantine unauthorized outputs. Recompute the gate from frozen evidence. Downgrade to Yellow or Red as required. A later upgrade needs completed review, a new manifest/version, and a fresh full run; prior exploratory outputs cannot enter the controlled analysis.

**Phase to address:**
Phase 4 — Day-1 Gate and Frozen Run Manifest.

---

### Pitfall 11: Frozen Artifacts Drift Mid-Run

**Confidence:** HIGH

**What goes wrong:**
Gold, family assignments, pair files, relevance, prompts, advisory patterns, model settings, or parser code changes after some cells run. Results are assembled as if one experiment occurred, although different cases saw different contracts.

**Why it happens:**
Errors are often discovered only during execution, and a small “obvious fix” feels cheaper than restarting.

**How to avoid:**
Before retrieval or model calls, hash the family registry, split manifest, relevance registry, prototype pairs, held-out gold, metamorphic pairs, prompts, advisory patterns, model/sampling configuration, adjudication schema, gate state, `N_strict`, and repeats. At every run start, verify the full manifest. Make run directories immutable and keep decision-log entries outside canonical result payloads.

**Warning signs:**
Case timestamps span file modifications; manifest hashes are missing or recomputed in place; only changed cases are rerun; report rows reference multiple prompt hashes without an explicit experiment-version boundary.

**Recovery / change control:**
Stop the current run, log the reason, increment the experiment version, refreeze every affected artifact, and rerun all affected systems from the beginning. Never splice pre-change and post-change cells into one headline result.

**Phase to address:**
Phase 4 — Day-1 Gate and Frozen Run Manifest.

---

### Pitfall 12: API Nondeterminism Is Mistaken for Reproducibility

**Confidence:** HIGH for the required controls; MEDIUM for provider-specific behavior

**What goes wrong:**
A model alias moves, temperature zero or a seed is assumed to guarantee identical output, raw responses are discarded, or only the best repeat is retained. Re-execution differs and there is no way to distinguish stochastic variation from a changed prompt, backend, or parser.

**Why it happens:**
Generative APIs are convenient but variable. Provider-side configuration can change, and a deterministic scorer can create the false impression that the generation step was deterministic too.

**How to avoid:**
Pin the model snapshot, explicitly set every sampling and output-limit parameter, record request IDs or equivalent backend fingerprints when available, and hash rendered prompts. Preserve raw response, parsed output, parser diagnostics, input/output tokens, finish reason, truncation, and model metadata for every call. Run the same preregistered repeat count for every strict-core cell and report disagreements. Canonical reports must be byte-stable for equivalent captured inputs, not promise identical future generations.

**Warning signs:**
The configuration says `latest`; omitted parameters rely on defaults; reruns overwrite prior output; repeat disagreement is absent; raw and parsed artifacts have no linkage; timestamps or absolute paths leak into canonical JSON.

**Recovery / change control:**
If captured artifacts are complete, regenerate deterministic reports without new calls. If prompts, raw output, or model identity are missing, reproducibility claims and paired comparisons are invalid; refreeze the run and execute the entire required matrix again.

**Phase to address:**
Phase 4 for provenance design; Phase 5 for execution enforcement.

---

### Pitfall 13: The Auxiliary Set Is Mixed into the Strict-Core Headline

**Confidence:** HIGH

**What goes wrong:**
Example-disjoint auxiliary cases—whose primary families may overlap the prototype bank—are pooled with the strict family-disjoint core. Different systems or repeats cover different subsets. A larger denominator produces a smoother but less valid headline metric.

**Why it happens:**
The strict core is deliberately small, and combining all available cases appears to improve sample size.

**How to avoid:**
Represent strict and auxiliary sets as separate manifest keys, run IDs, report sections, denominators, and tables. Require A/B/C coverage on every preregistered strict case for experimental success. Label auxiliary results exploratory and never average or weight them into strict-core metrics. Report `N_strict`, `N_aux`, fallback state, repeats, and missing cells explicitly.

**Warning signs:**
One accuracy denominator equals strict plus auxiliary counts; report rows lack a split field; strict metrics change when auxiliary cases are added; a system is compared on a favorable subset.

**Recovery / change control:**
Recalculate all metrics from case-level raw artifacts with split-specific denominators. Retract mixed headlines. If split identity was not preserved, the analysis cannot be recovered reliably and the affected run must be regenerated from the frozen manifest.

**Phase to address:**
Phase 2 in manifest design; Phase 6 in report acceptance tests.

---

### Pitfall 14: Evidence-Span Presence Is Reported as Semantic Support

**Confidence:** HIGH for SpecChoice semantics; MEDIUM from attribution research

**What goes wrong:**
A verbatim span exists in the source, so the accepted parameter or frame is declared correct even though the span is irrelevant, incomplete, or supports the opposite authority/choice-space interpretation. Evidence integrity is advertised as entailment.

**Why it happens:**
Substring verification is deterministic and produces an attractive percentage. Semantic support requires expert interpretation and does not fit the three-day automated scorer.

**How to avoid:**
Define EvidenceSpanIntegrity only as the fraction of submitted spans found verbatim in the pinned source. Keep semantic disposition and frame-axis correctness independent and human-reviewed. Emit `EVIDENCE_SPAN_EMPTY` and `EVIDENCE_SPAN_NOT_FOUND` without converting other outcomes. Include “valid evidence but unsupported inference” in failure analysis. Do not add generic semantic-entailment automation to the frozen scope.

**Warning signs:**
Reports use “grounded,” “proved,” or “semantically correct” as synonyms for a found span; fabricated evidence is the only evidence failure category; an accepted result passes solely because a keyword span exists.

**Recovery / change control:**
Correct the report language, separate integrity from semantic outcomes, and send questionable cases to the human reviewer. Recompute metrics if evidence had altered disposition. Do not use an automated entailment patch to preserve the old headline.

**Phase to address:**
Phase 1 for metric definition; Phase 6 for claim review.

---

### Pitfall 15: Four Metamorphic Cases Become Post-Hoc Prompt Tuning

**Confidence:** HIGH

**What goes wrong:**
Transformations are model-generated, edited after seeing responses, or repeatedly used to tune prompts before being presented as held-out consistency evidence. The expected directional relation is changed to fit actual outputs.

**Why it happens:**
Minimal pairs reveal failures quickly and are tempting debugging fixtures. With only four pairs, one changed judgment materially changes the result.

**How to avoid:**
Human-review the four required transformations and their axis/decision relations before model execution. Store and hash source A, source B, provenance, expected axes, and expected direction. Evaluate direction, not merely whether any label changed. Treat them as frozen evaluation artifacts; create separate development fixtures for parser/prompt debugging.

**Warning signs:**
Metamorphic file hashes postdate prompt changes; rationales mention observed model output; transformations contain stylistic differences beyond the intended axis; results report only absolute accuracy.

**Recovery / change control:**
Invalidate metamorphic claims, version and re-review the pairs, and rerun all systems on all four pairs. If an unbiased evaluation can no longer be defended, report them as qualitative development examples only.

**Phase to address:**
Phase 2 for curation and freeze; Phase 6 for directional analysis.

---

### Pitfall 16: A Tiny Controlled Spike Is Written Up as a General Breakthrough

**Confidence:** HIGH

**What goes wrong:**
Six to twelve strict cases are used to claim statistical significance, full-corpus recall improvement, confirmed new parameters, superiority over a private/internal pipeline, or a general UDB taxonomy solution. Best repeats or favorable failure families are highlighted while null and negative outcomes disappear.

**Why it happens:**
Percentage changes look large at small denominators, and positive narratives are perceived as more valuable than feasibility evidence.

**How to avoid:**
Make the case-level paired table primary. Report counts and denominators with every percentage, all repeat disagreements, each frame axis, shortcut failures, parser failures, and limitations. Interpret B−A and C−B descriptively. Do not perform or claim statistical significance. Treat B≤A, C≤B, unstable retrieval, or an unreliable frame axis as valid negative results when controls and raw evidence are intact.

**Warning signs:**
The abstract omits `N_strict`; “significant” appears without a preregistered valid test; only mean accuracy is shown; thresholds are optimized after labels are visible; Red or negative results are described as unsuccessful work.

**Recovery / change control:**
Retract or narrow unsupported claims, restore all cases/repeats, and rewrite the conclusion as a bounded feasibility result. Preserve the negative finding; do not start prompt optimization or recurate gold to force a positive result within the same version.

**Phase to address:**
Phase 6 — Evaluation and Feasibility Reporting.

---

### Pitfall 17: Optional Discovery and Upstream Work Start Before the Experiment Is Defensible

**Confidence:** HIGH

**What goes wrong:**
Top-10 discovery dossiers, core UnifiedDB integration, a public Issue, maintainer comment, or PR consume time before the runner, split, gate, and controlled run are complete. Public wording implies accepted interfaces, novelty over an unknown private pipeline, or confirmed architectural parameters.

**Why it happens:**
Upstream artifacts are visible deliverables, while a Red result or negative ablation can feel less tangible. The repository also lacks an established SpecChoice module, inviting premature placement decisions.

**How to avoid:**
Keep the prototype self-contained under `experiments/specchoice-v1.3.2/` and dependency-light. Cut optional discovery first when constrained. Require completion of all Green/Yellow deliverables before discovery. Require explicit human approval for every public action and satisfy the frozen upstream criteria: passing deterministic runner and splits, complete A/B/C, no active-PR duplication, maintainer-confirmed gap/invitation, and a small explainable diff. If existing internal work covers the idea, position results as independent validation, not novelty.

**Warning signs:**
Core UDB schemas or generators change during the spike; a maintainer draft is treated as a required report; discovery starts before complete strict-core coverage; public copy says “current pipeline”; a PR is planned after Red.

**Recovery / change control:**
Stop optional and public work. Preserve drafts locally. If a public action already occurred, notify the human reviewer, correct unsupported claims through an approved response, and do not delete or rewrite public history unilaterally. Return to the required feasibility package; upstream work becomes a separately approved follow-up.

**Phase to address:**
Phase 7 — Optional Discovery and Upstream Decision, with a “no earlier public work” guard in every prior phase.

## Technical Debt Patterns

Shortcuts that appear to save time but undermine the experiment contract.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Parse the current PR #2164 shape directly | Avoids a versioned adapter | Snapshot drift silently changes gold semantics | Never |
| Emit one aggregate accuracy | Simple report | Conceals surfacing, disposition, identity, evidence, and candidate failures | Never for headline results |
| Repair invalid model output | Fewer parser failures | Converts model/schema failure into evaluator behavior | Never; only the documented `reject` compatibility mapping may run before strict validation |
| Define families in the split file only | Fewer artifacts | No stable definition or auditable change control | Never |
| Reuse held-out examples as “helpful” demonstrations | Better apparent accuracy | Direct leakage invalidates the experiment | Never |
| Add embeddings, rerankers, or prompt optimization | May improve raw performance | Adds uncontrolled treatments and defeats the frozen hypothesis | Never in v1.3.2 |
| Add optional frame fields to the required schema | Richer analysis | Changes B/C treatment and increases parse burden | Only as non-primary metadata frozen before execution |
| Use the existing MCP fuzzy search as architecture truth | Fast integration | Mixes configurations, uses heuristic XLEN, and can truncate before ranking | Only for read-only discovery with explicit caveats; never for gold or validation |
| Run through the entire UDB generation/toolchain | Reuses repository infrastructure | Setup and mutable generated state consume the timebox and add failure modes | Only if `bin/doctor` already passes and no core coupling is introduced |
| Inline prompts in orchestration code | Quick prototype | Rendered treatment cannot be diffed, frozen, or hashed cleanly | Never for the controlled run |
| Keep only parsed responses | Smaller artifacts | Parser changes and model behavior cannot be audited | Never |
| Pool strict and auxiliary cases | Larger-looking sample | Family leakage enters the headline | Never |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| GitHub public PR snapshots | Fetch the live PR head or default branch | Resolve and verify the exact frozen commit SHA; hash consumed files |
| PR #2164 fixtures | Assume fields are a stable API | Use a versioned adapter and fail with `FIXTURE_VERSION_MISMATCH` |
| UnifiedDB generated trees | Search all of `gen/` as one database | Use only an explicit pinned/configuration-scoped source; do not use mixed MCP results as gold |
| UnifiedDB resolvers | Reuse a long-lived process across regeneration | For this spike, avoid regeneration; otherwise use an immutable snapshot and restart/invalidate caches |
| Auto-generated YAML | Patch generated read-only variants | Do not modify core data for the spike; if later required, edit the owning `.layout` and regenerate |
| YAML/JSON parsing | Permit implicit coercion, defaults, or unknown keys | Parse, validate strictly, preserve raw bytes, and emit structured diagnostics |
| Model API | Use a moving model alias and provider defaults | Pin the snapshot, set parameters explicitly, capture request/model metadata and finish reason |
| Structured-output mode | Assume valid structure implies correct values | Still validate semantics, evidence, enums, truncation/refusal, and preserve raw output |
| TF-IDF retrieval | Fit on held-out labels or retrieve passages independently | Fit only on frozen prototype representations and return complete pair IDs with stable ties |
| Report serialization | Include runtime timestamps and absolute paths | Put volatile metadata in a separate manifest; canonical core JSON uses stable sorting, UTF-8/LF, and NFC |

## Performance Traps

The expected scale is small, so the dominant performance risks are experiment distortion and timebox loss rather than production throughput.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Unbounded parser/model retries | Call counts differ by system and hard cases get more chances | No unplanned retries; record failures as outcomes | On the first extra call |
| Refitting retrieval per case or run | Pair ranks change with evaluation order | Fit once on the frozen prototype bank and hash vocabulary/config | As soon as target data influences the fit |
| Parallel calls without stable cell IDs | Responses attach to the wrong case/repeat after timeout | Preallocate `(case, system, repeat)` IDs and write atomically | At the first timeout or out-of-order response |
| Full repository scans for every case | Timebox is spent parsing thousands of YAML files | Materialize only pinned passages and provenance in the isolated dataset | Immediately in the three-day spike |
| Running optional discovery before required coverage | Strict matrix remains incomplete on Day 3 | Enforce the priority chain and cut work from the right | When any required cell is missing |
| Rebuilding the whole UDB toolchain after 90 minutes | No measurement spine by Day 1 | Follow the dependency-light fallback | At the frozen 90-minute stop rule |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Commit API keys or real provider configuration | Credential disclosure through the public repository or run artifacts | Commit only `model.example.yaml`; load credentials from the environment and scrub manifests |
| Treat specification/source text as executable prompt instructions | Source text can influence the evaluator outside the extraction task | Delimit source as data, keep system rules fixed, and never let source content alter tools, files, or run policy |
| Reuse the MCP path/regex surface for untrusted input | Known containment and regex resource risks can expose files or block execution | Do not expose it in SpecChoice; consume explicit pinned paths only |
| Follow links or includes from untrusted overlays during evaluation | Remote fetch or local include behavior can cross the intended source boundary | Disable remote resolution and enforce repository/snapshot containment |
| Automatically create Issues, comments, branches, or PRs | Unauthorized public state change and premature claims | Human approval is mandatory; public writes are outside the controlled run |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| One “accuracy” number | Human reviewers cannot see which architectural judgment failed | Lead with the case-level A/B/C table and separate metric families |
| Human-readable errors without stable codes | Results cannot be regression-tested or grouped reliably | Stable code plus structured case/finding fields; prose is secondary |
| Evidence without source anchor/hash | Reviewer cannot reproduce the span check | Show pinned source, section/anchor, exact span, and source hash |
| Red shown as an error screen | A conservative feasibility success looks like incomplete work | Present Red criteria, audited blockers, runner result, and revised feasibility conclusion |
| Missing decision log | Reviewers cannot distinguish preregistered choices from later changes | Record versioned decisions, exclusions, failures, and reasons not to upstream |
| Aggregate repeat means only | Nondeterminism and brittle cases disappear | Show every repeat disagreement and retain raw output links |

## "Looks Done But Isn't" Checklist

- [ ] **Source pins:** Every public artifact has a repository, PR number, exact commit SHA, consumed-file hash, and successful verification.
- [ ] **Fixture adapter:** All 11 pinned fixtures score from golden predictions, and schema/version mismatches fail explicitly.
- [ ] **Canonical no-finding state:** `surfaced=false` always implies null status/name and empty evidence; `parameter_status: not_surfaced` is rejected.
- [ ] **Candidate semantics:** The PR #2164 candidate is surfaced and classified out, not accepted, ignored, or folded into an ordinary negative.
- [ ] **Metric separation:** Surfacing, disposition, identity, classify-out, evidence, frame axes, retrieval, and stability each have their own denominator.
- [ ] **Identity independence:** Missing name warns but does not change correct `accept`; a correct name cannot rescue a wrong disposition.
- [ ] **Raw preservation:** Every parsed prediction and diagnostic links to an immutable raw response hash.
- [ ] **Strict parsing:** Unknown keys, invalid enums, empty surfaced evidence, truncation, and conflicts remain visible failures; no silent repair/retry exists.
- [ ] **Human authority:** Labels, membership, families, pair axes, relevance, fallback state, and public communication have recorded human review.
- [ ] **Pair quality:** At least the fallback-required number of defensible complete contrastive pairs exists; no pair was fabricated to meet a target.
- [ ] **Family isolation:** Exact example overlap is empty and prototype primary-family IDs do not intersect the strict core.
- [ ] **Auxiliary isolation:** The example-disjoint auxiliary set has separate run IDs, tables, denominators, and conclusions.
- [ ] **Relevance preregistration:** PairHit@K uses only human-reviewed judgments frozen before retrieval; unjudged cases are excluded from its denominator.
- [ ] **Retrieval semantics:** Complete pairs are retrieved deterministically; held-out items are not candidates; discovery ranking remains a separate task.
- [ ] **Frame freeze:** Exactly three required axes exist; `unknown` is allowed; advisory combination warnings never alter correctness.
- [ ] **Prompt isolation:** A/B/C use equal pair counts, identical shared rules/context/settings, and the correct A−B and B−C single-treatment differences.
- [ ] **Token accounting:** Actual input/output tokens, maximum output, finish reason, and truncation are recorded; no neutral padding is used.
- [ ] **Gate authorization:** Green/Yellow/Red, `N_strict`, repeats, and human sign-off are frozen before any model call.
- [ ] **Artifact freeze:** All listed data, prompts, schemas, patterns, and settings are hashed; no run combines pre-change and post-change cells.
- [ ] **Run completeness:** Every preregistered strict case has A/B/C results for the selected repeat count, or the experiment stops and reports the gap.
- [ ] **Metamorphic integrity:** Four human-reviewed pairs remain frozen and are scored for required directional change.
- [ ] **Evidence language:** EvidenceSpanIntegrity is described only as verbatim span auditability, never semantic entailment.
- [ ] **Canonical output:** Equivalent captured inputs produce byte-identical core JSON with stable sorts, UTF-8/LF, NFC, and no timestamp/absolute path.
- [ ] **Bounded claims:** Reports state case counts and limitations and make no statistical-significance, full-corpus, private-pipeline, or confirmed-parameter claim.
- [ ] **Negative/Red validity:** Negative ablations and Red feasibility success are documented as legitimate outcomes when their own criteria pass.
- [ ] **Upstream restraint:** Optional discovery and all public actions remain downstream of required work and explicit human approval.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Snapshot drift | HIGH | Restore pins or version inputs; rerun measurement and every dependent system |
| Collapsed measurement semantics | MEDIUM–HIGH | Repair scorer and reports from raw; rerun if prompt/decision space was affected |
| Identity/disposition conflation | MEDIUM | Recompute separate metrics; rerun if prompts made naming mandatory |
| Silent schema repair | HIGH | Reclassify parser failures; rerun full matrix if repairs/retries changed calls |
| Model-curated gold | HIGH | Quarantine, human-relabel, rebuild gate; choose Yellow/Red if thresholds fail |
| Family leakage | HIGH | New family/split version; rerun retrieval and all model cells |
| Post-hoc relevance | HIGH | Invalidate PairHit/C−B explanation; new blinded registry and rerun, or report unevaluated |
| Frame/schema creep | HIGH | Restore three axes; refreeze and rerun B/C |
| Prompt/token confound | HIGH | Fix shared assembler and rerun complete comparison symmetrically |
| Gate abuse | HIGH | Stop/quarantine calls; recompute gate; downgrade or start a new authorized version |
| Mid-run artifact drift | HIGH | Stop, log, version, refreeze, and restart all affected systems |
| Missing reproducibility artifacts | HIGH | Recover raw/metadata if possible; otherwise rerun full required matrix |
| Strict/auxiliary mixing | LOW–MEDIUM | Recompute from preserved split-tagged cases; rerun if tags were lost |
| Evidence overclaiming | LOW–MEDIUM | Correct claims, separate metrics, route semantic questions to humans |
| Metamorphic tuning | MEDIUM–HIGH | Re-review/version pairs and rerun; otherwise downgrade to qualitative examples |
| Small-sample overclaiming | LOW if raw data exist | Restore case-level data and narrow conclusion; do not optimize into a positive result |
| Premature upstream action | HIGH reputational cost | Stop, notify human reviewer, make only approved corrections, move follow-up out of spike |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Moving PR snapshot | Phase 1 | Exact SHAs and file hashes; 11-fixture contract test |
| Measurement collapse | Phase 1 | Golden/adversarial tests assert independent metrics and stable codes |
| Identity/disposition conflation | Phase 1 | Null-name `accept` remains disposition-correct; identity has its own denominator |
| Silent schema repair | Phases 1 and 3 | Raw-to-parsed lineage; invalid fixtures remain explicit parser failures |
| Model-curated gold | Phase 2 | Provenance plus recorded human review for every gold/pair decision |
| Family leakage | Phase 2 | Automated example and strict primary-family intersection tests |
| Post-hoc relevance | Phases 2 and 3 | Registry hash predates retrieval; complete-pair retrieval tests |
| Frame/schema creep | Phase 3 | Schema permits exactly three required axes; advisories are non-blocking |
| Prompt/token confound | Phases 3 and 4 | Rendered prompt structural diff and frozen token/settings manifest |
| Green/Yellow/Red abuse | Phase 4 | Machine-readable threshold report plus human gate sign-off |
| Mid-run artifact drift | Phase 4 | Pre-call manifest verification; immutable run directories |
| API nondeterminism hidden | Phases 4 and 5 | Pinned model/settings, raw responses, all repeats and disagreements |
| Auxiliary metric mixing | Phases 2 and 6 | Separate IDs, denominators, tables, and report acceptance test |
| Evidence overclaiming | Phases 1 and 6 | Integrity metric wording test and human semantic review |
| Metamorphic post-hoc tuning | Phases 2 and 6 | Frozen hashes and directional-relation report for all four pairs |
| Small-sample overclaiming | Phase 6 | Case-level paired table, counts, limitations, prohibited-claim review |
| Premature upstream work | Phase 7 | Required deliverables complete and explicit human approval recorded |

## Sources

### Project-primary sources

- **[HIGH]** `/Users/zhdeng/Downloads/LFX_RISCV_SpecChoice_v1.3.2_frozen_execution_baseline.md` — authoritative frozen experiment contract, including canonical schema, metrics, gates, change control, and upstream policy.
- **[HIGH]** [Project definition](../PROJECT.md) — milestone objective, active constraints, accepted negative/Red outcomes, and human-review authority.
- **[HIGH]** [Codebase concerns](../codebase/CONCERNS.md) — UnifiedDB schema churn, generated-state risks, MCP configuration mixing, stale caches, and absent SpecChoice boundary.
- **[HIGH]** [RISC-V UnifiedDB repository](https://github.com/riscv/riscv-unified-db) — official upstream project and contribution context.
- **[HIGH]** Frozen public inputs: [PR #1765 commit](https://github.com/riscv/riscv-unified-db/commit/8117d9a24e276e5ae21423dea2640b78db5924fe), [PR #1766 commit](https://github.com/riscv/riscv-unified-db/commit/3d03d48bde785e81220a2db3932b811422377ecf), [PR #2097 commit](https://github.com/riscv/riscv-unified-db/commit/72d18f75f5875f2d7b01027c6e2765084ac38283), [PR #2164 commit](https://github.com/riscv/riscv-unified-db/commit/22e84458c87a7ccf4c07034de1eb6d0bf9764144), [PR #2192 commit](https://github.com/riscv/riscv-unified-db/commit/4bdaa4be1a404f78ff5b2841edd535afb637566b), and [PR #1831 commit](https://github.com/riscv/riscv-unified-db/commit/e9f6b9a9d0094cbbf3b99bb24a1ca578a364aff6).

### External methodological sources

- **[MEDIUM, cross-checked]** [APS preregistration guidance](https://www.psychologicalscience.org/publications/psychological_science/preregistration) — freeze hypotheses, materials, measures, exclusions, and analysis plans before analysis; disclose deviations.
- **[MEDIUM, cross-checked]** [Benchmark Data Contamination of Large Language Models: A Survey](https://arxiv.org/abs/2406.04244) and [An Open-Source Data Contamination Report for Large Language Models](https://aclanthology.org/2024.findings-emnlp.30/) — benchmark overlap and near-duplicate exposure can make evaluation unreliable; preserve transparent case-level evidence.
- **[MEDIUM, primary research]** [Deduplicating Training Data Makes Language Models Better](https://research.google/pubs/deduplicating-training-data-makes-language-models-better/) — near duplicates alter learned distributions, supporting stronger-than-exact-match leakage checks.
- **[MEDIUM, official]** [OpenAI API backward compatibility](https://developers.openai.com/api/reference/overview#backwards-compatibility) and [reproducible outputs cookbook](https://developers.openai.com/cookbook/examples/reproducible_outputs_with_the_seed_parameter) — pin snapshots and parameters; seeds improve but do not guarantee repeatability.
- **[MEDIUM, official]** [JSON Schema implementation interfaces](https://json-schema.org/implementers/interfaces) — validation returns valid/invalid outcomes or errors; it is not silent semantic transformation.
- **[MEDIUM, official]** [OpenAI Structured Outputs](https://openai.com/index/introducing-structured-outputs-in-the-api/) — schema-constrained output does not prevent semantic value errors, refusals, or truncation and does not eliminate the need for audit artifacts.
- **[MEDIUM, peer-reviewed]** [Quantifying Language Models’ Sensitivity to Spurious Features in Prompt Design](https://proceedings.iclr.cc/paper_files/paper/2024/hash/6c0e99d736da621403018ca7b32b1a4d-Abstract-Conference.html) — few-shot performance can be highly sensitive to meaning-preserving formatting.
- **[MEDIUM, official]** [US Census Statistical Quality Standard E1](https://www.census.gov/about/policies/quality/standards/standarde1.html) and [UK ONS uncertainty guidance](https://www.ons.gov.uk/methodology/methodologytopicsandstatisticalconcepts/uncertaintyandhowwemeasureit) — sample conclusions require uncertainty, design, error, and replication context.
- **[MEDIUM, peer-reviewed]** [Automatic Evaluation of Attribution by Large Language Models](https://aclanthology.org/2023.findings-emnlp.307/) — evidence attribution asks whether the cited reference supports the claim, not merely whether a related/verbatim span is present.

---
*Pitfalls research for: SpecChoice v1.3.2 controlled RISC-V architectural-parameter extraction feasibility spike*
*Researched: 2026-07-30*
