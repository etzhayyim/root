"""Phase state machine for the mitooshi series_ingest (見通し) cell.

The G4 source membrane. A public series is recorded into the Datom log ONLY if its
:series/source-class is in the primary-public set; proprietary terminals (Bloomberg /
CapIQ / Refinitiv / 四季報) and scraped Google-Trends are NOT representable and REFUSE
ingest (kanjo §2(c)/(e) anti-gatekeeping precedent). Observations are append-only and
carry observed-at (非終末論 — latest is the current value, the stream is the trail; no
overwrite).

This is a REFUSAL gate, not a clamp: an off-source series is refused, never silently
re-labelled.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

ALLOWED_SOURCE_CLASS = (
    "public-broadcast", "primary-disclosure", "open-commons", "gov-open-data", "member-principal",
)


class IngestPhase(Enum):
    INIT = "init"
    SCREENED = "screened"
    RECORDED = "recorded"
    REFUSED = "refused"


@dataclass
class IngestState:
    phase: str = IngestPhase.INIT.value
    series_id: str = ""
    source_class: str = ""
    source: str = ""
    kind: str = ""
    obs: list = field(default_factory=list)  # [{observed_at, value}]
    refusal: str = ""
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> IngestState:
    return IngestState(**d.get("cell_state", {}))


def _norm(v: str | None) -> str:
    return (v or "").lstrip(":")


def transition_to_screened(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.series_id = state.get("series_id", cs.series_id)
    cs.source_class = _norm(state.get("source_class", cs.source_class))
    cs.source = state.get("source", cs.source)
    cs.kind = _norm(state.get("kind", cs.kind))
    cs.obs = list(state.get("obs", cs.obs))
    if cs.source_class not in ALLOWED_SOURCE_CLASS:
        cs.refusal = (
            f"G4: series {cs.series_id!r} source-class {cs.source_class!r} not in the "
            f"primary-public set {ALLOWED_SOURCE_CLASS}; proprietary terminals + scraped "
            f"Google-Trends are unrepresentable (kanjo §2(c)/(e))."
        )
        cs.phase = IngestPhase.REFUSED.value
        return {"cell_state": cs.__dict__}
    cs.refusal = ""
    cs.phase = IngestPhase.SCREENED.value
    return {"cell_state": cs.__dict__}


def transition_to_recorded(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    if cs.phase != IngestPhase.SCREENED.value:
        cs.refusal = f"cannot record from phase {cs.phase!r}; screen first"
        cs.phase = IngestPhase.REFUSED.value
        return {"cell_state": cs.__dict__}
    # append-only: observations sorted by observed-at; latest is current (非終末論)
    obs = sorted(cs.obs, key=lambda o: o.get("observed_at", 0))
    cs.payload = {
        "seriesId": cs.series_id,
        "sourceClass": cs.source_class,
        "kind": cs.kind,
        "obsCount": len(obs),
        "latestAt": obs[-1]["observed_at"] if obs else None,
        "latestValue": obs[-1].get("value") if obs else None,
        "recorded": True,
    }
    cs.phase = IngestPhase.RECORDED.value
    return {"cell_state": cs.__dict__}
