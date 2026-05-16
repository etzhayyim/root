"""RL preference pair generation — Phase 1 DPO dataset construction.

ADR-2604291800 Well-Becoming Spirit objective function.

Phase 1: cross-actor DPO pair generation from vertex_rl_step.
         Pairs rows with the same action_nsid from different actor_did values
         where reward_scalar differs by >= delta_threshold.

Pyzeebe task type registered via register():
  rl.generate.preferences  — R/P1D BPMN timer, gated by min_steps count

Key constraints observed from data (2026-05-06):
  - Within (action_nsid, actor_did) groups, reward_scalar has zero variance
    at current data volume. Cross-actor pairing is the only viable path.
  - delta_threshold is a task parameter, not hard-coded.
  - Gate uses total step count (all actors) rather than per-actor counts.
"""

from __future__ import annotations

import datetime as _dt
import logging
from typing import Any

from pymagatama.db_sync import sync_cursor

LOG = logging.getLogger("rl_preferences")


def _now_ts() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")


def _get_total_step_count() -> int:
    try:
        with sync_cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM vertex_rl_step WHERE source='server'")
            row = cur.fetchone()
        return int(row[0]) if row else 0
    except Exception as e:
        LOG.warning("get_total_step_count failed: %s", e)
        return 0


def task_rl_generate_preferences(
    min_steps: int = 50,
    delta_threshold: float = 0.05,
    batch_limit: int = 500,
) -> dict[str, Any]:
    """Cross-actor DPO preference pair generation from vertex_rl_step.

    BPMN: rl/rlGeneratePreferences.bpmn → Task_Generate (rl.generate.preferences, R/P1D)

    Strategy: for each action_nsid, find all (actor_a, actor_b) pairs where
      reward_scalar(actor_a) - reward_scalar(actor_b) >= delta_threshold.
    The higher-reward actor's step is 'chosen', the lower is 'rejected'.

    FEEL gate in BPMN: =totalSteps >= min_steps
    totalSteps is written to process variables by a preceding query step.

    Conventions:
    - rw-psycopg3-no-param-limit: LIMIT/OFFSET inlined as int literals
    - flush: bool = False: never FLUSH in pymagatama
    """
    total_steps = _get_total_step_count()
    if total_steps < int(min_steps):
        LOG.info(
            "rl.generate.preferences: skipped — total_steps=%d < min_steps=%d",
            total_steps, min_steps,
        )
        return {
            "generated": 0,
            "skipped": 0,
            "total_steps": total_steps,
            "gate_passed": False,
        }

    now = _now_ts()
    generated = 0
    skipped = 0
    threshold = float(delta_threshold)

    # Load all server-sourced steps (bounded: only server rows, no cross-source noise).
    # With current data volume (22–100 rows) a full load is safe.
    # At >10K rows switch to cursor-based per-action_nsid pagination.
    try:
        with sync_cursor() as cur:
            cur.execute(
                f"""SELECT vertex_id, action_nsid, actor_did,
                           reward_scalar, reward_floor, reward_spirit, reward_eta,
                           sensitivity_ord, owner_did, org_id, user_id, actor_id
                    FROM vertex_rl_step
                    WHERE source = 'server'
                      AND reward_scalar IS NOT NULL
                    ORDER BY action_nsid, reward_scalar DESC
                    LIMIT {int(batch_limit)}"""
            )
            rows = cur.fetchall()
    except Exception as e:
        LOG.warning("rl.generate.preferences: query failed: %s", e)
        return {"generated": 0, "skipped": 0, "total_steps": total_steps, "error": str(e)}

    # Group by action_nsid
    from collections import defaultdict
    by_action: dict[str, list[tuple[Any, ...]]] = defaultdict(list)
    for row in rows:
        action_nsid = str(row[1] or "")
        by_action[action_nsid].append(row)

    for action_nsid, steps in by_action.items():
        # Generate all cross-actor pairs where reward delta >= threshold.
        # steps is already sorted DESC by reward_scalar (from SQL ORDER BY).
        for i, chosen_row in enumerate(steps):
            for rejected_row in steps[i + 1 :]:
                chosen_scalar = float(chosen_row[3] or 0.0)
                rejected_scalar = float(rejected_row[3] or 0.0)
                reward_delta = chosen_scalar - rejected_scalar

                if reward_delta < threshold:
                    # Since sorted DESC, remaining will also be < threshold
                    break

                chosen_actor = str(chosen_row[2] or "")
                rejected_actor = str(rejected_row[2] or "")

                # Skip same-actor pairs (within-actor variance = zero, no signal)
                if chosen_actor == rejected_actor:
                    continue

                chosen_step_id = str(chosen_row[0])
                rejected_step_id = str(rejected_row[0])

                # Stable pair_id: sorted step IDs so (A,B) == (B,A)
                pair_key = ":".join(sorted([chosen_step_id, rejected_step_id]))
                pair_id = f"rl:pair:{pair_key}"

                try:
                    with sync_cursor() as cur:
                        cur.execute(
                            """INSERT INTO vertex_rl_preference_pair
                               (vertex_id, action_nsid,
                                chosen_step_id, rejected_step_id,
                                chosen_actor_did, rejected_actor_did,
                                chosen_reward, rejected_reward, reward_delta,
                                pairing_strategy,
                                sensitivity_ord, owner_did, org_id, user_id, actor_id,
                                created_at)
                               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::TIMESTAMP)""",
                            (
                                pair_id,
                                action_nsid,
                                chosen_step_id,
                                rejected_step_id,
                                chosen_actor,
                                rejected_actor,
                                chosen_scalar,
                                rejected_scalar,
                                round(reward_delta, 4),
                                "cross_actor_reward_delta",
                                int(chosen_row[7] or 1),
                                str(chosen_row[8] or ""),
                                str(chosen_row[9] or ""),
                                str(chosen_row[10] or ""),
                                str(chosen_row[11] or "rl.generate"),
                                now,
                            ),
                        )
                    generated += 1
                except Exception as e:
                    # Duplicate pair_id = already generated; skip silently
                    LOG.debug("insert pair skipped for %s: %s", pair_id, e)
                    skipped += 1

    LOG.info(
        "rl.generate.preferences: generated=%d skipped=%d total_steps=%d",
        generated, skipped, total_steps,
    )
    return {
        "generated": generated,
        "skipped": skipped,
        "total_steps": total_steps,
        "gate_passed": True,
    }


def register(worker: Any, *, timeout_ms: int) -> None:
    worker.task(
        task_type="rl.generate.preferences",
        single_value=False,
        timeout_ms=max(timeout_ms, 300_000),
    )(task_rl_generate_preferences)
