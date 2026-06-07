#!/usr/bin/env python3
"""mitooshi 見通し — cross-actor chokepoint RESILIENCE composite (R1, offline).

ADR-2606051800 / 2606012600. The "one maritime resilience picture" the charter references:
fuse the SAME chokepoint keyword across three actors —
  watari 渡り    → live vessel transit (current, from the trail's :transit-load series),
  watatsuna 綿津綱 → submarine-cable load (current, from the :cable-load series),
  mitooshi 見通し → the forecast next-value distribution (from the forecast artifact),
into ONE per-chokepoint composite ranked by resilience attention.

A RESILIENCE map, NEVER a target-list (watari G2 + watatsuna G2): the rank exists to route
redundancy / repair pre-staging / congestion-easing — never interdiction. Aggregate-first,
DERIVED :representative, live promotion G10-gated.

Inputs are the committed Datom artifacts (trail + forecast), so the composite is fully
reproducible: latest obs per series = "current"; forecast mean/sd = "expected next".

stdlib only. Usage:
    python3 synthesize.py [--trail FILE] [--forecast FILE] [--out OUTDIR]
"""
from __future__ import annotations

import pathlib
import sys

try:
    from analyze import load_edn
except ImportError:
    from mitooshi.methods.analyze import load_edn  # type: ignore

_HERE = pathlib.Path(__file__).resolve().parent.parent
_TRAIL = _HERE / "data" / "persisted" / "chokepoint-trail.kotoba.edn"
_FORECAST = _HERE / "data" / "persisted" / "chokepoint-forecast.kotoba.edn"


def _chokepoint_of(series_id: str) -> str:
    """s-malacca-cable / s-malacca-transit → :malacca"""
    core = series_id[2:] if series_id.startswith("s-") else series_id
    for suffix in ("-cable", "-transit"):
        if core.endswith(suffix):
            core = core[: -len(suffix)]
    return ":" + core


def latest_by_series(trail_rows: list[dict]) -> dict[str, float]:
    """{series_id: value at the max observed-at} — the current value per series."""
    latest: dict[str, tuple[int, float]] = {}
    for r in trail_rows:
        if ":obs/series" not in r:
            continue
        sid, t, v = r[":obs/series"], int(r[":obs/observed-at"]), float(r[":obs/value"])
        if sid not in latest or t > latest[sid][0]:
            latest[sid] = (t, v)
    return {sid: v for sid, (t, v) in latest.items()}


def forecast_by_series(fc_rows: list[dict]) -> dict[str, tuple[float, float]]:
    """{series_id: (forecast mean, sd)}."""
    out: dict[str, tuple[float, float]] = {}
    for r in fc_rows:
        if ":forecast/series" in r:
            out[r[":forecast/series"]] = (float(r.get(":forecast/mean", 0.0)),
                                          float(r.get(":forecast/sd", 0.0)))
    return out


def synthesize(trail_rows: list[dict], fc_rows: list[dict]) -> list[dict]:
    """Per-chokepoint composite. Returns rows sorted by resilience attention (desc).

    attention = normalized cable load (capacity-at-risk, the dominant resilience term) +
    a live-pressure bump from current transit. Both normalized to [0,1] across chokepoints
    so the blend is scale-free (transit ~1-3 vessels vs cable ~hundreds of Tbps)."""
    cur = latest_by_series(trail_rows)
    fc = forecast_by_series(fc_rows)

    chokes: dict[str, dict] = {}
    for sid, v in cur.items():
        cp = _chokepoint_of(sid)
        d = chokes.setdefault(cp, {"chokepoint": cp, "transit": None, "cable_load": None,
                                   "forecast_cable_mean": None})
        if sid.endswith("-transit"):
            d["transit"] = v
            d["forecast_transit_mean"] = fc.get(sid, (None, None))[0]
        elif sid.endswith("-cable"):
            d["cable_load"] = v
            d["forecast_cable_mean"] = fc.get(sid, (None, None))[0]

    cables = [d["cable_load"] for d in chokes.values() if d["cable_load"] is not None]
    transits = [d["transit"] for d in chokes.values() if d["transit"] is not None]
    max_cable = max(cables) if cables else 1.0
    max_transit = max(transits) if transits else 1.0

    for d in chokes.values():
        nc = (d["cable_load"] / max_cable) if d["cable_load"] and max_cable else 0.0
        nt = (d["transit"] / max_transit) if d["transit"] and max_transit else 0.0
        # cable load dominates (capacity-at-risk); live transit is a secondary pressure term
        d["attention"] = round(0.7 * nc + 0.3 * nt, 4)
    return sorted(chokes.values(), key=lambda x: -x["attention"])


def render_edn(composite: list[dict]) -> str:
    L = [";; chokepoint-resilience-composite.kotoba.edn — cross-actor (watari+watatsuna+mitooshi).",
         ";; ONE maritime resilience picture per chokepoint: live transit + cable load +",
         ";; forecast. attention = 0.7*norm(cable) + 0.3*norm(transit). A RESILIENCE map,",
         ";; NEVER a target-list (routed to redundancy/repair, never interdiction).",
         ";; DERIVED :representative. Live promotion G10-gated. ADR-2606012600.", "", "["]
    for d in composite:
        def _n(x):
            return "nil" if x is None else x
        L.append(
            f' {{:choke/id {d["chokepoint"]} :choke/transit {_n(d.get("transit"))} '
            f':choke/cable-load-tbps {_n(d.get("cable_load"))} '
            f':choke/forecast-cable-mean {_n(d.get("forecast_cable_mean"))} '
            f':choke/attention {d["attention"]} :choke/sourcing :representative}}')
    L.append("]")
    return "\n".join(L) + "\n"


def main(argv: list[str]) -> int:
    trail = pathlib.Path(argv[argv.index("--trail") + 1]) if "--trail" in argv else _TRAIL
    forecast = pathlib.Path(argv[argv.index("--forecast") + 1]) if "--forecast" in argv else _FORECAST
    composite = synthesize(load_edn(trail), load_edn(forecast))
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "chokepoint-resilience-composite.kotoba.edn").write_text(render_edn(composite))
    print("mitooshi cross-actor chokepoint resilience composite (redundancy, not interdiction):")
    for d in composite:
        print(f"  {d['chokepoint']:18s} attention={d['attention']:.3f}  "
              f"transit={d.get('transit')}  cable={d.get('cable_load')}Tbps  "
              f"fc-cable={d.get('forecast_cable_mean')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
