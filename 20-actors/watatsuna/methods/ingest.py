#!/usr/bin/env python3
"""watatsuna 綿津綱 — TeleGeography-bridge ingester (public cable dataset → kotoba EAVT).

Normalizes a public submarine-cable dataset (submarinecablemap.com / TeleGeography-shaped
JSON: cables[] + landing_points[]) into the watatsuna kotoba ontology
(:cable/* :station/* :cable.link/*), merges it with the curated seed graph (dedup by id),
and writes a merged graph that analyze.py / the viz can consume.

CONSTITUTIONAL GATES:
  G1 public-only — public-record infrastructure only. The bridge MUST NOT carry classified
     routes, precise armoring/burial depth, or live repair-vessel position beyond public AIS.
  G2 resilience-not-interdiction — chokepoint tags come ONLY from the input; this ingester
     NEVER synthesizes a chokepoint (that would be fabricated targeting signal).
  G5 sourcing-honesty — offline/sample ingest is tagged :representative (a bounded sample,
     even when shaped like the real feed). Only a live, operator-gated, attributed fetch from
     the primary registry may tag :authoritative.
  G7 outward-gated — LIVE fetch (--live URL) requires env WATATSUNA_OPERATOR_GATE=<council-token>;
     even then it is a scaffold (refused) in R0. Default offline mode needs no flag.

Usage:
    python3 ingest.py                          # bridge data/ingest/*.json + seed → merged graph
    python3 ingest.py data/ingest/foo.json     # bridge a specific source file
    python3 ingest.py --live <URL> ...         # REFUSED unless operator gate present (R0 scaffold)
"""
from __future__ import annotations
import sys, os, re, json, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import load_edn  # reuse the EDN reader

ACTOR = pathlib.Path(__file__).resolve().parent.parent
KNOWN_CHOKEPOINTS = {
    "luzon-strait", "malacca", "suez-red-sea", "south-china-sea", "gibraltar",
    "hormuz", "bab-el-mandeb", "sunda", "lombok", "taiwan-strait",
}


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def bridge_source(path: pathlib.Path, sourcing: str = "representative"):
    """One public dataset JSON → (cable records, station records, link records)."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    lp = {p["id"]: p for p in doc.get("landing_points", [])}
    cables, stations, links = [], [], []
    station_id = {}  # input lp.id → kotoba :station/id

    for p in doc.get("landing_points", []):
        sid = f"station.{p.get('country', 'xx').lower()}.{_slug(p['name'])}"
        station_id[p["id"]] = sid
        rec = {":station/id": sid, ":station/name": p["name"],
               ":station/country": p.get("country", "??")}
        if "lat" in p:
            rec[":station/lat"] = p["lat"]
        if "lon" in p:
            rec[":station/lon"] = p["lon"]
        # G2/G1: chokepoints ONLY from input, and only known names (never synthesized)
        cps = [c for c in (p.get("chokepoints") or []) if c in KNOWN_CHOKEPOINTS]
        if cps:
            rec[":station/chokepoint"] = cps
        rec[":station/sourcing"] = f":{sourcing}"
        stations.append(rec)

    for c in doc.get("cables", []):
        cid = f"cable.{_slug(c['id'])}"
        rec = {":cable/id": cid, ":cable/name": c["name"], ":cable/status": ":in-service"}
        if c.get("owners"):
            rec[":cable/owner-consortium"] = c["owners"]
        if "length_km" in c:
            rec[":cable/length-km"] = int(c["length_km"])
        if "design_capacity_tbps" in c:
            rec[":cable/design-capacity-tbps"] = float(c["design_capacity_tbps"])
        if "rfs" in c:
            rec[":cable/rfs-year"] = int(c["rfs"])
        rec[":cable/sourcing"] = f":{sourcing}"
        cables.append(rec)
        for raw_lp in c.get("landing_point_ids", []):
            sid = station_id.get(raw_lp)
            if not sid:
                continue
            links.append({
                ":cable.link/id": f"lk.{_slug(c['id'])}.{sid.split('.')[-1]}",
                ":cable.link/cable": cid, ":cable.link/station": sid,
                ":cable.link/sourcing": f":{sourcing}",
            })
    return cables, stations, links


def _key(rec):
    for k in (":cable/id", ":station/id", ":cable.link/id", ":cable.seg/id", ":cable.fault/id"):
        if k in rec:
            return rec[k]
    return None


def to_edn(recs, header):
    def v(x):
        if isinstance(x, bool):
            return "true" if x else "false"
        if isinstance(x, list):
            return "[" + " ".join(v(i) for i in x) + "]"
        if isinstance(x, str):
            return x if x.startswith(":") else f'"{x}"'
        return str(x)
    lines = header + ["["]
    for r in recs:
        lines.append(" {" + " ".join(f"{k} {v(val)}" for k, val in r.items()) + "}")
    lines.append("]")
    return "\n".join(lines) + "\n"


def main():
    if "--live" in sys.argv:
        if not os.environ.get("WATATSUNA_OPERATOR_GATE"):
            sys.exit("REFUSED: live cable-dataset ingest is G7/Council-gated. Set "
                     "WATATSUNA_OPERATOR_GATE=<council-token> + supply an operator DID. "
                     "Offline mode (no --live) needs no flag.")
        sys.exit("REFUSED: live fetch is an R0 scaffold — not implemented. Wire the "
                 "TeleGeography / submarinecablemap public feed via @etzhayyim/sdk under "
                 "Council ratification, tag :authoritative, then re-run.")

    # explicit source(s) or all data/ingest/*.json
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    srcs = [pathlib.Path(a) for a in args] or sorted((ACTOR / "data" / "ingest").glob("*.json"))

    bridged = []
    for s in srcs:
        cs, ss, ls = bridge_source(s)
        bridged += cs + ss + ls
        print(f"  bridged {s.name}: {len(cs)} cables · {len(ss)} stations · {len(ls)} links")

    # write the bridge-only artifact
    bridge_out = ACTOR / "data" / "ingest" / "telegeography-bridge.kotoba.edn"
    bridge_out.write_text(to_edn(bridged, [
        ";; watatsuna — GENERATED bridge graph (public dataset → kotoba EAVT). DO NOT hand-edit.",
        ";; :representative (offline/sample). Live operator-gated fetch would tag :authoritative (G5/G7).",
    ]), encoding="utf-8")

    # merge with the curated seed (dedup by id; seed wins on conflict)
    seed = load_edn(ACTOR / "data" / "seed-cable-graph.kotoba.edn")
    merged, seen = [], set()
    for rec in seed + bridged:
        if not isinstance(rec, dict):
            continue
        k = _key(rec)
        if k is None or k in seen:
            continue
        seen.add(k)
        merged.append(rec)
    merged_out = ACTOR / "data" / "cable-graph.merged.kotoba.edn"
    merged_out.write_text(to_edn(merged, [
        ";; watatsuna — GENERATED merged graph (seed + ingest bridge). DO NOT hand-edit.",
        ";; dedup by id, seed wins. aggregate-first · sourcing-honest (ADR-2606012600).",
    ]), encoding="utf-8")

    nc = sum(1 for r in merged if ":cable/id" in r)
    ns = sum(1 for r in merged if ":station/id" in r)
    print(f"= merged graph: {nc} cables · {ns} stations · {len(merged)} total records")
    print(f"✓ wrote {bridge_out.relative_to(ACTOR)}")
    print(f"✓ wrote {merged_out.relative_to(ACTOR)}")
    print(f"→ next: python3 methods/analyze.py {merged_out.relative_to(ACTOR)} --out out")


if __name__ == "__main__":
    main()
