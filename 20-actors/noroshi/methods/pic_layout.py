"""noroshi (烽) photonic-IC layout generator (ADR-2606051600 §R1b). Stdlib only (gdsfactory optional).

Generates a silicon-photonic transmitter PIC as a neutral **ModelOp plan** — an ordered list of
components, ports, and waveguide routes (the sumitsubo CAD `ModelOp` pattern) — and closes the loop
back to `link_budget.py`: the plan's total on-chip waveguide length feeds the link budget, so a layout
change is immediately reflected in the optical margin.

Clean-room open-EDA (G1/N5): the layout vocabulary is GDSFactory-shaped (component/port/route), and IF
`gdsfactory` is importable the plan is built into a real `Component` and a GDS is written. It is NEVER
required, NEVER a proprietary tool, and the GDS *write* is outward-gated (G8) — at R0 the verifiable
deliverable is the deterministic plan, not a fabricable mask. No NDA foundry PDK (G1).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from link_budget import LinkDesign, compute


@dataclass(frozen=True)
class ModelOp:
    """One layout operation: place a component, or route a waveguide between two ports."""

    op: str                       # "place" | "route"
    name: str
    kind: str = ""                # for place: laser / mzm / grating_coupler / waveguide / photodetector
    x_um: float = 0.0
    y_um: float = 0.0
    length_um: float = 0.0        # for route: waveguide length
    ports: tuple = ()             # for route: (from_port, to_port)


@dataclass(frozen=True)
class PicPlan:
    name: str
    ops: list
    total_waveguide_um: float
    components: list = field(default_factory=list)


# A minimal Tx PIC: laser → MZM modulator → routing waveguide → grating coupler (off-chip).
def transmitter_plan(name: str = "noroshi-tx-pic", route_um: float = 1500.0) -> PicPlan:
    if route_um <= 0:
        raise ValueError("route_um (modulator→coupler waveguide length) must be positive")
    ops = [
        ModelOp("place", "laser0", kind="laser", x_um=0.0, y_um=0.0),
        ModelOp("place", "mzm0", kind="mzm", x_um=200.0, y_um=0.0),
        ModelOp("place", "gc0", kind="grating_coupler", x_um=200.0 + route_um, y_um=0.0),
        ModelOp("route", "wg_laser_mzm", length_um=200.0, ports=("laser0.o", "mzm0.i")),
        ModelOp("route", "wg_mzm_gc", length_um=route_um, ports=("mzm0.o", "gc0.i")),
    ]
    total_wg = sum(o.length_um for o in ops if o.op == "route")
    comps = [o.name for o in ops if o.op == "place"]
    return PicPlan(name=name, ops=ops, total_waveguide_um=total_wg, components=comps)


# A minimal Rx PIC: grating coupler (off-chip in) → routing waveguide → photodetector.
def receiver_plan(name: str = "noroshi-rx-pic", route_um: float = 1000.0) -> PicPlan:
    if route_um <= 0:
        raise ValueError("route_um (coupler→photodetector waveguide length) must be positive")
    ops = [
        ModelOp("place", "gc_in", kind="grating_coupler", x_um=0.0, y_um=0.0),
        ModelOp("place", "pd0", kind="photodetector", x_um=route_um, y_um=0.0),
        ModelOp("route", "wg_gc_pd", length_um=route_um, ports=("gc_in.o", "pd0.i")),
    ]
    total_wg = sum(o.length_um for o in ops if o.op == "route")
    comps = [o.name for o in ops if o.op == "place"]
    return PicPlan(name=name, ops=ops, total_waveguide_um=total_wg, components=comps)


def plan_to_link_design(plan: PicPlan, base: LinkDesign | None = None) -> LinkDesign:
    """Feed the plan's on-chip waveguide length into a link budget (the layout→budget loop)."""
    base = base or LinkDesign()
    tx_wg_cm = plan.total_waveguide_um / 1e4   # µm → cm
    return LinkDesign(
        name=f"{plan.name}-budget",
        tx_waveguide_cm=tx_wg_cm,
        rx_waveguide_cm=base.rx_waveguide_cm,
    )


def full_link_design(tx_plan: PicPlan, rx_plan: PicPlan, base: LinkDesign | None = None) -> LinkDesign:
    """Compose BOTH on-chip waveguide lengths (tx + rx PIC) into one end-to-end link design."""
    base = base or LinkDesign()
    return LinkDesign(
        name=f"{tx_plan.name}+{rx_plan.name}-budget",
        tx_waveguide_cm=tx_plan.total_waveguide_um / 1e4,
        rx_waveguide_cm=rx_plan.total_waveguide_um / 1e4,
    )


def try_build_gds(plan: PicPlan, out_path: str = "out/noroshi-tx-pic.gds") -> dict:
    """Build a real GDS via gdsfactory IF available; otherwise return a gated, honest stub result.

    The GDS write is outward-gated (G8) and only attempted when the open-source gdsfactory is
    importable — never a proprietary EDA tool, never a bundled NDA PDK (G1/N5).
    """
    try:
        import gdsfactory as gf  # noqa: F401  (optional open-EDA backend)
    except Exception as exc:  # ImportError or environment error
        return {
            "built": False,
            "reason": f"gdsfactory not available ({type(exc).__name__}); GDS write gated (G8) — "
                      "the verifiable R0 artifact is the ModelOp plan, not a mask",
            "components": plan.components,
        }
    c = gf.Component(plan.name)
    refs = {}
    for op in plan.ops:
        if op.op == "place":
            comp = {
                "laser": gf.components.straight,        # placeholder open-PDK primitives
                "mzm": gf.components.mzi,
                "grating_coupler": gf.components.grating_coupler_elliptical,
                "photodetector": gf.components.straight,
            }.get(op.kind, gf.components.straight)
            refs[op.name] = c.add_ref(comp())
            refs[op.name].move((op.x_um, op.y_um))
    c.write_gds(out_path)
    return {"built": True, "path": out_path, "components": plan.components}


def report() -> str:
    tx, rx = transmitter_plan(), receiver_plan()
    budget = compute(full_link_design(tx, rx))
    gds = try_build_gds(tx)
    lines = ["# noroshi 烽 — photonic-IC layout (open-EDA / GDSFactory-shaped ModelOp plan)", ""]
    for plan, role in ((tx, "transmitter"), (rx, "receiver")):
        lines += [
            f"## {role} plan: {plan.name}",
            f"- components       : {', '.join(plan.components)}",
            f"- total waveguide  : {plan.total_waveguide_um:.0f} µm ({plan.total_waveguide_um/1e4:.3f} cm)",
            "- ops:",
        ]
        for o in plan.ops:
            if o.op == "place":
                lines.append(f"  - place {o.name} ({o.kind}) @ ({o.x_um:.0f},{o.y_um:.0f}) µm")
            else:
                lines.append(f"  - route {o.name}: {o.ports[0]} → {o.ports[1]}  ({o.length_um:.0f} µm)")
        lines.append("")
    lines += [
        "## end-to-end layout → link budget (tx + rx waveguide, the closed loop)",
        f"- both PIC waveguides → received {budget.received_dbm} dBm, "
        f"margin {budget.margin_db} dB → {'CLOSES' if budget.closes else 'FAILS'}",
        "",
        "## GDS write (open-EDA backend, outward-gated G8)",
        f"- {'built ' + gds['path'] if gds.get('built') else gds['reason']}",
        "",
        "> R0 verifiable artifact = the deterministic ModelOp plan + the layout→budget loop. "
        "The GDS write runs only with the open-source gdsfactory installed and is G8-gated; "
        "no proprietary EDA, no NDA foundry PDK (G1/N5).",
    ]
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover — offline demo
    print(report())
