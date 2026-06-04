"""Phase state machine for the todoke handoff_proof (受渡証) cell.

Proof-of-delivery for the final metre — and the actor's privacy spine. Two constitutional
invariants are enforced by construction here:

  * **G8 privacy-by-construction** — proof-of-delivery is produced ON-DEVICE only. No cloud
    imagery, no facial recognition, no biometric recipient ID. The only admissible proof
    kinds are :recipient-signature, :locker-code, and :on-device-photo-hash (a hash, never an
    uploaded image). A :cloud-image or :face-match proof kind is a violation and raises (N5).
  * **G12 no-server-key + G13 consent-bound** — the recipient (a member or a consenting
    counterparty) signs the hand-off; the server never signs, and a doorstep hand-off without
    a recorded recipient consent reference is refused.

Transitions are pure and unit-tested; the cell's .solve() raises until Council activation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# G8: the ONLY admissible proof kinds. Cloud/biometric kinds are unrepresentable → refused.
ADMISSIBLE_PROOF_KINDS = ("recipient-signature", "locker-code", "on-device-photo-hash")
FORBIDDEN_PROOF_KINDS = ("cloud-image", "face-match", "biometric")


class HandoffPhase(Enum):
    INIT = "init"
    ARRIVED = "arrived"
    CONSENT_VERIFIED = "consent_verified"
    PROOF_CAPTURED = "proof_captured"
    PROOF_SEALED = "proof_sealed"


@dataclass
class HandoffState:
    phase: str = HandoffPhase.INIT.value
    job_id: str = "did:web:todoke.etzhayyim.com/job/demo-0001"
    recipient_did: str = ""
    consent_ref: str = ""          # encrypted consent record reference (G13)
    proof_kind: str = "recipient-signature"
    recipient_sig: str = ""        # member/recipient signature (G12 — server never signs)
    server_signed: bool = False    # must stay False (G12 invariant)
    on_device_only: bool = True    # G8 invariant — proof never leaves the device as imagery
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> HandoffState:
    return HandoffState(**d.get("cell_state", {}))


def transition_to_arrived(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.phase = HandoffPhase.ARRIVED.value
    cs.job_id = state.get("job_id", cs.job_id)
    cs.recipient_did = state.get("recipient_did", cs.recipient_did)
    return {"cell_state": cs.__dict__, "next_node": "verify_consent"}


def transition_to_consent_verified(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.consent_ref = state.get("consent_ref", "")
    # G13: no doorstep hand-off without a recorded (encrypted) recipient consent reference.
    if not cs.consent_ref:
        raise ValueError("G13 violation: hand-off requires a recipient consent reference")
    cs.phase = HandoffPhase.CONSENT_VERIFIED.value
    return {"cell_state": cs.__dict__, "next_node": "capture_proof"}


def transition_to_proof_captured(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    kind = state.get("proof_kind", cs.proof_kind)
    # G8: forbidden (cloud/biometric) proof kinds are a constitutional violation.
    if kind in FORBIDDEN_PROOF_KINDS or kind not in ADMISSIBLE_PROOF_KINDS:
        raise ValueError(
            f"G8 violation: proof_kind {kind!r} not in {ADMISSIBLE_PROOF_KINDS} (no cloud/biometric, N5)"
        )
    cs.phase = HandoffPhase.PROOF_CAPTURED.value
    cs.proof_kind = kind
    cs.on_device_only = True
    return {"cell_state": cs.__dict__, "next_node": "seal_proof"}


def transition_to_proof_sealed(state: dict[str, Any]) -> dict[str, Any]:
    cs = _state(state)
    cs.recipient_sig = state.get("recipient_sig", "")
    # G12: the server must never sign; only the recipient/member signature seals the proof.
    if state.get("server_signed", False):
        raise ValueError("G12 violation: server-side signing is prohibited (no-server-key)")
    cs.server_signed = False
    sealed = bool(cs.recipient_sig)
    cs.phase = HandoffPhase.PROOF_SEALED.value
    cs.payload = {
        "handoff_proof": {
            "jobId": cs.job_id,
            "recipientDid": cs.recipient_did,
            "consentRef": cs.consent_ref,
            "proofKind": cs.proof_kind,
            "onDeviceOnly": cs.on_device_only,   # G8 — always True
            "serverSigned": cs.server_signed,    # G12 — always False
            "sealed": sealed,                    # True iff recipient signed (G12)
        }
    }
    return {"cell_state": cs.__dict__, "next_node": "end"}
