"""bridge.py — 高札 (kosatsu) cross-actor SoS composition. ADR-2606072000.

kosatsu is the competing-claim BOARD; the SoS intel value comes from composing its divergence
view with the sibling accountability/intel actors over the SHARED kotoba Datom log. This module
computes the JOIN KEYS kosatsu exposes so a downstream actor can link a designation subject to
its other observations — WITHOUT kosatsu reaching into another actor's graph (each actor owns
its own datoms; bridge only emits the keys).

  - tadori 辿   : a :designated-wallet subject → on-chain attribution case (authorized only)
  - keizu 系図  : a :designated-org/entity subject → public power-relations node (if public role)
  - tsumugi 紡ぎ: a subject's asserter → power-entity 縁 (who designates whom, as influence)
  - kanae 鼎    : the by-authority / divergence aggregates → fiscal/atlas render
  - tasuke 助   : never — a victim-support flow is person-consented, disjoint (no auto-link)

The bridge is MAP-ONLY (G9): it surfaces a join key for resilience/awareness/due-process, never
an enforcement instruction. It NEVER promotes a contested designation to a verdict.

Stdlib only. Deterministic.
"""

from __future__ import annotations

from weave import divergence, status_as_of

# subject kind → the sibling actor that can further observe it (join target). Person/org subjects
# only bridge to a PUBLIC-role actor when they are already a public power role (keizu's own G1
# decides admissibility downstream); kosatsu only emits the key, never the link.
BRIDGE_TARGETS = {
    "designated-wallet": "tadori",
    "designated-domain": "tadori",
    "designated-org": "keizu",
    "designated-entity": "keizu",
}


def join_keys(g: dict, ts: int | None = None) -> list[dict]:
    """For each currently-LISTED-by-someone subject, emit a cross-actor join key + its divergence
    class. Delisted-everywhere / silent subjects are skipped (nothing live to compose). The key
    is advisory routing only (G9)."""
    out = []
    subjects = g["subjects"]
    for sid, s in subjects.items():
        div = divergence(g, sid, ts)
        if not div["listing"]:          # nobody currently lists it → no live composition
            continue
        kind = str(s.get(":subject/kind", "")).lstrip(":")
        target = BRIDGE_TARGETS.get(kind)
        out.append({
            "subject": sid,
            "subject_kind": kind,
            "divergence_class": div["class"],
            "listing_asserters": div["listing"],
            "bridge_to": target,                 # None when no sibling observes this kind
            "note": "advisory join key for SoS awareness; never an enforcement instruction (G9)",
        })
    return sorted(out, key=lambda x: (x["bridge_to"] or "~", x["subject"]))


def tsumugi_en_edges(g: dict, ts: int | None = None) -> list[dict]:
    """tsumugi 縁 projection: each currently-listed designation is an asserter→subject INFLUENCE
    edge (who exercises designating power over whom). Edge-primary, attributed; never a per-node
    score. Feeds tsumugi's power-entity 縁 weave."""
    out = []
    for d in g["designations"]:
        sub, ass = d.get(":designation/subject"), d.get(":designation/asserter")
        if status_as_of(g, sub, ass, ts) == "listed":
            out.append({
                "from": ass, "to": sub, "kind": "designation-power",
                "measure": str(d.get(":designation/measure", "")).lstrip(":"),
                "as_of": d.get(":designation/posted-at"),
            })
    return sorted(out, key=lambda x: (x["from"], x["to"]))


if __name__ == "__main__":
    import pathlib
    from _edn import load_edn
    from weave import weave

    seed = load_edn(pathlib.Path(__file__).resolve().parents[1] / "data" / "seed-designation-graph.kotoba.edn")
    g = weave(seed)
    print("# kosatsu cross-actor join keys (advisory, G9)\n")
    for k in join_keys(g):
        print(f"- {k['subject']} [{k['divergence_class']}] kind={k['subject_kind']} → {k['bridge_to']} "
              f"(listed by {k['listing_asserters']})")
    print(f"\n# tsumugi 縁 edges: {len(tsumugi_en_edges(g))} designation-power edges")
