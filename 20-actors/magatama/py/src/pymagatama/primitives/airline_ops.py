"""Airline Operations Control XRPC primitives for BPMN/LangServer."""

from __future__ import annotations

import datetime as _dt
import uuid
from typing import Any

from pymagatama.db_sync import sync_cursor


APP_DID = "did:web:air-ops.gftd.ai"
ACTOR_SLUG = "air-ops"


def _now() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _vid(kind: str, key: str) -> str:
    safe_key = key.replace("/", "_").replace(" ", "_")[:160] or uuid.uuid4().hex
    return f"air-ops:{kind}:{safe_key}"


def _new_vid(kind: str) -> str:
    return f"air-ops:{kind}:{uuid.uuid4().hex}"


def file_flight_plan(
    callerDid: str = "",
    flightNo: str = "",
    depDate: str = "",
    depIata: str = "",
    arrIata: str = "",
    route: str = "",
    altIata: str = "",
    fuelOnBoard: float = 0.0,
    estimatedFlightTime: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("flight-plan", f"{flightNo}:{depDate}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_ops_flight_plan
              (vertex_id, flight_no, dep_date, dep_iata, arr_iata, route, alt_iata,
               fuel_on_board, estimated_flight_time, status, filed_at, created_at,
               actor_did, org_id, user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, depDate, depIata, arrIata, route or "",
                altIata or "", float(fuelOnBoard), estimatedFlightTime or "",
                "filed", now, now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "depDate": depDate,
        "flightPlanStatus": "filed",
    }


def dispatch_brief(
    callerDid: str = "",
    flightNo: str = "",
    depDate: str = "",
    captainDid: str = "",
    weatherSummary: str = "",
    notamCount: int = 0,
    releaseRef: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("dispatch-brief", f"{flightNo}:{depDate}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_ops_flight_plan
              (vertex_id, flight_no, dep_date, captain_did, weather_summary,
               notam_count, release_ref, status, briefed_at, created_at, actor_did,
               org_id, user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, depDate, captainDid or "", weatherSummary or "",
                int(notamCount), releaseRef or vertex_id,
                "briefed", now, now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "depDate": depDate,
        "releaseRef": releaseRef or vertex_id,
        "briefStatus": "briefed",
    }


def fetch_notam(
    callerDid: str = "",
    iataCode: str = "",
    notamType: str = "all",
    validFrom: str = "",
    validTo: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("notam-fetch")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_ops_flight_plan
              (vertex_id, iata_code, notam_type, valid_from, valid_to,
               status, fetched_at, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, iataCode, notamType, validFrom or now[:10], validTo or now[:10],
                "fetched", now, now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "iataCode": iataCode,
        "notamType": notamType,
        "fetchStatus": "fetched",
        "notamCount": 0,
    }


def fetch_weather(
    callerDid: str = "",
    iataCode: str = "",
    reportType: str = "metar",
    validTime: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("weather-fetch")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_ops_flight_plan
              (vertex_id, iata_code, report_type, valid_time,
               status, fetched_at, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, iataCode, reportType, validTime or now,
                "fetched", now, now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "iataCode": iataCode,
        "reportType": reportType,
        "fetchStatus": "fetched",
    }


def record_tech_log(
    callerDid: str = "",
    flightNo: str = "",
    depDate: str = "",
    tailNumber: str = "",
    defectCode: str = "",
    description: str = "",
    rectification: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("tech-log")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_ops_tech_log
              (vertex_id, flight_no, dep_date, tail_number, defect_code,
               description, rectification, status, created_at, actor_did,
               org_id, user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, depDate, tailNumber, defectCode or "",
                description or "", rectification or "",
                "recorded", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "tailNumber": tailNumber,
        "defectCode": defectCode,
        "techLogStatus": "recorded",
    }


def order_fuel(
    callerDid: str = "",
    flightNo: str = "",
    depDate: str = "",
    depIata: str = "",
    fuelType: str = "JET-A",
    requestedKg: float = 0.0,
    upliftRef: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("fuel-order", f"{flightNo}:{depDate}:{depIata}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_ops_flight_plan
              (vertex_id, flight_no, dep_date, dep_iata, fuel_type, requested_kg,
               uplift_ref, status, ordered_at, created_at, actor_did, org_id,
               user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, depDate, depIata, fuelType, float(requestedKg),
                upliftRef or vertex_id, "ordered", now, now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "fuelType": fuelType,
        "requestedKg": float(requestedKg),
        "upliftRef": upliftRef or vertex_id,
    }


def submit_pirep(
    callerDid: str = "",
    flightNo: str = "",
    depDate: str = "",
    reportTime: str = "",
    altitude: int = 0,
    turbulenceLevel: str = "",
    icingLevel: str = "",
    windSpeed: int = 0,
    windDir: int = 0,
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("pirep")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_ops_flight_plan
              (vertex_id, flight_no, dep_date, report_time, altitude,
               turbulence_level, icing_level, wind_speed, wind_dir,
               status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, depDate, reportTime or now, int(altitude),
                turbulenceLevel or "nil", icingLevel or "nil",
                int(windSpeed), int(windDir),
                "submitted", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "turbulenceLevel": turbulenceLevel or "nil",
        "pirepStatus": "submitted",
    }


def monitor_flight(
    callerDid: str = "",
    flightNo: str = "",
    depDate: str = "",
    phase: str = "",
    delayMins: int = 0,
    positionLat: float = 0.0,
    positionLon: float = 0.0,
    altitudeFt: int = 0,
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("monitor")
    now = _now()
    if delayMins <= 15:
        alert_level = "green"
    elif delayMins <= 60:
        alert_level = "amber"
    else:
        alert_level = "red"
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_ops_flight_plan
              (vertex_id, flight_no, dep_date, phase, delay_mins,
               position_lat, position_lon, altitude_ft, alert_level,
               status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, depDate, phase or "en_route", int(delayMins),
                float(positionLat), float(positionLon), int(altitudeFt),
                alert_level, "monitored", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "phase": phase or "en_route",
        "delayMins": int(delayMins),
        "alertLevel": alert_level,
    }


def register(worker: Any, *, timeout_ms: int = 60_000) -> None:
    tasks = {
        "air.ops.flight_plan.file": file_flight_plan,
        "air.ops.dispatch.brief": dispatch_brief,
        "air.ops.notam.fetch": fetch_notam,
        "air.ops.weather.fetch": fetch_weather,
        "air.ops.tech_log.record": record_tech_log,
        "air.ops.fuel.order": order_fuel,
        "air.ops.pirep.submit": submit_pirep,
        "air.ops.flight.monitor": monitor_flight,
    }
    for task_type, handler in tasks.items():
        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(handler)
