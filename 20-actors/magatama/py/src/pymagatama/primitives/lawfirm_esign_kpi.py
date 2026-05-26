"""
lawfirm.esign.* + lawfirm.kpi.snapshot — LangServer handlers.

Task types:
  lawfirm.esign.request   Issue e-signature envelope (DocuSign / Adobe / RazorpaySign)
  lawfirm.esign.webhook   Receive provider envelope-status webhook
  lawfirm.kpi.snapshot    Read streaming MV snapshot (RLS-gated CEO/COO/CLO)

Provider abstraction: docusign (default) / adobesign / razorpaysign.
Credentials via env vars; missing creds → returns dry_run envelope (for testing).

ADR-0036 Hyperdrive direct.
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
import os
import uuid
from typing import Any

LOG = logging.getLogger("lawfirm.esign_kpi")

_FIRM_DID = "did:web:lawfirm.etzhayyim.com"

# RLS allowlist for KPI snapshot (CEO + COO + CLO)
_KPI_READERS = {
    "did:web:j-kawasaki.etzhayyim.com",
    "did:web:a-nakamura.etzhayyim.com",
    "did:web:k-bakshi.etzhayyim.com",
}


def _now_iso() -> str:
    return _dt.datetime.now(tz=_dt.UTC).strftime("%Y-%m-%d %H:%M:%S")

def _vid(kind: str) -> str:
    stamp = _dt.datetime.now(tz=_dt.UTC).strftime("%Y%m%d%H%M%S")
    return f"at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.lawfirm.{kind}/{stamp}-{uuid.uuid4().hex[:8]}"


# ── Persistence helpers ───────────────────────────────────────────────────────

def _execute(sql_str: str, params: dict) -> bool:
    try:
        from sqlalchemy import text
        from pymagatama.db_alchemy import sa_rowcount
        sa_rowcount(text(sql_str), params)
        return True
    except Exception as exc:
        LOG.warning("execute failed: %s", exc)
        return False

def _query(sql_str: str, params: dict | None = None) -> list[dict]:
    try:
        from sqlalchemy import text
        from pymagatama.db_alchemy import sa_query
        return sa_query(text(sql_str), params or {})
    except Exception as exc:
        LOG.warning("query failed: %s", exc)
        return []


# ── DocuSign provider call (real or dry-run) ──────────────────────────────────

def _provider_create_envelope(
    provider: str,
    document_kind: str,
    matter_uri: str,
    recipients: list[dict],
    pdf_b64: str,
    template_id: str,
    template_vars: dict,
    expires_in_days: int,
    callback_url: str,
) -> dict:
    """Call the chosen provider; fall back to dry_run on missing creds."""
    if provider == "docusign":
        token = os.environ.get("DOCUSIGN_INTEGRATION_TOKEN", "")
        account_id = os.environ.get("DOCUSIGN_ACCOUNT_ID", "")
        if not token or not account_id:
            return {
                "ok": True,
                "envelope_id": f"dry-{uuid.uuid4().hex[:12]}",
                "signing_urls": [f"https://demo.docusign.net/Signing/StartInSession.aspx?t={uuid.uuid4().hex}" for _ in recipients],
                "dry_run": True,
                "expires_at": (_dt.datetime.now(tz=_dt.UTC) + _dt.timedelta(days=expires_in_days)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        # Real DocuSign REST call (skipped here — implementation lives in the
        # CF Worker side once the integration secret is provisioned. The
        # Python primitive returns dry_run when creds absent, which is the
        # current Day-0 state).
        try:
            import urllib.request
            url = f"https://demo.docusign.net/restapi/v2.1/accounts/{account_id}/envelopes"
            body = json.dumps({
                "emailSubject": f"[Bakshi & Partners] {document_kind} — please sign",
                "documents": [{
                    "documentBase64": pdf_b64,
                    "name": f"{document_kind}.pdf",
                    "fileExtension": "pdf",
                    "documentId": "1",
                }] if pdf_b64 else [],
                "templateId": template_id or None,
                "templateRoles": [
                    {
                        "email": r["email"],
                        "name": r["name"],
                        "roleName": r.get("role", "signer"),
                    } for r in recipients
                ] if template_id else [],
                "recipients": {
                    "signers": [
                        {
                            "email": r["email"],
                            "name": r["name"],
                            "recipientId": str(i + 1),
                            "routingOrder": str(i + 1),
                        } for i, r in enumerate(recipients) if r.get("role") in ("client", "advocate")
                    ],
                } if not template_id else {},
                "status": "sent",
            }).encode()
            req = urllib.request.Request(
                url, data=body,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read())
            return {
                "ok": True,
                "envelope_id": payload.get("envelopeId", ""),
                "signing_urls": [],
                "expires_at": (_dt.datetime.now(tz=_dt.UTC) + _dt.timedelta(days=expires_in_days)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        except Exception as exc:
            return {"ok": False, "error": f"docusign_call_failed: {exc}"}

    if provider == "adobesign":
        # Stub — same dry_run pattern; Adobe REST integration deferred
        return {
            "ok": True,
            "envelope_id": f"adobe-dry-{uuid.uuid4().hex[:12]}",
            "signing_urls": [],
            "dry_run": True,
            "expires_at": (_dt.datetime.now(tz=_dt.UTC) + _dt.timedelta(days=expires_in_days)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    if provider == "razorpaysign":
        return {
            "ok": True,
            "envelope_id": f"rzp-dry-{uuid.uuid4().hex[:12]}",
            "signing_urls": [],
            "dry_run": True,
            "expires_at": (_dt.datetime.now(tz=_dt.UTC) + _dt.timedelta(days=expires_in_days)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    return {"ok": False, "error": f"unknown_provider: {provider}"}


# ── Task: lawfirm.esign.request ───────────────────────────────────────────────

async def task_lawfirm_esign_request(
    document_kind: str = "engagementLetter",
    matter_uri: str = "",
    recipients: list[dict] | None = None,
    document_pdf_b64: str = "",
    template_id: str = "",
    template_vars: str = "",
    provider: str = "docusign",
    expires_in_days: int = 14,
    callback_url: str = "",
) -> dict:
    recipients = recipients or []
    if not recipients:
        return {"ok": False, "error": "no_recipients"}

    try:
        tvars = json.loads(template_vars) if template_vars else {}
    except Exception:
        tvars = {}

    res = _provider_create_envelope(
        provider, document_kind, matter_uri, recipients,
        document_pdf_b64, template_id, tvars, expires_in_days, callback_url,
    )
    if not res.get("ok"):
        return res

    envelope_id = res["envelope_id"]
    expires_at = res.get("expires_at", "")

    # Persist request row
    _execute(
        "INSERT INTO vertex_lawfirm_esign_request (vertex_id, envelope_id, "
        "provider, document_kind, matter_uri, recipients_json, status, "
        "expires_at, callback_url, created_at, owner_did) "
        "VALUES (:vid, :eid, :prov, :dk, :muri, :rec, :status, :exp, :cb, :now, :owner)",
        {
            "vid":    _vid("esignRequest"),
            "eid":    envelope_id,
            "prov":   provider,
            "dk":     document_kind,
            "muri":   matter_uri,
            "rec":    json.dumps(recipients, ensure_ascii=False)[:8000],
            "status": "sent",
            "exp":    expires_at,
            "cb":     callback_url,
            "now":    _now_iso(),
            "owner":  _FIRM_DID,
        },
    )

    return {
        "ok":           True,
        "envelope_id":  envelope_id,
        "signing_urls": res.get("signing_urls", []),
        "expires_at":   expires_at,
        "dry_run":      bool(res.get("dry_run")),
    }


# ── Task: lawfirm.esign.webhook (envelope status updates) ─────────────────────

async def task_lawfirm_esign_webhook(
    envelope_id: str = "",
    status: str = "",
    completed_at: str = "",
    provider: str = "docusign",
    raw_payload: str = "",
) -> dict:
    """Receive DocuSign / Adobe / Razorpay envelope-status webhook."""
    if not envelope_id:
        return {"ok": False, "error": "missing_envelope_id"}

    _execute(
        "UPDATE vertex_lawfirm_esign_request "
        "SET status = :status, completed_at = :completed, updated_at = :now, "
        "    raw_status_json = :raw "
        "WHERE envelope_id = :eid",
        {
            "status":    status,
            "completed": completed_at or (_now_iso() if status == "completed" else ""),
            "now":       _now_iso(),
            "raw":       raw_payload[:30_000],
            "eid":       envelope_id,
        },
    )
    LOG.info("esign envelope=%s provider=%s status=%s", envelope_id, provider, status)
    return {"ok": True, "envelope_id": envelope_id, "status": status}


# ── Task: lawfirm.kpi.snapshot ────────────────────────────────────────────────

async def task_lawfirm_kpi_snapshot(
    window_months: int = 6,
    currency: str = "USD",
    requester_did: str = "",
) -> dict:
    if requester_did and requester_did not in _KPI_READERS:
        return {"ok": False, "error": "rls_denied"}

    revenue = _query(
        "SELECT month, currency, stream, amount_minor_total, payment_count "
        "FROM mv_lawfirm_revenue_monthly "
        "WHERE currency = :ccy "
        f"ORDER BY month DESC LIMIT {int(window_months)}",
        {"ccy": currency},
    )

    outstanding = _query(
        "SELECT COUNT(*) AS cnt, COALESCE(SUM(total_minor), 0) AS total_minor "
        "FROM mv_lawfirm_outstanding_invoices WHERE currency = :ccy",
        {"ccy": currency},
    )

    pipeline = _query(
        "SELECT compliance_check, COUNT(*) AS cnt "
        "FROM mv_lawfirm_marketing_publish_calendar "
        "GROUP BY compliance_check"
    )

    matters = _query(
        "SELECT COUNT(*) AS cnt FROM vertex_lawfirm_matter WHERE status = 'active'"
    )

    return {
        "ok":                   True,
        "snapshot_at":          _now_iso(),
        "revenue_by_month":     revenue,
        "outstanding_invoices": (outstanding[0] if outstanding else {"cnt": 0, "total_minor": 0}),
        "marketing_pipeline":   pipeline,
        "active_matter_count":  (matters[0]["cnt"] if matters else 0),
    }


# ── Worker registration ───────────────────────────────────────────────────────

def register(app: Any, timeout_ms: int = 60_000) -> None:
    from pymagatama.langserver_compat import LangServerWorker
    if not isinstance(app, LangServerWorker):
        return

    @app.task(task_type="lawfirm.esign.request",
              timeout_ms=timeout_ms, max_jobs_to_activate=4)
    async def _req(document_kind: str = "engagementLetter", matter_uri: str = "",
                   recipients: list[dict] | None = None,
                   document_pdf_b64: str = "", template_id: str = "",
                   template_vars: str = "", provider: str = "docusign",
                   expires_in_days: int = 14, callback_url: str = "") -> dict:
        return await task_lawfirm_esign_request(
            document_kind=document_kind, matter_uri=matter_uri,
            recipients=recipients or [], document_pdf_b64=document_pdf_b64,
            template_id=template_id, template_vars=template_vars,
            provider=provider, expires_in_days=expires_in_days,
            callback_url=callback_url,
        )

    @app.task(task_type="lawfirm.esign.webhook",
              timeout_ms=timeout_ms, max_jobs_to_activate=8)
    async def _wh(envelope_id: str = "", status: str = "",
                  completed_at: str = "", provider: str = "docusign",
                  raw_payload: str = "") -> dict:
        return await task_lawfirm_esign_webhook(
            envelope_id=envelope_id, status=status,
            completed_at=completed_at, provider=provider, raw_payload=raw_payload,
        )

    @app.task(task_type="lawfirm.kpi.snapshot",
              timeout_ms=timeout_ms, max_jobs_to_activate=4)
    async def _kpi(window_months: int = 6, currency: str = "USD",
                   requester_did: str = "") -> dict:
        return await task_lawfirm_kpi_snapshot(
            window_months=window_months, currency=currency, requester_did=requester_did,
        )

    LOG.info("Registered tasks: lawfirm.esign.{request,webhook}, lawfirm.kpi.snapshot")
