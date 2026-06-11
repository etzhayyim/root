#!/usr/bin/env python3
"""Walk Wikipedia Category recursively, bulk insert pages as vertex_repo_record.

Usage: PG_URL=... python3 wiki-category-sweep.py <CATEGORY> <REPO> <COLL> <PREFIX>
  e.g. Category:Semiconductor_devices did:web:handotai.etzhayyim.com com.etzhayyim.apps.handotai.device wikiHD
"""
import os, sys, json, time, urllib.request, urllib.parse
import psycopg2, psycopg2.extras
from datetime import datetime, timezone

PG, CAT, REPO, COLL, PFX = os.environ["PG_URL"], sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
MAX_DEPTH = int(os.environ.get("MAX_DEPTH","4"))
LANG = os.environ.get("WIKI_LANG","en")
API = f"https://{LANG}.wikipedia.org/w/api.php"

def q(params):
    url = API + "?" + urllib.parse.urlencode({**params, "format":"json"})
    req = urllib.request.Request(url, headers={"User-Agent":"etzhayyim-collect/1.0 (contact: ops@etzhayyim.com)"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                time.sleep(0.25)
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 2 ** attempt
                time.sleep(wait); continue
            print(f"  err {url[:80]}: {e}", file=sys.stderr); return {}
        except Exception as e:
            print(f"  err {url[:80]}: {e}", file=sys.stderr); return {}
    return {}

seen_cats = set()
pages = {}  # pageid -> title
def walk(cat, depth):
    if depth > MAX_DEPTH or cat in seen_cats: return
    seen_cats.add(cat)
    cont = ""
    while True:
        params = {"action":"query","list":"categorymembers","cmtitle":cat,"cmlimit":500}
        if cont: params["cmcontinue"] = cont
        d = q(params)
        for m in d.get("query",{}).get("categorymembers",[]):
            ns = m.get("ns"); pid = m.get("pageid"); t = m.get("title","")
            if ns == 0 and pid: pages[pid] = t
            elif ns == 14: walk(t, depth+1)
        cont = d.get("continue",{}).get("cmcontinue")
        if not cont: break
    if len(seen_cats) % 20 == 0:
        print(f"  cats={len(seen_cats)} pages={len(pages)}", file=sys.stderr)

print(f"walking {CAT} depth<={MAX_DEPTH}…", file=sys.stderr)
walk(CAT, 0)
print(f"total: cats={len(seen_cats)} pages={len(pages)}", file=sys.stderr)

conn = psycopg2.connect(PG); cur = conn.cursor()
cur.execute(f"SELECT rkey FROM vertex_repo_record WHERE collection=%s AND rkey LIKE '{PFX}-%%'", (COLL,))
existing = {r[0] for r in cur.fetchall()}
now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
now_ms = int(time.time()*1000)
rows = []; new = 0
for pid, title in pages.items():
    rkey = f"{PFX}-{pid}"
    if rkey in existing: continue
    val = {"$type": COLL, "wikiPageId": str(pid), "title": title, "source": f"wikipedia-{CAT}"}
    uri = f"at://{REPO}/{COLL}/{rkey}"
    rows.append((uri, COLL, rkey, REPO, json.dumps(val, ensure_ascii=False), now_iso, now_ms, now_iso))
    new += 1
if rows:
    psycopg2.extras.execute_values(cur,
        "INSERT INTO vertex_repo_record (uri,cid,collection,rkey,repo,repo_rev,value_json,indexed_at,takedown_ref,ts_ms,created_at) VALUES %s",
        rows, template="(%s,'',%s,%s,%s,'',%s,%s,NULL,%s,%s)", page_size=500)
    conn.commit()
print(f"DONE new={new}", file=sys.stderr)
cur.close(); conn.close()
