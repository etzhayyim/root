#!/usr/bin/env python3
"""kasa 嵩 — ingest cell: PUBLIC compute-capacity data → kotoba EAVT observations.

Bridges public, redistributable data points into the `:compute.series/*` + `:compute.obs/*`
vocabulary, gating every row through the G1 admissibility layer (sources.admissible). Two
shapes are accepted offline (data/ingest/*.json):

  • "rows"  : {"source": "src.epoch", "publisher": "epoch-ai", "access": "open-dataset",
              "rows": [ {"series": "cap.flops.frontier-training.world", "year": 2025,
                         "value": 1.0e26, "sourcing": "estimated",
                         "method": "Epoch AI largest-model training FLOP"} ]}
  • "series": optional new :compute.series definitions (same file, key "series": [ {...} ]).

NETWORK DISCIPLINE (G7 + ADR-2605262400 §7 passive-only):
  - DEFAULT = OFFLINE. Reads pre-downloaded files from data/ingest/*.json (no network).
  - LIVE fetch requires BOTH `KASA_OPERATOR_GATE=1` AND an explicit `--fetch-epoch`. Even
    then it is a single polite request to the public CC-BY Epoch AI dataset, never a scrape.
  - Real reported rows are `:authoritative`; the seed stays `:representative`. Merge keeps the
    more-authoritative source on id collision (authoritative > estimated/representative).

  python3 methods/ingest.py                       # offline: bridge data/ingest/*.json + seed
  KASA_OPERATOR_GATE=1 python3 methods/ingest.py --fetch-epoch   # live Epoch AI CC-BY (gated)
ADR-2606072000.
"""
from __future__ import annotations
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "methods"))
import kasa_edn  # noqa: E402
from sources import admissible  # noqa: E402

SEED = os.path.join(HERE, "data", "seed-compute-capacity.kotoba.edn")
RANK = {":representative": 0, ":estimated": 1, ":synthesized": 0, ":authoritative": 2}


def rows_to_obs(obj):
    """A "rows" ingest file → list of :compute.obs dicts. G1-gated by sources.admissible."""
    source = obj["source"]
    publisher = obj.get("publisher", "")
    access = obj.get("access")
    if not admissible(publisher, access):
        sys.exit(f"refused (G1): publisher {publisher!r}/access {access!r} is not an admissible "
                 f"public source (Charter Rider §2(e)+§2(c)). Read the press release, never the terminal.")
    out = []
    for r in obj.get("rows", []):
        sid = r["series"]
        year = int(r["year"])
        sourcing = ":" + r.get("sourcing", "authoritative").lstrip(":")
        out.append({
            ":compute.obs/id": f"obs.{sid}.{year}",
            ":compute.obs/series": sid,
            ":compute.obs/year": year,
            ":compute.obs/value": float(r["value"]),
            ":compute.obs/source": source,
            ":compute.obs/method": r.get("method", ""),
            ":compute.obs/sourcing": sourcing,
        })
    return out


def offline_ingest():
    """Bridge any data/ingest/*.json ("rows"-shaped); collect new series + obs."""
    ingest_dir = os.path.join(HERE, "data", "ingest")
    series, obs = [], []
    if os.path.isdir(ingest_dir):
        for fn in sorted(os.listdir(ingest_dir)):
            if not fn.endswith(".json"):
                continue
            with open(os.path.join(ingest_dir, fn)) as fh:
                obj = json.load(fh)
            series += obj.get("series", [])
            obs += rows_to_obs(obj)
    return series, obs


def fetch_epoch():
    """LIVE Epoch AI notable-models CSV fetch — G7-gated, single polite request, CC-BY source."""
    if os.environ.get("KASA_OPERATOR_GATE") != "1":
        sys.exit("refused: live fetch requires KASA_OPERATOR_GATE=1 (G7 Council+operator). "
                 "Offline mode reads data/ingest/*.json.")
    import urllib.request
    url = "https://epoch.ai/data/notable_ai_models.csv"
    req = urllib.request.Request(url, headers={"User-Agent": "etzhayyim-kasa research jun@etzhayyim.group"})
    with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310 (gated, public CC-BY host)
        text = r.read().decode("utf-8", "replace")
    # caller-side parse is R1 (column schema versioning); R0 just proves the gated path + persists raw.
    raw = os.path.join(HERE, "data", "ingest", "epoch-notable-models.csv")
    with open(raw, "w") as f:
        f.write(text)
    print(f"kasa ingest: fetched Epoch AI CC-BY dataset ({len(text)} bytes) → {raw} "
          f"(parse into rows-JSON is R1; place a rows-shaped file in data/ingest/ to bridge).")
    return [], []


def merge_with_seed(series, obs):
    """Merge ingested over the :representative/:estimated seed; more-authoritative wins on id."""
    seed = kasa_edn.read_file(SEED)
    by_id = {}
    for row in seed:
        rid = row.get(":compute.series/id") or row.get(":compute.obs/id") or row.get(":compute.source/id")
        by_id[rid] = row
    for row in series + obs:
        rid = row.get(":compute.series/id") or row.get(":compute.obs/id")
        old = by_id.get(rid)
        new_rank = RANK.get(row.get(":compute.obs/sourcing") or row.get(":compute.series/sourcing"), 0)
        old_rank = RANK.get((old or {}).get(":compute.obs/sourcing") or (old or {}).get(":compute.series/sourcing"), -1)
        if old is None or new_rank >= old_rank:
            by_id[rid] = row
    return list(by_id.values())


def main():
    if "--fetch-epoch" in sys.argv:
        series, obs = fetch_epoch()
    else:
        series, obs = offline_ingest()
        n = len(obs)
        print(f"kasa ingest (offline): bridged {len(series)} series · {n} obs from data/ingest/"
              + ("" if n else " (none present — seed is the graph; drop rows-JSON in data/ingest/)"))
    merged = merge_with_seed(series, obs)
    out = os.path.join(HERE, "data", "capacity.merged.kotoba.edn")
    with open(out, "w") as f:
        f.write(";; kasa — merged compute-capacity graph (seed ⊕ ingested; authoritative wins). GENERATED by ingest.py.\n[")
        f.write("\n".join(" {" + " ".join(f"{k} {_v(v)}" for k, v in row.items()) + "}" for row in merged))
        f.write("\n]\n")
    print(f"  → data/capacity.merged.kotoba.edn ({len(merged)} rows). Run analyze.py on it for growth.")


def _v(v):
    if isinstance(v, str):
        return v if v.startswith(":") else '"' + v.replace('"', '\\"') + '"'
    if isinstance(v, bool):
        return "true" if v else "false"
    return repr(v)


if __name__ == "__main__":
    main()
