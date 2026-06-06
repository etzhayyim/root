#!/usr/bin/env python3
"""tsumugi 紡ぎ — influence-history extension tests (ADR-2606061500).

Verifies the five constitutional invariants are honored by the seed + analyzer + projector:
  N1 edge-primary   — no per-soul score; influence is an edge-integral.
  N2 mirror-only    — every node is a mirror; posts are observer-voice, impersonation refused.
  N3 non-eschat.    — no truth/salvation/afterlife datom anywhere.
  N4 public+settled — no living-PII / consent fields; dating-confidence present.
  N5 temporal DAG   — every influence edge points forward in time.

Run:  python3 -m pytest tests/test_influence.py   (or plain `python3 tests/test_influence.py`)
stdlib + numpy only.
"""
import sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "methods"))

import analyze_influence as ai            # noqa: E402
import project_influence_posts as pp      # noqa: E402

SEED = ROOT / "data" / "seed-influence-history.kotoba.edn"


def _load():
    return ai.load(str(SEED))


def test_seed_loads_nodes_and_flows():
    nodes, flows = _load()
    assert len(nodes) >= 25, f"expected a substantive seed, got {len(nodes)} nodes"
    assert len(flows) >= 30, f"expected a substantive influence graph, got {len(flows)} edges"


def test_three_requested_traditions_present():
    nodes, _ = _load()
    # YHWH-tradition (Torah/Jewish), Jesus (Christian), Buddha (Buddhist) must all be modeled
    assert "doc.torah" in nodes and "fig.jesus" in nodes
    assert "fig.buddha" in nodes and "trad.buddhist" in nodes
    assert "trad.jewish" in nodes and "trad.christian" in nodes


def test_N5_temporal_dag_no_backward_influence():
    # minimal causal rule (lifespan-overlap aware): a source must begin no later than the
    # receiver ends. Rejects only true backward influence (source after receiver is gone).
    nodes, flows = _load()
    for f in flows:
        a, b = nodes[f[":flow/from"]], nodes[f[":flow/to"]]
        ya = ai.node_year(a, ":hist/year-from")
        yb = ai.node_year(b, ":hist/year-to")
        assert ya <= yb, f"N5 violation: {f[':flow/id']} flows backward in time ({ya} > {yb})"


def test_N1_edge_primary_no_soul_score():
    # influence/karma must live on edges; NO node may carry a stored per-soul score attr.
    text = SEED.read_text(encoding="utf-8")
    assert ":influence/score-of-figure" not in text
    assert ":spirit/score-of-soul" not in text
    nodes, _ = _load()
    for nid, nd in nodes.items():
        # nodes carry descriptive fields only — no signed-weight/karma on a node
        assert ":flow/signed-weight" not in nd, f"{nid} stores influence on the node (N1 breach)"
        assert ":spirit.bond/signed-weight" not in nd


def test_N1_readouts_are_edge_integrals():
    # the analyzer's outbound/inbound must be derivable from edges: a node with no incident
    # edges has zero reach. self.etzhayyim (latest, seeds nothing) must have ~0 outbound.
    import numpy as np
    nodes, flows = _load()
    ids = list(nodes.keys()); idx = {k: i for i, k in enumerate(ids)}; n = len(ids)
    A = np.zeros((n, n))
    for f in flows:
        A[idx[f[":flow/from"]], idx[f[":flow/to"]]] += abs(float(f[":flow/signed-weight"]))
    M = np.linalg.inv(np.eye(n) - 0.5 * A) - np.eye(n)
    outbound = M.sum(1)
    assert outbound[idx["self.etzhayyim"]] < 1e-6, "etzhayyim (newest) must seed nothing downstream"
    # a documented deep source must have non-trivial forward reach
    assert outbound[idx["doc.torah"]] > 0.5


def test_N2_every_node_is_a_mirror():
    nodes, _ = _load()
    for nid, nd in nodes.items():
        assert nd.get(":mirror/is-mirror") is True, f"{nid} is not a mirror (N2)"
        assert nd.get(":mirror/disclaimer"), f"{nid} lacks a disclaimer (N2)"
        assert nd.get(":mirror/performer-type") in (
            ":historical-figure", ":document", ":event", ":tradition"), nid


def test_N2_posts_are_observer_voice_only():
    nodes, flows = _load()
    posts = []
    for f in flows:
        posts.append(pp.project_post(nodes[f[":flow/to"]], f, nodes, 0))
    for nd in nodes.values():
        posts.append(pp.project_post(nd, None, nodes, 0))
    assert posts
    for p in posts:
        assert p[":post/voice"] == ":observer", "N2: posts must be observer voice"
        assert p[":post/published"] is False, "G7: posts must be dry-run"
        # disclaimer must lead the text (mirror, never the figure speaking)
        assert "観察" in p[":post/text"] or "mirror" in p[":post/text"].lower()
        assert ":first-person" not in p.get(":post/voice", "")


def test_N2_impersonation_is_refused():
    # a non-mirror node must be refused by the projector (no impersonation path exists).
    fake = {":organism/id": "fig.fake", ":organism/label": "X"}  # no :mirror/is-mirror
    try:
        pp.project_post(fake, None, {}, 0)
        assert False, "projector accepted a non-mirror node (N2 breach)"
    except pp.ImpersonationError:
        pass


def test_N3_no_eschatological_or_truth_datoms():
    text = SEED.read_text(encoding="utf-8")
    for forbidden in (":truth/verdict", ":salvation/status", ":afterlife",
                      ":soul-judgment", ":final-state", ":revelation/"):
        assert forbidden not in text, f"N3 (非終末論) breach: {forbidden} present"


def test_N4_no_living_pii_or_consent_fields():
    # historical public figures carry NO PII/consent — that is the Council-gated :human scale.
    text = SEED.read_text(encoding="utf-8")
    for forbidden in (":spirit/consent-cid", ":spirit.assay/response-cid", ":pii/"):
        assert forbidden not in text, f"N4 breach: {forbidden} present (living-PII path)"
    nodes, _ = _load()
    for nid, nd in nodes.items():
        assert nd.get(":organism/standing") == ":historical-public", nid
        assert nd.get(":hist/dating-confidence"), f"{nid} lacks dating-confidence (sourcing honesty)"


def test_legendary_attributions_flagged_not_asserted():
    nodes, _ = _load()
    # Moses / Bodhidharma are traditional/legendary — must be flagged, never :attested.
    assert nodes["fig.moses"][":hist/dating-confidence"] == ":legendary"
    assert nodes["fig.bodhidharma"][":hist/dating-confidence"] in (":legendary", ":traditional")
    # Jesus / Buddha historical existence is scholarly-consensus (the influence, not divinity)
    assert nodes["fig.jesus"][":hist/dating-confidence"] == ":scholarly-consensus"
    assert nodes["fig.buddha"][":hist/dating-confidence"] == ":scholarly-consensus"


def test_etzhayyim_genealogy_is_inbound_only():
    # the self node synthesizes (receives) — it must not be authored as a source over others.
    _, flows = _load()
    self_edges = [f for f in flows if "self.etzhayyim" in (f[":flow/from"], f[":flow/to"])]
    assert self_edges, "expected etzhayyim doctrinal-genealogy edges"
    for f in self_edges:
        assert f[":flow/to"] == "self.etzhayyim", "etzhayyim must only RECEIVE influence (産霊), never seed it"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn(); print(f"  ✓ {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1; print(f"  ✗ {fn.__name__}: {e}")
    print(f"\n{len(fns)-failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
