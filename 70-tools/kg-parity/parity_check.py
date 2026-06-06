#!/usr/bin/env python3
"""G3 parity-check harness for the open-data KG cutover (RW ↔ etzhayyim/kotoba).

Compares the vendor RisingWave `kg.vertex_entity` against the etzhayyim open-data
KG store, **per source_id**, and reports whether they are at parity. This is the
public-data analogue of MIGRATION-rw-to-kotoba-sovereign Step-7 (the "14-day RW
diff = 0" cutover gate) for the wikidata / crossref / openstreetmap / gBiz sources
migrated by ADR-2605312100. Pass = 0 diff per source.

Why id-set diff is meaningful: both sides compute the entity `id` with the SAME
algorithm (qid for wikidata, sha256(doi)[:16] for crossref, sha256(osm_id)[:16]
for osm, sha256(corp_num)[:16] for gBiz) — the etzhayyim extractors are faithful
ports of the vendor ones — so a set difference is a real missing/extra entity, not
a keying artifact.

NOT runnable from a dev session: the RW side needs `KOTOBA_URL` reachability (and the
kotoba side needs a live kotoba-server, gated on G1). The pure `diff_snapshots`
core is unit-tested (see test_kg_parity.py). An operator runs this where RW (+
optionally kotoba) is reachable, once G1 (kotoba datomic activation) lands.

Usage:
    # etzhayyim side from the local SQLite ingest store (default):
    KOTOBA_URL=postgres://… python parity_check.py \\
        --sources wikidata,crossref,openstreetmap \\
        --sqlite-dir /var/lib/etzhayyim/organism \\
        --out report.json

    # etzhayyim side from kotoba datomic (once G1 is live):
    KOTOBA_URL=… KOTOBA_XRPC_URL=… python parity_check.py --etz-backend kotoba …
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from dataclasses import dataclass, field
from typing import Any

# source_id values are identical on both sides (etzhayyim ports the vendor
# extractors verbatim). gBiz is included but harvested only when enabled.
DEFAULT_SOURCES = ["wikidata", "crossref", "openstreetmap", "japan_company_registry"]

_SAMPLE_CAP = 50  # cap id lists in the report so it stays human-sized


@dataclass
class Snapshot:
    """One side's view of a source: the entity id-set (count derived from it)."""

    source_id: str
    ids: set[str] = field(default_factory=set)

    @property
    def count(self) -> int:
        return len(self.ids)


# ── Pure diff core (unit-tested) ──────────────────────────────────────────────
def diff_snapshots(rw: dict[str, Snapshot], etz: dict[str, Snapshot]) -> dict[str, Any]:
    """Compare RW vs etzhayyim id-sets per source. Pure — no IO. Returns a report
    dict with `parity_ok` true iff every requested source has 0 difference."""
    sources = sorted(set(rw) | set(etz))
    per_source: dict[str, Any] = {}
    overall_ok = True
    for sid in sources:
        rw_ids = rw.get(sid, Snapshot(sid)).ids
        etz_ids = etz.get(sid, Snapshot(sid)).ids
        only_rw = sorted(rw_ids - etz_ids)
        only_etz = sorted(etz_ids - rw_ids)
        ok = not only_rw and not only_etz
        overall_ok = overall_ok and ok
        per_source[sid] = {
            "rw_count": len(rw_ids),
            "etz_count": len(etz_ids),
            "count_diff": len(etz_ids) - len(rw_ids),
            "missing_in_etz": len(only_rw),   # present in RW, absent from etzhayyim
            "missing_in_rw": len(only_etz),   # present in etzhayyim, absent from RW
            "missing_in_etz_sample": only_rw[:_SAMPLE_CAP],
            "missing_in_rw_sample": only_etz[:_SAMPLE_CAP],
            "parity_ok": ok,
        }
    return {"parity_ok": overall_ok, "sources": per_source}


# ── Side readers (IO; guarded — not runnable without the real backends) ───────
def read_rw(source_ids: list[str], rw_url: str | None) -> dict[str, Snapshot]:
    """Read entity ids from the vendor RisingWave `kg.vertex_entity` per source."""
    rw_url = rw_url or os.environ.get("KOTOBA_URL")
    if not rw_url:
        raise RuntimeError("KOTOBA_URL required for the RW side (operator must provide)")
    try:
        import psycopg  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("psycopg[binary] required for the RW side") from exc
    out: dict[str, Snapshot] = {s: Snapshot(s) for s in source_ids}
    with psycopg.connect(rw_url, autocommit=True) as conn:  # pragma: no cover (needs RW)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT source_id, id FROM kg.vertex_entity WHERE source_id = ANY(%s)",
                (source_ids,),
            )
            for sid, eid in cur.fetchall():
                if sid in out and eid is not None:
                    out[sid].ids.add(str(eid))
    return out


def read_etz_sqlite(source_ids: list[str], sqlite_dir: str | None) -> dict[str, Snapshot]:
    """Read entity ids from the etzhayyim local ingest store (ingest_kg_open.db)."""
    sqlite_dir = sqlite_dir or os.environ.get("ORGANISM_SQLITE_DIR", "/var/lib/etzhayyim/organism")
    db_path = os.path.join(sqlite_dir, "ingest_kg_open.db")
    out: dict[str, Snapshot] = {s: Snapshot(s) for s in source_ids}
    if not os.path.exists(db_path):
        return out
    with sqlite3.connect(db_path) as conn:
        placeholders = ",".join("?" for _ in source_ids)
        rows = conn.execute(
            f"SELECT source_id, id FROM vertex_kg_entity WHERE source_id IN ({placeholders})",
            source_ids,
        ).fetchall()
    for sid, eid in rows:
        if sid in out and eid is not None:
            out[sid].ids.add(str(eid))
    return out


def read_etz_kotoba(source_ids: list[str]) -> dict[str, Snapshot]:  # pragma: no cover (needs G1)
    """Read entity ids from kotoba datomic (once G1 is live). Datalog q on the
    etzhayyim-owned public graph: find ?id where [?e :kg/claim/sourceId sid]."""
    raise RuntimeError(
        "kotoba backend not available: G1 (kotoba datomic activation + public "
        "kotoba-server deploy) is not yet live. Use --etz-backend sqlite until then."
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Open-data KG cutover parity check (RW ↔ etzhayyim)")
    ap.add_argument("--sources", default=",".join(DEFAULT_SOURCES),
                    help="comma-separated source_id list")
    ap.add_argument("--rw-url", default=None, help="RisingWave DSN (else $KOTOBA_URL)")
    ap.add_argument("--etz-backend", choices=["sqlite", "kotoba"], default="sqlite")
    ap.add_argument("--sqlite-dir", default=None, help="etzhayyim ingest SQLite dir (else $ORGANISM_SQLITE_DIR)")
    ap.add_argument("--out", default=None, help="write the JSON report to this path")
    args = ap.parse_args(argv)

    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    rw = read_rw(sources, args.rw_url)
    etz = read_etz_kotoba(sources) if args.etz_backend == "kotoba" else read_etz_sqlite(sources, args.sqlite_dir)
    report = diff_snapshots(rw, etz)

    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
    print(text)
    # exit 0 only at full parity → usable as a cutover CI gate.
    return 0 if report["parity_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
