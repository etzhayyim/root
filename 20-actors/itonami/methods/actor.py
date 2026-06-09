#!/usr/bin/env python3
"""itonami 営み — R11 WASM actor entrypoint (ADR-2606082300).

The single uniform API that the kotoba pywasm actor (componentize-py) exports — it wires the
nine cells into the WIT-sketched surface (wasm/README.md) so itonami is actually invokable as
a content-addressed WASM actor under "one Worker, many WASM actors" (ADR-2606014500/4600).

Exports (each returns a string — JSON for views, EDN for the canonical Datom log):
  summary()      one-screen brain view: line OEE + top alert + drift + attend-first line
  analyze_json() per-station + line KPIs + routed findings
  digest_json()  fused daily digest + Murakumo narration (G7)
  alert_json()   graded threshold alerts (advisory only, G1)
  fleet_json()   multi-line plant rollup + ranking
  datoms(tx)     canonical EAVT Datom log (the durable ground state, ADR-2605312345)

CONSTITUTIONAL: the WASM component is READ-ONLY by construction — no OT socket, no filesystem,
no network at runtime; seeds are bundled read-only. It cannot actuate (G1), carries no worker
dimension (G2), and runs inference only via Murakumo (G7). All the cells' gates hold in-WASM
because the component contains no machinery that could violate them.

Pure stdlib (json). Usage:
    python3 actor.py <summary|analyze|digest|alert|fleet|datoms> [--tx N]
"""
from __future__ import annotations
import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load, analyze  # noqa: E402
import optimize, inspect as vis, datom_emit, digest as dg, alert as al, fleet as fl, trend as tr  # noqa: E402

_DATA = pathlib.Path(__file__).resolve().parent.parent / "data"


def _clean(obj):
    """JSON-safe: drop non-finite floats (e.g. energy/good = inf) to null + keep determinism."""
    if isinstance(obj, float):
        return None if (obj == float("inf") or obj != obj) else obj
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    return obj


def _ctx():
    stations, ticks = load(_DATA / "seed-factory-ops.kotoba.edn")
    detections = vis.load_detections(_DATA / "seed-vision-detections.kotoba.edn")
    hist_p = _DATA / "seed-ops-history.kotoba.edn"
    history = tr.load_history(hist_p) if hist_p.exists() else None
    return stations, ticks, detections, history


def _json(obj) -> str:
    return json.dumps(_clean(obj), sort_keys=True, ensure_ascii=False)


def analyze_json() -> str:
    stations, ticks, _, _ = _ctx()
    res = analyze(stations, ticks)
    stns = {s: res[s] for s in res if not s.startswith("_")}
    return _json({"line": res["_line"], "stations": stns, "recommend": res["_recommend"]})


def digest_json() -> str:
    stations, ticks, detections, history = _ctx()
    d = dg.build_digest(stations, ticks, detections, history)
    narration = dg.narrate(d)
    return _json({"narration": narration["text"], "backend": narration["backend"],
                  "facts": dg._facts(d)})


def alert_json() -> str:
    stations, ticks, _, _ = _ctx()
    alerts = al.evaluate(stations, analyze(stations, ticks))
    return _json({"alerts": alerts, "counts": al.counts(alerts)})


def fleet_json() -> str:
    stations, ticks = load(_DATA / "seed-fleet-ops.kotoba.edn")
    return _json(fl.rollup(stations, ticks))


def datoms(tx: int = 1) -> str:
    """Canonical EAVT Datom log (durable ground state) — EDN, not JSON."""
    stations, ticks, _, _ = _ctx()
    return datom_emit.emit(stations, ticks, analyze(stations, ticks), tx)


def summary() -> str:
    """One-screen brain view fusing the headline signals."""
    stations, ticks, detections, history = _ctx()
    res = analyze(stations, ticks)
    alerts = al.evaluate(stations, res)
    d = dg.build_digest(stations, ticks, detections, history)
    fleet = fl.rollup(*load(_DATA / "seed-fleet-ops.kotoba.edn"))
    top_alert = alerts[0] if alerts else None
    return _json({
        "line_oee": res["_line"]["oee"],
        "bottleneck": res["_recommend"]["bottleneck"]["station"],
        "top_alert": ({"scope": top_alert["scope"], "kpi": top_alert["kpi"],
                       "severity": top_alert["severity"]} if top_alert else None),
        "drift_degrading": (d["drift"]["n"] if d.get("drift") else 0),
        "fleet_attend_first": fleet["plant"]["worst_line"],
    })


_VERBS = {"summary": summary, "analyze": analyze_json, "digest": digest_json,
          "alert": alert_json, "fleet": fleet_json}


def main(argv):
    verb = argv[1] if len(argv) > 1 and not argv[1].startswith("--") else "summary"
    if verb == "datoms":
        tx = int(argv[argv.index("--tx") + 1]) if "--tx" in argv else 1
        sys.stdout.write(datoms(tx))
        return 0
    fn = _VERBS.get(verb)
    if fn is None:
        sys.stderr.write(f"unknown verb {verb!r}; choose {sorted(_VERBS) + ['datoms']}\n")
        return 2
    sys.stdout.write(fn() + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
