# Phase 3: Human-Reviewed Data Preregistration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-03
**Phase:** 3-human-reviewed-data-preregistration
**Areas discussed:** Data Admission and Dispute Handling, Primary-Family and Strict/Auxiliary Assignment, Contrastive Pair Review Standard, Relevance, Metamorphic, and H2 Approval Packet

---

## Data Admission and Dispute Handling

### Disputed-item handling

| Option | Description | Selected |
|--------|-------------|----------|
| Approve stable subset | Quarantine disputed items, count only approved items, and version any later modification | ✓ |
| Block entire H2 package | Any disputed item blocks aggregate approval | |
| Block affected category | A dispute blocks only its prototype or held-out category | |

**User's choice:** Approve the stable subset and retain disputed items as non-counting audit evidence.

### Structural admission order

| Option | Description | Selected |
|--------|-------------|----------|
| Machine admission first | Structural and provenance checks pass before semantic review | ✓ |
| Review with gaps | Human review may begin before structural closure | |
| Human override | A reviewer may approve despite structural failure | |

**User's choice:** Machine admission first; distinguish `invalid` structural failures from `disputed` semantics.

### Reuse across pairs

| Option | Description | Selected |
|--------|-------------|----------|
| No count-eligible reuse | One example/source span belongs to at most one approved pair | ✓ |
| Reuse by axis | Reuse is allowed when discriminating axes differ | |
| Count unique passages | Multiple pairs may reuse material but thresholds use unique-passage counts | |

**User's choice:** No count-eligible reuse.

### Threshold backfill

| Option | Description | Selected |
|--------|-------------|----------|
| Freeze candidate universe | No replacements after review begins; shortfall becomes Yellow/Red evidence | ✓ |
| One supplemental round | Permit one preregistered, fully re-reviewed supplemental version | |
| Continue within timebox | Add candidates until a threshold or time limit is reached | |

**User's choice:** Freeze the candidate universe before review and prohibit threshold-driven backfill.

---

## Primary-Family and Strict/Auxiliary Assignment

### Registry formation

| Option | Description | Selected |
|--------|-------------|----------|
| Definition first | Approve closed definitions and criteria before item assignment | ✓ |
| Cluster first | Group examples and name families afterward | |
| Specification structure | Use extension/CSR/instruction/section categories directly | |

**User's choice:** A closed, definition-first registry.

### Ambiguous primary family

| Option | Description | Selected |
|--------|-------------|----------|
| Dispute and exclude | No eligibility set accepts an ambiguous primary family | ✓ |
| Auxiliary ambiguous family | Allow `primary_family: ambiguous` in auxiliary only | |
| Choose broadest family | Assign the most general applicable family | |

**User's choice:** Dispute and exclude; retain overlap only as secondary tags.

### Strict/auxiliary assignment

| Option | Description | Selected |
|--------|-------------|----------|
| Isolation rules only | Example and primary-family relationships determine the split | ✓ |
| Add human difficulty | Reviewers may demote strict candidates based on representativeness | |
| Strict only | Exclude family-overlap cases and omit auxiliary | |

**User's choice:** Split assignment is entirely determined by frozen isolation rules.

### Registry-change invalidation

| Option | Description | Selected |
|--------|-------------|----------|
| Full-chain invalidation | Any registry change invalidates all dependent approvals | ✓ |
| Affected families only | Preserve approvals outside modified families | |
| Semantic changes only | Preserve approvals across non-semantic patch revisions | |

**User's choice:** Full-chain invalidation and re-review.

---

## Contrastive Pair Review Standard

### Qualifying relationship

| Option | Description | Selected |
|--------|-------------|----------|
| Controlled minimal contrast | Share material structure and differ only on declared decisive axes | ✓ |
| Same family | Opposite dispositions within one family are sufficient | |
| Thematic similarity | Human-perceived usefulness is sufficient | |

**User's choice:** Controlled minimal contrast; extra semantic confounds cause dispute.

### Evidence binding

| Option | Description | Selected |
|--------|-------------|----------|
| Claim-to-span mapping | Each semantic claim explicitly references exact source evidence | ✓ |
| One list per side | Non-empty evidence per side is sufficient | |
| Unique span per claim | A source span cannot support multiple claims | |

**User's choice:** Explicit claim-to-span mapping, with declared multi-claim reuse permitted.

### Review order

| Option | Description | Selected |
|--------|-------------|----------|
| Items before relation | Approve both sides independently, then assess pair structure and axes | ✓ |
| Holistic pair | Approve labels and relationship in one decision | |
| Contrast before labels | Adjust item labels to strengthen a useful pair | |

**User's choice:** Independent item review before pair-relation review; relation failure cannot rewrite gold.

### Pair direction

| Option | Description | Selected |
|--------|-------------|----------|
| Directed pair | Freeze positive/contrast roles, delta, and order | ✓ |
| Unordered pair | Prompt assembly may choose the order later | |
| Count both directions | Register both orders as separate pairs | |

**User's choice:** Directed, non-interchangeable pairs; swapping is a new version but not a new count.

---

## Relevance, Metamorphic, and H2 Approval Packet

### Relevance coverage

| Option | Description | Selected |
|--------|-------------|----------|
| Complete strict coverage | Every strict case has relevant IDs or explicit `no_relevant_pair` | ✓ |
| High-confidence subset | Missing relevance records are allowed | |
| At least one pair each | Every strict case must name a relevant pair | |

**User's choice:** Complete strict-core coverage with explicit no-relevant-pair judgments allowed.

### Relevance criterion

| Option | Description | Selected |
|--------|-------------|----------|
| Target axes plus structure | Freeze decisive axes and require a structurally matching pair | ✓ |
| Same family | Shared primary family is sufficient | |
| Reviewer usefulness | Free-text perceived helpfulness is sufficient | |

**User's choice:** Preregister target choice object and decisive axes, then require structural matching; do not rank relevant pairs in advance.

### Metamorphic source policy

| Option | Description | Selected |
|--------|-------------|----------|
| Real preferred, human synthetic allowed | Explicit synthetic provenance, exact edits, semantic delta, and approval | ✓ |
| Real source only | Both sides must be accepted authoritative passages | |
| Model candidates allowed | A model may generate variants before human review | |

**User's choice:** Prefer real sources; permit explicitly synthetic human-authored minimal variants under strict labeling and review.

### H2 versus branch authority

| Option | Description | Selected |
|--------|-------------|----------|
| H2 data approval, Phase 4 authorization | H2 binds trusted data/counts and deterministic eligibility only | ✓ |
| H2 final branch | H2 directly authorizes Green/Yellow/Red | |
| No Phase 3 eligibility | Defer all threshold interpretation to Phase 4 | |

**User's choice:** H2 approves data and eligibility evidence; Phase 4 owns the final human-signed execution branch.

---

## the agent's Discretion

- Internal module and class names.
- Schema-file decomposition and CLI command names.
- Immutable generation and review-packet directory names.
- Additional stable structural diagnostic codes.
- YAML authoring with canonical JSON projection versus canonical JSON authoring, provided one form is authoritative and byte-stable.

## Deferred Ideas

None.
