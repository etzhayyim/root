"""Offline tests for the pure assertion core (no browser, no LLM)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kotoba_e2e.signals import Request, Signals, evaluate, APPVIEW_HOST  # noqa: E402


def _sw_served_feed_req():
    return Request(
        url="https://etzhayyim.com/xrpc/app.bsky.feed.getDiscoverFeed?limit=50",
        status=200, response_headers={"x-kotoba-sw": "local-wasm-feed", "x-kotoba-src": "blocks"},
    )


def browser_only_signals():
    return Signals(
        requests=[
            Request(url="https://etzhayyim.com/kotoba/yoro-social-v1.root.json", status=200),
            Request(url="https://etzhayyim.com/kotoba/blocks/bafyreiat6d", status=200),
            _sw_served_feed_req(),
        ],
        console=["log: [kotoba-sw] block-hydrated 870 datoms"],
        sw_controller=True,
        post_count=103,
        skeleton_seen=True,
        skeleton_removed=True,
    )


def test_browser_only_passes_all_core():
    ok, checks = evaluate(browser_only_signals())
    assert ok is True
    by = {c.name: c for c in checks}
    assert by["sw_active"].passed
    assert by["blocks_hydrated"].passed
    assert by["no_risingwave_reads"].passed
    assert by["feed_served_by_sw"].passed
    assert by["skeleton_lifecycle"].passed
    assert by["posts_rendered"].passed


def test_risingwave_feed_read_fails_core():
    s = browser_only_signals()
    # a feed read that hit the RisingWave AppView → core must fail
    s.requests.append(Request(
        url=f"https://{APPVIEW_HOST}/xrpc/app.bsky.feed.getTimeline", status=200,
    ))
    ok, checks = evaluate(s)
    assert ok is False
    assert not {c.name: c for c in checks}["no_risingwave_reads"].passed


def test_no_sw_fails_core():
    s = browser_only_signals()
    s.sw_controller = False
    s.console = []
    s.requests = [r for r in s.requests if not r.header("x-kotoba-sw")]
    s.requests = [r for r in s.requests if "/kotoba/" in r.url]  # keep blocks, drop sw-served feed
    ok, checks = evaluate(s)
    assert {c.name: c for c in checks}["sw_active"].passed is False
    assert ok is False


def test_seed_fallback_counts_as_hydrated():
    s = Signals(
        requests=[
            Request(url="https://etzhayyim.com/kotoba/seed-datoms.json", status=200),
            _sw_served_feed_req(),
        ],
        sw_controller=True, post_count=10, skeleton_seen=True, skeleton_removed=True,
    )
    ok, checks = evaluate(s)
    assert {c.name: c for c in checks}["blocks_hydrated"].passed  # seed is an accepted fallback
    assert ok is True


def test_idb_served_counts_as_hydrated_no_fresh_fetch():
    # Reload served from IndexedDB: no fresh block/seed fetch this load, but the
    # SW response is stamped x-kotoba-src=idb → still browser-only hydrated.
    s = Signals(
        requests=[Request(
            url="https://etzhayyim.com/xrpc/app.bsky.feed.getDiscoverFeed",
            status=200, response_headers={"x-kotoba-sw": "local-wasm-feed", "x-kotoba-src": "idb"},
        )],
        sw_controller=True, post_count=103, skeleton_seen=True, skeleton_removed=True,
    )
    ok, checks = evaluate(s)
    assert {c.name: c for c in checks}["blocks_hydrated"].passed
    assert ok is True


def test_stuck_skeleton_flagged_quality_not_core():
    s = browser_only_signals()
    s.skeleton_removed = False
    ok, checks = evaluate(s)
    # core still ok (skeleton is a quality check), but the quality check fails
    assert ok is True
    assert {c.name: c for c in checks}["skeleton_lifecycle"].passed is False



def test_data_path_classifies_csr_sw_ssr_empty():
    from kotoba_e2e.signals import classify_data_path
    assert classify_data_path(browser_only_signals()) == "csr-sw"
    # SSR: content rendered, no client feed read
    ssr = Signals(requests=[Request(url="https://etzhayyim.com/profile/x", status=200)],
                  sw_controller=True, post_count=9, skeleton_seen=True, skeleton_removed=True)
    assert classify_data_path(ssr) == "ssr"
    # csr-net: client feed read NOT sw-served
    net = Signals(requests=[Request(url="https://etzhayyim.com/xrpc/app.bsky.feed.getTimeline", status=200)])
    assert classify_data_path(net) == "csr-net"
    assert classify_data_path(Signals()) == "empty"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn(); print(f"✓ {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} passed")
