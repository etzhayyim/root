"""RL signal collection — Phase 0 trajectory accretion.

ADR-2604291800 Well-Becoming Spirit objective function.

Phase 0: collect vertex_wellbecoming_event rows into vertex_rl_step.
         No training. Signal accretion only.

Pyzeebe task type registered via register():
  rl.collect.trajectories  — R/PT1H cursor scan of wellbecoming events → rl_step

Reward decomposition from wellbecoming_event:
  reward_floor   = NOT floor_violated                    (ADR-2604291800 Invariant 1)
  reward_spirit  = score_spirit                          (0.0–1.0)
  reward_eta     = (separation_delta + 1.0) / 2.0       (Shannon η proxy, mapped 0–1)
  reward_scalar  = score_total                           (composite U_total)
"""

from __future__ import annotations

import datetime as _dt
import logging
from typing import Any

from pymagatama.db_sync import sync_cursor

LOG = logging.getLogger("rl_signal")

_CURSOR_ID = "rl:collect:cursor"
# Attribution window: how far back to look for a dispatch that caused this step.
_ATTRIBUTION_WINDOW_MIN = 30


def _now_ts() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")


def _attribute_dispatch(actor_did: str, step_vid: str, step_ts: str) -> None:
    """Link the most recent unattributed dispatch for actor_did to this step.

    Looks for a successful dispatch within the last _ATTRIBUTION_WINDOW_MIN minutes
    that has not yet been attributed to any step.  When found, writes
    triggered_by_dispatch on the step and outcome_step_id on the dispatch log row.
    Both writes are best-effort; attribution failure never blocks step collection.
    """
    try:
        window_start = (
            _dt.datetime.fromisoformat(step_ts.replace(" ", "T"))
            - _dt.timedelta(minutes=_ATTRIBUTION_WINDOW_MIN)
        ).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return

    try:
        with sync_cursor() as cur:
            cur.execute(
                "SELECT vertex_id FROM vertex_rl_aif_dispatch_log "
                "WHERE actor_did = %s "
                "  AND dispatch_ok = true "
                "  AND outcome_step_id IS NULL "
                "  AND dispatched_at >= %s::TIMESTAMP "
                "ORDER BY dispatched_at DESC LIMIT 1",
                (actor_did, window_start),
            )
            row = cur.fetchone()
            if not row:
                return
            dispatch_vid = row[0]

            cur.execute(
                "UPDATE vertex_rl_step SET triggered_by_dispatch = %s WHERE vertex_id = %s",
                (dispatch_vid, step_vid),
            )
            cur.execute(
                "UPDATE vertex_rl_aif_dispatch_log SET outcome_step_id = %s WHERE vertex_id = %s",
                (step_vid, dispatch_vid),
            )
            LOG.debug("attributed dispatch=%s → step=%s", dispatch_vid, step_vid)
    except Exception as exc:  # noqa: BLE001
        LOG.warning("attribution failed step=%s: %s", step_vid, exc)


def _sep_to_eta(sep_delta: float | None) -> float | None:
    """Map separation_delta [-1.0, 1.0] → reward_eta [0.0, 1.0]."""
    if sep_delta is None:
        return None
    clamped = max(-1.0, min(1.0, float(sep_delta)))
    return round((clamped + 1.0) / 2.0, 4)


def _get_cursor_ts() -> str:
    """Read last processed created_at from vertex_rl_collect_cursor."""
    try:
        with sync_cursor() as cur:
            cur.execute(
                "SELECT last_event_ts FROM vertex_rl_collect_cursor WHERE vertex_id = %s LIMIT 1",
                (_CURSOR_ID,),
            )
            row = cur.fetchone()
        if row and row[0]:
            return str(row[0])
    except Exception as e:
        LOG.warning("get_cursor_ts failed: %s", e)
    return "2024-01-01 00:00:00"


def _update_cursor(last_ts: str, batch_count: int, total: int) -> None:
    now = _now_ts()
    try:
        with sync_cursor() as cur:
            cur.execute(
                "DELETE FROM vertex_rl_collect_cursor WHERE vertex_id = %s",
                (_CURSOR_ID,),
            )
            cur.execute(
                """INSERT INTO vertex_rl_collect_cursor
                   (vertex_id, last_event_ts, last_step_count, total_collected, updated_at)
                   VALUES (%s, %s::TIMESTAMP, %s, %s, %s::TIMESTAMP)""",
                (_CURSOR_ID, last_ts, batch_count, total, now),
            )
    except Exception as e:
        LOG.warning("update_cursor failed: %s", e)


def task_rl_collect_trajectories(batch_size: int = 200) -> dict[str, Any]:
    """Cursor-based scan of vertex_wellbecoming_event → vertex_rl_step.

    BPMN: rl/rlCollectTrajectories.bpmn → Task_Collect (rl.collect.trajectories, R/PT1H)

    Conventions:
    - rw-psycopg3-no-param-limit: LIMIT is inlined as int literal
    - rw-large-table-no-is-null-scan: cursor-based, not IS NULL scan
    - flush: bool = False: never FLUSH in pymagatama
    """
    cursor_ts = _get_cursor_ts()
    now = _now_ts()
    collected = 0
    skipped = 0
    max_ts = cursor_ts

    try:
        with sync_cursor() as cur:
            cur.execute(
                f"""SELECT vertex_id, case_id, agent_did, activity,
                           score_spirit, score_total, separation_delta,
                           floor_violated, model, created_at
                    FROM vertex_wellbecoming_event
                    WHERE created_at > %s::TIMESTAMP
                    ORDER BY created_at ASC
                    LIMIT {int(batch_size)}""",
                (cursor_ts,),
            )
            rows = cur.fetchall()
    except Exception as e:
        LOG.warning("collect query failed: %s", e)
        return {"collected": 0, "skipped": 0, "cursor_ts": cursor_ts, "error": str(e)}

    for row in rows:
        (event_id, case_id, agent_did, activity,
         score_spirit, score_total, sep_delta,
         floor_violated, model, created_at) = row

        step_id = f"rl:step:{event_id}"
        reward_floor = not bool(floor_violated)
        reward_eta = _sep_to_eta(sep_delta)
        reward_scalar = float(score_total or 0.0)
        created_str = str(created_at) if created_at else now

        try:
            with sync_cursor() as cur:
                cur.execute(
                    """INSERT INTO vertex_rl_step
                       (vertex_id, episode_id, action_nsid,
                        reward_floor, reward_spirit, reward_eta, reward_scalar,
                        source, source_event_id, actor_did, model,
                        sensitivity_ord, owner_did, org_id, user_id, actor_id,
                        created_at)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::TIMESTAMP)""",
                    (
                        step_id,
                        str(case_id or ""),
                        str(activity or "wellbecoming.agent.loop"),
                        reward_floor,
                        float(score_spirit) if score_spirit is not None else None,
                        reward_eta,
                        reward_scalar,
                        "server",
                        str(event_id),
                        str(agent_did or ""),
                        str(model or ""),
                        1,
                        str(agent_did or ""),
                        str(agent_did or ""),
                        str(agent_did or ""),
                        "rl.collect",
                        created_str,
                    ),
                )
            collected += 1
            if created_str > max_ts:
                max_ts = created_str
            # Phase 3: attribute a recent dispatch to this step (best-effort).
            if agent_did:
                _attribute_dispatch(str(agent_did), step_id, created_str)
        except Exception as e:
            LOG.warning("insert rl_step failed for %s: %s", event_id, e)
            skipped += 1

    # Update cursor to the latest processed timestamp
    if collected > 0:
        try:
            # Get total count for logging
            with sync_cursor() as cur:
                cur.execute("SELECT total_collected FROM vertex_rl_collect_cursor WHERE vertex_id = %s LIMIT 1", (_CURSOR_ID,))
                prev_row = cur.fetchone()
            prev_total = int(prev_row[0] or 0) if prev_row else 0
        except Exception:
            prev_total = 0
        _update_cursor(max_ts, collected, prev_total + collected)

    LOG.info(
        "rl.collect.trajectories: collected=%d skipped=%d cursor_was=%s cursor_now=%s",
        collected, skipped, cursor_ts[:19], max_ts[:19],
    )
    return {
        "collected": collected,
        "skipped": skipped,
        "cursor_ts": max_ts,
        "has_more": len(rows) == batch_size,
    }


def register(worker: Any, *, timeout_ms: int) -> None:
    worker.task(
        task_type="rl.collect.trajectories",
        single_value=False,
        timeout_ms=max(timeout_ms, 120_000),
    )(task_rl_collect_trajectories)
