#!/usr/bin/env python3
"""torifune 鳥船 — kotoba Datom-log emitter (canonical EAVT state, ADR-2605312345).

Projects the launch-vehicle graph into append-only kotoba Datoms [e a v tx op].
  GROUND (durable, op :add) — node + 縁 datoms. This IS the Datom log.
  DERIVED (transient, :bond/is-transient true) — Δv margin, carbon balance, deorbit debt;
    computed on READ, NOT persisted (N1).

G1: no strike-trajectory / munition-payload attribute is emitted (none exists; check_g1 runs).

Pure stdlib. Usage: python3 datom_emit.py [seed.edn] [--out OUTDIR] [--tx N]
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from ascent_sim import load, simulate, check_g1  # noqa: E402,F401
from carbon_balance import balance  # noqa: E402
from disposal_plan import plan  # noqa: E402

NODE_ATTRS = [":organism/kind", ":organism/label", ":organism/sourcing",
              ":vehicle/class", ":vehicle/reusable", ":vehicle/stages",
              ":stage/index", ":stage/dry-mass-kg", ":stage/prop-mass-kg", ":stage/recovery",
              ":engine/cycle", ":engine/isp-s", ":engine/thrust-kn",
              ":propellant/kind", ":propellant/carbon-balance", ":plant-cell/kind",
              ":mission/payload-to-orbit-kg", ":mission/target-regime",
              ":payload/class", ":traj/class", ":disposal/method", ":disposal/deorbit-debt"]
EDGE_ATTRS = [":en/from", ":en/to", ":en/kind", ":en/dv-contribution", ":organism/sourcing"]


def _fmt(v) -> str:
    if v is True:  return "true"
    if v is False: return "false"
    if v is None:  return "nil"
    if isinstance(v, str):
        return v if v.startswith(":") else '"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"'
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def emit(nodes: dict, edges: list, tx: int = 1) -> str:
    check_g1(nodes)
    sim = simulate(nodes, edges)
    carb = balance(nodes, edges)
    disp = plan(nodes, edges)

    L = [";; torifune 鳥船 — GENERATED kotoba Datom log (ADR-2606162355). DO NOT hand-edit.",
         ";; Canonical EAVT state (ADR-2605312345). [e a v tx op].",
         ";; GROUND op :add = durable. DERIVED :bond/is-transient = computed on read (N1).",
         ";; G1: civilian launch only — no strike-trajectory / munition-payload attribute exists.",
         "["]
    for nid, n in nodes.items():
        for a in NODE_ATTRS:
            if a in n and n[a] is not None:
                L.append(f"[{_fmt(nid)} {a} {_fmt(n[a])} {tx} :add]")
    for e in edges:
        eid = f"en.{e[':en/from']}.{e[':en/kind'].lstrip(':')}.{e[':en/to']}"
        for a in EDGE_ATTRS:
            if a in e and e[a] is not None:
                L.append(f"[{_fmt(eid)} {a} {_fmt(e[a])} {tx} :add]")

    L.append(";; ── DERIVED readouts (transient; computed on read) ──")
    L.append(f"[{_fmt('lv.vehicle.ama')} :bond/dv-total-ms {sim['total_dv_ms']:g} {tx} :derived] ;; :bond/is-transient true")
    L.append(f"[{_fmt('lv.vehicle.ama')} :bond/dv-margin-ms {sim['dv_margin_ms']:g} {tx} :derived] ;; :bond/is-transient true")
    L.append(f"[{_fmt('lv.vehicle.ama')} :bond/carbon-balance-kgco2e {carb['net_kgco2e']:g} {tx} :derived] ;; :bond/is-transient true")
    L.append(f"[{_fmt('lv.vehicle.ama')} :bond/deorbit-debt {disp['total_deorbit_debt']:g} {tx} :derived] ;; :bond/is-transient true")
    L.append("]")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-ama-vehicle.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    tx = int(argv[argv.index("--tx") + 1]) if "--tx" in argv else 1
    outdir.mkdir(parents=True, exist_ok=True)
    nodes, edges = load(seed)
    out = outdir / "launch-datoms.kotoba.edn"
    out.write_text(emit(nodes, edges, tx), encoding="utf-8")
    print(f"torifune datom log → {out} ({len(nodes)} nodes + {len(edges)} 縁, tx={tx})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
