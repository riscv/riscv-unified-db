# SPDX-License-Identifier: BSD-3-Clause-Clear
"""End-to-end tracer tests for the closed test-only lexical retriever."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from copy import deepcopy
from pathlib import Path
import unittest

from specchoice_evidence.canonical import canonical_json_bytes
from specchoice_treatments.cli import build_parser, main
from specchoice_treatments.retrieval import (
    build_retrieval_report_v1,
    load_retrieval_contract_v1,
    verify_retrieval_contract_v1,
)


class RetrievalContractTests(unittest.TestCase):
    """The tracer proves one target through the sole offline CLI."""

    root = Path(__file__).parents[1]
    target_path = "fixtures/treatments/synthetic-target-v1.json"
    corpus_path = "fixtures/treatments/synthetic-complete-pairs-v1.json"
    config_path = "config/treatments/lexical-retrieval-contract-v1.json"

    def setUp(self) -> None:
        self.target = json.loads((self.root / self.target_path).read_bytes())
        self.corpus = json.loads((self.root / self.corpus_path).read_bytes())
        self.config = load_retrieval_contract_v1(self.root, self.config_path)

    def _run_cli(self) -> tuple[int, bytes]:
        output = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
        with redirect_stdout(output):
            exit_code = main([
                "verify-retrieval-contract",
                "--target", self.target_path,
                "--corpus", self.corpus_path,
                "--config", self.config_path,
            ])
        output.flush()
        return exit_code, output.buffer.getvalue()

    def test_cli_tracer_returns_exact_two_complete_pairs(self) -> None:
        exit_code, stdout = self._run_cli()
        report = build_retrieval_report_v1(
            target=self.target,
            corpus=self.corpus,
            config=self.config,
            experiment_root=self.root,
        )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout, canonical_json_bytes(report))
        self.assertEqual([item["pair_id"] for item in report["results"]], [
            "SYNTH_PAIR_ALPHA", "SYNTH_PAIR_GAMMA",
        ])
        self.assertEqual(len(report["results"]), 2)
        self.assertEqual(
            [{key: item[key] for key in ("pair_id", "positive_source_text", "contrast_source_text", "cosine_score")}
             for item in report["results"]],
            [{
                "pair_id": "SYNTH_PAIR_ALPHA",
                "positive_source_text": "Alpha positive: implementation chooses label.\n",
                "contrast_source_text": "Alpha contrast: ISA fixes label.\n",
                "cosine_score": "0.60058743602146969",
            }, {
                "pair_id": "SYNTH_PAIR_GAMMA",
                "positive_source_text": "Gamma positive: implementation chooses flag.\n",
                "contrast_source_text": "Gamma contrast: ISA fixes flag.\n",
                "cosine_score": "0.24681266140992938",
            }],
        )

    def test_target_text_changes_rank(self) -> None:
        changed_target = deepcopy(self.target)
        changed_target["source_text"] = "Beta platform software access.\n"
        changed_target["source_sha256"] = ""
        changed_target["record_sha256"] = ""
        changed = verify_retrieval_contract_v1(
            target=changed_target,
            corpus=self.corpus,
            config=self.config,
            experiment_root=self.root,
        )
        baseline = verify_retrieval_contract_v1(
            target=self.target,
            corpus=self.corpus,
            config=self.config,
            experiment_root=self.root,
        )

        self.assertNotEqual(
            [item.pair_id for item in baseline],
            [item.pair_id for item in changed],
        )
        self.assertEqual([item.pair_id for item in changed], ["SYNTH_PAIR_BETA", "SYNTH_PAIR_ALPHA"])

    def test_report_matches_prompt_c_selection(self) -> None:
        parser = build_parser()
        subparsers = next(action for action in parser._actions if action.dest == "command")
        self.assertEqual(set(subparsers.choices), {"verify-retrieval-contract"})

        report = build_retrieval_report_v1(
            target=self.target,
            corpus=self.corpus,
            config=self.config,
            experiment_root=self.root,
        )
        manifest = json.loads(
            (self.root / "prompts/treatments/prompt-bundle-manifest-v1.json").read_bytes()
        )
        self.assertEqual(
            [item["pair_id"] for item in report["results"]],
            manifest["pair_selection"]["C"],
        )
        self.assertTrue(report["prompt_c_pair_ids_match"])


if __name__ == "__main__":
    unittest.main()
