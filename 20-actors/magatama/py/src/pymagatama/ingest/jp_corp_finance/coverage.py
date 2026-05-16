from __future__ import annotations

from typing import Any

from pymagatama.db_sync import fetch_all


def _text(value: Any) -> str:
    return "" if value is None else str(value)


def _int(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _coverage_item(row: tuple[Any, ...]) -> dict[str, str]:
    return {
        "jcn": _text(row[0]),
        "companyName": _text(row[1]),
        "disclosureMethod": _text(row[2]),
        "latestPeriodEnd": _text(row[3]),
        "latestDisclosureVid": _text(row[4]),
        "coverageStatus": _text(row[5]),
        "missingReason": _text(row[6]),
        "checkedAt": _text(row[7]),
    }


def get_coverage(*, jcn: str = "", edinet_code: str = "") -> dict[str, Any]:
    """Return latest coverage for one company by JCN or EDINET code."""
    jcn = jcn.strip()
    edinet_code = edinet_code.strip()
    if not jcn and not edinet_code:
        return {"ok": False, "error": "jcn or edinetCode required"}
    if jcn:
        rows = fetch_all(
            """
            SELECT jcn, company_name, disclosure_method, latest_period_end,
                   latest_disclosure_vid, coverage_status, missing_reason, checked_at
              FROM vertex_jp_corp_finance_coverage
             WHERE jcn = %s
             ORDER BY checked_at DESC
             LIMIT 1
            """,
            (jcn,),
        )
    else:
        rows = fetch_all(
            """
            SELECT c.jcn, c.company_name, c.disclosure_method, c.latest_period_end,
                   c.latest_disclosure_vid, c.coverage_status, c.missing_reason, c.checked_at
              FROM vertex_jp_corp_finance_coverage c
              JOIN vertex_jp_corp_disclosure d
                ON d.vertex_id = c.latest_disclosure_vid
             WHERE d.edinet_code = %s
             ORDER BY c.checked_at DESC
             LIMIT 1
            """,
            (edinet_code,),
        )
    if not rows:
        return {
            "ok": True,
            "found": False,
            "jcn": jcn,
            "edinetCode": edinet_code,
            "coverageStatus": "missing",
            "missingReason": "coverage_not_found",
        }
    return {"ok": True, "found": True, **_coverage_item(rows[0])}


def list_missing(
    *,
    coverage_status: str = "missing",
    missing_reason: str = "",
    limit: int = 100,
    cursor: str = "",
) -> dict[str, Any]:
    """List missing/stale/source_unknown/failed coverage rows, ordered by JCN."""
    allowed_statuses = {"missing", "stale", "source_unknown", "failed"}
    status = (coverage_status or "missing").strip()
    if status not in allowed_statuses:
        return {"ok": False, "items": [], "error": f"unsupported coverageStatus: {status}"}
    bounded_limit = max(1, min(_int(limit, 100), 500))
    where = ["coverage_status = %s"]
    params: list[Any] = [status]
    if missing_reason:
        where.append("missing_reason = %s")
        params.append(missing_reason)
    if cursor:
        where.append("jcn > %s")
        params.append(cursor)
    params.append(bounded_limit + 1)
    rows = fetch_all(
        f"""
        SELECT jcn, company_name, disclosure_method, latest_period_end,
               latest_disclosure_vid, coverage_status, missing_reason, checked_at
          FROM vertex_jp_corp_finance_coverage
         WHERE {' AND '.join(where)}
         ORDER BY jcn ASC
         LIMIT %s
        """,
        tuple(params),
    )
    page = rows[:bounded_limit]
    next_cursor = _text(page[-1][0]) if len(rows) > bounded_limit and page else ""
    return {
        "ok": True,
        "items": [_coverage_item(row) for row in page],
        "cursor": next_cursor,
    }
