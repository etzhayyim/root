"""Airline Departure Control System XRPC primitives for BPMN/LangServer."""

from __future__ import annotations

import datetime as _dt
import hashlib
import uuid
from typing import Any

from pymagatama.db_sync import sync_cursor


APP_DID = "did:web:air-dcs.gftd.ai"
ACTOR_SLUG = "air-dcs"


def _now() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _vid(kind: str, key: str) -> str:
    safe_key = key.replace("/", "_").replace(" ", "_")[:160] or uuid.uuid4().hex
    return f"air-dcs:{kind}:{safe_key}"


def _new_vid(kind: str) -> str:
    return f"air-dcs:{kind}:{uuid.uuid4().hex}"


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def process_checkin(
    callerDid: str = "",
    pnrRef: str = "",
    flightNo: str = "",
    depDate: str = "",
    passengerName: str = "",
    documentType: str = "",
    documentNumber: str = "",
    **_: Any,
) -> dict[str, Any]:
    pnr_hash = _hash(pnrRef)
    vertex_id = _vid("checkin", f"{flightNo}:{depDate}:{pnr_hash[:16]}")
    now = _now()
    doc_hash = _hash(f"{documentType}:{documentNumber}") if documentNumber else ""
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_dcs_checkin
              (vertex_id, pnr_hash, flight_no, dep_date, doc_hash,
               status, checked_in_at, created_at, actor_did, org_id,
               user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, pnr_hash, flightNo, depDate, doc_hash,
                "checked_in", now, now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "pnrRef": pnrRef,
        "flightNo": flightNo,
        "checkinStatus": "checked_in",
    }


def process_boarding_pass(
    callerDid: str = "",
    pnrRef: str = "",
    flightNo: str = "",
    depDate: str = "",
    seatNumber: str = "",
    gateCode: str = "",
    boardingGroup: str = "",
    **_: Any,
) -> dict[str, Any]:
    pnr_hash = _hash(pnrRef)
    vertex_id = _new_vid("boarding-pass")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_dcs_checkin
              (vertex_id, pnr_hash, flight_no, dep_date, seat_number,
               gate_code, boarding_group, status, created_at, actor_did,
               org_id, user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, pnr_hash, flightNo, depDate, seatNumber,
                gateCode or "", boardingGroup or "A",
                "boarding_pass_issued", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "pnrRef": pnrRef,
        "seatNumber": seatNumber,
        "gateCode": gateCode,
        "boardingGroup": boardingGroup,
    }


def accept_baggage(
    callerDid: str = "",
    pnrRef: str = "",
    flightNo: str = "",
    depDate: str = "",
    tagNumber: str = "",
    weightKg: float = 0.0,
    bagCount: int = 1,
    **_: Any,
) -> dict[str, Any]:
    pnr_hash = _hash(pnrRef)
    vertex_id = _vid("baggage", tagNumber or f"{flightNo}:{depDate}:{pnr_hash[:12]}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_dcs_baggage
              (vertex_id, pnr_hash, flight_no, dep_date, tag_number, weight_kg,
               bag_count, status, accepted_at, created_at, actor_did, org_id,
               user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, pnr_hash, flightNo, depDate, tagNumber, float(weightKg),
                int(bagCount), "accepted", now, now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "tagNumber": tagNumber,
        "weightKg": float(weightKg),
        "bagCount": int(bagCount),
        "baggageStatus": "accepted",
    }


def reconcile_baggage(
    callerDid: str = "",
    flightNo: str = "",
    depDate: str = "",
    loadedCount: int = 0,
    offloadedCount: int = 0,
    missingCount: int = 0,
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("bag-reconcile")
    now = _now()
    reconciled = missingCount == 0
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_dcs_baggage
              (vertex_id, flight_no, dep_date, loaded_count, offloaded_count,
               missing_count, status, created_at, actor_did, org_id,
               user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, depDate, int(loadedCount), int(offloadedCount),
                int(missingCount), "reconciled" if reconciled else "discrepancy",
                now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "depDate": depDate,
        "loadedCount": int(loadedCount),
        "missingCount": int(missingCount),
        "reconciled": reconciled,
    }


def compute_load_sheet(
    callerDid: str = "",
    flightNo: str = "",
    depDate: str = "",
    paxCount: int = 0,
    bagWeightKg: float = 0.0,
    cargoWeightKg: float = 0.0,
    fuelKg: float = 0.0,
    towKg: float = 0.0,
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("load-sheet", f"{flightNo}:{depDate}")
    now = _now()
    zfw_kg = float(towKg) - float(fuelKg)
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_dcs_load_sheet
              (vertex_id, flight_no, dep_date, pax_count, bag_weight_kg,
               cargo_weight_kg, fuel_kg, tow_kg, zfw_kg, status, created_at,
               actor_did, org_id, user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, depDate, int(paxCount), float(bagWeightKg),
                float(cargoWeightKg), float(fuelKg), float(towKg), zfw_kg,
                "computed", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "depDate": depDate,
        "towKg": float(towKg),
        "zfwKg": zfw_kg,
        "paxCount": int(paxCount),
    }


def transmit_apis(
    callerDid: str = "",
    flightNo: str = "",
    depDate: str = "",
    destCountry: str = "",
    paxCount: int = 0,
    transmissionRef: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("apis")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_dcs_checkin
              (vertex_id, flight_no, dep_date, dest_country, pax_count,
               transmission_ref, status, transmitted_at, created_at, actor_did,
               org_id, user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, depDate, destCountry, int(paxCount),
                transmissionRef or vertex_id, "transmitted", now, now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "destCountry": destCountry,
        "paxCount": int(paxCount),
        "transmissionRef": transmissionRef or vertex_id,
    }


def track_turnaround(
    callerDid: str = "",
    flightNo: str = "",
    depDate: str = "",
    arrivalTime: str = "",
    gateReadyTime: str = "",
    boardingStartTime: str = "",
    estimatedDepTime: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("turnaround", f"{flightNo}:{depDate}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_dcs_checkin
              (vertex_id, flight_no, dep_date, arrival_time, gate_ready_time,
               boarding_start_time, estimated_dep_time, status, created_at,
               actor_did, org_id, user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, depDate, arrivalTime, gateReadyTime or "",
                boardingStartTime or "", estimatedDepTime or "",
                "in_progress", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "depDate": depDate,
        "turnaroundStatus": "in_progress",
        "estimatedDepTime": estimatedDepTime,
    }


def departure_control(
    callerDid: str = "",
    flightNo: str = "",
    depDate: str = "",
    finalPaxCount: int = 0,
    boardedCount: int = 0,
    actualDepTime: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("dep-control")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_dcs_checkin
              (vertex_id, flight_no, dep_date, final_pax_count, boarded_count,
               actual_dep_time, status, created_at, actor_did, org_id,
               user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, depDate, int(finalPaxCount), int(boardedCount),
                actualDepTime or now, "departed", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 3, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "depDate": depDate,
        "finalPaxCount": int(finalPaxCount),
        "boardedCount": int(boardedCount),
        "actualDepTime": actualDepTime or now,
        "departureStatus": "departed",
    }


def register(worker: Any, *, timeout_ms: int = 60_000) -> None:
    tasks = {
        "air.dcs.checkin.process": process_checkin,
        "air.dcs.boarding_pass.process": process_boarding_pass,
        "air.dcs.baggage.accept": accept_baggage,
        "air.dcs.baggage.reconcile": reconcile_baggage,
        "air.dcs.load_sheet.compute": compute_load_sheet,
        "air.dcs.apis.transmit": transmit_apis,
        "air.dcs.turnaround.track": track_turnaround,
        "air.dcs.departure.control": departure_control,
    }
    for task_type, handler in tasks.items():
        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(handler)
