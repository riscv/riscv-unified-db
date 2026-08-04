# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Raw-byte A/B/C prompt rendering for the offline treatment contract."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from specchoice_evidence.canonical import canonical_json_bytes, sha256_bytes
from specchoice_measurement.strict_json import decode_strict_json
from specchoice_treatments.schema import FRAME_ENUMS, REQUIRED_FRAME_AXES


PROMPT_SECTION_ORDER = (
    "shared_guidance",
    "demonstrations",
    "target",
    "frame_instructions",
    "adjudication_instructions",
    "output_schema",
    "evidence_rules",
)
_TREATMENTS_ROOT = Path(__file__).resolve().parents[2]
_PROMPT_CONTRACT_PATH = _TREATMENTS_ROOT / "config/treatments/prompt-contract-v1.json"
_SYNTHETIC_TARGET_PATH = _TREATMENTS_ROOT / "fixtures/treatments/synthetic-target-v1.json"
_SYNTHETIC_PAIR_CORPUS_PATH = _TREATMENTS_ROOT / "fixtures/treatments/synthetic-complete-pairs-v1.json"
_SYNTHETIC_RETRIEVAL_RECEIPT_PATH = _TREATMENTS_ROOT / "fixtures/treatments/synthetic-retrieval-receipt-v1.json"
_PROMPT_CONTRACT_KEYS = frozenset({
    "schema_version", "section_order", "shared_guidance", "frame_instructions",
    "adjudication_instructions", "output_schema", "evidence_rules", "demonstration_count",
    "fixed_pair_selection", "retrieval_contract_id", "retrieval_receipt_sha256", "allowed_differences",
    "offline_lexical_rule", "provider_fields",
})
_TARGET_KEYS = frozenset({
    "schema_version", "target_id", "source_text", "source_sha256", "record_sha256",
    "test_only", "count_eligible",
})
_FIXED_SELECTION_KEYS = frozenset({
    "selection_id", "target_source_sha256", "ordered_pair_ids", "test_only", "count_eligible",
})
_CORPUS_KEYS = frozenset({"schema_version", "test_only", "count_eligible", "pairs", "corpus_sha256"})
_PAIR_KEYS = frozenset({
    "pair_id", "positive", "contrast", "shared_structure", "discriminating_axes",
    "test_only", "count_eligible",
})
_PAIR_SIDE_KEYS = frozenset({"source_text", "source_sha256", "frame", "evidence_spans"})
_PAIR_FRAME_AXIS_KEYS = frozenset({"value", "evidence_span"})
_SPAN_KEYS = frozenset({"source_sha256", "start_byte", "end_byte", "text"})
_RETRIEVAL_RECEIPT_KEYS = frozenset({
    "schema_version", "test_only", "count_eligible", "target_source_sha256", "corpus_sha256",
    "ordered_pair_ids", "retrieval_contract_id", "receipt_sha256",
})


class PromptBundleError(ValueError):
    """Stable failure emitted before an offline prompt bundle can be trusted."""


def _load_canonical_json(path: Path, code: str) -> object:
    raw = path.read_bytes()
    try:
        value = decode_strict_json(raw)
    except (UnicodeDecodeError, ValueError) as error:
        raise PromptBundleError(code) from error
    if canonical_json_bytes(value) != raw:
        raise PromptBundleError(code)
    return value


def _require_text(value: object, code: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value) or "\r" in value:
        raise PromptBundleError(code)
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise PromptBundleError(code) from error
    return value


def _require_pair_ids(value: object, code: str) -> tuple[str, str]:
    if not isinstance(value, list) or len(value) != 2:
        raise PromptBundleError(code)
    pair_ids = tuple(value)
    if any(not isinstance(item, str) or not item for item in pair_ids) or len(set(pair_ids)) != 2:
        raise PromptBundleError(code)
    return pair_ids  # type: ignore[return-value]


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_prompt_contract_v1(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != _PROMPT_CONTRACT_KEYS:
        raise PromptBundleError("PROMPT_CONTRACT_INVALID")
    if value.get("schema_version") != "prompt-contract-v1" or tuple(value.get("section_order", ())) != PROMPT_SECTION_ORDER:
        raise PromptBundleError("PROMPT_CONTRACT_INVALID")
    if value.get("demonstration_count") != 2 or value.get("provider_fields") != "not_applicable_red":
        raise PromptBundleError("PROMPT_CONTRACT_INVALID")
    if value.get("offline_lexical_rule") != "python_re_findall_unicode_word_boundaries_v1":
        raise PromptBundleError("PROMPT_CONTRACT_INVALID")
    for field in ("shared_guidance", "frame_instructions", "adjudication_instructions", "evidence_rules", "retrieval_contract_id", "retrieval_receipt_sha256"):
        _require_text(value.get(field), "PROMPT_CONTRACT_INVALID")
    output_schema = value.get("output_schema")
    if not isinstance(output_schema, dict) or set(output_schema) != {"A", "BC"}:
        raise PromptBundleError("PROMPT_CONTRACT_INVALID")
    _require_text(output_schema.get("A"), "PROMPT_CONTRACT_INVALID")
    _require_text(output_schema.get("BC"), "PROMPT_CONTRACT_INVALID")
    selection = value.get("fixed_pair_selection")
    if not isinstance(selection, dict) or set(selection) != _FIXED_SELECTION_KEYS:
        raise PromptBundleError("PROMPT_CONTRACT_INVALID")
    if selection.get("selection_id") != "fixed-synthetic-pairs-v1" or selection.get("test_only") is not True or selection.get("count_eligible") is not False:
        raise PromptBundleError("PROMPT_CONTRACT_INVALID")
    _require_text(selection.get("target_source_sha256"), "PROMPT_CONTRACT_INVALID")
    _require_pair_ids(selection.get("ordered_pair_ids"), "PROMPT_CONTRACT_INVALID")
    allowed = value.get("allowed_differences")
    if allowed != {"A_B": ["frame_instructions", "output_schema"], "B_C": ["demonstrations"]}:
        raise PromptBundleError("PROMPT_CONTRACT_INVALID")
    return value


def _validate_synthetic_target_v1(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != _TARGET_KEYS:
        raise PromptBundleError("PROMPT_TARGET_INVALID")
    if value.get("schema_version") != "synthetic-treatment-target-v1":
        raise PromptBundleError("PROMPT_TARGET_INVALID")
    _require_text(value.get("target_id"), "PROMPT_TARGET_INVALID")
    source_text = _require_text(value.get("source_text"), "PROMPT_TARGET_INVALID")
    if value.get("test_only") is not True or value.get("count_eligible") is not False:
        raise PromptBundleError("PROMPT_TARGET_INVALID")
    if value.get("source_sha256") != sha256_bytes(source_text.encode("utf-8")):
        raise PromptBundleError("PROMPT_TARGET_INVALID")
    expected = {key: item for key, item in value.items() if key != "record_sha256"}
    if value.get("record_sha256") != sha256_bytes(canonical_json_bytes(expected)):
        raise PromptBundleError("PROMPT_TARGET_INVALID")
    if not source_text.endswith("\n") or source_text.endswith("\n\n"):
        raise PromptBundleError("PROMPT_TARGET_INVALID")
    return value


def _closed_contract_and_target(config: object, target: object) -> tuple[dict[str, object], dict[str, object]]:
    canonical_config = _load_canonical_json(_PROMPT_CONTRACT_PATH, "PROMPT_CONTRACT_INVALID")
    canonical_target = _load_canonical_json(_SYNTHETIC_TARGET_PATH, "PROMPT_TARGET_INVALID")
    if canonical_json_bytes(config) != canonical_json_bytes(canonical_config):
        raise PromptBundleError("PROMPT_CONTRACT_INVALID")
    if canonical_json_bytes(target) != canonical_json_bytes(canonical_target):
        raise PromptBundleError("PROMPT_TARGET_INVALID")
    contract = _validate_prompt_contract_v1(config)
    closed_target = _validate_synthetic_target_v1(target)
    selection = contract["fixed_pair_selection"]
    assert isinstance(selection, dict)
    if selection["target_source_sha256"] != closed_target["source_sha256"]:
        raise PromptBundleError("PROMPT_CONTRACT_INVALID")
    return contract, closed_target


def _validate_pair_span(value: object, source_raw: bytes) -> None:
    if not isinstance(value, dict) or set(value) != _SPAN_KEYS:
        raise PromptBundleError("PROMPT_PAIR_CORPUS_INVALID")
    start = value.get("start_byte")
    end = value.get("end_byte")
    if (
        value.get("source_sha256") != sha256_bytes(source_raw)
        or not _is_int(start)
        or not _is_int(end)
        or not 0 <= start < end <= len(source_raw)
    ):
        raise PromptBundleError("PROMPT_PAIR_CORPUS_INVALID")
    try:
        text = source_raw[start:end].decode("utf-8")
    except UnicodeDecodeError as error:
        raise PromptBundleError("PROMPT_PAIR_CORPUS_INVALID") from error
    if value.get("text") != text:
        raise PromptBundleError("PROMPT_PAIR_CORPUS_INVALID")


def _validate_pair_side(value: object) -> None:
    if not isinstance(value, dict) or set(value) != _PAIR_SIDE_KEYS:
        raise PromptBundleError("PROMPT_PAIR_CORPUS_INVALID")
    source_text = _require_text(value.get("source_text"), "PROMPT_PAIR_CORPUS_INVALID")
    if not source_text.endswith("\n") or source_text.endswith("\n\n"):
        raise PromptBundleError("PROMPT_PAIR_CORPUS_INVALID")
    source_raw = source_text.encode("utf-8")
    if value.get("source_sha256") != sha256_bytes(source_raw):
        raise PromptBundleError("PROMPT_PAIR_CORPUS_INVALID")
    spans = value.get("evidence_spans")
    if not isinstance(spans, list) or not spans:
        raise PromptBundleError("PROMPT_PAIR_CORPUS_INVALID")
    for span in spans:
        _validate_pair_span(span, source_raw)
    frame = value.get("frame")
    if not isinstance(frame, dict) or tuple(frame) != REQUIRED_FRAME_AXES:
        raise PromptBundleError("PROMPT_PAIR_CORPUS_INVALID")
    for axis in REQUIRED_FRAME_AXES:
        item = frame[axis]
        if not isinstance(item, dict) or set(item) != _PAIR_FRAME_AXIS_KEYS or item.get("value") not in FRAME_ENUMS[axis]:
            raise PromptBundleError("PROMPT_PAIR_CORPUS_INVALID")
        _validate_pair_span(item.get("evidence_span"), source_raw)


def _load_complete_pair_corpus_v1() -> dict[str, object]:
    corpus = _load_canonical_json(_SYNTHETIC_PAIR_CORPUS_PATH, "PROMPT_PAIR_CORPUS_INVALID")
    if not isinstance(corpus, dict) or set(corpus) != _CORPUS_KEYS:
        raise PromptBundleError("PROMPT_PAIR_CORPUS_INVALID")
    if corpus.get("schema_version") != "synthetic-complete-pair-corpus-v1" or corpus.get("test_only") is not True or corpus.get("count_eligible") is not False:
        raise PromptBundleError("PROMPT_PAIR_CORPUS_INVALID")
    expected = {key: item for key, item in corpus.items() if key != "corpus_sha256"}
    if corpus.get("corpus_sha256") != sha256_bytes(canonical_json_bytes(expected)):
        raise PromptBundleError("PROMPT_PAIR_CORPUS_INVALID")
    pairs = corpus.get("pairs")
    if not isinstance(pairs, list) or len(pairs) < 3:
        raise PromptBundleError("PROMPT_PAIR_CORPUS_INVALID")
    pair_ids: list[str] = []
    for pair in pairs:
        if not isinstance(pair, dict) or set(pair) != _PAIR_KEYS:
            raise PromptBundleError("PROMPT_PAIR_CORPUS_INVALID")
        pair_id = pair.get("pair_id")
        if not isinstance(pair_id, str) or not pair_id:
            raise PromptBundleError("PROMPT_PAIR_CORPUS_INVALID")
        pair_ids.append(pair_id)
        if pair.get("test_only") is not True or pair.get("count_eligible") is not False:
            raise PromptBundleError("PROMPT_PAIR_CORPUS_INVALID")
        structure = pair.get("shared_structure")
        axes = pair.get("discriminating_axes")
        if (
            not isinstance(structure, list)
            or not structure
            or any(not isinstance(item, str) or not item for item in structure)
            or not isinstance(axes, list)
            or not axes
            or len(axes) != len(set(axes))
            or any(axis not in REQUIRED_FRAME_AXES for axis in axes)
        ):
            raise PromptBundleError("PROMPT_PAIR_CORPUS_INVALID")
        _validate_pair_side(pair.get("positive"))
        _validate_pair_side(pair.get("contrast"))
    if len(pair_ids) != len(set(pair_ids)):
        raise PromptBundleError("PROMPT_PAIR_ID_DUPLICATE")
    return corpus


def _resolve_pairs(pair_ids: tuple[str, str], corpus: Mapping[str, object]) -> tuple[dict[str, object], dict[str, object]]:
    pairs = corpus["pairs"]
    assert isinstance(pairs, list)
    by_id = {pair["pair_id"]: pair for pair in pairs if isinstance(pair, dict)}
    if set(pair_ids) - set(by_id):
        raise PromptBundleError("PROMPT_PAIR_CORPUS_INVALID")
    resolved = tuple(by_id[pair_id] for pair_id in pair_ids)
    if any(pair["test_only"] is not True or pair["count_eligible"] is not False for pair in resolved):
        raise PromptBundleError("PROMPT_PAIR_CORPUS_INVALID")
    return resolved  # type: ignore[return-value]


def _load_retrieval_receipt_v1(contract: Mapping[str, object], target: Mapping[str, object], corpus: Mapping[str, object]) -> tuple[str, str]:
    receipt = _load_canonical_json(_SYNTHETIC_RETRIEVAL_RECEIPT_PATH, "PROMPT_PAIR_CORPUS_INVALID")
    if not isinstance(receipt, dict) or set(receipt) != _RETRIEVAL_RECEIPT_KEYS:
        raise PromptBundleError("PROMPT_PAIR_CORPUS_INVALID")
    expected = {key: item for key, item in receipt.items() if key != "receipt_sha256"}
    if (
        receipt.get("schema_version") != "synthetic-retrieval-receipt-v1"
        or receipt.get("test_only") is not True
        or receipt.get("count_eligible") is not False
        or receipt.get("receipt_sha256") != sha256_bytes(canonical_json_bytes(expected))
        or receipt.get("receipt_sha256") != contract["retrieval_receipt_sha256"]
        or receipt.get("target_source_sha256") != target["source_sha256"]
        or receipt.get("corpus_sha256") != corpus["corpus_sha256"]
        or receipt.get("retrieval_contract_id") != contract["retrieval_contract_id"]
    ):
        raise PromptBundleError("PROMPT_PAIR_CORPUS_INVALID")
    return _require_pair_ids(receipt.get("ordered_pair_ids"), "PROMPT_PAIR_CORPUS_INVALID")


def _raw_section(text: str, *, allow_empty: bool = False) -> bytes:
    value = _require_text(text, "PROMPT_RAW_BYTES_INVALID", allow_empty=allow_empty)
    raw = value.encode("utf-8")
    if not allow_empty and (not raw or not raw.endswith(b"\n") or raw.endswith(b"\n\n")):
        raise PromptBundleError("PROMPT_RAW_BYTES_INVALID")
    return raw


def render_prompt_sections_v1(config: object, target: object, system: str) -> dict[str, bytes]:
    """Render one closed system prompt as ordered, unhashed raw-byte sections."""
    contract, closed_target = _closed_contract_and_target(config, target)
    if system not in {"A", "B", "C"}:
        raise PromptBundleError("PROMPT_CONTRACT_INVALID")
    corpus = _load_complete_pair_corpus_v1()
    selection = contract["fixed_pair_selection"]
    assert isinstance(selection, dict)
    pair_ids = _load_retrieval_receipt_v1(contract, closed_target, corpus) if system == "C" else _require_pair_ids(selection["ordered_pair_ids"], "PROMPT_CONTRACT_INVALID")
    pairs = _resolve_pairs(pair_ids, corpus)
    selection_label = "retrieved contract pair" if system == "C" else "fixed synthetic pair"
    demonstrations = "".join(
        f"Demonstration {index}: {selection_label} {pair_id} canonical complete-pair payload:\n"
        f"{canonical_json_bytes(pair).decode('utf-8')}"
        for index, (pair_id, pair) in enumerate(zip(pair_ids, pairs, strict=True), start=1)
    )
    output_schema = contract["output_schema"]
    assert isinstance(output_schema, Mapping)
    target_text = closed_target["source_text"]
    assert isinstance(target_text, str)
    section_text = {
        "shared_guidance": contract["shared_guidance"],
        "demonstrations": demonstrations,
        "target": f"Target source text:\n{target_text}",
        "frame_instructions": "" if system == "A" else contract["frame_instructions"],
        "adjudication_instructions": contract["adjudication_instructions"],
        "output_schema": output_schema["A" if system == "A" else "BC"],
        "evidence_rules": contract["evidence_rules"],
    }
    sections = {
        name: _raw_section(text, allow_empty=name == "frame_instructions" and system == "A")
        for name, text in section_text.items()
    }
    if tuple(sections) != PROMPT_SECTION_ORDER:
        raise PromptBundleError("PROMPT_RAW_BYTES_INVALID")
    raw = b"".join(sections.values())
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise PromptBundleError("PROMPT_RAW_BYTES_INVALID") from error
    if not raw or b"\r" in raw or not raw.endswith(b"\n") or raw.endswith(b"\n\n"):
        raise PromptBundleError("PROMPT_RAW_BYTES_INVALID")
    return sections


def render_treatment_prompt_v1(config: object, target: object) -> dict[str, bytes]:
    """Render all three exact offline system prompts without publishing files."""
    return {system: b"".join(render_prompt_sections_v1(config, target, system).values()) for system in ("A", "B", "C")}
