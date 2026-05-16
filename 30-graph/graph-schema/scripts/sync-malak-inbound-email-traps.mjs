import { createHash } from "node:crypto";
import process from "node:process";
import pg from "pg";

const { Client } = pg;

const MALAK_DID = "did:web:malak.gftd.ai";
const MAILER_REPO = "did:web:ml1nb0nd.gftd.ai";
const INBOUND_COLLECTION = "ai.gftd.apps.mailer.inboundEmail";
const PDS_ORIGIN = process.env.PDS_ORIGIN || "https://atproto.gftd.ai";

function sha256(value) {
  return createHash("sha256").update(String(value)).digest("hex");
}

function localPart(address) {
  return String(address || "").trim().toLowerCase().split("@")[0] || "";
}

function stableId(prefix, value) {
  return `${prefix}-${sha256(value).slice(0, 20)}`;
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

async function fetchEmailTraps(client) {
  const { rows } = await client.query(`
    SELECT trap_id, address, provider
    FROM vertex_malak_phishing_trap
    WHERE trap_kind = 'email'
      AND status = 'active'
  `);
  return rows.map((row) => ({
    trapId: row.trap_id,
    address: row.address,
    provider: row.provider || "gftd-owned-inbound-mail",
    toLocalHash: sha256(localPart(row.address)),
  }));
}

function buildTrapMessage(record, trap) {
  const value = record.value && typeof record.value === "object" ? record.value : {};
  const providerMessageId = String(value.messageId || record.uri || "");
  const receivedAtMs = Number(value.receivedAtMs || 0);
  const receivedAt = receivedAtMs > 0 ? new Date(receivedAtMs).toISOString() : new Date().toISOString();
  const payloadHash = sha256(JSON.stringify({ uri: record.uri, cid: record.cid, value }));
  const messageId = stableId("trapmsg", providerMessageId || payloadHash);
  const evidenceId = stableId("evidence", `${trap.trapId}:${providerMessageId || payloadHash}`);
  const subject = value.subject === "[encrypted]" ? "[encrypted]" : String(value.subject || "");
  const bodyPreview = [
    "redacted inbound email trap message",
    `recipient=${trap.address}`,
    `toLocalHash=${value.toLocalHash || trap.toLocalHash}`,
    `contentProtection=${value.contentProtection || "unknown"}`,
    `pdsUri=${record.uri || ""}`,
  ].join("; ");

  return {
    messageId,
    evidenceId,
    trapId: trap.trapId,
    trapKind: "email",
    recipient: trap.address,
    provider: trap.provider,
    providerMessageId,
    sender: value.fromAddressHash ? `sha256:${value.fromAddressHash}` : "[encrypted]",
    subject,
    bodyPreview,
    urlsJson: "[]",
    headersJson: JSON.stringify({ pdsUri: record.uri || "", cid: record.cid || "", contentProtection: value.contentProtection || "" }),
    rawPayloadHash: payloadHash,
    payloadHash,
    tlp: "amber",
    receivedAt,
    createdAt: new Date().toISOString(),
  };
}

async function insertTrapMessage(client, row) {
  await client.query(
    `
      INSERT INTO vertex_malak_trap_message (
        vertex_id,
        rkey,
        repo,
        message_id,
        evidence_id,
        trap_id,
        trap_kind,
        recipient,
        provider,
        provider_message_id,
        sender,
        subject,
        body_preview,
        urls_json,
        headers_json,
        raw_payload_hash,
        payload_hash,
        tlp,
        received_at,
        created_at,
        created_date,
        sensitivity_ord,
        owner_did,
        org_id,
        user_id,
        actor_did,
        org_did
      )
      SELECT
        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
        $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
        CAST($21 AS DATE), CAST($22 AS BIGINT), $3, $3, $3, $3, $3
      WHERE NOT EXISTS (
        SELECT 1
        FROM vertex_malak_trap_message
        WHERE provider_message_id = $10
           OR evidence_id = $5
           OR payload_hash = $17
      )
    `,
    [
      `at://${MALAK_DID}/ai.gftd.apps.malak.trapMessage/${row.messageId}`,
      row.messageId,
      MALAK_DID,
      row.messageId,
      row.evidenceId,
      row.trapId,
      row.trapKind,
      row.recipient,
      row.provider,
      row.providerMessageId,
      row.sender,
      row.subject,
      row.bodyPreview,
      row.urlsJson,
      row.headersJson,
      row.rawPayloadHash,
      row.payloadHash,
      row.tlp,
      row.receivedAt,
      row.createdAt,
      row.createdAt.slice(0, 10),
      100,
    ],
  );
}

async function main() {
  const dryRun = process.argv.includes("--dry-run");
  const databaseUrl = process.env.DATABASE_URL || process.env.RW_URL || process.env.RW_CONN;
  const limit = numberEnv("MALAK_TRAP_SYNC_LIMIT", 100, 1, 100);
  if (!databaseUrl && !dryRun) throw new Error("DATABASE_URL, RW_URL, or RW_CONN is required unless --dry-run is used");

  const client = databaseUrl ? new Client({ connectionString: databaseUrl }) : null;
  if (client) await client.connect();
  try {
    const traps = client ? await fetchEmailTraps(client) : [];
    const trapByHash = new Map(traps.map((trap) => [trap.toLocalHash, trap]));
    const records = await fetchInboundRecords(limit);
    const rows = records
      .map((record) => {
        const value = record.value && typeof record.value === "object" ? record.value : {};
        const hash = String(value.toLocalHash || "");
        const trap = trapByHash.get(hash);
        return trap ? buildTrapMessage(record, trap) : null;
      })
      .filter(Boolean);

    if (!dryRun && client) {
      for (const row of rows) await insertTrapMessage(client, row);
      await client.query("FLUSH");
    }

    console.log(JSON.stringify({
      ok: true,
      dryRun,
      trapCount: traps.length,
      scanned: records.length,
      matched: rows.length,
      messages: rows.map((row) => ({
        messageId: row.messageId,
        evidenceId: row.evidenceId,
        trapId: row.trapId,
        recipient: row.recipient,
        providerMessageId: row.providerMessageId,
      })),
    }, null, 2));
  } finally {
    if (client) await client.end();
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
