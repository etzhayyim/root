#!/usr/bin/env python3
"""Ingest curated Hugging Face datasets for Oka distillation.

This stores bounded, normalized text samples in vertex_hf_dataset_record so
they can flow into v_training_text when sensitivity_ord=0. Eval-only datasets
are stored with sensitivity_ord=1 and therefore stay out of training views.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any


OWNER_DID = "did:web:training.etzhayyim.com"
SCRIPT_ACTOR = "sys.oka.hf-quality-datasets"


@dataclass(frozen=True)
class DatasetSpec:
    repo_id: str
    split: str
    role: str
    lang: str
    license: str
    limit: int
    sensitivity_ord: int = 0
    config: str | None = None


SPECS: list[DatasetSpec] = [
    DatasetSpec("allenai/tulu-3-sft-mixture", "train", "frontier_sft_mixture", "multi", "odc-by", 800),
    DatasetSpec("HuggingFaceH4/ultrachat_200k", "train_sft", "dialogue_sft", "en", "mit", 800),
    DatasetSpec("HuggingFaceH4/ultrafeedback_binarized", "train_prefs", "preference_pair", "en", "mit", 800),
    DatasetSpec("nvidia/OpenMathInstruct-2", "train_1M", "math_reasoning_sft", "en", "cc-by-4.0", 800),
    DatasetSpec("microsoft/orca-math-word-problems-200k", "train", "math_word_problem_sft", "en", "mit", 800),
    DatasetSpec("llm-jp/databricks-dolly-15k-ja", "train", "japanese_instruction_sft", "ja", "cc-by-sa-3.0", 800),
    DatasetSpec("elyza/ELYZA-tasks-100", "test", "japanese_eval_seed", "ja", "cc-by-sa-4.0", 100, sensitivity_ord=1),
]


CATALOG_SQL = """
INSERT INTO vertex_hf_dataset (
  vertex_id, owner_did, sensitivity_ord,
  slug, org, name, modality, license, hf_url, task_categories, tags,
  row_count_expected, row_count_ingested, last_synced_at, status,
  created_at, org_id, user_id, actor_id
)
SELECT
  %s, %s, %s,
  %s, %s, %s, 'text', %s, %s, %s, %s,
  %s, %s, %s, 'active',
  %s, %s, %s, %s
WHERE NOT EXISTS (SELECT 1 FROM vertex_hf_dataset WHERE vertex_id = %s)
"""

UPDATE_CATALOG_SQL = """
UPDATE vertex_hf_dataset
SET row_count_ingested = %s, last_synced_at = %s
WHERE slug = %s
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


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def stable_id(*parts: Any) -> str:
    body = "\x1f".join("" if p is None else str(p) for p in parts)
    return hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()[:24]


def safe_slug(repo_id: str, split: str) -> str:
    return f"{repo_id}/{split}"


def catalog_vid(slug: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)[:180]
    return f"at://{OWNER_DID}/com.etzhayyim.apps.hfDataset.dataset/{safe}"


def record_vid(slug: str, record_id: str) -> str:
    safe_s = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)[:150]
    safe_r = re.sub(r"[^a-zA-Z0-9._-]", "-", record_id)[:170]
    return f"at://{OWNER_DID}/com.etzhayyim.apps.hfDataset.record/{safe_s}--{safe_r}"


def compact_json(row: dict[str, Any]) -> str:
    return json.dumps(row, ensure_ascii=False, default=str, separators=(",", ":"))


def messages_to_text(messages: Any) -> str:
    if not isinstance(messages, list):
        return str(messages or "")
    lines: list[str] = []
    for msg in messages:
        if isinstance(msg, dict):
            role = str(msg.get("role") or msg.get("from") or "message")
            content = str(msg.get("content") or msg.get("value") or "")
            if content:
                lines.append(f"{role}: {content}")
        elif msg:
            lines.append(str(msg))
    return "\n".join(lines)


def normalize_row(spec: DatasetSpec, row: dict[str, Any], index: int) -> tuple[str, str]:
    repo = spec.repo_id
    if repo == "allenai/tulu-3-sft-mixture":
        rid = str(row.get("id") or stable_id(repo, index, row.get("source")))
        text = messages_to_text(row.get("messages"))
    elif repo == "HuggingFaceH4/ultrachat_200k":
        rid = str(row.get("prompt_id") or stable_id(repo, index, row.get("prompt")))
        text = messages_to_text(row.get("messages"))
    elif repo == "HuggingFaceH4/ultrafeedback_binarized":
        rid = str(row.get("prompt_id") or stable_id(repo, index, row.get("prompt")))
        prompt = str(row.get("prompt") or "")
        chosen = messages_to_text(row.get("chosen"))
        rejected = messages_to_text(row.get("rejected"))
        text = (
            f"Preference training item\nPrompt: {prompt}\n\n"
            f"Chosen answer:\n{chosen}\n\nRejected answer:\n{rejected}\n"
            f"score_chosen={row.get('score_chosen')} score_rejected={row.get('score_rejected')}"
        )
    elif repo == "nvidia/OpenMathInstruct-2":
        problem = str(row.get("problem") or "")
        solution = str(row.get("generated_solution") or "")
        answer = str(row.get("expected_answer") or "")
        rid = stable_id(repo, spec.split, index, problem)
        text = f"Problem: {problem}\n\nSolution: {solution}\n\nExpected answer: {answer}"
    elif repo == "microsoft/orca-math-word-problems-200k":
        question = str(row.get("question") or "")
        answer = str(row.get("answer") or "")
        rid = stable_id(repo, spec.split, index, question)
        text = f"Question: {question}\n\nAnswer: {answer}"
    elif repo == "llm-jp/databricks-dolly-15k-ja":
        instruction = str(row.get("instruction") or "")
        context = str(row.get("context") or "")
        response = str(row.get("response") or "")
        rid = stable_id(repo, spec.split, index, instruction, context)
        text = f"指示: {instruction}\n\n文脈: {context}\n\n応答: {response}"
    elif repo == "elyza/ELYZA-tasks-100":
        rid = stable_id(repo, spec.split, index, row.get("input"))
        text = (
            f"評価入力: {row.get('input') or ''}\n\n"
            f"参照出力: {row.get('output') or ''}\n\n"
            f"評価観点: {row.get('eval_aspect') or ''}"
        )
    else:
        rid = stable_id(repo, spec.split, index, compact_json(row))
        text = compact_json(row)
    return rid, text.strip()


def connect_rw(dsn: str):
    try:
        import psycopg

        return psycopg.connect(dsn, autocommit=True, prepare_threshold=0)
    except ImportError:
        import psycopg2

        conn = psycopg2.connect(dsn)
        conn.autocommit = True
        return conn


def ensure_catalog(cur: Any, spec: DatasetSpec, inserted: int) -> None:
    slug = safe_slug(spec.repo_id, spec.split)
    ts = now_iso()
    cur.execute(
        CATALOG_SQL,
        (
            catalog_vid(slug),
            OWNER_DID,
            spec.sensitivity_ord,
            slug,
            spec.repo_id.split("/", 1)[0],
            f"{spec.repo_id}::{spec.split}",
            spec.license,
            f"https://huggingface.co/datasets/{spec.repo_id}",
            "text-generation,question-answering,preference-modeling",
            f"oka,{spec.role},{spec.lang},distillation",
            spec.limit,
            inserted,
            ts,
            ts,
            OWNER_DID,
            OWNER_DID,
            SCRIPT_ACTOR,
            catalog_vid(slug),
        ),
    )
    cur.execute(UPDATE_CATALOG_SQL, (inserted, ts, slug))


def insert_batch(cur: Any, rows: list[tuple[Any, ...]]) -> None:
    if not rows:
        return
    placeholders = ", ".join(["(" + ", ".join(["%s"] * len(RECORD_COLUMNS)) + ")"] * len(rows))
    values = [item for row in rows for item in row]
    aliases = ", ".join(RECORD_COLUMNS)
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


def ingest_spec(cur: Any, spec: DatasetSpec, *, token: str | None, batch_size: int, dry_run: bool) -> int:
    from datasets import load_dataset

    slug = safe_slug(spec.repo_id, spec.split)
    dataset = load_dataset(
        spec.repo_id,
        spec.config,
        split=spec.split,
        streaming=True,
        token=token,
    )
    pending: list[tuple[Any, ...]] = []
    inserted = 0
    for index, row_any in enumerate(dataset):
        if inserted >= spec.limit:
            break
        row = dict(row_any)
        rid, text = normalize_row(spec, row, index)
        if len(text.encode("utf-8", errors="replace")) < 20:
            continue
        if dry_run:
            inserted += 1
            continue
        pending.append(
            (
                record_vid(slug, rid),
                OWNER_DID,
                spec.sensitivity_ord,
                slug,
                rid,
                spec.split,
                spec.lang,
                text,
                len(text.encode("utf-8", errors="replace")),
                compact_json(row),
                f"hf:{spec.repo_id}:{spec.split}",
                now_iso(),
                OWNER_DID,
                OWNER_DID,
                SCRIPT_ACTOR,
            )
        )
        inserted += 1
        if len(pending) >= batch_size:
            insert_batch(cur, pending)
            pending = []
    if not dry_run:
        insert_batch(cur, pending)
        ensure_catalog(cur, spec, inserted)
    return inserted


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rw-url", default=os.environ.get("KOTOBA_URL") or os.environ.get("DATABASE_URL"))
    parser.add_argument("--hf-token", default=os.environ.get("HF_TOKEN"))
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit-scale", type=float, default=1.0)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not args.rw_url and not args.dry_run:
        raise SystemExit("Set KOTOBA_URL or DATABASE_URL")

    specs = [
        DatasetSpec(
            s.repo_id,
            s.split,
            s.role,
            s.lang,
            s.license,
            max(1, int(s.limit * args.limit_scale)),
            s.sensitivity_ord,
            s.config,
        )
        for s in SPECS
    ]
    total = 0
    conn = None if args.dry_run else connect_rw(args.rw_url)
    cur = None if conn is None else conn.cursor()
    try:
        for spec in specs:
            count = ingest_spec(cur, spec, token=args.hf_token, batch_size=args.batch_size, dry_run=args.dry_run)
            total += count
            print(json.dumps({"repo_id": spec.repo_id, "split": spec.split, "rows": count, "role": spec.role}))
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()
    print(json.dumps({"ok": True, "rows": total, "dry_run": args.dry_run}))


if __name__ == "__main__":
    main()
