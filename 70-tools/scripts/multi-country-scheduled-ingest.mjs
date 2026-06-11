#!/usr/bin/env node
/**
 * ╔══════════════════════════════════════════════════════════════════════╗
 * ║  SUPERSEDED — DO NOT RUN ON THE RELIGIOUS-CORP SUBSTRATE              ║
 * ║                                                                       ║
 * ║  Status: pre-religious-corp commercial-fund era artifact (live BRREG  ║
 * ║          / per-country API paging at cron-tick time — VIOLATES        ║
 * ║          ADR-2605262400 §7 passive-only invariant).                   ║
 * ║                                                                       ║
 * ║  Superseded by:                                                        ║
 * ║    - ADR-2605263800 — per-country corp-registry fetchers (W2          ║
 * ║      deliverables: ca_sedar.py / au_asic.py / de_unternehmensregister ║
 * ║      .py / fr_rncs_infogreffe.py)                                     ║
 * ║    - ADR-2605263900 — per-country open-government-data fetchers       ║
 * ║      (W1+W2: us_data_gov.py / uk_data_gov_uk.py / jp_data_go_jp.py /  ║
 * ║      eu_data_europa_eu.py / fr_data_gouv_fr.py / de_govdata_de.py)    ║
 * ║                                                                       ║
 * ║  Why superseded (religious-corp substrate-fit):                       ║
 * ║    - Passive-only discipline per ADR-2605262400 §7: organisms MUST    ║
 * ║      NOT perform live per-country API paging at organism-tick time;   ║
 * ║      only pre-published bulk archives. The legacy /tmp/...-state.json ║
 * ║      offset-tracking pattern is a live-paging anti-pattern.           ║
 * ║    - Per-source acceptance flag gate (~/.etzhayyim/source-acceptance/ ║
 * ║      <source>.toml) supersedes the implicit cron-driven scheduling    ║
 * ║      (operators explicitly accept upstream ToS once, then the         ║
 * ║      e7m-dataset CLI handles cadence-respect)                         ║
 * ║    - State now lives in `com.etzhayyim.substrate.datasetPin` PDS      ║
 * ║      records + IPFS revision-content-hash (NOT /tmp/*.json)           ║
 * ║                                                                       ║
 * ║  Operator action:                                                     ║
 * ║    - Replace cron-driven multi-country paging with `e7m-dataset pull  ║
 * ║      <source>` per the W1/W2 fetcher table in ADR-2605263800 §2 +     ║
 * ║      ADR-2605263900 §2.                                               ║
 * ║                                                                       ║
 * ║  Removal scheduled: ADR-2605263800 W4 + ADR-2605263900 W4 deliverable.║
 * ╚══════════════════════════════════════════════════════════════════════╝
 *
 * Scheduled (resumable) wrapper for multi-country-direct-ingest.
 *
 * Tracks per-source page offset in /tmp/multi-country-ingest-state.json so
 * each cron fire ingests the next slice without re-fetching.
 *
 * Usage (called from cron):
 *   node 70-tools/scripts/multi-country-scheduled-ingest.mjs --source nor --pages 5 --page-size 200
 *
 * State file format:
 *   { "nor": { "lastPage": 42, "totalIngested": 8400, "ts": "..." }, ... }
 *
 * API rate limit handling:
 *   - BRREG NOR: max offset 10,000 → use organisasjonsform filter cycling
 *   - PRH FIN: paginated via page=N (no apparent ceiling)
 *   - data.gov.il ISR: paginated via offset
 *   - SEC EDGAR: full list, paginate locally
 *
 * Reset state for a source:
 *   node ... --source nor --reset
 */

import { readFile, writeFile } from "node:fs/promises";
import { spawnSync } from "node:child_process";

const STATE_FILE = "/tmp/multi-country-ingest-state.json";

const args = process.argv.slice(2);
function getArg(name, fallback) {
  const idx = args.indexOf(`--${name}`);
  if (idx === -1) return fallback;
  return args[idx + 1] ?? fallback;
}
function hasFlag(name) {
  return args.includes(`--${name}`);
}

const SOURCE = getArg("source", "");
const PAGES = Number(getArg("pages", "5"));
const PAGE_SIZE = Number(getArg("page-size", "100"));
const ORGFORM = getArg("orgform", ""); // NOR partition by organisasjonsform
const RESET = hasFlag("reset");

if (!SOURCE) {
  console.error("Usage: --source <nor|fin|cze|isr|usa> [--pages N] [--page-size N] [--orgform XX] [--reset]");
  process.exit(1);
}

const STATE_KEY = ORGFORM ? `${SOURCE}:${ORGFORM}` : SOURCE;

async function loadState() {
  try {
    const raw = await readFile(STATE_FILE, "utf8");
    return JSON.parse(raw);
  } catch {
    return {};
  }
}

async function saveState(state) {
  await writeFile(STATE_FILE, JSON.stringify(state, null, 2));
}

async function main() {
  const state = await loadState();
  const src = state[STATE_KEY] ?? { lastPage: -1, totalIngested: 0 };

  if (RESET) {
    state[STATE_KEY] = { lastPage: -1, totalIngested: 0, ts: new Date().toISOString() };
    await saveState(state);
    console.log(`[scheduled-ingest] reset state for ${SOURCE}`);
    return;
  }

  const startPage = src.lastPage + 1;
  console.log(`[scheduled-ingest] ${SOURCE}: start_page=${startPage} pages=${PAGES} page_size=${PAGE_SIZE}`);

  // Invoke the underlying ingest script
  const result = spawnSync("node", [
    "/Users/junkawasaki/github/etzhayyim-root/70-tools/scripts/multi-country-direct-ingest.mjs",
    "--source", SOURCE,
    "--pages", String(PAGES),
    "--page-size", String(PAGE_SIZE),
    "--start-page", String(startPage),
  ], { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });

  const stdout = result.stdout ?? "";
  const stderr = result.stderr ?? "";
  console.log(stdout);
  if (stderr) console.error(stderr);

  // Parse "Inserted: NN" line
  const match = stdout.match(/Inserted:\s+(\d+)/);
  const inserted = match ? Number(match[1]) : 0;

  // Detect API failure (so we don't bump offset on failure)
  const failed = /fetch failed/i.test(stdout);
  const pagesActuallyDone = failed ? Math.floor(inserted / PAGE_SIZE) : PAGES;

  // Update state — only advance lastPage by pages successfully completed
  state[SOURCE] = {
    lastPage: startPage + pagesActuallyDone - 1,
    totalIngested: (src.totalIngested ?? 0) + inserted,
    lastInserted: inserted,
    lastFailed: failed,
    ts: new Date().toISOString(),
  };
  await saveState(state);

  console.log(`[scheduled-ingest] ${SOURCE}: inserted=${inserted} new_total=${state[SOURCE].totalIngested} next_page=${state[SOURCE].lastPage + 1} failed=${failed}`);
}

main().catch((e) => {
  console.error("FATAL:", e);
  process.exit(1);
});
