"""Game Play Uploader handlers for BPMN + Zeebe."""

from __future__ import annotations

import json
import time
from typing import Any
from uuid import NAMESPACE_URL, uuid4, uuid5

from pymagatama.db_sync import sync_cursor

OWNER_DID = "did:web:game-play-uploader.etzhayyim.com"
RATE_JPY_PER_HOUR = 100
COLLECTION_TABLES = {
    "com.etzhayyim.apps.gamePlayUploader.participant": "vertex_game_play_participant",
    "com.etzhayyim.apps.gamePlayUploader.uploadSession": "vertex_game_play_upload_session",
    "com.etzhayyim.apps.gamePlayUploader.upload": "vertex_game_play_upload",
    "com.etzhayyim.apps.gamePlayUploader.review": "vertex_game_play_review",
    "com.etzhayyim.apps.gamePlayUploader.reward": "vertex_game_play_reward",
}


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def _s(value: Any, default: str = "") -> str:
    return str(value if value is not None else default)


def _num(value: Any, default: int = 0) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def _execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        return int(cur.rowcount or 0)


def _fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in (cur.fetchall() or [])]


def _vertex_id(collection: str, record_id: str) -> str:
    return f"at://{OWNER_DID}/{collection}/{record_id}"


def _edge_id(table: str, src: str, dst: str, relation: str) -> str:
    return f"{table}:{uuid5(NAMESPACE_URL, f'{src}|{dst}|{relation}')}"


def _typed_values(kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    if kind == "participant":
        return {
            "participant_id": _s(payload.get("participantId")),
            "display_name": _s(payload.get("displayName")),
            "age_band": _s(payload.get("ageBand")),
            "payout_handle": _s(payload.get("payoutHandle")),
        }
    if kind == "uploadSession":
        return {
            "game_title": _s(payload.get("gameTitle")),
            "platform": _s(payload.get("platform")),
            "duration_sec": _num(payload.get("durationSec")),
            "capture_started_at": _s(payload.get("captureStartedAt")),
        }
    if kind == "upload":
        return {
            "object_uri": _s(payload.get("objectUri")),
            "duration_sec": _num(payload.get("durationSec")),
            "sha256": _s(payload.get("sha256")),
        }
    if kind == "review":
        return {
            "review_id": _s(payload.get("reviewId")),
            "decision": _s(payload.get("decision")),
            "reviewer_did": _s(payload.get("reviewerDid")),
            "quality_score": _num(payload.get("qualityScore")),
            "reward_estimate_jpy": _num(payload.get("rewardEstimateJpy")),
        }
    if kind == "reward":
        return {"reward_jpy": _num(payload.get("rewardJpy"))}
    return {}


def _write_edge(cur: Any, table: str, src: str, dst: str, relation: str, payload: dict[str, Any], created_at: str) -> None:
    cur.execute(
        f"""
        INSERT INTO {table}
          (edge_id,src_vid,dst_vid,relation_kind,value_json,created_at,updated_at,owner_did,sensitivity_ord)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (edge_id) DO UPDATE SET
          value_json = EXCLUDED.value_json,
          updated_at = EXCLUDED.updated_at
        """,
        (
            _edge_id(table, src, dst, relation),
            src,
            dst,
            relation,
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
            created_at,
            _s(payload.get("updatedAt")) or created_at,
            OWNER_DID,
            2,
        ),
    )


def _write_related_edges(cur: Any, collection: str, kind: str, record_id: str, payload: dict[str, Any], created_at: str) -> None:
    vertex_id = _vertex_id(collection, record_id)
    if kind == "uploadSession":
        participant = _s(payload.get("participantDid"))
        if participant:
            _write_edge(cur, "edge_game_play_participant_session", _vertex_id("com.etzhayyim.apps.gamePlayUploader.participant", participant), vertex_id, "created_upload_session", payload, created_at)
    elif kind == "upload":
        session_id = _s(payload.get("sessionId"))
        if session_id:
            _write_edge(cur, "edge_game_play_session_upload", _vertex_id("com.etzhayyim.apps.gamePlayUploader.uploadSession", session_id), vertex_id, "has_upload", payload, created_at)
    elif kind == "review":
        upload_id = _s(payload.get("uploadId"))
        if upload_id:
            _write_edge(cur, "edge_game_play_upload_review", _vertex_id("com.etzhayyim.apps.gamePlayUploader.upload", upload_id), vertex_id, "reviewed_by", payload, created_at)
    elif kind == "reward":
        upload_id = _s(payload.get("uploadId"))
        if upload_id:
            _write_edge(cur, "edge_game_play_upload_reward", _vertex_id("com.etzhayyim.apps.gamePlayUploader.upload", upload_id), vertex_id, "earned_reward", payload, created_at)


def _record(collection: str, kind: str, payload: dict[str, Any], record_id: str | None = None) -> dict[str, Any]:
    table = COLLECTION_TABLES.get(collection)
    if table is None:
        raise ValueError(f"unsupported game play uploader collection: {collection}")
    rid = record_id or _id(kind)
    created = _s(payload.get("createdAt") or payload.get("updatedAt") or now_iso())
    rec = {**payload, "id": payload.get("id") or rid, "createdAt": created}
    typed = _typed_values(kind, rec)
    values = {
        "vertex_id": _vertex_id(collection, rid),
        "record_id": rid,
        "owner_did": OWNER_DID,
        "participant_did": _s(payload.get("participantDid")) or None,
        "session_id": _s(payload.get("sessionId")) or None,
        "upload_id": _s(payload.get("uploadId")) or None,
        "label": _s(payload.get("displayName") or payload.get("gameTitle") or payload.get("objectUri") or kind),
        "status": _s(payload.get("status")),
        "value_json": json.dumps(rec, ensure_ascii=False, sort_keys=True),
        "created_at": created,
        "updated_at": _s(payload.get("updatedAt")) or created,
        "sensitivity_ord": 2,
        **typed,
    }
    columns = ["vertex_id", "record_id", "owner_did", "participant_did", "session_id", "upload_id", "label", "status", "value_json", "created_at", "updated_at", "sensitivity_ord", *typed]
    placeholders = ",".join(["%s"] * len(columns))
    updates = ",".join([f"{c}=EXCLUDED.{c}" for c in columns if c != "vertex_id"])
    with sync_cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO {table} ({",".join(columns)})
            VALUES ({placeholders})
            ON CONFLICT (vertex_id) DO UPDATE SET {updates}
            """,
            tuple(values[c] for c in columns),
        )
        _write_related_edges(cur, collection, kind, rid, rec, created)
    return rec


def _list(collection: str, where_sql: str = "", params: tuple[Any, ...] = (), limit: int = 500) -> list[dict[str, Any]]:
    table = COLLECTION_TABLES.get(collection)
    if table is None:
        return []
    rows = _fetch_all(
        f"SELECT value_json AS record_json FROM {table} WHERE TRUE {where_sql} ORDER BY created_at DESC LIMIT %s",
        (*params, max(1, min(limit, 1000))),
    )
    out: list[dict[str, Any]] = []
    for row in rows:
        try:
            parsed = json.loads(str(row["record_json"]))
        except (TypeError, ValueError):
            continue
        if isinstance(parsed, dict):
            out.append(parsed)
    return out


def _reward(duration_sec: int, rate: int = RATE_JPY_PER_HOUR) -> int:
    return int(round((max(0, duration_sec) / 3600) * max(0, rate)))


def register_participant(participantDid: Any = None, displayName: Any = None, ageBand: Any = "unknown", payoutHandle: Any = None, guardianConsentRef: Any = None, **_: Any) -> dict[str, Any]:
    participant_did = _s(participantDid)
    if not participant_did:
        return {"error": "participantDid required"}
    participant_id = _id("player")
    _record("com.etzhayyim.apps.gamePlayUploader.participant", "participant", {
        "participantId": participant_id,
        "participantDid": participant_did,
        "displayName": _s(displayName),
        "ageBand": _s(ageBand or "unknown"),
        "payoutHandle": _s(payoutHandle),
        "guardianConsentRef": _s(guardianConsentRef),
        "status": "registered",
    }, participant_id)
    return {"participantId": participant_id, "status": "registered"}


def create_upload_session(participantDid: Any = None, gameTitle: Any = None, platform: Any = None, durationSec: Any = 0, captureStartedAt: Any = None, **_: Any) -> dict[str, Any]:
    participant_did = _s(participantDid)
    game_title = _s(gameTitle)
    if not participant_did or not game_title:
        return {"error": "participantDid and gameTitle required"}
    session_id = _id("session")
    object_key = f"game-play-uploader/{participant_did.replace(':', '_')}/{session_id}.mp4"
    upload_intent = {
        "provider": "backend-signed-object-storage",
        "objectKey": object_key,
        "contentType": "video/mp4",
        "expiresInSec": 900,
    }
    session = {
        "sessionId": session_id,
        "participantDid": participant_did,
        "gameTitle": game_title,
        "platform": _s(platform),
        "durationSec": _num(durationSec),
        "captureStartedAt": _s(captureStartedAt),
        "uploadIntent": upload_intent,
        "status": "awaitingUpload",
    }
    _record("com.etzhayyim.apps.gamePlayUploader.uploadSession", "uploadSession", session, session_id)
    return {"sessionId": session_id, "uploadIntent": upload_intent}


def record_gameplay_upload(sessionId: Any = None, objectUri: Any = None, durationSec: Any = 0, sha256: Any = None, metadata: Any = None, **_: Any) -> dict[str, Any]:
    session_id = _s(sessionId)
    object_uri = _s(objectUri)
    if not session_id or not object_uri:
        return {"error": "sessionId and objectUri required"}
    upload_id = _id("upload")
    upload = {
        "uploadId": upload_id,
        "sessionId": session_id,
        "objectUri": object_uri,
        "durationSec": _num(durationSec),
        "sha256": _s(sha256),
        "metadata": metadata if isinstance(metadata, dict) else {},
        "status": "pendingReview",
    }
    _record("com.etzhayyim.apps.gamePlayUploader.upload", "upload", upload, upload_id)
    return {"uploadId": upload_id, "status": "pendingReview"}


def review_upload(uploadId: Any = None, decision: Any = None, reviewerDid: Any = None, notes: Any = None, qualityScore: Any = None, **_: Any) -> dict[str, Any]:
    upload_id = _s(uploadId)
    decision_s = _s(decision)
    if not upload_id or decision_s not in {"approved", "rejected", "needsReview"}:
        return {"error": "uploadId and valid decision required"}
    uploads = _list("com.etzhayyim.apps.gamePlayUploader.upload", "AND upload_id=%s", (upload_id,), 1)
    duration = _num(uploads[0].get("durationSec") if uploads else 0)
    reward = _reward(duration) if decision_s == "approved" else 0
    review = {
        "reviewId": _id("review"),
        "uploadId": upload_id,
        "decision": decision_s,
        "reviewerDid": _s(reviewerDid),
        "notes": _s(notes),
        "qualityScore": qualityScore,
        "rewardEstimateJpy": reward,
    }
    _record("com.etzhayyim.apps.gamePlayUploader.review", "review", review, review["reviewId"])
    if reward > 0:
        _record("com.etzhayyim.apps.gamePlayUploader.reward", "reward", {"uploadId": upload_id, "rewardJpy": reward, "status": "estimated"})
    return {"uploadId": upload_id, "decision": decision_s, "rewardEstimateJpy": reward}


def calculate_reward(durationSec: Any = 0, rateJpyPerHour: Any = RATE_JPY_PER_HOUR, **_: Any) -> dict[str, Any]:
    duration = _num(durationSec)
    rate = _num(rateJpyPerHour, RATE_JPY_PER_HOUR)
    return {"rewardJpy": _reward(duration, rate), "rateJpyPerHour": rate, "durationSec": duration}


def get_campaign_status(participantDid: Any = None, **_: Any) -> dict[str, Any]:
    participant_did = _s(participantDid)
    where = "AND participant_did=%s" if participant_did else ""
    params: tuple[Any, ...] = (participant_did,) if participant_did else ()
    participants = _list("com.etzhayyim.apps.gamePlayUploader.participant", where, params)
    uploads = _list("com.etzhayyim.apps.gamePlayUploader.upload")
    reviews = _list("com.etzhayyim.apps.gamePlayUploader.review")
    approved_upload_ids = {_s(r.get("uploadId")) for r in reviews if _s(r.get("decision")) == "approved"}
    approved_duration = sum(_num(u.get("durationSec")) for u in uploads if _s(u.get("uploadId")) in approved_upload_ids)
    return {
        "participants": len(participants) if participant_did else len(_list("com.etzhayyim.apps.gamePlayUploader.participant")),
        "uploads": len(uploads),
        "approvedDurationSec": approved_duration,
        "rewardJpy": _reward(approved_duration),
    }
