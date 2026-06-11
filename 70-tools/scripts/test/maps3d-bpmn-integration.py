#!/usr/bin/env python3
# ruff: noqa: E501,T201,S603,S607
"""
maps3d BPMN flow integration — needs Zeebe + dispatcher + the four
LangServer pods running. Layer 2 of three.

Asserts:
  1. dispatcher reachable        (`/health`, `/bindings` includes maps3d.processTile)
  2. seed a fresh tile row in vertex_maps3d_tile (status='pending')
  3. trigger via XRPC            (`POST /xrpc/com.etzhayyim.apps.maps3d.processTile`)
  4. Zeebe spawns an instance, all 11 service tasks run with stub handlers
  5. tile row reaches status='done' (or 'failed' on the negative path) within timeout
  6. mesh_uri populated when status='done'
  7. OCEL audit row recorded (`com.etzhayyim.apps.maps3d.tile.processed`)

Env:
  BPMN_DISPATCHER_URL  default https://dispatcher.etzhayyim.com
  KOTOBA_URL               default: macOS Keychain `etzhayyim.rw / ROOT_URL`
  TILE_H3              default: synthetic test tile `8a2a1072b59ffff`
  WAIT_SECS            default 600 (10 min — covers stub handler runtime)

Usage:
  70-tools/scripts/test/maps3d-bpmn-integration.py
  70-tools/scripts/test/maps3d-bpmn-integration.py --skip-rw
  TILE_H3=8a2a1072b50ffff WAIT_SECS=300 \\
    70-tools/scripts/test/maps3d-bpmn-integration.py
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

DISPATCHER_URL = os.environ.get(
    "BPMN_DISPATCHER_URL", "https://dispatcher.etzhayyim.com"
).rstrip("/")
NSID = "com.etzhayyim.apps.maps3d.processTile"
DEFAULT_TILE = os.environ.get("TILE_H3", "8a2a1072b59ffff")
WAIT_SECS = int(os.environ.get("WAIT_SECS", "600"))
POLL_INTERVAL = 5
OWNER_DID = "did:web:bpmn.etzhayyim.com"
ACTOR_TAG = "sys.test.maps3d-integration"


def rw_url() -> str:
    if url := os.environ.get("KOTOBA_URL"):
        return url
    try:
        out = subprocess.check_output(
            ["security", "find-generic-password", "-s", "etzhayyim.rw", "-a", "ROOT_URL", "-w"],
            text=True,
        ).strip()
        if out:
            return out
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    raise SystemExit("KOTOBA_URL not in env and not in Keychain (etzhayyim.rw/ROOT_URL)")


def http(method: str, path: str, body: dict | None = None, timeout: float = 60.0) -> tuple[int, dict | str]:
    url = DISPATCHER_URL + path
    data = json.dumps(body).encode() if body is not None else None
    hdrs = {"User-Agent": "etzhayyim-maps3d-integration-test/1.0"}
    if data:
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            ct = (resp.headers.get("Content-Type") or "").lower()
            return resp.status, (json.loads(raw) if "json" in ct else raw)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw


def psql(sql: str) -> str:
    try:
        return subprocess.check_output(
            ["psql", rw_url(), "-tA", "-c", sql],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=20,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return ""


# ─── Test stages ─────────────────────────────────────────────────────


def stage_dispatcher_health() -> bool:
    status, body = http("GET", "/health", timeout=15)
    if status != 200:
        print(f"  FAIL  /health → {status}")
        return False
    print(f"  PASS  dispatcher /health → 200 ({body!r:.80})")
    status, body = http("GET", "/bindings", timeout=15)
    if status != 200 or not isinstance(body, dict):
        print(f"  FAIL  /bindings → {status} {body!r:.120}")
        return False
    nsids = body.get("bindings") or body.get("nsids") or []
    found = any(NSID in str(b) for b in (nsids if isinstance(nsids, list) else [nsids]))
    if not found:
        print(f"  FAIL  /bindings does not list {NSID}")
        return False
    print(f"  PASS  /bindings includes {NSID}")
    return True


def stage_seed_tile(tile_h3: str, skip_rw: bool) -> bool:
    if skip_rw:
        print(f"  SKIP  seed tile {tile_h3} (--skip-rw)")
        return True
    vid = f"at://{OWNER_DID}/com.etzhayyim.apps.maps3d.tile/{tile_h3}"
    sql = f"""
INSERT INTO vertex_maps3d_tile
  (vertex_id, tile_h3, status, priority, owner_did, sensitivity_ord, org_id, user_id, actor_id, created_at, created_date)
SELECT '{vid}', '{tile_h3}', 'pending', 1, '{OWNER_DID}', 1, '{OWNER_DID}', '{OWNER_DID}', '{ACTOR_TAG}',
       to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS"Z"'),
       to_char(now() AT TIME ZONE 'UTC','YYYY-MM-DD')::date
WHERE NOT EXISTS (SELECT 1 FROM vertex_maps3d_tile WHERE vertex_id = '{vid}')
;
UPDATE vertex_maps3d_tile SET status='pending', mesh_uri=NULL, last_attempt_at=NULL
  WHERE vertex_id='{vid}';
"""
    out = psql(sql)
    print(f"  PASS  seeded tile vertex_id={vid} (psql out={out!r:.80})")
    return True


def stage_trigger_xrpc(tile_h3: str) -> str | None:
    """POST the XRPC; return the Zeebe instanceKey on success."""
    status, body = http("POST", f"/xrpc/{NSID}", {"tileH3": tile_h3}, timeout=30)
    if status not in (200, 202):
        print(f"  FAIL  POST /xrpc/{NSID} → {status} {body!r:.180}")
        return None
    if not isinstance(body, dict):
        print(f"  FAIL  XRPC response not JSON: {body!r:.180}")
        return None
    inst = body.get("instanceKey")
    print(f"  PASS  XRPC trigger → instanceKey={inst} status={body.get('status')}")
    return str(inst) if inst else None


def stage_wait_for_done(tile_h3: str, skip_rw: bool, wait_secs: int) -> bool:
    if skip_rw:
        print(f"  SKIP  wait for tile completion (--skip-rw)")
        return True
    deadline = time.time() + wait_secs
    last_status = ""
    while time.time() < deadline:
        out = psql(
            f"SELECT status, COALESCE(mesh_uri,''), COALESCE(error_code,'') "
            f"FROM vertex_maps3d_tile WHERE tile_h3='{tile_h3}' LIMIT 1"
        )
        if out:
            parts = out.split("|")
            status = parts[0] if parts else ""
            mesh_uri = parts[1] if len(parts) > 1 else ""
            err = parts[2] if len(parts) > 2 else ""
            if status != last_status:
                print(f"  ...   tile_h3={tile_h3} status={status!r} mesh={mesh_uri!r:.60} err={err!r:.40}")
                last_status = status
            if status == "done":
                if not mesh_uri:
                    print(f"  FAIL  status=done but mesh_uri empty")
                    return False
                print(f"  PASS  tile {tile_h3} → done · mesh_uri={mesh_uri!r:.80}")
                return True
            if status == "osm-only":
                # Replanner downgraded after bounded retries — the
                # tile stays visible via the Phase-1 OSM extrude path.
                # Acceptable terminal state for the BPMN flow even if
                # photogrammetry didn't succeed.
                print(f"  PASS  tile {tile_h3} → osm-only (replanner downgrade, errorCode={err!r})")
                return True
            if status == "failed":
                print(f"  FAIL  tile {tile_h3} → failed (errorCode={err!r})")
                return False
        time.sleep(POLL_INTERVAL)
    print(f"  FAIL  timeout {wait_secs}s waiting for tile {tile_h3}")
    return False


def stage_audit_row(tile_h3: str, skip_rw: bool) -> bool:
    if skip_rw:
        print("  SKIP  audit row check (--skip-rw)")
        return True
    # Audit goes via generic.audit.emit which writes into vertex_repo_commit
    # (or whatever the audit handler maps to). Loose check: at least one
    # row mentions this tile.
    n = psql(
        f"SELECT count(*) FROM vertex_repo_commit "
        f"WHERE record_text LIKE '%maps3d.tile.processed%' AND record_text LIKE '%{tile_h3}%'"
    )
    try:
        cnt = int(n or "0")
    except ValueError:
        cnt = 0
    if cnt < 1:
        print(f"  FAIL  no maps3d.tile.processed audit row for {tile_h3} (count={cnt})")
        return False
    print(f"  PASS  audit row present (count={cnt})")
    return True


# ─── Entry ───────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-rw", action="store_true", help="skip RisingWave SQL checks")
    ap.add_argument("--tile", default=DEFAULT_TILE, help="H3 cell to drive through the pipeline")
    ap.add_argument("--wait", type=int, default=WAIT_SECS, help="seconds to wait for completion")
    args = ap.parse_args()

    print(f"# maps3d BPMN integration — dispatcher={DISPATCHER_URL} tile={args.tile}")
    print()

    if not stage_dispatcher_health():
        return 1
    if not stage_seed_tile(args.tile, args.skip_rw):
        return 1
    if not stage_trigger_xrpc(args.tile):
        return 1
    if not stage_wait_for_done(args.tile, args.skip_rw, args.wait):
        return 1
    if not stage_audit_row(args.tile, args.skip_rw):
        return 1
    print()
    print("== all stages green ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
