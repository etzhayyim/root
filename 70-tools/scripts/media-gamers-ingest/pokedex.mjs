#!/usr/bin/env node
// pokedex.mjs — PokeAPI → com.etzhayyim.apps.media_gamers.knowledge.publishPokemon
//
// Switched from Serebii HTML scraping to PokeAPI REST (JSON) in 2026-04-20:
// Serebii pokedex-swsh now uses slug redirects + a single HTML page contains the
// game-wide type chart which pollutes regex type extraction. PokeAPI is the
// canonical structured source for names/types/stats/abilities/heights/weights.
//
// Usage:
//   etzhayyim_TOKEN=$(etzhayyim agent-token --lxm com.etzhayyim.apps.media_gamers.knowledge.publishPokemon) \
//     node 70-tools/scripts/media-gamers-ingest/pokedex.mjs \
//     --game pokemon-legends-z-a \
//     --start 1 --end 151 \
//     --state /tmp/zapokedex.json

import {
  publish, loadState, saveState, parseArgs,
  requireToken, paced, abortIfMostlyFail,
} from "./lib.mjs";
import { setTimeout as delay } from "node:timers/promises";

const NSID = "com.etzhayyim.apps.media_gamers.knowledge.publishPokemon";
const POKEAPI_BASE = process.env.POKEAPI_BASE || "https://pokeapi.co/api/v2/pokemon";
const POKEAPI_DELAY_MS = 300; // ~3 req/s against public PokeAPI (polite)

const args = parseArgs(process.argv);
const game = args.game;
const start = Number(args.start || 1);
const end = Number(args.end || 151);
const statePath = args.state;

if (!game) {
  console.error("ERROR: --game <game_slug> required (e.g. pokemon-legends-z-a)");
  process.exit(2);
}

const token = requireToken();
const state = loadState(statePath);
state[game] = state[game] || { done: [] };

async function fetchPokemon(id) {
  await delay(POKEAPI_DELAY_MS);
  const res = await fetch(`${POKEAPI_BASE}/${id}`, {
    headers: { "User-Agent": "media-gamers-ingest/1 (etzhayyim)" },
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`pokeapi ${id} -> HTTP ${res.status}`);
  return await res.json();
}

function extractPayload(data, gameSlug) {
  const statByName = (name) => data.stats.find((s) => s.stat.name === name)?.base_stat ?? 0;
  return {
    game_slug: gameSlug,
    slug: String(data.name),
    name: String(data.name).replace(/(^|-)(\w)/g, (_, sep, ch) => (sep ? "-" : "") + ch.toUpperCase()).replace(/-/g, " "),
    dex_no: Number(data.id),
    types: data.types.map((t) => t.type.name),
    abilities: data.abilities.map((a) => a.ability.name),
    base_stats: {
      hp: statByName("hp"),
      atk: statByName("attack"),
      def: statByName("defense"),
      spa: statByName("special-attack"),
      spd: statByName("special-defense"),
      spe: statByName("speed"),
    },
    // PokeAPI height is in decimetres (1/10 m) and weight in hectograms — the
    // AT Lexicon integer units match directly (height_cm = decimetres * 10).
    height_cm: Number(data.height) * 10,
    weight_hg: Number(data.weight),
    base_exp: data.base_experience ? Number(data.base_experience) : undefined,
    lang: "en",
    sources: [`${POKEAPI_BASE}/${data.id}`],
  };
}

async function importOne(dexNo) {
  if (state[game].done.includes(dexNo)) return { ok: true, body: { skipped: true } };
  const data = await fetchPokemon(dexNo);
  if (!data) return { ok: false, body: { error: `404 at pokeapi ${dexNo}`, skipped: true } };
  const payload = extractPayload(data, game);
  if (!payload.name || payload.types.length === 0) {
    return { ok: false, body: { error: `malformed data for dex ${dexNo}` } };
  }
  const r = await publish(NSID, payload, token);
  if (r.ok) {
    state[game].done.push(dexNo);
    saveState(statePath, state);
  }
  return r;
}

console.log(`[pokedex] importing dex ${start}..${end} for game=${game} via PokeAPI`);
const dexList = Array.from({ length: end - start + 1 }, (_, i) => start + i);
const results = await paced(dexList, importOne);
console.log(`\n[pokedex] OK=${results.ok} FAIL=${results.fail}`);
for (const f of results.failed.slice(0, 10)) {
  console.log(`  fail dex=${f.item}  err=${(f.error || "").slice(0, 120)}`);
}
abortIfMostlyFail(results);
