#!/usr/bin/env python3
"""State-machine tests for 扶持 (fuchi) cells (R0). .solve() is NOT called (it raises).

Standalone-runnable: python3 test_state_machines.py
"""
from __future__ import annotations

import sys

from covenant_intake.cell import CovenantIntakeCell
from covenant_intake.state_machine import (
    IntakePhase,
    transition_to_recorded,
    transition_to_screened,
)
from need_assessment.cell import NeedAssessmentCell
from need_assessment.state_machine import AssessPhase, transition_to_assessed
from allocation_compute.cell import AllocationComputeCell
from allocation_compute.state_machine import ComputePhase, transition_to_computed
from routing_dispatch.cell import RoutingDispatchCell
from routing_dispatch.state_machine import RoutePhase, transition_to_routed
from governance_gate.cell import GovernanceGateCell
from governance_gate.state_machine import (
    GovPhase,
    transition_to_decided,
    transition_to_routed as gov_route_to,
)


# ── covenant_intake (G4/G5/G9) ──────────────────────────────────────────────
def _intake(**over):
    base = {"cell_state": {}, "did": "did:m:abel", "covenant": "vowed",
            "tenure_months": 96, "hazard_permille": 1800,
            "owns_payoff": False, "server_held_key": False}
    base.update(over)
    return transition_to_screened(base)


def test_intake_screens_and_records():
    cs = _intake()["cell_state"]
    assert cs["phase"] == IntakePhase.SCREENED.value
    cs2 = transition_to_recorded({"cell_state": cs})["cell_state"]
    assert cs2["phase"] == IntakePhase.RECORDED.value
    assert cs2["payload"]["ownsPayoff"] is False and cs2["payload"]["serverHeldKey"] is False


def test_intake_refuses_bad_covenant():
    cs = _intake(covenant="anon")["cell_state"]
    assert cs["phase"] == IntakePhase.REFUSED.value and "G4" in cs["refusal"]


def test_intake_refuses_owns_payoff():
    cs = _intake(owns_payoff=True)["cell_state"]
    assert cs["phase"] == IntakePhase.REFUSED.value and "G5" in cs["refusal"]


def test_intake_refuses_server_key():
    cs = _intake(server_held_key=True)["cell_state"]
    assert cs["phase"] == IntakePhase.REFUSED.value and "no-server-key" in cs["refusal"]


def test_intake_cannot_record_without_screen():
    cs = transition_to_recorded({"cell_state": {}})["cell_state"]
    assert cs["phase"] == IntakePhase.REFUSED.value


# ── need_assessment (G2/G3) ─────────────────────────────────────────────────
def test_assess_builds_envelope():
    cs = transition_to_assessed({"cell_state": {}, "did": "did:m:abel", "lines": [
        {"line": "food", "imputed_usd_micros_yr": 4_000_000_000, "cash_usd_micros": 0},
        {"line": "energy", "imputed_usd_micros_yr": 1_000_000_000, "cash_usd_micros": 0},
    ]})["cell_state"]
    assert cs["phase"] == AssessPhase.ASSESSED.value
    assert cs["imputed_total"] == 5_000_000_000
    assert all(p["cashUsdMicros"] == 0 for p in cs["payload"])


def test_assess_refuses_cash_line():
    cs = transition_to_assessed({"cell_state": {}, "did": "d", "lines": [
        {"line": "cash", "imputed_usd_micros_yr": 1, "cash_usd_micros": 0}]})["cell_state"]
    assert cs["phase"] == AssessPhase.REFUSED.value and "G3" in cs["refusal"]


def test_assess_refuses_nonzero_cash():
    cs = transition_to_assessed({"cell_state": {}, "did": "d", "lines": [
        {"line": "food", "imputed_usd_micros_yr": 1, "cash_usd_micros": 9}]})["cell_state"]
    assert cs["phase"] == AssessPhase.REFUSED.value and "cash≡0" in cs["refusal"]


# ── allocation_compute (G1/G2/G5) ───────────────────────────────────────────
def _compute(**over):
    base = {"cell_state": {}, "did": "did:m:abel", "instrument": "sustenance",
            "tenure_months": 96, "hazard_permille": 1800, "owns_payoff": False}
    base.update(over)
    return transition_to_computed(base)


def test_compute_produces_weight_and_zero_cash():
    cs = _compute()["cell_state"]
    assert cs["phase"] == ComputePhase.COMPUTED.value
    assert cs["weight"] > 0
    assert cs["payload"]["cashUsdMicros"] == 0 and cs["payload"]["serverHeldKey"] is False


def test_compute_refuses_equity_instrument():
    cs = _compute(instrument="equity")["cell_state"]
    assert cs["phase"] == ComputePhase.REFUSED.value and "G1" in cs["refusal"]


def test_compute_refuses_carry_and_dividend():
    for bad in ("carry", "dividend", "revenue-share", "exit"):
        cs = _compute(instrument=bad)["cell_state"]
        assert cs["phase"] == ComputePhase.REFUSED.value and "G1" in cs["refusal"]


def test_compute_refuses_owns_payoff():
    cs = _compute(owns_payoff=True)["cell_state"]
    assert cs["phase"] == ComputePhase.REFUSED.value and "G5" in cs["refusal"]


# ── routing_dispatch (G3) ───────────────────────────────────────────────────
def test_route_decomposes_to_rails():
    cs = transition_to_routed({"cell_state": {}, "did": "a", "lines": [
        {"line": "food", "imputed_usd_micros_yr": 5, "cash_usd_micros": 0},
        {"line": "liquidity", "imputed_usd_micros_yr": 5, "cash_usd_micros": 0},
    ]})["cell_state"]
    assert cs["phase"] == RoutePhase.ROUTED.value
    by = {r["kind"]: r for r in cs["rails"]}
    assert by["food-mitsuho"]["memberPrincipal"] is False
    assert by["liquidity-warifu"]["memberPrincipal"] is True
    assert cs["in_kind_coverage"] == 0.5


def test_route_refuses_cash_rail():
    cs = transition_to_routed({"cell_state": {}, "did": "a", "lines": [
        {"line": "food", "imputed_usd_micros_yr": 1, "cash_usd_micros": 9}]})["cell_state"]
    assert cs["phase"] == RoutePhase.REFUSED.value and "cash≡0" in cs["refusal"]


# ── governance_gate (G7) ────────────────────────────────────────────────────
def test_gov_auto_for_low_in_kind():
    cs = gov_route_to({"cell_state": {}, "alloc_id": "a", "imputed_total": 8_000_000_000,
                       "context": "food energy sustenance"})["cell_state"]
    assert cs["route"] == "auto"
    cs2 = transition_to_decided({"cell_state": cs})["cell_state"]
    assert cs2["outcome"] == "accepted"


def test_gov_vote_above_ceiling():
    cs = gov_route_to({"cell_state": {}, "alloc_id": "a", "imputed_total": 28_000_000_000,
                       "context": "remote-robotics teleop"})["cell_state"]
    assert cs["route"] == "sbt-vote"
    cs2 = transition_to_decided({"cell_state": cs, "yes": 11, "no": 2})["cell_state"]
    assert cs2["outcome"] == "accepted"


def test_gov_council_for_invariant_touch():
    cs = gov_route_to({"cell_state": {}, "alloc_id": "a", "imputed_total": 1,
                       "context": "new commons-land grant for housing"})["cell_state"]
    assert cs["route"] == "council-lv7"
    cs2 = transition_to_decided({"cell_state": cs})["cell_state"]
    assert cs2["outcome"] == "pending"


def test_gov_refused_for_rider_hit():
    cs = gov_route_to({"cell_state": {}, "alloc_id": "a", "imputed_total": 1,
                       "context": "requests an affiliate ad-revenue share"})["cell_state"]
    assert cs["route"] == "refused"
    cs2 = transition_to_decided({"cell_state": cs})["cell_state"]
    assert cs2["outcome"] == "refused"


# ── all .solve() raise at R0 ────────────────────────────────────────────────
def test_all_cells_solve_raises():
    for C in (CovenantIntakeCell, NeedAssessmentCell, AllocationComputeCell,
              RoutingDispatchCell, GovernanceGateCell):
        try:
            C().solve({})
        except RuntimeError:
            continue
        raise AssertionError(f"{C.__name__}.solve must raise at R0")


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"test_state_machines.py: {len(fns)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
