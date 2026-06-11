#!/usr/bin/env python3
"""kaiyaku 解約 — kotoba Datom-log emitter (canonical EAVT state, ADR-2605312345).

Projects the 縁-ledger into append-only kotoba Datoms [e a v tx op]. Two strata:

  GROUND (durable, op :add) — the :svc/* / :member/* nodes and :en/* ties. This IS
    the Datom log (synthetic demo seed at R0; live per-member facts are consent- +
    G7-gated and would live encrypted via com.etzhayyim.encrypted.*).

  DERIVED (transient, :bond/is-transient true) — burden / recommendation / plan-tier
    readouts. Per G2 these are computed on READ and never stored as ground state, so
    a stale "this tie is severable" verdict can never outlive the facts beneath it.

Pure stdlib — runnable inside the kaiyaku kotoba pywasm actor (componentize-py).
Usage:
    python3 datom_emit.py [seed.edn] [--out OUTDIR] [--tx N]
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load, analyze  # noqa: E402
from plan import plans, select_tier  # noqa: E402

NODE_ATTRS = [":svc/label", ":svc/kind", ":svc/category", ":svc/sourcing",
              ":svc/notice-days", ":svc/penalty-jpy",
              ":member/label", ":member/sourcing"]
EDGE_ATTRS = [":en/from", ":en/to", ":en/kind", ":en/monthly-cost-jpy",
              ":en/usage-score", ":en/last-used-days", ":en/first-seen",
              ":en/dep", ":en/sourcing"]


def _fmt(v) -> str:
    if v is True:
        return "true"
    if v is False:
        return "false"
    if v is None:
        return "nil"
    if isinstance(v, str):
        return v if v.startswith(":") else '"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"'
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def emit(nodes: dict, edges: list, res: dict, tx: int = 1) -> str:
    L = []
    L.append(";; kaiyaku 解約 — GENERATED kotoba Datom log (ADR-2606112201). DO NOT hand-edit.")
    L.append(";; Canonical EAVT state (ADR-2605312345). [e a v tx op].")
    L.append(";; GROUND op :add = durable. DERIVED :bond/is-transient = computed on read (G2).")
    L.append("")
    L.append(";; ── GROUND: nodes")
    for nid in sorted(nodes):
        n = nodes[nid]
        for a in NODE_ATTRS:
            if a in n and not isinstance(n[a], dict):
                L.append(f'[{_fmt(nid)} {a} {_fmt(n[a])} {tx} :add]')
        cancel = n.get(":svc/cancel")
        if isinstance(cancel, dict):
            for k in sorted(cancel):
                L.append(f'[{_fmt(nid)} :svc/cancel{k} {_fmt(cancel[k])} {tx} :add]')
    L.append("")
    L.append(";; ── GROUND: 縁 (ties)")
    for i, e in enumerate(edges):
        eid = f'"en:{i:03d}"'
        for a in EDGE_ATTRS:
            if a in e:
                L.append(f'[{eid} {a} {_fmt(e[a])} {tx} :add]')
    L.append("")
    L.append(";; ── DERIVED (transient — burden/recommendation computed on read, G2)")
    for t in res["ties"]:
        eid = _fmt(f"readout:{t['svc']}")
        L.append(f'[{eid} :bond/is-transient true {tx} :add]')
        L.append(f'[{eid} :enkiri/burden {t["burden"]:g} {tx} :add]')
        L.append(f'[{eid} :enkiri/recommendation {t["recommendation"]} {tx} :add]')
        L.append(f'[{eid} :enkiri/plan-tier "{select_tier(nodes[t["svc"]])}" {tx} :add]')
    L.append("")
    L.append(f';; ties={len(res["ties"])} recoverable-jpy-mo={res["recoverable_monthly_jpy"]:g}')
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-en-ledger.kotoba.edn"
    out = here / "out"
    tx = 1
    if "--out" in argv:
        out = pathlib.Path(argv[argv.index("--out") + 1])
    if "--tx" in argv:
        tx = int(argv[argv.index("--tx") + 1])
    nodes, edges = load(seed)
    res = analyze(nodes, edges)
    out.mkdir(parents=True, exist_ok=True)
    text = emit(nodes, edges, res, tx)
    (out / "enkiri-datoms.kotoba.edn").write_text(text, encoding="utf-8")
    print(f"kaiyaku: {text.count(':add')} datoms → {out / 'enkiri-datoms.kotoba.edn'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
