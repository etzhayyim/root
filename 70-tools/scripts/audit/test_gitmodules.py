"""Tests for the iter-65 .gitmodules fix.

iter-65 added `ignore = dirty` to the `[submodule "90-docs/baien/datasets"]`
block in .gitmodules, suppressing a recurring `Too many levels of
symbolic links` warning from git status that fired on every commit
in the iter-30-64 audit-substrate work session.

The fix is one config line in one file. Without a test, a future
git-submodule reorg could trivially revert it and the noise returns
silently. These tests catch that.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
GITMODULES = REPO_ROOT / ".gitmodules"


def _read_gitmodules() -> str:
    return GITMODULES.read_text() if GITMODULES.is_file() else ""


# ─── Structural canary ─────────────────────────────────────────────────


class TestGitmodulesFix:
    def test_gitmodules_file_exists(self):
        assert GITMODULES.is_file(), ".gitmodules missing at repo root"

    def test_baien_datasets_submodule_block_exists(self):
        body = _read_gitmodules()
        assert '[submodule "90-docs/baien/datasets"]' in body, (
            "baien/datasets submodule block missing from .gitmodules"
        )

    def test_baien_datasets_has_ignore_dirty(self):
        """iter-65: `ignore = dirty` is what suppresses the recurring
        `Too many levels of symbolic links` warning during git status
        traversal of the nested DataLad subdatasets."""
        body = _read_gitmodules()
        # Find the block + verify `ignore = dirty` is inside it (before
        # the next [submodule ...] or end-of-file).
        block_start = body.find('[submodule "90-docs/baien/datasets"]')
        assert block_start != -1, "baien/datasets block missing"

        # Block ends at the next [submodule ...] header or EOF.
        next_block = body.find("[submodule ", block_start + 1)
        block_body = body[block_start:next_block] if next_block != -1 else body[block_start:]

        assert "ignore = dirty" in block_body, (
            "iter-65 fix lost: `ignore = dirty` missing from the "
            "[submodule 90-docs/baien/datasets] block in .gitmodules. "
            "Without it, `git status` emits a 'Too many levels of "
            "symbolic links' warning on every invocation (the nested "
            "DataLad subdataset's git-annex symlinks exceed MAXSYMLINKS "
            "during git's working-tree walk)."
        )


# ─── Behavioral verification: `git status` emits no warning ───────────


class TestGitStatusClean:
    def test_git_status_emits_no_symlink_loop_warning(self):
        result = subprocess.run(
            ["git", "status"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            timeout=15,
        )
        combined = (result.stdout + result.stderr).lower()
        assert "too many levels of symbolic links" not in combined, (
            "iter-65 fix appears reverted or insufficient: git status "
            "is emitting the symlink-loop warning again. Check "
            ".gitmodules for the `ignore = dirty` flag on the "
            "90-docs/baien/datasets submodule block."
        )

    def test_git_status_succeeds(self):
        result = subprocess.run(
            ["git", "status"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            timeout=15,
        )
        assert result.returncode == 0, (
            f"git status failed with rc {result.returncode}\n"
            f"stderr:\n{result.stderr}"
        )
