"""Pure assertions over captured browser signals.

The browser layer (Playwright) captures network requests, console messages and a
few DOM facts; these PURE functions turn them into a pass/fail verdict for the
"browser-only kotoba" contract. No browser, no LLM, no network here — so the
whole assertion core is unit-testable offline (test_signals.py).

The contract being verified (the work shipped in commits 5afe52..63f6c9):
  * the kotoba Service Worker is active and SERVES feed/profile reads,
  * those reads are hydrated from content-addressed IPFS blocks
    (/kotoba/yoro-social-v1.root.json + /kotoba/blocks/<cid>), NOT from a server,
  * NO feed read reaches the RisingWave AppView (atproto.etzhayyim.com),
  * the boot skeleton renders then is removed (no blank screen, no stuck overlay),
  * at least one post is rendered.
"""

from __future__ import annotations

from dataclasses import dataclass, field

APPVIEW_HOST = "atproto.etzhayyim.com"
FEED_READ_NSIDS = (
    "app.bsky.feed.getTimeline",
    "app.bsky.feed.getDiscoverFeed",
    "app.bsky.feed.getAuthorFeed",
    "app.bsky.feed.getPostThread",
    "app.bsky.actor.getProfile",
)


@dataclass
class Request:
    url: str
    method: str = "GET"
    status: int = 0
    response_headers: dict = field(default_factory=dict)

    def header(self, name: str) -> str:
        # header names are case-insensitive
        low = name.lower()
        for k, v in (self.response_headers or {}).items():
            if k.lower() == low:
                return v
        return ""


@dataclass
class Signals:
    requests: list = field(default_factory=list)        # list[Request]
    console: list = field(default_factory=list)         # list[str]
    sw_controller: bool = False                          # navigator.serviceWorker.controller set
    post_count: int = 0                                  # rendered post cards
    skeleton_seen: bool = False
    skeleton_removed: bool = False


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""


def _is_feed_read(url: str) -> bool:
    return any(("/xrpc/" + n) in url for n in FEED_READ_NSIDS)


def check_sw_active(s: Signals) -> Check:
    served = [r for r in s.requests if r.header("x-kotoba-sw")]
    sw_log = any("[kotoba-sw]" in c for c in s.console)
    ok = s.sw_controller or bool(served) or sw_log
    return Check(
        "sw_active", ok,
        f"controller={s.sw_controller} sw-served-responses={len(served)} sw-log={sw_log}",
    )


def check_blocks_hydrated(s: Signals) -> Check:
    """The browser served kotoba reads from its OWN hydrated Datom log.

    Two kinds of evidence, either suffices:
      (a) fresh fetches of the content-addressed source this load
          (/kotoba/yoro-social-v1.root.json + /kotoba/blocks/<cid>, or the seed
          snapshot fallback), OR
      (b) an SW-served response stamped `x-kotoba-src` ∈ {blocks,idb,seed} — proof
          the data came from the in-browser kotoba node even when this (reload)
          load was served from the IndexedDB cache without re-fetching blocks.
    """
    root = [r for r in s.requests if "/kotoba/yoro-social-v1.root.json" in r.url]
    blocks = [r for r in s.requests if "/kotoba/blocks/" in r.url]
    seed = [r for r in s.requests if "/kotoba/seed-datoms.json" in r.url]
    src_hdrs = [
        r.header("x-kotoba-src") for r in s.requests
        if r.header("x-kotoba-src") in ("blocks", "idb", "seed")
    ]
    fetched = bool(root and blocks) or bool(seed)
    served_from_log = bool(src_hdrs)
    ok = fetched or served_from_log
    src = (
        "blocks" if (root and blocks) else
        "seed" if seed else
        (src_hdrs[0] if src_hdrs else "none")
    )
    return Check(
        "blocks_hydrated", ok,
        f"root={len(root)} blocks={len(blocks)} seed={len(seed)} "
        f"sw-src={src_hdrs[:1]} src={src}",
    )


def check_no_risingwave_reads(s: Signals) -> Check:
    """No feed/profile READ may reach the RisingWave AppView host."""
    offenders = [
        r.url for r in s.requests
        if APPVIEW_HOST in r.url and _is_feed_read(r.url)
    ]
    return Check(
        "no_risingwave_reads", len(offenders) == 0,
        "clean" if not offenders else f"{len(offenders)} feed read(s) hit {APPVIEW_HOST}: {offenders[:3]}",
    )


def check_feed_served_by_sw(s: Signals) -> Check:
    """Feed reads that DID happen were answered by the SW (x-kotoba-sw header)."""
    feed_reqs = [r for r in s.requests if _is_feed_read(r.url)]
    if not feed_reqs:
        return Check("feed_served_by_sw", False, "no feed read observed at all")
    by_sw = [r for r in feed_reqs if r.header("x-kotoba-sw")]
    ok = len(by_sw) == len(feed_reqs)
    return Check("feed_served_by_sw", ok, f"{len(by_sw)}/{len(feed_reqs)} feed reads SW-served")


def check_skeleton_lifecycle(s: Signals) -> Check:
    ok = s.skeleton_seen and s.skeleton_removed
    return Check("skeleton_lifecycle", ok, f"seen={s.skeleton_seen} removed={s.skeleton_removed}")


def check_posts_rendered(s: Signals) -> Check:
    return Check("posts_rendered", s.post_count > 0, f"posts={s.post_count}")


def classify_data_path(s: Signals) -> str:
    """How did this page's DATA reach the screen?

      'csr-sw'  — a client feed/profile XRPC was issued AND SW-served (browser-only)
      'csr-net' — a client feed/profile XRPC was issued but NOT SW-served (hit network)
      'ssr'     — content rendered with NO client data XRPC ⇒ server-side rendered
                  (the data source is a server fetch, INVISIBLE to the browser — so
                  'no_risingwave_reads' is a false-clean for these pages)
      'empty'   — no client data read and no content rendered
    """
    feed_reqs = [r for r in s.requests if _is_feed_read(r.url)]
    if feed_reqs:
        return "csr-sw" if all(r.header("x-kotoba-sw") for r in feed_reqs) else "csr-net"
    return "ssr" if s.post_count > 0 else "empty"


def check_data_path(s: Signals) -> Check:
    """Informational: classify the data path + flag SSR honestly.

    Passes for 'csr-sw' (true browser-only) and (vacuously) is informational
    otherwise; the message names the path so an SSR page is not mistaken for
    browser-only. 'csr-net' is the only one that means a browser-visible server
    read happened (already caught by no_risingwave_reads if it was the AppView).
    """
    path = classify_data_path(s)
    ok = path == "csr-sw"
    note = {
        "csr-sw": "feed/profile read SW-served browser-side (browser-only)",
        "csr-net": "client read went to network (NOT SW-served)",
        "ssr": "server-side rendered — data source NOT browser-observable (no client XRPC)",
        "empty": "no client data read and nothing rendered",
    }[path]
    return Check("data_path", ok, f"{path} — {note}")


# Core (must-pass) checks vs informational ones. The "browser-only" verdict turns
# on the core set; skeleton/posts are quality signals.
CORE_CHECKS = (check_sw_active, check_blocks_hydrated, check_no_risingwave_reads)
QUALITY_CHECKS = (check_data_path, check_feed_served_by_sw, check_skeleton_lifecycle, check_posts_rendered)


def evaluate(s: Signals) -> tuple[bool, list]:
    """Return (browser_only_ok, all_checks). browser_only_ok = all CORE pass."""
    core = [fn(s) for fn in CORE_CHECKS]
    quality = [fn(s) for fn in QUALITY_CHECKS]
    ok = all(c.passed for c in core)
    return ok, core + quality
