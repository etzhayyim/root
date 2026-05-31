"""Yadoya catalog query primitives for BPMN/LangServer.

Moves the read-side hotel search/list logic out of the Cloudflare Worker.
Mutation flows already have BPMN definitions under 00-contracts/bpmn/ai/gftd/yadoya.
"""

from __future__ import annotations

from typing import Any

from pymagatama.db_sync import sync_cursor


HOTEL_COLUMNS = (
    "vertex_id",
    "owner_did",
    "name",
    "country",
    "region",
    "city",
    "chain_did",
    "property_did",
    "isic_code",
    "price_jpy_min",
    "status",
    "created_at",
)


def _int(v: Any, default: int, *, min_value: int, max_value: int) -> int:
    try:
        n = int(v)
    except (TypeError, ValueError):
        n = default
    return max(min_value, min(max_value, n))


def _row_dict(row: Any) -> dict[str, Any]:
    return {col: row[i] for i, col in enumerate(HOTEL_COLUMNS)}


def task_yadoya_search_hotels(
    country: str = "",
    region: str = "",
    city: str = "",
    chainDid: str = "",
    isicCode: str = "",
    priceJpyMax: Any = 0,
    limit: Any = 50,
    **_: Any,
) -> dict[str, Any]:
    """Filtered catalog search for app.etzhayyim.apps.yadoya.searchHotels."""
    limit_n = _int(limit, 50, min_value=1, max_value=200)
    try:
        price_max = int(priceJpyMax or 0)
    except (TypeError, ValueError):
        price_max = 0

    clauses = ["status = %s"]
    params: list[Any] = ["published"]
    if country:
        clauses.append("country = %s")
        params.append(country)
    if region:
        clauses.append("region = %s")
        params.append(region)
    if city:
        clauses.append("city = %s")
        params.append(city)
    if chainDid:
        clauses.append("chain_did = %s")
        params.append(chainDid)
    if isicCode:
        clauses.append("isic_code = %s")
        params.append(isicCode)
    if price_max > 0:
        clauses.append("price_jpy_min <= %s")
        params.append(price_max)

    sql = (
        f"SELECT {', '.join(HOTEL_COLUMNS)} "
        "FROM vertex_yadoya_hotel "
        f"WHERE {' AND '.join(clauses)} "
        "ORDER BY region NULLS LAST, city NULLS LAST, name NULLS LAST "
        f"LIMIT {limit_n}"
    )
    with sync_cursor() as cur:
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
    hotels = [_row_dict(row) for row in rows]
    return {"hotels": hotels, "total": len(hotels)}


def task_yadoya_list_hotels(
    region: str = "",
    chainDid: str = "",
    limit: Any = 50,
    offset: Any = 0,
    **_: Any,
) -> dict[str, Any]:
    """Unfiltered/paged catalog listing for app.etzhayyim.apps.yadoya.listHotels."""
    limit_n = _int(limit, 50, min_value=1, max_value=500)
    offset_n = _int(offset, 0, min_value=0, max_value=100_000)

    clauses = ["status = %s"]
    params: list[Any] = ["published"]
    if region:
        clauses.append("region = %s")
        params.append(region)
    if chainDid:
        clauses.append("chain_did = %s")
        params.append(chainDid)

    sql = (
        f"SELECT {', '.join(HOTEL_COLUMNS)} "
        "FROM vertex_yadoya_hotel "
        f"WHERE {' AND '.join(clauses)} "
        "ORDER BY region NULLS LAST, city NULLS LAST, name NULLS LAST "
        f"LIMIT {limit_n} OFFSET {offset_n}"
    )
    with sync_cursor() as cur:
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
    hotels = [_row_dict(row) for row in rows]
    return {"hotels": hotels, "total": len(hotels), "offset": offset_n, "limit": limit_n}


def register(worker: Any, *, timeout_ms: int = 60_000) -> None:
    worker.task(
        task_type="xrpc.app.etzhayyim.apps.yadoya.searchHotels",
        single_value=False,
        timeout_ms=timeout_ms,
    )(task_yadoya_search_hotels)
    worker.task(
        task_type="xrpc.app.etzhayyim.apps.yadoya.listHotels",
        single_value=False,
        timeout_ms=timeout_ms,
    )(task_yadoya_list_hotels)
