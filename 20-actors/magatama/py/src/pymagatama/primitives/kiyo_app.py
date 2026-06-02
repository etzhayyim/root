"""Kiyo AppView read/write XRPC primitives for BPMN/LangServer."""

from __future__ import annotations

import datetime as _dt
import decimal as _decimal
import time
from typing import Any

from pymagatama.db_sync import sync_cursor


KIYO_DID = "did:web:kiyo.etzhayyim.com"
PAPER_COLLECTION = "com.etzhayyim.apps.kiyo.paper"


def _now() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _jsonable(v: Any) -> Any:
    if isinstance(v, (_dt.datetime, _dt.date)):
        return v.isoformat()
    if isinstance(v, _decimal.Decimal):
        f = float(v)
        return int(f) if f.is_integer() else f
    return v


def _rows(cur: Any) -> list[dict[str, Any]]:
    cols = [d[0] for d in (cur.description or [])]
    return [{cols[i]: _jsonable(row[i]) for i in range(len(cols))} for row in cur.fetchall()]


def _bounded_int(v: Any, default: int, *, min_value: int, max_value: int) -> int:
    try:
        n = int(v)
    except (TypeError, ValueError):
        n = default
    return max(min_value, min(max_value, n))


def _paper_vid(paper_id: str) -> str:
    return f"at://{KIYO_DID}/{PAPER_COLLECTION}/{paper_id}"


def task_kiyo_withdraw_paper(paperId: str = "", **_: Any) -> dict[str, Any]:
    if not paperId:
        return {"error": "paperId required"}
    with sync_cursor() as cur:
        cur.execute("UPDATE vertex_kiyo_paper SET status = %s WHERE paper_id = %s", ("withdrawn", paperId))
    return {"withdrawn": True}


def task_kiyo_add_review(
    paperId: str = "", rating: Any = None, body: str = "", reviewType: str = "comment", callerDid: str = "", **_: Any
) -> dict[str, Any]:
    if not paperId or not body:
        return {"error": "paperId and body required"}
    now = _now()
    reviewer = callerDid or KIYO_DID
    review_id = f"at://{KIYO_DID}/com.etzhayyim.apps.kiyo.review/{int(time.time() * 1000):x}"
    rating_v: int | None
    try:
        rating_v = int(rating) if rating is not None else None
    except (TypeError, ValueError):
        rating_v = None
    with sync_cursor() as cur:
        cur.execute(
            "INSERT INTO vertex_kiyo_review "
            "(vertex_id,paper_id,reviewer_did,rating,body,review_type,owner_did,actor_did,org_did,created_at,sensitivity_ord) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (review_id, paperId, reviewer, rating_v, body, reviewType or "comment", reviewer, reviewer, "anon", now, 0),
        )
    return {"reviewId": review_id, "accepted": True}


def task_kiyo_endorse_paper(paperId: str = "", callerDid: str = "", **_: Any) -> dict[str, Any]:
    if not paperId:
        return {"error": "paperId required"}
    caller = callerDid or KIYO_DID
    paper_vid = _paper_vid(paperId)
    edge_id = f"edge:kiyo:endorses:{caller}:{paperId}"
    with sync_cursor() as cur:
        cur.execute(
            "INSERT INTO edge_kiyo_endorses (edge_id,src_vid,dst_vid,created_at) VALUES (%s,%s,%s,%s)",
            (edge_id, caller, paper_vid, _now()),
        )
        cur.execute("SELECT endorsement_count FROM mv_kiyo_paper_stats WHERE paper_id = %s LIMIT 1", (paperId,))
        stats = _rows(cur)
    return {"endorsed": True, "totalEndorsements": int((stats[0] if stats else {}).get("endorsement_count") or 0)}


def task_kiyo_get_paper(paperId: str = "", **_: Any) -> dict[str, Any]:
    with sync_cursor() as cur:
        cur.execute("SELECT * FROM vertex_kiyo_paper WHERE paper_id = %s LIMIT 1", (paperId,))
        papers = _rows(cur)
        if not papers:
            return {"error": "not found"}
        cur.execute("SELECT * FROM mv_kiyo_paper_stats WHERE paper_id = %s LIMIT 1", (paperId,))
        stats = _rows(cur)
        cur.execute(
            "SELECT dst_vid, role FROM edge_kiyo_authored_by WHERE src_vid = %s ORDER BY order_num ASC",
            (_paper_vid(paperId),),
        )
        authors = _rows(cur)
    p = papers[0]
    s = stats[0] if stats else {}
    return {
        "paperId": p.get("paper_id"),
        "title": p.get("title"),
        "abstract": p.get("abstract"),
        "subject": p.get("subject"),
        "authors": [a.get("dst_vid") for a in authors],
        "authorType": p.get("author_type"),
        "status": p.get("status"),
        "ipfsCid": p.get("ipfs_cid"),
        "latestVersion": p.get("latest_version"),
        "submittedAt": p.get("submitted_at"),
        "citationCount": int(s.get("citation_in_count") or 0),
        "reviewCount": int(s.get("review_count") or 0),
        "endorsements": int(s.get("endorsement_count") or 0),
    }


def task_kiyo_list_papers(subject: str = "", authorType: str = "", since: str = "", limit: Any = 50, offset: Any = 0, **_: Any) -> dict[str, Any]:
    limit_n = _bounded_int(limit, 50, min_value=1, max_value=100)
    offset_n = _bounded_int(offset, 0, min_value=0, max_value=100_000)
    clauses = ["status = %s"]
    params: list[Any] = ["active"]
    if subject:
        clauses.append("subject @> ARRAY[%s]::VARCHAR[]")
        params.append(subject)
    if authorType:
        clauses.append("author_type = %s")
        params.append(authorType)
    if since:
        clauses.append("submitted_at >= %s")
        params.append(since)
    with sync_cursor() as cur:
        cur.execute(
            "SELECT paper_id,title,subject,author_type,submitted_at,ipfs_cid FROM vertex_kiyo_paper "
            f"WHERE {' AND '.join(clauses)} ORDER BY submitted_at DESC LIMIT {limit_n} OFFSET {offset_n}",
            tuple(params),
        )
        papers = _rows(cur)
    return {"papers": papers, "offset": offset_n, "limit": limit_n}


def task_kiyo_search_papers(q: str = "", subject: str = "", limit: Any = 20, offset: Any = 0, **_: Any) -> dict[str, Any]:
    limit_n = _bounded_int(limit, 20, min_value=1, max_value=50)
    offset_n = _bounded_int(offset, 0, min_value=0, max_value=100_000)
    clauses = ["status = %s"]
    params: list[Any] = ["active"]
    if subject:
        clauses.append("subject @> ARRAY[%s]::VARCHAR[]")
        params.append(subject)
    if q:
        clauses.append("(title ILIKE %s OR abstract ILIKE %s)")
        params.extend([f"%{q}%", f"%{q}%"])
    with sync_cursor() as cur:
        cur.execute(
            "SELECT paper_id,title,abstract,ipfs_cid,1.0 AS score FROM vertex_kiyo_paper "
            f"WHERE {' AND '.join(clauses)} ORDER BY submitted_at DESC LIMIT {limit_n} OFFSET {offset_n}",
            tuple(params),
        )
        papers = _rows(cur)
    return {"papers": papers, "offset": offset_n, "limit": limit_n}


def task_kiyo_get_paper_file(paperId: str = "", version: Any = None, fileType: str = "pdf", ipfsGatewayUrl: str = "https://ipfs.etzhayyim.com", **_: Any) -> dict[str, Any]:
    version_n = _bounded_int(version, 0, min_value=0, max_value=10_000) if version not in (None, "") else 0
    cid = ""
    with sync_cursor() as cur:
        if version_n > 0:
            cur.execute(
                "SELECT ipfs_cid, source_ipfs_cid FROM vertex_kiyo_revision WHERE paper_id = %s AND version = %s LIMIT 1",
                (paperId, version_n),
            )
            rows = _rows(cur)
            if rows:
                cid = str(rows[0].get("source_ipfs_cid") if fileType == "source" else rows[0].get("ipfs_cid") or "")
        else:
            cur.execute("SELECT ipfs_cid, latest_version FROM vertex_kiyo_paper WHERE paper_id = %s LIMIT 1", (paperId,))
            rows = _rows(cur)
            if rows:
                cid = str(rows[0].get("ipfs_cid") or "")
    if not cid:
        return {"error": "not found"}
    base = (ipfsGatewayUrl or "https://ipfs.etzhayyim.com").rstrip("/")
    return {
        "url": f"{base}/ipfs/{cid}",
        "cid": cid,
        "version": version_n,
        "contentType": "application/x-tar" if fileType == "source" else "application/pdf",
    }


def task_kiyo_list_by_author(authorDid: str = "", limit: Any = 50, offset: Any = 0, **_: Any) -> dict[str, Any]:
    limit_n = _bounded_int(limit, 50, min_value=1, max_value=100)
    offset_n = _bounded_int(offset, 0, min_value=0, max_value=100_000)
    with sync_cursor() as cur:
        cur.execute("SELECT * FROM mv_kiyo_author_hindex WHERE author_did = %s LIMIT 1", (authorDid,))
        hrows = _rows(cur)
        cur.execute(
            "SELECT p.paper_id, p.title, e.role, p.submitted_at, s.citation_in_count AS citationCount "
            "FROM edge_kiyo_authored_by e "
            "JOIN vertex_kiyo_paper p ON p.vertex_id = e.src_vid "
            "LEFT JOIN mv_kiyo_paper_stats s ON s.paper_id = p.paper_id "
            "WHERE e.dst_vid = %s ORDER BY p.submitted_at DESC "
            f"LIMIT {limit_n} OFFSET {offset_n}",
            (authorDid,),
        )
        papers = _rows(cur)
    h = hrows[0] if hrows else {}
    total_citations = int(h.get("total_citations") or 0)
    return {
        "authorDid": authorDid,
        "hIndex": int(total_citations ** 0.5) if h else 0,
        "totalPapers": int(h.get("total_papers") or 0),
        "totalCitations": total_citations,
        "papers": papers,
        "offset": offset_n,
        "limit": limit_n,
    }


def task_kiyo_get_citation_graph(paperId: str = "", **_: Any) -> dict[str, Any]:
    paper_vid = _paper_vid(paperId)
    with sync_cursor() as cur:
        cur.execute("SELECT src_vid, ref_label, confidence FROM edge_kiyo_cites WHERE dst_vid = %s LIMIT 100", (paper_vid,))
        citing = _rows(cur)
        cur.execute("SELECT dst_vid, resolved_doi, ref_label, confidence FROM edge_kiyo_cites WHERE src_vid = %s LIMIT 100", (paper_vid,))
        cited = _rows(cur)
    return {"paperId": paperId, "citing": citing, "cited": cited}


def task_kiyo_get_stats(**_: Any) -> dict[str, Any]:
    with sync_cursor() as cur:
        cur.execute("SELECT COUNT(paper_id) AS totalPapers FROM vertex_kiyo_paper WHERE status = %s", ("active",))
        totals = _rows(cur)
        cur.execute(
            "SELECT subject_code, paper_count, recent_30d_count FROM mv_kiyo_subject_stats "
            "ORDER BY paper_count DESC LIMIT 50"
        )
        subject_rows = _rows(cur)
    return {
        "totalPapers": int((totals[0] if totals else {}).get("totalPapers") or (totals[0] if totals else {}).get("totalpapers") or 0),
        "subjects": [
            {
                "subjectCode": s.get("subject_code"),
                "paperCount": int(s.get("paper_count") or 0),
                "recent30d": int(s.get("recent_30d_count") or 0),
            }
            for s in subject_rows
        ],
    }


def register(worker: Any, *, timeout_ms: int = 60_000) -> None:
    tasks = {
        "xrpc.com.etzhayyim.apps.kiyo.addReview": task_kiyo_add_review,
        "xrpc.com.etzhayyim.apps.kiyo.endorsePaper": task_kiyo_endorse_paper,
        "xrpc.com.etzhayyim.apps.kiyo.getCitationGraph": task_kiyo_get_citation_graph,
        "xrpc.com.etzhayyim.apps.kiyo.getPaper": task_kiyo_get_paper,
        "xrpc.com.etzhayyim.apps.kiyo.getPaperFile": task_kiyo_get_paper_file,
        "xrpc.com.etzhayyim.apps.kiyo.getStats": task_kiyo_get_stats,
        "xrpc.com.etzhayyim.apps.kiyo.listByAuthor": task_kiyo_list_by_author,
        "xrpc.com.etzhayyim.apps.kiyo.listPapers": task_kiyo_list_papers,
        "xrpc.com.etzhayyim.apps.kiyo.searchPapers": task_kiyo_search_papers,
        "xrpc.com.etzhayyim.apps.kiyo.withdrawPaper": task_kiyo_withdraw_paper,
    }
    for task_type, handler in tasks.items():
        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(handler)
