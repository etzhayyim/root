"""DataLad subdataset orchestration helpers.

`e7m-dataset add` chains:

  staging → ensure_subdataset()
          → import_files(fetch_result)
          → save_subdataset()
          → copy_to_local_store()

Each step is a thin wrapper around `datalad` / `git annex` invoked as a
subprocess. Failures bubble up as `subprocess.CalledProcessError`.

The directory remote (`local-store`) is created lazily on first
subdataset creation, pointing into
`${paths.annex_store}/<subdataset_name>/`. The backend is explicitly
set to SHA256E per ADR-2605241500 §D2 to override DataLad's MD5E
default when the superdataset uses `text2git`.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .paths import Paths


SUPERDATASET_REL = Path("90-docs/baien/datasets")


def _repo_root() -> Path:
    from .manifest import repo_root_from_cwd
    return repo_root_from_cwd()


def superdataset_path() -> Path:
    return _repo_root() / SUPERDATASET_REL


def subdataset_path(name: str) -> Path:
    return superdataset_path() / name


def ensure_subdataset(name: str, paths: Paths) -> Path:
    """Create-or-get the subdataset; init the directory remote on first
    create. Idempotent."""
    sub = subdataset_path(name)
    if sub.exists() and (sub / ".datalad").exists():
        return sub
    super_path = superdataset_path()
    sub.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["datalad", "create", "-d", str(super_path), str(sub)],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(sub), "config", "annex.backend", "SHA256E"],
        check=True,
    )
    remote_root = paths.subdataset_annex_dir(name)
    remote_root.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "git", "-C", str(sub), "annex", "initremote", "local-store",
            "type=directory", f"directory={remote_root}",
            "encryption=none", "chunk=64MiB",
        ],
        check=True,
    )
    return sub


def import_files(sub: Path, staging_dir: Path, *, move: bool = True) -> int:
    """Copy/move files from `staging_dir` into the subdataset tree
    (preserving relative paths). Returns the number of files placed."""
    count = 0
    for src in staging_dir.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(staging_dir)
        dst = sub / rel
        if dst.exists():
            # idempotent: skip identical-size files
            if dst.stat().st_size == src.stat().st_size:
                continue
            dst.unlink()
        dst.parent.mkdir(parents=True, exist_ok=True)
        if move:
            shutil.move(str(src), str(dst))
        else:
            shutil.copy2(src, dst)
        count += 1
    return count


def save_subdataset(sub: Path, message: str) -> str:
    """`datalad save -m <message>` and return the resulting commit sha."""
    subprocess.run(
        ["datalad", "save", "-d", str(sub), "-m", message],
        check=True,
    )
    sha = subprocess.check_output(
        ["git", "-C", str(sub), "rev-parse", "HEAD"], text=True
    ).strip()
    return sha


def copy_to_local_store(sub: Path, *, jobs: int = 4) -> None:
    """`git annex copy . --to=local-store --jobs=<n>`."""
    subprocess.run(
        [
            "git", "-C", str(sub), "annex", "copy", ".",
            "--to=local-store", f"--jobs={jobs}",
        ],
        check=True,
    )


__all__ = [
    "SUPERDATASET_REL",
    "copy_to_local_store",
    "ensure_subdataset",
    "import_files",
    "save_subdataset",
    "subdataset_path",
    "superdataset_path",
]
