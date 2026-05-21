"""etzhayyim_sdk — Python binding for the @etzhayyim/sdk RW-free substrate.

Public API exports. All substrate calls must go through this package;
direct imports of @atproto/api, viem, or IPFS client libraries from app
code are prohibited (ADR-2605172000).

Status: M3 — pds + mst are real impls; ipfs + l2 are detailed stubs (M4/M5).

ADR references:
  ADR-2605172000 — RW-free substrate hard rule (this package is the only seam)
  ADR-2605171800 — MST → IPFS → Base L2 anchor pipeline
  ADR-2605215200 — shinka Pregel MST rewrite
  ADR-2605215300 — yoro Python primitives MST rewrite addendum
"""

from __future__ import annotations

from etzhayyim_sdk import coalesce, cursor, errors, ipfs, l2, llm, mst, pds
from etzhayyim_sdk.coalesce import RequestCoalescer
from etzhayyim_sdk.errors import (
    LlmAuthError,
    LlmError,
    LlmNetworkError,
    LlmParseError,
    LlmRateLimitError,
    LlmServerError,
    PdsAuthError,
    PdsError,
    PdsNetworkError,
    PdsNotFoundError,
    PdsServerError,
)
from etzhayyim_sdk.types import (
    ActorQualityReportRecord,
    BpmnActivityEventRecord,
    EvolutionEventRecord,
    KyumeiSignalRecord,
    ShinkaHeartbeatRecord,
    TranslationLinkRecord,
)

__version__ = "0.1.0"

__all__ = [
    # Modules (stub + real)
    "pds",
    "mst",
    "ipfs",
    "l2",
    "llm",
    "coalesce",
    "cursor",
    "errors",
    # Error types (PDS hierarchy)
    "PdsError",
    "PdsAuthError",
    "PdsNotFoundError",
    "PdsServerError",
    "PdsNetworkError",
    # Error types (LLM hierarchy)
    "LlmError",
    "LlmNetworkError",
    "LlmServerError",
    "LlmAuthError",
    "LlmRateLimitError",
    "LlmParseError",
    # Coalescer (real impl — M2 critical path)
    "RequestCoalescer",
    # Types (real — lexicon-matched dataclasses)
    "ShinkaHeartbeatRecord",
    "KyumeiSignalRecord",
    "EvolutionEventRecord",
    "TranslationLinkRecord",
    "BpmnActivityEventRecord",
    "ActorQualityReportRecord",
]
