---
schema_version: 1
open_count: 0
waived_count: 0
fixed_count: 2
total_count: 2
last_updated: 2026-07-31T18:04:08.419Z
---

# Broken Windows Ledger

> Cross-phase defect register. `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 02 | deviation | experiments/specchoice-v1.3.2/config/measurement/canonical-adjudication-schema-v1.json |  | Canonical schema bytes and accepted-path validation were corrected during 02-02 verification. | fixed |  | 2026-07-31T15:18:50.933Z | 2026-07-31T15:20:40.686Z |
| 2 | 02 | deviation | experiments/specchoice-v1.3.2/src/specchoice_measurement/cli.py |  | Adversarial report publication uses exclusive create and directory fsync to preserve existing targets. | fixed |  | 2026-07-31T18:03:49.941Z | 2026-07-31T18:04:08.419Z |

````json
[
  {
    "id": 1,
    "kind": "deviation",
    "phase": "02",
    "file": "experiments/specchoice-v1.3.2/config/measurement/canonical-adjudication-schema-v1.json",
    "line": null,
    "description": "Canonical schema bytes and accepted-path validation were corrected during 02-02 verification.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-07-31T15:18:50.933Z",
    "resolved_at": "2026-07-31T15:20:40.686Z"
  },
  {
    "id": 2,
    "kind": "deviation",
    "phase": "02",
    "file": "experiments/specchoice-v1.3.2/src/specchoice_measurement/cli.py",
    "line": null,
    "description": "Adversarial report publication uses exclusive create and directory fsync to preserve existing targets.",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-07-31T18:03:49.941Z",
    "resolved_at": "2026-07-31T18:04:08.419Z"
  }
]
````
