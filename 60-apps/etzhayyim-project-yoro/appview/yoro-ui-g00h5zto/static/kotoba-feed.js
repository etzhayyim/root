// kotoba-feed.js — pure feed/profile assembly + CRDT merge over the kotoba Datom
// log. Extracted from kotoba-sw.js so the SW and node tests share ONE source of
// truth for the logic that decides what users see and whether edits are lost.
// No Service-Worker globals, no wasm — pure functions over plain datom arrays
// (shape: { e, a, v_edn, added }).

// v_edn is the EDN-encoded value; for our string-typed attrs that is exactly
// JSON.stringify(value), so JSON.parse recovers it. Posts carry a render-ready
// `:yoro.post/view` whose value is the JSON-stringified feedView object.
export function edVal(v_edn) {
  try {
    return JSON.parse(v_edn);
  } catch {
    return v_edn;
  }
}

export function safeParse(s) {
  if (typeof s !== "string") return s;
  try {
    return JSON.parse(s);
  } catch {
    return null;
  }
}

// did:web:etzhayyim.com:actor:foo  → also matches handle / bare actor segment.
export function actorMatches(view, wanted) {
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
export function buildPostViews(datoms) {
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

export function buildProfileView(datoms, wanted) {
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
  const posts = buildPostViews(datoms).filter((v) => actorMatches(v, hit.did) || actorMatches(v, hit.handle));
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

// Union two datom arrays, deduped by (e, attr, value) — the CRDT merge of two
// append-only Datom sets (order-independent, idempotent).
export function mergeDatoms(a, b) {
  const key = (d) => `${d.e} ${d.a} ${d.v_edn}`;
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
