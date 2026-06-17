"""State-machine tests for todoke cells (R0). .solve() is NOT called (it raises).

NOTE (ADR-2606160842 py→clj port wave): the route_sequencing cell has been ported to
.cljc — its state machine + tests now live at
``cells/route_sequencing/state_machine.cljc`` and ``test_state_machine.cljc`` (run under
``bb``). The Python route_sequencing cell (which imported ``methods.last_mile``) was removed
so the Python ``methods/last_mile.py`` can be pruned; its behaviour is preserved + proven in
the .cljc port. This file now covers only the handoff_proof cell, which is pure Python and
carries no last_mile dependency.
"""

import pytest

from handoff_proof.cell import HandoffProofCell
from handoff_proof.state_machine import (
    HandoffPhase,
    transition_to_arrived,
    transition_to_consent_verified,
    transition_to_proof_captured,
    transition_to_proof_sealed,
)

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
