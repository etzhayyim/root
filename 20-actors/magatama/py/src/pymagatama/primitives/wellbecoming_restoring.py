"""Well-Becoming γ Restoring Force primitive — E (homeostasis term).

ADR-0098 Repo-as-Attractor:
  SBGE の γ-項: restoring_delta_i = -γ * (q_i - q_i^0)

  q_i^0 = baseline score (first observed score per agent, write-once).
  Each tick records deviation and restoring_delta to vertex_belief_restoring.
  mv_belief_restoring_summary tracks deviation_status for D-feed gate.

Pyzeebe task type: wellbecoming.restoring.capture
"""

from __future__ import annotations

import datetime as _dt
import logging
import os
from typing import Any

from pymagatama.db_sync import sync_cursor
from pymagatama.primitives.pydantic_job import ZeebeJobInput
from pymagatama.langserver_compat import LangServerJob as Job, LangServerWorker

LOG = logging.getLogger("wellbecoming.restoring")

# γ: 復元力の学習率。小さいほど保守的。
_GAMMA_LR: float = float(os.environ.get("WB_GAMMA_LR", "0.05"))

# 信念状態が少ないエージェントは除外
_MIN_SCORED_EVENTS: int = int(os.environ.get("WB_MIN_SCORED_EVENTS", "3"))


class _RestoringInput(ZeebeJobInput):
    gamma_lr: float = _GAMMA_LR
    min_scored_events: int = _MIN_SCORED_EVENTS


def _now_iso() -> str:
    return _dt.datetime.now(tz=_dt.UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _tick_ms() -> int:
    return int(_dt.datetime.now(tz=_dt.UTC).timestamp() * 1000)


def task_belief_restoring_capture(
    gamma_lr: float = _GAMMA_LR,
    min_scored_events: int = _MIN_SCORED_EVENTS,
) -> dict[str, Any]:
    """γ 復元力を計算して vertex_belief_restoring に記録する。

    restoring_delta_i = -γ * (q_i - q_i^0)

    q_i^0 = vertex_belief_baseline の q0 (初回観測スコア、write-once)。
    baseline が未存在のエージェントは今回のスコアで初期化する。

    Returns:
        agents_processed: 信念状態が既知のエージェント数
        rows_written:     upsert した行数
        max_abs_deviation: 最大 |deviation| (収束指標)
        mean_abs_deviation: 平均 |deviation|
        n_new_baselines: 今回新規に baseline を登録したエージェント数
    """
    with sync_cursor() as cur:
        cur.execute(
            f"""
            SELECT agent_did, mean_score_total
            FROM mv_attractor_stability_by_agent
            WHERE scored_events >= {int(min_scored_events)}
              AND mean_score_total IS NOT NULL
            ORDER BY agent_did
            """
        )
        agents = cur.fetchall()

    if not agents:
        LOG.info("restoring_capture: no agents with sufficient scored events")
        return {
            "ok": True,
            "agents_processed": 0,
            "rows_written": 0,
            "max_abs_deviation": 0.0,
            "mean_abs_deviation": 0.0,
            "n_new_baselines": 0,
            "gamma_lr": gamma_lr,
        }

    agent_dids = [row[0] for row in agents]
    agent_map = {row[0]: float(row[1]) for row in agents}

    # 既存 baseline を一括取得
    did_list = ",".join(f"'{d}'" for d in agent_dids)
    with sync_cursor() as cur:
        cur.execute(
            f"""
            SELECT agent_did, q0
            FROM vertex_belief_baseline
            WHERE agent_did IN ({did_list})
            """
        )
        baseline_rows = cur.fetchall()

    baseline_map = {row[0]: float(row[1]) for row in baseline_rows}

    tick_ms = _tick_ms()
    now_iso = _now_iso()

    # baseline 未存在のエージェントに初回スコアで INSERT
    new_baselines: list[tuple] = []
    for agent_did in agent_dids:
        if agent_did not in baseline_map:
            q0 = agent_map[agent_did]
            vertex_id = f"wb:baseline:{agent_did}"
            new_baselines.append((vertex_id, agent_did, q0, now_iso, now_iso))
            baseline_map[agent_did] = q0

    if new_baselines:
        with sync_cursor() as cur:
            existing_ids = [r[0] for r in new_baselines]
            id_list = ",".join(f"'{vid}'" for vid in existing_ids)
            cur.execute(
                f"DELETE FROM vertex_belief_baseline WHERE vertex_id IN ({id_list})"
            )
            for row in new_baselines:
                cur.execute(
                    """
                    INSERT INTO vertex_belief_baseline
                      (vertex_id, agent_did, q0, captured_at, updated_at,
                       sensitivity_ord, org_id, user_id, actor_id)
                    VALUES (%s, %s, %s, %s::timestamp, %s::timestamp,
                            1, '', '', 'sys.bpmn.wellbecoming')
                    """,
                    row,
                )

    # 各エージェントの restoring_delta を計算
    rows: list[tuple] = []
    for agent_did in agent_dids:
        q_i = agent_map[agent_did]
        q0 = baseline_map[agent_did]
        deviation = q_i - q0
        restoring_delta = -gamma_lr * deviation
        vertex_id = f"wb:restoring:{agent_did}:{tick_ms}"
        rows.append((
            vertex_id, agent_did,
            q_i, q0, deviation, restoring_delta, gamma_lr,
            now_iso, now_iso,
        ))

    if not rows:
        return {
            "ok": True,
            "agents_processed": len(agents),
            "rows_written": 0,
            "max_abs_deviation": 0.0,
            "mean_abs_deviation": 0.0,
            "n_new_baselines": len(new_baselines),
            "gamma_lr": gamma_lr,
        }

    # vertex_belief_restoring に delete-then-insert
    with sync_cursor() as cur:
        existing_ids = [r[0] for r in rows]
        id_list = ",".join(f"'{vid}'" for vid in existing_ids)
        cur.execute(
            f"DELETE FROM vertex_belief_restoring WHERE vertex_id IN ({id_list})"
        )
        for row in rows:
            cur.execute(
                """
                INSERT INTO vertex_belief_restoring
                  (vertex_id, agent_did, q_current, q0, deviation, restoring_delta,
                   gamma_lr, tick_at, updated_at,
                   sensitivity_ord, org_id, user_id, actor_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s,
                        %s::timestamp, %s::timestamp,
                        1, '', '', 'sys.bpmn.wellbecoming')
                """,
                row,
            )

    abs_devs = [abs(r[4]) for r in rows]
    max_abs = max(abs_devs) if abs_devs else 0.0
    mean_abs = sum(abs_devs) / len(abs_devs) if abs_devs else 0.0

    LOG.info(
        "restoring_capture: agents=%d rows=%d new_baselines=%d "
        "max_abs_dev=%.4f mean_abs_dev=%.4f gamma=%.3f",
        len(agents),
        len(rows),
        len(new_baselines),
        max_abs,
        mean_abs,
        gamma_lr,
    )

    return {
        "ok": True,
        "agents_processed": len(agents),
        "rows_written": len(rows),
        "max_abs_deviation": max_abs,
        "mean_abs_deviation": mean_abs,
        "n_new_baselines": len(new_baselines),
        "gamma_lr": gamma_lr,
        "tick_ms": tick_ms,
    }


def register(worker: LangServerWorker, timeout_ms: int = 60_000) -> None:
    """Zeebe worker にタスクを登録する。"""

    @worker.task(
        task_type="wellbecoming.restoring.capture",
        timeout_ms=timeout_ms,
    )
    async def _capture(job: Job) -> dict[str, Any]:
        inp = _RestoringInput.from_job(job)
        return task_belief_restoring_capture(
            gamma_lr=inp.gamma_lr,
            min_scored_events=inp.min_scored_events,
        )
