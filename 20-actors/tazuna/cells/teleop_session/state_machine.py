"""Phase state machine for the tazuna (手綱) teleop_session cell.

The defining, safety-critical tazuna skill: admit a remote teleoperation session over a physical
robot ONLY as Transparent Force and ONLY under no-server-key, then relay member-signed actuation
commands while a deadman / e-stop / latency budget continuously guards a safe-stop. The gates are
enforced here as pure, unit-tested transitions; the cell's .solve() raises until Council activation.

Invariants enforced (the load-bearing four):
  G3 — Transparent Force: a grant cannot be built without a force-authorization reference
       (1 SBT=1 vote admission of the robot's force class); every command is anchored on-chain.
  G4 — no-server-key: the grant carries serverHeldKey=false + an encrypted-envelope REFERENCE only;
       every actuation command is member-signed and a server signature is refused (ADR-2605231525).
  G10 — soft-RT supervision: a deadman lapse or a latency-budget breach forces a safe-stop /
        autonomy-fallback; an e-stop is always honoured. NOT a certified safety system.
  N1  — force class: :weaponizable is unrepresentable; only the three admitted classes pass.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

MEMBER = "member"
ENCREF_PREFIX = "encref:"
ADMITTED_FORCE_CLASSES = ("observational", "soft-actuation", "powered-actuation")
ALWAYS_PERMITTED = ("halt", "estop", "handback")  # safety commands never gated


class SessionPhase(Enum):
    INIT = "init"
    FORCE_AUTHORIZED = "force_authorized"
    GRANT_BUILT = "grant_built"
    COMMAND_RELAYED = "command_relayed"
    SAFE_STOPPED = "safe_stopped"


@dataclass
class SessionState:
    phase: str = SessionPhase.INIT.value
    robot_id: str = "sanae-saotome-01"
    principal: str = MEMBER                 # G4: always the member
    force_class: str = "soft-actuation"
    force_auth_ref: str = ""                # G3: required to build a grant
    server_held_key: bool = False           # G4: always false
    secret_ref: str = "encref:com.etzhayyim.encrypted/tazuna-session"
    deadman_ms: int = 300
    latency_budget_ms: int = 150
    # command relay inputs
    command_kind: str = "move"
    member_sig: str = ""
    server_sig: str = ""                     # G4: must remain empty
    elapsed_since_presence_ms: int = 0       # G10: deadman input
    observed_latency_ms: int = 0             # G10: latency input
    payload: dict = field(default_factory=dict)


def _state(d: dict[str, Any]) -> SessionState:
    return SessionState(**d.get("cell_state", {}))


def transition_verify_force_auth(state: dict[str, Any]) -> dict[str, Any]:
    """G3/N1: admit the session only if the force class is representable and force-authorized."""
    cs = _state(state)
    cs.force_class = state.get("force_class", cs.force_class)
    cs.force_auth_ref = state.get("force_auth_ref", cs.force_auth_ref)

    if cs.force_class not in ADMITTED_FORCE_CLASSES:
        raise ValueError(
            f"N1 violation: force class {cs.force_class!r} is unrepresentable "
            "(:weaponizable / force-as-harm can never be admitted; Mission Charter §1.12)"
        )
    if not cs.force_auth_ref:
        raise ValueError(
            "G3 violation: Transparent Force requires a force-authorization reference "
            "(1 SBT=1 vote admission of this force class) before a teleop session is admitted"
        )

    cs.phase = SessionPhase.FORCE_AUTHORIZED.value
    return {"cell_state": cs.__dict__, "next_node": "grant_built"}


def transition_build_grant(state: dict[str, Any]) -> dict[str, Any]:
    """G4: build a server-keyless grant holding only an encrypted-envelope ref — never plaintext."""
    cs = _state(state)
    cs.secret_ref = state.get("secret_ref", cs.secret_ref)
    cs.server_held_key = False              # G4 invariant

    if not cs.secret_ref.startswith(ENCREF_PREFIX):
        raise ValueError(
            "G4 violation: the grant may carry only an encrypted-envelope ref "
            "(com.etzhayyim.encrypted.*); plaintext credentials are never stored"
        )

    cs.phase = SessionPhase.GRANT_BUILT.value
    cs.payload["grant"] = {
        "robotId": cs.robot_id,
        "principal": MEMBER,
        "serverHeldKey": False,
        "secretRef": cs.secret_ref,
        "forceAuthRef": cs.force_auth_ref,
        "deadmanMs": cs.deadman_ms,
        "latencyBudgetMs": cs.latency_budget_ms,
        "onChainAnchor": True,
        "outwardGated": True,
    }
    return {"cell_state": cs.__dict__, "next_node": "relay_command"}


def _safe_state(cs: SessionState) -> str:
    """G10: the soft-RT supervision verdict (also exported for methods/teleop_safety.py parity)."""
    if cs.command_kind == "estop":
        return "estopped"
    if cs.elapsed_since_presence_ms > cs.deadman_ms:
        return "deadman-lapse"
    if cs.observed_latency_ms > cs.latency_budget_ms:
        return "latency-breach"
    return "nominal"


def transition_relay_command(state: dict[str, Any]) -> dict[str, Any]:
    """G4/G10: relay a member-signed command, but force a safe-stop on any supervision breach.

    A safety command (:halt/:estop/:handback) is always permitted. An actuation command requires
    a member signature, refuses any server signature, and is dropped to a safe-stop if the deadman
    has lapsed or the latency budget is breached.
    """
    cs = _state(state)
    cs.command_kind = state.get("command_kind", cs.command_kind)
    cs.member_sig = state.get("member_sig", cs.member_sig)
    cs.server_sig = state.get("server_sig", cs.server_sig)
    cs.elapsed_since_presence_ms = state.get("elapsed_since_presence_ms", cs.elapsed_since_presence_ms)
    cs.observed_latency_ms = state.get("observed_latency_ms", cs.observed_latency_ms)

    if cs.server_sig:
        raise ValueError("G4 violation: server signature refused (no-server-key, ADR-2605231525)")

    verdict = _safe_state(cs)

    # Safety commands are always honoured, signature-free.
    if cs.command_kind in ALWAYS_PERMITTED:
        cs.phase = SessionPhase.SAFE_STOPPED.value if cs.command_kind != "handback" else SessionPhase.COMMAND_RELAYED.value
        cs.payload["command"] = {"kind": cs.command_kind, "safeState": verdict, "memberSigned": False}
        return {"cell_state": cs.__dict__, "next_node": "end"}

    # Actuation commands require a member signature (G4).
    if not cs.member_sig:
        raise ValueError("G4 violation: member signature required to relay an actuation command")

    # G10: a supervision breach forces a safe-stop/autonomy-fallback instead of actuating.
    if verdict != "nominal":
        cs.phase = SessionPhase.SAFE_STOPPED.value
        cs.payload["command"] = {
            "kind": "halt",
            "safeState": "autonomy-fallback" if verdict in ("deadman-lapse", "latency-breach") else verdict,
            "reason": verdict,
            "memberSigned": True,
        }
        return {"cell_state": cs.__dict__, "next_node": "end"}

    cs.phase = SessionPhase.COMMAND_RELAYED.value
    cs.payload["command"] = {
        "kind": cs.command_kind,
        "safeState": "nominal",
        "memberSigned": True,
        "serverSigned": False,
        "dryRun": True,        # G7: R0 is plan/replay only
        "onChainAnchored": True,  # G3/G11
    }
    return {"cell_state": cs.__dict__, "next_node": "end"}
