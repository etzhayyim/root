"""State-machine tests for yadori cells (R0). .solve() is NOT called (it raises)."""

import pytest

from availability_check.cell import AvailabilityCheckCell
from availability_check.state_machine import (
    AvailabilityPhase,
    live_rdap_allowed,
    transition_to_availability_recorded,
    transition_to_classified,
    transition_to_normalized,
    transition_to_rdap_resolved,
)
from reservation.cell import ReservationCell
from reservation.state_machine import (
    ReservationPhase,
    transition_to_authorized,
    transition_to_intent_built,
    transition_to_quoted,
    transition_to_screened,
)


def _run(
    sld="example-newproject",
    speculative=False,
    charter_clean=True,
    registrar="cloudflare",
    council_approved_registrar=False,
    funding_source="member-okaimono",
    member_sig="member-ed25519-sig",
    server_sig="",
):
    s = transition_to_screened(
        {"cell_state": {}, "sld": sld, "speculative": speculative, "charter_clean": charter_clean}
    )
    s = transition_to_quoted(
        {**s, "registrar": registrar,
         "council_approved_registrar": council_approved_registrar,
         "funding_source": funding_source}
    )
    s = transition_to_intent_built(s)
    s = transition_to_authorized({**s, "member_sig": member_sig, "server_sig": server_sig})
    return s


def test_happy_path_reaches_authorized():
    s = _run()
    cs = s["cell_state"]
    assert cs["phase"] == ReservationPhase.AUTHORIZED.value
    intent = cs["payload"]["reservation_intent"]
    assert intent["serverHeldKey"] is False        # G5
    assert intent["payer"] == "member"             # G2 — yadori never the buyer
    assert intent["signed"] is True and intent["signedBy"] == "member"
    assert cs["payload"]["authorization"]["serverSigned"] is False
    assert cs["payload"]["authorization"]["outwardGated"] is True  # G7


def test_g6_blocks_trademark_name():
    with pytest.raises(ValueError, match="G6 violation"):
        _run(sld="google")


def test_g6_blocks_speculation():
    with pytest.raises(ValueError, match="G6 violation"):
        _run(speculative=True)


def test_g6_blocks_charter_unclean_name():
    with pytest.raises(ValueError, match="G6 violation"):
        _run(charter_clean=False)


def test_g3_default_registrar_is_cloudflare():
    s = _run(registrar="cloudflare")
    assert s["cell_state"]["registrar"] == "cloudflare"


def test_g3_external_registrar_requires_council():
    with pytest.raises(ValueError, match="G3 violation"):
        _run(registrar="godaddy", council_approved_registrar=False)


def test_g3_external_registrar_allowed_with_council_flag():
    s = _run(registrar="godaddy", council_approved_registrar=True)
    assert s["cell_state"]["registrar"] == "godaddy"


def test_g2_rejects_fiat_funding():
    with pytest.raises(ValueError, match="G2 violation"):
        _run(funding_source="org-fiat")


def test_g5_refuses_server_signature():
    with pytest.raises(ValueError, match="G5 violation"):
        _run(member_sig="member-sig", server_sig="server-sig")


def test_g5_requires_member_signature():
    with pytest.raises(ValueError, match="G5 violation"):
        _run(member_sig="")


def test_solve_raises_at_r0():
    with pytest.raises(RuntimeError, match="R0 scaffold"):
        ReservationCell().solve({})


# ── availability_check cell ────────────────────────────────────────────────

def _check(fqdn, fixtures=None, operator_gate=False):
    s = transition_to_normalized({"cell_state": {}, "fqdn": fqdn})
    s = transition_to_rdap_resolved({**s, "operator_gate": operator_gate})
    s = transition_to_classified({**s, "fixtures": fixtures or {}})
    s = transition_to_availability_recorded(s)
    return s["cell_state"]["payload"]["availability_record"]


def test_available_from_fixture_through_cell():
    rec = _check("free-name.dev", fixtures={"free-name.dev": 404})
    assert rec["availability"] == "available"
    assert rec["source"] == "fixture"
    assert rec["rdapUrl"].endswith("/domain/free-name.dev")


def test_registered_from_fixture_through_cell():
    rec = _check("example.com", fixtures={"example.com": 200})
    assert rec["availability"] == "registered"


def test_idn_normalized_through_cell():
    rec = _check("café.com", fixtures={"xn--caf-dma.com": 404})
    assert rec["asciiFqdn"] == "xn--caf-dma.com"
    assert rec["availability"] == "available"


def test_invalid_domain_flagged_through_cell():
    rec = _check("nodot")
    assert rec["availability"] == "invalid"


def test_offline_no_fixture_is_unknown_not_available():
    # G8: never guess :available with no evidence.
    rec = _check("mystery.com")
    assert rec["availability"] == "unknown"
    assert rec["source"] == "none"


def test_g7_live_blocked_without_env_flag(monkeypatch):
    # Operator attests but env flag absent → live NOT allowed (offline → unknown, no socket).
    monkeypatch.delenv("YADORI_ALLOW_LIVE_RDAP", raising=False)
    assert live_rdap_allowed({"operator_gate": True}) is False
    rec = _check("mystery.org", operator_gate=True)
    assert rec["availability"] == "unknown"


def test_g7_live_blocked_without_operator_attestation(monkeypatch):
    # Env flag set but no operator attestation → still NOT allowed.
    monkeypatch.setenv("YADORI_ALLOW_LIVE_RDAP", "1")
    assert live_rdap_allowed({"operator_gate": False}) is False


def test_g7_live_allowed_only_when_both_present(monkeypatch):
    monkeypatch.setenv("YADORI_ALLOW_LIVE_RDAP", "1")
    assert live_rdap_allowed({"operator_gate": True}) is True


def test_availability_cell_solve_raises_at_r0():
    with pytest.raises(RuntimeError, match="R0 scaffold"):
        AvailabilityCheckCell().solve({})
