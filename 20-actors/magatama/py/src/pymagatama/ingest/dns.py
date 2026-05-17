"""DNS / Cloudflare Registrar handlers for BPMN + Zeebe."""

from __future__ import annotations

import json
import re
import time
from typing import Any
from uuid import uuid4

from pymagatama.db_sync import sync_cursor

OWNER_DID = "did:web:scndu0rf.etzhayyim.com"
CF_REGISTRAR_DID = "did:web:scndu0rf.etzhayyim.com:actor:cfRegistrar"
SQ_EXPORTER_DID = "did:web:sqddf3sp.etzhayyim.com:actor:sqExporter"
DOMAIN_RE = re.compile(r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def today() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def _id(prefix: str = "dns") -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def _domain_slug(domain: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", domain.lower()).strip("_")


def _caller(kwargs: dict[str, Any]) -> str:
    for key in ("requesterDid", "callerDid", "did", "actorDid"):
        value = kwargs.get(key)
        if isinstance(value, str) and value:
            return value
    caller = kwargs.get("caller")
    if isinstance(caller, dict) and isinstance(caller.get("did"), str):
        return caller["did"]
    return OWNER_DID


def _fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in (cur.fetchall() or [])]


def _execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        return int(cur.rowcount or 0)


def ensure_cf_registrar_actor() -> None:
    _execute(
        """INSERT INTO vertex_actor
        (vertex_id, sensitivity_ord, owner_did, did, handle, display_name, name, execution_tier, performer_type, status, category, classification, operator, agent_type, runtime_type, ui_type, country, created_at)
        VALUES (%s,0,%s,%s,%s,%s,%s,'T1','service','active','infra','dns-registrar','gftd.co.jp','autonomous','worker','appview','jp',%s)
        ON CONFLICT (vertex_id) DO NOTHING""",
        (CF_REGISTRAR_DID, OWNER_DID, CF_REGISTRAR_DID, "cf-registrar-scndu0rf.etzhayyim.com", "Cloudflare Registrar Receiver", "Cloudflare Registrar Receiver", today()),
    )
    profile = {
        "displayName": "Cloudflare Registrar Receiver",
        "description": "Accepts inbound domain transfers and drives the Cloudflare Registrar API.",
        "isBot": True,
        "agentType": "autonomous",
    }
    _execute(
        """INSERT INTO vertex_actor_manifest
        (vertex_id, sensitivity_ord, owner_did, did, name, display_name, description, execution_tier, performer_type, profile_json, status, created_date)
        VALUES (%s,0,%s,%s,%s,%s,%s,'T1','service',%s,'active',%s::date)
        ON CONFLICT (vertex_id) DO NOTHING""",
        (CF_REGISTRAR_DID, OWNER_DID, CF_REGISTRAR_DID, "Cloudflare Registrar Receiver", "Cloudflare Registrar Receiver", "Cloudflare Registrar API receiver", json.dumps(profile, ensure_ascii=False), today()),
    )


def transfer_from_squarespace(**kwargs: Any) -> dict[str, Any]:
    ensure_cf_registrar_actor()
    domain = str(kwargs.get("domain") or "").strip().lower().rstrip(".")
    if not DOMAIN_RE.match(domain):
        return {"error": "domain required"}
    approvals = kwargs.get("approvals")
    approval_list = approvals if isinstance(approvals, list) else []
    approval_list = [str(a) for a in approval_list[:8] if a]
    status = "approved" if len(approval_list) >= 3 else "requested"
    rkey = _id("transfer")
    transfer_request_uri = f"at://{CF_REGISTRAR_DID}/ai.gftd.apps.dns.transferRequest/{rkey}"
    requested_at = now_iso()
    record = {
        "domain": domain,
        "fromRegistrar": "squarespace",
        "toRegistrar": "cloudflare",
        "requesterDid": _caller(kwargs),
        "cfRegistrarDid": CF_REGISTRAR_DID,
        "sqExporterDid": SQ_EXPORTER_DID,
        "projectConvoId": rkey,
        "status": status,
        "approvals": approval_list,
        "requestedAt": requested_at,
    }
    if kwargs.get("note"):
        record["note"] = str(kwargs.get("note"))[:512]
    _execute(
        """INSERT INTO vertex_atrecord_dns_transfer_request
        (vertex_id, _seq, owner_did, rkey, domain, from_registrar, to_registrar, requester_did, cf_registrar_did, sq_exporter_did, project_convo_id, status, approvals_json, requested_at, record_json)
        VALUES (%s, _next_seq('vertex_atrecord_dns_transfer_request'), %s, %s, %s, 'squarespace', 'cloudflare', %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (vertex_id) DO UPDATE SET status=EXCLUDED.status, approvals_json=EXCLUDED.approvals_json, record_json=EXCLUDED.record_json""",
        (transfer_request_uri, CF_REGISTRAR_DID, rkey, domain, record["requesterDid"], CF_REGISTRAR_DID, SQ_EXPORTER_DID, rkey, status, json.dumps(approval_list), requested_at, json.dumps(record, ensure_ascii=False, sort_keys=True)),
    )
    return {
        "transferRequestUri": transfer_request_uri,
        "transferRequestRkey": rkey,
        "status": status,
        "missingApprovals": max(0, 3 - len(approval_list)),
    }


def transfer_outcome(**kwargs: Any) -> dict[str, Any]:
    ensure_cf_registrar_actor()
    domain = str(kwargs.get("domain") or "").strip().lower().rstrip(".")
    result = str(kwargs.get("result") or "")
    if not DOMAIN_RE.match(domain):
        return {"error": "domain required"}
    if result not in {"success", "failure", "aborted"}:
        return {"error": "result must be success, failure, or aborted"}
    rkey = str(kwargs.get("rkey") or _id("outcome"))
    completed_at = str(kwargs.get("completedAt") or now_iso())
    zone_did = str(kwargs.get("zoneDid") or f"did:web:dns.etzhayyim.com:zone:{_domain_slug(domain)}")
    record = {
        "transferRequestUri": kwargs.get("transferRequestUri") or "",
        "domain": domain,
        "result": result,
        "zoneDid": zone_did if result == "success" else kwargs.get("zoneDid"),
        "cloudflareZoneId": kwargs.get("cloudflareZoneId"),
        "failureReason": kwargs.get("failureReason"),
        "rollbackSteps": kwargs.get("rollbackSteps") if isinstance(kwargs.get("rollbackSteps"), list) else [],
        "completedAt": completed_at,
    }
    _execute(
        """INSERT INTO vertex_atrecord_dns_transfer_outcome
        (vertex_id, _seq, owner_did, rkey, transfer_request_uri, domain, result, zone_did, cloudflare_zone_id, failure_reason, rollback_steps_json, completed_at, record_json)
        VALUES (%s, _next_seq('vertex_atrecord_dns_transfer_outcome'), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (vertex_id) DO UPDATE SET record_json=EXCLUDED.record_json""",
        (f"at://{CF_REGISTRAR_DID}/ai.gftd.apps.dns.transferOutcome/{rkey}", CF_REGISTRAR_DID, rkey, record["transferRequestUri"], domain, result, record.get("zoneDid"), record.get("cloudflareZoneId"), record.get("failureReason"), json.dumps(record["rollbackSteps"]), completed_at, json.dumps(record, ensure_ascii=False, sort_keys=True)),
    )
    if result != "success":
        return {"status": "recorded", "result": result, "domain": domain}
    _execute(
        """INSERT INTO vertex_actor
        (vertex_id, sensitivity_ord, owner_did, did, handle, display_name, name, execution_tier, performer_type, status, category, classification, operator, agent_type, runtime_type, ui_type, country, created_at)
        VALUES (%s,0,%s,%s,%s,%s,%s,'T1','service','active','dns-zone','cloudflare-zone','gftd.co.jp','logical','db-only','metadata-only','jp',%s)
        ON CONFLICT (vertex_id) DO NOTHING""",
        (zone_did, OWNER_DID, zone_did, f"{_domain_slug(domain)}.dns.etzhayyim.com", domain, domain, today()),
    )
    ownership_id = f"at://{CF_REGISTRAR_DID}/ai.gftd.apps.dns.ownershipTransfer/{_id('own')}"
    ownership = {
        "domain": domain,
        "fromRegistrar": "squarespace",
        "toRegistrar": "cloudflare",
        "transferDate": completed_at,
        "status": "completed",
        "zoneDid": zone_did,
    }
    _execute(
        """INSERT INTO vertex_atrecord_dns_ownership_transfer
        (vertex_id, _seq, owner_did, domain, from_registrar, to_registrar, zone_did, transfer_date, status, record_json)
        VALUES (%s, _next_seq('vertex_atrecord_dns_ownership_transfer'), %s, %s, 'squarespace', 'cloudflare', %s, %s, 'completed', %s)
        ON CONFLICT (vertex_id) DO NOTHING""",
        (ownership_id, CF_REGISTRAR_DID, domain, zone_did, completed_at, json.dumps(ownership, ensure_ascii=False, sort_keys=True)),
    )
    return {"status": "completed", "result": result, "domain": domain, "zoneDid": zone_did, "ownershipTransferUri": ownership_id}
