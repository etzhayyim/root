#!/usr/bin/env python3
"""hakoniwa 箱庭 — forward simulation kernel (Friedkin-Johnsen opinion dynamics over the box).

ADR-2606111500. Runs a CONTAINED miniature world of FICTIONAL latent personas forward in
discrete steps and produces an ENSEMBLE of trajectories. The spread of the ensemble's
population statistic IS the forecast distribution (computed in distribution.py) — hakoniwa
never asserts a single foretold future (G2 / 非終末論).

Kernel (per persona i, deterministic):
    x_i(t+1) = λ_i · Σ_j w_ij · x_j(t) + (1 - λ_i) · a_i
  where
    λ_i  = :persona/susceptibility (openness to influence),
    w_ij = incoming :influences weights, row-normalised over i's neighbours,
    a_i  = anchor = :persona/initial-stance + Σ active-signal pushes the persona is exposed to,
    x_i(0) = a_i (with signals not yet active).
  This converges to a fixed point. Signals activate at their :signal/at-step, shifting anchors.

Ensemble: K replicas. Replica r perturbs each persona's anchor by a DETERMINISTIC seeded
jitter (sha256 of f"{seed}:{r}:{persona_id}" → centred in [-amp, amp]) — NO Math.random, so
the run is byte-reproducible and pywasm-portable. The per-replica town-wide population
statistic is collected; their distribution is the output.

CONSTITUTIONAL:
  G1 — agents are synthetic archetypes (enforced at load by world.assert_synthetic).
  G2 — output is a distribution (distribution.py); this module returns the raw ensemble only.
  G3 — the simulation models stance diffusion for RESILIENCE planning; it is NOT a persuasion
    optimiser. There is no objective that maximises influence over real people, and no real
    people are in the box.

Pure stdlib (no numpy) — runnable inside a kotoba pywasm actor (componentize-py).
Usage:
    python3 simulate.py [scenario.edn] [--steps N] [--replicas K] [--seed S]
"""
from __future__ import annotations
import sys
import hashlib
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import world as W  # noqa: E402

DEFAULT_STEPS = 12
DEFAULT_REPLICAS = 64
DEFAULT_SEED = 7
DEFAULT_JITTER = 0.10  # anchor perturbation amplitude across replicas (the ensemble spread)
MAX_ITER = 200
TOL = 1.0e-6


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def _jitter(seed: int, replica: int, pid: str, amp: float) -> float:
    """Deterministic per-(replica, persona) anchor jitter in [-amp, amp]. No Math.random."""
    h = hashlib.sha256(f"{seed}:{replica}:{pid}".encode("utf-8")).digest()
    # take 4 bytes → [0,1) → centre to [-amp, amp]
    u = int.from_bytes(h[:4], "big") / float(1 << 32)
    return (u * 2.0 - 1.0) * amp


def build_topology(nodes: dict, edges: list):
    """Return (pids, susceptibility, base_anchor, weight, incoming, signal_push_by_persona).

    incoming[i] = list of (j, w_ij) row-normalised so Σ_j w_ij == 1 (empty → fully anchored).
    signal_push_by_persona[step] applied additively to anchors from a signal's at-step onward.
    """
    P = W.personas(nodes)
    pids = list(P.keys())  # EDN insertion order → deterministic
    sus = {i: float(P[i].get(":persona/susceptibility", 0.5)) for i in pids}
    base_anchor = {i: _clamp01(float(P[i].get(":persona/initial-stance", 0.5))) for i in pids}
    weight = {i: float(P[i].get(":persona/weight", 1.0)) for i in pids}

    raw_in = {i: [] for i in pids}
    for e in edges:
        if e.get(":en/kind") == ":influences":
            j, i = e.get(":en/from"), e.get(":en/to")
            if j in sus and i in sus:
                raw_in[i].append((j, float(e.get(":en/weight", 1.0))))
    incoming = {}
    for i, lst in raw_in.items():
        tot = sum(w for _, w in lst)
        incoming[i] = [(j, w / tot) for j, w in lst] if tot > 0 else []

    # signals: persona → list of (push, at_step) it is exposed to
    sig = W.signals(nodes)
    exposure = {i: [] for i in pids}
    for e in edges:
        if e.get(":en/kind") == ":exposed-to":
            i, s = e.get(":en/from"), e.get(":en/to")
            if i in exposure and s in sig:
                exposure[i].append((float(sig[s].get(":signal/push", 0.0)),
                                    int(sig[s].get(":signal/at-step", 0))))
    return pids, sus, base_anchor, weight, incoming, exposure


def _anchor_at_step(base: float, exposures: list, step: int, jit: float) -> float:
    a = base + jit
    for push, at in exposures:
        if step >= at:
            a += push
    return _clamp01(a)


def run_replica(pids, sus, base_anchor, incoming, exposure, steps, seed, replica, jitter):
    """One deterministic forward run; returns final stance vector x[i]."""
    jit = {i: _jitter(seed, replica, i, jitter) for i in pids}
    # initial state = anchor at step 0
    x = {i: _anchor_at_step(base_anchor[i], exposure[i], 0, jit[i]) for i in pids}
    for step in range(1, steps + 1):
        anchor = {i: _anchor_at_step(base_anchor[i], exposure[i], step, jit[i]) for i in pids}
        # iterate the FJ map to its fixed point within this step (inner relaxation)
        for _ in range(MAX_ITER):
            nx = {}
            for i in pids:
                nbr = sum(w * x[j] for j, w in incoming[i])
                lam = sus[i] if incoming[i] else 0.0  # no neighbours → fully anchored
                nx[i] = _clamp01(lam * nbr + (1.0 - lam) * anchor[i])
            delta = max(abs(nx[i] - x[i]) for i in pids)
            x = nx
            if delta < TOL:
                break
    return x


def population_statistic(x: dict, weight: dict, member_ids=None) -> float:
    """Aggregate-first readout: population weighted-mean final stance (G1 — never per-persona)."""
    ids = member_ids if member_ids is not None else list(x.keys())
    wsum = sum(weight[i] for i in ids)
    if wsum <= 0:
        return 0.0
    return sum(weight[i] * x[i] for i in ids) / wsum


def ensemble(nodes: dict, edges: list, steps=DEFAULT_STEPS, replicas=DEFAULT_REPLICAS,
             seed=DEFAULT_SEED, jitter=DEFAULT_JITTER):
    """Return (outcomes_per_replica, meta). outcomes is a list[float] of the town-wide statistic."""
    pids, sus, base_anchor, weight, incoming, exposure = build_topology(nodes, edges)
    # which personas the outcome measures (default :all)
    outs = W.outcomes(nodes)
    member_ids = None
    if outs:
        first = next(iter(outs.values()))
        if first.get(":outcome/measures") != ":all":
            member_ids = pids  # only :all is wired in R0; named-population is a future facet
    results = []
    for r in range(replicas):
        x = run_replica(pids, sus, base_anchor, incoming, exposure, steps, seed, r, jitter)
        results.append(population_statistic(x, weight, member_ids))
    meta = {"personas": len(pids), "edges": len(edges), "steps": steps,
            "replicas": replicas, "seed": seed, "jitter": jitter}
    return results, meta


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    scenario = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else here / "data" / "seed-scenario.kotoba.edn"

    def opt(flag, default, cast):
        return cast(argv[argv.index(flag) + 1]) if flag in argv else default

    steps = opt("--steps", DEFAULT_STEPS, int)
    replicas = opt("--replicas", DEFAULT_REPLICAS, int)
    seed = opt("--seed", DEFAULT_SEED, int)

    nodes, edges = W.load(scenario)
    results, meta = ensemble(nodes, edges, steps=steps, replicas=replicas, seed=seed)
    mean = sum(results) / len(results)
    print(f"hakoniwa: {meta['personas']} synthetic personas, {meta['edges']} 縁, "
          f"{steps} steps × {replicas} replicas → ensemble mean {mean:.4f}")
    print("  (distribution-only output via distribution.py — never a point assertion, G2)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
