"""grid_edge state machine — microgrid commissioning + dispatch (gated transitions).

Pure, deterministic transitions enforcing hikari gates. The runnable control loop
lives in ../../methods/microgrid.py; this wires it into a phase machine that ends
at a member-signed, dry-run dispatch record (G7/G8/G10). cell.py .solve() stays
Council-gated — these transitions are exercised by tests, not live actuation.
"""

from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "methods"))

from microgrid import commission_microgrid, to_datoms  # noqa: E402
from _substrate import require_member_signature, witness_quorum_ok  # noqa: E402


class GridPhase(Enum):
    INIT = "init"
    COMMISSIONED = "commissioned"
    DISPATCH_COMMITTED = "dispatch_committed"


@dataclass
class GridState:
    phase: str = GridPhase.INIT.value
    microgrid_id: str = "microgrid-01"
    use: str = "grid-control"
    load_step_kw: float = 140.0
    freq_restored: bool = False
    rocof_tripped: bool = False
    member_sig: str = ""
    server_sig: str = ""
    witness_sigs: list[str] = field(default_factory=list)
    payload: dict = field(default_factory=dict)


def _state(state: dict[str, Any]) -> GridState:
    cs = state.get("cell_state")
    if isinstance(cs, dict):
        gs = GridState()
        gs.__dict__.update(cs)
        return gs
    return GridState()


def transition_commission(state: dict[str, Any]) -> dict[str, Any]:
    """Run the microgrid acceptance test (raises if use is non-civilian, N1)."""
    cs = _state(state)
    cs.use = state.get("use", cs.use)
    cs.load_step_kw = float(state.get("load_step_kw", cs.load_step_kw))
    result = commission_microgrid(load_step_kw=cs.load_step_kw, use=cs.use)
    cs.freq_restored = result.freq_restored
    cs.rocof_tripped = result.rocof_tripped
    cs.payload["commissioning"] = to_datoms(result, cs.microgrid_id)
    cs.phase = GridPhase.COMMISSIONED.value
    return {"cell_state": cs.__dict__, "next_node": "commit_dispatch"}


def transition_commit_dispatch(state: dict[str, Any]) -> dict[str, Any]:
    """G7/G15 member-signed dispatch + G8 witness quorum; always dry-run at R0."""
    cs = _state(state)
    cs.member_sig = state.get("member_sig", cs.member_sig)
    cs.server_sig = state.get("server_sig", cs.server_sig)
    cs.witness_sigs = state.get("witness_sigs", cs.witness_sigs)

    require_member_signature(cs.member_sig, cs.server_sig)  # raises on violation
    quorum = witness_quorum_ok(cs.witness_sigs)
    if not cs.freq_restored:
        raise ValueError("acceptance test failed: frequency not restored; cannot commission")

    cs.payload["dispatch"] = {
        "microgridId": cs.microgrid_id,
        "use": cs.use,
        "freqRestored": cs.freq_restored,
        "rocofTripped": cs.rocof_tripped,
        "memberSig": cs.member_sig,
        "witnessOk": quorum["ok"],
        "escalateCouncilLv6": quorum.get("escalate_council_lv6", False),
        "serverHeldKey": False,  # G15 structural invariant
        "dryRun": True,          # G10: R0 offline only
    }
    cs.phase = GridPhase.DISPATCH_COMMITTED.value
    return {"cell_state": cs.__dict__, "next_node": "end"}
