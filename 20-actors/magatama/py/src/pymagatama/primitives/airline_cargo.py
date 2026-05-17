"""Airline Cargo XRPC primitives for BPMN/LangServer."""

from __future__ import annotations

import datetime as _dt
import uuid
from typing import Any

from pymagatama.db_sync import sync_cursor


APP_DID = "did:web:air-cargo.etzhayyim.com"
ACTOR_SLUG = "air-cargo"


def _now() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _vid(kind: str, key: str) -> str:
    safe_key = key.replace("/", "_").replace(" ", "_")[:160] or uuid.uuid4().hex
    return f"air-cargo:{kind}:{safe_key}"


def _new_vid(kind: str) -> str:
    return f"air-cargo:{kind}:{uuid.uuid4().hex}"


def create_cargo_booking(
    callerDid: str = "",
    bookingRef: str = "",
    originIata: str = "",
    destIata: str = "",
    flightNo: str = "",
    depDate: str = "",
    weightKg: float = 0.0,
    commodity: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("booking", bookingRef or f"{flightNo}:{depDate}:{originIata}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_cargo_booking
              (vertex_id, booking_ref, origin_iata, dest_iata, flight_no, dep_date,
               weight_kg, commodity, status, created_at, actor_did, org_id,
               user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, bookingRef or vertex_id, originIata, destIata, flightNo, depDate,
                float(weightKg), commodity or "",
                "booked", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "bookingRef": bookingRef or vertex_id,
        "flightNo": flightNo,
        "weightKg": float(weightKg),
        "bookingStatus": "booked",
    }


def issue_awb(
    callerDid: str = "",
    awbNumber: str = "",
    bookingRef: str = "",
    shipperName: str = "",
    consigneeName: str = "",
    originIata: str = "",
    destIata: str = "",
    chargeableWeightKg: float = 0.0,
    currency: str = "USD",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("awb", awbNumber or bookingRef)
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_cargo_awb
              (vertex_id, awb_number, booking_ref, shipper_name, consignee_name,
               origin_iata, dest_iata, chargeable_weight_kg, currency, status,
               issued_at, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, awbNumber, bookingRef, shipperName or "", consigneeName or "",
                originIata, destIata, float(chargeableWeightKg), currency,
                "issued", now, now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "awbNumber": awbNumber,
        "bookingRef": bookingRef,
        "chargeableWeightKg": float(chargeableWeightKg),
        "awbStatus": "issued",
    }


def accept_cargo(
    callerDid: str = "",
    awbNumber: str = "",
    flightNo: str = "",
    depDate: str = "",
    actualWeightKg: float = 0.0,
    pieces: int = 1,
    specialHandling: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("cargo-accept")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_cargo_booking
              (vertex_id, awb_number, flight_no, dep_date, actual_weight_kg, pieces,
               special_handling, status, accepted_at, created_at, actor_did, org_id,
               user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, awbNumber, flightNo, depDate, float(actualWeightKg),
                int(pieces), specialHandling or "",
                "accepted", now, now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "awbNumber": awbNumber,
        "actualWeightKg": float(actualWeightKg),
        "pieces": int(pieces),
        "acceptanceStatus": "accepted",
    }


def assign_uld(
    callerDid: str = "",
    uldNumber: str = "",
    flightNo: str = "",
    depDate: str = "",
    awbNumbers: str = "",
    loadedWeightKg: float = 0.0,
    position: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("uld", f"{uldNumber}:{flightNo}:{depDate}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_cargo_booking
              (vertex_id, uld_number, flight_no, dep_date, awb_numbers,
               loaded_weight_kg, position, status, created_at, actor_did, org_id,
               user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, uldNumber, flightNo, depDate, awbNumbers or "",
                float(loadedWeightKg), position or "",
                "loaded", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "uldNumber": uldNumber,
        "flightNo": flightNo,
        "loadedWeightKg": float(loadedWeightKg),
        "uldStatus": "loaded",
    }


def track_shipment(
    callerDid: str = "",
    awbNumber: str = "",
    eventType: str = "",
    eventStation: str = "",
    eventTime: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("track")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_cargo_booking
              (vertex_id, awb_number, event_type, event_station, event_time,
               status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, awbNumber, eventType, eventStation or "",
                eventTime or now, eventType.lower().replace(" ", "_") or "tracked",
                now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "awbNumber": awbNumber,
        "eventType": eventType,
        "eventStation": eventStation,
        "eventTime": eventTime or now,
    }


def process_claim(
    callerDid: str = "",
    claimRef: str = "",
    awbNumber: str = "",
    claimType: str = "",
    claimAmount: float = 0.0,
    currency: str = "USD",
    description: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("claim", claimRef or awbNumber)
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_cargo_booking
              (vertex_id, claim_ref, awb_number, claim_type, claim_amount, currency,
               description, status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, claimRef or vertex_id, awbNumber, claimType,
                float(claimAmount), currency, description or "",
                "under_review", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "claimRef": claimRef or vertex_id,
        "awbNumber": awbNumber,
        "claimAmount": float(claimAmount),
        "claimStatus": "under_review",
    }


def settle_cass(
    callerDid: str = "",
    agentCode: str = "",
    settlementPeriod: str = "",
    awbCount: int = 0,
    grossAmount: float = 0.0,
    netAmount: float = 0.0,
    currency: str = "USD",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("cass-settlement", f"{agentCode}:{settlementPeriod}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_cargo_cass_settlement
              (vertex_id, agent_code, settlement_period, awb_count, gross_amount,
               net_amount, currency, status, settled_at, created_at, actor_did,
               org_id, user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, agentCode, settlementPeriod, int(awbCount),
                float(grossAmount), float(netAmount), currency,
                "settled", now, now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "agentCode": agentCode,
        "settlementPeriod": settlementPeriod,
        "netAmount": float(netAmount),
        "currency": currency,
        "settlementStatus": "settled",
    }


def report_cargo_security(
    callerDid: str = "",
    screeningRef: str = "",
    flightNo: str = "",
    depDate: str = "",
    method: str = "",
    awbNumber: str = "",
    result: str = "clear",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("cargo-sec")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_cargo_booking
              (vertex_id, screening_ref, flight_no, dep_date, method, awb_number,
               result, status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, screeningRef or vertex_id, flightNo, depDate,
                method or "x-ray", awbNumber or "", result,
                "screened", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "screeningRef": screeningRef or vertex_id,
        "flightNo": flightNo,
        "awbNumber": awbNumber,
        "result": result,
        "securityStatus": "screened",
    }


def register(worker: Any, *, timeout_ms: int = 60_000) -> None:
    tasks = {
        "air.cargo.booking.create": create_cargo_booking,
        "air.cargo.awb.issue": issue_awb,
        "air.cargo.cargo.accept": accept_cargo,
        "air.cargo.uld.assign": assign_uld,
        "air.cargo.shipment.track": track_shipment,
        "air.cargo.claim.process": process_claim,
        "air.cargo.cass.settle": settle_cass,
        "air.cargo.security.report": report_cargo_security,
    }
    for task_type, handler in tasks.items():
        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(handler)
