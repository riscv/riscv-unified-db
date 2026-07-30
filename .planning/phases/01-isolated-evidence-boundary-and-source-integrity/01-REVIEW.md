---
phase: 01-isolated-evidence-boundary-and-source-integrity
reviewed: 2026-07-30T16:00:48Z
depth: standard
files_reviewed: 19
files_reviewed_list:
  - experiments/specchoice-v1.3.2/audit/environment/environment-receipt-phase-start-001.json
  - experiments/specchoice-v1.3.2/baselines/phase-start-v2.json
  - experiments/specchoice-v1.3.2/bundles/candidates/source-contract-v2-pr2192-86a0021b/snapshot-manifest.json
  - experiments/specchoice-v1.3.2/config/boundary_allowlist.json
  - experiments/specchoice-v1.3.2/receipts/control-update-decision-plan01.json
  - experiments/specchoice-v1.3.2/receipts/environment-decision.json
  - experiments/specchoice-v1.3.2/receipts/integrity-receipt.json
  - experiments/specchoice-v1.3.2/receipts/integrity-receipt.md
  - experiments/specchoice-v1.3.2/receipts/reviewer-boundary-decision.json
  - experiments/specchoice-v1.3.2/receipts/source-publication-decision.json
  - experiments/specchoice-v1.3.2/src/specchoice_evidence/baseline.py
  - experiments/specchoice-v1.3.2/src/specchoice_evidence/bundle.py
  - experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py
  - experiments/specchoice-v1.3.2/src/specchoice_evidence/environment.py
  - experiments/specchoice-v1.3.2/src/specchoice_evidence/receipt.py
  - experiments/specchoice-v1.3.2/src/specchoice_evidence/source_contract.py
  - experiments/specchoice-v1.3.2/tests/test_bundle_verifier.py
  - experiments/specchoice-v1.3.2/tests/test_environment.py
  - experiments/specchoice-v1.3.2/tests/test_filesystem_boundary.py
findings:
  critical: 2
  warning: 2
  info: 0
  total: 4
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-30T16:00:48Z
**Depth:** standard
**Files Reviewed:** 19
**Status:** issues_found

## Summary

The boundary, candidate, receipt, environment, and reviewer-decision flows were reviewed in context, including the verifier and filesystem dependencies they call. The submitted tests pass, but the authority checks are forgeable by any writer of the local artifacts and receipt publication can overwrite or tear the established integrity package.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Reviewer authorization is only forgeable payload text

**Classification:** BLOCKER

**File:** `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_evidence/source_contract.py:236`

**Issue:** `validate_source_publication_decision()` treats a fixed literal token and three JSON booleans as reviewer authorization (lines 236-261). The local-acceptance path repeats the pattern with a fixed disposition and booleans (lines 316-324), then `command_accept_local_mvp()` accepts the resulting decision (CLI lines 366-374). There is no signature, trusted key, immutable attestation, or protected reviewer-owned store. Consequently, any local process that can write a JSON file can manufacture an "approved" decision for a candidate and generate a locally accepted receipt; the SHA-256 fields only bind attacker-controlled bytes and do not authenticate the reviewer. This defeats the Phase 1 reviewer boundary.

**Fix:** Define a reviewer trust root outside the writable evidence directory (for example, a pinned public key), require a detached signature over the canonical decision bytes, and verify that signature in both source-publication and local-acceptance validation before honoring authorization fields. Bind the verified signer identity and signature algorithm/key ID into the decision schema.

### CR-02: Receipt commands overwrite the established integrity receipt

**Classification:** BLOCKER

**File:** `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_evidence/receipt.py:270`

**Issue:** `write_receipt_package()` uses unconditional `write_text()` and `write_bytes()` (lines 276-281), so it silently replaces existing evidence. In particular, `write-integrity-receipt` defaults to the same `receipts/integrity-receipt.json` and `.md` paths as the local-MVP success flow (CLI lines 590-596), but constructs the intentionally rejected receipt (CLI lines 333-350). Running that command after local acceptance destroys the passing receipt and replaces it with a failure artifact. This is data loss and breaks the claimed immutable, replayable evidence chain.

**Fix:** Make receipt targets create-once (`open("xb")` plus fsync and atomic rename) and reject pre-existing paths. Use separate, generation-specific filenames for blocked versus local-MVP receipts; never let commands with opposite outcomes share defaults.

## Warnings

### WR-01: Candidate construction bypasses the canonical decision-file gate

**Classification:** WARNING

**File:** `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_evidence/cli.py:311`

**Issue:** `command_build_candidate()` decodes `args.decision` directly (line 313), unlike `command_validate_source_decision()` which rejects non-canonical decision bytes (lines 274-280). A non-canonical source decision is therefore rejected by the validation command but can still authorize construction. This creates a candidate whose stated approval artifact fails the advertised canonicality gate.

**Fix:** Add a canonical source-decision loader analogous to `_load_canonical_local_acceptance_decision()` and use it in both validation and candidate construction.

### WR-02: Receipt package writes are ordered inconsistently and are not crash-safe

**Classification:** WARNING

**File:** `/Users/zhdeng/Documents/LFX_RISCV_SpecChoice/experiments/specchoice-v1.3.2/src/specchoice_evidence/receipt.py:276`

**Issue:** The method docstring promises to persist canonical JSON first, but the implementation writes Markdown claiming `reviewer_package_complete: true` before it writes the JSON (lines 276-281). If the later JSON write fails, the Markdown remains a completed-looking package while the JSON is missing or still represents an older receipt. The error path handles only Markdown failure, so this split-brain state is left on disk.

**Fix:** Stage both artifacts under unique temporary names, fsync them, publish the authoritative JSON with `reviewer_package_complete: false`, then publish the Markdown and finally atomically replace JSON with the completed version. On any failure, remove only the staged files and leave the prior package untouched.

---

_Reviewed: 2026-07-30T16:00:48Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
