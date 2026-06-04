"""LangServer actor for claim.etzhayyim.com claim operations."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
import uvicorn


LOG = logging.getLogger("claim-consumer-actor")
OWNER_DID = "did:web:claim.etzhayyim.com"
CONSUMER_FAMILY = "claim-consumer"
CLAIM_COLLECTION = "com.etzhayyim.claim.stakedAttestation"

FRAUD_SYSTEM_PROMPT = (
    "You are a fraud detector for staked claims on the etzhayyim network. "
    "A user posted a public attestation with a GCC bond. Your job is to estimate "
    "the probability that the claim is FRAUD or DECEPTIVE on its face. "
    'Output ONLY valid JSON: { "confidence": number (0..1), "reasoning": string }. '
    "confidence=1 means CERTAIN fraud, 0 means likely truthful. "
    "Be conservative: opinion / value judgments / speculative-but-good-faith claims should return < 0.5. "
    "Reserve > 0.92 for clear scam patterns (impossible promises, known scams, deliberate deception with checkable falsity)."
)


def configure_logging() -> None:
    if LOG.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    LOG.addHandler(handler)
    LOG.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


AGENTGATEWAY_MCP_URL = os.environ.get(
    "AGENTGATEWAY_MCP_URL",
    "http://agentgateway-mcp.mitama-udf.svc.cluster.local:8080",
)
PORT = int(os.environ.get("PORT", "8080"))
TOOL_NAME = "claim.unchallenged.sweep"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rw_dsn() -> str:
    return os.environ.get("RW_URL") or os.environ.get("DATABASE_URL") or ""


def connect_rw() -> Any:
    import psycopg

    dsn = rw_dsn()
    if not dsn:
        raise RuntimeError("RW_URL or DATABASE_URL is required")
    return psycopg.connect(dsn, autocommit=True, prepare_threshold=None)


def claim_vertex_id(claim_id: str) -> str:
    return f"at://{OWNER_DID}/{CLAIM_COLLECTION}/{claim_id[2:] if claim_id.startswith('0x') else claim_id}"


def clean(value: Any) -> str:
    return "" if value is None else str(value)


def clamp01(value: Any) -> float:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, n))


def hmac_hex(secret: str, body: str) -> str:
    return hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()


def fetch_pending_unchallenged(limit: int) -> list[dict[str, Any]]:
    with connect_rw() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  s.claim_id,
                  s.claimant_addr,
                  s.bond,
                  s.at_record_cid,
                  s.challenge_period_sec,
                  s.posted_at,
                  s.created_at
                FROM vertex_claim_stake s
                LEFT JOIN vertex_claim_challenge ch ON ch.claim_id = s.claim_id
                WHERE s.state = 'pending'
                  AND ch.claim_id IS NULL
                ORDER BY s.created_at ASC
                LIMIT %s
                """,
                (limit * 4,),
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row, strict=False)) for row in cur.fetchall()]


def expired_rows(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    now_ts = time.time()
    expired: list[dict[str, Any]] = []
    for row in rows:
        try:
            created = row["created_at"]
            if isinstance(created, datetime):
                created_ts = created.timestamp()
            else:
                created_ts = datetime.fromisoformat(clean(created).replace("Z", "+00:00")).timestamp()
            window_sec = float(row.get("challenge_period_sec") or 0)
        except (TypeError, ValueError):
            continue
        if created_ts + window_sec < now_ts:
            expired.append(row)
        if len(expired) >= limit:
            break
    return expired


def parse_model_json(content: str) -> dict[str, Any]:
    match = re.search(r"\{[\s\S]*\}", content or "")
    if not match:
        return {"confidence": 0.0, "reasoning": content[:1000], "skip": True}
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"confidence": 0.0, "reasoning": content[:1000], "skip": True}
    return {
        "confidence": clamp01(parsed.get("confidence")),
        "reasoning": clean(parsed.get("reasoning")),
        "skip": False,
    }


async def ask_murakumo_fraud(row: dict[str, Any]) -> dict[str, Any]:
    url = os.environ.get("MURAKUMO_URL", "").strip()
    if not url:
        return {"confidence": 0.0, "reasoning": "MURAKUMO_URL not configured", "skip": True}
    user = (
        f"Claim id: {row.get('claim_id')}\n"
        f"at-record-cid: {row.get('at_record_cid')}\n"
        f"bond (wei): {row.get('bond')}\n"
        f"claimant addr: {row.get('claimant_addr')}\n"
        f"posted block: {row.get('posted_at')}"
    )
    payload = {
        "model": os.environ.get("MURAKUMO_MODEL", "qwen3-30b-a3b"),
        "messages": [
            {"role": "system", "content": FRAUD_SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
        "max_tokens": 400,
    }
    headers = {"content-type": "application/json"}
    token = os.environ.get("MURAKUMO_BEARER", "").strip()
    if token:
        headers["authorization"] = f"Bearer {token}"
    async with httpx.AsyncClient(timeout=90, follow_redirects=True) as client:
        res = await client.post(url, json=payload, headers=headers)
    res.raise_for_status()
    data = res.json()
    content = clean(((data.get("choices") or [{}])[0].get("message") or {}).get("content"))
    return parse_model_json(content)


def persist_witness_alarms(alarms: list[dict[str, Any]]) -> int:
    if not alarms:
        return 0
    ts = now_iso()
    inserted = 0
    with connect_rw() as conn:
        with conn.cursor() as cur:
            for alarm in alarms:
                claim_id = clean(alarm["claim_id"])
                rkey = f"claim-witness-{claim_id[2:18] if claim_id.startswith('0x') else claim_id[:16]}-{int(time.time() * 1000)}"
                attest_vid = f"at://{OWNER_DID}/com.etzhayyim.monitor.attestation/{rkey}"
                cur.execute(
                    """
                    INSERT INTO vertex_yoro_monitor_attestation
                      (vertex_id, sensitivity_ord, owner_did, rkey, repo, monitor_did, axis,
                       subject_did, observed_at, status, fault_class, signals_json,
                       created_at, org_id, user_id, actor_id)
                    VALUES
                      (%s, 1, %s, %s, %s, %s, %s,
                       %s, %s, %s, %s, %s,
                       %s, %s, %s, %s)
                    """,
                    (
                        attest_vid,
                        OWNER_DID,
                        rkey,
                        OWNER_DID,
                        OWNER_DID,
                        "claim-integrity",
                        claim_vertex_id(claim_id),
                        ts,
                        "fault",
                        "stake_witness_alarm",
                        json.dumps(
                            {
                                "claimId": claim_id,
                                "bond": clean(alarm.get("bond")),
                                "atRecordCid": clean(alarm.get("at_record_cid")),
                                "murakumoConfidence": alarm.get("confidence"),
                            },
                            separators=(",", ":"),
                        ),
                        ts,
                        "anon",
                        "anon",
                        f"sys.{CONSUMER_FAMILY}",
                    ),
                )
                inserted += max(0, cur.rowcount or 0)
    return inserted


async def submit_unchallenged_sweep(claim_ids: list[str]) -> dict[str, Any]:
    secret = os.environ.get("CLAIM_SETTLER_HMAC", "").strip()
    if not secret:
        raise RuntimeError("CLAIM_SETTLER_HMAC is required")
    url = os.environ.get("AUTHZ_SWEEP_URL", "https://authz.etzhayyim.com/internal/claim-unchallenged-sweep")
    body = json.dumps({"claimIds": claim_ids}, separators=(",", ":"))
    headers = {"content-type": "application/json", "x-claim-settler-auth": hmac_hex(secret, body)}
    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
        res = await client.post(url, content=body, headers=headers)
    text = res.text
    if not res.is_success:
        raise RuntimeError(f"authz sweep HTTP {res.status_code}: {text[:200]}")
    try:
        parsed = res.json()
    except json.JSONDecodeError:
        return {"results": []}
    return parsed if isinstance(parsed, dict) else {"results": []}


async def unchallenged_sweep(limit: int | None = None, **_: Any) -> dict[str, Any]:
    started = time.time()
    batch_limit = int(limit or os.environ.get("CLAIM_CHALLENGE_BATCH", "5"))
    threshold = float(os.environ.get("CLAIM_CHALLENGE_THRESHOLD", "0.92"))
    errors: list[str] = []

    rows = fetch_pending_unchallenged(batch_limit)
    expired = expired_rows(rows, batch_limit)
    if not expired:
        return {
            "result": {
                "ok": True,
                "scanned": 0,
                "submitted": 0,
                "witnessAlarms": 0,
                "errors": [],
                "latencyMs": int((time.time() - started) * 1000),
                "ts": now_iso(),
            }
        }

    alarms: list[dict[str, Any]] = []
    for row in expired:
        try:
            verdict = await ask_murakumo_fraud(row)
            if not verdict.get("skip") and float(verdict["confidence"]) >= threshold:
                alarms.append({**row, "confidence": verdict["confidence"]})
        except Exception as exc:  # noqa: BLE001
            claim_id = clean(row.get("claim_id"))
            LOG.warning("murakumo re-score failed for %s: %s", claim_id[:14], exc)
            errors.append(f"{claim_id[:14]}: murakumo {exc}")

    witness_alarms = persist_witness_alarms(alarms)
    claim_ids = [clean(row["claim_id"]) for row in expired]

    submitted = 0
    try:
        parsed = await submit_unchallenged_sweep(claim_ids)
        results = parsed.get("results") if isinstance(parsed, dict) else []
        if isinstance(results, list) and results:
            submitted = len([r for r in results if isinstance(r, dict) and r.get("ok")])
            errors.extend(
                f"{clean(r.get('claimId'))[:14]}: {clean(r.get('error') or 'unknown')}"
                for r in results
                if isinstance(r, dict) and not r.get("ok")
            )
        else:
            submitted = len(claim_ids)
    except Exception as exc:  # noqa: BLE001
        LOG.warning("authz sweep failed: %s", exc)
        errors.append(f"authz sweep failed: {exc}")

    return {
        "result": {
            "ok": not errors,
            "scanned": len(expired),
            "submitted": submitted,
            "witnessAlarms": witness_alarms,
            "errors": errors,
            "latencyMs": int((time.time() - started) * 1000),
            "ts": now_iso(),
        }
    }


app = FastAPI(title="claim-consumer-actor", version="1.0.0")


@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    return {
        "ok": True,
        "runtimeKind": "k8s-langserver",
        "agentGatewayMcpUrl": AGENTGATEWAY_MCP_URL,
        "tools": [TOOL_NAME],
    }


@app.get("/tools")
async def tools() -> dict[str, Any]:
    return {"tools": [{"name": TOOL_NAME, "runtime": "langserver"}]}


async def _invoke_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name != TOOL_NAME:
        raise HTTPException(status_code=404, detail=f"unknown tool: {name}")
    return await unchallenged_sweep(**arguments)


@app.post("/invoke")
async def invoke(payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name") or payload.get("tool") or "")
    arguments = payload.get("arguments") or payload.get("input") or {}
    if not isinstance(arguments, dict):
        raise HTTPException(status_code=400, detail="arguments must be an object")
    return {"ok": True, "name": name, "result": await _invoke_tool(name, arguments)}


@app.post("/runs")
async def runs(payload: dict[str, Any]) -> dict[str, Any]:
    assistant_id = str(payload.get("assistant_id") or TOOL_NAME)
    arguments = payload.get("input") or payload.get("arguments") or {}
    if not isinstance(arguments, dict):
        raise HTTPException(status_code=400, detail="input must be an object")
    return {"status": "completed", "assistant_id": assistant_id, "output": await _invoke_tool(assistant_id, arguments)}


if __name__ == "__main__":
    try:
        configure_logging()
        LOG.info("claim-consumer-actor starting, runtime=k8s-langserver, agentgateway_mcp_url=%s", AGENTGATEWAY_MCP_URL)
        uvicorn.run(app, host="0.0.0.0", port=PORT)
    except KeyboardInterrupt:
        LOG.info("stopped")
