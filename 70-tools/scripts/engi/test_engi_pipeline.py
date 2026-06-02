#!/usr/bin/env python3
"""Tests for (c) atproto adapter, (a) grasp_render, (d) danjo/tadori retrofit.

ADR-2606011000. Run: python3 test_engi_pipeline.py (or pytest)."""
from __future__ import annotations

import json

import engi_ingest as ei
import grasp_render as gr
import retrofit_danjo_tadori as rt
import firehose_dryrun as fd
from engi_ingest import Follow

MEMBERS = {"did:plc:alice", "did:plc:bob", "did:plc:erin", "did:plc:frank"}


# --------------------------------------------------------------------------- #
# (c) atproto adapter
# --------------------------------------------------------------------------- #
def test_c_atproto_adapter_maps_follow_and_dep():
    records = [
        {"author_did": "did:plc:alice",
         "record": {"$type": "app.bsky.graph.follow", "subject": "did:plc:bob"}},
        {"author_did": "did:plc:bob",
         "record": {"$type": "com.etzhayyim.engi.dep", "subject": "did:plc:alice"}},
        {"author_did": "did:plc:alice",
         "record": {"$type": "app.bsky.feed.post", "text": "ignored"}},  # not a graph edge
    ]
    follows = ei.from_atproto_records(records, MEMBERS)
    kinds = sorted(f.kind for f in follows)
    assert kinds == ["depends-on", "follows"], kinds  # post skipped


def test_c_adapter_then_ingest_floor_clean():
    records = [
        {"author_did": "did:plc:alice",
         "record": {"$type": "app.bsky.graph.follow", "subject": "did:plc:bob"}},
        {"author_did": "did:plc:carol",     # latent
         "record": {"$type": "app.bsky.graph.follow", "subject": "did:plc:bob"}},
    ]
    follows = ei.from_atproto_records(records, MEMBERS)
    res = ei.ingest(follows, MEMBERS)
    edn = ei.to_edn(res)
    assert ei.validate_floor(edn, res, MEMBERS) == []
    assert "carol" not in edn                       # latent never named


# --------------------------------------------------------------------------- #
# (a) grasp_render
# --------------------------------------------------------------------------- #
def _spec():
    follows = [
        Follow("did:plc:alice", "did:plc:bob"),
        Follow("did:plc:erin", "did:plc:bob"),
        Follow("did:plc:frank", "did:plc:bob"),
        Follow("did:plc:alice", "did:plc:erin"),
        Follow("did:plc:frank", "did:plc:erin"),
        Follow("did:plc:alice", "did:plc:frank"),    # → 3 members carry concentration
        Follow("did:plc:carol", "did:plc:bob"),     # latent
        Follow("did:plc:dave", "did:plc:erin"),      # latent
    ]
    res = ei.ingest(follows, MEMBERS)
    return gr.render_spec(list(res.grasp.values()), res.latent_aggregate), res


def test_a_render_has_latent_single_anonymous_node():
    spec, _ = _spec()
    latent = [n for n in spec["nodes"] if n["kind"] == "latent-aggregate"]
    assert len(latent) == 1, "latent must be exactly one anonymous node (R2)"
    assert "n=2" in latent[0]["label"]               # carol + dave, counted not named


def test_a_render_no_latent_identity_anywhere():
    spec, _ = _spec()
    blob = json.dumps(spec, ensure_ascii=False)
    assert "carol" not in blob and "dave" not in blob and "did:plc:carol" not in blob


def test_a_render_surfaces_top_concentration_for_release():
    spec, _ = _spec()
    # bob has the highest in-degree (3 members + latent) → flagged suggest_release.
    bob = [n for n in spec["nodes"] if n.get("id") == "org.did-plc-bob"]
    assert bob and bob[0]["suggest_release"] is True


def test_a_k_anonymity_collapses_small_cohort():
    # 2 members < K_ANON(3) → no per-member naming; one member-aggregate node.
    small = {"did:plc:alice", "did:plc:bob"}
    res = ei.ingest([Follow("did:plc:alice", "did:plc:bob")], small)
    spec = gr.render_spec(list(res.grasp.values()), res.latent_aggregate)
    member_nodes = [n for n in spec["nodes"] if n["kind"] == "member"]
    agg = [n for n in spec["nodes"] if n["kind"] == "member-aggregate"]
    assert member_nodes == [] and len(agg) == 1, "small cohort must aggregate (R3)"


# --------------------------------------------------------------------------- #
# (d) danjo / tadori retrofit
# --------------------------------------------------------------------------- #
def test_d_danjo_observation_is_non_adjudicating_edge():
    en = rt.danjo_observation_to_en(
        {"id": "o1", "subject": "org.a", "object": "org.b", "kind": "procurement",
         "weight": 3.0, "verified": True})
    assert en[":en/kind"] == ":entangled-with"       # NOT a verdict / ownership
    assert en[":en/source"] == ":danjo-observation"
    assert en[":en/grasping-load"] == 3.0
    assert ":owns" not in json.dumps(en)


def test_d_tadori_finding_maps_control_to_custodies():
    en = rt.tadori_finding_to_en(
        {"id": "f1", "actor": "org.addr", "entity": "org.ex", "relation": "controls",
         "txValue": 12.5})
    assert en[":en/kind"] == ":custodies"
    assert en[":en/source"] == ":onchain"
    assert en[":en/grasping-load"] == 12.5


def test_d_no_owns_in_crosswalk():
    assert ":owns" not in json.dumps(rt.CROSSWALK)


# --------------------------------------------------------------------------- #
# dry run over real FirehoseEvent shape (ADR-2605231902)
# --------------------------------------------------------------------------- #
EVENTS = [
    {"seq": 1, "did": "did:plc:alice", "collection": "app.bsky.graph.follow",
     "rkey": "3k1", "op": "create", "recordCid": "bafy1"},
    {"seq": 2, "did": "did:plc:alice", "collection": "app.bsky.graph.follow",
     "rkey": "3k2", "op": "create", "recordCid": "bafy2"},     # → latent carol
    {"seq": 3, "did": "did:plc:bob", "collection": "com.etzhayyim.engi.dep",
     "rkey": "3k3", "op": "create", "recordCid": "bafy3"},
    {"seq": 4, "did": "did:plc:alice", "collection": "app.bsky.feed.post",
     "rkey": "3k4", "op": "create", "recordCid": "bafy4"},     # ignored
    {"seq": 5, "did": "did:plc:bob", "collection": "app.bsky.graph.follow",
     "rkey": "3k5", "op": "delete"},                            # skipped
]
SUBJECTS = {
    ("did:plc:alice", "3k1"): "did:plc:bob",
    ("did:plc:alice", "3k2"): "did:plc:carol",
    ("did:plc:bob", "3k3"): "did:plc:alice",
}
SMALL_MEMBERS = {"did:plc:alice", "did:plc:bob"}


def _fetch(did, rkey):
    return SUBJECTS.get((did, rkey))


def test_dryrun_ignores_nongraph_and_delete():
    recs = fd.events_to_records(EVENTS, _fetch)
    assert len(recs) == 3                          # post + delete dropped


def test_dryrun_pipeline_clean_and_latent_anonymous():
    report = fd.dry_run(EVENTS, SMALL_MEMBERS, _fetch)
    assert report["floor"] == "CLEAN"
    assert report["member_edges_emitted"] == 2     # alice→bob + bob→alice(dep)
    assert report["latent_anonymous"]["latent-organism-count"] == 1   # carol
    assert "carol" not in report["edn"]


def test_dryrun_fails_closed_on_floor_breach(monkeypatch=None):
    # Inject a fetcher that would route a member edge but then poison the output to
    # prove dry_run raises rather than emitting a dirty graph.
    orig = ei.to_edn
    try:
        ei.to_edn = lambda res: orig(res) + '\n  {:organism/did "did:plc:carol"}'
        raised = False
        try:
            fd.dry_run(EVENTS, SMALL_MEMBERS, _fetch)
        except RuntimeError as e:
            raised = "FLOOR DIRTY" in str(e)
        assert raised, "dry_run must fail closed on a floor breach"
    finally:
        ei.to_edn = orig


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} engi-pipeline tests passed")
