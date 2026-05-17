"""Airline Safety Management System XRPC primitives for BPMN/LangServer."""

from __future__ import annotations

import datetime as _dt
import uuid
from typing import Any

from pymagatama.db_sync import sync_cursor


APP_DID = "did:web:air-sms.etzhayyim.com"
ACTOR_SLUG = "air-sms"


def _now() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _vid(kind: str, key: str) -> str:
    safe_key = key.replace("/", "_").replace(" ", "_")[:160] or uuid.uuid4().hex
    return f"air-sms:{kind}:{safe_key}"


def _new_vid(kind: str) -> str:
    return f"air-sms:{kind}:{uuid.uuid4().hex}"


def submit_safety_report(
    callerDid: str = "",
    reportRef: str = "",
    reporterDid: str = "",
    category: str = "",
    occurrence: str = "",
    station: str = "",
    flightNo: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("safety-report", reportRef or occurrence or uuid.uuid4().hex[:16])
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_sms_safety_report
              (vertex_id, report_ref, reporter_did, category, occurrence, station,
               flight_no, status, submitted_at, created_at, actor_did, org_id,
               user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, reportRef or vertex_id, reporterDid or callerDid or APP_DID,
                category, occurrence or "", station or "", flightNo or "",
                "submitted", now, now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 2, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "reportRef": reportRef or vertex_id,
        "category": category,
        "reportStatus": "submitted",
    }


def assess_risk(
    callerDid: str = "",
    reportRef: str = "",
    likelihood: int = 1,
    severity: int = 1,
    mitigations: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("risk-assess")
    now = _now()
    risk_score = int(likelihood) * int(severity)
    if risk_score >= 15:
        risk_level = "high"
    elif risk_score >= 8:
        risk_level = "medium"
    else:
        risk_level = "low"
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_sms_safety_report
              (vertex_id, report_ref, likelihood, severity, risk_score,
               risk_level, mitigations, status, created_at, actor_did, org_id,
               user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, reportRef, int(likelihood), int(severity), risk_score,
                risk_level, mitigations or "",
                "assessed", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 2, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "reportRef": reportRef,
        "riskScore": risk_score,
        "riskLevel": risk_level,
        "likelihood": int(likelihood),
        "severity": int(severity),
    }


def record_iosa_finding(
    callerDid: str = "",
    auditRef: str = "",
    findingRef: str = "",
    iosaCategory: str = "",
    findingType: str = "",
    dueDate: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("iosa-finding", findingRef or f"{auditRef}:{iosaCategory}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_sms_safety_report
              (vertex_id, audit_ref, finding_ref, iosa_category, finding_type,
               due_date, status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, auditRef, findingRef or vertex_id, iosaCategory, findingType or "",
                dueDate or now[:10],
                "open", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 2, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "auditRef": auditRef,
        "findingRef": findingRef or vertex_id,
        "iosaCategory": iosaCategory,
        "findingStatus": "open",
    }


def file_regulatory(
    callerDid: str = "",
    regulatoryBody: str = "",
    filingType: str = "",
    filingRef: str = "",
    periodStart: str = "",
    periodEnd: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("regulatory", f"{regulatoryBody}:{filingType}:{filingRef or periodStart}")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_sms_safety_report
              (vertex_id, regulatory_body, filing_type, filing_ref, period_start,
               period_end, status, filed_at, created_at, actor_did, org_id,
               user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, regulatoryBody, filingType, filingRef or vertex_id,
                periodStart or now[:10], periodEnd or now[:10],
                "filed", now, now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 2, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "regulatoryBody": regulatoryBody,
        "filingRef": filingRef or vertex_id,
        "filingStatus": "filed",
    }


def report_occurrence(
    callerDid: str = "",
    occurrenceRef: str = "",
    occurrenceType: str = "",
    occurrenceDate: str = "",
    station: str = "",
    severity: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("occurrence", occurrenceRef or occurrenceType)
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_sms_safety_report
              (vertex_id, occurrence_ref, occurrence_type, occurrence_date, station,
               severity, status, created_at, actor_did, org_id, user_id, actor_id,
               sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, occurrenceRef or vertex_id, occurrenceType,
                occurrenceDate or now[:10], station or "", severity or "low",
                "reported", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 2, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "occurrenceRef": occurrenceRef or vertex_id,
        "occurrenceType": occurrenceType,
        "severity": severity or "low",
    }


def distribute_bulletin(
    callerDid: str = "",
    bulletinRef: str = "",
    bulletinType: str = "",
    subject: str = "",
    targetAudience: str = "",
    effectiveDate: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _vid("bulletin", bulletinRef or bulletinType)
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_sms_safety_report
              (vertex_id, bulletin_ref, bulletin_type, subject, target_audience,
               effective_date, status, distributed_at, created_at, actor_did,
               org_id, user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, bulletinRef or vertex_id, bulletinType, subject or "",
                targetAudience or "all", effectiveDate or now[:10],
                "distributed", now, now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 2, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "bulletinRef": bulletinRef or vertex_id,
        "bulletinType": bulletinType,
        "bulletinStatus": "distributed",
    }


def screen_dg(
    callerDid: str = "",
    flightNo: str = "",
    depDate: str = "",
    dgClass: str = "",
    unNumber: str = "",
    quantity: float = 0.0,
    unit: str = "",
    notocRef: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("dg-screen")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_sms_safety_report
              (vertex_id, flight_no, dep_date, dg_class, un_number, quantity,
               unit, notoc_ref, status, created_at, actor_did, org_id, user_id,
               actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, flightNo, depDate, dgClass, unNumber or "",
                float(quantity), unit or "kg", notocRef or vertex_id,
                "screened", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 2, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "flightNo": flightNo,
        "dgClass": dgClass,
        "unNumber": unNumber,
        "notocRef": notocRef or vertex_id,
        "screenStatus": "screened",
    }


def raise_security_alert(
    callerDid: str = "",
    alertRef: str = "",
    threatType: str = "",
    flightNo: str = "",
    depDate: str = "",
    threatLevel: str = "low",
    description: str = "",
    **_: Any,
) -> dict[str, Any]:
    vertex_id = _new_vid("sec-alert")
    now = _now()
    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_air_sms_safety_report
              (vertex_id, alert_ref, threat_type, flight_no, dep_date,
               threat_level, description, status, created_at, actor_did,
               org_id, user_id, actor_id, sensitivity_ord, owner_did)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                vertex_id, alertRef or vertex_id, threatType, flightNo or "",
                depDate or "", threatLevel, description or "",
                "active", now,
                APP_DID, "anon", callerDid or APP_DID, ACTOR_SLUG, 2, callerDid or APP_DID,
            ),
        )
    return {
        "vertexId": vertex_id,
        "status": "ok",
        "alertRef": alertRef or vertex_id,
        "threatType": threatType,
        "threatLevel": threatLevel,
        "alertStatus": "active",
    }


def register(worker: Any, *, timeout_ms: int = 60_000) -> None:
    tasks = {
        "air.sms.safety_report.submit": submit_safety_report,
        "air.sms.risk.assess": assess_risk,
        "air.sms.iosa.finding": record_iosa_finding,
        "air.sms.regulatory.file": file_regulatory,
        "air.sms.occurrence.report": report_occurrence,
        "air.sms.bulletin.distribute": distribute_bulletin,
        "air.sms.dg.screen": screen_dg,
        "air.sms.security.alert": raise_security_alert,
    }
    for task_type, handler in tasks.items():
        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(handler)
