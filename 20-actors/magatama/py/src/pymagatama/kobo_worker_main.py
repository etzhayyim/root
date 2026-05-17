"""
Zeebe worker for kobo (酵母) — individual agent lifecycle layer (ADR-2605071200).

Yeast analogy: individual agents bud (asexual reproduction), sporulate
(stress-escape to dormancy via houshi), and germinate (revival from spore).

Subscribes to 3 domain job types:
  kobo.bud_agent  — record a budding event (parent→child agent edge)
  kobo.sporulate  — store agent state as CBOR spore, prepare for houshi custody
  kobo.germinate  — revive agent from spore with quorum confirmation

Run:
  python -m pymagatama.kobo_worker_main

Env:
  AGENTGATEWAY_MCP_URL  — LangServer AgentGateway URL (default 127.0.0.1:8080)
  RW_URL         — RisingWave postgres URL
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import signal
import time
from datetime import datetime, timezone
from typing import Any

from pymagatama.langserver_compat import LangServerWorker, create_langserver_channel

from pymagatama.db_sync import fetch_one, sync_cursor
from pymagatama.local_agent_env import load_env_file, load_keychain_secret

LOG = logging.getLogger("kobo_worker")

KOBO_DID = "did:web:kobo.etzhayyim.com"
HOUSHI_DID = "did:web:houshi.etzhayyim.com"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uid(prefix: str) -> str:
    digest = hashlib.sha256(f"{prefix}{time.time_ns()}".encode()).hexdigest()[:12]
    return f"{prefix}-{digest}"


# ─── kobo.bud_agent ───────────────────────────────────────────────────────────


async def task_bud_agent(
    parentDid: str = "",
    childDid: str = "",
    childVertexId: str = "",
    childRole: str = "",
    parentEta: float = 0.5,
    callerDid: str = "",
    buddingEdgeId: str = "",
    **_: Any,
) -> dict[str, Any]:
    """Record a budding event: parent agent produces a child agent."""

    if not parentDid or not childDid:
        return {"error": "parentDid and childDid required"}

    edge_id = buddingEdgeId or _uid("bud")
    now = _now()

    def _run() -> dict[str, Any]:
        with sync_cursor() as cur:
            cur.execute(
                """
                INSERT INTO edge_kobo_budding
                  (edge_id, src_vid, dst_vid, relation_kind, value_json,
                   created_at, updated_at, owner_did, sensitivity_ord,
                   parent_did, child_did, child_role, parent_eta, budded_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    edge_id,
                    f"at://{KOBO_DID}/ai.gftd.apps.kobo.agent/{parentDid.split(':')[-1]}",
                    childVertexId or f"at://{KOBO_DID}/ai.gftd.apps.kobo.agent/{childDid.split(':')[-1]}",
                    "kobo_budding",
                    json.dumps({"callerDid": callerDid, "childRole": childRole}),
                    now, now, KOBO_DID, 0,
                    parentDid, childDid, childRole or "clone", parentEta, now,
                ),
            )
        return {
            "buddingEdgeId": edge_id,
            "parentDid": parentDid,
            "childDid": childDid,
            "buddedAt": now,
        }

    result = await asyncio.to_thread(_run)
    LOG.info("bud_agent: %s → %s edge=%s", parentDid, childDid, edge_id)
    return result


# ─── kobo.sporulate ───────────────────────────────────────────────────────────


async def task_sporulate(
    sporeVertexId: str = "",
    agentDid: str = "",
    agentVertexId: str = "",
    blobCbor: str = "",
    revivalKeyHint: str = "",
    quorumN: int = 2,
    callerDid: str = "",
    **_: Any,
) -> dict[str, Any]:
    """Freeze agent state into a CBOR spore blob for houshi custody."""

    if not agentDid:
        return {"error": "agentDid required"}

    spore_id = sporeVertexId.split("/")[-1] if sporeVertexId else _uid("spore")
    spore_vid = sporeVertexId or f"at://{HOUSHI_DID}/ai.gftd.apps.houshi.spore/{spore_id}"
    now = _now()
    spore_hash = hashlib.sha256((blobCbor or agentDid).encode()).hexdigest()[:32]

    def _run() -> dict[str, Any]:
        with sync_cursor() as cur:
            # Mark kobo agent as dormant
            if agentVertexId:
                cur.execute(
                    "UPDATE vertex_kobo_agent SET status = 'dormant', updated_at = %s WHERE vertex_id = %s",
                    (now, agentVertexId),
                )
            # Insert spore record in houshi
            cur.execute(
                """
                INSERT INTO vertex_houshi_spore
                  (vertex_id, record_id, owner_did, label, status, stream_id,
                   agent_did, value_json, created_at, updated_at, sensitivity_ord,
                   origin_agent_did, origin_vertex_id, spore_hash, blob_cbor,
                   revival_key_hint, quorum_n, custody_count, germinated_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    spore_vid, _uid("rec"), HOUSHI_DID, "houshi_spore", "dormant", "",
                    KOBO_DID, json.dumps({"callerDid": callerDid}),
                    now, now, 0,
                    agentDid, agentVertexId or "",
                    spore_hash, blobCbor[:1000] if blobCbor else "",
                    revivalKeyHint or "", quorumN, 0, None,
                ),
            )
        return {
            "sporeVertexId": spore_vid,
            "sporeId": spore_id,
            "sporeHash": spore_hash,
            "agentDid": agentDid,
            "sporulatedAt": now,
        }

    result = await asyncio.to_thread(_run)
    LOG.info("sporulate: %s spore=%s quorumN=%d", agentDid, spore_id, quorumN)
    return result


# ─── kobo.germinate ───────────────────────────────────────────────────────────


async def task_germinate(
    sporeVertexId: str = "",
    quorumN: int = 2,
    newAgentDid: str = "",
    newAgentVertexId: str = "",
    originAgentDid: str = "",
    restoredEta: float = 0.5,
    callerDid: str = "",
    **_: Any,
) -> dict[str, Any]:
    """Revive an agent from spore with quorum confirmation."""

    if not sporeVertexId:
        return {"error": "sporeVertexId required", "germinated": False, "confirmedCount": 0}

    now = _now()

    def _run() -> dict[str, Any]:
        spore_row = fetch_one(
            "SELECT vertex_id, custody_count, quorum_n, origin_agent_did FROM vertex_houshi_spore WHERE vertex_id = %s LIMIT 1",
            (sporeVertexId,),
        )
        if not spore_row:
            return {"error": f"spore not found: {sporeVertexId}", "germinated": False, "confirmedCount": 0}

        _vid, custody_count, db_quorum_n, origin_did = spore_row
        effective_quorum = int(db_quorum_n or quorumN)
        confirmed_count = int(custody_count or 0) + 1

        with sync_cursor() as cur:
            cur.execute(
                "UPDATE vertex_houshi_spore SET custody_count = %s, updated_at = %s WHERE vertex_id = %s",
                (confirmed_count, now, sporeVertexId),
            )

            if confirmed_count >= effective_quorum:
                # Quorum reached — germinate
                cur.execute(
                    "UPDATE vertex_houshi_spore SET status = 'germinated', germinated_at = %s, updated_at = %s WHERE vertex_id = %s",
                    (now, now, sporeVertexId),
                )
                # Revive kobo agent
                if newAgentVertexId:
                    cur.execute(
                        "UPDATE vertex_kobo_agent SET status = 'active', updated_at = %s WHERE vertex_id = %s",
                        (now, newAgentVertexId),
                    )

                return {
                    "germinated": True,
                    "confirmedCount": confirmed_count,
                    "newAgentDid": newAgentDid or (origin_did or originAgentDid),
                    "germinatedAt": now,
                }

        return {
            "germinated": False,
            "confirmedCount": confirmed_count,
            "requiredCount": effective_quorum,
        }

    result = await asyncio.to_thread(_run)
    LOG.info(
        "germinate: spore=%s germinated=%s confirmed=%s",
        sporeVertexId.split("/")[-1], result.get("germinated"), result.get("confirmedCount"),
    )
    return result


# ─── worker entrypoint ────────────────────────────────────────────────────────


async def run_worker() -> None:
    gateway = os.environ.get("AGENTGATEWAY_MCP_URL", "127.0.0.1:8080")
    channel = create_langserver_channel(grpc_address=gateway)
    worker = LangServerWorker(channel)
    timeout_ms = int(os.environ.get("KOBO_TASK_TIMEOUT_MS", "120000"))

    registrations = {
        "kobo.bud_agent": task_bud_agent,
        "kobo.sporulate": task_sporulate,
        "kobo.germinate": task_germinate,
    }
    for task_type, fn in registrations.items():
        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(fn)

    LOG.info(
        "kobo zeebe worker registered %d task types via %s",
        len(registrations), gateway,
    )

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)
    task = asyncio.create_task(worker.work())
    await stop.wait()
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


def main() -> None:
    load_env_file()
    if not os.environ.get("RW_URL"):
        rw_url = load_keychain_secret(service="gftd.rw", account="ROOT_URL")
        if rw_url:
            os.environ["RW_URL"] = rw_url
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    os.environ.setdefault("AGENTGATEWAY_MCP_URL", "127.0.0.1:8080")
    os.environ.setdefault("RW_SYNC_POOL", "0")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
