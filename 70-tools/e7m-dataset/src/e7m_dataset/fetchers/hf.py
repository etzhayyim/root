"""Hugging Face Hub fetcher (datasets + models).

Stages an HF repo snapshot under
``${ETZ_DATASET_ROOT}/datasets-staging/hf-{owner}-{repo}-{captureTs}/``.

Uses the public Hub HTTP API (no SDK dep, just httpx):

  - ``GET /api/{datasets|models}/<owner>/<repo>/revision/<rev>``
      → resolves to a commit sha, surfaces `cardData.license`.
  - ``GET /api/{datasets|models}/<owner>/<repo>/tree/<sha>?recursive=true``
      → enumerates files (paginated when very large).
  - ``GET /{datasets|models}/<owner>/<repo>/resolve/<sha>/<path>``
      → streams individual file bytes; LFS redirects are followed
        transparently by httpx (follow_redirects=True).

The revision is the resolved 40-char git sha — stable even when the
caller asked for ``main`` / a tag / a branch. License is captured from
the model card when present, otherwise None (operator must supply).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import httpx

from . import FetchResult


DEFAULT_BASE_URL = "https://huggingface.co"
DEFAULT_USER_AGENT = "etzhayyim-e7m-dataset/0.0.1 (+https://etzhayyim.com)"


@dataclass
class HfFetchOpts:
    """Configuration for an HF Hub pull."""

    owner: str
    repo: str
    revision: str = "main"
    repo_type: str = "datasets"  # or "models"
    base_url: str = DEFAULT_BASE_URL
    user_agent: str = DEFAULT_USER_AGENT
    timeout_sec: float = 600.0
    # Defensive size cap (bytes). 0 disables the cap; None falls back to
    # a conservative 50 GiB default suitable for typical reference sets.
    max_bytes: Optional[int] = 50 * (1 << 30)
    # Optional include/exclude glob filters (Pathlib `Path.match`).
    include_globs: list[str] = field(default_factory=list)
    exclude_globs: list[str] = field(default_factory=list)
    # Inject for tests.
    client: Optional[httpx.Client] = None


class HfFetchError(RuntimeError):
    pass


def _api_url(opts: HfFetchOpts, suffix: str = "") -> str:
    return f"{opts.base_url}/api/{opts.repo_type}/{opts.owner}/{opts.repo}{suffix}"


def _resolve_revision(client: httpx.Client, opts: HfFetchOpts) -> tuple[str, Optional[str]]:
    """Return (sha, license_or_none)."""
    r = client.get(_api_url(opts, f"/revision/{opts.revision}"))
    if r.status_code == 404:
        # Fallback: plain endpoint with ?revision=<rev> (older form).
        r = client.get(_api_url(opts), params={"revision": opts.revision})
    if r.status_code >= 300:
        raise HfFetchError(
            f"resolve {opts.owner}/{opts.repo}@{opts.revision}: "
            f"{r.status_code} {r.text[:200]!r}"
        )
    info = r.json()
    sha = info.get("sha") or (info.get("commit") or {}).get("id")
    if not sha:
        raise HfFetchError(
            f"no sha in HF response for {opts.owner}/{opts.repo}@{opts.revision}"
        )
    card = info.get("cardData") or {}
    lic = card.get("license") if isinstance(card, dict) else None
    return sha, (str(lic) if lic else None)


def _list_tree(client: httpx.Client, opts: HfFetchOpts, sha: str) -> list[dict[str, Any]]:
    """Return flat list of `{path, size, type=file}` entries."""
    url = _api_url(opts, f"/tree/{sha}")
    out: list[dict[str, Any]] = []
    cursor: Optional[str] = None
    while True:
        params: dict[str, Any] = {"recursive": "true"}
        if cursor:
            params["cursor"] = cursor
        r = client.get(url, params=params)
        if r.status_code >= 300:
            raise HfFetchError(
                f"tree {opts.owner}/{opts.repo}@{sha}: "
                f"{r.status_code} {r.text[:200]!r}"
            )
        page = r.json()
        if isinstance(page, list):
            out.extend(e for e in page if e.get("type") == "file")
            return out
        out.extend(e for e in page.get("entries", []) if e.get("type") == "file")
        cursor = page.get("nextCursor")
        if not cursor:
            return out


def _matches(path: str, globs: list[str]) -> bool:
    if not globs:
        return False
    p = Path(path)
    return any(p.match(g) for g in globs)


def _filter(files: list[dict[str, Any]], opts: HfFetchOpts) -> list[dict[str, Any]]:
    if opts.include_globs:
        files = [f for f in files if _matches(f["path"], opts.include_globs)]
    if opts.exclude_globs:
        files = [f for f in files if not _matches(f["path"], opts.exclude_globs)]
    return files


def _download_file(
    client: httpx.Client,
    opts: HfFetchOpts,
    sha: str,
    rel_path: str,
    dest: Path,
) -> int:
    url = f"{opts.base_url}/{opts.repo_type}/{opts.owner}/{opts.repo}/resolve/{sha}/{rel_path}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with client.stream("GET", url) as r:
        if r.status_code >= 300:
            body = r.read()
            raise HfFetchError(
                f"download {rel_path}: {r.status_code} {body[:200]!r}"
            )
        with dest.open("wb") as fh:
            for chunk in r.iter_bytes(chunk_size=1 << 20):
                fh.write(chunk)
                n += len(chunk)
    return n


def fetch(staging_dir: Path, opts: HfFetchOpts) -> FetchResult:
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dataset_dirname = f"hf-{opts.owner}-{opts.repo}-{capture_ts}"
    out_dir = staging_dir / dataset_dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    owned_client = opts.client is None
    client = opts.client or httpx.Client(
        timeout=opts.timeout_sec,
        follow_redirects=True,
        headers={"User-Agent": opts.user_agent},
    )
    try:
        sha, lic = _resolve_revision(client, opts)
        files = _filter(_list_tree(client, opts, sha), opts)

        planned = sum(int(f.get("size") or 0) for f in files)
        if opts.max_bytes and planned and planned > opts.max_bytes:
            raise HfFetchError(
                f"hf {opts.owner}/{opts.repo}@{sha[:8]}: planned "
                f"{planned} bytes exceeds max_bytes={opts.max_bytes}. "
                f"Tighten --include / --exclude or pass --max-bytes 0."
            )

        total = 0
        for entry in files:
            rel = entry["path"]
            dest = out_dir / rel
            size = int(entry.get("size") or 0)
            if dest.exists() and size and dest.stat().st_size == size:
                total += dest.stat().st_size
                continue
            total += _download_file(client, opts, sha, rel, dest)
    finally:
        if owned_client:
            client.close()

    return FetchResult(
        name=(
            f"hf-dataset:{opts.owner}/{opts.repo}"
            if opts.repo_type == "datasets"
            else f"hf-model:{opts.owner}/{opts.repo}"
        ),
        revision=f"git:{sha}",
        staging_path=out_dir,
        file_count=len(files),
        size_bytes=total,
        source={
            "type": "hf-dataset" if opts.repo_type == "datasets" else "hf-model",
            "url": f"{opts.base_url}/{opts.repo_type}/{opts.owner}/{opts.repo}",
            "owner": opts.owner,
            "repo": opts.repo,
            "requestedRevision": opts.revision,
            "resolvedSha": sha,
            "captured_at": capture_ts,
            "license": lic,
            "includeGlobs": list(opts.include_globs),
            "excludeGlobs": list(opts.exclude_globs),
        },
    )


__all__ = [
    "DEFAULT_BASE_URL",
    "DEFAULT_USER_AGENT",
    "HfFetchError",
    "HfFetchOpts",
    "fetch",
]
