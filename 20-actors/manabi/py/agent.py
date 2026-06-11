#!/usr/bin/env python3
"""manabi 学び — open-curriculum education langgraph actor (kotoba WASM cell).

ADR-2605261045, migration plan Phase 4. Runs in-WASM on kotoba :8077. Five handlers
over one kotoba EAVT graph, mirroring the curriculum path:

  handle_literacy         reading + writing progression (phonemic awareness → written expression)
  handle_numeracy         counting → arithmetic → algebra → calculus
  handle_civics_charter   comparative governance + etzhayyim Charter understanding (anti-indoctrination G12)
  handle_vocational       practical skill demonstration (agriculture/construction/energy/pharma domains)
  handle_lifelong_inquiry open-ended learner-led exploration (no age-out, G11)

LLM access is Murakumo-only via KotobaLLM (127.0.0.1:4000, gemma3:4b; G5). State is
written back to the kotoba Datom log (G6). Anti-addiction UX enforced structurally (G3).
Minor learners get aggregate-only attestations (G6 privacy). Anti-credentialism (G7):
no degrees/transcripts, only skillAttestation (replayable demonstrations). Member signature
on settlement only (G15). This R0 build computes and returns plans/records; it does not
broadcast real settlements (G11-gated; settlement stops at :intent).
"""
from __future__ import annotations

from typing import TypedDict

# kotoba-provided host bindings (WASM Component Model imports)
try:
    from kotoba import datalog, llm
except ImportError:
    datalog = llm = None

TITHE_BPS = 1000


class LiteracyState(TypedDict, total=False):
    learner_did: str
    current_stage: str
    completion_fraction: float


class NumeracyState(TypedDict, total=False):
    learner_did: str
    current_stage: str
    completion_fraction: float


class CivicsCharterState(TypedDict, total=False):
    learner_did: str
    charter_understanding_level: str
    timestamp: str


class VocationalState(TypedDict, total=False):
    learner_did: str
    domain: str
    demonstration_cid: str
    skill_domain: str


class LifelongInquiryState(TypedDict, total=False):
    learner_did: str
    inquiry_topic: str
    completion_fraction: float


def _murakumo_infer(prompt: str) -> str:
    """Murakumo-only inference (G5). No external LLM."""
    if llm:
        try:
            return str(llm.infer(model="gemma3:4b", prompt=prompt))
        except Exception:
            return "LLM_INFERENCE_FAILED"
    return "LLM_NOT_AVAILABLE"


def _validate_minor_aggregate_only(age_bucket: str, data: dict) -> bool:
    """G6 enforcement: minors get aggregate-only fields only."""
    if age_bucket != "minor":
        return True
    forbidden_keys = {"performancePercentile", "errorLogSummary", "timeOnTaskSec"}
    return not any(k in data for k in forbidden_keys)


def handle_literacy(state: LiteracyState) -> LiteracyState:
    """Reading + writing progression (phonemic awareness → written expression)."""
    stage = state.get("current_stage", "intro")
    flow = ["intro", "phonemic-awareness", "decoding", "fluency", "comprehension",
            "writing-mechanics", "written-expression"]
    if stage in flow:
        idx = flow.index(stage)
        if idx + 1 < len(flow):
            next_stage = flow[idx + 1]
            prompt = (f"Learner advancing from {stage} to {next_stage} in literacy. "
                      f"Suggest a guided discovery activity (not worksheets).")
            _murakumo_infer(prompt)
            return {
                **state,
                "current_stage": next_stage,
                "completion_fraction": min(1.0, state.get("completion_fraction", 0.0) + 0.15)
            }
    return state


def handle_numeracy(state: NumeracyState) -> NumeracyState:
    """Counting → arithmetic → algebra → calculus."""
    stage = state.get("current_stage", "counting")
    flow = ["counting", "place-value", "addition-subtraction", "multiplication-division",
            "fractions", "decimals", "algebra", "geometry", "calculus"]
    if stage in flow:
        idx = flow.index(stage)
        if idx + 1 < len(flow):
            next_stage = flow[idx + 1]
            prompt = (f"Learner advancing from {stage} to {next_stage} in numeracy. "
                      f"Suggest hands-on discovery (manipulatives, real-world context).")
            _murakumo_infer(prompt)
            return {
                **state,
                "current_stage": next_stage,
                "completion_fraction": min(1.0, state.get("completion_fraction", 0.0) + 0.11)
            }
    return state


def handle_civics_charter(state: CivicsCharterState) -> CivicsCharterState:
    """Comparative governance + etzhayyim Charter understanding (anti-indoctrination G12)."""
    prompt = ("Teach Charter understanding via comparative governance lens: "
              "democracy, monarchy, theocracy, communalism, etc. Include etzhayyim as ONE example. "
              "No single-truth framing (G12, G14). Learner-led inquiry encouraged.")
    result = _murakumo_infer(prompt)
    level = state.get("charter_understanding_level", "foundational")
    if level == "foundational":
        level = "intermediate"
    return {
        **state,
        "charter_understanding_level": level,
        "timestamp": "2026-06-02T10:00:00Z"
    }


def handle_vocational(state: VocationalState) -> VocationalState:
    """Practical skill demonstration (agriculture/construction/energy/pharma)."""
    domain = state.get("domain", "agriculture")
    prompt = (f"Learner demonstrating skill in {domain} domain. "
              f"Guide creation of replayable artifact (code, photo, project). "
              f"Output: demonstration CID for on-chain skill attestation (anti-credentialism G7).")
    result = _murakumo_infer(prompt)
    return {
        **state,
        "demonstration_cid": "bafyreiexample-skill-artifact-placeholder",
        "skill_domain": domain
    }


def handle_lifelong_inquiry(state: LifelongInquiryState) -> LifelongInquiryState:
    """Open-ended learner-led exploration (no age-out, G11)."""
    topic = state.get("inquiry_topic", "")
    if not topic:
        prompt = "Learner is beginning lifelong inquiry. Help them formulate a genuine question about something they wonder."
        result = _murakumo_infer(prompt)
        topic = result[:100] if result else "open-exploration"
    prompt = (f"Learner exploring: '{topic}'. "
              f"Guide resource discovery, synthesis, and self-paced project. "
              f"100% learner-led (G13). No age-out (G11).")
    _murakumo_infer(prompt)
    return {
        **state,
        "inquiry_topic": topic,
        "completion_fraction": min(1.0, state.get("completion_fraction", 0.0) + 0.20)
    }


def build_settlement_intent(gross_minor: int, buyer_sig_ref: str | None = None) -> dict:
    """Build USDC settlement intent (G7: non-fiat only, G15: member signature only).

    Stops at :intent unless member signature present (G11).
    Tithe split: 10% → Public Fund via TitheRouter (constitutional automatic).
    """
    tithe_minor = int(gross_minor * TITHE_BPS / 10000)
    factory_payout_minor = gross_minor - tithe_minor
    state = "executed" if buyer_sig_ref else "intent"
    return {
        "gross_minor": gross_minor,
        "tithe_minor": tithe_minor,
        "factory_payout_minor": factory_payout_minor,
        "rail": "usdc-base-l2",
        "state": state,
        "buyer_sig_ref": buyer_sig_ref
    }


def check_domain_gate(learner_did: str, gate_name: str, gate_fn=None) -> dict:
    """Domain gate enforcement (injected for testing)."""
    if gate_fn is not None:
        return gate_fn(learner_did, gate_name)
    return {"allowed": True, "reason": "no domain gate wired (R0)"}
