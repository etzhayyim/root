#!/usr/bin/env python3
"""grasp_render — 取-concentration aggregate render-spec for kanae.

ADR-2606011000 §D2/§D7 + ADR-2605302300 (kanae render-only, aggregate-first).

Turns `:grasp/*` datoms (from engi_ingest) into a kanae-style render spec (treemap of
取-集中 — "who/what grasps the earth") that kanae's WASM renderer can draw, the same
way it draws fundFlowEdge Sankey/treemaps. NON-ADJUDICATING: it surfaces concentration
so it can be routed to release (Tithe / Land Trust / ladder); it makes no accusation.

FLOOR (mirrors kanae aggregate-first + ADR-2605310100 §4(2)):
  R1  Named nodes are CLAIMED members only (covenant-visible, 2605310100 §1–§2).
  R2  The latent remainder is a SINGLE anonymous aggregate node — never per-identity.
  R3  Member tiers below the k-anonymity floor K collapse into an aggregate tier node,
      so a small named cohort is never singled out as a leaderboard (kanae §7 anti-class
      / ADR-2605301020 no-leaderboard).

Run:   python3 grasp_render.py
Test:  python3 test_grasp_render.py
"""
from __future__ import annotations

import json

K_ANON = 3  # R3: a named tier must contain ≥ K members, else it aggregates.


def render_spec(grasp_datoms: list[dict], latent_aggregate: dict,
                k_anon: int = K_ANON) -> dict:
    """Build an aggregate treemap render spec from :grasp datoms + the latent aggregate.

    grasp_datoms: list of {:grasp/organism, :grasp/concentration, :grasp/load,
                  :grasp/release-path}  (members only — engi_ingest guarantees this).
    latent_aggregate: {"latent-organism-count", "latent-incident-edges"}.
    """
    members = [g for g in grasp_datoms if ":grasp/organism" in g]
    members.sort(key=lambda g: g.get(":grasp/concentration", 0.0), reverse=True)

    total_member_conc = sum(g.get(":grasp/concentration", 0.0) for g in members)
    nodes: list[dict] = []

    # R3: split into a "named" head (each its own node) and a small-cohort tail that
    # aggregates. We name a member only if at least k_anon members share its concentration
    # band OR it sits in a head large enough to not single anyone out.
    if len(members) >= k_anon:
        head = members  # cohort large enough; naming members is covenant-visible (R1)
        for g in head:
            conc = g.get(":grasp/concentration", 0.0)
            nodes.append({
                "id": g[":grasp/organism"],
                "label": g[":grasp/organism"],
                "value": conc,
                "load": g.get(":grasp/load", 0.0),
                "kind": "member",
                "release_path": g.get(":grasp/release-path", "[]"),
                "suggest_release": conc >= _release_threshold(members),
            })
    elif members:
        # too few to name without singling out → one aggregate node (R3).
        nodes.append({
            "id": "grasp.member-aggregate",
            "label": f"members (aggregate, n={len(members)})",
            "value": total_member_conc,
            "load": round(sum(g.get(":grasp/load", 0.0) for g in members), 3),
            "kind": "member-aggregate",
            "suggest_release": False,
        })

    # R2: latent remainder = a single anonymous node, never per-identity.
    lat_n = latent_aggregate.get("latent-organism-count", 0)
    if lat_n:
        nodes.append({
            "id": "grasp.latent-aggregate",
            "label": f"latent organisms (anonymous, n={lat_n})",
            "value": float(latent_aggregate.get("latent-incident-edges", 0)),
            "kind": "latent-aggregate",
            "suggest_release": False,
        })

    return {
        "type": "treemap",
        "title": "取-集中 (grasping concentration) — non-adjudicating; route to release",
        "method_version": next((g.get(":grasp/method-version") for g in grasp_datoms
                                if g.get(":grasp/method-version")), None),
        "k_anon": k_anon,
        "total_member_concentration": round(total_member_conc, 3),
        "nodes": nodes,
        "disclaimer": ("Aggregate-first. Named nodes are consenting covenant members; "
                       "latent organisms appear only as one anonymous aggregate. "
                       "Concentration is surfaced to route 取 to release, not to accuse."),
    }


def _release_threshold(members: list[dict]) -> float:
    """Suggest release for the top concentration band (>= 80th percentile)."""
    if not members:
        return float("inf")
    concs = sorted(g.get(":grasp/concentration", 0.0) for g in members)
    idx = max(0, int(0.8 * (len(concs) - 1)))
    return concs[idx]


if __name__ == "__main__":
    import engi_ingest as ei
    from engi_ingest import Follow
    members = {"did:plc:alice", "did:plc:bob", "did:plc:erin", "did:plc:frank"}
    follows = [
        Follow("did:plc:alice", "did:plc:bob"),
        Follow("did:plc:erin", "did:plc:bob"),
        Follow("did:plc:frank", "did:plc:bob"),
        Follow("did:plc:alice", "did:plc:erin"),
        Follow("did:plc:carol", "did:plc:bob"),   # carol latent
        Follow("did:plc:dave", "did:plc:erin"),    # dave latent
    ]
    res = ei.ingest(follows, members)
    spec = render_spec(list(res.grasp.values()), res.latent_aggregate)
    print(json.dumps(spec, indent=2, ensure_ascii=False))
