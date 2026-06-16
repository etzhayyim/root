#!/usr/bin/env python3
"""aburi 炙り — autorun heartbeat + kotoba live-bridge tests (ADR-2606161630). Pure stdlib;
the network leg is INJECTED so every test runs OFFLINE (no server key, no live node)."""
import sys
import json
import pathlib
import tempfile

ACTOR_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ACTOR_DIR / "methods"))

import kotoba  # noqa: E402
import autorun  # noqa: E402
import kotoba_bridge as kb  # noqa: E402

PLAY = {"kind": "play-data-safety", "apps": [
    {"app": "FreeGame", "shared": [
        {"type": "Location", "purpose": "Advertising or marketing", "collectors": ["AppLovin"]},
        {"type": "Device or other IDs", "purpose": "Advertising or marketing", "collectors": ["AdMob"]}]}]}
APPLE = {"kind": "apple-app-privacy-report", "apps": [
    {"app": "SocialApp", "accessed": ["Location", "Identifiers"],
     "domains": ["graph.facebook.com", "doubleclick.net"]}]}


def _setup(dr, exports):
    intake = pathlib.Path(dr) / "intake"
    intake.mkdir(parents=True)
    for name, doc in exports.items():
        (intake / name).write_text(json.dumps(doc), encoding="utf-8")
    log = pathlib.Path(dr) / "log.kotoba.edn"
    return intake, log


def _fake_transport(calls):
    def t(url, body):
        calls.append(body)
        n = len(calls)
        return {"status": "ok", "tx_cid": f"bafyremote{n}", "commit_cid": f"bafycommit{n}",
                "datom_count": 1}
    return t


# ── autorun (heartbeat) ──────────────────────────────────────────────────────
def test_autorun_ingests_and_dedups():
    with tempfile.TemporaryDirectory() as dr:
        intake, log = _setup(dr, {"play-1.json": PLAY, "apple-1.json": APPLE})
        r0 = autorun.run_cycle(0, intake, log)
        assert len(r0["appended"]) == 2, f"expected 2 ingested, got {r0['appended']}"
        assert r0["verify"]["ok"], "commit-DAG broken after ingest"
        # second cycle: same intake CIDs → no-op (G5 dedup)
        r1 = autorun.run_cycle(1, intake, log)
        assert r1["appended"] == [] and r1["skipped"] == 2, f"dedup failed: {r1}"
        assert kotoba.verify_chain(log)["ok"]


def test_autorun_resume_is_byte_identical():
    with tempfile.TemporaryDirectory() as dr:
        intake, log = _setup(dr, {"play-1.json": PLAY})
        autorun.run_cycle(0, intake, log)
        head_a = kotoba.head_cid(log)
    with tempfile.TemporaryDirectory() as dr2:
        intake2, log2 = _setup(dr2, {"play-1.json": PLAY})
        autorun.run_cycle(0, intake2, log2)
        head_b = kotoba.head_cid(log2)
    assert head_a == head_b, "ingest head CID is not deterministic across runs"


# ── kotoba bridge (live transact, injected) ──────────────────────────────────
def test_default_is_dry_run():
    with tempfile.TemporaryDirectory() as dr:
        intake, log = _setup(dr, {"play-1.json": PLAY, "apple-1.json": APPLE})
        autorun.run_cycle(0, intake, log)
        res = kb.push(log, live=False)
        assert res["mode"] == "dry-run" and res["pending"] == 2
        assert len(kotoba.read_log(log)) == 2, "dry-run must not append a checkpoint"


def test_live_push_advances_cursor_exactly_once():
    with tempfile.TemporaryDirectory() as dr:
        intake, log = _setup(dr, {"play-1.json": PLAY, "apple-1.json": APPLE})
        autorun.run_cycle(0, intake, log)
        calls = []
        res = kb.push(log, live=True, transport=_fake_transport(calls))
        assert res["pushed"] == 2 and len(calls) == 2
        assert kotoba.verify_chain(log)["ok"], "chain broke after checkpoint append"
        assert len(kotoba.read_log(log)) == 3, "exactly one checkpoint tx appended"
        # re-run: cursor advanced → nothing new to push (checkpoint tx is excluded)
        calls2 = []
        res2 = kb.push(log, live=True, transport=_fake_transport(calls2))
        assert res2["pushed"] == 0 and calls2 == [], f"cursor not exactly-once: {res2}"


def test_expected_parent_chains():
    with tempfile.TemporaryDirectory() as dr:
        intake, log = _setup(dr, {"play-1.json": PLAY, "apple-1.json": APPLE})
        autorun.run_cycle(0, intake, log)
        calls = []
        kb.push(log, live=True, transport=_fake_transport(calls))
        assert "expected_parent" not in calls[0], "first push must not chain"
        assert calls[1]["expected_parent"] == "bafycommit1", "second push must chain off first commit"


def test_provenance_in_tx_edn():
    with tempfile.TemporaryDirectory() as dr:
        intake, log = _setup(dr, {"play-1.json": PLAY})
        autorun.run_cycle(0, intake, log)
        calls = []
        kb.push(log, live=True, transport=_fake_transport(calls))
        assert ":aburi.tx/local-cid" in calls[0]["tx_edn"], "provenance missing from tx_edn"
        assert calls[0]["graph"] == "aburi"


def test_host_allowlist_rejects_foreign_endpoint():
    for bad in ("https://evil.example.com/transact", "http://10.0.0.5:8077/x"):
        try:
            kb.push(pathlib.Path("/nonexistent"), endpoint=bad, live=False)
            assert False, f"foreign endpoint accepted: {bad}"
        except kb.KotobaBoundaryViolation:
            pass


def test_live_requires_operator_did_no_server_key():
    """no-server-key: the operator bearer needs the node's PUBLIC DID env var; with the real
    transport and no DID set, a live push refuses rather than minting/holding a key."""
    import os
    os.environ.pop(kb.ENV_OPERATOR_DID, None)
    with tempfile.TemporaryDirectory() as dr:
        intake, log = _setup(dr, {"play-1.json": PLAY})
        autorun.run_cycle(0, intake, log)
        try:
            kb.push(log, live=True)  # real transport → operator_bearer() → must raise
            assert False, "live push without operator DID did not refuse"
        except kb.KotobaBoundaryViolation as e:
            assert kb.ENV_OPERATOR_DID in str(e)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} passed")
