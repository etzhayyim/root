"""Karma 覚者 DAO arbitration primitives.

Triggered by `karma.evaluate` (recommendation = 'escalate-dao') OR by
caller with elevated standing (positive multi-generational karma streak).

Voting model:
  - voters discovered by Pregel cohort intersection (find_voters)
  - 2/3 supermajority of non-abstain votes → immediate finalize
  - sweeper finalizes by plurality after window closes
  - tied plurality → 'dismiss' (default conservative outcome)

Pyzeebe task types:
  karma.dao.findVoters       Pregel-style voter discovery
  karma.dao.openArbitration  INSERT vertex_karma_arbitration
  karma.dao.castVote         INSERT vertex_karma_vote + tally
  karma.dao.finalize         UPDATE vertex_karma_arbitration on supermajority
  karma.dao.sweepExpired     R/PT15M sweeper for expired windows
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import logging
import time
import uuid
from typing import Any

from pymagatama.db_sync import sync_cursor

LOG = logging.getLogger("karma.dao")

KARMA_DID = "did:web:karma.gftd.ai"

VOTE_POSITIONS = ("admit", "floor", "dismiss", "abstain")
SUPERMAJORITY_PCT = 2.0 / 3.0


# ── Helpers ────────────────────────────────────────────────────────────


def _now_ms() -> int:
    return int(time.time() * 1000)


def _now_ts() -> str:
    return _dt.datetime.now(tz=_dt.UTC).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")


def _now_iso() -> str:
    return (
        _dt.datetime.now(tz=_dt.UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _content_addressed_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return f"{prefix}-{digest[:24]}"


# ── Task: find voters (Pregel-style cohort intersection) ───────────────


async def task_karma_dao_find_voters(**kwargs: Any) -> dict[str, Any]:
    """Discover eligible 覚者 voters via 2-hop graph traversal from
    edge endpoints, excluding the source/target/opener themselves.

    Phase K1 heuristic: voter eligibility = "appears as source on at
    least one help-direction edge with vul ≥ 1.0 in the past 1y AND has
    zero floor violations in the past 5y" (positive multi-generational
    karma streak proxy). The full 覚者 status check is Phase K2.
    """
    edge_id = kwargs.get("edgeId")
    candidate = kwargs.get("candidate") or {}
    opened_by = kwargs.get("openedBy") or ""
    min_voters = int(kwargs.get("minVoters") or 5)

    seeds: set[str] = set()
    if edge_id:
        with sync_cursor() as cur:
            cur.execute(
                """
                SELECT source_did_at_event, target_did_at_event
                FROM edge_karma_dependency
                WHERE edge_id = %s
                LIMIT 1
                """,
                (edge_id,),
            )
            row = cur.fetchone()
            if row:
                if row[0]:
                    seeds.add(row[0])
                if row[1]:
                    seeds.add(row[1])
    else:
        if candidate.get("sourceDid"):
            seeds.add(candidate["sourceDid"])
        if candidate.get("targetDid"):
            seeds.add(candidate["targetDid"])

    excluded = set(seeds) | {opened_by}
    if not seeds:
        return {"voters": [], "voterCount": 0}

    one_year_ago = _now_ms() - 365 * 24 * 60 * 60 * 1000
    five_years_ago = _now_ms() - 5 * 365 * 24 * 60 * 60 * 1000

    with sync_cursor() as cur:
        # Pregel superstep 1: 1-hop neighbors of seeds (in either direction).
        seed_list = list(seeds)
        placeholders = ",".join(["%s"] * len(seed_list))
        cur.execute(
            f"""
            SELECT DISTINCT
                CASE WHEN source_did_at_event IN ({placeholders})
                     THEN target_did_at_event
                     ELSE source_did_at_event
                END AS neighbor_did
            FROM edge_karma_dependency
            WHERE source_did_at_event IN ({placeholders})
               OR target_did_at_event IN ({placeholders})
            """,
            tuple(seed_list) * 3,
        )
        neighbors = {r[0] for r in cur.fetchall() if r[0]}

        # Filter: positive karma streak + no recent floor violation.
        candidates: list[str] = []
        for did in neighbors:
            if did in excluded:
                continue

            # Has at least one help-direction edge in past 1y?
            cur.execute(
                """
                SELECT count(*)
                FROM edge_karma_dependency
                WHERE source_did_at_event = %s
                  AND direction = 'help'
                  AND ts_ms >= %s
                """,
                (did, one_year_ago),
            )
            if int(cur.fetchone()[0]) == 0:
                continue

            # Zero floor violations in past 5y?
            cur.execute(
                """
                SELECT count(*)
                FROM edge_karma_dependency
                WHERE source_did_at_event = %s
                  AND tier = 'floor'
                  AND direction = 'harm'
                  AND ts_ms >= %s
                """,
                (did, five_years_ago),
            )
            if int(cur.fetchone()[0]) > 0:
                continue

            candidates.append(did)
            if len(candidates) >= min_voters * 4:  # enough headroom
                break

    return {"voters": candidates, "voterCount": len(candidates)}


# ── Task: open arbitration ─────────────────────────────────────────────


async def task_karma_dao_open_arbitration(**kwargs: Any) -> dict[str, Any]:
    edge_id = kwargs.get("edgeId") or ""
    candidate = kwargs.get("candidate")
    opened_by = kwargs["openedBy"]
    rationale = kwargs.get("rationale") or ""
    voting_days = int(kwargs.get("votingDays") or 7)
    min_voters = int(kwargs.get("minVoters") or 5)
    voters = kwargs.get("voters") or []
    if not isinstance(voters, list):
        voters = []

    nonce = uuid.uuid4().hex
    arbitration_id = _content_addressed_id(
        "arb", edge_id or "candidate", opened_by, str(_now_ms()), nonce
    )
    vertex_id = f"arbitration-{arbitration_id}"

    opened_at = _now_ts()
    opened_at_ms = _now_ms()
    closes_at_ms = opened_at_ms + voting_days * 24 * 60 * 60 * 1000
    today_iso = _dt.datetime.now(tz=_dt.UTC).date().isoformat()

    candidate_json = json.dumps(candidate, separators=(",", ":")) if candidate else None
    invited_csv = ",".join(voters)

    with sync_cursor() as cur:
        cur.execute(
            """
            INSERT INTO vertex_karma_arbitration (
                vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                arbitration_id, edge_id, candidate_json, opened_by_did,
                opened_at, opened_at_ms, closes_at_ms,
                voting_days, min_voters, invited_voters_csv,
                rationale, status,
                created_at, org_id, user_id, actor_id
            ) VALUES (
                %s, NULL, %s, 1, %s,
                %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, 'open',
                %s, %s, %s, %s
            )
            """,
            (
                vertex_id, today_iso, opened_by,
                arbitration_id, edge_id or None, candidate_json, opened_by,
                opened_at, opened_at_ms, closes_at_ms,
                voting_days, min_voters, invited_csv,
                rationale,
                opened_at, opened_by, opened_by, "karma.dao.openArbitration",
            ),
        )

    return {"arbitrationId": arbitration_id, "closesAtMs": closes_at_ms}


# ── Task: cast vote ────────────────────────────────────────────────────


def _tally_for(arbitration_id: str) -> dict[str, int]:
    counts = {p: 0 for p in VOTE_POSITIONS}
    with sync_cursor() as cur:
        cur.execute(
            """
            SELECT vote_position, count(*)
            FROM vertex_karma_vote
            WHERE arbitration_id = %s
            GROUP BY vote_position
            """,
            (arbitration_id,),
        )
        for pos, cnt in cur.fetchall():
            if pos in counts:
                counts[pos] = int(cnt)
    counts["total"] = sum(counts[p] for p in VOTE_POSITIONS)
    return counts


def _supermajority_outcome(tally: dict[str, int]) -> tuple[bool, str, float]:
    """Return (reached, position, supermajority_pct).

    Supermajority = position has ≥ 2/3 of non-abstain votes
    AND non-abstain total >= 3 (minimum substantive participation).
    """
    non_abstain = tally["total"] - tally.get("abstain", 0)
    if non_abstain < 3:
        return False, "", 0.0
    best_pos = ""
    best_count = 0
    for pos in ("admit", "floor", "dismiss"):
        c = tally.get(pos, 0)
        if c > best_count:
            best_count = c
            best_pos = pos
    pct = best_count / non_abstain if non_abstain > 0 else 0.0
    return pct >= SUPERMAJORITY_PCT, best_pos, pct


async def task_karma_dao_cast_vote(**kwargs: Any) -> dict[str, Any]:
    arbitration_id = kwargs["arbitrationId"]
    voter_did = kwargs["voterDid"]
    position = (kwargs["position"] or "").lower()
    signature = kwargs["signature"]
    signature_alg = kwargs.get("signatureAlg") or "es256"
    rationale_cid = kwargs.get("rationaleCid")

    if position not in VOTE_POSITIONS:
        raise ValueError(f"karma.dao.castVote: invalid position {position}")

    now_ms = _now_ms()

    with sync_cursor() as cur:
        # Verify arbitration is open + voter is invited + window not closed.
        cur.execute(
            """
            SELECT status, closes_at_ms, invited_voters_csv
            FROM vertex_karma_arbitration
            WHERE arbitration_id = %s
            LIMIT 1
            """,
            (arbitration_id,),
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(f"arbitration {arbitration_id} not found")
        status, closes_at_ms, invited_csv = row
        if status != "open":
            raise ValueError(f"arbitration not open (status={status})")
        if int(closes_at_ms) <= now_ms:
            raise ValueError("voting window closed")
        invited = set((invited_csv or "").split(","))
        if voter_did not in invited:
            raise ValueError("voter not in invited set")

        # No double-vote check.
        cur.execute(
            """
            SELECT count(*) FROM vertex_karma_vote
            WHERE arbitration_id = %s AND voter_did = %s
            """,
            (arbitration_id, voter_did),
        )
        if int(cur.fetchone()[0]) > 0:
            raise ValueError("voter already cast")

        vote_id = _content_addressed_id(
            "vote", arbitration_id, voter_did, position, str(now_ms)
        )
        vertex_id = f"vote-{vote_id}"
        today_iso = _dt.datetime.now(tz=_dt.UTC).date().isoformat()

        cur.execute(
            """
            INSERT INTO vertex_karma_vote (
                vertex_id, _seq, created_date, sensitivity_ord, owner_did,
                vote_id, arbitration_id, voter_did, vote_position,
                signature, signature_alg, rationale_cid, ts_ms,
                created_at, org_id, user_id, actor_id
            ) VALUES (
                %s, NULL, %s, 1, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            """,
            (
                vertex_id, today_iso, voter_did,
                vote_id, arbitration_id, voter_did, position,
                signature, signature_alg, rationale_cid, now_ms,
                _now_ts(), voter_did, voter_did, "karma.dao.castVote",
            ),
        )

    tally = _tally_for(arbitration_id)
    reached, majority_pos, pct = _supermajority_outcome(tally)

    return {
        "voteId": vote_id,
        "tally": tally,
        "quorumReached": reached,
        "majorityPosition": majority_pos,
        "supermajorityPct": pct,
    }


# ── Task: finalize ─────────────────────────────────────────────────────


async def task_karma_dao_finalize(**kwargs: Any) -> dict[str, Any]:
    arbitration_id = kwargs["arbitrationId"]
    majority_position = kwargs.get("majorityPosition") or "dismiss"
    supermajority_pct = float(kwargs.get("supermajorityPct") or 0.0)
    finalized_at = _now_ts()

    with sync_cursor() as cur:
        cur.execute(
            """
            UPDATE vertex_karma_arbitration
            SET status = 'closed',
                closed_at = %s,
                finalized_position = %s,
                finalized_at = %s,
                finalized_supermajority_pct = %s
            WHERE arbitration_id = %s
            """,
            (
                finalized_at,
                majority_position,
                finalized_at,
                supermajority_pct,
                arbitration_id,
            ),
        )

    return {"finalizedAt": finalized_at}


# ── Task: sweep expired (timer-driven) ──────────────────────────────────


async def task_karma_dao_sweep_expired(**kwargs: Any) -> dict[str, Any]:
    """R/PT15M sweeper. Finalize arbitrations whose window has closed
    by plurality (tied → 'dismiss')."""
    now_ms = _now_ms()
    finalized = 0
    still_open = 0
    finalized_at = _now_ts()

    with sync_cursor() as cur:
        cur.execute(
            """
            SELECT arbitration_id
            FROM vertex_karma_arbitration
            WHERE status = 'open' AND closes_at_ms <= %s
            ORDER BY closes_at_ms ASC
            LIMIT 200
            """,
            (now_ms,),
        )
        expired_ids = [r[0] for r in cur.fetchall()]

        for arb_id in expired_ids:
            tally = _tally_for(arb_id)
            non_abstain = tally["total"] - tally.get("abstain", 0)

            # Plurality among admit/floor/dismiss.
            best_pos = "dismiss"
            best_count = -1
            tied = False
            for pos in ("admit", "floor", "dismiss"):
                c = tally.get(pos, 0)
                if c > best_count:
                    best_pos = pos
                    best_count = c
                    tied = False
                elif c == best_count:
                    tied = True

            # Tied → conservative dismiss.
            if tied:
                best_pos = "dismiss"

            pct = best_count / non_abstain if non_abstain > 0 else 0.0

            cur.execute(
                """
                UPDATE vertex_karma_arbitration
                SET status = 'closed',
                    closed_at = %s,
                    finalized_position = %s,
                    finalized_at = %s,
                    finalized_supermajority_pct = %s
                WHERE arbitration_id = %s AND status = 'open'
                """,
                (finalized_at, best_pos, finalized_at, pct, arb_id),
            )
            finalized += 1

        cur.execute(
            "SELECT count(*) FROM vertex_karma_arbitration WHERE status = 'open'"
        )
        still_open = int(cur.fetchone()[0])

    return {"finalized": finalized, "stillOpen": still_open}


# ── Worker registration ─────────────────────────────────────────────────


def register(worker: Any, *, timeout_ms: int = 60_000) -> None:
    """Wire all karma DAO task types onto the shared LangServer worker.

      task_type="karma.dao.findVoters"
      task_type="karma.dao.openArbitration"
      task_type="karma.dao.castVote"
      task_type="karma.dao.finalize"
      task_type="karma.dao.sweepExpired"
    """
    def t(name: str, fn: Any, *, ms: int | None = None) -> None:
        worker.task(task_type=name, single_value=False, timeout_ms=ms or timeout_ms)(fn)

    t("karma.dao.findVoters",      task_karma_dao_find_voters,      ms=60_000)
    t("karma.dao.openArbitration", task_karma_dao_open_arbitration, ms=30_000)
    t("karma.dao.castVote",        task_karma_dao_cast_vote,        ms=30_000)
    t("karma.dao.finalize",        task_karma_dao_finalize,         ms=30_000)
    t("karma.dao.sweepExpired",    task_karma_dao_sweep_expired,    ms=60_000)


__all__ = [
    "register",
    "task_karma_dao_find_voters",
    "task_karma_dao_open_arbitration",
    "task_karma_dao_cast_vote",
    "task_karma_dao_finalize",
    "task_karma_dao_sweep_expired",
]
