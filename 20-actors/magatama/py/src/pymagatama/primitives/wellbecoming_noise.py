"""Well-Becoming ξ Stochastic Noise Injection — F (OU noise term).

ADR-0098 Repo-as-Attractor:
  SBGE の ξ-項: ξ_i(t+dt) = ξ_i(t)*exp(-θ*dt) + σ*sqrt(1-exp(-2θ*dt))*N(0,1)

  Ornstein-Uhlenbeck process — colored noise preventing attractor trapping.
  Each tick updates the current OU state per agent (delete+insert, one row).
  mv_belief_noise_summary tracks mean/max amplitude for monitoring.

Pyzeebe task type: wellbecoming.noise.inject
"""

from __future__ import annotations

import datetime as _dt
import logging
import math
import os
import random
from typing import Any

from pymagatama.db_sync import sync_cursor
from pymagatama.primitives.pydantic_job import ZeebeJobInput
from pymagatama.langserver_compat import LangServerJob as Job, LangServerWorker

LOG = logging.getLogger("wellbecoming.noise")

# OU process default parameters
_SIGMA: float = float(os.environ.get("WB_NOISE_SIGMA", "0.01"))
_OU_THETA: float = float(os.environ.get("WB_NOISE_OU_THETA", "0.1"))
_DT_SEC: float = float(os.environ.get("WB_NOISE_DT_SEC", "3600.0"))  # 1h tick
_MIN_SCORED_EVENTS: int = int(os.environ.get("WB_MIN_SCORED_EVENTS", "3"))


class _NoiseInput(ZeebeJobInput):
    sigma: float = _SIGMA
    ou_theta: float = _OU_THETA
    dt_sec: float = _DT_SEC
    min_scored_events: int = _MIN_SCORED_EVENTS


def _now_iso() -> str:
    return _dt.datetime.now(tz=_dt.UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _tick_ms() -> int:
    return int(_dt.datetime.now(tz=_dt.UTC).timestamp() * 1000)


def task_belief_noise_inject(
    sigma: float = _SIGMA,
    ou_theta: float = _OU_THETA,
    dt_sec: float = _DT_SEC,
    min_scored_events: int = _MIN_SCORED_EVENTS,
) -> dict[str, Any]:
    """OU ノイズプロセスを更新して vertex_belief_noise に記録する。

    ξ_i(t+dt) = ξ_i(t)*exp(-θ*dt) + σ*sqrt(1-exp(-2θ*dt))*N(0,1)

    各エージェントの現在 OU 状態を delete+insert で更新 (1 エージェント 1 行)。
    安定した vertex_id = 'wb:noise:{agent_did}' を使用 (時刻を含まない)。

    Returns:
        agents_processed: 信念状態が既知のエージェント数
        rows_written:     更新した行数
        mean_abs_xi:      平均 |ξ| (ノイズ振幅の監視指標)
        max_abs_xi:       最大 |ξ|
    """
    with sync_cursor() as cur:
        cur.execute(
            f"""
            SELECT agent_did
            FROM mv_attractor_stability_by_agent
            WHERE scored_events >= {int(min_scored_events)}
              AND mean_score_total IS NOT NULL
            ORDER BY agent_did
            """
        )
        agents = [row[0] for row in cur.fetchall()]

    if not agents:
        LOG.info("noise_inject: no agents with sufficient scored events")
        return {
            "ok": True,
            "agents_processed": 0,
            "rows_written": 0,
            "mean_abs_xi": 0.0,
            "max_abs_xi": 0.0,
        }

    did_list = ",".join(f"'{d}'" for d in agents)

    # 既存 OU 状態を取得
    with sync_cursor() as cur:
        cur.execute(
            f"""
            SELECT agent_did, xi_value
            FROM vertex_belief_noise
            WHERE agent_did IN ({did_list})
            """
        )
        existing = {row[0]: float(row[1]) for row in cur.fetchall()}

    tick_ms = _tick_ms()
    now_iso = _now_iso()

    # OU 更新係数
    exp_decay = math.exp(-ou_theta * dt_sec)
    noise_std = sigma * math.sqrt(max(0.0, 1.0 - exp_decay ** 2))

    rows: list[tuple] = []
    for agent_did in agents:
        xi_prev = existing.get(agent_did, 0.0)
        xi_new = xi_prev * exp_decay + noise_std * random.gauss(0.0, 1.0)
        vertex_id = f"wb:noise:{agent_did}"
        rows.append((vertex_id, agent_did, tick_ms, xi_new, sigma, ou_theta, now_iso))

    # delete-then-insert (RisingWave は ON CONFLICT 非対応)
    with sync_cursor() as cur:
        vid_list = ",".join(f"'{r[0]}'" for r in rows)
        cur.execute(
            f"DELETE FROM vertex_belief_noise WHERE vertex_id IN ({vid_list})"
        )
        for row in rows:
            cur.execute(
                """
                INSERT INTO vertex_belief_noise
                  (vertex_id, agent_did, tick_ms, xi_value, sigma, ou_theta,
                   created_at, sensitivity_ord, org_id, user_id, actor_id)
                VALUES (%s, %s, %s, %s, %s, %s,
                        %s::timestamp,
                        1, '', '', 'sys.bpmn.wellbecoming')
                """,
                row,
            )

    abs_xis = [abs(r[3]) for r in rows]
    mean_abs = sum(abs_xis) / len(abs_xis) if abs_xis else 0.0
    max_abs = max(abs_xis) if abs_xis else 0.0

    LOG.info(
        "noise_inject: agents=%d rows=%d mean_abs_xi=%.5f max_abs_xi=%.5f sigma=%.4f theta=%.3f",
        len(agents),
        len(rows),
        mean_abs,
        max_abs,
        sigma,
        ou_theta,
    )

    return {
        "ok": True,
        "agents_processed": len(agents),
        "rows_written": len(rows),
        "mean_abs_xi": mean_abs,
        "max_abs_xi": max_abs,
        "tick_ms": tick_ms,
    }


def register(worker: LangServerWorker, timeout_ms: int = 60_000) -> None:
    """Zeebe worker にタスクを登録する。"""

    @worker.task(
        task_type="wellbecoming.noise.inject",
        timeout_ms=timeout_ms,
    )
    async def _inject(job: Job) -> dict[str, Any]:
        inp = _NoiseInput.from_job(job)
        return task_belief_noise_inject(
            sigma=inp.sigma,
            ou_theta=inp.ou_theta,
            dt_sec=inp.dt_sec,
            min_scored_events=inp.min_scored_events,
        )
