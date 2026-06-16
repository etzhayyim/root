#!/usr/bin/env python3
"""torifune 鳥船 — civilian ascent / staging GNC sim over the launch-vehicle graph.

ADR-2606162355. Reads a kotoba-EDN launch-vehicle graph (:organism/* nodes + :en/* 縁 over
the launch-vehicle-ontology) and computes — deterministically, pure stdlib — the staged
Tsiolkovsky Δv budget, the payload-to-orbit margin against the target regime, and the per-stage
breakdown. This is the engineering core the other methods import.

CONSTITUTIONAL (read before any change):
  G1 — CIVILIAN LAUNCH ONLY, NEVER a weapon-delivery / ballistic-strike vehicle. The trajectory
    class is restricted to {:ascent :orbit-insertion :rendezvous :deorbit} and the payload class
    to civilian classes — strike trajectories and munition/kinetic payloads are UNREPRESENTABLE
    (validated by check_g1 + the seed). No targeting, no impact-point solver exists here.
  G8 — sourcing honesty. Numbers are representative engineering estimates, never measured flight
    data (no Ama flight campaign exists; that is Council-gated).

Pure stdlib (no numpy) — runnable inside a kotoba pywasm actor (componentize-py).
Usage:
    python3 ascent_sim.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys, re, math, pathlib

# ── minimal EDN reader (subset: vectors [], maps {}, :keyword, "string", num, bool, nil)
_TOK = re.compile(r'[\s,]+|;[^\n]*|(\[|\]|\{|\}|"(?:\\.|[^"\\])*"|[^\s,\[\]{}]+)')


def _tokens(s: str):
    for m in _TOK.finditer(s):
        t = m.group(1)
        if t is not None:
            yield t


def _atom(t: str):
    if t.startswith('"'):
        return t[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    if t == 'true':  return True
    if t == 'false': return False
    if t == 'nil':   return None
    if t.startswith(':'):
        return t
    try:
        return int(t)
    except ValueError:
        try:
            return float(t)
        except ValueError:
            return t


_END = object()


def _parse(it):
    t = next(it)
    if t == '[':
        out = []
        while (x := _parse(it)) is not _END:
            out.append(x)
        return out
    if t == '{':
        out = {}
        while (k := _parse(it)) is not _END:
            out[k] = _parse(it)
        return out
    if t in (']', '}'):
        return _END
    return _atom(t)


def read_edn(text: str):
    return _parse(_tokens(text))


# ── constants ────────────────────────────────────────────────────────────────
G0 = 9.80665  # standard gravity, m/s^2

# representative Δv-to-orbit (m/s, incl. gravity + drag + steering losses) per regime — G8
REGIME_DV = {":leo-low": 9400.0, ":leo-high": 9600.0, ":sso": 9700.0,
             ":meo": 11000.0, ":geo": 13000.0, ":heo": 12000.0}

# G1 — the ONLY admissible trajectory + payload classes (no strike / munition member)
CIVILIAN_TRAJ = {":ascent", ":orbit-insertion", ":rendezvous", ":deorbit"}
CIVILIAN_PAYLOAD = {":connectivity-sat", ":earth-observation-sat", ":science",
                    ":crewed", ":cargo"}
# attributes that would turn the sim into a weapon — must never appear (G1)
BANNED_ATTRS = (":traj/impact-point", ":traj/depressed", ":payload/yield",
                ":payload/warhead", ":guidance/terminal", ":target/coords")


def load(path: pathlib.Path):
    """Return (nodes_by_id, edges) from a launch-vehicle EDN graph."""
    forms = read_edn(path.read_text(encoding="utf-8"))
    nodes, edges = {}, []
    for f in forms:
        if not isinstance(f, dict):
            continue
        if ":organism/id" in f:
            nodes[f[":organism/id"]] = f
        elif ":en/from" in f and ":en/to" in f:
            edges.append(f)
    return nodes, edges


def check_g1(nodes: dict):
    """G1: civilian launch only — strike trajectories / munition payloads unrepresentable.

    Raises ValueError on any non-civilian trajectory/payload class or banned weapon attribute.
    """
    for nid, n in nodes.items():
        for b in BANNED_ATTRS:
            if b in n:
                raise ValueError(f"G1 violation: weapon attribute {b} on {nid}")
        if n.get(":organism/kind") == ":trajectory":
            cls = n.get(":traj/class")
            if cls not in CIVILIAN_TRAJ:
                raise ValueError(f"G1 violation: non-civilian trajectory class {cls} on {nid}")
        if n.get(":organism/kind") == ":payload":
            cls = n.get(":payload/class")
            if cls not in CIVILIAN_PAYLOAD:
                raise ValueError(f"G1 violation: non-civilian payload class {cls} on {nid}")
    return True


def _engine_for_stage(nodes, edges, stage_id):
    """The engine that :powers a given stage (its Isp drives the stage Δv)."""
    for e in edges:
        if e.get(":en/kind") == ":powers" and e.get(":en/to") == stage_id:
            return nodes.get(e.get(":en/from"))
    return None


def simulate(nodes: dict, edges: list):
    """Staged Tsiolkovsky Δv (computed on read; transient — N1).

    For an N-stage serial vehicle, stage k burns with all higher stages + payload as inert mass:
        m0_k = Σ_{i>=k}(dry_i + prop_i) + payload
        mf_k = dry_k + Σ_{i>k}(dry_i + prop_i) + payload
        dv_k = Isp_k * g0 * ln(m0_k / mf_k)
    """
    check_g1(nodes)
    stages = sorted((n for n in nodes.values() if n.get(":organism/kind") == ":stage"),
                    key=lambda s: s.get(":stage/index", 0))
    # the mission payload mass (single mission seed)
    mission = next((n for n in nodes.values() if n.get(":organism/kind") == ":mission"), None)
    payload_kg = float(mission.get(":mission/payload-to-orbit-kg", 0.0)) if mission else 0.0
    target = mission.get(":mission/target-regime") if mission else None

    # mass above stage k (higher-index stages + payload), built from the top down
    above = payload_kg
    per_stage = []
    masses = [(float(s.get(":stage/dry-mass-kg", 0.0)),
               float(s.get(":stage/prop-mass-kg", 0.0)), s) for s in stages]
    # accumulate "above" for each stage from the top
    above_of = [0.0] * len(masses)
    acc = payload_kg
    for k in range(len(masses) - 1, -1, -1):
        above_of[k] = acc
        acc += masses[k][0] + masses[k][1]

    total_dv = 0.0
    for k, (dry, prop, s) in enumerate(masses):
        eng = _engine_for_stage(nodes, edges, s[":organism/id"])
        isp = float(eng.get(":engine/isp-s", 0.0)) if eng else 0.0
        m0 = dry + prop + above_of[k]
        mf = dry + above_of[k]
        dv = isp * G0 * math.log(m0 / mf) if mf > 0 and m0 > mf else 0.0
        total_dv += dv
        per_stage.append({"stage": s[":organism/id"],
                          "label": s.get(":organism/label", s[":organism/id"]),
                          "isp_s": isp, "dv_ms": dv, "m0_kg": m0, "mf_kg": mf})

    required = REGIME_DV.get(target, 9400.0)
    return {"per_stage": per_stage, "total_dv_ms": total_dv,
            "required_dv_ms": required, "dv_margin_ms": total_dv - required,
            "payload_kg": payload_kg, "target_regime": target}


def report_md(nodes: dict, edges: list, res: dict) -> str:
    L = []
    L.append("# torifune 鳥船 — Ama 天-class ascent / Δv report (civilian launch)\n")
    L.append("> **G1 — CIVILIAN LAUNCH ONLY, NEVER a weapon-delivery / ballistic-strike "
             "vehicle.** Trajectory class ∈ {ascent, orbit-insertion, rendezvous, deorbit}; "
             "payload class is civilian; strike trajectories + munition payloads are "
             "unrepresentable. **G2** propellant is zero-net-carbon. **G8** numbers are "
             "representative engineering estimates, never measured flight data.\n")
    tgt = (res["target_regime"] or "—").lstrip(":")
    L.append(f"**Mission**: {res['payload_kg']:.0f} kg → {tgt} · "
             f"required Δv ≈ {res['required_dv_ms']:.0f} m/s\n")
    L.append("\n## Staged Δv budget (Tsiolkovsky, computed on read)\n")
    L.append("| stage | Isp (s) | m₀ (kg) | m_f (kg) | Δv (m/s) |")
    L.append("|---|---:|---:|---:|---:|")
    for s in res["per_stage"]:
        L.append(f"| {s['label']} | {s['isp_s']:.0f} | {s['m0_kg']:.0f} | "
                 f"{s['mf_kg']:.0f} | {s['dv_ms']:.0f} |")
    L.append(f"| **total** | | | | **{res['total_dv_ms']:.0f}** |")
    margin = res["dv_margin_ms"]
    verdict = "✅ orbit achievable" if margin > 0 else "❌ insufficient Δv"
    L.append(f"\n**Δv margin to {tgt}: {margin:+.0f} m/s** — {verdict} "
             "(reusable reserve folds into this margin).\n")
    L.append("\n---\n_torifune 鳥船 · ADR-2606162355 · civilian-launch-only · "
             "weapon-unrepresentable · zero-net-carbon · representative estimates. Actual "
             "launch operation is Council + operator-DID gated (no-server-key)._\n")
    return "\n".join(L)


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-ama-vehicle.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    outdir.mkdir(parents=True, exist_ok=True)

    nodes, edges = load(seed)
    res = simulate(nodes, edges)
    (outdir / "ascent-report.md").write_text(report_md(nodes, edges, res), encoding="utf-8")
    print(f"torifune: {len(nodes)} nodes, {len(edges)} 縁 → {outdir/'ascent-report.md'}")
    print(f"  total Δv {res['total_dv_ms']:.0f} m/s, margin {res['dv_margin_ms']:+.0f} m/s "
          f"to {(res['target_regime'] or '—').lstrip(':')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
