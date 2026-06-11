#!/usr/bin/env python3
"""mitooshi 見通し — kakaku 価格 price / supply-demand bridge (R0, offline).

ADR-2606051800 (mitooshi) × ADR-2605091200 (kakaku). The cross-actor composition that
lets mitooshi FORECAST the very price / supply-demand series kakaku OBSERVES — the price
analogue of the watari/watatsuna chokepoint bridge (bridge.py). kakaku derives two public,
:representative observation kinds per canonical product:

  kakaku :ph/* (price history)   :ph/product + :ph/total-price → kind :price-level        (minor)
  kakaku :sd/* (supply/demand)   :sd/product + :sd/index       → kind :supply-demand-index (index)

This bridge maps them into mitooshi `:series` + `:obs` datoms keyed on the product. Running it
over successive snapshots builds the append-only as-of trail mitooshi forecasts (非終末論).

CONSTITUTIONAL (mitooshi gates G2/G3/G4/G11):
  - kakaku's outputs are DERIVED public observations of merchant prices; the bridge ingests
    them as :representative / :public-broadcast, NEVER as authoritative fact, tagging
    :obs/source-actor "kakaku" (G11 honesty, G4 source-class).
  - mitooshi forecasts these series as DISTRIBUTIONS routed to RESILIENCE (where will scarcity
    arise?), never a price target and never a trade (G2 non-speculative). The bridge emits only
    series+obs; the forecast (distribution, :forecast/use :resilience) stays in forecast.py.
  - Non-price/SD records (offers, merchants, spreads) are ignored — spread is a present-state
    transparency reading, not a forecastable series here.
  - Live wiring to kakaku's live output is G10-gated; R0 reads a static snapshot file.

stdlib only. Usage:
    python3 bridge_kakaku.py --kakaku ../data/bridge/kakaku-sample.edn --at 1 [--out OUTDIR]
"""
from __future__ import annotations

import pathlib
import sys

try:
    from analyze import load_edn
except ImportError:
    from mitooshi.methods.analyze import load_edn  # type: ignore


def _pslug(pid: str) -> str:
    """Slugify a kakaku product id (e.g. 'jan_4901777300443' or ':jan-...') for a series id."""
    return str(pid).lstrip(":").replace("_", "-").replace(".", "-").lower()


def _series(pid: str, suffix: str, kind: str, unit: str) -> dict:
    sid = f"s-{_pslug(pid)}-{suffix}"
    return {":series/id": sid, ":series/name": f"{_pslug(pid)} {kind}",
            ":series/kind": f":{kind}", ":series/unit": unit,
            ":series/freq": ":daily", ":series/source": "kakaku price roll-up (DERIVED, public)",
            ":series/source-class": ":public-broadcast", ":series/sourcing": ":representative"}


def bridge_kakaku(records: list, observed_at: int) -> dict:
    """records = kakaku-shaped :ph/* and :sd/* observation maps. Returns {series, obs, skipped}.

    A :price-level series per product carrying :ph/total-price, and a :supply-demand-index
    series per product carrying :sd/index. Records lacking a product key are skipped."""
    series: dict[str, dict] = {}
    obs: list[dict] = []
    skipped = 0

    for rec in records or []:
        if ":ph/product" in rec and ":ph/total-price" in rec:
            pid = rec[":ph/product"]
            s = _series(pid, "price", "price-level", "minor")
            series[s[":series/id"]] = s
            obs.append({":obs/id": f"obs.{s[':series/id']}.{observed_at}",
                        ":obs/series": s[":series/id"], ":obs/observed-at": observed_at,
                        ":obs/value": float(rec[":ph/total-price"]), ":obs/source-actor": "kakaku"})
        elif ":sd/product" in rec and ":sd/index" in rec:
            pid = rec[":sd/product"]
            s = _series(pid, "supply-demand", "supply-demand-index", "index")
            series[s[":series/id"]] = s
            obs.append({":obs/id": f"obs.{s[':series/id']}.{observed_at}",
                        ":obs/series": s[":series/id"], ":obs/observed-at": observed_at,
                        ":obs/value": float(rec[":sd/index"]), ":obs/source-actor": "kakaku"})
        else:
            skipped += 1

    return {"series": series, "obs": obs, "skipped": skipped}


def _emit_edn(b: dict, observed_at: int) -> str:
    L = [f";; kakaku-observations.kotoba.edn — bridged from kakaku 価格 @ ts={observed_at}.",
         ";; DERIVED public :representative observations (NOT authoritative). ADR-2606051800.", "", "["]
    for s in b["series"].values():
        L.append(f' {{:series/id "{s[":series/id"]}" :series/kind {s[":series/kind"]} '
                 f':series/unit "{s[":series/unit"]}" :series/source-class :public-broadcast '
                 f':series/sourcing :representative}}')
    for o in b["obs"]:
        L.append(f' {{:obs/id "{o[":obs/id"]}" :obs/series "{o[":obs/series"]}" '
                 f':obs/observed-at {o[":obs/observed-at"]} :obs/value {o[":obs/value"]} '
                 f':obs/source-actor "{o[":obs/source-actor"]}"}}')
    L.append("]")
    return "\n".join(L) + "\n"


def main(argv: list[str]) -> int:
    if "--at" not in argv or "--kakaku" not in argv:
        sys.exit(__doc__)
    observed_at = int(argv[argv.index("--at") + 1])
    records = load_edn(pathlib.Path(argv[argv.index("--kakaku") + 1]))

    b = bridge_kakaku(records, observed_at)
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "kakaku-observations.kotoba.edn").write_text(_emit_edn(b, observed_at))
    print(f"mitooshi kakaku-bridge @ ts={observed_at}: {len(b['series'])} series, "
          f"{len(b['obs'])} obs; {b['skipped']} non-price/SD records ignored")
    for c in sorted(b["series"]):
        print(f"  → {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
