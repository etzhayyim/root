#!/usr/bin/env python3
"""Ingest and publish court-record Hugging Face datasets.

Subcommands:
  ingest-sf
    Stream jamiequint/sf_criminal_court tables from Hugging Face into
    vertex_hf_dataset / vertex_hf_dataset_record.

  export-world
    Build a source-normalized worldwide court-record dataset from
    vertex_legal_corpus_document and optionally push it to Hugging Face.

The SF source contains public court records with names and case numbers.
By default this script stores rows with sensitivity_ord=1 so they do not
enter mv_hf_dataset_text_for_training. Use --allow-training only after a
policy review for the target use.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any


SF_REPO_ID = "jamiequint/sf_criminal_court"
SF_OWNER_DID = "did:web:legal-corpus.etzhayyim.com"
WORLD_DEFAULT_REPO_ID = "etzhayyim/world_criminal_court"
SCRIPT_ACTOR = "sys.legal-court-hf-datasets"

SF_TABLES: dict[str, dict[str, Any]] = {
    "attorneys": {"rows": 72_289, "text_columns": ["case_number", "name", "attorney_type"]},
    "calendar": {"rows": 318_993, "text_columns": None},
    "calendar_with_judicial_assignments": {"rows": 318_993, "text_columns": None},
    "cases": {"rows": 77_406, "text_columns": None},
    "da_arrests": {"rows": 176_130, "text_columns": None},
    "da_prosecuted": {"rows": 120_827, "text_columns": None},
    "judicial_assignment_sources": {"rows": 14, "text_columns": None},
    "judicial_assignments": {"rows": 804, "text_columns": None},
    "judicial_department_assignments": {"rows": 777, "text_columns": None},
    "judicial_officers": {"rows": 77, "text_columns": None},
    "register_of_actions": {"rows": 776_728, "text_columns": None},
    "sfsc_case_matches": {"rows": 13_790, "text_columns": None},
    "sfsc_charge_dispositions": {"rows": 44_029, "text_columns": None},
}

CATALOG_SQL = """
INSERT INTO vertex_hf_dataset (
  vertex_id, owner_did, sensitivity_ord,
  slug, org, name, modality, license, hf_url, task_categories, tags,
  row_count_expected, row_count_ingested, last_synced_at, status,
  created_at, org_id, user_id, actor_id
)
SELECT
  %s, %s, %s,
  %s, %s, %s, %s, %s, %s, %s, %s,
  %s, %s, %s, 'active',
  %s, %s, %s, %s
WHERE NOT EXISTS (SELECT 1 FROM vertex_hf_dataset WHERE vertex_id = %s)
"""

RECORD_SQL = """
INSERT INTO vertex_hf_dataset_record (
  vertex_id, owner_did, sensitivity_ord, slug, record_id, split, lang,
  text_for_training, text_byte_size, raw_json, source_uri,
  created_at, org_id, user_id, actor_id
)
SELECT
  %s, %s, %s, %s, %s, %s, %s,
  %s, %s, %s, %s,
  %s, %s, %s, %s
WHERE NOT EXISTS (SELECT 1 FROM vertex_hf_dataset_record WHERE vertex_id = %s)
"""

RECORD_COLUMNS = [
    "vertex_id",
    "owner_did",
    "sensitivity_ord",
    "slug",
    "record_id",
    "split",
    "lang",
    "text_for_training",
    "text_byte_size",
    "raw_json",
    "source_uri",
    "created_at",
    "org_id",
    "user_id",
    "actor_id",
]

UPDATE_CATALOG_SQL = """
UPDATE vertex_hf_dataset
SET row_count_ingested = %s, last_synced_at = %s
WHERE slug = %s
"""

WORLD_CASES_SQL = """
SELECT
  vertex_id,
  source_id,
  canonical_uri,
  document_type,
  jurisdiction,
  court,
  language_code,
  title,
  citation,
  decided_at,
  published_at,
  fetched_at,
  body_uri,
  body_byte_size,
  topic_tags_csv
FROM vertex_legal_corpus_document
WHERE COALESCE(jurisdiction, '') NOT ILIKE '%%san francisco%%'
  AND COALESCE(court, '') NOT ILIKE '%%san francisco%%'
  AND COALESCE(canonical_uri, '') NOT ILIKE '%%sfsuperiorcourt%%'
  AND (
    %s = false
    OR COALESCE(document_type, '') ILIKE '%%criminal%%'
    OR COALESCE(title, '') ILIKE '%%criminal%%'
    OR COALESCE(topic_tags_csv, '') ILIKE '%%criminal%%'
    OR COALESCE(topic_tags_csv, '') ILIKE '%%penal%%'
  )
ORDER BY jurisdiction, source_id, decided_at NULLS LAST, vertex_id
LIMIT %s
"""


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def stable_id(*parts: Any) -> str:
    body = "\x1f".join("" if p is None else str(p) for p in parts)
    return hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()[:24]


def scrub_json_value(v: Any) -> Any:
    if isinstance(v, bytes | bytearray):
        return "<bytes>"
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return v


def compact_json(row: dict[str, Any]) -> str:
    return json.dumps({k: scrub_json_value(v) for k, v in row.items()}, ensure_ascii=False, default=str)


def text_from_row(table: str, row: dict[str, Any], text_columns: list[str] | None) -> str:
    if text_columns:
        values = [str(row[c]) for c in text_columns if row.get(c) not in (None, "")]
        if values:
            return "\n".join(values)
    return compact_json(row)


def record_id_for_row(table: str, row: dict[str, Any], index: int) -> str:
    for key in ("id", "case_number", "case_id", "court_case_id", "incident_number"):
        if row.get(key) not in (None, ""):
            return f"{table}:{row[key]}:{index}"
    return f"{table}:{stable_id(table, compact_json(row))}:{index}"


def vertex_id_for_record(slug: str, record_id: str) -> str:
    safe_slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)[:160]
    safe_record = re.sub(r"[^a-zA-Z0-9._-]", "-", record_id)[:180]
    return f"at://{SF_OWNER_DID}/com.etzhayyim.apps.legalCourtDataset.record/{safe_slug}--{safe_record}"


def connect_rw(dsn: str):
    try:
        import psycopg

        return psycopg.connect(dsn, autocommit=True, prepare_threshold=0)
    except ImportError:
        import psycopg2

        conn = psycopg2.connect(dsn)
        conn.autocommit = True
        return conn


def load_hf_table(repo_id: str, table: str, split: str, token: str | None) -> Iterable[dict[str, Any]]:
    from datasets import load_dataset

    kwargs: dict[str, Any] = {"split": split, "streaming": True}
    if token:
        kwargs["token"] = token
    dataset = load_dataset(repo_id, table, **kwargs)
    yield from dataset


def load_hf_table_parquet(repo_id: str, table: str, token: str | None, batch_size: int) -> Iterable[dict[str, Any]]:
    from huggingface_hub import hf_hub_download
    import pyarrow.parquet as pq

    path = hf_hub_download(
        repo_id=repo_id,
        repo_type="dataset",
        filename=f"{table}.parquet",
        token=token,
    )
    pf = pq.ParquetFile(path)
    for batch in pf.iter_batches(batch_size=batch_size):
        yield from batch.to_pylist()


def ensure_catalog(
    cur: Any,
    *,
    slug: str,
    name: str,
    expected_rows: int | None,
    sensitivity_ord: int,
) -> None:
    ts = now_iso()
    vertex_id = f"at://{SF_OWNER_DID}/com.etzhayyim.apps.legalCourtDataset.dataset/{re.sub(r'[^a-zA-Z0-9]', '-', slug)}"
    cur.execute(
        CATALOG_SQL,
        (
            vertex_id,
            SF_OWNER_DID,
            sensitivity_ord,
            slug,
            slug.split("/", 1)[0],
            name,
            "tabular+text",
            "cc-by-nc-4.0",
            f"https://huggingface.co/datasets/{SF_REPO_ID}",
            "tabular-classification,legal-analytics,court-records",
            "criminal-justice,court-records,legal,san-francisco,public-records",
            expected_rows,
            0,
            None,
            ts,
            SF_OWNER_DID,
            SF_OWNER_DID,
            SCRIPT_ACTOR,
            vertex_id,
        ),
    )


def insert_record_batch(cur: Any, rows: list[tuple[Any, ...]], idempotent: bool) -> None:
    if not rows:
        return
    placeholders = ", ".join(["(" + ", ".join(["%s"] * len(RECORD_COLUMNS)) + ")"] * len(rows))
    values = [item for row in rows for item in row]
    aliases = ", ".join(RECORD_COLUMNS)
    if not idempotent:
        cur.execute(
            f"""
            INSERT INTO vertex_hf_dataset_record ({", ".join(RECORD_COLUMNS)})
            VALUES {placeholders}
            """,
            tuple(values),
        )
        return
    cur.execute(
        f"""
        INSERT INTO vertex_hf_dataset_record ({", ".join(RECORD_COLUMNS)})
        SELECT {aliases}
        FROM (VALUES {placeholders}) AS v({aliases})
        WHERE NOT EXISTS (
          SELECT 1 FROM vertex_hf_dataset_record r WHERE r.vertex_id = v.vertex_id
        )
        """,
        tuple(values),
    )


def ingest_sf(args: argparse.Namespace) -> None:
    dsn = args.rw_url or os.environ.get("KOTOBA_URL") or os.environ.get("DATABASE_URL")
    if not dsn and not args.dry_run:
        raise SystemExit("Set KOTOBA_URL or DATABASE_URL, or pass --dry-run")

    token = args.hf_token or os.environ.get("HF_TOKEN")
    sensitivity_ord = 0 if args.allow_training else args.sensitivity_ord
    tables = args.table or list(SF_TABLES)
    inserted_total = 0

    conn = None if args.dry_run else connect_rw(dsn)
    cur = None if conn is None else conn.cursor()
    try:
        for table in tables:
            if table not in SF_TABLES:
                raise SystemExit(f"Unknown SF table: {table}")
            spec = SF_TABLES[table]
            slug = f"{SF_REPO_ID}/{table}"
            if cur is not None:
                ensure_catalog(
                    cur,
                    slug=slug,
                    name=f"sf_criminal_court::{table}",
                    expected_rows=spec["rows"],
                    sensitivity_ord=sensitivity_ord,
                )

            count = 0
            pending: list[tuple[Any, ...]] = []
            source_rows = (
                load_hf_table(SF_REPO_ID, table, args.split, token)
                if args.source == "datasets"
                else load_hf_table_parquet(SF_REPO_ID, table, token, args.read_batch_size)
            )
            for i, row in enumerate(source_rows):
                if i < args.offset:
                    continue
                if args.limit is not None and i >= args.limit:
                    break
                row = dict(row)
                rid = record_id_for_row(table, row, i)
                text = text_from_row(table, row, spec["text_columns"])
                raw = compact_json(row)
                vid = vertex_id_for_record(slug, rid)
                if args.dry_run:
                    count += 1
                    continue
                pending.append(
                    (
                        vid,  # vertex_id
                        SF_OWNER_DID,  # owner_did
                        sensitivity_ord,
                        slug,
                        rid,
                        args.split,
                        "en",
                        text,
                        len(text.encode("utf-8", errors="replace")),
                        raw,
                        f"hf:{SF_REPO_ID}:{table}",
                        now_iso(),
                        SF_OWNER_DID,
                        SF_OWNER_DID,
                        SCRIPT_ACTOR,
                    )
                )
                count += 1
                if len(pending) >= args.batch_size:
                    insert_record_batch(cur, pending, args.idempotent)
                    pending = []
                if count % args.progress_every == 0:
                    print(f"{table}: {count} rows")
            if cur is not None and pending:
                insert_record_batch(cur, pending, args.idempotent)
            if cur is not None:
                cur.execute(UPDATE_CATALOG_SQL, (count, now_iso(), slug))
            inserted_total += count
            print(f"{table}: {'would ingest' if args.dry_run else 'ingested'} {count} rows")
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

    print(json.dumps({"ok": True, "repo_id": SF_REPO_ID, "rows": inserted_total, "dry_run": args.dry_run}))


def write_world_readme(out_dir: Path, repo_id: str, row_count: int, criminal_only: bool) -> None:
    readme = f"""---
license: cc-by-4.0
task_categories:
- text-classification
- tabular-classification
language:
- en
tags:
- court-records
- legal
- criminal-justice
- public-records
pretty_name: Worldwide Criminal Court Records
---

# Worldwide Criminal Court Records

Source-normalized court-record export from `vertex_legal_corpus_document`.
This is the non-San-Francisco companion to `jamiequint/sf_criminal_court`.

Rows exported: {row_count}

Criminal-only filter: {str(criminal_only).lower()}

Files:

- `cases.parquet`: one normalized source document per case/opinion/docket-like record.
- `register_of_actions.parquet`: one event-like row per exported record.
- `sources.parquet`: source and jurisdiction counts.

The export excludes San Francisco Superior Court style records by jurisdiction,
court name, and canonical URI filters. The upstream corpus determines coverage;
jurisdictions without public structured sources will be absent.
"""
    (out_dir / "README.md").write_text(readme, encoding="utf-8")


def export_world(args: argparse.Namespace) -> None:
    dsn = args.rw_url or os.environ.get("KOTOBA_URL") or os.environ.get("DATABASE_URL")
    if not dsn:
        raise SystemExit("Set KOTOBA_URL or DATABASE_URL")

    import pandas as pd

    out_dir = Path(args.out_dir) if args.out_dir else Path(tempfile.mkdtemp(prefix="world-court-hf-"))
    out_dir.mkdir(parents=True, exist_ok=True)

    with connect_rw(dsn) as conn:
        df = pd.read_sql_query(WORLD_CASES_SQL, conn, params=(bool(args.criminal_only), int(args.limit)))

    if df.empty:
        raise SystemExit("No world court rows matched the current filters")

    df = df.copy()
    df["case_number"] = df["citation"].fillna("").where(df["citation"].fillna("") != "", df["vertex_id"].map(lambda x: stable_id(x)))
    df["case_id"] = df["vertex_id"]
    df["filing_date"] = df["published_at"]
    df["source_url"] = df["canonical_uri"]

    cases_cols = [
        "case_id",
        "case_number",
        "title",
        "citation",
        "jurisdiction",
        "court",
        "document_type",
        "language_code",
        "filing_date",
        "decided_at",
        "published_at",
        "fetched_at",
        "source_id",
        "source_url",
        "body_uri",
        "body_byte_size",
        "topic_tags_csv",
    ]
    cases = df[cases_cols]
    actions = pd.DataFrame(
        {
            "id": range(1, len(df) + 1),
            "case_id": df["case_id"],
            "case_number": df["case_number"],
            "action_date": df["decided_at"].fillna(df["published_at"]).fillna(df["fetched_at"]),
            "action_type": df["document_type"],
            "entry_text": df["title"],
            "source_id": df["source_id"],
            "source_url": df["canonical_uri"],
        }
    )
    sources = (
        df.groupby(["source_id", "jurisdiction"], dropna=False)
        .size()
        .reset_index(name="record_count")
        .sort_values(["source_id", "jurisdiction"])
    )

    cases.to_parquet(out_dir / "cases.parquet", index=False)
    actions.to_parquet(out_dir / "register_of_actions.parquet", index=False)
    sources.to_parquet(out_dir / "sources.parquet", index=False)
    write_world_readme(out_dir, args.repo_id, len(cases), bool(args.criminal_only))

    print(f"wrote {len(cases)} world rows to {out_dir}")

    if args.push:
        token = args.hf_token or os.environ.get("HF_TOKEN")
        if not token:
            raise SystemExit("Set HF_TOKEN or pass --hf-token to push")
        from huggingface_hub import HfApi

        api = HfApi(token=token)
        api.create_repo(repo_id=args.repo_id, repo_type="dataset", private=args.private, exist_ok=True)
        api.upload_folder(
            repo_id=args.repo_id,
            repo_type="dataset",
            folder_path=str(out_dir),
            commit_message=f"world court export {now_iso()}",
        )
        print(f"pushed dataset to https://huggingface.co/datasets/{args.repo_id}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sf = sub.add_parser("ingest-sf", help="ingest jamiequint/sf_criminal_court into RisingWave")
    sf.add_argument("--rw-url")
    sf.add_argument("--hf-token")
    sf.add_argument("--table", action="append", choices=sorted(SF_TABLES))
    sf.add_argument("--split", default="train")
    sf.add_argument("--limit", type=int)
    sf.add_argument("--offset", type=int, default=0)
    sf.add_argument("--dry-run", action="store_true")
    sf.add_argument("--source", choices=["parquet", "datasets"], default="parquet")
    sf.add_argument("--idempotent", action="store_true", help="skip already-present vertex_id rows via anti-join")
    sf.add_argument("--allow-training", action="store_true", help="store sensitivity_ord=0 instead of protected default")
    sf.add_argument("--sensitivity-ord", type=int, default=1)
    sf.add_argument("--batch-size", type=int, default=500)
    sf.add_argument("--read-batch-size", type=int, default=10_000)
    sf.add_argument("--progress-every", type=int, default=10_000)
    sf.set_defaults(func=ingest_sf)

    world = sub.add_parser("export-world", help="export non-SF worldwide court records to HF-style parquet")
    world.add_argument("--rw-url")
    world.add_argument("--hf-token")
    world.add_argument("--repo-id", default=WORLD_DEFAULT_REPO_ID)
    world.add_argument("--out-dir")
    world.add_argument("--limit", type=int, default=1_000_000)
    world.add_argument("--criminal-only", action=argparse.BooleanOptionalAction, default=True)
    world.add_argument("--push", action="store_true")
    world.add_argument("--private", action="store_true")
    world.set_defaults(func=export_world)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
