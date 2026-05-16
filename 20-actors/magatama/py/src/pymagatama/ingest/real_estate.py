"""Real Estate read handlers for BPMN + Zeebe."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pymagatama.db_sync import sync_cursor


def _clamp_limit(value: Any, fallback: int = 50) -> int:
    try:
        parsed = int(value if value is not None else fallback)
    except (TypeError, ValueError):
        parsed = fallback
    return max(1, min(parsed, 200))


def _offset(value: Any) -> int:
    try:
        parsed = int(value or 0)
    except (TypeError, ValueError):
        parsed = 0
    return max(0, parsed)


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value


def _fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return [_jsonable(dict(zip(cols, row))) for row in (cur.fetchall() or [])]


def search_listings(**kwargs: Any) -> dict[str, Any]:
    limit = _clamp_limit(kwargs.get("limit"), 50)
    offset = _offset(kwargs.get("offset"))
    where: list[str] = []
    params: list[Any] = []

    if kwargs.get("countryIso2"):
        where.append("country_iso2 = %s")
        params.append(str(kwargs["countryIso2"]).upper())
    if kwargs.get("city"):
        where.append("city = %s")
        params.append(str(kwargs["city"]))
    if kwargs.get("listingKind"):
        where.append("listing_kind = %s")
        params.append(str(kwargs["listingKind"]))
    if kwargs.get("offerStatus"):
        where.append("offer_status = %s")
        params.append(str(kwargs["offerStatus"]))
    if kwargs.get("currency"):
        where.append("currency = %s")
        params.append(str(kwargs["currency"]).upper())
    if kwargs.get("sourceId"):
        where.append("source_id = %s")
        params.append(str(kwargs["sourceId"]))
    if kwargs.get("canonicalPropertyKey"):
        where.append("canonical_property_key = %s")
        params.append(str(kwargs["canonicalPropertyKey"]))
    if kwargs.get("minPrice") is not None:
        where.append("price >= %s")
        params.append(float(kwargs["minPrice"]))
    if kwargs.get("maxPrice") is not None:
        where.append("price <= %s")
        params.append(float(kwargs["maxPrice"]))

    clause = f"WHERE {' AND '.join(where)}" if where else ""
    rows = _fetch_all(
        f"""SELECT * FROM vertex_real_estate_listing
        {clause}
        ORDER BY last_seen_at DESC NULLS LAST
        LIMIT %s OFFSET %s""",
        (*params, limit, offset),
    )
    return {"items": rows, "count": len(rows), "limit": limit, "offset": offset}


def get_property(**kwargs: Any) -> dict[str, Any]:
    property_vid = kwargs.get("propertyVid")
    canonical_key = kwargs.get("canonicalPropertyKey")
    if property_vid:
        rows = _fetch_all("SELECT * FROM vertex_real_estate_property WHERE vertex_id=%s LIMIT 1", (str(property_vid),))
    elif canonical_key:
        rows = _fetch_all("SELECT * FROM vertex_real_estate_property WHERE canonical_property_key=%s LIMIT 1", (str(canonical_key),))
    else:
        return {"error": "propertyVid or canonicalPropertyKey required"}
    if not rows:
        return {"error": "not found"}

    prop = rows[0]
    prop_vid = str(prop.get("vertex_id") or "")
    prop_key = str(prop.get("canonical_property_key") or "")
    listings: list[dict[str, Any]] = []
    transactions: list[dict[str, Any]] = []
    if kwargs.get("includeListings") is not False:
        listings = _fetch_all(
            """SELECT * FROM vertex_real_estate_listing
            WHERE property_vid=%s OR canonical_property_key=%s
            ORDER BY last_seen_at DESC NULLS LAST
            LIMIT 50""",
            (prop_vid, prop_key),
        )
    if kwargs.get("includeTransactions"):
        transactions = _fetch_all(
            """SELECT * FROM vertex_real_estate_transaction
            WHERE property_vid=%s
            ORDER BY signed_at DESC NULLS LAST
            LIMIT 50""",
            (prop_vid,),
        )
    return {"property": prop, "listings": listings, "transactions": transactions}


def get_market_stats(**kwargs: Any) -> dict[str, Any]:
    limit = _clamp_limit(kwargs.get("limit"), 50)
    where = ["offer_status IN ('active', 'pending')"]
    params: list[Any] = []
    if kwargs.get("countryIso2"):
        where.append("country_iso2 = %s")
        params.append(str(kwargs["countryIso2"]).upper())
    if kwargs.get("city"):
        where.append("city = %s")
        params.append(str(kwargs["city"]))
    if kwargs.get("listingKind"):
        where.append("listing_kind = %s")
        params.append(str(kwargs["listingKind"]))
    if kwargs.get("currency"):
        where.append("currency = %s")
        params.append(str(kwargs["currency"]).upper())
    rows = _fetch_all(
        f"""SELECT
          country_iso2,
          city,
          listing_kind,
          currency,
          COUNT(*) AS listing_count,
          AVG(price) AS avg_price,
          MIN(price) AS min_price,
          MAX(price) AS max_price,
          AVG(price_per_sqm) AS avg_price_per_sqm,
          MAX(last_seen_at) AS latest_seen_at
        FROM vertex_real_estate_listing
        WHERE {' AND '.join(where)}
        GROUP BY country_iso2, city, listing_kind, currency
        ORDER BY COUNT(*) DESC
        LIMIT %s""",
        (*params, limit),
    )
    return {"items": rows, "count": len(rows)}
