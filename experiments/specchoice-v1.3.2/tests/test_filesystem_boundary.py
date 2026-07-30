# SPDX-License-Identifier: BSD-3-Clause-Clear
from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from specchoice_evidence.canonical import canonical_json_bytes, sha256_bytes
from specchoice_evidence.baseline import (
    BaselineError,
    capture_baseline,
    check_boundary,
    create_restart_baseline,
    load_baseline,
    path_is_allowed,
    validate_restart_lineage,
)
from specchoice_evidence.filesystem import (
    FilesystemPolicyError,
    inspect_authoritative_path,
    reject_hardlink_dependency,
    require_relative_posix_path,
)
from specchoice_evidence.cli import build_parser


class FilesystemBoundaryTests(unittest.TestCase):
    def test_committed_out_of_allowlist_path_is_blocking(self) -> None:
        """A clean live worktree must not hide a post-baseline committed violation."""
        payload = {
            "allowlist": {"exact_files": [], "roots": ["experiments/specchoice-v1.3.2/"]},
            "file_kind_policy": {"allowed": ["directory", "regular_file"], "rejected": []},
            "index": {"staged_paths": []},
            "repository": {"head_commit": "", "path_basis": "repository_relative_posix"},
            "schema_version": "1",
            "worktree": {"ignored_paths_in_scope": [], "tracked_changes": [], "untracked_files": []},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args: str) -> None:
                subprocess.run(["git", "-C", os.fspath(root), *args], check=True, stdout=subprocess.PIPE)
            git("init")
            (root / "inside.txt").write_text("baseline", encoding="utf-8")
            git("add", "inside.txt")
            git("-c", "user.email=test@example.invalid", "-c", "user.name=SpecChoice Test", "commit", "-m", "baseline")
            payload["repository"]["head_commit"] = subprocess.run(
                ["git", "-C", os.fspath(root), "rev-parse", "HEAD"], check=True, stdout=subprocess.PIPE, text=True
            ).stdout.strip()
            baseline = root / "baseline.json"
            capture_baseline(baseline, payload)
            (root / "outside.txt").write_text("committed violation", encoding="utf-8")
            git("add", "outside.txt")
            git("-c", "user.email=test@example.invalid", "-c", "user.name=SpecChoice Test", "commit", "-m", "outside")
            result = check_boundary(root, baseline)
        self.assertEqual(result.blocking_violations, 1)
        self.assertEqual(result.classifications[0]["path"], "outside.txt")

    def test_control_decision_binds_active_artifacts_and_requires_approval(self) -> None:
        experiment_root = Path(__file__).resolve().parents[1]
        baseline = experiment_root / "baselines/phase-start-v2.json"
        allowlist = experiment_root / "config/boundary_allowlist.json"
        policy = experiment_root / "baselines/ds-store-policy-override-v1.json"
        payload = {
            "allowlist": {"path": "config/boundary_allowlist.json", "sha256": sha256_bytes(allowlist.read_bytes())},
            "baseline": {"path": "baselines/phase-start-v2.json", "sha256": sha256_bytes(baseline.read_bytes())},
            "boundary_policy": {
                "path": "baselines/ds-store-policy-override-v1.json",
                "schema_version": "1",
                "sha256": sha256_bytes(policy.read_bytes()),
            },
            "disputes": [],
            "reviewer": {"disposition": "approved", "signal": "approved"},
            "schema_version": "1",
        }
        with tempfile.TemporaryDirectory() as directory:
            decision = Path(directory) / "control-decision.json"
            decision.write_bytes(canonical_json_bytes(payload))
            parser = build_parser()
            arguments = [
                "validate-control-decision",
                str(decision),
                "--baseline",
                "baselines/phase-start-v2.json",
                "--allowlist",
                "config/boundary_allowlist.json",
                "--policy-override",
                "baselines/ds-store-policy-override-v1.json",
            ]
            self.assertEqual(parser.parse_args(arguments).handler(parser.parse_args(arguments)), 0)
            payload["reviewer"]["disposition"] = "disputed"
            decision.write_bytes(canonical_json_bytes(payload))
            with self.assertRaisesRegex(BaselineError, "CONTROL_DECISION_NOT_APPROVED"):
                parser.parse_args(arguments).handler(parser.parse_args(arguments))

    def test_allowlist_is_exact_not_prefix(self) -> None:
        allowlist = {"roots": ["experiments/specchoice-v1.3.2/"], "exact_files": [".planning/STATE.md"]}
        self.assertTrue(path_is_allowed("experiments/specchoice-v1.3.2/a.txt", allowlist))
        self.assertFalse(path_is_allowed("experiments/specchoice-v1.3.2-escape/a.txt", allowlist))
        self.assertTrue(path_is_allowed(".planning/STATE.md", allowlist))

    def test_escape_and_symlink_fail_before_open(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "safe.txt").write_text("safe", encoding="utf-8")
            os.symlink("safe.txt", root / "link.txt")
            for invalid in ("../safe.txt", "/safe.txt", "safe\\x.txt"):
                with self.assertRaisesRegex(FilesystemPolicyError, "PATH_ESCAPE_DETECTED"):
                    require_relative_posix_path(invalid)
            with self.assertRaisesRegex(FilesystemPolicyError, "SYMLINK_REJECTED"):
                inspect_authoritative_path(root, "link.txt")

    def test_relative_posix_path_rejects_normalized_escape_syntax(self) -> None:
        for invalid in ("safe/.", "safe//child", "./safe", "safe/../outside"):
            with self.assertRaisesRegex(FilesystemPolicyError, "PATH_ESCAPE_DETECTED"):
                require_relative_posix_path(invalid)

    def test_regular_file_is_independent_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sample.txt").write_bytes(b"raw\r\nbytes")
            evidence = inspect_authoritative_path(root, "sample.txt")
            self.assertEqual(evidence.file_kind, "regular_file")
            self.assertEqual(evidence.byte_length, 10)
            self.assertEqual(evidence.hardlink_count, 1)

    def test_hardlink_dependency_is_rejected_without_rejecting_independent_bytes(self) -> None:
        with self.assertRaisesRegex(FilesystemPolicyError, "HARDLINK_DEPENDENCY_REJECTED"):
            reject_hardlink_dependency(True)
        reject_hardlink_dependency(False)

    def test_regular_hardlink_remains_independently_hashed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.bin"
            source.write_bytes(b"independent content")
            os.link(source, root / "linked.bin")
            evidence = inspect_authoritative_path(root, "linked.bin")
        self.assertEqual(evidence.file_kind, "regular_file")
        self.assertEqual(evidence.hardlink_count, 2)
        self.assertEqual(evidence.byte_length, len(b"independent content"))

    def test_fifo_and_unproven_mount_boundary_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            os.mkfifo(root / "evidence.fifo")
            with self.assertRaisesRegex(FilesystemPolicyError, "SPECIAL_FILE_KIND_REJECTED"):
                inspect_authoritative_path(root, "evidence.fifo")
        root_stat = os.stat_result((stat.S_IFDIR | 0o755, 1, 10, 1, 0, 0, 0, 0, 0, 0))
        mounted_stat = os.stat_result((stat.S_IFDIR | 0o755, 2, 11, 1, 0, 0, 0, 0, 0, 0))

        def fake_lstat(path: Path) -> os.stat_result:
            return root_stat if path.name == "root" else mounted_stat

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            root.mkdir()
            with patch.object(Path, "lstat", fake_lstat):
                with self.assertRaisesRegex(FilesystemPolicyError, "MOUNT_BOUNDARY_UNPROVEN"):
                    inspect_authoritative_path(root, "mounted")

    def test_baseline_refuses_overwrite_and_requires_canonical_bytes(self) -> None:
        payload = {
            "schema_version": "1",
            "allowlist": {"roots": ["experiments/specchoice-v1.3.2/"], "exact_files": []},
            "worktree": {"tracked_changes": [], "untracked_files": [], "ignored_paths_in_scope": []},
        }
        with tempfile.TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline.json"
            capture_baseline(baseline, payload)
            load_baseline(baseline)
            with self.assertRaisesRegex(BaselineError, "BASELINE_ALREADY_EXISTS"):
                capture_baseline(baseline, payload)
            baseline.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(BaselineError, "BASELINE_NOT_CANONICAL"):
                load_baseline(baseline)

    def test_baseline_entries_require_stable_path_ordering(self) -> None:
        payload = {
            "schema_version": "1",
            "allowlist": {"roots": ["experiments/specchoice-v1.3.2/"], "exact_files": []},
            "worktree": {
                "tracked_changes": [],
                "untracked_files": [
                    {"path": "z.txt", "file_kind": "regular_file", "byte_length": 1, "sha256": "a" * 64},
                    {"path": "a.txt", "file_kind": "regular_file", "byte_length": 1, "sha256": "a" * 64},
                ],
                "ignored_paths_in_scope": [],
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline.json"
            baseline.write_bytes(canonical_json_bytes(payload))
            with self.assertRaisesRegex(BaselineError, "BASELINE_PATHS_NOT_SORTED"):
                load_baseline(baseline)

    def test_new_outside_allowlist_is_blocking(self) -> None:
        payload = {
            "schema_version": "1",
            "allowlist": {"roots": ["experiments/specchoice-v1.3.2/"], "exact_files": []},
            "worktree": {"tracked_changes": [], "untracked_files": [], "ignored_paths_in_scope": []},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline.json"
            capture_baseline(baseline, payload)
            (root / "outside.txt").write_text("outside", encoding="utf-8")
            with patch("specchoice_evidence.baseline.capture_current_paths", return_value={"outside.txt"}):
                result = check_boundary(root, baseline)
        self.assertEqual(result.blocking_violations, 1)
        self.assertEqual(result.classifications[0]["status"], "new_out_of_boundary")

    def test_restart_retains_original_inventory_without_reclassification(self) -> None:
        payload = {
            "schema_version": "1",
            "allowlist": {"roots": ["experiments/specchoice-v1.3.2/"], "exact_files": []},
            "file_kind_policy": {"allowed": ["directory", "regular_file"], "rejected": []},
            "index": {"staged_paths": []},
            "repository": {"head_commit": "a" * 40, "path_basis": "repository_relative_posix"},
            "worktree": {
                "tracked_changes": [],
                "untracked_files": [{"path": ".DS_Store", "file_kind": "regular_file", "byte_length": 1, "sha256": "b" * 64}],
                "ignored_paths_in_scope": [],
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            v1 = root / "phase-start-v1.json"
            v2 = root / "phase-start-v2.json"
            parent_hash = capture_baseline(v1, payload)
            restart_hash, returned_parent = create_restart_baseline(
                v1,
                v2,
                previous_reference="phase-start-v1.json",
                reason_code="D15_RESTART_NEW_OUT_OF_BOUNDARY",
                remediation={"removed_path": "experiments/.DS_Store"},
            )
            self.assertEqual(returned_parent, parent_hash)
            self.assertNotEqual(restart_hash, parent_hash)
            self.assertEqual(validate_restart_lineage(v2, v1), (restart_hash, parent_hash))
            self.assertEqual(v1.read_bytes(), canonical_json_bytes(payload))
            successor = json.loads(v2.read_text(encoding="utf-8"))
            successor["worktree"]["untracked_files"] = []
            v2.write_bytes(canonical_json_bytes(successor))
            with self.assertRaisesRegex(BaselineError, "RESTART_RECLASSIFICATION_DETECTED"):
                validate_restart_lineage(v2, v1)

    def test_modified_preexisting_path_outside_allowlist_blocks(self) -> None:
        payload = {
            "schema_version": "1",
            "allowlist": {"roots": ["experiments/specchoice-v1.3.2/"], "exact_files": []},
            "worktree": {
                "tracked_changes": [],
                "untracked_files": [
                    {
                        "path": "outside.txt",
                        "file_kind": "regular_file",
                        "byte_length": 3,
                        "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
                    }
                ],
                "ignored_paths_in_scope": [],
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline.json"
            capture_baseline(baseline, payload)
            (root / "outside.txt").write_text("changed", encoding="utf-8")
            with patch("specchoice_evidence.baseline.capture_current_paths", return_value={"outside.txt"}):
                result = check_boundary(root, baseline)
        self.assertEqual(result.blocking_violations, 1)
        self.assertEqual(result.classifications[0]["status"], "modified_out_of_boundary")

    def test_ds_store_churn_is_visible_but_nonblocking(self) -> None:
        payload = {
            "schema_version": "1",
            "allowlist": {"roots": ["experiments/specchoice-v1.3.2/"], "exact_files": []},
            "worktree": {
                "tracked_changes": [],
                "untracked_files": [
                    {"path": ".DS_Store", "file_kind": "regular_file", "byte_length": 3, "sha256": "b" * 64},
                    {"path": "outside.txt", "file_kind": "regular_file", "byte_length": 3, "sha256": "b" * 64},
                ],
                "ignored_paths_in_scope": [],
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline.json"
            capture_baseline(baseline, payload)
            (root / ".DS_Store").write_bytes(b"changed")
            (root / "outside.txt").write_bytes(b"changed")
            with patch(
                "specchoice_evidence.baseline.capture_current_paths",
                return_value={".DS_Store", "outside.txt"},
            ):
                result = check_boundary(root, baseline)
        by_path = {item["path"]: item for item in result.classifications}
        self.assertEqual(by_path[".DS_Store"]["status"], "modified_out_of_boundary")
        self.assertFalse(by_path[".DS_Store"]["blocking"])
        self.assertFalse(by_path[".DS_Store"]["attributed_to_phase"])
        self.assertEqual(by_path[".DS_Store"]["diagnostic"], "DS_STORE_IGNORED_OS_METADATA")
        self.assertTrue(by_path["outside.txt"]["blocking"])
        self.assertEqual(result.blocking_violations, 1)

    def test_new_and_deleted_ds_store_are_visible_but_nonblocking(self) -> None:
        payload = {
            "schema_version": "1",
            "allowlist": {"roots": ["experiments/specchoice-v1.3.2/"], "exact_files": []},
            "worktree": {
                "tracked_changes": [],
                "untracked_files": [
                    {"path": "removed/.DS_Store", "file_kind": "regular_file", "byte_length": 3, "sha256": "b" * 64}
                ],
                "ignored_paths_in_scope": [],
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline.json"
            capture_baseline(baseline, payload)
            (root / "new").mkdir()
            (root / "new" / ".DS_Store").write_bytes(b"new")
            with patch(
                "specchoice_evidence.baseline.capture_current_paths",
                return_value={"new/.DS_Store"},
            ):
                result = check_boundary(root, baseline)
        by_path = {item["path"]: item for item in result.classifications}
        self.assertEqual(by_path["removed/.DS_Store"]["status"], "deleted_out_of_boundary")
        self.assertEqual(by_path["new/.DS_Store"]["status"], "new_out_of_boundary")
        self.assertTrue(all(not item["blocking"] for item in by_path.values()))
