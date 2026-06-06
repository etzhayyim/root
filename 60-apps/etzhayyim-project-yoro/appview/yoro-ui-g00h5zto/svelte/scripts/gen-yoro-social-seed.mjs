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
const LIMIT = limitArg >= 0 ? parseInt(argv[limitArg + 1], 10) || 100 : 100;
const ORIGIN = process.env.FEED_ORIGIN || "https://etzhayyim.com";
const FEED_URL = `${ORIGIN}/xrpc/app.bsky.feed.getFeed?feed=etzhayyim&limit=${LIMIT}`;

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

async function main() {
  console.log(`→ fetching feed: ${FEED_URL}`);
  const r = await fetch(FEED_URL, { headers: { accept: "application/json" } });
  if (!r.ok) throw new Error(`getFeed HTTP ${r.status}`);
  const body = await r.json();
  const items = Array.isArray(body.feed) ? body.feed : [];
  console.log(`  got ${items.length} feed items`);

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
