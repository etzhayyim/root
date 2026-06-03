"""Live KPI evaluator for the Business Operating graph.

Loads before/after rows from `vertex_yatabase_metrics_daily`, maps them into
the `metrics_before` / `metrics_after` contract, then invokes the deterministic
business_operating graph. This is the production-facing proof path for
"did the agent actually move the business?"
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from lg_yatabase.bmc.db import fetchrow
from lg_yatabase.graphs.business_operating import GRAPH as BUSINESS_OPERATING_GRAPH


class BusinessOperatingLiveEvalState(TypedDict, total=False):
    before_date: str
    after_date: str
    business_input: dict[str, Any]
    lift_evaluation: dict[str, Any]
    metrics_before: dict[str, Any]
    metrics_after: dict[str, Any]
    business_operating_result: dict[str, Any]
    report: dict[str, Any]
    error: str


_METRIC_KEYS = [
    "mrr_total_jpy",
    "total_tenants",
    "activated_count",
    "mcp_calls_30d",
    "conversion_rate",
    "churn_rate",
]


async def load_metrics(state: BusinessOperatingLiveEvalState) -> BusinessOperatingLiveEvalState:
    before_date = state.get("before_date")
    after_date = state.get("after_date")
    if not before_date or not after_date:
        return {"error": "before_date and after_date are required"}

    before = await _load_metrics_row(before_date)
    after = await _load_metrics_row(after_date)
    if before is None:
        return {"error": f"metrics_before not found for {before_date}"}
    if after is None:
        return {"error": f"metrics_after not found for {after_date}"}
    return {"metrics_before": before, "metrics_after": after}


async def run_business_operating(
    state: BusinessOperatingLiveEvalState,
) -> BusinessOperatingLiveEvalState:
    if state.get("error"):
        return {}

    business_input = dict(state.get("business_input") or {})
    business_input["metrics_before"] = state["metrics_before"]
    business_input["metrics_after"] = state["metrics_after"]
    business_input["lift_evaluation"] = state.get("lift_evaluation") or {
        "primary_metric": "mrr_total_jpy",
        "min_absolute_lift": 1,
        "min_relative_lift": 0,
        "guardrail_metrics": ["churn_rate"],
        "max_guardrail_drop": 0.0,
    }
    result = await BUSINESS_OPERATING_GRAPH.ainvoke(business_input)
    return {"business_operating_result": result}


def report(state: BusinessOperatingLiveEvalState) -> BusinessOperatingLiveEvalState:
    if state.get("error"):
        return {
            "report": {
                "ok": False,
                "error": state["error"],
                "before_date": state.get("before_date"),
                "after_date": state.get("after_date"),
            }
        }

    result = state.get("business_operating_result") or {}
    progress = ((result.get("report") or {}).get("business_progress") or {})
    return {
        "report": {
            "ok": True,
            "before_date": state.get("before_date"),
            "after_date": state.get("after_date"),
            "can_advance_business": progress.get("can_advance_business", False),
            "has_proven_business_lift": progress.get("has_proven_business_lift", False),
            "live_kpi_evidence": progress.get("live_kpi_evidence", {}),
            "business_progress": progress,
            "decisions": (result.get("report") or {}).get("decisions", []),
            "actions": (result.get("report") or {}).get("actions", []),
            "risks": (result.get("report") or {}).get("risks", []),
        }
    }


async def _load_metrics_row(run_date: str) -> dict[str, Any] | None:
    row = await fetchrow(
        """
        SELECT run_date, mrr_total_jpy, mrr_by_tier, total_tenants,
               activated_count, mcp_calls_30d, query_lang_split,
               conversion_rate, churn_rate
        FROM vertex_yatabase_metrics_daily
        WHERE run_date = $1
        LIMIT 1
        """,
        date.fromisoformat(run_date),
    )
    if row is None:
        return None

    metrics: dict[str, Any] = {"run_date": str(row.get("run_date") or run_date)}
    for key in _METRIC_KEYS:
        metrics[key] = row.get(key)

    # business_operating fixtures often use paid_conversion; keep an alias so
    # live rows can drive the same primary metric name.
    metrics["paid_conversion"] = row.get("conversion_rate")
    metrics["mrr_by_tier"] = _decode_jsonish(row.get("mrr_by_tier"), {})
    metrics["query_lang_split"] = _decode_jsonish(row.get("query_lang_split"), {})
    return metrics


def _decode_jsonish(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except json.JSONDecodeError:
        return default


def _build() -> Any:
    sg = StateGraph(BusinessOperatingLiveEvalState)
    sg.add_node("load_metrics", load_metrics)
    sg.add_node("run_business_operating", run_business_operating)
    sg.add_node("report", report)
    sg.add_edge(START, "load_metrics")
    sg.add_edge("load_metrics", "run_business_operating")
    sg.add_edge("run_business_operating", "report")
    sg.add_edge("report", END)
    return sg.compile()


GRAPH = _build()

