"""manifest.append — append-only JSONL round-trip."""

from __future__ import annotations

import json

import pytest

from e7m_dataset import manifest as manifest_mod


def _make_repo_root(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# stub", encoding="utf-8")
    (tmp_path / "90-docs").mkdir()
    return tmp_path


def test_append_round_trip(tmp_path, monkeypatch):
    root = _make_repo_root(tmp_path)
    monkeypatch.chdir(root)

    row_a = {"name": "A", "revision": "r1"}
    row_b = {"name": "B", "revision": "r2"}
    p = manifest_mod.append(row_a)
    manifest_mod.append(row_b)

    assert p == root / "90-docs" / "baien" / "datasets.jsonl"
    lines = p.read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0]) == row_a
    assert json.loads(lines[1]) == row_b


def test_repo_root_from_cwd_errors_outside(tmp_path, monkeypatch):
    """When cwd is not inside an etzhayyim/root checkout, raise."""
    monkeypatch.chdir(tmp_path)
    with pytest.raises(RuntimeError):
        manifest_mod.repo_root_from_cwd()
