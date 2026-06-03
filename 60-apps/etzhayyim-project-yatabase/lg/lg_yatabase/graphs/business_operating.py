"""Business operating graph.

This graph is the orchestration layer for company-management / BMC work.
It keeps LLM-facing planning and synthesis separate from deterministic
math nodes. Heavy solvers can replace the local adapters later without
changing the LangGraph topology.
"""

from __future__ import annotations

import heapq
import math
import time
from collections import defaultdict
from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

AnalysisKind = Literal[
    "bmc",
    "kpi_causal",
    "financial_flow",
    "resource_allocation",
    "scheduling",
    "scenario_simulation",
    "market_game",
]


class BusinessOperatingState(TypedDict, total=False):
    company_profile: dict[str, Any]
    bmc: dict[str, Any]
    kpis: dict[str, Any]
    financials: dict[str, Any]
    constraints: dict[str, Any]
    market_signals: list[dict[str, Any]]
    projects: list[dict[str, Any]]
    resources: list[dict[str, Any]]
    tasks: list[dict[str, Any]]
    competitors: list[dict[str, Any]]
    requested_analyses: list[AnalysisKind]
    metrics_before: dict[str, Any]
    metrics_after: dict[str, Any]
    lift_evaluation: dict[str, Any]

    run_id: str
    started_at_ms: int
    bmc_graph: dict[str, Any]
    hypotheses: list[dict[str, Any]]
    analysis_results: dict[str, Any]
    decisions: list[dict[str, Any]]
    actions: list[dict[str, Any]]
    risks: list[dict[str, Any]]
    report: dict[str, Any]


BMC_BLOCKS = [
    "customer_segments",
    "value_propositions",
    "channels",
    "customer_relationships",
    "revenue_streams",
    "key_resources",
    "key_activities",
    "key_partners",
    "cost_structure",
]

BMC_EDGES = [
    ("customer_segments", "value_propositions", "needs"),
    ("value_propositions", "channels", "delivered_by"),
    ("channels", "customer_relationships", "supports"),
    ("channels", "revenue_streams", "drives"),
    ("customer_relationships", "revenue_streams", "retains"),
    ("key_activities", "value_propositions", "produces"),
    ("key_resources", "key_activities", "enables"),
    ("key_partners", "key_activities", "supports"),
    ("cost_structure", "key_activities", "constrains"),
    ("revenue_streams", "key_resources", "funds"),
]


def _now_ms() -> int:
    return int(time.time() * 1000)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _analysis_enabled(state: BusinessOperatingState, kind: AnalysisKind) -> bool:
    requested = state.get("requested_analyses") or []
    return not requested or kind in requested


def _append_result(
    state: BusinessOperatingState,
    key: str,
    value: dict[str, Any],
) -> dict[str, Any]:
    results = dict(state.get("analysis_results") or {})
    results[key] = value
    return {"analysis_results": results}


def intake(state: BusinessOperatingState) -> BusinessOperatingState:
    return {
        "run_id": state.get("run_id") or f"business-op-{_now_ms()}",
        "started_at_ms": state.get("started_at_ms") or _now_ms(),
        "company_profile": state.get("company_profile") or {},
        "bmc": state.get("bmc") or {},
        "kpis": state.get("kpis") or {},
        "financials": state.get("financials") or {},
        "constraints": state.get("constraints") or {},
        "market_signals": state.get("market_signals") or [],
        "projects": state.get("projects") or [],
        "resources": state.get("resources") or [],
        "tasks": state.get("tasks") or [],
        "competitors": state.get("competitors") or [],
        "metrics_before": state.get("metrics_before") or {},
        "metrics_after": state.get("metrics_after") or {},
        "lift_evaluation": state.get("lift_evaluation") or {},
        "analysis_results": state.get("analysis_results") or {},
        "hypotheses": state.get("hypotheses") or [],
        "decisions": state.get("decisions") or [],
        "actions": state.get("actions") or [],
        "risks": state.get("risks") or [],
    }


def bmc_topology_node(state: BusinessOperatingState) -> BusinessOperatingState:
    if not _analysis_enabled(state, "bmc"):
        return {}

    canvas = state.get("bmc") or {}
    nodes: list[dict[str, Any]] = []
    for block in BMC_BLOCKS:
        content = canvas.get(block)
        if isinstance(content, list):
            weight = len(content)
        elif isinstance(content, dict):
            weight = len(content)
        elif content:
            weight = 1
        else:
            weight = 0
        nodes.append({"id": block, "kind": "bmc_block", "weight": weight, "filled": weight > 0})

    edges = [{"source": s, "target": t, "relation": r} for s, t, r in BMC_EDGES]
    missing = [n["id"] for n in nodes if not n["filled"]]
    centrality = _degree_centrality([n["id"] for n in nodes], [(e["source"], e["target"]) for e in edges])
    graph = {
        "nodes": nodes,
        "edges": edges,
        "missing_blocks": missing,
        "centrality": centrality,
        "recommended_library": "NetworkX",
    }
    return {
        "bmc_graph": graph,
        **_append_result(state, "bmc", graph),
    }


def planner_agent_node(state: BusinessOperatingState) -> BusinessOperatingState:
    hypotheses = list(state.get("hypotheses") or [])
    bmc_graph = state.get("bmc_graph") or {}
    missing = bmc_graph.get("missing_blocks") or []
    kpis = state.get("kpis") or {}
    financials = state.get("financials") or {}

    if missing:
        hypotheses.append({
            "id": "bmc-fill-" + missing[0],
            "kind": "bmc",
            "statement": f"{missing[0]} is under-specified and may block execution.",
            "required_node": "bmc_topology",
            "confidence": 0.7,
        })

    retention = _safe_float(kpis.get("retention_30d"), default=math.nan)
    activation = _safe_float(kpis.get("activation_rate"), default=math.nan)
    if not math.isnan(retention) and not math.isnan(activation) and activation > retention:
        hypotheses.append({
            "id": "activation-retention-gap",
            "kind": "kpi_causal",
            "statement": "Activation is not converting into 30-day retention.",
            "required_node": "kpi_causal",
            "target_kpi": "retention_30d",
            "confidence": 0.64,
        })

    runway = _safe_float(financials.get("runway_months"), default=999.0)
    if runway < 6:
        hypotheses.append({
            "id": "runway-allocation-pressure",
            "kind": "resource_allocation",
            "statement": "Runway below six months requires budget reallocation.",
            "required_node": "resource_allocation",
            "confidence": 0.78,
        })

    return {"hypotheses": hypotheses}


def kpi_causal_node(state: BusinessOperatingState) -> BusinessOperatingState:
    if not _analysis_enabled(state, "kpi_causal"):
        return {}

    kpis = state.get("kpis") or {}
    signals = state.get("market_signals") or []
    candidates: list[dict[str, Any]] = []
    for name, value in kpis.items():
        if isinstance(value, dict):
            current = _safe_float(value.get("current"))
            target = _safe_float(value.get("target"), current)
        else:
            current = _safe_float(value)
            target = current
        gap = target - current
        if abs(gap) > 0:
            candidates.append({
                "effect": name,
                "gap": gap,
                "direction": "increase" if gap > 0 else "decrease",
                "candidate_causes": _candidate_causes(name, signals),
                "recommended_library": "DoWhy/EconML/statsmodels",
            })
    result = {"candidates": candidates, "method": "heuristic causal-prior generation"}
    return _append_result(state, "kpi_causal", result)


def financial_flow_node(state: BusinessOperatingState) -> BusinessOperatingState:
    if not _analysis_enabled(state, "financial_flow"):
        return {}

    f = state.get("financials") or {}
    cash = _safe_float(f.get("cash"))
    monthly_revenue = _safe_float(f.get("monthly_revenue"))
    monthly_cost = _safe_float(f.get("monthly_cost"))
    gross_margin = _safe_float(f.get("gross_margin"), 0.0)
    burn = monthly_cost - monthly_revenue
    runway = cash / burn if burn > 0 else math.inf
    result = {
        "cash": cash,
        "monthly_revenue": monthly_revenue,
        "monthly_cost": monthly_cost,
        "burn": burn,
        "runway_months": runway if math.isfinite(runway) else None,
        "gross_margin": gross_margin,
        "bottleneck": "cash" if burn > 0 and runway < 6 else "growth" if monthly_revenue <= 0 else "none",
        "recommended_library": "pandas/NetworkX/QuantLib",
    }
    return _append_result(state, "financial_flow", result)


def resource_allocation_node(state: BusinessOperatingState) -> BusinessOperatingState:
    if not _analysis_enabled(state, "resource_allocation"):
        return {}

    budget = _safe_float((state.get("constraints") or {}).get("budget"))
    projects = list(state.get("projects") or [])
    selected: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    total_cost = 0.0
    total_expected_value = 0.0

    ranked = sorted(
        projects,
        key=lambda p: (
            -_safe_float(p.get("expected_value")),
            _safe_float(p.get("cost")),
            p.get("id") or p.get("name") or "",
        ),
    )
    if budget <= 0:
        result = {
            "selected": selected,
            "rejected": [{
                "id": p.get("id") or p.get("name"),
                "reason": "no_budget",
            } for p in ranked],
            "total_cost": total_cost,
            "total_expected_value": total_expected_value,
            "expected_net_value": 0.0,
            "unused_budget": None,
            "method": "greedy positive-net-value fallback",
            "recommended_library": "OR-Tools/PuLP/Pyomo/Gurobi",
        }
        return _append_result(state, "resource_allocation", result)

    for p in ranked:
        cost = _safe_float(p.get("cost"))
        expected_value = _safe_float(p.get("expected_value"))
        project_id = p.get("id") or p.get("name")
        if expected_value <= cost:
            rejected.append({"id": project_id, "reason": "non_positive_expected_net_value"})
            continue
        if total_cost + cost <= budget:
            selected.append({
                "id": project_id,
                "cost": cost,
                "expected_value": expected_value,
                "expected_net_value": expected_value - cost,
            })
            total_cost += cost
            total_expected_value += expected_value
        else:
            rejected.append({"id": project_id, "reason": "budget_exceeded"})

    result = {
        "selected": selected,
        "rejected": rejected,
        "total_cost": total_cost,
        "total_expected_value": total_expected_value,
        "expected_net_value": total_expected_value - total_cost,
        "unused_budget": max(budget - total_cost, 0.0) if budget > 0 else None,
        "method": "greedy positive-net-value fallback",
        "recommended_library": "OR-Tools/PuLP/Pyomo/Gurobi",
    }
    return _append_result(state, "resource_allocation", result)


def scheduling_node(state: BusinessOperatingState) -> BusinessOperatingState:
    if not _analysis_enabled(state, "scheduling"):
        return {}

    tasks = list(state.get("tasks") or [])
    task_by_id = {str(t.get("id")): t for t in tasks if t.get("id") is not None}
    order, cycles = _topological_order(task_by_id)
    start = 0
    schedule: list[dict[str, Any]] = []
    for task_id in order:
        task = task_by_id[task_id]
        duration = max(_safe_float(task.get("duration_days"), 1.0), 0.0)
        schedule.append({"id": task_id, "start_day": start, "end_day": start + duration})
        start += duration

    result = {
        "schedule": schedule,
        "cycles": cycles,
        "makespan_days": start,
        "recommended_library": "NetworkX/OR-Tools/Prefect/Airflow",
    }
    return _append_result(state, "scheduling", result)


def scenario_simulation_node(state: BusinessOperatingState) -> BusinessOperatingState:
    if not _analysis_enabled(state, "scenario_simulation"):
        return {}

    f = state.get("financials") or {}
    revenue = _safe_float(f.get("monthly_revenue"))
    cost = _safe_float(f.get("monthly_cost"))
    scenarios = []
    for name, growth, cost_delta in [
        ("base", 0.03, 0.00),
        ("upside", 0.08, 0.03),
        ("downside", -0.03, -0.02),
    ]:
        rev = revenue
        cash_delta = 0.0
        for _month in range(12):
            rev *= 1 + growth
            cash_delta += rev - (cost * (1 + cost_delta))
        scenarios.append({"name": name, "revenue_month_12": rev, "cash_delta_12m": cash_delta})
    result = {"scenarios": scenarios, "recommended_library": "PySD/scipy/simpy"}
    return _append_result(state, "scenario_simulation", result)


def market_game_node(state: BusinessOperatingState) -> BusinessOperatingState:
    if not _analysis_enabled(state, "market_game"):
        return {}

    competitors = state.get("competitors") or []
    own_price = _safe_float((state.get("financials") or {}).get("price"))
    competitor_prices = [_safe_float(c.get("price")) for c in competitors if c.get("price") is not None]
    median_competitor = sorted(competitor_prices)[len(competitor_prices) // 2] if competitor_prices else None
    if median_competitor is None or own_price <= 0:
        posture = "unknown"
    elif own_price < median_competitor * 0.8:
        posture = "undercut"
    elif own_price > median_competitor * 1.2:
        posture = "premium"
    else:
        posture = "parity"
    result = {
        "posture": posture,
        "own_price": own_price or None,
        "median_competitor_price": median_competitor,
        "recommended_library": "OpenSpiel/Mesa/Nashpy",
    }
    return _append_result(state, "market_game", result)


def risk_constraint_node(state: BusinessOperatingState) -> BusinessOperatingState:
    risks = list(state.get("risks") or [])
    results = state.get("analysis_results") or {}

    financial = results.get("financial_flow") or {}
    runway = financial.get("runway_months")
    if runway is not None and runway < 6:
        risks.append({"id": "short-runway", "severity": "high", "summary": "Runway below six months."})

    scheduling = results.get("scheduling") or {}
    if scheduling.get("cycles"):
        risks.append({"id": "dependency-cycle", "severity": "high", "summary": "Task dependency cycle blocks execution."})

    bmc = results.get("bmc") or {}
    if len(bmc.get("missing_blocks") or []) >= 3:
        risks.append({"id": "bmc-under-specified", "severity": "medium", "summary": "Three or more BMC blocks are empty."})

    return {"risks": risks}


def synthesis_agent_node(state: BusinessOperatingState) -> BusinessOperatingState:
    results = state.get("analysis_results") or {}
    decisions = list(state.get("decisions") or [])
    actions = list(state.get("actions") or [])

    allocation = results.get("resource_allocation") or {}
    selected = allocation.get("selected") or []
    if selected:
        decisions.append({
            "id": "fund-selected-projects",
            "type": "resource_allocation",
            "recommendation": "Fund selected projects within budget.",
            "project_ids": [p["id"] for p in selected],
        })
        actions.extend({
            "kind": "project_funding",
            "project_id": p["id"],
            "cost": p["cost"],
            "requires_human_approval": True,
        } for p in selected)

    causal = results.get("kpi_causal") or {}
    for candidate in causal.get("candidates") or []:
        if abs(_safe_float(candidate.get("gap"))) > 0:
            actions.append({
                "kind": "causal_validation",
                "target_kpi": candidate["effect"],
                "tool": "DoWhy/EconML",
                "requires_human_approval": False,
            })

    if not decisions:
        decisions.append({
            "id": "continue-measurement",
            "type": "operating_cadence",
            "recommendation": "Continue measurement; no high-confidence action found.",
        })

    return {"decisions": decisions, "actions": actions}


def report_node(state: BusinessOperatingState) -> BusinessOperatingState:
    business_progress = _evaluate_business_progress(state)
    report = {
        "run_id": state.get("run_id"),
        "duration_ms": _now_ms() - int(state.get("started_at_ms") or _now_ms()),
        "summary": {
            "hypotheses": len(state.get("hypotheses") or []),
            "analyses": sorted((state.get("analysis_results") or {}).keys()),
            "decisions": len(state.get("decisions") or []),
            "actions": len(state.get("actions") or []),
            "risks": len(state.get("risks") or []),
        },
        "decisions": state.get("decisions") or [],
        "actions": state.get("actions") or [],
        "risks": state.get("risks") or [],
        "business_progress": business_progress,
        "visualization_target": "ComfyUI/Graphviz/NetworkX export node",
    }
    return {"report": report}


def _evaluate_business_progress(state: BusinessOperatingState) -> dict[str, Any]:
    results = state.get("analysis_results") or {}
    actions = state.get("actions") or []
    decisions = state.get("decisions") or []
    risks = state.get("risks") or []

    allocation = results.get("resource_allocation") or {}
    scheduling = results.get("scheduling") or {}
    causal = results.get("kpi_causal") or {}
    live_lift = _evaluate_live_kpi_lift(state)

    selected = allocation.get("selected") or []
    total_cost = _safe_float(allocation.get("total_cost"))
    expected_net_value = _safe_float(allocation.get("expected_net_value"))
    budget = _safe_float((state.get("constraints") or {}).get("budget"))

    gates = {
        "has_decision": bool(decisions),
        "has_executable_action": bool(actions),
        "execution_actions_human_gated": all(
            a.get("requires_human_approval") is True
            for a in actions
            if a.get("kind") in {"project_funding", "external_dispatch", "spend_commitment"}
        ),
        "allocation_within_budget": not selected or (budget > 0 and total_cost <= budget),
        "allocation_positive_expected_net_value": not selected or expected_net_value > 0,
        "schedule_has_no_cycles": not bool(scheduling.get("cycles")),
        "has_kpi_validation_path": bool(causal.get("candidates")) or any(
            a.get("kind") == "causal_validation" for a in actions
        ),
        "risks_are_explicit": isinstance(risks, list),
    }
    passed = [name for name, ok in gates.items() if ok]
    failed = [name for name, ok in gates.items() if not ok]
    score = round(len(passed) / max(len(gates), 1), 3)
    verification_level = (
        "live_kpi_before_after"
        if live_lift["status"] in {"passed", "failed"}
        else "deterministic_fixture"
    )
    return {
        "can_advance_business": not failed,
        "has_proven_business_lift": live_lift["status"] == "passed",
        "score": score,
        "passed_gates": passed,
        "failed_gates": failed,
        "verification_level": verification_level,
        "minimum_viable_gates": sorted(gates.keys()),
        "live_kpi_evidence": live_lift,
    }


def _evaluate_live_kpi_lift(state: BusinessOperatingState) -> dict[str, Any]:
    before = state.get("metrics_before") or {}
    after = state.get("metrics_after") or {}
    config = state.get("lift_evaluation") or {}
    if not before or not after:
        return {
            "status": "not_provided",
            "reason": "metrics_before and metrics_after are required for live KPI verification",
        }

    primary = str(config.get("primary_metric") or "mrr_total_jpy")
    min_absolute_lift = _safe_float(config.get("min_absolute_lift"), 0.0)
    min_relative_lift = _safe_float(config.get("min_relative_lift"), 0.0)
    guardrails = list(config.get("guardrail_metrics") or [])
    max_guardrail_drop = _safe_float(config.get("max_guardrail_drop"), 0.0)

    before_value = _safe_float(before.get(primary), math.nan)
    after_value = _safe_float(after.get(primary), math.nan)
    if math.isnan(before_value) or math.isnan(after_value):
        return {
            "status": "failed",
            "reason": f"primary metric {primary!r} missing or non-numeric",
            "primary_metric": primary,
        }

    absolute_lift = after_value - before_value
    relative_lift = absolute_lift / abs(before_value) if before_value else (1.0 if absolute_lift > 0 else 0.0)
    primary_passed = absolute_lift >= min_absolute_lift and relative_lift >= min_relative_lift

    guardrail_results = []
    guardrails_passed = True
    for metric in guardrails:
        before_guard = _safe_float(before.get(metric), math.nan)
        after_guard = _safe_float(after.get(metric), math.nan)
        if math.isnan(before_guard) or math.isnan(after_guard):
            guardrails_passed = False
            guardrail_results.append({
                "metric": metric,
                "status": "missing",
            })
            continue
        drop = before_guard - after_guard
        passed = drop <= max_guardrail_drop
        guardrails_passed = guardrails_passed and passed
        guardrail_results.append({
            "metric": metric,
            "before": before_guard,
            "after": after_guard,
            "drop": drop,
            "passed": passed,
        })

    status = "passed" if primary_passed and guardrails_passed else "failed"
    return {
        "status": status,
        "primary_metric": primary,
        "before": before_value,
        "after": after_value,
        "absolute_lift": absolute_lift,
        "relative_lift": round(relative_lift, 6),
        "min_absolute_lift": min_absolute_lift,
        "min_relative_lift": min_relative_lift,
        "primary_passed": primary_passed,
        "guardrails_passed": guardrails_passed,
        "guardrails": guardrail_results,
    }


def _degree_centrality(nodes: list[str], edges: list[tuple[str, str]]) -> dict[str, float]:
    if not nodes:
        return {}
    degree = {n: 0 for n in nodes}
    for s, t in edges:
        degree[s] = degree.get(s, 0) + 1
        degree[t] = degree.get(t, 0) + 1
    denom = max(len(nodes) - 1, 1)
    return {node: value / denom for node, value in degree.items()}


def _candidate_causes(kpi_name: str, signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    causes = []
    name = kpi_name.lower()
    for signal in signals:
        text = f"{signal.get('name', '')} {signal.get('summary', '')}".lower()
        overlap = sum(1 for token in name.split("_") if token and token in text)
        if overlap:
            causes.append({
                "signal": signal.get("id") or signal.get("name"),
                "confidence": min(0.5 + overlap * 0.15, 0.9),
            })
    if not causes:
        causes.append({"signal": "needs_instrumentation", "confidence": 0.3})
    return causes


def _topological_order(task_by_id: dict[str, dict[str, Any]]) -> tuple[list[str], list[str]]:
    indegree: dict[str, int] = {task_id: 0 for task_id in task_by_id}
    outgoing: dict[str, list[str]] = defaultdict(list)
    for task_id, task in task_by_id.items():
        for dep in task.get("depends_on") or []:
            dep_id = str(dep)
            if dep_id in task_by_id:
                outgoing[dep_id].append(task_id)
                indegree[task_id] += 1

    ready = [task_id for task_id, count in indegree.items() if count == 0]
    heapq.heapify(ready)
    order: list[str] = []
    while ready:
        task_id = heapq.heappop(ready)
        order.append(task_id)
        for nxt in outgoing[task_id]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                heapq.heappush(ready, nxt)

    cycles = sorted(task_id for task_id, count in indegree.items() if count > 0)
    return order, cycles


def _build() -> Any:
    sg = StateGraph(BusinessOperatingState)
    sg.add_node("intake", intake)
    sg.add_node("bmc_topology", bmc_topology_node)
    sg.add_node("planner", planner_agent_node)
    sg.add_node("kpi_causal", kpi_causal_node)
    sg.add_node("financial_flow", financial_flow_node)
    sg.add_node("resource_allocation", resource_allocation_node)
    sg.add_node("scheduling", scheduling_node)
    sg.add_node("scenario_simulation", scenario_simulation_node)
    sg.add_node("market_game", market_game_node)
    sg.add_node("risk_constraint", risk_constraint_node)
    sg.add_node("synthesis", synthesis_agent_node)
    sg.add_node("report", report_node)

    sg.add_edge(START, "intake")
    sg.add_edge("intake", "bmc_topology")
    sg.add_edge("bmc_topology", "planner")
    sg.add_edge("planner", "kpi_causal")
    sg.add_edge("kpi_causal", "financial_flow")
    sg.add_edge("financial_flow", "resource_allocation")
    sg.add_edge("resource_allocation", "scheduling")
    sg.add_edge("scheduling", "scenario_simulation")
    sg.add_edge("scenario_simulation", "market_game")
    sg.add_edge("market_game", "risk_constraint")
    sg.add_edge("risk_constraint", "synthesis")
    sg.add_edge("synthesis", "report")
    sg.add_edge("report", END)
    return sg.compile()


GRAPH = _build()
