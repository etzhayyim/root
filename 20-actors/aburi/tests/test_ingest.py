#!/usr/bin/env python3
"""aburi 炙り — ingest (acquisition leg) tests (ADR-2606161630). Pure stdlib, SYNTHETIC fixtures
only (no real personal data — tests must never carry a real export)."""
import sys
import pathlib

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

import ingest  # noqa: E402
import analyze  # noqa: E402
from datom_emit import NODE_ATTRS, EDGE_ATTRS  # noqa: E402

# ── synthetic exports (resemble the real formats; carry NO real person/value) ──
PLAY = {"kind": "play-data-safety", "apps": [
    {"app": "FreeGame", "shared": [
        {"type": "Location", "purpose": "Advertising or marketing", "collectors": ["AppLovin"]},
        {"type": "Device or other IDs", "purpose": "Advertising or marketing", "collectors": ["AdMob"]},
        {"type": "Purchases", "purpose": "Analytics"}]}]}

APPLE = {"kind": "apple-app-privacy-report", "apps": [
    {"app": "SocialApp", "accessed": ["Location", "Identifiers"],
     "domains": ["graph.facebook.com", "doubleclick.net", "adsrvr.org"]}]}

TAKEOUT = {"kind": "google-takeout-ads", "adPersonalization": True,
           "activityControls": {"web": True, "location": True, "youtube": False}}

PERMS = {"kind": "android-permission-dump", "apps": [
    {"package": "com.example.app", "grants": ["ACCESS_FINE_LOCATION", "READ_CONTACTS", "AD_ID"]}]}


def _datoms(raw, kind):
    return ingest.export_to_datoms(raw, kind, "bsynthetic")


def test_play_adapter_maps_advertising_flows():
    nodes, edges = ingest.load_graph(ingest.adapt_play_data_safety(PLAY))
    cols = {n[":organism/id"] for n in nodes.values() if n[":organism/kind"] == ":collector"}
    assert "ax.col.applovin" in cols and "ax.col.admob" in cols, f"ad collectors not mapped: {cols}"
    flows = [e for e in edges if e[":en/kind"] == ":flows-to"]
    assert flows, "no :flows-to edges from a Play data-safety export"
    # an advertising-purpose share should carry higher load than a non-ad share
    assert max(e[":en/load"] for e in flows) >= 0.8


def test_apple_adapter_maps_domains_to_collectors():
    nodes, edges = ingest.load_graph(ingest.adapt_apple_app_privacy_report(APPLE))
    cols = {n[":organism/id"] for n in nodes.values() if n[":organism/kind"] == ":collector"}
    assert {"ax.col.meta-audience", "ax.col.google-admanager", "ax.col.the-trade-desk"} <= cols, \
        f"ad domains not resolved to collectors: {cols}"


def test_takeout_and_permission_adapters_nonempty():
    for raw, kind in ((TAKEOUT, ":google-takeout-ads"), (PERMS, ":android-permission-dump")):
        nodes, edges = ingest.load_graph(ingest.ADAPTERS[kind](raw))
        assert nodes and edges, f"{kind} produced an empty graph"


def test_g8_credential_key_raises():
    poisoned = dict(PLAY); poisoned["session_token"] = "abc.def.ghi"
    try:
        _datoms(poisoned, ":play-data-safety")
        assert False, "credential-shaped key did not raise (G8)"
    except ValueError as e:
        assert "G8" in str(e)


def test_g8_advertising_id_value_raises():
    poisoned = {"kind": "apple-app-privacy-report", "apps": [
        {"app": "X", "accessed": ["Identifiers"], "domains": ["doubleclick.net"],
         "note": "device 38400000-8cf0-11bd-b23e-10b96e40000d"}]}
    try:
        _datoms(poisoned, ":apple-app-privacy-report")
        assert False, "advertising-id (UUID) value did not raise (G8)"
    except ValueError as e:
        assert "G8" in str(e)


def test_g8_email_and_pan_values_raise():
    for bad in ({"kind": "x", "apps": [{"app": "a@b.com"}]},
                {"kind": "x", "apps": [{"app": "card 4111 1111 1111 1111"}]}):
        try:
            ingest.guard(bad)
            assert False, f"raw value did not raise (G8): {bad}"
        except ValueError as e:
            assert "G8" in str(e)


def test_g8_only_allowlist_attrs_in_datoms():
    """Every emitted datom's attribute is in the datom_emit allowlist or an intake-marker — no
    credential / raw-identifier attribute can ever reach the substrate."""
    allowed = set(NODE_ATTRS) | set(EDGE_ATTRS) | {":aburi.intake/cid", ":aburi.intake/kind"}
    for raw, kind in ((PLAY, ":play-data-safety"), (APPLE, ":apple-app-privacy-report"),
                      (TAKEOUT, ":google-takeout-ads"), (PERMS, ":android-permission-dump")):
        for d in _datoms(raw, kind):
            assert d[0] == ":db/add"
            assert d[2] in allowed, f"non-allowlisted attr {d[2]} emitted from {kind}"


def test_ingested_graph_is_analyzable():
    """The acquisition leg feeds the SAME analyzer: an ingested graph yields a real exposure
    readout (who-tracks-you), end-to-end."""
    nodes, edges = ingest.load_graph(ingest.adapt_apple_app_privacy_report(APPLE))
    res = analyze.analyze(nodes, edges)
    assert res["exposure"], "no collector exposure computed from an ingested graph"
    top = max(res["exposure"].items(), key=lambda kv: kv[1])[0]
    assert nodes[top][":organism/kind"] == ":collector"


def test_determinism():
    a = _datoms(PLAY, ":play-data-safety")
    b = _datoms(PLAY, ":play-data-safety")
    assert a == b, "ingest is not deterministic"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
