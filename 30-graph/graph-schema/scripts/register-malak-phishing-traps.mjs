import { createHash } from "node:crypto";
import process from "node:process";
import pg from "pg";

const { Client } = pg;

const MALAK_DID = "did:web:malak.gftd.ai";
const DEFAULT_EMAIL_TRAP = "spamtrap@malak.gftd.ai";
const DEFAULT_GFTD_AI_EMAIL_TRAP = "trap-email-malak-spamtrap-primary@gftd.ai";

function splitList(value) {
  return String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function stableTrapId(kind, address) {
  if (kind === "email" && address === DEFAULT_EMAIL_TRAP) {
    return "trap-email-malak-spamtrap-primary";
  }
  const digest = createHash("sha256").update(`${kind}:${address}`).digest("hex").slice(0, 16);
  return `trap-${kind}-${digest}`;
}

function validEmail(address) {
  return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(address);
}

function validSmsNumber(address) {
  return /^\+[1-9]\d{7,14}$/.test(address);
}

function buildTrapRows(env) {
  const emailProvider = env.MALAK_TRAP_EMAIL_PROVIDER || "gftd-owned-inbound-mail";
  const smsProvider = env.MALAK_TRAP_SMS_PROVIDER || "telnyx";
  const legalBasis = env.MALAK_TRAP_LEGAL_BASIS || "owned_inbound_spamtrap_defensive_cti";
  const retentionPolicy = env.MALAK_TRAP_RETENTION_POLICY || "hash_and_preview_only";
  const now = new Date().toISOString();
  const createdDate = now.slice(0, 10);

  const emails = new Set([
    DEFAULT_EMAIL_TRAP,
    DEFAULT_GFTD_AI_EMAIL_TRAP,
    ...splitList(env.MALAK_TRAP_EMAIL),
    ...splitList(env.MALAK_TRAP_EMAILS),
  ]);
  const smsNumbers = new Set([
    ...splitList(env.MALAK_TELNYX_TRAP_NUMBER),
    ...splitList(env.MALAK_TELNYX_TRAP_NUMBERS),
    ...splitList(env.TELNYX_PHONE_NUMBER),
  ]);

  const rows = [];
  for (const address of emails) {
    if (!validEmail(address)) throw new Error(`invalid trap email: ${address}`);
    const trapId = stableTrapId("email", address);
    rows.push({
      trapId,
      trapKind: "email",
      address,
      provider: emailProvider,
      label: address === DEFAULT_EMAIL_TRAP ? "Malak primary inbound-only phishing spamtrap" : "Malak inbound-only phishing spamtrap",
      legalBasis,
      retentionPolicy,
      status: "active",
      sensitivityOrd: 100,
      createdAt: now,
      createdDate,
    });
  }

  for (const address of smsNumbers) {
    if (!validSmsNumber(address)) throw new Error(`invalid SMS trap number, expected E.164: ${address}`);
    rows.push({
      trapId: stableTrapId("sms", address),
      trapKind: "sms",
      address,
      provider: smsProvider,
      label: "Malak inbound-only SMS phishing trap",
      legalBasis,
      retentionPolicy,
      status: "active",
      sensitivityOrd: 120,
      createdAt: now,
      createdDate,
    });
  }

  return rows;
}

async function insertTrap(client, row) {
  await client.query(
    `
      INSERT INTO vertex_malak_phishing_trap (
        vertex_id,
        rkey,
        repo,
        trap_id,
        trap_kind,
        address,
        provider,
        label,
        legal_basis,
        retention_policy,
        status,
        created_at,
        updated_at,
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
        $11, $12, $12, CAST($13 AS DATE), CAST($14 AS BIGINT), $3, $3, $3, $3, $3
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_malak_phishing_trap WHERE trap_id = $4
      )
    `,
    [
      `at://${MALAK_DID}/ai.gftd.apps.malak.phishingTrap/${row.trapId}`,
      row.trapId,
      MALAK_DID,
      row.trapId,
      row.trapKind,
      row.address,
      row.provider,
      row.label,
      row.legalBasis,
      row.retentionPolicy,
      row.status,
      row.createdAt,
      row.createdDate,
      row.sensitivityOrd,
    ],
  );
}

async function main() {
  const dryRun = process.argv.includes("--dry-run");
  const databaseUrl = process.env.DATABASE_URL || process.env.RW_URL || process.env.RW_CONN;
  const rows = buildTrapRows(process.env);

  if (dryRun) {
    console.log(JSON.stringify({ dryRun: true, trapCount: rows.length, traps: rows }, null, 2));
    return;
  }

  if (!databaseUrl) {
    throw new Error("DATABASE_URL, RW_URL, or RW_CONN is required unless --dry-run is used");
  }

  const client = new Client({ connectionString: databaseUrl });
  await client.connect();
  try {
    for (const row of rows) await insertTrap(client, row);
    await client.query("FLUSH");
  } finally {
    await client.end();
  }
  console.log(JSON.stringify({ ok: true, trapCount: rows.length, traps: rows.map(({ trapId, trapKind, address, provider }) => ({ trapId, trapKind, address, provider })) }, null, 2));
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
