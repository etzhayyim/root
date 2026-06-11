#!/usr/bin/env python3
"""kamado 竈 — feedstock-class guard (G1 enforcement point #3 of 3).

ADR-2606051500. The structural invariant, mirrored on nusa's `:thc-class` guard:
a refining feedstock MUST be closed-loop carbon. `:fossil-virgin-crude` is NOT a
representable value — the schema enum, the lexicon `const`, and this guard all refuse
it, so kamado cannot, by construction, operate a fossil-fed refinery (which is what
makes "automate a fossil refinery" impossible rather than merely discouraged).

This is the honest answer made structural: since robotics cannot neutralize fossil
carbon (carbon_balance.py), the only harm-free path is to forbid the fossil feedstock.

stdlib only; importable by analyze.py and unit-tested.
"""
from __future__ import annotations

# G1: the ONLY representable feedstock classes. Anything else is a charter violation.
ALLOWED_FEEDSTOCK = (":biogenic", ":captured-co2", ":recycled-carbon",
                     ":existing-inventory-decommission")

# G3: the ONLY representable intervention kinds on an EXISTING fossil asset. Life-extension
# of a fossil unit (:expand / :restart-fossil / :revamp-throughput) is unrepresentable.
ALLOWED_INTERVENTION = (":decommission", ":remediate", ":convert", ":monitor")


def _norm(v) -> str:
    return (v or "").lstrip(":") if isinstance(v, str) else str(v)


def screen_feedstock(feedstock: str, ctx: str = "") -> str:
    """G1: refuse any feedstock that is not closed-loop carbon. Returns the keyword."""
    fk = feedstock if isinstance(feedstock, str) and feedstock.startswith(":") else f":{_norm(feedstock)}"
    if fk not in ALLOWED_FEEDSTOCK:
        raise ValueError(
            f"G1 violation{f' ({ctx})' if ctx else ''}: feedstock-class {feedstock!r} is not "
            f"representable. kamado refines closed-loop carbon ONLY {ALLOWED_FEEDSTOCK}; "
            f"`:fossil-virgin-crude` and any fossil-extracted feedstock are excluded by "
            f"construction (robotics cannot neutralize fossil carbon — only the feedstock can)."
        )
    return fk


def screen_intervention(kind: str, ctx: str = "") -> str:
    """G3: an EXISTING fossil asset may only be wound down/converted, never extended."""
    ik = kind if isinstance(kind, str) and kind.startswith(":") else f":{_norm(kind)}"
    if ik not in ALLOWED_INTERVENTION:
        raise ValueError(
            f"G3 violation{f' ({ctx})' if ctx else ''}: intervention {kind!r} is not "
            f"representable. kamado may only {ALLOWED_INTERVENTION} an existing fossil asset "
            f"(§2(d) — decommission/transition only; never expand/restart/extend a fossil unit)."
        )
    return ik
