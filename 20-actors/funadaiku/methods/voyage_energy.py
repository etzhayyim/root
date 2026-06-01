#!/usr/bin/env python3
"""funadaiku 船大工 — Nagi 凪 class voyage energy-budget simulation.

ADR-2606013400. Stdlib-only reduced-order analytic model of the zero-emission
powertrain over a representative coastal voyage. Computes how much of the voyage
propulsion + hotel energy is met by each source — wind-assist, solar, hydrogen
fuel-cell (with battery buffering peaks) — and the resulting green-H2 demand.

HONEST: this is a transparent first-order model (Admiralty propulsion-power law +
flat-rate solar capacity factor + average wind-assist saving fraction), NOT CFD or
sea-keeping. It exists to make the wind/solar/hydrogen split EMPIRICAL rather than
asserted. Numbers are :representative. The 6-DOF dynamics live in kami-autodrive
ShipHydro (ADR-2606010600); marine CFD is deferred (R2+).

Run:  python methods/voyage_energy.py   ->  writes out/voyage-energy-report.md
"""

from __future__ import annotations

import os
from dataclasses import dataclass

# ── reference vessel (mirrors data/vessel.edn, Nagi 凪 class) ──────────────────

@dataclass(frozen=True)
class Vessel:
    name: str = "Nagi 凪 (coastal cargo)"
    dwt: int = 3000
    displacement_t: float = 4500.0          # full-load displacement ~ 1.5x DWT (small cargo)
    admiralty_coeff: float = 450.0          # Δ^(2/3)·V^3 / P_shaft ; typical small cargo
    service_speed_kn: float = 10.0
    hotel_load_kw: float = 120.0            # auxiliary / hotel / control load
    # powertrain installed capacities
    solar_kwp: float = 160.0
    fuelcell_kw: float = 2400.0
    battery_kwh: float = 2000.0
    rotor_sails: int = 2


@dataclass(frozen=True)
class Voyage:
    name: str = "representative coastal short-sea leg"
    distance_nm: float = 200.0
    # environment / route assumptions (:representative)
    solar_capacity_factor: float = 0.13     # marine daytime-averaged annual CF
    wind_assist_saving_frac: float = 0.18    # avg propulsion-power saved by 2 rotor sails
    #   (rotor sails on suitable routes save ~10-30%; 18% = conservative mid)
    propulsive_efficiency: float = 0.62      # hull+pod quasi-propulsive coefficient
    fuelcell_lhv_eff: float = 0.52           # PEM FC electrical efficiency (LHV)


H2_LHV_KWH_PER_KG = 33.33  # lower-heating-value energy density of hydrogen


def shaft_power_kw(v: Vessel) -> float:
    """Admiralty-coefficient propulsion power at service speed (calm water)."""
    disp23 = v.displacement_t ** (2.0 / 3.0)
    return disp23 * (v.service_speed_kn ** 3) / v.admiralty_coeff


def simulate(v: Vessel, voy: Voyage) -> dict:
    hours = voy.distance_nm / v.service_speed_kn

    # propulsion demand at the bus (account for propulsive efficiency of pod+hull)
    p_shaft = shaft_power_kw(v)
    p_prop_bus = p_shaft / voy.propulsive_efficiency
    prop_energy_kwh = p_prop_bus * hours
    hotel_energy_kwh = v.hotel_load_kw * hours
    total_demand_kwh = prop_energy_kwh + hotel_energy_kwh

    # ── wind-assist: reduces propulsion demand directly ──
    wind_kwh = prop_energy_kwh * voy.wind_assist_saving_frac

    # ── solar: average power = peak * capacity factor, over voyage hours ──
    solar_avg_kw = v.solar_kwp * voy.solar_capacity_factor
    solar_kwh = min(solar_avg_kw * hours, hotel_energy_kwh + prop_energy_kwh * 0.10)
    #   cap solar so it serves hotel + a little propulsion (it is NOT a main mover)

    # ── hydrogen fuel cell: supplies the residual; battery only shifts peaks ──
    residual_kwh = max(0.0, total_demand_kwh - wind_kwh - solar_kwh)
    h2_kg = residual_kwh / (H2_LHV_KWH_PER_KG * voy.fuelcell_lhv_eff)

    shares = {
        "wind_assist": wind_kwh / total_demand_kwh,
        "solar": solar_kwh / total_demand_kwh,
        "hydrogen_fuelcell": residual_kwh / total_demand_kwh,
    }

    # battery sanity: can it cover a peak-shave window (e.g. 30 min harbour manoeuvre)?
    harbour_manoeuvre_kw = p_prop_bus * 0.6 + v.hotel_load_kw
    battery_minutes = v.battery_kwh / harbour_manoeuvre_kw * 60.0

    return {
        "hours": hours,
        "p_shaft_kw": p_shaft,
        "p_prop_bus_kw": p_prop_bus,
        "prop_energy_kwh": prop_energy_kwh,
        "hotel_energy_kwh": hotel_energy_kwh,
        "total_demand_kwh": total_demand_kwh,
        "wind_kwh": wind_kwh,
        "solar_kwh": solar_kwh,
        "residual_kwh": residual_kwh,
        "h2_kg": h2_kg,
        "shares": shares,
        "battery_harbour_minutes": battery_minutes,
        "fossil_engine": False,
    }


def report(v: Vessel, voy: Voyage, r: dict) -> str:
    s = r["shares"]
    pct = lambda x: f"{x*100:.1f}%"
    md = f"""# funadaiku 船大工 — Nagi 凪 voyage energy budget

> ADR-2606013400 · reduced-order analytic model (`methods/voyage_energy.py`) · :representative
> **No fossil engine** (G13/N5). Hydrogen must be green (G14, well-to-wake).

## Inputs

| Vessel ({v.name}) | | Voyage ({voy.name}) | |
|---|---|---|---|
| DWT | {v.dwt} | Distance | {voy.distance_nm:.0f} nm |
| Displacement | {v.displacement_t:.0f} t | Service speed | {v.service_speed_kn:.0f} kn |
| Solar | {v.solar_kwp:.0f} kWp | Voyage time | {r['hours']:.1f} h |
| Fuel cell | {v.fuelcell_kw:.0f} kW | Solar capacity factor | {pct(voy.solar_capacity_factor)} |
| Battery | {v.battery_kwh:.0f} kWh | Wind-assist saving | {pct(voy.wind_assist_saving_frac)} |
| Rotor sails | {v.rotor_sails} | FC efficiency (LHV) | {pct(voy.fuelcell_lhv_eff)} |

## Result

- Propulsion shaft power @ {v.service_speed_kn:.0f} kn: **{r['p_shaft_kw']:.0f} kW** (Admiralty law, calm water)
- Bus propulsion power (÷ QPC {voy.propulsive_efficiency}): **{r['p_prop_bus_kw']:.0f} kW**
- Voyage energy demand (propulsion + hotel): **{r['total_demand_kwh']:.0f} kWh**

### Energy met by source

| Source | Energy (kWh) | Share | Role |
|---|---:|---:|---|
| Wind-assist (2× rotor sail) | {r['wind_kwh']:.0f} | **{pct(s['wind_assist'])}** | primary fuel-saver |
| Solar deck | {r['solar_kwh']:.0f} | **{pct(s['solar'])}** | hotel + top-up |
| Hydrogen fuel cell (residual) | {r['residual_kwh']:.0f} | **{pct(s['hydrogen_fuelcell'])}** | electrical prime mover |
| **Fossil engine** | 0 | **0.0%** | none (G13) |

- **Green hydrogen demand for this leg: {r['h2_kg']:.0f} kg** (LHV {H2_LHV_KWH_PER_KG} kWh/kg ÷ FC {pct(voy.fuelcell_lhv_eff)})
- Battery covers a harbour manoeuvre (~60% prop + hotel) for **{r['battery_harbour_minutes']:.0f} min** → zero-emission at berth/port.

## Honest reading

Wind + solar together meet **{pct(s['wind_assist'] + s['solar'])}** of this representative
coastal leg; hydrogen carries the remaining **{pct(s['hydrogen_fuelcell'])}** as the prime mover —
exactly the survey conclusion that **no single source is a complete prime mover** at cargo
scale. Wind-assist share rises on windier/longer routes and falls on calm ones; solar is
capped to hotel + a little propulsion by construction (low areal power). Tank-to-wake CO₂ is
**zero**; the well-to-wake figure depends entirely on the **green-H₂ chain-of-custody** (G14) —
hydrogen made from fossil power would erase the benefit. This is a first-order model, not CFD.
"""
    return md


def to_edn(v: Vessel, voy: Voyage, r: dict) -> str:
    s = r["shares"]
    return f""";; funadaiku Nagi 凪 — voyage energy-budget result (kotoba EAVT)
;; ADR-2606013400 · generated by methods/voyage_energy.py · :representative
[{{:voyage/id "funadaiku.nagi.voyage-rep-200nm" :voyage/vessel "funadaiku.nagi-0001"
  :voyage/distance-nm {voy.distance_nm:.0f} :voyage/hours {r['hours']:.2f}
  :voyage/total-demand-kwh {r['total_demand_kwh']:.0f}
  :voyage/share-wind {s['wind_assist']:.4f} :voyage/share-solar {s['solar']:.4f}
  :voyage/share-hydrogen {s['hydrogen_fuelcell']:.4f} :voyage/fossil-engine false
  :voyage/green-h2-kg {r['h2_kg']:.0f} :voyage/battery-harbour-min {r['battery_harbour_minutes']:.0f}
  :voyage/sourcing :representative}}]
"""


def main() -> None:
    v, voy = Vessel(), Voyage()
    r = simulate(v, voy)
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(here, "out")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "voyage-energy-report.md"), "w") as f:
        f.write(report(v, voy, r))
    with open(os.path.join(out, "voyage-energy.kotoba.edn"), "w") as f:
        f.write(to_edn(v, voy, r))
    sh = r["shares"]
    print(f"Nagi 凪 voyage {voy.distance_nm:.0f} nm @ {v.service_speed_kn:.0f} kn  "
          f"({r['hours']:.1f} h, {r['total_demand_kwh']:.0f} kWh)")
    print(f"  wind-assist {sh['wind_assist']*100:5.1f}% | "
          f"solar {sh['solar']*100:5.1f}% | "
          f"hydrogen {sh['hydrogen_fuelcell']*100:5.1f}% | fossil 0.0%")
    print(f"  green-H2 demand: {r['h2_kg']:.0f} kg   battery harbour: {r['battery_harbour_minutes']:.0f} min")
    print(f"  wrote out/voyage-energy-report.md + out/voyage-energy.kotoba.edn")


if __name__ == "__main__":
    main()
