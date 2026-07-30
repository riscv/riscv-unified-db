# SPDX-License-Identifier: BSD-3-Clause-Clear
"""Disposable Git graph tests for construction-only source proof."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from specchoice_evidence.git_proof import (
    GitProofError,
    fetch_canonical_pr_head,
    initialize_disposable_bare_repository,
    prove_pinned_snapshot,
    read_pinned_path,
    validate_consumed_file_request,
)


def git(*arguments: str, cwd: Path | None = None) -> str:
    """Run a disposable test Git command and return its stripped output."""
    return subprocess.run(
        ["git", *arguments],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


class GitProofTests(unittest.TestCase):
    """Exercise the Git object proof against local, disposable repositories."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.remote = self.root / "remote.git"
        self.audit = self.root / "audit.git"
        git("init", "-q", self.source.as_posix())
        git("config", "user.email", "test@example.invalid", cwd=self.source)
        git("config", "user.name", "SpecChoice test", cwd=self.source)
        (self.source / "fixture.txt").write_bytes(b"first\r\n")
        git("add", "fixture.txt", cwd=self.source)
        git("commit", "-qm", "first", cwd=self.source)
        self.ancestor = git("rev-parse", "HEAD", cwd=self.source)
        (self.source / "fixture.txt").write_bytes(b"second\r\n")
        git("commit", "-am", "second", "-q", cwd=self.source)
        self.head = git("rev-parse", "HEAD", cwd=self.source)
        git("clone", "--bare", "-q", self.source.as_posix(), self.remote.as_posix())
        git("--git-dir", self.remote.as_posix(), "update-ref", "refs/pull/7/head", self.head)
        initialize_disposable_bare_repository(self.audit)
        fetch_canonical_pr_head(self.audit, self.remote.as_posix(), 7)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_equal_head_and_reachable_ancestor_have_verified_commit_and_tree(self) -> None:
        equal = prove_pinned_snapshot(self.audit, 7, self.head)
        ancestor = prove_pinned_snapshot(self.audit, 7, self.ancestor)

        self.assertEqual(equal["verification_result"], "passed")
        self.assertEqual(equal["resolved_head_sha"], self.head)
        self.assertEqual(ancestor["verification_result"], "passed")
        self.assertEqual(ancestor["pinned_commit_sha"], self.ancestor)
        self.assertRegex(ancestor["pinned_tree_sha"], r"^[0-9a-f]{40}$")

    def test_unrelated_existing_commit_is_not_reachable_from_named_pr(self) -> None:
        other = self.root / "other"
        git("init", "-q", other.as_posix())
        git("config", "user.email", "test@example.invalid", cwd=other)
        git("config", "user.name", "SpecChoice test", cwd=other)
        (other / "other.txt").write_text("unrelated\n", encoding="utf-8")
        git("add", "other.txt", cwd=other)
        git("commit", "-qm", "unrelated", cwd=other)
        unrelated = git("rev-parse", "HEAD", cwd=other)
        git("-C", self.audit.as_posix(), "fetch", "--no-tags", other.as_posix(), unrelated)

        with self.assertRaisesRegex(GitProofError, "PR_PIN_NOT_REACHABLE"):
            prove_pinned_snapshot(self.audit, 7, unrelated)

    def test_missing_commit_tree_ref_path_and_subprocess_failures_are_distinct(self) -> None:
        with self.assertRaisesRegex(GitProofError, "PIN_COMMIT_MISSING"):
            prove_pinned_snapshot(self.audit, 7, "0" * 40)

        with self.assertRaisesRegex(GitProofError, "REQUESTED_PATH_MISSING"):
            read_pinned_path(self.audit, self.ancestor, "missing.txt")

        with self.assertRaisesRegex(GitProofError, "PR_REF_MISSING"):
            prove_pinned_snapshot(self.audit, 999, self.ancestor)

    def test_empty_or_unresolved_requests_never_authorize_whole_tree_copy(self) -> None:
        with self.assertRaisesRegex(GitProofError, "CONSUMED_FILE_INVENTORY_UNRESOLVED"):
            validate_consumed_file_request({"schema_version": "1", "state": "unresolved", "entries": []})
        with self.assertRaisesRegex(GitProofError, "CONSUMED_FILE_INVENTORY_EMPTY"):
            validate_consumed_file_request({"schema_version": "1", "state": "reviewed", "entries": []})


if __name__ == "__main__":
    unittest.main()
