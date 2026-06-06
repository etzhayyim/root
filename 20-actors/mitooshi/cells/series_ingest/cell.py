"""LangGraph Pregel wrapper for mitooshi series_ingest (見通し) — R0 scaffold.

G4 source membrane: records a primary-public time-series + its append-only observations
into the kotoba Datom log. The coded reasoner lives in state_machine.py. .solve() raises
at R0 — any LIVE ingest (AIS/ADS-B firehose, EDINET pull, Common-Crawl, member-principal
Google-Trends) is Council Lv6+ + operator gated (G10).
"""
from __future__ import annotations
from typing import Any


class SeriesIngestCell:
    """Primary-public series + observation ingest. G4."""

    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "mitooshi R0 scaffold: series_ingest screens offline; live data ingest "
            "(AIS/ADS-B/EDINET/Common-Crawl/member-principal Trends) is Council Lv6+ + operator gated (G10)."
        )
