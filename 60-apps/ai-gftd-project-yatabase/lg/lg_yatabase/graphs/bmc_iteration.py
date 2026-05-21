"""yatabase `bmc_iteration` graph — lean Build-Measure-Learn loop.

Runs inside the lg-yatabase Granian pod (mitama-yata-pool). The pod
owns the only writer for `vertex_bmc_*` — yatabase CF Worker is a
forwarder. State machine:

    bootstrap → load_bmc_state → pick_hypothesis → measure → evaluate
                                                              ↓
                                                            decide
                                                              ↓
                                                          update_bmc → END

Hypothesis status transitions are append-only events to
`vertex_bmc_hypothesis_event` (root CLAUDE.md §"Record-log semantics").

Measurement dispatchers (see metric_query prefix):

    sql:vertex_signup_count_window[:Nd]
    sql:vertex_billing_event_metric_sum:{metric}:{Nd|Nh}
    sql:vertex_lead_count_by_status:{status}
    sql:vertex_lead_count_by_source:{source}
    sql:vertex_org_plan_count_by_tier:{tier}
    sql:vertex_audit_log_referrer_funnel:{from_path}:{to_path}
    external:stripe_subscriptions[:filter]

deai.etzhayyim.com dispatchers:
    sql:vertex_deai_session_completion_rate[:Nd]
    sql:vertex_deai_retention_7d
    sql:vertex_deai_match_resonance_avg[:Nd]
    sql:vertex_deai_assessment_count[:Nd]
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Literal, TypedDict

import httpx
from langgraph.graph import END, START, StateGraph

from lg_yatabase.bmc import repository
from lg_yatabase.bmc.db import fetch as pg_fetch, fetchval as pg_fetchval

_log = logging.getLogger(__name__)

DecisionLiteral = Literal["persevere", "pivot", "kill", "extend"]


class _State(TypedDict, total=False):
    # Inputs
    org_did: str
    actor_did: str
    trigger: str
    dry_run: bool
    forced_hypothesis_slug: str

    # Identity
    iteration_id: str
    started_at_iso: str
    started_at_ms: int

    # BMC head
    bmc_version_in: int
    canvas: dict[str, Any]

    # Picked hypothesis
    hyp_slug: str
    hyp_block: str
    hyp_statement: str
    hyp_metric: str
    hyp_metric_query: str
    hyp_threshold: float
    hyp_baseline: float
    hyp_deadline_iso: str
    hyp_min_sample: int
    hyp_auto_apply_pivot: bool
    iteration_no: int

    # Measurement
    measured_value: float
    sample_size: int
    measurement_source: str
    measurement_error: str
    measurement_window_start_ms: int
    measurement_window_end_ms: int
    measurement_raw: str
    measurement_latency_ms: int

    # Evaluation
    passed: bool
    deadline_reached: bool
    min_sample_reached: bool

    # Decision
    decision: DecisionLiteral
    decision_rationale: str
    authored_by: str
    proposed_block_edits: dict[str, Any]
    canvas_after_edits: dict[str, Any]

    # Outputs
    bmc_version_out: int
    iteration_vertex_id: str
    decision_vertex_id: str
    metric_sample_vertex_id: str
    state_vertex_id: str
    notes: str
    idle: bool
    picked_out: dict[str, Any] | None
    measurement_out: dict[str, Any] | None
    evaluation_out: dict[str, Any] | None
    decision_out: dict[str, Any] | None


# ── Helpers ────────────────────────────────────────────────────────────


_WINDOW_RE = re.compile(r"^(\d+)([smhd])$")


def _parse_window_ms(s: str) -> int:
    m = _WINDOW_RE.match(s or "")
    if not m:
        return 30 * 86400 * 1000
    n = int(m.group(1))
    unit = m.group(2)
    return n * {"s": 1000, "m": 60_000, "h": 3_600_000, "d": 86_400_000}[unit]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Nodes ──────────────────────────────────────────────────────────────


async def _bootstrap(state: _State) -> _State:
    return {
        "iteration_id": uuid.uuid4().hex,
        "started_at_iso": _now_iso(),
        "started_at_ms": int(time.time() * 1000),
        "authored_by": "agent:lg-bmc",
        "idle": False,
        "passed": False,
        "deadline_reached": False,
        "min_sample_reached": False,
        "org_did": state.get("org_did") or "anon",
        "actor_did": state.get("actor_did") or "agent:lg-bmc",
    }


async def _load_bmc_state(state: _State) -> _State:
    org = state["org_did"]
    head = await repository.get_head(org)
    if head is None:
        return {"bmc_version_in": 0, "canvas": {}}
    try:
        canvas = json.loads(head["canvas_json"])
    except Exception:
        canvas = {}
    return {"bmc_version_in": int(head["version"]), "canvas": canvas}


async def _pick_hypothesis(state: _State) -> _State:
    org = state["org_did"]
    forced = state.get("forced_hypothesis_slug")
    if forced:
        rows, _ = await repository.list_hypotheses(
            org_did=org, status=None, block=None, offset=0, limit=1,
        )
        match = [r for r in rows if r["slug"] == forced]
        h = match[0] if match else None
    else:
        h = await repository.pick_next_hypothesis(org)
    if h is None:
        return {"idle": True, "notes": "no active hypothesis; loop idle"}
    iter_no = await repository.next_iteration_no(h["slug"], org)
    return {
        "idle": False,
        "hyp_slug": h["slug"],
        "hyp_block": h["block"],
        "hyp_statement": h["statement"],
        "hyp_metric": h["metric"],
        "hyp_metric_query": h["metric_query"],
        "hyp_threshold": float(h["threshold"]),
        "hyp_baseline": float(h["baseline"]),
        "hyp_deadline_iso": h["deadline_iso"],
        "hyp_min_sample": int(h["min_sample"]),
        "hyp_auto_apply_pivot": bool(h.get("auto_apply_pivot")),
        "iteration_no": iter_no,
        "picked_out": {
            "slug": h["slug"],
            "block": h["block"],
            "iterationNo": iter_no,
            "threshold": repr(float(h["threshold"])),
        },
    }


async def _measure(state: _State) -> _State:
    if state.get("idle"):
        return {}
    mq = state.get("hyp_metric_query", "")
    prefix = mq.split(":", 1)[0] if mq else ""
    t0 = time.time()
    if prefix == "sql":
        out = await _measure_sql(mq)
    elif prefix == "external" and mq.startswith("external:stripe"):
        out = await _measure_stripe(mq)
    else:
        out = {"value": 0.0, "sample": 0, "source": "unknown-prefix",
               "error": f"unsupported metric_query prefix: {prefix or '(empty)'}",
               "window_start_ms": 0, "window_end_ms": 0, "raw": ""}
    latency = int((time.time() - t0) * 1000)
    return {
        "measured_value": float(out["value"]),
        "sample_size": int(out["sample"]),
        "measurement_source": str(out["source"]),
        "measurement_error": str(out.get("error") or ""),
        "measurement_window_start_ms": int(out.get("window_start_ms") or 0),
        "measurement_window_end_ms": int(out.get("window_end_ms") or 0),
        "measurement_raw": str(out.get("raw") or "")[:4096],
        "measurement_latency_ms": latency,
        "measurement_out": {
            "value": repr(float(out["value"])),
            "sample": int(out["sample"]),
            "source": str(out["source"]),
            "error": str(out.get("error") or ""),
        },
    }


async def _measure_sql(metric_query: str) -> dict[str, Any]:
    parts = metric_query.split(":")
    dispatcher = parts[1] if len(parts) > 1 else ""
    arg1 = parts[2] if len(parts) > 2 else ""
    arg2 = parts[3] if len(parts) > 3 else ""
    now_ms = int(time.time() * 1000)
    window_ms = _parse_window_ms(arg2 or arg1 or "30d")
    since_ms = now_ms - window_ms
    since_iso = datetime.fromtimestamp(since_ms / 1000.0, tz=timezone.utc).isoformat()

    try:
        if dispatcher == "vertex_signup_count_window":
            c = await pg_fetchval(
                """
                SELECT COUNT(*) FROM vertex_api_key
                WHERE owner_did LIKE 'did:web:t-%.yata-tenant.etzhayyim.com'
                  AND created_at >= $1
                """,
                since_iso,
            )
            return {"value": float(c or 0), "sample": int(c or 0),
                    "source": f"vertex_api_key.count_since={since_iso}",
                    "window_start_ms": since_ms, "window_end_ms": now_ms, "raw": ""}
        if dispatcher == "vertex_billing_event_metric_sum":
            metric = arg1 or "api_request"
            row = await pg_fetch(
                """
                SELECT COALESCE(SUM(qty), 0) AS s, COUNT(*) AS c
                FROM vertex_billing_event
                WHERE metric = $1 AND ts_ms >= $2
                """,
                metric, since_ms,
            )
            r = row[0] if row else {"s": 0, "c": 0}
            return {"value": float(r["s"] or 0), "sample": int(r["c"] or 0),
                    "source": f"vertex_billing_event.sum metric={metric} since={since_iso}",
                    "window_start_ms": since_ms, "window_end_ms": now_ms, "raw": ""}
        if dispatcher == "vertex_lead_count_by_status":
            status = arg1 or "new"
            c = await pg_fetchval(
                "SELECT COUNT(*) FROM vertex_lead WHERE outreach_status = $1", status,
            )
            return {"value": float(c or 0), "sample": int(c or 0),
                    "source": f"vertex_lead.count status={status}",
                    "window_start_ms": 0, "window_end_ms": now_ms, "raw": ""}
        if dispatcher == "vertex_lead_count_by_source":
            src = arg1 or "hn-scraper"
            c = await pg_fetchval(
                "SELECT COUNT(*) FROM vertex_lead WHERE source = $1", src,
            )
            return {"value": float(c or 0), "sample": int(c or 0),
                    "source": f"vertex_lead.count source={src}",
                    "window_start_ms": 0, "window_end_ms": now_ms, "raw": ""}
        if dispatcher == "vertex_org_plan_count_by_tier":
            tier = arg1 or "starter"
            c = await pg_fetchval(
                "SELECT COUNT(*) FROM vertex_org_plan WHERE tier = $1 AND status = 'active'",
                tier,
            )
            return {"value": float(c or 0), "sample": int(c or 0),
                    "source": f"vertex_org_plan.count tier={tier}",
                    "window_start_ms": 0, "window_end_ms": now_ms, "raw": ""}
        if dispatcher == "vertex_audit_log_referrer_funnel":
            from_path = arg1 or "/comparison"
            to_path = arg2 or "/quickstart"
            since30 = now_ms - 30 * 86_400_000
            rows = await pg_fetch(
                """
                SELECT
                  SUM(CASE WHEN path = $1 THEN 1 ELSE 0 END) AS from_n,
                  SUM(CASE WHEN path = $2 THEN 1 ELSE 0 END) AS to_n
                FROM vertex_audit_log
                WHERE ts_ms >= $3
                """,
                from_path, to_path, since30,
            )
            r = rows[0] if rows else {"from_n": 0, "to_n": 0}
            from_n = float(r["from_n"] or 0)
            to_n = float(r["to_n"] or 0)
            ratio = to_n / from_n if from_n > 0 else 0.0
            return {"value": ratio, "sample": int(from_n),
                    "source": f"audit_log {from_path}->{to_path} 30d",
                    "window_start_ms": since30, "window_end_ms": now_ms, "raw": ""}
        # ── deai.etzhayyim.com dispatchers ───────────────────────────────────
        # metric_query forms:
        #   sql:vertex_deai_session_completion_rate[:Nd]
        #   sql:vertex_deai_retention_7d
        #   sql:vertex_deai_match_resonance_avg[:Nd]
        #   sql:vertex_deai_assessment_count[:Nd]
        if dispatcher == "vertex_deai_session_completion_rate":
            # sessions that hit SESSION_SIZE responses / all sessions started
            # proxy for "complete": >= 20 responses recorded
            rows = await pg_fetch(
                """
                SELECT
                  COUNT(DISTINCT s.session_id) AS started,
                  COUNT(DISTINCT CASE WHEN r.resp_count >= 20
                                      THEN s.session_id END) AS completed
                FROM vertex_deai_session s
                LEFT JOIN (
                  SELECT session_id, COUNT(*) AS resp_count
                  FROM vertex_deai_response
                  GROUP BY session_id
                ) r ON r.session_id = s.session_id
                WHERE s.started_at >= $1
                """,
                since_iso,
            )
            row = rows[0] if rows else {"started": 0, "completed": 0}
            started = float(row["started"] or 0)
            completed = float(row["completed"] or 0)
            rate = completed / started if started > 0 else 0.0
            return {"value": rate, "sample": int(started),
                    "source": f"vertex_deai_session.completion_rate since={since_iso}",
                    "window_start_ms": since_ms, "window_end_ms": now_ms, "raw": ""}
        if dispatcher == "vertex_deai_retention_7d":
            # users with a session in the last 7d who also had one 7-14d ago
            now_ms_local = int(time.time() * 1000)
            w7_start = datetime.fromtimestamp((now_ms_local - 7 * 86_400_000) / 1000.0, tz=timezone.utc).isoformat()
            w14_start = datetime.fromtimestamp((now_ms_local - 14 * 86_400_000) / 1000.0, tz=timezone.utc).isoformat()
            prev_users = await pg_fetchval(
                """
                SELECT COUNT(DISTINCT actor_did)
                FROM vertex_deai_session
                WHERE started_at >= $1 AND started_at < $2
                """,
                w14_start, w7_start,
            )
            retained = await pg_fetchval(
                """
                SELECT COUNT(DISTINCT a.actor_did)
                FROM vertex_deai_session a
                JOIN vertex_deai_session b ON b.actor_did = a.actor_did
                  AND b.started_at >= $1 AND b.started_at < $2
                WHERE a.started_at >= $2
                """,
                w14_start, w7_start,
            )
            n = float(prev_users or 0)
            rate = float(retained or 0) / n if n > 0 else 0.0
            return {"value": rate, "sample": int(n),
                    "source": "vertex_deai_session.retention_7d",
                    "window_start_ms": now_ms_local - 14 * 86_400_000,
                    "window_end_ms": now_ms_local, "raw": ""}
        if dispatcher == "vertex_deai_match_resonance_avg":
            rows = await pg_fetch(
                """
                SELECT AVG(resonance_score) AS avg_score, COUNT(*) AS n
                FROM vertex_deai_match
                WHERE matched_at >= $1
                """,
                since_iso,
            )
            row = rows[0] if rows else {"avg_score": 0, "n": 0}
            return {"value": float(row["avg_score"] or 0), "sample": int(row["n"] or 0),
                    "source": f"vertex_deai_match.resonance_avg since={since_iso}",
                    "window_start_ms": since_ms, "window_end_ms": now_ms, "raw": ""}
        if dispatcher == "vertex_deai_assessment_count":
            c = await pg_fetchval(
                """
                SELECT COUNT(DISTINCT s.session_id)
                FROM vertex_deai_session s
                JOIN (
                  SELECT session_id FROM vertex_deai_response
                  GROUP BY session_id HAVING COUNT(*) >= 20
                ) r ON r.session_id = s.session_id
                WHERE s.started_at >= $1
                """,
                since_iso,
            )
            return {"value": float(c or 0), "sample": int(c or 0),
                    "source": f"vertex_deai_session.completed_count since={since_iso}",
                    "window_start_ms": since_ms, "window_end_ms": now_ms, "raw": ""}
    except Exception as e:
        _log.exception("[bmc.measure_sql] dispatcher=%s failed", dispatcher)
        return {"value": 0.0, "sample": 0, "source": "sql-error",
                "error": str(e)[:200],
                "window_start_ms": since_ms, "window_end_ms": now_ms, "raw": ""}
    return {"value": 0.0, "sample": 0, "source": "unknown-dispatcher",
            "error": f"unknown sql dispatcher: {dispatcher!r}",
            "window_start_ms": since_ms, "window_end_ms": now_ms, "raw": ""}


async def _measure_stripe(metric_query: str) -> dict[str, Any]:
    key = os.environ.get("STRIPE_SECRET_KEY")
    if not key:
        return {"value": 0.0, "sample": 0, "source": "stripe-key-missing",
                "error": "STRIPE_SECRET_KEY not set",
                "window_start_ms": 0, "window_end_ms": int(time.time() * 1000), "raw": ""}
    parts = metric_query.split(":")
    filt = parts[2] if len(parts) > 2 else "active"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(
                "https://api.stripe.com/v1/subscriptions",
                params={"limit": 100, "status": filt},
                headers={"authorization": f"Bearer {key}"},
            )
        if r.status_code != 200:
            return {"value": 0.0, "sample": 0, "source": "stripe-http-error",
                    "error": f"HTTP {r.status_code}",
                    "window_start_ms": 0, "window_end_ms": int(time.time() * 1000),
                    "raw": r.text[:512]}
        data = r.json()
        items = data.get("data", []) or []
        return {"value": float(len(items)), "sample": len(items),
                "source": f"stripe subscriptions(status={filt})",
                "window_start_ms": 0, "window_end_ms": int(time.time() * 1000),
                "raw": json.dumps({"count": len(items), "has_more": data.get("has_more", False)})[:512]}
    except Exception as e:
        _log.exception("[bmc.measure_stripe] failed")
        return {"value": 0.0, "sample": 0, "source": "stripe-throw",
                "error": str(e)[:200],
                "window_start_ms": 0, "window_end_ms": int(time.time() * 1000), "raw": ""}


def _evaluate(state: _State) -> _State:
    if state.get("idle"):
        return {}
    threshold = float(state.get("hyp_threshold", 0.0))
    measured = float(state.get("measured_value", 0.0))
    deadline_iso = state.get("hyp_deadline_iso", "")
    min_sample = int(state.get("hyp_min_sample", 0))
    sample = int(state.get("sample_size", 0))
    passed = measured >= threshold
    deadline_reached = False
    if deadline_iso:
        try:
            dl = datetime.fromisoformat(deadline_iso.replace("Z", "+00:00"))
            deadline_reached = datetime.now(tz=timezone.utc) >= dl
        except Exception:
            pass
    min_sample_reached = sample >= min_sample
    return {
        "passed": passed,
        "deadline_reached": deadline_reached,
        "min_sample_reached": min_sample_reached,
        "evaluation_out": {
            "passed": passed,
            "deadlineReached": deadline_reached,
            "minSampleReached": min_sample_reached,
        },
    }


def _decide_deterministic(state: _State) -> tuple[DecisionLiteral, str]:
    passed = bool(state.get("passed"))
    deadline = bool(state.get("deadline_reached"))
    min_sample = bool(state.get("min_sample_reached"))
    measured = state.get("measured_value", 0)
    threshold = state.get("hyp_threshold", 0)
    sample = state.get("sample_size", 0)
    min_n = state.get("hyp_min_sample", 0)
    iter_no = state.get("iteration_no", 1)
    if passed and min_sample:
        return "persevere", (
            f"measured={measured} >= threshold={threshold} with "
            f"sample={sample} (>= min {min_n}). Iteration #{iter_no} — promote BMC."
        )
    if not passed and deadline:
        action: DecisionLiteral = "kill" if iter_no >= 3 else "pivot"
        return action, (
            f"deadline reached; measured={measured} < threshold={threshold} "
            f"after {iter_no} iteration(s). "
            + ("Recommend kill — hypothesis exhausted." if action == "kill"
               else "Recommend pivot — propose BMC block edit.")
        )
    if not min_sample:
        return "extend", f"sample={sample} < min {min_n}; not enough signal yet."
    return "extend", (
        f"measured={measured} < threshold={threshold} but deadline not "
        f"reached — extending iteration window."
    )


async def _call_murakumo(system: str, user: str, model: str) -> str | None:
    """LLM call via Murakumo fleet (gemma-4-e4b-it). Returns content or None."""
    base = os.environ.get("MURAKUMO_BASE_URL", "https://murakumo.etzhayyim.com")
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Health check first — skip if fleet offline.
            try:
                meta = await client.get(f"{base}/_app/meta", timeout=5.0)
                meta_json = meta.json() if meta.status_code == 200 else {}
                health = (meta_json.get("fleet") or {}).get("healthPct", -1)
                if health == 0:
                    _log.warning("[bmc.llm.murakumo] fleet offline (healthPct=0)")
                    return None
            except Exception:
                pass
            r = await client.post(
                f"{base}/api/openai/v1/chat/completions",
                headers={"content-type": "application/json", "x-magatama-verified": "true"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "max_tokens": 400,
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                },
            )
        if r.status_code != 200:
            _log.warning("[bmc.llm.murakumo] HTTP %d", r.status_code)
            return None
        content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        return re.sub(r"<think>[\s\S]*?</think>", "", content).strip()
    except Exception as e:
        _log.warning("[bmc.llm.murakumo] threw: %s", e)
        return None


async def _call_openrouter(system: str, user: str, model: str) -> str | None:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        return None
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "authorization": f"Bearer {key}",
                    "content-type": "application/json",
                    "http-referer": "https://yatabase.etzhayyim.com",
                    "x-title": "lg-yatabase BMC iteration agent",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "max_tokens": 400,
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                },
            )
        if r.status_code != 200:
            _log.warning("[bmc.llm.openrouter] HTTP %d", r.status_code)
            return None
        return r.json().get("choices", [{}])[0].get("message", {}).get("content", "") or None
    except Exception as e:
        _log.warning("[bmc.llm.openrouter] threw: %s", e)
        return None


async def _decide(state: _State) -> _State:
    if state.get("idle"):
        return {}
    action, rationale = _decide_deterministic(state)
    authored_by = "agent:lg-bmc"
    proposed: dict[str, Any] = {}

    system = (
        "You are the resident BMC iteration agent for yatabase.etzhayyim.com.\n"
        "Return a SINGLE JSON object: { action, rationale, proposed_block_edits? }.\n"
        "action ∈ {persevere, pivot, kill, extend}. action=persevere when measured>=threshold AND min_sample reached.\n"
        "action=kill when iteration_no>=3 and consistently failing. action=pivot ONLY when deadline reached AND measured<threshold AND iteration_no<3. On pivot, include proposed_block_edits with concrete add_bullets (≤3, ≤200 chars each).\n"
        "Cite the measured number and threshold. Prefer the deterministic_hint when unsure. Output ONLY JSON."
    )
    user = json.dumps({
        "hypothesis": {
            "slug": state.get("hyp_slug"),
            "block": state.get("hyp_block"),
            "statement": state.get("hyp_statement"),
            "threshold": state.get("hyp_threshold"),
            "min_sample": state.get("hyp_min_sample"),
            "deadline_iso": state.get("hyp_deadline_iso"),
        },
        "measurement": {
            "value": state.get("measured_value"),
            "sample": state.get("sample_size"),
            "source": state.get("measurement_source"),
            "error": state.get("measurement_error"),
        },
        "flags": {
            "passed": state.get("passed"),
            "deadline_reached": state.get("deadline_reached"),
            "min_sample_reached": state.get("min_sample_reached"),
            "iteration_no": state.get("iteration_no"),
        },
        "deterministic_hint": {"action": action, "rationale": rationale},
        "bmc_block_keys": [
            "customerSegments", "valuePropositions", "channels",
            "customerRelationships", "revenueStreams", "keyResources",
            "keyActivities", "keyPartnerships", "costStructure",
        ],
        "current_block_bullets": (state.get("canvas") or {}).get(state.get("hyp_block", ""), {}).get("bullets", []),
    }, ensure_ascii=False)

    model_mu = os.environ.get("YATA_LLM_MODEL", "gemma-4-e4b-it")
    model_or = os.environ.get("YATA_LLM_MODEL", "anthropic/claude-haiku-4")
    raw: str | None = None
    provider = ""
    for provider, fetch in (("murakumo", lambda: _call_murakumo(system, user, model_mu)),
                            ("openrouter", lambda: _call_openrouter(system, user, model_or))):
        raw = await fetch()
        if raw:
            break
    if raw:
        stripped = re.sub(r"^```(?:json)?\s*|\s*```\s*$", "", raw.strip())
        try:
            parsed = json.loads(stripped)
        except Exception:
            parsed = None
        if isinstance(parsed, dict) and parsed.get("action") in ("persevere", "pivot", "kill", "extend"):
            action = parsed["action"]  # type: ignore[assignment]
            rationale = str(parsed.get("rationale") or rationale)[:1000]
            authored_by = f"agent:llm-{provider}"
            pe = parsed.get("proposed_block_edits") or {}
            if isinstance(pe, dict) and pe.get("block"):
                bullets = pe.get("add_bullets") or []
                if isinstance(bullets, list):
                    proposed = {
                        "block": str(pe["block"])[:64],
                        "addBullets": [str(b)[:280] for b in bullets[:3]],
                    }
    return {
        "decision": action,
        "decision_rationale": rationale,
        "authored_by": authored_by,
        "proposed_block_edits": proposed,
        "decision_out": {
            "action": action,
            "rationale": rationale,
            "authoredBy": authored_by,
            "proposedBlockEdits": proposed,
        },
    }


async def _update_bmc(state: _State) -> _State:
    if state.get("idle"):
        return {"notes": "idle"}
    if state.get("dry_run"):
        return {"notes": "dry-run; skipped persistence"}

    org = state["org_did"]
    actor = state.get("actor_did", "agent:lg-bmc")
    iter_no = int(state.get("iteration_no", 1))
    version_in = int(state.get("bmc_version_in", 0))
    version_out = version_in  # pivot-apply may bump it below.

    iter_row = await repository.record_iteration(
        hypothesis_slug=state["hyp_slug"],
        iteration_no=iter_no,
        bmc_version_in=version_in,
        bmc_version_out=version_out,
        measured_value=float(state.get("measured_value", 0)),
        measurement_source=state.get("measurement_source", "unknown"),
        passed=bool(state.get("passed")),
        notes=(state.get("measurement_error") or "")[:2048],
        actor_did=actor,
        org_did=org,
    )
    iter_vid = iter_row["vertex_id"]

    sample_row = await repository.record_metric_sample(
        iteration_vertex_id=iter_vid,
        hypothesis_slug=state["hyp_slug"],
        metric=state.get("hyp_metric", ""),
        metric_query=state.get("hyp_metric_query", ""),
        measured_value=float(state.get("measured_value", 0)),
        sample_size=int(state.get("sample_size", 0)),
        source=state.get("measurement_source", "unknown"),
        actor_did=actor,
        org_did=org,
        window_start_ms=state.get("measurement_window_start_ms"),
        window_end_ms=state.get("measurement_window_end_ms"),
        raw_response=state.get("measurement_raw"),
        latency_ms=state.get("measurement_latency_ms"),
        error_text=state.get("measurement_error") or None,
    )

    dec_row = await repository.record_decision(
        iteration_vertex_id=iter_vid,
        hypothesis_slug=state["hyp_slug"],
        action=state.get("decision", "extend"),
        rationale=state.get("decision_rationale", ""),
        authored_by=state.get("authored_by", "agent:lg-bmc"),
        actor_did=actor,
        org_did=org,
    )
    dec_vid = dec_row["vertex_id"]

    action = state.get("decision", "extend")
    state_vid = ""
    if action == "pivot" and state.get("hyp_auto_apply_pivot"):
        pe = state.get("proposed_block_edits") or {}
        canvas = dict(state.get("canvas") or {})
        block = pe.get("block")
        if isinstance(block, str) and block:
            existing = dict(canvas.get(block) or {})
            bullets = list(existing.get("bullets") or [])
            for b in (pe.get("addBullets") or []):
                if b and b not in bullets:
                    bullets.append(b)
            existing["bullets"] = bullets
            canvas[block] = existing
        appended = await repository.append_state(
            canvas_json=json.dumps(canvas)[:65536],
            rationale=f"auto pivot from iteration {iter_vid[:16]}",
            source=f"iteration:{iter_vid}",
            actor_did=actor,
            org_did=org,
            created_by=state.get("authored_by", "agent:lg-bmc"),
        )
        state_vid = appended["vertex_id"]
        version_out = int(appended["version"])
        await repository.link_pivot_to_state(
            decision_vertex_id=dec_vid,
            state_vertex_id=state_vid,
            actor_did=actor,
            org_did=org,
        )

    if action == "kill" or (action == "persevere" and state.get("min_sample_reached")):
        await repository.append_hypothesis_event(
            slug=state["hyp_slug"],
            next_status=("killed" if action == "kill" else "completed"),
            authored_by=state.get("authored_by", "agent:lg-bmc"),
            actor_did=actor,
            org_did=org,
            reason=f"terminal {action} from iteration {iter_vid[:16]}",
            iteration_vertex_id=iter_vid,
        )

    notes = (
        f"BMC v{version_in}->{version_out} · {state['hyp_slug']} · "
        f"iter #{iter_no} · {action} (by {state.get('authored_by','agent:lg-bmc')})"
    )
    return {
        "bmc_version_out": version_out,
        "iteration_vertex_id": iter_vid,
        "decision_vertex_id": dec_vid,
        "metric_sample_vertex_id": sample_row["vertex_id"],
        "state_vertex_id": state_vid,
        "notes": notes,
    }


# ── Graph wiring ───────────────────────────────────────────────────────


def _maybe_idle(state: _State) -> str:
    return END if state.get("idle") else "measure"


_g: StateGraph = StateGraph(_State)
_g.add_node("bootstrap", _bootstrap)
_g.add_node("load_bmc_state", _load_bmc_state)
_g.add_node("pick_hypothesis", _pick_hypothesis)
_g.add_node("measure", _measure)
_g.add_node("evaluate", _evaluate)
_g.add_node("decide", _decide)
_g.add_node("update_bmc", _update_bmc)

_g.add_edge(START, "bootstrap")
_g.add_edge("bootstrap", "load_bmc_state")
_g.add_edge("load_bmc_state", "pick_hypothesis")
_g.add_conditional_edges("pick_hypothesis", _maybe_idle, {"measure": "measure", END: END})
_g.add_edge("measure", "evaluate")
_g.add_edge("evaluate", "decide")
_g.add_edge("decide", "update_bmc")
_g.add_edge("update_bmc", END)

GRAPH = _g.compile()
