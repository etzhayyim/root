#!/usr/bin/env python3
"""mitooshi 見通し — watari / watatsuna chokepoint bridge (R0, offline).

ADR-2606051800. The cross-actor composition the maritime-resilience picture is built on:
watari 渡り (live moving-craft) and watatsuna 綿津綱 (submarine cables) both emit chokepoint-
keyed aggregates over the SAME keyword space (:malacca, :luzon-strait, :suez-red-sea,
:hormuz, …). This bridge maps those aggregates into mitooshi `:series` + `:obs` datoms, so
mitooshi can FORECAST the very chokepoints watari/watatsuna OBSERVE. The shared chokepoint
keyword is the join — observe (watari/watatsuna) → forecast (mitooshi).

  watari   :movement/chokepoint    + :movement/chokepoint-transit  → kind :transit-load (vessels)
  watatsuna :resilience/chokepoint + :resilience/chokepoint-load   → kind :cable-load   (Tbps)

Each bridge run is ONE snapshot at --at <ts>; running it over successive snapshots builds the
append-only as-of trail mitooshi forecasts (非終末論). Non-chokepoint records (lanes, craft,
stations) are ignored.

CONSTITUTIONAL: the watari/watatsuna outputs are themselves :derived (their headers say "do
NOT re-ingest as authoritative"); the bridge honours that — it ingests them as PUBLIC
:representative observations of the chokepoint, never as authoritative fact, and tags the
source actor (G11 honesty). Source-class is :public-broadcast (G4). Live wiring to the actors'
live outputs is G10-gated; R0 reads a static snapshot file.

stdlib only. Usage:
    python3 bridge.py --watari ../data/bridge/watari-sample.edn \
                      --watatsuna ../data/bridge/watatsuna-sample.edn --at 1 [--out OUTDIR]
"""
from __future__ import annotations

import pathlib
import sys

try:
    from analyze import load_edn
except ImportError:
    from mitooshi.methods.analyze import load_edn  # type: ignore

# the shared chokepoint keyword space (watari ∩ watatsuna ∩ mitooshi seed)
KNOWN_CHOKEPOINTS = (
    ":malacca", ":luzon-strait", ":suez-red-sea", ":hormuz", ":gibraltar",
    ":south-china-sea", ":bab-el-mandeb",
)


def _slug(cp: str) -> str:
    return cp.lstrip(":")


def _series(cp: str, suffix: str, kind: str, unit: str, actor: str) -> dict:
    sid = f"s-{_slug(cp)}-{suffix}"
    return {":series/id": sid, ":series/name": f"{_slug(cp)} {kind}",
            ":series/kind": f":{kind}", ":series/unit": unit,
            ":series/freq": ":daily", ":series/source": f"{actor} chokepoint roll-up (DERIVED, public)",
            ":series/source-class": ":public-broadcast", ":series/sourcing": ":representative"}


def bridge(records_by_actor: dict[str, list], observed_at: int) -> dict:
    """records_by_actor = {"watari": [...], "watatsuna": [...]}. Returns {series, obs, skipped}."""
    series: dict[str, dict] = {}
    obs: list[dict] = []
    skipped = 0

    for rec in records_by_actor.get("watari", []) or []:
        cp = rec.get(":movement/chokepoint")
        if not cp:
            skipped += 1
            continue
        s = _series(cp, "transit", "transit-load", "vessels", "watari")
        series[s[":series/id"]] = s
        obs.append({":obs/id": f"obs.{s[':series/id']}.{observed_at}", ":obs/series": s[":series/id"],
                    ":obs/observed-at": observed_at, ":obs/value": float(rec.get(":movement/chokepoint-transit", 0)),
                    ":obs/source-actor": "watari"})

    for rec in records_by_actor.get("watatsuna", []) or []:
        cp = rec.get(":resilience/chokepoint")
        if not cp:
            skipped += 1
            continue
        s = _series(cp, "cable", "cable-load", "Tbps", "watatsuna")
        series[s[":series/id"]] = s
        obs.append({":obs/id": f"obs.{s[':series/id']}.{observed_at}", ":obs/series": s[":series/id"],
                    ":obs/observed-at": observed_at, ":obs/value": float(rec.get(":resilience/chokepoint-load", 0)),
                    ":obs/source-actor": "watatsuna"})

    return {"series": series, "obs": obs, "skipped": skipped}


def _emit_edn(b: dict, observed_at: int) -> str:
    L = [f";; chokepoint-observations.kotoba.edn — bridged from watari/watatsuna @ ts={observed_at}.",
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
    if "--at" not in argv:
        sys.exit(__doc__)
    observed_at = int(argv[argv.index("--at") + 1])
    by_actor: dict[str, list] = {}
    for actor, flag in (("watari", "--watari"), ("watatsuna", "--watatsuna")):
        if flag in argv:
            by_actor[actor] = load_edn(pathlib.Path(argv[argv.index(flag) + 1]))
    if not by_actor:
        sys.exit("bridge: provide at least one of --watari <edn> / --watatsuna <edn>")

    b = bridge(by_actor, observed_at)
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
        outdir.mkdir(parents=True, exist_ok=True)
        (outdir / "chokepoint-observations.kotoba.edn").write_text(_emit_edn(b, observed_at))
    chokepts = sorted({s[":series/id"] for s in b["series"].values()})
    print(f"mitooshi bridge @ ts={observed_at}: {len(b['series'])} series, {len(b['obs'])} obs "
          f"from {len(by_actor)} actor(s); {b['skipped']} non-chokepoint records ignored")
    for c in chokepts:
        print(f"  → {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
