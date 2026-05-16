"""kouza.gftd.ai resident scheduler and MCP-facing control handlers."""

from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from datetime import UTC, datetime
from typing import Any

from pymagatama import udf
from pymagatama.db_sync import sync_cursor

NS = "ai.gftd.apps.kouza"


def _dump(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _loads(params_json: str) -> dict[str, Any]:
    if not params_json:
        return {}
    data = json.loads(params_json)
    if not isinstance(data, dict):
        raise ValueError("JSON body must be an object")
    return data


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _record_did(owner_did: str, collection: str, rkey: str) -> str:
    return f"at://{owner_did}/{collection}/{rkey}"


def _core_sync_endpoint() -> str:
    base = os.environ.get("KOUZA_CORE_URL", "").strip().rstrip("/")
    if not base:
        return ""
    return f"{base}/xrpc/{NS}.syncConnection"


def _call_core_sync(connection_did: str, owner_did: str, timeout_sec: float = 20.0) -> dict[str, Any]:
    url = _core_sync_endpoint()
    if not url:
        return {}
    payload = json.dumps(
        {"connectionDid": connection_did, "ownerDid": owner_did},
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/129.0.0.0 Safari/537.36"
        ),
    }
    bearer = os.environ.get("KOUZA_CORE_BEARER", "").strip()
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            raw = resp.read(65536).decode("utf-8", errors="replace")
            data = json.loads(raw) if raw else {}
            if not isinstance(data, dict):
                raise ValueError("kouza-core response must be a JSON object")
            data["_httpStatus"] = resp.status
            return data
    except urllib.error.HTTPError as e:
        body = e.read(4096).decode("utf-8", errors="replace")
        raise RuntimeError(f"kouza-core HTTP {e.code}: {body[:500]}") from e


def _int_param(params: dict[str, Any], key: str, default: int, minimum: int, maximum: int) -> int:
    raw = params.get(key, default)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ValueError(f"{key} must be an integer") from None
    if value < minimum or value > maximum:
        raise ValueError(f"{key} must be between {minimum} and {maximum}")
    return value


def _select_due_connections(owner_did: str, stale_minutes: int, limit: int) -> list[tuple[str, str, str]]:
    where_owner = "AND c.owner_did = %s" if owner_did else ""
    params: list[Any] = []
    if owner_did:
        params.append(owner_did)
    params.append(stale_minutes)
    safe_limit = max(1, min(200, int(limit)))
    sql = f"""
        SELECT c.vertex_id, c.owner_did, c.provider_key
        FROM vertex_atrecord_kouza_institution_connection c
        WHERE c.status = 'active'
          {where_owner}
          AND NOT EXISTS (
            SELECT 1
            FROM vertex_atrecord_kouza_sync_run r
            WHERE r.connection_did = c.vertex_id
              AND r.started_at > (NOW() - (%s * INTERVAL '1 minute'))
        )
        ORDER BY c.updated_at NULLS FIRST, c.created_at ASC
        LIMIT {safe_limit}
    """
    with sync_cursor() as cur:
        cur.execute(sql, tuple(params))
        return list(cur.fetchall())


def sync_due_connections_payload(params: dict[str, Any]) -> dict[str, Any]:
    owner_did = str(params.get("ownerDid") or "").strip()
    if owner_did and not owner_did.startswith("did:"):
        raise ValueError("ownerDid must be a DID")
    limit = _int_param(params, "maxConnections", 25, 1, 200)
    stale_minutes = _int_param(params, "staleMinutes", 60, 1, 10080)
    dry_run = bool(params.get("dryRun") or False)

    rows = _select_due_connections(owner_did, stale_minutes, limit)
    if dry_run:
        return {
            "ok": True,
            "dryRun": True,
            "adapterMode": "kouza-core" if _core_sync_endpoint() else "local-pending",
            "connectionsScanned": len(rows),
            "syncRunsCreated": 0,
            "syncRunDids": [],
        }

    if _core_sync_endpoint():
        sync_run_dids: list[str] = []
        for connection_did, row_owner_did, _provider_key in rows:
            result = _call_core_sync(connection_did, row_owner_did)
            sync_run_did = str(result.get("syncRunDid") or "")
            if sync_run_did:
                sync_run_dids.append(sync_run_did)
        return {
            "ok": True,
            "dryRun": False,
            "adapterMode": "kouza-core",
            "connectionsScanned": len(rows),
            "syncRunsCreated": len(sync_run_dids),
            "syncRunDids": sync_run_dids,
        }

    now = _now_iso()
    sync_run_dids: list[str] = []
    with sync_cursor() as cur:
        cur.execute("SELECT COALESCE(MAX(_seq), 0) + 1 FROM vertex_atrecord_kouza_sync_run")
        seq = int(cur.fetchone()[0])
        for idx, (connection_did, row_owner_did, provider_key) in enumerate(rows):
            rkey = f"sync-zeebe-{_hash({'connectionDid': connection_did, 'now': now, 'idx': idx})}"
            sync_run_did = _record_did(row_owner_did, f"{NS}.syncRun", rkey)
            cur.execute(
                """
                INSERT INTO vertex_atrecord_kouza_sync_run (
                  vertex_id, _seq, owner_did, rkey, connection_did, adapter_key,
                  started_at, finished_at, accounts_imported, transactions_imported,
                  documents_imported, status, error_code, error_message, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0, 0, 0, %s, %s, %s, %s)
                """,
                (
                    sync_run_did,
                    seq + idx,
                    row_owner_did,
                    rkey,
                    connection_did,
                    provider_key or "zeebe-python-resident",
                    now,
                    now,
                    "adapter_pending",
                    "ADAPTER_NOT_CONFIGURED",
                    "Resident Zeebe/Python scheduler recorded a due sync; provider adapter is not configured yet.",
                    now,
                ),
            )
            cur.execute(
                """
                UPDATE vertex_atrecord_kouza_institution_connection
                SET last_sync_run_did = %s, updated_at = %s
                WHERE vertex_id = %s
                """,
                (sync_run_did, now, connection_did),
            )
            sync_run_dids.append(sync_run_did)

    return {
        "ok": True,
        "dryRun": False,
        "adapterMode": "local-pending",
        "connectionsScanned": len(rows),
        "syncRunsCreated": len(sync_run_dids),
        "syncRunDids": sync_run_dids,
    }


@udf(
    nsid="ai.gftd.apps.kouza.syncDueConnections",
    io_threads=16,
    input_types=["VARCHAR"],
    result_type="VARCHAR",
    capability_tags=("kouza", "sync", "scheduler", "mcp"),
    agent_tool="Scan due kouza institution connections and record resident syncRun audit rows.",
)
def kouza_sync_due_connections(params_json: str) -> str:
    try:
        return _dump(sync_due_connections_payload(_loads(params_json)))
    except (ValueError, json.JSONDecodeError) as e:
        return _dump({"ok": False, "error": str(e), "connectionsScanned": 0, "syncRunsCreated": 0})
    except Exception as e:  # noqa: BLE001
        return _dump(
            {
                "ok": False,
                "error": f"kouza.syncDueConnections failed: {e}",
                "connectionsScanned": 0,
                "syncRunsCreated": 0,
            }
        )
