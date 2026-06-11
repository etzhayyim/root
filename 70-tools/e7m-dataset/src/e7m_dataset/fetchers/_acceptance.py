"""Per-source acceptance-flag gate for Tier-C upstream archives.

Per ADR-2605262400 W3. Tier-C upstreams (Rapid7 Open Data, CAIDA,
OpenINTEL, CZDS, Common Crawl) each require explicit acceptance of
their terms of use before any download is initiated. The operator
records that acceptance once by writing a small TOML flag file under

  ~/.etzhayyim/source-acceptance/<source>.toml

The fetcher reads it before issuing any HTTP request. Missing /
malformed acceptance ⇒ ``MissingAcceptanceFlag`` ⇒ fetch aborts
fail-closed.

Acceptance file shape (minimal):

    [acceptance]
    source           = "rapid7-open-data"
    accepted_at      = "2026-05-26T13:40:00Z"
    accepted_by_did  = "did:web:etzhayyim.com:actor:dataset-operator"
    upstream_tos_url = "https://opendata.rapid7.com/about/"
    notes            = "Research use only, internal-only G13 carve-out"

The operator may add additional keys; the gate only checks that the
file exists, parses as TOML, and contains a non-empty ``accepted_at``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


_DEFAULT_DIR = Path.home() / ".etzhayyim" / "source-acceptance"


class MissingAcceptanceFlag(RuntimeError):
    """Raised when a Tier-C source has no operator-acceptance record."""


@dataclass(frozen=True)
class Acceptance:
    source: str
    accepted_at: str
    accepted_by_did: str = ""
    upstream_tos_url: str = ""
    notes: str = ""
    extra: dict[str, Any] = None  # type: ignore[assignment]


def acceptance_dir() -> Path:
    """Resolve the directory holding per-source acceptance flags.

    Overridable via ``ETZ_SOURCE_ACCEPTANCE_DIR`` env var (used in
    tests + ephemeral sandbox runs).
    """
    override = os.environ.get("ETZ_SOURCE_ACCEPTANCE_DIR")
    if override:
        return Path(override)
    return _DEFAULT_DIR


def require_acceptance(source: str) -> Acceptance:
    """Read + validate the acceptance flag for `source`.

    Returns the parsed Acceptance on success. Raises
    ``MissingAcceptanceFlag`` on any of: missing dir, missing file,
    malformed TOML, missing ``[acceptance]`` table, missing
    ``accepted_at``.
    """
    path = acceptance_dir() / f"{source}.toml"
    if not path.exists():
        raise MissingAcceptanceFlag(
            f"No acceptance flag for Tier-C source '{source}'. "
            f"Create {path} with an [acceptance] table containing "
            f"accepted_at + accepted_by_did before this fetch will run. "
            f"See ADR-2605262400 W3."
        )
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise MissingAcceptanceFlag(
            f"Acceptance flag at {path} is not valid TOML: {exc}"
        ) from exc
    block = raw.get("acceptance")
    if not isinstance(block, dict):
        raise MissingAcceptanceFlag(
            f"Acceptance flag at {path} is missing the [acceptance] table."
        )
    accepted_at = block.get("accepted_at", "")
    if not isinstance(accepted_at, str) or not accepted_at.strip():
        raise MissingAcceptanceFlag(
            f"Acceptance flag at {path} is missing accepted_at."
        )
    known = {"source", "accepted_at", "accepted_by_did", "upstream_tos_url", "notes"}
    extras = {k: v for k, v in block.items() if k not in known}
    return Acceptance(
        source=str(block.get("source") or source),
        accepted_at=accepted_at,
        accepted_by_did=str(block.get("accepted_by_did", "")),
        upstream_tos_url=str(block.get("upstream_tos_url", "")),
        notes=str(block.get("notes", "")),
        extra=extras or {},
    )


__all__ = [
    "Acceptance",
    "MissingAcceptanceFlag",
    "acceptance_dir",
    "require_acceptance",
]
