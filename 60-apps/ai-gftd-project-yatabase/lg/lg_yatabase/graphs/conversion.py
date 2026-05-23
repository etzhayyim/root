"""yatabase Conversion actor — usage-based upgrade trigger.

Runs daily at 10:15 JST via APScheduler (registered in server.py).
Identifies free tenants approaching quota and sends targeted upgrade offers.

Pipeline: find_candidates → score → enqueue_offer → report

Quota thresholds (80% of Free tier):
  node_count   > 400,000  (Free limit: 500K)
  mcp_calls_mo > 8,000    (Free limit: 10K)
  query_7d     > 100      (high-engagement signal)
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from lg_yatabase.bmc.db import execute, fetch
from . import _llm

_log = logging.getLogger(__name__)

_UPGRADE_SUBJECT = "yatabase — Developer プランで制限を解除しませんか？"


def _upgrade_body(reason: str, llm_note: str = "") -> str:
    note = f"\n\n{llm_note}" if llm_note else ""
    return f"""\
こんにちは！

yatabase をご利用いただきありがとうございます。

{reason}

◆ Developer プラン ($33/月) にアップグレードすると:
  • API リクエスト 1,000万/月 (Free の 333×)
  • ストレージ 500 GB
  • MV スロット 100 個
  • OWL EL+RL+QL reasoning
  • SLA 99.9%

今すぐアップグレード: https://yatabase.etzhayyim.com/studio/billing{note}

ご質問があればいつでもご連絡ください。

yatabase team
"""


# ── State ─────────────────────────────────────────────────────────────────────

class ConversionState(TypedDict, total=False):
    run_date: str
    quota_candidates: list[dict]   # approaching node/MCP quota
    activity_candidates: list[dict]  # high query activity
    triggered: int
    summary: str


# ── Nodes ──────────────────────────────────────────────────────────────────────

async def find_candidates(state: ConversionState) -> ConversionState:
    today = datetime.now(timezone.utc).date().isoformat()
    quota: list[dict] = []
    activity: list[dict] = []
    try:
        # owner_did = org_did; columns added by migration 20260521110000
        quota_rows = await fetch(
            """
            SELECT vertex_id, owner_did AS org_did,
                   COALESCE(contact_email, '') AS contact_email,
                   COALESCE(node_count, 0) AS node_count,
                   COALESCE(mcp_calls_month, 0) AS mcp_calls_month
            FROM vertex_api_key
            WHERE COALESCE(plan, 'free') = 'free'
              AND (COALESCE(node_count, 0) > 400000 OR COALESCE(mcp_calls_month, 0) > 8000)
            LIMIT 30
            """
        )
        quota = [dict(r) for r in quota_rows]
    except Exception as e:
        _log.warning("[conversion] quota query failed: %s", e)

    try:
        activity_rows = await fetch(
            """
            SELECT ak.vertex_id, ak.owner_did AS org_did,
                   COALESCE(ak.contact_email, '') AS contact_email,
                   COALESCE(SUM(be.qty), 0) AS query_7d
            FROM vertex_api_key ak
            LEFT JOIN vertex_billing_event be
              ON be.org_did = ak.owner_did
             AND be.metric = 'api_request'
             AND be.created_at > NOW() - INTERVAL '7 days'
            WHERE COALESCE(ak.plan, 'free') = 'free'
            GROUP BY ak.vertex_id, ak.owner_did, ak.contact_email
            HAVING COALESCE(SUM(be.qty), 0) > 100
            LIMIT 30
            """
        )
        activity = [dict(r) for r in activity_rows]
    except Exception as e:
        _log.warning("[conversion] activity query failed: %s", e)

    _log.info("[conversion] quota=%d activity=%d candidates", len(quota), len(activity))
    return {**state, "run_date": today, "quota_candidates": quota, "activity_candidates": activity}


async def enqueue_offer(state: ConversionState) -> ConversionState:
    triggered = 0
    seen: set[str] = set()

    async def _send(org_did: str, email: str, reason: str) -> None:
        nonlocal triggered
        if org_did in seen:
            return
        seen.add(org_did)
        # Idempotent: skip if upgrade-trigger sent within 14d
        try:
            existing = await fetch(
                """
                SELECT 1 FROM vertex_email_outbox
                WHERE org_did = $1 AND kind = 'upgrade-trigger'
                  AND created_at > NOW() - INTERVAL '14 days'
                LIMIT 1
                """,
                org_did,
            )
            if existing:
                return
        except Exception:
            pass

        # Optional LLM personalisation
        llm_note = ""
        try:
            parsed, source = _llm.call_llm_json(
                f"yatabase upgrade trigger. reason={reason}. "
                "One personalized benefit sentence ≤60 chars (Japanese OK). "
                'JSON: {"note": "..."}',
                max_tokens=80,
            )
            if parsed and source == "llm":
                llm_note = str(parsed.get("note", ""))[:80]
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
                "upgrade-trigger",
                _UPGRADE_SUBJECT,
                _upgrade_body(reason, llm_note),
                email,
                "queued-no-recipient" if not email.strip() else "queued",
                datetime.now(timezone.utc),
            )
            triggered += 1
        except Exception as e:
            _log.warning("[conversion] insert failed for %s: %s", org_did, e)

    for t in (state.get("quota_candidates") or []):
        nc = t.get("node_count", 0)
        mc = t.get("mcp_calls_month", 0)
        if nc > 400000:
            reason = f"現在 {nc:,} ノードを使用中です。無料プランの上限 (500,000ノード) まであと少しです。"
        else:
            reason = f"今月 {mc:,} 件の MCP calls を使用中です。無料上限 (10,000件) に近づいています。"
        await _send(t.get("org_did", ""), t.get("contact_email", ""), reason)

    for t in (state.get("activity_candidates") or []):
        q7 = t.get("query_7d", 0)
        reason = f"直近7日間で {int(q7):,} 件のクエリを実行されています。活発なご利用ありがとうございます！"
        await _send(t.get("org_did", ""), t.get("contact_email", ""), reason)

    return {**state, "triggered": triggered}


async def report(state: ConversionState) -> ConversionState:
    run_date = state.get("run_date", "")
    triggered = state.get("triggered", 0)
    quota = len(state.get("quota_candidates") or [])
    activity = len(state.get("activity_candidates") or [])
    summary = (
        f"[{run_date}] conversion: quota_candidates={quota} "
        f"activity_candidates={activity} triggered={triggered}"
    )
    _log.info("[conversion] %s", summary)
    return {**state, "summary": summary}


# ── Graph ──────────────────────────────────────────────────────────────────────

def _build() -> Any:
    sg = StateGraph(ConversionState)
    sg.add_node("find_candidates", find_candidates)
    sg.add_node("enqueue_offer", enqueue_offer)
    sg.add_node("report", report)
    sg.add_edge(START, "find_candidates")
    sg.add_edge("find_candidates", "enqueue_offer")
    sg.add_edge("enqueue_offer", "report")
    sg.add_edge("report", END)
    return sg.compile()


GRAPH = _build()
