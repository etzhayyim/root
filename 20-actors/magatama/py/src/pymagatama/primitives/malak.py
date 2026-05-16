"""Malak XRPC primitives for BPMN/LangServer.

This module covers the Malak methods that were still implemented only in the
Cloudflare Worker. Older Malak BPMNs continue to use generic DB tasks.
"""

from __future__ import annotations

import datetime as _dt
import decimal as _decimal
import hashlib
import json
import re
import time
import uuid
from typing import Any

from pymagatama.db_sync import sync_cursor


MALAK_DID = "did:web:malak.gftd.ai"


def _now() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _id(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1000):x}-{uuid.uuid4().hex[:8]}"


def _str(v: Any) -> str:
    return "" if v is None else str(v)


def _num(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _jsonable(v: Any) -> Any:
    if isinstance(v, (_dt.datetime, _dt.date)):
        return v.isoformat()
    if isinstance(v, _decimal.Decimal):
        return float(v)
    return v


def _rows(cur: Any) -> list[dict[str, Any]]:
    cols = [d[0] for d in (cur.description or [])]
    return [{cols[i]: _jsonable(row[i]) for i in range(len(cols))} for row in cur.fetchall()]


def _sha(obj: Any) -> str:
    body = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _urls(body: str, urls: Any) -> list[str]:
    out = [str(v) for v in urls] if isinstance(urls, list) else []
    out += re.findall(r"\bhttps?://[^\s<>\"')]+", body or "")
    return list(dict.fromkeys([u for u in out if u]))[:50]


def task_malak_list_wallets(actorId: str = "", chain: str = "", limit: Any = 50, offset: Any = 0, **_: Any) -> dict[str, Any]:
    limit_n = max(1, min(int(limit or 50), 100))
    offset_n = max(0, int(offset or 0))
    clauses: list[str] = []
    params: list[Any] = []
    if actorId:
        clauses.append("actor_node_id = %s")
        params.append(f"intel:{actorId}")
    if chain:
        clauses.append("chain = %s")
        params.append(chain)
    sql = "SELECT * FROM vertex_malak_wallet_address"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += f" LIMIT {limit_n} OFFSET {offset_n}"
    with sync_cursor() as cur:
        cur.execute(sql, tuple(params))
        wallets = _rows(cur)
    return {"wallets": wallets, "total": len(wallets), "offset": offset_n, "limit": limit_n}


def task_malak_register_phishing_trap_inbox(
    trapKind: str = "",
    address: str = "",
    provider: str = "",
    label: str = "",
    legalBasis: str = "",
    retentionPolicy: str = "",
    status: str = "active",
    **_: Any,
) -> dict[str, Any]:
    trap_kind = trapKind.lower().strip()
    if trap_kind not in ("email", "sms") or not address or not provider or not legalBasis:
        return {"error": "trapKind, address, provider, and legalBasis are required"}
    status_v = (status or "active").lower()
    if status_v not in ("active", "paused", "retired"):
        return {"error": "status must be active, paused, or retired"}
    now = _now()
    trap_id = _id(f"trap-{trap_kind}")
    with sync_cursor() as cur:
        cur.execute(
            "INSERT INTO vertex_malak_phishing_trap "
            "(vertex_id,rkey,repo,trap_id,trap_kind,address,provider,label,legal_basis,retention_policy,"
            "status,created_at,updated_at,created_date,sensitivity_ord,owner_did,org_id,user_id,actor_did,org_did) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                f"at://{MALAK_DID}/ai.gftd.apps.malak.phishingTrap/{trap_id}",
                trap_id, MALAK_DID, trap_id, trap_kind, address, provider, label, legalBasis,
                retentionPolicy, status_v, now, now, now[:10], 120 if trap_kind == "sms" else 100,
                MALAK_DID, MALAK_DID, MALAK_DID, MALAK_DID, MALAK_DID,
            ),
        )
    return {"trapId": trap_id, "trapKind": trap_kind, "address": address, "status": status_v}


def task_malak_ingest_trap_message(
    trapId: str = "",
    trapKind: str = "",
    recipient: str = "",
    provider: str = "",
    providerMessageId: str = "",
    sender: str = "",
    subject: str = "",
    bodyPreview: str = "",
    rawPayloadHash: str = "",
    receivedAt: str = "",
    headersJson: str = "",
    urls: Any = None,
    tlp: str = "amber",
    **_: Any,
) -> dict[str, Any]:
    trap_kind = trapKind.lower().strip()
    if trap_kind not in ("email", "sms") or not recipient or not provider or not sender or not bodyPreview:
        return {"error": "trapKind, recipient, provider, sender, and bodyPreview are required"}
    now = _now()
    message_id = _id("trapmsg")
    evidence_id = f"evidence-{message_id}"
    url_list = _urls(bodyPreview, urls)
    payload = {
        "messageId": message_id,
        "evidenceId": evidence_id,
        "trapId": trapId,
        "trapKind": trap_kind,
        "recipient": recipient,
        "provider": provider,
        "providerMessageId": providerMessageId,
        "sender": sender,
        "subject": subject,
        "bodyPreview": bodyPreview[:4000],
        "urls": url_list,
        "rawPayloadHash": rawPayloadHash,
        "receivedAt": receivedAt or now,
    }
    payload_hash = _sha(payload)
    with sync_cursor() as cur:
        cur.execute(
            "INSERT INTO vertex_malak_trap_message "
            "(vertex_id,rkey,repo,message_id,evidence_id,trap_id,trap_kind,recipient,provider,provider_message_id,"
            "sender,subject,body_preview,urls_json,headers_json,raw_payload_hash,payload_hash,tlp,received_at,"
            "created_at,created_date,sensitivity_ord,owner_did,org_id,user_id,actor_did,org_did) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                f"at://{MALAK_DID}/ai.gftd.apps.malak.trapMessage/{message_id}",
                message_id, MALAK_DID, message_id, evidence_id, trapId, trap_kind, recipient, provider,
                providerMessageId, sender, subject, bodyPreview[:4000], json.dumps(url_list),
                headersJson, rawPayloadHash, payload_hash, (tlp or "amber").lower(), receivedAt or now,
                now, now[:10], 120 if trap_kind == "sms" or tlp == "red" else 100,
                MALAK_DID, MALAK_DID, MALAK_DID, MALAK_DID, MALAK_DID,
            ),
        )
    return {"messageId": message_id, "evidenceId": evidence_id, "payloadHash": payload_hash, "urlCount": len(url_list)}


def task_malak_list_agency_referral_drafts(
    actorId: str = "", caseId: str = "", draftState: str = "draft", limit: Any = 50, offset: Any = 0, **_: Any
) -> dict[str, Any]:
    return _list_table("vertex_malak_agency_referral_draft", "drafts", "created_at", limit, offset, {
        "actor_id": actorId,
        "case_id": caseId,
        "draft_state": draftState,
    })


def task_malak_list_agency_referral_exports(
    referralId: str = "", packageId: str = "", format: str = "", transmissionState: str = "not_transmitted",
    limit: Any = 50, offset: Any = 0, **_: Any
) -> dict[str, Any]:
    return _list_table("vertex_malak_agency_referral_export", "exports", "exported_at", limit, offset, {
        "referral_id": referralId,
        "package_id": packageId,
        "package_format": format,
        "transmission_state": transmissionState,
    })


def _list_table(table: str, out_key: str, order_col: str, limit: Any, offset: Any, filters: dict[str, str]) -> dict[str, Any]:
    limit_n = max(1, min(int(limit or 50), 100))
    offset_n = max(0, int(offset or 0))
    clauses: list[str] = []
    params: list[Any] = []
    for col, val in filters.items():
        if val:
            clauses.append(f"{col} = %s")
            params.append(val)
    sql = f"SELECT * FROM {table}"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += f" ORDER BY {order_col} DESC LIMIT {limit_n} OFFSET {offset_n}"
    with sync_cursor() as cur:
        cur.execute(sql, tuple(params))
        rows = _rows(cur)
    return {out_key: rows, "total": len(rows), "offset": offset_n, "limit": limit_n}


def task_malak_review_agency_referral_draft(
    referralId: str = "", decision: str = "", reviewerDid: str = "", reviewerRole: str = "",
    reason: str = "", approvalRef: str = "", externalCaseRef: str = "", notes: str = "", **_: Any
) -> dict[str, Any]:
    decision_v = decision.lower()
    if not referralId or decision_v not in ("approve", "reject", "escalate") or not reviewerDid or not reason:
        return {"error": "referralId, decision, reviewerDid, and reason are required"}
    now = _now()
    review_id = _id(f"review-{referralId}")
    draft_state = "approved" if decision_v == "approve" else "rejected" if decision_v == "reject" else "escalated"
    payload_hash = _sha({"reviewId": review_id, "referralId": referralId, "decision": decision_v, "reason": reason})
    with sync_cursor() as cur:
        cur.execute("SELECT * FROM vertex_malak_agency_referral_draft WHERE referral_id = %s LIMIT 1", (referralId,))
        draft = _rows(cur)
        if not draft:
            return {"error": "referral draft not found"}
        cur.execute(
            "INSERT INTO vertex_malak_agency_referral_review "
            "(vertex_id,rkey,repo,review_id,referral_id,decision,draft_state,reviewer_did,reviewer_role,reason,"
            "approval_ref,external_case_ref,notes,payload_hash,created_at,created_date,sensitivity_ord,owner_did,"
            "org_id,user_id,actor_did,org_did) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                f"at://{MALAK_DID}/ai.gftd.apps.malak.agencyReferralReview/{review_id}",
                review_id, MALAK_DID, review_id, referralId, decision_v, draft_state, reviewerDid,
                reviewerRole, reason, approvalRef or draft[0].get("approval_ref", ""), externalCaseRef,
                notes, payload_hash, now, now[:10], draft[0].get("sensitivity_ord", 100), MALAK_DID,
                MALAK_DID, reviewerDid, MALAK_DID, MALAK_DID,
            ),
        )
        cur.execute(
            "UPDATE vertex_malak_agency_referral_draft SET draft_state = %s, approval_ref = %s, updated_at = %s "
            "WHERE referral_id = %s",
            (draft_state, approvalRef or draft[0].get("approval_ref", ""), now, referralId),
        )
    return {"referralId": referralId, "reviewId": review_id, "draftState": draft_state, "decision": decision_v, "payloadHash": payload_hash}


def task_malak_export_agency_referral_package(
    referralId: str = "", format: str = "json", includeReviews: bool = True, includeEvidenceIds: bool = True, **_: Any
) -> dict[str, Any]:
    if not referralId:
        return {"error": "referralId is required"}
    fmt = (format or "json").lower()
    if fmt not in ("json", "stix"):
        return {"error": "format must be json or stix"}
    with sync_cursor() as cur:
        cur.execute("SELECT * FROM vertex_malak_agency_referral_draft WHERE referral_id = %s LIMIT 1", (referralId,))
        drafts = _rows(cur)
        if not drafts:
            return {"error": "referral draft not found"}
        draft = drafts[0]
        if draft.get("draft_state") != "approved":
            return {"error": "referral draft must be approved before export"}
        reviews: list[dict[str, Any]] = []
        if includeReviews:
            cur.execute("SELECT * FROM vertex_malak_agency_referral_review WHERE referral_id = %s ORDER BY created_at ASC", (referralId,))
            reviews = _rows(cur)
    evidence_ids = json.loads(draft.get("evidence_ids_json") or "[]") if includeEvidenceIds else []
    now = _now()
    package_id = _id(f"pkg-{referralId}")
    package = {"packageId": package_id, "exportedAt": now, "referral": draft, "reviews": reviews, "evidenceIds": evidence_ids}
    payload_hash = _sha(package)
    with sync_cursor() as cur:
        cur.execute(
            "INSERT INTO vertex_malak_agency_referral_export "
            "(vertex_id,rkey,repo,package_id,referral_id,package_format,payload_hash,transmission_state,exported_at,"
            "created_date,sensitivity_ord,owner_did,org_id,user_id,actor_did,org_did) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                f"at://{MALAK_DID}/ai.gftd.apps.malak.agencyReferralExport/{package_id}",
                package_id, MALAK_DID, package_id, referralId, fmt, payload_hash, "not_transmitted",
                now, now[:10], draft.get("sensitivity_ord", 100), MALAK_DID, MALAK_DID, MALAK_DID, MALAK_DID, MALAK_DID,
            ),
        )
    return {"referralId": referralId, "packageId": package_id, "format": fmt, "payloadHash": payload_hash, "package": package}


def task_malak_build_agency_referral_evidence_bundle(referralId: str = "", requireComplete: bool = False, **_: Any) -> dict[str, Any]:
    if not referralId:
        return {"error": "referralId is required"}
    with sync_cursor() as cur:
        cur.execute("SELECT evidence_ids_json FROM vertex_malak_agency_referral_draft WHERE referral_id = %s LIMIT 1", (referralId,))
        rows = _rows(cur)
        if not rows:
            return {"error": "referral draft not found"}
        evidence_ids = json.loads(rows[0].get("evidence_ids_json") or "[]")
        resolved: list[dict[str, Any]] = []
        missing: list[str] = []
        for eid in evidence_ids:
            cur.execute("SELECT * FROM vertex_malak_trap_message WHERE evidence_id = %s LIMIT 1", (eid,))
            found = _rows(cur)
            if found:
                resolved.append(found[0])
            else:
                missing.append(str(eid))
        if requireComplete and missing:
            return {"error": "missing evidence", "missingEvidenceIds": missing}
        now = _now()
        bundle_id = _id(f"bundle-{referralId}")
        bundle = {"referralId": referralId, "evidence": resolved}
        bundle_hash = _sha(bundle)
        cur.execute(
            "INSERT INTO vertex_malak_agency_referral_evidence_bundle "
            "(vertex_id,rkey,repo,bundle_id,referral_id,evidence_ids_json,resolved_evidence_json,missing_evidence_ids_json,"
            "evidence_count,bundle_hash,complete,created_at,created_date,sensitivity_ord,owner_did,org_id,user_id,actor_did,org_did) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                f"at://{MALAK_DID}/ai.gftd.apps.malak.agencyReferralEvidenceBundle/{bundle_id}",
                bundle_id, MALAK_DID, bundle_id, referralId, json.dumps(evidence_ids),
                json.dumps(resolved, ensure_ascii=False), json.dumps(missing), len(resolved),
                bundle_hash, not missing, now, now[:10], 100, MALAK_DID, MALAK_DID, MALAK_DID, MALAK_DID, MALAK_DID,
            ),
        )
    return {"referralId": referralId, "bundleId": bundle_id, "bundleHash": bundle_hash, "complete": not missing, "evidenceCount": len(resolved), "missingEvidenceIds": missing, "evidenceBundle": bundle}


def task_malak_export_stix_bundle(actorId: str = "", limit: Any = 50, **_: Any) -> dict[str, Any]:
    limit_n = max(1, min(int(limit or 50), 100))
    with sync_cursor() as cur:
        sql = "SELECT * FROM vertex_threat WHERE repo IS NOT NULL"
        params: tuple[Any, ...] = ()
        if actorId:
            sql += " AND code = %s"
            params = (actorId,)
        sql += f" LIMIT {limit_n}"
        cur.execute(sql, params)
        actors = _rows(cur)
        cur.execute(f"SELECT * FROM vertex_malak_wallet_address LIMIT {limit_n}")
        wallets = _rows(cur)
    return {
        "type": "bundle",
        "id": f"bundle--{uuid.uuid4()}",
        "objects": [
            {"type": "identity", "id": "identity--gftd-malak-platform", "name": "GFTD Malak Cybercrime Intelligence"},
            *[{"type": "threat-actor", "id": f"threat-actor--{a.get('code')}", "name": a.get("name", "")} for a in actors],
            *[{"type": "cryptocurrency-addr", "id": f"cryptocurrency-addr--{uuid.uuid4()}", "value": w.get("address", ""), "currency": str(w.get("chain", "")).upper()} for w in wallets],
        ],
    }


def task_malak_draft_agency_briefing(
    briefingType: str = "",
    targetAgencyPath: str = "",
    requesterDid: str = "",
    title: str = "",
    briefingFacts: Any = None,
    sourceDocs: Any = None,
    language: str = "ja",
    tlp: str = "AMBER",
    outputDir: str = "",
    targetAgencyName: str = "",
    targetAgencyDid: str = "",
    liveWrite: bool = False,
    **_: Any,
) -> dict[str, Any]:
    """MCP entrypoint for `ai.gftd.apps.malak.draftAgencyBriefing`.

    Drives the briefing LangGraph chain (assemble→render→extract→resolve→
    write_graph→PEGEL→persist→export) and returns metadata only — raw
    markdown is on disk + RW vertex_malak_briefing*, never in response.
    Phase 0 = liveWrite stays False; graph rows are staged in state but
    NOT INSERT'd into live RW until law clearance (PHASE-1-LAUNCH-READINESS G1+G2).
    """
    if not briefingType or not targetAgencyPath or not isinstance(briefingFacts, dict):
        return {"error": "briefingType, targetAgencyPath, briefingFacts (object) are required"}
    if not title or not requesterDid:
        return {"error": "title and requesterDid are required"}

    import asyncio as _asyncio
    from pymagatama.malak.langgraph.briefing import run_briefing

    try:
        result = _asyncio.run(run_briefing(
            briefing_type=briefingType,
            target_agency_path=targetAgencyPath,
            target_agency_name=targetAgencyName,
            target_agency_did=targetAgencyDid,
            requester_did=requesterDid,
            title=title,
            briefing_facts=briefingFacts,
            output_dir=outputDir or "",
            language=language,
            tlp=tlp,
            source_docs=list(sourceDocs or []),
            live_write=bool(liveWrite),
        ))
    except Exception as e:  # noqa: BLE001
        return {"error": f"briefing pipeline failed: {e}"}

    return {
        "briefingId":     result.get("briefing_id", ""),
        "version":        result.get("version", 1),
        "files":          result.get("files") or {},
        "documentSha256": result.get("document_sha256", ""),
        "sectionShas":    result.get("section_shas") or [],
        "pegelTicks":     result.get("pegel_ticks") or [],
        "entityCounts":   result.get("entity_counts") or {},
        "graphVertexIds": result.get("graph_vertex_ids") or {},
        "error":          result.get("error") or "",
    }


def task_malak_draft_police_report(
    caseId: str = "",
    caseFacts: Any = None,
    outputDir: str = "",
    docTypes: Any = None,
    **_: Any,
) -> dict[str, Any]:
    """MCP entrypoint for `ai.gftd.apps.malak.draftPoliceReport`.

    Drives the police_report LangGraph chain (assemble→6 drafts→PEGEL→persist)
    and returns metadata only — raw markdown is on disk + RW ticks, never in
    the response (Vault zero-knowledge invariant per CLAUDE.md root rules).
    """
    if not caseId or not isinstance(caseFacts, dict):
        return {"error": "caseId and caseFacts (object) are required"}

    import asyncio as _asyncio
    from pymagatama.malak.langgraph.police_report import run_police_report

    doc_types = [str(d) for d in (docTypes or [])] or None
    try:
        result = _asyncio.run(run_police_report(
            case_id=caseId,
            case_facts=caseFacts,
            output_dir=outputDir or "",
            doc_types=doc_types,
        ))
    except Exception as e:  # noqa: BLE001
        return {"error": f"police_report pipeline failed: {e}"}

    docs = result.get("documents") or {}
    sha = {dt: hashlib.sha256(md.encode("utf-8")).hexdigest() for dt, md in docs.items()}
    return {
        "caseNo":         result.get("case_no", ""),
        "files":          result.get("files") or {},
        "documentSha256": sha,
        "pegelTicks":     result.get("pegel_ticks") or [],
        "reportingLine":  result.get("reporting_line") or [],
        "error":          result.get("error") or "",
    }


# ─────────────────────────────────────────────────────────────────────────
# Phase 0 surveillance + agency-outreach stubs (2026-05-13)
#
# These 15 NSIDs were merged into malak from the retired `mehikari` project
# on 2026-05-13 (CXO-LEDGER #32-33). Phase 0 = 法務 review only — Kunal CLO
# triage期限 2026-06-01 + 外部弁護士契約 2026-07-15。Phase 1 着手判断 = 2026-08-01.
#
# Each stub returns a structured "phase0_stub" response WITHOUT calling any
# business logic. The 4 edge gates (queryPerson warrant / exportEvidence
# two-stage approval / registerAgencyProspect opt-in / sendAgencyOutreach
# business-hour) are also rechecked here for defense-in-depth.
#
# Spec: `_working/malak/surveillance/DESIGN.md` (8 surveillance + 7 outreach)
# Compliance: `_working/malak/surveillance/COMPLIANCE-MEMO.md` §6 SAFETY_GATES
# ─────────────────────────────────────────────────────────────────────────

_PHASE0_STUB_MESSAGE = (
    "Phase 0: handler not yet implemented; legal review in progress "
    "(Kunal CLO triage 2026-06-01 / external counsel 2026-07-15). "
    "See _working/malak/surveillance/DESIGN.md."
)
_PHASE0_NEXT_MILESTONE = "Phase 1 着手判断 2026-08-01"
_ALLOWED_OPT_IN_SOURCES = {"exhibition_list", "lecture_host", "referral", "inbound"}


def _phase0_stub(method: str, extra: dict | None = None) -> dict[str, Any]:
    return {
        "status": "phase0_stub",
        "nsid": f"ai.gftd.apps.malak.{method}",
        "phase": 0,
        "message": _PHASE0_STUB_MESSAGE,
        "nextMilestone": _PHASE0_NEXT_MILESTONE,
        **(extra or {}),
    }


# ── 検索系 (police operator surface, 8 NSIDs) ────────────────────────────


def task_malak_register_camera(**kwargs: Any) -> dict[str, Any]:
    if not kwargs.get("agreementId"):
        return {"status": "rejected", "rejectionReason": "agreementId required (camera owner agreement)"}
    return _phase0_stub("registerCamera", {"cameraId": kwargs.get("cameraId", "")})


def task_malak_ingest_surveillance_clip(**kwargs: Any) -> dict[str, Any]:
    return _phase0_stub("ingestSurveillanceClip", {"clipId": kwargs.get("clipSha256", "")})


def task_malak_query_scene(**kwargs: Any) -> dict[str, Any]:
    if not kwargs.get("sceneText") or not kwargs.get("requesterDid"):
        return {"status": "rejected", "error": "sceneText and requesterDid required"}
    return _phase0_stub("queryScene", {"queryId": "", "results": []})


def task_malak_query_person(**kwargs: Any) -> dict[str, Any]:
    # Defense-in-depth: edge already enforces this; re-check.
    lb = kwargs.get("legalBasis") or {}
    if not (isinstance(lb, dict) and (lb.get("warrantRef") or lb.get("enquiryRef"))):
        return {
            "status": "denied",
            "error": "WARRANT_OR_ENQUIRY_REQUIRED: legalBasis.warrantRef OR legalBasis.enquiryRef required",
        }
    return _phase0_stub("queryPerson", {"queryId": "", "status": "phase0_stub"})


def task_malak_review_surveillance_matches(**kwargs: Any) -> dict[str, Any]:
    if not kwargs.get("queryId") or not kwargs.get("reviewerDid"):
        return {"status": "rejected", "error": "queryId and reviewerDid required"}
    return _phase0_stub("reviewSurveillanceMatches", {"queryId": kwargs.get("queryId", "")})


def task_malak_export_surveillance_evidence(**kwargs: Any) -> dict[str, Any]:
    if not kwargs.get("supervisorDid") or not kwargs.get("sectionChiefDid"):
        return {
            "status": "denied",
            "error": "TWO_STAGE_APPROVAL_REQUIRED: supervisorDid + sectionChiefDid both required",
        }
    return _phase0_stub("exportSurveillanceEvidence", {"caseNo": "", "files": {}, "documentSha256": {}})


def task_malak_list_surveillance_queries(**_: Any) -> dict[str, Any]:
    return _phase0_stub("listSurveillanceQueries", {"queries": [], "cursor": "", "offset": 0, "limit": 0})


def task_malak_get_surveillance_audit_trail(**_: Any) -> dict[str, Any]:
    return _phase0_stub("getSurveillanceAuditTrail", {"events": [], "cursor": "", "offset": 0, "limit": 0})


# ── 営業系 (B2G agency-outreach, 7 NSIDs) ───────────────────────────────


def task_malak_register_agency_prospect(**kwargs: Any) -> dict[str, Any]:
    src = kwargs.get("optInSource")
    if not src or src not in _ALLOWED_OPT_IN_SOURCES:
        return {
            "status": "rejectedOptInSource",
            "error": f"optInSource must be one of {sorted(_ALLOWED_OPT_IN_SOURCES)}; got {src!r}",
        }
    if not kwargs.get("optInAt"):
        return {"status": "rejectedOptInMissing", "error": "optInAt required"}
    return _phase0_stub("registerAgencyProspect", {"prospectId": ""})


def task_malak_draft_agency_outreach(**_: Any) -> dict[str, Any]:
    return _phase0_stub("draftAgencyOutreach", {"draftId": "", "subject": "", "bodyMarkdown": "", "safetyFlags": []})


def task_malak_review_agency_outreach(**kwargs: Any) -> dict[str, Any]:
    if not kwargs.get("draftId") or not kwargs.get("approverDid"):
        return {"status": "rejected", "error": "draftId and approverDid required"}
    return _phase0_stub("reviewAgencyOutreach", {"draftId": kwargs.get("draftId", "")})


def task_malak_send_agency_outreach(**kwargs: Any) -> dict[str, Any]:
    hint = kwargs.get("scheduleHint")
    if hint != "nextBusinessHour":
        # Defense-in-depth business-hour check (UTC → JST)
        now_jst = _dt.datetime.now(tz=_dt.timezone(_dt.timedelta(hours=9)))
        if now_jst.weekday() >= 5 or not (9 <= now_jst.hour < 17):
            return {
                "status": "rejectedOutsideHours",
                "error": "Outside 09:00-17:00 JST weekdays; resubmit with scheduleHint=nextBusinessHour to queue.",
            }
    return _phase0_stub("sendAgencyOutreach", {"sendId": "", "msMessageId": ""})


def task_malak_handle_agency_outreach_reply(**_: Any) -> dict[str, Any]:
    return _phase0_stub("handleAgencyOutreachReply", {"replyId": "", "senderClass": "unknown"})


def task_malak_unsubscribe_agency_outreach(**kwargs: Any) -> dict[str, Any]:
    if not kwargs.get("token"):
        return {"status": "tokenInvalid", "error": "token required"}
    return _phase0_stub("unsubscribeAgencyOutreach", {"unsubscribedAt": _now()})


def task_malak_list_agency_outreach(**_: Any) -> dict[str, Any]:
    return _phase0_stub(
        "listAgencyOutreach",
        {"outreaches": [], "stageCounts": {}, "cursor": "", "offset": 0, "limit": 0},
    )


def register(worker: Any, *, timeout_ms: int = 120_000) -> None:
    tasks = {
        "xrpc.ai.gftd.apps.malak.buildAgencyReferralEvidenceBundle": task_malak_build_agency_referral_evidence_bundle,
        "xrpc.ai.gftd.apps.malak.draftAgencyBriefing": task_malak_draft_agency_briefing,
        "xrpc.ai.gftd.apps.malak.draftPoliceReport": task_malak_draft_police_report,
        "xrpc.ai.gftd.apps.malak.exportAgencyReferralPackage": task_malak_export_agency_referral_package,
        "xrpc.ai.gftd.apps.malak.exportStixBundle": task_malak_export_stix_bundle,
        "xrpc.ai.gftd.apps.malak.ingestTrapMessage": task_malak_ingest_trap_message,
        "xrpc.ai.gftd.apps.malak.listAgencyReferralDrafts": task_malak_list_agency_referral_drafts,
        "xrpc.ai.gftd.apps.malak.listAgencyReferralExports": task_malak_list_agency_referral_exports,
        "xrpc.ai.gftd.apps.malak.listWallets": task_malak_list_wallets,
        "xrpc.ai.gftd.apps.malak.registerPhishingTrapInbox": task_malak_register_phishing_trap_inbox,
        "xrpc.ai.gftd.apps.malak.reviewAgencyReferralDraft": task_malak_review_agency_referral_draft,
        # Phase 0 surveillance + outreach stubs (2026-05-13)
        "xrpc.ai.gftd.apps.malak.registerCamera": task_malak_register_camera,
        "xrpc.ai.gftd.apps.malak.ingestSurveillanceClip": task_malak_ingest_surveillance_clip,
        "xrpc.ai.gftd.apps.malak.queryScene": task_malak_query_scene,
        "xrpc.ai.gftd.apps.malak.queryPerson": task_malak_query_person,
        "xrpc.ai.gftd.apps.malak.reviewSurveillanceMatches": task_malak_review_surveillance_matches,
        "xrpc.ai.gftd.apps.malak.exportSurveillanceEvidence": task_malak_export_surveillance_evidence,
        "xrpc.ai.gftd.apps.malak.listSurveillanceQueries": task_malak_list_surveillance_queries,
        "xrpc.ai.gftd.apps.malak.getSurveillanceAuditTrail": task_malak_get_surveillance_audit_trail,
        "xrpc.ai.gftd.apps.malak.registerAgencyProspect": task_malak_register_agency_prospect,
        "xrpc.ai.gftd.apps.malak.draftAgencyOutreach": task_malak_draft_agency_outreach,
        "xrpc.ai.gftd.apps.malak.reviewAgencyOutreach": task_malak_review_agency_outreach,
        "xrpc.ai.gftd.apps.malak.sendAgencyOutreach": task_malak_send_agency_outreach,
        "xrpc.ai.gftd.apps.malak.handleAgencyOutreachReply": task_malak_handle_agency_outreach_reply,
        "xrpc.ai.gftd.apps.malak.unsubscribeAgencyOutreach": task_malak_unsubscribe_agency_outreach,
        "xrpc.ai.gftd.apps.malak.listAgencyOutreach": task_malak_list_agency_outreach,
    }
    for task_type, handler in tasks.items():
        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(handler)
