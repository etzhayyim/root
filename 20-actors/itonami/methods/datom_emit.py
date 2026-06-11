#!/usr/bin/env python3
"""itonami 営み — kotoba Datom-log emitter (canonical EAVT state, ADR-2605312345).

Projects factory-operations observations into append-only kotoba Datoms [e a v tx op].

  GROUND (durable, op :add) — :station/* node datoms + :tick/* scan-cycle observations.
    The scan-cycle observation IS the canonical state (kotoba-os: scan-cycle = Datom txn).
  DERIVED (transient, :bond/is-transient true) — per-station OEE / energy / quality KPIs
    + routed recommendations; computed on READ, NOT persisted (G3 — KPIs are not facts,
    they are read-time aggregates of the disclosed ticks).

Pure stdlib — runnable inside the itonami kotoba pywasm actor (componentize-py).
Usage:
    python3 datom_emit.py [seed.edn] [--out OUTDIR] [--tx N]
"""
from __future__ import annotations
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load, analyze  # noqa: E402

STATION_ATTRS = [":station/label", ":station/line", ":station/takt-s",
                 ":station/rated-kw", ":station/sourcing"]
TICK_ATTRS = [":tick/station", ":tick/t", ":tick/state", ":tick/cycles",
              ":tick/good", ":tick/scrap", ":tick/kwh", ":tick/interval-s"]
DERIVED_KPIS = ["oee", "availability", "performance", "quality",
                "energy_per_good", "idle_energy_frac", "scrap_rate"]
KPI_ATTR = {
    "oee": ":ops/oee", "availability": ":ops/availability",
    "performance": ":ops/performance", "quality": ":ops/quality",
    "energy_per_good": ":ops/energy-per-good", "idle_energy_frac": ":ops/idle-energy-frac",
    "scrap_rate": ":ops/scrap-rate",
}


def _fmt(v) -> str:
    if v is True:
        return "true"
    if v is False:
        return "false"
    if v is None:
        return "nil"
    if v == float("inf"):
        return ":inf"
    if isinstance(v, str):
        return v if v.startswith(":") else '"' + v.replace('\\', '\\\\').replace('"', '\\"') + '"'
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def emit(stations: dict, ticks: list, res: dict, tx: int = 1) -> str:
    L = []
    L.append(";; itonami 営み — GENERATED kotoba Datom log (ADR-2606082300). DO NOT hand-edit.")
    L.append(";; Canonical EAVT state (ADR-2605312345). [e a v tx op].")
    L.append(";; GROUND op :add = durable (station + scan-cycle ticks).")
    L.append(";; DERIVED :bond/is-transient = KPIs computed on read (G3 — aggregates, not facts).")
    L.append("[")

    for sid, st in stations.items():
        for a in STATION_ATTRS:
            if a in st and st[a] is not None:
                L.append(f"[{_fmt(sid)} {a} {_fmt(st[a])} {tx} :add]")

    for tk in ticks:
        sid = tk.get(":tick/station")
        t = tk.get(":tick/t")
        eid = f"tick.{str(sid).lstrip(':')}.{t}"
        for a in TICK_ATTRS:
            if a in tk and tk[a] is not None:
                L.append(f"[{_fmt(eid)} {a} {_fmt(tk[a])} {tx} :add]")

    L.append(";; ── DERIVED KPIs (transient; aggregate of scan-cycle ticks, computed on read) ──")
    for sid in sorted(s for s in res if not s.startswith("_")):
        r = res[sid]
        for k in DERIVED_KPIS:
            L.append(f"[{_fmt(sid)} {KPI_ATTR[k]} {_fmt(r[k])} {tx} :derived] "
                     ";; :bond/is-transient true")

    rec = res.get("_recommend", {})
    L.append(";; ── routed findings (transient; to human/Council, never a write-back — G1) ──")
    for kind, payload in rec.items():
        L.append(f"[:line.sarutahiko-a :ops/routed-{kind} {_fmt(payload['station'])} {tx} :derived] "
                 ";; :bond/is-transient true")

    L.append("]")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-factory-ops.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    tx = int(argv[argv.index("--tx") + 1]) if "--tx" in argv else 1
    outdir.mkdir(parents=True, exist_ok=True)

    stations, ticks = load(seed)
    res = analyze(stations, ticks)
    out = outdir / "itonami-datoms.kotoba.edn"
    out.write_text(emit(stations, ticks, res, tx), encoding="utf-8")
    print(f"itonami datom log → {out} ({len(stations)} stations + {len(ticks)} ticks, tx={tx})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
