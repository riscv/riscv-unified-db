# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Closed offline treatment contracts for the SpecChoice feasibility spike."""

from .schema import (
    FRAME_ENUMS,
    REQUIRED_FRAME_AXES,
    ParsedTreatmentResponse,
    TreatmentContractError,
    evaluate_frame_advisories_v1,
    parse_treatment_response_v1,
    validate_delegation_frame_v1,
    validate_source_span_v1,
)
from .prompts import (
    PROMPT_SECTION_ORDER,
    PromptBundleError,
    build_prompt_bundle_manifest_v1,
    count_prompt_bytes_v1,
    offline_lexical_token_count_v1,
    render_prompt_sections_v1,
    render_treatment_prompt_v1,
    validate_contract_response_origin_v1,
    validate_treatment_diffs_v1,
    write_offline_prompt_bundle_v1,
)
from .retrieval import (
    RetrievalContractError,
    RetrievedPair,
    build_retrieval_report_v1,
    construct_pair_document_v1,
    load_retrieval_contract_v1,
    rank_complete_pairs_v1,
    tokenize_retrieval_text_v1,
    validate_test_only_corpus_v1,
    validate_test_only_target_v1,
    verify_retrieval_contract_v1,
)

FRAME_COMBINATION_REQUIRES_REVIEW = "FRAME_COMBINATION_REQUIRES_REVIEW"

__all__ = [
    "FRAME_COMBINATION_REQUIRES_REVIEW",
    "FRAME_ENUMS",
    "PROMPT_SECTION_ORDER",
    "PromptBundleError",
    "REQUIRED_FRAME_AXES",
    "RetrievalContractError",
    "RetrievedPair",
    "ParsedTreatmentResponse",
    "TreatmentContractError",
    "evaluate_frame_advisories_v1",
    "build_prompt_bundle_manifest_v1",
    "build_retrieval_report_v1",
    "count_prompt_bytes_v1",
    "construct_pair_document_v1",
    "offline_lexical_token_count_v1",
    "load_retrieval_contract_v1",
    "parse_treatment_response_v1",
    "render_prompt_sections_v1",
    "render_treatment_prompt_v1",
    "rank_complete_pairs_v1",
    "tokenize_retrieval_text_v1",
    "validate_contract_response_origin_v1",
    "validate_delegation_frame_v1",
    "validate_test_only_corpus_v1",
    "validate_test_only_target_v1",
    "validate_source_span_v1",
    "validate_treatment_diffs_v1",
    "write_offline_prompt_bundle_v1",
    "verify_retrieval_contract_v1",
]
