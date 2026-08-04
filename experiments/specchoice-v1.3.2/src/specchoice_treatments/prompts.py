# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Raw-byte A/B/C prompt rendering for the offline treatment contract."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from specchoice_evidence.canonical import canonical_json_bytes, sha256_bytes
from specchoice_measurement.strict_json import decode_strict_json


PROMPT_SECTION_ORDER = (
    "shared_guidance",
    "demonstrations",
    "target",
    "frame_instructions",
    "adjudication_instructions",
    "output_schema",
    "evidence_rules",
)
_PROMPT_CONTRACT_PATH = Path(__file__).resolve().parents[2] / "config/treatments/prompt-contract-v1.json"
_SYNTHETIC_TARGET_PATH = Path(__file__).resolve().parents[2] / "fixtures/treatments/synthetic-target-v1.json"
_PROMPT_CONTRACT_KEYS = frozenset({
    "schema_version", "section_order", "shared_guidance", "frame_instructions",
    "adjudication_instructions", "output_schema", "evidence_rules", "demonstration_count",
    "fixed_pair_ids", "retrieved_contract_pair_ids", "allowed_differences",
    "offline_lexical_rule", "provider_fields",
})
_TARGET_KEYS = frozenset({
    "schema_version", "target_id", "source_text", "test_only", "count_eligible", "target_sha256",
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


def _validate_prompt_contract_v1(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != _PROMPT_CONTRACT_KEYS:
        raise PromptBundleError("PROMPT_CONTRACT_INVALID")
    if value.get("schema_version") != "prompt-contract-v1" or tuple(value.get("section_order", ())) != PROMPT_SECTION_ORDER:
        raise PromptBundleError("PROMPT_CONTRACT_INVALID")
    if value.get("demonstration_count") != 2 or value.get("provider_fields") != "not_applicable_red":
        raise PromptBundleError("PROMPT_CONTRACT_INVALID")
    if value.get("offline_lexical_rule") != "python_re_findall_unicode_word_boundaries_v1":
        raise PromptBundleError("PROMPT_CONTRACT_INVALID")
    for field in (
        "shared_guidance", "frame_instructions", "adjudication_instructions", "evidence_rules",
    ):
        _require_text(value.get(field), "PROMPT_CONTRACT_INVALID")
    output_schema = value.get("output_schema")
    if not isinstance(output_schema, dict) or set(output_schema) != {"A", "BC"}:
        raise PromptBundleError("PROMPT_CONTRACT_INVALID")
    _require_text(output_schema.get("A"), "PROMPT_CONTRACT_INVALID")
    _require_text(output_schema.get("BC"), "PROMPT_CONTRACT_INVALID")
    _require_pair_ids(value.get("fixed_pair_ids"), "PROMPT_CONTRACT_INVALID")
    _require_pair_ids(value.get("retrieved_contract_pair_ids"), "PROMPT_CONTRACT_INVALID")
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
    expected = {key: item for key, item in value.items() if key != "target_sha256"}
    if value.get("target_sha256") != sha256_bytes(canonical_json_bytes(expected)):
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
    return _validate_prompt_contract_v1(config), _validate_synthetic_target_v1(target)


def _raw_section(text: str, *, allow_empty: bool = False) -> bytes:
    value = _require_text(text, "PROMPT_RAW_BYTES_INVALID", allow_empty=allow_empty)
    raw = value.encode("utf-8")
    if not allow_empty and (not raw or not raw.endswith(b"\n") or raw.endswith(b"\n\n")):
        raise PromptBundleError("PROMPT_RAW_BYTES_INVALID")
    return raw


def render_prompt_sections_v1(
    config: object,
    target: object,
    system: str,
) -> dict[str, bytes]:
    """Render one closed system prompt as ordered, unhashed raw-byte sections."""
    contract, closed_target = _closed_contract_and_target(config, target)
    if system not in {"A", "B", "C"}:
        raise PromptBundleError("PROMPT_CONTRACT_INVALID")
    pairs = contract["retrieved_contract_pair_ids"] if system == "C" else contract["fixed_pair_ids"]
    assert isinstance(pairs, list)
    demonstrations = "".join(
        f"Demonstration {index}: fixed synthetic pair {pair_id}.\n"
        for index, pair_id in enumerate(pairs, start=1)
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
    return {
        system: b"".join(render_prompt_sections_v1(config, target, system).values())
        for system in ("A", "B", "C")
    }
