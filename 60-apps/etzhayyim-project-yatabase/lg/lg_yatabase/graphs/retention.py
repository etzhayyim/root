"""yatabase Retention actor — churn signal detection and win-back.

Runs daily at 11:00 JST via APScheduler (registered in server.py).
Monitors paid tenants for inactivity and declining usage, then:
  - Low risk (7-13d inactive): sends "What are you building?" email
  - Medium risk (14-20d): sends feature highlight + support offer
  - High risk (21d+): escalates to human review via outbox

Pipeline: detect_signals → classify_risk → engage_low_medium → escalate_high → report
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from lg_yatabase.bmc.db import execute, fetch

_log = logging.getLogger(__name__)

_LOW_SUBJECT = "yatabase — 最近どのようなものを構築されていますか？"
_MEDIUM_SUBJECT = "yatabase — お困りのことはありませんか？"
_LOW_BODY = """\
こんにちは！

yatabase をご利用いただきありがとうございます。
最近クエリが少なくなっているようですが、どのようなものを構築されていますか？

新機能のご紹介:
  • OWL EL reasoning — `SPARQL CONSTRUCT` でオントロジー推論
  • MCP endpoint — Claude / Cursor から直接グラフを操作
  • Streaming MV — リアルタイム集計ビュー

何かお役に立てることがあれば、このメールにご返信ください。

yatabase team
"""

_MEDIUM_BODY = """\
こんにちは！

お変わりありませんか？最近 yatabase のご利用が少なくなっているようです。

セットアップでお困りの場合は、15分のサポートをご提供しています:
  → https://yatabase.etzhayyim.com/support

または docs をご覧ください:
  → https://yatabase.etzhayyim.com/docs

引き続きよろしくお願いします。

yatabase team
"""


# ── State ─────────────────────────────────────────────────────────────────────

class RetentionState(TypedDict, total=False):
    run_date: str
    low_risk: list[dict]     # 7-13d no queries
    medium_risk: list[dict]  # 14-20d no queries
    high_risk: list[dict]    # 21d+ no queries → escalate human
    reengaged: int
    escalated: int
    summary: str


# ── Nodes ──────────────────────────────────────────────────────────────────────

async def detect_signals(state: RetentionState) -> RetentionState:
    today = datetime.now(timezone.utc).date().isoformat()
    low: list[dict] = []
    medium: list[dict] = []
    high: list[dict] = []
    try:
        # owner_did = org_did; columns added by migration 20260521110000
        rows = await fetch(
            """
            SELECT vertex_id, owner_did AS org_did,
                   COALESCE(contact_email, '') AS contact_email,
                   COALESCE(plan, 'free') AS plan,
                   last_query_at,
                   EXTRACT(EPOCH FROM (NOW() - last_query_at)) / 86400 AS days_inactive
            FROM vertex_api_key
            WHERE COALESCE(plan, 'free') IN ('starter', 'pro', 'business')
              AND last_query_at IS NOT NULL
              AND last_query_at < NOW() - INTERVAL '7 days'
            ORDER BY last_query_at ASC
            LIMIT 100
            """
        )
        for r in rows:
            d = float(r.get("days_inactive") or 0)
            rec = dict(r)
            if d < 14:
                low.append(rec)
            elif d < 21:
                medium.append(rec)
            else:
                high.append(rec)
    except Exception as e:
        _log.warning("[retention] detect_signals query failed: %s", e)

    _log.info("[retention] low=%d medium=%d high=%d", len(low), len(medium), len(high))
    return {**state, "run_date": today, "low_risk": low, "medium_risk": medium, "high_risk": high}


async def engage_low_medium(state: RetentionState) -> RetentionState:
    reengaged = 0

    async def _send(org_did: str, email: str, kind: str, subject: str, body: str) -> None:
        nonlocal reengaged
        try:
            existing = await fetch(
                """
                SELECT 1 FROM vertex_email_outbox
                WHERE org_did = $1 AND kind = $2
                  AND created_at > NOW() - INTERVAL '30 days'
                LIMIT 1
                """,
                org_did, kind,
            )
            if existing:
                return
        except Exception:
            pass
        try:
            await execute(
                """
                INSERT INTO vertex_email_outbox
                  (vertex_id, org_did, kind, subject, body_text,
                   recipient_email, status, created_at)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
                """,
                str(uuid.uuid4()),
                org_did,
                kind,
                subject,
                body,
                email,
                "queued-no-recipient" if not (email or "").strip() else "queued",
                datetime.now(timezone.utc),
            )
            reengaged += 1
        except Exception as e:
            _log.warning("[retention] insert failed for %s: %s", org_did, e)

    for t in (state.get("low_risk") or []):
        await _send(
            t.get("org_did", ""), t.get("contact_email", ""),
            "reengagement-low", _LOW_SUBJECT, _LOW_BODY,
        )
    for t in (state.get("medium_risk") or []):
        await _send(
            t.get("org_did", ""), t.get("contact_email", ""),
            "reengagement-medium", _MEDIUM_SUBJECT, _MEDIUM_BODY,
        )

    return {**state, "reengaged": reengaged}


async def escalate_high(state: RetentionState) -> RetentionState:
    escalated = 0
    for t in (state.get("high_risk") or []):
        org_did = t.get("org_did", "unknown")
        days = t.get("days_inactive", 0)
        plan = t.get("plan", "unknown")
        try:
            existing = await fetch(
                """
                SELECT 1 FROM vertex_email_outbox
                WHERE org_did = $1 AND kind = 'churn-escalate'
                  AND created_at > NOW() - INTERVAL '30 days'
                LIMIT 1
                """,
                org_did,
            )
            if existing:
                continue
        except Exception:
            pass
        try:
            body = (
                f"org_did: {org_did}\n"
                f"plan: {plan}\n"
                f"days_inactive: {days:.0f}\n"
                f"contact_email: {t.get('contact_email', '')}\n\n"
                "アクション: 割引オファーまたはキャンセル処理を判断してください。"
            )
            await execute(
                """
                INSERT INTO vertex_email_outbox
                  (vertex_id, org_did, kind, subject, body_text,
                   recipient_email, status, created_at)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
                """,
                str(uuid.uuid4()),
                org_did,
                "churn-escalate",
                f"yatabase チャーンリスク: {org_did[:24]} ({plan}, {days:.0f}d inactive)",
                body,
                "jun@etzhayyim.com",
                "queued-no-recipient",
                datetime.now(timezone.utc),
            )
            escalated += 1
        except Exception as e:
            _log.warning("[retention] escalate insert failed for %s: %s", org_did, e)

    return {**state, "escalated": escalated}


async def report(state: RetentionState) -> RetentionState:
    run_date = state.get("run_date", "")
    low = len(state.get("low_risk") or [])
    med = len(state.get("medium_risk") or [])
    high = len(state.get("high_risk") or [])
    reengaged = state.get("reengaged", 0)
    escalated = state.get("escalated", 0)
    summary = (
        f"[{run_date}] retention: low={low} medium={med} high={high} "
        f"reengaged={reengaged} escalated={escalated}"
    )
    _log.info("[retention] %s", summary)
    return {**state, "summary": summary}


# ── Graph ──────────────────────────────────────────────────────────────────────

def _build() -> Any:
    sg = StateGraph(RetentionState)
    sg.add_node("detect_signals", detect_signals)
    sg.add_node("engage_low_medium", engage_low_medium)
    sg.add_node("escalate_high", escalate_high)
    sg.add_node("report", report)
    sg.add_edge(START, "detect_signals")
    sg.add_edge("detect_signals", "engage_low_medium")
    sg.add_edge("engage_low_medium", "escalate_high")
    sg.add_edge("escalate_high", "report")
    sg.add_edge("report", END)
    return sg.compile()


GRAPH = _build()
