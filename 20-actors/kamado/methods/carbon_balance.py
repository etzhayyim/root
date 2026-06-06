#!/usr/bin/env python3
"""kamado 竈 — net-atmospheric-carbon balance for a refining pathway.

ADR-2606051500 · the EMPIRICAL answer to two questions:

  (1) Is petroleum refining actually a multi-generational harm?
  (2) Can robotics / process-control make it harmless?

The model is a per-tonne-of-finished-hydrocarbon carbon ledger over the carbon's
WHOLE life — origin → process → fate — because the harm lives in the carbon atoms,
not in the unit operations. For 1 t of finished hydrocarbon product:

    net_delta = origin_credit + process_emissions + fate_release      [tCO2e / t]

  origin_credit  — where the carbon came from (the stock→flow question):
      :fossil-virgin-crude   →  0      (carbon was in GEOLOGICAL storage; releasing it
                                        is a one-way stock→flow transfer that does not
                                        reverse on human timescales — THE multi-gen harm.
                                        NOTE: NOT a representable kamado feedstock — see
                                        feedstock_guard.py / G1. Modelled here only as the
                                        avoided baseline.)
      :biogenic              → -C_PROD  (a plant/alga fixed atmospheric CO2 to make it)
      :captured-co2          → -C_PROD  (DAC / point-source atmospheric capture)
      :recycled-carbon       → -C_PROD * RECYCLE_CREDIT (waste C kept out of a burn)
  process_emissions — refining + synthesis energy. hikari-renewable ≈ 0; fossil-powered
                      adds the refinery's own scope-1/2 burn. THIS is the only slice
                      robotics/control actually moves.
  fate_release   — combusted transport fuel releases the carbon (+C_PROD); a durable
                   material locks it (0, but G12 end-of-life route required).

The headline finding falls straight out of the arithmetic: a fossil→combusted pathway is
~+3.5 tCO2e/t, of which the process slice that automation can touch is ~0.4 (~11%). You
cannot robotics your way to net≤0 — the +C_PROD fate and the 0 fossil origin are in the
carbon, not the plant. The ONLY pathway to D3 (net atmospheric Δ ≤ 0) is to change the
feedstock to closed-loop carbon. That is kamado's entire thesis, and it is just a sum.

stdlib only. Usage:
    python3 carbon_balance.py            # print the pathway ledger table
"""
from __future__ import annotations

import sys
from dataclasses import dataclass

# ── physical constants (well-established, public) ────────────────────────────
# A finished liquid hydrocarbon fuel is ~85% carbon by mass; full combustion of
# 1 t therefore releases ~3.1 tCO2 (gasoline ≈3.10, diesel ≈3.17, jet ≈3.15).
C_PROD = 3.10  # tCO2 worth of carbon embodied in 1 t of finished hydrocarbon

# Process scope-1/2 burn per tonne of product, by energy source.
PROCESS = {
    ":fossil-powered": 0.40,   # refinery burns its own fuel gas + grid fossil power
    ":grid-mixed": 0.22,
    ":hikari-renewable": 0.04,  # PV/wind/green-H2 process heat (ADR-2605261100)
}
# Robotics/advanced-process-control trims the process slice (tighter combustion, less
# flaring, fewer upsets) — a real but BOUNDED reduction. It never touches origin/fate.
APC_PROCESS_REDUCTION = 0.30  # ≤30% of the process slice, optimistic

RECYCLE_CREDIT = 0.85  # recycled-carbon origin credit (waste C diverted from a burn)

# D3 tolerance: a pathway is "closed-loop / charter-passing" iff net ≤ this small band.
D3_TOLERANCE = 0.15  # tCO2e/t — allows residual non-CO2 / measurement slack


@dataclass(frozen=True)
class Pathway:
    name: str
    feedstock: str       # :fossil-virgin-crude | :biogenic | :captured-co2 | :recycled-carbon
    energy: str          # key into PROCESS
    fate: str            # :combusted-fuel | :durable-material
    apc: bool = False     # robotics / advanced process control applied
    representable: bool = True  # False = NOT a kamado-buildable feedstock (G1)


def origin_credit(feedstock: str) -> float:
    if feedstock == ":fossil-virgin-crude":
        return 0.0                       # carbon out of geological storage → no credit
    if feedstock in (":biogenic", ":captured-co2"):
        return -C_PROD                   # carbon drawn from the atmosphere
    if feedstock == ":recycled-carbon":
        return -C_PROD * RECYCLE_CREDIT
    raise ValueError(f"unknown feedstock class {feedstock!r}")


def process_emissions(energy: str, apc: bool) -> float:
    base = PROCESS[energy]
    return base * (1 - APC_PROCESS_REDUCTION) if apc else base


def fate_release(fate: str) -> float:
    if fate == ":combusted-fuel":
        return C_PROD                    # the carbon is returned to the atmosphere
    if fate == ":durable-material":
        return 0.0                       # locked (G12: end-of-life route required)
    raise ValueError(f"unknown fate {fate!r}")


def balance(p: Pathway) -> dict:
    o = origin_credit(p.feedstock)
    pr = process_emissions(p.energy, p.apc)
    f = fate_release(p.fate)
    net = o + pr + f
    return {
        "origin": round(o, 3),
        "process": round(pr, 3),
        "fate": round(f, 3),
        "net": round(net, 3),
        "passes_d3": net <= D3_TOLERANCE,
    }


# ── the pathway set: a fossil BASELINE (avoided, not buildable) + the buildable set ──
PATHWAYS = [
    Pathway("fossil diesel, fossil-powered (BASELINE — NOT buildable, G1)",
            ":fossil-virgin-crude", ":fossil-powered", ":combusted-fuel",
            apc=False, representable=False),
    Pathway("fossil diesel + full robotic APC (still NOT buildable — shows APC limit)",
            ":fossil-virgin-crude", ":fossil-powered", ":combusted-fuel",
            apc=True, representable=False),
    Pathway("biogenic alkane diesel, hikari-powered, combusted",
            ":biogenic", ":hikari-renewable", ":combusted-fuel", apc=True),
    Pathway("captured-CO2 e-fuel (green-H2 FT), combusted",
            ":captured-co2", ":hikari-renewable", ":combusted-fuel", apc=True),
    Pathway("recycled-carbon naphtha, hikari-powered, combusted",
            ":recycled-carbon", ":hikari-renewable", ":combusted-fuel", apc=True),
    Pathway("biogenic naphtha → durable polymer (carbon locked)",
            ":biogenic", ":hikari-renewable", ":durable-material", apc=True),
]


def render() -> str:
    L = []
    P = L.append
    P("# kamado 竈 — net-atmospheric-carbon ledger (tCO2e per tonne product)")
    P("")
    P(f"C_PROD={C_PROD} · D3 tolerance ≤{D3_TOLERANCE} · APC trims ≤{int(APC_PROCESS_REDUCTION*100)}% of process only")
    P("")
    P("| pathway | feedstock | origin | process | fate | NET | D3? | buildable |")
    P("|---|---|---:|---:|---:|---:|:---:|:---:|")
    for p in PATHWAYS:
        b = balance(p)
        P(f"| {p.name} | `{p.feedstock}` | {b['origin']:+.2f} | {b['process']:+.2f} | "
          f"{b['fate']:+.2f} | **{b['net']:+.2f}** | {'✅' if b['passes_d3'] else '❌'} | "
          f"{'yes' if p.representable else '— (G1)'} |")
    P("")
    base = balance(PATHWAYS[0])
    apc = balance(PATHWAYS[1])
    share = (base["net"] - apc["net"]) / base["net"] * 100
    P(f"- fossil baseline NET = **{base['net']:+.2f}** tCO2e/t → strongly positive, "
      f"one-way stock→flow = **genuinely multi-generational**.")
    P(f"- full robotic APC on the SAME fossil pathway only moves it to **{apc['net']:+.2f}** "
      f"— a **{share:.0f}%** cut, all from the process slice; origin+fate (~89%) is untouched.")
    P(f"- → robotics/control makes fossil refining *cleaner*, never *harmless*. The only "
      f"pathways that reach net≤0 are the ones that change the **feedstock** (G1).")
    return "\n".join(L)


def main(argv) -> int:
    print(render())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
