"""Airline Frequent Flyer Program XRPC primitives for BPMN/LangServer."""

from __future__ import annotations

import datetime as _dt
import uuid
from typing import Any

from pymagatama.db_sync import sync_cursor


APP_DID = "did:web:air-ffp.gftd.ai"
ACTOR_SLUG = "air-ffp"


def _now() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _vid(kind: str, key: str) -> str:
    safe_key = key.replace("/", "_").replace(" ", "_")[:160] or uuid.uuid4().hex
    return f"air-ffp:{kind}:{safe_key}"


def _new_vid(kind: str) -> str:
    return f"air-ffp:{kind}:{uuid.uuid4().hex}"


def enroll_member(
    callerDid: str = "",
    memberDid: str = "",
    memberNumber: str = "",
    firstName: str = "",
    lastName: str = "",
    email: str = "",
    nationality: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("member", memberNumber or memberDid)
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_ffp_member
              (vertex_id, member_did, member_number, first_name, last_name, email,
               nationality, tier, miles_balance, status, enrolled_at, created_at,
               actor_did, org_id, user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, memberDid or callerDid or APP_DID,
                memberNumber or vertex_id,
                firstName or "", lastName or "", email or "", nationality or "",
                "classic", 0, "active", now, now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "memberNumber": memberNumber or vertex_id,
        "tier": "classic",
        "milesBalance": 0,
        "enrollmentStatus": "active",
    }


def accrue_miles(
    callerDid: str = "",
    memberNumber: str = "",
    flightNo: str = "",
    depDate: str = "",
    milesEarned: int = 0,
    bonusMiles: int = 0,
    transactionRef: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("accrue")
    now = _now()
    total_miles = int(milesEarned) + int(bonusMiles)
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_ffp_transaction
              (vertex_id, member_number, flight_no, dep_date, miles_earned,
               bonus_miles, total_miles, transaction_ref, transaction_type,
               status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, memberNumber, flightNo or "", depDate or "", int(milesEarned),
                int(bonusMiles), total_miles, transactionRef or vertex_id,
                "accrual", "posted", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "memberNumber": memberNumber,
        "milesEarned": int(milesEarned),
        "bonusMiles": int(bonusMiles),
        "totalMiles": total_miles,
        "transactionRef": transactionRef or vertex_id,
    }


def redeem_reward(
    callerDid: str = "",
    memberNumber: str = "",
    rewardCode: str = "",
    milesRequired: int = 0,
    currentBalance: int = 0,
    redemptionRef: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("redeem")
    now = _now()
    sufficient = int(currentBalance) >= int(milesRequired)
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_ffp_transaction
              (vertex_id, member_number, reward_code, miles_required, current_balance,
               sufficient, redemption_ref, transaction_type, status, created_at,
               actor_did, org_id, user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, memberNumber, rewardCode, int(milesRequired),
                int(currentBalance), sufficient, redemptionRef or vertex_id,
                "redemption",
                "approved" if sufficient else "declined",
                now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "memberNumber": memberNumber,
        "rewardCode": rewardCode,
        "sufficient": sufficient,
        "redemptionStatus": "approved" if sufficient else "declined",
        "redemptionRef": redemptionRef or vertex_id,
    }


def update_tier(
    callerDid: str = "",
    memberNumber: str = "",
    newTier: str = "",
    previousTier: str = "",
    qualifyingMiles: int = 0,
    effectiveDate: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("tier-update")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_ffp_member
              (vertex_id, member_number, new_tier, previous_tier, qualifying_miles,
               effective_date, status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, memberNumber, newTier, previousTier or "",
                int(qualifyingMiles), effectiveDate or now[:10],
                "tier_updated", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "memberNumber": memberNumber,
        "newTier": newTier,
        "previousTier": previousTier,
        "effectiveDate": effectiveDate or now[:10],
    }


def transfer_miles(
    callerDid: str = "",
    fromMemberNumber: str = "",
    toMemberNumber: str = "",
    milesAmount: int = 0,
    transferRef: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("transfer")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_ffp_transaction
              (vertex_id, from_member_number, to_member_number, miles_amount,
               transfer_ref, transaction_type, status, created_at, actor_did,
               org_id, user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, fromMemberNumber, toMemberNumber, int(milesAmount),
                transferRef or vertex_id, "transfer",
                "completed", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "fromMemberNumber": fromMemberNumber,
        "toMemberNumber": toMemberNumber,
        "milesAmount": int(milesAmount),
        "transferRef": transferRef or vertex_id,
        "transferStatus": "completed",
    }


def purchase_miles(
    callerDid: str = "",
    memberNumber: str = "",
    milesPurchased: int = 0,
    pricePerMile: float = 0.0,
    totalPrice: float = 0.0,
    currency: str = "USD",
    paymentRef: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("purchase")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_ffp_transaction
              (vertex_id, member_number, miles_purchased, price_per_mile,
               total_price, currency, payment_ref, transaction_type, status,
               created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, memberNumber, int(milesPurchased), float(pricePerMile),
                float(totalPrice), currency, paymentRef or vertex_id,
                "purchase", "completed", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "memberNumber": memberNumber,
        "milesPurchased": int(milesPurchased),
        "totalPrice": float(totalPrice),
        "currency": currency,
        "purchaseStatus": "completed",
    }


def expire_miles(
    callerDid: str = "",
    memberNumber: str = "",
    milesExpired: int = 0,
    expiryDate: str = "",
    reason: str = "inactivity",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("expire")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_ffp_transaction
              (vertex_id, member_number, miles_expired, expiry_date, reason,
               transaction_type, status, created_at, actor_did, org_id, user_id,
               actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, memberNumber, int(milesExpired), expiryDate or now[:10],
                reason, "expiry", "expired", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "memberNumber": memberNumber,
        "milesExpired": int(milesExpired),
        "expiryDate": expiryDate or now[:10],
        "expiryStatus": "expired",
    }


def partner_reconcile(
    callerDid: str = "",
    partnerCode: str = "",
    reconciliationPeriod: str = "",
    transactionCount: int = 0,
    totalMiles: int = 0,
    currency: str = "USD",
    settlementAmount: float = 0.0,
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("partner-reconcile", f"{partnerCode}:{reconciliationPeriod}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_ffp_transaction
              (vertex_id, partner_code, reconciliation_period, transaction_count,
               total_miles, currency, settlement_amount, transaction_type, status,
               reconciled_at, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, partnerCode, reconciliationPeriod, int(transactionCount),
                int(totalMiles), currency, float(settlementAmount),
                "partner_reconciliation", "reconciled", now, now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "partnerCode": partnerCode,
        "reconciliationPeriod": reconciliationPeriod,
        "totalMiles": int(totalMiles),
        "settlementAmount": float(settlementAmount),
        "reconcileStatus": "reconciled",
    }


def register(worker: Any, *, timeout_ms: int = 60_000) -> None:
    tasks = {
        "air.ffp.member.enroll": enroll_member,
        "air.ffp.miles.accrue": accrue_miles,
        "air.ffp.reward.redeem": redeem_reward,
        "air.ffp.tier.update": update_tier,
        "air.ffp.miles.transfer": transfer_miles,
        "air.ffp.miles.purchase": purchase_miles,
        "air.ffp.miles.expire": expire_miles,
        "air.ffp.partner.reconcile": partner_reconcile,
    }
    for task_type, handler in tasks.items():
        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(handler)
