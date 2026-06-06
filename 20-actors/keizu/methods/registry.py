"""registry.py — 系図 (keizu) public-source registry access. ADR-2606066000.

Loads registry/sources.seed.json and exposes the source catalog to the ingest/bridge paths:
  - get_source / source_ids
  - sourcing_for(source_id) — G11 honesty DRIVEN BY the registry: a record from a VERIFIED source
    may be :authoritative; from an unverified-seed source it stays :representative.
  - assert_source_allowed — the Charter Rider §2(e)/N5 commercial-gov-intel deny-list as a
    reusable RUNTIME guard (the same SOURCE_DENY weave.validate_* enforces on derived datoms).

Stdlib only.
"""

from __future__ import annotations

import json
import pathlib

from weave import SOURCE_DENY, source_denied

_REG_PATH = pathlib.Path(__file__).resolve().parents[1] / "registry" / "sources.seed.json"


def load_registry(path: pathlib.Path = _REG_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def source_ids() -> list[str]:
    return [s["sourceId"] for s in load_registry()["sources"]]


def get_source(source_id: str) -> dict:
    for s in load_registry()["sources"]:
        if s["sourceId"] == source_id:
            return s
    raise KeyError(f"no such source {source_id!r}")


def sourcing_for(source_id: str) -> str:
    """G11 — :authoritative only when the registry marks the source verified; else :representative.
    An unknown source id is treated conservatively as :representative (never auto-authoritative)."""
    try:
        status = get_source(source_id).get("verificationStatus", "")
    except KeyError:
        return ":representative"
    return ":authoritative" if status == "verified" else ":representative"


def assert_source_allowed(*texts: str) -> None:
    """Charter Rider §2(e)/N5 — raise if any text cites a commercial gov-intel terminal. Reusable
    runtime guard (mirror of the SOURCE_DENY check baked into weave.validate_rel/validate_money)."""
    if (d := source_denied(list(texts))):
        raise ValueError(f"Rider §2(e)/N5: {d!r} is a prohibited commercial gov-intel terminal")


__all__ = ["load_registry", "source_ids", "get_source", "sourcing_for",
           "assert_source_allowed", "SOURCE_DENY"]
