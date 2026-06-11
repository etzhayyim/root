// Shared helpers for media-gamers-ingest scripts.
// Polite pacing + retry loop. Reused by pokedex.mjs / items.mjs.

import { readFileSync, writeFileSync } from "node:fs";
import { setTimeout as delay } from "node:timers/promises";

export const PDS_BASE = "https://a7m8oocs.etzhayyim.com";
export const SEREBII_DELAY_MS = 500; // 2 req/s — polite
export const PDS_DELAY_MS = 3000; // 3s between PDS writes
export const MAX_ATTEMPTS = 5;
export const RETRY_BACKOFF_MS = 3000;

export function requireToken() {
  const t = process.env.etzhayyim_TOKEN;
  if (!t) {
    console.error("ERROR: set etzhayyim_TOKEN (run: etzhayyim agent-token --lxm <NSID>)");
    process.exit(2);
  }
  return t;
}

export function parseArgs(argv) {
  const out = {};
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const k = a.slice(2);
      const v = argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[++i] : true;
      out[k] = v;
    }
  }
  return out;
}

export async function fetchSerebii(url) {
  await delay(SEREBII_DELAY_MS);
  const res = await fetch(url, {
    headers: { "User-Agent": "media-gamers-ingest/1 (etzhayyim, one-shot offline importer)" },
  });
  if (res.status === 404) return null; // caller treats null as skip
  if (!res.ok) throw new Error(`serebii ${url} -> HTTP ${res.status}`);
  return await res.text();
}

export async function publish(nsid, payload, token) {
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    const controller = new AbortController();
    const to = setTimeout(() => controller.abort(), 60_000);
    try {
      const res = await fetch(`${PDS_BASE}/xrpc/${nsid}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
      clearTimeout(to);
      const text = await res.text();
      let body;
      try { body = JSON.parse(text); } catch { body = { error: text.slice(0, 200) }; }
      if (res.ok && body.ok) return { ok: true, body, attempt };
      if (body?.error?.includes("hung")) {
        // transient infra — back off and retry
        if (attempt < MAX_ATTEMPTS) await delay(RETRY_BACKOFF_MS);
        continue;
      }
      return { ok: false, body, attempt };
    } catch (e) {
      clearTimeout(to);
      if (attempt < MAX_ATTEMPTS) await delay(RETRY_BACKOFF_MS);
      else return { ok: false, body: { error: String(e) }, attempt };
    }
  }
  return { ok: false, body: { error: "max attempts exhausted" }, attempt: MAX_ATTEMPTS };
}

export function loadState(path) {
  if (!path) return {};
  try { return JSON.parse(readFileSync(path, "utf8")); } catch { return {}; }
}
export function saveState(path, state) {
  if (!path) return;
  writeFileSync(path, JSON.stringify(state, null, 2));
}

export async function paced(items, fn) {
  const results = { ok: 0, fail: 0, failed: [] };
  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const r = await fn(item, i);
    if (r.ok) results.ok++;
    else { results.fail++; results.failed.push({ item, error: r.body?.error || "unknown" }); }
    if (i < items.length - 1) await delay(PDS_DELAY_MS);
  }
  return results;
}

export function abortIfMostlyFail(results, threshold = 0.3) {
  const total = results.ok + results.fail;
  if (total === 0) return;
  const failRate = results.fail / total;
  if (failRate > threshold) {
    console.error(`\n>>> failure rate ${(failRate * 100).toFixed(1)}% > ${threshold * 100}% threshold`);
    console.error(">>> infra likely unstable — stop and retry later");
    process.exit(1);
  }
}
