"""suji (筋) — end-to-end: laptop posture → bones load → muscle tension → 強張り. Stdlib.

Ties the chain together and answers the actual question: what does a laptop posture do
to the body? It runs the full pipeline for each reference workstation

    workstation → posture (kinematics) → joint loads (static inverse dynamics)
                → muscle tensions (%MVC) → stiffness map (Rohmert session dose)

and reports the comparison (laptop-on-lap vs laptop-on-desk vs external-monitor-at-
eye-level). The comparison is SELF-REFERENCED (G3): the same body across postures, the
Wellbecoming choice "raise the screen / support the arms" — never a ranking of people,
never a diagnosis (G1). Run: `python3 analyze.py` (writes out/posture-report.md).
"""

from __future__ import annotations

from dataclasses import dataclass

from load import PostureLoads, solve_posture_loads
from muscle import MuscleTension, solve_muscle_tensions
from posture import REFERENCE_WORKSTATIONS, Posture, Workstation, posture_from_workstation
from segment import BodyModel, build_body
from strain import MuscleStrain, session_strain, stiffness_band


@dataclass(frozen=True)
class ScenarioResult:
    workstation: str
    posture: Posture
    loads: PostureLoads
    tensions: list[MuscleTension]
    strains: list[MuscleStrain]

    @property
    def worst_stiffness(self) -> MuscleStrain:
        return max(self.strains, key=lambda s: s.stiffness_index)


def analyze_workstation(body: BodyModel, ws: Workstation, session_minutes: float = 120.0) -> ScenarioResult:
    posture = posture_from_workstation(ws)
    loads = solve_posture_loads(body, posture)
    tensions = solve_muscle_tensions(body, posture, loads)
    strains = session_strain(tensions, session_minutes)
    return ScenarioResult(ws.name, posture, loads, tensions, strains)


def analyze_all(total_mass_kg: float = 70.0, stature_m: float = 1.70,
                session_minutes: float = 120.0) -> list[ScenarioResult]:
    body = build_body(total_mass_kg, stature_m)
    return [analyze_workstation(body, ws, session_minutes) for ws in REFERENCE_WORKSTATIONS]


def render_report(results: list[ScenarioResult], session_minutes: float = 120.0) -> str:
    L: list[str] = []
    L.append("# suji 筋 — laptop posture biomechanics report")
    L.append("")
    L.append("> NON-DIAGNOSTIC (G1, 医師法 §17): physical loads only — moments, forces, "
             "%MVC, a normalised stiffness dose. NOT a diagnosis or treatment. "
             "`:representative` adult; cervical leg validated vs Hansraj 2014.")
    L.append(f"> Session held: {session_minutes:.0f} min continuous.")
    L.append("")
    # Cervical (tech-neck) headline table
    L.append("## Cervical spine load (forward head / tech-neck)")
    L.append("")
    L.append("| workstation | head flexion | neck load | ×head-weight |")
    L.append("|---|---|---|---|")
    for r in results:
        c = r.loads.cervical
        L.append(f"| {r.workstation} | {c.head_flexion_deg:.0f}° | "
                 f"{c.compressive_load_kgf:.1f} kgf | {c.multiplier_vs_head:.1f}× |")
    L.append("")
    # Per-scenario stiffness map
    for r in results:
        L.append(f"## {r.workstation}")
        L.append("")
        p = r.posture
        L.append(f"- posture: head {p.head_flexion_deg:.0f}° · trunk {p.trunk_flexion_deg:.0f}° "
                 f"· shoulder {p.shoulder_flexion_deg:.0f}° · arms "
                 f"{'supported' if p.arms_supported else 'UNSUPPORTED'}")
        L.append("")
        L.append("| muscle | tension %MVC | endurance | stiffness (強張り) | band |")
        L.append("|---|---|---|---|---|")
        for s in sorted(r.strains, key=lambda s: -s.stiffness_index):
            end = "∞" if s.endurance_minutes == float("inf") else f"{s.endurance_minutes:.0f} min"
            L.append(f"| {s.name} | {s.mvc_pct:.0f}% | {end} | "
                     f"{s.stiffness_index:.2f} | {stiffness_band(s.stiffness_index)} |")
        w = r.worst_stiffness
        L.append("")
        L.append(f"- worst: **{w.name}** stiffness {w.stiffness_index:.2f} "
                 f"({stiffness_band(w.stiffness_index)})")
        L.append("")
    # Comparison / Wellbecoming guidance
    base = next(r for r in results if r.workstation == "laptop-on-lap")
    best = min(results, key=lambda r: r.worst_stiffness.stiffness_index)
    L.append("## Comparison (self-referenced Wellbecoming, G3)")
    L.append("")
    bc = base.loads.cervical.compressive_load_kgf
    fc = best.loads.cervical.compressive_load_kgf
    L.append(f"- `{base.workstation}` neck load {bc:.1f} kgf → "
             f"`{best.workstation}` {fc:.1f} kgf "
             f"(**−{(1 - fc / bc) * 100:.0f}%** cervical compressive load).")
    bw = base.worst_stiffness
    bestw = best.worst_stiffness
    L.append(f"- worst-muscle stiffness {bw.stiffness_index:.2f} ({bw.name}) → "
             f"{bestw.stiffness_index:.2f} ({bestw.name}).")
    L.append("- mechanism, not advice: raising the screen toward eye level reduces head "
             "flexion (the dominant cervical-load term); supporting the forearms unloads "
             "the upper trapezius (the 肩こり muscle). A clinician (mitate/iyashi) owns any "
             "health interpretation.")
    L.append("")
    return "\n".join(L)


def main() -> None:
    import os
    session = 120.0
    results = analyze_all(session_minutes=session)
    report = render_report(results, session)
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "posture-report.md")
    with open(path, "w") as fh:
        fh.write(report)
    print(report)
    print(f"\n[wrote {path}]")


if __name__ == "__main__":
    main()
