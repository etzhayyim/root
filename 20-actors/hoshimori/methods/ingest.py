#!/usr/bin/env python3
"""hoshimori 星守 — orbital-catalog ingest bridge (ADR-2606073600 §G7).

Bridges the PUBLIC CelesTrak SATCAT (https://celestrak.org/pub/satcat.csv) into the
orbital organism graph as **AGGREGATE-ONLY** stewardship facts, then merges with the
curated seed (seed wins on :organism/id collision; new owners append).

G1 (constitutional — the hard rule this file is built around): hoshimori is a
STEWARDSHIP map, NEVER a targeting / interception aid. This ingest therefore emits
**only regime-aggregate object COUNTS per owner and per orbital shell** — it NEVER
stores a per-object state vector (apogee/perigee/inclination/epoch). The per-object
orbital elements in the SATCAT are read transiently to BUCKET an object into a shell
regime and are then discarded; only the bucket COUNTS persist. ASAT / kinetic-intercept
uses stay unrepresentable (§1.12): there is no per-object positional datom to target.

NETWORK DISCIPLINE (G7): live fetch requires HOSHIMORI_OPERATOR_GATE=1 (Council+operator).
Offline default reads a pre-downloaded data/ingest/satcat.csv if present, else re-emits
the seed unchanged. Catalog-derived counts are :authoritative; the seed sample stays as-is.

  HOSHIMORI_OPERATOR_GATE=1 python3 methods/ingest.py --fetch     # live CelesTrak (gated)
  python3 methods/ingest.py                                       # offline: data/ingest/satcat.csv + seed
"""
from __future__ import annotations
import csv
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
SEED = HERE / "data" / "seed-orbit-graph.kotoba.edn"
OUT = HERE / "data" / "orbit-catalog.merged.kotoba.edn"
SATCAT_URL = "https://celestrak.org/pub/satcat.csv"

# CelesTrak SATCAT OWNER code → (id-slug, display, ISO-3166 jurisdiction). Bounded map of
# the major catalog owners; unmapped codes pass through with the raw code as jurisdiction.
OWNER = {
    "US": ("us", "United States", "US"), "CIS": ("ru", "Russia / CIS", "RU"),
    "PRC": ("cn", "China (PRC)", "CN"), "ESA": ("esa", "European Space Agency", "EU"),
    "JPN": ("jp", "Japan", "JP"), "IND": ("in", "India", "IN"), "FR": ("fr", "France", "FR"),
    "UK": ("gb", "United Kingdom", "GB"), "GER": ("de", "Germany", "DE"), "ITSO": ("itso", "Intelsat (ITSO)", "INT"),
    "SES": ("lu", "SES (Luxembourg)", "LU"), "ORB": ("orb", "Orbcomm", "US"), "GLOB": ("glob", "Globalstar", "US"),
    "SKOR": ("kr", "South Korea", "KR"), "TWN": ("tw", "Taiwan", "TW"), "CA": ("ca", "Canada", "CA"),
    "LUXE": ("lu2", "Luxembourg", "LU"), "NETH": ("nl", "Netherlands", "NL"), "SPN": ("es", "Spain", "ES"),
    "ITLY": ("it", "Italy", "IT"), "BRAZ": ("br", "Brazil", "BR"), "AUS": ("au", "Australia", "AU"),
    "SAFR": ("za", "South Africa", "ZA"), "ISRA": ("il", "Israel", "IL"), "ARGN": ("ar", "Argentina", "AR"),
    "TURK": ("tr", "Turkey", "TR"), "UAE": ("ae", "United Arab Emirates", "AE"), "INDO": ("id", "Indonesia", "ID"),
    "EUME": ("eume", "EUMETSAT", "EU"), "EUTE": ("eute", "Eutelsat", "FR"), "NOR": ("no", "Norway", "NO"),
    "SAUD": ("sa", "Saudi Arabia", "SA"), "THAI": ("th", "Thailand", "TH"), "MEX": ("mx", "Mexico", "MX"),
    "VENZ": ("ve", "Venezuela", "VE"), "EGYP": ("eg", "Egypt", "EG"), "PAKI": ("pk", "Pakistan", "PK"),
}


def regime(apogee, perigee, period):
    """Bucket an object into a shell regime from its orbital elements (then discard them, G1)."""
    try:
        ap = float(apogee); pe = float(perigee); pd = float(period or 0)
    except (ValueError, TypeError):
        return None
    if ap <= 0:
        return None
    if 35000 <= ap <= 37000 and pe >= 33000:
        return ":geo"
    if ap > 37000 or (ap - pe) > 20000:
        return ":heo"
    if ap <= 2000:
        return ":leo"
    if ap <= 35000:
        return ":meo"
    return ":geo"


def aggregate(rows):
    """SATCAT rows → per-owner + per-regime AGGREGATE counts (no per-object retention)."""
    owners = {}   # code → {pay, rb, deb, total, regimes:{}}
    regimes = {}  # regime → count (on-orbit payloads+bodies)
    for r in rows:
        if (r.get("DECAY_DATE") or "").strip():   # decayed = no longer on orbit
            continue
        owner = (r.get("OWNER") or "TBD").strip() or "TBD"
        otype = (r.get("OBJECT_TYPE") or "").strip()
        o = owners.setdefault(owner, {"pay": 0, "rb": 0, "deb": 0, "total": 0})
        o["total"] += 1
        if otype == "PAY":
            o["pay"] += 1
        elif otype == "R/B":
            o["rb"] += 1
        elif otype == "DEB":
            o["deb"] += 1
        reg = regime(r.get("APOGEE"), r.get("PERIGEE"), r.get("PERIOD"))
        if reg and otype in ("PAY", "R/B"):
            regimes[reg] = regimes.get(reg, 0) + 1
    return owners, regimes


def emit_operator(code, agg):
    slug, label, juris = OWNER.get(code, (code.lower().replace("/", "-"), code, code))
    return ('{:organism/id "orbit.cat.%s" :organism/kind :operator :organism/label %s '
            ':op/kind :catalog-owner :op/jurisdiction "%s" :op/object-count %d '
            ':op/payload-count %d :op/rocket-body-count %d :op/debris-count %d '
            ':organism/sourcing :authoritative}' %
            (slug, _s(label + " (cataloged objects)"), juris,
             agg["total"], agg["pay"], agg["rb"], agg["deb"]))


def emit_occupancy(reg, n):
    return ('{:organism/id "orbit.occ.%s" :organism/kind :occupancy :organism/label %s '
            ':occ/regime %s :occ/on-orbit-count %d :organism/sourcing :authoritative}' %
            (reg.lstrip(":"), _s("On-orbit occupancy " + reg.lstrip(":").upper()), reg, n))


def _s(x):
    return '"' + str(x).replace("\\", "\\\\").replace('"', '\\"') + '"'


def fetch_satcat(dest):
    if os.environ.get("HOSHIMORI_OPERATOR_GATE") != "1":
        sys.exit("refused: live CelesTrak fetch requires HOSHIMORI_OPERATOR_GATE=1 (G7 Council+operator).")
    import urllib.request
    req = urllib.request.Request(SATCAT_URL, headers={"User-Agent": "etzhayyim-hoshimori research jun@etzhayyim.group"})
    with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310 (gated, public catalog)
        dest.write_bytes(r.read())


def main(argv):
    ingest_dir = HERE / "data" / "ingest"
    ingest_dir.mkdir(exist_ok=True)
    satcat = ingest_dir / "satcat.csv"
    if "--fetch" in argv:
        fetch_satcat(satcat)
        print(f"hoshimori.ingest: fetched CelesTrak SATCAT → {satcat} ({satcat.stat().st_size} bytes)")

    seed_text = SEED.read_text(encoding="utf-8").rstrip()
    if not satcat.exists():
        OUT.write_text(seed_text + "\n", encoding="utf-8")
        print("hoshimori.ingest: no satcat.csv — seed is the graph (drop CelesTrak CSV in data/ingest/).")
        return 0

    with satcat.open(newline="") as fh:
        owners, regimes = aggregate(list(csv.DictReader(fh)))
    # top owners by total on-orbit objects (bounded; the rest fold into nothing — counts only)
    top = sorted(owners.items(), key=lambda kv: -kv[1]["total"])
    top = [(c, a) for c, a in top if a["total"] >= 20][:60]
    ops = [emit_operator(c, a) for c, a in top]
    occ = [emit_occupancy(reg, regimes[reg]) for reg in sorted(regimes)]

    body = seed_text[:seed_text.rfind("]")].rstrip()
    extras = "\n ;; ── CelesTrak SATCAT aggregate ingest (:authoritative; counts only, G1 no-ephemeris) ──\n " + \
             "\n ".join(ops + occ)
    OUT.write_text(body + extras + "\n]\n", encoding="utf-8")
    total_objs = sum(a["total"] for a in owners.values())
    print(f"hoshimori.ingest: {len(owners)} owners / {total_objs} on-orbit objects aggregated "
          f"→ {len(ops)} owner nodes + {len(occ)} regime-occupancy nodes (counts only)")
    print(f"  regimes: " + " ".join(f"{r.lstrip(':')}={n}" for r, n in sorted(regimes.items())))
    print(f"  → {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
