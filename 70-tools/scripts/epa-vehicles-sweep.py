#!/usr/bin/env python3
"""EPA fueleconomy.gov vehicles.csv → vertex_repo_record (kuruma.model).

Yorishiro-aligned (ADR-2605211900).
  Contract : ai.etzhayyim.yorishiro.fueleconomy.downloadVehiclesCsv
  Lexicon  : 00-contracts/lexicons/ai/etzhayyim/yorishiro/fueleconomy/downloadVehiclesCsv.json
  MCP equiv: @etzhayyim/yorishiro-fueleconomy-mcp
  Charter  : grant (US Government public-domain CSV, 17 USC §105)

Direct urlopen is retained here because the response is a ~21 MB CSV
that would balloon memory if shuttled through the MCP JSON envelope.
The in-cluster equivalent — yorishiro_fueleconomy cell with a
streaming variant — is the canonical path. The on-the-wire URL +
method matches the lexicon's pathTemplate exactly.
"""
import os, sys, csv, io, json, time, urllib.request
import psycopg2, psycopg2.extras
from datetime import datetime, timezone

PG = os.environ["PG_URL"]
REPO = "did:web:kuruma.etzhayyim.com"
COLL = "com.etzhayyim.apps.kuruma.vehicle"

print("fetching EPA CSV (~21MB)…", file=sys.stderr)
# yorishiro op: ai.etzhayyim.yorishiro.fueleconomy.downloadVehiclesCsv (see file docstring)
with urllib.request.urlopen("https://www.fueleconomy.gov/feg/epadata/vehicles.csv", timeout=60) as r:
    data = r.read().decode("utf-8", errors="replace")
rdr = csv.DictReader(io.StringIO(data))
rows_csv = list(rdr)
print(f"  {len(rows_csv)} vehicles", file=sys.stderr)

conn = psycopg2.connect(PG); cur = conn.cursor()
cur.execute("SELECT rkey FROM vertex_repo_record WHERE collection=%s AND rkey LIKE 'epa-%%'", (COLL,))
existing = {r[0] for r in cur.fetchall()}
print(f"existing: {len(existing)}", file=sys.stderr)

now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
now_ms = int(time.time()*1000)
batch = []; new = 0

def flush():
    global batch
    if not batch: return
    psycopg2.extras.execute_values(cur,
        "INSERT INTO vertex_repo_record (uri,cid,collection,rkey,repo,repo_rev,value_json,indexed_at,takedown_ref,ts_ms,created_at) VALUES %s",
        batch, template="(%s,'',%s,%s,%s,'',%s,%s,NULL,%s,%s)", page_size=500)
    conn.commit()
    batch = []

for v in rows_csv:
    vid = v.get("id","").strip()
    if not vid: continue
    rkey = f"epa-{vid}"
    if rkey in existing: continue
    existing.add(rkey)
    val = {"$type": COLL, "epaId": vid, "make": v.get("make",""), "model": v.get("model",""),
           "year": v.get("year",""), "vclass": v.get("VClass",""), "fuelType": v.get("fuelType",""),
           "source": "epa-fueleconomy"}
    uri = f"at://{REPO}/{COLL}/{rkey}"
    batch.append((uri, COLL, rkey, REPO, json.dumps(val, ensure_ascii=False), now_iso, now_ms, now_iso))
    new += 1
    if len(batch) >= 500:
        flush()
        if new % 5000 == 0: print(f"  new={new}", file=sys.stderr)
flush()
print(f"DONE new={new}", file=sys.stderr)
cur.close(); conn.close()
