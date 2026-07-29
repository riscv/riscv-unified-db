# Stack Research

**Domain:** Controlled, reproducible LLM feasibility experiment inside a brownfield specification repository  
**Researched:** 2026-07-30  
**Confidence:** MEDIUM overall — HIGH for reuse of checked-in UnifiedDB pins; MEDIUM for current external package/provider details because the model provider is not yet frozen

## Recommendation

Build SpecChoice as an isolated Python 3.14 package under
`experiments/specchoice-v1.3.2/`. Reuse UnifiedDB's uv, jsonschema, ruamel.yaml,
pytest, and Ruff versions. Add exactly one unconditional third-party dependency:
`scikit-learn==1.9.0`. Keep any live-model SDK in a separately selected and
locked dependency group after the human reviewer freezes the provider.

This is the smallest reliable stack for the three-day spike. It avoids coupling
the experiment to UDB's Ruby/YAML/IDL generation path while avoiding a bespoke
TF-IDF implementation that would consume the limited validation budget.

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| CPython | 3.14.6 | Runner, schemas, retrieval, scoring, reports, CLI | Reuses the repository pin. The standard library already supplies canonical JSON, SHA-256, NFC normalization, dataclasses, typing, argument parsing, and statistics. **Confidence: HIGH.** |
| uv | 0.11.31 | Isolated environment and exact dependency lock | Reuses `.mise.toml`; a nested `pyproject.toml` plus `uv.lock` keeps the experiment reproducible without changing UDB's root dependency graph. Use `--locked` for audited runs. **Confidence: HIGH.** |
| JSON Schema + `jsonschema` | Draft 2020-12; package 4.26.0 | Fixture, prediction, frame, pair, split, manifest, and report validation | Already present in UnifiedDB. `Draft202012Validator` supports explicit schema checking and strict unknown-key rejection. A checked-in schema remains the contract, independent of the model SDK. **Confidence: HIGH.** |
| scikit-learn | 1.9.0 | `TfidfVectorizer` and `cosine_similarity` only | Current stable release with CPython 3.14 wheels. It is the sole new core dependency and removes risk from hand-rolling retrieval math. **Confidence: MEDIUM.** |
| Filesystem JSON/text artifacts | SpecChoice v1.3.2 schemas | Raw calls, parsed predictions, diagnostics, manifests, and canonical reports | The corpus is tiny and immutable. Git-visible files are more auditable than a database or experiment service. **Confidence: HIGH.** |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `ruamel.yaml` | 0.19.1 | Safe loading of human-authored frozen manifests, gold, and prototype data | Read inputs with `YAML(typ="safe")`, normalize to plain Python values, then validate with JSON Schema. Do not emit predictions, reports, or UDB YAML. Already locked by UDB. |
| `pytest` | 9.1.1 | Golden, adversarial, split-isolation, retrieval, parsing, and byte-determinism tests | Reuse the root version and conventions. Network calls must be replaced by a replay/fake provider in tests. |
| `ruff` | 0.16.0 | Linting and formatting | Reuse the root configuration and version; do not add another formatter. |
| `openai` | 2.50.0, optional | One concrete live-call adapter if OpenAI is the preregistered provider | Put in a non-default `openai` dependency group. It supports Python 3.14, Responses API structured output, usage fields, request IDs, and raw response access. Do not make it part of the core measurement/replay path. |

Do not directly depend on NumPy, SciPy, joblib, threadpoolctl, httpx, or
Pydantic. They may be transitive dependencies of scikit-learn or a selected
provider SDK, but SpecChoice should not import them or make them part of its
contracts.

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `bin/uv` | Repository-supported uv entry point | Create a separate experiment lockfile; do not edit the root `uv.lock`. |
| `pytest` snapshots/golden bytes | Canonical-output regression tests | Compare exact UTF-8 bytes and SHA-256 digests, not merely parsed object equality. |
| Standard-library `argparse` | Stable CLI | Enough for `validate`, `retrieve`, `assemble`, `run`, `score`, and `report`; Click/Typer add no value in three days. |
| Standard-library `logging` | Human diagnostics | Canonical reports must be generated from structured records, never scraped logs. |

## Required Implementation Boundaries

### 1. Strict schema and parser boundary

Use checked-in Draft 2020-12 schemas and call
`Draft202012Validator.check_schema()` during tests/startup. Every object sets
`additionalProperties: false` and explicitly lists required keys.

Model-facing schemas should stay within the selected provider's supported JSON
Schema subset. For the canonical adjudication invariant, place a disjoint
`anyOf` inside the `adjudication` property:

- one branch requires `surfaced: false`, null status/name, and an empty evidence list;
- surfaced branches require an allowed status and at least one non-empty evidence span.

This avoids provider-unsupported `if`/`then`/`else` while remaining enforceable
by local `jsonschema`. Local validation is authoritative even when the provider
offers structured output.

Parse generated output as JSON only. The parser must:

- cap input size before `json.loads`;
- reject duplicate object keys with `object_pairs_hook`;
- reject `NaN`/`Infinity` with `parse_constant`;
- preserve raw output before parsing;
- never repair, default, or re-ask silently;
- translate validation failures into frozen SpecChoice diagnostic codes rather
  than serializing version-sensitive `jsonschema` prose.

### 2. Deterministic retrieval boundary

Use one `TfidfVectorizer` with every parameter explicit:

```python
TfidfVectorizer(
    input="content",
    encoding="utf-8",
    decode_error="strict",
    lowercase=True,
    analyzer="word",
    token_pattern=r"(?u)\b\w\w+\b",
    ngram_range=(1, 1),
    stop_words=None,
    max_df=1.0,
    min_df=1,
    max_features=None,
    norm="l2",
    use_idf=True,
    smooth_idf=True,
    sublinear_tf=False,
)
```

Build one document per complete pair from fixed fields in a fixed order. Sort
pairs by `pair_id`, fit only on prototype-pair documents, and only transform
held-out targets. Compute `cosine_similarity`, then rank with
`(-score, pair_id)` and take exactly two pairs for the controlled experiment.
Do not use `NearestNeighbors`, approximate search, randomness, or target text in
IDF fitting. Record the library version, vectorizer parameters, ordered corpus
hash, scores, and selected pair IDs.

### 3. Model-provider boundary

Use a small internal `ModelClient` protocol, not an orchestration framework:

```python
class ModelClient(Protocol):
    def generate(self, request: ModelRequest) -> ModelResult: ...
```

`ModelRequest` owns the condition, prompt bytes/hash, exact model snapshot,
schema, sampling settings, maximum output tokens, and timeout. `ModelResult`
owns requested/reported model IDs, provider request ID, status/finish reason,
raw provider envelope, raw output text, provider-reported input/output tokens,
and error details.

The A/B/C loop depends only on this protocol. Prompt assembly determines the
treatment; the provider adapter must not rewrite prompts, choose examples,
repair JSON, or score outputs. Implement:

- a `ReplayModelClient` for golden/offline tests;
- one synchronous live adapter only after provider selection;
- non-streaming calls, so a terminal incomplete/refusal status is inspected
  before parsing;
- SDK automatic retries disabled (for OpenAI, `max_retries=0`); an explicit
  `retry-failed` command may create a new recorded attempt under one frozen
  policy;
- secrets read from environment variables, never configuration or `.env`
  committed files.

Do not hard-code a model name in source. Freeze a dated/immutable model snapshot
and all sampling parameters in the preregistration manifest. Temperature zero
does not make remote generation deterministic; reproducibility comes from raw
response preservation, repeats, hashes, and deterministic downstream handling.

### 4. Canonical report boundary

Use only `unicodedata`, `json`, `hashlib`, `pathlib`, `collections`, and
`statistics`. Recursively normalize strings to NFC, normalize line endings to
LF, pre-sort semantically unordered arrays, and serialize with:

```python
json.dumps(
    report,
    ensure_ascii=False,
    indent=2,
    sort_keys=True,
    allow_nan=False,
) + "\n"
```

Write UTF-8 with `newline="\n"` and hash the final bytes with SHA-256. Core
reports exclude timestamps, absolute paths, wall-clock durations, and provider
request metadata; put those in a separate run manifest. Generate Markdown with
small Python functions from the same validated report object—no Jinja, pandas,
notebooks, or charting stack.

## Installation

The experiment should own this minimal dependency set:

```toml
[project]
requires-python = ">=3.14,<3.15"
dependencies = [
  "jsonschema==4.26.0",
  "ruamel-yaml==0.19.1",
  "scikit-learn==1.9.0",
]

[dependency-groups]
dev = ["pytest==9.1.1", "ruff==0.16.0"]
openai = ["openai==2.50.0"]  # only if this provider is preregistered
```

```bash
cd experiments/specchoice-v1.3.2
../../bin/uv lock
../../bin/uv sync --locked
../../bin/uv run --locked pytest -q

# Only for a preregistered OpenAI live run
../../bin/uv sync --locked --group openai
```

Check in the experiment's `uv.lock`. Do not install ad hoc packages into the
root `.venv`, and do not require the C++ toolchain, Ruby resolver, containers,
Node, or Java for the standalone spike.

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| scikit-learn 1.9.0 | Pure-standard-library TF-IDF | Use only if `uv` cannot obtain compatible wheels within the environment timebox. Freeze the exact TF, IDF, tokenization, normalization, zero-vector, and tie rules before implementing it. |
| JSON Schema + TypedDict/dataclasses | Pydantic models | Use Pydantic only if a future production service needs runtime object construction across many endpoints. It duplicates the schema source of truth in this spike. |
| Thin `ModelClient` plus one official SDK | LiteLLM or a multi-provider gateway | Use a gateway only in a later project whose hypothesis actually compares providers. It adds normalization behavior and another changing interface here. |
| Filesystem manifests and JSON | MLflow/W&B/database | Use experiment tracking infrastructure only for a long-running, multi-user campaign; 18–24 hours and at most dozens of calls do not justify it. |
| Provider-reported usage | tokenizer package estimates | Add a provider tokenizer only if preregistration requires pre-call hard token enforcement and the selected provider cannot return authoritative usage. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Embeddings, FAISS, Chroma, Pinecone, vector databases | Explicitly changes the frozen retrieval treatment and adds learned/opaque behavior | TF-IDF over complete pairs plus cosine similarity |
| LangChain, LlamaIndex, Haystack, Semantic Kernel | Generic RAG/orchestration abstractions obscure prompt, retry, and serialization controls | Plain Python modules and a tiny provider protocol |
| DSPy, GEPA, prompt search, automatic prompt repair | Confounds the preregistered A/B/C comparison | Checked-in, hashed prompt templates |
| Learned rerankers or LLM-as-retriever | Violates the frozen hypothesis | Stable pair-level score and `pair_id` tie-break |
| YAML model output or UDB YAML emission | YAML has more parser ambiguity and UDB emission is out of scope | JSON predictions and canonical JSON reports; YAML is read-only human-authored input |
| pandas, notebooks, Jinja, plotting libraries | Adds dependencies and hidden display/order behavior for a tiny dataset | `collections`, `statistics`, deterministic Markdown functions |
| Fuzzy matching or semantic-entailment packages | Would change identity/evidence semantics | Exact normalized identifiers and verbatim-span auditing |
| Root UDB schema/backend changes | The spike is not a UDB redesign | Isolated `experiments/specchoice-v1.3.2/` package |

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `scikit-learn==1.9.0` | CPython 3.11+; published CPython 3.14 wheels | Official metadata lists NumPy >=1.24.1, SciPy >=1.10.0, joblib >=1.4.0, and threadpoolctl >=3.5.0. Let the experiment lockfile resolve these transitively. |
| `jsonschema==4.26.0` | Repository Python >=3.12 and pinned Python 3.14.6 | Already resolved in root `uv.lock`; explicitly select `Draft202012Validator`. |
| `ruamel.yaml==0.19.1` | Python >=3.9; pure Python wheel | Already resolved in root `uv.lock`; do not install optional LibYAML extras for this tiny read-only workload. |
| `pytest==9.1.1` | Python 3.14.6 | Already pinned in root `pyproject.toml`/`uv.lock`. |
| `ruff==0.16.0` | Repository toolchain | Already pinned; reuse root settings. |
| `openai==2.50.0` | Python >=3.10 including 3.14 | Current official release as of 2026-07-30; optional and provider-specific. Pin it in `uv.lock` before preregistration. |

The attempted local lock-resolution probe did not reach package resolution
because `bin/uv` first attempted to bootstrap mise and the research sandbox had
no DNS access. Official package metadata confirms the Python 3.14 wheels, but
the implementation phase should run `bin/doctor` and the nested `uv lock`
command once in the connected repository environment.

## Sources

- [UnifiedDB root `pyproject.toml`](../../pyproject.toml) and
  [`.mise.toml`](../../.mise.toml) — repository Python, uv, jsonschema,
  ruamel.yaml, pytest, and Ruff pins. **Confidence: HIGH (direct repository
  evidence).**
- [scikit-learn 1.9.0 on PyPI](https://pypi.org/project/scikit-learn/) and
  [official installation documentation](https://scikit-learn.org/stable/install.html)
  — release, dependencies, and Python 3.14 wheels. **Confidence: MEDIUM
  (official sources cross-checked through websearch).**
- [TfidfVectorizer API](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
  and [cosine similarity API](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise.cosine_similarity.html)
  — explicit retrieval behavior. **Confidence: MEDIUM.**
- [`jsonschema` 4.26 validator API](https://python-jsonschema.readthedocs.io/en/stable/api/jsonschema/validators/)
  and [PyPI release](https://pypi.org/project/jsonschema/) — Draft 2020-12 and
  current version. **Confidence: MEDIUM.**
- [`ruamel.yaml` on PyPI](https://pypi.org/project/ruamel.yaml/) and
  [pytest changelog](https://docs.pytest.org/en/stable/changelog.html) —
  current releases and compatibility. **Confidence: MEDIUM.**
- [OpenAI Python SDK](https://pypi.org/project/openai/),
  [official SDK repository](https://github.com/openai/openai-python), and
  [Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs)
  — optional adapter version, raw/usage metadata, supported schema subset, and
  strict-output behavior. **Confidence: MEDIUM.**
- [Python 3.14 `json`](https://docs.python.org/3.14/library/json.html),
  [`hashlib`](https://docs.python.org/3.14/library/hashlib.html), and
  [`unicodedata`](https://docs.python.org/3.14/library/unicodedata.html) —
  canonical serialization, SHA-256, and NFC. **Confidence: MEDIUM.**
- [uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)
  and [uv project layout](https://docs.astral.sh/uv/concepts/projects/layout/)
  — locked execution and nested lockfile behavior. **Confidence: MEDIUM.**

---
*Stack research for: SpecChoice v1.3.2*
*Researched: 2026-07-30*
