"""
Zeebe worker for kinoko (きのこ) — fruiting body / PoNF consensus layer (ADR-2605071200).

Fruiting body analogy: a block forms when accumulated Shannon η-gated nutrient
flow exceeds the threshold (totalFlow ≥ 100, minEta ≥ 0.5). Proof of Nutrient
Flow (PoNF) consensus.

Subscribes to 1 domain job type:
  kinoko.check_flow_threshold — query mv_kabi_nutrient_flow and form a block if
                                 threshold is met

Run:
  python -m pymagatama.kinoko_worker_main

Env:
  AGENTGATEWAY_MCP_URL               — LangServer AgentGateway URL (default 127.0.0.1:8080)
  RW_URL                      — RisingWave postgres URL
  KINOKO_FLOW_THRESHOLD       — totalFlow threshold (default 100)
  KINOKO_ETA_THRESHOLD        — minEta threshold (default 0.5)
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

LOG = logging.getLogger("kinoko_worker")

KINOKO_DID = "did:web:kinoko.gftd.ai"

FLOW_THRESHOLD = float(os.environ.get("KINOKO_FLOW_THRESHOLD", "100"))
ETA_THRESHOLD = float(os.environ.get("KINOKO_ETA_THRESHOLD", "0.5"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uid(prefix: str) -> str:
    digest = hashlib.sha256(f"{prefix}{time.time_ns()}".encode()).hexdigest()[:12]
    return f"{prefix}-{digest}"


# ─── kinoko.check_flow_threshold ─────────────────────────────────────────────


async def task_check_flow_threshold(
    blockVertexId: str = "",
    lastBlockId: str = "",
    blockHash: str = "",
    **_: Any,
) -> dict[str, Any]:
    """Query nutrient flow MV and form a PoNF block if threshold is met."""

    def _run() -> dict[str, Any]:
        # Query the nutrient flow materialized view
        flow_row = fetch_one(
            """
            SELECT
              COALESCE(SUM(flow_value), 0) AS total_flow,
              COALESCE(MIN(eta), 1.0) AS min_eta,
              COALESCE(COUNT(DISTINCT src_vid), 0) AS participant_count
            FROM edge_kabi_hypha
            WHERE status = 'active'
            """,
            (),
        )

        total_flow = float(flow_row[0]) if flow_row else 0.0
        min_eta = float(flow_row[1]) if flow_row else 1.0
        participant_count = int(flow_row[2]) if flow_row else 0

        block_formed = (total_flow >= FLOW_THRESHOLD and min_eta >= ETA_THRESHOLD)

        if not block_formed:
            return {
                "blockFormed": False,
                "totalFlow": total_flow,
                "participantCount": participant_count,
                "minEta": min_eta,
            }

        # Form the block
        block_id = _uid("blk")
        block_vid = f"at://{KINOKO_DID}/ai.gftd.apps.kinoko.block/{block_id}"
        now = _now()
        snapshot_hash = hashlib.sha256(
            f"{total_flow}{min_eta}{participant_count}{now}".encode()
        ).hexdigest()[:32]

        with sync_cursor() as cur:
            cur.execute(
                """
                INSERT INTO vertex_kinoko_block
                  (vertex_id, record_id, owner_did, label, status, stream_id,
                   agent_did, value_json, created_at, updated_at, sensitivity_ord,
                   total_flow, participant_count, min_eta, snapshot_hash,
                   prev_block_id, formed_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    block_vid, _uid("rec"), KINOKO_DID, "kinoko_block", "active", "",
                    KINOKO_DID, json.dumps({"lastBlockId": lastBlockId}),
                    now, now, 0,
                    total_flow, participant_count, min_eta, snapshot_hash,
                    lastBlockId or None, now,
                ),
            )
            # Reset active hypha flows after block formation
            cur.execute(
                "UPDATE edge_kabi_hypha SET status = 'consumed', updated_at = %s WHERE status = 'active'",
                (now,),
            )

        return {
            "blockFormed": True,
            "blockVertexId": block_vid,
            "blockId": block_id,
            "totalFlow": total_flow,
            "participantCount": participant_count,
            "minEta": min_eta,
            "snapshotHash": snapshot_hash,
        }

    result = await asyncio.to_thread(_run)
    LOG.info(
        "check_flow_threshold: blockFormed=%s totalFlow=%.1f minEta=%.2f",
        result["blockFormed"], result["totalFlow"], result["minEta"],
    )
    return result


# ─── worker entrypoint ────────────────────────────────────────────────────────


async def run_worker() -> None:
    gateway = os.environ.get("AGENTGATEWAY_MCP_URL", "127.0.0.1:8080")
    channel = create_langserver_channel(grpc_address=gateway)
    worker = LangServerWorker(channel)
    timeout_ms = int(os.environ.get("KINOKO_TASK_TIMEOUT_MS", "60000"))

    registrations = {
        "kinoko.check_flow_threshold": task_check_flow_threshold,
    }
    for task_type, fn in registrations.items():
        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(fn)

    LOG.info(
        "kinoko zeebe worker registered %d task types via %s",
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
