#!/usr/bin/env python3
"""Chunked S3 → RisingWave INSERT to avoid OOM.

Uses INCLUDE file AS source_file + WHERE filter on batch_id range.
Each chunk = 500 batches (~1.5GB), commit between chunks.
"""

import argparse
import logging
import time

import psycopg2

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

RW_HOST = "45.32.79.245"
RW_PORT = 4566

S3_CONF = """s3.region_name='sg-sin-1', s3.bucket_name='kagami-graphar',
    s3.credentials.access='ME8Q1FVL9HOPVM9G5KB8',
    s3.credentials.secret='1OW7osVoqJaD39Z0LANwrsT8Dsr2vPv0YMcwbKUO',
    s3.endpoint_url='https://sg-sin-1.linodeobjects.com'"""


def get_conn():
    return psycopg2.connect(host=RW_HOST, port=RW_PORT, user="root", dbname="dev", connect_timeout=30)


def recreate_sources(conn):
    """Drop and recreate sources with INCLUDE file column."""
    cur = conn.cursor()

    sources = [
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

    for name, cols, pattern in sources:
        cur.execute(f"DROP SOURCE IF EXISTS {name} CASCADE")
        conn.commit()
        cur.execute(f"""CREATE SOURCE {name} ({cols})
            INCLUDE file AS source_file
            WITH (connector='s3', match_pattern='{pattern}', {S3_CONF})
            FORMAT PLAIN ENCODE PARQUET""")
        conn.commit()
        log.info(f"  Source {name}: created with INCLUDE file")


def truncate_tables(conn):
    cur = conn.cursor()
    for t in ["vertex_page", "edge_links_to", "edge_links_to_domain"]:
        cur.execute(f"DELETE FROM {t} WHERE 1=1")
        conn.commit()
        log.info(f"  TRUNCATED {t}")


def chunked_insert(conn, table, source, source_cols, chunk_size=500, total_batches=51564):
    """INSERT INTO table FROM source in chunks of chunk_size batch IDs."""
    cur = conn.cursor()
    inserted_total = 0

    for chunk_start in range(0, total_batches, chunk_size):
        chunk_end = min(chunk_start + chunk_size, total_batches)
        # batch_id is 6-digit zero-padded in filename
        # e.g. cc-parquet/batch_001500_pages.parquet
        # Filter: source_file >= 'cc-parquet/batch_<chunk_start>' AND < 'cc-parquet/batch_<chunk_end>'
        start_str = f"cc-parquet/batch_{chunk_start:06d}_"
        end_str = f"cc-parquet/batch_{chunk_end:06d}_"

        sql = f"""INSERT INTO {table} ({source_cols})
                  SELECT {source_cols}
                  FROM {source}
                  WHERE source_file >= '{start_str}' AND source_file < '{end_str}'"""

        t0 = time.time()
        try:
            cur.execute(sql)
            conn.commit()
            elapsed = time.time() - t0
            log.info(f"  {table} [{chunk_start}-{chunk_end}]: {elapsed:.0f}s")
            inserted_total += 1
        except psycopg2.OperationalError as e:
            log.error(f"  {table} [{chunk_start}-{chunk_end}] OOM: {str(e)[:100]}")
            log.info("  Sleeping 30s for RW recovery...")
            time.sleep(30)
            try:
                conn.close()
            except:
                pass
            conn = get_conn()
            cur = conn.cursor()
        except Exception as e:
            log.error(f"  {table} [{chunk_start}-{chunk_end}]: {str(e).split(chr(10))[0][:120]}")
            conn.rollback()

    return conn


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--chunk-size", type=int, default=500)
    p.add_argument("--total-batches", type=int, default=52000)
    p.add_argument("--truncate", action="store_true")
    p.add_argument("--table", choices=["pages", "links", "dlinks", "all"], default="all")
    args = p.parse_args()

    conn = get_conn()

    log.info("=== Recreate sources with INCLUDE file ===")
    recreate_sources(conn)
    time.sleep(3)

    if args.truncate:
        log.info("=== TRUNCATE ===")
        truncate_tables(conn)

    page_cols = """rkey, url, domain, title, description, language, content_type,
        status_code, outlink_count, crawl, ip_address, og_image, robots,
        content_hash, previous_content_hash, version, crawled_at,
        vertex_id, _seq, created_date, sensitivity_ord, owner_did"""

    link_cols = """label, anchor_text, edge_id, src_vid, dst_vid,
        _seq, created_date, sensitivity_ord, owner_did"""

    dlink_cols = """label, count, edge_id, src_vid, dst_vid,
        _seq, created_date, sensitivity_ord, owner_did"""

    if args.table in ("pages", "all"):
        log.info("=== INSERT vertex_page ===")
        conn = chunked_insert(conn, "vertex_page", "cc_pages_s3", page_cols, args.chunk_size, args.total_batches)

    if args.table in ("links", "all"):
        log.info("=== INSERT edge_links_to ===")
        conn = chunked_insert(conn, "edge_links_to", "cc_links_s3", link_cols, args.chunk_size, args.total_batches)

    if args.table in ("dlinks", "all"):
        log.info("=== INSERT edge_links_to_domain ===")
        conn = chunked_insert(conn, "edge_links_to_domain", "cc_dlinks_s3", dlink_cols, args.chunk_size, args.total_batches)

    log.info("=== Verify ===")
    cur = conn.cursor()
    for t in ["vertex_page", "edge_links_to", "edge_links_to_domain"]:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        log.info(f"  {t}: {cur.fetchone()[0]:,}")

    conn.close()


if __name__ == "__main__":
    main()
