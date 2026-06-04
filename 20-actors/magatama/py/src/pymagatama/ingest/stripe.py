"""Stripe Issuing handlers for BPMN + Zeebe."""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
import uuid
from typing import Any

from pymagatama.db_sync import sync_cursor
from pymagatama.ingest import credits

ACTOR = "did:web:stripe.etzhayyim.com"


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _str(value: Any) -> str:
    return "" if value is None else str(value)


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


def _gid(prefix: str) -> str:
    return f"{prefix}_{int(time.time() * 1000):x}_{uuid.uuid4().hex[:8]}"


def _rkey(value: str) -> str:
    return "".join(c if c.isalnum() or c in "._~-" else "-" for c in value.lower())[:220] or uuid.uuid4().hex


def _execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        return int(cur.rowcount or 0)


def _fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in (cur.fetchall() or [])]


def _fetch_one(sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    rows = _fetch_all(sql, params)
    return rows[0] if rows else None


def _stripe_form(data: dict[str, Any]) -> bytes:
    pairs: list[tuple[str, str]] = []

    def add(prefix: str, value: Any) -> None:
        if value is None:
            return
        if isinstance(value, dict):
            for k, v in value.items():
                add(f"{prefix}[{k}]", v)
        elif isinstance(value, list):
            for i, v in enumerate(value):
                add(f"{prefix}[{i}]", v)
        else:
            pairs.append((prefix, str(value)))

    for key, value in data.items():
        add(key, value)
    return urllib.parse.urlencode(pairs).encode()


def _stripe(method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    key = os.environ.get("STRIPE_SECRET_KEY") or os.environ.get("SS_STRIPE_SECRET_KEY") or ""
    if not key:
        return {"error": "stripeNotConfigured"}
    req = urllib.request.Request(
        f"https://api.stripe.com/v1{path}",
        method=method,
        data=None if method == "GET" else _stripe_form(body or {}),
        headers={"authorization": f"Bearer {key}", "content-type": "application/x-www-form-urlencoded", "user-agent": "etzhayyim-stripe-zeebe/1"},
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw)
        except Exception:
            data = {"raw": raw[:500]}
        return {"error": "stripeApiError", "status": e.code, "detail": data}


def _normalize_cardholder(row: dict[str, Any]) -> dict[str, Any]:
    return {"id": row.get("id"), "userId": row.get("user_id"), "name": row.get("name"), "email": row.get("email"), "phone": row.get("phone"), "authTier": row.get("auth_tier"), "stripeCardholderId": row.get("stripe_cardholder_id"), "status": row.get("status"), "orgId": row.get("org_id"), "actorId": row.get("actor_id"), "createdAt": row.get("created_at")}


def _normalize_card(row: dict[str, Any]) -> dict[str, Any]:
    return {"id": row.get("id"), "cardholderId": row.get("cardholder_id"), "userId": row.get("user_id"), "cardType": row.get("card_type"), "status": row.get("status"), "lastFour": row.get("last_four"), "currency": row.get("currency"), "spendingLimitAmount": _int(row.get("spending_limit_amount")), "spendingLimitInterval": row.get("spending_limit_interval"), "stripeCardId": row.get("stripe_card_id"), "createdAt": row.get("created_at"), "updatedAt": row.get("updated_at")}


def _normalize_auth(row: dict[str, Any]) -> dict[str, Any]:
    return {"id": row.get("id"), "cardId": row.get("card_id"), "userId": row.get("user_id"), "stripeCardId": row.get("stripe_card_id"), "amount": _int(row.get("amount")), "currency": row.get("currency"), "decision": row.get("decision"), "reason": row.get("reason"), "availableBefore": _int(row.get("available_before")), "availableAfter": _int(row.get("available_after")), "createdAt": row.get("created_at")}


def _cardholder(user_id: str, active: bool = False) -> dict[str, Any] | None:
    sql = "SELECT * FROM vertex_stripe_cardholder WHERE user_id=%s"
    params: tuple[Any, ...] = (user_id,)
    if active:
        sql += " AND status='active'"
    row = _fetch_one(sql + " LIMIT 1", params)
    return _normalize_cardholder(row) if row else None


def _card(user_id: str, card_id: str) -> dict[str, Any] | None:
    row = _fetch_one("SELECT * FROM vertex_stripe_issued_card WHERE user_id=%s AND id=%s LIMIT 1", (user_id, card_id))
    return _normalize_card(row) if row else None


def _card_by_stripe(stripe_card_id: str) -> dict[str, Any] | None:
    row = _fetch_one("SELECT * FROM vertex_stripe_issued_card WHERE stripe_card_id=%s LIMIT 1", (stripe_card_id,))
    return _normalize_card(row) if row else None


def _auth_tier(user_id: str) -> str:
    for col in ("membership_plan", "\"membershipPlan\""):
        try:
            row = _fetch_one(f"SELECT {col} AS plan FROM vertex_auth_account WHERE user_id=%s LIMIT 1", (user_id,))
            plan = _str((row or {}).get("plan"))
            if plan in ("telecom", "verified"):
                return plan
        except Exception:
            pass
    return "guest"


def _insert_cardholder(record: dict[str, Any]) -> None:
    _execute(
        """INSERT INTO vertex_stripe_cardholder
        (vertex_id, sensitivity_ord, owner_did, rkey, repo, collection, status, id, user_id, name, email, phone, auth_tier, stripe_cardholder_id, org_id, actor_id, created_at, actor_did, org_did)
        VALUES (%s,1,%s,%s,%s,'com.etzhayyim.apps.stripe.cardholder',%s,%s,%s,%s,%s,%s,%s,%s,'anon',%s,%s,%s,'anon')
        ON CONFLICT (vertex_id) DO NOTHING""",
        (f"at://{ACTOR}/com.etzhayyim.apps.stripe.cardholder/{_rkey(record['id'])}", ACTOR, record["id"], ACTOR, record["status"], record["id"], record["userId"], record["name"], record["email"], record.get("phone", ""), record["authTier"], record["stripeCardholderId"], ACTOR, record["createdAt"], ACTOR),
    )


def _insert_card(record: dict[str, Any]) -> None:
    _execute(
        """INSERT INTO vertex_stripe_issued_card
        (vertex_id, sensitivity_ord, owner_did, rkey, repo, collection, status, id, cardholder_id, user_id, card_type, last_four, currency, spending_limit_amount, spending_limit_interval, stripe_card_id, org_id, actor_id, created_at, updated_at, actor_did, org_did)
        VALUES (%s,1,%s,%s,%s,'com.etzhayyim.apps.stripe.issuedCard',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'anon',%s,%s,%s,%s,'anon')
        ON CONFLICT (vertex_id) DO NOTHING""",
        (f"at://{ACTOR}/com.etzhayyim.apps.stripe.issuedCard/{_rkey(record['id'])}", ACTOR, record["id"], ACTOR, record["status"], record["id"], record["cardholderId"], record["userId"], record["cardType"], record["lastFour"], record["currency"], record["spendingLimitAmount"], record["spendingLimitInterval"], record["stripeCardId"], ACTOR, record["createdAt"], record.get("updatedAt", ""), ACTOR),
    )


def create_cardholder(userId: str = "", name: str = "", email: str = "", phone: str = "", billingAddress: dict[str, Any] | None = None, **_: Any) -> dict[str, Any]:
    if not userId or not name or not email:
        return {"error": "missingRequiredFields", "required": ["userId", "name", "email"]}
    tier = _auth_tier(userId)
    if tier == "guest":
        return {"error": "authTierInsufficient", "required": "verified", "current": tier}
    existing = _cardholder(userId)
    if existing:
        return {"error": "cardholderAlreadyExists", "cardholder": existing}
    result = _stripe("POST", "/issuing/cardholders", {"name": name, "email": email, "phone_number": phone, "type": "individual", "billing": {"address": billingAddress or {}}, "status": "active"})
    if result.get("error"):
        return {"error": "stripeApiError", "detail": result}
    rec = {"id": _gid("ch"), "userId": userId, "name": name, "email": email, "phone": phone, "authTier": tier, "stripeCardholderId": _str(result.get("id")), "status": "active", "createdAt": now_iso()}
    _insert_cardholder(rec)
    return {"status": "created", "cardholder": rec}


def issue_card(userId: str = "", cardType: str = "virtual", currency: str = "jpy", spendingLimitAmount: Any = 0, spendingLimitInterval: str = "monthly", initialCreditAllocation: Any = 0, destinationId: str = "", **_: Any) -> dict[str, Any]:
    if not userId:
        return {"error": "missingUserId"}
    tier = _auth_tier(userId)
    ctype = "physical" if cardType == "physical" else "virtual"
    if tier == "guest" or (ctype == "physical" and tier != "telecom"):
        return {"error": "authTierInsufficient", "required": "telecom" if ctype == "physical" else "verified", "current": tier}
    holder = _cardholder(userId, True)
    if not holder:
        return {"error": "noCardholder", "message": "Create a cardholder first"}
    amount = _int(spendingLimitAmount)
    result = _stripe("POST", "/issuing/cards", {"cardholder": holder["stripeCardholderId"], "type": ctype, "currency": currency or "jpy", "status": "active", "spending_controls": {"spending_limits": [{"amount": amount, "interval": spendingLimitInterval or "monthly"}]} if amount > 0 else None, "metadata": {"etzhayyimCreditsAllocated": "0", "etzhayyimCreditsConsumed": "0", "etzhayyimCreditsUserId": userId, "etzhayyimCreditsUpdatedAt": now_iso()}})
    if result.get("error"):
        return {"error": "stripeApiError", "detail": result}
    rec = {"id": _gid("card"), "cardholderId": holder["id"], "userId": userId, "cardType": ctype, "status": "active", "lastFour": _str(result.get("last4")), "currency": currency or "jpy", "spendingLimitAmount": amount, "spendingLimitInterval": spendingLimitInterval or "monthly", "stripeCardId": _str(result.get("id")), "createdAt": now_iso()}
    _insert_card(rec)
    allocation = assign_card_credits(userId=userId, cardId=rec["id"], amount=initialCreditAllocation, destinationId=destinationId) if _int(initialCreditAllocation) > 0 else None
    return {"status": "issued", "card": rec, **({"allocation": allocation} if allocation else {})}


def get_card(userId: str = "", cardId: str = "", **_: Any) -> dict[str, Any]:
    card = _card(userId, cardId) if userId and cardId else None
    return card or {"error": "notFound"}


def list_cards(userId: str = "", limit: Any = 20, **_: Any) -> dict[str, Any]:
    if not userId:
        return {"error": "missingUserId"}
    rows = _fetch_all("SELECT * FROM vertex_stripe_issued_card WHERE user_id=%s ORDER BY created_at DESC LIMIT %s", (userId, max(1, min(_int(limit, 20), 100))))
    items = [_normalize_card(r) for r in rows]
    return {"items": items, "total": len(items)}


def _stripe_card_credits(stripe_card: dict[str, Any]) -> dict[str, Any]:
    meta = stripe_card.get("metadata") if isinstance(stripe_card.get("metadata"), dict) else {}
    allocated = _int(meta.get("etzhayyimCreditsAllocated"))
    consumed = _int(meta.get("etzhayyimCreditsConsumed"))
    return {"allocated": allocated, "consumed": consumed, "available": max(allocated - consumed, 0), "userId": _str(meta.get("etzhayyimCreditsUserId"))}


def _update_card_credits(stripe_card_id: str, allocated: int, consumed: int, user_id: str) -> dict[str, Any]:
    return _stripe("POST", f"/issuing/cards/{stripe_card_id}", {f"metadata[etzhayyimCreditsAllocated]": str(max(allocated, 0)), f"metadata[etzhayyimCreditsConsumed]": str(max(consumed, 0)), f"metadata[etzhayyimCreditsUserId]": user_id, f"metadata[etzhayyimCreditsUpdatedAt]": now_iso()})


def assign_card_credits(userId: str = "", cardId: str = "", amount: Any = 0, destinationId: str = "", **_: Any) -> dict[str, Any]:
    value = _int(amount)
    if not userId or not cardId or value <= 0:
        return {"error": "missingRequiredFields", "required": ["userId", "cardId", "amount"]}
    card = _card(userId, cardId)
    if not card:
        return {"error": "cardNotFound"}
    allowed = credits.check_spend_allowed(userId=userId, action="cardAllocate", amount=value, destinationId=destinationId)
    if not allowed.get("allowed"):
        return {"error": "insufficientCredits", "reason": allowed.get("reason"), "balance": allowed.get("balance", 0), "required": value}
    spend = credits.spend_credits(userId=userId, action="cardAllocate", amount=value, destinationId=destinationId, sourceRef=f"stripe:cardAllocate:{cardId}:{uuid.uuid4().hex}")
    if spend.get("error"):
        return {"error": "creditSpendFailed", "detail": spend}
    stripe_card = _stripe("GET", f"/issuing/cards/{card['stripeCardId']}")
    current = _stripe_card_credits(stripe_card) if not stripe_card.get("error") else {"allocated": 0, "consumed": 0}
    allocated = _int(current.get("allocated")) + value
    consumed = _int(current.get("consumed"))
    updated = _update_card_credits(card["stripeCardId"], allocated, consumed, userId)
    if updated.get("error"):
        return {"error": "stripeMetadataUpdateFailed", "detail": updated, "warning": "credits already spent"}
    _insert_allocation(cardId, userId, value, allocated, consumed, max(allocated - consumed, 0), destinationId)
    return {"status": "allocated", "cardId": cardId, "allocated": allocated, "consumed": consumed, "available": max(allocated - consumed, 0), "creditsBalanceAfter": spend.get("balance"), "creditsTxId": spend.get("txId")}


def _insert_allocation(card_id: str, user_id: str, amount: int, allocated: int, consumed: int, available: int, destination_id: str) -> None:
    rid = _gid("cca")
    _execute("INSERT INTO vertex_stripe_card_credit_allocation (vertex_id,sensitivity_ord,owner_did,rkey,repo,collection,status,id,card_id,user_id,amount,allocated_total,consumed_total,available_total,destination_id,org_id,actor_id,created_at,actor_did,org_did) VALUES (%s,1,%s,%s,%s,'com.etzhayyim.apps.stripe.cardCreditAllocation','active',%s,%s,%s,%s,%s,%s,%s,%s,'anon',%s,%s,%s,'anon') ON CONFLICT (vertex_id) DO NOTHING", (f"at://{ACTOR}/com.etzhayyim.apps.stripe.cardCreditAllocation/{rid}", ACTOR, rid, ACTOR, rid, card_id, user_id, amount, allocated, consumed, available, destination_id, ACTOR, now_iso(), ACTOR))


def get_card_credits(userId: str = "", cardId: str = "", **_: Any) -> dict[str, Any]:
    card = _card(userId, cardId) if userId and cardId else None
    if not card:
        return {"error": "cardNotFound"}
    stripe_card = _stripe("GET", f"/issuing/cards/{card['stripeCardId']}")
    if stripe_card.get("error"):
        return {"error": "stripeApiError", "detail": stripe_card}
    return {"cardId": cardId, **_stripe_card_credits(stripe_card)}


def handle_authorization(authorization: dict[str, Any] | None = None, payload: str = "", **_: Any) -> dict[str, Any]:
    auth = authorization or (json.loads(payload) if payload else {})
    card_field = auth.get("card")
    stripe_card_id = card_field if isinstance(card_field, str) else _str((card_field or {}).get("id"))
    pending = auth.get("pending_request") or auth.get("pendingRequest") or {}
    amount = _int(pending.get("amount") or auth.get("amount"))
    currency = _str(pending.get("currency") or auth.get("currency") or "jpy")
    if not stripe_card_id or amount <= 0:
        return {"approved": False, "reason": "invalidAuthorizationPayload"}
    card = _card_by_stripe(stripe_card_id)
    if not card:
        return {"approved": False, "reason": "cardNotFound"}
    stripe_card = _stripe("GET", f"/issuing/cards/{stripe_card_id}")
    if stripe_card.get("error"):
        return {"approved": False, "reason": "stripeCardFetchFailed", "detail": stripe_card}
    snap = _stripe_card_credits(stripe_card)
    if _int(snap["available"]) < amount:
        _insert_authorization(card["id"], card["userId"], stripe_card_id, amount, currency, "decline", "insufficientAssignedCredits", _int(snap["available"]), _int(snap["available"]))
        return {"approved": False, "reason": "insufficientAssignedCredits", "available": snap["available"], "required": amount}
    next_consumed = _int(snap["consumed"]) + amount
    updated = _update_card_credits(stripe_card_id, _int(snap["allocated"]), next_consumed, snap.get("userId") or card["userId"])
    if updated.get("error"):
        return {"approved": False, "reason": "metadataUpdateFailed", "detail": updated}
    after = max(_int(snap["allocated"]) - next_consumed, 0)
    _insert_authorization(card["id"], card["userId"], stripe_card_id, amount, currency, "approve", "assignedCreditsAvailable", _int(snap["available"]), after)
    _insert_consumption(card["id"], card["userId"], stripe_card_id, amount, _int(snap["allocated"]), next_consumed, after)
    return {"approved": True, "cardId": card["id"], "amount": amount, "creditSnapshot": {"allocated": snap["allocated"], "consumed": next_consumed, "available": after}}


def _insert_authorization(card_id: str, user_id: str, stripe_card_id: str, amount: int, currency: str, decision: str, reason: str, before: int, after: int) -> None:
    rid = _gid("auth")
    _execute("INSERT INTO vertex_stripe_authorization (vertex_id,sensitivity_ord,owner_did,rkey,repo,collection,status,id,card_id,user_id,stripe_card_id,amount,currency,decision,reason,available_before,available_after,org_id,actor_id,created_at,actor_did,org_did) VALUES (%s,1,%s,%s,%s,'com.etzhayyim.apps.stripe.authorization','active',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'anon',%s,%s,%s,'anon') ON CONFLICT (vertex_id) DO NOTHING", (f"at://{ACTOR}/com.etzhayyim.apps.stripe.authorization/{rid}", ACTOR, rid, ACTOR, rid, card_id, user_id, stripe_card_id, amount, currency, decision, reason, before, after, ACTOR, now_iso(), ACTOR))


def _insert_consumption(card_id: str, user_id: str, stripe_card_id: str, amount: int, allocated: int, consumed: int, available: int) -> None:
    rid = _gid("ccc")
    _execute("INSERT INTO vertex_stripe_card_credit_consumption (vertex_id,sensitivity_ord,owner_did,rkey,repo,collection,status,id,card_id,user_id,stripe_card_id,amount,allocated_total,consumed_total,available_total,org_id,actor_id,created_at,actor_did,org_did) VALUES (%s,1,%s,%s,%s,'com.etzhayyim.apps.stripe.cardCreditConsumption','active',%s,%s,%s,%s,%s,%s,%s,%s,'anon',%s,%s,%s,'anon') ON CONFLICT (vertex_id) DO NOTHING", (f"at://{ACTOR}/com.etzhayyim.apps.stripe.cardCreditConsumption/{rid}", ACTOR, rid, ACTOR, rid, card_id, user_id, stripe_card_id, amount, allocated, consumed, available, ACTOR, now_iso(), ACTOR))


def _card_status(userId: str, cardId: str, status: str, label: str) -> dict[str, Any]:
    card = _card(userId, cardId) if userId and cardId else None
    if not card:
        return {"error": "notFound"}
    result = _stripe("POST", f"/issuing/cards/{card['stripeCardId']}", {"status": status})
    if result.get("error"):
        return {"error": "stripeApiError", "detail": result}
    _execute("UPDATE vertex_stripe_issued_card SET status=%s, updated_at=%s WHERE user_id=%s AND id=%s", (status, now_iso(), userId, cardId))
    return {"status": label, "cardId": cardId}


def freeze_card(userId: str = "", cardId: str = "", **_: Any) -> dict[str, Any]:
    return _card_status(userId, cardId, "inactive", "frozen")


def unfreeze_card(userId: str = "", cardId: str = "", **_: Any) -> dict[str, Any]:
    return _card_status(userId, cardId, "active", "unfrozen")


def cancel_card(userId: str = "", cardId: str = "", **_: Any) -> dict[str, Any]:
    return _card_status(userId, cardId, "canceled", "canceled")


def update_spending_limit(userId: str = "", cardId: str = "", amount: Any = None, interval: str = "monthly", categories: list[str] | None = None, **_: Any) -> dict[str, Any]:
    card = _card(userId, cardId) if userId and cardId and amount is not None else None
    if not card:
        return {"error": "missingRequiredFields"}
    value = _int(amount)
    result = _stripe("POST", f"/issuing/cards/{card['stripeCardId']}", {"spending_controls": {"spending_limits": [{"amount": value, "interval": interval or "monthly", "categories": categories or []}]}})
    if result.get("error"):
        return {"error": "stripeApiError", "detail": result}
    rid = _gid("sl")
    _execute("INSERT INTO vertex_stripe_spending_limit (vertex_id,sensitivity_ord,owner_did,rkey,repo,collection,status,id,card_id,user_id,amount,interval,categories_json,org_id,actor_id,created_at,actor_did,org_did) VALUES (%s,1,%s,%s,%s,'com.etzhayyim.apps.stripe.spendingLimit','active',%s,%s,%s,%s,%s,%s,'anon',%s,%s,%s,'anon') ON CONFLICT (vertex_id) DO NOTHING", (f"at://{ACTOR}/com.etzhayyim.apps.stripe.spendingLimit/{rid}", ACTOR, rid, ACTOR, rid, cardId, userId, value, interval or "monthly", json.dumps(categories or []), ACTOR, now_iso(), ACTOR))
    return {"status": "updated", "cardId": cardId, "amount": value, "interval": interval or "monthly"}


def list_transactions(userId: str = "", cardId: str = "", limit: Any = 50, **_: Any) -> dict[str, Any]:
    if not userId:
        return {"error": "missingUserId"}
    if cardId:
        rows = _fetch_all("SELECT * FROM vertex_stripe_authorization WHERE user_id=%s AND card_id=%s ORDER BY created_at DESC LIMIT %s", (userId, cardId, max(1, min(_int(limit, 50), 100))))
    else:
        rows = _fetch_all("SELECT * FROM vertex_stripe_authorization WHERE user_id=%s ORDER BY created_at DESC LIMIT %s", (userId, max(1, min(_int(limit, 50), 100))))
    items = [_normalize_auth(r) for r in rows]
    return {"items": items, "total": len(items)}


def get_cardholder(userId: str = "", **_: Any) -> dict[str, Any]:
    if not userId:
        return {"error": "missingUserId"}
    return _cardholder(userId) or {"error": "notFound"}


def wave(**_: Any) -> dict[str, Any]:
    return {"status": "posted"}


def stats(**_: Any) -> dict[str, Any]:
    ch = _fetch_one("SELECT COUNT(*) AS cnt FROM vertex_stripe_cardholder") or {}
    cards = _fetch_one("SELECT COUNT(*) AS cnt FROM vertex_stripe_issued_card") or {}
    auths = _fetch_one("SELECT COUNT(*) AS cnt FROM vertex_stripe_authorization") or {}
    return {"totalCardholders": _int(ch.get("cnt")), "totalCards": _int(cards.get("cnt")), "totalAuthorizations": _int(auths.get("cnt")), "domain": "stripe"}


def handle_commit(collection: str = "", action: str = "", **_: Any) -> dict[str, Any]:
    if action and action != "create":
        return {"ok": True, "detail": "skip non-create"}
    return {"ok": True, "detail": f"accepted {collection or 'commit'}"}
