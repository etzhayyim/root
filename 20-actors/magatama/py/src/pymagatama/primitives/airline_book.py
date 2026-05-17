"""Airline Booking XRPC primitives for BPMN/LangServer."""

from __future__ import annotations

import datetime as _dt
import hashlib
import uuid
from typing import Any

from pymagatama.db_sync import sync_cursor


APP_DID = "did:web:air-book.etzhayyim.com"
ACTOR_SLUG = "air-book"


def _now() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _vid(kind: str, key: str) -> str:
    safe_key = key.replace("/", "_").replace(" ", "_")[:160] or uuid.uuid4().hex
    return f"air-book:{kind}:{safe_key}"


def _new_vid(kind: str) -> str:
    return f"air-book:{kind}:{uuid.uuid4().hex}"


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def create_pnr(
    callerDid: str = "",
    flightNo: str = "",
    depDate: str = "",
    passengerName: str = "",
    passengerDob: str = "",
    contactEmail: str = "",
    originIata: str = "",
    destIata: str = "",
    **_: Any,
) -> dict[str, Any]:
    pnr_key = f"{flightNo}:{depDate}:{_hash(passengerName)[:16]}"
    vertex_id = _vid("pnr", pnr_key)
    now = _now()
    passenger_hash = _hash(f"{passengerName}:{passengerDob}")
    contact_hash = _hash(contactEmail) if contactEmail else ""
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_book_pnr
              (vertex_id, flight_no, dep_date, passenger_hash, contact_hash,
               origin_iata, dest_iata, status, created_at, actor_did, org_id,
               user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, depDate, passenger_hash, contact_hash,
                originIata, destIata, "created", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "depDate": depDate,
        "pnrStatus": "created",
    }


def confirm_booking(
    callerDid: str = "",
    pnrRef: str = "",
    paymentRef: str = "",
    fareClass: str = "",
    totalFare: float = 0.0,
    currency: str = "USD",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("booking")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_book_pnr
              (vertex_id, pnr_ref, payment_ref, fare_class, total_fare, currency,
               status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, pnrRef, paymentRef or "", fareClass, float(totalFare), currency,
                "confirmed", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "pnrRef": pnrRef,
        "bookingStatus": "confirmed",
        "totalFare": float(totalFare),
        "currency": currency,
    }


def issue_ticket(
    callerDid: str = "",
    pnrRef: str = "",
    ticketNumber: str = "",
    fareClass: str = "",
    issuingAirline: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("ticket", ticketNumber or pnrRef)
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_book_ticket
              (vertex_id, pnr_ref, ticket_number, fare_class, issuing_airline,
               status, issued_at, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, pnrRef, ticketNumber, fareClass, issuingAirline or "",
                "issued", now, now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "pnrRef": pnrRef,
        "ticketNumber": ticketNumber,
        "ticketStatus": "issued",
    }


def assign_seat(
    callerDid: str = "",
    pnrRef: str = "",
    flightNo: str = "",
    depDate: str = "",
    seatNumber: str = "",
    seatClass: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("seat", f"{flightNo}:{depDate}:{seatNumber}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_book_pnr
              (vertex_id, pnr_ref, flight_no, dep_date, seat_number, seat_class,
               status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, pnrRef, flightNo, depDate, seatNumber, seatClass or "",
                "seat_assigned", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "pnrRef": pnrRef,
        "seatNumber": seatNumber,
        "seatClass": seatClass,
    }


def add_ancillary(
    callerDid: str = "",
    pnrRef: str = "",
    ancillaryType: str = "",
    ancillaryCode: str = "",
    quantity: int = 1,
    price: float = 0.0,
    currency: str = "USD",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("ancillary")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_book_ancillary
              (vertex_id, pnr_ref, ancillary_type, ancillary_code, quantity, price,
               currency, status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, pnrRef, ancillaryType, ancillaryCode or "", int(quantity),
                float(price), currency, "added", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "pnrRef": pnrRef,
        "ancillaryType": ancillaryType,
        "quantity": int(quantity),
        "price": float(price),
    }


def cancel_booking(
    callerDid: str = "",
    pnrRef: str = "",
    reason: str = "",
    refundAmount: float = 0.0,
    currency: str = "USD",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("cancel")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_book_pnr
              (vertex_id, pnr_ref, cancel_reason, refund_amount, currency,
               status, cancelled_at, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, pnrRef, reason or "", float(refundAmount), currency,
                "cancelled", now, now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "pnrRef": pnrRef,
        "bookingStatus": "cancelled",
        "refundAmount": float(refundAmount),
        "currency": currency,
    }


def reprotect_passenger(
    callerDid: str = "",
    originalPnrRef: str = "",
    newFlightNo: str = "",
    newDepDate: str = "",
    irropReason: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("irrop-pnr")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_book_pnr
              (vertex_id, original_pnr_ref, flight_no, dep_date, irrop_reason,
               status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, originalPnrRef, newFlightNo, newDepDate, irropReason or "",
                "reprotected", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "originalPnrRef": originalPnrRef,
        "newFlightNo": newFlightNo,
        "newDepDate": newDepDate,
        "reprotectionStatus": "reprotected",
    }


def settle_bsp(
    callerDid: str = "",
    agentCode: str = "",
    settlementPeriod: str = "",
    ticketCount: int = 0,
    grossAmount: float = 0.0,
    netAmount: float = 0.0,
    currency: str = "USD",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("bsp-settlement", f"{agentCode}:{settlementPeriod}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_book_bsp_settlement
              (vertex_id, agent_code, settlement_period, ticket_count, gross_amount,
               net_amount, currency, status, settled_at, created_at, actor_did,
               org_id, user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, agentCode, settlementPeriod, int(ticketCount),
                float(grossAmount), float(netAmount), currency,
                "settled", now, now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "agentCode": agentCode,
        "settlementPeriod": settlementPeriod,
        "netAmount": float(netAmount),
        "currency": currency,
    }


def register(worker: Any, *, timeout_ms: int = 60_000) -> None:
    tasks = {
        "air.book.pnr.create": create_pnr,
        "air.book.booking.confirm": confirm_booking,
        "air.book.ticket.issue": issue_ticket,
        "air.book.seat.assign": assign_seat,
        "air.book.ancillary.add": add_ancillary,
        "air.book.booking.cancel": cancel_booking,
        "air.book.irrop.reprotect": reprotect_passenger,
        "air.book.bsp.settle": settle_bsp,
    }
    for task_type, handler in tasks.items():
        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(handler)
