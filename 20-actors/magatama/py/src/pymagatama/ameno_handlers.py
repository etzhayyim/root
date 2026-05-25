"""Ameno LangServer handlers (ADR-2605111200).

Receives XRPC saveResult / listHistory forwarded from
ameno.etzhayyim.com CF Worker → bpmn-dispatcher → AgentGateway MCP →
ameno-langserver pod, and persists / queries vertex_ameno_inferenceresult
via the shared sync psycopg pool.

Lexicons (SSoT):
  00-contracts/lexicons/ai/gftd/apps/ameno/saveResult.json
  00-contracts/lexicons/ai/gftd/apps/ameno/listHistory.json
  00-contracts/lexicons/ai/gftd/apps/ameno/inferenceResult.json
"""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Iterable

from pymagatama.db_sync import sync_cursor as _sync_cursor

_TABLE = "vertex_ameno_inferenceresult"
_KNOWN_MODELS = {"gemma-4-e2b-it", "gemma-4-e4b-it", "baien-bitnet-2b"}

# Phase 5c — credits AF event recorded per browser inference. Flat 10 credits
# per saveResult plus 1 credit per 100 output tokens. Tunable via env at
# the langserver pod boundary so we don't have to redeploy app code to
# adjust the murakumo Tier 2 reward curve.
_CREDIT_EVENT_TYPE = "ameno_browser_inference"
_CREDIT_BASE = int(os.environ.get("AMENO_CREDIT_BASE", "10"))
_CREDIT_PER_100_TOKENS = int(os.environ.get("AMENO_CREDIT_PER_100_TOKENS", "1"))

# subscribeBriefs scope guard — only social collections allowed (Phase 4a).
_ALLOWED_BRIEF_COLLECTIONS = {"app.bsky.feed.post"}
_NATS_URL = os.environ.get("NATS_URL", "nats://nats.nats.svc.cluster.local:4222")
_NATS_SUBJECT_PREFIX = os.environ.get("PUBLISH_SUBJECT_PREFIX", "pds.repo.commit")
_LIST_COLS = (
    "result_id",
    "vertex_id",
    "model_id",
    "actor_did",
    "prompt",
    "output",
    "elapsed_ms",
    "tokens_per_sec",
    "created_at",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_str(raw: Any, default: str = "") -> str:
    return str(raw) if raw is not None else default


def _safe_int(raw: Any, default: int = 0) -> int:
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _new_result_id() -> str:
    return f"infer-{int(time.time() * 1000):x}-{secrets.token_hex(4)}"


def _credit_amount(output_tokens: int) -> int:
    """Phase 5c — base + per-100-tokens reward. Tier 2 (browser) crowd-source."""
    return max(0, _CREDIT_BASE + (max(0, output_tokens) // 100) * _CREDIT_PER_100_TOKENS)


def _record_credit_event(
    cur: Any,
    actor_did: str,
    org_did: str,
    result_id: str,
    output_tokens: int,
    created_at: str,
) -> None:
    """Append an AF event row crediting the actor for one browser inference.

    Best-effort — the saveResult INSERT has already committed by the time
    we're here; a credit-side failure should never roll back the inference
    persist. Caller wraps this in try/except.
    """
    amount = _credit_amount(output_tokens)
    if amount <= 0:
        return
    user_id = actor_did or "anon"
    ts_ms = int(time.time() * 1000)
    af_vertex_id = f"af://credits/{user_id}/{result_id}"
    cur.execute(
        """
        INSERT INTO vertex_credits_af_event (
          vertex_id, user_id, event_type, amount, ts_ms, created_at,
          actor_did, org_did
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            af_vertex_id,
            user_id,
            _CREDIT_EVENT_TYPE,
            amount,
            ts_ms,
            created_at,
            actor_did or "anon",
            org_did or "anon",
        ),
    )


def handle_save_result(payload: dict[str, Any]) -> dict[str, Any]:
    """app.etzhayyim.apps.ameno.saveResult — INSERT vertex_ameno_inferenceresult."""
    model_id = _safe_str(payload.get("modelId"))
    if not model_id:
        return {"status": "failed", "error": "modelId required"}
    if model_id not in _KNOWN_MODELS:
        return {"status": "failed", "error": f"unknown modelId: {model_id}"}
    prompt = _safe_str(payload.get("prompt"))
    output = _safe_str(payload.get("output"))
    if not prompt or not output:
        return {"status": "failed", "error": "prompt and output required"}

    result_id = _new_result_id()
    actor_did = _safe_str(payload.get("actorDid"))
    vertex_id = (
        f"at://{actor_did or 'did:web:ameno.etzhayyim.com'}"
        f"/app.etzhayyim.apps.ameno.inferenceResult/{result_id}"
    )
    created_at = _now_iso()
    lora_adapters_raw = payload.get("loraAdapters")
    lora_adapters_json = (
        json.dumps(list(lora_adapters_raw)) if isinstance(lora_adapters_raw, Iterable) and not isinstance(lora_adapters_raw, (str, bytes)) else ""
    )

    columns = (
        "vertex_id",
        "result_id",
        "model_id",
        "lora_adapters",
        "prompt",
        "output",
        "prompt_tokens",
        "output_tokens",
        "elapsed_ms",
        "tokens_per_sec",
        "webgpu_adapter",
        "rag_context_used",
        "actor_did",
        "org_did",
        "owner_did",
        "sensitivity_ord",
        "created_at",
    )
    values = (
        vertex_id,
        result_id,
        model_id,
        lora_adapters_json,
        prompt,
        output,
        _safe_int(payload.get("promptTokens")),
        _safe_int(payload.get("outputTokens")),
        _safe_int(payload.get("elapsedMs")),
        _safe_int(payload.get("tokensPerSec")),
        _safe_str(payload.get("webgpuAdapter")),
        bool(payload.get("ragContextUsed")),
        actor_did or "anon",
        _safe_str(payload.get("orgDid"), "anon"),
        actor_did or "did:web:ameno.etzhayyim.com",
        2,
        created_at,
    )
    placeholders = ", ".join(["%s"] * len(columns))
    column_list = ", ".join(columns)
    insert_sql = f"INSERT INTO {_TABLE} ({column_list}) VALUES ({placeholders})"

    org_did = _safe_str(payload.get("orgDid"), "anon")
    try:
        with _sync_cursor() as cur:
            cur.execute(insert_sql, values)
            try:
                _record_credit_event(
                    cur,
                    actor_did,
                    org_did,
                    result_id,
                    _safe_int(payload.get("outputTokens")),
                    created_at,
                )
            except Exception:  # noqa: BLE001
                # Phase 5c: credit event is best-effort. The inference is
                # already persisted by the line above; a metering failure
                # must not roll back the user-visible saveResult result.
                pass
    except Exception as exc:  # noqa: BLE001
        return {"status": "failed", "error": str(exc)}

    return {
        "status": "persisted",
        "resultId": result_id,
        "uri": vertex_id,
    }


def _sse_event(event: str, data: dict[str, Any]) -> bytes:
    """Encode one SSE frame (event + data + blank line)."""
    return f"event: {event}\ndata: {json.dumps(data, separators=(',', ':'))}\n\n".encode()


def _extract_brief(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Pull the fields a browser subscriber needs for inference + provenance."""
    record = payload.get("record") if isinstance(payload.get("record"), dict) else {}
    text = ""
    if isinstance(record, dict):
        text = str(record.get("text") or "").strip()
    if not text:
        return None
    return {
        "uri": str(payload.get("uri") or ""),
        "authorDid": str(payload.get("did") or payload.get("authorDid") or ""),
        "collection": str(payload.get("collection") or "app.bsky.feed.post"),
        "text": text[:4000],
        "tsMs": int(payload.get("seq") or payload.get("tsMs") or int(time.time() * 1000)),
    }


async def subscribe_briefs_sse(payload: dict[str, Any]) -> AsyncIterator[bytes]:
    """app.etzhayyim.apps.ameno.subscribeBriefs — yield SSE frames per NATS commit event.

    Subscribes to NATS subject `pds.repo.commit.<collection_underscored>` and
    yields one `event: brief` frame per matching record. Closes the stream after
    `maxEvents` events or `idleTimeoutSec` seconds of inactivity.
    """
    collection = str(payload.get("collection") or "app.bsky.feed.post")
    if collection not in _ALLOWED_BRIEF_COLLECTIONS:
        yield _sse_event("error", {"error": f"collection not allowed: {collection}"})
        yield _sse_event("done", {"reason": "collection-not-allowed"})
        return

    max_events = max(1, min(_safe_int(payload.get("maxEvents"), 100), 1000))
    idle_timeout = max(5.0, min(float(_safe_int(payload.get("idleTimeoutSec"), 60)), 600.0))
    subject = f"{_NATS_SUBJECT_PREFIX}.{collection.replace('.', '_')}"

    try:
        import nats as _nats  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        yield _sse_event("error", {"error": f"nats client unavailable: {exc}"})
        yield _sse_event("done", {"reason": "nats-import-failed"})
        return

    try:
        nc = await _nats.connect(_NATS_URL, connect_timeout=3, max_reconnect_attempts=2)
    except Exception as exc:  # noqa: BLE001
        yield _sse_event("error", {"error": f"nats connect failed: {exc}"})
        yield _sse_event("done", {"reason": "nats-connect-failed"})
        return

    queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=max_events * 2)

    async def _msg_handler(msg: Any) -> None:
        try:
            data = json.loads(msg.data.decode("utf-8"))
        except Exception:
            return
        brief = _extract_brief(data)
        if brief is None:
            return
        try:
            queue.put_nowait(_sse_event("brief", brief))
        except asyncio.QueueFull:
            pass

    sub = await nc.subscribe(subject, cb=_msg_handler)
    yield _sse_event("ready", {"subject": subject, "maxEvents": max_events})
    delivered = 0
    try:
        while delivered < max_events:
            try:
                frame = await asyncio.wait_for(queue.get(), timeout=idle_timeout)
            except asyncio.TimeoutError:
                yield _sse_event("done", {"reason": "idle-timeout", "delivered": delivered})
                return
            yield frame
            delivered += 1
        yield _sse_event("done", {"reason": "max-events", "delivered": delivered})
    finally:
        try:
            await sub.unsubscribe()
        except Exception:
            pass
        try:
            await nc.close()
        except Exception:
            pass


_ADAPTER_COLS = (
    "adapter_id",
    "did",
    "domain",
    "status",
    "base_model",
    "weight_b2_uri",
    "weight_byte_size",
    "weight_sha256",
    "adapter_rank",
    "adapter_alpha",
    "adapter_format",
    "display_name_yomi",
    "created_at",
)


def handle_list_actor_adapters(payload: dict[str, Any]) -> dict[str, Any]:
    """app.etzhayyim.apps.ameno.listActorAdapters — SELECT vertex_lora_adapter."""
    actor_did = _safe_str(payload.get("actorDid"))
    if not actor_did:
        return {"items": [], "total": 0, "error": "actorDid required"}
    domain = _safe_str(payload.get("domain"))
    limit = max(1, min(_safe_int(payload.get("limit"), 20), 100))

    clauses = ["did = %s", "status = %s"]
    params: list[Any] = [actor_did, "active"]
    if domain:
        clauses.append("domain = %s")
        params.append(domain)
    where = " AND ".join(clauses)

    select_cols = ", ".join(_ADAPTER_COLS)
    list_sql = (
        f"SELECT {select_cols} FROM vertex_lora_adapter WHERE {where} "
        f"ORDER BY created_at DESC LIMIT %s"
    )
    count_sql = f"SELECT COUNT(*) FROM vertex_lora_adapter WHERE {where}"

    items: list[dict[str, Any]] = []
    total = 0
    try:
        with _sync_cursor() as cur:
            cur.execute(count_sql, params)
            row = cur.fetchone()
            total = int(row[0] if row else 0)
            cur.execute(list_sql, [*params, limit])
            for r in cur.fetchall() or []:
                # adapter_alpha is DOUBLE PRECISION on RW but the lexicon
                # constrains output to integer (×1000) per AT Protocol rules.
                alpha_raw = r[9] if r[9] is not None else 0.0
                items.append(
                    {
                        "adapterId": r[0] or "",
                        "actorDid": r[1] or "",
                        "domain": r[2] or "",
                        "status": r[3] or "",
                        "baseModel": r[4] or "",
                        "weightB2Uri": r[5] or "",
                        "weightByteSize": int(r[6] or 0),
                        "weightSha256": r[7] or "",
                        "adapterRank": int(r[8] or 0),
                        "adapterAlpha": int(round(float(alpha_raw) * 1000)),
                        "adapterFormat": r[10] or "",
                        "displayNameYomi": r[11] or "",
                        "createdAt": r[12] or "",
                    }
                )
    except Exception:  # noqa: BLE001
        return {"items": [], "total": 0}

    return {"items": items, "total": total}


def handle_list_my_credits(payload: dict[str, Any]) -> dict[str, Any]:
    """app.etzhayyim.apps.ameno.listMyCredits — SELECT mv_ameno_credits_balance for one user."""
    actor_did = _safe_str(payload.get("actorDid"))
    if not actor_did:
        return {"actorDid": "", "balance": 0, "eventCount": 0}
    try:
        with _sync_cursor() as cur:
            cur.execute(
                """
                SELECT balance, event_count, last_event_ts_ms, last_event_created_at
                FROM mv_ameno_credits_balance
                WHERE user_id = %s
                LIMIT 1
                """,
                (actor_did,),
            )
            row = cur.fetchone()
    except Exception:  # noqa: BLE001
        return {"actorDid": actor_did, "balance": 0, "eventCount": 0}
    if not row:
        return {"actorDid": actor_did, "balance": 0, "eventCount": 0}
    return {
        "actorDid": actor_did,
        "balance": int(row[0] or 0),
        "eventCount": int(row[1] or 0),
        "lastEventTsMs": int(row[2] or 0),
        "lastEventCreatedAt": row[3] or "",
    }


def handle_list_history(payload: dict[str, Any]) -> dict[str, Any]:
    """app.etzhayyim.apps.ameno.listHistory — SELECT from vertex_ameno_inferenceresult."""
    actor_did = _safe_str(payload.get("actorDid"))
    model_id = _safe_str(payload.get("modelId"))
    limit_raw = _safe_int(payload.get("limit"), 20)
    limit = max(1, min(limit_raw, 100))
    offset = max(0, _safe_int(payload.get("offset"), 0))

    clauses: list[str] = []
    params: list[Any] = []
    if actor_did:
        clauses.append("actor_did = %s")
        params.append(actor_did)
    if model_id:
        clauses.append("model_id = %s")
        params.append(model_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    select_cols = ", ".join(_LIST_COLS)
    list_sql = (
        f"SELECT {select_cols} FROM {_TABLE} {where} "
        f"ORDER BY created_at DESC LIMIT %s OFFSET %s"
    )
    count_sql = f"SELECT COUNT(*) FROM {_TABLE} {where}"

    items: list[dict[str, Any]] = []
    total = 0
    try:
        with _sync_cursor() as cur:
            cur.execute(count_sql, params)
            row = cur.fetchone()
            total = int(row[0] if row else 0)
            cur.execute(list_sql, [*params, limit, offset])
            for r in cur.fetchall() or []:
                items.append(
                    {
                        "resultId": r[0] or "",
                        "uri": r[1] or "",
                        "modelId": r[2] or "",
                        "actorDid": r[3] or "",
                        "prompt": r[4] or "",
                        "output": r[5] or "",
                        "elapsedMs": int(r[6] or 0),
                        "tokensPerSec": int(r[7] or 0),
                        "createdAt": r[8] or "",
                    }
                )
    except Exception:  # noqa: BLE001
        return {"items": [], "total": 0, "offset": offset, "limit": limit}

    return {"items": items, "total": total, "offset": offset, "limit": limit}
