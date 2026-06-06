"""State-machine tests for the karakuri service_resolve cell (R0). .solve() is NOT called."""

import pytest

from service_resolve.cell import ServiceResolveCell
from service_resolve.state_machine import (
    OUTCOME_UNKNOWN_SERVICE,
    ResolvePhase,
    transition_lookup,
    transition_tier_select,
    transition_tos_stance,
)


def _resolve(service):
    s = transition_lookup({"service": service})
    if s["next_node"] == "end":
        return s
    s = transition_tier_select(s)
    s = transition_tos_stance(s)
    return s


def test_google_resolves_to_t1_no_engine():
    p = _resolve("google")["cell_state"]["payload"]
    assert p["tier"] == "t1-official-api"
    assert p["officialApi"] is True
    assert p["t2Stance"] == "prohibited"        # browser-automation refused
    assert "t2Engine" not in p


def test_legacy_portal_resolves_to_t2_browser_use():
    p = _resolve("legacy-portal")["cell_state"]["payload"]
    assert p["tier"] == "t2-headless-browser"
    assert p["t2Stance"] == "permitted"
    assert p["t2Engine"] == "browser-use"


def test_noauto_saas_resolves_to_t3():
    p = _resolve("noauto-saas")["cell_state"]["payload"]
    assert p["tier"] == "t3-structured-export"
    assert p["t2Stance"] == "prohibited"


def test_unknown_service_degrades_honestly():
    s = _resolve("hooli")
    cs = s["cell_state"]
    assert cs["phase"] == ResolvePhase.REFUSED.value
    assert cs["payload"]["outcome"] == OUTCOME_UNKNOWN_SERVICE
    assert "tier" not in cs["payload"]


def test_solve_raises_at_r0():
    with pytest.raises(RuntimeError, match="R0 scaffold"):
        ServiceResolveCell().solve({})
