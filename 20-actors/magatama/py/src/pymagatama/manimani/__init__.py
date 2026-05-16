"""manimani — LangGraph user-intake routing pipeline (ADR-2605080800).

Public API surface for the manimani actor:

  - :class:`ManimaniState`            — Pydantic v2 StateGraph state (ADR-2605080200)
  - :class:`IngestInput`              — XRPC body of `ai.gftd.apps.manimani.ingest`
  - :class:`ProjectClassification`    — classifier structured output
  - :class:`Artifact`                 — output of one processor invocation
  - :func:`build_graph`               — compiled LangGraph StateGraph (7 node)
  - :func:`build_app`                 — Granian-ready FastAPI app exposing
                                        `/runs`, `/runs/{id}`, `/health`,
                                        `/_app/meta`, and the 6 XRPC bridges
                                        per ADR-2605080600 + ADR-2605080800.

Deployment: `pymagatama.manimani.server:app` is the canonical Granian
ASGI target (Helm release `mitama-manimani-pool`). Image: same
`ghcr.io/gftdcojp/pymagatama:<tag>-amd64` as the Zeebe worker; the
LangGraph runtime is selected at process boot via
`MANIMANI_RUNTIME=langgraph` env var (Phase 2 wiring).
"""

from pymagatama.manimani.state import (  # noqa: F401
    ManimaniState,
    IngestInput,
    Artifact,
    ProjectClassification,
    NewProjectProposal,
    SourceKind,
    ProjectKind,
    ArtifactKind,
    RunStatus,
)
from pymagatama.manimani.graph import build_graph  # noqa: F401

__all__ = [
    "ManimaniState",
    "IngestInput",
    "Artifact",
    "ProjectClassification",
    "NewProjectProposal",
    "SourceKind",
    "ProjectKind",
    "ArtifactKind",
    "RunStatus",
    "build_graph",
]
