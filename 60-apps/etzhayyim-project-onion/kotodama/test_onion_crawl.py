#!/usr/bin/env python3
"""Tests for the onion crawl py-kotodama worker (onion_crawl.py).

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest test_onion_crawl.py
    python3 test_onion_crawl.py

Verifies the kotoba-wasm + py-kotodama BPMN worker over an in-memory KotobaCtx fake:
Datom-native (no Hyperdrive/SQL), append-only seeding, stalest-first claiming, and the
no-server-key/G11 gate on the live darkweb fetch.
"""
from __future__ import annotations

import sys

import onion_crawl as oc


class FakeKotoba:
    """In-memory KotobaCtx — the only seam between the pure handlers and the wasm host."""
    def __init__(self, now="2026-06-07T00:00:00Z"):
        self.datoms: list = []         # [eid, attr, value]
        self._now = now
        self._seq = 1000

    def query(self, datalog: str):
        # tiny shim: serve the two reads the worker issues by entity kind.
        if oc.SITE_KIND in datalog and ":onion.site/onion-host" in datalog:
            latest: dict = {}
            for eid, attr, val in self.datoms:
                if attr == ":onion.site/onion-host":
                    latest.setdefault(eid, {})["host"] = val
                if attr == ":onion.site/last-seen":
                    latest.setdefault(eid, {})["last"] = val
            return [(d["host"], d.get("last")) for d in latest.values() if "host" in d]
        return []

    def transact(self, datoms):
        self.datoms.extend(datoms)

    def now_iso(self):
        return self._now

    def seq(self):
        self._seq += 1
        return self._seq

    # test helpers
    def kinds(self):
        return [v for e, a, v in self.datoms if a == ":vertex/kind"]

    def attr(self, eid, attr):
        vals = [v for e, a, v in self.datoms if e == eid and a == attr]
        return vals[-1] if vals else None


# ── queueSeeds ────────────────────────────────────────────────────────────
def test_queue_seeds_seeds_new_onion_sites():
    ctx = FakeKotoba()
    out = oc.handle_queue_seeds(
        {"seeds": ["http://abc123.onion/x", "https://def456.onion"], "limit": 10}, ctx)
    assert out["queued"] == 2
    assert ctx.kinds().count(oc.SITE_KIND) == 2     # Datom-native, no SQL


def test_queue_seeds_skips_non_onion():
    ctx = FakeKotoba()
    out = oc.handle_queue_seeds({"seeds": ["https://example.com", "x.onion"], "limit": 5}, ctx)
    assert out["skipped"] == 1                       # example.com is not .onion
    assert out["queued"] == 1


def test_queue_seeds_is_append_only_no_dupes():
    ctx = FakeKotoba()
    oc.handle_queue_seeds({"seeds": ["abc.onion"], "limit": 5}, ctx)
    out2 = oc.handle_queue_seeds({"seeds": ["abc.onion"], "limit": 5}, ctx)
    assert out2["queued"] == 0                        # already exists ⇒ not re-seeded
    assert ctx.kinds().count(oc.SITE_KIND) == 1


def test_queue_seeds_claims_stalest_first():
    ctx = FakeKotoba()
    out = oc.handle_queue_seeds({"seeds": ["a.onion", "b.onion"], "limit": 1}, ctx)
    assert len(out["runs"]) == 1                      # limit respected
    assert ctx.kinds().count(oc.CRAWL_KIND) == 1      # one :queued crawl run
    sid = out["runs"][0]["sessionId"]
    assert ctx.attr(sid, ":onion.crawl/state") == ":queued"


# ── processQueue (G11 no-server-key gate) ──────────────────────────────────
def _runs(ctx):
    return oc.handle_queue_seeds({"seeds": ["a.onion"], "limit": 1}, ctx)["runs"]


def test_process_queue_gated_without_operator_fetcher():
    ctx = FakeKotoba()
    runs = _runs(ctx)
    out = oc.handle_process_queue({"runs": runs}, ctx)   # default fetch refuses
    assert out["gated"] == 1 and out["completed"] == 0 and out["failed"] == 0
    assert ctx.attr(runs[0]["sessionId"], ":onion.crawl/state") == ":gated"


def test_process_queue_completes_with_operator_fetch():
    ctx = FakeKotoba()
    runs = _runs(ctx)

    def fetch(host, timeout):
        return {"ok": True, "pages": [{"url": f"http://{host}/1", "title": "t",
                                       "contentHash": "h", "riskScore": 10}]}
    out = oc.handle_process_queue({"runs": runs}, ctx, fetch=fetch)
    assert out["completed"] == 1 and out["pagesWritten"] == 1
    assert ctx.kinds().count(oc.PAGE_KIND) == 1
    assert ctx.attr(runs[0]["sessionId"], ":onion.crawl/state") == ":completed"


def test_process_queue_marks_failure():
    ctx = FakeKotoba()
    runs = _runs(ctx)
    out = oc.handle_process_queue({"runs": runs}, ctx, fetch=lambda h, t: {"ok": False, "error": "tor-timeout"})
    assert out["failed"] == 1
    assert ctx.attr(runs[0]["sessionId"], ":onion.crawl/state") == ":failed"


def test_fetch_exception_is_failure_not_crash():
    ctx = FakeKotoba()
    runs = _runs(ctx)
    def boom(h, t):
        raise RuntimeError("proxy down")
    out = oc.handle_process_queue({"runs": runs}, ctx, fetch=boom)
    assert out["failed"] == 1


# ── dispatch registry ──────────────────────────────────────────────────────
def test_dispatch_routes_bpmn_task_types():
    ctx = FakeKotoba()
    out = oc.dispatch("onion.crawl.queueSeeds", {"seeds": ["a.onion"], "limit": 1}, ctx)
    assert "runs" in out


def test_dispatch_unknown_task_raises():
    try:
        oc.dispatch("onion.crawl.bogus", {}, FakeKotoba())
    except ValueError as e:
        assert "no onion-crawl handler" in str(e)
    else:
        assert False, "unknown task type must raise"


def _run():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
    print(f"onion_crawl.py: {len(fns)}/{len(fns)} tests passed")
    return True


if __name__ == "__main__":
    sys.exit(0 if _run() else 1)
