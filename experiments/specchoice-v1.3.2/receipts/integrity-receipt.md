# Phase 1 Integrity Receipt

- Authoritative SHA-256: `de81c088eab230967f60b536598b77ddf154e34659b79aac9375543b7ac7d2f8`
- Generator version: `1`
- Outcome: `fail`
- Reviewer package complete: `true`
- Phase-start baseline SHA-256: `e8f7e153ffbc5285b361039153f8eea6205448e9f82e2b14efa9af3e74912e15`
- Environment decision SHA-256: `9f0342c4d2848200e5f894c834f69e828aeb70a7fb813e541258f43d7fc3d246`
- Source identity: `rejected_attempt`

## Boundary classifications

- `.DS_Store` — `modified_out_of_boundary`, blocking=false, attributed_to_phase=false
- `.github/.DS_Store` — `preexisting_unrelated`, blocking=false, attributed_to_phase=false
- `.planning/.DS_Store` — `modified_out_of_boundary`, blocking=false, attributed_to_phase=false
- `.planning/STATE.md` — `allowed_phase_change`, blocking=false, attributed_to_phase=true
- `backends/.DS_Store` — `preexisting_unrelated`, blocking=false, attributed_to_phase=false
- `doc/.DS_Store` — `preexisting_unrelated`, blocking=false, attributed_to_phase=false
- `experiments/.DS_Store` — `new_out_of_boundary`, blocking=false, attributed_to_phase=false
- `ext/.DS_Store` — `preexisting_unrelated`, blocking=false, attributed_to_phase=false
- `sorbet/.DS_Store` — `preexisting_unrelated`, blocking=false, attributed_to_phase=false
- `spec/.DS_Store` — `preexisting_unrelated`, blocking=false, attributed_to_phase=false
- `spec/std/.DS_Store` — `preexisting_unrelated`, blocking=false, attributed_to_phase=false
- `tests/.DS_Store` — `preexisting_unrelated`, blocking=false, attributed_to_phase=false
- `tools/.DS_Store` — `preexisting_unrelated`, blocking=false, attributed_to_phase=false

## Diagnostics

- `SOURCE_GENERATION_NOT_ACCEPTED`
- `DS_STORE_IGNORED_OS_METADATA`
