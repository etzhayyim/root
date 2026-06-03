"""Shared kami-cine pipeline helpers for the `cine_generate_scene` and
`cine_generate_panel` LangGraph graphs.

Bridges the 8-stage cinematic pipeline (WIT `etzhayyim:kami-cine@1.0.0`,
`40-engine/kami-engine/wit/cine/package.wit`) to mangaka's pod-side
persistence:

  - shared cine ledger:  graphar.vertex_cine_stage  (one row per stage
                         artifact, NSID = com.etzhayyim.apps.cine.<stage>)
  - mangaka run summary: graphar.vertex_mangaka_cine_run
  - mangaka panel bind:  graphar.vertex_mangaka_cine_panel

All writes go to RisingWave PG :4566 via asyncpg per ADR-2605111200 — pods
are the sole writers, CF Workers never hold HYPERDRIVE.

The 8 lexicons under `00-contracts/lexicons/com/etzhayyim/apps/cine/` are the
contract that this module implements; field names here match those JSON
schemas 1:1 so the same payload dict can later be POSTed verbatim to PDS
`com.atproto.repo.createRecord` if external federation is enabled.
"""

from __future__ import annotations

import json
import logging
import os
import secrets
import time
from typing import Any, Iterable

import psycopg

_log = logging.getLogger(__name__)

_APP_DID = os.environ.get("MANGAKA_APP_DID", "did:web:mangaka.etzhayyim.com")
_RW_URL = os.environ.get("RW_URL", "")
_ORG_DID = os.environ.get("MANGAKA_ORG_DID", "anon")

STAGE_NAMES: tuple[str, ...] = (
    "worldModel",
    "usdScene",
    "neuralGeom",
    "temporalField",
    "neuralRender",
    "diffusionPass",
    "exrSeq",
    "encode",
)

# Default per-stage producer DIDs. Override per-graph if you stand up
# specialized actor DIDs (e.g. did:web:mangaka.etzhayyim.com:actor:storyboarder).
_DEFAULT_PRODUCER_DIDS: dict[str, str] = {
    "worldModel":    f"{_APP_DID}:actor:storyboarder",
    "usdScene":      f"{_APP_DID}:actor:layoutDesigner",
    "neuralGeom":    f"{_APP_DID}:actor:geomReconstructor",
    "temporalField": f"{_APP_DID}:actor:temporalSolver",
    "neuralRender":  f"{_APP_DID}:actor:neuralRenderer",
    "diffusionPass": f"{_APP_DID}:actor:cinematicRefiner",
    "exrSeq":        f"{_APP_DID}:actor:compositor",
    "encode":        f"{_APP_DID}:actor:finalizer",
}


# ── identifiers ────────────────────────────────────────────────────────────

# RFC4122-like 13-char base32 — collision-safe within a session, matches
# AT Protocol TID feel without dragging in the full TID lib.
_B32 = "234567abcdefghijklmnopqrstuvwxyz"

def new_rkey(prefix: str = "") -> str:
    suffix = "".join(_B32[secrets.randbelow(32)] for _ in range(13))
    return f"{prefix}{suffix}" if prefix else suffix


def new_run_id() -> str:
    return f"run-{new_rkey()}"


def cine_vertex_id(stage: str, rkey: str, producer_did: str | None = None) -> str:
    did = producer_did or _APP_DID
    return f"at://{did}/com.etzhayyim.apps.cine.{stage}/{rkey}"


def mangaka_vertex_id(kind: str, rkey: str) -> str:
    return f"at://{_APP_DID}/com.etzhayyim.mangaka.{kind}/{rkey}"


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ── ledger writes ──────────────────────────────────────────────────────────

async def record_stage(
    *,
    stage: str,
    pipeline_run_id: str,
    subject_kind: str,
    subject_ref: str,
    payload: dict[str, Any],
    producer_did: str | None = None,
    asset_cid: str | None = None,
    rw_url: str | None = None,
) -> dict[str, Any]:
    """INSERT one com.etzhayyim.apps.cine.<stage> artifact row.

    `payload` MUST be the per-stage lexicon body (e.g. for worldModel:
    {prompt, style, referenceCids, worldKind, extentsCm, modelCid, seed,
    tokenCount}). Stored as JSON blob in payload_jsonld; structured fields
    (assetCid, producerDid, createdAt) are projected to columns for cheap
    look-up.

    Returns:
        {
            "stage": str,
            "rkey": str,
            "vertex_id": str,
            "createdAt": str,
        }
    """
    if stage not in STAGE_NAMES:
        return {"error": f"unknown stage {stage!r}; valid: {STAGE_NAMES}"}
    url = rw_url or _RW_URL
    if not url:
        return {"error": "RW_URL not configured"}

    producer = producer_did or _DEFAULT_PRODUCER_DIDS[stage]
    rkey = new_rkey(prefix=f"{stage[:3]}-")
    vid = cine_vertex_id(stage, rkey, producer)
    created = now_iso()

    conn = await psycopg.AsyncConnection.connect(url, autocommit=True)
    try:
        cur = conn.cursor()
        await cur.execute(
            "DELETE FROM graphar.vertex_cine_stage WHERE vertex_id = %s", (vid,)
        )
        await cur.execute(
            "INSERT INTO graphar.vertex_cine_stage "
            "(vertex_id, _seq, stage, pipeline_run_id, subject_kind, subject_ref, "
            " asset_cid, payload_jsonld, producer_did, actor_did, org_did, created_at) "
            "VALUES (%s, 0, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                vid,
                stage,
                pipeline_run_id,
                subject_kind,
                subject_ref,
                asset_cid,
                json.dumps(payload, separators=(",", ":")),
                producer,
                producer,
                _ORG_DID,
                created,
            ),
        )
    finally:
        await conn.close()

    return {"stage": stage, "rkey": rkey, "vertex_id": vid, "createdAt": created}


async def record_run(
    *,
    pipeline_run_id: str,
    subject_kind: str,
    subject_ref: str,
    stages_completed: Iterable[str],
    scene_cids: dict[str, str | None] | None = None,
    status: str = "scene_ready",
    producer_did: str | None = None,
    rw_url: str | None = None,
) -> dict[str, Any]:
    """Upsert a vertex_mangaka_cine_run row tracking which stages this run
    completed and the per-stage artifact CIDs.

    Called at the end of `cine_generate_scene` (status='scene_ready') and
    again at the end of `cine_generate_panel` (status='panels_rendered').
    """
    url = rw_url or _RW_URL
    if not url:
        return {"error": "RW_URL not configured"}

    producer = producer_did or _APP_DID
    vid = mangaka_vertex_id("cineRun", pipeline_run_id)
    created = now_iso()
    cids = scene_cids or {}

    conn = await psycopg.AsyncConnection.connect(url, autocommit=True)
    try:
        cur = conn.cursor()
        await cur.execute(
            "DELETE FROM graphar.vertex_mangaka_cine_run WHERE vertex_id = %s",
            (vid,),
        )
        await cur.execute(
            "INSERT INTO graphar.vertex_mangaka_cine_run "
            "(vertex_id, _seq, pipeline_run_id, subject_kind, subject_ref, "
            " stages_completed, scene_world_cid, scene_usd_cid, scene_geom_cid, "
            " scene_temporal_cid, status, producer_did, actor_did, org_did, created_at) "
            "VALUES (%s, 0, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                vid,
                pipeline_run_id,
                subject_kind,
                subject_ref,
                ",".join(stages_completed),
                cids.get("worldModel"),
                cids.get("usdScene"),
                cids.get("neuralGeom"),
                cids.get("temporalField"),
                status,
                producer,
                producer,
                _ORG_DID,
                created,
            ),
        )
    finally:
        await conn.close()

    return {"vertex_id": vid, "status": status, "createdAt": created}


async def record_panel(
    *,
    panel_rkey: str,
    page_rkey: str | None,
    pipeline_run_id: str,
    render_blob_key: str | None,
    refined_blob_key: str | None,
    panel_blob_key: str | None,
    score: int = 0,
    producer_did: str | None = None,
    rw_url: str | None = None,
) -> dict[str, Any]:
    """INSERT one finalized panel binding (output of cine_generate_panel)."""
    url = rw_url or _RW_URL
    if not url:
        return {"error": "RW_URL not configured"}

    producer = producer_did or _APP_DID
    vid = mangaka_vertex_id("cinePanel", f"{panel_rkey}-{pipeline_run_id}")
    created = now_iso()

    conn = await psycopg.AsyncConnection.connect(url, autocommit=True)
    try:
        cur = conn.cursor()
        await cur.execute(
            "DELETE FROM graphar.vertex_mangaka_cine_panel WHERE vertex_id = %s",
            (vid,),
        )
        await cur.execute(
            "INSERT INTO graphar.vertex_mangaka_cine_panel "
            "(vertex_id, _seq, panel_rkey, page_rkey, pipeline_run_id, "
            " render_blob_key, refined_blob_key, panel_blob_key, score, "
            " producer_did, actor_did, org_did, created_at) "
            "VALUES (%s, 0, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (
                vid,
                panel_rkey,
                page_rkey,
                pipeline_run_id,
                render_blob_key,
                refined_blob_key,
                panel_blob_key,
                int(score),
                producer,
                producer,
                _ORG_DID,
                created,
            ),
        )
    finally:
        await conn.close()

    return {"vertex_id": vid, "panel_rkey": panel_rkey, "createdAt": created}
