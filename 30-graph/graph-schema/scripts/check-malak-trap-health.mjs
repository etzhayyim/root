import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import process from "node:process";
import pg from "pg";

const { Client } = pg;

const MAILER_REPO = "did:web:ml1nb0nd.gftd.ai";
const INBOUND_COLLECTION = "ai.gftd.apps.mailer.inboundEmail";
const PDS_ORIGIN = process.env.PDS_ORIGIN || "https://atproto.gftd.ai";
const LAUNCHD_LABEL = "ai.gftd.malak-trap-sync";

function sha256(value) {
  return createHash("sha256").update(String(value)).digest("hex");
}

function localPart(address) {
  return String(address || "").trim().toLowerCase().split("@")[0] || "";
}

function numberEnv(name, fallback, min, max) {
  const n = Number.parseInt(process.env[name] || "", 10);
  if (!Number.isFinite(n)) return fallback;
  return Math.max(min, Math.min(max, n));
}

async function fetchInboundRecords(limit) {
  const url = new URL(`${PDS_ORIGIN.replace(/\/+$/, "")}/xrpc/com.atproto.repo.listRecords`);
  url.searchParams.set("repo", MAILER_REPO);
  url.searchParams.set("collection", INBOUND_COLLECTION);
  url.searchParams.set("limit", String(limit));
  const resp = await fetch(url);
  const text = await resp.text();
  if (!resp.ok) throw new Error(`listRecords failed: ${resp.status} ${text.slice(0, 500)}`);
  const data = JSON.parse(text);
  return Array.isArray(data.records) ? data.records : [];
}

async function fetchTrapRows(client) {
  const { rows } = await client.query(`
    SELECT trap_id, trap_kind, address, provider, status
    FROM vertex_malak_phishing_trap
    ORDER BY trap_kind, address
  `);
  return rows;
}

async function fetchEvidenceRows(client) {
  const { rows } = await client.query(`
    SELECT trap_id, trap_kind, recipient, provider_message_id, received_at, created_at
    FROM vertex_malak_trap_message
    ORDER BY received_at DESC
  `);
  return rows;
}

function launchdStatus() {
  try {
    const domain = `gui/${process.getuid()}/${LAUNCHD_LABEL}`;
    const text = execFileSync("launchctl", ["print", domain], { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
    const state = text.match(/\bstate = ([^\n]+)/)?.[1]?.trim() || "unknown";
    const lastExitCode = text.match(/\blast exit code = ([^\n]+)/)?.[1]?.trim() || "";
    const runInterval = text.match(/\brun interval = ([^\n]+)/)?.[1]?.trim() || "";
    const runs = text.match(/\bruns = ([^\n]+)/)?.[1]?.trim() || "";
    return { installed: true, label: LAUNCHD_LABEL, state, lastExitCode, runInterval, runs };
  } catch {
    return { installed: false, label: LAUNCHD_LABEL };
  }
}

function summarize(records, traps, evidenceRows) {
  const activeEmailTraps = traps
    .filter((trap) => trap.trap_kind === "email" && trap.status === "active")
    .map((trap) => ({ ...trap, toLocalHash: sha256(localPart(trap.address)) }));
  const trapByHash = new Map(activeEmailTraps.map((trap) => [trap.toLocalHash, trap]));
  const pdsTrapRecords = records.filter((record) => {
    const value = record.value && typeof record.value === "object" ? record.value : {};
    return trapByHash.has(String(value.toLocalHash || ""));
  });
  const providerMessageIds = new Set(
    pdsTrapRecords.map((record) => String(record.value?.messageId || record.uri || "")).filter(Boolean),
  );
  const evidenceProviderMessageIds = new Set(evidenceRows.map((row) => String(row.provider_message_id || "")).filter(Boolean));
  const missingEvidence = [...providerMessageIds].filter((id) => !evidenceProviderMessageIds.has(id));
  const latestPdsMs = Math.max(0, ...pdsTrapRecords.map((record) => Number(record.value?.receivedAtMs || 0)));
  const latestEvidenceMs = Math.max(0, ...evidenceRows.map((row) => Date.parse(row.received_at || "") || 0));
  const lagMs = latestPdsMs > 0 && latestEvidenceMs > 0 ? Math.max(0, latestPdsMs - latestEvidenceMs) : null;

  return {
    activeEmailTrapCount: activeEmailTraps.length,
    scannedInboundCount: records.length,
    pdsTrapInboundCount: pdsTrapRecords.length,
    evidenceCount: evidenceRows.length,
    missingEvidenceCount: missingEvidence.length,
    missingEvidenceProviderMessageIds: missingEvidence,
    latestPdsTrapReceivedAt: latestPdsMs > 0 ? new Date(latestPdsMs).toISOString() : "",
    latestEvidenceReceivedAt: latestEvidenceMs > 0 ? new Date(latestEvidenceMs).toISOString() : "",
    lagMs,
    trapRatio: records.length > 0 ? pdsTrapRecords.length / records.length : 0,
  };
}

async function main() {
  const databaseUrl = process.env.DATABASE_URL || process.env.RW_URL || process.env.RW_CONN;
  const limit = numberEnv("MALAK_TRAP_HEALTH_LIMIT", 100, 1, 100);
  if (!databaseUrl) throw new Error("DATABASE_URL, RW_URL, or RW_CONN is required");

  const client = new Client({ connectionString: databaseUrl });
  await client.connect();
  try {
    const [traps, evidenceRows, records] = await Promise.all([
      fetchTrapRows(client),
      fetchEvidenceRows(client),
      fetchInboundRecords(limit),
    ]);
    const summary = summarize(records, traps, evidenceRows);
    const launchd = launchdStatus();
    const ok = summary.activeEmailTrapCount > 0
      && summary.missingEvidenceCount === 0
      && launchd.installed
      && (launchd.lastExitCode === "" || launchd.lastExitCode === "0");

    console.log(JSON.stringify({
      ok,
      status: ok ? "ok" : "degraded",
      checkedAt: new Date().toISOString(),
      launchd,
      ...summary,
    }, null, 2));
    if (!ok && process.argv.includes("--strict")) process.exitCode = 2;
  } finally {
    await client.end();
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
