"""Demining AppView handlers for BPMN + Zeebe.

Cloudflare Worker stays a thin edge facade. Humanitarian Mine Action domain
rules, Tier 3 field handling, and graph writes live here.
"""

from __future__ import annotations

import json
import time
from typing import Any
from uuid import uuid4

from pymagatama.db_sync import sync_cursor

OWNER_DID = "did:web:dm1nactz.gftd.ai"
PROHIBITED_PATTERNS = ("produce_apm", "stockpile_apm", "transfer_apm", "deploy_apm", "manufacture_apm")
TIER3_FIELDS = {"geometryWkt", "hitCoordsWkt", "operatorDid", "operatorDids", "victimRef"}


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def _ctx_did(kwargs: dict[str, Any], fallback: str = OWNER_DID) -> str:
    for key in ("did", "callerDid", "actorDid", "ownerDid"):
        value = kwargs.get(key)
        if isinstance(value, str) and value:
            return value
    caller = kwargs.get("caller")
    if isinstance(caller, dict):
        did = caller.get("did")
        if isinstance(did, str) and did:
            return did
    return fallback


def _reject_prohibited(record: dict[str, Any]) -> str | None:
    text = json.dumps(record, ensure_ascii=False, sort_keys=True).lower()
    for pattern in PROHIBITED_PATTERNS:
        if pattern in text:
            return f"prohibited activity in record: {pattern}"
    return None


def _split_tier3(input: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    public: dict[str, Any] = {}
    tier3: dict[str, Any] = {}
    for key, value in input.items():
        if key in TIER3_FIELDS:
            tier3[key] = value
        else:
            public[key] = value
    return public, tier3


def _fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in (cur.fetchall() or [])]


def _execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        return int(cur.rowcount or 0)


def _write_public(owner: str, record_type: str, record_id: str, collection: str, rec: dict[str, Any], tier: int) -> None:
    vertex_id = f"at://{owner}/{collection}/{record_id}"
    _execute(
        """INSERT INTO vertex_atrecord_demining_public
        (vertex_id, _seq, owner_did, record_type, record_id, collection, record_json, sensitivity_tier, created_at)
        VALUES (%s, _next_seq('vertex_atrecord_demining_public'), %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (vertex_id) DO UPDATE SET
          record_json=EXCLUDED.record_json,
          sensitivity_tier=EXCLUDED.sensitivity_tier,
          created_at=EXCLUDED.created_at""",
        (vertex_id, owner, record_type, record_id, collection, json.dumps(rec, ensure_ascii=False, sort_keys=True), tier, now_iso()),
    )


def _audit(actor: str, action: str, record_id: str = "", record_type: str = "", field_name: str = "", jurisdiction: str = "", reason: str = "") -> None:
    _execute(
        """INSERT INTO vertex_atrecord_demining_tier3_audit
        (vertex_id, _seq, occurred_at, actor_did, action, record_id, record_type, field_name, jurisdiction, reason)
        VALUES (%s, _next_seq('vertex_atrecord_demining_tier3_audit'), %s, %s, %s, %s, %s, %s, %s, %s)""",
        (_id("audit"), now_iso(), actor, action, record_id or None, record_type or None, field_name or None, jurisdiction or None, reason or None),
    )


def _store_tier3(record_id: str, record_type: str, owner: str, jurisdiction: str | None, actor: str, fields: dict[str, Any]) -> dict[str, list[str]]:
    stored: list[str] = []
    skipped: list[str] = []
    for field, value in fields.items():
        if value is None or value == "":
            skipped.append(field)
            continue
        value_text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)
        vertex_id = f"demining:tier3:{record_id}:{field}"
        _execute(
            """INSERT INTO vertex_atrecord_demining_tier3_field
            (vertex_id, _seq, owner_did, record_id, record_type, field_name, field_value, jurisdiction, actor_did, released, created_at, updated_at)
            VALUES (%s, _next_seq('vertex_atrecord_demining_tier3_field'), %s, %s, %s, %s, %s, %s, %s, FALSE, %s, %s)
            ON CONFLICT (vertex_id) DO UPDATE SET
              field_value=EXCLUDED.field_value,
              jurisdiction=EXCLUDED.jurisdiction,
              actor_did=EXCLUDED.actor_did,
              updated_at=EXCLUDED.updated_at""",
            (vertex_id, owner, record_id, record_type, field, value_text, jurisdiction, actor, now_iso(), now_iso()),
        )
        stored.append(field)
        _audit(actor, "write", record_id, record_type, field, jurisdiction or "")
    return {"stored": stored, "skipped": skipped}


def _load_tier3(record_id: str, field: str, actor: str) -> str | None:
    rows = _fetch_all(
        """SELECT field_value, record_type, jurisdiction
        FROM vertex_atrecord_demining_tier3_field
        WHERE record_id=%s AND field_name=%s
        ORDER BY _seq DESC
        LIMIT 1""",
        (record_id, field),
    )
    if not rows:
        return None
    row = rows[0]
    _audit(actor, "read", record_id, str(row.get("record_type") or ""), field, str(row.get("jurisdiction") or ""))
    value = row.get("field_value")
    return str(value) if value is not None else None


def _mark_released(area_id: str, decision_id: str, actor: str) -> None:
    _execute(
        """UPDATE vertex_atrecord_demining_tier3_field
        SET released=TRUE, released_at=%s, released_by_decision=%s, updated_at=%s
        WHERE record_id=%s""",
        (now_iso(), decision_id, now_iso(), area_id),
    )
    _audit(actor, "release", area_id, "hazardArea", reason=f"decision={decision_id}")


def register_hazard_area(**kwargs: Any) -> dict[str, Any]:
    reject = _reject_prohibited(kwargs)
    if reject:
        return {"error": reject}
    area_id = _id("area")
    actor = _ctx_did(kwargs)
    owner = str(kwargs.get("ownerDid") or actor)
    public, tier3 = _split_tier3(kwargs)
    res = _store_tier3(area_id, "hazardArea", owner, kwargs.get("jurisdiction"), actor, tier3)
    rec = {**public, "areaId": area_id, "tier": 3, "createdAt": now_iso()}
    _write_public(owner, "hazardArea", area_id, "ai.gftd.apps.demining.hazardArea", rec, 3)
    return {"areaId": area_id, "tier": 3, "tier3Stored": res["stored"], "tier3Skipped": res["skipped"]}


def list_hazard_areas(status: Any = None, adminAreaDid: Any = None, contaminationType: Any = None, offset: Any = 0, limit: Any = 50, **_: Any) -> dict[str, Any]:
    lim = max(1, min(int(limit or 50), 200))
    off = max(0, int(offset or 0))
    rows = _fetch_all(
        """SELECT record_id, owner_did, record_json, created_at
        FROM vertex_atrecord_demining_public
        WHERE record_type='hazardArea'
        ORDER BY _seq DESC""",
    )
    areas: list[dict[str, Any]] = []
    for row in rows:
        try:
            rec = json.loads(str(row.get("record_json") or "{}"))
        except json.JSONDecodeError:
            rec = {"areaId": row.get("record_id")}
        if status and rec.get("status") != status:
            continue
        if adminAreaDid and rec.get("adminAreaDid") != adminAreaDid:
            continue
        if contaminationType:
            types = rec.get("contaminationTypes") if isinstance(rec.get("contaminationTypes"), list) else []
            if contaminationType not in types:
                continue
        rec.pop("geometryWkt", None)
        areas.append(rec)
    total = len(areas)
    return {
        "areas": areas[off : off + lim],
        "total": total,
        "offset": off,
        "limit": lim,
        "note": "Geometry omitted. Tier 3 access requires demining.viewCoordinates capability.",
    }


def record_detection(**kwargs: Any) -> dict[str, Any]:
    reject = _reject_prohibited(kwargs)
    if reject:
        return {"error": reject}
    detection_id = _id("det")
    actor = _ctx_did(kwargs)
    owner = str(kwargs.get("operatorDid") or actor)
    public, tier3 = _split_tier3(kwargs)
    _store_tier3(detection_id, "detectionEvent", owner, kwargs.get("jurisdiction"), actor, tier3)
    _write_public(owner, "detectionEvent", detection_id, "ai.gftd.apps.demining.detectionEvent", {**public, "detectionId": detection_id, "tier": 3, "createdAt": now_iso()}, 3)
    return {"detectionId": detection_id}


def record_clearance_task(**kwargs: Any) -> dict[str, Any]:
    reject = _reject_prohibited(kwargs)
    if reject:
        return {"error": reject}
    task_id = str(kwargs.get("taskId") or _id("task"))
    actor = _ctx_did(kwargs)
    public, tier3 = _split_tier3(kwargs)
    _store_tier3(task_id, "clearanceTask", actor, kwargs.get("jurisdiction"), actor, tier3)
    _write_public(actor, "clearanceTask", task_id, "ai.gftd.apps.demining.clearanceTask", {**public, "taskId": task_id, "tier": 2, "createdAt": now_iso()}, 2)
    return {"taskId": task_id}


def release_area(**kwargs: Any) -> dict[str, Any]:
    reject = _reject_prohibited(kwargs)
    if reject:
        return {"error": reject}
    area_id = str(kwargs.get("areaId") or "")
    if not area_id:
        return {"error": "areaId required"}
    actor = _ctx_did(kwargs)
    decision_id = _id("rel")
    stored = _load_tier3(area_id, "geometryWkt", actor)
    polygon_public = kwargs.get("polygonPublic") or stored
    _mark_released(area_id, decision_id, actor)
    rec = {**kwargs, "decisionId": decision_id, "areaId": area_id, "polygonPublic": polygon_public, "tier": 1, "decidedAt": kwargs.get("decidedAt") or now_iso()}
    _write_public(actor, "landReleaseDecision", decision_id, "ai.gftd.apps.demining.landReleaseDecision", rec, 1)
    return {"decisionId": decision_id, "tier": 1, "polygonPublished": bool(polygon_public)}


def record_eore_session(**kwargs: Any) -> dict[str, Any]:
    session_id = str(kwargs.get("sessionId") or _id("eore"))
    actor = _ctx_did(kwargs)
    rec = {**kwargs, "sessionId": session_id, "tier": 1, "createdAt": now_iso()}
    _write_public(actor, "eoreSession", session_id, "ai.gftd.apps.demining.eoreSession", rec, 1)
    return {"sessionId": session_id}


def record_victim(**kwargs: Any) -> dict[str, Any]:
    reject = _reject_prohibited(kwargs)
    if reject:
        return {"error": reject}
    record_id = _id("victim")
    actor = _ctx_did(kwargs)
    public, tier3 = _split_tier3(kwargs)
    _store_tier3(record_id, "victimRecord", actor, kwargs.get("jurisdiction"), actor, tier3)
    _write_public(actor, "victimRecord", record_id, "ai.gftd.apps.demining.victimRecord", {**public, "recordId": record_id, "tier": 3, "createdAt": now_iso()}, 3)
    return {"recordId": record_id}
