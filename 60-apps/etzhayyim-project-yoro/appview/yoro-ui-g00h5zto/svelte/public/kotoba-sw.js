// kotoba-sw.js — yoro production browser-node shim (ADR-2606013600 P1).
//
// Served at the origin ROOT (/kotoba-sw.js) so its scope is `/` and it can see
// `/xrpc/*`. Registered from +layout.svelte. Module Service Worker.
//
// NETWORK-FIRST: `/xrpc/...searchActors` goes to the live server when online
// (no staleness/shadowing). On network failure it is served from the in-browser
// kotoba-wasm read engine — offline edge resilience, no server round-trip.
//
// PERSISTENCE: the hydrated datoms are cached in IndexedDB, so a reload restores
// the node WITHOUT re-fetching the seed (reseed-free). A background refresh
// re-pulls the same-origin snapshot and re-hydrates only when it changed
// (snapshot-level delta); incremental basis_t delta activates when pointed at a
// live same-origin `datomic.datoms` endpoint.

import init, { KotobaNode } from "./kotoba/kotoba_wasm.js";

const SEED_URL = "/kotoba/seed-datoms.json"; // JSON snapshot fallback (CORS-free)
// IPFS-block path (ADR-2605312345 / 2606014600): the canonical source. The
// browser reads a tiny root pointer, then hydrates the kotoba Datom log by
// fetching CID-addressed Prolly-tree blocks and verifying each CID on ingest —
// NO kotoba query node is exposed; the only published thing is self-verifying
// content + a root hash. Falls back to the JSON snapshot if unavailable.
const ROOT_URL = "/kotoba/yoro-social-v1.root.json";
const BLOCK_URL = (cid) => `/kotoba/blocks/${cid}`;
const SEARCH_NSIDS = new Set([
  "app.bsky.actor.searchActors",
  "com.etzhayyim.yoro.actor.searchActors",
]);

// ── Browser-only feed/profile reads (ADR-2606013800 + 2605312345) ───────────
// These NSIDs are assembled ENTIRELY in the browser from the in-page kotoba
// Datom log (the same-origin seed), never from a server adapter. The apex
// Worker rewrites app.bsky.feed.* → com.etzhayyim.yoro.feed.* and forwards to
// the rw-free adapter, which does not implement them (404) — so without this
// shim the home/author feed is empty. We intercept BOTH spellings.
const FEED_TIMELINE_NSIDS = new Set([
  "app.bsky.feed.getTimeline",
  "app.bsky.feed.getDiscoverFeed",
  "com.etzhayyim.yoro.feed.getTimeline",
  "com.etzhayyim.yoro.feed.getDiscoverFeed",
]);
const FEED_AUTHOR_NSIDS = new Set([
  "app.bsky.feed.getAuthorFeed",
  "com.etzhayyim.yoro.feed.getAuthorFeed",
]);
const FEED_THREAD_NSIDS = new Set([
  "app.bsky.feed.getPostThread",
  "com.etzhayyim.yoro.feed.getPostThread",
]);
const PROFILE_NSIDS = new Set([
  "app.bsky.actor.getProfile",
  "com.etzhayyim.yoro.actor.getProfile",
]);
function isFeedNsid(nsid) {
  return (
    FEED_TIMELINE_NSIDS.has(nsid) ||
    FEED_AUTHOR_NSIDS.has(nsid) ||
    FEED_THREAD_NSIDS.has(nsid) ||
    PROFILE_NSIDS.has(nsid)
  );
}

// Raw hydrated datom array (same shape as seed-datoms.json: {e,a,v_edn,added}).
// Kept in sync by hydrate()/refreshSnapshot(); feed/profile views are built
// from THIS, in JS, so they never depend on a wasm export-shape detail.
let seedDatoms = [];
// How the local Datom log was hydrated: "blocks" (canonical CID-verified IPFS
// block path) | "seed" (JSON snapshot fallback) | "idb" | "none". Surfaced on
// feed/profile responses as x-kotoba-src for observability.
let hydrateSource = "none";

// v_edn is the EDN-encoded value; for our string-typed attrs that is exactly
// JSON.stringify(value), so JSON.parse recovers it. Posts carry a render-ready
// `:yoro.post/view` whose value is the JSON-stringified feedView object.
function edVal(v_edn) {
  try {
    return JSON.parse(v_edn);
  } catch {
    return v_edn;
  }
}

// did:web:etzhayyim.com:actor:foo  → also matches handle / bare actor segment.
function actorMatches(view, wanted) {
  if (!wanted) return true;
  const a = view && view.author ? view.author : {};
  const w = String(wanted).toLowerCase();
  return [a.did, a.handle, a.displayName]
    .filter(Boolean)
    .some((x) => String(x).toLowerCase() === w || String(x).toLowerCase().includes(w));
}

// Build the render-ready feedView post objects from the local datom log.
// Each post entity carries `:yoro.post/view` (the full app.bsky.feed.defs#postView
// produced upstream and stored at publish time), plus scalar attrs for sort/filter.
function buildPostViews(datoms) {
  const byE = new Map();
  for (const d of datoms) {
    if (!d || !d.a || !d.a.startsWith(":yoro.post/")) continue;
    let o = byE.get(d.e);
    if (!o) {
      o = {};
      byE.set(d.e, o);
    }
    const k = d.a.slice(":yoro.post/".length);
    const v = edVal(d.v_edn);
    o[k] = k === "view" ? safeParse(v) : v;
  }
  const out = [];
  for (const o of byE.values()) {
    const view = o.view && typeof o.view === "object" ? o.view : null;
    if (!view || !view.uri) continue;
    // sort key: prefer scalar createdAt, fall back to the view's record.
    view.__sortAt = o.createdAt || (view.record && view.record.createdAt) || view.indexedAt || "";
    out.push(view);
  }
  out.sort((a, b) => (b.__sortAt < a.__sortAt ? -1 : b.__sortAt > a.__sortAt ? 1 : 0));
  for (const v of out) delete v.__sortAt;
  return out;
}
function safeParse(s) {
  if (typeof s !== "string") return s;
  try {
    return JSON.parse(s);
  } catch {
    return null;
  }
}

function buildProfileView(datoms, wanted) {
  const byE = new Map();
  for (const d of datoms) {
    if (!d || !d.a || !d.a.startsWith(":yoro.profile/")) continue;
    let o = byE.get(d.e);
    if (!o) {
      o = {};
      byE.set(d.e, o);
    }
    o[d.a.slice(":yoro.profile/".length)] = edVal(d.v_edn);
  }
  const w = String(wanted || "").toLowerCase();
  let hit = null;
  for (const p of byE.values()) {
    if (!w) continue;
    if (
      String(p.did || "").toLowerCase() === w ||
      String(p.handle || "").toLowerCase() === w ||
      String(p.handle || "").toLowerCase().includes(w)
    ) {
      hit = p;
      break;
    }
  }
  if (!hit) return null;
  const posts = buildPostViews(datoms).filter((v) =>
    actorMatches(v, hit.did) || actorMatches(v, hit.handle),
  );
  return {
    did: hit.did || "",
    handle: hit.handle || "",
    displayName: hit.displayName || hit.handle || "",
    description: hit.description || "",
    avatar:
      hit.avatar ||
      `https://api.dicebear.com/9.x/identicon/svg?seed=${encodeURIComponent(hit.did || hit.handle || "")}`,
    postsCount: posts.length,
    followersCount: 0,
    followsCount: 0,
    indexedAt: hit.indexedAt || new Date(0).toISOString(),
    viewer: {},
    labels: [],
  };
}

function jsonResponse(obj, tag) {
  return new Response(JSON.stringify(obj), {
    status: 200,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "x-kotoba-sw": tag,
      "x-kotoba-src": hydrateSource,
    },
  });
}

// ── IndexedDB persistence ──────────────────────────────────────────────────
const DB_NAME = "kotoba-node";
const STORE = "state";
function openDb() {
  return new Promise((resolve, reject) => {
    const r = indexedDB.open(DB_NAME, 1);
    r.onupgradeneeded = () => r.result.createObjectStore(STORE);
    r.onsuccess = () => resolve(r.result);
    r.onerror = () => reject(r.error);
  });
}
async function idbGet(key) {
  try {
    const db = await openDb();
    return await new Promise((resolve) => {
      const req = db.transaction(STORE, "readonly").objectStore(STORE).get(key);
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => resolve(undefined);
    });
  } catch {
    return undefined;
  }
}
async function idbPut(key, value) {
  try {
    const db = await openDb();
    await new Promise((resolve) => {
      const req = db.transaction(STORE, "readwrite").objectStore(STORE).put(value, key);
      req.onsuccess = () => resolve();
      req.onerror = () => resolve();
    });
  } catch {
    /* best-effort */
  }
}

// ── OPFS append-only transaction journal (P2) ──────────────────────────────
// Local writes are durably appended to an OPFS JSONL log (one tx per line) in
// addition to the IndexedDB materialized state. The journal is the replay /
// audit / future-push source; IndexedDB is the fast restore cache.
const TX_JOURNAL = "kotoba-tx.jsonl";
async function appendTxJournal(datoms, ts) {
  try {
    const root = await navigator.storage.getDirectory();
    const fh = await root.getFileHandle(TX_JOURNAL, { create: true });
    // createSyncAccessHandle is dedicated-worker-only; in a Service Worker use
    // the async writable stream + seek-to-end for append.
    const size = (await fh.getFile()).size;
    const w = await fh.createWritable({ keepExistingData: true });
    await w.seek(size);
    await w.write(JSON.stringify({ t: ts, datoms }) + "\n");
    await w.close();
  } catch (e) {
    console.warn("[kotoba-sw] OPFS journal append failed", e);
  }
}
async function txJournalCount() {
  try {
    const root = await navigator.storage.getDirectory();
    const fh = await root.getFileHandle(TX_JOURNAL, { create: false });
    const txt = await (await fh.getFile()).text();
    return txt.split("\n").filter(Boolean).length;
  } catch {
    return 0;
  }
}

let node = null;
let ready = null;

function hydrate(datoms) {
  node = node || new KotobaNode();
  seedDatoms = Array.isArray(datoms) ? datoms : []; // feed/profile build source
  return node.loadDatoms(JSON.stringify(datoms));
}

// Canonical hydration: traverse the kotoba Prolly tree over CID-verified IPFS
// blocks. Reads the root pointer, ingests each block (ingestBlock re-hashes the
// bytes and rejects on CID mismatch — trustless), then hydrateFromProlly builds
// the read arrangements. Feed/profile builders read the materialised datoms via
// exportDatoms (same {e,a,v_edn} shape as the JSON seed). Returns true on success.
async function bootFromBlocks() {
  if (typeof KotobaNode.prototype.ingestBlock !== "function") return false; // old wasm
  const r = await fetch(ROOT_URL, { cache: "no-cache" });
  if (!r.ok) return false;
  const manifest = await r.json();
  if (!manifest || !manifest.root) return false;
  const n = new KotobaNode();
  const cids =
    Array.isArray(manifest.blocks) && manifest.blocks.length
      ? manifest.blocks
      : n.missingBlockCids(manifest.root);
  for (const cid of cids) {
    const br = await fetch(BLOCK_URL(cid), { cache: "force-cache" });
    if (!br.ok) throw new Error(`block ${cid} HTTP ${br.status}`);
    n.ingestBlock(cid, new Uint8Array(await br.arrayBuffer())); // throws on CID mismatch
  }
  const applied = n.hydrateFromProlly(manifest.root);
  if (!applied) return false;
  node = n;
  seedDatoms = JSON.parse(n.exportDatoms()); // feed/profile build source
  hydrateSource = "blocks";
  // Persist for offline reload (JSON snapshot of the block-hydrated state).
  await idbPut("datoms", seedDatoms);
  await idbPut("len", seedDatoms.length);
  console.log(
    `[kotoba-sw] block-hydrated ${applied} datoms from root ${String(manifest.root).slice(0, 16)}… (${n.blockCount()} CID-verified blocks)`,
  );
  return true;
}

async function boot() {
  await init();
  node = new KotobaNode();

  // 1) CANONICAL: hydrate from CID-verified IPFS blocks (no node exposed).
  try {
    if (await bootFromBlocks()) return;
  } catch (e) {
    console.warn("[kotoba-sw] block path failed — falling back to snapshot", e);
  }

  // 2) Reseed-free restore: if we persisted datoms before, load them and skip
  //    the network entirely. A background refresh keeps them fresh.
  const cached = await idbGet("datoms");
  if (Array.isArray(cached) && cached.length) {
    hydrate(cached);
    hydrateSource = "idb";
    console.log(`[kotoba-sw] restored ${cached.length} datoms from IndexedDB`);
    refreshSnapshot().catch(() => {});
    return;
  }

  // 3) Last resort: pull the same-origin JSON snapshot, hydrate, and persist.
  await refreshSnapshot();
}

// Snapshot-level delta: re-fetch the same-origin seed; re-hydrate + persist only
// if it differs from what we have (cheap freshness without a server query path).
async function refreshSnapshot() {
  try {
    const r = await fetch(SEED_URL, { cache: "no-cache" });
    if (!r.ok) return;
    const fresh = await r.json();
    const prevLen = (await idbGet("len")) ?? -1;
    const sig = Array.isArray(fresh) ? fresh.length : -1;
    if (sig !== prevLen || !node) {
      const n = hydrate(fresh);
      hydrateSource = "seed";
      await idbPut("datoms", fresh);
      await idbPut("len", sig);
      console.log(`[kotoba-sw] hydrated+persisted ${n} datoms (snapshot delta)`);
    }
  } catch {
    /* offline — keep whatever we restored */
  }
}

// Idempotent — runs boot() once. Called from BOTH activate and the fetch
// handler: on a cold SW restart `activate` does NOT re-fire, so the first
// intercepted request is what kicks off the IndexedDB restore.
function ensureReady() {
  if (!ready) ready = boot();
  return ready;
}

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => {
  ensureReady();
  event.waitUntil(self.clients.claim());
});

// P2 local write: the page posts {type:'transact', datoms, ts} → assert into the
// local engine, re-persist the materialized state to IndexedDB, and append the
// tx to the OPFS journal. Acks via the provided MessagePort.
self.addEventListener("message", (event) => {
  const m = event.data || {};
  if (m.type !== "transact" || !Array.isArray(m.datoms)) return;
  event.waitUntil(
    (async () => {
      let ack = { ok: false };
      try {
        await ensureReady();
        const asserted = node.transact(JSON.stringify(m.datoms));
        const full = JSON.parse(node.exportDatoms());
        await idbPut("datoms", full);
        await idbPut("len", full.length);
        await appendTxJournal(m.datoms, m.ts ?? 0);
        ack = { ok: true, asserted, total: full.length, journal: await txJournalCount() };
      } catch (e) {
        ack = { ok: false, error: String(e) };
      }
      if (event.ports && event.ports[0]) event.ports[0].postMessage(ack);
    })(),
  );
});

self.addEventListener("fetch", (event) => {
  let url;
  try {
    url = new URL(event.request.url);
  } catch {
    return;
  }
  if (url.origin !== self.location.origin) return;
  const m = url.pathname.match(/^\/xrpc\/([^/?]+)$/);
  if (!m) return;
  const nsid = m[1];
  if (!SEARCH_NSIDS.has(nsid) && !isFeedNsid(nsid)) return; // not ours → network

  // ── Browser-only feed / profile reads (kotoba-wasm Datom log) ─────────────
  // Assembled locally from the same-origin seed; on any miss/exception we fall
  // through to the network (hybrid — never makes the broken alias path worse).
  if (isFeedNsid(nsid)) {
    event.respondWith(
      (async () => {
        try {
          await ensureReady();
          const limit = Math.max(1, Math.min(100, parseInt(url.searchParams.get("limit") || "50", 10) || 50));

          if (PROFILE_NSIDS.has(nsid)) {
            const actor = url.searchParams.get("actor") || url.searchParams.get("handle") || "";
            const prof = buildProfileView(seedDatoms, actor);
            if (prof) return jsonResponse(prof, "local-wasm-profile");
            return fetch(event.request);
          }

          if (FEED_THREAD_NSIDS.has(nsid)) {
            const uri = url.searchParams.get("uri") || "";
            const view = buildPostViews(seedDatoms).find((v) => v.uri === uri);
            if (view) {
              return jsonResponse(
                { thread: { $type: "app.bsky.feed.defs#threadViewPost", post: view, replies: [] } },
                "local-wasm-thread",
              );
            }
            return fetch(event.request);
          }

          // getTimeline / getDiscoverFeed / getAuthorFeed
          let views = buildPostViews(seedDatoms);
          if (FEED_AUTHOR_NSIDS.has(nsid)) {
            const actor = url.searchParams.get("actor") || "";
            views = views.filter((v) => actorMatches(v, actor));
          }
          const feed = views.slice(0, limit).map((v) => ({ post: v }));
          // Empty local set → defer to network (don't shadow a live server with []).
          if (feed.length === 0) return fetch(event.request);
          return jsonResponse(
            { feed, cursor: "" },
            FEED_AUTHOR_NSIDS.has(nsid) ? "local-wasm-authorfeed" : "local-wasm-feed",
          );
        } catch {
          return fetch(event.request); // hybrid fallback
        }
      })(),
    );
    return;
  }

  event.respondWith(
    (async () => {
      const q = url.searchParams.get("q") || "";

      // NETWORK-FIRST: try the live server.
      let resp = null;
      let live = null;
      try {
        resp = await fetch(event.request);
        const ct = resp.headers.get("content-type") || "";
        if (!ct.includes("json")) return resp; // opaque/non-JSON → untouched
        live = await resp.clone().json().catch(() => null);
      } catch {
        resp = null;
      }

      // Local registered-actor set from the in-browser node (reliable backfill).
      let localActors = [];
      try {
        await ensureReady();
        if (node) localActors = JSON.parse(node.searchActors(q)).actors || [];
      } catch {
        /* node not ready */
      }

      if (resp && live) {
        // BACKFILL: if the live server is missing registered actors (e.g. it
        // lost data on a restart), add them back from the local seed so search
        // never silently degrades. When live is complete, pass it through
        // untouched (rich shape, correct order).
        const liveDids = new Set((live.actors || []).map((a) => a && a.did));
        const missing = localActors.filter((a) => a && a.did && !liveDids.has(a.did));
        if (missing.length === 0) return resp;
        const merged = { ...live, actors: [...(live.actors || []), ...missing] };
        merged.totalActors = merged.actors.length;
        return new Response(JSON.stringify(merged), {
          status: 200,
          headers: {
            "content-type": "application/json; charset=utf-8",
            "x-kotoba-sw": "backfill",
          },
        });
      }

      // Network failed → serve the local node (offline edge resilience).
      if (localActors.length) {
        return new Response(JSON.stringify({ actors: localActors }), {
          status: 200,
          headers: {
            "content-type": "application/json; charset=utf-8",
            "x-kotoba-sw": "local-wasm-offline",
          },
        });
      }
      return resp || Response.error();
    })(),
  );
});

// Kick off boot() as soon as the SW starts (cold restarts included), while the
// network is still up — so init() can fetch the wasm and the IndexedDB restore
// completes before any offline request arrives.
ensureReady();
