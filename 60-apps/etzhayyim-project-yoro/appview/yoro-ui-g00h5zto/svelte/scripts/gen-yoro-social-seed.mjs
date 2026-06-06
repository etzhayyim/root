#!/usr/bin/env node
/**
 * gen-yoro-social-seed.mjs — regenerate the browser kotoba node's same-origin
 * seed (`public/kotoba/seed-datoms.json`) so it carries POST datoms, not just
 * actor profiles.
 *
 * WHY: the seed shipped only `:yoro.profile/*` datoms (12 actors), so the
 * in-browser kotoba node had nothing to build a feed from — `/` showed no
 * posts. The posts live in the AT Protocol AppView (`app.bsky.feed.getFeed`,
 * which still returns real records); this script datafies them into the kotoba
 * Datom log so the Service Worker (kotoba-sw.js) can assemble the home /
 * author / discover feed and post threads ENTIRELY in the browser — no
 * server-side feed adapter (ADR-2605312345 Datom log canonical; ADR-2605215000
 * no commercial backend; ADR-2606013800 same-origin read).
 *
 * Datom shape mirrors the existing seed: {e, a, v_edn, added} where v_edn is the
 * EDN-encoded value — for our string attrs that is exactly JSON.stringify(value).
 * Each post additionally carries a render-ready `:yoro.post/view` whose value is
 * the JSON-stringified app.bsky.feed.defs#postView (the SW serves it verbatim,
 * guaranteeing UI shape-fidelity with what the AppView already produced).
 *
 * Usage:
 *   node scripts/gen-yoro-social-seed.mjs               # fetch live feed, rewrite seed
 *   FEED_ORIGIN=https://etzhayyim.com node scripts/...  # override source origin
 *   node scripts/gen-yoro-social-seed.mjs --limit 200   # more posts
 *
 * The build's sync-static.mjs mirrors public/ → static/, so writing public/ is
 * enough; we also write static/ directly so a no-build smoke test sees it.
 */
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const svelteDir = resolve(here, "..");
const publicSeed = resolve(svelteDir, "public/kotoba/seed-datoms.json");
const staticSeed = resolve(svelteDir, "../static/kotoba/seed-datoms.json");

const argv = process.argv.slice(2);
const limitArg = argv.indexOf("--limit");
// --limit caps the TOTAL post set (bounds the browser download). The discover
// getFeed returns ~100 with no cursor, so coverage beyond that comes from
// paginating each distinct author's getAuthorFeed (which DOES return a cursor).
const TOTAL_CAP = limitArg >= 0 ? parseInt(argv[limitArg + 1], 10) || 500 : 500;
const PER_AUTHOR_CAP = 300; // pages of 100; bounds any single prolific author
const ORIGIN = process.env.FEED_ORIGIN || "https://etzhayyim.com";
const FEED_URL = `${ORIGIN}/xrpc/app.bsky.feed.getFeed?feed=etzhayyim&limit=100`;

// EDN-encode a JS string value the way the seed does (== JSON.stringify).
const edn = (v) => JSON.stringify(v);

function existingProfileDatoms() {
  // Preserve the actor-profile datoms already in the seed (searchActors source).
  if (!existsSync(publicSeed)) return [];
  try {
    const arr = JSON.parse(readFileSync(publicSeed, "utf8"));
    return Array.isArray(arr) ? arr.filter((d) => d && typeof d.a === "string" && d.a.startsWith(":yoro.profile/")) : [];
  } catch {
    return [];
  }
}

function postDatoms(items) {
  const out = [];
  const seen = new Set();
  for (const it of items) {
    const view = it && it.post ? it.post : null;
    if (!view || !view.uri || seen.has(view.uri)) continue;
    // Drop malformed/corrupt posts before they enter the browser-only seed: an
    // empty author DID or an `at:///…` URI with no repo DID (both observed in the
    // AppView feed) render as a broken-link card that can resolve no profile/thread.
    if (!view.author || !view.author.did) continue;
    if (view.uri.includes(':///')) continue;
    seen.add(view.uri);
    const e = `post:${view.uri}`;
    const rec = view.record || {};
    const push = (a, value) => out.push({ e, a, v_edn: edn(value), added: true });
    push(":yoro.post/uri", String(view.uri));
    if (view.cid) push(":yoro.post/cid", String(view.cid));
    if (view.author && view.author.did) push(":yoro.post/author", String(view.author.did));
    if (view.author && view.author.handle) push(":yoro.post/authorHandle", String(view.author.handle));
    const createdAt = rec.createdAt || view.indexedAt || "";
    if (createdAt) push(":yoro.post/createdAt", String(createdAt));
    if (view.indexedAt) push(":yoro.post/indexedAt", String(view.indexedAt));
    if (typeof view.text === "string") push(":yoro.post/text", view.text);
    // render-ready full postView (string value = JSON of the view object).
    push(":yoro.post/view", JSON.stringify(view));
  }
  return out;
}

async function getJson(url) {
  const r = await fetch(url, { headers: { accept: "application/json" } });
  if (!r.ok) throw new Error(`HTTP ${r.status} ${url}`);
  return r.json();
}

// Paginate one author's getAuthorFeed via its cursor, up to PER_AUTHOR_CAP.
async function authorItems(did) {
  const out = [];
  let cursor = "";
  for (let page = 0; page < Math.ceil(PER_AUTHOR_CAP / 100); page++) {
    const u = `${ORIGIN}/xrpc/app.bsky.feed.getAuthorFeed?actor=${encodeURIComponent(did)}&limit=100${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ""}`;
    let body;
    try {
      body = await getJson(u);
    } catch (e) {
      console.warn(`    author ${did} page ${page} failed: ${e.message}`);
      break;
    }
    const items = Array.isArray(body.feed) ? body.feed : [];
    out.push(...items);
    if (!body.cursor || items.length === 0) break;
    cursor = body.cursor;
  }
  return out;
}

async function main() {
  console.log(`→ discover feed: ${FEED_URL}`);
  const body = await getJson(FEED_URL);
  const seed = Array.isArray(body.feed) ? body.feed : [];
  console.log(`  got ${seed.length} discover items`);

  // Distinct authors → paginate each to expand coverage past the 100 cap.
  const authors = [...new Set(seed.map((x) => x.post?.author?.did).filter(Boolean))];
  console.log(`  ${authors.length} distinct authors → paginating getAuthorFeed`);

  const byUri = new Map();
  const add = (it) => {
    const uri = it?.post?.uri;
    if (uri && !byUri.has(uri)) byUri.set(uri, it);
  };
  seed.forEach(add);
  for (const did of authors) {
    if (byUri.size >= TOTAL_CAP) break;
    const items = await authorItems(did);
    items.forEach(add);
    console.log(`    ${did}: +${items.length} (total ${byUri.size})`);
  }

  const items = [...byUri.values()].slice(0, TOTAL_CAP);
  console.log(`  → ${items.length} unique posts (cap ${TOTAL_CAP})`);

  const profiles = existingProfileDatoms();
  const posts = postDatoms(items);
  const postCount = new Set(posts.filter((d) => d.a === ":yoro.post/uri").map((d) => d.e)).size;
  const merged = [...profiles, ...posts];

  const json = JSON.stringify(merged, null, 0) + "\n";
  writeFileSync(publicSeed, json);
  console.log(`✓ wrote ${publicSeed} (${profiles.length} profile + ${posts.length} post datoms = ${postCount} posts)`);
  try {
    writeFileSync(staticSeed, json);
    console.log(`✓ mirrored ${staticSeed}`);
  } catch (e) {
    console.warn(`  (static mirror skipped: ${e.message})`);
  }
}

main().catch((e) => {
  console.error("✗", e.message);
  process.exit(1);
});
