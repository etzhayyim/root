"""Mailer handlers for BPMN + Zeebe."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
import urllib.request
import uuid
from typing import Any

from pymagatama.db_sync import sync_cursor
from pymagatama.gewp import (
    GewpMessage,
    compose_resend_payload,
    new_message,
    new_thread_id,
    parse_from_email,
    to_dict as gewp_to_dict,
)
from pymagatama.local_agent_env import load_keychain_secret

ACTOR = "did:web:mailer.etzhayyim.com"
INBOUND_REPO = "did:web:ml1nb0nd.etzhayyim.com"
INBOUND_COLLECTION = "ai.gftd.apps.mailer.inboundEmail"
PDS_ORIGIN = os.environ.get("PDS_ORIGIN", "https://atproto.etzhayyim.com")


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _str(value: Any) -> str:
    return "" if value is None else str(value)


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


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


def _http_json(url: str, *, method: str = "GET", body: bytes | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any], str]:
    req = urllib.request.Request(url, method=method, data=body, headers={"accept": "application/json", "user-agent": "gftd-mailer-zeebe/1", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw)
        except Exception:
            data = {}
        return e.code, data, raw


KEYCHAIN_SECRET_REFS: dict[str, tuple[str, str]] = {
    "RESEND_API_KEY": ("gftd.resend", "API_KEY"),
    "SS_RESEND_API_KEY": ("gftd.resend", "API_KEY"),
    "EMAIL_RELAY_ADMIN_TOKEN": ("gftd.email-relay", "ADMIN_TOKEN"),
    "SS_EMAIL_RELAY_ADMIN_TOKEN": ("gftd.email-relay", "ADMIN_TOKEN"),
}


def _secret(*names: str) -> str:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    for name in names:
        ref = KEYCHAIN_SECRET_REFS.get(name)
        if not ref:
            continue
        value = load_keychain_secret(service=ref[0], account=ref[1])
        if value:
            return value
    return ""


def health(**_: Any) -> dict[str, Any]:
    return {"ok": True, "app": "mailer", "ts": now_iso()}


def list_emails(limit: Any = 30, toLocal: str = "", **_: Any) -> dict[str, Any]:
    n = max(1, min(_int(limit, 30), 100))
    to_local = toLocal.lower().strip()
    where = "WHERE to_local=%s" if to_local else ""
    params: tuple[Any, ...] = (to_local,) if to_local else ()
    rows = _fetch_all(
        f"""SELECT vertex_id, message_id, from_address_hash, to_local, to_local_hash,
        subject, body_text, received_at_ms, content_protection, status
        FROM vertex_mailer_inbound_email {where}
        ORDER BY received_at_ms DESC
        LIMIT {n}""",
        params,
    )
    if not rows:
        return _list_emails_from_pds(n, to_local)
    items = [
        {
            "uri": row.get("vertex_id") or "",
            "cid": "",
            "messageId": row.get("message_id") or "",
            "toLocal": row.get("to_local") or "",
            "toLocalHash": row.get("to_local_hash") or "",
            "fromAddressHash": row.get("from_address_hash") or "",
            "subject": row.get("subject") or "",
            "bodyText": row.get("body_text") or "",
            "receivedAtMs": row.get("received_at_ms") or 0,
            "contentProtection": row.get("content_protection") or "plaintext",
            "status": row.get("status") or "",
        }
        for row in rows
    ]
    return {"items": items, "count": len(items)}


def _list_emails_from_pds(limit: int, to_local: str) -> dict[str, Any]:
    qs = urllib.parse.urlencode({"repo": INBOUND_REPO, "collection": INBOUND_COLLECTION, "limit": str(limit)})
    status, data, raw = _http_json(f"{PDS_ORIGIN}/xrpc/com.atproto.repo.listRecords?{qs}")
    if status >= 400:
        return {"items": [], "count": 0, "error": f"pds_{status}", "body": raw[:200]}
    records = data.get("records") if isinstance(data.get("records"), list) else []
    items = []
    for rec in records:
        value = rec.get("value") if isinstance(rec, dict) else {}
        if not isinstance(value, dict):
            continue
        item = {
            "uri": rec.get("uri") or "",
            "cid": rec.get("cid") or "",
            "toLocal": _str(value.get("toLocal")),
            "toLocalHash": _str(value.get("toLocalHash")),
            "fromAddressHash": _str(value.get("fromAddressHash")),
            "subject": _str(value.get("subject")),
            "bodyText": _str(value.get("bodyText")),
            "receivedAtMs": value.get("receivedAtMs"),
            "contentProtection": _str(value.get("contentProtection")) or "plaintext",
            "status": _str(value.get("status")),
        }
        if not to_local or item["toLocal"] == to_local:
            items.append(item)
    return {"items": items, "count": len(items)}


def list_bindings(limit: Any = 50, **_: Any) -> dict[str, Any]:
    n = max(1, min(_int(limit, 50), 200))
    rows = _fetch_all(
        f"""SELECT email, did, direction, verified, created_at_ms
        FROM vertex_mailer_email_binding
        ORDER BY created_at_ms DESC
        LIMIT {n}""",
    )
    items = [
        {
            "email": row.get("email") or "",
            "did": row.get("did") or "",
            "direction": row.get("direction") or "",
            "verified": bool(row.get("verified")),
            "createdAtMs": row.get("created_at_ms") or 0,
        }
        for row in rows
    ]
    return {"items": items, "count": len(items)}


def stats(**_: Any) -> dict[str, Any]:
    emails = _fetch_one("SELECT COUNT(*) AS total FROM vertex_mailer_inbound_email") or {}
    bindings = _fetch_one("SELECT COUNT(*) AS total FROM vertex_mailer_email_binding") or {}
    return {"emails": _int(emails.get("total")), "bindings": _int(bindings.get("total")), "ts": now_iso()}


def send_email(to: str = "", subject: str = "", text: str = "", html: str = "", from_: str = "", fromAddress: str = "", replyTo: str = "", **kwargs: Any) -> dict[str, Any]:
    sender = from_ or fromAddress or _str(kwargs.get("from")) or "abuse-report@etzhayyim.com"
    if not to or not subject or not text:
        return {"error": "to/subject/text required"}
    api_key = _secret("RESEND_API_KEY", "SS_RESEND_API_KEY")
    if not api_key:
        return {"error": "RESEND_API_KEY not configured"}
    payload: dict[str, Any] = {"from": sender, "to": [to], "subject": subject, "text": text}
    if html:
        payload["html"] = html
    if replyTo:
        payload["reply_to"] = replyTo
    status, data, raw = _http_json(
        "https://api.resend.com/emails",
        method="POST",
        headers={"authorization": f"Bearer {api_key}", "content-type": "application/json"},
        body=json.dumps(payload).encode(),
    )
    message_id = _str(data.get("id"))
    sent_at = now_iso()
    outbound_record_error = ""
    try:
        _record_outbound(message_id, sender, to, subject, text, html, "resend", "sent" if status < 400 else "error", "" if status < 400 else raw[:500])
    except Exception as exc:
        outbound_record_error = str(exc)[:300]
    if status >= 400:
        return {"error": "resend_api_failed", "status": status, "body": raw[:500], "outboundRecordError": outbound_record_error}
    result = {"messageId": message_id, "provider": "resend", "from": sender, "to": to, "subject": subject, "sentAt": sent_at}
    if outbound_record_error:
        result["outboundRecordError"] = outbound_record_error
    return result


def _record_outbound(
    message_id: str, sender: str, to: str, subject: str, text: str, html: str,
    provider: str, status: str, error: str,
    gewp_thread_id: str = "", gewp_step: int = 0,
) -> None:
    rid = f"outbound-{uuid.uuid4().hex[:16]}"
    now_ms = int(time.time() * 1000)
    vertex_id = f"at://{ACTOR}/ai.gftd.apps.mailer.outboundEmail/{rid}"
    _execute("DELETE FROM vertex_mailer_outbound_email WHERE vertex_id = %s", (vertex_id,))
    _execute(
        """INSERT INTO vertex_mailer_outbound_email
        (vertex_id, sensitivity_ord, owner_did, rkey, repo, message_id, from_address, to_address,
         subject, body_text, body_html, provider, provider_message_id, status, error, sent_at_ms,
         created_at, org_id, user_id, actor_id, gewp_thread_id, gewp_step)
        VALUES (%s,1,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'anon','anon',%s,%s,%s)""",
        (vertex_id, ACTOR, rid, ACTOR, message_id, sender, to, subject, text, html,
         provider, message_id, status, error, now_ms, now_iso(), ACTOR,
         gewp_thread_id or None, gewp_step or None),
    )


def provision_mailbox(handle: str = "", did: str = "", purpose: str = "", **_: Any) -> dict[str, Any]:
    local = handle.strip().lower()
    if not local:
        return {"error": "handle is required", "email": "", "did": ""}
    if not re.match(r"^[a-z][a-z0-9._-]{0,63}$", local):
        return {"error": "handle must be alpha-start, lowercase, kebab/dot/underscore", "email": "", "did": ""}
    recipient_did = did or f"did:web:{local}.etzhayyim.com"
    email = f"{local}@etzhayyim.com"
    relay_url = os.environ.get("EMAIL_RELAY_ADMIN_URL", "https://email-relay.etzhayyim.com/register-email")
    token = _secret("EMAIL_RELAY_ADMIN_TOKEN", "SS_EMAIL_RELAY_ADMIN_TOKEN")
    if not token:
        return {"email": email, "did": recipient_did, "registered": False, "error": "EMAIL_RELAY_ADMIN_TOKEN not configured"}
    status, data, raw = _http_json(
        relay_url,
        method="POST",
        headers={"authorization": f"Bearer {token}", "content-type": "application/json"},
        body=json.dumps({"email": email, "did": recipient_did, "purpose": purpose or None}).encode(),
    )
    if status >= 400:
        return {"email": email, "did": recipient_did, "registered": False, "error": f"relay_{status}", "body": raw[:300]}
    return {"email": email, "did": recipient_did, "registered": data.get("ok") is True, "alreadyExisted": data.get("alreadyExisted") is True}


def send_gewp_message(
    to: str = "",
    subject: str = "",
    text: str = "",
    html: str = "",
    from_: str = "",
    fromAddress: str = "",
    replyTo: str = "",
    gewp_thread_id: str = "",
    gewp_step: int = 0,
    gewp_payload: dict[str, Any] | None = None,
    gewp_to_role: str = "vertex",
    gewp_to_node: str = "",
    gewp_sender_did: str = "",
    gewp_performative: str = "inform",
    **kwargs: Any,
) -> dict[str, Any]:
    """Send a GEWP-conformant email (agent-to-agent or agent-to-human).

    Composes all 3 GEWP layers:
      Layer 1: application/vnd.gewp+json attachment (canonical)
      Layer 2: <!-- GEWP:{base64url} --> in HTML body (fallback)
      Layer 3: X-GEWP-* headers (best-effort routing hint)
    """
    sender = from_ or fromAddress or _str(kwargs.get("from")) or "mailer@etzhayyim.com"
    if not to or not subject:
        return {"error": "to/subject required"}
    api_key = _secret("RESEND_API_KEY", "SS_RESEND_API_KEY")
    if not api_key:
        return {"error": "RESEND_API_KEY not configured"}

    msg: GewpMessage = new_message(
        thread_id=gewp_thread_id or new_thread_id(),
        step=gewp_step,
        sender_id=f"https://{ACTOR.replace('did:web:', '')}",
        sender_email=sender,
        sender_did=gewp_sender_did or ACTOR,
        to_email=to,
        to_role=gewp_to_role,
        to_node=gewp_to_node,
        payload=gewp_payload or {},
        performative=gewp_performative,
        extensions=["ext:atproto"],
    )

    html_body = html or f"<p>{text}</p>"
    resend_payload = compose_resend_payload(
        sender=sender,
        to_addresses=[to],
        subject=subject,
        text_body=text,
        html_body=html_body,
        msg=msg,
        reply_to=replyTo,
    )

    status, data, raw = _http_json(
        "https://api.resend.com/emails",
        method="POST",
        headers={"authorization": f"Bearer {api_key}", "content-type": "application/json"},
        body=json.dumps(resend_payload).encode(),
    )
    message_id = _str(data.get("id"))
    sent_at = now_iso()
    try:
        _record_outbound(
            message_id, sender, to, subject, text, html_body,
            "resend", "sent" if status < 400 else "error",
            "" if status < 400 else raw[:500],
            gewp_thread_id=msg.thread.id,
            gewp_step=msg.thread.step,
        )
    except Exception:
        pass
    if status >= 400:
        return {"error": "resend_api_failed", "status": status, "body": raw[:500]}
    return {
        "messageId": message_id,
        "provider": "resend",
        "from": sender,
        "to": to,
        "subject": subject,
        "sentAt": sent_at,
        "gewpThreadId": msg.thread.id,
        "gewpStep": msg.thread.step,
    }


def parse_inbound_gewp(
    vertex_id: str = "",
    body_html: str = "",
    attachment_json: str = "",
    **_: Any,
) -> dict[str, Any]:
    """Extract GEWP payload from a stored inbound email record.

    Tries Layer 1 (attachment_json) then Layer 2 (HTML comment).
    Returns {'type': 'human.intent'} when neither layer is present.
    """
    msg = parse_from_email(
        attachment_json=attachment_json or None,
        html_body=body_html or None,
    )
    if msg is None:
        return {"type": "human.intent", "vertexId": vertex_id, "gewp": None}

    try:
        if vertex_id:
            _execute(
                """UPDATE vertex_mailer_inbound_email
                   SET gewp_thread_id=%s, gewp_step=%s, gewp_type=%s, gewp_performative=%s
                   WHERE vertex_id=%s""",
                (msg.thread.id, msg.thread.step, msg.type, msg.performative, vertex_id),
            )
    except Exception:
        pass

    return {
        "type": msg.type,
        "vertexId": vertex_id,
        "gewp": gewp_to_dict(msg),
    }


def handle_commit(collection: str = "", action: str = "", **_: Any) -> dict[str, Any]:
    if action and action != "create":
        return {"ok": True, "detail": "skip non-create"}
    if collection in (INBOUND_COLLECTION, "ai.gftd.apps.mailer.emailBinding"):
        return {"ok": True, "detail": f"processed {collection}"}
    return {"ok": True, "detail": "commit accepted"}


def heartbeat(**_: Any) -> dict[str, Any]:
    return {"ok": True, "actions": [{"action": "noop", "ts": now_iso()}]}
