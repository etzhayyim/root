"""LangGraph Pregel wrapper for 高札 (kosatsu) designation_ingest — R0 scaffold.

Normalizes a public authority's designation export into validated `:designation/*` datoms.
.solve() raises at R0 (G8): live ingest of a real sanctions list is Council Lv6+ + operator +
member-signature gated. Offline normalization runs via methods/ingest.py.
"""
from __future__ import annotations

from typing import Any


class DesignationIngestCell:
    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "kosatsu R0 scaffold: designation_ingest normalizes offline; live list ingest "
            "(OFAC/EU/UN/UK-OFSI/JP-MOF/Interpol) is Council Lv6+ + operator + member-sig gated (G8)."
        )
