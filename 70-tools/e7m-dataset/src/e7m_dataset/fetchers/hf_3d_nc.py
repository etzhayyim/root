"""HuggingFace 3D NC-subset fetcher (CC-BY-NC mixed, Tier C, G13).

Stages a 3D-asset subset from a HuggingFace dataset known to carry
CC-BY-NC (or mixed-with-NC) licensing — primarily Objaverse-XL NC
slices — under
``${ETZ_DATASET_ROOT}/datasets-staging/hf-3d-nc-{owner}-{repo}-{captureTs}/``.

Per ADR-2605262500 §2 (Tier C — G13 fleet-internal carve-out). Derived
sim recordings from any scene that consumes this fetcher's output MUST
carry `-nc-` infix and route through judah LiteLLM + SBT-gate only.
The fetcher itself does not produce a published artifact; it is the
**ingest** layer of the G13 backstop.

Implementation = thin wrapper around `e7m_dataset.fetchers.hf.fetch`
with three additional enforcement layers:

  1. Operator MUST pin one of the KNOWN_NC_REPOS allowlist slugs OR
     pass ``--explicit-nc-acknowledged`` (operator-on-license).
  2. Include-glob is locked to 3D-asset extensions
     (.glb / .gltf / .obj / .fbx / .ply / .stl / .usd / .usdc / .usdz)
     so we don't pull NC-tainted READMEs or images that aren't usable
     in kami-usd anyway.
  3. The output FetchResult carries ``tier="C"`` and
     ``license="CC-BY-NC-4.0-or-mixed"`` in `source`, regardless of
     what the HF model card claims — G13 is a content-tier judgement,
     not a metadata-trust judgement.

The staging directory name carries ``hf-3d-nc-`` as a visual flag
distinct from the generic ``hf-`` prefix used by `fetchers/hf.py`.
This makes accidental Tier-A treatment of a Tier-C bundle obvious
in shell prompts and git status.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import httpx

from . import FetchResult
from . import hf as hf_fetcher


# Allowlist of known CC-BY-NC (or NC-mixed) 3D asset HF datasets.
# Operator MUST pass one of these slugs unless they pass
# `--explicit-nc-acknowledged` (signing the license-on-them).
KNOWN_NC_REPOS: dict[str, dict[str, str]] = {
    "objaverse-xl-cc-by-nc": {
        "owner": "allenai",
        "repo": "objaverse-xl",
        "subset_note": "NC subset filtered via metadata.license == 'cc-by-nc-*' (operator-side filter; this fetcher pulls per-subset shard).",
    },
    "objaverse-xl-nc-cars": {
        "owner": "allenai",
        "repo": "objaverse-xl",
        "subset_note": "Passenger-car-set vol2 NC subset — used by wadachi R1 W3 props per ADR-2605262500 §9.",
    },
}

# Lock the include-globs to 3D-asset extensions only.
DEFAULT_3D_ASSET_GLOBS: tuple[str, ...] = (
    "*.glb", "*.gltf",
    "*.obj", "*.fbx",
    "*.ply", "*.stl",
    "*.usd", "*.usdc", "*.usdz", "*.usda",
)


@dataclass
class Hf3dNcFetchOpts:
    # One of KNOWN_NC_REPOS slugs.
    slug: Optional[str] = None
    # Operator-supplied owner/repo (requires `explicit_nc_acknowledged=True`).
    explicit_owner: Optional[str] = None
    explicit_repo: Optional[str] = None
    explicit_nc_acknowledged: bool = False
    revision: str = "main"
    # Defensive cap. Objaverse-XL slices can be very large; default 20 GiB.
    max_bytes: Optional[int] = 20 * (1 << 30)
    # Extra include globs OR replace defaults.
    extra_include_globs: list[str] = field(default_factory=list)
    replace_default_globs: bool = False
    user_agent: str = hf_fetcher.DEFAULT_USER_AGENT
    timeout_sec: float = 1800.0
    client: Optional[httpx.Client] = None


def _resolve_repo(opts: Hf3dNcFetchOpts) -> tuple[str, str, str, str]:
    """Return (owner, repo, slug_or_explicit, subset_note)."""
    if opts.slug is not None:
        spec = KNOWN_NC_REPOS.get(opts.slug)
        if spec is None:
            raise ValueError(
                f"unknown HF 3D NC slug '{opts.slug}'. Known: "
                f"{sorted(KNOWN_NC_REPOS)} — or pass "
                f"--explicit-owner / --explicit-repo / "
                f"--explicit-nc-acknowledged for an operator-on-license repo."
            )
        return spec["owner"], spec["repo"], opts.slug, spec["subset_note"]

    if opts.explicit_owner and opts.explicit_repo:
        if not opts.explicit_nc_acknowledged:
            raise ValueError(
                "explicit_owner/explicit_repo require explicit_nc_acknowledged=True "
                "(G13 license-on-operator acknowledgement; operator signs that "
                "they verified the upstream license is NC-compatible and that "
                "all derived sim outputs will follow ADR-2605262500 §7 G4-G5)."
            )
        slug = f"{opts.explicit_owner}-{opts.explicit_repo}"
        return opts.explicit_owner, opts.explicit_repo, slug, "operator-supplied"

    raise ValueError(
        "either `slug` (from KNOWN_NC_REPOS) or "
        "`explicit_owner + explicit_repo + explicit_nc_acknowledged=True` required"
    )


def fetch(staging_dir: Path, opts: Hf3dNcFetchOpts) -> FetchResult:
    """Fetch a NC-licensed 3D-asset bundle from HF Hub.

    Delegates to `e7m_dataset.fetchers.hf.fetch` after enforcing the
    G13 NC allowlist + 3D-asset glob lockdown, then renames the
    staging dir from ``hf-{owner}-{repo}-{ts}`` to
    ``hf-3d-nc-{slug}-{ts}`` for clear visual tier flagging.
    """
    owner, repo, slug, subset_note = _resolve_repo(opts)

    include_globs = list(opts.extra_include_globs)
    if not opts.replace_default_globs:
        include_globs = list(DEFAULT_3D_ASSET_GLOBS) + include_globs
    if not include_globs:
        raise ValueError(
            "include_globs is empty: would pull arbitrary non-3D files. "
            "Set replace_default_globs=False or add extra_include_globs."
        )

    hf_opts = hf_fetcher.HfFetchOpts(
        owner=owner,
        repo=repo,
        revision=opts.revision,
        repo_type="datasets",
        max_bytes=opts.max_bytes,
        include_globs=include_globs,
        exclude_globs=[],
        user_agent=opts.user_agent,
        timeout_sec=opts.timeout_sec,
        client=opts.client,
    )

    inner = hf_fetcher.fetch(staging_dir, hf_opts)

    # Rename the staging dir so it carries the `hf-3d-nc-` visual flag.
    capture_ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    new_dirname = f"hf-3d-nc-{slug}-{capture_ts}"
    new_dir = staging_dir / new_dirname
    if new_dir.exists():
        new_dir = staging_dir / f"{new_dirname}-{inner.revision[-8:]}"
    inner.staging_path.rename(new_dir)

    # Recompute totals (no byte change; just path move).
    size_bytes = sum(p.stat().st_size for p in new_dir.rglob("*") if p.is_file())
    file_count = sum(1 for p in new_dir.rglob("*") if p.is_file())

    return FetchResult(
        name=f"hf-3d-nc:{slug}",
        revision=inner.revision,
        staging_path=new_dir,
        file_count=file_count,
        size_bytes=size_bytes,
        source={
            **inner.source,
            "fetcher": "hf_3d_nc",
            "slug": slug,
            "owner": owner,
            "repo": repo,
            "subset_note": subset_note,
            "tier": "C",                                 # G13
            "license": "CC-BY-NC-4.0-or-mixed",          # ADR-2605262500 Tier C
            "g13_nc_infix_required_in_artifacts": True,
            "captured_at": capture_ts,
            "include_globs_locked_3d_only": True,
        },
    )


__all__ = [
    "DEFAULT_3D_ASSET_GLOBS",
    "Hf3dNcFetchOpts",
    "KNOWN_NC_REPOS",
    "fetch",
]
