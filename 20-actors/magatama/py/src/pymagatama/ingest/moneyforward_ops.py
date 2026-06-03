"""MoneyForward replacement handlers for pod-side LangServer tasks.

The functions in this module are deliberately small SQL boundaries. Durable
retry and process state belong to LangGraph/Pregel orchestration; transactional
records live in RisingWave vertex tables.
"""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from typing import Any

from pymagatama.db_sync import sync_cursor

OWNER_MAP = {
    "works": "did:plc:etzhayyim-works",
    "japan": "did:plc:etzhayyim-japan",
    "labo": "did:plc:etzhayyim-labo",
}


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def today() -> str:
    return now_iso()[:10]


def _str(value: Any) -> str:
    return "" if value is None else str(value)


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def resolve_owner(value: Any) -> str:
    text = _str(value)
    if text.startswith("did:"):
        return text
    return OWNER_MAP.get(text, OWNER_MAP["works"])


def _fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in (cur.fetchall() or [])]


def _fetch_one(sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    rows = _fetch_all(sql, params)
    return rows[0] if rows else None


def _execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        return int(cur.rowcount or 0)


def _insert_if_missing(table: str, vertex_id: str, sql: str, params: tuple[Any, ...]) -> int:
    try:
        existing = _fetch_one(f"SELECT vertex_id FROM {table} WHERE vertex_id=%s LIMIT 1", (vertex_id,))
    except RuntimeError as exc:
        if "RW_URL env var not set" not in str(exc):
            raise
        existing = None
    if existing:
        return 0
    return _execute(sql, params)


def _next_seq(table: str) -> int:
    with sync_cursor() as cur:
        cur.execute(f"SELECT COALESCE(MAX(_seq), 0) + 1 AS seq FROM {table}")
        row = cur.fetchone()
        return int(row[0] if row else 1)


def _slug(text: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(part for part in out.split("-") if part)[:80] or "record"


def _vid(owner: str, nsid: str, rkey: str) -> str:
    return f"{owner}|{nsid}|{rkey}"


def _uri(owner: str, nsid: str, rkey: str) -> str:
    return f"at://{owner}/{nsid}/{rkey}"


def _json(value: Any) -> str:
    return json.dumps(value or {}, ensure_ascii=False, separators=(",", ":"))


def _as_utc_ts(value: str, end_of_day: bool = False) -> str:
    date = (value or today())[:10]
    time_part = "23:59:59" if end_of_day else "00:00:00"
    return f"{date} {time_part}+00:00"


def issue_invoice(
    owner: str = "",
    customerDid: str = "",
    projectDid: str = "",
    agreementDid: str = "",
    invoiceNumber: str = "",
    period: Any = None,
    lineItems: Any = None,
    includeApprovedTimeEntries: Any = False,
    taxRate: Any = 0.10,
    discountAmount: Any = 0,
    currency: str = "JPY",
    issuedAt: str = "",
    dueAt: str = "",
    **_: Any,
) -> dict[str, Any]:
    owner_did = resolve_owner(owner)
    if not customerDid or not issuedAt or not dueAt:
        return {"error": "customerDid, issuedAt, dueAt required"}
    items = list(lineItems or [])
    attached = 0
    if includeApprovedTimeEntries and projectDid:
        period_from = (period or {}).get("from") if isinstance(period, dict) else ""
        period_to = (period or {}).get("to") if isinstance(period, dict) else ""
        filters = ["project_did=%s", "approval_status='approved'", "billable=true"]
        args: list[Any] = [projectDid]
        if period_from:
            filters.append("entry_date >= %s")
            args.append(period_from[:10])
        if period_to:
            filters.append("entry_date <= %s")
            args.append(period_to[:10])
        rows = _fetch_all(
            f"SELECT vertex_id, member_did, entry_date, hours FROM vertex_atrecord_kousuu_time_entry WHERE {' AND '.join(filters)} ORDER BY entry_date",
            tuple(args),
        )
        for row in rows:
            items.append({
                "kind": "time",
                "description": f"Billable time {row['entry_date']} {row['member_did']}",
                "quantity": float(row.get("hours") or 0),
                "unitRate": 0,
                "amount": 0,
                "sourceDid": row["vertex_id"],
            })
        attached = len(rows)
    subtotal = sum(_float(item.get("amount")) for item in items) - _float(discountAmount)
    tax_rate = _float(taxRate, 0.10)
    tax_amount = round(subtotal * tax_rate)
    total = subtotal + tax_amount
    number = invoiceNumber or f"INV-{int(time.time())}"
    rkey = _slug(number)
    vertex_id = _vid(owner_did, "com.etzhayyim.apps.seikyu.invoice", rkey)
    period_from = (period or {}).get("from", "")[:10] if isinstance(period, dict) else None
    period_to = (period or {}).get("to", "")[:10] if isinstance(period, dict) else None
    inserted = _insert_if_missing(
        "vertex_atrecord_seikyu_invoice",
        vertex_id,
        """INSERT INTO vertex_atrecord_seikyu_invoice
        (vertex_id,_seq,owner_did,customer_did,project_did,agreement_did,invoice_number,
         period_from,period_to,issued_at,due_at,subtotal,tax_rate,tax_amount,total,currency,
         status,pdf_cid,peppol_message_id,sent_at,paid_at,created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'draft',NULL,NULL,NULL,NULL,%s)""",
        (
            vertex_id, _next_seq("vertex_atrecord_seikyu_invoice"), owner_did,
            customerDid, projectDid or None, agreementDid or None, number,
            period_from, period_to, issuedAt, dueAt, subtotal, tax_rate, tax_amount,
            total, currency or "JPY", now_iso(),
        ),
    )
    return {
        "invoiceDid": vertex_id,
        "uri": _uri(owner_did, "com.etzhayyim.apps.seikyu.invoice", rkey),
        "subtotal": subtotal,
        "taxAmount": tax_amount,
        "total": total,
        "status": "draft",
        "timeEntriesAttached": attached,
        "inserted": inserted > 0,
    }


def send_invoice(invoiceDid: str = "", pdfCid: str = "", peppolMessageId: str = "", **_: Any) -> dict[str, Any]:
    if not invoiceDid:
        return {"error": "invoiceDid required"}
    updated = _execute(
        """UPDATE vertex_atrecord_seikyu_invoice
        SET status='sent', pdf_cid=COALESCE(NULLIF(%s,''), pdf_cid),
            peppol_message_id=COALESCE(NULLIF(%s,''), peppol_message_id), sent_at=%s
        WHERE vertex_id=%s""",
        (pdfCid, peppolMessageId, now_iso(), invoiceDid),
    )
    return {"ok": updated > 0, "invoiceDid": invoiceDid, "status": "sent"}


def void_invoice(invoiceDid: str = "", reason: str = "", **_: Any) -> dict[str, Any]:
    updated = _execute(
        "UPDATE vertex_atrecord_seikyu_invoice SET status='void', pdf_cid=COALESCE(pdf_cid,%s) WHERE vertex_id=%s",
        (reason or None, invoiceDid),
    )
    return {"ok": updated > 0, "invoiceDid": invoiceDid, "status": "void"}


def record_payment_received(
    invoiceDid: str = "",
    paymentDate: str = "",
    amount: Any = 0,
    currency: str = "JPY",
    paymentMethod: str = "",
    reference: str = "",
    **_: Any,
) -> dict[str, Any]:
    invoice = _fetch_one("SELECT owner_did,total FROM vertex_atrecord_seikyu_invoice WHERE vertex_id=%s", (invoiceDid,))
    if not invoice:
        return {"error": "invoice not found"}
    rkey = _slug(f"{invoiceDid}-{paymentDate or today()}-{reference or int(time.time())}")
    vertex_id = _vid(invoice["owner_did"], "com.etzhayyim.apps.seikyu.paymentReceived", rkey)
    _insert_if_missing(
        "vertex_atrecord_seikyu_payment_received",
        vertex_id,
        """INSERT INTO vertex_atrecord_seikyu_payment_received
        (vertex_id,_seq,owner_did,invoice_did,payment_date,amount,currency,payment_method,reference,created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            vertex_id, _next_seq("vertex_atrecord_seikyu_payment_received"),
            invoice["owner_did"], invoiceDid, (paymentDate or today())[:10],
            _float(amount), currency or "JPY", paymentMethod or None, reference or None, now_iso(),
        ),
    )
    paid = _fetch_one(
        "SELECT COALESCE(SUM(amount),0) AS paid FROM vertex_atrecord_seikyu_payment_received WHERE invoice_did=%s",
        (invoiceDid,),
    )
    status = "paid" if _float((paid or {}).get("paid")) >= _float(invoice.get("total")) else "partiallyPaid"
    _execute("UPDATE vertex_atrecord_seikyu_invoice SET status=%s, paid_at=CASE WHEN %s='paid' THEN %s ELSE paid_at END WHERE vertex_id=%s", (status, status, now_iso(), invoiceDid))
    return {"ok": True, "paymentDid": vertex_id, "invoiceDid": invoiceDid, "status": status}


def list_invoices(owner: str = "", status: str = "", customerDid: str = "", limit: Any = 100, **_: Any) -> dict[str, Any]:
    owner_did = resolve_owner(owner)
    args: list[Any] = [owner_did]
    filters = ["owner_did=%s"]
    if status:
        args.append(status)
        filters.append("status=%s")
    if customerDid:
        args.append(customerDid)
        filters.append("customer_did=%s")
    rows = _fetch_all(
        f"SELECT *, _seq AS cursor FROM vertex_atrecord_seikyu_invoice WHERE {' AND '.join(filters)} ORDER BY _seq DESC LIMIT %s",
        tuple(args + [max(1, min(_int(limit, 100), 500))]),
    )
    return {"invoices": rows}


def get_invoice_aging(owner: str = "", **_: Any) -> dict[str, Any]:
    owner_did = resolve_owner(owner)
    rows = _fetch_all("SELECT * FROM view_seikyu_invoice_aging WHERE owner_did=%s ORDER BY due_at", (owner_did,))
    return {"owner": owner_did, "items": rows}


def submit_peppol(invoiceDid: str = "", messageId: str = "", **_: Any) -> dict[str, Any]:
    msg = messageId or f"peppol-{int(time.time())}"
    updated = _execute("UPDATE vertex_atrecord_seikyu_invoice SET peppol_message_id=%s WHERE vertex_id=%s", (msg, invoiceDid))
    return {"ok": updated > 0, "invoiceDid": invoiceDid, "peppolMessageId": msg}


def draft_agreement(
    owner: str = "",
    counterpartyDid: str = "",
    title: str = "",
    agreementType: str = "other",
    effectiveFrom: str = "",
    termMonths: Any = None,
    autoRenew: Any = False,
    totalAmount: Any = None,
    currency: str = "JPY",
    recurringAmount: Any = None,
    recurringFrequency: str = "",
    pdfCid: str = "",
    **_: Any,
) -> dict[str, Any]:
    owner_did = resolve_owner(owner)
    if not counterpartyDid or not title or not effectiveFrom or not pdfCid:
        return {"error": "counterpartyDid, title, effectiveFrom, pdfCid required"}
    rkey = _slug(f"{title}-{int(time.time())}")
    vertex_id = _vid(owner_did, "com.etzhayyim.apps.keiyaku.agreement", rkey)
    _insert_if_missing(
        "vertex_atrecord_keiyaku_agreement",
        vertex_id,
        """INSERT INTO vertex_atrecord_keiyaku_agreement
        (vertex_id,_seq,owner_did,counterparty_did,title,agreement_type,effective_from,
         term_months,auto_renew,total_amount,currency,pdf_cid,signing_status,signed_at,
         terminated_at,created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'drafted',NULL,NULL,%s)""",
        (
            vertex_id, _next_seq("vertex_atrecord_keiyaku_agreement"), owner_did,
            counterpartyDid, title, agreementType, effectiveFrom[:10], termMonths,
            bool(autoRenew), totalAmount, currency or "JPY", pdfCid, now_iso(),
        ),
    )
    if recurringAmount:
        schedule_id = _vid(owner_did, "com.etzhayyim.apps.seikyu.recurringSchedule", _slug(rkey))
        _insert_if_missing(
            "vertex_atrecord_seikyu_recurring_schedule",
            schedule_id,
            """INSERT INTO vertex_atrecord_seikyu_recurring_schedule
            (vertex_id,_seq,owner_did,customer_did,agreement_did,amount,currency,frequency,next_issue_date,status,created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'active',%s)""",
            (
                schedule_id, _next_seq("vertex_atrecord_seikyu_recurring_schedule"),
                owner_did, counterpartyDid, vertex_id, _float(recurringAmount),
                currency or "JPY", recurringFrequency or "monthly", effectiveFrom[:10], now_iso(),
            ),
        )
    return {"agreementDid": vertex_id, "uri": _uri(owner_did, "com.etzhayyim.apps.keiyaku.agreement", rkey)}


def submit_for_signature(agreementDid: str = "", signerDid: str = "", **_: Any) -> dict[str, Any]:
    agreement = _fetch_one("SELECT owner_did FROM vertex_atrecord_keiyaku_agreement WHERE vertex_id=%s", (agreementDid,))
    if not agreement:
        return {"error": "agreement not found"}
    flow_id = _vid(agreement["owner_did"], "com.etzhayyim.apps.keiyaku.signingFlow", _slug(f"{agreementDid}-{signerDid}-{int(time.time())}"))
    _insert_if_missing(
        "vertex_atrecord_keiyaku_signing_flow",
        flow_id,
        """INSERT INTO vertex_atrecord_keiyaku_signing_flow
        (vertex_id,_seq,owner_did,agreement_did,signer_did,status,requested_at,completed_at,created_at)
        VALUES (%s,%s,%s,%s,%s,'requested',%s,NULL,%s)""",
        (flow_id, _next_seq("vertex_atrecord_keiyaku_signing_flow"), agreement["owner_did"], agreementDid, signerDid or None, now_iso(), now_iso()),
    )
    _execute("UPDATE vertex_atrecord_keiyaku_agreement SET signing_status='sent' WHERE vertex_id=%s", (agreementDid,))
    return {"ok": True, "agreementDid": agreementDid, "signingFlowDid": flow_id, "status": "sent"}


def sign_agreement(agreementDid: str = "", signedAt: str = "", **_: Any) -> dict[str, Any]:
    ts = signedAt or now_iso()
    updated = _execute("UPDATE vertex_atrecord_keiyaku_agreement SET signing_status='signed', signed_at=%s WHERE vertex_id=%s", (ts, agreementDid))
    _execute("UPDATE vertex_atrecord_keiyaku_signing_flow SET status='completed', completed_at=%s WHERE agreement_did=%s", (ts, agreementDid))
    return {"ok": updated > 0, "agreementDid": agreementDid, "status": "signed"}


def void_agreement(agreementDid: str = "", reason: str = "", **_: Any) -> dict[str, Any]:
    updated = _execute("UPDATE vertex_atrecord_keiyaku_agreement SET signing_status='void', terminated_at=%s WHERE vertex_id=%s", (now_iso(), agreementDid))
    return {"ok": updated > 0, "agreementDid": agreementDid, "status": "void", "reason": reason}


def list_active_agreements(owner: str = "", **_: Any) -> dict[str, Any]:
    owner_did = resolve_owner(owner)
    rows = _fetch_all("SELECT * FROM view_keiyaku_active_agreements WHERE owner_did=%s ORDER BY effective_from DESC", (owner_did,))
    return {"owner": owner_did, "agreements": rows}


def create_project(owner: str = "", customerDid: str = "", projectCode: str = "", projectName: str = "", budgetHours: Any = None, budgetCostJpy: Any = None, startDate: str = "", endDate: str = "", **_: Any) -> dict[str, Any]:
    owner_did = resolve_owner(owner)
    if not projectCode or not projectName or not startDate:
        return {"error": "projectCode, projectName, startDate required"}
    rkey = _slug(projectCode)
    vertex_id = _vid(owner_did, "com.etzhayyim.apps.kousuu.project", rkey)
    _insert_if_missing(
        "vertex_atrecord_kousuu_project",
        vertex_id,
        """INSERT INTO vertex_atrecord_kousuu_project
        (vertex_id,_seq,owner_did,customer_did,project_code,project_name,budget_hours,budget_cost_jpy,start_date,end_date,status,created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'active',%s)""",
        (vertex_id, _next_seq("vertex_atrecord_kousuu_project"), owner_did, customerDid or None, projectCode, projectName, budgetHours, budgetCostJpy, startDate[:10], endDate[:10] if endDate else None, now_iso()),
    )
    return {"projectDid": vertex_id, "uri": _uri(owner_did, "com.etzhayyim.apps.kousuu.project", rkey)}


def record_time_entry(owner: str = "", memberDid: str = "", projectDid: str = "", taskDid: str = "", entryDate: str = "", hours: Any = 0, billable: Any = True, **_: Any) -> dict[str, Any]:
    owner_did = resolve_owner(owner)
    if not memberDid or not projectDid or not entryDate:
        return {"error": "memberDid, projectDid, entryDate required"}
    rkey = _slug(f"{memberDid}-{projectDid}-{entryDate}-{int(time.time() * 1000)}")
    vertex_id = _vid(owner_did, "com.etzhayyim.apps.kousuu.timeEntry", rkey)
    _insert_if_missing(
        "vertex_atrecord_kousuu_time_entry",
        vertex_id,
        """INSERT INTO vertex_atrecord_kousuu_time_entry
        (vertex_id,_seq,owner_did,member_did,project_did,task_did,entry_date,hours,billable,invoice_lineitem_cid,approval_status,approved_by_did,approved_at,created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL,'submitted',NULL,NULL,%s)""",
        (vertex_id, _next_seq("vertex_atrecord_kousuu_time_entry"), owner_did, memberDid, projectDid, taskDid or None, entryDate[:10], _float(hours), bool(billable), now_iso()),
    )
    return {"timeEntryDid": vertex_id, "uri": _uri(owner_did, "com.etzhayyim.apps.kousuu.timeEntry", rkey)}


def approve_time_entry(timeEntryDid: str = "", approvedByDid: str = "", approved: Any = True, **_: Any) -> dict[str, Any]:
    status = "approved" if bool(approved) else "rejected"
    updated = _execute("UPDATE vertex_atrecord_kousuu_time_entry SET approval_status=%s, approved_by_did=%s, approved_at=%s WHERE vertex_id=%s", (status, approvedByDid or None, now_iso(), timeEntryDid))
    return {"ok": updated > 0, "timeEntryDid": timeEntryDid, "status": status}


def get_project_burn(owner: str = "", projectDid: str = "", **_: Any) -> dict[str, Any]:
    owner_did = resolve_owner(owner)
    if projectDid:
        rows = _fetch_all("SELECT * FROM view_kousuu_project_burn WHERE project_did=%s ORDER BY period_month", (projectDid,))
    else:
        rows = _fetch_all("SELECT * FROM view_kousuu_project_burn WHERE owner_did=%s ORDER BY project_code, period_month", (owner_did,))
    return {"owner": owner_did, "projectDid": projectDid or None, "items": rows}


def submit_expense(owner: str = "", employeeDid: str = "", projectDid: str = "", vendorName: str = "", expenseDate: str = "", amount: Any = 0, currency: str = "JPY", taxRate: Any = 0, category: str = "", receiptCid: str = "", **_: Any) -> dict[str, Any]:
    owner_did = resolve_owner(owner)
    if not employeeDid or not expenseDate:
        return {"error": "employeeDid and expenseDate required"}
    rkey = _slug(f"{employeeDid}-{expenseDate}-{int(time.time() * 1000)}")
    vertex_id = _vid(owner_did, "com.etzhayyim.apps.keihi.expense", rkey)
    _insert_if_missing(
        "vertex_atrecord_keihi_expense",
        vertex_id,
        """INSERT INTO vertex_atrecord_keihi_expense
        (vertex_id,_seq,owner_did,employee_did,project_did,vendor_name,expense_date,amount,currency,tax_rate,category,receipt_cid,status,approved_by_did,approved_at,created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'submitted',NULL,NULL,%s)""",
        (vertex_id, _next_seq("vertex_atrecord_keihi_expense"), owner_did, employeeDid, projectDid or None, vendorName or None, expenseDate[:10], _float(amount), currency or "JPY", _float(taxRate), category or None, receiptCid or None, now_iso()),
    )
    return {"expenseDid": vertex_id, "uri": _uri(owner_did, "com.etzhayyim.apps.keihi.expense", rkey), "status": "submitted"}


def approve_expense(expenseDid: str = "", approved: Any = True, approvedByDid: str = "", reason: str = "", **_: Any) -> dict[str, Any]:
    status = "approved" if bool(approved) else "rejected"
    updated = _execute("UPDATE vertex_atrecord_keihi_expense SET status=%s, approved_by_did=%s, approved_at=%s WHERE vertex_id=%s", (status, approvedByDid or None, now_iso(), expenseDid))
    return {"ok": updated > 0, "expenseDid": expenseDid, "status": status, "reason": reason, "kaikeiSourceType": "com.etzhayyim.apps.keihi.expense.approved" if status == "approved" else ""}


def upsert_employee(owner: str = "", employeeDid: str = "", displayNameEncrypted: str = "", employmentStatus: str = "active", joinedOn: str = "", leftOn: str = "", **_: Any) -> dict[str, Any]:
    owner_did = resolve_owner(owner)
    if not employeeDid or not displayNameEncrypted:
        return {"error": "employeeDid and displayNameEncrypted required"}
    rkey = _slug(employeeDid)
    vertex_id = _vid(owner_did, "com.etzhayyim.apps.jinji.employee", rkey)
    _execute("DELETE FROM vertex_atrecord_jinji_employee WHERE vertex_id=%s", (vertex_id,))
    _execute(
        """INSERT INTO vertex_atrecord_jinji_employee
        (vertex_id,_seq,owner_did,employee_did,display_name_encrypted,employment_status,joined_on,left_on,created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (vertex_id, _next_seq("vertex_atrecord_jinji_employee"), owner_did, employeeDid, displayNameEncrypted, employmentStatus, joinedOn[:10] if joinedOn else None, leftOn[:10] if leftOn else None, now_iso()),
    )
    return {"ok": True, "employeeVertexId": vertex_id}


def record_attendance(owner: str = "", employeeDid: str = "", workDate: str = "", minutesWorked: Any = 0, status: str = "submitted", **_: Any) -> dict[str, Any]:
    owner_did = resolve_owner(owner)
    rkey = _slug(f"{employeeDid}-{workDate}")
    vertex_id = _vid(owner_did, "com.etzhayyim.apps.jinji.attendance", rkey)
    _insert_if_missing(
        "vertex_atrecord_jinji_attendance",
        vertex_id,
        """INSERT INTO vertex_atrecord_jinji_attendance
        (vertex_id,_seq,owner_did,employee_did,work_date,minutes_worked,status,created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
        (vertex_id, _next_seq("vertex_atrecord_jinji_attendance"), owner_did, employeeDid, workDate[:10], _int(minutesWorked), status or "submitted", now_iso()),
    )
    return {"ok": True, "attendanceDid": vertex_id}


def complete_payroll_run(owner: str = "", payrollMonth: str = "", grossTotalEncrypted: str = "", statutoryTotalEncrypted: str = "", netTotalEncrypted: str = "", **_: Any) -> dict[str, Any]:
    owner_did = resolve_owner(owner)
    if not payrollMonth or not grossTotalEncrypted:
        return {"error": "payrollMonth and grossTotalEncrypted required"}
    rkey = _slug(payrollMonth)
    vertex_id = _vid(owner_did, "com.etzhayyim.apps.jinji.payrollRun", rkey)
    _execute("DELETE FROM vertex_atrecord_jinji_payroll_run WHERE vertex_id=%s", (vertex_id,))
    _execute(
        """INSERT INTO vertex_atrecord_jinji_payroll_run
        (vertex_id,_seq,owner_did,payroll_month,gross_total_encrypted,statutory_total_encrypted,net_total_encrypted,status,completed_at,created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,'completed',%s,%s)""",
        (vertex_id, _next_seq("vertex_atrecord_jinji_payroll_run"), owner_did, payrollMonth, grossTotalEncrypted, statutoryTotalEncrypted or None, netTotalEncrypted or None, now_iso(), now_iso()),
    )
    return {"ok": True, "payrollRunDid": vertex_id, "status": "completed", "kaikeiSourceType": "com.etzhayyim.apps.jinji.payrollRun.completed"}


def generate_statutory_report(
    owner: str = "",
    reportType: str = "",
    periodFrom: str = "",
    periodTo: str = "",
    artifactCid: str = "",
    **_: Any,
) -> dict[str, Any]:
    owner_did = resolve_owner(owner)
    if not reportType or not periodFrom or not periodTo:
        return {"error": "reportType, periodFrom, periodTo required"}
    rkey = _slug(f"{reportType}-{periodFrom[:10]}-{periodTo[:10]}")
    vertex_id = _vid(owner_did, "com.etzhayyim.apps.kaikei.statutoryReport", rkey)
    _execute("DELETE FROM vertex_kaikei_statutory_report WHERE vertex_id=%s", (vertex_id,))
    _execute(
        """INSERT INTO vertex_kaikei_statutory_report
        (vertex_id,_seq,owner_did,report_type,period_from,period_to,artifact_cid,status,generated_at,created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,'generated',%s,%s)""",
        (
            vertex_id, _next_seq("vertex_kaikei_statutory_report"), owner_did,
            reportType, periodFrom[:10], periodTo[:10], artifactCid or None, now_iso(), now_iso(),
        ),
    )
    return {"ok": True, "reportDid": vertex_id, "status": "generated"}


def validate_moneyforward_parity(
    owner: str = "",
    periodFrom: str = "",
    periodTo: str = "",
    mfExportCid: str = "",
    mfTotal: Any = 0,
    **_: Any,
) -> dict[str, Any]:
    owner_did = resolve_owner(owner)
    if not periodFrom or not periodTo:
        return {"error": "periodFrom and periodTo required"}
    rw = _fetch_one(
        """SELECT COALESCE(SUM(amount),0) AS total
        FROM vertex_atrecord_kaikei_journal_entry
        WHERE owner_did=%s AND posted_at >= %s AND posted_at <= %s""",
        (owner_did, _as_utc_ts(periodFrom), _as_utc_ts(periodTo, end_of_day=True)),
    )
    rw_total = _float((rw or {}).get("total"))
    mf_total = _float(mfTotal, rw_total)
    diff = rw_total - mf_total
    status = "matched" if abs(diff) < 1 else "mismatch"
    rkey = _slug(f"{periodFrom[:10]}-{periodTo[:10]}-{int(time.time())}")
    vertex_id = _vid(owner_did, "com.etzhayyim.apps.kaikei.moneyForwardParityRun", rkey)
    _execute(
        """INSERT INTO vertex_kaikei_moneyforward_parity_run
        (vertex_id,_seq,owner_did,period_from,period_to,mf_export_cid,rw_total,mf_total,diff_amount,status,checked_at,created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            vertex_id, _next_seq("vertex_kaikei_moneyforward_parity_run"), owner_did,
            periodFrom[:10], periodTo[:10], mfExportCid or None, rw_total, mf_total,
            diff, status, now_iso(), now_iso(),
        ),
    )
    return {"ok": True, "parityRunDid": vertex_id, "status": status, "diffAmount": diff}


def register_saas_asset(
    owner: str = "",
    provider: str = "",
    assetType: str = "",
    externalId: str = "",
    displayName: str = "",
    assigneeDid: str = "",
    metadata: Any = None,
    status: str = "active",
    **_: Any,
) -> dict[str, Any]:
    owner_did = resolve_owner(owner)
    if not provider or not assetType or not externalId or not displayName:
        return {"error": "provider, assetType, externalId, displayName required"}
    rkey = _slug(f"{provider}-{assetType}-{externalId}")
    vertex_id = _vid(owner_did, "com.etzhayyim.apps.kaisya.saasAsset", rkey)
    _execute("DELETE FROM vertex_kaisya_saas_asset WHERE vertex_id=%s", (vertex_id,))
    _execute(
        """INSERT INTO vertex_kaisya_saas_asset
        (vertex_id,_seq,owner_did,provider,asset_type,external_id,display_name,assignee_did,metadata_json,status,observed_at,created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            vertex_id, _next_seq("vertex_kaisya_saas_asset"), owner_did,
            provider, assetType, externalId, displayName, assigneeDid or None,
            _json(metadata), status or "active", now_iso(), now_iso(),
        ),
    )
    return {"ok": True, "assetDid": vertex_id}


def record_year_end_adjustment(
    owner: str = "",
    employeeDid: str = "",
    taxYear: Any = 0,
    declarationHash: str = "",
    artifactCid: str = "",
    status: str = "submitted",
    **_: Any,
) -> dict[str, Any]:
    owner_did = resolve_owner(owner)
    if not employeeDid or not taxYear or not declarationHash:
        return {"error": "employeeDid, taxYear, declarationHash required"}
    rkey = _slug(f"{employeeDid}-{taxYear}")
    vertex_id = _vid(owner_did, "com.etzhayyim.apps.jinji.yearEndAdjustment", rkey)
    _execute("DELETE FROM vertex_atrecord_jinji_year_end_adjustment WHERE vertex_id=%s", (vertex_id,))
    done = now_iso() if status == "completed" else None
    _execute(
        """INSERT INTO vertex_atrecord_jinji_year_end_adjustment
        (vertex_id,_seq,owner_did,employee_did,tax_year,declaration_hash,status,artifact_cid,completed_at,created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            vertex_id, _next_seq("vertex_atrecord_jinji_year_end_adjustment"),
            owner_did, employeeDid, _int(taxYear), declarationHash, status or "submitted",
            artifactCid or None, done, now_iso(),
        ),
    )
    return {"ok": True, "yearEndAdjustmentDid": vertex_id}


def register_mynumber_vault_ref(
    owner: str = "",
    employeeDid: str = "",
    vaultRefEncrypted: str = "",
    declarationHash: str = "",
    status: str = "active",
    **_: Any,
) -> dict[str, Any]:
    owner_did = resolve_owner(owner)
    if not employeeDid or not vaultRefEncrypted or not declarationHash:
        return {"error": "employeeDid, vaultRefEncrypted, declarationHash required"}
    rkey = _slug(employeeDid)
    vertex_id = _vid(owner_did, "com.etzhayyim.apps.jinji.mynumberVaultRef", rkey)
    _execute("DELETE FROM vertex_atrecord_jinji_mynumber_vault_ref WHERE vertex_id=%s", (vertex_id,))
    _execute(
        """INSERT INTO vertex_atrecord_jinji_mynumber_vault_ref
        (vertex_id,_seq,owner_did,employee_did,vault_ref_encrypted,declaration_hash,status,created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
        (
            vertex_id, _next_seq("vertex_atrecord_jinji_mynumber_vault_ref"),
            owner_did, employeeDid, vaultRefEncrypted, declarationHash,
            status or "active", now_iso(),
        ),
    )
    return {"ok": True, "vaultRefDid": vertex_id}
