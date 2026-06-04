"""etzhayyim Market XRPC primitives for BPMN/LangServer."""

from __future__ import annotations

import datetime as _dt
import decimal as _decimal
import hashlib
import time
import uuid
from typing import Any

from pymagatama.db_sync import sync_cursor


PRIMARY_DID = "did:web:market.etzhayyim.com"
APP_ID = "market"
VALID_LANES = {"vault", "sashiosae", "lawfirm", "bpmn", "murakumo"}
LANE_FLOOR_LIMIT = {
    "vault": {"maxNotional": 10000.0, "currency": "USDC"},
    "sashiosae": {"maxNotional": 5_000_000.0, "currency": "JPY"},
    "lawfirm": {"maxNotional": 50_000.0, "currency": "USDC"},
    "bpmn": {"maxNotional": 50_000.0, "currency": "USDC"},
    "murakumo": {"maxNotional": 100_000.0, "currency": "USDC"},
}


def _now() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _rkey() -> str:
    return f"{int(time.time() * 1000):x}{uuid.uuid4().hex[:8]}"[:12]


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


def _rows(cur: Any) -> list[dict[str, Any]]:
    cols = [d[0] for d in (cur.description or [])]
    return [{cols[i]: _jsonable(row[i]) for i in range(len(cols))} for row in cur.fetchall()]


def _lane(v: Any) -> str | None:
    lane = _str(v)
    return lane if lane in VALID_LANES else None


def _gate(input: dict[str, Any], lane: str) -> dict[str, Any]:
    limit = LANE_FLOOR_LIMIT.get(lane)
    if not limit:
        return {"floorPass": False, "spiritSeparationDelta": 1.0, "reason": f"unknown lane: {lane}"}
    price_unit = _num(input.get("priceUnit") or input.get("price_unit") or input.get("totalPrice") or input.get("total_price"), 0.0)
    quantity = _num(input.get("quantity"), 0.0)
    notional = price_unit if (input.get("totalPrice") is not None or input.get("total_price") is not None) else price_unit * quantity
    child_safe = input.get("child_safe") is True or input.get("childSafe") is True
    max_notional = float(limit["maxNotional"])
    if not child_safe and notional > max_notional:
        return {
            "floorPass": False,
            "spiritSeparationDelta": 0.4 + min(0.5, (notional - max_notional) / max_notional / 4),
            "reason": f"notional {notional} {limit['currency']} > floor {max_notional:g} {limit['currency']}; pass child_safe=true with explicit attestation if intentional",
        }
    return {"floorPass": True, "spiritSeparationDelta": -min(0.15, notional / max_notional / 10)}


def _anchor(issuer_did: str, lxm: str, quantity: float, unit_price: float, vertex_id: str, now: str) -> str:
    raw = f"{issuer_did}|{lxm}|{quantity}|{unit_price}|{vertex_id}|{now}".encode()
    return "anchor:sha256:" + hashlib.sha256(raw).hexdigest()


def task_market_list_offer(lane: Any = "", status: Any = "active", limit: Any = 50, offset: Any = 0, **_: Any) -> dict[str, Any]:
    limit_i = max(1, min(int(_num(limit, 50)), 200))
    offset_i = max(0, int(_num(offset, 0)))
    params: list[Any] = [_str(status) or "active"]
    where = "WHERE status = %s"
    lane_s = _lane(lane)
    if lane_s:
        where += " AND lane = %s"
        params.append(lane_s)
    params.extend([limit_i, offset_i])
    with sync_cursor() as cur:
        cur.execute(f"SELECT * FROM vertex_market_listing {where} ORDER BY published_at DESC LIMIT %s OFFSET %s", tuple(params))
        rows = _rows(cur)
    return {"listings": rows, "offers": rows, "limit": limit_i, "offset": offset_i}


def task_market_publish_offer(**body: Any) -> dict[str, Any]:
    lane = _lane(body.get("lane"))
    if not lane:
        return {"error": "InvalidLane", "validLanes": sorted(VALID_LANES)}
    title = _str(body.get("title"))
    actor_did = _str(body.get("actor_did")) or _str(body.get("actorDid")) or _str(body.get("issuerDid"))
    if not title:
        return {"error": "MissingTitle"}
    if not actor_did:
        return {"error": "MissingActorDid"}
    price_unit = _num(body.get("price_unit") or body.get("priceUnit"), 0.0)
    quantity = _num(body.get("quantity") or body.get("maxQuantity"), 1.0)
    gate = _gate({"priceUnit": price_unit, "quantity": quantity, **body}, lane)
    if not gate["floorPass"]:
        return {"error": "MokutekiFloorViolation", "reason": gate.get("reason")}

    listing_id = _rkey()
    now = _now()
    vertex_id = f"at://{PRIMARY_DID}/com.etzhayyim.market.listing/{listing_id}"
    issuer_did = _str(body.get("issuerDid")) or _str(body.get("issuer_did")) or f"did:erc725:etzhayyim:260425:{lane}"
    currency = _str(body.get("settlementCurrency")) or _str(body.get("settlement_currency")) or _str(body.get("currency")) or "JPY"
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_market_listing
              (vertex_id,created_date,sensitivity_ord,owner_did,listing_id,lane,issuer_did,title,description,
               price_unit,settlement_currency,min_quantity,max_quantity,terms_uri,status,mokuteki_floor_pass,
               spirit_separation_delta,published_at,created_at,org_id,user_id,actor_id,actor_did,org_did,
               at_did,quantity,currency)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, now[:10], 1, PRIMARY_DID, listing_id, lane, issuer_did, title,
                _str(body.get("description")), price_unit, currency, _num(body.get("minQuantity"), 0.0),
                _num(body.get("maxQuantity"), quantity), _str(body.get("termsUri")) or None, "active",
                bool(gate["floorPass"]), float(gate["spiritSeparationDelta"]), now, now,
                _str(body.get("org_id")) or PRIMARY_DID, actor_did, APP_ID, actor_did, _str(body.get("org_did")) or "anon",
                _str(body.get("at_did")) or None, quantity, currency,
            ),
        )
    return {
        "ok": True,
        "listingId": listing_id,
        "vertexId": vertex_id,
        "vertex_id": vertex_id,
        "status": "active",
        "mokutekiFloorPass": True,
        "mokuteki_floor_pass": True,
        "spiritSeparationDelta": gate["spiritSeparationDelta"],
    }


def _listing_by_id(listing_id: str) -> dict[str, Any] | None:
    with sync_cursor() as cur:
        cur.execute(
            "SELECT * FROM vertex_market_listing WHERE vertex_id = %s OR listing_id = %s LIMIT 1",
            (listing_id, listing_id),
        )
        rows = _rows(cur)
    return rows[0] if rows else None


def task_market_quote_price(listingId: Any = "", listing_vertex_id: Any = "", vertex_id: Any = "", quantity: Any = 1, **_: Any) -> dict[str, Any]:
    listing_key = _str(listingId) or _str(listing_vertex_id) or _str(vertex_id)
    if not listing_key:
        return {"error": "MissingListingVertexId"}
    listing = _listing_by_id(listing_key)
    if not listing:
        return {"error": "ListingNotFound"}
    if listing.get("status") != "active":
        return {"error": "ListingNotActive", "status": listing.get("status")}
    qty = _num(quantity, 1.0)
    max_qty = _num(listing.get("max_quantity"), qty)
    if qty > max_qty:
        return {"error": "InsufficientQuantity", "available": max_qty, "requested": qty}
    total = _num(listing.get("price_unit"), 0.0) * qty
    return {
        "ok": True,
        "listing_vertex_id": listing.get("vertex_id"),
        "listingId": listing.get("listing_id"),
        "lane": listing.get("lane"),
        "title": listing.get("title"),
        "price_unit": listing.get("price_unit"),
        "priceUnit": listing.get("price_unit"),
        "settlementCurrency": listing.get("settlement_currency"),
        "currency": listing.get("settlement_currency"),
        "quantity": qty,
        "total_price": total,
        "totalPrice": total,
        "expiresAt": (_dt.datetime.now(tz=_dt.UTC) + _dt.timedelta(seconds=60)).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }


def task_market_settle_invoice(**body: Any) -> dict[str, Any]:
    listing_key = _str(body.get("listing_vertex_id")) or _str(body.get("listingId")) or _str(body.get("listing_id"))
    actor_did = _str(body.get("actor_did")) or _str(body.get("actorDid")) or _str(body.get("payerDid")) or _str(body.get("payer_did"))
    if not listing_key:
        return {"error": "MissingListingVertexId"}
    if not actor_did:
        return {"error": "MissingActorDid"}
    listing = _listing_by_id(listing_key)
    if not listing:
        return {"error": "ListingNotFound"}
    if listing.get("status") != "active":
        return {"error": "ListingNotActive", "status": listing.get("status")}
    lane = _lane(listing.get("lane")) or "bpmn"
    quantity = _num(body.get("quantity"), 1.0)
    unit_price = _num(listing.get("price_unit"), 0.0)
    total_price = unit_price * quantity
    gate = _gate({"listing_vertex_id": listing_key, "quantity": quantity, "totalPrice": total_price, "lane": lane, **body}, lane)
    if not gate["floorPass"]:
        return {"error": "MokutekiFloorViolation", "reason": gate.get("reason")}

    invoice_id = _rkey()
    now = _now()
    vertex_id = f"at://{PRIMARY_DID}/com.etzhayyim.market.settlement/{invoice_id}"
    issuer_did = _str(listing.get("issuer_did")) or f"did:erc725:etzhayyim:260425:{lane}"
    payer_did = _str(body.get("payerDid")) or _str(body.get("payer_did")) or actor_did
    settlement_currency = _str(listing.get("settlement_currency")) or "USDC"
    anchor = _anchor(issuer_did, "com.etzhayyim.market.settleInvoice", quantity, unit_price, vertex_id, now)
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_market_settlement
              (vertex_id,created_date,sensitivity_ord,owner_did,invoice_id,listing_id,lane,issuer_did,payer_did,lxm,
               quantity,unit_price,total_price,settlement_currency,settlement_tx_hash,mokuteki_floor_pass,status,memo,
               enqueued_at,mined_at,created_at,org_id,user_id,actor_id,actor_did,org_did,
               at_did,listing_vertex_id,currency,settled_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, now[:10], 1, PRIMARY_DID, invoice_id, str(listing.get("listing_id") or listing_key),
                lane, issuer_did, payer_did, "com.etzhayyim.market.settleInvoice", quantity, unit_price, total_price,
                settlement_currency, anchor, True, "pending", _str(body.get("memo")) or None, now, None, now,
                PRIMARY_DID, actor_did, "com.etzhayyim.market.settleInvoice", actor_did, _str(body.get("org_did")) or "anon",
                _str(body.get("at_did")) or None, listing.get("vertex_id"), settlement_currency, None,
            ),
        )
    return {
        "ok": True,
        "invoiceId": invoice_id,
        "bundleQueueId": invoice_id,
        "vertex_id": vertex_id,
        "vertexId": vertex_id,
        "listing_vertex_id": listing.get("vertex_id"),
        "status": "pending",
        "total_price": total_price,
        "totalPrice": total_price,
        "currency": settlement_currency,
        "settlementTxHash": anchor,
        "settlement_tx_hash": anchor,
        "mokutekiFloorPass": True,
        "spiritSeparationDelta": gate["spiritSeparationDelta"],
    }


def task_market_observe_demand(**body: Any) -> dict[str, Any]:
    lane = _lane(body.get("lane")) or "bpmn"
    signal_kind = _str(body.get("signalKind")) or _str(body.get("signal_kind")) or "intent"
    actor_did = _str(body.get("actor_did")) or _str(body.get("actorDid")) or "anon"
    now = _now()
    observed_at = _str(body.get("observed_at")) or _str(body.get("observedAt")) or now
    vertex_id = f"at://{PRIMARY_DID}/com.etzhayyim.market.demandSignal/{_rkey()}"
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_market_demand_signal
              (vertex_id,created_date,sensitivity_ord,owner_did,signal_kind,lane,demand_hash,magnitude,
               observed_at,created_at,org_id,user_id,actor_id,actor_did,org_did,description,at_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, observed_at[:10], 1, PRIMARY_DID, signal_kind, lane,
                _str(body.get("demand_hash")) or _str(body.get("demandHash")) or "",
                _num(body.get("magnitude"), 1.0), observed_at, now, PRIMARY_DID, actor_did,
                "com.etzhayyim.market.observeDemand", actor_did, _str(body.get("org_did")) or "anon",
                _str(body.get("description")), _str(body.get("at_did")) or None,
            ),
        )
    return {"ok": True, "vertexId": vertex_id, "vertex_id": vertex_id, "lane": lane, "signal_kind": signal_kind}


def task_market_well_known(**_: Any) -> dict[str, Any]:
    with sync_cursor() as cur:
        cur.execute(
            """
            SELECT lane,issuer_did,title,description,price_unit,settlement_currency,min_quantity,max_quantity,published_at
            FROM vertex_market_listing
            WHERE status = 'active' AND mokuteki_floor_pass = TRUE
            """
        )
        listings = _rows(cur)
        cur.execute("SELECT lane,demand_total,supply_settled,vacuum_score FROM mv_market_vacuum_score")
        vacuum = _rows(cur)
    vacuum_by_lane: dict[str, dict[str, float]] = {}
    for v in vacuum:
        lane = str(v.get("lane") or "")
        cur = vacuum_by_lane.get(lane, {"demand": 0.0, "supply": 0.0, "vacuum": 0.0})
        cur["demand"] += _num(v.get("demand_total"), 0.0)
        cur["supply"] += _num(v.get("supply_settled"), 0.0)
        cur["vacuum"] += _num(v.get("vacuum_score"), 0.0)
        vacuum_by_lane[lane] = cur
    return {
        "@context": "https://etzhayyim.com/ns/market/v1",
        "actor": PRIMARY_DID,
        "adr": "2605011300",
        "phase": "1.2",
        "lanes": [
            {
                "lane": lane,
                "issuer_did": f"did:erc725:etzhayyim:260425:{lane}",
                "vacuum": vacuum_by_lane.get(lane, {"demand": 0, "supply": 0, "vacuum": 0}),
                "listings": [
                    {
                        "title": l.get("title"),
                        "description": l.get("description"),
                        "price_unit": l.get("price_unit"),
                        "settlement_currency": l.get("settlement_currency"),
                        "min_quantity": l.get("min_quantity"),
                        "max_quantity": l.get("max_quantity"),
                        "published_at": l.get("published_at"),
                    }
                    for l in listings
                    if l.get("lane") == lane
                ],
            }
            for lane in sorted(VALID_LANES)
        ],
        "nsids": {
            "list": "https://market.etzhayyim.com/xrpc/com.etzhayyim.market.listOffer",
            "quote": "https://market.etzhayyim.com/xrpc/com.etzhayyim.market.quotePrice",
            "publish": "https://market.etzhayyim.com/xrpc/com.etzhayyim.market.publishOffer",
            "settle": "https://market.etzhayyim.com/xrpc/com.etzhayyim.market.settleInvoice",
            "observe": "https://market.etzhayyim.com/xrpc/com.etzhayyim.market.observeDemand",
        },
        "auth": "Service Auth ES256 JWT, lxm-scoped, <=60s lifetime",
    }


def register(worker: Any, *, timeout_ms: int = 60_000) -> None:
    tasks = {
        "xrpc.com.etzhayyim.market.listOffer": task_market_list_offer,
        "xrpc.com.etzhayyim.market.observeDemand": task_market_observe_demand,
        "xrpc.com.etzhayyim.market.publishOffer": task_market_publish_offer,
        "xrpc.com.etzhayyim.market.quotePrice": task_market_quote_price,
        "xrpc.com.etzhayyim.market.settleInvoice": task_market_settle_invoice,
        "xrpc.com.etzhayyim.market.wellKnownMarket": task_market_well_known,
    }
    for task_type, handler in tasks.items():
        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(handler)
