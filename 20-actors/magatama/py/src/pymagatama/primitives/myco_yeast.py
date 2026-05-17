"""Myco-Yeast artificial organism Zeebe workers (ADR-2605071200).

Semantic task implementations for the three-layer architecture:
  kobo  (酵母) — individual agents:   bud / germinate / sporulate
  kabi  (カビ) — mycelial network:    anastomosis probe
  kinoko (キノコ) — fruiting body:    PoNF flow threshold check
  hakkou (発酵) — fermentation:       create record / LLM transform / finalize

Task types registered via register():
  kobo.bud_agent
  kobo.germinate
  kobo.sporulate
  kabi.anastomosis_probe
  kinoko.check_flow_threshold
  hakkou.create_ferment_record
  hakkou.llm_transform
  hakkou.finalize_ferment
"""

from __future__ import annotations

import datetime as _dt
import logging
from typing import Any

from pymagatama import llm
from pymagatama.db_sync import sync_cursor

logger = logging.getLogger(__name__)

_NOW = lambda: _dt.datetime.utcnow().isoformat() + "Z"


# ---------------------------------------------------------------------------
# kobo 酵母 — individual agent lifecycle
# ---------------------------------------------------------------------------

def task_kobo_bud_agent(
    parentDid: str = "",
    childDid: str = "",
    childVertexId: str = "",
    childRole: str = "agent",
    parentEta: float = 0.5,
    callerDid: str = "",
    buddingEdgeId: str = "",
) -> dict:
    """Insert vertex_kobo_agent (child) + edge_kobo_budding in one transaction."""
    if not (parentDid and childDid and childVertexId and buddingEdgeId):
        return {"error": "parentDid, childDid, childVertexId, buddingEdgeId required"}
    now = _NOW()
    try:
        with sync_cursor() as cur:
            cur.execute(
                """
                INSERT INTO vertex_kobo_agent
                  (vertex_id, agent_did, parent_did, role, status, eta, stress_score,
                   created_at, owner_did, sensitivity_ord)
                SELECT %s, %s, %s, %s, 'active', %s, 0, %s, %s, 1
                WHERE NOT EXISTS (
                  SELECT 1 FROM vertex_kobo_agent WHERE vertex_id = %s
                )
                """,
                (childVertexId, childDid, parentDid, childRole,
                 float(parentEta), now, callerDid or parentDid,
                 childVertexId),
            )
            cur.execute(
                """
                INSERT INTO edge_kobo_budding
                  (edge_id, src_vid, dst_vid, created_at, owner_did, sensitivity_ord)
                SELECT %s, %s, %s, %s, %s, 1
                WHERE NOT EXISTS (
                  SELECT 1 FROM edge_kobo_budding WHERE edge_id = %s
                )
                """,
                (buddingEdgeId, parentDid, childVertexId, now,
                 callerDid or parentDid, buddingEdgeId),
            )
        return {"ok": True, "childVertexId": childVertexId}
    except Exception as exc:
        logger.exception("kobo.bud_agent failed")
        return {"ok": False, "error": str(exc)}


def task_kobo_germinate(
    sporeVertexId: str = "",
    quorumN: int = 2,
    newAgentDid: str = "",
    newAgentVertexId: str = "",
    originAgentDid: str = "",
    restoredEta: float = 0.5,
    callerDid: str = "",
) -> dict:
    """Check custody quorum, revive agent from spore, mark spore germinated.

    Returns germinated=True if quorum was met and agent was revived.
    """
    if not (sporeVertexId and newAgentDid and newAgentVertexId):
        return {"error": "sporeVertexId, newAgentDid, newAgentVertexId required",
                "germinated": False}
    try:
        with sync_cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM edge_houshi_custody
                WHERE src_vid = %s AND custody_confirmed = true
                """,
                (sporeVertexId,),
            )
            row = cur.fetchone()
            confirmed_count = int(row[0]) if row else 0

        if confirmed_count < quorumN:
            return {"germinated": False, "confirmedCount": confirmed_count,
                    "quorumN": quorumN}

        now = _NOW()
        with sync_cursor() as cur:
            cur.execute(
                """
                INSERT INTO vertex_kobo_agent
                  (vertex_id, agent_did, parent_did, status, eta, stress_score,
                   created_at, owner_did, sensitivity_ord)
                SELECT %s, %s, %s, 'active', %s, 0, %s, %s, 1
                WHERE NOT EXISTS (
                  SELECT 1 FROM vertex_kobo_agent WHERE vertex_id = %s
                )
                """,
                (newAgentVertexId, newAgentDid, originAgentDid,
                 float(restoredEta), now, callerDid or originAgentDid,
                 newAgentVertexId),
            )
            cur.execute(
                """
                INSERT INTO vertex_houshi_spore
                  (vertex_id, germinated_at, status)
                SELECT %s, %s, 'germinated'
                ON CONFLICT (vertex_id) DO UPDATE
                  SET germinated_at = EXCLUDED.germinated_at,
                      status = EXCLUDED.status
                """,
                (sporeVertexId, now),
            )
        return {"germinated": True, "confirmedCount": confirmed_count,
                "newAgentVertexId": newAgentVertexId}
    except Exception as exc:
        logger.exception("kobo.germinate failed")
        return {"germinated": False, "error": str(exc)}


def task_kobo_sporulate(
    sporeVertexId: str = "",
    agentDid: str = "",
    agentVertexId: str = "",
    blobCbor: str = "",
    revivalKeyHint: str = "",
    quorumN: int = 2,
    callerDid: str = "",
) -> dict:
    """Insert houshi spore and update kobo_agent status to sporulated."""
    if not (sporeVertexId and agentDid and agentVertexId):
        return {"error": "sporeVertexId, agentDid, agentVertexId required"}
    now = _NOW()
    try:
        with sync_cursor() as cur:
            cur.execute(
                """
                INSERT INTO vertex_houshi_spore
                  (vertex_id, agent_did, blob_cbor, revival_key_hint, quorum_n,
                   status, created_at, owner_did, sensitivity_ord)
                SELECT %s, %s, %s, %s, %s, 'dormant', %s, %s, 1
                WHERE NOT EXISTS (
                  SELECT 1 FROM vertex_houshi_spore WHERE vertex_id = %s
                )
                """,
                (sporeVertexId, agentDid, blobCbor, revivalKeyHint,
                 int(quorumN), now, callerDid or agentDid, sporeVertexId),
            )
            cur.execute(
                """
                INSERT INTO vertex_kobo_agent (vertex_id, status, updated_at)
                SELECT %s, 'sporulated', %s
                ON CONFLICT (vertex_id) DO UPDATE
                  SET status = 'sporulated', updated_at = EXCLUDED.updated_at
                """,
                (agentVertexId, now),
            )
        return {"ok": True, "sporeVertexId": sporeVertexId}
    except Exception as exc:
        logger.exception("kobo.sporulate failed")
        return {"ok": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# kabi カビ — mycelial network anastomosis
# ---------------------------------------------------------------------------

def task_kabi_anastomosis_probe(
    networkADid: str = "",
    networkBDid: str = "",
    edgeId: str = "",
    callerDid: str = "",
) -> dict:
    """LLM compatibility probe + INSERT edge_kabi_anastomosis.

    Returns probeResult dict with compatible:bool and compatibility_score:float.
    """
    if not (networkADid and networkBDid and edgeId):
        return {"error": "networkADid, networkBDid, edgeId required",
                "probeResult": {"compatible": False}}

    system = (
        "You are a mycelial network compatibility analyst. "
        "Assess whether two agent networks can safely merge (anastomosis). "
        "Return ONE JSON object with keys: compatible (bool), "
        "compatibility_score (0.0-1.0), reason (string, max 120 chars)."
    )
    user = (
        f"Network A DID: {networkADid}\n"
        f"Network B DID: {networkBDid}\n"
        "Assess anastomosis compatibility."
    )
    llm_result = llm.call_tier_json(
        "classifier",
        system=system,
        user=user,
        max_tokens=200,
        temperature=0.1,
    )
    if not llm_result.get("ok"):
        return {"error": llm_result.get("error", "llm failed"),
                "probeResult": {"compatible": False}}

    probe = llm_result.get("data") or {}
    compatible = bool(probe.get("compatible", False))
    score = float(probe.get("compatibility_score", 0.0))
    reason = str(probe.get("reason", ""))

    now = _NOW()
    try:
        with sync_cursor() as cur:
            cur.execute(
                """
                INSERT INTO edge_kabi_anastomosis
                  (edge_id, src_vid, dst_vid, compatible, compatibility_score,
                   probe_reason, created_at, owner_did, sensitivity_ord)
                SELECT %s, %s, %s, %s, %s, %s, %s, %s, 1
                WHERE NOT EXISTS (
                  SELECT 1 FROM edge_kabi_anastomosis WHERE edge_id = %s
                )
                """,
                (edgeId, networkADid, networkBDid, compatible, score,
                 reason[:500], now, callerDid or networkADid, edgeId),
            )
    except Exception as exc:
        logger.exception("kabi.anastomosis_probe db write failed")
        return {"error": str(exc), "probeResult": {"compatible": False}}

    return {"probeResult": {"compatible": compatible,
                            "compatibility_score": score,
                            "reason": reason}}


# ---------------------------------------------------------------------------
# kinoko キノコ — PoNF fruiting body / consensus
# ---------------------------------------------------------------------------

def task_kinoko_check_flow_threshold(
    blockVertexId: str = "",
    lastBlockId: str = "",
    blockHash: str = "",
) -> dict:
    """Query mv_kabi_nutrient_flow; form PoNF block if threshold met.

    PoNF threshold: totalFlow >= 100 AND minEta >= 0.5.
    Returns blockFormed:bool, totalFlow, participantCount, minEta.
    """
    try:
        with sync_cursor() as cur:
            cur.execute(
                "SELECT SUM(total_flow), COUNT(*), AVG(avg_eta) "
                "FROM mv_kabi_nutrient_flow"
            )
            row = cur.fetchone()
    except Exception as exc:
        logger.exception("kinoko.check_flow_threshold query failed")
        return {"blockFormed": False, "error": str(exc)}

    total_flow = float(row[0] or 0)
    participant_count = int(row[1] or 0)
    min_eta = float(row[2] or 0.0)

    if total_flow < 100 or min_eta < 0.5:
        return {"blockFormed": False, "totalFlow": total_flow,
                "participantCount": participant_count, "minEta": min_eta}

    if not blockVertexId:
        return {"error": "blockVertexId required when threshold met",
                "blockFormed": False}

    now = _NOW()
    try:
        with sync_cursor() as cur:
            cur.execute(
                """
                INSERT INTO vertex_kinoko_block
                  (vertex_id, prev_block_id, block_hash, total_flow,
                   participant_count, eta_min_used, block_status, status,
                   created_at, owner_did, sensitivity_ord)
                SELECT %s, %s, %s, %s, %s, %s, 'finalized', 'active', %s,
                       'did:web:kinoko.etzhayyim.com', 1
                WHERE NOT EXISTS (
                  SELECT 1 FROM vertex_kinoko_block WHERE vertex_id = %s
                )
                """,
                (blockVertexId, lastBlockId, blockHash, total_flow,
                 participant_count, min_eta, now, blockVertexId),
            )
    except Exception as exc:
        logger.exception("kinoko.check_flow_threshold block insert failed")
        return {"blockFormed": False, "error": str(exc)}

    return {"blockFormed": True, "blockVertexId": blockVertexId,
            "totalFlow": total_flow, "participantCount": participant_count,
            "minEta": min_eta}


# ---------------------------------------------------------------------------
# hakkou 発酵 — fermentation pipeline
# ---------------------------------------------------------------------------

def task_hakkou_create_ferment_record(
    fermentVertexId: str = "",
    agentDid: str = "",
    inputKind: str = "",
    inputRef: str = "",
    outputKind: str = "",
    callerDid: str = "",
) -> dict:
    """Insert vertex_hakkou_ferment with status=running."""
    if not (fermentVertexId and agentDid and inputKind):
        return {"error": "fermentVertexId, agentDid, inputKind required"}
    now = _NOW()
    try:
        with sync_cursor() as cur:
            cur.execute(
                """
                INSERT INTO vertex_hakkou_ferment
                  (vertex_id, agent_did, input_kind, input_ref, output_kind,
                   status, created_at, owner_did, sensitivity_ord)
                SELECT %s, %s, %s, %s, %s, 'running', %s, %s, 1
                WHERE NOT EXISTS (
                  SELECT 1 FROM vertex_hakkou_ferment WHERE vertex_id = %s
                )
                """,
                (fermentVertexId, agentDid, inputKind, inputRef, outputKind,
                 now, callerDid or agentDid, fermentVertexId),
            )
        return {"ok": True, "fermentVertexId": fermentVertexId}
    except Exception as exc:
        logger.exception("hakkou.create_ferment_record failed")
        return {"ok": False, "error": str(exc)}


def task_hakkou_llm_transform(
    inputKind: str = "",
    inputRef: str = "",
    outputKind: str = "",
) -> dict:
    """LLM fermentation: structured knowledge extraction from raw input.

    Returns fermentOutput dict with the extracted structured content.
    """
    if not (inputKind and outputKind):
        return {"error": "inputKind, outputKind required"}

    system = (
        "You are a fermentation knowledge engine. "
        "Transform raw input into structured knowledge. "
        "Extract key facts, relationships, and insights. "
        "Be precise and citation-grounded. "
        "Return ONE JSON object with keys: "
        "summary (string), facts (array of strings), "
        "relationships (array of {subject, predicate, object}), "
        "confidence (0.0-1.0)."
    )
    user = (
        f"Ferment the following {inputKind} input into a structured {outputKind}. "
        f"Input reference: {inputRef}"
    )
    result = llm.call_tier_json(
        "classifier",
        system=system,
        user=user,
        max_tokens=800,
        temperature=0.1,
    )
    if not result.get("ok"):
        return {"error": result.get("error", "llm failed"), "fermentOutput": {}}
    return {"fermentOutput": result.get("data") or {}}


def task_hakkou_finalize_ferment(
    fermentVertexId: str = "",
    outputVertexId: str = "",
    ethanolHash: str = "",
    co2AuditRef: str = "",
) -> dict:
    """Update vertex_hakkou_ferment with output ref, ethanol hash, status=done."""
    if not fermentVertexId:
        return {"error": "fermentVertexId required"}
    now = _NOW()
    try:
        with sync_cursor() as cur:
            cur.execute(
                """
                INSERT INTO vertex_hakkou_ferment
                  (vertex_id, output_vertex_id, ethanol_hash, co2_audit_ref,
                   status, updated_at)
                SELECT %s, %s, %s, %s, 'done', %s
                ON CONFLICT (vertex_id) DO UPDATE
                  SET output_vertex_id = EXCLUDED.output_vertex_id,
                      ethanol_hash = EXCLUDED.ethanol_hash,
                      co2_audit_ref = EXCLUDED.co2_audit_ref,
                      status = 'done',
                      updated_at = EXCLUDED.updated_at
                """,
                (fermentVertexId, outputVertexId, ethanolHash,
                 co2AuditRef, now),
            )
        return {"ok": True, "fermentVertexId": fermentVertexId}
    except Exception as exc:
        logger.exception("hakkou.finalize_ferment failed")
        return {"ok": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# registration
# ---------------------------------------------------------------------------

def register(worker: Any, *, timeout_ms: int = 300_000) -> None:
    worker.task(task_type="kobo.bud_agent", single_value=False,
                timeout_ms=timeout_ms)(
        lambda parentDid="", childDid="", childVertexId="", childRole="agent",
               parentEta=0.5, callerDid="", buddingEdgeId="": task_kobo_bud_agent(
            parentDid=parentDid, childDid=childDid, childVertexId=childVertexId,
            childRole=childRole, parentEta=parentEta, callerDid=callerDid,
            buddingEdgeId=buddingEdgeId,
        )
    )

    worker.task(task_type="kobo.germinate", single_value=False,
                timeout_ms=timeout_ms)(
        lambda sporeVertexId="", quorumN=2, newAgentDid="", newAgentVertexId="",
               originAgentDid="", restoredEta=0.5, callerDid="": task_kobo_germinate(
            sporeVertexId=sporeVertexId, quorumN=quorumN, newAgentDid=newAgentDid,
            newAgentVertexId=newAgentVertexId, originAgentDid=originAgentDid,
            restoredEta=restoredEta, callerDid=callerDid,
        )
    )

    worker.task(task_type="kobo.sporulate", single_value=False,
                timeout_ms=timeout_ms)(
        lambda sporeVertexId="", agentDid="", agentVertexId="", blobCbor="",
               revivalKeyHint="", quorumN=2, callerDid="": task_kobo_sporulate(
            sporeVertexId=sporeVertexId, agentDid=agentDid,
            agentVertexId=agentVertexId, blobCbor=blobCbor,
            revivalKeyHint=revivalKeyHint, quorumN=quorumN, callerDid=callerDid,
        )
    )

    worker.task(task_type="kabi.anastomosis_probe", single_value=False,
                timeout_ms=timeout_ms)(
        lambda networkADid="", networkBDid="", edgeId="",
               callerDid="": task_kabi_anastomosis_probe(
            networkADid=networkADid, networkBDid=networkBDid,
            edgeId=edgeId, callerDid=callerDid,
        )
    )

    worker.task(task_type="kinoko.check_flow_threshold", single_value=False,
                timeout_ms=timeout_ms)(
        lambda blockVertexId="", lastBlockId="",
               blockHash="": task_kinoko_check_flow_threshold(
            blockVertexId=blockVertexId, lastBlockId=lastBlockId,
            blockHash=blockHash,
        )
    )

    worker.task(task_type="hakkou.create_ferment_record", single_value=False,
                timeout_ms=timeout_ms)(
        lambda fermentVertexId="", agentDid="", inputKind="", inputRef="",
               outputKind="", callerDid="": task_hakkou_create_ferment_record(
            fermentVertexId=fermentVertexId, agentDid=agentDid,
            inputKind=inputKind, inputRef=inputRef, outputKind=outputKind,
            callerDid=callerDid,
        )
    )

    worker.task(task_type="hakkou.llm_transform", single_value=False,
                timeout_ms=max(timeout_ms, 120_000))(
        lambda inputKind="", inputRef="", outputKind="": task_hakkou_llm_transform(
            inputKind=inputKind, inputRef=inputRef, outputKind=outputKind,
        )
    )

    worker.task(task_type="hakkou.finalize_ferment", single_value=False,
                timeout_ms=timeout_ms)(
        lambda fermentVertexId="", outputVertexId="", ethanolHash="",
               co2AuditRef="": task_hakkou_finalize_ferment(
            fermentVertexId=fermentVertexId, outputVertexId=outputVertexId,
            ethanolHash=ethanolHash, co2AuditRef=co2AuditRef,
        )
    )
