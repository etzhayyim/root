"""
Zeebe worker for saikin (細菌) — bacteria horizontal transfer layer (ADR-2605072000).

Horizontal gene transfer (HGT) analogy: cross-actor signal propagation across
otherwise disconnected actor clusters. saikin probes the environment for novel
signals, transfers them horizontally to target actors, and forms cooperative
colonies of related signals.

Subscribes to 5 domain job types:
  saikin.probe_environment  — scan external sources for novel signals
  saikin.transfer_signal    — HGT-style copy of signal to target actor namespace
  saikin.form_colony        — group related signals into a cooperative colony
  saikin.lyse               — decompose and release a processed signal
  saikin.handoff_to_ki      — bridge saikin→ki: seed vertex_ki_absorb from a colony

Run:
  python -m pymagatama.saikin_worker_main

Env:
  AGENTGATEWAY_MCP_URL     — LangServer AgentGateway URL (default 127.0.0.1:8080)
  RW_URL            — RisingWave postgres URL
  SAIKIN_BATCH_SIZE — max signals per probe cycle (default 10)
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

from pymagatama.db_sync import fetch_all, fetch_one, sync_cursor
from pymagatama.local_agent_env import load_env_file, load_keychain_secret

LOG = logging.getLogger("saikin_worker")

SAIKIN_DID = "did:web:saikin.etzhayyim.com"
KOKE_DID = "did:web:koke.etzhayyim.com"
KI_DID = "did:web:ki.etzhayyim.com"

BATCH_SIZE = int(os.environ.get("SAIKIN_BATCH_SIZE", "10"))


# ─── helpers ──────────────────────────────────────────────────────────────


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uid(prefix: str) -> str:
    digest = hashlib.sha256(f"{prefix}{time.time_ns()}".encode()).hexdigest()[:12]
    return f"{prefix}-{digest}"


# ─── saikin.probe_environment ─────────────────────────────────────────────


async def task_probe_environment(**_: Any) -> dict[str, Any]:
    """Probe environment for novel signals not yet in koke fixation."""

    def _run() -> dict[str, Any]:
        rows = fetch_all(
            f"""
            SELECT vertex_id, signal_hash, input_kind, raw_ref
            FROM vertex_saikin_signal
            WHERE status = 'unprocessed'
            ORDER BY created_at ASC
            LIMIT {int(BATCH_SIZE)}
            """,
            (),
        )
        signals = [
            {
                "signalId": r[0].split("/")[-1],
                "vertexId": r[0],
                "signalHash": r[1] or "",
                "inputKind": r[2] or "text",
                "rawRef": r[3] or "",
            }
            for r in (rows or [])
        ]
        return {"signalCount": len(signals), "signals": signals}

    result = await asyncio.to_thread(_run)
    # Phase D2 (ADR-2605082000): embed routing decision so the topology can
    # use field-based conditional edges instead of a Python router callable.
    # Mirrors saikin_cycle._has_signals_gate exactly.
    result["nextRoute"] = "transfer" if int(result.get("signalCount") or 0) > 0 else "no_signals"
    LOG.info("probe_environment: found %d unprocessed signals", result["signalCount"])
    return result


# ─── saikin.transfer_signal ───────────────────────────────────────────────


async def task_transfer_signal(
    signalId: str = "",
    targetActorDid: str = "",
    signals: list[dict[str, Any]] | None = None,
    **_: Any,
) -> dict[str, Any]:
    """HGT-style horizontal transfer of a signal to a target actor namespace."""

    if not signalId and not (signals and len(signals) > 0):
        return {"error": "signalId or signals required"}

    if signals:
        sig = signals[0]
        signal_id = sig.get("signalId", "")
        raw_ref = sig.get("rawRef", "")
        input_kind = sig.get("inputKind", "text")
        target_did = targetActorDid or KOKE_DID
    else:
        signal_id = signalId
        raw_ref = ""
        input_kind = "text"
        target_did = targetActorDid or KOKE_DID

    transfer_id = _uid("hgt")
    now = _now()
    signal_hash = hashlib.sha256(raw_ref.encode()).hexdigest()[:32] if raw_ref else ""

    def _run() -> dict[str, Any]:
        with sync_cursor() as cur:
            cur.execute(
                """
                INSERT INTO edge_saikin_transfer
                  (edge_id, src_vid, dst_vid, relation_kind, value_json,
                   created_at, updated_at, owner_did, sensitivity_ord,
                   signal_id, target_actor_did, transfer_kind, transferred_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    transfer_id,
                    f"at://{SAIKIN_DID}/ai.gftd.apps.saikin.signal/{signal_id}",
                    f"at://{target_did}/",
                    "saikin_transfer",
                    json.dumps({"inputKind": input_kind, "signalHash": signal_hash}),
                    now, now, SAIKIN_DID, 0,
                    signal_id, target_did, "horizontal", now,
                ),
            )
            if signal_id:
                cur.execute(
                    "UPDATE vertex_saikin_signal SET status = 'transferred', updated_at = %s WHERE vertex_id LIKE %s",
                    (now, f"%{signal_id}%"),
                )
        return {
            "transferId": transfer_id,
            "signalId": signal_id,
            "targetActorDid": target_did,
            "status": "transferred",
            "transferredAt": now,
        }

    result = await asyncio.to_thread(_run)
    # Phase D2: route on transfer outcome — mirrors _transfer_outcome_gate.
    result["nextRoute"] = "form_colony" if result.get("status") == "transferred" else "lyse"
    LOG.info("transfer_signal: %s → %s", signal_id, target_did)
    return result


# ─── saikin.form_colony ───────────────────────────────────────────────────


async def task_form_colony(
    signalIds: list[str] | None = None,
    colonyLabel: str = "",
    **_: Any,
) -> dict[str, Any]:
    """Group related signals into a cooperative colony (biofilm analogy)."""

    if not signalIds:
        return {"error": "signalIds required"}

    colony_id = _uid("col")
    colony_vid = f"at://{SAIKIN_DID}/ai.gftd.apps.saikin.colony/{colony_id}"
    now = _now()
    member_count = len(signalIds)

    def _run() -> dict[str, Any]:
        with sync_cursor() as cur:
            cur.execute(
                """
                INSERT INTO vertex_saikin_colony
                  (vertex_id, record_id, owner_did, label, status, stream_id,
                   agent_did, value_json, created_at, updated_at, sensitivity_ord,
                   colony_label, member_count, formed_at, lysed_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    colony_vid, _uid("rec"), SAIKIN_DID,
                    colonyLabel or "saikin_colony", "active", "",
                    SAIKIN_DID, json.dumps({"signalIds": signalIds}),
                    now, now, 0,
                    colonyLabel or "", member_count, now, None,
                ),
            )
            for sid in signalIds:
                edge_id = _uid("cmb")
                cur.execute(
                    """
                    INSERT INTO edge_saikin_member
                      (edge_id, src_vid, dst_vid, relation_kind, value_json,
                       created_at, updated_at, owner_did, sensitivity_ord,
                       colony_id, signal_id, joined_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        edge_id, colony_vid,
                        f"at://{SAIKIN_DID}/ai.gftd.apps.saikin.signal/{sid}",
                        "saikin_member", json.dumps({}),
                        now, now, SAIKIN_DID, 0,
                        colony_id, sid, now,
                    ),
                )
        return {
            "colonyId": colony_id,
            "colonyVertexId": colony_vid,
            "memberCount": member_count,
            "status": "active",
            "formedAt": now,
        }

    result = await asyncio.to_thread(_run)
    LOG.info("form_colony: %s with %d members", colony_id, member_count)
    return result


# ─── saikin.lyse ──────────────────────────────────────────────────────────


async def task_lyse(
    signalId: str = "",
    reason: str = "",
    **_: Any,
) -> dict[str, Any]:
    """Decompose and release a processed signal (lysis analogy)."""

    if not signalId:
        return {"error": "signalId required"}

    now = _now()

    def _run() -> dict[str, Any]:
        row = fetch_one(
            "SELECT vertex_id FROM vertex_saikin_signal WHERE vertex_id LIKE %s LIMIT 1",
            (f"%{signalId}%",),
        )
        if not row:
            return {"error": f"signal not found: {signalId}"}

        vid = row[0]
        with sync_cursor() as cur:
            cur.execute(
                "UPDATE vertex_saikin_signal SET status = 'lysed', updated_at = %s WHERE vertex_id = %s",
                (now, vid),
            )
        return {
            "lysed": True,
            "signalId": signalId,
            "reason": reason,
            "lysedAt": now,
        }

    result = await asyncio.to_thread(_run)
    LOG.info("lyse: %s reason=%s", signalId, reason)
    return result


# ─── saikin.handoff_to_ki ────────────────────────────────────────────────


async def task_handoff_to_ki(
    colonyId: str = "",
    signalId: str = "",
    **_: Any,
) -> dict[str, Any]:
    """Bridge saikin→ki: seed a vertex_ki_absorb row from a formed colony."""

    if not colonyId and not signalId:
        return {"error": "colonyId or signalId required"}

    absorb_id = _uid("xyl")
    absorb_vid = f"at://{KI_DID}/ai.gftd.apps.ki.absorb/{absorb_id}"
    now = _now()

    def _run() -> dict[str, Any]:
        # Resolve source vertex: prefer colony, fall back to signal
        source_vid = ""
        input_kind = "text"
        content_snippet = ""

        if colonyId:
            colony = fetch_one(
                "SELECT vertex_id, colony_label, value_json FROM vertex_saikin_colony WHERE vertex_id LIKE %s LIMIT 1",
                (f"%{colonyId}%",),
            )
            if colony:
                source_vid = colony[0]
                content_snippet = colony[1] or ""
                try:
                    val = json.loads(colony[2] or "{}")
                    content_snippet = content_snippet or str(val.get("signalIds", ""))
                except (json.JSONDecodeError, TypeError):
                    pass

        if not source_vid and signalId:
            sig = fetch_one(
                "SELECT vertex_id, input_kind, raw_ref FROM vertex_saikin_signal WHERE vertex_id LIKE %s LIMIT 1",
                (f"%{signalId}%",),
            )
            if sig:
                source_vid = sig[0]
                input_kind = sig[1] or "text"
                content_snippet = sig[2] or ""

        if not source_vid:
            return {"error": f"neither colony {colonyId!r} nor signal {signalId!r} found"}

        content_hash = hashlib.sha256(content_snippet.encode()).hexdigest()[:32]

        with sync_cursor() as cur:
            cur.execute(
                """
                INSERT INTO vertex_ki_absorb
                  (vertex_id, record_id, owner_did, label, status, stream_id,
                   agent_did, value_json, created_at, updated_at, sensitivity_ord,
                   source_vertex_id, input_kind, content_hash, absorbed_at, synthesized_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    absorb_vid, _uid("rec"), KI_DID, "ki_absorb", "absorbed", "",
                    SAIKIN_DID, json.dumps({"content": content_snippet[:500], "saikinColonyId": colonyId}),
                    now, now, 0,
                    source_vid, input_kind, content_hash, now, None,
                ),
            )
        return {
            "kiAbsorbId": absorb_id,
            "kiAbsorbVertexId": absorb_vid,
            "sourceVertexId": source_vid,
            "handedOffAt": now,
        }

    result = await asyncio.to_thread(_run)
    LOG.info(
        "handoff_to_ki: colony=%s signal=%s absorb=%s",
        colonyId, signalId, result.get("kiAbsorbId"),
    )
    return result


# ─── worker entrypoint ────────────────────────────────────────────────────


async def run_worker() -> None:
    gateway = os.environ.get("AGENTGATEWAY_MCP_URL", "127.0.0.1:8080")
    channel = create_langserver_channel(grpc_address=gateway)
    worker = LangServerWorker(channel)
    timeout_ms = int(os.environ.get("SAIKIN_TASK_TIMEOUT_MS", "120000"))

    registrations = {
        "saikin.probe_environment": task_probe_environment,
        "saikin.transfer_signal": task_transfer_signal,
        "saikin.form_colony": task_form_colony,
        "saikin.lyse": task_lyse,
        "saikin.handoff_to_ki": task_handoff_to_ki,
    }
    for task_type, fn in registrations.items():
        worker.task(task_type=task_type, single_value=False, timeout_ms=timeout_ms)(fn)

    LOG.info(
        "saikin zeebe worker registered %d task types via %s",
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
