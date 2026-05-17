"""
hf_dataset — HuggingFace Hub dataset catalog ingest.

Zeebe task types:
  hf.dataset.scan          — apply a vertex_hfhub_filter → populate vertex_hfhub_dataset
                             + edge_hfhub_filter_match (called by datasetScan.bpmn)
  hf.dataset.fetchSplits   — fetch split/parquet metadata for a single repo_id
                             → vertex_hfhub_split + vertex_hfhub_file + edge_hfhub_split_file
  hf.dataset.applyFilter   — re-evaluate edge_hfhub_filter_match for a filter against
                             already-catalogued datasets (no Hub API call)

Env (from K8s Secret training-hf-creds — same secret as training_export.py):
  HF_TOKEN      HuggingFace API token (read-only is sufficient)

RW conventions applied:
  - No ON CONFLICT — PK implicit upsert (same-PK re-INSERT overwrites)
  - LIMIT inlined as {int(n)} — avoids psycopg3 prepared-statement rejection
  - No CURRENT_DATE in hot-path queries — pass date string from Python
  - flush=False on all inserts (avoid RW_DDL_GUARD)
  - dml_rate_limit not needed here (catalog rows <500K total, not bulk)
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.request
from typing import Any

from pymagatama.db_sync import sync_cursor

LOG = logging.getLogger(__name__)

_OWNER_DID = "did:web:ingest.etzhayyim.com"
_HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
_HF_API = "https://huggingface.co/api"
_DS_SERVER = "https://datasets-server.huggingface.co"
_TIMEOUT = 30
_SCAN_LIMIT = int(os.environ.get("HF_SCAN_LIMIT", "500"))


# ── helpers ───────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())


def _today() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def _hf_get(path: str, params: dict[str, Any] | None = None) -> Any:
    url = f"{_HF_API}/{path.lstrip('/')}"
    if params:
        qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items() if v is not None)
        url = f"{url}?{qs}"
    headers: dict[str, str] = {"Accept": "application/json"}
    if _HF_TOKEN:
        headers["Authorization"] = f"Bearer {_HF_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return json.loads(resp.read().decode())
    except Exception as exc:
        LOG.warning("hf_get failed url=%s: %s", url, exc)
        return None


def _ds_server_get(endpoint: str, repo_id: str) -> Any:
    url = f"{_DS_SERVER}/{endpoint}?dataset={urllib.parse.quote(repo_id, safe='')}"
    headers: dict[str, str] = {}
    if _HF_TOKEN:
        headers["Authorization"] = f"Bearer {_HF_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return json.loads(resp.read().decode())
    except Exception as exc:
        LOG.debug("ds_server_get failed repo=%s endpoint=%s: %s", repo_id, endpoint, exc)
        return None


def _execute(sql_str: str, params: tuple[Any, ...] = ()) -> int:
    with sync_cursor() as cur:
        cur.execute(sql_str, params)
        return int(cur.rowcount or 0)


def _fetchall(sql_str: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    with sync_cursor() as cur:
        cur.execute(sql_str, params)
        return cur.fetchall() or []


# ── HF Hub API layer ──────────────────────────────────────────────────────────

def _parse_filter_spec(row: tuple[Any, ...]) -> dict[str, Any]:
    """Unpack vertex_hfhub_filter row into a dict."""
    (
        vertex_id, slug, filter_tags, filter_tasks, filter_languages,
        filter_license, min_downloads, max_rows, require_gated, exclude_private,
    ) = row
    return {
        "vertex_id": vertex_id,
        "slug": slug,
        "tags": json.loads(filter_tags) if filter_tags else [],
        "tasks": json.loads(filter_tasks) if filter_tasks else [],
        "languages": json.loads(filter_languages) if filter_languages else [],
        "license": filter_license,
        "min_downloads": min_downloads,
        "max_rows": max_rows,
        "require_gated": require_gated,
        "exclude_private": exclude_private,
    }


def _list_hf_datasets(fspec: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    """Call HF Hub datasets list API with filter criteria."""
    import urllib.parse  # local import — already in stdlib

    params: dict[str, Any] = {"full": "true", "limit": int(limit)}
    if fspec["tags"]:
        # HF Hub accepts repeated `filter` params; urllib doesn't easily support that.
        # Build the query string manually for multiple tags.
        base = f"{_HF_API}/datasets?full=true&limit={int(limit)}"
        for t in fspec["tags"]:
            base += f"&filter={urllib.parse.quote(t)}"
        for t in fspec["tasks"]:
            base += f"&filter={urllib.parse.quote(t)}"
        for lang in fspec["languages"]:
            base += f"&filter=language:{urllib.parse.quote(lang)}"
        if fspec["license"]:
            base += f"&filter=license:{urllib.parse.quote(fspec['license'])}"
        headers: dict[str, str] = {"Accept": "application/json"}
        if _HF_TOKEN:
            headers["Authorization"] = f"Bearer {_HF_TOKEN}"
        req = urllib.request.Request(base, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
                return json.loads(resp.read().decode()) or []
        except Exception as exc:
            LOG.warning("hf_list_datasets failed: %s", exc)
            return []
    else:
        result = _hf_get("datasets", params)
        return result if isinstance(result, list) else []


def _extract_dataset_row(info: dict[str, Any]) -> dict[str, Any]:
    """Normalise a HF Hub dataset info dict into our schema fields."""
    repo_id = info.get("id", "")
    author = info.get("author", "")
    card = info.get("cardData", {}) or {}
    tags: list[str] = info.get("tags", [])
    task_categories: list[str] = []
    languages: list[str] = []
    for t in tags:
        if t.startswith("task_categories:"):
            task_categories.append(t.removeprefix("task_categories:"))
        elif t.startswith("language:"):
            languages.append(t.removeprefix("language:"))

    return {
        "vertex_id": f"hf:dataset:{repo_id}",
        "repo_id": repo_id,
        "author": author,
        "sha": info.get("sha", ""),
        "license": info.get("license", "") or card.get("license", ""),
        "size_category": info.get("cardData", {}).get("size_categories", [""])[0] if card.get("size_categories") else "",
        "downloads_month": int(info.get("downloads", 0) or 0),
        "likes": int(info.get("likes", 0) or 0),
        "gated": bool(info.get("gated", False)),
        "disabled": bool(info.get("disabled", False)),
        "private": bool(info.get("private", False)),
        "description": str(info.get("description", "") or "")[:4000],
        "card_data": json.dumps(card, ensure_ascii=False)[:8000],
        "tags": tags,
        "task_categories": task_categories,
        "languages": languages,
    }


def _dataset_passes_filter(ds: dict[str, Any], fspec: dict[str, Any]) -> bool:
    if fspec["exclude_private"] and ds["private"]:
        return False
    if fspec["require_gated"] and not ds["gated"]:
        return False
    if fspec["min_downloads"] and ds["downloads_month"] < fspec["min_downloads"]:
        return False
    return True


# ── DB write helpers ──────────────────────────────────────────────────────────

def _upsert_dataset(ds: dict[str, Any]) -> None:
    ts = _now_iso()
    date = _today()
    _execute(
        """INSERT INTO vertex_hfhub_dataset
        (vertex_id, created_date, repo_id, author, sha, license, size_category,
         downloads_month, likes, gated, disabled, private, description, card_data,
         status, last_scanned_at, actor_did, created_at)
        VALUES (%s, %s::date, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, 'active', %s::timestamp, %s, %s::timestamp)""",
        (
            ds["vertex_id"], date, ds["repo_id"], ds["author"], ds["sha"],
            ds["license"], ds["size_category"], ds["downloads_month"], ds["likes"],
            ds["gated"], ds["disabled"], ds["private"],
            ds["description"], ds["card_data"],
            ts, _OWNER_DID, ts,
        ),
    )


def _upsert_edges(ds: dict[str, Any]) -> None:
    vid = ds["vertex_id"]
    for tag in ds["tags"]:
        _execute(
            "INSERT INTO edge_hfhub_dataset_tag (dataset_id, tag) VALUES (%s, %s)",
            (vid, tag),
        )
    for task in ds["task_categories"]:
        _execute(
            "INSERT INTO edge_hfhub_dataset_task (dataset_id, task_category) VALUES (%s, %s)",
            (vid, task),
        )
    for lang in ds["languages"]:
        _execute(
            "INSERT INTO edge_hfhub_dataset_language (dataset_id, lang_code) VALUES (%s, %s)",
            (vid, lang),
        )


def _upsert_filter_match(filter_id: str, dataset_id: str) -> None:
    _execute(
        "INSERT INTO edge_hfhub_filter_match (filter_id, dataset_id, matched_at) VALUES (%s, %s, %s::timestamp)",
        (filter_id, dataset_id, _now_iso()),
    )


# ── Zeebe task handlers ───────────────────────────────────────────────────────

def task_hf_dataset_scan(
    filter_id: str | None = None,
    limit: int | None = None,
    **_: Any,
) -> dict[str, Any]:
    """
    Scan HuggingFace Hub for datasets matching a stored filter spec.

    Variables:
      filter_id  vertex_hfhub_filter.vertex_id (required)
      limit      max datasets to process per invocation (default HF_SCAN_LIMIT)
    """
    if not filter_id:
        return {"ok": False, "error": "filter_id required"}

    rows = _fetchall(
        """SELECT vertex_id, slug, filter_tags, filter_tasks, filter_languages,
                  filter_license, min_downloads, max_rows, require_gated, exclude_private
           FROM vertex_hfhub_filter
           WHERE vertex_id = %s AND enabled = true""",
        (filter_id,),
    )
    if not rows:
        return {"ok": False, "error": f"filter not found or disabled: {filter_id}"}

    fspec = _parse_filter_spec(rows[0])
    scan_limit = int(limit or _SCAN_LIMIT)
    datasets = _list_hf_datasets(fspec, scan_limit)

    inserted = 0
    matched = 0
    for info in datasets:
        ds = _extract_dataset_row(info)
        if not _dataset_passes_filter(ds, fspec):
            continue
        try:
            _upsert_dataset(ds)
            _upsert_edges(ds)
            _upsert_filter_match(filter_id, ds["vertex_id"])
            inserted += 1
            matched += 1
        except Exception as exc:
            LOG.warning("upsert failed repo=%s: %s", ds["repo_id"], exc)

    # Update filter last_run_at + match_count
    _execute(
        "UPDATE vertex_hfhub_filter SET last_run_at = %s::timestamp, match_count = %s WHERE vertex_id = %s",
        (_now_iso(), matched, filter_id),
    )

    LOG.info("hf.dataset.scan filter=%s scanned=%d matched=%d", filter_id, len(datasets), matched)
    return {"ok": True, "filter_id": filter_id, "scanned": len(datasets), "inserted": inserted, "matched": matched}


def task_hf_dataset_fetch_splits(
    repo_id: str | None = None,
    **_: Any,
) -> dict[str, Any]:
    """
    Fetch split stats and parquet file list for a single dataset.

    Writes to vertex_hfhub_split, vertex_hfhub_file, edge_hfhub_split_file.

    Variables:
      repo_id  HuggingFace dataset repo id (e.g. "squad")
    """
    if not repo_id:
        return {"ok": False, "error": "repo_id required"}

    splits_resp = _ds_server_get("splits", repo_id)
    parquet_resp = _ds_server_get("parquet", repo_id)

    splits_written = 0
    files_written = 0

    if splits_resp and "splits" in splits_resp:
        sizes: dict[str, dict[str, Any]] = {}
        if parquet_resp and "parquet_files" in parquet_resp:
            for pf in parquet_resp["parquet_files"]:
                key = f"{pf.get('config','default')}:{pf.get('split','')}"
                grp = sizes.setdefault(key, {"num_bytes": 0, "num_files": 0, "files": []})
                grp["num_bytes"] += pf.get("size", 0) or 0
                grp["num_files"] += 1
                grp["files"].append(pf)

        for sp in splits_resp["splits"]:
            config = sp.get("config", "default")
            split = sp.get("split", "")
            split_vid = f"hf:split:{repo_id}:{config}:{split}"
            info_key = f"{config}:{split}"
            grp = sizes.get(info_key, {})

            ts = _now_iso()
            _execute(
                """INSERT INTO vertex_hfhub_split
                (vertex_id, created_date, repo_id, config_name, split_name,
                 num_rows, num_bytes, num_files, features_json, actor_did, created_at)
                VALUES (%s, %s::date, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s)""",
                (
                    split_vid, _today(), repo_id, config, split,
                    sp.get("num_rows"),
                    grp.get("num_bytes"),
                    grp.get("num_files", 0),
                    json.dumps(sp.get("features", {}), ensure_ascii=False)[:4000],
                    _OWNER_DID, ts,
                ),
            )
            splits_written += 1

            for pf in grp.get("files", []):
                fpath = pf.get("filename", pf.get("url", ""))
                blob_url = (
                    f"https://huggingface.co/datasets/{repo_id}/resolve/main/{fpath}"
                    if not fpath.startswith("http")
                    else fpath
                )
                file_vid = f"hf:file:{repo_id}:{config}:{split}:{fpath}"
                _execute(
                    """INSERT INTO vertex_hfhub_file
                    (vertex_id, created_date, repo_id, split_vertex_id, file_path,
                     file_format, file_size, blob_url, actor_did, created_at)
                    VALUES (%s, %s::date, %s, %s, %s,
                            'parquet', %s, %s, %s, %s)""",
                    (
                        file_vid, _today(), repo_id, split_vid,
                        fpath, pf.get("size"), blob_url, _OWNER_DID, ts,
                    ),
                )
                _execute(
                    "INSERT INTO edge_hfhub_split_file (split_id, file_id) VALUES (%s, %s)",
                    (split_vid, file_vid),
                )
                files_written += 1

    # Mark dataset active
    _execute(
        "UPDATE vertex_hfhub_dataset SET status = 'active', last_scanned_at = %s::timestamp WHERE repo_id = %s",
        (_now_iso(), repo_id),
    )

    LOG.info("hf.dataset.fetchSplits repo=%s splits=%d files=%d", repo_id, splits_written, files_written)
    return {"ok": True, "repo_id": repo_id, "splits": splits_written, "files": files_written}


def task_hf_dataset_apply_filter(
    filter_id: str | None = None,
    **_: Any,
) -> dict[str, Any]:
    """
    Re-evaluate a filter against already-catalogued vertex_hfhub_dataset rows.
    Does NOT call the HF Hub API. Useful after editing filter criteria.

    Variables:
      filter_id  vertex_hfhub_filter.vertex_id (required)
    """
    if not filter_id:
        return {"ok": False, "error": "filter_id required"}

    rows = _fetchall(
        """SELECT vertex_id, slug, filter_tags, filter_tasks, filter_languages,
                  filter_license, min_downloads, max_rows, require_gated, exclude_private
           FROM vertex_hfhub_filter WHERE vertex_id = %s""",
        (filter_id,),
    )
    if not rows:
        return {"ok": False, "error": f"filter not found: {filter_id}"}

    fspec = _parse_filter_spec(rows[0])

    # Pull tags/tasks/languages per dataset via edges
    dataset_rows = _fetchall(
        "SELECT vertex_id, repo_id, downloads_month, private, gated FROM vertex_hfhub_dataset "
        "WHERE status = 'active' LIMIT 50000"
    )

    matched = 0
    for (vid, repo_id, downloads, private, gated) in dataset_rows:
        ds_meta = {
            "vertex_id": vid,
            "repo_id": repo_id,
            "downloads_month": downloads or 0,
            "private": bool(private),
            "gated": bool(gated),
        }
        if not _dataset_passes_filter(ds_meta, fspec):
            continue
        _upsert_filter_match(filter_id, vid)
        matched += 1

    _execute(
        "UPDATE vertex_hfhub_filter SET last_run_at = %s::timestamp, match_count = %s WHERE vertex_id = %s",
        (_now_iso(), matched, filter_id),
    )

    LOG.info("hf.dataset.applyFilter filter=%s matched=%d", filter_id, matched)
    return {"ok": True, "filter_id": filter_id, "evaluated": len(dataset_rows), "matched": matched}


# ── urllib.parse import guard ─────────────────────────────────────────────────
import urllib.parse  # noqa: E402 — stdlib, used in _list_hf_datasets
