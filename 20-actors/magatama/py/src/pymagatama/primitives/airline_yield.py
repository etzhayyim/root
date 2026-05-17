"""Airline Yield Management XRPC primitives for BPMN/LangServer."""

from __future__ import annotations

import datetime as _dt
import uuid
from typing import Any

from pymagatama.db_sync import sync_cursor


APP_DID = "did:web:air-yield.etzhayyim.com"
ACTOR_SLUG = "air-yield"


def _now() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _vid(kind: str, key: str) -> str:
    safe_key = key.replace("/", "_").replace(" ", "_")[:160] or uuid.uuid4().hex
    return f"air-yield:{kind}:{safe_key}"


def _new_vid(kind: str) -> str:
    return f"air-yield:{kind}:{uuid.uuid4().hex}"


def publish_fare_class(
    callerDid: str = "",
    flightNo: str = "",
    depDate: str = "",
    fareClass: str = "",
    baseFare: float = 0.0,
    currency: str = "USD",
    inventory: int = 0,
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("fare-class", f"{flightNo}:{depDate}:{fareClass}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_yield_fare_class
              (vertex_id, flight_no, dep_date, fare_class, base_fare, currency,
               inventory, status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, depDate, fareClass, float(baseFare), currency,
                int(inventory), "active", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "fareClass": fareClass,
        "baseFare": float(baseFare),
        "currency": currency,
        "inventory": int(inventory),
    }


def adjust_inventory(
    callerDid: str = "",
    flightNo: str = "",
    depDate: str = "",
    fareClass: str = "",
    delta: int = 0,
    reason: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("inv-adjust")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_yield_fare_class
              (vertex_id, flight_no, dep_date, fare_class, inventory_delta, adjust_reason,
               status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, depDate, fareClass, int(delta), reason or "",
                "adjusted", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "fareClass": fareClass,
        "delta": int(delta),
    }


def file_fare(
    callerDid: str = "",
    fareCode: str = "",
    originIata: str = "",
    destIata: str = "",
    amount: float = 0.0,
    currency: str = "USD",
    effectiveDate: str = "",
    discountCode: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("atpco-fare", f"{fareCode}:{originIata}:{destIata}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_yield_fare_class
              (vertex_id, fare_code, origin_iata, dest_iata, amount, currency,
               effective_date, discount_code, status, created_at, actor_did,
               org_id, user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, fareCode, originIata, destIata, float(amount), currency,
                effectiveDate or now[:10], discountCode or "",
                "filed", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "fareCode": fareCode,
        "originIata": originIata,
        "destIata": destIata,
        "amount": float(amount),
        "currency": currency,
    }


def set_overbooking(
    callerDid: str = "",
    flightNo: str = "",
    depDate: str = "",
    overbookingFactor: float = 1.0,
    maxOverbooking: int = 0,
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("overbooking", f"{flightNo}:{depDate}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_yield_fare_class
              (vertex_id, flight_no, dep_date, overbooking_factor, max_overbooking,
               status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, depDate, float(overbookingFactor), int(maxOverbooking),
                "set", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "depDate": depDate,
        "overbookingFactor": float(overbookingFactor),
        "maxOverbooking": int(maxOverbooking),
    }


def process_group(
    callerDid: str = "",
    groupRef: str = "",
    flightNo: str = "",
    depDate: str = "",
    paxCount: int = 0,
    fareClass: str = "",
    groupFare: float = 0.0,
    currency: str = "USD",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("group", groupRef or f"{flightNo}:{depDate}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_yield_fare_class
              (vertex_id, group_ref, flight_no, dep_date, pax_count, fare_class,
               group_fare, currency, status, created_at, actor_did, org_id,
               user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, groupRef, flightNo, depDate, int(paxCount), fareClass,
                float(groupFare), currency, "processed", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "groupRef": groupRef,
        "flightNo": flightNo,
        "paxCount": int(paxCount),
        "groupFare": float(groupFare),
        "currency": currency,
    }


def dynamic_price(
    callerDid: str = "",
    flightNo: str = "",
    depDate: str = "",
    fareClass: str = "",
    loadFactor: float = 0.0,
    recommendedFare: float = 0.0,
    currency: str = "USD",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("dynamic-price")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_yield_fare_class
              (vertex_id, flight_no, dep_date, fare_class, load_factor,
               recommended_fare, currency, status, created_at, actor_did,
               org_id, user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, depDate, fareClass, float(loadFactor),
                float(recommendedFare), currency, "priced", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "fareClass": fareClass,
        "loadFactor": float(loadFactor),
        "recommendedFare": float(recommendedFare),
        "currency": currency,
    }


def revenue_report(
    callerDid: str = "",
    flightNo: str = "",
    depDate: str = "",
    paxRevenue: float = 0.0,
    cargoRevenue: float = 0.0,
    ancillaryRevenue: float = 0.0,
    currency: str = "USD",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("revenue-report", f"{flightNo}:{depDate}")
    now = _now()
    total_revenue = float(paxRevenue) + float(cargoRevenue) + float(ancillaryRevenue)
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_yield_fare_class
              (vertex_id, flight_no, dep_date, pax_revenue, cargo_revenue,
               ancillary_revenue, total_revenue, currency, status, created_at,
               actor_did, org_id, user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, depDate, float(paxRevenue), float(cargoRevenue),
                float(ancillaryRevenue), total_revenue, currency,
                "reported", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "depDate": depDate,
        "totalRevenue": total_revenue,
        "currency": currency,
    }


def demand_forecast(
    callerDid: str = "",
    flightNo: str = "",
    depDate: str = "",
    forecastPax: int = 0,
    forecastRevenue: float = 0.0,
    currency: str = "USD",
    modelVersion: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("demand-forecast")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_yield_fare_class
              (vertex_id, flight_no, dep_date, forecast_pax, forecast_revenue, currency,
               model_version, status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, depDate, int(forecastPax), float(forecastRevenue),
                currency, modelVersion or "v1", "forecast", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "depDate": depDate,
        "forecastPax": int(forecastPax),
        "forecastRevenue": float(forecastRevenue),
        "currency": currency,
    }


def register(worker: Any, *, timeout_ms: int = 60_000) -> None:
    tasks = {
        "air.yield.fare_class.publish": publish_fare_class,
        "air.yield.inventory.adjust": adjust_inventory,
        "air.yield.fare.file": file_fare,
        "air.yield.overbooking.set": set_overbooking,
        "air.yield.group.process": process_group,
        "air.yield.price.dynamic": dynamic_price,
        "air.yield.revenue.report": revenue_report,
        "air.yield.demand.forecast": demand_forecast,
    }
    for task_type, handler in tasks.items():
        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(handler)
