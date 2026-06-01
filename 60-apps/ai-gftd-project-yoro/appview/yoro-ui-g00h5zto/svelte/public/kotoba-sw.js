// kotoba-sw.js — yoro production browser-node shim (ADR-2606013600 P1).
//
// Served at the origin ROOT (/kotoba-sw.js) so its scope is `/` and it can see
// `/xrpc/*`. Registered from +layout.svelte. Module Service Worker.
//
// Production posture = NETWORK-FIRST: when online, `/xrpc/...searchActors` goes
// to the live server unchanged (no staleness, no shadowing). When the network
// fails (offline / server unreachable), the request is served from the
// in-browser kotoba read engine (kotoba-wasm) hydrated from a same-origin seed
// snapshot — edge resilience without a server round-trip. Everything we don't
// recognise is left to the network entirely.

import init, { KotobaNode } from "./kotoba/kotoba_wasm.js";

const SEED_URL = "/kotoba/seed-datoms.json"; // same-origin snapshot (CORS-free)
const SEARCH_NSIDS = new Set([
  "app.bsky.actor.searchActors",
  "app.etzhayyim.yoro.actor.searchActors",
]);

let node = null;
let ready = null;

async function boot() {
  await init();
  node = new KotobaNode();
  try {
    const r = await fetch(SEED_URL, { cache: "no-cache" });
    if (r.ok) {
      const seed = await r.json();
      const n = node.loadDatoms(JSON.stringify(seed));
      console.log(`[kotoba-sw] offline fallback ready: ${n} datoms`);
    }
  } catch (e) {
    /* offline at activate — node stays empty until a later boot */
  }
}

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => {
  ready = boot();
  event.waitUntil(self.clients.claim());
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
        // Offline → serve from the local wasm read node.
        try {
          if (ready) await ready;
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
