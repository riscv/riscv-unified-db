# Phase 4: Offline Treatments, Retrieval, and Branch Freeze - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-04
**Phase:** 4-offline-treatments-retrieval-and-branch-freeze
**Areas discussed:** Red freeze contract, Two-pair retrieval proof, Offline prompt samples, Red model boundary

---

## Red Freeze Contract

| Question | Selected | Alternatives considered |
|----------|----------|-------------------------|
| H3 handling of `red_required` | Decision-free readiness plus independent human approval of Red only | Human Green/Yellow override; machine-auto-freeze Red |
| Red counts | `N_strict=0`, `repeat_count=0` | Retain repeat count 2; record planned and effective counts |
| H4 representation | `h4_required=false`, `not_applicable_red` inside H3; no H4 file | Separate H4 N/A artifact; omit H4 entirely |
| Disputed/incomplete recovery | Both fail closed; incomplete may re-sign unchanged readiness, disputed rebuilds a versioned chain | Re-sign same packet for both; rebuild everything for both |

**User's choices:** Recommended option 1 for all four questions.
**Notes:** H3 must preserve the approved Phase 3 Red conclusion without converting eligibility into automatic execution authority.

---

## Two-Pair Retrieval Proof

| Question | Selected | Alternatives considered |
|----------|----------|-------------------------|
| Proving top-two with one authoritative pair | Isolated test-only corpus; authoritative path fails closed | Static review only; reuse one authoritative pair twice |
| Test corpus source | Contract-only non-RISC-V synthetic text | Modified real passages; copied authoritative pairs with changed IDs |
| Query inputs | Frozen target source text only | Add human frame; add family/axis labels |
| Zero-score second result | Return exactly two without a threshold; stable `pair_id` tie-break | Fail on zero score; return only one pair |

**User's choices:** Recommended option 1 for all four questions.
**Notes:** Test fixtures are explicitly non-counting and may prove mechanics only; no labels or relevance fields enter retrieval.

---

## Offline Prompt Samples

| Question | Selected | Alternatives considered |
|----------|----------|-------------------------|
| Offline target | Dedicated synthetic contract fixture | PR #2164 fixture; one side of the prototype pair |
| Bundle contents | Rendered prompts plus human contract responses | Prompts only; pseudo-model responses |
| Authority format | UTF-8/LF prompt bytes plus canonical JSON responses/manifest | All YAML; Markdown only |
| Red token accounting | Exact byte/code-point/line counts plus labeled lexical proxy | Select a model tokenizer; omit counts |

**User's choices:** Recommended option 1 for all four questions.
**Notes:** Structural diffs are fail-closed and permit only the frozen A/B/C treatment differences; neutral padding remains forbidden.

---

## Red Model Boundary

| Question | Selected | Alternatives considered |
|----------|----------|-------------------------|
| Provider/model adapter | Implement no adapter or invocation surface | Always-blocked stub; complete disabled adapter |
| Proving unreachability | CLI allowlist, dependency scan, and runtime negative proof | H3 runtime gate only; documentation only |
| Retrieval exposure | `verify-retrieval-contract` for test-only inputs | Production command guarded by H3; unit tests only |
| Provider/model/credentials config | No file; explicit N/A and false fields in H3 | Null/N/A config file; dormant provider config |

**User's choices:** Recommended option 1 for all four questions.
**Notes:** Absence of network, provider, credentials, model, and production-retrieval surfaces is required Red evidence.

---

## the agent's Discretion

- Internal Python module and schema decomposition.
- Additional stable diagnostic codes beyond the locked `INSUFFICIENT_RETRIEVAL_PAIRS` behavior.
- Exact synthetic contract text and standard-library lexical-token rule.
- Human-readable report layout within the canonical JSON authority boundary.

## Deferred Ideas

None.
