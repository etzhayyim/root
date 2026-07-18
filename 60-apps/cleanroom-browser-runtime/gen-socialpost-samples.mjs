// gen-socialpost-samples.mjs
//
// Materialize sample DRY-RUN socialpost events for the L4 cohort by running
// each actor's runtime (create one record per entity) and collecting the
// app.bsky.feed.post-shaped events its Datom writes emit. Proves the
// `socialpost` capability is operational (dry-run, G8-gated) — nothing posts
// outward. Output: 00-contracts/schemas/cleanroom-socialpost-samples.json
//
// Run: node 60-apps/cleanroom-browser-runtime/gen-socialpost-samples.mjs
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { KotobaActor } from "./kotoba-runtime.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "../..");
const idx = JSON.parse(readFileSync(resolve(ROOT, "00-contracts/schemas/cleanroom-actors.index.json"), "utf8"));

const samples = [];
let total = 0;
for (const a of idx.actors.filter((x) => x.tier === "L4")) {
  const m = JSON.parse(readFileSync(resolve(ROOT, `../com-etzhayyim-${a.handle}/manifest.json`), "utf8"));
  const actor = new KotobaActor(m);
  // one create per entity → one dry-run post each
  for (const e of actor.entities) actor.create(e, {});
  const feed = actor.socialFeed();
  total += feed.length;
  samples.push({ handle: a.handle, did: a.did, posts: feed.slice(0, 3) });
}

const doc = {
  schemaVersion: "1.0",
  kind: "socialpost-samples",
  lexicon: "app.bsky.feed.post",
  mode: "dry-run",
  gate: "G8 (outward posting gated — these samples never leave the page)",
  adr: ["260607"],
  cohort: "L4",
  actorCount: samples.length,
  sampledPosts: total,
  samples,
};
const out = resolve(ROOT, "00-contracts/schemas/cleanroom-socialpost-samples.json");
writeFileSync(out, JSON.stringify(doc, null, 2) + "\n");
console.log(`wrote ${out}: ${samples.length} actors, ${total} dry-run posts`);
