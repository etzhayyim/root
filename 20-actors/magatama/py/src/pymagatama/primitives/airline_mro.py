"""Airline MRO (Maintenance, Repair & Overhaul) XRPC primitives for BPMN/LangServer."""

from __future__ import annotations

import datetime as _dt
import uuid
from typing import Any

from pymagatama.db_sync import sync_cursor


APP_DID = "did:web:air-mro.etzhayyim.com"
ACTOR_SLUG = "air-mro"


def _now() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _vid(kind: str, key: str) -> str:
    safe_key = key.replace("/", "_").replace(" ", "_")[:160] or uuid.uuid4().hex
    return f"air-mro:{kind}:{safe_key}"


def _new_vid(kind: str) -> str:
    return f"air-mro:{kind}:{uuid.uuid4().hex}"


def create_work_order(
    callerDid: str = "",
    tailNumber: str = "",
    workOrderRef: str = "",
    taskType: str = "",
    description: str = "",
    priority: str = "routine",
    dueDate: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("work-order", workOrderRef or f"{tailNumber}:{taskType}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_mro_work_order
              (vertex_id, tail_number, work_order_ref, task_type, description,
               priority, due_date, status, created_at, actor_did, org_id,
               user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, tailNumber, workOrderRef or vertex_id, taskType,
                description or "", priority, dueDate or now[:10],
                "open", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "workOrderRef": workOrderRef or vertex_id,
        "tailNumber": tailNumber,
        "priority": priority,
        "workOrderStatus": "open",
    }


def track_component(
    callerDid: str = "",
    partNumber: str = "",
    serialNumber: str = "",
    tailNumber: str = "",
    installDate: str = "",
    cyclesSinceNew: int = 0,
    hoursSinceNew: float = 0.0,
    nextDueDate: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("component", f"{partNumber}:{serialNumber}")
    now = _now()
    today = now[:10]
    days_to_next_due = 0
    if nextDueDate and nextDueDate >= today:
        try:
            due_dt = _dt.date.fromisoformat(nextDueDate)
            days_to_next_due = (due_dt - _dt.date.fromisoformat(today)).days
        except ValueError:
            days_to_next_due = 0
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_mro_component
              (vertex_id, part_number, serial_number, tail_number, install_date,
               cycles_since_new, hours_since_new, next_due_date, days_to_next_due,
               status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, partNumber, serialNumber, tailNumber, installDate or today,
                int(cyclesSinceNew), float(hoursSinceNew), nextDueDate, days_to_next_due,
                "serviceable", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "partNumber": partNumber,
        "serialNumber": serialNumber,
        "daysToNextDue": days_to_next_due,
        "componentStatus": "serviceable",
    }


def check_airworthiness(
    callerDid: str = "",
    tailNumber: str = "",
    checkType: str = "",
    checkDate: str = "",
    expiryDate: str = "",
    inspector: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("airworthiness", f"{tailNumber}:{checkType}")
    now = _now()
    today = now[:10]
    days_until_due = 0
    if expiryDate and expiryDate >= today:
        try:
            exp_dt = _dt.date.fromisoformat(expiryDate)
            days_until_due = (exp_dt - _dt.date.fromisoformat(today)).days
        except ValueError:
            days_until_due = 0
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_mro_work_order
              (vertex_id, tail_number, check_type, check_date, expiry_date,
               inspector, days_until_due, status, created_at, actor_did, org_id,
               user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, tailNumber, checkType, checkDate or today,
                expiryDate, inspector or "", days_until_due,
                "airworthy", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "tailNumber": tailNumber,
        "checkType": checkType,
        "expiryDate": expiryDate,
        "daysUntilDue": days_until_due,
        "airworthinessStatus": "airworthy",
    }


def report_occurrence(
    callerDid: str = "",
    tailNumber: str = "",
    flightNo: str = "",
    occurrenceDate: str = "",
    category: str = "",
    description: str = "",
    reportRef: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("occurrence")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_mro_work_order
              (vertex_id, tail_number, flight_no, occurrence_date, category,
               description, report_ref, status, created_at, actor_did, org_id,
               user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, tailNumber, flightNo or "", occurrenceDate or now[:10],
                category or "", description or "", reportRef or vertex_id,
                "reported", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "tailNumber": tailNumber,
        "occurrenceDate": occurrenceDate or now[:10],
        "reportRef": reportRef or vertex_id,
        "occurrenceStatus": "reported",
    }


def schedule_maintenance(
    callerDid: str = "",
    tailNumber: str = "",
    checkType: str = "",
    scheduledDate: str = "",
    estimatedDays: int = 1,
    hangarCode: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("maint-sched", f"{tailNumber}:{checkType}:{scheduledDate}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_mro_work_order
              (vertex_id, tail_number, check_type, scheduled_date, estimated_days,
               hangar_code, status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, tailNumber, checkType, scheduledDate or now[:10],
                int(estimatedDays), hangarCode or "",
                "scheduled", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "tailNumber": tailNumber,
        "checkType": checkType,
        "scheduledDate": scheduledDate or now[:10],
        "maintenanceStatus": "scheduled",
    }


def reliability_report(
    callerDid: str = "",
    tailNumber: str = "",
    reportPeriod: str = "",
    dispatchReliability: float = 0.0,
    technicalDelayCount: int = 0,
    pireps: int = 0,
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("reliability", f"{tailNumber}:{reportPeriod}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_mro_work_order
              (vertex_id, tail_number, report_period, dispatch_reliability,
               technical_delay_count, pireps, status, created_at, actor_did,
               org_id, user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, tailNumber, reportPeriod, float(dispatchReliability),
                int(technicalDelayCount), int(pireps),
                "reported", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "tailNumber": tailNumber,
        "reportPeriod": reportPeriod,
        "dispatchReliability": float(dispatchReliability),
    }


def order_spare_part(
    callerDid: str = "",
    partNumber: str = "",
    quantity: int = 1,
    supplierCode: str = "",
    urgency: str = "routine",
    workOrderRef: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("spare-order")
    now = _now()
    aog_escalated = urgency.lower() == "aog"
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_mro_component
              (vertex_id, part_number, quantity, supplier_code, urgency,
               work_order_ref, aog_escalated, status, ordered_at, created_at,
               actor_did, org_id, user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, partNumber, int(quantity), supplierCode or "",
                urgency, workOrderRef or "", aog_escalated,
                "ordered", now, now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "partNumber": partNumber,
        "quantity": int(quantity),
        "urgency": urgency,
        "aogEscalated": aog_escalated,
        "orderStatus": "ordered",
    }


def record_gse(
    callerDid: str = "",
    gseId: str = "",
    gseType: str = "",
    iataCode: str = "",
    serviceDate: str = "",
    nextServiceDate: str = "",
    operationalStatus: str = "serviceable",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("gse", f"{gseId}:{iataCode}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_mro_work_order
              (vertex_id, gse_id, gse_type, iata_code, service_date,
               next_service_date, operational_status, status, created_at, actor_did,
               org_id, user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, gseId, gseType, iataCode,
                serviceDate or now[:10], nextServiceDate or "",
                operationalStatus, "recorded", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 1, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "gseId": gseId,
        "gseType": gseType,
        "iataCode": iataCode,
        "operationalStatus": operationalStatus,
    }


def register(worker: Any, *, timeout_ms: int = 60_000) -> None:
    tasks = {
        "air.mro.work_order.create": create_work_order,
        "air.mro.component.track": track_component,
        "air.mro.airworthiness.check": check_airworthiness,
        "air.mro.occurrence.report": report_occurrence,
        "air.mro.maintenance.schedule": schedule_maintenance,
        "air.mro.reliability.report": reliability_report,
        "air.mro.spare_part.order": order_spare_part,
        "air.mro.gse.record": record_gse,
    }
    for task_type, handler in tasks.items():
        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(handler)
