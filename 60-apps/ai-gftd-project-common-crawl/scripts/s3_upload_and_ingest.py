#!/usr/bin/env python3
"""Upload Parquet to S3 + RisingWave ingest (steps 1-2-3).

Watches parquet-rs/ for new files, uploads to S3, then bulk INSERTs into RW.
Can run while cc-phase3 is still producing Parquet files.

Usage:
  # After cc-phase3 completes (or while running for incremental upload):
  python3 scripts/s3_upload_and_ingest.py

  # Upload only (no RW ingest):
  python3 scripts/s3_upload_and_ingest.py --upload-only

  # Ingest only (Parquet already on S3):
  python3 scripts/s3_upload_and_ingest.py --ingest-only
"""

import argparse
import logging
import os
import time

import boto3
import psycopg2
from botocore.config import Config

# ── Config ──

PARQUET_DIR = os.environ.get("CC_PARQUET_DIR", "/Volumes/251220/CC/2603/parquet-rs")
S3_BUCKET = "kagami-graphar"
S3_PREFIX = "cc-parquet"
S3_ENDPOINT = "https://sg-sin-1.linodeobjects.com"
S3_REGION = "sg-sin-1"
S3_ACCESS = os.environ.get("S3_ACCESS_KEY", "ME8Q1FVL9HOPVM9G5KB8")
S3_SECRET = os.environ.get("S3_SECRET_KEY", "1OW7osVoqJaD39Z0LANwrsT8Dsr2vPv0YMcwbKUO")

RW_HOST = os.environ.get("RW_HOST", "45.32.79.245")
RW_PORT = int(os.environ.get("RW_PORT", "4566"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def get_s3():
    return boto3.client("s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS,
        aws_secret_access_key=S3_SECRET,
        region_name=S3_REGION,
        config=Config(request_checksum_calculation="when_required"),
    )


def get_rw():
    return psycopg2.connect(host=RW_HOST, port=RW_PORT, user="root", dbname="dev", connect_timeout=10)


# ── Step 1: S3 Upload ──

def upload_parquet(s3):
    """Upload all Parquet files to S3, skipping already-uploaded."""
    # List existing S3 keys
    existing = set()
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=f"{S3_PREFIX}/"):
        for obj in page.get("Contents", []):
            existing.add(obj["Key"].split("/")[-1])

    # Upload new files
    uploaded = 0
    skipped = 0
    files = sorted(f for f in os.listdir(PARQUET_DIR) if f.endswith(".parquet"))
    for f in files:
        if f in existing:
            skipped += 1
            continue
        path = os.path.join(PARQUET_DIR, f)
        key = f"{S3_PREFIX}/{f}"
        s3.upload_file(path, S3_BUCKET, key)
        uploaded += 1
        if uploaded % 100 == 0:
            log.info(f"  Uploaded {uploaded}/{len(files)} ({skipped} skipped)")

    log.info(f"S3 upload: {uploaded} new, {skipped} skipped, {len(files)} total")
    return uploaded


# ── Step 2: RW Ingest ──

S3_CONF = f"""s3.region_name='{S3_REGION}',
    s3.bucket_name='{S3_BUCKET}',
    s3.credentials.access='{S3_ACCESS}',
    s3.credentials.secret='{S3_SECRET}',
    s3.endpoint_url='{S3_ENDPOINT}'"""

SOURCES = [
    ("cc_pages_s3", """rkey VARCHAR, url VARCHAR, domain VARCHAR, title VARCHAR,
    description VARCHAR, language VARCHAR, content_type VARCHAR,
    status_code VARCHAR, outlink_count BIGINT, crawl VARCHAR,
    ip_address VARCHAR, og_image VARCHAR, robots VARCHAR,
    content_hash VARCHAR, previous_content_hash VARCHAR,
    version BIGINT, crawled_at VARCHAR,
    vertex_id VARCHAR, _seq BIGINT, created_date DATE,
    sensitivity_ord BIGINT, owner_did VARCHAR""",
     "cc-parquet/*_pages.parquet"),

    ("cc_links_s3", """label VARCHAR, anchor_text VARCHAR,
    edge_id VARCHAR, src_vid VARCHAR, dst_vid VARCHAR,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR""",
     "cc-parquet/*_links.parquet"),

    ("cc_dlinks_s3", """label VARCHAR, count BIGINT,
    edge_id VARCHAR, src_vid VARCHAR, dst_vid VARCHAR,
    _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR""",
     "cc-parquet/*_dlinks.parquet"),
]


def create_sources(conn):
    """Create or recreate S3 sources."""
    cur = conn.cursor()
    for name, cols, pattern in SOURCES:
        cur.execute(f"DROP SOURCE IF EXISTS {name} CASCADE")
        conn.commit()
        cur.execute(f"""CREATE SOURCE {name} ({cols})
            WITH (connector='s3', match_pattern='{pattern}', {S3_CONF})
            FORMAT PLAIN ENCODE PARQUET""")
        conn.commit()
        log.info(f"Source {name}: created")


def ingest_from_sources(conn):
    """INSERT INTO tables FROM S3 sources."""
    cur = conn.cursor()

    inserts = [
        ("vertex_page", "INSERT INTO vertex_page SELECT * FROM cc_pages_s3"),
        ("edge_links_to", "INSERT INTO edge_links_to SELECT * FROM cc_links_s3"),
        ("edge_links_to_domain", "INSERT INTO edge_links_to_domain SELECT * FROM cc_dlinks_s3"),
    ]

    for table, sql in inserts:
        t0 = time.time()
        try:
            cur.execute(sql)
            conn.commit()
            log.info(f"  {table}: {time.time()-t0:.1f}s")
        except Exception as e:
            log.error(f"  {table}: {str(e).split(chr(10))[0][:120]}")
            conn.rollback()


# ── Step 3: Populate vertex_domain ──

def populate_domains(conn):
    """Populate vertex_domain from DISTINCT vertex_page.domain."""
    cur = conn.cursor()
    try:
        # Clear existing CC domains
        cur.execute("DELETE FROM vertex_domain WHERE 1=1")
        conn.commit()

        cur.execute("""
            INSERT INTO vertex_domain (vertex_id, domain, did, handle, display_name,
                                       topics, performer_type, status,
                                       _seq, sensitivity_ord, created_date, owner_did)
            SELECT
                p.domain, p.domain,
                'did:web:site.gftd.ai:' || REPLACE(p.domain, '.', '-'),
                'site.gftd.ai:' || REPLACE(p.domain, '.', '-'),
                p.domain, NULL::VARCHAR, 'service', 'active',
                0::BIGINT, 0::BIGINT, NULL::DATE, NULL::VARCHAR
            FROM (SELECT DISTINCT domain FROM vertex_page
                  WHERE domain IS NOT NULL AND domain != '') p
        """)
        conn.commit()

        cur.execute("SELECT COUNT(*) FROM vertex_domain")
        count = cur.fetchone()[0]
        log.info(f"vertex_domain: {count:,} rows populated")
    except Exception as e:
        log.error(f"populate_domains: {e}")
        conn.rollback()


def verify(conn):
    """Print final counts."""
    cur = conn.cursor()
    for t in ["vertex_page", "edge_links_to", "edge_links_to_domain", "vertex_domain"]:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        log.info(f"  {t}: {cur.fetchone()[0]:,}")

    cur.execute("SELECT COUNT(*) FROM mv_cc_domain_page_count")
    log.info(f"  mv_cc_domain_page_count: {cur.fetchone()[0]:,}")

    cur.execute("SELECT domain, page_count FROM mv_cc_domain_page_count ORDER BY page_count DESC LIMIT 5")
    log.info("  Top domains:")
    for r in cur.fetchall():
        log.info(f"    {r[0]}: {r[1]:,}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--upload-only", action="store_true")
    p.add_argument("--ingest-only", action="store_true")
    args = p.parse_args()

    t0 = time.time()

    if not args.ingest_only:
        log.info("=== Step 1: S3 Upload ===")
        s3 = get_s3()
        upload_parquet(s3)

    if not args.upload_only:
        log.info("=== Step 2: RW Ingest ===")
        conn = get_rw()
        create_sources(conn)
        time.sleep(3)  # wait for source file discovery
        ingest_from_sources(conn)

        log.info("=== Step 3: Populate vertex_domain ===")
        populate_domains(conn)

        log.info("=== Verify ===")
        verify(conn)
        conn.close()

    log.info(f"Done in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
