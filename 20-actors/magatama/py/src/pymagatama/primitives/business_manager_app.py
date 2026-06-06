"""Business Manager ERP XRPC primitives for BPMN/LangServer."""

from __future__ import annotations

from datetime import datetime, timezone
import decimal as _decimal
import json
import time
import uuid
from typing import Any

from pymagatama.kotoba_datomic import get_kotoba_client


APP_DID = "did:web:business-manager.etzhayyim.com"
APP_ID = "bm4f8k2d1"
JOURNAL_APPROVAL_THRESHOLD = 1_000_000
DEFAULT_PAYMENT_TERMS_DAYS = 30
PO_EXECUTIVE_APPROVAL_THRESHOLD = 5_000_000
PROBATION_MONTHS = 3


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _id(prefix: str) -> str:
    return f"{prefix}_{int(time.time() * 1000):x}_{uuid.uuid4().hex[:8]}"


def _str(v: Any) -> str:
    return v if isinstance(v, str) else ""


def _num(v: Any, fallback: float = 0.0) -> float:
    try:
        n = float(v)
        return n if n == n and n not in (float("inf"), float("-inf")) else fallback
    except (TypeError, ValueError):
        return fallback


def _jsonable(v: Any) -> Any:
    if isinstance(v, (_dt.datetime, _dt.date)):
        return v.isoformat()
    if isinstance(v, _decimal.Decimal):
        f = float(v)
        return int(f) if f.is_integer() else f
    return v


def _vid(kind: str, key: str) -> str:
    return f"at://{APP_DID}/com.etzhayyim.apps.businessManager.{kind}/{key}"


def _rows(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in raw_rows:
        raw = {k: _jsonable(v) for k, v in row.items()}
        for key in ("line_items", "items"):
            if isinstance(raw.get(key), str) and raw[key].startswith("["):
                try:
                    raw[key] = json.loads(raw[key])
                except json.JSONDecodeError:
                    pass
        aliases = {
            "vertex_id": "vertexId",
            "entry_id": "entryId",
            "debit_account": "debitAccount",
            "credit_account": "creditAccount",
            "fiscal_period": "fiscalPeriod",
            "approval_status": "approvalStatus",
            "posted_at": "postedAt",
            "invoice_id": "invoiceId",
            "line_items": "lineItems",
            "payment_terms_days": "paymentTermsDays",
            "due_date": "dueDate",
            "issued_at": "issuedAt",
            "payment_id": "paymentId",
            "status_after": "statusAfter",
            "paid_at": "paidAt",
            "employee_id": "employeeId",
            "full_name": "fullName",
            "employment_type": "employmentType",
            "start_date": "startDate",
            "probation_status": "probationStatus",
            "probation_end_date": "probationEndDate",
            "registered_at": "registeredAt",
            "po_id": "poId",
            "total_amount": "totalAmount",
            "approval_level": "approvalLevel",
            "approver_comment": "approverComment",
            "decided_at": "decidedAt",
            "allocation_id": "allocationId",
            "allocated_amount": "allocatedAmount",
            "spent_amount": "spentAmount",
            "remaining_amount": "remainingAmount",
            "allocated_at": "allocatedAt",
            "created_at": "createdAt",
        }
        for src, dst in aliases.items():
            if src in raw and dst not in raw:
                raw[dst] = raw[src]
        out.append(raw)
    return out


def _write(kind: str, rec: dict[str, Any]) -> dict[str, Any]:
    record = {**rec, "org_id": rec.get("org_id") or "anon", "user_id": rec.get("user_id") or "anon", "actor_id": rec.get("actor_id") or APP_ID}
    if kind == "journalEntry":
            vid = _vid(kind, record["entryId"])
            get_kotoba_client().insert_row(
                "vertex_business_manager_journal_entry",
                {
                    "vertex_id": vid,
                    "entry_id": record["entryId"],
                    "description": record["description"],
                    "debit_account": record["debitAccount"],
                    "credit_account": record["creditAccount"],
                    "amount": _num(record["amount"]),
                    "currency": record.get("currency", "JPY"),
                    "fiscal_period": record.get("fiscalPeriod", ""),
                    "approval_status": record.get("approvalStatus", ""),
                    "posted_at": record.get("postedAt") or _now(),
                    "created_at": record.get("created_at") or _now(),
                    "org_id": record["org_id"],
                    "user_id": record["user_id"],
                    "actor_id": record["actor_id"],
                    "sensitivity_ord": 2,
                    "owner_did": APP_DID,
                },
            )
            return {"uri": vid}
        if kind == "invoice":
            vid = _vid(kind, record["invoiceId"])
            line_items = record.get("lineItems", "[]")
            if not isinstance(line_items, str):
                line_items = json.dumps(line_items, ensure_ascii=False)
            get_kotoba_client().insert_row(
                "vertex_business_manager_invoice",
                {
                    "vertex_id": vid,
                    "invoice_id": record["invoiceId"],
                    "counterparty": record.get("counterparty", ""),
                    "direction": record.get("direction", ""),
                    "amount": _num(record.get("amount")),
                    "currency": record.get("currency", "JPY"),
                    "line_items": line_items,
                    "payment_terms_days": int(_num(record.get("paymentTermsDays"))),
                    "due_date": record.get("dueDate", ""),
                    "status": record.get("status", "open"),
                    "issued_at": record.get("issuedAt", ""),
                    "created_at": record.get("created_at") or _now(),
                    "org_id": record["org_id"],
                    "user_id": record["user_id"],
                    "actor_id": record["actor_id"],
                    "sensitivity_ord": 2,
                    "owner_did": APP_DID,
                },
            )
            return {"uri": vid}
        if kind == "payment":
            vid = _vid(kind, record["paymentId"])
            invoice_vid = _vid("invoice", record["invoiceId"])
            get_kotoba_client().insert_row(
                "vertex_business_manager_payment",
                {
                    "vertex_id": vid,
                    "payment_id": record["paymentId"],
                    "invoice_id": record["invoiceId"],
                    "amount": _num(record["amount"]),
                    "method": record.get("method", ""),
                    "status_after": record.get("statusAfter", ""),
                    "paid_at": record.get("paidAt") or _now(),
                    "org_id": record["org_id"],
                    "user_id": record["user_id"],
                    "actor_id": record["actor_id"],
                    "sensitivity_ord": 2,
                    "owner_did": APP_DID,
                },
            )
            get_kotoba_client().insert_row(
                "edge_business_manager_invoice_payment",
                {
                    "edge_id": f"{invoice_vid}:PAID_BY:{vid}",
                    "src_vid": invoice_vid,
                    "dst_vid": vid,
                    "invoice_id": record["invoiceId"],
                    "payment_id": record["paymentId"],
                    "relation": "PAID_BY",
                    "created_at": record.get("paidAt") or _now(),
                    "owner_did": APP_DID,
                    "sensitivity_ord": 2,
                },
            )
            return {"uri": vid}
        if kind == "employee":
            vid = _vid(kind, record["employeeId"])
            get_kotoba_client().insert_row(
                "vertex_business_manager_employee",
                {
                    "vertex_id": vid,
                    "employee_id": record["employeeId"],
                    "full_name": record["fullName"],
                    "department": record["department"],
                    "role": record["role"],
                    "employment_type": record["employmentType"],
                    "start_date": record["startDate"],
                    "salary": _num(record["salary"]),
                    "probation_status": record["probationStatus"],
                    "probation_end_date": record["probationEndDate"],
                    "status": record.get("status", "active"),
                    "registered_at": record.get("registeredAt") or _now(),
                    "created_at": record.get("created_at") or _now(),
                    "org_id": record["org_id"],
                    "user_id": record["user_id"],
                    "actor_id": record["actor_id"],
                    "sensitivity_ord": 2,
                    "owner_did": APP_DID,
                },
            )
            return {"uri": vid}
        if kind == "purchaseOrder":
            vid = _vid(kind, record["poId"])
            items = record.get("items", "[]")
            if not isinstance(items, str):
                items = json.dumps(items, ensure_ascii=False)
            get_kotoba_client().insert_row(
                "vertex_business_manager_purchase_order",
                {
                    "vertex_id": vid,
                    "po_id": record["poId"],
                    "vendor": record.get("vendor", ""),
                    "items": items,
                    "total_amount": _num(record.get("totalAmount")),
                    "department": record.get("department", ""),
                    "justification": record.get("justification", ""),
                    "approval_level": record.get("approvalLevel", ""),
                    "status": record.get("status", ""),
                    "approver_comment": record.get("approverComment", ""),
                    "decided_at": record.get("decidedAt", ""),
                    "created_at": record.get("createdAt") or record.get("created_at") or _now(),
                    "org_id": record["org_id"],
                    "user_id": record["user_id"],
                    "actor_id": record["actor_id"],
                    "sensitivity_ord": 2,
                    "owner_did": APP_DID,
                },
            )
            return {"uri": vid}
        if kind == "budgetAllocation":
            vid = _vid(kind, record["allocationId"])
            get_kotoba_client().insert_row(
                "vertex_business_manager_budget_allocation",
                {
                    "vertex_id": vid,
                    "allocation_id": record["allocationId"],
                    "department": record["department"],
                    "fiscal_period": record["fiscalPeriod"],
                    "allocated_amount": _num(record["allocatedAmount"]),
                    "spent_amount": _num(record.get("spentAmount")),
                    "remaining_amount": _num(record.get("remainingAmount")),
                    "category": record.get("category", ""),
                    "status": record.get("status", "active"),
                    "allocated_at": record.get("allocatedAt") or _now(),
                    "created_at": record.get("created_at") or _now(),
                    "org_id": record["org_id"],
                    "user_id": record["user_id"],
                    "actor_id": record["actor_id"],
                    "sensitivity_ord": 2,
                    "owner_did": APP_DID,
                },
            )
            return {"uri": vid}
    raise ValueError(f"unknown business-manager kind: {kind}")


def _list(kind: str, *, limit: int = 100) -> list[dict[str, Any]]:
    tables = {
        "journalEntry": ("vertex_business_manager_journal_entry", "created_at"),
        "invoice": ("vertex_business_manager_invoice", "created_at"),
        "payment": ("vertex_business_manager_payment", "paid_at"),
        "employee": ("vertex_business_manager_employee", "created_at"),
        "purchaseOrder": ("vertex_business_manager_purchase_order", "created_at"),
        "budgetAllocation": ("vertex_business_manager_budget_allocation", "created_at"),
    }
    table, order_col = tables[kind]
    # R0: select_where does not support ORDER BY, so fetching all then sorting in Python.
    raw_rows = get_kotoba_client().select_where(table)
    sorted_rows = sorted(raw_rows, key=lambda x: x.get(order_col) or "", reverse=True)
    return _rows(sorted_rows[:limit])


def _find(kind: str, key: str, value: str) -> dict[str, Any] | None:
    tables = {
        "journalEntry": "vertex_business_manager_journal_entry",
        "invoice": "vertex_business_manager_invoice",
        "payment": "vertex_business_manager_payment",
        "employee": "vertex_business_manager_employee",
        "purchaseOrder": "vertex_business_manager_purchase_order",
        "budgetAllocation": "vertex_business_manager_budget_allocation",
    }
    table = tables[kind]
    # R0: using select_first_where for direct lookup.
    raw_row = get_kotoba_client().select_first_where(table, key, value)
    return _rows([raw_row])[0] if raw_row else None
    return None


def _parse_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    if isinstance(v, str) and v.startswith("["):
        try:
            parsed = json.loads(v)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return []


def task_business_manager_health(**_: Any) -> dict[str, Any]:
    return {"status": "healthy", "app": "Business Manager", "nanoid": APP_ID, "did": APP_DID, "now": _now()}


def task_business_manager_describe(**_: Any) -> dict[str, Any]:
    return {
        "name": "Business Manager",
        "did": APP_DID,
        "nanoid": APP_ID,
        "capabilities": [
            "health", "describe", "wave", "echo", "createJournalEntry", "createInvoice",
            "recordPayment", "registerEmployee", "createPurchaseOrder", "approvePurchaseOrder",
            "allocateBudget", "coverageStats",
        ],
        "protocols": ["xrpc", "w-protocol", "mcp"],
    }


def task_business_manager_wave(message: str = "hello", **_: Any) -> dict[str, Any]:
    return {"ok": True, "nanoid": APP_ID, "message": message or "hello"}


def task_business_manager_echo(**kwargs: Any) -> dict[str, Any]:
    return {"ok": True, "nanoid": APP_ID, "args": kwargs}


def task_business_manager_create_journal_entry(description: str = "", debitAccount: str = "", creditAccount: str = "", amount: Any = 0, currency: str = "JPY", fiscalPeriod: str = "", **_: Any) -> dict[str, Any]:
    amt = _num(amount)
    if not description or not debitAccount or not creditAccount:
        return {"ok": False, "error": "missing_params", "detail": "description, debitAccount, creditAccount required"}
    if amt <= 0:
        return {"ok": False, "error": "invalid_amount", "detail": "Journal entry amount must be positive"}
    if debitAccount == creditAccount:
        return {"ok": False, "error": "same_account", "detail": "Debit and credit accounts must be different"}
    approval = "pending_approval" if amt >= JOURNAL_APPROVAL_THRESHOLD else "auto_approved"
    entry_id = _id("je")
    _write("journalEntry", {"entryId": entry_id, "description": description, "debitAccount": debitAccount, "creditAccount": creditAccount, "amount": amt, "currency": currency or "JPY", "fiscalPeriod": fiscalPeriod, "approvalStatus": approval, "postedAt": _now(), "created_at": _now()})
    return {"ok": True, "entryId": entry_id, "amount": amt, "currency": currency or "JPY", "approvalStatus": approval}


def task_business_manager_create_invoice(counterparty: str = "", direction: str = "payable", amount: Any = 0, currency: str = "JPY", lineItems: Any = None, paymentTermsDays: Any = DEFAULT_PAYMENT_TERMS_DAYS, **_: Any) -> dict[str, Any]:
    amt = _num(amount)
    terms = int(_num(paymentTermsDays, DEFAULT_PAYMENT_TERMS_DAYS))
    items = _parse_list(lineItems)
    if not counterparty or amt <= 0:
        return {"ok": False, "error": "missing_params", "detail": "counterparty and positive amount required"}
    if items:
        total = sum(_num((li or {}).get("amount")) for li in items if isinstance(li, dict))
        if abs(total - amt) > 0.01:
            return {"ok": False, "error": "amount_mismatch", "detail": f"Line items total ({total}) does not match invoice amount ({amt})"}
    if terms < 0 or terms > 365:
        return {"ok": False, "error": "invalid_terms", "detail": "Payment terms must be between 0 and 365 days"}
    due = (_dt.datetime.now(tz=_dt.UTC) + _dt.timedelta(days=terms)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    invoice_id = _id("inv")
    _write("invoice", {"invoiceId": invoice_id, "counterparty": counterparty, "direction": direction or "payable", "amount": amt, "currency": currency or "JPY", "lineItems": json.dumps(items, ensure_ascii=False), "paymentTermsDays": terms, "dueDate": due, "status": "open", "issuedAt": _now(), "created_at": _now()})
    return {"ok": True, "invoiceId": invoice_id, "direction": direction or "payable", "amount": amt, "currency": currency or "JPY", "dueDate": due}


def task_business_manager_record_payment(invoiceId: str = "", amount: Any = 0, method: str = "bankTransfer", **_: Any) -> dict[str, Any]:
    payment_amount = _num(amount)
    if not invoiceId or payment_amount <= 0:
        return {"ok": False, "error": "missing_params", "detail": "invoiceId and positive amount required"}
    invoice = _find("invoice", "invoiceId", invoiceId)
    if not invoice:
        return {"ok": False, "error": "invoice_not_found", "detail": f"Invoice {invoiceId} not found"}
    if _str(invoice.get("status")) == "paid":
        return {"ok": False, "error": "already_paid", "detail": "Invoice is already fully paid"}
    invoice_amount = _num(invoice.get("amount"))
    new_status = "partial" if payment_amount < invoice_amount else "paid" if payment_amount == invoice_amount else "overpaid"
    payment_id = _id("pay")
    _write("invoice", {**invoice, "invoiceId": invoiceId, "status": new_status})
    _write("payment", {"paymentId": payment_id, "invoiceId": invoiceId, "amount": payment_amount, "method": method or "bankTransfer", "statusAfter": new_status, "paidAt": _now(), "created_at": _now()})
    return {"ok": True, "paymentId": payment_id, "invoiceId": invoiceId, "paymentAmount": payment_amount, "newStatus": new_status}


def task_business_manager_register_employee(fullName: str = "", department: str = "", role: str = "", employmentType: str = "fullTime", startDate: str = "", salary: Any = 0, **_: Any) -> dict[str, Any]:
    if not fullName or not department or not role:
        return {"ok": False, "error": "missing_params", "detail": "fullName, department, role required"}
    sal = _num(salary)
    if employmentType == "fullTime" and sal <= 0:
        return {"ok": False, "error": "invalid_salary", "detail": "Full-time employees must have a positive salary"}
    probation = "on_probation" if employmentType in ("fullTime", "partTime") else "confirmed" if employmentType == "contract" else "not_applicable"
    start = startDate or _now()
    try:
        end = (_dt.datetime.fromisoformat(start.replace("Z", "+00:00")) + _dt.timedelta(days=PROBATION_MONTHS * 30)).replace(microsecond=0).isoformat().replace("+00:00", "Z") if probation == "on_probation" else ""
    except ValueError:
        end = ""
    emp_id = _id("emp")
    _write("employee", {"employeeId": emp_id, "fullName": fullName, "department": department, "role": role, "employmentType": employmentType or "fullTime", "startDate": start, "salary": sal, "probationStatus": probation, "probationEndDate": end, "status": "active", "registeredAt": _now(), "created_at": _now()})
    return {"ok": True, "employeeId": emp_id, "fullName": fullName, "department": department, "probationStatus": probation, "probationEndDate": end}


def task_business_manager_create_purchase_order(vendor: str = "", items: Any = None, department: str = "", justification: str = "", **_: Any) -> dict[str, Any]:
    parsed = _parse_list(items)
    if not vendor or not parsed or not department:
        return {"ok": False, "error": "missing_params", "detail": "vendor, items, department required"}
    total = sum(_num((it or {}).get("quantity")) * _num((it or {}).get("unitPrice")) for it in parsed if isinstance(it, dict))
    if total <= 0:
        return {"ok": False, "error": "invalid_amount", "detail": "Purchase order total must be positive"}
    level = "auto" if total < JOURNAL_APPROVAL_THRESHOLD else "manager" if total < PO_EXECUTIVE_APPROVAL_THRESHOLD else "executive"
    if level == "executive" and not justification:
        return {"ok": False, "error": "justification_required", "detail": "Purchase orders over threshold require justification"}
    po_id = _id("po")
    status = "approved" if level == "auto" else "pending"
    _write("purchaseOrder", {"poId": po_id, "vendor": vendor, "items": json.dumps(parsed, ensure_ascii=False), "totalAmount": total, "department": department, "justification": justification, "approvalLevel": level, "status": status, "createdAt": _now(), "created_at": _now()})
    return {"ok": True, "poId": po_id, "vendor": vendor, "totalAmount": total, "approvalLevel": level, "status": status}


def task_business_manager_approve_purchase_order(poId: str = "", decision: str = "approve", comment: str = "", **_: Any) -> dict[str, Any]:
    if not poId:
        return {"ok": False, "error": "missing_params", "detail": "poId required"}
    order = _find("purchaseOrder", "poId", poId)
    if not order:
        return {"ok": False, "error": "po_not_found"}
    if _str(order.get("status")) != "pending":
        return {"ok": False, "error": "not_pending", "detail": f"PO is {order.get('status')}, not pending"}
    new_status = "approved" if decision == "approve" else "rejected"
    _write("purchaseOrder", {**order, "poId": poId, "status": new_status, "approverComment": comment, "decidedAt": _now()})
    return {"ok": True, "poId": poId, "decision": new_status}


def task_business_manager_allocate_budget(department: str = "", fiscalPeriod: str = "", allocatedAmount: Any = 0, category: str = "operating", **_: Any) -> dict[str, Any]:
    amt = _num(allocatedAmount)
    if not department or not fiscalPeriod:
        return {"ok": False, "error": "missing_params", "detail": "department and fiscalPeriod required"}
    if amt <= 0:
        return {"ok": False, "error": "invalid_amount", "detail": "Budget allocation must be positive"}
    if category == "capital" and amt < 100_000:
        return {"ok": False, "error": "capital_minimum", "detail": "Capital budget allocation must be at least JPY 100,000"}
    allocation_id = _id("bgt")
    _write("budgetAllocation", {"allocationId": allocation_id, "department": department, "fiscalPeriod": fiscalPeriod, "allocatedAmount": amt, "spentAmount": 0, "remainingAmount": amt, "category": category or "operating", "status": "active", "allocatedAt": _now(), "created_at": _now()})
    return {"ok": True, "allocationId": allocation_id, "department": department, "fiscalPeriod": fiscalPeriod, "allocatedAmount": amt, "category": category or "operating"}


def task_business_manager_coverage_stats(**_: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "journalEntries": len(_list("journalEntry", limit=500)),
        "invoices": len(_list("invoice", limit=500)),
        "activeEmployees": len([r for r in _list("employee", limit=500) if r.get("status") == "active"]),
        "purchaseOrders": len(_list("purchaseOrder", limit=500)),
        "activeBudgets": len([r for r in _list("budgetAllocation", limit=500) if r.get("status") == "active"]),
    }


def register(worker: Any, *, timeout_ms: int = 60_000) -> None:
    tasks = {
        "xrpc.com.etzhayyim.apps.businessManager.allocateBudget": task_business_manager_allocate_budget,
        "xrpc.com.etzhayyim.apps.businessManager.approvePurchaseOrder": task_business_manager_approve_purchase_order,
        "xrpc.com.etzhayyim.apps.businessManager.coverageStats": task_business_manager_coverage_stats,
        "xrpc.com.etzhayyim.apps.businessManager.createInvoice": task_business_manager_create_invoice,
        "xrpc.com.etzhayyim.apps.businessManager.createJournalEntry": task_business_manager_create_journal_entry,
        "xrpc.com.etzhayyim.apps.businessManager.createPurchaseOrder": task_business_manager_create_purchase_order,
        "xrpc.com.etzhayyim.apps.businessManager.describe": task_business_manager_describe,
        "xrpc.com.etzhayyim.apps.businessManager.echo": task_business_manager_echo,
        "xrpc.com.etzhayyim.apps.businessManager.health": task_business_manager_health,
        "xrpc.com.etzhayyim.apps.businessManager.recordPayment": task_business_manager_record_payment,
        "xrpc.com.etzhayyim.apps.businessManager.registerEmployee": task_business_manager_register_employee,
        "xrpc.com.etzhayyim.apps.businessManager.wave": task_business_manager_wave,
    }
    for task_type, handler in tasks.items():
        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(handler)
