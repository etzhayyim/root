"""keiei graph package — per-role deliberation pipelines.

Phase 1 (iter126): cto only — wired through `_pipeline` with an LLM-backed
`deliberate` stage (graceful fallback to deterministic stub when no
LLM endpoint is reachable).

Phase 2: add cfo / cmo / chro for vacant-seat coverage.
Phase 3: shadow roles (ceo / coo / clo / ciso / cdo).
"""

from __future__ import annotations

from typing import Any

from ._pipeline import DecideResponse, deliberate

# Importing each role module registers its hook into _pipeline._HOOKS.
from . import cto  # noqa: F401  — side-effect import
from . import cfo  # noqa: F401
from . import cmo  # noqa: F401
from . import chro # noqa: F401
from . import ceo  # noqa: F401
from . import coo  # noqa: F401
from . import clo  # noqa: F401
from . import ciso # noqa: F401
from . import cdo  # noqa: F401

__all__ = ["DecideResponse", "deliberate"]


async def dispatch_decide(role_id: str, params: dict[str, Any]) -> DecideResponse:
    """Public entry called by lsp_server._decide after gate verdict allows."""
    return await deliberate(role_id, params)
