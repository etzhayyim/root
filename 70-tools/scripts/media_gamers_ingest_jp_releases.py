#!/usr/bin/env python3
"""
Ingest Japan-release video games from Wikidata into RisingWave vertex_game_title.

Selection rule (Wikidata SPARQL):
- instance of (or subclass of) video game (Q7889)
- and either:
  - country of origin = Japan (P495=Q17), or
  - publication/release statement has location qualifier Japan (P577 + P291=Q17)
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import time
from typing import List, Tuple

import psycopg2 # kotoba-datomic-projection: historical offline script
from psycopg2.extras import execute_values
import requests

WDQS_URL = "https://query.wikidata.org/sparql"
UA = "etzhayyim-media-gamers-ingest/1.0 (ops@etzhayyim.com)"

COUNT_QUERY = """
SELECT (COUNT(DISTINCT ?game) AS ?cnt) WHERE {
  ?game wdt:P31/wdt:P279* wd:Q7889 .
  FILTER(
    EXISTS { ?game wdt:P495 wd:Q17 } ||
    EXISTS { ?game p:P577 ?s . ?s pq:P291 wd:Q17 }
  )
}
"""

PAGE_QUERY_TMPL = """
SELECT ?game ?titleJa ?titleEn (MIN(?rd) AS ?firstRelease) WHERE {
  ?game wdt:P31/wdt:P279* wd:Q7889 .
  FILTER(
    EXISTS { ?game wdt:P495 wd:Q17 } ||
    EXISTS { ?game p:P577 ?s . ?s pq:P291 wd:Q17 }
  )

  OPTIONAL { ?game rdfs:label ?titleJa FILTER(lang(?titleJa) = "ja") }
  OPTIONAL { ?game rdfs:label ?titleEn FILTER(lang(?titleEn) = "en") }
  OPTIONAL { ?game wdt:P577 ?rd }
}
GROUP BY ?game ?titleJa ?titleEn
ORDER BY ?game
LIMIT __LIMIT__
OFFSET __OFFSET__
"""


def wdqs_json(query: str, timeout: int = 90) -> dict:
  for attempt in range(6):
    try:
      r = requests.get(
        WDQS_URL,
        params={"query": query, "format": "json"},
        timeout=timeout,
        headers={"User-Agent": UA},
      )
      if r.status_code in (429, 503):
        time.sleep(2 ** attempt)
        continue
      r.raise_for_status()
      return r.json()
    except Exception:
      if attempt == 5:
        raise
      time.sleep(2 ** attempt)
  raise RuntimeError("unreachable")


def parse_date_year(date_str: str | None) -> Tuple[str | None, int | None]:
  if not date_str:
    return None, None
  # Wikidata date format: 1997-06-20T00:00:00Z
  d = date_str.split("T", 1)[0]
  if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", d):
    return None, None
  try:
    year = int(d.split("-", 1)[0])
  except Exception:
    year = None
  return d, year


def qid_from_uri(uri: str) -> str:
  return uri.rsplit("/", 1)[-1]


def fetch_page(limit: int, offset: int) -> List[Tuple]:
  q = PAGE_QUERY_TMPL.replace("__LIMIT__", str(limit)).replace("__OFFSET__", str(offset))
  obj = wdqs_json(q)
  rows = []
  for b in obj.get("results", {}).get("bindings", []):
    game_uri = b["game"]["value"]
    qid = qid_from_uri(game_uri)
    title_ja = b.get("titleJa", {}).get("value")
    title_en = b.get("titleEn", {}).get("value")
    first_release_raw = b.get("firstRelease", {}).get("value")
    first_release_date, release_year = parse_date_year(first_release_raw)

    if not title_ja and not title_en:
      title_en = qid

    rows.append(
      (
        f"did:wikidata:{qid}",  # vertex_id
        None,  # _seq
        dt.date.today().isoformat(),  # created_date
        0,  # sensitivity_ord
        "did:web:media-gamers.etzhayyim.com",  # owner_did
        f"wikidata:{qid}",  # external_ids
        title_en,
        title_ja,
        release_year,
        first_release_date,
        None,  # franchise_did
        None,  # engine_did
        None,  # developer_did
        None,  # publisher_did
        None,  # genre_did
        None,  # mode_did
        None,  # rating_esrb
        None,  # rating_cero
      )
    )
  return rows


def upsert_rows(conn, rows: List[Tuple]) -> int:
  if not rows:
    return 0
  insert_sql = """
  INSERT INTO vertex_game_title (
    vertex_id, _seq, created_date, sensitivity_ord, owner_did,
    external_ids, title_en, title_ja, release_year, first_release_date,
    franchise_did, engine_did, developer_did, publisher_did, genre_did, mode_did,
    rating_esrb, rating_cero
  ) VALUES %s
  """
  ids = [r[0] for r in rows]
  with conn.cursor() as cur:
    cur.execute("DELETE FROM vertex_game_title WHERE vertex_id = ANY(%s)", (ids,))
    execute_values(cur, insert_sql, rows, page_size=500)
  conn.commit()
  return len(rows)


def main() -> int:
  ap = argparse.ArgumentParser()
  ap.add_argument("--rw-conn", default=os.getenv("KOTOBA_URL", "REDACTED_USE_DATABASE_URL_ENV?sslmode=disable"))
  ap.add_argument("--page-size", type=int, default=400)
  ap.add_argument("--max-records", type=int, default=0, help="0 = all")
  ap.add_argument("--sleep-ms", type=int, default=250)
  ap.add_argument("--dry-run", action="store_true")
  args = ap.parse_args()

  total_obj = wdqs_json(COUNT_QUERY)
  total = int(total_obj["results"]["bindings"][0]["cnt"]["value"])
  target = total if args.max_records <= 0 else min(total, args.max_records)

  print(f"[info] wdqs_total={total} target={target} page_size={args.page_size}")

  conn = None
  if not args.dry_run:
    conn = psycopg2.connect(args.rw_conn)

  processed = 0
  inserted = 0
  offset = 0

  try:
    while processed < target:
      remaining = target - processed
      limit = min(args.page_size, remaining)
      rows = fetch_page(limit=limit, offset=offset)
      if not rows:
        print(f"[warn] empty page at offset={offset}; stopping")
        break

      if args.dry_run:
        wrote = len(rows)
      else:
        wrote = upsert_rows(conn, rows)

      processed += len(rows)
      inserted += wrote
      offset += limit
      print(f"[progress] processed={processed}/{target} wrote={inserted}")
      time.sleep(max(args.sleep_ms, 0) / 1000.0)
  finally:
    if conn is not None:
      conn.close()

  print(f"[done] processed={processed} wrote={inserted}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
