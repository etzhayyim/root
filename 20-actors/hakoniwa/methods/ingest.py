#!/usr/bin/env python3
"""hakoniwa 箱庭 — REAL PUBLIC-entity ingest → enriched box → kotoba EDN + content-address.

OUTWARD CELL (G8, R1-authorized). The only hakoniwa cell that reaches the network. It pulls a
BOUNDED slice of REAL PUBLIC entities (organizations / topics) from Wikidata and folds them into
a box as `:entity` nodes that the SYNTHETIC personas deliberate over. It runs operator/mesh-side
(it needs the network), never in-browser WASM.

CONSTITUTIONAL (read before any change):
  G1 — REAL ENTITIES ARE ORGS / TOPICS ONLY; the AGENTS stay SYNTHETIC. An ingested QID whose
       P31 instance-of set hits a natural-person class (Q5 "human", …) is DROPPED — no person,
       no PII, no biographical field is ever stored. The personas are generated fictional
       archetypes (`:persona/synthetic true`), never ingested from anyone. `assert_synthetic`
       (world.py) re-checks the emitted box; a test pins the human-refusal.
  G6 — sourcing honesty: ingested entities are `:authoritative` (real, public, CC0); the
       generated personas are `:synthetic`; coverage is a bounded illustrative slice.
  G2/G3 — the box still only produces a DISTRIBUTION routed to resilience (downstream cells).

Source (PUBLIC, no auth, CC0): Wikidata Special:EntityData/<QID>.json — entity labels, P31
instance-of, and a bounded set of structural properties (P361/P527/P749/P127) → :relates-to
edges among the ingested entities.

Pure-stdlib (urllib). Deterministic given the same fetched data (persona generation is
hash-seeded — no Math.random).

Usage:
    python3 ingest.py [--sources data/ingest-sources.edn] [--out OUTDIR] [--offline]
    # --offline: skip the network, use tests/fixtures/wikidata_entities.json
"""
from __future__ import annotations
import sys
import json
import hashlib
import pathlib
import urllib.request
import urllib.error

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import world as W  # noqa: E402
import cid as cidlib  # noqa: E402

UA = "etzhayyim-hakoniwa/0.1 (+https://etzhayyim.com; public-entity ingest)"
TIMEOUT = 20
COHORTS = [":prepared-anchor", ":cautious-commuter", ":skeptic", ":connector", ":newcomer"]


def _entitydata_url(base: str, qid: str) -> str:
    return base.rstrip("/") + "/" + qid + ".json"


def fetch_entity(base: str, qid: str) -> dict:
    """Fetch one Wikidata entity record (PUBLIC, no auth). Returns the entity sub-dict."""
    req = urllib.request.Request(_entitydata_url(base, qid),
                                 headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        doc = json.loads(r.read().decode("utf-8"))
    return doc["entities"][qid]


def _label(ent: dict) -> str:
    labels = ent.get("labels", {})
    for lang in ("en", "ja"):
        if lang in labels:
            return labels[lang]["value"]
    return ent.get("id", "?")


def _p31(ent: dict) -> list[str]:
    out = []
    for claim in ent.get("claims", {}).get("P31", []):
        try:
            out.append(claim["mainsnak"]["datavalue"]["value"]["id"])
        except (KeyError, TypeError):
            continue
    return out


def _prop_targets(ent: dict, pid: str) -> list[str]:
    out = []
    for claim in ent.get("claims", {}).get(pid, []):
        try:
            out.append(claim["mainsnak"]["datavalue"]["value"]["id"])
        except (KeyError, TypeError):
            continue
    return out


def _h(*parts) -> int:
    return int.from_bytes(hashlib.sha256(":".join(map(str, parts)).encode()).digest()[:6], "big")


def _u(*parts) -> float:
    return (_h(*parts) % 100000) / 100000.0


def generate_personas(n: int, topic_id: str, seed: int = 7) -> tuple[list[dict], list[dict]]:
    """Generate n SYNTHETIC fictional-archetype personas (G1) deliberating over the topic.
    Deterministic (hash-seeded). Returns (persona_nodes, edges: stance + influence)."""
    personas, edges = [], []
    for i in range(n):
        cohort = COHORTS[i % len(COHORTS)]
        # cohort-shaped priors with deterministic jitter (no Math.random)
        base_sus = {":prepared-anchor": 0.18, ":cautious-commuter": 0.47, ":skeptic": 0.30,
                    ":connector": 0.62, ":newcomer": 0.78}[cohort]
        base_stance = {":prepared-anchor": 0.82, ":cautious-commuter": 0.53, ":skeptic": 0.20,
                       ":connector": 0.50, ":newcomer": 0.44}[cohort]
        sus = round(min(0.95, max(0.05, base_sus + (_u(seed, "sus", i) - 0.5) * 0.1)), 3)
        stance = round(min(0.95, max(0.05, base_stance + (_u(seed, "st", i) - 0.5) * 0.1)), 3)
        pid = f"persona.g{i:02d}"
        node = {":sim/id": pid, ":sim/kind": ":persona",
                ":sim/label": f"synthetic archetype {cohort.lstrip(':')} #{i}",
                ":sim/sourcing": ":synthetic", ":persona/synthetic": True,
                ":persona/cohort": cohort, ":persona/susceptibility": sus,
                ":persona/initial-stance": stance}
        if cohort == ":connector":
            node[":persona/weight"] = 1.5
        personas.append(node)
        edges.append({":en/from": pid, ":en/to": topic_id, ":en/kind": ":holds-stance",
                      ":en/weight": stance, ":en/sourcing": ":synthetic"})
    # influence web: each persona is influenced by 2 deterministic others (small-world)
    for i in range(n):
        for k in range(2):
            j = _h(seed, "inf", i, k) % n
            if j != i:
                w = round(0.3 + _u(seed, "w", i, k) * 0.5, 3)
                edges.append({":en/from": f"persona.g{j:02d}", ":en/to": f"persona.g{i:02d}",
                              ":en/kind": ":influences", ":en/weight": w, ":en/sourcing": ":synthetic"})
    return personas, edges


def build_box(sources: dict, fetched: dict[str, dict]) -> tuple[dict, list, dict]:
    """Fold the fetched REAL entities + generated SYNTHETIC personas into one box.
    Returns (nodes, edges, provenance). G1: real entities are orgs/topics; persons are dropped."""
    person_classes = set(sources.get(":ingest/person-classes", []))
    props = sources.get(":ingest/properties", {})
    topic = sources.get(":ingest/topic", {})
    n_personas = int(sources.get(":ingest/synthetic-personas", 16))

    nodes: dict = {}
    edges: list = []
    kept, dropped = [], []

    # topic entity (the deliberation anchor) + outcome
    topic_id = "entity.topic"
    nodes[topic_id] = {":sim/id": topic_id, ":sim/kind": ":entity",
                       ":sim/label": topic.get(":topic/label", "public topic"),
                       ":sim/sourcing": ":representative",
                       ":entity/public-ref": "topic.resilience-commons"}
    nodes["outcome.adoption"] = {":sim/id": "outcome.adoption", ":sim/kind": ":outcome",
                                 ":sim/label": "synthetic-cohort mean adoption stance",
                                 ":sim/sourcing": ":representative", ":outcome/measures": ":all",
                                 ":outcome/statistic": ":mean-stance",
                                 ":outcome/use": topic.get(":topic/use", ":preparedness")}

    # REAL public entities (G1: orgs/topics only — refuse natural persons)
    for spec in sources.get(":ingest/entities", []):
        qid = spec.get(":qid")
        ent = fetched.get(qid)
        if not ent:
            continue
        p31 = set(_p31(ent))
        if p31 & person_classes:
            dropped.append({"qid": qid, "reason": "natural-person (P31∈person-classes)"})
            continue                                   # G1 — never store a person
        eid = f"entity.wd-{qid.lower()}"
        nodes[eid] = {":sim/id": eid, ":sim/kind": ":entity", ":sim/label": _label(ent),
                      ":sim/sourcing": ":authoritative", ":entity/public-ref": f"wd:{qid}"}
        kept.append({"qid": qid, "label": _label(ent), "eid": eid})

    # structural :relates-to edges among the kept entities (closed box)
    kept_qids = {k["qid"]: k["eid"] for k in kept}
    for spec in sources.get(":ingest/entities", []):
        qid = spec.get(":qid")
        if qid not in kept_qids or qid not in fetched:
            continue
        for pname, pid in props.items():
            if pname == ":instance-of":
                continue
            for tgt in _prop_targets(fetched[qid], pid):
                if tgt in kept_qids:
                    edges.append({":en/from": kept_qids[qid], ":en/to": kept_qids[tgt],
                                  ":en/kind": ":relates-to", ":en/weight": 1.0,
                                  ":en/sourcing": ":authoritative"})

    # generated SYNTHETIC personas deliberating over the topic
    personas, pedges = generate_personas(n_personas, topic_id)
    for p in personas:
        nodes[p[":sim/id"]] = p
    edges.extend(pedges)

    # a sonae-style authoritative relay signal entering the box
    nodes["signal.relay"] = {":sim/id": "signal.relay", ":sim/kind": ":signal",
                             ":sim/label": "official preparedness advisory RELAY (sonae-style)",
                             ":sim/sourcing": ":representative",
                             ":signal/push": 0.15, ":signal/at-step": 3}
    for p in personas[: max(1, len(personas) * 2 // 3)]:
        edges.append({":en/from": p[":sim/id"], ":en/to": "signal.relay",
                      ":en/kind": ":exposed-to", ":en/weight": 1.0, ":en/sourcing": ":synthetic"})

    provenance = {"source": "wikidata", "kept": kept, "dropped": dropped,
                  "n_entities_kept": len(kept), "n_entities_dropped": len(dropped),
                  "n_personas": len(personas), "n_nodes": len(nodes), "n_edges": len(edges)}
    return nodes, edges, provenance


def _fmt(v) -> str:
    if v is True:
        return "true"
    if v is False:
        return "false"
    if v is None:
        return "nil"
    if isinstance(v, str):
        return v if v.startswith(":") else json.dumps(v, ensure_ascii=False)
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


NODE_ORDER = [":sim/kind", ":sim/label", ":sim/sourcing", ":entity/public-ref",
              ":persona/synthetic", ":persona/cohort", ":persona/susceptibility",
              ":persona/initial-stance", ":persona/weight", ":signal/push", ":signal/at-step",
              ":outcome/measures", ":outcome/statistic", ":outcome/use"]
EDGE_ORDER = [":en/from", ":en/to", ":en/kind", ":en/weight", ":en/sourcing"]


def to_edn(nodes: dict, edges: list) -> str:
    L = [";; hakoniwa 箱庭 — GENERATED ingested box (ADR-2606111500). DO NOT hand-edit.",
         ";; REAL PUBLIC entities (:authoritative, Wikidata CC0) + SYNTHETIC personas (:synthetic, G1).",
         ";; No natural persons (P31=Q5 dropped at ingest). No PII. Agents are fictional archetypes.",
         "["]
    for nid, n in nodes.items():
        parts = [f'{{:sim/id {_fmt(nid)}']
        for a in NODE_ORDER:
            if a in n and n[a] is not None:
                parts.append(f"{a} {_fmt(n[a])}")
        L.append(" ".join(parts) + "}")
    for e in edges:
        parts = ["{"]
        parts += [f"{a} {_fmt(e[a])}" for a in EDGE_ORDER if a in e]
        L.append(" ".join(parts).replace("{ ", "{") + "}")
    L.append("]")
    return "\n".join(L) + "\n"


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    src_path = here / "data" / "ingest-sources.edn"
    if "--sources" in argv:
        src_path = pathlib.Path(argv[argv.index("--sources") + 1])
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    offline = "--offline" in argv
    outdir.mkdir(parents=True, exist_ok=True)

    sources = W.read_edn(src_path.read_text(encoding="utf-8"))
    base = sources[":ingest/source"][":source/url"]
    qids = [s[":qid"] for s in sources[":ingest/entities"]]

    fetched: dict[str, dict] = {}
    errors = []
    if offline:
        fx = here / "tests" / "fixtures" / "wikidata_entities.json"
        fetched = json.loads(fx.read_text(encoding="utf-8"))
    else:
        for qid in qids:
            try:
                fetched[qid] = fetch_entity(base, qid)
            except (urllib.error.URLError, KeyError, ValueError, TimeoutError, OSError) as e:
                errors.append({"qid": qid, "error": str(e)})

    nodes, edges, prov = build_box(sources, fetched)
    W.assert_synthetic(nodes)                          # G1 re-check on the emitted box

    edn = to_edn(nodes, edges)
    (outdir / "ingested-box.kotoba.edn").write_text(edn, encoding="utf-8")
    box_cid = cidlib.cidv1_raw(edn.encode("utf-8"))
    prov.update({"errors": errors, "offline": offline, "box_cid": box_cid, "qids_requested": qids})
    (outdir / "ingest-provenance.json").write_text(json.dumps(prov, ensure_ascii=False, indent=2),
                                                   encoding="utf-8")
    (outdir / "ingested-box.cid").write_text(box_cid + "\n", encoding="utf-8")

    print(f"hakoniwa ingest: {prov['n_entities_kept']} real entities kept, "
          f"{prov['n_entities_dropped']} dropped (G1), {prov['n_personas']} synthetic personas "
          f"→ {prov['n_nodes']} nodes / {prov['n_edges']} 縁")
    print(f"  box CID {box_cid}  ({'offline fixture' if offline else 'live Wikidata'})")
    if errors:
        print(f"  ⚠ {len(errors)} fetch error(s) — entity dropped from the bounded slice")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
