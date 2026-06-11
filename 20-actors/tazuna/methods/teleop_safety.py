"""tazuna (手綱) teleop-safety reasoner — stdlib only (ADR-2606042100).

The safety-critical core of the teleoperation control plane, kept pure and deterministic so it can be
unit-tested offline. It answers four questions for every relayed command, in priority order:

  1. force-class admission (N1) — is the robot's force class representable + force-authorized (G3)?
  2. no-server-key (G4)        — is the command member-signed, with NO server signature?
  3. soft-RT supervision (G10) — has the deadman lapsed or the latency budget been breached?
  4. safe verdict             — what safe_state should the command carry (nominal / deadman-lapse /
                                latency-breach / estopped / autonomy-fallback)?

This is best-effort SOFT-real-time supervision, NOT a certified (IEC 61508 / ISO 13849) safety
system; hard-RT and safety-rated live actuation are R5/Lv7+ (G10, kotoba-os N2 precedent). It never
emits a live actuation (G7): the verdict is advisory + replayable, and the cell drops to a safe-stop
on any breach.
"""

from __future__ import annotations

from dataclasses import dataclass

ADMITTED_FORCE_CLASSES = ("observational", "soft-actuation", "powered-actuation")
ALWAYS_PERMITTED = ("halt", "estop", "handback")  # safety commands; never gated, never signature-required
ACTUATION_KINDS = ("move", "manipulate")


class ForceClassError(ValueError):
    """N1 — the force class is unrepresentable (e.g. weaponizable / force-as-harm)."""


class TransparentForceError(ValueError):
    """G3 — no force-authorization reference (1 SBT=1 vote) admits this session."""


class NoServerKeyError(ValueError):
    """G4 — a server signature was presented, or a member signature is missing for actuation."""


@dataclass(frozen=True)
class Command:
    kind: str                       # move / manipulate / halt / estop / handback
    member_sig: str = ""
    server_sig: str = ""            # MUST be empty (G4)
    elapsed_since_presence_ms: int = 0
    observed_latency_ms: int = 0


@dataclass(frozen=True)
class Grant:
    force_class: str = "soft-actuation"
    force_auth_ref: str = ""        # required (G3)
    deadman_ms: int = 300
    latency_budget_ms: int = 150


@dataclass(frozen=True)
class SafetyVerdict:
    safe_state: str                 # nominal / deadman-lapse / latency-breach / estopped / autonomy-fallback
    actuates: bool                  # whether the actuation command is allowed to pass (always dry-run at R0)
    effective_kind: str             # the command actually relayed (a breach rewrites move -> halt)
    reason: str


def admit_session(grant: Grant) -> None:
    """N1 + G3: raise unless the force class is representable AND force-authorized. No return value."""
    if grant.force_class not in ADMITTED_FORCE_CLASSES:
        raise ForceClassError(
            f"N1: force class {grant.force_class!r} is unrepresentable; "
            "weaponizable / force-as-harm can never be admitted (Mission Charter §1.12)"
        )
    if not grant.force_auth_ref:
        raise TransparentForceError(
            "G3: Transparent Force requires a force-authorization reference "
            "(1 SBT=1 vote admission) before a teleop session is admitted"
        )


def evaluate(command: Command, grant: Grant) -> SafetyVerdict:
    """Return the safety verdict for one relayed command. Raises on N1/G3/G4 violations.

    Priority: e-stop > deadman lapse > latency breach > nominal. A safety command
    (halt/estop/handback) is always permitted and never requires a signature. An actuation command
    (move/manipulate) requires a member signature, refuses any server signature, and is rewritten to
    a safe-stop (effective_kind='halt', autonomy-fallback) on any supervision breach.
    """
    admit_session(grant)

    # G4: a server signature is always refused, for any command.
    if command.server_sig:
        raise NoServerKeyError(
            "G4: server signature refused — the platform never signs a physical-robot command "
            "(no-server-key, ADR-2605231525)"
        )

    # E-stop and other safety commands are always honoured.
    if command.kind == "estop":
        return SafetyVerdict("estopped", actuates=False, effective_kind="estop", reason="emergency stop")
    if command.kind in ("halt", "handback"):
        return SafetyVerdict("nominal", actuates=False, effective_kind=command.kind, reason="safety command")

    if command.kind not in ACTUATION_KINDS:
        raise ValueError(f"unknown command kind {command.kind!r}")

    # G4: actuation requires a member signature.
    if not command.member_sig:
        raise NoServerKeyError("G4: a member signature is required to relay an actuation command")

    # G10: soft-RT supervision — deadman first, then latency.
    if command.elapsed_since_presence_ms > grant.deadman_ms:
        return SafetyVerdict(
            "autonomy-fallback", actuates=False, effective_kind="halt",
            reason=f"deadman lapse ({command.elapsed_since_presence_ms}ms > {grant.deadman_ms}ms)",
        )
    if command.observed_latency_ms > grant.latency_budget_ms:
        return SafetyVerdict(
            "autonomy-fallback", actuates=False, effective_kind="halt",
            reason=f"latency breach ({command.observed_latency_ms}ms > {grant.latency_budget_ms}ms)",
        )

    # Nominal: the actuation passes — but still dry-run / outward-gated at R0 (G7).
    return SafetyVerdict("nominal", actuates=True, effective_kind=command.kind, reason="member-signed, in-budget")


if __name__ == "__main__":  # pragma: no cover — offline demo
    g = Grant(force_class="soft-actuation", force_auth_ref="forceauth:sanae-soft-001")
    for c in (
        Command("move", member_sig="m:sig", observed_latency_ms=40),
        Command("move", member_sig="m:sig", observed_latency_ms=400),
        Command("move", member_sig="m:sig", elapsed_since_presence_ms=900),
        Command("estop"),
    ):
        v = evaluate(c, g)
        print(f"{c.kind:>10}  ->  {v.safe_state:>18}  actuates={v.actuates}  ({v.reason})")
