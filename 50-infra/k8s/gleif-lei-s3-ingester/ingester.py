#!/usr/bin/env python3
"""
GLEIF LEI S3 bulk ingester.

Two phases per run:
  Phase 1 — download: fetch GLEIF Golden Copy ZIP, cache to B2 under
             b2://{B2_BUCKET}/gleif/lei2.0/{publish_date}/lei2.0-L1-full.zip
  Phase 2 — ingest: stream ZIP from B2 local temp, iterparse XML,
             batch INSERT into vertex_open_lei_entity (WHERE NOT EXISTS guard)

Progress is tracked per-run in vertex_open_lei_s3_run.  Shard-level
progress uses vertex_open_lei_gleif_shard with dataset_kind='lei-cdf-s3'.
"""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import time
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import boto3
from kotoba_datomic import get_kotoba_client

# ── config ────────────────────────────────────────────────────────────────────
B2_BUCKET = os.environ.get("B2_BUCKET", "etzhayyim-nats")
B2_ENDPOINT = os.environ.get("B2_ENDPOINT", "https://s3.us-west-004.backblazeb2.com")
B2_REGION = os.environ.get("B2_REGION", "us-west-004")
AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]

BATCH_SIZE = max(50, int(os.environ.get("BATCH_SIZE", "500")))
MAX_RECORDS = int(os.environ.get("MAX_RECORDS", "0"))  # 0 = unlimited
DOWNLOAD_DIR = Path(os.environ.get("DOWNLOAD_DIR", "/tmp/gleif"))
GLEIF_GOLDEN_COPY_API = os.environ.get(
    "GLEIF_GOLDEN_COPY_API",
    "https://goldencopy.gleif.org/api/v2/golden-copies/publishes/latest",
)
FETCH_TIMEOUT = int(os.environ.get("FETCH_TIMEOUT", "120"))
USER_AGENT = "etzhayyim-gleif-s3-ingester/1.0 (+https://etzhayyim.com)"

RW_HEALTH_GATE = os.environ.get("RW_HEALTH_GATE", "true").lower() == "true"
RW_MIN_COMPUTE_READY = int(os.environ.get("RW_MIN_COMPUTE_READY", "2"))
RW_MIN_COMPUTE_AGE_SECONDS = int(os.environ.get("RW_MIN_COMPUTE_AGE_SECONDS", "1800"))

DATASET_KIND = "lei-cdf-s3"
OWNER_DID = "did:web:open-lei.etzhayyim.com"
ACTOR_ID = "sys.k8s.open-lei.gleif-s3-ingester"

# ── helpers ────────────────────────────────────────────────────────────────────
def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def strip_ns(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def log(obj: dict[str, Any]) -> None:
    print(json.dumps({**obj, "ts": utc_now()}, sort_keys=True), flush=True)


# ── RW health gate ─────────────────────────────────────────────────────────────
def check_rw_health(client: Any) -> None:
    if not RW_HEALTH_GATE:
        return
    try:
        client.q('[:find ?e :where [?e :db/ident :db/ident]]')
        log({"event": "kotoba_health_ok"})
    except Exception as exc:
        raise RuntimeError(f"kotoba health gate failed: {exc}")


# ── GLEIF Golden Copy API ──────────────────────────────────────────────────────
def get_golden_copy_meta() -> tuple[str, str, int]:
    req = urllib.request.Request(
        GLEIF_GOLDEN_COPY_API,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as resp:
        payload = json.loads(resp.read())
    data = payload["data"]
    # publish_date is "2026-05-07 08:00:00" — take date portion only
    publish_date: str = data["publish_date"].split(" ")[0]
    xml_file: dict = data["lei2"]["full_file"]["xml"]
    download_url: str = xml_file["url"]
    size: int = xml_file.get("size", 0)
    return publish_date, download_url, size


# ── B2 helpers ─────────────────────────────────────────────────────────────────
def make_s3() -> Any:
    return boto3.client(
        "s3",
        endpoint_url=B2_ENDPOINT,
        region_name=B2_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )


def b2_key(publish_date: str) -> str:
    return f"gleif/lei2.0/{publish_date}/lei2.0-L1-full.zip"


def b2_exists(s3: Any, key: str) -> bool:
    try:
        s3.head_object(Bucket=B2_BUCKET, Key=key)
        return True
    except s3.exceptions.ClientError:
        return False
    except Exception:
        return False


def download_to_b2(s3: Any, download_url: str, key: str, expected_size: int) -> Path:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    local_path = DOWNLOAD_DIR / "lei2.0-L1-full.zip"

    log({"event": "download_start", "url": download_url, "expected_bytes": expected_size})
    req = urllib.request.Request(download_url, headers={"User-Agent": USER_AGENT})
    total = 0
    chunk_size = 4 * 1024 * 1024  # 4 MiB chunks
    with urllib.request.urlopen(req, timeout=600) as resp, open(local_path, "wb") as f:
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
            total += len(chunk)

    log({"event": "download_done", "bytes": total, "path": str(local_path)})

    log({"event": "b2_upload_start", "key": key, "bytes": total})
    s3.upload_file(str(local_path), B2_BUCKET, key)
    log({"event": "b2_upload_done", "key": key})

    return local_path


def download_from_b2(s3: Any, key: str) -> Path:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    local_path = DOWNLOAD_DIR / "lei2.0-L1-full.zip"
    log({"event": "b2_download_start", "key": key})
    s3.download_file(B2_BUCKET, key, str(local_path))
    log({"event": "b2_download_done", "path": str(local_path)})
    return local_path


# ── XML parsing ────────────────────────────────────────────────────────────────
def _text(elem: ET.Element, *path: str) -> str:
    for tag in path:
        child = elem.find(f"{{*}}{tag}")
        if child is None:
            child = elem.find(tag)
        if child is not None:
            elem = child
        else:
            return ""
    return (elem.text or "").strip()


def parse_lei_records(zip_path: Path) -> Iterator[dict[str, Any]]:
    zf = zipfile.ZipFile(zip_path, "r")
    names = [n for n in zf.namelist() if n.endswith(".xml") and "__MACOSX" not in n]
    if not names:
        names = [n for n in zf.namelist() if not n.endswith("/")]

    for name in names:
        log({"event": "xml_parse_start", "file": name})
        with zf.open(name) as fh:
            context = ET.iterparse(fh, events=("end",))
            for event, elem in context:
                local = strip_ns(elem.tag)
                if local != "LEIRecord":
                    continue
                lei = _text(elem, "LEI")
                if not lei:
                    elem.clear()
                    continue

                entity = elem.find("{*}Entity") or elem.find("Entity")
                reg = elem.find("{*}Registration") or elem.find("Registration")

                legal_name = ""
                country = ""
                legal_form = ""
                registration_authority = ""
                entity_status = ""
                if entity is not None:
                    legal_name = _text(entity, "LegalName")
                    country = _text(entity, "LegalAddress", "Country") or _text(entity, "LegalJurisdiction")
                    lf = entity.find("{*}LegalForm") or entity.find("LegalForm")
                    if lf is not None:
                        legal_form = _text(lf, "EntityLegalFormCode")
                    ra = entity.find("{*}RegistrationAuthority") or entity.find("RegistrationAuthority")
                    if ra is not None:
                        registration_authority = _text(ra, "RegistrationAuthorityID")
                    entity_status = _text(entity, "EntityStatus")

                registration_status = "UNKNOWN"
                issued_at = None
                next_renewal_at = None
                if reg is not None:
                    registration_status = _text(reg, "RegistrationStatus") or "UNKNOWN"
                    issued_at = _text(reg, "InitialRegistrationDate") or None
                    next_renewal_at = _text(reg, "NextRenewalDate") or None

                yield {
                    "vertex_id": f"at://did:web:open-lei.etzhayyim.com/com.etzhayyim.apps.openLei.entity/{lei}",
                    "lei": lei,
                    "legal_name": legal_name or lei,
                    "country": country[:64] if country else "",
                    "legal_form": legal_form[:64] if legal_form else "",
                    "registration_authority": registration_authority[:128] if registration_authority else "",
                    "registration_status": registration_status[:64],
                    "issued_at": issued_at,
                    "next_renewal_at": next_renewal_at,
                    "status": "active" if registration_status == "ISSUED" else "lapsed",
                    "created_at": utc_now(),
                    "created_date": utc_date(),
                    "owner_did": OWNER_DID,
                    "sensitivity_ord": 1,
                    "org_id": OWNER_DID,
                    "user_id": OWNER_DID,
                    "actor_id": ACTOR_ID,
                }
                elem.clear()

    zf.close()


# ── DB writes ──────────────────────────────────────────────────────────────────
_INSERT_SQL = """
INSERT INTO vertex_open_lei_entity (
  vertex_id, created_date, sensitivity_ord, owner_did,
  lei, legal_name, country, legal_form, registration_authority,
  registration_status, issued_at, next_renewal_at, status,
  created_at, org_id, user_id, actor_id
)
SELECT
  v.vertex_id, CAST(v.created_date AS DATE), v.sensitivity_ord, v.owner_did,
  v.lei, v.legal_name, v.country, v.legal_form, v.registration_authority,
  v.registration_status, v.issued_at, v.next_renewal_at, v.status,
  v.created_at, v.org_id, v.user_id, v.actor_id
FROM (VALUES {placeholders}) AS v(
  vertex_id, created_date, sensitivity_ord, owner_did,
  lei, legal_name, country, legal_form, registration_authority,
  registration_status, issued_at, next_renewal_at, status,
  created_at, org_id, user_id, actor_id
)
WHERE NOT EXISTS (
  SELECT 1 FROM vertex_open_lei_entity e WHERE e.vertex_id = v.vertex_id
)
"""

_COLS = [
    "vertex_id", "created_date", "sensitivity_ord", "owner_did",
    "lei", "legal_name", "country", "legal_form", "registration_authority",
    "registration_status", "issued_at", "next_renewal_at", "status",
    "created_at", "org_id", "user_id", "actor_id",
]


def batch_insert(client: Any, rows: list[dict[str, Any]]) -> int:
    rows = [r for r in rows if r.get("lei")]
    if not rows:
        return 0
    client.insert_rows("vertex_open_lei_record", rows)
    return len(rows)


def upsert_s3_run(
    client: Any,
    *,
    publish_date: str,
    key: str,
    status: str,
    records_read: int,
    records_written: int,
    error_msg: str = "",
) -> None:
    vid = f"at://did:web:open-lei.etzhayyim.com/com.etzhayyim.apps.openLei.s3Run/{publish_date}"
    client.insert_row("vertex_open_lei_s3_run", {
        "vertex_id": vid,
        "created_date": utc_date(),
        "owner_did": OWNER_DID,
        "publish_date": publish_date,
        "b2_bucket": B2_BUCKET,
        "b2_key": key,
        "records_read": records_read,
        "records_written": records_written,
        "run_status": status,
        "error_msg": error_msg[:512] if error_msg else "",
        "started_at": utc_now(),
        "finished_at": utc_now(),
        "created_at": utc_now(),
        "org_id": OWNER_DID,
        "user_id": OWNER_DID,
        "actor_id": ACTOR_ID,
    })


# ── main ───────────────────────────────────────────────────────────────────────
def run() -> dict[str, Any]:
    s3 = make_s3()
    client = get_kotoba_client()

    check_rw_health(client)

    # Phase 1: resolve publish date + ensure ZIP is in B2
    log({"event": "golden_copy_query", "url": GLEIF_GOLDEN_COPY_API})
    publish_date, download_url, expected_size = get_golden_copy_meta()
    key = b2_key(publish_date)
    log({"event": "golden_copy_meta", "publishDate": publish_date, "key": key, "bytes": expected_size})

    if b2_exists(s3, key):
        log({"event": "b2_cache_hit", "key": key})
        zip_path = download_from_b2(s3, key)
    else:
        log({"event": "b2_cache_miss", "key": key})
        zip_path = download_to_b2(s3, download_url, key, expected_size)

    # Phase 2: ingest
    total_read = 0
    total_written = 0
    batch: list[dict[str, Any]] = []

    for record in parse_lei_records(zip_path):
        batch.append(record)
        total_read += 1

        if len(batch) >= BATCH_SIZE:
            written = batch_insert(client, batch)
            total_written += written
            log({"event": "batch", "read": total_read, "written": total_written})
            batch = []

        if MAX_RECORDS and total_read >= MAX_RECORDS:
            break

    # flush tail
    if batch:
        written = batch_insert(client, batch)
        total_written += written

    upsert_s3_run(
        client,
        publish_date=publish_date,
        key=key,
        status="succeeded",
        records_read=total_read,
        records_written=total_written,
    )

    return {
        "ok": True,
        "publishDate": publish_date,
        "b2Key": key,
        "recordsRead": total_read,
        "recordsWritten": total_written,
    }


def main() -> None:
    try:
        result = run()
        print(json.dumps(result, sort_keys=True), flush=True)
    except Exception as exc:
        print(
            json.dumps({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, sort_keys=True),
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
