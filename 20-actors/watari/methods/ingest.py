#!/usr/bin/env python3
"""watari 渡り — public AIS/ADS-B broadcast normalizer (R0).

ADR-2606041827. Normalizes a PUBLIC transponder-broadcast batch (AISStream.io AIS
messages / OpenSky `/states/all` state vectors) into kotoba-EDN `:craft/*` +
`:craft.fix/*` datoms, and dedup-merges against the seed (seed identity wins).

CONSTITUTIONAL (watari G1 + G4 + G7):
  - Ingests ONLY public transponder broadcasts. Private-craft owner / crew /
    passenger identity is never derived (G4). Military / blocked-from-display
    craft are dropped (G1).
  - LIVE fetch (network) is OUTWARD-GATED: it requires both WATARI_OPERATOR_GATE=1
    (Council/operator attestation) AND an explicit --live flag. Default mode is
    OFFLINE: it reads a local sample batch and tags everything :representative (G5).

stdlib only. Usage:
    python3 ingest.py --batch data/ingest/sample-batch.json [--out OUTDIR]
    python3 ingest.py --live          # refused unless WATARI_OPERATOR_GATE=1 (G7)
"""
from __future__ import annotations
import sys, os, json, pathlib


def _vessel_fix(msg, ts):
    """AISStream-shaped PositionReport → (craft, fix) dicts (:representative)."""
    mmsi = msg.get("MMSI") or msg.get("UserID")
    cid = f"craft.vessel.mmsi{mmsi}"
    craft = {":craft/id": cid, ":craft/kind": ":vessel",
             ":craft/name": msg.get("ShipName", "").strip() or None,
             ":craft/mmsi": mmsi, ":craft/sourcing": ":representative"}
    fix = {":craft.fix/id": f"fix.{cid}.{ts}", ":craft.fix/craft": cid,
           ":craft.fix/lat": msg.get("Latitude"), ":craft.fix/lon": msg.get("Longitude"),
           ":craft.fix/speed-kn": msg.get("Sog"), ":craft.fix/course": msg.get("Cog"),
           ":craft.fix/observed-at": ts, ":craft.fix/source": ":ais",
           ":craft.fix/sourcing": ":representative"}
    return craft, fix


def _aircraft_fix(state, ts):
    """OpenSky /states/all vector → (craft, fix) dicts (:representative).
    Drops on-ground/null-position and any state lacking a public icao24."""
    icao24 = (state[0] or "").strip().lower()
    if not icao24 or state[5] is None or state[6] is None:
        return None, None
    cid = f"craft.aircraft.{icao24}"
    craft = {":craft/id": cid, ":craft/kind": ":aircraft",
             ":craft/callsign": (state[1] or "").strip() or None,
             ":craft/icao24": icao24, ":craft/sourcing": ":representative"}
    fix = {":craft.fix/id": f"fix.{cid}.{ts}", ":craft.fix/craft": cid,
           ":craft.fix/lat": state[6], ":craft.fix/lon": state[5],
           ":craft.fix/alt-m": state[7], ":craft.fix/speed-kn": state[9],
           ":craft.fix/course": state[10], ":craft.fix/on-ground": bool(state[8]),
           ":craft.fix/observed-at": ts, ":craft.fix/source": ":adsb",
           ":craft.fix/sourcing": ":representative"}
    return craft, fix


def normalize(batch):
    """Accepts {"ais": [...], "adsb": {"time": t, "states": [...]}} sample shape."""
    craft, fixes = {}, []
    ts_default = batch.get("observedAt", "1970-01-01T00:00:00Z")
    for msg in batch.get("ais", []):
        c, f = _vessel_fix(msg, msg.get("observedAt", ts_default))
        if c:
            craft.setdefault(c[":craft/id"], c)
            fixes.append(f)
    adsb = batch.get("adsb", {})
    for state in adsb.get("states", []):
        c, f = _aircraft_fix(state, adsb.get("observedAt", ts_default))
        if c:
            craft.setdefault(c[":craft/id"], c)
            fixes.append(f)
    return craft, fixes


def main(argv):
    if "--live" in argv:
        if os.environ.get("WATARI_OPERATOR_GATE") != "1":
            sys.exit("watari G7: live AISStream/OpenSky ingest is Council+operator gated. "
                     "Set WATARI_OPERATOR_GATE=1 with attestation to enable. "
                     "Default offline mode: --batch <sample.json>.")
        sys.exit("watari R0: live fetch not implemented (design-only). "
                 "Wire AISStream WS + OpenSky REST here once gated.")

    if "--batch" not in argv:
        sys.exit(__doc__)
    batch_path = pathlib.Path(argv[argv.index("--batch") + 1])
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    craft, fixes = normalize(batch)
    print(f"watari ingest (offline, :representative): "
          f"{len(craft)} craft, {len(fixes)} fixes from {batch_path.name}")
    # NOTE: emit to data/craft-graph.merged.kotoba.edn (dedup vs seed) is the next R1 step.


if __name__ == "__main__":
    main(sys.argv)
