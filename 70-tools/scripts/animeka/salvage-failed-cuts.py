#!/usr/bin/env python3
# ruff: noqa: E501,T201,S603,S607
"""Salvage failed cutRunner cuts by re-posting with whatever CIDs were captured.

A failed cut shows up as a `vertex_repo_commit` row with collection
`com.etzhayyim.bpmn.audit`, vertex_id ending in `cutRunner:create`, and a
value_json payload containing `cutId / sbCid / lyCid / kfCid / bgCid /
postStatus`. When `postStatus != 200` the cut never made it to the AT
Protocol feed even though up to four blob CIDs were already pinned in
the audit log. This script reads those audits, filters cuts that have
at least N non-null CIDs and no prior PDS post, and reposts each as a
"salvaged" 1-4-image embed.

Auth: uses the legacy `x-magatama-verified: true` internal-trust
header — the same path the BPMN worker takes (ADR-0023 break-glass).
PDS verifies via env-toggled `PDS_LEGACY_INTERNAL_TRUST=1`.

Usage:
  salvage-failed-cuts.py                 # dry-run (default)
  salvage-failed-cuts.py --apply         # actually post
  salvage-failed-cuts.py --since-hours 8 # widen window
  salvage-failed-cuts.py --min-cids 3    # stricter quality
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

PSQL_BIN = os.environ.get("PSQL", "/opt/homebrew/opt/libpq/bin/psql")
KOTOBA_URL = os.environ.get("KOTOBA_URL", "REDACTED_USE_DATABASE_URL_ENV")
PDS_URL = os.environ.get("PDS_URL", "https://atproto.etzhayyim.com")
REPO = os.environ.get("ANIMEKA_REPO", "did:web:an1m3k4x.etzhayyim.com")
COLLECTION = "app.bsky.feed.post"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/129.0.0.0 Safari/537.36"
)


def psql_rows(sql: str) -> list[list[str]]:
    """Run psql with tab-separated unaligned output, return list of column lists."""
    try:
        out = subprocess.check_output(
            [PSQL_BIN, KOTOBA_URL, "-At", "-F", "\t", "-c", sql],
            text=True, stderr=subprocess.PIPE, timeout=30,
        )
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"psql failed: {e.stderr[:300]}\n")
        return []
    rows: list[list[str]] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        rows.append(line.split("\t"))
    return rows


def list_cutrunner_audits(since_ms: int, limit: int = 100) -> list[dict]:
    """Pull recent cutRunner audit payloads."""
    sql = (
        "SELECT ts_ms, value_json::varchar "
        "FROM vertex_repo_commit "
        f"WHERE vertex_id LIKE '%cutRunner%' AND ts_ms > {since_ms} "
        f"ORDER BY ts_ms DESC LIMIT {limit};"
    )
    out: list[dict] = []
    for row in psql_rows(sql):
        if len(row) < 2:
            continue
        try:
            ts_ms = int(row[0])
            payload = json.loads(row[1])
        except (ValueError, json.JSONDecodeError):
            continue
        out.append(
            {
                "ts_ms": ts_ms,
                "cutId": payload.get("cutId"),
                "sbCid": _normalize_cid(payload.get("sbCid")),
                "lyCid": _normalize_cid(payload.get("lyCid")),
                "kfCid": _normalize_cid(payload.get("kfCid")),
                "bgCid": _normalize_cid(payload.get("bgCid")),
                "postStatus": payload.get("postStatus"),
            }
        )
    return out


def _normalize_cid(v: object) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    if not s or s.lower() == "null":
        return None
    return s


def cut_already_posted(cut_id: str) -> bool:
    """Return True if any feed.post in REPO mentions this cutId in its text."""
    if not cut_id:
        return False
    safe = cut_id.replace("'", "''")
    sql = (
        "SELECT 1 FROM vertex_repo_record "
        f"WHERE repo='{REPO}' AND collection='{COLLECTION}' "
        f"AND value_json::varchar LIKE '%{safe}%' LIMIT 1;"
    )
    return bool(psql_rows(sql))


def build_embed(sb: str | None, ly: str | None, kf: str | None, bg: str | None) -> dict | None:
    images: list[dict] = []

    def add(alt: str, cid: str | None) -> None:
        if not cid:
            return
        images.append(
            {
                "alt": alt,
                "image": {
                    "$type": "blob",
                    "ref": {"$link": cid},
                    "mimeType": "image/png",
                    "size": 250_000,
                },
            }
        )

    add("絵コンテ", sb)
    add("レイアウト", ly)
    add("キーフレーム", kf)
    add("背景", bg)
    if not images:
        return None
    return {"$type": "app.bsky.embed.images", "images": images}


def create_post(cut_id: str, embed: dict) -> tuple[int, str]:
    record = {
        "$type": "app.bsky.feed.post",
        "text": (
            f"🎬 {cut_id} — autopilot cut (salvaged)\n"
            "12-stage BPMN pipeline (Animagine XL on RunPod L40S)"
        ),
        "createdAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "embed": embed,
    }
    body = json.dumps({"repo": REPO, "collection": COLLECTION, "record": record}).encode()
    req = urllib.request.Request(
        f"{PDS_URL}/xrpc/com.atproto.repo.createRecord",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-magatama-verified": "true",
            "User-Agent": UA,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, resp.read().decode()[:240]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:240]
    except Exception as e:  # noqa: BLE001
        return -1, f"transport error: {e}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since-hours", type=float, default=4.0, help="audit window")
    ap.add_argument("--min-cids", type=int, default=2, help="minimum CIDs to be salvageable (1..4)")
    ap.add_argument("--apply", action="store_true", help="actually post (default: dry-run)")
    ap.add_argument("--limit", type=int, default=100, help="max audits to scan")
    ap.add_argument(
        "--delay-sec", type=float, default=8.0,
        help="seconds between posts to avoid B2 SlowDown (Hummock back-pressure)",
    )
    ap.add_argument("--retry", type=int, default=3, help="retries per post on 5xx/timeout")
    args = ap.parse_args()

    since_ms = int((time.time() - args.since_hours * 3600.0) * 1000)
    audits = list_cutrunner_audits(since_ms, limit=args.limit)
    print(f"scanned {len(audits)} cutRunner audits in last {args.since_hours}h")

    salvageable: list[dict] = []
    skip_no_cids = 0
    skip_already_posted = 0
    skip_already_succeeded = 0
    for a in audits:
        cids = [a["sbCid"], a["lyCid"], a["kfCid"], a["bgCid"]]
        non_null = sum(1 for c in cids if c)
        if non_null < args.min_cids:
            skip_no_cids += 1
            continue
        if a.get("postStatus") == 200:
            skip_already_succeeded += 1
            continue
        if cut_already_posted(a["cutId"]):
            skip_already_posted += 1
            continue
        salvageable.append(a)

    print(
        f"skipped: {skip_no_cids} (cids<{args.min_cids}), "
        f"{skip_already_succeeded} (status=200), "
        f"{skip_already_posted} (post already exists)"
    )
    print(f"salvageable: {len(salvageable)}")
    for a in salvageable:
        cids = [a["sbCid"], a["lyCid"], a["kfCid"], a["bgCid"]]
        marks = "".join("S" if i == 0 and c else "L" if i == 1 and c else "K" if i == 2 and c else "B" if i == 3 and c else "-" for i, c in enumerate(cids))
        print(f"  {a['cutId']:42s} {marks} prevStatus={a.get('postStatus')}")

    if not args.apply:
        print("\n(dry-run — pass --apply to post)")
        return 0

    if not salvageable:
        return 0

    print()
    posted = 0
    failed = 0
    for idx, a in enumerate(salvageable):
        if idx > 0 and args.delay_sec > 0:
            time.sleep(args.delay_sec)
        embed = build_embed(a["sbCid"], a["lyCid"], a["kfCid"], a["bgCid"])
        if not embed:
            continue
        # Retry on transient errors (B2 SlowDown surfaces as 5xx or timeout).
        status, body = -1, ""
        for attempt in range(max(1, args.retry)):
            status, body = create_post(a["cutId"], embed)
            if 200 <= status < 300:
                break
            transient = status == -1 or 500 <= status < 600
            if not transient:
                break
            backoff = (2 ** attempt) * 4.0
            print(f"    retry {a['cutId'][:30]} attempt={attempt + 1} status={status} backoff={backoff:.0f}s")
            time.sleep(backoff)
        ok = 200 <= status < 300
        marker = "✓" if ok else "✗"
        print(f"  {marker} {a['cutId']:42s} status={status} body={body[:80]}")
        if ok:
            posted += 1
        else:
            failed += 1

    print(f"\nposted={posted} failed={failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
