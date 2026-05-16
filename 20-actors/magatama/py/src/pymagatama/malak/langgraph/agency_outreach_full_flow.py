"""agency_outreach_full_flow — LangGraph composite chain (replaces BPMN).

Composite of 5 sub-NSIDs:
    registerAgencyProspect → draftAgencyOutreach → reviewAgencyOutreach
    → sendAgencyOutreach → handleAgencyOutreachReply

Architecture (per ADR-2605080600 + ADR-2605082000 LangGraph Graph-Definition-
as-Data + ADR-2605082200 LangServer Thin Dispatcher Contract):

  Start
    │
    ▼
  validate_input
    │
    ▼ [Conditional: opt_in_gate]
    │ ok                                    │ reject
    ▼                                       ▼
  register_prospect                        END (status=abort_opt_in)
    │
    ▼ [Conditional: jurisdiction_gate]
    │ ok                                    │ reject
    ▼                                       ▼
  draft_outreach                            END (status=abort_jurisdiction)
    │
    ▼ [Conditional: safety_verdict_gate]
    │ ok                                    │ abort
    ▼                                       ▼
  human_review                              END (status=abort_safety)
    │
    ▼ [Conditional: approval_verdict_gate]
    │ approve                               │ deny
    ▼                                       ▼
  schedule_send                             END (status=abort_unapproved)
    │  (queue if outside business hours)
    ▼
  send_outreach
    │
    ▼
  emit_pegel
    │
    ▼
  audit_emit
    │
    ▼
  END (status=sent)

5 abort 経路: opt_in / jurisdiction / safety / unapproved / outside_hours
全 status は `vertex_malak_surveillance_investigation_tick` に記録される。

Replaces:
    00-contracts/bpmn/ai/gftd/malak/agencyOutreachFullFlow.bpmn (archived)
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
import re
import time
import uuid
from typing import Any, Dict, List, Optional, TypedDict
from zoneinfo import ZoneInfo

from langgraph.graph import StateGraph, END

from .workflow import run_langgraph_pipeline

# Reuse jurisdiction loader from agency_outreach prototype if present.
try:
    from _working.malak.surveillance.langgraph_agency_outreach import (
        jurisdiction_status as _jurisdiction_status,
        ALLOWED_OPT_IN_SOURCES as _ALLOWED_OPT_IN_SOURCES,
    )
except ImportError:
    # Production fallback — same constants, jurisdiction status from cooperation_status field if present.
    _ALLOWED_OPT_IN_SOURCES = {"exhibition_list", "lecture_host", "referral", "inbound"}
    def _jurisdiction_status(cc: str) -> Dict[str, str]:
        return {"status": "standard", "note": ""}

logger = logging.getLogger(__name__)
JST = ZoneInfo("Asia/Tokyo")


class OutreachFlowState(TypedDict, total=False):
    # input
    prospect_id: str
    requester_did: str
    addressee_jurisdiction: str   # ISO 3166-1 alpha-3
    prefecture: str               # JP-specific (only when jurisdiction == "jpn")
    dept: str
    addressee_role: str
    addressee_cipher: str
    wrapped_key: str
    kid: str
    opt_in_source: str
    opt_in_at: str
    opt_in_evidence: str
    use_case_pitch: str
    template_key: str
    rag_hints: List[str]
    sales_manager_did: str
    extra_approver_did: str       # for restricted jurisdictions
    sender_did: str
    channel_email: str
    schedule_hint: str            # immediate | nextBusinessHour
    # internal
    cooperation_status: str
    cooperation_note: str
    draft_id: str
    draft_subject: str
    draft_body: str
    safety_flags: List[str]
    safety_action: str            # ok | rewrite | abort
    blocked_reason: str
    approver_did: str
    approved_at: str
    schedule_status: str
    scheduled_for: str
    # output
    send_id: str
    ms_message_id: str
    sent_at: str
    pegel_tick_id: str
    status: str                   # sent | queued | abort_*
    error: str


_BUSINESS_DAYS = {0, 1, 2, 3, 4}  # Mon-Fri
_BUSINESS_HOUR_START = 9
_BUSINESS_HOUR_END = 17

_NG_GIFT = ["無料デモ", "お試し提供", "粗品", "お土産", "お食事"]
_NG_EXAGGERATION = ["100%検挙", "必ず特定", "唯一の", "業界最高"]
_NG_AUTHORITY = ["警察庁採用", "警察庁公認"]
_NG_CASE_REF = [r"先日の[^\s。]{1,20}事件"]


def _now_jst() -> _dt.datetime:
    return _dt.datetime.now(JST)


def _malak_did(suffix: str = "") -> str:
    return f"did:web:malak.gftd.ai{(':' + suffix) if suffix else ''}"


# ── Nodes ─────────────────────────────────────────────────────────────


def validate_input_node(state: OutreachFlowState) -> Dict[str, Any]:
    if not state.get("prospect_id") and not state.get("opt_in_source"):
        return {"status": "abort_input", "error": "prospect_id or opt_in_source required"}
    if not state.get("addressee_jurisdiction"):
        return {"status": "abort_jurisdiction", "error": "addressee_jurisdiction (ISO 3166 alpha-3) required"}
    return {
        "safety_flags": [],
        "schedule_status": "immediate",
    }


def gate_opt_in(state: OutreachFlowState) -> str:
    if state.get("status", "").startswith("abort"):
        return "abort"
    src = state.get("opt_in_source", "")
    at = state.get("opt_in_at", "")
    if not at or src not in _ALLOWED_OPT_IN_SOURCES:
        return "abort_opt_in"
    return "register_prospect"


def abort_opt_in_node(state: OutreachFlowState) -> Dict[str, Any]:
    return {
        "status": "abort_opt_in",
        "error":  f"opt_in_source={state.get('opt_in_source')!r} not in whitelist or opt_in_at missing",
    }


def register_prospect_node(state: OutreachFlowState) -> Dict[str, Any]:
    """Calls task_malak_register_agency_prospect logic (idempotent)."""
    if state.get("prospect_id"):
        return {}  # already registered
    pid = f"prospect-{uuid.uuid4().hex[:12]}"
    return {"prospect_id": pid}


def jurisdiction_check_node(state: OutreachFlowState) -> Dict[str, Any]:
    cc = state.get("addressee_jurisdiction", "")
    coop = _jurisdiction_status(cc)
    status = coop["status"]
    out: Dict[str, Any] = {
        "cooperation_status": status,
        "cooperation_note":   coop.get("note", ""),
    }
    if status == "prohibited":
        out["status"] = "abort_jurisdiction"
        out["error"] = f"cooperation_status=prohibited for {cc}; outreach hard-blocked"
    elif status == "restricted" and not state.get("extra_approver_did"):
        out["status"] = "abort_jurisdiction_unapproved"
        out["error"] = f"cooperation_status=restricted for {cc}; extra_approver_did required"
    return out


def gate_jurisdiction(state: OutreachFlowState) -> str:
    if state.get("status", "").startswith("abort"):
        return "abort"
    return "draft_outreach"


def abort_jurisdiction_node(state: OutreachFlowState) -> Dict[str, Any]:
    return {} if state.get("status") else {"status": "abort_jurisdiction", "error": "jurisdiction blocked"}


_EN_OVERPROMISE = ("guarantee", "100%", "industry-leading", "always", "never fails")


def _build_draft_jp(state: OutreachFlowState) -> tuple[str, str]:
    subject = (
        f"監視カメラ シーン/人物検索 ガード設計のご説明 "
        f"({_now_jst().strftime('%Y-%m')}, amanomibashira / Gftd Japan)"
    )
    body = (
        "<<RENDER:addresseeName>> 様\n\n"
        f"{state.get('opt_in_evidence', '展示会名簿')} にてお名刺交換させていただきました。\n"
        "amanomibashira (運営法人) の営業担当 と申します。\n\n"
        "監視カメラ映像から自然言語シーン記述で関連クリップを検索する技術について、"
        "技術仕様 (顔特徴量の国内拘束 + 令状ゲート + 人間判断介在) をご説明する機会を頂戴できれば幸甚です。\n\n"
        "ご関心がおありの場合は malak-surveillance@gftd.ai までご一報ください。\n"
        "オプトアウト: {{unsubscribeUrl}}\n\n"
        "amanomibashira (運営) / 技術受託: Gftd Japan株式会社\n"
    )
    return subject, body


def _build_draft_en(state: OutreachFlowState, variant: str) -> tuple[str, str]:
    """EN drafts per `templates/sales_email_v1_en.md`. variant ∈ {generic, interpol, eu}."""
    if variant == "interpol":
        subject = "Cross-border surveillance ethics-by-design — briefing offer (amanomibashira / Gftd Japan, Japan)"
        intro = (
            "Thank you for the introduction at "
            f"{state.get('opt_in_evidence', 'the event')}. I'm writing from amanomibashira (Japan), "
            "the operating entity behind malak.surveillance, to share our design posture for "
            "cross-border investigation cooperation aligned with INTERPOL Constitution Article 32.\n\n"
        )
    elif variant == "eu":
        subject = "Open-vocabulary surveillance scene search — GDPR-aligned ethics-by-design briefing (amanomibashira / Gftd Japan)"
        intro = (
            f"Dear <<RENDER:addresseeName>>,\n\nThank you for the introduction at "
            f"{state.get('opt_in_evidence', 'the event')}. I'm writing from amanomibashira (Japan); "
            "this message is sent on the lawful basis of legitimate interest under GDPR Art 6(1)(f), "
            "and you can object at any time via the unsubscribe link below.\n\n"
        )
    else:  # generic English-speaking LEA
        subject = "Open-vocabulary surveillance scene search — ethics-by-design briefing (amanomibashira / Gftd Japan — Japan)"
        intro = (
            f"Dear <<RENDER:addresseeName>>,\n\nThank you for the introduction at "
            f"{state.get('opt_in_evidence', 'the event')}. I'm writing from amanomibashira (Japan), "
            "the operating entity behind a system called malak.surveillance.\n\n"
        )

    body = (
        f"{intro}"
        "We are developing open-vocabulary scene search over street CCTV — for example, "
        "\"red cap, bicycle, black backpack\" — for fraud-network investigation support. "
        "Two points are most relevant to your remit:\n\n"
        "  1) Face templates are AES-256-GCM-encrypted and kept inside a Japan-based on-prem GPU "
        "pod. They are never sent to Cloudflare or any non-JP inference provider; the master key "
        "is geofenced. The exact re-identification path (queryPerson) is hard-gated at the edge, "
        "orchestrator, and LangGraph layers — without a warrant or formal enquiry reference the "
        "request returns HTTP 403 before reaching any inference component.\n\n"
        "  2) Scene-description search (no person identification) and known-person re-"
        "identification are separated at the path level. The former runs as ordinary "
        "administrative-investigation support; the latter is the only path that touches face "
        "templates and is conditional on a recorded human investigator review.\n\n"
        "We would be glad to share a 15-page technical brief covering compliance posture against "
        "APPI, the NPA R6 procurement draft, the EU AI Act, and the FATF Recommendations.\n\n"
        "If you'd find a 45-minute briefing useful — secure video, or in person at your office — "
        "please reply to malak-surveillance@gftd.ai.\n\n"
        "If you'd rather not hear from us, unsubscribe here: {{unsubscribeUrl}}\n\n"
        "Best regards,\n\n"
        "{{senderName}}\n"
        "amanomibashira (operating entity, Japan)\n"
        "Technical implementation contracted to: Gftd Japan株式会社\n"
        "Postal: <<RENDER:senderPostalAddress>> (CAN-SPAM compliance)\n"
        "Privacy contact: privacy@gftd.ai\n"
    )
    return subject, body


def _en_variant_for_jurisdiction(cc: str, template_key: str) -> str:
    """Resolve EN body variant from `template_key` or fallback to jurisdiction."""
    if template_key == "v1_intro_en_interpol":
        return "interpol"
    if template_key == "v1_intro_en_continental_eu":
        return "eu"
    if cc.lower().startswith("intl:interpol") or cc.lower() in {"intl:europol", "intl:eurojust", "intl:unodc"}:
        return "interpol"
    if cc.lower() in {"deu", "fra", "ita", "nld", "esp", "bel", "che", "aut", "pol", "swe", "nor", "dnk", "fin"}:
        return "eu"
    return "generic"


def draft_outreach_node(state: OutreachFlowState) -> Dict[str, Any]:
    """Build draft per language + jurisdiction. Phase 0 = template-based;
    Phase 1 hooks qwen3-30b for personalisation (kept within SAFETY_GATES)."""
    draft_id = f"draft-{uuid.uuid4().hex[:12]}"
    lang = (state.get("template_key") or "").endswith("_en") or \
           (state.get("template_key") or "").startswith("v1_") and "en" in (state.get("template_key") or "") or \
           any(state.get("template_key", "").endswith(s) for s in ["_en", "_en_interpol", "_en_continental_eu"])
    is_en = lang or state.get("template_key", "").endswith(("_en", "_en_interpol", "_en_continental_eu"))

    if is_en:
        variant = _en_variant_for_jurisdiction(state.get("addressee_jurisdiction", ""), state.get("template_key", ""))
        subject, body = _build_draft_en(state, variant)
    else:
        subject, body = _build_draft_jp(state)

    flags: List[str] = []
    # SAFETY_GATES quick checks (shared between JP/EN)
    for ng in _NG_GIFT:
        if ng in body:
            flags.append("no_gift_offer")
            break
    for ng in _NG_EXAGGERATION:
        if ng in body:
            flags.append("no_exaggeration")
            break
    for ng in _NG_AUTHORITY:
        if ng in body:
            flags.append("no_authority_claim")
            break
    if "{{unsubscribeUrl}}" not in body:
        flags.append("unsubscribe_url_missing")
    if "amanomibashira" not in body or "Gftd Japan" not in body:
        flags.append("sender_info_missing")
    # EN-specific extras
    if is_en:
        for ng in _EN_OVERPROMISE:
            if ng.lower() in body.lower():
                flags.append("en_no_overpromise")
                break
        if "Postal:" not in body and "<<RENDER:senderPostalAddress>>" not in body:
            flags.append("en_no_can_spam_violation")
        if state.get("addressee_jurisdiction", "").lower() in {"deu", "fra", "ita", "nld", "esp", "bel", "che", "aut", "pol", "swe"} \
           and "GDPR" not in body:
            flags.append("en_no_gdpr_violation")
    safety_action = "abort" if flags else "ok"
    return {
        "draft_id":       draft_id,
        "draft_subject":  subject,
        "draft_body":     body,
        "safety_flags":   flags,
        "safety_action":  safety_action,
        "blocked_reason": ", ".join(flags) if flags else "",
    }


def gate_safety(state: OutreachFlowState) -> str:
    if state.get("safety_action") == "abort":
        return "abort_safety"
    return "human_review"


def abort_safety_node(state: OutreachFlowState) -> Dict[str, Any]:
    return {"status": "abort_safety", "error": f"SAFETY_GATES violated: {state.get('safety_flags')}"}


def human_review_node(state: OutreachFlowState) -> Dict[str, Any]:
    """Real impl: kaisya consent helper submits + waits. Mock: read
    sales_manager_did from state — if present, treat as approved."""
    if not state.get("sales_manager_did"):
        return {"status": "abort_unapproved", "error": "sales_manager_did required for review"}
    return {
        "approver_did": state["sales_manager_did"],
        "approved_at":  _now_jst().isoformat(),
    }


def gate_approval(state: OutreachFlowState) -> str:
    if state.get("status", "").startswith("abort"):
        return "abort_unapproved"
    return "schedule_send"


def abort_unapproved_node(state: OutreachFlowState) -> Dict[str, Any]:
    return {} if state.get("status") else {"status": "abort_unapproved", "error": "no approver"}


def schedule_send_node(state: OutreachFlowState) -> Dict[str, Any]:
    n = _now_jst()
    if n.weekday() in _BUSINESS_DAYS and _BUSINESS_HOUR_START <= n.hour < _BUSINESS_HOUR_END:
        return {"schedule_status": "immediate"}
    if state.get("schedule_hint") != "nextBusinessHour":
        # Treat as queued
        nxt = n.replace(hour=_BUSINESS_HOUR_START, minute=0, second=0, microsecond=0)
        if n.hour >= _BUSINESS_HOUR_END or n.weekday() not in _BUSINESS_DAYS:
            nxt += _dt.timedelta(days=1)
        while nxt.weekday() not in _BUSINESS_DAYS:
            nxt += _dt.timedelta(days=1)
        return {
            "schedule_status": "queued",
            "scheduled_for":   nxt.isoformat(),
            "status":          "queued",
        }
    # nextBusinessHour: same compute path
    nxt = n.replace(hour=_BUSINESS_HOUR_START, minute=0, second=0, microsecond=0)
    if n.hour >= _BUSINESS_HOUR_END or n.weekday() not in _BUSINESS_DAYS:
        nxt += _dt.timedelta(days=1)
    while nxt.weekday() not in _BUSINESS_DAYS:
        nxt += _dt.timedelta(days=1)
    return {
        "schedule_status": "queued",
        "scheduled_for":   nxt.isoformat(),
        "status":          "queued",
    }


def gate_schedule(state: OutreachFlowState) -> str:
    return "audit_emit" if state.get("status") == "queued" else "send_outreach"


def send_outreach_node(state: OutreachFlowState) -> Dict[str, Any]:
    """Mock microsoft.gftd.ai sendMail call."""
    sid = f"send-{uuid.uuid4().hex[:12]}"
    msg_id = f"ms-{uuid.uuid4().hex[:16]}"
    return {
        "send_id":       sid,
        "ms_message_id": msg_id,
        "sent_at":       _now_jst().isoformat(),
        "status":        "sent",
    }


async def emit_pegel_node(state: OutreachFlowState) -> Dict[str, Any]:
    if state.get("status", "").startswith("abort"):
        return {}
    details = (
        f"prospect_id={state.get('prospect_id', '')}\n"
        f"draft_id={state.get('draft_id', '')}\n"
        f"jurisdiction={state.get('addressee_jurisdiction', '')}\n"
        f"cooperation_status={state.get('cooperation_status', '')}\n"
        f"send_id={state.get('send_id', '')}\n"
        f"ms_message_id={state.get('ms_message_id', '')}\n"
        f"status={state.get('status', '')}\n"
    )
    try:
        pegel = await run_langgraph_pipeline(
            role_id="malak",
            params={
                "tlp": "AMBER",
                "action": f"outreach:{state.get('status', '')}",
                "details": details,
            },
        )
        tid = (pegel or {}).get("tick_vertex_id") or ""
        return {"pegel_tick_id": tid}
    except Exception as e:  # noqa: BLE001
        return {"error": f"pegel emit failed: {e}"}


def audit_emit_node(state: OutreachFlowState) -> Dict[str, Any]:
    logger.info(
        "malak.outreach.%s prospect_id=%s draft_id=%s jurisdiction=%s coop=%s ms_message_id=%s",
        state.get("status", "unknown"),
        state.get("prospect_id", ""),
        state.get("draft_id", ""),
        state.get("addressee_jurisdiction", ""),
        state.get("cooperation_status", ""),
        state.get("ms_message_id", ""),
    )
    return {}


# ── Graph ──────────────────────────────────────────────────────────────


def build_agency_outreach_graph():
    g = StateGraph(OutreachFlowState)
    g.add_node("validate_input",    validate_input_node)
    g.add_node("abort_opt_in",      abort_opt_in_node)
    g.add_node("register_prospect", register_prospect_node)
    g.add_node("jurisdiction_check", jurisdiction_check_node)
    g.add_node("abort_jurisdiction", abort_jurisdiction_node)
    g.add_node("draft_outreach",    draft_outreach_node)
    g.add_node("abort_safety",      abort_safety_node)
    g.add_node("human_review",      human_review_node)
    g.add_node("abort_unapproved",  abort_unapproved_node)
    g.add_node("schedule_send",     schedule_send_node)
    g.add_node("send_outreach",     send_outreach_node)
    g.add_node("emit_pegel",        emit_pegel_node)
    g.add_node("audit_emit",        audit_emit_node)

    g.set_entry_point("validate_input")
    g.add_conditional_edges(
        "validate_input",
        gate_opt_in,
        {"register_prospect": "register_prospect", "abort_opt_in": "abort_opt_in", "abort": "audit_emit"},
    )
    g.add_edge("abort_opt_in", "audit_emit")
    g.add_edge("register_prospect", "jurisdiction_check")
    g.add_conditional_edges(
        "jurisdiction_check",
        gate_jurisdiction,
        {"draft_outreach": "draft_outreach", "abort": "abort_jurisdiction"},
    )
    g.add_edge("abort_jurisdiction", "audit_emit")
    g.add_conditional_edges(
        "draft_outreach",
        gate_safety,
        {"human_review": "human_review", "abort_safety": "abort_safety"},
    )
    g.add_edge("abort_safety", "audit_emit")
    g.add_conditional_edges(
        "human_review",
        gate_approval,
        {"schedule_send": "schedule_send", "abort_unapproved": "abort_unapproved"},
    )
    g.add_edge("abort_unapproved", "audit_emit")
    g.add_conditional_edges(
        "schedule_send",
        gate_schedule,
        {"send_outreach": "send_outreach", "audit_emit": "audit_emit"},
    )
    g.add_edge("send_outreach", "emit_pegel")
    g.add_edge("emit_pegel", "audit_emit")
    g.add_edge("audit_emit", END)
    return g.compile()


async def run_outreach_flow(**kwargs: Any) -> Dict[str, Any]:
    graph = build_agency_outreach_graph()
    initial: OutreachFlowState = dict(kwargs)  # type: ignore[assignment]
    return await graph.ainvoke(initial)
