"""Airline Scheduling XRPC primitives for BPMN/LangServer."""

from __future__ import annotations

import datetime as _dt
import hashlib
import uuid
from typing import Any

from pymagatama.db_sync import sync_cursor


APP_DID = "did:web:air-sched.etzhayyim.com"
ACTOR_SLUG = "air-sched"


def _now() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _vid(kind: str, key: str) -> str:
    safe_key = key.replace("/", "_").replace(" ", "_")[:160] or uuid.uuid4().hex
    return f"air-sched:{kind}:{safe_key}"


def _new_vid(kind: str) -> str:
    return f"air-sched:{kind}:{uuid.uuid4().hex}"


def register_schedule(
    callerDid: str = "",
    flightNo: str = "",
    depDate: str = "",
    depIata: str = "",
    arrIata: str = "",
    depTime: str = "",
    arrTime: str = "",
    aircraftType: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("schedule", f"{flightNo}:{depDate}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_sched_schedule
              (vertex_id, flight_no, dep_date, dep_iata, arr_iata, dep_time, arr_time,
               aircraft_type, status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, depDate, depIata, arrIata, depTime, arrTime,
                aircraftType or "", "scheduled", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "depDate": depDate,
        "depIata": depIata,
        "arrIata": arrIata,
    }


def request_slot(
    callerDid: str = "",
    flightNo: str = "",
    depDate: str = "",
    depIata: str = "",
    slotType: str = "departure",
    requestedTime: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("slot", f"{flightNo}:{depDate}:{slotType}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_sched_slot
              (vertex_id, flight_no, dep_date, dep_iata, slot_type, requested_time,
               status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, depDate, depIata, slotType, requestedTime,
                "requested", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "slotType": slotType,
        "requestedTime": requestedTime,
    }


def allocate_slot(
    callerDid: str = "",
    slotRef: str = "",
    allocatedTime: str = "",
    allocatedBy: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("slot-alloc")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_sched_slot
              (vertex_id, slot_ref, allocated_time, allocated_by,
               status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, slotRef, allocatedTime, allocatedBy or "",
                "allocated", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "slotRef": slotRef,
        "allocatedTime": allocatedTime,
        "slotStatus": "allocated",
    }


def assign_fleet(
    callerDid: str = "",
    flightNo: str = "",
    depDate: str = "",
    aircraftType: str = "",
    tailNumber: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("fleet-assign")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_sched_schedule
              (vertex_id, flight_no, dep_date, aircraft_type, tail_number,
               status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, depDate, aircraftType, tailNumber or "",
                "fleet_assigned", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "depDate": depDate,
        "aircraftType": aircraftType,
        "tailNumber": tailNumber,
    }


def publish_schedule(
    callerDid: str = "",
    seasonCode: str = "",
    validFrom: str = "",
    validTo: str = "",
    flightCount: int = 0,
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("schedule-pub", seasonCode)
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_sched_schedule
              (vertex_id, season_code, valid_from, valid_to, flight_count,
               status, published_at, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, seasonCode, validFrom, validTo, int(flightCount),
                "published", now, now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "seasonCode": seasonCode,
        "publishedAt": now,
        "flightCount": int(flightCount),
    }


def assign_gate(
    callerDid: str = "",
    flightNo: str = "",
    depDate: str = "",
    gateCode: str = "",
    terminal: str = "",
    airport: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("gate", f"{flightNo}:{depDate}:{airport}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_sched_schedule
              (vertex_id, flight_no, dep_date, gate_code, terminal, airport,
               status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, depDate, gateCode, terminal or "", airport or "",
                "gate_assigned", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "gateCode": gateCode,
        "terminal": terminal,
    }


def change_frequency(
    callerDid: str = "",
    flightNo: str = "",
    seasonCode: str = "",
    oldFrequency: str = "",
    newFrequency: str = "",
    effectiveDate: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("freq-change")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_sched_schedule
              (vertex_id, flight_no, season_code, old_frequency, new_frequency,
               effective_date, status, created_at, actor_did, org_id, user_id,
               actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, seasonCode, oldFrequency, newFrequency,
                effectiveDate or now[:10], "frequency_changed", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "oldFrequency": oldFrequency,
        "newFrequency": newFrequency,
        "effectiveDate": effectiveDate,
    }


def register_codeshare(
    callerDid: str = "",
    operatingFlightNo: str = "",
    marketingFlightNo: str = "",
    partnerAirline: str = "",
    depDate: str = "",
    seatAllocation: int = 0,
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("codeshare", f"{operatingFlightNo}:{marketingFlightNo}:{depDate}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_sched_codeshare
              (vertex_id, operating_flight_no, marketing_flight_no, partner_airline,
               dep_date, seat_allocation, status, created_at, actor_did, org_id,
               user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, operatingFlightNo, marketingFlightNo, partnerAirline,
                depDate, int(seatAllocation), "active", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "operatingFlightNo": operatingFlightNo,
        "marketingFlightNo": marketingFlightNo,
        "partnerAirline": partnerAirline,
    }


def register(worker: Any, *, timeout_ms: int = 60_000) -> None:
    tasks = {
        "air.sched.schedule.register": register_schedule,
        "air.sched.slot.request": request_slot,
        "air.sched.slot.allocate": allocate_slot,
        "air.sched.fleet.assign": assign_fleet,
        "air.sched.schedule.publish": publish_schedule,
        "air.sched.gate.assign": assign_gate,
        "air.sched.frequency.change": change_frequency,
        "air.sched.codeshare.register": register_codeshare,
    }
    for task_type, handler in tasks.items():
        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(handler)
