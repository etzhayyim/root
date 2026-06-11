"""State-machine tests for todoke cells (R0). .solve() is NOT called (it raises)."""

import pytest

from handoff_proof.cell import HandoffProofCell
from handoff_proof.state_machine import (
    HandoffPhase,
    transition_to_arrived,
    transition_to_consent_verified,
    transition_to_proof_captured,
    transition_to_proof_sealed,
)
from route_sequencing.cell import RouteSequencingCell
from route_sequencing.state_machine import (
    RoutePhase,
    transition_to_envelope_checked,
    transition_to_job_loaded,
    transition_to_route_emitted,
    transition_to_sequenced,
)

# --- route_sequencing -----------------------------------------------------------------

# A scrambled set of collinear stops: optimal open path = ascending x.
_STOPS = [
    {"id": 0, "x": 0.0, "y": 0.0, "zone": "sidewalk"},
    {"id": 1, "x": 30.0, "y": 0.0, "zone": "doorpath"},
    {"id": 2, "x": 10.0, "y": 0.0, "zone": "sidewalk"},
    {"id": 3, "x": 20.0, "y": 0.0, "zone": "doorpath"},
    {"id": 4, "x": 5.0, "y": 0.0, "zone": "crosswalk"},
]


def _run_route(stops=None, sae_level=4, commanded_mps=1.0):
    s = transition_to_job_loaded(
        {"stops": stops if stops is not None else _STOPS, "sae_level": sae_level, "commanded_mps": commanded_mps}
    )
    s = transition_to_envelope_checked(s)
    if s["cell_state"]["envelope_ok"]:
        s = transition_to_sequenced(s)
        s = transition_to_route_emitted(s)
    return s


def test_route_happy_path_sequences_and_emits():
    s = _run_route()
    assert s["cell_state"]["phase"] == RoutePhase.ROUTE_EMITTED.value
    rec = s["cell_state"]["payload"]["last_mile_route"]
    assert rec["order"] == [0, 4, 2, 3, 1]      # ascending-x optimal open path
    assert abs(rec["lengthM"] - 30.0) < 1e-6
    assert rec["saeWithinCeiling"] is True


def test_route_g7_refuses_road_zone():
    stops = _STOPS + [{"id": 9, "x": 40.0, "y": 0.0, "zone": "road"}]
    s = _run_route(stops=stops)
    assert s["cell_state"]["envelope_ok"] is False
    assert "outside todoke ODD" in s["cell_state"]["refusal"]


def test_route_g7_refuses_sae_level_5():
    s = _run_route(sae_level=5)
    assert s["cell_state"]["envelope_ok"] is False
    assert "exceeds ceiling" in s["cell_state"]["refusal"]


def test_route_g7_refuses_speed_over_sidewalk_cap():
    s = _run_route(commanded_mps=3.0)  # > 1.8 sidewalk cap
    assert s["cell_state"]["envelope_ok"] is False
    assert "exceeds" in s["cell_state"]["refusal"]


def test_route_solve_raises_at_r0():
    with pytest.raises(RuntimeError, match="R0 scaffold"):
        RouteSequencingCell().solve({})


# --- handoff_proof --------------------------------------------------------------------

def _run_handoff(consent_ref="enc:consent-0001", proof_kind="recipient-signature",
                 recipient_sig="sig-recipient", server_signed=False):
    s = transition_to_arrived({"recipient_did": "did:web:member.example/r1"})
    s = transition_to_consent_verified({**s, "consent_ref": consent_ref})
    s = transition_to_proof_captured({**s, "proof_kind": proof_kind})
    s = transition_to_proof_sealed({**s, "recipient_sig": recipient_sig, "server_signed": server_signed})
    return s


def test_handoff_happy_path_seals_on_device():
    s = _run_handoff()
    rec = s["cell_state"]["payload"]["handoff_proof"]
    assert s["cell_state"]["phase"] == HandoffPhase.PROOF_SEALED.value
    assert rec["onDeviceOnly"] is True       # G8
    assert rec["serverSigned"] is False      # G12
    assert rec["sealed"] is True


def test_handoff_g13_requires_consent():
    with pytest.raises(ValueError, match="G13 violation"):
        _run_handoff(consent_ref="")


def test_handoff_g8_rejects_cloud_image_proof():
    with pytest.raises(ValueError, match="G8 violation"):
        _run_handoff(proof_kind="cloud-image")


def test_handoff_g8_rejects_face_match():
    with pytest.raises(ValueError, match="G8 violation"):
        _run_handoff(proof_kind="face-match")


def test_handoff_g12_rejects_server_signing():
    with pytest.raises(ValueError, match="G12 violation"):
        _run_handoff(server_signed=True)


def test_handoff_unsigned_is_not_sealed():
    s = _run_handoff(recipient_sig="")
    assert s["cell_state"]["payload"]["handoff_proof"]["sealed"] is False


def test_handoff_solve_raises_at_r0():
    with pytest.raises(RuntimeError, match="R0 scaffold"):
        HandoffProofCell().solve({})
