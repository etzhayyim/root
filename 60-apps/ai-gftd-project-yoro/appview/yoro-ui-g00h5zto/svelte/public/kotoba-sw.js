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

const SEED_URL = "/kotoba/seed-datoms.json"; // same-origin snapshot (CORS-free)
const SEARCH_NSIDS = new Set([
  "app.bsky.actor.searchActors",
  "app.etzhayyim.yoro.actor.searchActors",
]);

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
  return node.loadDatoms(JSON.stringify(datoms));
}

async function boot() {
  await init();
  node = new KotobaNode();

  // 1) Reseed-free restore: if we persisted datoms before, load them and skip
  //    the network entirely. A background refresh keeps them fresh.
  const cached = await idbGet("datoms");
  if (Array.isArray(cached) && cached.length) {
    hydrate(cached);
    console.log(`[kotoba-sw] restored ${cached.length} datoms from IndexedDB`);
    refreshSnapshot().catch(() => {});
    return;
  }

  // 2) First run: pull the same-origin snapshot, hydrate, and persist.
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
  if (!m || !SEARCH_NSIDS.has(m[1])) return; // not ours → default network

  event.respondWith(
    (async () => {
      // NETWORK-FIRST: live data wins when reachable.
      try {
        return await fetch(event.request);
      } catch (netErr) {
        // Offline → serve from the local wasm read node (restored from IDB).
        try {
          await ensureReady();
          if (!node) throw netErr;
          const q = url.searchParams.get("q") || "";
          return new Response(node.searchActors(q), {
            status: 200,
            headers: {
              "content-type": "application/json; charset=utf-8",
              "x-kotoba-sw": "local-wasm-offline",
            },
          });
        } catch {
          return Response.error();
        }
      }
    })(),
  );
});

// Kick off boot() as soon as the SW starts (cold restarts included), while the
// network is still up — so init() can fetch the wasm and the IndexedDB restore
// completes before any offline request arrives.
ensureReady();
