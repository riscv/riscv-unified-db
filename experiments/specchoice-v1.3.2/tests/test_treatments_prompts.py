# SPDX-License-Identifier: BSD-3-Clause-Clear
from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from specchoice_evidence.canonical import canonical_json_bytes
from specchoice_treatments.prompts import (
    PromptBundleError,
    PROMPT_SECTION_ORDER,
    render_prompt_sections_v1,
    render_treatment_prompt_v1,
)


class PromptBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        experiment = Path(__file__).parents[1]
        self.config_path = experiment / "config/treatments/prompt-contract-v1.json"
        self.target_path = experiment / "fixtures/treatments/synthetic-target-v1.json"
        self.config = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.target = json.loads(self.target_path.read_text(encoding="utf-8"))

    def test_named_section_tracer_renders_three_systems(self) -> None:
        rendered = render_treatment_prompt_v1(self.config, self.target)

        self.assertEqual(tuple(rendered), ("A", "B", "C"))
        for system, raw in rendered.items():
            self.assertIsInstance(raw, bytes)
            self.assertNotIn(b"\r", raw)
            self.assertTrue(raw.endswith(b"\n"))
            self.assertFalse(raw.endswith(b"\n\n"))
            self.assertEqual(
                tuple(render_prompt_sections_v1(self.config, self.target, system)),
                PROMPT_SECTION_ORDER,
            )
            self.assertEqual(raw, b"".join(render_prompt_sections_v1(self.config, self.target, system).values()))

    def test_frame_and_shared_sections_are_exact(self) -> None:
        sections = {
            system: render_prompt_sections_v1(self.config, self.target, system)
            for system in ("A", "B", "C")
        }

        self.assertEqual(self.config["demonstration_count"], 2)
        for system in sections:
            self.assertEqual(sections[system]["demonstrations"].count(b"Demonstration "), 2)
        self.assertEqual(sections["A"]["frame_instructions"], b"")
        self.assertEqual(sections["B"]["frame_instructions"], sections["C"]["frame_instructions"])
        for section in ("adjudication_instructions", "output_schema", "evidence_rules"):
            self.assertEqual(sections["B"][section], sections["C"][section])
            self.assertTrue(sections["B"][section])
        for section in ("shared_guidance", "target"):
            self.assertEqual(sections["A"][section], sections["B"][section])
            self.assertEqual(sections["B"][section], sections["C"][section])

    def test_target_and_raw_text_boundaries_fail_closed(self) -> None:
        invalid_target = deepcopy(self.target)
        invalid_target["source_text"] = ""
        for invalid_config, target in (
            (self.config, invalid_target),
            ({**self.config, "extra": True}, self.target),
            ({**self.config, "shared_guidance": "line\r\n"}, self.target),
        ):
            with self.assertRaisesRegex(PromptBundleError, "^PROMPT_(CONTRACT|TARGET|RAW_BYTES)_INVALID$"):
                render_treatment_prompt_v1(invalid_config, target)

        noncanonical = json.loads(canonical_json_bytes(self.config))
        noncanonical["shared_guidance"] = noncanonical["shared_guidance"].replace("\n", "\r\n")
        with self.assertRaisesRegex(PromptBundleError, "^PROMPT_CONTRACT_INVALID$"):
            render_treatment_prompt_v1(noncanonical, self.target)


if __name__ == "__main__":
    unittest.main()
