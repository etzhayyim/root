#!/usr/bin/env python3
"""ADR-0057 — manga BPMN actor end-to-end integration test.

Validates:
  1. Lexicons synced to vertex_mcp_tool_def (4 new tools visible)
  2. BPMN files synced to vertex_bpmn_process_def (2 new processes)
  3. /xrpc/com.etzhayyim.apps.mangaka.generateEpisode kicks BPMN
  4. Process completes within 10 min (76-panel render)
  5. vertex_mangaka has 1 work + 20 pages
  6. mv_mangaka_process_trace has ~6 audit events (one per phase)
  7. /mcp tools/list exposes the 4 new tools
  8. /xrpc/com.etzhayyim.apps.mangaka.getProcessTrace returns the same OCEL trace
  9. /xrpc/com.etzhayyim.apps.mangaka.getEpisode returns work + 20 pages

Usage:
    KOTOBA_URL=postgresql://root@localhost:4566/dev python manga-actor-integration.py
    # Or against staging:
    DISPATCHER_URL=http://dispatcher.etzhayyim.com:8080 \
    MANGAKA_URL=https://mangaka.etzhayyim.com \
    KOTOBA_URL=$KOTOBA_URL \
    python manga-actor-integration.py

Exit codes:
    0 — all checks pass
    1 — one or more checks fail (details printed)
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

import urllib.request
import urllib.error

DISPATCHER_URL = os.environ.get("DISPATCHER_URL", "http://dispatcher.etzhayyim.com:8080")
MANGAKA_URL = os.environ.get("MANGAKA_URL", "https://mangaka.etzhayyim.com")
KOTOBA_URL = os.environ.get("KOTOBA_URL", "")

EXPECTED_TOOLS = {
    "com.etzhayyim.apps.mangaka.generateEpisode",
    "com.etzhayyim.apps.mangaka.getEpisode",
    "com.etzhayyim.apps.mangaka.listEpisodes",
    "com.etzhayyim.apps.mangaka.getProcessTrace",
}
EXPECTED_BPMN = {"mangaka_generate_episode", "mangaka_episode_autopilot"}
EXPECTED_PHASES = 6  # script / panels / balloons / pages / domain / post


def http_post(url: str, payload: dict, timeout: int = 60) -> tuple[int, dict]:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-kotodama-verified": "true"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def http_get(url: str, timeout: int = 30) -> tuple[int, dict]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def pg_query(sql: str, params: tuple = ()) -> list[dict]:
    if not KOTOBA_URL:
        raise RuntimeError("KOTOBA_URL not set")
    import psycopg
    with psycopg.connect(KOTOBA_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            cols = [d.name for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


# ─── Test cases ─────────────────────────────────────────────────────────────

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, msg: str = "") -> None:
    results.append((name, ok, msg))
    status = "✅" if ok else "❌"
    print(f"  {status} {name}{': ' + msg if msg else ''}")


def test_1_mcp_registry() -> None:
    print("\n[1/9] vertex_mcp_tool_def has 4 new tools")
    if not KOTOBA_URL:
        check("mcp registry", False, "KOTOBA_URL not set — skipping DB checks")
        return
    rows = pg_query(
        "SELECT nsid FROM vertex_mcp_tool_def WHERE actor_did = 'did:web:mangaka.etzhayyim.com' AND nsid = ANY(%s)",
        (list(EXPECTED_TOOLS),),
    )
    found = {r["nsid"] for r in rows}
    missing = EXPECTED_TOOLS - found
    check("mcp tools registered", not missing, f"missing={missing}" if missing else f"all 4 present")


def test_2_bpmn_registered() -> None:
    print("\n[2/9] vertex_bpmn_process_def has 2 new processes")
    if not KOTOBA_URL:
        check("bpmn registry", False, "KOTOBA_URL not set")
        return
    rows = pg_query(
        "SELECT process_id FROM vertex_bpmn_process_def WHERE process_id = ANY(%s)",
        (list(EXPECTED_BPMN),),
    )
    found = {r["process_id"] for r in rows}
    missing = EXPECTED_BPMN - found
    check("bpmn processes registered", not missing, f"missing={missing}" if missing else "both present")


def test_3_4_5_kick_and_wait() -> tuple[str, str] | None:
    print("\n[3/9] POST /xrpc/...generateEpisode kicks BPMN")
    payload = {
        "charSlug": f"rei-ayanami-evangelion-test-{int(time.time())}",
        "charName": "Rei",
        "appearance": "blue hair red eyes pale skin school uniform",
        "genre": "shojo",
        "setting": "abandoned subway tunnel",
    }
    status, body = http_post(f"{DISPATCHER_URL}/xrpc/com.etzhayyim.apps.mangaka.generateEpisode", payload)
    if status != 200:
        check("kick generateEpisode", False, f"HTTP {status}: {body}")
        return None
    episode_uri = body.get("episodeUri") or body.get("workVertexId") or ""
    process_key = body.get("processInstanceKey", "")
    check("kick generateEpisode", bool(episode_uri), f"episodeUri={episode_uri}, processKey={process_key}")
    if not episode_uri:
        return None

    print("\n[4/9] BPMN process completes within 10 min")
    case_id = episode_uri.rsplit("/", 1)[-1]  # rkey is the case_id segment
    deadline = time.time() + 600
    final_status = None
    while time.time() < deadline:
        try:
            rows = pg_query(
                "SELECT status FROM mv_mangaka_process_case_summary WHERE case_id = %s",
                (case_id,),
            )
            if rows and rows[0]["status"] == "complete":
                final_status = "complete"
                break
            elif rows and rows[0]["status"] == "failed":
                final_status = "failed"
                break
        except Exception as e:
            print(f"    poll error: {e}")
        time.sleep(15)
    check("bpmn completes", final_status == "complete", f"status={final_status}")

    print("\n[5/9] vertex_mangaka has 1 work + 20 pages")
    if KOTOBA_URL and final_status:
        work_rows = pg_query(
            "SELECT COUNT(*) AS n FROM vertex_mangaka WHERE vertex_id = %s",
            (episode_uri,),
        )
        page_rows = pg_query(
            "SELECT COUNT(*) AS n FROM vertex_mangaka WHERE kind = 'page' AND work_id LIKE %s",
            (f"{payload['charSlug']}-%",),
        )
        wn = int(work_rows[0]["n"]) if work_rows else 0
        pn = int(page_rows[0]["n"]) if page_rows else 0
        check("work + pages", wn == 1 and pn == 20, f"work={wn}, pages={pn}")
    return episode_uri, case_id


def test_6_ocel_trace(case_id: str) -> None:
    print("\n[6/9] mv_mangaka_process_trace has ~6 audit events")
    if not KOTOBA_URL:
        check("ocel trace", False, "KOTOBA_URL not set")
        return
    rows = pg_query(
        "SELECT activity, status FROM mv_mangaka_process_trace WHERE case_id = %s ORDER BY ts_ms",
        (case_id,),
    )
    activities = [r["activity"] for r in rows]
    check("ocel events count", len(rows) >= EXPECTED_PHASES,
          f"got {len(rows)} events: {activities}")


def test_7_mcp_tools_list() -> None:
    print("\n[7/9] /mcp tools/list exposes the 4 new tools")
    status, body = http_post(
        f"{MANGAKA_URL}/mcp",
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
    )
    if status != 200:
        check("mcp tools/list", False, f"HTTP {status}: {body}")
        return
    tools = {t.get("name") for t in body.get("result", {}).get("tools", [])}
    missing = EXPECTED_TOOLS - tools
    check("mcp tools/list 4 new tools", not missing,
          f"missing={missing}" if missing else f"all 4 visible")


def test_8_get_process_trace(episode_uri: str) -> None:
    print("\n[8/9] /xrpc/...getProcessTrace returns OCEL trace")
    status, body = http_post(
        f"{MANGAKA_URL}/xrpc/com.etzhayyim.apps.mangaka.getProcessTrace",
        {"episodeUri": episode_uri},
    )
    if status != 200:
        check("getProcessTrace", False, f"HTTP {status}")
        return
    events = body.get("events", [])
    summary = body.get("summary", {})
    check("getProcessTrace events", len(events) >= EXPECTED_PHASES,
          f"events={len(events)}, summary.status={summary.get('status')}")


def test_9_get_episode(episode_uri: str) -> None:
    print("\n[9/9] /xrpc/...getEpisode returns work + 20 pages")
    status, body = http_post(
        f"{MANGAKA_URL}/xrpc/com.etzhayyim.apps.mangaka.getEpisode",
        {"episodeUri": episode_uri},
    )
    if status != 200:
        check("getEpisode", False, f"HTTP {status}")
        return
    work = body.get("work", {})
    pages = body.get("pages", [])
    check("getEpisode work + 20 pages",
          bool(work) and len(pages) == 20,
          f"work={bool(work)}, pages={len(pages)}")


# ─── Run ────────────────────────────────────────────────────────────────────

def main() -> int:
    print(f"DISPATCHER_URL={DISPATCHER_URL}")
    print(f"MANGAKA_URL={MANGAKA_URL}")
    print(f"KOTOBA_URL={'<set>' if KOTOBA_URL else '<unset>'}")

    test_1_mcp_registry()
    test_2_bpmn_registered()
    kick_result = test_3_4_5_kick_and_wait()
    if kick_result:
        episode_uri, case_id = kick_result
        test_6_ocel_trace(case_id)
        test_7_mcp_tools_list()
        test_8_get_process_trace(episode_uri)
        test_9_get_episode(episode_uri)
    else:
        print("[6-9/9] skipped — no episode kicked")
        for n in ("ocel trace", "mcp tools/list 4 new tools", "getProcessTrace", "getEpisode work + 20 pages"):
            check(n, False, "skipped")

    print()
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"=== {passed}/{total} checks passed ===")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
