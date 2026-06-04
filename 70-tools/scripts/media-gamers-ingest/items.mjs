#!/usr/bin/env node
// items.mjs — Serebii items DB → com.etzhayyim.apps.media_gamers.knowledge.publishGameItem
//
// Usage:
//   etzhayyim_TOKEN=$(etzhayyim agent-token --lxm com.etzhayyim.apps.media_gamers.knowledge.publishGameItem) \
//     node 70-tools/scripts/media-gamers-ingest/items.mjs \
//     --game pokemon-pokopia \
//     --index https://www.serebii.net/pokemonpokopia/items.shtml \
//     --state /tmp/pokopia-items-state.json
//
// Reads the Serebii item index page, extracts item slugs, then walks each
// item detail page to pull name / category / effect / acquisition / trade
// value. Paces 2 req/s against Serebii, 3s between PDS writes, 3-attempt retry.
// Aborts if >30% records fail (usually means RisingWave is backlogged).

import {
  fetchSerebii, publish, loadState, saveState, parseArgs,
  requireToken, paced, abortIfMostlyFail,
} from "./lib.mjs";

const NSID = "com.etzhayyim.apps.media_gamers.knowledge.publishGameItem";

const args = parseArgs(process.argv);
const game = args.game;
const indexUrl = args.index;
const statePath = args.state;
const limit = args.limit ? Number(args.limit) : Infinity;

if (!game || !indexUrl) {
  console.error("ERROR: --game <slug> and --index <serebii_index_url> required");
  process.exit(2);
}

const token = requireToken();
const state = loadState(statePath);
state[game] = state[game] || { done: [] };

function extractItemLinks(html, baseUrl) {
  // Serebii item index uses <a href="items/<slug>.shtml">NAME</a>
  const origin = new URL(baseUrl).origin;
  const base = baseUrl.replace(/[^/]+$/, "");
  const links = new Map();
  const re = /<a\s+href="(items\/[a-z0-9][a-z0-9-]*\.shtml)">([^<]{2,80})<\/a>/gi;
  let m;
  while ((m = re.exec(html)) !== null) {
    const url = base + m[1];
    const name = m[2].trim();
    const slug = m[1].match(/items\/([a-z0-9-]+)\.shtml/)[1];
    if (!links.has(slug)) links.set(slug, { slug, name, url });
  }
  return [...links.values()];
}

function extractItemDetail(html) {
  // Category, effect/description, trade value — best effort regex.
  const catMatch = html.match(/Category[\s\S]{0,60}?<td[^>]*>([^<]{2,80})<\/td>/i);
  const effectMatch = html.match(/(?:Effect|Description)[\s\S]{0,200}?<td[^>]*>([^<]{2,500})<\/td>/i);
  const sellStdMatch = html.match(/Standard[\s\S]{0,60}?(\d{2,5})/i);
  const sellFavMatch = html.match(/Favorite[\s\S]{0,60}?(\d{2,5})/i);
  const acquireMatch = html.match(/(?:Overworld|Obtained)[\s\S]{0,60}?<td[^>]*>([^<]{2,200})<\/td>/i);
  return {
    category: catMatch ? catMatch[1].trim() : null,
    effect: effectMatch ? effectMatch[1].trim() : null,
    sell_price: sellStdMatch ? Number(sellStdMatch[1]) : null,
    sell_price_favorite: sellFavMatch ? Number(sellFavMatch[1]) : null,
    acquisition: acquireMatch ? [acquireMatch[1].trim()] : [],
  };
}

function categoryToItemType(cat) {
  if (!cat) return "other";
  const c = cat.toLowerCase();
  if (c.includes("furniture")) return "tool";
  if (c.includes("utilit")) return "tool";
  if (c.includes("food") || c.includes("cook")) return "consumable";
  if (c.includes("material") || c.includes("ingredient") || c.includes("ore")) return "material";
  if (c.includes("berry") || c.includes("fruit")) return "consumable";
  if (c.includes("tool") || c.includes("equipment")) return "tool";
  if (c.includes("key")) return "key-item";
  return "other";
}

async function importOne({ slug, name, url }) {
  if (state[game].done.includes(slug)) return { ok: true, body: { skipped: true } };
  const html = await fetchSerebii(url);
  const detail = extractItemDetail(html);
  const payload = {
    game_slug: game,
    slug,
    name,
    description: detail.effect || "",
    item_type: categoryToItemType(detail.category),
    stackable: true,
    lang: "en",
    acquisition: detail.acquisition,
    effects: detail.effect ? [detail.effect] : [],
    sources: [url],
  };
  if (detail.sell_price != null) payload.sell_price = detail.sell_price;
  const r = await publish(NSID, payload, token);
  if (r.ok) {
    state[game].done.push(slug);
    saveState(statePath, state);
  }
  return r;
}

console.log(`[items] reading index ${indexUrl}`);
const indexHtml = await fetchSerebii(indexUrl);
const all = extractItemLinks(indexHtml, indexUrl);
const todo = all.slice(0, limit);
console.log(`[items] found ${all.length} links in index; importing ${todo.length}`);

const results = await paced(todo, importOne);
console.log(`\n[items] OK=${results.ok} FAIL=${results.fail}`);
for (const f of results.failed.slice(0, 10)) {
  console.log(`  fail slug=${f.item.slug}  err=${(f.error || "").slice(0, 120)}`);
}
abortIfMostlyFail(results);
