"""shomei_aggregate — roll verified claims into a personhoodCredential. R0 scaffold. ADR-2606072100.

Aggregation logic (IAL ladder + proof-of-personhood + W3C VC) is implemented + tested in
methods/aggregate.py. Live issuance of a com.etzhayyim.shomei.personhoodCredential to the kotoba
Datom log is outward-gated (G11) and member-signed (G7 no-server-key); the cell .solve() raises at R0.
"""
from __future__ import annotations

from typing import Any


class AggregateCell:
    def solve(self, input_state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "shomei R0 scaffold: shomei_aggregate computes credentials offline "
            "(methods/aggregate.py); live member-signed issuance is outward-gated (G7/G11)."
        )
