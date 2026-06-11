"""State-machine tests for nusa cells (R0). .solve() is NOT called (it raises).

Run in isolation (repo pytest plugin env is broken):
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_state_machines.py
"""

import pytest

from cultivation_license_plan.cell import CultivationLicensePlanCell
from cultivation_license_plan.state_machine import (
    LicensePhase,
    transition_to_authorized,
    transition_to_plan_built,
    transition_to_screened as license_screen,
)
from fiber_provenance.cell import FiberProvenanceCell
from fiber_provenance.state_machine import (
    ProvenancePhase,
    transition_to_recorded,
    transition_to_screened,
)
from observation_bridge.cell import ObservationBridgeCell


# ─────────────────────────── fiber_provenance (G1/G2) ───────────────────────
def _provenance(thc_class="low-thc", fiber_use=("textile", "shimenawa"), cultivar="hemp.tochigishiro"):
    s = transition_to_screened(
        {"cell_state": {}, "cultivar": cultivar, "thc_class": thc_class, "fiber_use": list(fiber_use)}
    )
    return transition_to_recorded(s)


def test_fiber_provenance_low_thc_records():
    out = _provenance()
    cs = out["cell_state"]
    assert cs["phase"] == ProvenancePhase.RECORDED.value
    assert cs["payload"]["thcClass"] == "low-thc"
    assert cs["payload"]["screened"] is True


def test_fiber_provenance_fiber_class_records():
    out = _provenance(thc_class=":fiber", fiber_use=["aratae"])  # keyword form also accepted
    assert out["cell_state"]["payload"]["thcClass"] == "fiber"


def test_fiber_provenance_rejects_psychoactive():
    """G1: a psychoactive cultivar never yields a provenance record."""
    with pytest.raises(ValueError, match="G1 violation"):
        _provenance(thc_class="psychoactive")


def test_fiber_provenance_rejects_high_thc_keyword():
    with pytest.raises(ValueError, match="G1 violation"):
        transition_to_screened({"cell_state": {}, "cultivar": "x", "thc_class": ":high-thc"})


def test_fiber_provenance_rejects_consumption_use():
    """G2: a non-fibre (consumption) use is refused."""
    with pytest.raises(ValueError, match="G2 violation"):
        _provenance(fiber_use=["smoking"])


def test_fiber_provenance_record_requires_screen():
    with pytest.raises(ValueError, match="THC-class screen"):
        transition_to_recorded({"cell_state": {"screened": False}})


# ─────────────────────── cultivation_license_plan (G1/G4/G5/G8) ──────────────
def _license(
    thc_class="low-thc",
    purpose="industrial-fiber",
    funding_source="member-okaimono",
    member_sig="member-ed25519-sig",
    server_sig="",
    cultivar="hemp.tochigishiro",
):
    s = license_screen({"cell_state": {}, "cultivar": cultivar, "thc_class": thc_class, "purpose": purpose})
    s = transition_to_plan_built({**s, "funding_source": funding_source})
    return transition_to_authorized({**s, "member_sig": member_sig, "server_sig": server_sig})


def test_license_member_principal_serverless_outward_gated():
    out = _license()
    cs = out["cell_state"]
    assert cs["phase"] == LicensePhase.AUTHORIZED.value
    p = cs["payload"]
    assert p["licenseePrincipal"] == "member"      # G4
    assert p["fundingSource"] == "member-okaimono"  # G4
    assert p["serverHeldKey"] is False              # G5
    assert p["outwardGated"] is True                # G8
    assert p["signedBy"] == "member"                # G5


def test_license_rejects_org_funding():
    with pytest.raises(ValueError, match="G4 violation"):
        _license(funding_source="org-treasury")


def test_license_refuses_server_signature():
    with pytest.raises(ValueError, match="G5 violation"):
        _license(server_sig="server-sig")


def test_license_requires_member_signature():
    with pytest.raises(ValueError, match="member signature"):
        _license(member_sig="")


def test_license_rejects_psychoactive_cultivar():
    with pytest.raises(ValueError, match="G1 violation"):
        _license(thc_class="psychoactive")


def test_license_rejects_unknown_purpose():
    with pytest.raises(ValueError, match="purpose"):
        _license(purpose="recreational")


# ─────────────────────────── observation_bridge (G3) ────────────────────────
def test_observation_bridge_routes_off_actor():
    b = ObservationBridgeCell()
    assert "danjo" in b.route("legislative-trace")
    assert "moushibumi" in b.route("public-comment")
    assert "yakushi" in b.route("cannabis-derived-medicine")


def test_observation_bridge_rejects_unknown_concern():
    with pytest.raises(ValueError, match="unknown concern"):
        ObservationBridgeCell().route("advocate-legalization")


# ─────────────────────────── R0: .solve() raises ────────────────────────────
@pytest.mark.parametrize("cell", [FiberProvenanceCell(), CultivationLicensePlanCell(), ObservationBridgeCell()])
def test_solve_raises_at_r0(cell):
    with pytest.raises(RuntimeError, match="R0 scaffold"):
        cell.solve({})
