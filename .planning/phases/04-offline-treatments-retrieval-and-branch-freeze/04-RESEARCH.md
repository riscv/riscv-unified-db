# Phase 4: Offline Treatments, Retrieval, and Branch Freeze - Research

**Researched:** 2026-08-04
**Domain:** Offline A/B/C treatment contracts, deterministic lexical retrieval, and immutable Red branch authority
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** H3 uses the established two-layer pattern: code produces a decision-free readiness packet, then a separate human decision binds its exact hashes. The human decision may be `approved_red`, `disputed`, or `incomplete`; it cannot override the Phase 3 `red_required` result to Green or Yellow. — **Reversibility:** one-way — once an H3 decision is signed against the immutable readiness root, changing the approved branch requires a versioned successor readiness/decision chain rather than mutation.
- **D-02:** The Red execution contract records exactly `N_strict=0` and `repeat_count=0`. It does not retain planned or nominal repeat values that could imply an executable model matrix.
- **D-03:** H3 records `h4_required=false` with reason `not_applicable_red`. No separate H4 decision or N/A artifact is created.
- **D-04:** Both `disputed` and `incomplete` fail closed and create no branch authority. If all bound inputs are unchanged, an incomplete decision may be followed by a new immutable decision against the same readiness. A disputed decision requires corrected upstream inputs, a version increment, and complete regeneration of the readiness and decision chain.

- **D-05:** Prove top-two retrieval with an isolated test-only corpus containing at least three complete pairs. The corpus exists only to verify TF-IDF, cosine ranking, target dependence, complete-pair atomicity, and deterministic tie-breaking. The authoritative Phase 3 one-pair path must fail closed rather than reuse or duplicate its pair.
- **D-06:** Test corpus content is contract-only synthetic text with no RISC-V research semantics. Every item is explicitly `test_only=true` and `count_eligible=false`; test fixtures cannot enter H2 authority, the experiment freeze root, eligibility counts, or model evidence.
- **D-07:** Retrieval query input is the frozen target source text only. Case identity, gold, DelegationFrame, primary family, decisive axes, relevance judgments, and final disposition are forbidden query inputs.
- **D-08:** With at least two distinct eligible pairs, retrieval always returns exactly two complete pairs even when one or both cosine scores are zero. It introduces no similarity threshold, exposes each score, and orders by cosine score descending then `pair_id` ascending. Fewer than two distinct pairs yields `INSUFFICIENT_RETRIEVAL_PAIRS` and no partial ranking.

- **D-09:** Render A/B/C using a dedicated synthetic target marked `test_only=true` and `count_eligible=false`, together with the isolated test-only pair corpus. These artifacts demonstrate prompt and parser contracts only; they are not strict, auxiliary, prototype, discovery, or experiment cases.
- **D-10:** The offline bundle includes exact rendered A/B/C prompt bytes and human-authored contract responses. Every response records `origin=contract_fixture` and `model_generated=false`; contract responses cannot be admitted as raw model responses or run evidence.
- **D-11:** Prompt authority is raw UTF-8/LF text. Responses and the bundle manifest use the existing NFC-normalized, sorted-key canonical JSON and SHA-256 rules. Every prompt and response has its own hash.
- **D-12:** Structural comparison fails closed on any non-treatment difference. A omits DelegationFrame instructions and output while B includes them; B and C have the identical frame/adjudication contract; B and C differ only in fixed versus retrieved pair selection. Demonstration count, target bytes, shared guidance, decision space, evidence rules, and relevant serialization rules remain identical. No neutral-text padding is permitted.
- **D-13:** Red offline accounting records exact UTF-8 byte, Unicode code-point, and line counts plus a deterministic standard-library `offline_lexical_token_count`. Provider token fields are `not_applicable_red`; Phase 4 does not select or install a model tokenizer.

- **D-14:** Do not implement a provider/model adapter, provider SDK, HTTP client, credentials loader, model CLI, external-call path, or dormant model invocation stub. Phase 4 exposes only offline frame, prompt, retrieval-contract verification, and H3 freeze capabilities.
- **D-15:** Prove model unreachability structurally and at runtime. The CLI allowlist contains no model, provider, or run command; dependency checks reject network, provider-SDK, and credentials imports in the Phase 4 boundary; unknown model commands fail deterministically without network activity.
- **D-16:** The only retrieval CLI surface is `verify-retrieval-contract`, and it accepts only `test_only` corpora. Non-test-only inputs are rejected. No authoritative or production retrieval command exists on the Red branch.
- **D-17:** Create no provider or model configuration file. H3 records `provider_config_present=false`, `model_snapshot=not_applicable_red`, `credentials_boundary=not_applicable_red`, and `external_calls_authorized=false`. The freeze inventory contains no secret, environment-variable, or credentials path.

### the agent's Discretion

The planner may choose internal Python module and schema-file decomposition, additional stable diagnostics, the exact contract-fixture prose, the deterministic standard-library lexical-token rule, and human-readable report layout. Those choices must reuse existing canonical JSON, hashing, strict parsing, immutable-attempt, descriptor-bound filesystem, CLI, and readiness/decision patterns. Do not add a dependency when the standard library or installed project code suffices.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within the frozen Phase 4 scope.
</user_constraints>

## Project Constraints (from AGENTS.md)

- Follow the repository priority order: do not implement unnecessary work; reuse repository code; prefer the standard library and native capabilities; reuse installed dependencies; keep clear one-line logic unabstracted; only then add the smallest tested custom code. [VERIFIED: AGENTS.md]
- Keep the prototype isolated under `experiments/specchoice-v1.3.2/`; do not alter core UDB schemas, generated architecture data, or root dependency state. [VERIFIED: .planning/PROJECT.md:27-27]
- Use the existing Python `unittest` tests and run the documented local commands with `PYTHONDONTWRITEBYTECODE=1` and `PYTHONPATH=src`; repository-wide validation remains `./bin/regress --all` when relevant to a real UDB change. [VERIFIED: AGENTS.md]
- Do not commit, switch branches, install dependencies, call remote services, or make public upstream changes in Phase 4 research/planning. [VERIFIED: parent task scope; .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:40-43]

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TS-10 | Machine-evaluated and human-approved gate records one branch plus `N_strict` and repeats, and Red blocks model execution. [VERIFIED: .planning/REQUIREMENTS.md:36-36] | H3 recomputation, immutable readiness/decision/authority chain, Red-only field assertions, and structural/runtime no-model proof. |
| H1-01 | B/C contain exactly the three DelegationFrame axes, frozen enums including `unknown`, and one verbatim evidence span per axis. [VERIFIED: .planning/REQUIREMENTS.md:45-45] | Closed frame schema/parser, exact B/C rendering, span-to-source verification, advisory-only diagnostics. |
| H2-02 | Retrieve exactly two complete pairs with frozen TF-IDF/cosine settings, target-dependent ranking, and `pair_id` ties; never use learned retrieval. [VERIFIED: .planning/REQUIREMENTS.md:53-53] | Test-only corpus schema, deterministic pair-level retrieval, target-only input enforcement, zero-score/tie/insufficient-corpus tests. |
</phase_requirements>

## Summary

Phase 4 is a Red-path control/freeze phase, not an execution phase. The accepted upstream authority is already `red_required`, with one qualifying pair, zero strict cases, and all retrieval/model/publication permissions false; the new implementation must bind that state rather than recalculate it or try to make it executable. Quote: `"eligibility_status":"red_required"`, `"model_execution_authorized":false`, `"retrieval_authorized":false`, and `"phase4_decision_required":true`. [VERIFIED: experiments/specchoice-v1.3.2/phase3/data-authority-v1.json:1]

Implement the phase in a small new `specchoice_treatments` package inside the existing standalone experiment boundary. It should use the current canonical JSON/SHA-256 functions, strict duplicate-key decoder, descriptor-held exact-resume writer, Phase 3 chain validator, and `argparse` pattern. Python 3.14.5, Git 2.54.0, and Ruff 0.12.0 are present; the existing dependency-light workspace explicitly uses the Python standard library only. [VERIFIED: experiments/specchoice-v1.3.2/README.md:1-22; environment audit 2026-08-04]

**Primary recommendation:** Build exactly four strictly sequential plans—frame contract, prompt bundle, test-only retrieval verifier, then H3 Red authority/no-model enforcement—and add no third-party package or model-facing surface.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|---|---|---|---|
| Closed DelegationFrame parsing and span validation | API / Backend | Database / Storage | Local Python owns validation; canonical fixtures are immutable file inputs, not application state. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:87-93] |
| A/B/C prompt bytes, diff manifest, and lexical accounting | API / Backend | CDN / Static | Deterministic local renderer produces raw UTF-8/LF prompt bytes and canonical JSON projections. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:32-36] |
| TF-IDF/cosine contract proof | API / Backend | Database / Storage | A local function ranks an explicitly test-only in-memory/file corpus; no service, vector store, or learned tier is allowed. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:25-28] |
| H3 readiness, human decision, and Red authority | API / Backend | Database / Storage | Code recomputes/binds local evidence while a human provides the decision artifact; immutable files preserve the authority chain. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:18-21] |
| Model unreachability proof | API / Backend | — | A local source/CLI audit proves there is no provider, credential, model, or network entry point. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:40-43] |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---|---:|---|---|
| Python standard library (`argparse`, `collections`, `math`, `re`, `unicodedata`, `hashlib`, `json`) | Python 3.14.5 | Local CLI, lexical counts/retrieval, deterministic arithmetic, text accounting, canonical serialization. | The experiment workspace already has a standard-library-only boundary; `Counter` is a standard dict subclass for token tallying and `argparse` supports required subparser dispatch. [VERIFIED: experiments/specchoice-v1.3.2/README.md:1-22; CITED: https://docs.python.org/3/library/collections.html; CITED: https://docs.python.org/3.14/library/argparse.html] |
| `specchoice_evidence.canonical` | existing | NFC/LF canonical JSON and SHA-256. | It normalizes canonical text, serializes sorted-key UTF-8 JSON with trailing LF, and hashes authoritative bytes. [VERIFIED: experiments/specchoice-v1.3.2/src/specchoice_evidence/canonical.py:18-53] |
| `specchoice_evidence.filesystem` | existing | Descriptor-bound no-replace/exact-resume publication. | It supplies `write_exact_descriptor_files` and authoritative file readers, avoiding custom atomic-write logic. [VERIFIED: experiments/specchoice-v1.3.2/src/specchoice_evidence/filesystem.py:251-335] |
| `specchoice_measurement.strict_json` | existing | UTF-8 strict JSON and duplicate-key rejection. | `decode_strict_json` rejects duplicate keys before object construction. [VERIFIED: experiments/specchoice-v1.3.2/src/specchoice_measurement/strict_json.py:32-52] |
| `specchoice_data.h2` | existing | Recompute accepted Phase 3 chain and apply readiness/decision/authority pattern. | Its functions already separate decision-free packet/readiness, human decision validation, and exact-resume authority publication. [VERIFIED: experiments/specchoice-v1.3.2/src/specchoice_data/h2.py:455-645] |

### Supporting

| Library | Version | Purpose | When to Use |
|---|---:|---|---|
| `unittest` | Python 3.14.5 | Unit/integration/adversarial tests. | Use for every Phase 4 contract and filesystem/authority failure case. [VERIFIED: experiments/specchoice-v1.3.2/tests/test_data_h2.py:26-250] |
| Ruff | 0.12.0 | Static formatting/lint check. | Run against only Phase 4 source and tests in task-level validation. [VERIFIED: environment audit 2026-08-04] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|---|---|---|
| Standard-library TF-IDF/cosine for three synthetic pairs | scikit-learn, embeddings, vector DB, learned reranker | Rejected: adds a dependency and violates the locked no-embedding/no-learned retrieval scope. [VERIFIED: .planning/REQUIREMENTS.md:53-53; .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:47-47] |
| Existing canonical/filesystem functions | New JSON canonicalizer or atomic writer | Rejected: duplicates security-critical behavior already established in the experiment boundary. [VERIFIED: experiments/specchoice-v1.3.2/src/specchoice_evidence/canonical.py:18-53; experiments/specchoice-v1.3.2/src/specchoice_evidence/filesystem.py:251-335] |
| No model/provider layer | Stub adapter, SDK, HTTP client, credentials reader, or model CLI | Rejected by the explicit Red boundary; a dormant stub is still an unauthorized surface. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:40-43] |

**Installation:** None. Do not run a package-manager command. [VERIFIED: experiments/specchoice-v1.3.2/README.md:1-22]

## Architecture Patterns

### System Architecture Diagram

```text
Phase 3 immutable inputs                 Phase 4 test-only inputs
data-authority + H2 artifacts            synthetic target + >=3 pair corpus
          |                                          |
          v                                          v
  reopen/recompute Phase 3 chain              strict corpus parser
          |                                          |
          |                                  target-text-only TF-IDF/cosine
          |                                          |
          +-----------> frame schema <--------------+
                         |             |
                         v             v
                 B/C strict output   A/B/C raw UTF-8/LF prompts
                         |             |
                         +-------> canonical manifest/diff/accounting
                                           |
                                           v
                       H3 decision-free readiness (Red-only fields + closed inventory)
                                           |
                              human `approved_red` / `disputed` / `incomplete`
                                           |
                         approved_red only -> immutable H3 Red authority
                                           |
                                           v
                     Phase 5 input: no model/provider/H4 execution surface
```

The diagram encodes the required one-way authority flow: test-only retrieval validates a contract but cannot contribute to Phase 3/H2 counts or H3 experiment authority. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:25-28; 106-109]

### Recommended Project Structure

```text
experiments/specchoice-v1.3.2/
├── src/specchoice_treatments/          # new isolated Phase 4 package [ASSUMED]
│   ├── schema.py                        # frame, corpus, response, and H3 exact-key validators [ASSUMED]
│   ├── prompts.py                       # raw prompt renderer, diff manifest, lexical accounting [ASSUMED]
│   ├── retrieval.py                     # frozen lexical TF-IDF/cosine contract verifier [ASSUMED]
│   ├── h3.py                            # recomputation, readiness, human-decision, Red authority [ASSUMED]
│   └── cli.py                           # only `verify-retrieval-contract` subcommand [ASSUMED]
├── config/treatments/                   # closed JSON contracts/advisory patterns [ASSUMED]
├── fixtures/treatments/                 # synthetic target, >=3 test-only pairs, A/B/C responses [ASSUMED]
├── prompts/treatments/                  # raw A/B/C UTF-8/LF prompts and canonical manifest [ASSUMED]
├── reports/h3/                          # deterministic H3 packet/Markdown projection [ASSUMED]
├── receipts/                            # H3 readiness [ASSUMED]
├── reviews/                             # human H3 decision only [ASSUMED]
└── tests/test_treatments_*.py           # frame, prompt, retrieval, H3/boundary tests [ASSUMED]
```

These are proposed file locations, not existing paths. Keep all of them inside the approved experiment root; this is the smallest separation that prevents Phase 4 code from modifying frozen `specchoice_data` inputs. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:104-109]

### Pattern 1: Closed frame contract with source-bound evidence

**What:** Parse B/C contract responses with duplicate-key rejection and exact keys. Require exactly the three axes and reject missing, extra, or invalid values. For every axis, verify the recorded span is non-empty UTF-8 text and byte-for-byte equals the corresponding slice of the synthetic target source.

**When to use:** Both rendered B/C contract fixtures and future non-Red execution parsing; A must never gain a frame field just to make structural comparison easier. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:33-35]

The frozen axis values are verbatim: `authority: implementation | ISA | software | platform | unknown`; `choice_object: direct_value | count | width | legal_set | access_mode | presence | extension_gate | other`; `choice_space_origin: implementation_selected | ISA_fixed | derived | not_applicable | unknown`. [VERIFIED: /Users/zhdeng/Downloads/LFX_RISCV_SpecChoice_v1.3.2_frozen_execution_baseline.md:427-448]

### Pattern 2: Pair-level deterministic lexical retrieval

**What:** Validate the isolated corpus before ranking: every entry must be a complete pair and test-only/non-count-eligible; derive one document per pair; derive the query solely from target source text; calculate specified frozen TF-IDF/cosine values; return the top two full pairs using `(-score, pair_id)` ordering. Report scores even when they are zero.

**When to use:** Only `verify-retrieval-contract` and its tests. It is not production retrieval and must reject Phase 3 authority/corpus input before tokenization. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:25-28; 40-43]

```python
# Deterministic final ordering after scores have been calculated.
# Source: locked D-08 ordering rule.
top_two = sorted(scored_pairs, key=lambda item: (-item.score, item.pair_id))[:2]
```

The code snippet implements only the locked order, `"cosine score descending then pair_id ascending"`; it must not add a threshold or use incidental insertion order. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:28-28]

### Pattern 3: Raw text authority + canonical manifest projection

**What:** Render each prompt as raw UTF-8/LF bytes; hash the raw bytes directly. Emit response records, hashes, treatment-diff result, counts, and inventory as canonical JSON. Markdown, if created, is a deterministic projection of canonical JSON and never a separate authority.

**When to use:** Prompt bundle and H3 packet/readiness/authority publication. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:32-36; experiments/specchoice-v1.3.2/src/specchoice_evidence/canonical.py:18-53]

### Pattern 4: Readiness is not authority

**What:** Recompute Phase 3 inputs immediately before building H3 readiness; bind the exact packet, manifest, raw prompt/response hashes, retrieval verifier report, closed runtime inventory, and Phase 3 identities. Validate a complete human decision separately. Create immutable authority only for a complete `approved_red` decision; `disputed`/`incomplete` remain auditable decisions with no authority.

**When to use:** H3 only. Do not reuse H2's name/version fields blindly; preserve its structure but define a separate H3 schema and exact Red-only invariants. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:18-21; experiments/specchoice-v1.3.2/src/specchoice_data/h2.py:487-554; 618-645]

### Anti-Patterns to Avoid

- **Reading Phase 3 counts and re-deriving eligibility:** H3 consumes exact existing authority/report/packet/readiness/decision bindings; it must not reopen semantic labels or alter Red. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:106-109]
- **Using the natural approved pair twice to satisfy top-two retrieval:** the Phase 3 one-pair path must return the insufficient-pairs diagnostic and no partial ranking. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:25-28]
- **A helpful model stub:** any adapter, SDK, HTTP client, credential reader, CLI command, or unreachable invocation violates Red. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:40-43]
- **Neutral prompt padding or unequal pair counts:** it changes the treatment instead of measuring its natural byte/lexical difference. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:35-36]
- **Treating contract responses as model evidence:** their required values are `origin=contract_fixture` and `model_generated=false`, so they must be rejected from raw-response/run-evidence paths. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:32-33]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Canonical JSON/NFC/SHA-256 | A second serializer/hash helper | `canonical_json_bytes`, `normalize_canonical_text`, `sha256_bytes` | Existing behavior controls the authoritative bytes and trailing LF. [VERIFIED: experiments/specchoice-v1.3.2/src/specchoice_evidence/canonical.py:18-53] |
| Immutable exact-resume writes | `Path.write_bytes` plus existence checks | `write_exact_descriptor_files` / descriptor-bound reader | Existing primitive guards leaf types, races, partial/divergent targets, and exact resume. [VERIFIED: experiments/specchoice-v1.3.2/src/specchoice_evidence/filesystem.py:251-335] |
| Strict JSON loading | Plain `json.loads` | `decode_strict_json` | Duplicate keys must fail before later exact-key checks. [VERIFIED: experiments/specchoice-v1.3.2/src/specchoice_measurement/strict_json.py:32-52] |
| Phase 3 evidence validation | A copy of H2's chain calculations | `validate_phase3_chain_v1` and `validate_phase3_data_authority_v1` | The existing validator reopens authoritative leaves and ties the exact source authority to Phase 3 bindings. [VERIFIED: experiments/specchoice-v1.3.2/src/specchoice_data/h2.py:107-130; 601-615] |
| CLI parser | Custom command dispatch | `argparse` required subparsers and `set_defaults` handler pattern | Existing local CLI already uses this simple, testable pattern. [VERIFIED: experiments/specchoice-v1.3.2/src/specchoice_data/cli.py:128-162; CITED: https://docs.python.org/3.14/library/argparse.html] |

**Key insight:** The only justified new implementation is the domain-specific, explicitly frozen lexical retrieval and treatment/H3 contract; all serialization, parsing, filesystem, and authority mechanics already exist.

## Common Pitfalls

### Pitfall 1: Accidentally converting the retrieval proof into executable retrieval

**What goes wrong:** A CLI accepts the Phase 3 pair corpus, an authority file, or a non-test target, then a later phase mistakes its result for experiment evidence.

**Why it happens:** The one approved natural pair looks reusable, but it cannot prove two distinct complete pair retrieval and its authority has `retrieval_authorized=false`.

**How to avoid:** Make corpus and target schemas require `test_only=true` and `count_eligible=false`; reject every other input before ranking; use a fresh synthetic three-pair fixture; test the Phase 3 corpus rejection.

**Warning signs:** A retrieval report contains `WARL_IMPLEMENTATION_SELECTED_VS_ISA_FIXED`, strict IDs, family/gold fields, or any source path outside the test-only fixture root. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:25-28; experiments/specchoice-v1.3.2/phase3/data-authority-v1.json:1]

### Pitfall 2: Structural equality hides an intervention leak

**What goes wrong:** B/C differ in shared guidelines, evidence rules, output schema, target bytes, serialization, or pair count while a coarse string comparison says prompts are “similar.”

**How to avoid:** Build a named-section manifest before rendering; compare hashes/bytes for every shared section; make allowed diffs explicit: A↔B frame presence only, B↔C pair-selection only; fail on every other difference.

**Warning signs:** A diff is accepted without a section allowlist, or A/B/C have different byte source hashes for shared target/rules/decision/evidence sections. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:35-36]

### Pitfall 3: Mistaking readiness or a human incomplete decision for H3 authority

**What goes wrong:** A packet/readiness exists and downstream code infers approval, or a disputed/incomplete decision is treated as a retry-able authorization.

**How to avoid:** Copy the established H2 separation: validate the human record's exact hashes and complete acknowledgments, but publish H3 authority only when aggregate is `approved_red`. No authority exists for the other dispositions.

**Warning signs:** Authority writer lacks an explicit disposition check, or a missing human payload yields an output artifact. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:18-21; experiments/specchoice-v1.3.2/src/specchoice_data/h2.py:513-554; 623-642]

### Pitfall 4: “Offline” only means no call happened in one test

**What goes wrong:** A provider/config/credential/network dependency or command remains importable but happens not to run.

**How to avoid:** Assert both static and runtime absence: AST/import allowlist over the Phase 4 package, exact CLI subcommand inventory, rejection of model/provider/run unknown commands, and a patched socket/HTTP sentinel around command execution.

**Warning signs:** A Phase 4 import contains `urllib`, `http`, `socket`, `requests`, `httpx`, provider SDKs, credentials/keyring/dotenv modules, or a CLI parser exposes a model/provider/run command. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:40-43]

### Pitfall 5: Ambiguous lexical rules make “deterministic” non-reproducible

**What goes wrong:** Tokenization, document construction, TF scaling, IDF, rounding, or zero-vector behavior is left implicit and different implementations rank differently.

**How to avoid:** Put the exact lexical normalization/tokenization, pair-text concatenation, TF-IDF formula, cosine zero-vector policy, and score serialization into one closed config/manifest; hash it and test exact expected scores/ranks. The exact lexical rule is discretionary and must be selected once before fixture output is frozen. [ASSUMED]

## Code Examples

### Exact-order retrieval boundary

```python
# Source: locked D-08.
if len(distinct_eligible_pairs) < 2:
    raise RetrievalContractError("INSUFFICIENT_RETRIEVAL_PAIRS")
return sorted(scored_pairs, key=lambda item: (-item.score, item.pair_id))[:2]
```

The literals are locked verbatim: `INSUFFICIENT_RETRIEVAL_PAIRS`, `"cosine score descending then pair_id ascending"`, and exactly two distinct complete pairs. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:28-28]

### H3 authority publication guard

```python
# Source: established H2 approved-only writer pattern, specialized to Red.
validate_h3_decision_v1(decision=decision, packet=packet, readiness=readiness)
if decision["aggregate_disposition"] != "approved_red":
    raise H3ValidationError("H3_APPROVAL_REQUIRED")
return write_exact_descriptor_files(output_root, payloads)
```

`approved_red`, `disputed`, and `incomplete` are the complete H3 decision values; only the first may yield authority. The H2 ancestor uses the same validate-then-explicit-approval-before-write structure. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:18-21; experiments/specchoice-v1.3.2/src/specchoice_data/h2.py:618-642]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| Phase 3 data eligibility could be mistaken for execution permission | H3 is the sole final execution-branch authority; Phase 3 stays immutable input with all execution permissions false | Phase 3 completion | Prevents eligibility or data adequacy from becoming model/retrieval authority. [VERIFIED: experiments/specchoice-v1.3.2/phase3/data-authority-v1.json:1; .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:106-109] |
| H2's real one-pair corpus might be reused for a top-two proof | Isolated synthetic `test_only` three-pair corpus proves the algorithm only | Locked Phase 4 D-05/D-06 | Maintains data isolation and lets insufficient real coverage remain Red evidence. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:25-26] |

**Deprecated/outdated:** Treating a Phase 3 `red_required` result as an incomplete defect is invalid. It is the frozen complete input to an H3 Red no-model freeze, not a reason to add data, rerun retrieval, or invoke a model. [VERIFIED: .planning/phases/03-human-reviewed-data-preregistration/03-VERIFICATION.md:13-25; .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:9-9]

## Recommended Plan Decomposition

Plans must remain strictly sequential. Each wave has exactly one objective; no parallel plan is permitted inside a wave.

| Wave | One objective | Plan scope | Required proof before the next wave |
|---:|---|---|---|
| 1 | Freeze the frame/output contract | Create closed frame/advisory/response schemas and strict parser; make B/C require exactly three source-bound axes; preserve advisory non-blocking behavior. | Parser accepts the frozen valid fixtures and rejects extra/missing axis, invalid enum, duplicate key, empty/mismatched span, and any A frame. |
| 2 | Freeze the offline A/B/C bundle | Create synthetic target/pairs, raw UTF-8/LF prompt renderer, human contract responses, hashes, structural-diff allowlist, and byte/code-point/line/lexical counts. | A/B/C bytes and manifest reproduce exactly; equal pair counts and shared-section hashes pass; unauthorized diff/padding and response-origin misuse fail. |
| 3 | Prove deterministic test-only retrieval | Implement/freeze lexical settings and pair-level TF-IDF/cosine verifier; expose exactly `verify-retrieval-contract`. | Three-pair target-dependent rankings, zero-score/tie ordering, complete-pair atomicity, `<2` failure, and non-test/Phase-3 input rejection pass offline. |
| 4 | Freeze the Red branch and prove unreachability | Build H3 recomputation/readiness/decision/authority plus closed inventory and static/runtime no-model boundary checks. | Only `approved_red` creates immutable Red authority with `N_strict=0`, `repeat_count=0`, H4 N/A fields, and no provider/model/network surface; all other decisions/drift fail closed. |

The four objectives match the already approved roadmap increments and preserve the dependency order `frame → prompts → retrieval → H3`. [VERIFIED: .planning/ROADMAP.md:245-278]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|---|---|---:|---|---|
| Python | all Phase 4 code/tests | ✓ | 3.14.5 | — |
| Python standard library | parser, hashing, text, retrieval, CLI | ✓ | bundled | — |
| Git | existing repository validation / `git diff --check` | ✓ | 2.54.0 | — |
| Ruff | local static check | ✓ | 0.12.0 | `python -m py_compile` only if Ruff becomes unavailable [ASSUMED] |
| Provider SDK/model CLI/network/credentials | model execution | intentionally absent | — | Red no-call branch; do not install a fallback. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:40-43] |

**Missing dependencies with no fallback:** None. The absence of provider/model tooling is required Red evidence, not a block. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:40-43]

## Validation Architecture

### Test Framework

| Property | Value |
|---|---|
| Framework | Python `unittest` (installed with Python 3.14.5). [VERIFIED: experiments/specchoice-v1.3.2/tests/test_data_h2.py:1-250; environment audit 2026-08-04] |
| Config file | None; tests run through `PYTHONPATH=src python3 -m unittest`. [VERIFIED: .planning/phases/03-human-reviewed-data-preregistration/03-VALIDATION.md] |
| Quick run command | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_treatments_frame tests.test_treatments_prompts tests.test_treatments_retrieval tests.test_treatments_h3 -q` [ASSUMED] |
| Full phase command | `cd experiments/specchoice-v1.3.2 && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest tests.test_data_admission tests.test_data_splits tests.test_data_relevance tests.test_data_h2 tests.test_treatments_frame tests.test_treatments_prompts tests.test_treatments_retrieval tests.test_treatments_h3 tests.test_canonical tests.test_filesystem_boundary -q && ruff check --isolated src/specchoice_treatments tests/test_treatments_frame.py tests/test_treatments_prompts.py tests/test_treatments_retrieval.py tests/test_treatments_h3.py` [ASSUMED] |

The current predecessor command passed with 72 tests and Ruff during this research session: `tests.test_data_admission`, `tests.test_data_splits`, `tests.test_data_relevance`, `tests.test_data_h2`, `tests.test_canonical`, and `tests.test_filesystem_boundary`. [VERIFIED: execution audit 2026-08-04]

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|---|---|---|---|---|
| H1-01 | B/C accept exactly three frozen axes; `unknown` is valid; each axis has a verbatim source slice; A rejects/omits a frame. | unit | quick run | ❌ Wave 1 |
| H1-01 | Advisory combinations produce only a stable non-blocking warning and cannot alter parsed axis/adjudication values. | unit | quick run | ❌ Wave 1 |
| H2-02 | Target-only input returns exactly two complete pair IDs, scores, and deterministic score-descending/ID-ascending order. | unit | quick run | ❌ Wave 3 |
| H2-02 | Different target text can change rank; zero scores still return two; fewer than two returns `INSUFFICIENT_RETRIEVAL_PAIRS` with no partial list. | unit | quick run | ❌ Wave 3 |
| H2-02 | Non-test corpus/target and Phase 3 authority/corpus are rejected before rank calculation; no learned retrieval import appears. | integration/security | quick run | ❌ Wave 3 |
| TS-10 | H3 recomputes exact Phase 3 bindings and makes readiness decision-free; only complete `approved_red` decision publishes immutable authority. | integration | quick run | ❌ Wave 4 |
| TS-10 | H3 authority records verbatim `N_strict=0`, `repeat_count=0`, `h4_required=false`, `not_applicable_red`, and closed no-provider fields. | unit/integration | quick run | ❌ Wave 4 |
| TS-10 | Disputed/incomplete/missing decisions, frozen input drift, divergent resume, symlink/partial target, and H4/model escalation fail closed. | adversarial | full phase command | ❌ Wave 4 |
| TS-10 | Exact CLI allowlist, unknown model/provider/run commands, forbidden imports, and patched network sentinel prove no model reachability. | security/runtime | full phase command | ❌ Wave 4 |

### Sampling Rate

- **Per task commit:** Run the Wave-specific new `unittest` file plus relevant existing `test_canonical`/`test_filesystem_boundary` tests. [ASSUMED]
- **Per wave merge:** Run the full phase command above; it includes the accepted Phase 3 partition so an H3 change cannot silently break its input verifier. [ASSUMED]
- **Phase gate:** Full suite green, `ruff` green, `git diff --check` clean, and a human H3 decision review are required before Phase 5 consumes the authority. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:18-21; AGENTS.md]

### Wave 0 Gaps

- [ ] `tests/test_treatments_frame.py` — H1-01 closed frame/parser/advisory coverage.
- [ ] `tests/test_treatments_prompts.py` — raw prompt/hash/diff/count/contract-response coverage.
- [ ] `tests/test_treatments_retrieval.py` — H2-02 pair, target-only, zero/tie/insufficient, and test-only boundary coverage.
- [ ] `tests/test_treatments_h3.py` — TS-10 decision/authority/exact-resume/no-model boundary coverage.
- [ ] No framework install: existing `unittest` and Ruff are sufficient. [VERIFIED: environment audit 2026-08-04]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---|---|---|
| V2 Authentication | no | No service/user authentication exists in the standalone offline boundary. [VERIFIED: experiments/specchoice-v1.3.2/README.md:1-22] |
| V3 Session Management | no | No session/cookie/remote process exists. [VERIFIED: experiments/specchoice-v1.3.2/README.md:1-22] |
| V4 Access Control | yes | H3 authority is capability control: only complete `approved_red` can produce authority; all other decisions fail closed. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:18-21] |
| V5 Input Validation | yes | Strict UTF-8 duplicate-key rejection, exact keys/enums, byte-verified evidence spans, and test-only corpus gate. [VERIFIED: experiments/specchoice-v1.3.2/src/specchoice_measurement/strict_json.py:32-52; .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:25-28] |
| V6 Cryptography | yes | Reuse `hashlib.sha256` through the existing canonical module; do not invent hash/canonicalization logic. [VERIFIED: experiments/specchoice-v1.3.2/src/specchoice_evidence/canonical.py:18-53] |

### Known Threat Patterns for the Stack

| Pattern | STRIDE | Standard Mitigation |
|---|---|---|
| Tampered Phase 3/prompt/corpus/decision input | Tampering | Descriptor-bound authoritative reads, full recomputation, canonical hash bindings, and versioned successor on drift. [VERIFIED: experiments/specchoice-v1.3.2/src/specchoice_data/h2.py:107-130; 601-645] |
| Readiness/incomplete record presented as approval | Elevation of Privilege | Separate human decision validation and explicit `approved_red` gate before authority write. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:18-21] |
| Synthetic retrieval enters evidence or counts | Tampering / Elevation of Privilege | `test_only=true`, `count_eligible=false`, isolated fixture root, and rejection before ranking. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:25-28] |
| Provider/model/credential path becomes reachable | Elevation of Privilege / Information Disclosure | No package/config/CLI/import surface; AST and runtime socket sentinel tests. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:40-43] |
| Prompt treatment drift concealed by projection | Repudiation / Tampering | Raw-byte hashes and allowlisted structural diff; no padding. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:32-36] |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|---|---|---|
| A1 | The exact lexical token regex/normalization, pair-document construction, TF/IDF formula, cosine zero-vector convention, and score decimal encoding remain unchosen and must be frozen in Wave 3's closed retrieval contract. | Common Pitfalls / Wave 3 | Different implementations can produce a different ranking despite complying superficially with TF-IDF/cosine. |
| A2 | `specchoice_treatments` and its named test/config/fixture paths are recommended new paths rather than present repository paths. | Recommended Project Structure / Validation | Planner must create only the minimal paths it needs and avoid collision with an existing package added before execution. |
| A3 | Ruff fallback to `py_compile` is only a contingency; Ruff is currently available and remains the required static check while present. | Environment Availability | Reduced lint coverage if environment changes. |

## Open Questions (RESOLVED)

1. **Which exact standard-library lexical specification will be frozen?**
   - What we know: TF-IDF/cosine, target-only input, complete pairs, and deterministic ordering are locked; the planner may choose lexical-token details. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:25-28; 45-47]
   - What's unclear: token regex/case normalization, pair text composition, TF/IDF formula, score serialization, and zero-vector result are not yet a named closed artifact.
   - Recommendation: Decide all five in 04-03 before any generated retrieval report; hash the config and assert exact fixtures. This is a planner-owned discretionary technical choice, not a reason to request a new product decision. [ASSUMED]
   - **RESOLVED:** Wave 3 plan 04-03, Task 04-03-01 freezes the complete lexical contract in canonical hashed `experiments/specchoice-v1.3.2/config/treatments/lexical-retrieval-contract-v1.json` before the canonical retrieval report or any generated retrieval fixture/report is frozen. The decision is NFC then casefold normalization, regex `(?u)\\b\\w+\\b`, one LF-joined pair document in configured field order with sorted `discriminating_axes`, raw-count TF, `ln((1+N)/(1+df))+1` IDF, L2 cosine with a zero-vector score of `0`, full-precision ranking followed by `.17g` score serialization, and `contract_sha256` over the canonical config. [RESOLVED: `04-03-PLAN.md`, lexical-config artifact contract and Task 04-03-01 actions 2-3]

2. **How will the human H3 decision be entered without adding a broad CLI?**
   - What we know: H3 must use the existing machine-readiness + separate human-decision pattern, and Phase 4's only retrieval CLI is fixed. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:18-21; 42-42]
   - What's unclear: whether the planner needs a small dedicated read-only H3 validator command or should reuse a library/test checkpoint while a human supplies canonical JSON.
   - Recommendation: Default to a library-only H3 validator/publisher and human-supplied canonical decision artifact; add an H3 CLI only if the planner can demonstrate it does not expand the allowed command surface. [ASSUMED]
   - **RESOLVED:** Plan 04-04 selects library-first H3 validation and publication through `specchoice_treatments.h3`, with the human supplying the canonical `experiments/specchoice-v1.3.2/reviews/h3-branch-decision-v1.json` artifact at checkpoint 04-04-02. H3 adds no CLI command or flag; `specchoice_treatments.cli.build_parser()` remains unchanged, and the sole Phase 4 CLI is `verify-retrieval-contract`. [RESOLVED: `04-04-PLAN.md`, `<interfaces>`, H3 artifacts/CLI contract, and Task 04-04-02]

## Sources

### Primary (HIGH confidence)

- [Phase 4 Context](/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/.planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md) — locked D-01 through D-17, boundary, and integration constraints.
- [Requirements](/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/.planning/REQUIREMENTS.md) — TS-10, H1-01, H2-02 wording.
- [Existing H2 implementation](/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_data/h2.py) — chain/readiness/decision/authority pattern.
- [Canonical primitives](/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_evidence/canonical.py) and [filesystem primitives](/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_evidence/filesystem.py) — byte and immutable-write reuse.
- [Frozen execution baseline](/Users/zhdeng/Downloads/LFX_RISCV_SpecChoice_v1.3.2_frozen_execution_baseline.md) — exact DelegationFrame enums and treatment/retrieval controls.

### Secondary (MEDIUM confidence)

- [Python `collections` documentation](https://docs.python.org/3/library/collections.html) — `Counter` standard-library token tallies.
- [Python `argparse` documentation](https://docs.python.org/3.14/library/argparse.html) — required subparsers and handler dispatch.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — no new package is needed; the existing experiment README and current environment confirm the standard-library boundary. [VERIFIED: experiments/specchoice-v1.3.2/README.md:1-22; environment audit 2026-08-04]
- Architecture: HIGH — locked Context plus direct inspection of H2/canonical/filesystem code identifies the exact reuse seams. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:82-109; experiments/specchoice-v1.3.2/src/specchoice_data/h2.py:455-645]
- Pitfalls: HIGH — they arise directly from explicit fail-closed/Red constraints and established input/authority code. [VERIFIED: .planning/phases/04-offline-treatments-retrieval-and-branch-freeze/04-CONTEXT.md:18-43]

**Research date:** 2026-08-04
**Valid until:** 2026-09-03 (stable local-only stack; re-read if Phase 3 authority or Context changes).
