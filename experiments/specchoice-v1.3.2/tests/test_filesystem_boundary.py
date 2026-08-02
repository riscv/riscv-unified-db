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
    capture_committed_history,
    check_boundary,
    check_current_boundary,
    check_live_boundary,
    committed_boundary_projection,
    committed_boundary_projection_sha256,
    create_restart_baseline,
    load_baseline,
    path_is_allowed,
    validate_restart_lineage,
)
from specchoice_evidence.filesystem import (
    FilesystemPolicyError,
    inspect_authoritative_path,
    read_authoritative_file,
    reject_hardlink_dependency,
    require_relative_posix_path,
    replace_descriptor_file,
    write_new_descriptor_file,
)
from specchoice_evidence.cli import build_parser


class FilesystemBoundaryTests(unittest.TestCase):
    def _git(self, root: Path, *args: str) -> None:
        subprocess.run(["git", "-C", os.fspath(root), *args], check=True, stdout=subprocess.PIPE)

    def _commit(self, root: Path, message: str) -> str:
        self._git(
            root,
            "-c",
            "user.email=test@example.invalid",
            "-c",
            "user.name=SpecChoice Test",
            "commit",
            "-m",
            message,
        )
        return subprocess.run(
            ["git", "-C", os.fspath(root), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout.strip()

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

    def test_committed_history_collects_all_change_kinds_and_rejects_raw_record_damage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._git(root, "init")
            for name in ("modified.txt", "deleted.txt", "type-change.txt"):
                (root / name).write_text("baseline", encoding="utf-8")
            self._git(root, "add", ".")
            baseline_commit = self._commit(root, "baseline")
            (root / "added.txt").write_text("added", encoding="utf-8")
            (root / "modified.txt").write_text("modified", encoding="utf-8")
            self._git(root, "rm", "deleted.txt")
            (root / "type-change.txt").unlink()
            os.symlink("modified.txt", root / "type-change.txt")
            self._git(root, "add", "-A")
            reviewed_commit = self._commit(root, "all changes")
            changes = capture_committed_history(root, baseline_commit, reviewed_commit)

        self.assertEqual(
            {(change.path, change.change_kind) for change in changes},
            {
                ("added.txt", "added"),
                ("modified.txt", "modified"),
                ("deleted.txt", "deleted"),
                ("type-change.txt", "type_changed"),
            },
        )

        def malformed_git(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
            command = _args[0]
            assert isinstance(command, list)
            if "merge-base" in command:
                return subprocess.CompletedProcess(command, 0)
            if "rev-list" in command and "--parents" in command:
                return subprocess.CompletedProcess(command, 0, stdout=(b"a" * 40) + b" " + (b"b" * 40) + b"\n")
            if "rev-list" in command:
                return subprocess.CompletedProcess(command, 0, stdout=(b"a" * 40) + b"\n")
            if "diff" in command:
                return subprocess.CompletedProcess(command, 0, stdout=b":100644 100644 a b M\0")
            return subprocess.CompletedProcess(command, 0, stdout=(b"a" * 40) + b"\n")

        with patch("specchoice_evidence.baseline.subprocess.run", side_effect=malformed_git):
            with self.assertRaisesRegex(BaselineError, "BOUNDARY_HISTORY_PARSE_ERROR"):
                capture_committed_history(Path("fixture"), "start", "reviewed")

    def test_reviewed_revision_must_exist_and_descend_from_the_baseline_commit(self) -> None:
        payload = {
            "allowlist": {"exact_files": [], "roots": []},
            "repository": {"head_commit": "", "path_basis": "repository_relative_posix"},
            "schema_version": "1",
            "worktree": {"ignored_paths_in_scope": [], "tracked_changes": [], "untracked_files": []},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._git(root, "init")
            (root / "shared.txt").write_text("initial", encoding="utf-8")
            self._git(root, "add", "shared.txt")
            initial = self._commit(root, "initial")
            (root / "main.txt").write_text("main", encoding="utf-8")
            self._git(root, "add", "main.txt")
            baseline_commit = self._commit(root, "baseline")
            payload["repository"]["head_commit"] = baseline_commit
            baseline = root / "baseline.json"
            capture_baseline(baseline, payload)
            self._git(root, "checkout", "-b", "other", initial)
            (root / "other.txt").write_text("other", encoding="utf-8")
            self._git(root, "add", "other.txt")
            other = self._commit(root, "other")
            with self.assertRaisesRegex(BaselineError, "BOUNDARY_HISTORY_REVISION_INVALID"):
                check_boundary(root, baseline, reviewed_revision="missing")
            with self.assertRaisesRegex(BaselineError, "BOUNDARY_HISTORY_NOT_DESCENDANT"):
                check_boundary(root, baseline, reviewed_revision=other)

    def test_committed_history_preserves_add_then_delete_and_blocks_the_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._git(root, "init")
            (root / "initial.txt").write_text("baseline", encoding="utf-8")
            self._git(root, "add", "initial.txt")
            baseline_commit = self._commit(root, "baseline")
            baseline = root / "baseline.json"
            capture_baseline(
                baseline,
                {
                    "allowlist": {"exact_files": [], "roots": []},
                    "repository": {"head_commit": baseline_commit, "path_basis": "repository_relative_posix"},
                    "schema_version": "1",
                    "worktree": {"ignored_paths_in_scope": [], "tracked_changes": [], "untracked_files": []},
                },
            )
            transient = root / "outside-transient.txt"
            transient.write_text("must remain attributable", encoding="utf-8")
            self._git(root, "add", transient.name)
            self._commit(root, "add outside path")
            self._git(root, "rm", transient.name)
            reviewed = self._commit(root, "delete outside path")

            events = [event for event in capture_committed_history(root, baseline_commit, reviewed) if event.path == transient.name]
            frozen = committed_boundary_projection(root, baseline, reviewed_revision=reviewed)
            current = check_current_boundary(root, baseline)

        self.assertEqual([event.change_kind for event in events], ["added", "deleted"])
        self.assertEqual(len({event.commit for event in events}), 2)
        by_path = {item["path"]: item for item in frozen["boundary_classifications"]}
        self.assertEqual(
            [event["change_kind"] for event in by_path["outside-transient.txt"]["committed_changes"]],
            ["added", "deleted"],
        )
        self.assertTrue(by_path["outside-transient.txt"]["blocking"])
        self.assertTrue({item["path"]: item for item in current.classifications}["outside-transient.txt"]["blocking"])

    def test_committed_projection_is_frozen_at_revision_and_live_gate_is_separate(self) -> None:
        """Later decision/receipt commits and live dirt cannot alter an already reviewed basis."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._git(root, "init")
            (root / "initial.txt").write_text("baseline", encoding="utf-8")
            self._git(root, "add", "initial.txt")
            baseline_commit = self._commit(root, "baseline")
            baseline = root / "baseline.json"
            capture_baseline(
                baseline,
                {
                    "allowlist": {"exact_files": [], "roots": ["experiments/"]},
                    "repository": {"head_commit": baseline_commit, "path_basis": "repository_relative_posix"},
                    "schema_version": "1",
                    "worktree": {"ignored_paths_in_scope": [], "tracked_changes": [], "untracked_files": []},
                },
            )
            (root / "experiments").mkdir()
            (root / "experiments" / "implementation.txt").write_text("reviewed", encoding="utf-8")
            self._git(root, "add", "experiments/implementation.txt")
            reviewed = self._commit(root, "reviewed implementation")
            frozen = committed_boundary_projection(root, baseline, reviewed_revision=reviewed)
            frozen_digest = committed_boundary_projection_sha256(frozen)
            (root / "experiments" / "decision.json").write_text("later", encoding="utf-8")
            (root / "experiments" / "receipt.json").write_text("later", encoding="utf-8")
            self._git(root, "add", "experiments")
            self._commit(root, "later reviewer files")
            self.assertEqual(committed_boundary_projection(root, baseline, reviewed_revision=reviewed), frozen)
            self.assertEqual(committed_boundary_projection_sha256(frozen), frozen_digest)
            self.assertEqual(check_current_boundary(root, baseline).blocking_violations, 0)
            (root / "outside-committed.txt").write_text("block", encoding="utf-8")
            self._git(root, "add", "outside-committed.txt")
            self._commit(root, "post-review out of boundary")
            # The frozen proposal stays exactly at R, while the current issuance/finalize
            # gate sees the clean-worktree committed violation.
            self.assertEqual(committed_boundary_projection(root, baseline, reviewed_revision=reviewed), frozen)
            current = check_current_boundary(root, baseline)
            self.assertEqual(current.blocking_violations, 1)
            self.assertTrue({item["path"]: item for item in current.classifications}["outside-committed.txt"]["blocking"])
            with self.assertRaisesRegex(BaselineError, "BOUNDARY_REVIEWED_REVISION_NOT_FULL"):
                committed_boundary_projection(root, baseline, reviewed_revision="HEAD")
            (root / "outside-live.txt").write_text("block", encoding="utf-8")
            (root / ".DS_Store").write_text("visible", encoding="utf-8")
            live = check_live_boundary(root, baseline)
            self.assertEqual(live.blocking_violations, 1)
            by_path = {item["path"]: item for item in live.classifications}
            self.assertTrue(by_path["outside-live.txt"]["blocking"])
            self.assertFalse(by_path[".DS_Store"]["blocking"])
            self.assertEqual(by_path[".DS_Store"]["diagnostic"], "DS_STORE_IGNORED_OS_METADATA")

    def test_preexisting_inventory_path_preserves_committed_and_live_provenance_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._git(root, "init")
            path = root / "preexisting.txt"
            path.write_text("baseline", encoding="utf-8")
            self._git(root, "add", "preexisting.txt")
            baseline_commit = self._commit(root, "baseline")
            baseline = root / "baseline.json"
            capture_baseline(
                baseline,
                {
                    "allowlist": {"exact_files": [], "roots": []},
                    "repository": {"head_commit": baseline_commit, "path_basis": "repository_relative_posix"},
                    "schema_version": "1",
                    "worktree": {
                        "ignored_paths_in_scope": [],
                        "tracked_changes": [
                            {
                                "path": "preexisting.txt",
                                "file_kind": "regular_file",
                                "byte_length": len(b"baseline"),
                                "sha256": sha256_bytes(b"baseline"),
                            }
                        ],
                        "untracked_files": [],
                    },
                },
            )
            path.write_text("committed", encoding="utf-8")
            self._git(root, "add", "preexisting.txt")
            self._commit(root, "committed change")
            path.write_text("staged", encoding="utf-8")
            self._git(root, "add", "preexisting.txt")
            path.write_text("worktree", encoding="utf-8")
            result = check_boundary(root, baseline)

        self.assertEqual(len(result.classifications), 1)
        record = result.classifications[0]
        self.assertEqual(record["path"], "preexisting.txt")
        self.assertEqual(record["change_sources"], ["committed_history", "staged", "worktree"])
        self.assertEqual(record["committed_change"]["change_kind"], "modified")
        self.assertEqual(record["live_changes"], [{"source": "staged"}, {"source": "worktree"}])

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

    def test_descriptor_backed_read_requires_no_follow_support(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "sample.txt").write_bytes(b"raw\r\nbytes")
            evidence, content = read_authoritative_file(root, "sample.txt")
            self.assertEqual(evidence.sha256, sha256_bytes(content))
            self.assertEqual(content, b"raw\r\nbytes")
            with patch("specchoice_evidence.filesystem.os.O_NOFOLLOW", 0):
                with self.assertRaisesRegex(FilesystemPolicyError, "NOFOLLOW_UNAVAILABLE"):
                    read_authoritative_file(root, "sample.txt")

    def test_dirfd_reader_rejects_root_and_intermediate_rebind_without_escape(self) -> None:
        """A held authority directory must outlive lexical root/child replacement."""
        original_open = os.open
        for replaced_part in ("root", "nested"):
            with self.subTest(replaced_part=replaced_part), tempfile.TemporaryDirectory() as directory:
                parent = Path(directory)
                root = parent / "root"
                leaf = root / "nested" / "leaf.txt"
                leaf.parent.mkdir(parents=True)
                leaf.write_bytes(b"held-bytes")
                replacement = parent / "replacement"
                (replacement / "nested").mkdir(parents=True)
                (replacement / "nested" / "leaf.txt").write_bytes(b"replacement-bytes")
                triggered = False

                def rebind(path: object, flags: int, *args: object, **kwargs: object) -> int:
                    nonlocal triggered
                    # The hardened implementation opens the final component relative
                    # to a held parent; the old implementation opens the full path.
                    if not triggered and os.fspath(path) in {os.fspath(leaf), "leaf.txt"}:
                        triggered = True
                        if replaced_part == "root":
                            os.rename(root, parent / "old-root")
                            os.rename(replacement, root)
                        else:
                            os.rename(root / "nested", root / "old-nested")
                            os.rename(replacement / "nested", root / "nested")
                    return original_open(path, flags, *args, **kwargs)

                with patch("specchoice_evidence.filesystem.os.open", side_effect=rebind):
                    evidence, content = read_authoritative_file(root, "nested/leaf.txt")
                self.assertTrue(triggered)
                self.assertEqual(content, b"held-bytes")
                self.assertEqual(evidence.sha256, sha256_bytes(b"held-bytes"))

        # The two cutover writers must remain pinned to the original held parent
        # even if a concurrent pathname rebind happens between write and replace.
        for operation in ("create", "replace"):
            with self.subTest(operation=operation), tempfile.TemporaryDirectory() as directory:
                parent = Path(directory)
                root = parent / "root"
                root.mkdir()
                leaf = root / "authority.json"
                if operation == "replace":
                    leaf.write_bytes(b"v2")
                replacement = parent / "replacement"
                replacement.mkdir()
                triggered = False
                original_open = os.open

                def rebind(path: object, flags: int, *args: object, **kwargs: object) -> int:
                    nonlocal triggered
                    if not triggered and os.fspath(path) in {"authority.json", ".authority.json.cutover"}:
                        triggered = True
                        os.rename(root, parent / "old-root")
                        os.rename(replacement, root)
                    return original_open(path, flags, *args, **kwargs)

                with patch("specchoice_evidence.filesystem.os.open", side_effect=rebind):
                    if operation == "create":
                        write_new_descriptor_file(root, "authority.json", b"v3")
                    else:
                        replace_descriptor_file(root, "authority.json", b"v3", b"v2")
                self.assertTrue(triggered)
                self.assertEqual((parent / "old-root" / "authority.json").read_bytes(), b"v3")
                self.assertFalse((root / "authority.json").exists())

    def test_dirfd_reader_rejects_regular_to_fifo_immediate_open_without_blocking(self) -> None:
        """The final no-follow open must be nonblocking before a FIFO can be consumed."""
        original_open = os.open
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            leaf = root / "leaf.txt"
            leaf.write_bytes(b"regular")
            triggered = False

            def replace_with_fifo(path: object, flags: int, *args: object, **kwargs: object) -> int:
                nonlocal triggered
                if not triggered and os.fspath(path) in {os.fspath(leaf), "leaf.txt"}:
                    triggered = True
                    self.assertNotEqual(flags & os.O_NONBLOCK, 0, "final open must be nonblocking")
                    leaf.unlink()
                    os.mkfifo(leaf)
                return original_open(path, flags, *args, **kwargs)

            with patch("specchoice_evidence.filesystem.os.open", side_effect=replace_with_fifo):
                with self.assertRaisesRegex(FilesystemPolicyError, "SPECIAL_FILE_KIND_REJECTED"):
                    read_authoritative_file(root, "leaf.txt")
            self.assertTrue(triggered)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            existing = root / "leaf.txt"
            existing.write_bytes(b"existing")
            with self.assertRaisesRegex(FilesystemPolicyError, "AUTHORITATIVE_DESTINATION_EXISTS"):
                write_new_descriptor_file(root, "leaf.txt", b"new")
            self.assertEqual(existing.read_bytes(), b"existing")
            os.unlink(existing)
            os.symlink("elsewhere", existing)
            with self.assertRaisesRegex(FilesystemPolicyError, "SYMLINK_REJECTED"):
                replace_descriptor_file(root, "leaf.txt", b"new", b"existing")
            os.unlink(existing)
            os.mkfifo(existing)
            with self.assertRaisesRegex(FilesystemPolicyError, "SPECIAL_FILE_KIND_REJECTED"):
                replace_descriptor_file(root, "leaf.txt", b"new", b"existing")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("specchoice_evidence.filesystem.os.fsync", side_effect=OSError("fsync")):
                with self.assertRaisesRegex(FilesystemPolicyError, "AUTHORITATIVE_WRITE_INVALID"):
                    write_new_descriptor_file(root, "leaf.txt", b"new")
            (root / "leaf.txt").unlink()
            (root / "leaf.txt").write_bytes(b"old")
            with patch("specchoice_evidence.filesystem.os.replace", side_effect=OSError("replace")):
                with self.assertRaisesRegex(FilesystemPolicyError, "AUTHORITATIVE_WRITE_INVALID"):
                    replace_descriptor_file(root, "leaf.txt", b"new", b"old")
            self.assertEqual((root / "leaf.txt").read_bytes(), b"old")

            # A crash may leave the already-fsynced exact temporary payload. It is
            # reusable, but every other temporary form is an immutable failure.
            temporary = root / ".leaf.txt.cutover"
            temporary.write_bytes(b"new")
            replace_descriptor_file(root, "leaf.txt", b"new", b"old")
            self.assertEqual((root / "leaf.txt").read_bytes(), b"new")

        for maker, code in (
            (lambda path: path.write_bytes(b"wrong"), "AUTHORITATIVE_TEMPORARY_MISMATCH"),
            (lambda path: os.symlink("leaf.txt", path), "SYMLINK_REJECTED"),
            (lambda path: os.mkfifo(path), "SPECIAL_FILE_KIND_REJECTED"),
        ):
            with self.subTest(crash_temporary=code), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                leaf = root / "leaf.txt"
                temporary = root / ".leaf.txt.cutover"
                leaf.write_bytes(b"old")
                maker(temporary)
                with self.assertRaisesRegex(FilesystemPolicyError, code):
                    replace_descriptor_file(root, "leaf.txt", b"new", b"old")
                self.assertTrue(temporary.exists() or temporary.is_symlink())
                self.assertEqual(leaf.read_bytes(), b"old")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            leaf = root / "leaf.txt"
            leaf.write_bytes(b"old")
            with self.assertRaisesRegex(FilesystemPolicyError, "AUTHORITATIVE_TARGET_MISMATCH"):
                replace_descriptor_file(root, "leaf.txt", b"new", b"different")
            self.assertEqual(leaf.read_bytes(), b"old")
            with patch("specchoice_evidence.filesystem.os.write", return_value=0):
                with self.assertRaisesRegex(FilesystemPolicyError, "AUTHORITATIVE_WRITE_INVALID"):
                    replace_descriptor_file(root, "leaf.txt", b"new", b"old")
            self.assertTrue((root / ".leaf.txt.cutover").exists())

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
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            root.mkdir()
            (root / "mounted").mkdir()
            with patch(
                "specchoice_evidence.filesystem._open_directory",
                side_effect=FilesystemPolicyError("MOUNT_BOUNDARY_UNPROVEN"),
            ):
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
