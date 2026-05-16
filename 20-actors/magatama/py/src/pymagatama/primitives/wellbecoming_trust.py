"""Well-Becoming Trust Weight primitives — W_ij dynamic update + Bounded Confidence.

ADR-0098 Repo-as-Attractor:
  SBGE の W_ij（主体間信頼重み）を mv_attractor_stability_by_agent から計算し
  edge_trust_weight テーブルに upsert する。

  Bounded Confidence (Hegselmann-Krause):
    W_ij = exp(-k * D(q_i, q_j))  if D < bc_epsilon
           0                        if D >= bc_epsilon
    D(q_i, q_j) = |mean_score_total_i - mean_score_total_j|

Pyzeebe task type: wellbecoming.trust.updateWeights
"""

from __future__ import annotations

import datetime as _dt
import logging
import math
import os
from typing import Any

from pymagatama.db_sync import sync_cursor
from pymagatama.primitives.pydantic_job import ZeebeJobInput
from pymagatama.langserver_compat import LangServerJob as Job, LangServerWorker

LOG = logging.getLogger("wellbecoming.trust")

# Bounded Confidence 閾値 ε（この距離以上 → W_ij = 0）
_BC_EPSILON: float = float(os.environ.get("WB_BC_EPSILON", "0.3"))

# W_ij = exp(-k * distance) の steepness。k が大きいほど距離に敏感
_WEIGHT_K: float = float(os.environ.get("WB_WEIGHT_K", "5.0"))

# scored_events が少ない agent は信念推定が不安定 → 対象外
_MIN_SCORED_EVENTS: int = int(os.environ.get("WB_MIN_SCORED_EVENTS", "3"))


class _TrustWeightInput(ZeebeJobInput):
    bc_epsilon: float = _BC_EPSILON
    weight_k: float = _WEIGHT_K
    min_scored_events: int = _MIN_SCORED_EVENTS


def _now_iso() -> str:
    return _dt.datetime.now(tz=_dt.UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _compute_weight(distance: float, bc_epsilon: float, k: float) -> tuple[float, bool]:
    """距離から W_ij と blocked フラグを計算する。"""
    if distance >= bc_epsilon:
        return 0.0, True
    return math.exp(-k * distance), False


def task_trust_weight_update(
    bc_epsilon: float = _BC_EPSILON,
    weight_k: float = _WEIGHT_K,
    min_scored_events: int = _MIN_SCORED_EVENTS,
) -> dict[str, Any]:
    """mv_attractor_stability_by_agent から W_ij を計算して edge_trust_weight に upsert する。

    Returns:
        pairs_evaluated: 評価したエージェントペア数
        pairs_blocked:   Bounded Confidence で遮断されたペア数（W_ij = 0）
        pairs_updated:   upsert した行数
        agents_found:    信念状態が既知のエージェント数
    """
    with sync_cursor() as cur:
        # 信念状態が既知のエージェント一覧を取得（scored_events 閾値でフィルタ）
        cur.execute(
            f"""
            SELECT
              agent_did,
              mean_score_total,
              entropy_spread,
              attractor_status,
              scored_events
            FROM mv_attractor_stability_by_agent
            WHERE scored_events >= {int(min_scored_events)}
              AND mean_score_total IS NOT NULL
            ORDER BY agent_did
            """
        )
        agents = cur.fetchall()

    if len(agents) < 2:
        LOG.info("trust_weight_update: not enough agents with scored events (%d)", len(agents))
        return {
            "ok": True,
            "agents_found": len(agents),
            "pairs_evaluated": 0,
            "pairs_blocked": 0,
            "pairs_updated": 0,
            "bc_epsilon": bc_epsilon,
        }

    # エージェント情報を dict に変換
    agent_map = {
        row[0]: {
            "mean_score": row[1],
            "entropy_spread": row[2],
            "attractor_status": row[3],
            "scored_events": row[4],
        }
        for row in agents
    }
    agent_dids = list(agent_map.keys())

    now_iso = _now_iso()
    upserts: list[tuple] = []
    pairs_blocked = 0

    # 全ペア（i, j）の W_ij を計算（自己参照は除外）
    for i_did in agent_dids:
        for j_did in agent_dids:
            if i_did == j_did:
                continue
            score_i = agent_map[i_did]["mean_score"]
            score_j = agent_map[j_did]["mean_score"]
            distance = abs(score_i - score_j)
            weight, blocked = _compute_weight(distance, bc_epsilon, weight_k)
            edge_id = f"{i_did}→{j_did}"
            upserts.append((edge_id, i_did, j_did, weight, distance, bc_epsilon, blocked, now_iso))
            if blocked:
                pairs_blocked += 1

    if not upserts:
        return {
            "ok": True,
            "agents_found": len(agents),
            "pairs_evaluated": 0,
            "pairs_blocked": 0,
            "pairs_updated": 0,
            "bc_epsilon": bc_epsilon,
        }

    # edge_trust_weight に upsert（PK 重複 = overwrite, RisingWave 仕様）
    with sync_cursor() as cur:
        # 既存行を DELETE してから INSERT（RisingWave は ON CONFLICT 非対応）
        existing_ids = [u[0] for u in upserts]
        if existing_ids:
            id_list = ",".join(f"'{eid}'" for eid in existing_ids)
            cur.execute(f"DELETE FROM edge_trust_weight WHERE edge_id IN ({id_list})")

        for row in upserts:
            cur.execute(
                """
                INSERT INTO edge_trust_weight
                  (edge_id, src_did, dst_did, weight, distance, bc_epsilon, blocked, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::timestamp)
                """,
                row,
            )

    blocked_pairs = [
        f"{u[1].split(':')[-1]}→{u[2].split(':')[-1]}"
        for u in upserts if u[6]  # blocked=True
    ]

    LOG.info(
        "trust_weight_update: agents=%d pairs=%d blocked=%d epsilon=%.2f",
        len(agents),
        len(upserts),
        pairs_blocked,
        bc_epsilon,
    )

    return {
        "ok": True,
        "agents_found": len(agents),
        "pairs_evaluated": len(upserts),
        "pairs_blocked": pairs_blocked,
        "pairs_updated": len(upserts),
        "bc_epsilon": bc_epsilon,
        "weight_k": weight_k,
        "blocked_pairs": blocked_pairs[:10],  # log 用（最大 10 件）
    }


def register(worker: LangServerWorker, timeout_ms: int = 60_000) -> None:
    """Zeebe worker にタスクを登録する。"""

    @worker.task(
        task_type="wellbecoming.trust.updateWeights",
        timeout_ms=timeout_ms,
    )
    async def _update(job: Job) -> dict[str, Any]:
        inp = _TrustWeightInput.from_job(job)
        return task_trust_weight_update(
            bc_epsilon=inp.bc_epsilon,
            weight_k=inp.weight_k,
            min_scored_events=inp.min_scored_events,
        )
