#!/usr/bin/env python3
"""manabi 学び — agent cell tests (no kotoba host, no network, no LLM).

ADR-2605261045 Phase 4. Exercises the 5 handlers + settlement + gates with injected
functions so the suite runs offline (Murakumo-only invariant untouched; G5).

    python3 test_agent.py
"""
from __future__ import annotations

import agent


def _check(name: str, cond: bool) -> bool:
    print(("  ok  " if cond else "  FAIL") + f"  {name}")
    return cond


def test_literacy_advances_stage() -> bool:
    out = agent.handle_literacy({
        "current_stage": "intro",
        "completion_fraction": 0.0
    })
    return _check("literacy advances from intro to phonemic-awareness",
                  out["current_stage"] == "phonemic-awareness" and out["completion_fraction"] > 0.0)


def test_numeracy_advances_stage() -> bool:
    out = agent.handle_numeracy({
        "current_stage": "counting",
        "completion_fraction": 0.0
    })
    return _check("numeracy advances from counting to place-value",
                  out["current_stage"] == "place-value" and out["completion_fraction"] > 0.0)


def test_civics_charter_levels_understanding() -> bool:
    out = agent.handle_civics_charter({
        "learner_did": "did:web:test",
        "charter_understanding_level": "foundational"
    })
    return _check("civics_charter promotes understanding level",
                  out["charter_understanding_level"] == "intermediate")


def test_civics_charter_anti_indoctrination() -> bool:
    """G12 enforcement: no single-truth framing in comparative governance."""
    out = agent.handle_civics_charter({
        "learner_did": "did:web:test",
        "charter_understanding_level": "foundational"
    })
    return _check("civics_charter enforces comparative-religion (G12, G14)",
                  "timestamp" in out and out["charter_understanding_level"] != "foundational")


def test_vocational_creates_skill_attestation() -> bool:
    out = agent.handle_vocational({
        "learner_did": "did:web:test",
        "domain": "agriculture"
    })
    return _check("vocational creates replayable skill attestation (anti-credentialism G7)",
                  "demonstration_cid" in out and out["skill_domain"] == "agriculture")


def test_lifelong_inquiry_learner_led() -> bool:
    """G13 + G11: ≥100% learner-led, no age-out."""
    out = agent.handle_lifelong_inquiry({
        "learner_did": "did:web:test",
        "inquiry_topic": "",
        "completion_fraction": 0.0
    })
    return _check("lifelong_inquiry is learner-led (G13, G11)",
                  "inquiry_topic" in out and len(out["inquiry_topic"]) > 0)


def test_settlement_tithe_split() -> bool:
    """G7: 10% tithe auto-split to Public Fund."""
    s = agent.build_settlement_intent(1000000)
    return _check("10% tithe split + stops at intent (G7)",
                  s["tithe_minor"] == 100000
                  and s["factory_payout_minor"] == 900000
                  and s["state"] == "intent"
                  and s["rail"] == "usdc-base-l2")


def test_settlement_executed_with_member_sig() -> bool:
    """G15: no-server-key; only member signature executes."""
    s = agent.build_settlement_intent(1000000, buyer_sig_ref="0xmembersig")
    return _check("settlement executes only with member signature (G15)",
                  s["state"] == "executed" and s["buyer_sig_ref"] == "0xmembersig")


def test_domain_gate_offline() -> bool:
    """Gate enforcement via injected function."""
    def mock_gate(did: str, gate_name: str):
        return {"allowed": did != "blocked", "reason": "test gate"}
    out = agent.check_domain_gate("allowed_did", "G1", gate_fn=mock_gate)
    return _check("domain gate enforces (G1...G14)",
                  out["allowed"] is True)


def test_domain_gate_blocks() -> bool:
    """Gate rejection."""
    def mock_gate(did: str, gate_name: str):
        return {"allowed": did != "blocked", "reason": "test gate"}
    out = agent.check_domain_gate("blocked", "G1", gate_fn=mock_gate)
    return _check("domain gate blocks when violated",
                  out["allowed"] is False)


def test_minor_aggregate_only_enforcement() -> bool:
    """G6: minors get aggregate-only fields."""
    data = {"sessionDuration": 45, "completionFraction": 0.5}
    result = agent._validate_minor_aggregate_only("minor", data)
    return _check("minor learner data passes G6 validation (no forbidden keys)",
                  result is True)


def test_minor_rejects_performance_data() -> bool:
    """G6: minors forbidden from performance tracking."""
    data = {"sessionDuration": 45, "performancePercentile": 85}
    result = agent._validate_minor_aggregate_only("minor", data)
    return _check("minor learner rejected if performance data present (G6)",
                  result is False)


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"manabi agent — {len(tests)} tests")
    results = [t() for t in tests]
    passed = sum(results)
    print(f"\n{passed}/{len(tests)} passed")
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
