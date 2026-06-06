"""Tests for the noroshi photonic-IC layout generator (ADR-2606051600). Stdlib + pytest only."""

from __future__ import annotations

from link_budget import compute
from pic_layout import (
    full_link_design,
    plan_to_link_design,
    receiver_plan,
    report,
    transmitter_plan,
    try_build_gds,
)


def test_transmitter_plan_has_expected_components():
    plan = transmitter_plan()
    assert set(plan.components) == {"laser0", "mzm0", "gc0"}
    # two routed waveguides
    assert sum(1 for o in plan.ops if o.op == "route") == 2


def test_total_waveguide_is_sum_of_routes():
    plan = transmitter_plan(route_um=1500.0)
    assert plan.total_waveguide_um == 200.0 + 1500.0


def test_layout_feeds_link_budget_and_closes():
    plan = transmitter_plan()
    budget = compute(plan_to_link_design(plan))
    assert budget.closes  # the reference Tx layout closes the link


def test_longer_routing_lowers_margin():
    short = compute(plan_to_link_design(transmitter_plan(route_um=500.0)))
    long = compute(plan_to_link_design(transmitter_plan(route_um=5000.0)))
    assert long.margin_db < short.margin_db  # more waveguide ⇒ more loss ⇒ less margin


def test_gds_build_is_gated_or_built():
    plan = transmitter_plan()
    res = try_build_gds(plan)
    # Either gdsfactory is absent (gated, honest) or it built a GDS — never an error.
    assert res["built"] in (True, False)
    if not res["built"]:
        assert "gated" in res["reason"] or "not available" in res["reason"]


def test_report_renders_open_eda_framing():
    txt = report()
    assert "ModelOp" in txt
    assert "open-EDA" in txt or "gdsfactory" in txt
    assert "G1" in txt or "no proprietary EDA" in txt.lower() or "NDA" in txt


# ── coverage: guards, custom base, route ports ───────────────────────────────
def test_non_positive_route_length_rejected():
    import pytest
    with pytest.raises(ValueError):
        transmitter_plan(route_um=0.0)
    with pytest.raises(ValueError):
        transmitter_plan(route_um=-100.0)


def test_plan_to_link_design_uses_custom_base_rx_waveguide():
    from link_budget import LinkDesign
    plan = transmitter_plan()
    d = plan_to_link_design(plan, base=LinkDesign(rx_waveguide_cm=3.0))
    assert d.rx_waveguide_cm == 3.0
    assert d.tx_waveguide_cm == plan.total_waveguide_um / 1e4


def test_routes_carry_port_pairs():
    plan = transmitter_plan()
    routes = [o for o in plan.ops if o.op == "route"]
    assert all(len(r.ports) == 2 for r in routes)
    assert routes[-1].ports == ("mzm0.o", "gc0.i")


# ── receiver PIC + full end-to-end link ──────────────────────────────────────
def test_receiver_plan_has_coupler_and_photodetector():
    rx = receiver_plan()
    assert set(rx.components) == {"gc_in", "pd0"}
    routes = [o for o in rx.ops if o.op == "route"]
    assert len(routes) == 1 and routes[0].ports == ("gc_in.o", "pd0.i")


def test_receiver_plan_rejects_non_positive_route():
    import pytest
    with pytest.raises(ValueError):
        receiver_plan(route_um=0.0)


def test_full_link_design_uses_both_waveguides():
    tx, rx = transmitter_plan(), receiver_plan()
    d = full_link_design(tx, rx)
    assert d.tx_waveguide_cm == tx.total_waveguide_um / 1e4
    assert d.rx_waveguide_cm == rx.total_waveguide_um / 1e4


def test_full_link_closes_and_longer_rx_lowers_margin():
    tx = transmitter_plan()
    short = compute(full_link_design(tx, receiver_plan(route_um=500.0)))
    long = compute(full_link_design(tx, receiver_plan(route_um=8000.0)))
    assert short.closes
    assert long.margin_db < short.margin_db  # more rx waveguide ⇒ more loss ⇒ less margin


def test_report_mentions_receiver_and_end_to_end():
    txt = report()
    assert "receiver plan" in txt
    assert "end-to-end" in txt
