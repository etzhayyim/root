"""yatabase Metrics Daily actor — KPI snapshot for bmc_agent and Studio dashboard.

Runs daily at 09:00 JST (3 min before bmc_agent at 09:03 JST) via APScheduler.
Collects MRR, usage, cohort conversion, and churn; writes to
vertex_yatabase_metrics_daily.

Pipeline:
    collect_mrr → collect_usage → collect_cohort → snapshot → report

Env vars: none additional (uses shared DB pool)
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import date, datetime, timezone
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from lg_yatabase.bmc.db import execute, fetch, fetchval

_log = logging.getLogger(__name__)

_PLAN_PRICE_JPY: dict[str, int] = {
    "starter": 1980,
    "pro": 4980,
    "developer": 4980,   # legacy alias
    "business": 98000,
    "enterprise": 1000000,
}


# ── State ─────────────────────────────────────────────────────────────────────

class MetricsDailyState(TypedDict, total=False):
    run_date: str
    mrr_by_tier: dict[str, int]
    mrr_total_jpy: int
    total_tenants: int
    activated_count: int
    mcp_calls_30d: int
    query_lang_split: dict[str, float]
    conversion_rate_30d: float
    churn_rate_30d: float
    summary: str


# ── Nodes ─────────────────────────────────────────────────────────────────────

async def collect_mrr(state: MetricsDailyState) -> MetricsDailyState:
    today_str = date.today().isoformat()
    mrr_by_tier: dict[str, int] = {}
    total_tenants = 0
    try:
        rows = await fetch(
            """
            SELECT plan, COUNT(*) AS cnt
            FROM vertex_api_key
            WHERE revoked_at IS NULL
            GROUP BY plan
            LIMIT 20
            """
        )
        for r in rows:
            plan = str(r["plan"] or "free").lower()
            cnt = int(r["cnt"])
            total_tenants += cnt
            price = _PLAN_PRICE_JPY.get(plan, 0)
            mrr_by_tier[plan] = mrr_by_tier.get(plan, 0) + price * cnt
    except Exception as e:
        _log.warning("[metrics_daily] collect_mrr failed: %s", e)

    mrr_total = sum(mrr_by_tier.values())
    _log.info("[metrics_daily] MRR ¥%d, tenants=%d", mrr_total, total_tenants)
    return {
        **state,
        "run_date": today_str,
        "mrr_by_tier": mrr_by_tier,
        "mrr_total_jpy": mrr_total,
        "total_tenants": total_tenants,
    }


async def collect_usage(state: MetricsDailyState) -> MetricsDailyState:
    mcp_calls_30d = 0
    query_lang_split: dict[str, float] = {}
    try:
        mcp_val = await fetchval(
            """
            SELECT COALESCE(SUM(quantity), 0)
            FROM vertex_billing_event
            WHERE metric = 'mcp_call'
              AND created_at >= NOW() - INTERVAL '30 days'
            """
        )
        mcp_calls_30d = int(mcp_val or 0)

        lang_rows = await fetch(
            """
            SELECT query_lang, COUNT(*) AS cnt
            FROM vertex_billing_event
            WHERE metric = 'query'
              AND created_at >= NOW() - INTERVAL '30 days'
            GROUP BY query_lang
            LIMIT 10
            """
        )
        total_queries = sum(int(r["cnt"]) for r in lang_rows)
        if total_queries > 0:
            for r in lang_rows:
                lang = str(r["query_lang"] or "unknown")
                query_lang_split[lang] = round(int(r["cnt"]) / total_queries, 4)
    except Exception as e:
        _log.warning("[metrics_daily] collect_usage failed: %s", e)

    _log.info("[metrics_daily] mcp_calls_30d=%d lang_split=%s", mcp_calls_30d, query_lang_split)
    return {**state, "mcp_calls_30d": mcp_calls_30d, "query_lang_split": query_lang_split}


async def collect_cohort(state: MetricsDailyState) -> MetricsDailyState:
    conversion_rate = 0.0
    churn_rate = 0.0
    activated_count = 0
    try:
        # Signups in last 30 days
        signups_30d = await fetchval(
            """
            SELECT COUNT(*) FROM vertex_api_key
            WHERE created_at >= NOW() - INTERVAL '30 days'
              AND revoked_at IS NULL
            """
        )
        # How many of those converted to paid within 30d
        paid_30d = await fetchval(
            """
            SELECT COUNT(DISTINCT org_did) FROM vertex_billing_event
            WHERE metric = 'subscription_start'
              AND created_at >= NOW() - INTERVAL '30 days'
            """
        )
        if (signups_30d or 0) > 0:
            conversion_rate = round((paid_30d or 0) / (signups_30d or 1), 4)

        # Activated = tenants with >10 queries in last 7 days
        activated_count_val = await fetchval(
            """
            SELECT COUNT(DISTINCT org_did)
            FROM vertex_billing_event
            WHERE metric = 'query'
              AND created_at >= NOW() - INTERVAL '7 days'
            GROUP BY org_did
            HAVING COUNT(*) > 10
            """
        )
        activated_count = int(activated_count_val or 0)

        # Churn: paid tenants who cancelled in last 30 days / paid tenants 30d ago
        cancelled_30d = await fetchval(
            """
            SELECT COUNT(DISTINCT org_did) FROM vertex_billing_event
            WHERE metric = 'subscription_cancel'
              AND created_at >= NOW() - INTERVAL '30 days'
            """
        )
        paid_base = await fetchval(
            """
            SELECT COUNT(*) FROM vertex_api_key
            WHERE plan NOT IN ('free', 'anon')
              AND revoked_at IS NULL
            """
        )
        if (paid_base or 0) > 0:
            churn_rate = round((cancelled_30d or 0) / (paid_base or 1), 4)

    except Exception as e:
        _log.warning("[metrics_daily] collect_cohort failed: %s", e)

    _log.info(
        "[metrics_daily] conversion_rate=%.4f churn_rate=%.4f activated=%d",
        conversion_rate, churn_rate, activated_count,
    )
    return {
        **state,
        "conversion_rate_30d": conversion_rate,
        "churn_rate_30d": churn_rate,
        "activated_count": activated_count,
    }


async def snapshot(state: MetricsDailyState) -> MetricsDailyState:
    run_date = state.get("run_date", date.today().isoformat())
    try:
        await execute(
            """
            INSERT INTO vertex_yatabase_metrics_daily
              (run_date, mrr_total_jpy, mrr_by_tier, total_tenants,
               activated_count, mcp_calls_30d, query_lang_split,
               conversion_rate, churn_rate, created_at)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
            ON CONFLICT (run_date) DO UPDATE
              SET mrr_total_jpy   = EXCLUDED.mrr_total_jpy,
                  mrr_by_tier     = EXCLUDED.mrr_by_tier,
                  total_tenants   = EXCLUDED.total_tenants,
                  activated_count = EXCLUDED.activated_count,
                  mcp_calls_30d   = EXCLUDED.mcp_calls_30d,
                  query_lang_split= EXCLUDED.query_lang_split,
                  conversion_rate = EXCLUDED.conversion_rate,
                  churn_rate      = EXCLUDED.churn_rate
            """,
            run_date,
            state.get("mrr_total_jpy", 0),
            json.dumps(state.get("mrr_by_tier", {})),
            state.get("total_tenants", 0),
            state.get("activated_count", 0),
            state.get("mcp_calls_30d", 0),
            json.dumps(state.get("query_lang_split", {})),
            state.get("conversion_rate_30d", 0.0),
            state.get("churn_rate_30d", 0.0),
            datetime.now(timezone.utc),
        )
        _log.info("[metrics_daily] snapshot written for %s", run_date)
    except Exception as e:
        _log.warning("[metrics_daily] snapshot insert failed: %s", e)

    return state


async def report(state: MetricsDailyState) -> MetricsDailyState:
    run_date = state.get("run_date", "")
    mrr = state.get("mrr_total_jpy", 0)
    tenants = state.get("total_tenants", 0)
    activated = state.get("activated_count", 0)
    cvr = state.get("conversion_rate_30d", 0.0)
    churn = state.get("churn_rate_30d", 0.0)
    mcp = state.get("mcp_calls_30d", 0)
    summary = (
        f"[{run_date}] metrics_daily: MRR=¥{mrr:,} tenants={tenants} "
        f"activated={activated} CVR={cvr:.1%} churn={churn:.1%} MCP30d={mcp:,}"
    )
    # Report to bmc_agent context via outbox (kind='metrics-daily-report')
    try:
        await execute(
            """
            INSERT INTO vertex_email_outbox
              (vertex_id, org_did, kind, subject, body_text,
               recipient_email, status, created_at)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            """,
            str(uuid.uuid4()),
            "did:plc:yatabase-metrics-daily",
            "metrics-daily-report",
            f"yatabase Metrics Daily {run_date}",
            summary,
            "jun@gftd.group",
            "queued-no-recipient",
            datetime.now(timezone.utc),
        )
    except Exception as e:
        _log.warning("[metrics_daily] report outbox insert failed: %s", e)

    _log.info("[metrics_daily] %s", summary)
    return {**state, "summary": summary}


# ── Graph ──────────────────────────────────────────────────────────────────────

def _build() -> Any:
    sg = StateGraph(MetricsDailyState)
    sg.add_node("collect_mrr", collect_mrr)
    sg.add_node("collect_usage", collect_usage)
    sg.add_node("collect_cohort", collect_cohort)
    sg.add_node("snapshot", snapshot)
    sg.add_node("report", report)
    sg.add_edge(START, "collect_mrr")
    sg.add_edge("collect_mrr", "collect_usage")
    sg.add_edge("collect_usage", "collect_cohort")
    sg.add_edge("collect_cohort", "snapshot")
    sg.add_edge("snapshot", "report")
    sg.add_edge("report", END)
    return sg.compile()


GRAPH = _build()
