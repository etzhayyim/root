#!/usr/bin/env python3
"""tsumugi 紡ぎ — P2 latent-entity topic derivation (kotoba-EAVT native).

Derives LDA-style :topic/* nodes + :en/kind :topic-binding edges from the
evidence graph. Pure-stdlib deterministic resolver (R0 viewpoint-cluster stand-in
for full Gibbs-sampling LDA; P2-full Pregel cell deferred).

For each distinct :en/evidence-kind viewpoint in the evidence edges, emits:
  1. A :topic/* node with :topic/id, :topic/label, :topic/coherence, :topic/viewpoint
  2. Topic-binding :en/* edges from the topic to each entity bearing evidence of that
     viewpoint (G2 edge-primary / N1, no per-soul score)

CONSTITUTIONAL GATES:
  G2 edge-primary (N1): topics and bindings are computed FROM incident :en/evidence
     edges, deterministic per run. No stored topic-existence per entity.
  G6 Murakumo-only: no LLM call (this is pure arithmetic; Murakumo-only applies if
     narration is ever added, P2-full deferred).
  G4 no intent adjudication: topics are DESCRIPTIVE (evidence viewpoints), never
     explanatory or attributory. No LLM interpretation.

stdlib + no external dependencies. Usage:
    python3 topics.py [woven.edn]     # default 20-actors/tsumugi/out/woven-graph
"""
from __future__ import annotations
import sys, pathlib
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


def humanize_viewpoint(viewpoint_str: str) -> str:
    """Convert :semantic → semantic-viewpoint topic."""
    # Remove leading colon if present
    name = viewpoint_str[1:] if viewpoint_str.startswith(":") else viewpoint_str
    return f"{name}-viewpoint topic"


def derive_topics(edges: list) -> tuple:
    """
    Derive :topic/* nodes and :en/kind :topic-binding edges from evidence edges.

    Collects all distinct :en/evidence-kind values that appear in :evidence edges,
    treating each viewpoint as a candidate topic.

    Returns (topics, bindings) — both sorted deterministically.
    """
    # Collect evidence edges only
    evidence_edges = [e for e in edges if e.get(":en/kind") == ":evidence"]

    # Gather all distinct viewpoints and map entities to viewpoints + weights
    viewpoints_set = set()
    entity_viewpoint_weights = {}  # (entity_id, viewpoint) -> sum of weights

    for edge in evidence_edges:
        viewpoint = edge.get(":en/evidence-kind")
        entity_id = edge.get(":en/to")
        weight = edge.get(":en/evidence-weight", 0.0)

        if viewpoint is not None and entity_id is not None:
            viewpoints_set.add(viewpoint)
            key = (entity_id, viewpoint)
            entity_viewpoint_weights[key] = entity_viewpoint_weights.get(key, 0.0) + float(weight)

    # Get all unique entity IDs that have evidence
    entities_with_evidence = set(ent for ent, _ in entity_viewpoint_weights.keys())

    # 1. Emit :topic/* nodes for each distinct viewpoint
    topics = []
    for viewpoint in sorted(viewpoints_set):  # deterministic sort
        topic_id = "topic." + (viewpoint[1:] if viewpoint.startswith(":") else viewpoint)
        label = humanize_viewpoint(viewpoint)

        # Coherence: # of distinct entities with this viewpoint / total # entities with any evidence
        distinct_entities_with_viewpoint = len(
            set(ent for (ent, vp) in entity_viewpoint_weights.keys() if vp == viewpoint)
        )
        coherence = (
            round(distinct_entities_with_viewpoint / len(entities_with_evidence), 4)
            if entities_with_evidence
            else 0.0
        )

        topic = {
            ":topic/id": topic_id,
            ":topic/label": label,
            ":topic/coherence": coherence,
            ":topic/viewpoint": viewpoint,
        }
        topics.append(topic)

    # 2. Emit :en/kind :topic-binding edges
    bindings = []
    for (entity_id, viewpoint), summed_weight in sorted(entity_viewpoint_weights.items()):
        # topic-id derived from viewpoint
        topic_id = "topic." + (viewpoint[1:] if viewpoint.startswith(":") else viewpoint)

        # binding-confidence: clamp summed weight to [0, 1]
        binding_confidence = round(min(1.0, max(0.0, summed_weight)), 4)

        binding_id = f"topicbind.{topic_id}.{entity_id}"

        binding = {
            ":en/id": binding_id,
            ":en/kind": ":topic-binding",
            ":en/from": topic_id,
            ":en/to": entity_id,
            ":en/binding-confidence": binding_confidence,
            ":en/stability": 1.0,  # R0 single-run; multi-run stability = P2-full/Pregel
            ":en/source": ":derived",
        }
        bindings.append(binding)

    # Sort bindings by :en/id for determinism
    bindings.sort(key=lambda b: b[":en/id"])

    return topics, bindings


def to_edn(topics: list, bindings: list) -> str:
    """Serialize topic datoms + bindings to EDN format (ingest.py style)."""
    lines = [
        ";; tsumugi 紡ぎ — GENERATED topic graph (§D7.1 topic derivation, R0 viewpoint-cluster). DO NOT hand-edit.",
        ";; :topic/* nodes + :en/kind :topic-binding edges from evidence viewpoints (G2 edge-primary, N1).",
        "[",
    ]

    # Emit topics
    for topic in topics:
        pairs = []
        for k in [":topic/id", ":topic/label", ":topic/coherence", ":topic/viewpoint"]:
            if k in topic:
                pairs.append(f"{k} {v(topic[k])}")
        lines.append("{" + " ".join(pairs) + "}")

    # Emit bindings
    for binding in bindings:
        pairs = []
        for k in [":en/id", ":en/kind", ":en/from", ":en/to",
                  ":en/binding-confidence", ":en/stability", ":en/source"]:
            if k in binding:
                pairs.append(f"{k} {v(binding[k])}")
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
    edges = []
    for m in data:
        if ":en/id" in m:
            edges.append(m)

    # Derive topics and bindings
    topics, bindings = derive_topics(edges)

    # Write output
    out = here / "out" / "topic-graph.kotoba.edn"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(to_edn(topics, bindings), encoding="utf-8")

    # Print summary (matching ingest.py / analyze.py style)
    print(f"derived {len(topics)} topics over {len(set(b[':en/to'] for b in bindings))} entities · {len(bindings)} topic-bindings (R0 viewpoint-cluster; full LDA = Pregel/Murakumo, deferred)")
    print(f"✓ wrote {out}")
    print()
    print("HONEST R0 NOTE (viewpoint-cluster stand-in for LDA):")
    print("  This resolver clusters evidence by viewpoint (e.g., :semantic, :network).")
    print("  Each viewpoint = one topic; each entity's sum weight per viewpoint → binding-confidence.")
    print("  True LDA Gibbs sampling (φ/θ inference, multi-run stability) = P2-full Pregel cell")
    print("  over kotoba-kqe arrangements, Murakumo-only, deferred.")
    print("  Deterministic per run (sorted by viewpoint/entity_id).")


if __name__ == "__main__":
    main()
