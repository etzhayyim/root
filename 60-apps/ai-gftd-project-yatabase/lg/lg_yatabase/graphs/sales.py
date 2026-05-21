"""yatabase `sales` graph — mid/bottom-funnel orchestration.

Pipeline (LangGraph state-machine), invoked per active org_did:

    load_org_state → compute_health → decide_action → execute → wait_for_signal
                                            │
                          ┌─────────────────┼─────────────────────┐
                          ▼                 ▼                     ▼
                   do_nothing         send_onboarding        send_upgrade
                                      send_usage_recap       book_call
                                                             escalate_human

Signals consumed:
  - vertex_billing_event last 24h + 30d (api_request, storage_gb_hour, …)
  - vertex_audit_log last 7d (any 5xx → defer marketing touches)
  - vertex_email_outbox last 14d (recent touchpoints — don't double-touch)
  - vertex_billing_org_plan (current paid tier or inferred free)

Decision policy (LLM-augmented, deterministic fallback):
  - new tenant + 0 traffic     →  send_onboarding (1st touch)
  - new tenant + low traffic   →  send_usage_recap
  - low traffic + plan=free    →  do_nothing (don't pester evaluation users)
  - high traffic + plan=free   →  send_upgrade (quota approaching)
  - starter approaching cap    →  send_upgrade (recommend developer)
  - any 5xx in last 24h        →  do_nothing (wait for chikada to triage)
  - last_touch < 7d            →  do_nothing (rate-limit per-org)
  - paid + churn risk signals  →  escalate_human (sakamoto handoff)

Compliance: any outbound side-effect (email, calendar invite) lands in
vertex_email_outbox with status='queued' until a human reviewer
approves the recipient + body. Sales can only persuade; cannot ship
without sign-off.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from lg_yatabase.bmc.db import execute, fetch, fetchrow, fetchval
from lg_yatabase.templates import SalesKind, sales_touch

from . import _llm as _llm

_log = logging.getLogger(__name__)

DecisionLiteral = Literal[
    "do_nothing",
    "send_onboarding",
    "send_usage_recap",
    "send_upgrade",
    "book_call",
    "escalate_human",
]


_DECISION_TO_KIND: dict[str, SalesKind] = {
    "send_onboarding": "sales-onboarding",
    "send_usage_recap": "sales-usage-recap",
    "send_upgrade": "sales-upgrade",
    "book_call": "sales-book-call",
}


# Heuristics (constants tunable via env later)
_FREE_DAILY_CAP = 1000           # free tier cap (per CLAUDE.md)
_STARTER_DAILY_CAP = 100_000     # starter cap
_RATE_LIMIT_SECONDS = 7 * 86400  # 7 day per-org rate-limit


class _State(TypedDict, total=False):
    iteration_id: str
    started_at: int
    org_did: str
    plan: str
    signup_at: str
    tenant_name: str | None
    usage_24h: dict[str, int]
    usage_30d: dict[str, int]
    last_touch_at: str | None
    last_touch_kind: str | None
    incident_count_24h: int
    health_score: int
    decision: DecisionLiteral
    decision_reasoning: str
    decision_source: str
    touchpoint_id: str | None
    touchpoint_status: str
    next_check_at: str
    notes: str


# ── Helpers ─────────────────────────────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso_to_ts(s: str | None) -> float:
    if not s:
        return 0.0
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    except (ValueError, TypeError):
        return 0.0


# ── Nodes ───────────────────────────────────────────────────────────────


def _bootstrap(state: _State) -> _State:
    return {
        "iteration_id": uuid.uuid4().hex,
        "started_at": int(time.time() * 1000),
        "usage_24h": {},
        "usage_30d": {},
        "incident_count_24h": 0,
        "health_score": 0,
    }


async def _load_org_state(state: _State) -> _State:
    """Hit vertex_billing_org_plan + vertex_billing_event + vertex_audit_log
    + vertex_email_outbox for this org_did and populate the state shape."""
    org_did = (state.get("org_did") or "").strip()
    if not org_did:
        _log.warning("[sales.load_org_state] missing org_did — nothing to do")
        return {"plan": "free", "incident_count_24h": 0}

    now_ms = int(time.time() * 1000)
    ms_24h = now_ms - 24 * 3600 * 1000
    ms_30d = now_ms - 30 * 86400 * 1000
    ms_7d = now_ms - 7 * 86400 * 1000

    plan = "free"
    signup_at = ""
    tenant_name: str | None = None

    try:
        plan_row = await fetchrow(
            """
            SELECT plan, status, billing_period_start
              FROM vertex_billing_org_plan
             WHERE org_did = $1
             ORDER BY billing_period_start DESC
             LIMIT 1
            """,
            org_did,
        )
        if plan_row:
            plan = str(plan_row.get("plan") or "free")
            signup_at = str(plan_row.get("billing_period_start") or "")
    except Exception as e:                                       # noqa: BLE001
        _log.warning("[sales.load_org_state] plan lookup failed: %s", e)

    # Usage totals — RW pgwire bind parameterised int constants OK; LIMIT must
    # be inlined.
    usage_24h: dict[str, int] = {}
    usage_30d: dict[str, int] = {}
    try:
        rows_24h = await fetch(
            """
            SELECT metric, SUM(qty) AS qty
              FROM vertex_billing_event
             WHERE org_did = $1 AND ts_ms >= $2
             GROUP BY metric
            """,
            org_did, ms_24h,
        )
        for r in rows_24h:
            usage_24h[str(r.get("metric") or "")] = int(float(r.get("qty") or 0))
    except Exception as e:                                       # noqa: BLE001
        _log.warning("[sales.load_org_state] usage_24h failed: %s", e)

    try:
        rows_30d = await fetch(
            """
            SELECT metric, SUM(qty) AS qty
              FROM vertex_billing_event
             WHERE org_did = $1 AND ts_ms >= $2
             GROUP BY metric
            """,
            org_did, ms_30d,
        )
        for r in rows_30d:
            usage_30d[str(r.get("metric") or "")] = int(float(r.get("qty") or 0))
    except Exception as e:                                       # noqa: BLE001
        _log.warning("[sales.load_org_state] usage_30d failed: %s", e)

    incident_24h = 0
    try:
        incident_24h = int(await fetchval(
            """
            SELECT COUNT(*)
              FROM vertex_audit_log
             WHERE org_did = $1
               AND ts_ms >= $2
               AND status_code >= 500
            """,
            org_did, ms_24h,
        ) or 0)
    except Exception as e:                                       # noqa: BLE001
        _log.warning("[sales.load_org_state] incident lookup failed: %s", e)

    last_touch_at: str | None = None
    last_touch_kind: str | None = None
    try:
        # vertex_email_outbox has no org_did pointing at recipient — we
        # store the org owning the outreach via the kind+recipient_email
        # path. For now we approximate by reading the most-recent sales-*
        # row scoped by org_did='gftd' bucket; once outbox carries an
        # explicit target_org_did this becomes exact.
        touch_row = await fetchrow(
            """
            SELECT kind, scheduled_at
              FROM vertex_email_outbox
             WHERE recipient_email LIKE $1
               AND kind LIKE 'sales-%'
             ORDER BY scheduled_at DESC
             LIMIT 1
            """,
            f"%{org_did}%",
        )
        if touch_row:
            last_touch_at = str(touch_row.get("scheduled_at") or "") or None
            last_touch_kind = str(touch_row.get("kind") or "") or None
    except Exception as e:                                       # noqa: BLE001
        _log.warning("[sales.load_org_state] last_touch failed: %s", e)

    _log.info(
        "[sales.load_org_state] org=%s plan=%s api_24h=%d incidents_24h=%d last_touch=%s",
        org_did, plan, usage_24h.get("api_request", 0), incident_24h, last_touch_at,
    )

    return {
        "plan": plan,
        "signup_at": signup_at,
        "tenant_name": tenant_name,
        "usage_24h": usage_24h,
        "usage_30d": usage_30d,
        "incident_count_24h": incident_24h,
        "last_touch_at": last_touch_at,
        "last_touch_kind": last_touch_kind,
    }


def _compute_health(state: _State) -> _State:
    """Coarse 0-100 health from usage trajectory + incidents + last_touch.

    Pure function over state — no DB access.
    """
    api_24h = state.get("usage_24h", {}).get("api_request", 0)
    api_30d = state.get("usage_30d", {}).get("api_request", 0)
    daily_avg_30d = max(1, api_30d // 30)
    momentum = min(2.0, api_24h / daily_avg_30d) if api_24h > 0 else 0.0

    base = 30
    base += int(momentum * 30)  # 0-60 from momentum
    if api_24h > 0:
        base += 5
    if state.get("incident_count_24h", 0) > 0:
        base -= 25
    if state.get("plan", "free") != "free":
        base += 10
    health = max(0, min(100, base))
    return {"health_score": health}


async def _decide_action(state: _State) -> _State:
    """Pick one DecisionLiteral. Deterministic policy with LLM augmentation."""
    deterministic = _deterministic_policy(state)

    decision, reasoning, source = _llm.decide_sales_action(
        dict(state), default=deterministic["decision"],
    )
    # LLM may agree with deterministic policy — that's fine. If it
    # disagrees, accept its choice but still record the policy's reason
    # for the audit trail.
    if source == "llm" and decision != deterministic["decision"]:
        reasoning = f"{reasoning} (deterministic policy preferred: {deterministic['decision']})"
    elif source != "llm":
        reasoning = deterministic["reasoning"]
    return {
        "decision": decision,  # type: ignore[typeddict-item]
        "decision_reasoning": reasoning,
        "decision_source": source,
    }


def _deterministic_policy(state: _State) -> dict[str, str]:
    """Honest policy table mirroring the docstring."""
    incident = state.get("incident_count_24h", 0)
    if incident > 0:
        return {
            "decision": "do_nothing",
            "reasoning": "incident in last 24h — defer to chikada triage",
        }

    last_touch = state.get("last_touch_at")
    if last_touch and (time.time() - _iso_to_ts(last_touch)) < _RATE_LIMIT_SECONDS:
        return {
            "decision": "do_nothing",
            "reasoning": "rate-limit: last sales touch <7d ago",
        }

    api_24h = state.get("usage_24h", {}).get("api_request", 0)
    plan = state.get("plan", "free")

    if api_24h == 0 and not last_touch:
        return {
            "decision": "send_onboarding",
            "reasoning": "new tenant, zero traffic — first touch",
        }
    if api_24h > 0 and api_24h < 50 and plan == "free":
        return {
            "decision": "send_usage_recap",
            "reasoning": "low-but-nonzero traffic — highlight what they tried",
        }
    if plan == "free" and api_24h > int(_FREE_DAILY_CAP * 0.8):
        return {
            "decision": "send_upgrade",
            "reasoning": f"free plan at >{int(_FREE_DAILY_CAP * 0.8)}/day — approaching cap",
        }
    if plan == "starter" and api_24h > int(_STARTER_DAILY_CAP * 0.8):
        return {
            "decision": "send_upgrade",
            "reasoning": "starter plan approaching cap — recommend developer tier",
        }
    if plan in ("starter", "developer", "enterprise") and api_24h == 0:
        # Paid + silent → potential churn signal.
        return {
            "decision": "escalate_human",
            "reasoning": "paid plan with 0 traffic in 24h — possible churn risk",
        }
    return {
        "decision": "do_nothing",
        "reasoning": "no qualifying signal",
    }


async def _execute_action(state: _State) -> _State:
    """Dispatch on state['decision']. Each branch (except do_nothing /
    escalate_human) writes a vertex_email_outbox row with status='queued'
    so a human can flip status='approved' before send."""
    decision = state.get("decision", "do_nothing")
    org_did = (state.get("org_did") or "").strip() or "unknown"
    iteration_id = state.get("iteration_id", "")
    now = _now_iso()

    if decision == "do_nothing":
        return {"touchpoint_status": "skipped", "notes": state.get("decision_reasoning", "")}
    if decision == "escalate_human":
        # No outbox row — instead emit an audit signal the operator can
        # subscribe to. Cheapest path: leave a marker in the outbox with
        # an explicit escalation kind so existing UIs pick it up.
        outbox_id = f"sales:{iteration_id}:{org_did}:escalate"
        try:
            await execute(
                """
                INSERT INTO vertex_email_outbox (
                    vertex_id, org_did, recipient_email, recipient_name,
                    subject, body_text, body_html, kind, status,
                    scheduled_at, sent_at, retry_count, last_error, created_at
                ) VALUES (
                    $1, $2, '', '', $3, $4, '',
                    'sales-escalate-human', 'queued-no-recipient',
                    $5, '', 0, '', $5
                )
                """,
                outbox_id[:400], org_did[:200],
                f"sales: escalate {org_did}",
                f"reason: {state.get('decision_reasoning', '')}",
                now,
            )
            return {
                "touchpoint_id": outbox_id,
                "touchpoint_status": "queued-escalation",
                "notes": f"escalation marker written; reviewer pages sakamoto.",
            }
        except Exception as e:                                       # noqa: BLE001
            _log.warning("[sales.execute_action] escalate write failed: %s", e)
            return {"touchpoint_status": "error", "notes": f"escalate write failed: {e}"}

    kind = _DECISION_TO_KIND.get(decision, "sales-onboarding")
    body = sales_touch(
        kind,
        org_did,
        tenant_name=state.get("tenant_name"),
        metric_24h=state.get("usage_24h", {}),
    )
    outbox_id = f"sales:{iteration_id}:{org_did}:{decision}"
    try:
        await execute(
            """
            INSERT INTO vertex_email_outbox (
                vertex_id, org_did, recipient_email, recipient_name,
                subject, body_text, body_html, kind, status,
                scheduled_at, sent_at, retry_count, last_error, created_at
            ) VALUES (
                $1, $2, '', '', $3, $4, $5,
                $6, 'queued-no-recipient',
                $7, '', 0, '', $7
            )
            """,
            outbox_id[:400], org_did[:200],
            body.subject[:512], body.body_text[:32768], body.body_html[:32768],
            kind, now,
        )
    except Exception as e:                                       # noqa: BLE001
        _log.warning("[sales.execute_action] insert failed: %s", e)
        return {"touchpoint_status": "error", "notes": f"insert failed: {e}"}

    return {
        "touchpoint_id": outbox_id,
        "touchpoint_status": "queued-no-recipient",
        "notes": f"kind={kind} (reviewer fills recipient + approves before send)",
    }


def _wait_for_signal(state: _State) -> _State:
    """LangGraph interrupt point — sets the next-check timestamp.

    Real interrupt semantics will land when LangGraph checkpointer
    integration covers org_did-keyed resumption; today the cron fires
    hourly and re-reads org state from RW, so we just advertise the
    next check time.
    """
    next_check = time.strftime(
        "%Y-%m-%dT%H:%M:%SZ",
        time.gmtime(time.time() + 3600),
    )
    return {"next_check_at": next_check}


# ── Graph wiring ────────────────────────────────────────────────────────

_g: StateGraph = StateGraph(_State)
_g.add_node("bootstrap", _bootstrap)
_g.add_node("load_org_state", _load_org_state)
_g.add_node("compute_health", _compute_health)
_g.add_node("decide_action", _decide_action)
_g.add_node("execute_action", _execute_action)
_g.add_node("wait_for_signal", _wait_for_signal)

_g.add_edge(START, "bootstrap")
_g.add_edge("bootstrap", "load_org_state")
_g.add_edge("load_org_state", "compute_health")
_g.add_edge("compute_health", "decide_action")
_g.add_edge("decide_action", "execute_action")
_g.add_edge("execute_action", "wait_for_signal")
_g.add_edge("wait_for_signal", END)

GRAPH = _g.compile()
