"""Kaikei accounting handlers for BPMN + Zeebe."""

from __future__ import annotations

import time
from typing import Any

from pymagatama.db_sync import sync_cursor

NS = "com.etzhayyim.apps.kaikei"
ACTOR = "did:web:kaikei.etzhayyim.com"

OWNER_MAP = {
    "works": "did:plc:etzhayyim-works",
    "japan": "did:plc:etzhayyim-japan",
    "labo": "did:plc:etzhayyim-labo",
}

SENTINEL = {
    "pfExpense": "did:web:kaikei.etzhayyim.com:account:in-pf-expense",
    "pfPayable": "did:web:kaikei.etzhayyim.com:account:in-pf-payable-epfo",
    "esiExpense": "did:web:kaikei.etzhayyim.com:account:in-esi-expense",
    "esiPayable": "did:web:kaikei.etzhayyim.com:account:in-esi-payable-esic",
    "gstReceivable": "did:web:kaikei.etzhayyim.com:account:in-gst-itc-receivable",
    "gstPayable": "did:web:kaikei.etzhayyim.com:account:in-gst-net-payable",
    "taxExpense": "did:web:kaikei.etzhayyim.com:account:in-income-tax-expense",
    "taxPayable": "did:web:kaikei.etzhayyim.com:account:in-income-tax-payable",
    "whExpense": "did:web:kaikei.etzhayyim.com:account:jp-withholding-expense",
    "whPayable": "did:web:kaikei.etzhayyim.com:account:jp-withholding-payable",
}


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _str(value: Any) -> str:
    return "" if value is None else str(value)


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _limit(value: Any, default: int, max_value: int) -> int:
    return max(1, min(_int(value, default), max_value))


def resolve_owner(value: Any) -> str:
    text = _str(value)
    if text.startswith("did:"):
        return text
    return OWNER_MAP.get(text, "")


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


def _next_seq(table: str) -> int:
    with sync_cursor() as cur:
        cur.execute(f"SELECT COALESCE(MAX(_seq), 0) + 1 AS seq FROM {table}")
        row = cur.fetchone()
        return int(row[0] if row else 1)


def _rkey(text: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(part for part in out.split("-") if part) or "account"


def _resolve_account_did(owner_did: str, account_did: str) -> str:
    if not account_did.startswith("did:web:kaikei.etzhayyim.com:account:"):
        return account_did
    row = _fetch_one(
        """SELECT vertex_id FROM vertex_atrecord_kaikei_account
        WHERE owner_did=%s AND parent_account_did=%s AND is_archived=false
        ORDER BY _seq DESC LIMIT 1""",
        (owner_did, account_did),
    )
    return _str(row.get("vertex_id")) if row else account_did


def get_trial_balance(periodYm: str = "", owner: str = "", accountType: str = "", **_: Any) -> dict[str, Any]:
    owner_did = resolve_owner(owner) or OWNER_MAP["works"]
    if not periodYm:
        return {"error": "periodYm required"}
    args: list[Any] = [owner_did, periodYm]
    filters = ["tb.owner_did=%s", "tb.period_ym=%s"]
    if accountType:
        args.append(accountType)
        filters.append("a.account_type=%s")
    rows = _fetch_all(
        f"""SELECT tb.account_did, a.account_name, a.account_type, tb.side,
        tb.total_amount, tb.entry_count
        FROM mv_kaikei_trial_balance tb
        LEFT JOIN vertex_atrecord_kaikei_account a
          ON a.owner_did=tb.owner_did
         AND a.vertex_id=tb.owner_did || '|com.etzhayyim.apps.kaikei.account|' || SPLIT_PART(tb.account_did, ':', 5)
        WHERE {' AND '.join(filters)}
        ORDER BY a.account_type, a.account_name, tb.side""",
        tuple(args),
    )
    debit = sum(float(r.get("total_amount") or 0) for r in rows if r.get("side") == "debit")
    credit = sum(float(r.get("total_amount") or 0) for r in rows if r.get("side") == "credit")
    return {"periodYm": periodYm, "owner": owner_did, "rows": rows, "debitTotal": debit, "creditTotal": credit, "balanced": abs(debit - credit) < 1}


def list_journal_entries(owner: str = "", periodYm: str = "", accountDid: str = "", sourceType: str = "", limit: Any = 100, cursor: Any = None, **_: Any) -> dict[str, Any]:
    owner_did = resolve_owner(owner)
    if not owner_did:
        return {"error": "owner required"}
    args: list[Any] = [owner_did]
    filters = ["owner_did=%s"]
    if periodYm:
        args.append(periodYm); filters.append("period_ym=%s")
    if sourceType:
        args.append(sourceType); filters.append("source_type=%s")
    if accountDid:
        args.append(accountDid); filters.append("(debit_account_did=%s OR credit_account_did=%s)")
        args.append(accountDid)
    if cursor not in (None, ""):
        args.append(_int(cursor)); filters.append("_seq < %s")
    n = _limit(limit, 100, 500)
    rows = _fetch_all(
        f"""SELECT vertex_id, rkey, period_ym, posted_at, debit_account_did, credit_account_did,
        amount AS debit_amount, amount AS credit_amount, amount, currency, tax_code, memo, source_type,
        source_did AS transaction_id, source_did, NULL::integer AS line_no, _seq AS cursor
        FROM vertex_atrecord_kaikei_journal_entry
        WHERE {' AND '.join(filters)}
        ORDER BY _seq DESC LIMIT %s""",
        tuple(args + [n]),
    )
    return {"entries": rows, "cursor": rows[-1]["cursor"] if len(rows) == n else None}


def list_accounts(owner: str = "", accountType: str = "", includeArchived: Any = False, limit: Any = 100, cursor: Any = None, **_: Any) -> dict[str, Any]:
    owner_did = resolve_owner(owner)
    if not owner_did:
        return {"error": "owner required"}
    args: list[Any] = [owner_did]
    filters = ["owner_did=%s"]
    if accountType:
        args.append(accountType); filters.append("account_type=%s")
    if not (includeArchived is True or _str(includeArchived).lower() == "true"):
        filters.append("is_archived=false")
    if cursor not in (None, ""):
        args.append(_int(cursor)); filters.append("_seq > %s")
    n = _limit(limit, 100, 500)
    rows = _fetch_all(
        f"""SELECT vertex_id, rkey, account_code, account_name, account_type,
        parent_account_did, tax_code, is_archived, _seq AS cursor
        FROM vertex_atrecord_kaikei_account
        WHERE {' AND '.join(filters)}
        ORDER BY _seq ASC LIMIT %s""",
        tuple(args + [n]),
    )
    return {"accounts": rows, "cursor": rows[-1]["cursor"] if len(rows) == n else None}


def get_monthly_summary(owner: str = "", periodYm: str = "", fromYm: str = "", toYm: str = "", **_: Any) -> dict[str, Any]:
    owner_did = resolve_owner(owner)
    if not owner_did:
        return {"error": "owner required"}
    args: list[Any] = [owner_did]
    filters = ["owner_did=%s"]
    if periodYm:
        args.append(periodYm); filters.append("period_ym=%s")
    if fromYm:
        args.append(fromYm); filters.append("period_ym >= %s")
    if toYm:
        args.append(toYm); filters.append("period_ym <= %s")
    rows = _fetch_all(
        f"""SELECT owner_did, period_ym, account_type,
        SUM(flow_amount)::DOUBLE PRECISION AS flow_amount,
        SUM(bs_delta)::DOUBLE PRECISION AS bs_delta,
        SUM(entry_count)::BIGINT AS entry_count
        FROM view_kaikei_monthly_summary
        WHERE {' AND '.join(filters)}
        GROUP BY owner_did, period_ym, account_type
        ORDER BY period_ym, account_type""",
        tuple(args),
    )
    pl: dict[str, dict[str, float]] = {}
    bs: dict[str, dict[str, float]] = {}
    for row in rows:
        ym = _str(row.get("period_ym"))
        typ = _str(row.get("account_type"))
        if row.get("flow_amount") is not None:
            bucket = pl.setdefault(ym, {"revenue": 0, "expense": 0, "net": 0})
            if typ == "revenue":
                bucket["revenue"] = float(row.get("flow_amount") or 0)
            if typ == "expense":
                bucket["expense"] = float(row.get("flow_amount") or 0)
            bucket["net"] = bucket["revenue"] - bucket["expense"]
        if row.get("bs_delta") is not None:
            bs.setdefault(ym, {})[typ] = float(row.get("bs_delta") or 0)
    return {"owner": owner_did, "periodYm": periodYm or None, "fromYm": fromYm or None, "toYm": toYm or None, "pl": pl, "bs": bs, "rows": rows}


def _post_one_entry(owner_did: str, rkey: str, period_ym: str, debit_account_did: str, credit_account_did: str, amount_inr_paise: Any, currency: str, memo: str, source_type: str, source_did: str = "") -> dict[str, Any]:
    amount = max(0, round(_int(amount_inr_paise) / 100))
    debit = _resolve_account_did(owner_did, debit_account_did)
    credit = _resolve_account_did(owner_did, credit_account_did)
    vertex_id = f"{owner_did}|{NS}.journalEntry|{rkey}"
    now = now_iso()
    _execute(
        """INSERT INTO vertex_atrecord_kaikei_journal_entry
        (vertex_id, _seq, owner_did, rkey, period_ym, posted_at, debit_account_did,
         credit_account_did, amount, currency, memo, source_type, source_did, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (vertex_id) DO NOTHING""",
        (vertex_id, _next_seq("vertex_atrecord_kaikei_journal_entry"), owner_did, rkey, period_ym, now, debit, credit, amount, currency, memo, source_type, source_did or None, now),
    )
    return {"vertexId": vertex_id, "amount": amount, "debitAccountDid": debit, "creditAccountDid": credit}


def record_pf_payable(employerOrgId: str = "", wageMonth: str = "", totalEmployerPfInrPaise: Any = 0, totalEmployeePfInrPaise: Any = 0, totalAdminInrPaise: Any = 0, establishmentPfCode: str = "", trrn: str = "", triggerSource: str = "", triggerVertexId: str = "", **_: Any) -> dict[str, Any]:
    owner = resolve_owner(employerOrgId)
    if not owner or not wageMonth:
        return {"error": "employerOrgId and wageMonth required"}
    total = _int(totalEmployerPfInrPaise) + _int(totalEmployeePfInrPaise) + _int(totalAdminInrPaise)
    r = _post_one_entry(owner, f"pf-{wageMonth}-{int(time.time() * 1000)}", wageMonth, SENTINEL["pfExpense"], SENTINEL["pfPayable"], total, "INR", f"EPFO PF payable ({establishmentPfCode} {trrn})", triggerSource or "com.etzhayyim.apps.epfo.finalize", triggerVertexId)
    return {"ok": True, "vertexId": r["vertexId"], "totalAmountInrPaise": r["amount"] * 100}


def record_esi_payable(employerOrgId: str = "", wageMonth: str = "", totalEmployerContributionInrPaise: Any = 0, totalEmployeeContributionInrPaise: Any = 0, establishmentEsiCode: str = "", challanReference: str = "", triggerSource: str = "", triggerVertexId: str = "", **_: Any) -> dict[str, Any]:
    owner = resolve_owner(employerOrgId)
    if not owner or not wageMonth:
        return {"error": "employerOrgId and wageMonth required"}
    total = _int(totalEmployerContributionInrPaise) + _int(totalEmployeeContributionInrPaise)
    r = _post_one_entry(owner, f"esi-{wageMonth}-{int(time.time() * 1000)}", wageMonth, SENTINEL["esiExpense"], SENTINEL["esiPayable"], total, "INR", f"ESIC contribution ({establishmentEsiCode} {challanReference})", triggerSource or "com.etzhayyim.apps.esic.finalize", triggerVertexId)
    return {"ok": True, "vertexId": r["vertexId"], "totalAmountInrPaise": r["amount"] * 100}


def record_gst_payable(gstinHash: str = "", taxPeriod: str = "", totalNetTaxInrPaise: Any = 0, deltaTaxInrPaise: Any = 0, arn: str = "", amendmentReason: str = "", triggerSource: str = "", triggerVertexId: str = "", **_: Any) -> dict[str, Any]:
    if not taxPeriod:
        return {"error": "taxPeriod required"}
    owner = resolve_owner(gstinHash) or f"did:web:kaikei.etzhayyim.com:taxpayer:{_str(gstinHash or 'unknown')[:16]}"
    total = _int(totalNetTaxInrPaise) or _int(deltaTaxInrPaise)
    memo = f"GSTR-3B net tax (ARN {arn or '-'}{('/ amend:' + amendmentReason) if amendmentReason else ''})"
    r = _post_one_entry(owner, f"gst-{taxPeriod}-{int(time.time() * 1000)}", taxPeriod, SENTINEL["gstReceivable"], SENTINEL["gstPayable"], total, "INR", memo, triggerSource or "com.etzhayyim.apps.gstr3b.fileReturn", triggerVertexId)
    return {"ok": True, "vertexId": r["vertexId"], "totalAmountInrPaise": r["amount"] * 100}


def record_advance_tax(taxpayerPanHash: str = "", assessmentYear: str = "", totalTaxPaidInrPaise: Any = 0, advanceTaxPaidInrPaise: Any = 0, selfAssessmentTaxInrPaise: Any = 0, ackNumber: str = "", triggerSource: str = "", triggerVertexId: str = "", **_: Any) -> dict[str, Any]:
    if not assessmentYear:
        return {"error": "assessmentYear required"}
    owner = f"did:web:kaikei.etzhayyim.com:taxpayer:{_str(taxpayerPanHash or 'unknown')[:16]}"
    total = _int(totalTaxPaidInrPaise) or _int(advanceTaxPaidInrPaise) or _int(selfAssessmentTaxInrPaise)
    r = _post_one_entry(owner, f"itr1-{assessmentYear}-{int(time.time() * 1000)}", assessmentYear, SENTINEL["taxExpense"], SENTINEL["taxPayable"], total, "INR", f"ITR-1 advance/self-assessment tax (ack {ackNumber or '-'})", triggerSource or "com.etzhayyim.apps.itr1.fileReturn", triggerVertexId)
    return {"ok": True, "vertexId": r["vertexId"], "totalAmountInrPaise": r["amount"] * 100}


def recompute_withholding(employerOrgId: str = "", effectiveFromMonth: str = "", taxYear: str = "", employeeDid: str = "", amendmentReason: str = "", triggerSource: str = "", triggerVertexId: str = "", **_: Any) -> dict[str, Any]:
    owner = resolve_owner(employerOrgId)
    if not owner or not effectiveFromMonth:
        return {"error": "employerOrgId and effectiveFromMonth required"}
    memo = f"fuyou recompute marker (employee {employeeDid}{('/ ' + amendmentReason) if amendmentReason else ''})"
    r = _post_one_entry(owner, f"fuyou-recompute-{taxYear or 'na'}-{effectiveFromMonth}-{int(time.time() * 1000)}", effectiveFromMonth, SENTINEL["whExpense"], SENTINEL["whPayable"], 0, "JPY", memo, triggerSource or "com.etzhayyim.apps.fuyou.finalize", triggerVertexId)
    return {"ok": True, "vertexId": r["vertexId"], "monthsAffected": 0}


def map_account(ownerOrgId: str = "", sentinelDid: str = "", customerAccountCode: str = "", customerAccountName: str = "", customerAccountType: str = "", **_: Any) -> dict[str, Any]:
    owner = resolve_owner(ownerOrgId)
    if not owner:
        return {"error": "ownerOrgId required"}
    if not sentinelDid.startswith("did:web:kaikei.etzhayyim.com:account:"):
        return {"error": "sentinelDid must be a kaikei sentinel account DID"}
    if not customerAccountCode or not customerAccountName or not customerAccountType:
        return {"error": "customerAccountCode, customerAccountName, customerAccountType required"}
    rkey = _rkey(customerAccountCode)
    vertex_id = f"{owner}|{NS}.account|{rkey}"
    inserted = _execute(
        """INSERT INTO vertex_atrecord_kaikei_account
        (vertex_id, _seq, owner_did, rkey, account_code, account_name, account_type,
         parent_account_did, tax_code, is_archived, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,false,%s)
        ON CONFLICT (vertex_id) DO NOTHING""",
        (vertex_id, _next_seq("vertex_atrecord_kaikei_account"), owner, rkey, customerAccountCode, customerAccountName, customerAccountType, sentinelDid, sentinelDid, now_iso()),
    )
    return {"ok": True, "ownerDid": owner, "sentinelDid": sentinelDid, "customerAccountVertexId": vertex_id, "customerAccountCode": customerAccountCode, "inserted": inserted > 0, "alreadyMapped": inserted == 0}
