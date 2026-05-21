"""mst-projector — AT Protocol MST firehose subscriber → LanceDB indexed views.

Per ADR-2605215500 (Phase 3, server-side filter).  Public API surface:

    from mst_projector.indexer import get_indexer
    from mst_projector.query_api import build_app, serve
"""

from __future__ import annotations

__version__ = "0.0.0"
__all__ = ["indexer", "query_api"]
