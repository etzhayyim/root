#!/usr/bin/env python3
"""
L2 Actor embedding batch — multilingual-e5-small over view_actor_universal.

Reads unembedded rows from RisingWave (view_actor_universal LEFT JOIN
vertex_actor_embedding ON did), runs sentence-transformers
`intfloat/multilingual-e5-small` locally, UPSERTs 384-d vectors into
vertex_actor_embedding as comma-joined VARCHAR.

Why not a Python External UDF?
  RisingWave v0.2.1 Python External UDF binds to a single in-process
  pipeline with `io_threads=100` throttle (ADR-0044). For a 10-8B one-shot
  backfill a standalone batch is cheaper to steer: adjustable parallelism,
  resumable from checkpoint, can run on any box with GPU/MPS/CUDA.
  Incremental re-embed (streaming delta) should be a Python UDF later.

Why not Murakumo?
  Murakumo HTTP `/v1/embeddings` endpoint isn't wired yet. Local
  sentence-transformers avoids round-trips and burns local silicon
  efficiently on Apple M-series (MPS) or any CUDA box.

Usage
  # Dry run, 100 rows, high-activity kinds first:
  python3 actor-embedding-batch.py --dry-run --limit 100

  # Backfill one kind at a time (recommended first pass):
  python3 actor-embedding-batch.py --kind action --limit 1000
  python3 actor-embedding-batch.py --kind natural_person --limit 50000

  # Full backfill, resumable:
  nohup python3 actor-embedding-batch.py \
     --batch-size 256 --max-rows 10000000 \
     > /tmp/actor-embed.log 2>&1 &

Progress: /tmp/actor-embed-progress.json (checkpoint every 10k rows).
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
import psycopg2.extras

MODEL_ID = "intfloat/multilingual-e5-small"
MODEL_DIM = 384
PROGRESS_PATH = Path("/tmp/actor-embed-progress.json")

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    # Default to the Vultr primary (ADR-0048). Override via env.
    "REDACTED_USE_DATABASE_URL_ENV",
)


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def load_checkpoint() -> dict:
    if PROGRESS_PATH.exists():
        try:
            return json.loads(PROGRESS_PATH.read_text())
        except Exception:
            pass
    return {"embedded": 0, "last_did": "", "last_kind": ""}


def save_checkpoint(state: dict) -> None:
    PROGRESS_PATH.write_text(json.dumps(state, indent=2))


def fetch_candidates(conn, kind: str | None, limit: int, after_did: str) -> list[dict]:
    """Pick rows present in view_actor_universal but absent from vertex_actor_embedding."""
    sql = """
        SELECT u.did, u.handle, u.display_name, u.description, u.kind, u.vertex_id
        FROM view_actor_universal u
        LEFT JOIN vertex_actor_embedding e ON e.did = u.did
        WHERE u.did IS NOT NULL
          AND e.did IS NULL
    """
    params: list = []
    if kind:
        sql += " AND u.kind = %s"
        params.append(kind)
    if after_did:
        sql += " AND u.did > %s"
        params.append(after_did)
    sql += " ORDER BY u.did ASC LIMIT %s"
    params.append(limit)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


def build_corpus(row: dict) -> str:
    # multilingual-e5 models recommend "passage: " prefix for indexed documents.
    name = (row.get("display_name") or "").strip()
    desc = (row.get("description") or "").strip()
    kind = (row.get("kind") or "").strip()
    parts = [f"passage: {name}" if name else "passage:"]
    if desc:
        parts.append(desc)
    if kind:
        parts.append(f"kind={kind}")
    return " | ".join(parts)[:2000]


def l2_norm(v) -> float:
    return float(sum(x * x for x in v) ** 0.5)


def insert_embeddings(conn, rows: list[dict]) -> None:
    """Batch INSERT. RW Hyperdrive-origin pool; serial batches to avoid quota hits."""
    sql = """
        INSERT INTO vertex_actor_embedding
          (vertex_id, did, kind, embedding, embedding_norm, model_id, embedded_at, created_at)
        VALUES %s
    """
    now = datetime.now(timezone.utc).isoformat()
    values = []
    for r in rows:
        vec_csv = ",".join(f"{x:.6f}" for x in r["_embedding"])
        values.append(
            (r["vertex_id"], r["did"], r.get("kind"), vec_csv, r["_norm"],
             MODEL_ID, now, now)
        )
    with conn.cursor() as cur:
        psycopg2.extras.execute_values(cur, sql, values, page_size=len(values))
    conn.commit()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--kind", default=None, help="Only embed this vertex kind (e.g. 'action').")
    p.add_argument("--limit", type=int, default=1000, help="Rows per DB pull.")
    p.add_argument("--batch-size", type=int, default=64, help="GPU batch size.")
    p.add_argument("--max-rows", type=int, default=10_000_000, help="Stop after this many embeddings.")
    p.add_argument("--dry-run", action="store_true", help="Print progress; don't write embeddings.")
    p.add_argument("--reset", action="store_true", help="Drop checkpoint and start over.")
    args = p.parse_args()

    if args.reset and PROGRESS_PATH.exists():
        PROGRESS_PATH.unlink()

    log(f"DATABASE_URL = {DATABASE_URL.split('@')[-1]}")
    log(f"model = {MODEL_ID}")

    # Lazy-import the heavy deps so --help is instant.
    from sentence_transformers import SentenceTransformer  # type: ignore

    log("loading model …")
    model = SentenceTransformer(MODEL_ID)
    log(f"model loaded; dim = {model.get_sentence_embedding_dimension()}")
    assert model.get_sentence_embedding_dimension() == MODEL_DIM

    state = load_checkpoint()
    conn = psycopg2.connect(DATABASE_URL)
    try:
        embedded_total = state["embedded"]
        after_did = state.get("last_did", "")
        while embedded_total < args.max_rows:
            rows = fetch_candidates(conn, args.kind, args.limit, after_did)
            if not rows:
                log(f"no more candidates (embedded={embedded_total}); done.")
                break

            texts = [build_corpus(r) for r in rows]
            t0 = time.time()
            embs = model.encode(
                texts,
                batch_size=args.batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=False,
            )
            dt = time.time() - t0

            for r, vec in zip(rows, embs):
                r["_embedding"] = vec.tolist()
                r["_norm"] = l2_norm(r["_embedding"])

            if not args.dry_run:
                insert_embeddings(conn, rows)

            embedded_total += len(rows)
            after_did = rows[-1]["did"]
            state["embedded"] = embedded_total
            state["last_did"] = after_did
            state["last_kind"] = args.kind or ""
            save_checkpoint(state)
            rate = len(rows) / max(dt, 1e-6)
            log(f"batch: {len(rows):5d} rows in {dt:5.2f}s ({rate:6.1f} rps) | total={embedded_total}")

        log(f"complete. embedded={embedded_total}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
