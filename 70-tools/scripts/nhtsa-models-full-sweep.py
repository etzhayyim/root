#!/usr/bin/env python3
"""NHTSA full-maker model sweep.

Reads every Make_ID from vertex_repo_record (com.etzhayyim.apps.car_maker.maker),
fetches NHTSA GetModelsForMakeId/{id} for each, bulk-inserts models into
vertex_repo_record as com.etzhayyim.apps.kuruma.model.

Usage: PG_URL=postgres://... python3 70-tools/scripts/nhtsa-models-full-sweep.py

Concurrency: 20 parallel HTTP workers.
Progress: stderr log every 500 makers.
Idempotency: skips Model_IDs already present in vertex_repo_record.
"""

import os, sys, json, time, urllib.request, concurrent.futures
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras

PG_URL = os.environ.get("PG_URL") or sys.exit("set PG_URL")
REPO = "did:web:kuruma.etzhayyim.com"
COLL = "com.etzhayyim.apps.kuruma.model"
CAR_MAKER_COLL = "com.etzhayyim.apps.car_maker.maker"
CONCURRENCY = 20
BATCH_SIZE = 500

def fetch_models(make_id: str) -> list[dict]:
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeId/{make_id}?format=json"
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            d = json.loads(r.read().decode("utf-8"))
        return d.get("Results", []) or []
    except Exception:
        return []

def main():
    conn = psycopg2.connect(PG_URL)
    cur = conn.cursor()
    print("reading maker IDs from vertex_repo_record…", file=sys.stderr)
    cur.execute(
        "SELECT value_json FROM vertex_repo_record WHERE collection = %s",
        (CAR_MAKER_COLL,),
    )
    make_ids: list[str] = []
    for (vj,) in cur.fetchall():
        try:
            m = json.loads(vj or "{}")
        except Exception:
            continue
        mid = m.get("makeId") or m.get("Make_ID") or m.get("nhtsaMakeId")
        if mid:
            make_ids.append(str(mid))
    make_ids = list(set(make_ids))
    print(f"  → {len(make_ids)} unique maker IDs", file=sys.stderr)

    print("reading existing nhtsa-m rkeys…", file=sys.stderr)
    cur.execute(
        "SELECT rkey FROM vertex_repo_record WHERE collection = %s AND rkey LIKE 'nhtsa-m%%'",
        (COLL,),
    )
    existing = {r[0] for r in cur.fetchall()}
    print(f"  → {len(existing)} already present", file=sys.stderr)

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    now_ms = int(time.time() * 1000)

    total_fetched = 0
    total_new = 0
    batch_rows: list[tuple] = []

    def flush():
        nonlocal batch_rows
        if not batch_rows:
            return
        psycopg2.extras.execute_values(
            cur,
            """INSERT INTO vertex_repo_record
               (uri, cid, collection, rkey, repo, repo_rev, value_json, indexed_at, takedown_ref, ts_ms, created_at)
               VALUES %s""",
            batch_rows,
            template="(%s,'',%s,%s,%s,'',%s,%s,NULL,%s,%s)",
            page_size=BATCH_SIZE,
        )
        conn.commit()
        batch_rows = []

    processed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        for make_id, results in zip(
            make_ids,
            ex.map(fetch_models, make_ids, chunksize=1),
        ):
            processed += 1
            for r in results:
                model_id = r.get("Model_ID")
                model_name = r.get("Model_Name", "")
                if not model_id or not model_name:
                    continue
                rkey = f"nhtsa-m{model_id}"
                if rkey in existing:
                    continue
                existing.add(rkey)
                uri = f"at://{REPO}/{COLL}/{rkey}"
                value = json.dumps(
                    {
                        "$type": COLL,
                        "nhtsaModelId": str(model_id),
                        "name": model_name,
                        "maker": r.get("Make_Name", ""),
                        "makerId": str(r.get("Make_ID", "")),
                        "source": "nhtsa-vpic",
                    },
                    ensure_ascii=False,
                )
                batch_rows.append((uri, COLL, rkey, REPO, value, now_iso, now_ms, now_iso))
                total_new += 1
                total_fetched += 1
                if len(batch_rows) >= BATCH_SIZE:
                    flush()
            if processed % 500 == 0:
                print(
                    f"  [{processed}/{len(make_ids)}] new={total_new} fetched={total_fetched}",
                    file=sys.stderr,
                )
    flush()
    print(f"DONE. makers_processed={processed} new_models={total_new}", file=sys.stderr)
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
