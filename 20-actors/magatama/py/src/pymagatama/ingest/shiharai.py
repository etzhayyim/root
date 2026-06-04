"""Shiharai payment orchestration handlers for BPMN + Zeebe."""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.request
import uuid
from typing import Any

from pymagatama.db_sync import sync_cursor

ACTOR = "did:web:shiharai.etzhayyim.com"
APP = "shiharai"
APP_ACTOR_ID = "sys.shiharai"
APP_ORG = "etzhayyim"
APP_USER = "system"
APP_SENSITIVITY = 100
APPROVAL_MIN_LEN = 16


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def today() -> str:
    return now_iso()[:10]


def _str(value: Any) -> str:
    return "" if value is None else str(value)


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _bool(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).lower() not in {"0", "false", "no", "off"}


def _gid(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1000):x}-{uuid.uuid4().hex[:8]}"


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


def _vertex(collection: str, rkey: str) -> str:
    return f"at://{ACTOR}/com.etzhayyim.apps.shiharai.{collection}/{_rkey(rkey)}"


def _normalize_issuer_to_handle(issuer: str) -> str:
    i = issuer.lower()
    if "東京都水道" in issuer or "tokyo.suidoapp" in i or "waterworks.metro.tokyo" in i:
        return "tokyo-waterworks"
    if "paypay" in i and "bank" in i:
        return "paypay-bank"
    if "bitflyer" in i:
        return "bitflyer"
    if "paidy" in i:
        return "paidy"
    if "nuro" in i:
        return "nuro"
    if "fly.io" in i or "flyio" in i or "fly-io" in i:
        return "flyio"
    if "stripe" in i:
        return "stripe"
    return re.sub(r"^-+|-+$", "", re.sub(r"[^a-z0-9-]+", "-", i))[:48] or "unknown"


def _bpmn_call(method: str, params: dict[str, Any]) -> dict[str, Any]:
    # ADR-2604282300: com.etzhayyim.* must NOT route through CF Workers — use K8s ClusterIP.
    base = (
        os.environ.get("BPMN_DISPATCHER_INTERNAL_URL")
        or os.environ.get("BPMN_URL")
        or os.environ.get("DISPATCHER_URL")
        or "http://bpmn-dispatcher.mitama-udf.svc.cluster.local:8080"
    ).rstrip("/")
    req = urllib.request.Request(
        f"{base}/xrpc/com.etzhayyim.apps.bpmn.{method}",
        method="POST",
        data=json.dumps(params).encode(),
        headers={"content-type": "application/json", "user-agent": "etzhayyim-shiharai-zeebe/1"},
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        return {"error": f"bpmn.{method} failed: {e.code}", "body": raw[:500]}
    except Exception as e:
        return {"error": f"bpmn.{method} failed: {e}"}


def _insert_bill(bill: dict[str, Any]) -> None:
    _execute(
        """INSERT INTO vertex_shiharai_bill
        (vertex_id, created_date, sensitivity_ord, owner_did, rkey, repo, bill_id, issuer,
         biller_handle, amount_jpy, currency, due_date, customer_number, invoice_number,
         pay_url, method, source_email_id, state, extracted_at, created_at, org_id, user_id,
         actor_id, actor_did, org_did)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'JPY',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'anon')
        ON CONFLICT (vertex_id) DO NOTHING""",
        (
            _vertex("bill", bill["billId"]),
            today(),
            APP_SENSITIVITY,
            ACTOR,
            bill["billId"],
            ACTOR,
            bill["billId"],
            bill["issuer"],
            bill["billerHandle"],
            bill["amountJpy"],
            bill["dueDate"],
            bill.get("customerNumber") or "",
            bill.get("invoiceNumber") or "",
            bill.get("payUrl") or "",
            bill.get("method") or "unknown",
            bill.get("sourceEmailId") or "",
            bill["state"],
            bill["extractedAt"],
            now_iso(),
            APP_ORG,
            APP_USER,
            APP_ACTOR_ID,
            ACTOR,
        ),
    )


def extract_bill(emailBody: str = "", emailSubject: str = "", emailFrom: str = "", sourceEmailId: str = "", **_: Any) -> dict[str, Any]:
    if not emailBody and not emailSubject:
        return {"error": "emailBody or emailSubject required"}
    issuer = emailFrom or emailSubject[:64]
    body = emailBody or ""
    amount_match = re.search(r"(?:￥|¥|JPY)\s*([0-9,]+)", body) or re.search(r"([0-9,]+)\s*円", body)
    due_match = re.search(r"(\d{4})[\/\-年](\d{1,2})[\/\-月](\d{1,2})", body)
    customer_match = re.search(r"お客様番号[::\s]*([A-Z0-9\-]+)", body)
    pay_url_match = re.search(r"https?://[^\s<>\"]+", body)
    bill_id = _gid("bill")
    bill = {
        "billId": bill_id,
        "issuer": issuer,
        "billerHandle": _normalize_issuer_to_handle(issuer),
        "amountJpy": _int(amount_match.group(1).replace(",", "")) if amount_match else 0,
        "dueDate": f"{due_match.group(1)}-{due_match.group(2).zfill(2)}-{due_match.group(3).zfill(2)}" if due_match else today(),
        "customerNumber": customer_match.group(1) if customer_match else "",
        "payUrl": pay_url_match.group(0) if pay_url_match else "",
        "method": "inferred-from-email" if amount_match else "unknown",
        "sourceEmailId": sourceEmailId,
        "state": "due",
        "extractedAt": now_iso(),
    }
    _insert_bill(bill)
    return {"billId": bill_id, "bill": bill, "vertexId": _vertex("bill", bill_id)}


def list_pending_bills(limit: Any = 50, billerHandle: str = "", includeOverdue: Any = True, **_: Any) -> dict[str, Any]:
    n = max(1, min(_int(limit, 50), 200))
    include = _bool(includeOverdue, True)
    states = ("due", "overdue") if include else ("due",)
    if billerHandle:
        rows = _fetch_all(
            """SELECT bill_id, issuer, biller_handle, amount_jpy, due_date, customer_number, pay_url, method, state
            FROM vertex_shiharai_bill WHERE state = ANY(%s) AND biller_handle=%s ORDER BY due_date ASC LIMIT %s""",
            (list(states), billerHandle, n),
        )
    else:
        rows = _fetch_all(
            """SELECT bill_id, issuer, biller_handle, amount_jpy, due_date, customer_number, pay_url, method, state
            FROM vertex_shiharai_bill WHERE state = ANY(%s) ORDER BY due_date ASC LIMIT %s""",
            (list(states), n),
        )
    return {"limit": n, "billerHandle": billerHandle or None, "includeOverdue": include, "bills": rows}


def prepare_payment(
    billId: str = "",
    billerHandle: str = "",
    payUrl: str = "",
    expectedAmountJpy: Any = 0,
    method: str = "auto",
    requireConfirm: Any = True,
    processId: str = "",
    requesterDid: str = "",
    **_: Any,
) -> dict[str, Any]:
    if not billId:
        return {"error": "billId required"}
    bill = _fetch_one("SELECT * FROM vertex_shiharai_bill WHERE bill_id=%s LIMIT 1", (billId,)) or {}
    handle = billerHandle or _str(bill.get("biller_handle"))
    if not handle:
        return {"error": "billerHandle required"}
    url = payUrl or _str(bill.get("pay_url"))
    amount = _int(expectedAmountJpy) or _int(bill.get("amount_jpy"))
    pid = processId or f"shiharai-{handle}-v1"
    started = _bpmn_call(
        "startInstance",
        {
            "processId": pid,
            "variables": {"billId": billId, "billerHandle": handle, "payUrl": url, "expectedAmountJpy": amount, "method": method, "requireConfirm": _bool(requireConfirm), "requesterDid": requesterDid},
            "correlationKey": billId,
        },
    )
    if started.get("error"):
        return {"error": f"bpmn.startInstance: {started.get('error')}", "detail": started}
    instance_id = _str(started.get("instanceId"))
    job_id = f"job-{billId}"
    now = now_iso()
    _execute(
        """INSERT INTO vertex_shiharai_job
        (vertex_id, created_date, sensitivity_ord, owner_did, rkey, repo, job_id, bill_id, biller_handle,
         method, pay_url, state, require_confirm, enqueued_at, created_at, org_id, user_id, actor_id, actor_did, org_did)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'active',%s,%s,%s,%s,%s,%s,%s,'anon')
        ON CONFLICT (vertex_id) DO UPDATE SET state='active', pay_url=EXCLUDED.pay_url, enqueued_at=EXCLUDED.enqueued_at""",
        (_vertex("job", job_id), today(), APP_SENSITIVITY, ACTOR, job_id, ACTOR, job_id, billId, handle, method, url, "true" if _bool(requireConfirm) else "false", now, now, APP_ORG, APP_USER, APP_ACTOR_ID, ACTOR),
    )
    return {"billId": billId, "jobId": job_id, "bpmnInstanceId": instance_id, "state": "active"}


def confirm_payment(jobId: str = "", billId: str = "", bpmnInstanceId: str = "", approvalToken: str = "", expectedAmountJpy: Any = 0, approvedByDid: str = "did:anonymous", **_: Any) -> dict[str, Any]:
    if not bpmnInstanceId and jobId:
        row = _fetch_one("SELECT * FROM vertex_shiharai_job WHERE job_id=%s LIMIT 1", (jobId,))
        billId = billId or _str((row or {}).get("bill_id"))
    if not bpmnInstanceId and not billId:
        return {"error": "bpmnInstanceId, jobId or billId required"}
    if not approvalToken or len(approvalToken) < APPROVAL_MIN_LEN:
        return {"error": f"approvalToken required (>={APPROVAL_MIN_LEN} chars)"}
    token_hash = hashlib.sha256(approvalToken.encode()).hexdigest()
    signaled = _bpmn_call(
        "signalInstance",
        {"instanceId": bpmnInstanceId, "messageName": "approved", "payload": {"approvalTokenHash": token_hash, "approvedByDid": approvedByDid, "expectedAmountJpy": _int(expectedAmountJpy), "confirmedAt": now_iso()}},
    )
    if signaled.get("error"):
        return {"error": f"bpmn.signalInstance: {signaled.get('error')}", "detail": signaled}
    rid = bpmnInstanceId or jobId or billId
    _execute(
        """INSERT INTO vertex_shiharai_payment
        (vertex_id, created_date, sensitivity_ord, owner_did, rkey, repo, payment_id, bill_id,
         amount_jpy, approved_by_did, approval_token_hash, committed_at, created_at, org_id, user_id, actor_id, actor_did, org_did)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'anon')
        ON CONFLICT (vertex_id) DO NOTHING""",
        (_vertex("payment", rid), today(), APP_SENSITIVITY, ACTOR, rid, ACTOR, f"pay-{rid}", billId, _int(expectedAmountJpy), approvedByDid, token_hash, now_iso(), now_iso(), APP_ORG, APP_USER, APP_ACTOR_ID, ACTOR),
    )
    return {"jobId": jobId or None, "bpmnInstanceId": bpmnInstanceId or None, "billId": billId or None, "committed": False, "awaitingDaemonCommit": True}


def register_recurring(billerHandle: str = "", customerNumber: str = "", payMethod: str = "credit-card", requesterDid: str = "", **_: Any) -> dict[str, Any]:
    if not billerHandle or not customerNumber:
        return {"error": "billerHandle and customerNumber required"}
    recurring_id = _gid("recurring")
    started = _bpmn_call(
        "startInstance",
        {"processId": f"shiharai-{billerHandle}-recurring-v1", "variables": {"recurringId": recurring_id, "billerHandle": billerHandle, "customerNumber": customerNumber, "payMethod": payMethod, "requesterDid": requesterDid}, "correlationKey": recurring_id},
    )
    if started.get("error"):
        return {"error": f"bpmn.startInstance: {started.get('error')}", "detail": started}
    now = now_iso()
    _execute(
        """INSERT INTO vertex_shiharai_recurring
        (vertex_id, created_date, sensitivity_ord, owner_did, rkey, repo, recurring_id, biller_handle,
         customer_number, pay_method, state, registered_at, created_at, org_id, user_id, actor_id, actor_did, org_did)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'pending',%s,%s,%s,%s,%s,%s,'anon')
        ON CONFLICT (vertex_id) DO NOTHING""",
        (_vertex("recurring", recurring_id), today(), APP_SENSITIVITY, ACTOR, recurring_id, ACTOR, recurring_id, billerHandle, customerNumber, payMethod or "credit-card", now, now, APP_ORG, APP_USER, APP_ACTOR_ID, ACTOR),
    )
    return {"recurringId": recurring_id, "bpmnInstanceId": _str(started.get("instanceId")), "state": "pending"}


def list_recurring(limit: Any = 50, **_: Any) -> dict[str, Any]:
    n = max(1, min(_int(limit, 50), 200))
    rows = _fetch_all("SELECT recurring_id, biller_handle, customer_number, pay_method, state, registered_at FROM vertex_shiharai_recurring ORDER BY registered_at DESC LIMIT %s", (n,))
    return {"recurring": rows, "limit": n}


def get_job_status(jobId: str = "", bpmnInstanceId: str = "", **_: Any) -> dict[str, Any]:
    if not jobId and not bpmnInstanceId:
        return {"error": "jobId or bpmnInstanceId required"}
    job = _fetch_one("SELECT * FROM vertex_shiharai_job WHERE job_id=%s LIMIT 1", (jobId,)) if jobId else None
    state = _bpmn_call("getInstanceState", {"instanceId": bpmnInstanceId}) if bpmnInstanceId else {}
    return {"jobId": jobId or None, "bpmnInstanceId": bpmnInstanceId or None, "job": job or None, **state}
