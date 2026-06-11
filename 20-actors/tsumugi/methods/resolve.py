#!/usr/bin/env python3
"""tsumugi 紡ぎ — §D7.1 on-read latent-entity resolver (kotoba-EAVT native).

Replaces the RisingWave `vertex_lda_inference.ts` `vertex_latent_entity` logic with
pure stdlib aggregation over kotoba Datoms. Computes latent-entity existence as an
aggregate-first, method-versioned quantity FROM incident :en/evidence edges (G2
edge-primary / N1) — never a stored per-soul truth-score. Existence is a memoized,
reproducible projection, not authority.

CONSTITUTIONAL GATES:
  G1 power-only by construction — natural persons appear ONLY as :cohort/* aggregates,
     never as individual latent persons. This resolver operates on what was woven.
  G2 edge-primary (N1): existence is computed FROM incident :en/evidence edges, not
     a stored attribute. Existence = 1 - Π(1 - w_i) over edge weights, REPRODUCIBLE
     every run (deterministic sort by :organism/id, identical output).
  G6 Murakumo-only narration — this resolver does pure arithmetic, NO LLM call.
  非終末論: frontier never emits :fissioned/:suppressed. Fission = §D5 covenant claim
     (悔い改め・バプテスマ・得度 = social death/rebirth), Council Lv7+ gated, NO DID
     minted here, NO server key. This resolver only observes.

stdlib + no external dependencies. Usage:
    python3 resolve.py [woven.edn]     # default 20-actors/tsumugi/out/woven-graph
"""
from __future__ import annotations
import sys, pathlib, math
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analyze import read_edn  # reuse the EDN reader

ACTOR = pathlib.Path(__file__).resolve().parent.parent


def v(x):
    """Format a value for EDN output (ingest.py style)."""
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, str):
        return x if x.startswith(":") else f'"{x}"'
    return str(x)


def resolve_latent_entities(orgs: dict, edges: list) -> list:
    """
    Compute latent-entity existence via noisy-OR over incident :en/evidence edges.

    Returns a list of :latent/* datom dicts, sorted by :organism/id (deterministic).
    """
    latent_datoms = []

    # Collect latent organisms (unclaimed or standing=:latent)
    latent_org_ids = [
        org_id
        for org_id, org in orgs.items()
        if org.get(":organism/claimed?") is False or org.get(":organism/standing") == ":latent"
    ]

    # For each latent organism, collect incident evidence edges and compute existence
    for org_id in sorted(latent_org_ids):  # deterministic sort
        # Collect evidence edges where :en/to == org_id
        evidence_edges = [
            e
            for e in edges
            if e.get(":en/kind") == ":evidence" and e.get(":en/to") == org_id
        ]

        k = len(evidence_edges)  # evidence count

        if k == 0:
            # No evidence: frontier = :observed, existence = 0.0
            existence = 0.0
            viewpoint_consensus = 0
            frontier = ":observed"
        else:
            # Noisy-OR: existence = 1 - Π(1 - w_i)
            # Clamp weights to [0,1], default 0.0 if missing
            weights = []
            for e in evidence_edges:
                w_raw = e.get(":en/evidence-weight")
                if w_raw is None:
                    w = 0.0
                else:
                    w = float(w_raw)
                w = max(0.0, min(1.0, w))  # clamp to [0,1]
                weights.append(w)

            # Compute 1 - Π(1 - w_i)
            prod = 1.0
            for w in weights:
                prod *= (1.0 - w)
            existence = round(1.0 - prod, 4)

            # viewpoint_consensus: count DISTINCT :en/evidence-kind values
            viewpoints = set()
            for e in evidence_edges:
                kind = e.get(":en/evidence-kind")
                if kind is not None:
                    viewpoints.add(kind)
            viewpoint_consensus = len(viewpoints)

            # Frontier classification
            if existence >= 0.7 and viewpoint_consensus >= 2 and k >= 2:
                frontier = ":fission-ready"
            elif existence >= 0.4 and k >= 1:
                frontier = ":candidate"
            else:
                frontier = ":observed"

        # Emit :latent/* datom
        datom = {
            ":latent/organism": org_id,
            ":latent/existence": existence,
            ":latent/evidence-count": k,
            ":latent/viewpoint-consensus": viewpoint_consensus,
            ":latent/method-version": "latent-resolve/v1-noisy-or",
            ":latent/frontier": frontier,
        }
        latent_datoms.append(datom)

    return latent_datoms


def to_edn(datoms: list) -> str:
    """Serialize latent datoms to EDN format (ingest.py style)."""
    lines = [
        ";; tsumugi 紡ぎ — GENERATED latent-entity frontier (§D7.1 on-read resolver). DO NOT hand-edit.",
        ";; existence = aggregate-first, method-versioned, computed FROM incident :en/evidence edges (N1/G2).",
        "[",
    ]
    for d in datoms:
        pairs = []
        for k in [":latent/organism", ":latent/existence", ":latent/evidence-count",
                  ":latent/viewpoint-consensus", ":latent/method-version", ":latent/frontier"]:
            if k in d:
                pairs.append(f"{k} {v(d[k])}")
        lines.append("{" + " ".join(pairs) + "}")
    lines.append("]")
    return "\n".join(lines) + "\n"


def main():
    here = ACTOR

    # Parse argv[1] or use default
    if len(sys.argv) > 1:
        woven_path = pathlib.Path(sys.argv[1])
    else:
        woven_path = here / "out" / "woven-graph.kotoba.edn"

    if not woven_path.exists():
        sys.exit(f"ERROR: woven graph not found at {woven_path}")

    # Load woven graph
    data = read_edn(woven_path.read_text(encoding="utf-8"))
    orgs, edges = {}, []
    for m in data:
        if ":organism/id" in m:
            orgs[m[":organism/id"]] = m
        elif ":en/id" in m:
            edges.append(m)

    # Resolve latent entities
    latent_datoms = resolve_latent_entities(orgs, edges)

    # Classify by frontier
    by_frontier = {}
    for d in latent_datoms:
        f = d[":latent/frontier"]
        by_frontier.setdefault(f, []).append(d)

    fission_ready = len(by_frontier.get(":fission-ready", []))
    candidate = len(by_frontier.get(":candidate", []))
    observed = len(by_frontier.get(":observed", []))

    # Write output
    out = here / "out" / "latent-frontier.kotoba.edn"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(to_edn(latent_datoms), encoding="utf-8")

    # Print summary (matching ingest.py / analyze.py style)
    print(f"resolved {len(latent_datoms)} latent organisms: {fission_ready} fission-ready · {candidate} candidate · {observed} observed")
    print(f"✓ wrote {out}")
    print()
    print("HONEST FISSION NOTE (非終末論):")
    print("  :fission-ready does NOT fission. Fission = §D5 covenant claim (悔い改め·バプテスマ·得度):")
    print("  social death/rebirth. Council Lv7+ gated. NO DID minted here. NO server key.")
    print("  This resolver only OBSERVES.")


if __name__ == "__main__":
    main()
