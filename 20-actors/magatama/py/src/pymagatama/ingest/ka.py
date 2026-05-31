"""KA executive dashboard handlers for BPMN + Zeebe."""

from __future__ import annotations

from typing import Any

from pymagatama.db_sync import sync_cursor

NS = "app.etzhayyim.apps.ka"
ACTOR = "did:web:ka.etzhayyim.com"

QUERIES = {
    "entities": "SELECT entity_code, legal_name, status, notes FROM vertex_business_entity ORDER BY entity_code",
    "goals": "SELECT goal_code, display_name, goal_type, status, attainment_bps, target_date, target_value_jpy FROM vertex_goal ORDER BY attainment_bps DESC",
    "actions": "SELECT action_code, display_name, status, phase, topo_level, priority, effort_days, confidence_bps FROM vertex_action ORDER BY topo_level ASC, priority DESC",
    "revenue": "SELECT stream_code, display_name, status, current_mrr_jpy, target_mrr_jpy, gross_margin_bps, entity_id, notes FROM vertex_revenue_stream ORDER BY target_mrr_jpy DESC",
    "burn": "SELECT center_code, display_name, category, monthly_burn_jpy, reducible_bps, entity_id, notes FROM vertex_cost_center ORDER BY monthly_burn_jpy DESC",
    "risks": "SELECT risk_code, display_name, risk_type, severity, probability_bps, impact_jpy, expected_loss_jpy, status FROM vertex_risk WHERE status IN ('open','mitigating') ORDER BY expected_loss_jpy DESC",
    "cases": "SELECT case_code, display_name, case_type, status, counterparty, estimated_impact_jpy, document_count, last_activity_at FROM vertex_business_case WHERE status != 'closed' ORDER BY estimated_impact_jpy DESC",
    "kpi": "SELECT kpi_code, display_name, unit, direction, current_value, target_value, threshold_red, threshold_green, measured_at FROM vertex_kpi ORDER BY kpi_code",
    "projects": "SELECT bc.case_code, bc.display_name, COUNT(ip.src_vid) AS doc_count FROM vertex_business_case bc LEFT JOIN edge_in_project ip ON ip.dst_vid = bc.vertex_id WHERE bc.case_code LIKE 'P%' GROUP BY bc.case_code, bc.display_name ORDER BY doc_count DESC",
    "infra": "SELECT capability_code, display_name, capability_type, status, deployed_at FROM vertex_infra_capability ORDER BY status DESC, capability_code",
    "milestones": "SELECT milestone_code, display_name, target_date, actual_date, status FROM vertex_milestone ORDER BY target_date",
    "snapshots": "SELECT snapshot_at, total_documents, monthly_revenue_jpy, monthly_burn_jpy, net_margin_jpy, open_risks, open_cases FROM vertex_strategy_snapshot ORDER BY snapshot_at DESC LIMIT 5",
    "deps": "SELECT edge_id, src_vid, dst_vid, dep_type FROM edge_depends_on WHERE src_vid LIKE 'action:%' ORDER BY src_vid",
    "achieves": "SELECT src_vid, dst_vid, contribution_bps, confidence_bps FROM edge_achieves",
    "inbox_health": "SELECT total_30d, unread_30d, noise_30d, signal_30d FROM mv_inbox_health LIMIT 1",
    "dept_signals": "SELECT dept_code, signal_class, email_count, event_count, total_count FROM mv_kyber_dept_signals ORDER BY total_count DESC",
    "blob_stats": "SELECT row_count, dedup_hits, (logical_bytes/1024/1024)::BIGINT AS logical_mb, (physical_bytes/1024/1024)::BIGINT AS physical_mb FROM mv_blob_dedup_stats LIMIT 1",
}


def _fetch_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with sync_cursor() as cur:
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in (cur.fetchall() or [])]


def _query(name: str) -> list[dict[str, Any]]:
    return _fetch_all(QUERIES[name])


def get_dashboard(**_: Any) -> dict[str, Any]:
    return {
        "entities": _query("entities"),
        "goals": _query("goals"),
        "kpis": _query("kpi"),
        "revenue": _query("revenue"),
        "burn": _query("burn"),
        "risks": _query("risks"),
        "actions": _query("actions"),
        "cases": _query("cases"),
        "infra": _query("infra"),
    }


def get_goals(**_: Any) -> dict[str, Any]:
    return {"rows": _query("goals")}


def get_actions(**_: Any) -> dict[str, Any]:
    return {"rows": _query("actions")}


def get_revenue(**_: Any) -> dict[str, Any]:
    return {"rows": _query("revenue")}


def get_burn(**_: Any) -> dict[str, Any]:
    return {"rows": _query("burn")}


def get_risks(**_: Any) -> dict[str, Any]:
    return {"rows": _query("risks")}


def get_cases(**_: Any) -> dict[str, Any]:
    return {"rows": _query("cases")}


def get_kpi(**_: Any) -> dict[str, Any]:
    return {"rows": _query("kpi")}


def get_projects(**_: Any) -> dict[str, Any]:
    return {"rows": _query("projects")}


def get_infra(**_: Any) -> dict[str, Any]:
    return {"rows": _query("infra")}


def get_milestones(**_: Any) -> dict[str, Any]:
    return {"rows": _query("milestones")}


def get_snapshots(**_: Any) -> dict[str, Any]:
    return {"rows": _query("snapshots")}


def get_topo(**_: Any) -> dict[str, Any]:
    return {
        "goals": _query("goals"),
        "actions": _query("actions"),
        "deps": _query("deps"),
        "achieves": _query("achieves"),
        "infra": _query("infra"),
    }


def get_inbox(**_: Any) -> dict[str, Any]:
    health = _query("inbox_health")
    blob = _query("blob_stats")
    return {
        "email": health[0] if health else {},
        "dept_signals": _query("dept_signals"),
        "blob": blob[0] if blob else {},
    }
