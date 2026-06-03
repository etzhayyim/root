"""
etzhayyim.personnel.* — LangServer handlers for the
personnelAssignmentDecide.bpmn workflow.

Task types:
  etzhayyim.personnel.loadProfile     read Tier-3 RLS-gated profile bundle
  etzhayyim.personnel.minimaxScore    compute worst-case loss + Ω-axis deltas
  etzhayyim.personnel.notifyDeny      audit + notify CEO/CLO when blocked
  etzhayyim.personnel.writeAssignment write vertex_etzhayyim_assignment + RACI

ADR refs:
  ADR-0018 Tier 3 PII (CEO/COO/CLO read only)
  ADR-0036 Hyperdrive direct write
  ADR-2604291800 Well-Becoming Spirit objective function
  ADR-2605080300 SQLAlchemy Core only
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
import uuid
from typing import Any

LOG = logging.getLogger("etzhayyim.personnel")

_ORG_DID   = "did:web:etzhayyim.etzhayyim.com"
_OWNER_DID = "did:web:bpmn.etzhayyim.com"

# Tier 3 RLS allowlist (CEO + COO + CLO only)
_TIER3_READERS = {
    "did:web:j-kawasaki.etzhayyim.com",
    "did:web:a-nakamura.etzhayyim.com",
    "did:web:k-bakshi.etzhayyim.com",
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return _dt.datetime.now(tz=_dt.UTC).strftime("%Y-%m-%d %H:%M:%S")

def _vid(kind: str) -> str:
    stamp = _dt.datetime.now(tz=_dt.UTC).strftime("%Y%m%d%H%M%S")
    return f"at://{_OWNER_DID}/com.etzhayyim.apps.etzhayyim.{kind}/{stamp}-{uuid.uuid4().hex[:8]}"

def _query(sql_str: str, params: dict | None = None) -> list[dict]:
    try:
        from sqlalchemy import text
        from pymagatama.db_alchemy import sa_query
        return sa_query(text(sql_str), params or {})
    except Exception as exc:
        LOG.warning("sa_query failed: %s", exc)
        return []

def _execute(sql_str: str, params: dict) -> bool:
    try:
        from sqlalchemy import text
        from pymagatama.db_alchemy import sa_rowcount
        sa_rowcount(text(sql_str), params)
        return True
    except Exception as exc:
        LOG.warning("sa_execute failed: %s", exc)
        return False

def _llm_json(system: str, user: str, max_tokens: int = 1500) -> dict:
    try:
        from pymagatama.llm import call_tier
        result = call_tier("structured", system=system, user=user, max_tokens=max_tokens)
        content = result.get("content", "")
        if "```" in content:
            for chunk in content.split("```")[1::2]:
                stripped = chunk.lstrip("json").strip()
                try:
                    return json.loads(stripped)
                except Exception:
                    pass
        try:
            return json.loads(content)
        except Exception:
            return {"raw": content}
    except Exception as exc:
        LOG.warning("LLM call failed: %s", exc)
        return {"error": str(exc)}


# ── Task: loadProfile (Tier 3 RLS-gated read) ──────────────────────────────────

async def task_etzhayyim_personnel_load_profile(
    person_did: str,
    candidate_target: str = "",
    decision_kind: str = "assignment.create",
    requester_did: str = "",
) -> dict:
    """Load skill + bio + profile + career bundle for minimax scoring.

    RLS: requester_did MUST be CEO/COO/CLO. Otherwise returns redacted bundle.
    """
    redacted = requester_did not in _TIER3_READERS

    skills = _query(
        "SELECT skill_id, proficiency, peer_verified, last_used_at "
        "FROM vertex_etzhayyim_person_skill WHERE person_did = :did",
        {"did": person_did},
    )

    contracts = _query(
        "SELECT c.contract_id, c.contract_kind, c.principal_did, c.vendor_did, "
        "       c.title, c.start_date, c.end_date, c.status "
        "FROM vertex_etzhayyim_contract c "
        "JOIN edge_etzhayyim_person_contract e ON e.contract_id = c.contract_id "
        "WHERE e.person_did = :did AND c.status = 'active'",
        {"did": person_did},
    )

    person = _query(
        "SELECT person_did, display_name, department, title, employment_type, status "
        "FROM vertex_etzhayyim_person WHERE person_did = :did LIMIT 1",
        {"did": person_did},
    )

    bundle: dict[str, Any] = {
        "person":     person[0] if person else {},
        "skills":     skills,
        "contracts":  contracts,
        "redacted":   redacted,
    }

    if not redacted:
        bio = _query(
            "SELECT birth_year, gender, birthplace_pref, household_type, "
            "       socioeconomic_band, family_env_summary "
            "FROM vertex_etzhayyim_person_bio WHERE person_did = :did LIMIT 1",
            {"did": person_did},
        )
        education = _query(
            "SELECT level, institution, department, degree, major, "
            "       start_date, end_date, graduated "
            "FROM vertex_etzhayyim_person_education WHERE person_did = :did "
            "ORDER BY start_date DESC LIMIT 10",
            {"did": person_did},
        )
        career = _query(
            "SELECT employer, title, department, employment_type, "
            "       start_date, end_date, current, key_achievement, reason_for_leaving "
            "FROM vertex_etzhayyim_person_career WHERE person_did = :did "
            "ORDER BY start_date DESC LIMIT 20",
            {"did": person_did},
        )
        dependents = _query(
            "SELECT relation, birth_year, financial_dependent, care_dependent, lives_with "
            "FROM vertex_etzhayyim_person_dependent WHERE person_did = :did",
            {"did": person_did},
        )
        profile = _query(
            "SELECT assessed_at, big5_openness, big5_conscientiousness, "
            "       big5_extraversion, big5_agreeableness, big5_neuroticism, "
            "       self_preservation, risk_tolerance, conflict_style, "
            "       learning_velocity, autonomy_level, llm_compat_score, "
            "       strengths_summary, caveats_summary "
            "FROM vertex_etzhayyim_person_profile WHERE person_did = :did "
            "ORDER BY assessed_at DESC LIMIT 1",
            {"did": person_did},
        )
        utterance_stats = _query(
            "SELECT COUNT(*) AS n, AVG(sentiment) AS avg_sentiment, "
            "       AVG(conflict_score) AS avg_conflict, "
            "       AVG(certainty_score) AS avg_certainty "
            "FROM vertex_etzhayyim_person_utterance WHERE person_did = :did",
            {"did": person_did},
        )

        bundle.update({
            "bio":              bio[0] if bio else {},
            "education":        education,
            "career":           career,
            "dependents":       dependents,
            "profile":          profile[0] if profile else {},
            "utterance_stats":  utterance_stats[0] if utterance_stats else {},
        })

    return {"profile_bundle": bundle, "ok": True}


# ── Task: minimaxScore (worst-case + Ω-axis evaluation) ────────────────────────

_MINIMAX_SYSTEM = """You are the minimax scorer for etzhayyim.etzhayyim.com personnel
decisions. Principal: etzhayyim. Vendor: etzhayyim Japan株式会社.

Inputs: person profile bundle (skill/bio/career/profile) + candidate target
(role/project/contract path) + decision_kind.

Compute for THIS person × THIS target:
- worst_case_loss_jpy: monetary downside if assignment fails / IP leaks /
  retention break (integer, JPY)
- worst_case_summary: 1 sentence (Japanese) describing the worst-case path
- worst_case_probability: 0.0-1.0
- expected_value_jpy: integer expected monetary contribution
- regret_score: 0.0-1.0 (1.0 = highest regret, do not assign)
- spirit_floor_violated: true if any Ω axis = 0
  (Spirit/Wellbecoming/Feeling/Buffer)
- wellbecoming_delta / feeling_delta / buffer_delta: -1.0..+1.0
- ip_leak_risk: 0.0-1.0 (vendor SES leak especially high)
- retention_risk: 0.0-1.0 (likelihood of departure within 12 months)
- recommendation: "assign" | "block" | "needs_human_review"
- rationale: 1-2 sentences (Japanese) — be specific, cite evidence

Output ONLY JSON with these exact keys.
"""

async def task_etzhayyim_personnel_minimax_score(
    profile_bundle: dict,
    candidate_target: str,
    decision_kind: str = "assignment.create",
) -> dict:
    """Score a person × target candidate using minimax decision criterion."""

    user_msg = (
        f"decision_kind: {decision_kind}\n"
        f"candidate_target: {candidate_target}\n"
        f"profile_bundle: {json.dumps(profile_bundle, ensure_ascii=False)[:6000]}"
    )
    scored = _llm_json(_MINIMAX_SYSTEM, user_msg, max_tokens=1500)

    if "error" in scored and "regret_score" not in scored:
        # Heuristic fallback — assume mid risk, needs human review
        scored = {
            "worst_case_loss_jpy":    5_000_000,
            "worst_case_summary":     "LLM scoring unavailable — defaulting to mid risk",
            "worst_case_probability": 0.3,
            "expected_value_jpy":     3_000_000,
            "expected_value_summary": "fallback estimate",
            "regret_score":           0.5,
            "spirit_floor_violated":  False,
            "wellbecoming_delta":     0.0,
            "feeling_delta":          0.0,
            "buffer_delta":           0.0,
            "ip_leak_risk":           0.5,
            "retention_risk":         0.3,
            "recommendation":         "needs_human_review",
            "rationale":              "LLM 評価未取得のため人間判断必須",
        }

    person_did = (profile_bundle.get("person") or {}).get("person_did", "")

    # Persist to vertex_etzhayyim_person_minimax (Tier 3)
    row = {
        "vertex_id":              _vid("personMinimax"),
        "person_did":             person_did,
        "decision_kind":          decision_kind,
        "candidate_target":       candidate_target,
        "worst_case_loss_jpy":    float(scored.get("worst_case_loss_jpy") or 0),
        "worst_case_summary":     str(scored.get("worst_case_summary") or "")[:500],
        "worst_case_probability": float(scored.get("worst_case_probability") or 0.0),
        "expected_value_jpy":     float(scored.get("expected_value_jpy") or 0),
        "expected_value_summary": str(scored.get("expected_value_summary") or "")[:500],
        "regret_score":           float(scored.get("regret_score") or 0.5),
        "spirit_floor_violated":  bool(scored.get("spirit_floor_violated") or False),
        "wellbecoming_delta":     float(scored.get("wellbecoming_delta") or 0.0),
        "feeling_delta":          float(scored.get("feeling_delta") or 0.0),
        "buffer_delta":           float(scored.get("buffer_delta") or 0.0),
        "ip_leak_risk":           float(scored.get("ip_leak_risk") or 0.0),
        "retention_risk":         float(scored.get("retention_risk") or 0.0),
        "recommendation":         str(scored.get("recommendation") or "needs_human_review"),
        "rationale":              str(scored.get("rationale") or "")[:1000],
        "assessed_at":            _now_iso(),
        "assessor_did":           "did:web:etzhayyim.etzhayyim.com",
        "llm_model":              "structured",
        "created_at":             _now_iso(),
        "owner_did":              _ORG_DID,
    }
    _execute(
        "INSERT INTO vertex_etzhayyim_person_minimax "
        "(vertex_id, person_did, decision_kind, candidate_target, "
        " worst_case_loss_jpy, worst_case_summary, worst_case_probability, "
        " expected_value_jpy, expected_value_summary, regret_score, "
        " spirit_floor_violated, wellbecoming_delta, feeling_delta, buffer_delta, "
        " ip_leak_risk, retention_risk, recommendation, rationale, "
        " assessed_at, assessor_did, llm_model, created_at, owner_did) "
        "VALUES (:vertex_id, :person_did, :decision_kind, :candidate_target, "
        " :worst_case_loss_jpy, :worst_case_summary, :worst_case_probability, "
        " :expected_value_jpy, :expected_value_summary, :regret_score, "
        " :spirit_floor_violated, :wellbecoming_delta, :feeling_delta, :buffer_delta, "
        " :ip_leak_risk, :retention_risk, :recommendation, :rationale, "
        " :assessed_at, :assessor_did, :llm_model, :created_at, :owner_did)",
        row,
    )

    return {"minimax_result": scored, "ok": True}


# ── Task: notifyDeny (audit-only; integrators wire actual channel) ─────────────

async def task_etzhayyim_personnel_notify_deny(
    minimax_result: dict,
    recipient_dids: list[str] | None = None,
) -> dict:
    """Notify CEO/CLO when minimax gate blocks an assignment.

    Currently emits OCEL row only; integrate Teams/email send via
    microsoft.etzhayyim.com sendDraft from the consuming agent if needed.
    """
    recipients = recipient_dids or [
        "did:web:j-kawasaki.etzhayyim.com",
        "did:web:k-bakshi.etzhayyim.com",
    ]
    LOG.info(
        "personnel deny notified — recipients=%s regret=%s ip_leak_risk=%s",
        recipients,
        minimax_result.get("regret_score"),
        minimax_result.get("ip_leak_risk"),
    )
    return {"ok": True, "notified": recipients}


# ── Task: writeAssignment (post-approval) ──────────────────────────────────────

async def task_etzhayyim_personnel_write_assignment(
    person_did: str,
    candidate_target: str,
    minimax_result: dict,
    approval_decision: str,
) -> dict:
    """Write vertex_etzhayyim_assignment + RACI rows after COO approval."""
    if approval_decision != "approved":
        return {"ok": False, "error": f"not approved: {approval_decision}"}

    assignment_vid = _vid("assignment")
    assignment_id  = assignment_vid.rsplit("/", 1)[-1]

    # candidate_target convention: "role:<role_id>" or "project:<project_id>"
    # or "task:<task_nsid>" (RACI). Default to role binding.
    role_id    = ""
    project_id = ""
    task_nsid  = ""
    if candidate_target.startswith("role:"):
        role_id = candidate_target.split(":", 1)[1]
    elif candidate_target.startswith("project:"):
        project_id = candidate_target.split(":", 1)[1]
    elif candidate_target.startswith("task:"):
        task_nsid = candidate_target.split(":", 1)[1]

    if task_nsid:
        # RACI write — default role = R (responsible)
        _execute(
            "INSERT INTO vertex_etzhayyim_raci "
            "(vertex_id, task_nsid, person_did, raci_role, context, "
            " effective_date, created_at, owner_did) "
            "VALUES (:vid, :nsid, :did, 'R', :ctx, :eff, :now, :owner)",
            {
                "vid":   _vid("raci"),
                "nsid":  task_nsid,
                "did":   person_did,
                "ctx":   minimax_result.get("rationale", "")[:500],
                "eff":   _now_iso(),
                "now":   _now_iso(),
                "owner": _ORG_DID,
            },
        )
    else:
        _execute(
            "INSERT INTO vertex_etzhayyim_assignment "
            "(vertex_id, person_did, role_id, project_id, allocation_pct, "
            " start_date, status, created_at, owner_did) "
            "VALUES (:vid, :did, :rid, :pid, :pct, :start, 'active', :now, :owner)",
            {
                "vid":   assignment_vid,
                "did":   person_did,
                "rid":   role_id,
                "pid":   project_id,
                "pct":   100,
                "start": _now_iso(),
                "now":   _now_iso(),
                "owner": _ORG_DID,
            },
        )

    LOG.info(
        "personnel assignment written — person=%s target=%s id=%s",
        person_did, candidate_target, assignment_id,
    )
    return {"ok": True, "assignment_id": assignment_id}


# ── Worker registration ────────────────────────────────────────────────────────

def register(app: Any, timeout_ms: int = 90_000) -> None:
    """Register all etzhayyim.personnel.* task handlers."""
    from pymagatama.langserver_compat import LangServerWorker
    if not isinstance(app, LangServerWorker):
        return

    @app.task(task_type="etzhayyim.personnel.loadProfile",
              timeout_ms=timeout_ms, max_jobs_to_activate=4)
    async def _load(person_did: str = "", candidate_target: str = "",
                    decision_kind: str = "assignment.create",
                    requester_did: str = "") -> dict:
        return await task_etzhayyim_personnel_load_profile(
            person_did, candidate_target, decision_kind, requester_did,
        )

    @app.task(task_type="etzhayyim.personnel.minimaxScore",
              timeout_ms=timeout_ms, max_jobs_to_activate=2)
    async def _score(profile_bundle: dict | None = None,
                     candidate_target: str = "",
                     decision_kind: str = "assignment.create") -> dict:
        return await task_etzhayyim_personnel_minimax_score(
            profile_bundle or {}, candidate_target, decision_kind,
        )

    @app.task(task_type="etzhayyim.personnel.notifyDeny",
              timeout_ms=timeout_ms, max_jobs_to_activate=4)
    async def _deny(minimax_result: dict | None = None,
                    recipient_dids: list[str] | None = None) -> dict:
        return await task_etzhayyim_personnel_notify_deny(
            minimax_result or {}, recipient_dids,
        )

    @app.task(task_type="etzhayyim.personnel.writeAssignment",
              timeout_ms=timeout_ms, max_jobs_to_activate=4)
    async def _write(person_did: str = "", candidate_target: str = "",
                     minimax_result: dict | None = None,
                     approval_decision: str = "denied") -> dict:
        return await task_etzhayyim_personnel_write_assignment(
            person_did, candidate_target, minimax_result or {}, approval_decision,
        )

    LOG.info(
        "Registered tasks: etzhayyim.personnel.{loadProfile,minimaxScore,"
        "notifyDeny,writeAssignment}"
    )
