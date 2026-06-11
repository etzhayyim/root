"""water_supply state machine — supply commissioning + dosing + dispatch (gated).

Pure, deterministic transitions enforcing mizuho gates. The runnable control
loops live in ../../methods/water_supply.py (level/pressure) and
../../methods/chlorination.py (residual dosing); this wires them into a phase
machine that ends at a member-signed, dry-run supply record (G6/G10/G12). cell.py
.solve() stays Council-gated — these transitions are exercised by tests, not live
actuation.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

_METHODS = pathlib.Path(__file__).resolve().parents[2] / "methods"
if str(_METHODS) not in sys.path:
    sys.path.append(str(_METHODS))  # append: must NOT shadow the cells/water_supply package


def _load_method(name: str):
    """Load a methods/<name>.py module under a private alias.

    The method module `water_supply.py` shares a name with this cell's package
    (`cells/water_supply`), so importing it as a top-level `water_supply` would
    shadow the package in sys.modules. Loading it by file path under an aliased
    name (`_method_<name>`) keeps the two namespaces disjoint.
    """
    alias = f"_method_{name}"
    if alias in sys.modules:
        return sys.modules[alias]
    spec = importlib.util.spec_from_file_location(alias, _METHODS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[alias] = mod
    spec.loader.exec_module(mod)
    return mod


_ws = _load_method("water_supply")
_chl = _load_method("chlorination")

commission_water_supply = _ws.commission_water_supply
supply_datoms = _ws.to_datoms
commission_dosing = _chl.commission_dosing
dosing_datoms = _chl.to_datoms

from _substrate import require_member_signature, witness_quorum_ok  # noqa: E402


class SupplyPhase(Enum):
    INIT = "init"
    COMMISSIONED = "commissioned"
    SUPPLY_COMMITTED = "supply_committed"


@dataclass
class SupplyState:
    phase: str = SupplyPhase.INIT.value
    source_id: str = "spring-01"
    use: str = "supply"
    demand_step_lps: float = 20.0
    service_population: int = 200
    dosing_agent: str = "disinfect"
    per_member_consent: bool = False
    level_restored: bool = False
    residual_held: bool = False
    ceiling_respected: bool = False
    member_sig: str = ""
    server_sig: str = ""
    witness_sigs: list[str] = field(default_factory=list)
    payload: dict = field(default_factory=dict)


def _state(state: dict[str, Any]) -> SupplyState:
    cs = state.get("cell_state")
    if isinstance(cs, dict):
        ss = SupplyState()
        ss.__dict__.update(cs)
        return ss
    return SupplyState()


def transition_commission(state: dict[str, Any]) -> dict[str, Any]:
    """Run the supply + dosing acceptance tests (raises on non-civilian use / G3 /
    G6 fluoride-without-consent — all before any actuation modelling)."""
    cs = _state(state)
    cs.use = state.get("use", cs.use)
    cs.demand_step_lps = float(state.get("demand_step_lps", cs.demand_step_lps))
    cs.service_population = int(state.get("service_population", cs.service_population))
    cs.dosing_agent = state.get("dosing_agent", cs.dosing_agent)
    cs.per_member_consent = bool(state.get("per_member_consent", cs.per_member_consent))

    supply = commission_water_supply(
        demand_step_lps=cs.demand_step_lps,
        use=cs.use,
        service_population=cs.service_population,
    )
    dosing = commission_dosing(
        agent=cs.dosing_agent, per_member_consent=cs.per_member_consent
    )
    cs.level_restored = supply.level_restored
    cs.residual_held = dosing.residual_held
    cs.ceiling_respected = dosing.ceiling_respected
    cs.payload["supply"] = supply_datoms(supply, cs.source_id)
    cs.payload["dosing"] = dosing_datoms(dosing, cs.source_id)
    cs.phase = SupplyPhase.COMMISSIONED.value
    return {"cell_state": cs.__dict__, "next_node": "commit_supply"}


def transition_commit_supply(state: dict[str, Any]) -> dict[str, Any]:
    """G7/G12 member-signed supply record + G8 witness quorum; always dry-run at R0."""
    cs = _state(state)
    cs.member_sig = state.get("member_sig", cs.member_sig)
    cs.server_sig = state.get("server_sig", cs.server_sig)
    cs.witness_sigs = state.get("witness_sigs", cs.witness_sigs)

    require_member_signature(cs.member_sig, cs.server_sig)  # raises on violation
    quorum = witness_quorum_ok(cs.witness_sigs)
    if not cs.level_restored:
        raise ValueError("acceptance test failed: service level not restored; cannot commission")
    if not cs.ceiling_respected:
        raise ValueError("acceptance test failed: residual ceiling not respected; cannot commission")
    if not quorum["ok"]:
        raise ValueError(f"witness quorum < 2 (G8): cannot commit supply record ({quorum['reason']})")

    cs.payload["supply_record"] = {
        "sourceId": cs.source_id,
        "use": cs.use,
        "servicePopulation": cs.service_population,
        "levelRestored": cs.level_restored,
        "residualHeld": cs.residual_held,
        "ceilingRespected": cs.ceiling_respected,
        "dosingAgent": cs.dosing_agent,
        "memberSig": cs.member_sig,
        "witnessOk": quorum["ok"],
        "escalateCouncilLv6": quorum.get("escalate_council_lv6", False),
        "serverHeldKey": False,  # no-server-key structural invariant
        "dryRun": True,          # G10: R0 offline only
    }
    cs.phase = SupplyPhase.SUPPLY_COMMITTED.value
    return {"cell_state": cs.__dict__, "next_node": "end"}
