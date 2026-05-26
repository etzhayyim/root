"""apps.etzhayyim.com directory handlers for BPMN + Zeebe."""

from __future__ import annotations

import json
import time
from typing import Any
from uuid import NAMESPACE_URL, uuid4, uuid5

from pymagatama.db_sync import sync_cursor

OWNER_DID = "did:web:apps.etzhayyim.com"
COLLECTION_TABLES = {
    "app.etzhayyim.apps.apps.appListing": "vertex_apps_directory_listing",
    "app.etzhayyim.apps.apps.feature": "vertex_apps_directory_feature",
    "app.etzhayyim.apps.apps.installIntent": "vertex_apps_directory_install_intent",
}


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def _s(value: Any, default: str = "") -> str:
    return str(value if value is not None else default)


def _arr(value: Any) -> list[str]:
    return [str(v) for v in value] if isinstance(value, list) else []


def _execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        return int(cur.rowcount or 0)


def _fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in (cur.fetchall() or [])]


def _vertex_id(collection: str, record_id: str) -> str:
    return f"at://{OWNER_DID}/{collection}/{record_id}"


def _edge_id(table: str, src: str, dst: str, relation: str) -> str:
    return f"{table}:{uuid5(NAMESPACE_URL, f'{src}|{dst}|{relation}')}"


def _typed_values(kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    if kind == "appListing":
        return {
            "name": _s(payload.get("name")),
            "display_name": _s(payload.get("displayName")),
            "description": _s(payload.get("description")),
            "icon": _s(payload.get("icon")),
            "embed_url": _s(payload.get("embedUrl")),
        }
    if kind == "feature":
        try:
            rank = int(payload.get("rank") or 100)
        except (TypeError, ValueError):
            rank = 100
        return {
            "feature_id": _s(payload.get("featureId")),
            "rail": _s(payload.get("rail")),
            "rank": rank,
            "approved_by_did": _s(payload.get("approvedByDid")),
        }
    if kind == "installIntent":
        return {
            "intent_id": _s(payload.get("intentId")),
            "user_did": _s(payload.get("userDid")),
            "source": _s(payload.get("source")),
            "client": _s(payload.get("client")),
        }
    return {}


def _write_edge(cur: Any, table: str, src: str, dst: str, relation: str, payload: dict[str, Any], created_at: str) -> None:
    cur.execute(
        f"""
        INSERT INTO {table}
          (edge_id,src_vid,dst_vid,relation_kind,value_json,created_at,updated_at,owner_did,sensitivity_ord)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (edge_id) DO UPDATE SET
          value_json = EXCLUDED.value_json,
          updated_at = EXCLUDED.updated_at
        """,
        (
            _edge_id(table, src, dst, relation),
            src,
            dst,
            relation,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
            created_at,
            _s(payload.get("updatedAt")) or created_at,
            OWNER_DID,
            2,
        ),
    )


def _write_related_edges(cur: Any, collection: str, kind: str, record_id: str, payload: dict[str, Any], created_at: str) -> None:
    listing_id = _s(payload.get("listingId"))
    if not listing_id:
        return
    listing_vid = _vertex_id("app.etzhayyim.apps.apps.appListing", listing_id)
    vertex_id = _vertex_id(collection, record_id)
    if kind == "feature":
        _write_edge(cur, "edge_apps_directory_listing_feature", listing_vid, vertex_id, "featured_as", payload, created_at)
    elif kind == "installIntent":
        _write_edge(cur, "edge_apps_directory_listing_install_intent", listing_vid, vertex_id, "has_install_intent", payload, created_at)


def _record(collection: str, kind: str, payload: dict[str, Any], record_id: str | None = None) -> dict[str, Any]:
    table = COLLECTION_TABLES.get(collection)
    if table is None:
        raise ValueError(f"unsupported apps directory collection: {collection}")
    rid = record_id or _id(kind)
    created = _s(payload.get("createdAt") or payload.get("updatedAt") or now_iso())
    rec = {**payload, "id": payload.get("id") or rid, "createdAt": created}
    listing_id = _s(payload.get("listingId")) or (rid if kind == "appListing" else "")
    typed = _typed_values(kind, rec)
    values = {
        "vertex_id": _vertex_id(collection, rid),
        "record_id": rid,
        "owner_did": OWNER_DID,
        "listing_id": listing_id or None,
        "app_did": _s(payload.get("appDid")) or None,
        "label": _s(payload.get("displayName") or payload.get("name") or kind),
        "status": _s(payload.get("status")),
        "category": _s(payload.get("category")) or None,
        "value_json": json.dumps(rec, ensure_ascii=False, sort_keys=True),
        "created_at": created,
        "updated_at": _s(payload.get("updatedAt")) or created,
        "sensitivity_ord": 2,
        **typed,
    }
    columns = ["vertex_id", "record_id", "owner_did", "listing_id", "app_did", "label", "status", "category", "value_json", "created_at", "updated_at", "sensitivity_ord", *typed]
    placeholders = ",".join(["%s"] * len(columns))
    updates = ",".join([f"{c}=EXCLUDED.{c}" for c in columns if c != "vertex_id"])
    with sync_cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO {table} ({",".join(columns)})
            VALUES ({placeholders})
            ON CONFLICT (vertex_id) DO UPDATE SET {updates}
            """,
            tuple(values[c] for c in columns),
        )
        _write_related_edges(cur, collection, kind, rid, rec, created)
    return rec


def _list(collection: str, limit: int = 500) -> list[dict[str, Any]]:
    table = COLLECTION_TABLES.get(collection)
    if table is None:
        return []
    rows = _fetch_all(
        f"SELECT value_json AS record_json FROM {table} ORDER BY created_at DESC LIMIT %s",
        (max(1, min(limit, 1000)),),
    )
    out: list[dict[str, Any]] = []
    for row in rows:
        try:
            parsed = json.loads(str(row["record_json"]))
        except (TypeError, ValueError):
            continue
        if isinstance(parsed, dict):
            out.append(parsed)
    return out


def _latest_listing(listing_id: str = "", app_did: str = "") -> dict[str, Any] | None:
    for item in _list("app.etzhayyim.apps.apps.appListing"):
        if listing_id and _s(item.get("listingId")) == listing_id:
            return item
        if app_did and _s(item.get("appDid")) == app_did:
            return item
    return None


def register_app_listing(appDid: Any = None, name: Any = None, displayName: Any = None, description: Any = None, category: Any = None, icon: Any = None, embedUrl: Any = None, capabilities: Any = None, **_: Any) -> dict[str, Any]:
    app_did = _s(appDid)
    app_name = _s(name)
    if not app_did or not app_name:
        return {"error": "appDid and name required"}
    listing_id = _id("listing")
    listing = {
        "listingId": listing_id,
        "appDid": app_did,
        "name": app_name,
        "displayName": _s(displayName) or app_name,
        "description": _s(description),
        "category": _s(category, "uncategorized"),
        "icon": _s(icon),
        "embedUrl": _s(embedUrl),
        "capabilities": _arr(capabilities),
        "status": "active",
    }
    _record("app.etzhayyim.apps.apps.appListing", "appListing", listing, listing_id)
    return {"listingId": listing_id, "status": "active"}


def update_app_listing(listingId: Any = None, **kwargs: Any) -> dict[str, Any]:
    listing_id = _s(listingId)
    existing = _latest_listing(listing_id=listing_id)
    if not listing_id or not existing:
        return {"error": "listing not found", "listingId": listing_id}
    next_listing = {**existing, "updatedAt": now_iso()}
    for key in ("displayName", "description", "category", "icon", "embedUrl"):
        if key in kwargs and kwargs[key] is not None:
            next_listing[key] = _s(kwargs[key])
    if isinstance(kwargs.get("capabilities"), list):
        next_listing["capabilities"] = _arr(kwargs["capabilities"])
    _record("app.etzhayyim.apps.apps.appListing", "appListing", next_listing, listing_id)
    return {"listingId": listing_id, "status": "updated"}


def list_apps(category: Any = None, search: Any = None, limit: Any = 50, offset: Any = 0, **_: Any) -> dict[str, Any]:
    try:
        lim = max(1, min(int(limit), 100))
    except (TypeError, ValueError):
        lim = 50
    try:
        off = max(0, int(offset))
    except (TypeError, ValueError):
        off = 0
    cat = _s(category).lower()
    needle = _s(search).lower()
    latest: dict[str, dict[str, Any]] = {}
    for item in reversed(_list("app.etzhayyim.apps.apps.appListing", 1000)):
        latest[_s(item.get("listingId"))] = item
    rows = list(latest.values())
    if cat:
        rows = [r for r in rows if _s(r.get("category")).lower() == cat]
    if needle:
        rows = [r for r in rows if needle in json.dumps(r, ensure_ascii=False).lower()]
    return {"apps": rows[off:off + lim], "total": len(rows), "limit": lim, "offset": off}


def get_app_listing(listingId: Any = None, appDid: Any = None, **_: Any) -> dict[str, Any]:
    return {"listing": _latest_listing(_s(listingId), _s(appDid)) or {}}


def feature_app(listingId: Any = None, rail: Any = "featured", rank: Any = 100, reason: Any = None, approvedByDid: Any = None, **_: Any) -> dict[str, Any]:
    listing_id = _s(listingId)
    if not listing_id:
        return {"error": "listingId required"}
    feature_id = _id("feature")
    try:
        rank_i = int(rank)
    except (TypeError, ValueError):
        rank_i = 100
    _record("app.etzhayyim.apps.apps.feature", "feature", {"featureId": feature_id, "listingId": listing_id, "rail": _s(rail, "featured"), "rank": rank_i, "reason": _s(reason), "approvedByDid": _s(approvedByDid), "status": "active"}, feature_id)
    return {"featureId": feature_id, "status": "active"}


def record_install_intent(listingId: Any = None, userDid: Any = None, source: Any = None, client: Any = None, **_: Any) -> dict[str, Any]:
    listing_id = _s(listingId)
    if not listing_id:
        return {"error": "listingId required"}
    intent_id = _id("install")
    _record("app.etzhayyim.apps.apps.installIntent", "installIntent", {"intentId": intent_id, "listingId": listing_id, "userDid": _s(userDid), "source": _s(source), "client": _s(client), "status": "recorded"}, intent_id)
    return {"intentId": intent_id, "status": "recorded"}
