"""
yardOps.* — LangServer handlers for yard / dock-door coordination.

Task types:
  yardOps.slot.allocate
  yardOps.trailer.persist
  yardOps.dockDoor.select
  yardOps.dockJob.persist
  loadingRobot.mission.dispatch     (downstream trigger)
  yardOps.dockJob.complete
  yardOps.dockSchedule.read

Cost-compression role: dockDoor.select is the dwell-time minimizer.
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
import uuid
from typing import Any

LOG = logging.getLogger("yard_ops.primitive")

_YARD_DID = "did:web:yard-ops.etzhayyim.com"
_ROBOT_DID = "did:web:robot.etzhayyim.com:loading-robot"


def _now_iso() -> str:
    return _dt.datetime.now(tz=_dt.UTC).strftime("%Y-%m-%d %H:%M:%S")


def _vid(kind: str) -> str:
    stamp = _dt.datetime.now(tz=_dt.UTC).strftime("%Y%m%d%H%M%S")
    return f"at://{_YARD_DID}/com.etzhayyim.apps.yardOps.{kind}/{stamp}-{uuid.uuid4().hex[:8]}"


def _execute(sql_str: str, params: dict) -> bool:
    try:
        from sqlalchemy import text
        from pymagatama.db_alchemy import sa_rowcount
        sa_rowcount(text(sql_str), params)
        return True
    except Exception as exc:
        LOG.warning("yard_ops execute failed: %s", exc)
        return False


def _query(sql_str: str, params: dict) -> list[Any]:
    try:
        from sqlalchemy import text
        from pymagatama.db_alchemy import sa_query
        return sa_query(text(sql_str), params)
    except Exception as exc:
        LOG.warning("yard_ops query failed: %s", exc)
        return []


# ── Trailer check-in ────────────────────────────────────────────────────────

async def task_yard_ops_slot_allocate(
    trailerPlate: str = "",
    carrierDid: str = "",
    appointmentId: str = "",
) -> dict:
    suffix = uuid.uuid4().hex[:3].upper()
    return {"ok": True, "yardSlotCode": f"YS-{suffix}"}


async def task_yard_ops_trailer_persist(
    trailerPlate: str = "",
    carrierDid: str = "",
    yardSlotCode: str = "",
) -> dict:
    if not trailerPlate:
        return {"ok": False, "error": "trailerPlate required"}
    vid = _vid("trailer")
    payload = {
        "trailerPlate": trailerPlate, "carrierDid": carrierDid,
        "yardSlotCode": yardSlotCode, "checkedInAt": _now_iso(),
    }
    ok = _execute(
        """
        INSERT INTO vertex_yard_ops_trailer (
          vertex_id, vertex_key, label, status, value_json,
          created_at, updated_at, owner_did, actor_did, sensitivity_ord
        ) VALUES (
          :vid, :key, 'yardOps.trailer', 'in_yard', :payload,
          :now, :now, :did, :did, 2
        )
        """,
        {"vid": vid, "key": trailerPlate, "payload": json.dumps(payload),
         "now": _now_iso(), "did": _YARD_DID},
    )
    return {"ok": ok, "vertexId": vid, "trailerVertexId": vid,
            "yardSlotCode": yardSlotCode}


# ── Dock door + dock job ────────────────────────────────────────────────────

async def task_yard_ops_dock_door_select(
    trailerVertexId: str = "",
    direction: str = "inbound",
) -> dict:
    """Pick a dock door. Delegates to the LangGraph optimizer (reads
    mv_dock_dwell_minutes_15m); falls back to rotating-suffix if unavailable."""
    try:
        from pymagatama.langgraph_graphs.warehouse_yard_optimizer import (
            recommend_dock_door,
        )
        rec = recommend_dock_door(trailerVertexId or "", direction or "inbound")
        if rec.get("ok") and rec.get("dock_door_code"):
            return {"ok": True, "dockDoorCode": rec["dock_door_code"]}
    except Exception as exc:
        LOG.info("optimizer fallback (dock_door): %s", exc)
    suffix = uuid.uuid4().hex[:2].upper()
    return {"ok": True, "dockDoorCode": f"DOOR-{direction[:2].upper()}-{suffix}"}


async def task_yard_ops_dock_job_persist(
    trailerVertexId: str = "",
    dockDoorCode: str = "",
    direction: str = "inbound",
    loadPlanRef: str = "",
) -> dict:
    if not trailerVertexId or not dockDoorCode:
        return {"ok": False, "error": "trailerVertexId + dockDoorCode required"}
    vid = _vid("dockJob")
    payload = {
        "trailerVertexId": trailerVertexId,
        "dockDoorCode": dockDoorCode,
        "direction": direction,
        "loadPlanRef": loadPlanRef,
        "openedAt": _now_iso(),
    }
    ok = _execute(
        """
        INSERT INTO vertex_yard_ops_dock_job (
          vertex_id, vertex_key, label, status, value_json,
          created_at, updated_at, owner_did, actor_did, sensitivity_ord
        ) VALUES (
          :vid, :key, 'yardOps.dockJob', 'open', :payload,
          :now, :now, :did, :did, 2
        )
        """,
        {"vid": vid, "key": f"{dockDoorCode}:{trailerVertexId}",
         "payload": json.dumps(payload), "now": _now_iso(), "did": _YARD_DID},
    )
    # edge: trailer → dock_job
    if ok:
        edge_vid = _vid("edge.trailerDockJob")
        _execute(
            """
            INSERT INTO edge_yard_ops_trailer_dock_job (
              edge_id, edge_key, src_vid, dst_vid, relation, value_json,
              created_at, updated_at, owner_did, sensitivity_ord
            ) VALUES (
              :eid, :key, :src, :dst, 'assigned_to', :payload,
              :now, :now, :did, 2
            )
            """,
            {"eid": edge_vid, "key": f"{trailerVertexId}->{vid}",
             "src": trailerVertexId, "dst": vid,
             "payload": json.dumps({"direction": direction}),
             "now": _now_iso(), "did": _YARD_DID},
        )
    return {"ok": ok, "vertexId": vid, "dockJobVertexId": vid,
            "dockDoorCode": dockDoorCode}


# ── Loading-robot mission dispatch ──────────────────────────────────────────

async def task_loading_robot_mission_dispatch(
    dockJobVertexId: str = "",
    loadingRobotLoadPlan: str = "",
    loadingRobotCellDesign: str = "",
) -> dict:
    """Persist an edge dock_job → loading_mission and return a mission id.
    The actual robot execution is owned by the existing loading-robot
    BPMN (executeLoadingMission); this dispatch just marks the link."""
    if not dockJobVertexId:
        return {"ok": False, "error": "dockJobVertexId required"}
    mission_id = f"mission-{_dt.datetime.now(tz=_dt.UTC).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
    edge_vid = _vid("edge.dockJobMission")
    _execute(
        """
        INSERT INTO edge_yard_ops_dock_job_loading_mission (
          edge_id, edge_key, src_vid, dst_vid, relation, value_json,
          created_at, updated_at, owner_did, sensitivity_ord
        ) VALUES (
          :eid, :key, :src, :dst, 'dispatches', :payload,
          :now, :now, :did, 2
        )
        """,
        {"eid": edge_vid, "key": f"{dockJobVertexId}->{mission_id}",
         "src": dockJobVertexId,
         "dst": f"at://{_ROBOT_DID}/loadingRobot.mission/{mission_id}",
         "payload": json.dumps({
             "loadPlan": loadingRobotLoadPlan,
             "cellDesign": loadingRobotCellDesign,
         }),
         "now": _now_iso(), "did": _YARD_DID},
    )
    return {"ok": True, "loadingRobotMissionId": mission_id}


# ── Dock job completion ─────────────────────────────────────────────────────

async def task_yard_ops_dock_job_complete(
    dockJobVertexId: str = "",
    actualDurationMin: int = 0,
    exceptions: list | None = None,
) -> dict:
    if not dockJobVertexId:
        return {"ok": False, "error": "dockJobVertexId required"}
    vid = _vid("dockCompletion")
    payload = {
        "dockJobVertexId": dockJobVertexId,
        "actualDurationMin": int(actualDurationMin or 0),
        "exceptions": exceptions or [],
        "closedAt": _now_iso(),
    }
    ok = _execute(
        """
        INSERT INTO vertex_yard_ops_dock_completion (
          vertex_id, vertex_key, label, status, value_json,
          created_at, updated_at, owner_did, actor_did, sensitivity_ord
        ) VALUES (
          :vid, :key, 'yardOps.dockCompletion', 'closed', :payload,
          :now, :now, :did, :did, 2
        )
        """,
        {"vid": vid, "key": dockJobVertexId, "payload": json.dumps(payload),
         "now": _now_iso(), "did": _YARD_DID},
    )
    if ok:
        edge_vid = _vid("edge.dockJobCompletion")
        _execute(
            """
            INSERT INTO edge_yard_ops_dock_job_completion (
              edge_id, edge_key, src_vid, dst_vid, relation, value_json,
              created_at, updated_at, owner_did, sensitivity_ord
            ) VALUES (
              :eid, :key, :src, :dst, 'closed_by', :payload,
              :now, :now, :did, 2
            )
            """,
            {"eid": edge_vid, "key": f"{dockJobVertexId}->{vid}",
             "src": dockJobVertexId, "dst": vid,
             "payload": json.dumps({"durationMin": int(actualDurationMin or 0)}),
             "now": _now_iso(), "did": _YARD_DID},
        )
        # mark dock job as closed
        _execute(
            """
            UPDATE vertex_yard_ops_dock_job
               SET status = 'closed', updated_at = :now
             WHERE vertex_id = :vid
            """,
            {"vid": dockJobVertexId, "now": _now_iso()},
        )
    return {"ok": ok, "vertexId": vid, "completionVertexId": vid}


# ── Dock schedule query ─────────────────────────────────────────────────────

async def task_yard_ops_dock_schedule_read(
    fromTs: str = "",
    toTs: str = "",
) -> dict:
    rows = _query(
        """
        SELECT vertex_id, value_json, status, created_at
        FROM vertex_yard_ops_dock_job
        WHERE created_at >= :from_ts AND created_at <= :to_ts
        ORDER BY created_at ASC
        LIMIT 200
        """,
        {"from_ts": fromTs or "1970-01-01 00:00:00",
         "to_ts": toTs or "2999-12-31 23:59:59"},
    )
    schedule: list[dict] = []
    for row in rows:
        try:
            v = json.loads(row[1]) if isinstance(row[1], str) else (row[1] or {})
        except Exception:
            v = {}
        schedule.append({
            "dockJobVertexId": row[0],
            "dockDoorCode": v.get("dockDoorCode", ""),
            "trailerPlate": v.get("trailerPlate", ""),
            "direction": v.get("direction", ""),
            "etaTs": str(row[3]),
            "status": row[2] or "",
        })
    return {"ok": True, "schedule": schedule}


# ── Registration ────────────────────────────────────────────────────────────

def register(app: Any, timeout_ms: int = 60_000) -> None:
    from pymagatama.langserver_compat import LangServerWorker
    if not isinstance(app, LangServerWorker):
        return

    @app.task(task_type="yardOps.slot.allocate", timeout_ms=timeout_ms)
    async def _slot(trailerPlate: str = "", carrierDid: str = "",
                    appointmentId: str = "") -> dict:
        return await task_yard_ops_slot_allocate(
            trailerPlate=trailerPlate, carrierDid=carrierDid,
            appointmentId=appointmentId)

    @app.task(task_type="yardOps.trailer.persist", timeout_ms=timeout_ms)
    async def _trailer(trailerPlate: str = "", carrierDid: str = "",
                       yardSlotCode: str = "") -> dict:
        return await task_yard_ops_trailer_persist(
            trailerPlate=trailerPlate, carrierDid=carrierDid,
            yardSlotCode=yardSlotCode)

    @app.task(task_type="yardOps.dockDoor.select", timeout_ms=timeout_ms)
    async def _door(trailerVertexId: str = "", direction: str = "inbound") -> dict:
        return await task_yard_ops_dock_door_select(
            trailerVertexId=trailerVertexId, direction=direction)

    @app.task(task_type="yardOps.dockJob.persist", timeout_ms=timeout_ms)
    async def _job(trailerVertexId: str = "", dockDoorCode: str = "",
                   direction: str = "inbound", loadPlanRef: str = "") -> dict:
        return await task_yard_ops_dock_job_persist(
            trailerVertexId=trailerVertexId, dockDoorCode=dockDoorCode,
            direction=direction, loadPlanRef=loadPlanRef)

    @app.task(task_type="loadingRobot.mission.dispatch", timeout_ms=timeout_ms)
    async def _mission(dockJobVertexId: str = "",
                       loadingRobotLoadPlan: str = "",
                       loadingRobotCellDesign: str = "") -> dict:
        return await task_loading_robot_mission_dispatch(
            dockJobVertexId=dockJobVertexId,
            loadingRobotLoadPlan=loadingRobotLoadPlan,
            loadingRobotCellDesign=loadingRobotCellDesign)

    @app.task(task_type="yardOps.dockJob.complete", timeout_ms=timeout_ms)
    async def _complete(dockJobVertexId: str = "",
                        actualDurationMin: int = 0,
                        exceptions=None) -> dict:
        return await task_yard_ops_dock_job_complete(
            dockJobVertexId=dockJobVertexId,
            actualDurationMin=actualDurationMin,
            exceptions=exceptions)

    @app.task(task_type="yardOps.dockSchedule.read", timeout_ms=timeout_ms)
    async def _schedule(fromTs: str = "", toTs: str = "") -> dict:
        return await task_yard_ops_dock_schedule_read(fromTs=fromTs, toTs=toTs)

    LOG.info("Registered yardOps.* tasks (slot.allocate, trailer.persist, "
             "dockDoor.select, dockJob.{persist,complete}, dockSchedule.read) "
             "+ loadingRobot.mission.dispatch")
