#!/usr/bin/env python3
"""GeoNames bulk dumper — resident worker.

POST /trigger downloads geonames.org/export/dump/allCountries.zip (~470MB
compressed, ~12M TSV rows), parses each row into a vertex_spatial entry,
writes parquet shards to B2, INSERTs to RisingWave live (per-shard).

Schema: geonameid is unique → vertex_id deterministic, no collision risk.

ENV:
  DATABASE_URL, B2_ACCESS_KEY_ID, B2_SECRET_ACCESS_KEY,
  B2_ENDPOINT, B2_BUCKET, B2_PREFIX (default maps-bulk-ingest/geonames)
  GEONAMES_DUMP_URL (default https://download.geonames.org/export/dump/allCountries.zip)
  GEONAMES_DATASET  (default cities1000 — alternatives: allCountries, cities500, cities5000, cities15000)
  SHARD_ROWS, FLUSH_INTERVAL_SEC, PORT (defaults 10000, 60, 8080)
"""
from __future__ import annotations

import concurrent.futures
import io
import json
import logging
import os
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
from threading import Lock, Thread

import boto3
import psycopg2
import pyarrow as pa
import pyarrow.parquet as pq

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("geonames_dumper")

DATABASE_URL = os.environ.get("DATABASE_URL")
B2_BUCKET = os.environ.get("B2_BUCKET", "ai-gftd-nats")
B2_PREFIX = os.environ.get("B2_PREFIX", "maps-bulk-ingest/geonames")
B2_ENDPOINT = os.environ.get("B2_ENDPOINT", "https://s3.us-west-004.backblazeb2.com")
DATASET = os.environ.get("GEONAMES_DATASET", "cities1000")
DUMP_URL = os.environ.get(
    "GEONAMES_DUMP_URL",
    f"https://download.geonames.org/export/dump/{DATASET}.zip",
)
PORT = int(os.environ.get("PORT", "8080"))
SHARD_ROWS = int(os.environ.get("SHARD_ROWS", "10000"))
FLUSH_INTERVAL_SEC = float(os.environ.get("FLUSH_INTERVAL_SEC", "60"))
_flush_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)

_state = {
    "running": False,
    "started_at": None,
    "rows_written": 0,
    "current_geonameid": None,
    "error": None,
    "completed_at": None,
}
_lock = Lock()


def _b2():
    return boto3.client(
        "s3",
        endpoint_url=B2_ENDPOINT,
        aws_access_key_id=os.environ["B2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["B2_SECRET_ACCESS_KEY"],
    )


def _is_done(dump_id: str, key: str) -> bool:
    try:
        _b2().head_object(Bucket=B2_BUCKET, Key=f"{B2_PREFIX}/{dump_id}/.done/{key}")
        return True
    except Exception:
        return False


def _mark_done(dump_id: str, key: str) -> None:
    try:
        _b2().put_object(
            Bucket=B2_BUCKET,
            Key=f"{B2_PREFIX}/{dump_id}/.done/{key}",
            Body=datetime.now(timezone.utc).isoformat().encode(),
        )
    except Exception as e:
        log.warning("failed to mark %s done: %s", key, e)


def _stream_zip_tsv(url: str):
    """Download zip via curl, extract first .txt entry, yield TSV rows."""
    log.info("opening %s via curl --retry-all-errors", url)
    cmd = [
        "curl", "--silent", "--location",
        "--retry", "20", "--retry-max-time", "1800", "--retry-all-errors",
        "--connect-timeout", "30",
        url, "-o", "/tmp/geonames.zip",
    ]
    rc = subprocess.run(cmd, check=False).returncode
    if rc != 0:
        raise RuntimeError(f"curl exit {rc}")
    with zipfile.ZipFile("/tmp/geonames.zip") as zf:
        names = [n for n in zf.namelist() if n.endswith(".txt")]
        if not names:
            raise RuntimeError(f"no .txt in zip: {zf.namelist()}")
        with zf.open(names[0]) as f:
            for raw in io.TextIOWrapper(f, encoding="utf-8", errors="replace"):
                fields = raw.rstrip("\n").split("\t")
                if len(fields) >= 19:
                    yield fields


def _row(fields: list[str]) -> dict | None:
    try:
        gid = fields[0]
        name = fields[1][:200]
        lat = float(fields[4])
        lon = float(fields[5])
        fcl = fields[6]   # feature class (P=populated, A=admin, T=mountain, H=hydro, etc.)
        fcode = fields[7]  # feature code (PPL, PPLA, ADM1, …)
        country = fields[8]
        population = fields[14]
    except (ValueError, IndexError):
        return None
    if lat == 0 and lon == 0:
        return None
    if not gid or not name:
        return None
    label = _classify_geonames(fcl, fcode)
    return {
        "vertex_id": f"at://did:web:maps.etzhayyim.com/ai.gftd.apps.maps.spot/geonames-{gid}",
        "rkey": f"geonames-{gid}",
        "repo": "did:web:maps.etzhayyim.com",
        "label": label,
        "did": "did:web:maps.etzhayyim.com",
        "collection": "ai.gftd.apps.maps.spot",
        "name": name,
        "lat": lat,
        "lng": lon,
        "source_did": "did:web:maps.etzhayyim.com:registry:geonames:bulk",
        "category": f"geonames-{fcl.lower() or 'other'}",
        "description": (f"{fcode} pop={population} cc={country}")[:500],
        "country": country[:8] if country else None,
        "owner_did": "did:web:maps.etzhayyim.com",
        "sensitivity_ord": 0,
        "created_date": datetime.now(timezone.utc).date().isoformat(),
    }


_FCL_LABEL = {
    "P": "Place",          # populated places
    "A": "AdminArea",      # admin boundaries
    "T": "Mountain",       # mountains, hills
    "H": "River",          # streams, lakes, sea
    "L": "Spot",           # parks, areas
    "R": "Road",           # roads, railroads
    "S": "Building",       # spots, buildings, farms
    "U": "Spot",           # underwater
    "V": "Spot",           # forest, heath
}


def _classify_geonames(fcl: str, fcode: str) -> str:
    return _FCL_LABEL.get(fcl, "Spot")


def _flush_shard(rows: list[dict], dump_id: str, shard_idx: int) -> str:
    if not rows:
        return ""
    table = pa.Table.from_pylist(rows)
    buf = BytesIO()
    pq.write_table(table, buf, compression="zstd")
    buf.seek(0)
    key = f"{B2_PREFIX}/{dump_id}/shard-{shard_idx:05d}.parquet"
    _b2().put_object(Bucket=B2_BUCKET, Key=key, Body=buf.getvalue())
    log.info("wrote shard %s rows=%d", key, len(rows))
    return key


def _insert_rows_into_rw(rows: list[dict], batch_size: int = 1000) -> int:
    if not rows:
        return 0
    total = 0
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    try:
        cur = conn.cursor()
        cols = list(rows[0].keys())
        for i in range(0, len(rows), batch_size):
            chunk = rows[i : i + batch_size]
            placeholders = ", ".join("(" + ", ".join(["%s"] * len(cols)) + ")" for _ in chunk)
            sql = f"INSERT INTO vertex_spatial ({', '.join(cols)}) VALUES {placeholders}"
            params = [r[c] for r in chunk for c in cols]
            try:
                cur.execute(sql, params)
                conn.commit()
                total += len(chunk)
            except Exception as e:
                conn.rollback()
                log.warning("batch insert failed (chunk %d-%d): %s", i, i + len(chunk), e)
    finally:
        conn.close()
    return total


def _run_dump():
    dump_id = datetime.now(timezone.utc).strftime("%Y%m%d")
    with _lock:
        if _state["running"]:
            log.warning("dump already running")
            return
        _state.update(
            running=True,
            started_at=datetime.now(timezone.utc).isoformat(),
            rows_written=0,
            current_geonameid=None,
            error=None,
            completed_at=None,
        )
    try:
        if _is_done(dump_id, f"geonames-{DATASET}"):
            log.info("[%s] skip — already done in dump %s", DATASET, dump_id)
            with _lock:
                _state["completed_at"] = datetime.now(timezone.utc).isoformat()
            return

        log.info("starting dump %s dataset=%s shard=%d flush_sec=%.0f", dump_id, DATASET, SHARD_ROWS, FLUSH_INTERVAL_SEC)
        shard_rows: list[dict] = []
        shard_idx = 0
        rw_total = 0
        last_flush = time.time()
        for fields in _stream_zip_tsv(DUMP_URL):
            row = _row(fields)
            if not row:
                continue
            shard_rows.append(row)
            with _lock:
                _state["current_geonameid"] = fields[0]
                _state["rows_written"] = rw_total + len(shard_rows)
            should_flush = (
                len(shard_rows) >= SHARD_ROWS
                or (shard_rows and time.time() - last_flush >= FLUSH_INTERVAL_SEC)
            )
            if should_flush:
                fut_b2 = _flush_pool.submit(_flush_shard, list(shard_rows), dump_id, shard_idx)
                inserted = _insert_rows_into_rw(shard_rows)
                fut_b2.result()
                rw_total += inserted
                log.info("shard %d: r2=%d rw=%d cum=%d", shard_idx, len(shard_rows), inserted, rw_total)
                shard_rows.clear()
                shard_idx += 1
                last_flush = time.time()
                with _lock:
                    _state["rows_written"] = rw_total
        if shard_rows:
            fut_b2 = _flush_pool.submit(_flush_shard, list(shard_rows), dump_id, shard_idx)
            inserted = _insert_rows_into_rw(shard_rows)
            fut_b2.result()
            rw_total += inserted
            log.info("final shard %d: r2=%d rw=%d cum=%d", shard_idx, len(shard_rows), inserted, rw_total)

        log.info("dump %s complete, rw_total=%d", dump_id, rw_total)
        with _lock:
            _state["rows_written"] = rw_total
            _state["completed_at"] = datetime.now(timezone.utc).isoformat()
        _mark_done(dump_id, f"geonames-{DATASET}")
    except Exception as e:
        log.exception("dump failed")
        with _lock:
            _state["error"] = str(e)
    finally:
        with _lock:
            _state["running"] = False


class Handler(BaseHTTPRequestHandler):
    def _json(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def do_POST(self):  # noqa: N802
        if self.path == "/trigger":
            with _lock:
                if _state["running"]:
                    return self._json(409, {"error": "running", "state": _state})
            Thread(target=_run_dump, daemon=True).start()
            return self._json(202, {"accepted": True, "started_at": datetime.now(timezone.utc).isoformat()})
        return self._json(404, {"error": "not found"})

    def do_GET(self):  # noqa: N802
        if self.path == "/status":
            with _lock:
                return self._json(200, dict(_state))
        if self.path == "/health":
            return self._json(200, {"status": "ok"})
        return self._json(404, {"error": "not found"})

    def log_message(self, *args):
        pass


def main():
    if not DATABASE_URL:
        raise SystemExit("DATABASE_URL required")
    log.info("listening on :%d (dataset=%s url=%s)", PORT, DATASET, DUMP_URL)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
