Privileged Spec 19.3.1:

"The capacity and organization of a cache and the size of a cache block are both implementation-specific."

"In the initial set of CMO extensions, the size of a cache block shall be uniform throughout the system."

Manual observations:
- cache capacity → variable (implementation-specific)
- cache organization → variable (implementation-specific)
- cache block size → variable (implementation-specific)
- cache block size uniformity → constraint ("shall be uniform")

LLM filtering:
- Removed any invented parameters not directly justified by text
- Kept only parameters explicitly implied by "implementation-specific" and "shall"

LLMs used:
- GPT- 5.2(large-context model)

Reason:
Chosen for strong instruction-following and ability to process specification text while minimizing hallucinations.

Hallucination handling:
Earlier prompts caused the model to invent parameter names and behaviors not present in the specification.
The final prompt enforces strict grounding by requiring exact textual justification and prohibiting invented names.

Master Prompt:

You are assisting with AI-assisted extraction of architectural parameters from RISC-V specifications.

Extract parameters ONLY when the text explicitly implies variability via:
"implementation-specific", "implementation-defined", "optional", "may", "might", "should", or "shall".

Do NOT invent parameter names.
Quote exact sentences for justification.
Classify each parameter as named/unnamed and implementation-specific or architectural constraint.
Return results in YAML format suitable for the RISC-V Unified Database.

Use of LLM output:
The raw LLM output was treated as a candidate list of parameters.
Each candidate was manually verified against the specification text.
Only parameters with explicit textual justification were retained.
Any invented or weakly implied parameters were discarded.

LLM fine-tuning:
No model fine-tuning was performed.

Instead, hallucination was controlled using prompt engineering:
- Strict grounding rules
- Prohibition of invented parameter names
- Mandatory quotation of justifying sentences
- Manual verification of outputs

This approach was chosen because it is reproducible, transparent, and suitable for specification analysis tasks.

Prompt refinement process:
- Initial prompts produced hallucinated or overly broad parameters.
- Constraints were incrementally added to restrict extraction to explicit textual signals.
- The final prompt enforced grounding by requiring exact sentence-level justification.

Final outcome:
- Scope limited to Privileged Spec 19.3.1
- Four architectural parameters extracted
- All parameters are explicitly justified by the specification text
- Output formatted in YAML for direct inclusion in riscv-unified-db
- Hallucination risks mitigated through prompt design and manual verification

