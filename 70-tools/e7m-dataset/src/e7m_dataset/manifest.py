"""Append-only human index at 90-docs/baien/datasets.jsonl."""

from __future__ import annotations

import json
from pathlib import Path


MANIFEST_REL = Path("90-docs/baien/datasets.jsonl")


def repo_root_from_cwd() -> Path:
    cur = Path.cwd().resolve()
    for p in [cur, *cur.parents]:
        if (p / "CLAUDE.md").exists() and (p / "90-docs").is_dir():
            return p
    raise RuntimeError("e7m-dataset must be run inside the etzhayyim/root checkout")


def manifest_path(repo_root: Path) -> Path:
    return repo_root / MANIFEST_REL


def append(row: dict, repo_root: Path | None = None) -> Path:
    repo_root = repo_root or repo_root_from_cwd()
    path = manifest_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
    return path
