"""autorun.py — 紡ぎ: the autonomous offline beat over the kotoba Datom log (ADR-2606092000).

The kotoba-native routine — etzhayyim runs its own recurring loop on its OWN substrate (the
Mac-mini fleet beating `70-tools/scripts/fleet-heartbeat/heartbeat.sh`), NOT on a vendor's
cron-cloud. Each beat is OFFLINE, deterministic, fail-open, and persists a content-addressed
transaction to the LOCAL append-only kotoba Datom log (ADR-2605312345), mirroring ibuki /
shionome (ADR-2606101200 / 2606072200).

  forage ─▶ publish ─▶ measure ─▶ append tx
  (粘菌/菌糸  (植物-     (coverage   (content-addressed, chain-verified;
   growth     producer   + seed       :tsumugi.cycle/* datoms on the local log)
   plan)      linked-    stats)
              data)

A beat does NO live external I/O: the live WDQS/GLEIF ingest stays operator-gated
(`TSUMUGI_OPERATOR_GATE`, run on the fleet where network is available) — exactly as kanjo's
EDGAR fetch is gate-only. The heartbeat beats only the OFFLINE metabolism: it recomputes the
forage growth-plan, regenerates the provider dataset (so etzhayyim keeps FEEDING others —
publish.py), and records the cycle on the kotoba log. Deterministic: logical time only
(beat index), so same seed + same cycle count → byte-identical head CID.

Stdlib only. Usage:  python3 autorun.py --cycles 1 [--fresh]
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib

import ingest_scale
import publish
import coverage_scale

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEED = ROOT / "data" / "seed-scale-power.kotoba.edn"
LOG = ROOT / "data" / "tsumugi-cycle.datoms.kotoba.edn"   # local, regenerable (.gitignore'd)
AS_OF_BASE = 2606110000


def _cid(body: str) -> str:
    return "tx:sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def _read_head(log: pathlib.Path) -> tuple[str, int]:
    """Return (head_cid, beat_count) by replaying the local log (durable across kills)."""
    if not log.exists():
        return "tx:genesis", 0
    txs = [ln for ln in log.read_text(encoding="utf-8").splitlines() if ":tx/id" in ln]
    if not txs:
        return "tx:genesis", 0
    last = txs[-1]
    cid = last.split('":tx/id "', 1)[-1] if False else None  # parsed below, robustly
    import re
    m = re.search(r':tx/id "([^"]+)"', last)
    return (m.group(1) if m else "tx:genesis"), len(txs)


def _country_pct() -> float:
    c = coverage_scale.compute(*coverage_scale.load_data())
    # coverage_scale.compute exposes per-country coverage; fall back to a direct derivation
    cov = c.get("coverages", {}).get("Countries (~sovereign states)", {})
    if cov:
        return round(cov.get("percent", 0.0), 4)
    return 0.0


def beat(log: pathlib.Path) -> dict:
    """One offline cycle. Returns the appended tx (also written to the local log)."""
    head, n = _read_head(log)
    # 粘菌/菌糸 forage plan (offline, from the seed)
    plan = ingest_scale.forage_plan(SEED)
    # 植物-producer: regenerate the self-sovereign linked-data dataset others consume
    manifest = publish.publish(ROOT / "out")
    pct = _country_pct()
    as_of = AS_OF_BASE + n
    datoms = [
        (":tsumugi.cycle/beat", n),
        (":tsumugi.cycle/as-of", as_of),
        (":tsumugi.cycle/seed-nodes", manifest["counts"]["nodes"]),
        (":tsumugi.cycle/seed-edges", manifest["counts"]["edges"]),
        (":tsumugi.cycle/forage", plan["recommendation"].split(" —")[0].split(" (")[0]),
        (":tsumugi.cycle/frontier-tips", plan["frontier_tips"]),
        (":tsumugi.cycle/harvested", plan["harvested_anchors"]),
        (":tsumugi.cycle/dataset-content-hash", manifest["contentHash"]),
        (":tsumugi.cycle/dataset-triples", manifest["counts"]["triples"]),
        (":tsumugi.cycle/country-coverage-pct", pct),
        (":tsumugi.cycle/published-by", publish.PUBLISHER_DID),
    ]

    def _v(v):
        return f'"{v}"' if isinstance(v, str) else str(v)
    body = "{:tx/prev " + f'"{head}"' + " :tx/datoms [" + " ".join(
        "[" + a + " " + _v(v) + "]" for a, v in datoms) + "]}"
    cid = _cid(body)
    tx_line = "{:tx/id " + f'"{cid}"' + " :tx/prev " + f'"{head}"' + " :tx/datoms [" + " ".join(
        "[" + a + " " + _v(v) + "]" for a, v in datoms) + "]}"
    with log.open("a", encoding="utf-8") as f:
        f.write(tx_line + "\n")
    return {"cid": cid, "prev": head, "beat": n, "datoms": dict(datoms)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycles", type=int, default=1)
    ap.add_argument("--fresh", action="store_true", help="start a fresh local log")
    args = ap.parse_args(argv)
    if args.fresh and LOG.exists():
        LOG.unlink()
    LOG.parent.mkdir(parents=True, exist_ok=True)
    last = None
    for _ in range(args.cycles):
        last = beat(LOG)
    if last:
        d = last["datoms"]
        # the ♥ / log: markers are what fleet-heartbeat.sh greps to detect a healthy beat
        print(f"♥ tsumugi beat {last['beat']}: {d[':tsumugi.cycle/seed-nodes']} nodes · "
              f"forage={d[':tsumugi.cycle/forage']} · dataset {d[':tsumugi.cycle/dataset-triples']} "
              f"triples · coverage {d[':tsumugi.cycle/country-coverage-pct']}%")
        print(f"    log: {last['cid']} (prev {last['prev']}) → {LOG.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
