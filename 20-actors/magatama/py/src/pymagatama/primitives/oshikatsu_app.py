"""Oshikatsu creator subscription XRPC primitives for BPMN/LangServer."""

from __future__ import annotations

import datetime as _dt
import decimal as _decimal
import json
import time
import uuid
from typing import Any

from pymagatama.db_sync import sync_cursor


APP_DID = "did:web:oshikatsu.etzhayyim.com"
APP_ID = "dyd3lr50"
TIER_RANK = {"free": 0, "supporter": 1, "premium": 2, "vip": 3}
DEFAULT_TIERS = [
    {"name": "free", "priceCredits": 0, "label": "Free", "description": "Public content only"},
    {"name": "supporter", "priceCredits": 500, "label": "Supporter", "description": "Exclusive posts and early access"},
    {"name": "premium", "priceCredits": 2000, "label": "Premium", "description": "All content, DM access, behind-the-scenes"},
    {"name": "vip", "priceCredits": 5000, "label": "VIP", "description": "Everything + 1-on-1 sessions, custom content requests"},
]


def _now() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _id(prefix: str) -> str:
    return f"{prefix}_{int(time.time() * 1000):x}_{uuid.uuid4().hex[:8]}"


def _str(v: Any) -> str:
    return v if isinstance(v, str) else ""


def _num(v: Any, fallback: float = 0.0) -> float:
    try:
        n = float(v)
        return n if n == n and n not in (float("inf"), float("-inf")) else fallback
    except (TypeError, ValueError):
        return fallback


def _jsonable(v: Any) -> Any:
    if isinstance(v, (_dt.datetime, _dt.date)):
        return v.isoformat()
    if isinstance(v, _decimal.Decimal):
        f = float(v)
        return int(f) if f.is_integer() else f
    return v


def _vertex_id(kind: str, key: str) -> str:
    return f"at://{APP_DID}/app.etzhayyim.apps.oshikatsu.{kind}/{key}"


def _edge_id(kind: str, src: str, dst: str) -> str:
    return f"at://{APP_DID}/app.etzhayyim.apps.oshikatsu.edge/{kind}:{src}:{dst}"[:512]


def _rows(cur: Any) -> list[dict[str, Any]]:
    cols = [d[0] for d in (cur.description or [])]
    out: list[dict[str, Any]] = []
    for row in cur.fetchall():
        raw = {cols[i]: _jsonable(row[i]) for i in range(len(cols))}
        for key in ("tiers", "media_urls"):
            if isinstance(raw.get(key), str) and raw[key].startswith("["):
                try:
                    raw[key] = json.loads(raw[key])
                except json.JSONDecodeError:
                    pass
        aliases = {
            "vertex_id": "vertexId",
            "creator_did": "creatorDid",
            "display_name": "displayName",
            "subscriber_count": "subscriberCount",
            "total_earned_credits": "totalEarnedCredits",
            "tier_id": "tierId",
            "price_credits": "priceCredits",
            "subscriber_did": "subscriberDid",
            "started_at": "startedAt",
            "expires_at": "expiresAt",
            "auto_renew": "autoRenew",
            "cancelled_at": "cancelledAt",
            "content_type": "contentType",
            "min_tier": "minTier",
            "media_urls": "mediaUrls",
            "preview_text": "previewText",
            "like_count": "likeCount",
            "comment_count": "commentCount",
            "tip_total_credits": "tipTotalCredits",
            "published_at": "publishedAt",
            "from_did": "fromDid",
            "created_at": "createdAt",
            "updated_at": "updatedAt",
        }
        for src, dst in aliases.items():
            if src in raw and dst not in raw:
                raw[dst] = raw[src]
        out.append(raw)
    return out


def _write(kind: str, rec: dict[str, Any]) -> dict[str, Any]:
    record = {**rec, "orgId": rec.get("orgId") or "anon", "actorId": rec.get("actorId") or APP_ID}
    with sync_cursor() as cur:
        if kind == "creatorProfile":
            vid = _vertex_id("creatorProfile", _str(record["id"]))
            cur.execute(
                """
                INSERT INTO vertex_oshikatsu_creator_profile
                  (vertex_id,id,creator_did,display_name,bio,tiers,subscriber_count,total_earned_credits,status,created_at,org_id,user_id,actor_id,sensitivity_ord,owner_did)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (vertex_id) DO UPDATE SET
                  display_name=EXCLUDED.display_name,bio=EXCLUDED.bio,tiers=EXCLUDED.tiers,status=EXCLUDED.status
                """,
                (vid, record["id"], record["creatorDid"], record["displayName"], record.get("bio", ""), json.dumps(record.get("tiers") or [], ensure_ascii=False), int(_num(record.get("subscriberCount"))), _num(record.get("totalEarnedCredits")), record.get("status", "active"), record.get("createdAt") or _now(), record["orgId"], record.get("userId") or record["creatorDid"], record["actorId"], 2, APP_DID),
            )
            return {"uri": vid}
        if kind == "subscriptionTier":
            vid = _vertex_id("subscriptionTier", _str(record["tierId"]))
            cur.execute(
                """
                INSERT INTO vertex_oshikatsu_subscription_tier
                  (vertex_id,tier_id,rank,name,label,price_credits,description,creator_did,updated_at,org_id,user_id,actor_id,sensitivity_ord,owner_did)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (vertex_id) DO UPDATE SET
                  rank=EXCLUDED.rank,name=EXCLUDED.name,label=EXCLUDED.label,price_credits=EXCLUDED.price_credits,description=EXCLUDED.description,updated_at=EXCLUDED.updated_at
                """,
                (vid, record["tierId"], int(_num(record.get("rank"))), record.get("name", ""), record.get("label", ""), _num(record.get("priceCredits")), record.get("description", ""), record.get("creatorDid", ""), record.get("updatedAt") or _now(), record["orgId"], record.get("userId") or record.get("creatorDid", ""), record["actorId"], 2, APP_DID),
            )
            creator = _find("creatorProfile", "creatorDid", _str(record.get("creatorDid")))
            if creator:
                cur.execute(
                    "INSERT INTO edge_oshikatsu_creator_tier (edge_id,src_vid,dst_vid,creator_did,tier_id,relation,created_at,owner_did,sensitivity_ord) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (edge_id) DO NOTHING",
                    (_edge_id("creatorTier", _str(creator.get("vertexId")), vid), creator.get("vertexId"), vid, record.get("creatorDid"), record["tierId"], "HAS_TIER", _now(), APP_DID, 2),
                )
            return {"uri": vid}
        if kind == "subscription":
            vid = _vertex_id("subscription", _str(record["id"]))
            cur.execute(
                """
                INSERT INTO vertex_oshikatsu_subscription
                  (vertex_id,id,subscriber_did,creator_did,tier,price_credits,status,started_at,expires_at,auto_renew,created_at,org_id,user_id,actor_id,sensitivity_ord,owner_did)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (vertex_id) DO UPDATE SET status=EXCLUDED.status,tier=EXCLUDED.tier,expires_at=EXCLUDED.expires_at
                """,
                (vid, record["id"], record["subscriberDid"], record["creatorDid"], record.get("tier", ""), _num(record.get("priceCredits")), record.get("status", "active"), record.get("startedAt") or _now(), record.get("expiresAt", ""), bool(record.get("autoRenew", True)), record.get("createdAt") or _now(), record["orgId"], record.get("userId") or record["subscriberDid"], record["actorId"], 2, APP_DID),
            )
            cur.execute(
                "INSERT INTO edge_oshikatsu_subscription (edge_id,src_vid,dst_vid,subscriber_did,creator_did,subscription_id,tier,relation,created_at,owner_did,sensitivity_ord) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (edge_id) DO NOTHING",
                (_edge_id("subscription", record["subscriberDid"], record["creatorDid"]), record["subscriberDid"], record["creatorDid"], record["subscriberDid"], record["creatorDid"], record["id"], record.get("tier", ""), "SUBSCRIBES_TO", record.get("createdAt") or _now(), APP_DID, 2),
            )
            return {"uri": vid}
        if kind == "subscriptionCancel":
            vid = _vertex_id("subscriptionCancel", _str(record["id"]))
            cur.execute(
                "INSERT INTO vertex_oshikatsu_subscription_cancel (vertex_id,id,subscriber_did,creator_did,cancelled_at,org_id,user_id,actor_id,sensitivity_ord,owner_did) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (vertex_id) DO NOTHING",
                (vid, record["id"], record["subscriberDid"], record["creatorDid"], record.get("cancelledAt") or _now(), record["orgId"], record.get("userId") or record["subscriberDid"], record["actorId"], 2, APP_DID),
            )
            return {"uri": vid}
        if kind == "exclusiveContent":
            vid = _vertex_id("exclusiveContent", _str(record["id"]))
            cur.execute(
                """
                INSERT INTO vertex_oshikatsu_exclusive_content
                  (vertex_id,id,creator_did,title,body,content_type,min_tier,media_urls,preview_text,like_count,comment_count,tip_total_credits,status,published_at,created_at,org_id,user_id,actor_id,sensitivity_ord,owner_did)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (vertex_id) DO UPDATE SET title=EXCLUDED.title,body=EXCLUDED.body,status=EXCLUDED.status
                """,
                (vid, record["id"], record["creatorDid"], record["title"], record.get("body", ""), record.get("contentType", "post"), record.get("minTier", "supporter"), json.dumps(record.get("mediaUrls") or [], ensure_ascii=False), record.get("previewText", ""), int(_num(record.get("likeCount"))), int(_num(record.get("commentCount"))), _num(record.get("tipTotalCredits")), record.get("status", "published"), record.get("publishedAt") or _now(), record.get("createdAt") or _now(), record["orgId"], record.get("userId") or record["creatorDid"], record["actorId"], 2, APP_DID),
            )
            cur.execute(
                "INSERT INTO edge_oshikatsu_content_by_creator (edge_id,src_vid,dst_vid,creator_did,content_id,relation,created_at,owner_did,sensitivity_ord) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (edge_id) DO NOTHING",
                (_edge_id("contentBy", record["creatorDid"], record["id"]), record["creatorDid"], vid, record["creatorDid"], record["id"], "PUBLISHED", record.get("createdAt") or _now(), APP_DID, 2),
            )
            return {"uri": vid}
        if kind == "tip":
            vid = _vertex_id("tip", _str(record["id"]))
            cur.execute(
                "INSERT INTO vertex_oshikatsu_tip (vertex_id,id,from_did,creator_did,content_id,amount,message,created_at,org_id,user_id,actor_id,sensitivity_ord,owner_did) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (vertex_id) DO NOTHING",
                (vid, record["id"], record["fromDid"], record["creatorDid"], record.get("contentId", ""), _num(record.get("amount")), record.get("message", ""), record.get("createdAt") or _now(), record["orgId"], record.get("userId") or record["fromDid"], record["actorId"], 2, APP_DID),
            )
            cur.execute(
                "INSERT INTO edge_oshikatsu_tip_to_creator (edge_id,src_vid,dst_vid,from_did,creator_did,tip_id,amount,relation,created_at,owner_did,sensitivity_ord) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (edge_id) DO NOTHING",
                (_edge_id("tipTo", record["fromDid"], record["id"]), record["fromDid"], record["creatorDid"], record["fromDid"], record["creatorDid"], record["id"], _num(record.get("amount")), "TIPPED", record.get("createdAt") or _now(), APP_DID, 2),
            )
            if record.get("contentId"):
                cur.execute(
                    "INSERT INTO edge_oshikatsu_tip_for_content (edge_id,src_vid,dst_vid,tip_id,content_id,relation,created_at,owner_did,sensitivity_ord) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (edge_id) DO NOTHING",
                    (_edge_id("tipFor", record["id"], record["contentId"]), vid, _vertex_id("exclusiveContent", _str(record["contentId"])), record["id"], record["contentId"], "TIPS_CONTENT", record.get("createdAt") or _now(), APP_DID, 2),
                )
            return {"uri": vid}
    raise ValueError(f"unknown oshikatsu kind: {kind}")


def _list(kind: str, *, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    tables = {
        "creatorProfile": ("vertex_oshikatsu_creator_profile", "created_at"),
        "subscriptionTier": ("vertex_oshikatsu_subscription_tier", "updated_at"),
        "subscription": ("vertex_oshikatsu_subscription", "created_at"),
        "subscriptionCancel": ("vertex_oshikatsu_subscription_cancel", "cancelled_at"),
        "exclusiveContent": ("vertex_oshikatsu_exclusive_content", "created_at"),
        "tip": ("vertex_oshikatsu_tip", "created_at"),
    }
    table, order_col = tables[kind]
    with sync_cursor() as cur:
        cur.execute(
            f"SELECT * FROM {table} ORDER BY {order_col} DESC LIMIT %s OFFSET %s",
            (max(1, min(limit, 500)), max(0, offset)),
        )
        return _rows(cur)


def _find(kind: str, key: str, value: str) -> dict[str, Any] | None:
    for row in _list(kind, limit=500):
        if str(row.get(key) or "") == value:
            return row
    return None


def _tiers(raw: Any, creator_did: str = "") -> list[dict[str, Any]]:
    arr = raw if isinstance(raw, list) else DEFAULT_TIERS
    out = []
    for i, t in enumerate(arr):
        t = t if isinstance(t, dict) else {}
        out.append({
            "tierId": _str(t.get("tierId")) or _id("tier"),
            "rank": i,
            "name": _str(t.get("name")),
            "label": _str(t.get("label")) or _str(t.get("name")),
            "priceCredits": _num(t.get("priceCredits")),
            "description": _str(t.get("description")),
            "creatorDid": creator_did,
            "updatedAt": _now(),
        })
    return out


def task_oshikatsu_create_creator_profile(creatorDid: str = "", displayName: str = "", bio: str = "", tiers: Any = None, **_: Any) -> dict[str, Any]:
    if not creatorDid or not displayName:
        return {"error": "creatorDid and displayName required"}
    creator_id = _id("creator")
    tier_rows = _tiers(tiers, creatorDid)
    record = {"id": creator_id, "creatorDid": creatorDid, "displayName": displayName, "bio": bio, "tiers": tier_rows, "subscriberCount": 0, "totalEarnedCredits": 0, "status": "active", "createdAt": _now(), "userId": creatorDid}
    _write("creatorProfile", record)
    for tier in tier_rows:
        _write("subscriptionTier", {**tier, "userId": creatorDid})
    return {"id": creator_id, "creatorDid": creatorDid, "tiers": tier_rows, "status": "created"}


def task_oshikatsu_get_creator_profile(creatorDid: str = "", **_: Any) -> dict[str, Any]:
    if not creatorDid:
        return {"error": "creatorDid required"}
    profile = _find("creatorProfile", "creatorDid", creatorDid)
    if not profile:
        return {"error": "creator not found"}
    tiers = [t for t in _list("subscriptionTier", limit=500) if t.get("creatorDid") == creatorDid]
    return {**profile, "tiers": sorted(tiers, key=lambda r: int(_num(r.get("rank"), 0)))}


def task_oshikatsu_list_creators(limit: Any = 50, offset: Any = 0, **_: Any) -> dict[str, Any]:
    rows = [r for r in _list("creatorProfile", limit=int(_num(limit, 50)), offset=int(_num(offset, 0))) if r.get("status") == "active"]
    return {"items": rows, "offset": int(_num(offset, 0)), "limit": int(_num(limit, 50))}


def task_oshikatsu_update_tiers(creatorDid: str = "", tiers: Any = None, **_: Any) -> dict[str, Any]:
    if not creatorDid or not isinstance(tiers, list):
        return {"error": "creatorDid and tiers[] required"}
    rows = _tiers(tiers, creatorDid)
    for tier in rows:
        _write("subscriptionTier", {**tier, "userId": creatorDid})
    return {"creatorDid": creatorDid, "tiers": rows, "status": "updated"}


def task_oshikatsu_subscribe(subscriberDid: str = "", creatorDid: str = "", tier: str = "supporter", **_: Any) -> dict[str, Any]:
    if not subscriberDid or not creatorDid:
        return {"error": "subscriberDid and creatorDid required"}
    existing = [s for s in _list("subscription", limit=500) if s.get("subscriberDid") == subscriberDid and s.get("creatorDid") == creatorDid and s.get("status") == "active"]
    if existing:
        return {"error": "alreadySubscribed", "currentTier": existing[0].get("tier")}
    tier_rows = [t for t in _list("subscriptionTier", limit=500) if t.get("creatorDid") == creatorDid and t.get("name") == tier]
    price = _num(tier_rows[0].get("priceCredits")) if tier_rows else 0
    sub_id = _id("sub")
    expires = (_dt.datetime.now(tz=_dt.UTC) + _dt.timedelta(days=30)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    _write("subscription", {"id": sub_id, "subscriberDid": subscriberDid, "creatorDid": creatorDid, "tier": tier, "priceCredits": price, "status": "active", "startedAt": _now(), "expiresAt": expires, "autoRenew": True, "createdAt": _now(), "userId": subscriberDid})
    return {"id": sub_id, "tier": tier, "priceCredits": price, "expiresAt": expires, "status": "active"}


def task_oshikatsu_unsubscribe(subscriberDid: str = "", creatorDid: str = "", **_: Any) -> dict[str, Any]:
    if not subscriberDid or not creatorDid:
        return {"error": "subscriberDid and creatorDid required"}
    cancel_id = _id("unsub")
    _write("subscriptionCancel", {"id": cancel_id, "subscriberDid": subscriberDid, "creatorDid": creatorDid, "cancelledAt": _now(), "userId": subscriberDid})
    return {"status": "cancelled", "subscriberDid": subscriberDid, "creatorDid": creatorDid}


def task_oshikatsu_list_subscriptions(subscriberDid: str = "", creatorDid: str = "", limit: Any = 50, offset: Any = 0, **_: Any) -> dict[str, Any]:
    if not subscriberDid and not creatorDid:
        return {"error": "subscriberDid or creatorDid required"}
    rows = _list("subscription", limit=500)
    if subscriberDid:
        rows = [r for r in rows if r.get("subscriberDid") == subscriberDid]
    if creatorDid:
        rows = [r for r in rows if r.get("creatorDid") == creatorDid]
    off = int(_num(offset, 0))
    lim = int(_num(limit, 50))
    return {"items": rows[off:off + lim], "offset": off, "limit": lim}


def _has_access(subscriber_did: str, creator_did: str, required_tier: str) -> dict[str, Any]:
    if required_tier == "free":
        return {"hasAccess": True, "tier": "free"}
    subs = [s for s in _list("subscription", limit=500) if s.get("subscriberDid") == subscriber_did and s.get("creatorDid") == creator_did and s.get("status") == "active"]
    if not subs:
        return {"hasAccess": False, "reason": "notSubscribed"}
    sub = subs[0]
    if TIER_RANK.get(str(sub.get("tier")), 0) < TIER_RANK.get(required_tier, 0):
        return {"hasAccess": False, "reason": "tierInsufficient", "currentTier": sub.get("tier"), "requiredTier": required_tier}
    return {"hasAccess": True, "tier": sub.get("tier"), "expiresAt": sub.get("expiresAt")}


def task_oshikatsu_check_access(subscriberDid: str = "", creatorDid: str = "", requiredTier: str = "free", **_: Any) -> dict[str, Any]:
    if not subscriberDid or not creatorDid:
        return {"error": "subscriberDid and creatorDid required"}
    return _has_access(subscriberDid, creatorDid, requiredTier or "free")


def task_oshikatsu_publish_content(creatorDid: str = "", title: str = "", body: str = "", contentType: str = "post", minTier: str = "supporter", mediaUrls: Any = None, previewText: str = "", **_: Any) -> dict[str, Any]:
    if not creatorDid or not title:
        return {"error": "creatorDid and title required"}
    content_id = _id("content")
    _write("exclusiveContent", {"id": content_id, "creatorDid": creatorDid, "title": title, "body": body, "contentType": contentType or "post", "minTier": minTier or "supporter", "mediaUrls": mediaUrls if isinstance(mediaUrls, list) else [], "previewText": previewText, "likeCount": 0, "commentCount": 0, "tipTotalCredits": 0, "status": "published", "publishedAt": _now(), "createdAt": _now(), "userId": creatorDid})
    return {"id": content_id, "title": title, "minTier": minTier or "supporter", "status": "published"}


def task_oshikatsu_get_content(contentId: str = "", viewerDid: str = "", **_: Any) -> dict[str, Any]:
    if not contentId:
        return {"error": "contentId required"}
    content = _find("exclusiveContent", "id", contentId)
    if not content:
        return {"error": "content not found"}
    min_tier = _str(content.get("minTier")) or "free"
    if min_tier == "free" or viewerDid == content.get("creatorDid"):
        return content
    if not viewerDid:
        return {**content, "body": "", "mediaUrls": [], "locked": True, "reason": "loginRequired"}
    access = _has_access(viewerDid, _str(content.get("creatorDid")), min_tier)
    if not access.get("hasAccess"):
        return {**content, "body": "", "mediaUrls": [], "locked": True, **access}
    return content


def task_oshikatsu_list_content(creatorDid: str = "", viewerDid: str = "", limit: Any = 20, offset: Any = 0, **_: Any) -> dict[str, Any]:
    if not creatorDid:
        return {"error": "creatorDid required"}
    rows = [r for r in _list("exclusiveContent", limit=500) if r.get("creatorDid") == creatorDid]
    out = []
    for c in rows:
        if viewerDid == creatorDid or _has_access(viewerDid, creatorDid, _str(c.get("minTier")) or "free").get("hasAccess"):
            out.append(c)
        else:
            out.append({**c, "body": "", "mediaUrls": [], "locked": True})
    off = int(_num(offset, 0))
    lim = int(_num(limit, 20))
    return {"items": out[off:off + lim], "offset": off, "limit": lim}


def task_oshikatsu_tip(fromDid: str = "", creatorDid: str = "", amount: Any = 0, contentId: str = "", message: str = "", **_: Any) -> dict[str, Any]:
    amt = _num(amount)
    if not fromDid or not creatorDid or amt <= 0:
        return {"error": "fromDid, creatorDid, and positive amount required"}
    tip_id = _id("tip")
    _write("tip", {"id": tip_id, "fromDid": fromDid, "creatorDid": creatorDid, "contentId": contentId, "amount": amt, "message": message, "createdAt": _now(), "userId": fromDid})
    return {"id": tip_id, "amount": amt, "status": "completed"}


def task_oshikatsu_creator_stats(creatorDid: str = "", **_: Any) -> dict[str, Any]:
    if not creatorDid:
        return {"error": "creatorDid required"}
    subs = [s for s in _list("subscription", limit=500) if s.get("creatorDid") == creatorDid and s.get("status") == "active"]
    contents = [c for c in _list("exclusiveContent", limit=500) if c.get("creatorDid") == creatorDid]
    tips = [t for t in _list("tip", limit=500) if t.get("creatorDid") == creatorDid]
    return {"creatorDid": creatorDid, "activeSubscribers": len(subs), "publishedContent": len(contents), "totalTipsCredits": sum(_num(t.get("amount")) for t in tips)}


def task_oshikatsu_search(q: str = "", limit: Any = 20, **_: Any) -> dict[str, Any]:
    term = q.lower()
    if not term:
        return {"items": []}
    rows = [r for r in _list("creatorProfile", limit=500) if term in _str(r.get("displayName")).lower() or term in _str(r.get("bio")).lower()]
    return {"items": rows[: int(_num(limit, 20))]}


def register(worker: Any, *, timeout_ms: int = 60_000) -> None:
    tasks = {
        "xrpc.app.etzhayyim.apps.oshikatsu.checkAccess": task_oshikatsu_check_access,
        "xrpc.app.etzhayyim.apps.oshikatsu.createCreatorProfile": task_oshikatsu_create_creator_profile,
        "xrpc.app.etzhayyim.apps.oshikatsu.creatorStats": task_oshikatsu_creator_stats,
        "xrpc.app.etzhayyim.apps.oshikatsu.getContent": task_oshikatsu_get_content,
        "xrpc.app.etzhayyim.apps.oshikatsu.getCreatorProfile": task_oshikatsu_get_creator_profile,
        "xrpc.app.etzhayyim.apps.oshikatsu.listContent": task_oshikatsu_list_content,
        "xrpc.app.etzhayyim.apps.oshikatsu.listCreators": task_oshikatsu_list_creators,
        "xrpc.app.etzhayyim.apps.oshikatsu.listSubscriptions": task_oshikatsu_list_subscriptions,
        "xrpc.app.etzhayyim.apps.oshikatsu.publishContent": task_oshikatsu_publish_content,
        "xrpc.app.etzhayyim.apps.oshikatsu.search": task_oshikatsu_search,
        "xrpc.app.etzhayyim.apps.oshikatsu.subscribe": task_oshikatsu_subscribe,
        "xrpc.app.etzhayyim.apps.oshikatsu.tip": task_oshikatsu_tip,
        "xrpc.app.etzhayyim.apps.oshikatsu.unsubscribe": task_oshikatsu_unsubscribe,
        "xrpc.app.etzhayyim.apps.oshikatsu.updateTiers": task_oshikatsu_update_tiers,
    }
    for task_type, handler in tasks.items():
        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(handler)
