"""
hf_model — HuggingFace Hub model catalog ingest.

Zeebe task types:
  hf.model.scan             — apply a vertex_hfhub_filter (entity_type=model|both)
                              → populate vertex_hfhub_model + edges + edge_hfhub_filter_match
  hf.model.fetchDetail      — fetch full model card for a single repo_id
  hf.model.resolveLineage   — resolve edge_hfhub_model_base + edge_hfhub_model_dataset links

HF Hub API used:
  GET /api/models?limit=N&filter=...&full=true   — list with metadata
  GET /api/models/{repo_id}                       — single model detail

Env (reuses K8s Secret training-hf-creds):
  HF_TOKEN   read-only HuggingFace API token

RW conventions:
  - No ON CONFLICT — PK implicit upsert
  - LIMIT inlined as {int(n)} — avoids psycopg3 prepared-statement rejection
  - No CURRENT_DATE in prepared statements
  - flush=False on all inserts
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.parse
import urllib.request
from typing import Any

from pymagatama.db_sync import sync_cursor

LOG = logging.getLogger(__name__)

_OWNER_DID = "did:web:ingest.gftd.ai"
_HF_TOKEN = os.environ.get("HF_TOKEN", "").strip()
_HF_API = "https://huggingface.co/api"
_TIMEOUT = 30
_SCAN_LIMIT = int(os.environ.get("HF_MODEL_SCAN_LIMIT", "500"))


# ── helpers ───────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())


def _today() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def _hf_request(url: str) -> Any:
    headers: dict[str, str] = {"Accept": "application/json"}
    if _HF_TOKEN:
        headers["Authorization"] = f"Bearer {_HF_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return json.loads(resp.read().decode())
    except Exception as exc:
        LOG.warning("hf_request failed url=%s: %s", url, exc)
        return None


def _execute(sql_str: str, params: tuple[Any, ...] = ()) -> int:
    with sync_cursor() as cur:
        cur.execute(sql_str, params)
        return int(cur.rowcount or 0)


def _fetchall(sql_str: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    with sync_cursor() as cur:
        cur.execute(sql_str, params)
        return cur.fetchall() or []


# ── HF Hub API — model list ───────────────────────────────────────────────────

def _list_hf_models(fspec: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    """Call HF Hub /api/models with filter criteria."""
    base = f"{_HF_API}/models?full=true&limit={int(limit)}"
    for tag in fspec.get("tags", []):
        base += f"&filter={urllib.parse.quote(tag)}"
    for task in fspec.get("tasks", []):
        base += f"&filter={urllib.parse.quote(task)}"
    for lang in fspec.get("languages", []):
        base += f"&filter=language:{urllib.parse.quote(lang)}"
    if fspec.get("license"):
        base += f"&filter=license:{urllib.parse.quote(fspec['license'])}"
    result = _hf_request(base)
    return result if isinstance(result, list) else []


def _fetch_model_detail(repo_id: str) -> dict[str, Any] | None:
    """GET /api/models/{repo_id} — full model card."""
    return _hf_request(f"{_HF_API}/models/{urllib.parse.quote(repo_id, safe='/')}")


# ── field extraction ──────────────────────────────────────────────────────────

def _extract_model_row(info: dict[str, Any]) -> dict[str, Any]:
    """Normalise a HF Hub model info dict into vertex_hfhub_model columns."""
    repo_id = info.get("id") or info.get("modelId", "")
    card = info.get("cardData") or {}
    cfg = info.get("config") or {}
    sf = info.get("safetensors") or {}
    ti = info.get("transformersInfo") or {}

    tags: list[str] = info.get("tags") or []

    # Derive task categories from tags (e.g. "task_categories:text-classification")
    task_categories: list[str] = []
    languages: list[str] = []
    license_tag = ""
    for t in tags:
        if t.startswith("task_categories:"):
            task_categories.append(t.removeprefix("task_categories:"))
        elif t.startswith("language:"):
            languages.append(t.removeprefix("language:"))
        elif t.startswith("license:"):
            license_tag = t.removeprefix("license:")

    # pipeline_tag is more reliable than task_categories for primary task
    pipeline_tag = info.get("pipeline_tag") or (task_categories[0] if task_categories else "")

    # Parameter count from safetensors.total
    num_parameters: int | None = sf.get("total")
    if num_parameters is not None:
        num_parameters = int(num_parameters)

    # Primary dtype from safetensors.parameters (key with max value)
    params_by_dtype: dict[str, int] = sf.get("parameters") or {}
    primary_dtype = ""
    if params_by_dtype:
        primary_dtype = max(params_by_dtype, key=lambda k: params_by_dtype[k])

    # Architectures
    archs: list[str] = cfg.get("architectures") or []
    architecture = archs[0] if archs else ""

    # base_model from cardData (can be string or list)
    base_model_raw = card.get("base_model")
    base_model = ""
    base_models: list[str] = []
    if isinstance(base_model_raw, str):
        base_model = base_model_raw
        base_models = [base_model_raw] if base_model_raw else []
    elif isinstance(base_model_raw, list):
        base_models = [str(b) for b in base_model_raw if b]
        base_model = base_models[0] if base_models else ""

    # Training datasets from cardData.datasets
    training_datasets: list[str] = []
    ds_raw = card.get("datasets")
    if isinstance(ds_raw, list):
        training_datasets = [str(d) for d in ds_raw if d]
    elif isinstance(ds_raw, str) and ds_raw:
        training_datasets = [ds_raw]

    return {
        "vertex_id": f"hf:model:{repo_id}",
        "repo_id": repo_id,
        "author": info.get("author", ""),
        "sha": info.get("sha", ""),
        "pipeline_tag": pipeline_tag,
        "library_name": info.get("library_name", ""),
        "model_type": cfg.get("model_type", ""),
        "architecture": architecture,
        "auto_model_class": ti.get("auto_model", ""),
        "inference_state": str(info.get("inference", "") or ""),
        "num_parameters": num_parameters,
        "primary_dtype": primary_dtype,
        "used_storage_bytes": info.get("usedStorage"),
        "license": card.get("license") or license_tag,
        "base_model": base_model,
        "trending_score": info.get("trendingScore"),
        "downloads_month": int(info.get("downloads") or 0),
        "likes": int(info.get("likes") or 0),
        "gated": bool(info.get("gated", False)),
        "disabled": bool(info.get("disabled", False)),
        "private": bool(info.get("private", False)),
        "card_data": json.dumps(card, ensure_ascii=False)[:8000],
        "spaces_count": len(info.get("spaces") or []),
        "created_at_hf": info.get("createdAt", ""),
        "last_modified_hf": info.get("lastModified", ""),
        # derived
        "tags": tags,
        "task_categories": task_categories,
        "languages": languages,
        "base_models": base_models,
        "training_datasets": training_datasets,
    }


def _model_passes_filter(m: dict[str, Any], fspec: dict[str, Any]) -> bool:
    if fspec.get("exclude_private") and m["private"]:
        return False
    if fspec.get("require_gated") and not m["gated"]:
        return False
    min_dl = fspec.get("min_downloads")
    if min_dl and m["downloads_month"] < min_dl:
        return False
    return True


# ── DB writes ─────────────────────────────────────────────────────────────────

def _upsert_model(m: dict[str, Any]) -> None:
    ts = _now_iso()
    date = _today()
    _execute(
        """INSERT INTO vertex_hfhub_model
        (vertex_id, created_date, repo_id, author, sha,
         pipeline_tag, library_name, model_type, architecture, auto_model_class, inference_state,
         num_parameters, primary_dtype, used_storage_bytes,
         license, base_model, trending_score, downloads_month, likes,
         gated, disabled, private, card_data, spaces_count,
         status, last_scanned_at, created_at_hf, last_modified_hf,
         actor_did, created_at)
        VALUES (
          %s, %s::date, %s, %s, %s,
          %s, %s, %s, %s, %s, %s,
          %s, %s, %s,
          %s, %s, %s, %s, %s,
          %s, %s, %s, %s, %s,
          'active', %s::timestamp, %s::timestamp, %s::timestamp,
          %s, %s::timestamp
        )""",
        (
            m["vertex_id"], date, m["repo_id"], m["author"], m["sha"],
            m["pipeline_tag"], m["library_name"], m["model_type"],
            m["architecture"], m["auto_model_class"], m["inference_state"],
            m["num_parameters"], m["primary_dtype"], m["used_storage_bytes"],
            m["license"], m["base_model"], m["trending_score"],
            m["downloads_month"], m["likes"],
            m["gated"], m["disabled"], m["private"],
            m["card_data"], m["spaces_count"],
            ts, m["created_at_hf"], m["last_modified_hf"],
            _OWNER_DID, ts,
        ),
    )


def _upsert_model_edges(m: dict[str, Any]) -> None:
    vid = m["vertex_id"]
    for tag in m["tags"]:
        _execute("INSERT INTO edge_hfhub_model_tag (model_id, tag) VALUES (%s, %s)", (vid, tag))
    for task in m["task_categories"]:
        _execute("INSERT INTO edge_hfhub_model_task (model_id, task_category) VALUES (%s, %s)", (vid, task))
    # Also insert pipeline_tag as a task edge (more reliable)
    if m["pipeline_tag"] and m["pipeline_tag"] not in m["task_categories"]:
        _execute("INSERT INTO edge_hfhub_model_task (model_id, task_category) VALUES (%s, %s)",
                 (vid, m["pipeline_tag"]))
    for lang in m["languages"]:
        _execute("INSERT INTO edge_hfhub_model_language (model_id, lang_code) VALUES (%s, %s)", (vid, lang))
    for depth, bm in enumerate(m["base_models"], start=1):
        _execute(
            "INSERT INTO edge_hfhub_model_base (model_id, base_model_id, depth) VALUES (%s, %s, %s)",
            (vid, bm, depth),
        )
    for ds in m["training_datasets"]:
        _execute(
            "INSERT INTO edge_hfhub_model_dataset (model_id, dataset_repo_id) VALUES (%s, %s)",
            (vid, ds),
        )


def _upsert_filter_match(filter_id: str, model_id: str) -> None:
    _execute(
        "INSERT INTO edge_hfhub_filter_match (filter_id, dataset_id, matched_at) VALUES (%s, %s, %s::timestamp)",
        (filter_id, model_id, _now_iso()),
    )


# ── Zeebe task implementations ────────────────────────────────────────────────

def task_hf_model_scan(
    filter_id: str | None = None,
    limit: int | None = None,
    **_: Any,
) -> dict[str, Any]:
    """
    Scan HuggingFace Hub for models matching a stored filter spec.
    Uses the same vertex_hfhub_filter table as dataset scan (entity_type='model'|'both').

    Variables:
      filter_id  vertex_hfhub_filter.vertex_id (required)
      limit      max models per invocation (default HF_MODEL_SCAN_LIMIT)
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

    (vid, slug, filter_tags, filter_tasks, filter_languages,
     filter_license, min_downloads, max_rows, require_gated, exclude_private) = rows[0]

    fspec = {
        "tags": json.loads(filter_tags) if filter_tags else [],
        "tasks": json.loads(filter_tasks) if filter_tasks else [],
        "languages": json.loads(filter_languages) if filter_languages else [],
        "license": filter_license,
        "min_downloads": min_downloads,
        "require_gated": require_gated,
        "exclude_private": exclude_private,
    }

    scan_limit = int(limit or _SCAN_LIMIT)
    models = _list_hf_models(fspec, scan_limit)

    inserted = 0
    matched = 0
    for info in models:
        m = _extract_model_row(info)
        if not _model_passes_filter(m, fspec):
            continue
        try:
            _upsert_model(m)
            _upsert_model_edges(m)
            _upsert_filter_match(filter_id, m["vertex_id"])
            inserted += 1
            matched += 1
        except Exception as exc:
            LOG.warning("model upsert failed repo=%s: %s", m["repo_id"], exc)

    _execute(
        "UPDATE vertex_hfhub_filter SET last_run_at = %s::timestamp, match_count = %s WHERE vertex_id = %s",
        (_now_iso(), matched, filter_id),
    )

    LOG.info("hf.model.scan filter=%s scanned=%d matched=%d", filter_id, len(models), matched)
    return {"ok": True, "filter_id": filter_id, "scanned": len(models), "inserted": inserted, "matched": matched}


def task_hf_model_fetch_detail(
    repo_id: str | None = None,
    **_: Any,
) -> dict[str, Any]:
    """
    Fetch full model card detail for a single repo_id and upsert all fields.
    Enriches a previously-scanned model (from list API which has fewer fields).

    Variables:
      repo_id  HuggingFace model repo id (e.g. "google/gemma-4-31B-it")
    """
    if not repo_id:
        return {"ok": False, "error": "repo_id required"}

    info = _fetch_model_detail(repo_id)
    if not info:
        return {"ok": False, "error": f"model not found or API error: {repo_id}"}

    m = _extract_model_row(info)
    try:
        _upsert_model(m)
        _upsert_model_edges(m)
    except Exception as exc:
        LOG.warning("model fetchDetail failed repo=%s: %s", repo_id, exc)
        return {"ok": False, "repo_id": repo_id, "error": str(exc)}

    return {
        "ok": True,
        "repo_id": repo_id,
        "pipeline_tag": m["pipeline_tag"],
        "num_parameters": m["num_parameters"],
        "base_model": m["base_model"],
        "training_datasets": m["training_datasets"],
    }


def task_hf_model_resolve_lineage(
    batch_size: int = 50,
    **_: Any,
) -> dict[str, Any]:
    """
    For edge_hfhub_model_dataset rows where dataset_vertex_id is NULL,
    attempt to resolve to an existing vertex_hfhub_dataset vertex_id.
    Also fetches detail for pending models that lack num_parameters.

    Idempotent — safe to re-run.
    """
    # Resolve dataset cross-references
    unresolved = _fetchall(
        f"SELECT model_id, dataset_repo_id FROM edge_hfhub_model_dataset "
        f"WHERE dataset_vertex_id IS NULL LIMIT {int(batch_size)}"
    )
    ds_resolved = 0
    for (model_id, ds_repo_id) in unresolved:
        ds_vid = f"hf:dataset:{ds_repo_id}"
        exists = _fetchall(
            "SELECT 1 FROM vertex_hfhub_dataset WHERE vertex_id = %s LIMIT 1",
            (ds_vid,),
        )
        if exists:
            _execute(
                "INSERT INTO edge_hfhub_model_dataset (model_id, dataset_repo_id, dataset_vertex_id) "
                "VALUES (%s, %s, %s)",
                (model_id, ds_repo_id, ds_vid),
            )
            ds_resolved += 1

    # Enrich models that are missing num_parameters (were scanned from list API)
    pending = _fetchall(
        f"SELECT repo_id FROM vertex_hfhub_model "
        f"WHERE num_parameters IS NULL AND status = 'active' "
        f"ORDER BY downloads_month DESC LIMIT {int(batch_size)}"
    )
    enriched = 0
    for (repo_id,) in pending:
        result = task_hf_model_fetch_detail(repo_id=repo_id)
        if result.get("ok"):
            enriched += 1

    LOG.info("hf.model.resolveLineage ds_resolved=%d enriched=%d", ds_resolved, enriched)
    return {"ok": True, "ds_resolved": ds_resolved, "enriched": enriched}
