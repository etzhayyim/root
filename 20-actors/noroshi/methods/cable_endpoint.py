"""noroshi (烽) ↔ watatsuna (綿津綱) optical-network resilience join (ADR-2606051600 §R1c). Stdlib only.

watatsuna maps the submarine-cable **medium** (systems, landing stations, the chokepoints they sit
behind); noroshi designs the **CPO transceiver chips at the cable's ends**. This joins the two into
**one optical-network resilience picture**: every in-service cable terminates on a CPO transceiver at
each landing station, so the per-cable design capacity becomes a concrete count of noroshi
photonic-IC lanes — and that transceiver demand **concentrates behind the same maritime chokepoints**
watatsuna already ranks. The lens is **resilience** (where transceiver capacity piles up behind a
single chokepoint → diversify routes + pre-stage redundant endpoints), inheriting watatsuna's
constitutional framing: a resilience map, **NEVER a target-list** (watatsumi N8 + Charter Rider §2(d)).

Reads the watatsuna seed (`:cable/* :station/* :cable.link/*`) and sizes the CPO transceiver fleet
per cable, per station, and per chokepoint, using the noroshi CPO reference link (line rate +
energy/bit from `link_budget.py`). Deterministic; no live data, no hardware (G8/G10).
"""

from __future__ import annotations

import math
import pathlib
from dataclasses import dataclass

from _edn import load_edn
from link_budget import CPO_REFERENCE, compute

# Default: the watatsuna submarine-cable seed (sibling actor; resilience composition).
_WATATSUNA_SEED = (
    pathlib.Path(__file__).resolve().parents[2]
    / "watatsuna" / "data" / "seed-cable-graph.kotoba.edn"
)


@dataclass(frozen=True)
class CableEndpoints:
    cable_id: str
    name: str
    design_capacity_tbps: float
    stations: list           # station ids this cable lands on
    lanes_per_endpoint: int  # noroshi CPO lanes to serve the design capacity at one end
    energy_kw: float         # transceiver electrical power at one endpoint (kW)


def _lanes_for(capacity_tbps: float, line_rate_gbps: float) -> int:
    """CPO transceiver lanes needed to carry a cable's design capacity at one landing."""
    return max(1, math.ceil(capacity_tbps * 1000.0 / line_rate_gbps))


def load_graph(seed: pathlib.Path | None = None) -> dict:
    seed = seed or _WATATSUNA_SEED
    if not pathlib.Path(seed).exists():
        raise FileNotFoundError(
            f"watatsuna cable seed not found at {seed}; the noroshi×watatsuna join needs the "
            "sibling actor's seed (20-actors/watatsuna/data/seed-cable-graph.kotoba.edn)"
        )
    rows = load_edn(seed)
    cables, stations, links, segments = {}, {}, [], []
    for r in rows:
        if not isinstance(r, dict):
            continue
        if ":cable/id" in r:
            cables[r[":cable/id"]] = r
        elif ":station/id" in r:
            stations[r[":station/id"]] = r
        elif ":cable.link/id" in r:
            links.append(r)
        elif ":cable.seg/id" in r:
            segments.append(r)
    return {"cables": cables, "stations": stations, "links": links, "segments": segments}


def size_fleet(seed: pathlib.Path | None = None) -> dict:
    """Size the CPO transceiver fleet per cable / station / chokepoint from the watatsuna graph."""
    g = load_graph(seed)
    budget = compute(CPO_REFERENCE)
    line_rate = CPO_REFERENCE.line_rate_gbps
    # energy at one endpoint = energy/bit × design capacity (W = pJ/bit × Tb/s = J/s).
    per_cable: list[CableEndpoints] = []
    by_station_lanes: dict[str, int] = {}
    by_chokepoint: dict[str, dict] = {}        # station-tag attribution (landing-behind)
    by_chokepoint_seg: dict[str, dict] = {}    # segment attribution (authoritative physical crossing)

    incidence: dict[str, list[str]] = {}
    for lk in g["links"]:
        incidence.setdefault(lk[":cable.link/cable"], []).append(lk[":cable.link/station"])

    # Authoritative per-cable chokepoint crossings from :cable.seg/traverses.
    seg_crossings: dict[str, set] = {}
    for sg in g.get("segments", []):
        cid = sg.get(":cable.seg/cable")
        for cp in sg.get(":cable.seg/traverses", []) or []:
            seg_crossings.setdefault(cid, set()).add(cp)

    for cid, c in g["cables"].items():
        if c.get(":cable/status") not in (":in-service", None):
            continue
        cap = float(c.get(":cable/design-capacity-tbps", 0.0))
        stns = incidence.get(cid, [])
        lanes = _lanes_for(cap, line_rate)
        energy_kw = budget.energy_pj_per_bit * cap / 1e3  # pJ/bit × Tb/s = W; ÷1e3 → kW
        per_cable.append(CableEndpoints(cid, c.get(":cable/name", cid), cap, stns, lanes, round(energy_kw, 2)))
        for s in stns:
            by_station_lanes[s] = by_station_lanes.get(s, 0) + lanes
            for cp in g["stations"].get(s, {}).get(":station/chokepoint", []) or []:
                agg = by_chokepoint.setdefault(cp, {"lanes": 0, "cables": set(), "capacity_tbps": 0.0})
                agg["lanes"] += lanes
                agg["cables"].add(cid)
                agg["capacity_tbps"] += cap
        for cp in seg_crossings.get(cid, set()):    # authoritative crossing attribution
            agg = by_chokepoint_seg.setdefault(cp, {"lanes": 0, "cables": set(), "capacity_tbps": 0.0})
            agg["lanes"] += lanes
            agg["cables"].add(cid)
            agg["capacity_tbps"] += cap

    def _rank(d):
        return sorted(
            ({"chokepoint": k, "lanes": v["lanes"], "cables": len(v["cables"]),
              "capacity_tbps": round(v["capacity_tbps"], 1)} for k, v in d.items()),
            key=lambda x: x["lanes"], reverse=True,
        )

    return {
        "per_cable": per_cable,
        "by_station_lanes": by_station_lanes,
        "chokepoints": _rank(by_chokepoint),                 # landing-behind (station tags)
        "chokepoints_via_segments": _rank(by_chokepoint_seg),  # authoritative physical crossing
        "lane_rate_gbps": line_rate,
        "energy_pj_per_bit": budget.energy_pj_per_bit,
    }


def report(seed: pathlib.Path | None = None) -> str:
    f = size_fleet(seed)
    lines = [
        "# noroshi 烽 × watatsuna 綿津綱 — optical-network resilience (CPO transceivers at the cable ends)",
        "",
        f"Each in-service cable terminates on noroshi CPO transceivers ({f['lane_rate_gbps']:.2f} Gb/s/lane, "
        f"{f['energy_pj_per_bit']} pJ/bit). Demand sized from the watatsuna seed.",
        "",
        "## CPO transceiver demand behind each maritime chokepoint (resilience, NOT a target-list)",
        "| chokepoint | CPO lanes (per end) | cables | aggregate capacity (Tb/s) |",
        "|---|---|---|---|",
    ]
    for cp in f["chokepoints"]:
        lines.append(f"| {cp['chokepoint']} | {cp['lanes']} | {cp['cables']} | {cp['capacity_tbps']} |")
    lines += [
        "",
        "## same demand by AUTHORITATIVE segment crossing (:cable.seg/traverses — physical, not landing-tag)",
        "| chokepoint | CPO lanes (per end) | cables | aggregate capacity (Tb/s) |",
        "|---|---|---|---|",
    ]
    for cp in f["chokepoints_via_segments"]:
        lines.append(f"| {cp['chokepoint']} | {cp['lanes']} | {cp['cables']} | {cp['capacity_tbps']} |")
    lines += ["", "## per-cable endpoint transceiver sizing", "| cable | capacity (Tb/s) | landings | CPO lanes/end | endpoint power (kW) |", "|---|---|---|---|---|"]
    for c in sorted(f["per_cable"], key=lambda x: x.lanes_per_endpoint, reverse=True):
        lines.append(f"| {c.name} | {c.design_capacity_tbps} | {len(c.stations)} | {c.lanes_per_endpoint} | {c.energy_kw} |")
    lines += [
        "",
        "> **Composition**: watatsuna ranks where cable *capacity* concentrates behind a chokepoint; "
        "noroshi turns that into the *transceiver* fleet that must be built and diversified there. "
        "The output routes to **redundant endpoints + diverse routes + faster repair**, never "
        "interdiction (watatsuna G2 / watatsumi N8). R0: sizing arithmetic over the `:representative` "
        "watatsuna seed + the noroshi CPO reference; no live deployment (G8).",
    ]
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover — offline demo
    print(report())
