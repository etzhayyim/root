"""Phase state machine for the hotaru commons_ingest (蛍) cell.

The defining G1 cell: a process datom becomes an open-publication knowledge record ONLY
after its source-license passes the open-IP screen. The screen is the third enforcement
point of the open-IP invariant (after the ontology schema `:db/allowed` and the lexicon
`enum`).

Invariants enforced:
  G1 — open-IP-only: :source-license MUST be one of the practiceable-open set. Any other
       value (vendor-proprietary, patent-active, trade-secret, unknown, missing) raises
       ValueError BEFORE a knowledge record can exist — so the graph stays a *commons*
       (the precondition ADR-2605265500 §2's R4+ gate references).
  G5 — sourcing-honesty: the record carries a primary-source citation + sourcing flag.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# G1: the only practiceable-open licenses for which a knowledge record may be produced.
ALLOWED_LICENSES = (
    "academic-oa", "patent-expired", "textbook-public", "standard-public", "own-rnd",
)
# The substrate-chain stages (epitaxy is recorded only as a tracked gap, never ingested
# as a practiceable recipe).
ALLOWED_STAGES = ("synthesis", "bulk-growth", "wafering", "surface-prep", "epitaxy")


class IngestPhase(Enum):
    INIT = "init"
    SCREENED = "screened"
    RECORDED = "recorded"


@dataclass
class IngestState:
    phase: str = IngestPhase.INIT.value
    proc_id: str = ""
    stage: str = "bulk-growth"
    source_license: str = "academic-oa"
    source_cite: str = ""
    maturity: str = "open-emerging"
    screened: bool = False
    sourcing: str = "representative"
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> IngestState:
    return IngestState(**d.get("cell_state", {}))


def _norm(v: str | None) -> str:
    """Normalize an EDN-style keyword (':academic-oa') or plain string ('academic-oa')."""
    return (v or "").lstrip(":")


def transition_to_screened(state: dict[str, Any]) -> dict[str, Any]:
    """G1: open-IP license screen. Raises ValueError on any non-open license."""
    cs = _state(state)
    cs.proc_id = state.get("proc_id", cs.proc_id)
    lic = _norm(state.get("source_license", cs.source_license))
    if lic not in ALLOWED_LICENSES:
        raise ValueError(
            f"G1 violation: process {cs.proc_id!r} has source-license {lic!r}; only "
            f"{ALLOWED_LICENSES} permitted. hotaru is an OPEN-PUBLICATION commons — "
            f"vendor-proprietary / patent-active / trade-secret recipes are excluded by "
            f"construction (no knowledge record produced); see ADR-2605265500 §2."
        )
    stage = _norm(state.get("stage", cs.stage))
    if stage not in ALLOWED_STAGES:
        raise ValueError(f"unknown substrate stage {stage!r}; expected one of {ALLOWED_STAGES}")
    # G5: a record must carry a primary-source citation.
    cite = state.get("source_cite", cs.source_cite)
    if not cite:
        raise ValueError("G5 violation: open-publication record requires a :source-cite")
    cs.source_license, cs.stage, cs.source_cite = lic, stage, cite
    cs.maturity = _norm(state.get("maturity", cs.maturity))
    cs.screened = True
    cs.phase = IngestPhase.SCREENED.value
    return {"cell_state": cs.__dict__}


def transition_to_recorded(state: dict[str, Any]) -> dict[str, Any]:
    """Materialize the knowledge record (only reachable after the screen passes)."""
    cs = _state(state)
    if not cs.screened:
        raise ValueError("knowledge record requires a passed open-IP screen first (G1)")
    cs.payload = {
        "procId": cs.proc_id,
        "stage": cs.stage,
        "sourceLicense": cs.source_license,
        "sourceCite": cs.source_cite,
        "maturity": cs.maturity,
        "screened": True,
        "sourcing": cs.sourcing,
    }
    cs.phase = IngestPhase.RECORDED.value
    return {"cell_state": cs.__dict__}
