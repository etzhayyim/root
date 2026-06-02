#!/usr/bin/env python3
"""BPMN service-task worker for the My Number reference architecture.

The default adapter mode is mock. Real government connectors require separate
approval, credentials, private specifications, and security review.

TODO(substrate-boundary): replace RW writes (psycopg execute INSERT/UPDATE)
with AT Protocol MST writes via @etzhayyim/sdk per ADR-2605172000.
Collection: 'com.etzhayyim.apps.openJpnMynumber.personRef', rkey=person_id_hash.
Remove RW_URL env dependency when migration complete.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import secrets
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Iterable

try:
    import psycopg
    from psycopg.rows import dict_row
except Exception:  # noqa: BLE001
    psycopg = None
    dict_row = None


ROOT = Path(__file__).resolve().parent
ADAPTER_MODE = os.environ.get("OPEN_JPN_MYNUMBER_ADAPTER_MODE", "mock").strip().lower()
AGENTGATEWAY_MCP_URL = os.environ.get(
    "AGENTGATEWAY_MCP_URL",
    "http://agentgateway-mcp.mitama-udf.svc.cluster.local:8080",
)
RW_URL = os.environ.get("RW_URL") or os.environ.get("DATABASE_URL")


async def serve_langserver(tasks: dict[str, Callable[..., Any]]) -> None:
    port = int(os.environ.get("PORT", "8080"))

    class Handler(BaseHTTPRequestHandler):
        def _json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/healthz":
                self._json(200, {"ok": True, "runtimeKind": "k8s-langserver", "agentGatewayMcpUrl": AGENTGATEWAY_MCP_URL})
            elif self.path == "/tools":
                self._json(200, {"tools": [{"name": name, "runtime": "langserver"} for name in sorted(tasks)]})
            else:
                self._json(404, {"error": "not found"})

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            name = str(payload.get("name") or payload.get("tool") or payload.get("assistant_id") or "")
            arguments = payload.get("arguments") or payload.get("input") or {}
            handler = tasks.get(name)
            if handler is None:
                self._json(404, {"error": f"unknown tool: {name}"})
                return
            result = asyncio.run(handler(**arguments))
            self._json(200, {"ok": True, "name": name, "result": result})

    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    await asyncio.to_thread(server.serve_forever)


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(12).replace('-', '').replace('_', '')[:16]}"


class GraphConnection:
    def __init__(self, url: str):
        if psycopg is None or dict_row is None:
            raise RuntimeError("RW_URL is set but psycopg is not installed")
        self._con = psycopg.connect(url, row_factory=dict_row)

    def __enter__(self) -> "GraphConnection":
        self._con.__enter__()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self._con.__exit__(exc_type, exc, tb)

    def execute(self, query: str, params: Iterable[Any] | dict[str, Any] | None = None) -> Any:
        if isinstance(params, dict):
            query = re.sub(r":([A-Za-z_][A-Za-z0-9_]*)", r"%(\1)s", query)
        elif params is not None:
            query = query.replace("?", "%s")
        return self._con.execute(query, params)


def db() -> GraphConnection:
    if not RW_URL:
        raise RuntimeError("RW_URL or DATABASE_URL is required; SQLite fallback was retired in favor of Kysely/RisingWave")
    return GraphConnection(str(RW_URL))


def init_db() -> None:
    # DDL is managed by graph-schema Kysely migrations:
    # - 20260427003000_vertex_open_jpn_mynumber.ts
    # - 20260427033000_open_jpn_mynumber_application_medical.ts
    return


def audit(event_type: str, result: str, payload: dict[str, Any]) -> dict[str, Any]:
    init_db()
    event_id = new_id("vertex_evt")
    row = {
        "vertex_id": event_id,
        "event_type": event_type,
        "person_ref": payload.get("person_ref"),
        "requester_agency": payload.get("requester_agency"),
        "holder_agency": payload.get("holder_agency"),
        "purpose_code": payload.get("purpose_code"),
        "dataset_code": payload.get("dataset_code"),
        "result": result,
        "payload_json": json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        "created_at": now_iso(),
    }
    with db() as con:
        con.execute(
            """
            INSERT INTO vertex_open_jpn_mynumber_audit_event (
              vertex_id,event_type,person_ref,requester_agency,holder_agency,
              purpose_code,dataset_code,result,payload_json,created_at
            ) VALUES (
              :vertex_id,:event_type,:person_ref,:requester_agency,:holder_agency,
              :purpose_code,:dataset_code,:result,:payload_json,:created_at
            )
            """,
            row,
        )
        for ref_kind, ref_value in (
            ("person_ref", row["person_ref"]),
            ("requester_agency", row["requester_agency"]),
            ("holder_agency", row["holder_agency"]),
        ):
            if ref_value:
                con.execute(
                    """
                    INSERT INTO edge_open_jpn_mynumber_event_subject (
                      edge_id,from_vertex_id,to_ref,to_ref_kind,edge_type,created_at
                    ) VALUES (?,?,?,?,?,?)
                    """,
                    (new_id("edge_evt"), event_id, ref_value, ref_kind, "audits", row["created_at"]),
                )
    return {"audit_event_vertex_id": event_id, "audited_at": row["created_at"]}


def require_fields(payload: dict[str, Any], fields: list[str]) -> None:
    missing = [field for field in fields if not str(payload.get(field, "")).strip()]
    if missing:
        raise ValueError(f"missing required field(s): {', '.join(missing)}")


def ensure_mock_mode() -> None:
    if ADAPTER_MODE != "mock":
        raise RuntimeError("real adapter mode is not implemented in this scaffold")


async def verify_jpki(**payload: Any) -> dict[str, Any]:
    require_fields(payload, ["person_ref", "purpose_code"])
    ensure_mock_mode()
    cert_material = str(payload.get("certificate_pem") or payload.get("certificate_serial") or "mock")
    fingerprint = stable_hash(cert_material)
    result = {
        "person_ref": payload["person_ref"],
        "certificate_fingerprint": fingerprint,
        "certificate_status": "valid",
        "verification_method": "mock-ocsp",
        "checked_at": now_iso(),
    }
    result.update(audit("jpki.verify", "valid", {**payload, **result}))
    return result


async def register_person(**payload: Any) -> dict[str, Any]:
    require_fields(payload, ["person_ref", "agency_code", "subject_token"])
    alias_id = new_id("vertex_alias")
    alias_hash = stable_hash(str(payload["subject_token"]))
    init_db()
    with db() as con:
        insert_sql = """
            INSERT INTO vertex_open_jpn_mynumber_agency_alias (
              vertex_id,person_ref,agency_code,alias_kind,alias_value_hash,created_at
            ) VALUES (?,?,?,?,?,?)
        """
        con.execute(
            insert_sql,
            (
                alias_id,
                payload["person_ref"],
                payload["agency_code"],
                payload.get("alias_kind", "subject_token"),
                alias_hash,
                now_iso(),
            ),
        )
    result = {"person_ref": payload["person_ref"], "agency_alias_hash": alias_hash}
    result.update(audit("person.register", "registered", {**payload, **result}))
    return result


async def lookup_nonresident_address(**payload: Any) -> dict[str, Any]:
    require_fields(payload, ["requester_agency", "purpose_code", "search_token"])
    ensure_mock_mode()
    found = str(payload["search_token"]).startswith("known:")
    result = {
        "match_found": found,
        "candidate_count": 1 if found else 0,
        "address_ref": f"addr_{stable_hash(str(payload['search_token']))[:16]}" if found else None,
    }
    result.update(audit("nonresident.lookup", "found" if found else "not_found", {**payload, **result}))
    return result


async def assign_nonresident_address(**payload: Any) -> dict[str, Any]:
    require_fields(payload, ["person_ref", "requester_agency", "purpose_code"])
    address_ref = payload.get("address_ref") or new_id("addr")
    result = {"person_ref": payload["person_ref"], "address_ref": address_ref, "assigned": True}
    result.update(audit("nonresident.assign", "assigned", {**payload, **result}))
    return result


async def create_consent_session(**payload: Any) -> dict[str, Any]:
    require_fields(payload, ["person_ref", "requester_agency", "purpose_code", "scope"])
    consent_id = new_id("cns")
    expires_at = (datetime.now(UTC) + timedelta(minutes=int(payload.get("ttl_minutes", 30)))).replace(microsecond=0).isoformat()
    init_db()
    with db() as con:
        con.execute(
            """
            INSERT INTO vertex_open_jpn_mynumber_consent_receipt (
              vertex_id,person_ref,requester_agency,purpose_code,scope_json,
              expires_at,created_at
            ) VALUES (?,?,?,?,?,?,?)
            """,
            (
                consent_id,
                payload["person_ref"],
                payload["requester_agency"],
                payload["purpose_code"],
                json.dumps(payload["scope"], ensure_ascii=False, separators=(",", ":")),
                expires_at,
                now_iso(),
            ),
        )
    result = {"consent_id": consent_id, "status": "pending-user-auth", "expires_at": expires_at}
    result.update(audit("consent.create", "pending", {**payload, **result}))
    return result


async def broker_information_request(**payload: Any) -> dict[str, Any]:
    require_fields(payload, ["person_ref", "requester_agency", "holder_agency", "purpose_code", "dataset_code"])
    if not payload.get("consent_id") and payload.get("requires_consent", True):
        result = {"approved": False, "reason": "missing-consent"}
        result.update(audit("info.request", "denied", {**payload, **result}))
        return result
    ensure_mock_mode()
    response_ref = f"payload_{stable_hash(json.dumps(payload, sort_keys=True, default=str))[:20]}"
    result = {
        "approved": True,
        "response_ref": response_ref,
        "classification": "special-personal-information",
        "data_inline": None,
    }
    result.update(audit("info.request", "approved", {**payload, **result}))
    return result


async def disclose_self_information(**payload: Any) -> dict[str, Any]:
    require_fields(payload, ["person_ref", "purpose_code"])
    init_db()
    with db() as con:
        rows = con.execute(
            """
            SELECT vertex_id,event_type,requester_agency,holder_agency,purpose_code,
                   dataset_code,result,created_at
            FROM vertex_open_jpn_mynumber_audit_event
            WHERE person_ref = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (payload["person_ref"], int(payload.get("limit", 50))),
        ).fetchall()
    result = {"history": [dict(row) for row in rows]}
    result.update(audit("self.disclose", "returned", {**payload, "dataset_code": "provision_history"}))
    return result


async def issue_oauth_token(**payload: Any) -> dict[str, Any]:
    require_fields(payload, ["requester_agency", "client_id", "purpose_code", "scope"])
    ensure_mock_mode()
    scope = payload["scope"] if isinstance(payload["scope"], list) else [str(payload["scope"])]
    token_ref = new_id("vertex_tok")
    expires_at = (datetime.now(UTC) + timedelta(minutes=int(payload.get("ttl_minutes", 60)))).replace(microsecond=0).isoformat()
    init_db()
    with db() as con:
        con.execute(
            """
            INSERT INTO vertex_open_jpn_mynumber_oauth_token (
              vertex_id,requester_agency,client_id_hash,scope_json,purpose_code,
              active,expires_at,created_at
            ) VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                token_ref,
                payload["requester_agency"],
                stable_hash(str(payload["client_id"])),
                json.dumps(scope, ensure_ascii=False, separators=(",", ":")),
                payload["purpose_code"],
                True,
                expires_at,
                now_iso(),
            ),
        )
    result = {
        "token_ref": token_ref,
        "token_type": "Bearer",
        "scope": scope,
        "active": True,
        "expires_at": expires_at,
    }
    result.update(audit("oauth.issue", "issued", {**payload, **result, "client_id": "<redacted>"}))
    return result


async def introspect_oauth_token(**payload: Any) -> dict[str, Any]:
    require_fields(payload, ["token_ref", "requester_agency", "purpose_code"])
    init_db()
    with db() as con:
        row = con.execute(
            "SELECT * FROM mv_open_jpn_mynumber_oauth_token_status WHERE token_ref = ?",
            (payload["token_ref"],),
        ).fetchone()
    if not row:
        result = {"token_ref": payload["token_ref"], "active": False, "reason": "not-found"}
        result.update(audit("oauth.introspect", "inactive", {**payload, **result}))
        return result
    active = row["status"] == "active" and row["expires_at"] > now_iso()
    result = {
        "token_ref": row["token_ref"],
        "requester_agency": row["requester_agency"],
        "scope": json.loads(row["scope_json"]),
        "active": active,
        "status": row["status"],
        "expires_at": row["expires_at"],
        "revoked_at": row["revoked_at"],
    }
    result.update(audit("oauth.introspect", "active" if active else "inactive", {**payload, **result}))
    return result


async def revoke_oauth_token(**payload: Any) -> dict[str, Any]:
    require_fields(payload, ["token_ref", "requester_agency", "purpose_code"])
    init_db()
    revoked_at = now_iso()
    with db() as con:
        cur = con.execute(
            "UPDATE vertex_open_jpn_mynumber_oauth_token SET active = ?, revoked_at = ? WHERE vertex_id = ?",
            (False, revoked_at, payload["token_ref"]),
        )
    result = {"token_ref": payload["token_ref"], "revoked": cur.rowcount > 0, "revoked_at": revoked_at}
    result.update(audit("oauth.revoke", "revoked" if result["revoked"] else "not-found", {**payload, **result}))
    return result


def normalize_file_manifest(payload: dict[str, Any]) -> list[dict[str, Any]]:
    files = payload.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("files must be a non-empty array")
    normalized = []
    for idx, item in enumerate(files):
        if not isinstance(item, dict):
            raise ValueError(f"files[{idx}] must be an object")
        for field in ("name", "sha256", "bytes"):
            if field not in item:
                raise ValueError(f"files[{idx}].{field} is required")
        normalized.append({
            "name": str(item["name"]),
            "sha256": str(item["sha256"]).lower(),
            "bytes": int(item["bytes"]),
            "media_type": str(item.get("media_type") or "application/octet-stream"),
        })
    return normalized


async def validate_file_manifest(**payload: Any) -> dict[str, Any]:
    require_fields(payload, ["requester_agency", "purpose_code"])
    files = normalize_file_manifest(payload)
    manifest_hash = stable_hash(json.dumps(files, sort_keys=True, separators=(",", ":")))
    manifest_vertex_id = f"vertex_manifest_{manifest_hash[:24]}"
    init_db()
    with db() as con:
        insert_sql = """
            INSERT INTO vertex_open_jpn_mynumber_file_manifest (
              vertex_id,requester_agency,purpose_code,file_manifest_hash,
              file_count,total_bytes,manifest_json,created_at
            ) VALUES (?,?,?,?,?,?,?,?)
        """
        con.execute(
            insert_sql,
            (
                manifest_vertex_id,
                payload["requester_agency"],
                payload["purpose_code"],
                manifest_hash,
                len(files),
                sum(item["bytes"] for item in files),
                json.dumps(files, ensure_ascii=False, separators=(",", ":")),
                now_iso(),
            ),
        )
    result = {
        "valid": True,
        "file_manifest_vertex_id": manifest_vertex_id,
        "file_count": len(files),
        "total_bytes": sum(item["bytes"] for item in files),
        "file_manifest_hash": manifest_hash,
    }
    result.update(audit("file.manifest.validate", "valid", {**payload, **result}))
    return result


async def register_file_transfer(**payload: Any) -> dict[str, Any]:
    require_fields(payload, ["requester_agency", "purpose_code", "file_manifest_hash"])
    transfer_id = payload.get("transfer_id") or new_id("vertex_xfer")
    now = now_iso()
    init_db()
    with db() as con:
        transfer_sql = """
            INSERT INTO vertex_open_jpn_mynumber_file_transfer (
              vertex_id,requester_agency,holder_agency,purpose_code,
              file_manifest_hash,file_count,status,created_at,updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?)
        """
        con.execute(
            transfer_sql,
            (
                transfer_id,
                payload["requester_agency"],
                payload.get("holder_agency"),
                payload["purpose_code"],
                payload["file_manifest_hash"],
                int(payload.get("file_count", 0)),
                "registered",
                now,
                now,
            ),
        )
        manifest = con.execute(
            "SELECT vertex_id FROM vertex_open_jpn_mynumber_file_manifest WHERE file_manifest_hash = ?",
            (payload["file_manifest_hash"],),
        ).fetchone()
        if manifest:
            edge_sql = """
                INSERT INTO edge_open_jpn_mynumber_transfer_manifest (
                  edge_id,from_vertex_id,to_vertex_id,edge_type,created_at
                ) VALUES (?,?,?,?,?)
            """
            con.execute(
                edge_sql,
                (new_id("edge_xfer_manifest"), transfer_id, manifest["vertex_id"], "uses_manifest", now),
            )
    result = {"transfer_id": transfer_id, "status": "registered", "registered_at": now}
    result.update(audit("file.transfer.register", "registered", {**payload, **result}))
    return result


async def poll_file_transfer_status(**payload: Any) -> dict[str, Any]:
    require_fields(payload, ["transfer_id", "requester_agency", "purpose_code"])
    init_db()
    with db() as con:
        row = con.execute(
            "SELECT * FROM mv_open_jpn_mynumber_file_transfer_status WHERE transfer_id = ?",
            (payload["transfer_id"],),
        ).fetchone()
    if not row:
        result = {"transfer_id": payload["transfer_id"], "status": "not-found"}
        result.update(audit("file.transfer.status", "not-found", {**payload, **result}))
        return result
    result = {
        "transfer_id": row["transfer_id"],
        "status": row["status"],
        "file_manifest_hash": row["file_manifest_hash"],
        "file_manifest_vertex_id": row["file_manifest_vertex_id"],
        "file_count": row["file_count"],
        "total_bytes": row["total_bytes"],
        "updated_at": row["updated_at"],
    }
    result.update(audit("file.transfer.status", row["status"], {**payload, **result}))
    return result


async def submit_electronic_application(**payload: Any) -> dict[str, Any]:
    require_fields(payload, ["person_ref", "requester_agency", "procedure_code", "purpose_code"])
    ensure_mock_mode()
    application_payload = payload.get("application_payload") or {}
    payload_hash = stable_hash(json.dumps(application_payload, ensure_ascii=False, sort_keys=True, default=str))
    application_id = payload.get("application_id") or new_id("vertex_app")
    now = now_iso()
    external_reference = f"myna_app_{stable_hash(application_id)[:18]}"
    init_db()
    with db() as con:
        app_sql = """
            INSERT INTO vertex_open_jpn_mynumber_electronic_application (
              vertex_id,person_ref,requester_agency,procedure_code,purpose_code,
              application_payload_hash,status,external_reference,submitted_at,updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?)
        """
        con.execute(
            app_sql,
            (
                application_id,
                payload["person_ref"],
                payload["requester_agency"],
                payload["procedure_code"],
                payload["purpose_code"],
                payload_hash,
                "submitted",
                external_reference,
                now,
                now,
            ),
        )
        if payload.get("consent_id"):
            edge_sql = """
                INSERT INTO edge_open_jpn_mynumber_request_consent (
                  edge_id,from_vertex_id,to_vertex_id,edge_type,created_at
                ) VALUES (?,?,?,?,?)
            """
            con.execute(edge_sql, (new_id("edge_app_consent"), application_id, payload["consent_id"], "authorized_by", now))
    result = {
        "application_id": application_id,
        "status": "submitted",
        "external_reference": external_reference,
        "application_payload_hash": payload_hash,
        "submitted_at": now,
    }
    result.update(audit("electronic_application.submit", "submitted", {**payload, **result}))
    return result


async def get_electronic_application_status(**payload: Any) -> dict[str, Any]:
    require_fields(payload, ["application_id", "requester_agency", "purpose_code"])
    init_db()
    with db() as con:
        row = con.execute(
            "SELECT * FROM mv_open_jpn_mynumber_electronic_application_status WHERE application_id = ?",
            (payload["application_id"],),
        ).fetchone()
    if not row:
        result = {"application_id": payload["application_id"], "status": "not-found"}
        result.update(audit("electronic_application.status", "not-found", {**payload, **result}))
        return result
    result = {
        "application_id": row["application_id"],
        "person_ref": row["person_ref"],
        "procedure_code": row["procedure_code"],
        "purpose_code": row["purpose_code"],
        "status": row["status"],
        "external_reference": row["external_reference"],
        "updated_at": row["updated_at"],
    }
    result.update(audit("electronic_application.status", row["status"], {**payload, **result}))
    return result


async def request_medical_info(**payload: Any) -> dict[str, Any]:
    require_fields(payload, ["person_ref", "requester_agency", "purpose_code", "dataset_code"])
    if not payload.get("consent_id") and payload.get("requires_consent", True):
        result = {"medical_request_id": None, "status": "denied", "reason": "missing-consent"}
        result.update(audit("medical_info.request", "denied", {**payload, **result}))
        return result
    ensure_mock_mode()
    request_id = payload.get("medical_request_id") or new_id("vertex_med")
    now = now_iso()
    response_ref = f"pmh_{stable_hash(json.dumps(payload, sort_keys=True, default=str))[:20]}"
    init_db()
    with db() as con:
        req_sql = """
            INSERT INTO vertex_open_jpn_mynumber_medical_info_request (
              vertex_id,person_ref,requester_agency,purpose_code,dataset_code,
              consent_id,status,response_ref,requested_at,updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?)
        """
        con.execute(
            req_sql,
            (
                request_id,
                payload["person_ref"],
                payload["requester_agency"],
                payload["purpose_code"],
                payload["dataset_code"],
                payload.get("consent_id"),
                "available",
                response_ref,
                now,
                now,
            ),
        )
        if payload.get("consent_id"):
            edge_sql = """
                INSERT INTO edge_open_jpn_mynumber_request_consent (
                  edge_id,from_vertex_id,to_vertex_id,edge_type,created_at
                ) VALUES (?,?,?,?,?)
            """
            con.execute(edge_sql, (new_id("edge_med_consent"), request_id, payload["consent_id"], "authorized_by", now))
    result = {"medical_request_id": request_id, "status": "available", "response_ref": response_ref, "requested_at": now}
    result.update(audit("medical_info.request", "available", {**payload, **result}))
    return result


async def get_medical_info_status(**payload: Any) -> dict[str, Any]:
    require_fields(payload, ["medical_request_id", "requester_agency", "purpose_code"])
    init_db()
    with db() as con:
        row = con.execute(
            "SELECT * FROM mv_open_jpn_mynumber_medical_info_status WHERE medical_request_id = ?",
            (payload["medical_request_id"],),
        ).fetchone()
    if not row:
        result = {"medical_request_id": payload["medical_request_id"], "status": "not-found"}
        result.update(audit("medical_info.status", "not-found", {**payload, **result}))
        return result
    result = {
        "medical_request_id": row["medical_request_id"],
        "person_ref": row["person_ref"],
        "purpose_code": row["purpose_code"],
        "dataset_code": row["dataset_code"],
        "status": row["status"],
        "response_ref": row["response_ref"],
        "updated_at": row["updated_at"],
    }
    result.update(audit("medical_info.status", row["status"], {**payload, **result}))
    return result


TASKS: dict[str, Callable[..., Any]] = {
    "com.etzhayyim.apps.openJpnMynumber.verifyJpki": verify_jpki,
    "com.etzhayyim.apps.openJpnMynumber.registerPerson": register_person,
    "com.etzhayyim.apps.openJpnMynumber.lookupNonresidentAddress": lookup_nonresident_address,
    "com.etzhayyim.apps.openJpnMynumber.assignNonresidentAddress": assign_nonresident_address,
    "com.etzhayyim.apps.openJpnMynumber.createConsentSession": create_consent_session,
    "com.etzhayyim.apps.openJpnMynumber.brokerInformationRequest": broker_information_request,
    "com.etzhayyim.apps.openJpnMynumber.discloseSelfInformation": disclose_self_information,
    "com.etzhayyim.apps.openJpnMynumber.issueOauthToken": issue_oauth_token,
    "com.etzhayyim.apps.openJpnMynumber.introspectOauthToken": introspect_oauth_token,
    "com.etzhayyim.apps.openJpnMynumber.revokeOauthToken": revoke_oauth_token,
    "com.etzhayyim.apps.openJpnMynumber.validateFileManifest": validate_file_manifest,
    "com.etzhayyim.apps.openJpnMynumber.registerFileTransfer": register_file_transfer,
    "com.etzhayyim.apps.openJpnMynumber.pollFileTransferStatus": poll_file_transfer_status,
    "com.etzhayyim.apps.openJpnMynumber.submitElectronicApplication": submit_electronic_application,
    "com.etzhayyim.apps.openJpnMynumber.getElectronicApplicationStatus": get_electronic_application_status,
    "com.etzhayyim.apps.openJpnMynumber.requestMedicalInfo": request_medical_info,
    "com.etzhayyim.apps.openJpnMynumber.getMedicalInfoStatus": get_medical_info_status,
}


async def serve() -> None:
    await serve_langserver(TASKS)


async def run_task(task_type: str, payload_json: str) -> dict[str, Any]:
    if task_type not in TASKS:
        raise ValueError(f"unknown task type: {task_type}")
    payload = json.loads(payload_json)
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    return await TASKS[task_type](**payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--init-db", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="initialize and exit")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("serve")
    for task_type in TASKS:
        cmd = task_type.rsplit(".", 1)[-1]
        p = sub.add_parser(cmd)
        p.add_argument("payload_json")
    args = parser.parse_args()

    if args.init_db:
        init_db()
    if args.dry_run:
# CHARTER-VIOLATION §substrate (centralized DB forbidden — migrate to AT MST + IPFS + Base L2)
        print(json.dumps({"ok": True, "db": "kysely-risingwave", "url_env": "RW_URL|DATABASE_URL"}, ensure_ascii=False))
        return 0
    if args.command == "serve":
        asyncio.run(serve())
        return 0
    if args.command:
        task_type = f"com.etzhayyim.apps.openJpnMynumber.{args.command}"
        result = asyncio.run(run_task(task_type, args.payload_json))
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return 0
    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
