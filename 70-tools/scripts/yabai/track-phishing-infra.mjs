#!/usr/bin/env node
// Thin driver for com.etzhayyim.apps.yabai.trackPhishingInfra BPMN.
//
// Replaces: 60-apps/etzhayyim-project-yabai/tools/track-phishing-infra/track-phishing-infra.mjs
// The legacy script iterated phishing_url entities and ran local shell
// whois / dig / openssl / curl per row. This driver fetches the target
// list from RisingWave and POSTs each domain to the BPMN, which does
// all probes via primitives (http.fetch + tls.probe + db.insert).
//
// Usage:
//   node 70-tools/scripts/yabai/track-phishing-infra.mjs             # all entities
//   node 70-tools/scripts/yabai/track-phishing-infra.mjs --limit 5   # smoke
//   node 70-tools/scripts/yabai/track-phishing-infra.mjs --domain x  # one-off
//
// Env:
//   DISPATCHER_URL  (default https://dispatcher.etzhayyim.com)
//   RW_URL          (default $(security find-generic-password -s etzhayyim.rw -a ROOT_URL -w))

import { spawn, spawnSync } from "node:child_process";

const DISPATCHER = (process.env.DISPATCHER_URL ?? "https://dispatcher.etzhayyim.com").replace(/\/$/, "");
const args = process.argv.slice(2);
const flag = (n) => args.includes(n);
const opt = (n, d) => { const i = args.indexOf(n); return i >= 0 ? args[i + 1] : d; };
const LIMIT = opt("--limit", null);
const ONLY_DOMAIN = opt("--domain", null);

function sh(cmd, cmdArgs, opts = {}) {
  return new Promise((resolve) => {
    const p = spawn(cmd, cmdArgs, { stdio: ["ignore", "pipe", "pipe"] });
    let out = "", err = "";
    const t = setTimeout(() => p.kill("SIGKILL"), opts.timeoutMs ?? 60000);
    p.stdout.on("data", (b) => (out += b));
    p.stderr.on("data", (b) => (err += b));
    p.on("close", (c) => { clearTimeout(t); resolve({ code: c ?? -1, stdout: out, stderr: err }); });
  });
}

function rwUrl() {
  if (process.env.RW_URL) return process.env.RW_URL;
  const r = spawnSync("security", ["find-generic-password", "-s", "etzhayyim.rw", "-a", "ROOT_URL", "-w"]);
  return r.stdout.toString().trim();
}

async function psql(sql) {
  const r = await sh("psql", [rwUrl(), "-tA", "-F", "\t", "-c", sql], { timeoutMs: 30000 });
  if (r.code !== 0) throw new Error("psql: " + r.stderr);
  return r.stdout.trim();
}

async function trackOne(entityId, rawValue) {
  const domain = rawValue.replace(/^https?:\/\//, "").replace(/\/.*$/, "").trim().toLowerCase();
  const body = { entityId, domain };
  const r = await sh("curl", [
    "-sS", "--max-time", "80",
    "-X", "POST", `${DISPATCHER}/xrpc/com.etzhayyim.apps.yabai.trackPhishingInfra`,
    "-H", "Content-Type: application/json",
    "-d", JSON.stringify(body),
  ], { timeoutMs: 90000 });
  if (r.code !== 0) throw new Error(`xrpc: ${r.stderr}`);
  return JSON.parse(r.stdout);
}

async function main() {
  let targets;
  if (ONLY_DOMAIN) {
    targets = [{ entity_id: `url-${ONLY_DOMAIN.replace(/\./g, "_")}`, value: ONLY_DOMAIN }];
  } else {
    const limitClause = LIMIT ? `LIMIT ${parseInt(LIMIT, 10)}` : "";
    const raw = await psql(
      `SELECT entity_id, value FROM vertex_yabai_entity ` +
      `WHERE entity_type = 'phishing_url' AND value IS NOT NULL ` +
      `ORDER BY created_at DESC ${limitClause}`,
    );
    targets = raw.split("\n").filter(Boolean).map((line) => {
      const [entity_id, value] = line.split("\t");
      return { entity_id, value };
    });
  }
  console.error(`# yabai-track-phishing-infra: ${targets.length} target(s)`);

  let i = 0;
  for (const t of targets) {
    i++;
    const t0 = Date.now();
    try {
      const r = await trackOne(t.entity_id, t.value);
      const v = r.variables || {};
      const ms = Date.now() - t0;
      console.error(
        `[${i}/${targets.length}] ${v.domain} ip=${v.firstIp ?? "-"} ` +
        `asn=${v.asnBody?.as_number ?? "-"} reg=${v.rdap?.registrar ?? "-"} ` +
        `tls=${v.tlsOk ? "y" : "n"} anomalies=${(v.tlsAnomalies || []).join(",") || "-"} ` +
        `inserted=${v.inserted ?? "-"} (${ms}ms)`,
      );
    } catch (e) {
      console.error(`[${i}/${targets.length}] ${t.value} FAILED: ${e.message}`);
    }
  }
  console.error("# done");
}

main().catch((e) => { console.error(e); process.exit(1); });
