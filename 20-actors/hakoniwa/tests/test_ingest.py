#!/usr/bin/env python3
"""hakoniwa 箱庭 — real-entity ingest + LLM-persona swarm tests (ADR-2606111500 R1).
Pure stdlib, NETWORK-FREE (offline fixture), deterministic.

Verifies:
  - the ingest folds REAL public Wikidata entities into the box as :authoritative :entity nodes
  - G1: a fetched natural person (P31=Q5, Douglas Adams Q42) is DROPPED — never stored
  - G1: every generated agent is :persona/synthetic true with no PII; assert_synthetic passes on
    the emitted box
  - the ingested box LOADS via world.load and RUNS through simulate/distribution (a real box)
  - the box is content-addressed to a kotoba IPFS CIDv1 (ipfs-parity) deterministically
  - the LLM-persona swarm (swarm_ensemble) runs; with the deterministic kernel step it produces
    a valid distribution, and its fallback `via` is the kernel (no fleet in tests)
  - a swarm step_fn that returns an out-of-range stance is clamped to [0,1]
"""
import sys
import json
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

import world as W  # noqa: E402
import simulate as S  # noqa: E402
import distribution as D  # noqa: E402
import ingest as ING  # noqa: E402
import cid as cidlib  # noqa: E402

SOURCES = W.read_edn((ACTOR_DIR / "data" / "ingest-sources.edn").read_text(encoding="utf-8"))
FIXTURE = json.loads((ACTOR_DIR / "tests" / "fixtures" / "wikidata_entities.json").read_text(encoding="utf-8"))


def test_ingest_keeps_real_entities():
    nodes, edges, prov = ING.build_box(SOURCES, FIXTURE)
    ents = [n for n in nodes.values() if n.get(":sim/kind") == ":entity"
            and str(n.get(":entity/public-ref", "")).startswith("wd:")]
    assert len(ents) >= 4, f"expected real Wikidata entities, got {len(ents)}"
    for e in ents:
        assert e[":sim/sourcing"] == ":authoritative", "real public entity must be :authoritative"
    assert prov["n_entities_kept"] >= 4


def test_g1_drops_natural_person():
    """G1: Q42 (Douglas Adams, P31=Q5 human) is in the fixture but MUST be dropped."""
    # add Q42 to a copy of the sources allowlist so build_box is asked to ingest it
    src = dict(SOURCES)
    src[":ingest/entities"] = list(SOURCES[":ingest/entities"]) + [{":qid": "Q42", ":role": ":person"}]
    nodes, edges, prov = ING.build_box(src, FIXTURE)
    # no node may carry the Q42 public-ref
    for n in nodes.values():
        assert n.get(":entity/public-ref") != "wd:Q42", "G1 breach: a natural person was stored"
    assert any(d["qid"] == "Q42" for d in prov["dropped"]), "Q42 (human) was not recorded as dropped"
    assert prov["n_entities_dropped"] >= 1


def test_emitted_box_is_synthetic_and_loads():
    nodes, edges, _ = ING.build_box(SOURCES, FIXTURE)
    W.assert_synthetic(nodes)                      # G1 — passes (agents synthetic, no PII)
    personas = [n for n in nodes.values() if n.get(":sim/kind") == ":persona"]
    assert personas and all(p.get(":persona/synthetic") is True for p in personas)
    # round-trip through the EDN writer + world.load
    edn = ING.to_edn(nodes, edges)
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".edn", delete=False, encoding="utf-8") as fh:
        fh.write(edn)
        path = pathlib.Path(fh.name)
    n2, e2 = W.load(path)                           # must not raise (G1) + must parse
    assert len(n2) == len(nodes)
    results, meta = S.ensemble(n2, e2, steps=10, replicas=32, seed=7)
    dist = D.distribution(results)
    assert 0.0 <= dist["quantiles"][":p50"] <= 1.0


def test_box_content_address_deterministic():
    nodes, edges, _ = ING.build_box(SOURCES, FIXTURE)
    a = cidlib.cidv1_raw(ING.to_edn(nodes, edges).encode("utf-8"))
    nodes2, edges2, _ = ING.build_box(SOURCES, FIXTURE)
    b = cidlib.cidv1_raw(ING.to_edn(nodes2, edges2).encode("utf-8"))
    assert a == b, "ingested box CID is not deterministic"
    assert a.startswith("bafkrei"), f"not a CIDv1 raw/sha2-256 multibase-b CID: {a}"


def test_swarm_ensemble_runs_with_kernel_step():
    nodes, edges, _ = ING.build_box(SOURCES, FIXTURE)
    results, meta = S.swarm_ensemble(nodes, edges, steps=10, replicas=24, seed=7)  # default kernel step
    assert len(results) == 24
    assert all(0.0 <= r <= 1.0 for r in results)
    assert meta["swarm_via"] == [":kernel"], f"unexpected via channels: {meta['swarm_via']}"
    dist = D.distribution(results)
    assert dist["max"] - dist["min"] >= 0.0


def test_swarm_step_fn_is_clamped():
    """A rogue step_fn returning >1 / <0 must be clamped to [0,1] (defensive)."""
    nodes, edges, _ = ING.build_box(SOURCES, FIXTURE)
    rogue = lambda st, nm, su, an: {"stance": 99.0, "via": ":rogue"}  # noqa: E731
    results, _ = S.swarm_ensemble(nodes, edges, steps=4, replicas=4, seed=1, step_fn=rogue)
    assert all(0.0 <= r <= 1.0 for r in results), "swarm did not clamp an out-of-range stance"


def test_murakumo_persona_step_signature_matches_swarm():
    """persona_step must be drop-in for the swarm step_fn (offline → kernel fallback)."""
    import murakumo as M
    r = M.persona_step(0.5, 0.8, 0.6, 0.4, prefer_fleet=False)
    assert set(r) == {"stance", "via"} and 0.0 <= r["stance"] <= 1.0
    assert r["via"] == ":kernel-fallback"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
