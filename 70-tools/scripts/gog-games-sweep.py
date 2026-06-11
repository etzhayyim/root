#!/usr/bin/env python3
"""Sweep GOG public catalog → vertex_repo_record (media_gamers.title)."""
import os, sys, json, time, urllib.request
import psycopg2, psycopg2.extras
from datetime import datetime, timezone

PG = os.environ["PG_URL"]
REPO = "did:web:media-gamers.etzhayyim.com"
COLL = "com.etzhayyim.apps.media_gamers.title"

def fetch(page):
    url = f"https://catalog.gog.com/v1/catalog?limit=48&order=desc%3Atrending&productType=in%3Agame&page={page}"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"  page {page} err: {e}", file=sys.stderr)
        return {}

conn = psycopg2.connect(PG); cur = conn.cursor()
cur.execute("SELECT rkey FROM vertex_repo_record WHERE collection=%s AND rkey LIKE 'gog-%%'", (COLL,))
existing = {r[0] for r in cur.fetchall()}
print(f"existing gog-* rkeys: {len(existing)}", file=sys.stderr)

now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
now_ms = int(time.time()*1000)
rows = []; new = 0

d0 = fetch(1); pages = d0.get("pages", 1)
print(f"pages: {pages}", file=sys.stderr)
for p in range(1, pages+1):
    d = d0 if p == 1 else fetch(p)
    for g in d.get("products", []) or []:
        gid = g.get("id");
        if not gid: continue
        rkey = f"gog-{gid}"
        if rkey in existing: continue
        existing.add(rkey)
        val = {"$type": COLL, "gogId": str(gid), "title": g.get("title",""),
               "slug": g.get("slug",""), "source": "gog-catalog"}
        uri = f"at://{REPO}/{COLL}/{rkey}"
        rows.append((uri, COLL, rkey, REPO, json.dumps(val, ensure_ascii=False), now_iso, now_ms, now_iso))
        new += 1
    if p % 20 == 0: print(f"  [{p}/{pages}] new={new}", file=sys.stderr)

if rows:
    psycopg2.extras.execute_values(cur,
        "INSERT INTO vertex_repo_record (uri,cid,collection,rkey,repo,repo_rev,value_json,indexed_at,takedown_ref,ts_ms,created_at) VALUES %s",
        rows, template="(%s,'',%s,%s,%s,'',%s,%s,NULL,%s,%s)", page_size=500)
    conn.commit()
print(f"DONE new={new}", file=sys.stderr)
cur.close(); conn.close()
