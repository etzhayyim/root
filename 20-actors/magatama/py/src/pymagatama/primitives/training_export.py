"""
LLM training data export — kotoba Datom log (vertex_/edge_) → JSONL → B2.


Two Zeebe task types:
  training.export.text   — v_training_text → shard-NNNNN.jsonl.gz (B2)
  training.export.triple — v_training_triple → shard-NNNNN.jsonl.gz (B2)

Phase 1 (C): vertex_wet_chunk focus.
  label='wet_chunk' queries only the CommonCrawl markdown corpus.
  Cursor-based pagination via shard_index × TRAINING_SHARD_ROWS (default 50K).

B2 env vars (same as patent.py):
  B2_ACCESS_KEY_ID       Backblaze B2 application key ID
  B2_SECRET_ACCESS_KEY   Backblaze B2 application key
  B2_ENDPOINT            e.g. https://s3.us-west-004.backblazeb2.com

Output bucket: TRAINING_B2_BUCKET (default: etzhayyim-training-data)
Key pattern:   {TRAINING_B2_PREFIX}/{dataset_name}/{label}/shard-NNNNN.jsonl.gz

HuggingFace datasets compat (plain JSONL — no extra deps needed):
  from datasets import load_dataset
  ds = load_dataset("json", data_files="s3://etzhayyim-training-data/v1/etzhayyim-corpus/wet_chunk/shard-*.jsonl.gz",
                    storage_options={...})
"""

from __future__ import annotations

import gzip
import hashlib
import hmac
import io
import json
import os
import time
from typing import Any

from pymagatama.kotoba_datomic import get_kotoba_client
from datetime import datetime, timezone

_OWNER_DID = "did:web:training.etzhayyim.com"
_SHARD_ROWS = int(os.environ.get("TRAINING_SHARD_ROWS", "50000"))
_B2_BUCKET = os.environ.get("TRAINING_B2_BUCKET", "etzhayyim-training-data")
_B2_PREFIX = os.environ.get("TRAINING_B2_PREFIX", "v1")
_B2_KEY_ID = os.environ.get("B2_ACCESS_KEY_ID", "").strip()
_B2_KEY = os.environ.get("B2_SECRET_ACCESS_KEY", "").strip()
_B2_ENDPOINT = os.environ.get("B2_ENDPOINT", "https://s3.us-west-004.backblazeb2.com").rstrip("/")
_B2_REGION = os.environ.get("B2_REGION", "us-west-004")
_HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
_HF_REPO_ID = os.environ.get("HF_REPO_ID", "etzhayyim/etzhayyim-corpus").strip()


# ──────────────────────────────────────────────────────────────────────
# B2 upload (AWS Sig V4 — same pattern as patent.py, no boto3)
# ──────────────────────────────────────────────────────────────────────

def _b2_put(key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    """Upload bytes to B2. Returns s3-uri string."""
    import urllib.request as _req

    if not _B2_KEY_ID or not _B2_KEY:
        raise RuntimeError("B2_ACCESS_KEY_ID / B2_SECRET_ACCESS_KEY not set")

    url = f"{_B2_ENDPOINT}/{_B2_BUCKET}/{key}"
    now = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    date = now[:8]
    host = _B2_ENDPOINT.replace("https://", "").replace("http://", "")

    payload_hash = hashlib.sha256(data).hexdigest()
    canonical_headers = (
        f"content-type:{content_type}\n"
        f"host:{host}\n"
        f"x-amz-content-sha256:{payload_hash}\n"
        f"x-amz-date:{now}\n"
    )
    signed_headers = "content-type;host;x-amz-content-sha256;x-amz-date"
    canonical_req = (
        f"PUT\n/{_B2_BUCKET}/{key}\n\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
    )

    scope = f"{date}/{_B2_REGION}/s3/aws4_request"
    string_to_sign = (
        f"AWS4-HMAC-SHA256\n{now}\n{scope}\n"
        + hashlib.sha256(canonical_req.encode()).hexdigest()
    )

    def _sign(k: bytes, msg: str) -> bytes:
        return hmac.new(k, msg.encode(), hashlib.sha256).digest()

    signing_key = _sign(
        _sign(_sign(_sign(f"AWS4{_B2_KEY}".encode(), date), _B2_REGION), "s3"),
        "aws4_request",
    )
    signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()
    auth = (
        f"AWS4-HMAC-SHA256 Credential={_B2_KEY_ID}/{scope},"
        f" SignedHeaders={signed_headers},"
        f" Signature={signature}"
    )

    request = _req.Request(
        url, data=data, method="PUT",
        headers={
            "Content-Type": content_type,
            "x-amz-date": now,
            "x-amz-content-sha256": payload_hash,
            "Authorization": auth,
        },
    )
    with _req.urlopen(request, timeout=120) as resp:
        resp.read()

    return f"s3://{_B2_BUCKET}/{key}"


def _b2_get(key: str) -> bytes:
    """Download bytes from B2 using AWS Sig V4."""
    import urllib.request as _req

    if not _B2_KEY_ID or not _B2_KEY:
        raise RuntimeError("B2_ACCESS_KEY_ID / B2_SECRET_ACCESS_KEY not set")

    url = f"{_B2_ENDPOINT}/{_B2_BUCKET}/{key}"
    now = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    date = now[:8]
    host = _B2_ENDPOINT.replace("https://", "").replace("http://", "")

    payload_hash = hashlib.sha256(b"").hexdigest()
    canonical_headers = (
        f"host:{host}\n"
        f"x-amz-content-sha256:{payload_hash}\n"
        f"x-amz-date:{now}\n"
    )
    signed_headers = "host;x-amz-content-sha256;x-amz-date"
    canonical_req = (
        f"GET\n/{_B2_BUCKET}/{key}\n\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
    )

    scope = f"{date}/{_B2_REGION}/s3/aws4_request"
    string_to_sign = (
        f"AWS4-HMAC-SHA256\n{now}\n{scope}\n"
        + hashlib.sha256(canonical_req.encode()).hexdigest()
    )

    def _sign(k: bytes, msg: str) -> bytes:
        return hmac.new(k, msg.encode(), hashlib.sha256).digest()

    signing_key = _sign(
        _sign(_sign(_sign(f"AWS4{_B2_KEY}".encode(), date), _B2_REGION), "s3"),
        "aws4_request",
    )
    signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()
    auth = (
        f"AWS4-HMAC-SHA256 Credential={_B2_KEY_ID}/{scope},"
        f" SignedHeaders={signed_headers},"
        f" Signature={signature}"
    )

    request = _req.Request(
        url, method="GET",
        headers={
            "x-amz-date": now,
            "x-amz-content-sha256": payload_hash,
            "Authorization": auth,
        },
    )
    with _req.urlopen(request, timeout=300) as resp:
        return resp.read()



def _record_shard(
    vid: str,
    dataset_name: str,
    label: str,
    shard_index: int,
    row_count: int,
    b2_key: str,
) -> None:
    get_kotoba_client().insert_row(
        "vertex_training_shard",
        {
            "vertex_id": vid,
            "dataset_name": dataset_name,
            "label": label,
            "shard_index": shard_index,
            "row_count": row_count,
            "b2_key": b2_key,
            "status": "done",
            "created_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "owner_did": _OWNER_DID,
            "_seq": 0,
            "sensitivity_ord": 0,
        },
    )


def _to_jsonl_gz(records: list[dict[str, Any]]) -> bytes:


# ──────────────────────────────────────────────────────────────────────
# Task: training.export.text
# ──────────────────────────────────────────────────────────────────────

def task_training_export_text(
    dataset_name: str = "etzhayyim-corpus",
    label: str = "wet_chunk",
    shard_index: int = 0,
) -> dict[str, Any]:
    """
    Export one shard from v_training_text to B2 as gzipped JSONL.

    Inputs:
      dataset_name  destination folder name under B2 prefix (default: etzhayyim-corpus)
      label         'wet_chunk' | 'profile' | 'all' (default: wet_chunk)
      shard_index   0-based shard number; multiply by TRAINING_SHARD_ROWS for OFFSET

    Returns:
      {status, row_count, b2_key, next_shard, has_more}
      status='done' when the shard is empty (export complete).
    """
    kotoba_client = get_kotoba_client()
    query_limit = _SHARD_ROWS
    query_offset = shard_index * _SHARD_ROWS

    # R0: Using q() for complex WHERE, ORDER BY, LIMIT, OFFSET not covered by shims.
    # Datalog queries return map keys as keywords, converting to snake_case strings.

    # Base query components
    find_clause = "[(pull ?e [:v_training_text/vertex_id :v_training_text/label :v_training_text/content :v_training_text/lang :v_training_text/created_date])]"
    where_clauses = [
        '[?e :table/name "v_training_text"]'
    ]
    if label != "all":
        where_clauses.append(f'[?e :v_training_text/label "{label}"]')

    datalog_query = f"""
    [:find {find_clause}
     :where
     {" ".join(where_clauses)}
     :order-by [?e :v_training_text/vertex_id :asc]
     :limit {query_limit}
     :offset {query_offset}]
    """
    rows_from_q = kotoba_client.q(datalog_query)

    # Convert Datom keywords to snake_case strings
    records = []
    for r_list in rows_from_q: # each r_list is a list containing one dict, e.g., [{'v_training_text/vertex_id': value}]
        datom_dict = r_list[0] # get the dict from the list
        converted_dict = {}
        for k, v in datom_dict.items():
            # k is a string like ':v_training_text/vertex_id'
            # We want 'vertex_id'
            key_name = k.split('/')[-1] # get 'vertex_id' from 'v_training_text/vertex_id'
            converted_key = key_name.replace("-", "_") # convert kebab-case to snake_case
            converted_dict[converted_key] = v
        records.append(converted_dict)

    if not records:
        return {"status": "done", "row_count": 0, "shard_index": shard_index}

    # Sanitize label for B2 path: SigV4 + urllib disagree on URI-encoding
    # of ':', so labels like 'hf:ADSKAILab/...' break the signature.
    safe_label = label.replace(":", "_")
    b2_key = f"{_B2_PREFIX}/{dataset_name}/{safe_label}/shard-{shard_index:05d}.jsonl.gz"
    _b2_put(b2_key, _to_jsonl_gz(records), "application/x-ndjson")

    vid = f"training-shard:{dataset_name}:{label}:{shard_index}"
    _record_shard(vid, dataset_name, label, shard_index, len(records), b2_key)

    return {
        "status": "ok",
        "row_count": len(records),
        "b2_key": b2_key,
        "next_shard": shard_index + 1,
        "has_more": len(records) == _SHARD_ROWS,
    }


# ──────────────────────────────────────────────────────────────────────
# Task: training.export.triple
# ──────────────────────────────────────────────────────────────────────

def task_training_export_triple(
    dataset_name: str = "etzhayyim-triples",
    shard_index: int = 0,
) -> dict[str, Any]:
    """
    Export one shard from v_training_triple to B2 as gzipped JSONL.

    Returns:
      {status, row_count, b2_key, next_shard, has_more}
    """
    kotoba_client = get_kotoba_client()
    query_limit = _SHARD_ROWS
    query_offset = shard_index * _SHARD_ROWS

    # R0: Using q() for complex ORDER BY, LIMIT, OFFSET not covered by shims.
    # Datalog queries return map keys as keywords, converting to snake_case strings.
    datalog_query = f"""
    [:find (pull ?e [:v_training_triple/src_vid :v_training_triple/relation :v_training_triple/dst_vid :v_training_triple/created_date])
     :where
     [?e :table/name "v_training_triple"]
     [?e :v_training_triple/src_vid]
     [?e :v_training_triple/relation]
     [?e :v_training_triple/dst_vid]
     [?e :v_training_triple/created_date]
     :order-by [?e :v_training_triple/src_vid :asc] [?e :v_training_triple/relation :asc]
     :limit {query_limit}
     :offset {query_offset}]
    """
    rows_from_q = kotoba_client.q(datalog_query)

    records = []
    for r_list in rows_from_q:
        datom_dict = r_list[0]
        converted_dict = {}
        for k, v in datom_dict.items():
            key_name = k.split('/')[-1]
            converted_key = key_name.replace("-", "_")
            converted_dict[converted_key] = v
        records.append(converted_dict)

    if not records:
        return {"status": "done", "row_count": 0, "shard_index": shard_index}

    b2_key = f"{_B2_PREFIX}/{dataset_name}/triples/shard-{shard_index:05d}.jsonl.gz"
    _b2_put(b2_key, _to_jsonl_gz(records), "application/x-ndjson")

    vid = f"training-shard:{dataset_name}:triples:{shard_index}"
    _record_shard(vid, dataset_name, "triples", shard_index, len(records), b2_key)

    return {
        "status": "ok",
        "row_count": len(records),
        "b2_key": b2_key,
        "next_shard": shard_index + 1,
        "has_more": len(records) == _SHARD_ROWS,
    }


# ──────────────────────────────────────────────────────────────────────
# Task: training.push.huggingface
# ──────────────────────────────────────────────────────────────────────

def task_training_push_huggingface(
    dataset_name: str = "etzhayyim-corpus",
    label: str = "wet_chunk",
    repo_type: str = "dataset",
) -> dict[str, Any]:
    """
    Push completed B2 shards to HuggingFace Hub.

    Reads vertex_training_shard for status='done' rows matching dataset_name+label,
    downloads each shard from B2, and uploads to the HF Hub repo under
    data/{label}/shard-NNNNN.jsonl.gz.

    Env vars:
      HF_TOKEN    HuggingFace API token with write access to HF_REPO_ID
      HF_REPO_ID  HuggingFace dataset repo (default: etzhayyim/etzhayyim-corpus)

    Returns:
      {status, pushed_count, repo_id}
    """
    from huggingface_hub import HfApi  # lazy import — only loaded when task fires

    if not _HF_TOKEN:
        raise RuntimeError("HF_TOKEN not set")

    kotoba_client = get_kotoba_client()

    # R0: Using q() for multiple WHERE conditions and ORDER BY not covered by shims.
    # Datalog queries return map keys as keywords.
    datalog_query = f"""
    [:find ?shard_index ?b2_key ?row_count
     :where
     [?e :table/name "vertex_training_shard"]
     [?e :vertex_training_shard/dataset_name "{dataset_name}"]
     [?e :vertex_training_shard/label "{label}"]
     [?e :vertex_training_shard/status "done"]
     [?e :vertex_training_shard/shard_index ?shard_index]
     [?e :vertex_training_shard/b2_key ?b2_key]
     [?e :vertex_training_shard/row_count ?row_count]
     :order-by [?e :vertex_training_shard/shard_index :asc]]
    """
    shards = kotoba_client.q(datalog_query)

    if not shards:
        return {"status": "ok", "pushed_count": 0, "repo_id": _HF_REPO_ID}

    api = HfApi(token=_HF_TOKEN)
    api.create_repo(repo_id=_HF_REPO_ID, repo_type=repo_type, private=False, exist_ok=True)

    pushed = 0
    for shard_index, b2_key, row_count in shards:
        data = _b2_get(b2_key)
        path_in_repo = f"data/{label}/shard-{shard_index:05d}.jsonl.gz"
        api.upload_file(
            path_or_fileobj=io.BytesIO(data),
            path_in_repo=path_in_repo,
            repo_id=_HF_REPO_ID,
            repo_type=repo_type,
            commit_message=f"shard {shard_index:05d} ({row_count} rows)",
        )
        pushed += 1

    return {
        "status": "ok",
        "pushed_count": pushed,
        "repo_id": _HF_REPO_ID,
    }


def register(worker: Any, timeout_ms: int = 600_000) -> None:
    worker.task(task_type="training.export.text",        single_value=False, timeout_ms=timeout_ms)(task_training_export_text)
    worker.task(task_type="training.export.triple",      single_value=False, timeout_ms=timeout_ms)(task_training_export_triple)
    worker.task(task_type="training.push.huggingface",   single_value=False, timeout_ms=timeout_ms)(task_training_push_huggingface)
