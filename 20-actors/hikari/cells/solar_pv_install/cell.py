"""SolarPvInstallCell — hikari R0 scaffold per ADR-2605261100.

R0 scaffold. Site survey + panel install + tracker config + commissioning.
G2 (Charter Rider §2(g) panel sourcing audit per lot — no XUAR polysilicon,
no conflict minerals) structural enforcement.
"""

from __future__ import annotations

from typing import Any


class SolarPvInstallCell:
    """Solar PV install + tracker config + commissioning."""

    def __init__(self) -> None:
        pass

    def solve(self, state: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "hikari R0 scaffold: solar_pv_install cell not activated. "
            "Requires ADR-2605261100 Council ratify + ≥1 LANDS parcel + "
            "Charter Rider §2(g) panel sourcing audit framework operational."
        )
