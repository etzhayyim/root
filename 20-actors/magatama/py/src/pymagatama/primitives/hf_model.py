"""
HuggingFace Hub model catalog — Zeebe task handler registrations.

Task types:
  hf.model.listFilters      — list enabled vertex_hfhub_filter rows for models
  hf.model.scanAll          — iterate filter list, call scan per filter
  hf.model.scan             — scan HF Hub for 1 model filter
  hf.model.fetchDetailBatch — fetch full card for pending/unenriched models
  hf.model.fetchDetail      — fetch full card for 1 repo_id
  hf.model.resolveLineage   — resolve edge_hfhub_model_base + edge_hfhub_model_dataset
"""

from __future__ import annotations

import logging
from typing import Any

from pymagatama.db_sync import sync_cursor
from pymagatama.ingest.hf_model import (
    task_hf_model_fetch_detail,
    task_hf_model_resolve_lineage,
    task_hf_model_scan,
)

LOG = logging.getLogger(__name__)


def _fetchall(sql_str: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    with sync_cursor() as cur:
        cur.execute(sql_str, params)
        return cur.fetchall() or []


def task_hf_model_list_filters(**_: Any) -> dict[str, Any]:
    rows = _fetchall(
        "SELECT vertex_id FROM vertex_hfhub_filter "
        "WHERE enabled = true AND (entity_type = 'model' OR entity_type = 'both') "
        "LIMIT 200"
    )
    ids = [r[0] for r in rows]
    return {"ok": True, "filter_ids": ids, "filter_count": len(ids)}


def task_hf_model_scan_all(
    filter_ids: list[str] | None = None,
    limit_per_filter: int = 500,
    **_: Any,
) -> dict[str, Any]:
    ids = filter_ids or []
    total_scanned = 0
    total_matched = 0
    for fid in ids:
        try:
            result = task_hf_model_scan(filter_id=fid, limit=limit_per_filter)
            total_scanned += result.get("scanned", 0)
            total_matched += result.get("matched", 0)
        except Exception as exc:
            LOG.warning("model scan failed filter=%s: %s", fid, exc)
    return {"ok": True, "total_scanned": total_scanned, "total_matched": total_matched}


def task_hf_model_fetch_detail_batch(
    batch_size: int = 30,
    **_: Any,
) -> dict[str, Any]:
    """Fetch full model card for models missing parameter info (list API gaps)."""
    rows = _fetchall(
        f"SELECT repo_id FROM vertex_hfhub_model "
        f"WHERE num_parameters IS NULL AND status = 'active' "
        f"ORDER BY downloads_month DESC LIMIT {int(batch_size)}"
    )
    enriched = 0
    for (repo_id,) in rows:
        try:
            result = task_hf_model_fetch_detail(repo_id=repo_id)
            if result.get("ok"):
                enriched += 1
        except Exception as exc:
            LOG.warning("model fetchDetail failed repo=%s: %s", repo_id, exc)
    return {"ok": True, "processed": len(rows), "enriched": enriched}


def task_hf_model_scan_one(filter_id: str | None = None, limit: int = 500, **_: Any) -> dict[str, Any]:
    return task_hf_model_scan(filter_id=filter_id, limit=limit)


def task_hf_model_fetch_detail_one(repo_id: str | None = None, **_: Any) -> dict[str, Any]:
    return task_hf_model_fetch_detail(repo_id=repo_id)


def task_hf_model_resolve_lineage_one(**kwargs: Any) -> dict[str, Any]:
    return task_hf_model_resolve_lineage(**kwargs)


TASK_HANDLERS: dict[str, Any] = {
    "hf.model.listFilters": task_hf_model_list_filters,
    "hf.model.scanAll": task_hf_model_scan_all,
    "hf.model.scan": task_hf_model_scan_one,
    "hf.model.fetchDetailBatch": task_hf_model_fetch_detail_batch,
    "hf.model.fetchDetail": task_hf_model_fetch_detail_one,
    "hf.model.resolveLineage": task_hf_model_resolve_lineage_one,
}
