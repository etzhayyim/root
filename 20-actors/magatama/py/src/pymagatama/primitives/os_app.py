"""GFTD OS XRPC primitives for BPMN/LangServer."""

from __future__ import annotations

import datetime as _dt
import decimal as _decimal
import json
import time
import uuid
from typing import Any

from pymagatama.db_sync import sync_cursor


OS_DID = "did:web:os.etzhayyim.com"
APP_ID = "os"


def _now() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _id(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1000):x}-{uuid.uuid4().hex[:8]}"


def _jsonable(v: Any) -> Any:
    if isinstance(v, (_dt.datetime, _dt.date)):
        return v.isoformat()
    if isinstance(v, _decimal.Decimal):
        f = float(v)
        return int(f) if f.is_integer() else f
    return v


def _rows(cur: Any) -> list[dict[str, Any]]:
    cols = [d[0] for d in (cur.description or [])]
    out: list[dict[str, Any]] = []
    for row in cur.fetchall():
        raw = {cols[i]: _jsonable(row[i]) for i in range(len(cols))}
        props = raw.get("value_json") or raw.get("props")
        if isinstance(props, str) and props:
            try:
                parsed = json.loads(props)
                if isinstance(parsed, dict):
                    raw = {**parsed, **raw}
            except json.JSONDecodeError:
                pass
        aliases = {
            "vertex_id": "vertexId",
            "agent_id": "agentId",
            "app_id": "appId",
            "config_json": "config",
            "created_at": "createdAt",
            "updated_at": "updatedAt",
            "request_id": "requestId",
            "agent_did": "agentDid",
            "risk_tier": "riskTier",
            "estimated_cost": "estimatedCost",
            "context_json": "context",
            "expires_at": "expiresAt",
            "tags_json": "tags",
            "data_size": "dataSize",
            "window_id": "windowId",
            "content_type": "contentType",
            "content_url": "contentUrl",
        }
        for src, dst in aliases.items():
            if src in raw and dst not in raw:
                raw[dst] = raw[src]
        out.append(raw)
    return out


def _insert(collection: str, record: dict[str, Any], *, label: str = "", status: str = "") -> dict[str, Any]:
    record_kind = collection.rsplit(".", 1)[-1]
    rkey = str(record.get("agentId") or record.get("requestId") or record.get("windowId") or record.get("did") or _id("os"))[:64]
    now = str(record.get("created_at") or _now())
    vertex_id = f"at://{OS_DID}/{collection}/{rkey}"
    value = {**record, "vertexId": vertex_id, "rkey": rkey, "collection": collection, "label": label, "status": status or str(record.get("status") or "")}
    with sync_cursor() as cur:
        common = (str(record.get("org_id") or "anon"), str(record.get("user_id") or "anon"), str(record.get("actor_id") or APP_ID), OS_DID, 2)
        if record_kind == "agent":
            cur.execute(
                """
                INSERT INTO vertex_os_agent
                  (vertex_id,agent_id,did,app_id,name,status,config_json,created_at,updated_at,org_id,user_id,actor_id,owner_did,sensitivity_ord)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (vertex_id) DO UPDATE SET status=EXCLUDED.status, updated_at=EXCLUDED.updated_at, config_json=EXCLUDED.config_json
                """,
                (vertex_id, rkey, str(record.get("did") or ""), str(record.get("appId") or ""), str(record.get("name") or label), str(record.get("status") or status), str(record.get("config") or "{}"), now, str(record.get("updated_at") or now), *common),
            )
        elif record_kind == "agentEvent":
            cur.execute(
                """
                INSERT INTO vertex_os_agent_event
                  (vertex_id,agent_id,event,target,created_at,org_id,user_id,actor_id,owner_did,sensitivity_ord)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (vertex_id) DO UPDATE SET event=EXCLUDED.event, target=EXCLUDED.target
                """,
                (vertex_id, str(record.get("agentId") or ""), str(record.get("event") or ""), str(record.get("target") or ""), now, *common),
            )
            cur.execute(
                "INSERT INTO edge_os_agent_event (edge_id,src_vid,dst_vid,agent_id,relation,created_at,owner_did,sensitivity_ord) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (edge_id) DO NOTHING",
                (f"{OS_DID}:agent:{record.get('agentId')}:EVENT:{rkey}", f"at://{OS_DID}/ai.gftd.apps.os.agent/{record.get('agentId')}", vertex_id, str(record.get("agentId") or ""), str(record.get("event") or "EVENT"), now, OS_DID, 2),
            )
        elif record_kind == "consentRequest":
            cur.execute(
                """
                INSERT INTO vertex_os_consent_request
                  (vertex_id,request_id,agent_did,action,risk_tier,estimated_cost,context_json,status,created_at,org_id,user_id,actor_id,owner_did,sensitivity_ord)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (vertex_id) DO UPDATE SET status=EXCLUDED.status
                """,
                (vertex_id, rkey, str(record.get("agentDid") or ""), str(record.get("action") or ""), str(record.get("riskTier") or ""), float(record.get("estimatedCost") or 0), json.dumps(record.get("context"), ensure_ascii=False, default=str), str(record.get("status") or status), now, *common),
            )
        elif record_kind == "consentResponse":
            cur.execute(
                """
                INSERT INTO vertex_os_consent_response
                  (vertex_id,request_id,verdict,reason,created_at,org_id,user_id,actor_id,owner_did,sensitivity_ord)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (vertex_id) DO UPDATE SET verdict=EXCLUDED.verdict, reason=EXCLUDED.reason
                """,
                (vertex_id, rkey, str(record.get("verdict") or label), str(record.get("reason") or ""), now, *common),
            )
            cur.execute(
                "INSERT INTO edge_os_consent_response (edge_id,src_vid,dst_vid,request_id,relation,created_at,owner_did,sensitivity_ord) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (edge_id) DO NOTHING",
                (f"{OS_DID}:consent:{rkey}:RESPONSE:{vertex_id}", f"at://{OS_DID}/ai.gftd.apps.os.consentRequest/{rkey}", vertex_id, rkey, "RESPONDED_BY", now, OS_DID, 2),
            )
        elif record_kind == "budgetAllocation":
            cur.execute(
                """
                INSERT INTO vertex_os_budget_allocation
                  (vertex_id,agent_id,amount,expires_at,created_at,org_id,user_id,actor_id,owner_did,sensitivity_ord)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (vertex_id) DO UPDATE SET amount=EXCLUDED.amount, expires_at=EXCLUDED.expires_at
                """,
                (vertex_id, str(record.get("agentId") or ""), float(record.get("amount") or 0), str(record.get("expiresAt") or ""), now, *common),
            )
            cur.execute(
                "INSERT INTO edge_os_budget_agent (edge_id,src_vid,dst_vid,agent_id,relation,created_at,owner_did,sensitivity_ord) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (edge_id) DO NOTHING",
                (f"{OS_DID}:budget:{rkey}:FOR:{record.get('agentId')}", vertex_id, f"at://{OS_DID}/ai.gftd.apps.os.agent/{record.get('agentId')}", str(record.get("agentId") or ""), "ALLOCATED_TO", now, OS_DID, 2),
            )
        elif record_kind == "directoryEntry":
            cur.execute(
                "INSERT INTO vertex_os_directory_entry (vertex_id,did,name,tags_json,created_at,org_id,user_id,actor_id,owner_did,sensitivity_ord) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (vertex_id) DO UPDATE SET name=EXCLUDED.name,tags_json=EXCLUDED.tags_json",
                (vertex_id, str(record.get("did") or ""), str(record.get("name") or label), str(record.get("tags") or "[]"), now, *common),
            )
        elif record_kind == "syncEvent":
            cur.execute(
                "INSERT INTO vertex_os_sync_event (vertex_id,direction,path,data_size,created_at,org_id,user_id,actor_id,owner_did,sensitivity_ord) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (vertex_id) DO UPDATE SET data_size=EXCLUDED.data_size",
                (vertex_id, str(record.get("direction") or ""), str(record.get("path") or ""), int(record.get("dataSize") or 0), now, *common),
            )
        elif record_kind == "windowEvent":
            cur.execute(
                "INSERT INTO vertex_os_window_event (vertex_id,window_id,event,app_id,title,content_type,content_url,created_at,org_id,user_id,actor_id,owner_did,sensitivity_ord) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (vertex_id) DO UPDATE SET event=EXCLUDED.event",
                (vertex_id, rkey, str(record.get("event") or ""), str(record.get("appId") or ""), str(record.get("title") or label), str(record.get("contentType") or ""), str(record.get("contentUrl") or ""), now, *common),
            )
        elif record_kind == "auditEntry":
            cur.execute(
                "INSERT INTO vertex_os_audit_entry (vertex_id,audit_id,agent_id,event,target,value_json,created_at,org_id,user_id,actor_id,owner_did,sensitivity_ord) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (vertex_id) DO UPDATE SET value_json=EXCLUDED.value_json",
                (vertex_id, rkey, str(record.get("agentId") or ""), str(record.get("event") or ""), str(record.get("target") or ""), json.dumps(value, ensure_ascii=False, separators=(",", ":"), default=str), now, *common),
            )
            cur.execute(
                "INSERT INTO edge_os_agent_audit_entry (edge_id,src_vid,dst_vid,agent_id,relation,created_at,owner_did,sensitivity_ord) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (edge_id) DO NOTHING",
                (f"{OS_DID}:agent:{record.get('agentId')}:AUDIT:{rkey}", f"at://{OS_DID}/ai.gftd.apps.os.agent/{record.get('agentId')}", vertex_id, str(record.get("agentId") or ""), str(record.get("event") or "AUDIT"), now, OS_DID, 2),
            )
        else:
            raise ValueError(f"unsupported OS record kind: {record_kind}")
    return {"uri": vertex_id, "rkey": rkey}


def _list(collection: str, *, limit: int = 100) -> list[dict[str, Any]]:
    record_kind = collection.rsplit(".", 1)[-1]
    tables = {
        "agent": ("vertex_os_agent", "created_at"),
        "agentEvent": ("vertex_os_agent_event", "created_at"),
        "consentRequest": ("vertex_os_consent_request", "created_at"),
        "consentResponse": ("vertex_os_consent_response", "created_at"),
        "budgetAllocation": ("vertex_os_budget_allocation", "created_at"),
        "directoryEntry": ("vertex_os_directory_entry", "created_at"),
        "syncEvent": ("vertex_os_sync_event", "created_at"),
        "windowEvent": ("vertex_os_window_event", "created_at"),
        "auditEntry": ("vertex_os_audit_entry", "created_at"),
    }
    table, order_col = tables.get(record_kind, ("", "created_at"))
    if not table:
        return []
    with sync_cursor() as cur:
        cur.execute(
            f"SELECT * FROM {table} ORDER BY {order_col} DESC LIMIT %s",
            (max(1, min(limit, 500)),),
        )
        return _rows(cur)


def _filter(collection: str, pred: Any, *, limit: int = 100) -> list[dict[str, Any]]:
    return [r for r in _list(collection, limit=500) if pred(r)][: max(0, limit)]


def task_os_agent_spawn(appId: str = "", name: str = "", config: Any = None, **_: Any) -> dict[str, Any]:
    agent_id = _id("agent")
    did = f"did:web:{appId}.etzhayyim.com" if appId else f"did:web:{agent_id}.etzhayyim.com"
    ts = _now()
    _insert("ai.gftd.apps.os.agent", {
        "agentId": agent_id, "did": did, "appId": appId, "name": name, "status": "active",
        "config": json.dumps(config if isinstance(config, dict) else {}, ensure_ascii=False),
        "org_id": "anon", "user_id": "anon", "actor_id": APP_ID, "created_at": ts, "updated_at": ts,
    }, label=name, status="active")
    return {"agentId": agent_id, "did": did, "status": "active"}


def _agent_event(agentId: str, event: str, **extra: Any) -> dict[str, Any]:
    _insert("ai.gftd.apps.os.agentEvent", {"agentId": agentId, "event": event, **extra, "org_id": "anon", "user_id": "anon", "actor_id": APP_ID, "created_at": _now()}, label=event)
    return {"agentId": agentId}


def task_os_agent_stop(agentId: str = "", **_: Any) -> dict[str, Any]:
    _agent_event(agentId, "stop")
    return {"agentId": agentId, "status": "stopped"}


def task_os_agent_pause(agentId: str = "", **_: Any) -> dict[str, Any]:
    _agent_event(agentId, "pause")
    return {"agentId": agentId, "status": "paused"}


def task_os_agent_resume(agentId: str = "", **_: Any) -> dict[str, Any]:
    _agent_event(agentId, "resume")
    return {"agentId": agentId, "status": "active"}


def task_os_agent_list(**_: Any) -> dict[str, Any]:
    return {"agents": _list("ai.gftd.apps.os.agent", limit=100)}


def task_os_agent_migrate(agentId: str = "", target: str = "", **_: Any) -> dict[str, Any]:
    _agent_event(agentId, "migrate", target=target)
    return {"agentId": agentId, "target": target, "status": "migrating"}


def task_os_consent_submit(agentDid: str = "", action: str = "", riskTier: str = "", estimatedCost: Any = 0, context: Any = None, **_: Any) -> dict[str, Any]:
    request_id = _id("consent")
    _insert("ai.gftd.apps.os.consentRequest", {
        "requestId": request_id, "agentDid": agentDid, "action": action, "riskTier": riskTier,
        "estimatedCost": estimatedCost, "context": context, "status": "pending",
        "org_id": "anon", "user_id": "anon", "actor_id": APP_ID, "created_at": _now(),
    }, label=action, status="pending")
    return {"requestId": request_id, "status": "pending"}


def task_os_consent_approve(requestId: str = "", **_: Any) -> dict[str, Any]:
    _insert("ai.gftd.apps.os.consentResponse", {"requestId": requestId, "verdict": "approved", "org_id": "anon", "user_id": "anon", "actor_id": APP_ID, "created_at": _now()}, label="approved")
    return {"requestId": requestId, "verdict": "approved"}


def task_os_consent_deny(requestId: str = "", reason: str = "", **_: Any) -> dict[str, Any]:
    _insert("ai.gftd.apps.os.consentResponse", {"requestId": requestId, "verdict": "denied", "reason": reason, "org_id": "anon", "user_id": "anon", "actor_id": APP_ID, "created_at": _now()}, label="denied")
    return {"requestId": requestId, "verdict": "denied"}


def task_os_consent_pending(**_: Any) -> dict[str, Any]:
    return {"pending": _filter("ai.gftd.apps.os.consentRequest", lambda r: r.get("status") == "pending", limit=50)}


def task_os_budget_allocate(agentId: str = "", amount: Any = 0, expiresAt: str = "", **_: Any) -> dict[str, Any]:
    _insert("ai.gftd.apps.os.budgetAllocation", {"agentId": agentId, "amount": amount, "expiresAt": expiresAt, "org_id": "anon", "user_id": "anon", "actor_id": APP_ID, "created_at": _now()}, label=agentId)
    return {"agentId": agentId, "allocated": amount}


def task_os_budget_balance(agentId: str = "", **_: Any) -> dict[str, Any]:
    rows = _filter("ai.gftd.apps.os.budgetAllocation", lambda r: str(r.get("agentId") or "") == agentId, limit=500)
    balance = sum(float(r.get("amount") or 0) for r in rows)
    return {"agentId": agentId, "balance": balance}


def task_os_directory_search(tags: Any = None, limit: Any = 50, **_: Any) -> dict[str, Any]:
    wanted = {str(t).strip() for t in tags} if isinstance(tags, list) else set()
    rows = _list("ai.gftd.apps.os.directoryEntry", limit=500)
    def match(row: dict[str, Any]) -> bool:
        if not wanted:
            return True
        raw = row.get("tags")
        parsed = json.loads(raw) if isinstance(raw, str) and raw.startswith("[") else raw
        vals = {str(v) for v in parsed} if isinstance(parsed, list) else set()
        return bool(vals & wanted)
    return {"agents": [r for r in rows if match(r)][: int(limit or 50)]}


def task_os_directory_register(did: str = "", name: str = "", tags: Any = None, **_: Any) -> dict[str, Any]:
    _insert("ai.gftd.apps.os.directoryEntry", {"did": did, "name": name, "tags": json.dumps(tags if isinstance(tags, list) else []), "org_id": "anon", "user_id": "anon", "actor_id": APP_ID, "created_at": _now()}, label=name)
    return {"did": did, "registered": True}


def task_os_audit_trail(agentId: str = "", limit: Any = 50, **_: Any) -> dict[str, Any]:
    rows = _filter("ai.gftd.apps.os.auditEntry", lambda r: str(r.get("agentId") or "") == agentId, limit=int(limit or 50))
    return {"trail": rows}


def task_os_sync_push(path: str = "", data: Any = "", **_: Any) -> dict[str, Any]:
    _insert("ai.gftd.apps.os.syncEvent", {"direction": "push", "path": path, "dataSize": len(str(data)), "org_id": "anon", "user_id": "anon", "actor_id": APP_ID, "created_at": _now()}, label=path)
    return {"path": path, "direction": "push", "status": "synced"}


def task_os_sync_pull(path: str = "", **_: Any) -> dict[str, Any]:
    rows = _filter("ai.gftd.apps.os.syncEvent", lambda r: r.get("path") == path and r.get("direction") == "push", limit=1)
    return {"path": path, "direction": "pull", "latest": rows[0] if rows else None}


def task_os_window_open(appId: str = "", title: str = "", contentType: str = "", contentUrl: str = "", **_: Any) -> dict[str, Any]:
    window_id = _id("win")
    _insert("ai.gftd.apps.os.windowEvent", {"windowId": window_id, "event": "open", "appId": appId, "title": title, "contentType": contentType, "contentUrl": contentUrl, "org_id": "anon", "user_id": "anon", "actor_id": APP_ID, "created_at": _now()}, label=title)
    return {"windowId": window_id, "status": "opened"}


def task_os_window_close(windowId: str = "", **_: Any) -> dict[str, Any]:
    _insert("ai.gftd.apps.os.windowEvent", {"windowId": windowId, "event": "close", "org_id": "anon", "user_id": "anon", "actor_id": APP_ID, "created_at": _now()}, label="close")
    return {"windowId": windowId, "status": "closed"}


def task_os_health(**_: Any) -> dict[str, Any]:
    return {"ok": True, "appId": APP_ID, "actorDID": OS_DID, "ts": _now()}


def register(worker: Any, *, timeout_ms: int = 60_000) -> None:
    tasks = {
        "xrpc.ai.gftd.apps.os.agentList": task_os_agent_list,
        "xrpc.ai.gftd.apps.os.agentMigrate": task_os_agent_migrate,
        "xrpc.ai.gftd.apps.os.agentPause": task_os_agent_pause,
        "xrpc.ai.gftd.apps.os.agentResume": task_os_agent_resume,
        "xrpc.ai.gftd.apps.os.agentSpawn": task_os_agent_spawn,
        "xrpc.ai.gftd.apps.os.agentStop": task_os_agent_stop,
        "xrpc.ai.gftd.apps.os.auditTrail": task_os_audit_trail,
        "xrpc.ai.gftd.apps.os.budgetAllocate": task_os_budget_allocate,
        "xrpc.ai.gftd.apps.os.budgetBalance": task_os_budget_balance,
        "xrpc.ai.gftd.apps.os.consentApprove": task_os_consent_approve,
        "xrpc.ai.gftd.apps.os.consentDeny": task_os_consent_deny,
        "xrpc.ai.gftd.apps.os.consentPending": task_os_consent_pending,
        "xrpc.ai.gftd.apps.os.consentSubmit": task_os_consent_submit,
        "xrpc.ai.gftd.apps.os.directoryRegister": task_os_directory_register,
        "xrpc.ai.gftd.apps.os.directorySearch": task_os_directory_search,
        "xrpc.ai.gftd.apps.os.health": task_os_health,
        "xrpc.ai.gftd.apps.os.syncPull": task_os_sync_pull,
        "xrpc.ai.gftd.apps.os.syncPush": task_os_sync_push,
        "xrpc.ai.gftd.apps.os.windowClose": task_os_window_close,
        "xrpc.ai.gftd.apps.os.windowOpen": task_os_window_open,
    }
    for task_type, handler in tasks.items():
        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(handler)
