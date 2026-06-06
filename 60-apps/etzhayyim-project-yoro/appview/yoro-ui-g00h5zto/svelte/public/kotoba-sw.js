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

// ── Browser-local WRITES (post / reply / comment / like) ────────────────────
// Wikipedia-style: every write is computed AND stored in the in-page kotoba
// node, MEMBER-SIGNED (ed25519, the server never signs — ADR-2605231525), and
// appended to the append-only Datom log (revision history, 非終末論). The signed
// blocks are published to the apex separately; here we apply the write locally
// so the author sees it immediately and it survives reload (IndexedDB/OPFS).
const WRITE_NSIDS = new Set(["com.atproto.repo.createRecord"]);
// Collections we materialise into :yoro.* datoms; anything else → network.
const WRITE_COLLECTIONS = new Set([
  "app.bsky.feed.post", // post / reply / comment
  "app.bsky.feed.like",
  "app.bsky.feed.repost",
]);

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
  // Engagement counts DERIVED from the log (Wikipedia-style: counts are a
  // function of the append-only like/repost datoms, not a stored mutable field).
  const likeBy = new Map(); // postUri -> count
  const repostBy = new Map();
  for (const d of datoms) {
    if (d && d.a === ":yoro.like/subject") {
      const u = edVal(d.v_edn);
      likeBy.set(u, (likeBy.get(u) || 0) + 1);
    } else if (d && d.a === ":yoro.repost/subject") {
      const u = edVal(d.v_edn);
      repostBy.set(u, (repostBy.get(u) || 0) + 1);
    }
  }
  const out = [];
  for (const o of byE.values()) {
    const view = o.view && typeof o.view === "object" ? o.view : null;
    if (!view || !view.uri) continue;
    if (likeBy.has(view.uri)) view.likeCount = (view.likeCount || 0) + likeBy.get(view.uri);
    if (repostBy.has(view.uri)) view.repostCount = (view.repostCount || 0) + repostBy.get(view.uri);
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

// ── Member signing identity (no-server-key) ─────────────────────────────────
// A browser-held ed25519 identity (did:key). Generated once, persisted in IDB,
// reused across sessions. R0: SW-local key; a passkey/wallet-derived member key
// is the charter target (ADR-2605231525). Used to sign every local commit.
let memberDid = null;
async function ensureIdentity() {
  if (memberDid) return memberDid;
  let seedHex = await idbGet("id-seed");
  if (!seedHex) {
    const b = crypto.getRandomValues(new Uint8Array(32));
    seedHex = Array.from(b, (x) => x.toString(16).padStart(2, "0")).join("");
    await idbPut("id-seed", seedHex);
  }
  memberDid = node.useIdentity(seedHex); // did:key
  return memberDid;
}

// Sortable rkey (timestamp ms base36 + 4 random) — monotonic-ish, collision-safe.
function newRkey() {
  const r = crypto.getRandomValues(new Uint8Array(3));
  return (
    Date.now().toString(36) +
    Array.from(r, (x) => x.toString(36).padStart(2, "0")).join("").slice(0, 4)
  );
}

const edDatom = (e, a, value) => ({ e, a, v_edn: JSON.stringify(value), added: true });

// Apply a write LOCALLY: materialise :yoro.* datoms, member-sign the commit,
// persist, and inject into the live feed source. Returns the createRecord
// response {uri, cid} or null (→ caller defers to network).
async function handleCreateRecord(body) {
  const collection = body && body.collection;
  const record = (body && body.record) || {};
  if (!collection || !WRITE_COLLECTIONS.has(collection)) return null;
  await ensureReady();
  if (!node) return null;
  const did = await ensureIdentity();
  const rkey = newRkey();
  const cid = rkey; // content id placeholder (R0); real CID at publish/commit
  const uri = `at://${did}/${collection}/${rkey}`;
  const createdAt = record.createdAt || new Date().toISOString();
  const datoms = [];

  if (collection === "app.bsky.feed.post") {
    const text = typeof record.text === "string" ? record.text : "";
    const view = {
      uri,
      cid,
      rkey,
      record: {
        $type: "app.bsky.feed.post",
        text,
        createdAt,
        ...(record.embed ? { embed: record.embed } : {}),
        ...(record.reply ? { reply: record.reply } : {}),
        ...(record.facets ? { facets: record.facets } : {}),
      },
      author: {
        did,
        handle: did,
        displayName: did,
        avatar: `https://api.dicebear.com/9.x/identicon/svg?seed=${encodeURIComponent(did)}`,
      },
      indexedAt: createdAt,
      likeCount: 0,
      repostCount: 0,
      replyCount: 0,
      quoteCount: 0,
      viewCount: 0,
      text,
      facets: record.facets || [],
      ...(record.reply ? { reply: record.reply } : {}),
    };
    const e = `post:${uri}`;
    datoms.push(
      edDatom(e, ":yoro.post/uri", uri),
      edDatom(e, ":yoro.post/cid", cid),
      edDatom(e, ":yoro.post/author", did),
      edDatom(e, ":yoro.post/createdAt", createdAt),
      edDatom(e, ":yoro.post/indexedAt", createdAt),
      edDatom(e, ":yoro.post/text", text),
      edDatom(e, ":yoro.post/view", JSON.stringify(view)),
    );
  } else if (collection === "app.bsky.feed.like") {
    const subj = (record.subject && record.subject.uri) || "";
    const e = `like:${did}:${subj}`;
    datoms.push(
      edDatom(e, ":yoro.like/subject", subj),
      edDatom(e, ":yoro.like/by", did),
      edDatom(e, ":yoro.like/createdAt", createdAt),
    );
  } else if (collection === "app.bsky.feed.repost") {
    const subj = (record.subject && record.subject.uri) || "";
    const e = `repost:${did}:${subj}`;
    datoms.push(
      edDatom(e, ":yoro.repost/subject", subj),
      edDatom(e, ":yoro.repost/by", did),
      edDatom(e, ":yoro.repost/createdAt", createdAt),
    );
  }

  // Write into the kotoba node (write-set) + member-sign the commit.
  for (const d of datoms) node.assert(d.e, d.a, JSON.parse(d.v_edn));
  let signed = null;
  try {
    signed = JSON.parse(node.commitSigned()); // { root, did, sig } — member-signed
  } catch (e) {
    console.warn("[kotoba-sw] commitSigned failed (local write still applied)", e);
  }
  // Reflect in the live feed source + persist (optimistic, survives reload).
  seedDatoms = seedDatoms.concat(datoms);
  await idbPut("datoms", seedDatoms);
  await idbPut("len", seedDatoms.length);
  try {
    await appendTxJournal(datoms, Date.now()); // OPFS audit/journal
  } catch {}
  console.log(
    `[kotoba-sw] local write ${collection} by ${did.slice(0, 24)}… → ${uri.slice(-12)}${signed ? ` (signed root ${String(signed.root).slice(0, 12)}…)` : ""}`,
  );
  // Publish the new signed root + blocks so other browsers see it (best-effort).
  await publishToApex({ collection, uri });
  return { uri, cid, commit: signed ? { rev: signed.root } : undefined, validationStatus: "valid" };
}

const GRAPH = "yoro-social-v1";
const PUBLISH_URL = "/xrpc/com.etzhayyim.apps.kotoba.block.put";
// The published root this SW last rebased on (optimistic-concurrency base).
let publishedRoot = null;

// Union two datom arrays, deduped by (e, attr, value) — the CRDT merge of two
// append-only Datom sets (order-independent, idempotent).
function mergeDatoms(a, b) {
  const key = (d) => `${d.e} ${d.a} ${d.v_edn}`;
  const seen = new Set(a.map(key));
  const out = a.slice();
  for (const d of b) {
    const k = key(d);
    if (!seen.has(k)) {
      seen.add(k);
      out.push(d);
    }
  }
  return out;
}

// Hydrate a published root into a throwaway node and return its datoms (used to
// rebase on a concurrent publisher's head).
async function rootDatoms(root) {
  const n = new KotobaNode();
  for (let i = 0; i < 64; i++) {
    const miss = n.missingBlockCids(root);
    if (!miss || miss.length === 0) break;
    for (const cid of miss) {
      const br = await fetch(BLOCK_URL(cid), { cache: "force-cache" });
      if (!br.ok) throw new Error(`block ${cid} HTTP ${br.status}`);
      n.ingestBlock(cid, new Uint8Array(await br.arrayBuffer()));
    }
  }
  n.hydrateFromProlly(root);
  return JSON.parse(n.exportDatoms());
}

// Build the FULL merged tree from every current datom, member-sign the root,
// and publish (delta) to the apex under optimistic concurrency: the apex only
// advances the head if we rebased on the current head (prevRoot). On a 409 we
// merge the concurrent publisher's datoms and retry — so no edit is lost.
async function publishToApex(edit) {
  try {
    const seedHex = await idbGet("id-seed");
    if (!seedHex || typeof KotobaNode.prototype.exportBlocks !== "function") return;
    for (let attempt = 0; attempt < 4; attempt++) {
      const pub = new KotobaNode();
      pub.useIdentity(seedHex);
      for (const d of seedDatoms) {
        const val = JSON.parse(d.v_edn);
        pub.assert(d.e, d.a, typeof val === "string" ? val : JSON.stringify(val));
      }
      const signed = JSON.parse(pub.commitSigned()); // { root, did, sig }
      const blocks = JSON.parse(pub.exportBlocks()); // [{ cid, hex }]
      // DELTA: send only the blocks the apex lacks (immutable → never resent).
      let toSend = blocks;
      try {
        const hasResp = await fetch("/xrpc/com.etzhayyim.apps.kotoba.block.has", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ cids: blocks.map((b) => b.cid) }),
        });
        if (hasResp.ok) {
          const missing = new Set((await hasResp.json()).missing || []);
          toSend = blocks.filter((b) => missing.has(b.cid));
        }
      } catch {
        /* fall back to sending all */
      }
      const r = await fetch(PUBLISH_URL, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          graph: GRAPH,
          root: signed.root,
          prevRoot: publishedRoot, // optimistic-concurrency base
          did: signed.did,
          sig: signed.sig,
          blocks: toSend,
          edit,
        }),
      });
      const resJson = await r.clone().json().catch(() => ({}));

      if (r.status === 409 && resJson && resJson.currentRoot) {
        // Concurrent publisher advanced the head — merge their datoms and retry.
        try {
          const theirs = await rootDatoms(resJson.currentRoot);
          seedDatoms = mergeDatoms(seedDatoms, theirs);
        } catch (e) {
          console.warn("[kotoba-sw] rebase hydrate failed", e);
        }
        publishedRoot = resJson.currentRoot;
        console.log(`[kotoba-sw] publish conflict → rebased on ${String(resJson.currentRoot).slice(0, 12)}…, retry`);
        continue;
      }

      if (r.status === 429) {
        // Rate limited — do NOT retry. The write is already applied locally; it
        // will propagate with the next publish (which rebuilds the full tree).
        await idbPut("last-publish", { ok: false, rateLimited: true, root: signed.root, total: blocks.length });
        console.warn(`[kotoba-sw] publish rate-limited — will propagate on next write`);
        return;
      }

      if (r.ok) publishedRoot = signed.root;
      await idbPut("last-publish", {
        ok: r.ok,
        root: signed.root,
        sent: toSend.length,
        total: blocks.length,
        attempts: attempt + 1,
        ipEncrypted: !!(resJson && resJson.attest && resJson.attest.ipEncrypted),
        ipPrefix: resJson && resJson.attest ? resJson.attest.ipPrefix : "",
      });
      console.log(
        `[kotoba-sw] publish ${r.ok ? "ok" : "HTTP " + r.status} root ${String(signed.root).slice(0, 12)}… (${toSend.length}/${blocks.length} blocks, try ${attempt + 1})`,
      );
      return;
    }
    console.warn("[kotoba-sw] publish gave up after retries (local write intact)");
  } catch (e) {
    console.warn("[kotoba-sw] publish failed (local write intact)", e);
  }
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
// Resolve which root to hydrate: the LATEST published root from the apex (KV)
// if any member has published, else the static genesis pointer.
async function resolveRoot() {
  try {
    const lr = await fetch(`/xrpc/com.etzhayyim.apps.kotoba.root?graph=${GRAPH}`, { cache: "no-cache" });
    if (lr.ok) {
      const m = await lr.json();
      if (m && m.root) return m.root;
    }
  } catch {
    /* fall back to genesis */
  }
  const r = await fetch(ROOT_URL, { cache: "no-cache" });
  if (!r.ok) return null;
  const m = await r.json();
  return m && m.root ? m.root : null;
}

async function bootFromBlocks() {
  if (typeof KotobaNode.prototype.ingestBlock !== "function") return false; // old wasm
  const root = await resolveRoot();
  if (!root) return false;
  const n = new KotobaNode();
  // Iteratively fetch the covering tree: missingBlockCids(root) walks what the
  // node still needs; each block is served from /kotoba/blocks/<cid> (genesis =
  // static asset, post-genesis = apex KV) and CID-verified on ingest (trustless).
  for (let i = 0; i < 64; i++) {
    const missing = n.missingBlockCids(root);
    if (!missing || missing.length === 0) break;
    for (const cid of missing) {
      const br = await fetch(BLOCK_URL(cid), { cache: "force-cache" });
      if (!br.ok) throw new Error(`block ${cid} HTTP ${br.status}`);
      n.ingestBlock(cid, new Uint8Array(await br.arrayBuffer())); // throws on CID mismatch
    }
  }
  const applied = n.hydrateFromProlly(root);
  if (!applied) return false;
  node = n;
  seedDatoms = JSON.parse(n.exportDatoms()); // feed/profile build source
  hydrateSource = "blocks";
  publishedRoot = root; // optimistic-concurrency base for the next publish
  await idbPut("datoms", seedDatoms);
  await idbPut("len", seedDatoms.length);
  console.log(
    `[kotoba-sw] block-hydrated ${applied} datoms from root ${String(root).slice(0, 16)}… (${n.blockCount()} CID-verified blocks)`,
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

  // Passkey/wallet binding (no-server-key, ADR-2605231525): the page derives a
  // 32-byte ed25519 seed from the member's authenticator — e.g. the WebAuthn
  // PRF (hmac-secret) extension, or a wallet signature — and posts it here to
  // replace the SW-local key, so kotoba commits are signed by the MEMBER's own
  // key (not an ephemeral one). seedHex = 64 hex chars. The seed never leaves
  // the device; the server is never involved.
  if (m.type === "setIdentity" && typeof m.seedHex === "string") {
    event.waitUntil(
      (async () => {
        let ack = { ok: false };
        try {
          await ensureReady();
          await idbPut("id-seed", m.seedHex.trim());
          memberDid = node.useIdentity(m.seedHex.trim());
          ack = { ok: true, did: memberDid };
        } catch (e) {
          ack = { ok: false, error: String(e) };
        }
        if (event.ports && event.ports[0]) event.ports[0].postMessage(ack);
      })(),
    );
    return;
  }

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
  if (!SEARCH_NSIDS.has(nsid) && !isFeedNsid(nsid) && !WRITE_NSIDS.has(nsid)) return; // not ours

  // ── Browser-local WRITE (member-signed, stored in the kotoba node) ─────────
  if (WRITE_NSIDS.has(nsid)) {
    if (event.request.method !== "POST") return; // queries handled elsewhere
    event.respondWith(
      (async () => {
        try {
          const body = await event.request.clone().json();
          const res = await handleCreateRecord(body);
          if (res) return jsonResponse(res, "local-wasm-write");
          return fetch(event.request); // unsupported collection → network
        } catch (e) {
          console.warn("[kotoba-sw] write failed → network", e);
          return fetch(event.request);
        }
      })(),
    );
    return;
  }

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
