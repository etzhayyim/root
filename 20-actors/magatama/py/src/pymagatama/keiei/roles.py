"""C-suite AI role registry — declarative SSoT.

Mirror of ADR 2605101200 §3-§4 in code. The LSP server reads this module
to advertise capabilities and gate decisions. Adding/removing a role here
is the only place that needs editing.

Operating entity = amanomibashira (sole principal). Vendor = Gftd Japan.
Per `deps.toml [platform.operating_entity]` + `[gftdcojp_agent.org_members]`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

DecisionClass = Literal["A", "B", "C", "D"]
RoleMode = Literal["shadow", "primary"]

PRINCIPAL_DID = "did:web:etz-hayim"
CEO_EMAIL = "j.kawasaki@gftd.co.jp"


@dataclass(frozen=True)
class CxoRole:
    id: str                                # "ceo" / "cto" / ...
    title: str                             # display
    mode: RoleMode                         # shadow (human seat) or primary (vacant)
    human_seat: str | None                 # email or None
    autonomous_classes: tuple[DecisionClass, ...]   # AI may execute without human-confirm
    confirm_classes: tuple[DecisionClass, ...]      # AI prepares; human confirms
    escalate_to: tuple[str, ...]           # emails to escalate Class A and gated B
    financial_action_gated: bool = False   # True → no autonomous spend ever
    payroll_gated: bool = False            # True → no autonomous payroll/comp/hire/fire
    methods: tuple[str, ...] = ("decide", "review", "state", "escalate")
    notes: str = ""


# ---------------------------------------------------------------------------
# Registry — order matters for $/listRoles output and ledger seq seeding.
# ---------------------------------------------------------------------------

ROLES: tuple[CxoRole, ...] = (
    CxoRole(
        id="ceo",
        title="Chief Executive (chief-of-staff to 河崎)",
        mode="shadow",
        human_seat=CEO_EMAIL,
        autonomous_classes=("C",),
        confirm_classes=("B",),
        escalate_to=(CEO_EMAIL,),
        notes="AI-CEO never speaks AS 河崎 to external counterparties. Aggregates signal, drafts responses, prepares decision packets.",
    ),
    CxoRole(
        id="coo",
        title="Chief Operating",
        mode="shadow",
        human_seat="a.nakamura@gftd.co.jp",
        autonomous_classes=("C",),
        confirm_classes=("B",),
        escalate_to=(CEO_EMAIL,),
    ),
    CxoRole(
        id="clo",
        title="Chief Legal",
        mode="shadow",
        human_seat="k.bakshi@gftd.co.jp",
        autonomous_classes=("C",),
        confirm_classes=("B",),
        escalate_to=(CEO_EMAIL,),
    ),
    CxoRole(
        id="cto",
        title="Chief Technology (vacant seat — primary mode)",
        mode="primary",
        human_seat=None,
        autonomous_classes=("C",),
        confirm_classes=("B",),                 # B = ops-level: 24h auto-disclose
        escalate_to=(CEO_EMAIL,),
        notes="a.oda 契約終了 2026-04-20. AI-CTO drives infra/ADR/migration decisions; CEO 河崎 ratifies Class B within 24h.",
    ),
    CxoRole(
        id="cfo",
        title="Chief Financial (vacant — financial-action gated)",
        mode="primary",
        human_seat=None,
        autonomous_classes=("C",),
        confirm_classes=("B",),
        escalate_to=(CEO_EMAIL, "a.nakamura@gftd.co.jp"),
        financial_action_gated=True,
        notes="MUST NOT initiate Stripe charges, wire transfers, payroll, or sign legal docs. Drafts only.",
    ),
    CxoRole(
        id="cmo",
        title="Chief Marketing (vacant)",
        mode="primary",
        human_seat=None,
        autonomous_classes=("C",),              # owned-channel post only
        confirm_classes=("B",),                 # paid spend → human confirm
        escalate_to=(CEO_EMAIL, "a.nakamura@gftd.co.jp"),
        notes="t.ichihara=Branding, k.takahashi=Creative — neither holds CMO seat. AI-CMO autonomous on owned-channel content only; paid spend gated.",
    ),
    CxoRole(
        id="chro",
        title="Chief Human Resources (vacant — payroll gated)",
        mode="primary",
        human_seat=None,
        autonomous_classes=("C",),
        confirm_classes=("B",),
        escalate_to=(CEO_EMAIL, "a.nakamura@gftd.co.jp"),
        payroll_gated=True,
        notes="No autonomous hiring/firing/comp changes. Internal comms + scheduling OK.",
    ),
    CxoRole(
        id="ciso",
        title="Chief Information Security",
        mode="shadow",
        human_seat="n.takahashi@gftd.works",
        autonomous_classes=("C",),
        confirm_classes=("B",),                 # incident disclosure = B with confirm
        escalate_to=(CEO_EMAIL, "n.takahashi@gftd.works"),
    ),
    CxoRole(
        id="cdo",
        title="Chief Design (creative direction)",
        mode="shadow",
        human_seat="k.takahashi@gftd.co.jp",
        autonomous_classes=("C",),
        confirm_classes=("B",),
        escalate_to=("k.takahashi@gftd.co.jp", CEO_EMAIL),
    ),
)


def by_id(role_id: str) -> CxoRole:
    for r in ROLES:
        if r.id == role_id:
            return r
    raise KeyError(f"unknown role: {role_id!r}")


# ---------------------------------------------------------------------------
# Decision-class gating (single source — used by lsp_server before exec)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GateVerdict:
    allowed: bool
    requires_human_confirm: bool
    must_escalate: bool
    reason: str


def gate(role: CxoRole, decision_class: DecisionClass, *, action_kind: str = "") -> GateVerdict:
    """Enforce ADR 2605101200 §4 hard rules. Caller MUST consult before executing."""

    # Rule 4: Class A always escalated, never autonomous.
    if decision_class == "A":
        return GateVerdict(False, False, True, "Class A — CEO 河崎 ratification required")

    # Rule 2: financial-action gate (CFO).
    if role.financial_action_gated and action_kind in {"spend", "charge", "wire", "payroll", "sign-legal"}:
        return GateVerdict(False, True, False, "financial action — CFO is draft-only, requires human confirm")

    # Payroll gate (CHRO).
    if role.payroll_gated and action_kind in {"hire", "fire", "comp-change", "payroll-run"}:
        return GateVerdict(False, True, False, "HR action — CHRO requires human confirm")

    if decision_class in role.autonomous_classes:
        return GateVerdict(True, False, False, "autonomous")

    if decision_class in role.confirm_classes:
        # Class B for primary-mode roles = autonomous-with-24h-auto-disclose;
        # for shadow-mode roles = blocking human confirm.
        if role.mode == "primary":
            return GateVerdict(True, False, False, "primary-mode B: autonomous, 24h auto-disclose")
        return GateVerdict(False, True, False, "shadow-mode B: human confirm required")

    return GateVerdict(False, False, True, f"class {decision_class!r} outside role authority")
