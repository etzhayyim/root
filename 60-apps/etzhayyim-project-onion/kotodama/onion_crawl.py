#!/usr/bin/env python3
"""onion crawl — py-kotodama worker, runs on kotoba-wasm + py-kotodama (Datom-native).

ADR-2606071800 (substrate boundary) + 00-contracts/bpmn/com/etzhayyim/onion/crawlSeeds.bpmn.

The BPMN process `onion_crawl_seeds` (timer R/PT6H + manual) has two service tasks whose
zeebe:taskDefinition types are handled here:

  onion.crawl.queueSeeds   seed new .onion sites + claim the stalest for a crawl run
  onion.crawl.processQueue fetch each claimed run + append page records

This worker is the kotoba-native replacement for the legacy LangServer/k8s pod that wrote
vertex_onion_* rows directly via Hyperdrive (substrate-boundary violation). It now runs as a
**py-kotodama primitive inside a kotoba-wasm component**: all state lives in the kotoba Datom
log, read via kotoba-kqe Datalog and written via `transact` (no RisingWave/Hyperdrive/Kysely).

Constitutional posture:
  - substrate: kotoba Datom log only; reads `ctx.query` (kotoba-kqe), writes `ctx.transact`.
  - no-server-key / G11: the live darkweb fetch (Tor + darkweb-proxy) is an INJECTED capability;
    without an operator-provided fetcher, process_queue refuses to fetch and marks runs :gated.
  - Murakumo-only: any page classification is via the kotoba `llm` host binding (not used here).
  - the handlers are PURE over an injected `KotobaCtx`, so they run identically in-wasm
    (host binding) and under test (in-memory fake) — the kotoba-wasm wiring is the only seam.

stdlib only.
"""
from __future__ import annotations

from typing import Callable, Protocol
from urllib.parse import urlparse

SITE_KIND = "vertex_onion_site"
PAGE_KIND = "vertex_onion_page"
CRAWL_KIND = "vertex_onion_crawl"
OWNER_DID = "did:web:onion.etzhayyim.com"


class KotobaCtx(Protocol):
    """The kotoba-wasm host seam: kotoba-kqe read + Datom transact. In production this is
    backed by the component's `kotoba` host import; under test, an in-memory fake."""
    def query(self, datalog: str) -> list: ...
    def transact(self, datoms: list) -> None: ...
    def now_iso(self) -> str: ...
    def seq(self) -> int: ...


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def onion_host(url: str) -> str:
    try:
        h = urlparse(url if "://" in url else f"http://{url}").hostname or ""
        return h
    except ValueError:
        return ""


def slug_for_host(host: str) -> str:
    base = host[:-6] if host.endswith(".onion") else host
    return "".join(c if c.isalnum() else "_" for c in base)[:64]


def _site_datoms(host: str, category, now_iso: str, seq: int) -> list:
    slug = slug_for_host(host)
    vid = f"at://{OWNER_DID}/ai.etzhayyim.apps.onion.site/{slug}"
    return [
        [vid, ":vertex/kind", SITE_KIND],
        [vid, ":onion.site/vertex-id", vid],
        [vid, ":onion.site/onion-host", host],
        [vid, ":onion.site/owner-did", OWNER_DID],
        [vid, ":onion.site/category", category],
        [vid, ":onion.site/risk-score", 0],
        [vid, ":onion.site/reachable", True],
        [vid, ":onion.site/first-seen", now_iso],
        [vid, ":onion.site/last-seen", None],   # NULL → next tick claims as stalest
        [vid, ":onion.site/_seq", seq],
    ]


def _last_seen_key(last):
    """Sort key for staleness: NULL (never crawled) first, then oldest ISO timestamp."""
    return (0, "") if last in (None, "", "null") else (1, str(last))


# --------------------------------------------------------------------------- #
# onion.crawl.queueSeeds
# --------------------------------------------------------------------------- #
def handle_queue_seeds(job: dict, ctx: KotobaCtx) -> dict:
    """Seed new .onion sites from `seeds` (append-only; existing hosts are not duplicated),
    then claim the `limit` stalest sites for a crawl run (NULL last-seen first). Appends a
    :queued vertex_onion_crawl Datom per claimed run. BPMN IO: seeds/category/limit →
    queued/skipped/runs."""
    seeds = [str(u) for u in (job.get("seeds") or []) if u][:50]
    category = job.get("category") or None
    limit = int(job.get("limit", 10))
    now = ctx.now_iso()
    base_seq = ctx.seq()

    # existing sites by host (kotoba-kqe read)
    existing_rows = ctx.query(
        f'[:find ?host ?last :where [?e :vertex/kind "{SITE_KIND}"] '
        f'[?e :onion.site/onion-host ?host] [?e :onion.site/last-seen ?last]]')
    sites = {r[0]: r[1] for r in existing_rows}

    queued = 0
    skipped = 0
    new_datoms: list = []
    for url in seeds:
        host = onion_host(url)
        if not host.endswith(".onion"):
            skipped += 1
            continue
        if host in sites:
            continue                      # append-only: do not duplicate
        new_datoms.extend(_site_datoms(host, category, now, base_seq + queued))
        sites[host] = None                # newly seeded ⇒ NULL last-seen (claimable)
        queued += 1
    if new_datoms:
        ctx.transact(new_datoms)

    # claim the stalest sites for a crawl run
    claimable = sorted(sites.items(), key=lambda kv: _last_seen_key(kv[1]))[:limit]
    runs: list = []
    run_datoms: list = []
    for i, (host, _last) in enumerate(claimable):
        session_id = f"onion:crawl:{host}:{base_seq + i}"
        runs.append({"host": host, "sessionId": session_id})
        run_datoms.extend([
            [session_id, ":vertex/kind", CRAWL_KIND],
            [session_id, ":onion.crawl/onion-host", host],
            [session_id, ":onion.crawl/session-id", session_id],
            [session_id, ":onion.crawl/started-at", now],
            [session_id, ":onion.crawl/state", ":queued"],
        ])
    if run_datoms:
        ctx.transact(run_datoms)

    return {"queued": queued, "skipped": skipped, "runs": runs}


# --------------------------------------------------------------------------- #
# onion.crawl.processQueue
# --------------------------------------------------------------------------- #
def _gated_fetch(host: str, timeout_sec: int) -> dict:
    """Default fetcher — REFUSES (no-server-key / G11). A live crawl needs an operator-provided
    fetcher that drives the Tor + darkweb-proxy capability; without it, runs are :gated."""
    return {"ok": False, "gated": True, "pages": []}


def handle_process_queue(job: dict, ctx: KotobaCtx,
                         fetch: Callable[[str, int], dict] | None = None) -> dict:
    """Process each claimed run: fetch the host (INJECTED capability; default refuses, G11),
    append vertex_onion_page Datoms, and mark the run + site. BPMN IO: runs/timeoutSec →
    processed/completed/failed/pagesWritten. A :gated run (no operator fetcher) is neither
    completed nor failed — it stays claimable for a later authorized run."""
    runs = job.get("runs") or []
    timeout_sec = int(job.get("timeoutSec", 45))
    do_fetch = fetch or _gated_fetch
    now = ctx.now_iso()

    processed = completed = failed = gated = pages_written = 0
    for run in runs:
        host = run.get("host")
        session_id = run.get("sessionId")
        processed += 1
        try:
            res = do_fetch(host, timeout_sec)
        except Exception as e:  # a fetch exception is a failed run, not a crash
            res = {"ok": False, "error": str(e), "pages": []}

        if res.get("gated"):
            gated += 1
            ctx.transact([[session_id, ":onion.crawl/state", ":gated"]])
            continue
        if not res.get("ok"):
            failed += 1
            ctx.transact([
                [session_id, ":onion.crawl/state", ":failed"],
                [session_id, ":onion.crawl/finished-at", now],
                [session_id, ":onion.crawl/error", str(res.get("error", "unknown"))],
            ])
            continue

        # success — append a page record per fetched page + close the run + stamp the site
        page_datoms: list = []
        for j, page in enumerate(res.get("pages", [])):
            pid = f"{session_id}:page:{j}"
            page_datoms.extend([
                [pid, ":vertex/kind", PAGE_KIND],
                [pid, ":onion.page/onion-host", host],
                [pid, ":onion.page/onion-url", page.get("url", "")],
                [pid, ":onion.page/title", page.get("title")],
                [pid, ":onion.page/content-hash", page.get("contentHash")],
                [pid, ":onion.page/risk-score", int(page.get("riskScore", 0))],
                [pid, ":onion.page/crawled-at", now],
            ])
            pages_written += 1
        page_datoms.extend([
            [session_id, ":onion.crawl/state", ":completed"],
            [session_id, ":onion.crawl/finished-at", now],
            [session_id, ":onion.crawl/page-count", len(res.get("pages", []))],
            # stamp the site so it is no longer the stalest (host vertex_id derived from slug)
            [f"at://{OWNER_DID}/ai.etzhayyim.apps.onion.site/{slug_for_host(host)}",
             ":onion.site/last-seen", now],
        ])
        ctx.transact(page_datoms)
        completed += 1

    return {"processed": processed, "completed": completed, "failed": failed,
            "gated": gated, "pagesWritten": pages_written}


# --------------------------------------------------------------------------- #
# BPMN taskDefinition → handler registry (the kotoba-wasm job dispatch entry)
# --------------------------------------------------------------------------- #
TASK_HANDLERS = {
    "onion.crawl.queueSeeds": handle_queue_seeds,
    "onion.crawl.processQueue": handle_process_queue,
}


def dispatch(task_type: str, job: dict, ctx: KotobaCtx, **kw) -> dict:
    """Entry point the kotoba-wasm component calls for each Zeebe job. Routes a BPMN
    taskDefinition type to its handler; an unknown type is an explicit error (not a no-op)."""
    handler = TASK_HANDLERS.get(task_type)
    if handler is None:
        raise ValueError(f"no onion-crawl handler for task type {task_type!r}")
    return handler(job, ctx, **kw)
