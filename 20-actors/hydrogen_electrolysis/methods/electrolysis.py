from __future__ import annotations

import pathlib
import sys
from typing import Any


def _repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[3]


def _load_kami_sim() -> None:
    src = _repo_root() / "40-engine" / "kami-engine" / "kami-hydrogen-electrolysis-sim" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def run_comparison(active_area_cm2: float = 10_000.0) -> dict[str, Any]:
    _load_kami_sim()
    from kami_hydrogen_electrolysis_sim import rank_by_electrical_energy, simulate_default_cases
    from kami_hydrogen_electrolysis_sim.usd import scene_spec

    results = simulate_default_cases(active_area_cm2)
    low_temperature = [result for result in results if not result.name.startswith("soec")]
    best_low_temperature = rank_by_electrical_energy(low_temperature)[0]
    best_electrical = rank_by_electrical_energy(results)[0]
    return {
        "actor": "hydrogen_electrolysis",
        "engine": "kami-hydrogen-electrolysis-sim",
        "active_area_cm2": active_area_cm2,
        "best_low_temperature": best_low_temperature.to_dict(),
        "best_electrical": best_electrical.to_dict(),
        "results": [result.to_dict() for result in rank_by_electrical_energy(results)],
        "scene": scene_spec(results),
    }


def kotoba_datoms(comparison: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in comparison["results"]:
        entity = f"hydrogen-electrolysis/{result['name']}"
        rows.append(
            {
                ":db/id": entity,
                ":hydrogen.electrolysis/name": result["name"],
                ":hydrogen.electrolysis/actor": comparison["actor"],
                ":hydrogen.electrolysis/engine": comparison["engine"],
                ":hydrogen.electrolysis/electrical-kwh-per-kg-h2": round(result["electrical_kwh_per_kg"], 4),
                ":hydrogen.electrolysis/total-with-heat-kwh-per-kg-h2": round(result["total_with_heat_kwh_per_kg"], 4),
                ":hydrogen.electrolysis/hhv-electrical-efficiency-pct": round(result["hhv_electrical_efficiency_pct"], 3),
                ":hydrogen.electrolysis/hhv-total-efficiency-pct": round(result["hhv_total_efficiency_pct"], 3),
                ":hydrogen.electrolysis/h2-kg-per-hour": round(result["h2_kg_per_hour"], 6),
                ":hydrogen.electrolysis/output-pressure-bar": result["output_pressure_bar"],
            }
        )
    rows.append(
        {
            ":db/id": "hydrogen-electrolysis/recommendation/low-temperature",
            ":hydrogen.electrolysis/recommended-case": comparison["best_low_temperature"]["name"],
            ":hydrogen.electrolysis/rationale": "capillary-feed + zero-gap AEM + high-pressure minimizes bubble, ohmic, and compression losses",
        }
    )
    return rows


def render_report(comparison: dict[str, Any]) -> str:
    lines = [
        "# hydrogen_electrolysis — efficiency comparison",
        "",
        f"- actor: `{comparison['actor']}`",
        f"- simulation engine: `{comparison['engine']}`",
        f"- active area: `{comparison['active_area_cm2']:.0f} cm^2`",
        f"- best low-temperature candidate: `{comparison['best_low_temperature']['name']}`",
        f"- lowest electrical energy candidate: `{comparison['best_electrical']['name']}`",
        "",
        "| case | cell V | electrical kWh/kg-H2 | heat-inclusive kWh/kg-H2 | HHV electrical % | H2 kg/h | pressure bar |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for result in comparison["results"]:
        lines.append(
            "| {name} | {cell_voltage_v:.3f} | {electrical_kwh_per_kg:.2f} | "
            "{total_with_heat_kwh_per_kg:.2f} | {hhv_electrical_efficiency_pct:.1f} | "
            "{h2_kg_per_hour:.3f} | {output_pressure_bar:.0f} |".format(**result)
        )
    lines.extend(
        [
            "",
            "Interpretation: SOEC can minimize electrical input when useful heat is available. "
            "For low-temperature water electrolysis, the strongest candidate is "
            "`cfe-zero-gap-aem-high-pressure` because it combines capillary bubble suppression, "
            "short ion path, AEM stack economics, and reduced downstream compression.",
        ]
    )
    return "\n".join(lines) + "\n"
