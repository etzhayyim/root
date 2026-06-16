#!/usr/bin/env python3
"""torifune 鳥船 — zero-net-carbon propellant accounting (G2).

ADR-2606162355. Computes the net carbon balance of a mission's propellant load and flags any
disfavored (fossil / toxic-hypergolic) propellant. G2 requires every propellant actually FUELED
into the vehicle to have a measured carbon-balance ≤ 0.

  net = Σ over stages (stage prop-mass-kg × carbon-balance of the propellant that fuels its engine)

Pure stdlib. Usage: python3 carbon_balance.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ascent_sim import load, _engine_for_stage  # noqa: E402

DISFAVORED = {":disfavored-fossil", ":disfavored-hypergolic-toxic"}


def _propellant_for_engine(nodes, edges, engine_id):
    for e in edges:
        if e.get(":en/kind") == ":fuels" and e.get(":en/to") == engine_id:
            return nodes.get(e.get(":en/from"))
    return None


def balance(nodes: dict, edges: list):
    """Per-stage + net carbon balance; G2 pass iff every fueled propellant is net ≤ 0."""
    rows, net, used_disfavored = [], 0.0, []
    for s in (n for n in nodes.values() if n.get(":organism/kind") == ":stage"):
        eng = _engine_for_stage(nodes, edges, s[":organism/id"])
        prop = _propellant_for_engine(nodes, edges, eng[":organism/id"]) if eng else None
        if not prop:
            continue
        cb = float(prop.get(":propellant/carbon-balance", 0.0))
        mass = float(s.get(":stage/prop-mass-kg", 0.0))
        contrib = cb * mass
        net += contrib
        kind = prop.get(":propellant/kind")
        if kind in DISFAVORED:
            used_disfavored.append((s[":organism/id"], kind))
        rows.append({"stage": s[":organism/id"], "prop": prop.get(":organism/label"),
                     "kind": kind, "carbon_per_kg": cb, "mass_kg": mass,
                     "contrib_kgco2e": contrib})
    return {"rows": rows, "net_kgco2e": net, "used_disfavored": used_disfavored,
            "g2_pass": net <= 0.0 and not used_disfavored}


def report_md(nodes, edges, res) -> str:
    L = ["# torifune 鳥船 — propellant carbon balance (G2 zero-net-carbon)\n"]
    L.append("> **G2 — zero-net-carbon propellant only.** Green-H₂ hydrolox / kamado-synthetic "
             "methalox (net≤0); fossil + toxic-hypergolic are DISFAVORED. Carbon is MEASURED, "
             "never assumed (Rider §2(d)).\n")
    L.append("\n| stage | propellant | kind | kgCO₂e/kg | prop mass (kg) | contribution (kgCO₂e) |")
    L.append("|---|---|---|---:|---:|---:|")
    for r in res["rows"]:
        L.append(f"| {r['stage']} | {r['prop']} | {r['kind'].lstrip(':')} | "
                 f"{r['carbon_per_kg']:g} | {r['mass_kg']:.0f} | {r['contrib_kgco2e']:.0f} |")
    L.append(f"\n**Net mission carbon balance: {res['net_kgco2e']:.0f} kgCO₂e** — "
             f"{'✅ G2 PASS (net ≤ 0)' if res['g2_pass'] else '❌ G2 FAIL'}\n")
    if res["used_disfavored"]:
        L.append("\n⚠️ **disfavored propellant fueled:** " +
                 ", ".join(f"{sid} ({k.lstrip(':')})" for sid, k in res["used_disfavored"]) + "\n")
    else:
        L.append("\n_No disfavored propellant fueled into the vehicle._\n")
    L.append("\n---\n_torifune 鳥船 · ADR-2606162355 · zero-net-carbon · measured not assumed._\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-ama-vehicle.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)
    nodes, edges = load(seed)
    res = balance(nodes, edges)
    (outdir / "carbon-report.md").write_text(report_md(nodes, edges, res), encoding="utf-8")
    print(f"torifune carbon: net {res['net_kgco2e']:.0f} kgCO2e "
          f"({'G2 PASS' if res['g2_pass'] else 'G2 FAIL'}) → {outdir/'carbon-report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
