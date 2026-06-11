#!/usr/bin/env node
/**
 * Bulk-migrate existing `did:web:authn.etzhayyim.com:user:*` accounts to
 * `did:erc725:etzhayyim:260425:<addr>` on the etzhayyim private chain (ADR-0074
 * Step 4 of the sign-up migration).
 *
 * For each legacy account this script:
 *
 *   1. Computes seedHash = keccak256("etzhayyim-account:migrate:" || did:web)
 *   2. POSTs to authz `/internal/provision-root-identity` with
 *      `{ stableId: "migrate:" + did, label: did, facadeDids: [did] }`.
 *      authz deploys a fresh `etzhayyimRootIdentity` contract on chain 260425
 *      and follows up with `linkFacade` so the legacy DID resolves to the
 *      new identity via `resolveFacade(keccak256(did))`.
 *   3. Logs `(did:web → did:erc725, identityAddress, txHash)` per account.
 *
 * Invariants exploited:
 *   * Idempotent — re-running is safe. authz fast-returns when
 *     `identityByRootDid[seedHash]` is already populated, and skips
 *     `linkFacade` when the row already maps to the same root.
 *   * No D1 rewrite — the legacy `did:web` row in `vertex_etzhayyim_auth_account`
 *     stays unchanged. In-flight sessions (JWT.iss = legacy did:web)
 *     resolve to the new identity via the registry's facade path; new
 *     sessions issued by the migrated sign-up flow already get the
 *     canonical `did:erc725:` accountDid.
 *
 * Known limitation (v0):
 *   * A returning user who later runs through `createGuestAccount` /
 *     `passkeyVerifyRegister` will get a SECOND root deployed under a
 *     different stableId (`guest:` / `passkey:` prefix). The legacy
 *     did:web facade still points at the migrated root from this script.
 *     Closing the gap fully would require sign-up to first
 *     `resolveFacade(legacyDid)` and reuse if present — separate PR.
 *
 * Usage:
 *   node 70-tools/scripts/migrate-did-web-to-erc725.mjs --dry-run      (default)
 *   node 70-tools/scripts/migrate-did-web-to-erc725.mjs --apply
 *   node 70-tools/scripts/migrate-did-web-to-erc725.mjs --apply --limit 5
 *
 * Required env (or macOS Keychain `etzhayyim.cloudflare/CLAIM_SETTLER_HMAC`):
 *   CLAIM_SETTLER_HMAC   shared HMAC for authz `/internal/*` routes
 *   AUTHZ_BASE_URL       defaults to https://authz.etzhayyim.com
 *   D1_DATABASE_NAME     defaults to etzhayyim-auth-passkey
 */
import { execSync } from "node:child_process";
import { createHmac } from "node:crypto";

const args = parseArgs(process.argv.slice(2));
const apply = !!args.apply;
const limit = Number(args.limit ?? 0) || 0;
const authzBase = (process.env.AUTHZ_BASE_URL ?? "https://authz.etzhayyim.com").replace(/\/+$/, "");
const dbName = process.env.D1_DATABASE_NAME ?? "etzhayyim-auth-passkey";

const hmac = (process.env.CLAIM_SETTLER_HMAC ?? readKeychain("etzhayyim.cloudflare", "CLAIM_SETTLER_HMAC")).trim();
if (!hmac) {
  console.error("ERROR: CLAIM_SETTLER_HMAC missing. Set env or `security add-generic-password -s etzhayyim.cloudflare -a CLAIM_SETTLER_HMAC -w <hex>`.");
  process.exit(2);
}

console.error(`mode      = ${apply ? "APPLY" : "dry-run"}`);
console.error(`authz     = ${authzBase}`);
console.error(`d1        = ${dbName}`);
console.error(`limit     = ${limit || "all"}`);
console.error("");

const accounts = listLegacyAccounts(dbName);
console.error(`found ${accounts.length} did:web account(s) in ${dbName}`);

const slice = limit > 0 ? accounts.slice(0, limit) : accounts;
console.error(`processing ${slice.length} account(s)\n`);

let provisioned = 0;
let skipped = 0;
let failed = 0;

for (const acct of slice) {
  const did = acct.did;
  const label = did;
  const stableId = `migrate:${did}`;
  if (!apply) {
    console.log(JSON.stringify({ did, status: "would-provision", stableId, label, facadeDids: [did] }));
    skipped += 1;
    continue;
  }
  try {
    const result = await postProvision({ stableId, label, facadeDids: [did] });
    const facadeOk = (result.facades ?? []).every((f) => f.linked);
    console.log(JSON.stringify({
      did,
      rootDid: result.rootDid,
      identityAddress: result.identityAddress,
      txHash: result.txHash,
      receiptStatus: result.receiptStatus,
      facadeOk,
      facades: result.facades ?? [],
    }));
    provisioned += 1;
  } catch (e) {
    console.log(JSON.stringify({ did, error: e?.message ?? String(e) }));
    failed += 1;
  }
}

console.error("");
console.error(`done. provisioned=${provisioned} dry-skipped=${skipped} failed=${failed}`);
process.exit(failed > 0 ? 1 : 0);

// ── helpers ─────────────────────────────────────────────────────────────────

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === "--apply") out.apply = true;
    else if (a === "--dry-run") out.apply = false;
    else if (a === "--limit") out.limit = argv[++i];
    else if (a.startsWith("--limit=")) out.limit = a.slice("--limit=".length);
  }
  return out;
}

function readKeychain(service, account) {
  try {
    return execSync(
      `security find-generic-password -s ${shellQuote(service)} -a ${shellQuote(account)} -w`,
      { stdio: ["ignore", "pipe", "ignore"] },
    ).toString();
  } catch { return ""; }
}

function shellQuote(s) {
  return `'${String(s).replace(/'/g, "'\\''")}'`;
}

function listLegacyAccounts(name) {
  const cmd = [
    "npx --yes wrangler d1 execute",
    shellQuote(name),
    "--remote",
    "--json",
    "--command",
    shellQuote("SELECT did, legacy_did, handle FROM vertex_etzhayyim_auth_account WHERE did LIKE 'did:web:%'"),
  ].join(" ");
  let raw;
  try {
    raw = execSync(cmd, { stdio: ["ignore", "pipe", "pipe"] }).toString();
  } catch (e) {
    console.error("wrangler d1 execute failed:", e?.stderr?.toString?.() ?? e?.message);
    process.exit(2);
  }
  let parsed;
  try { parsed = JSON.parse(raw); } catch { console.error("bad JSON from wrangler:", raw.slice(0, 400)); process.exit(2); }
  const rows = [];
  for (const block of Array.isArray(parsed) ? parsed : [parsed]) {
    if (Array.isArray(block?.results)) rows.push(...block.results);
  }
  return rows.filter((r) => typeof r?.did === "string" && r.did.startsWith("did:web:"));
}

async function postProvision({ stableId, label, facadeDids }) {
  const body = JSON.stringify({ stableId, label, facadeDids });
  const sig = createHmac("sha256", hmac).update(body).digest("hex");
  const resp = await fetch(`${authzBase}/internal/provision-root-identity`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-claim-settler-auth": sig },
    body,
  });
  const text = await resp.text();
  if (!resp.ok) {
    throw new Error(`HTTP ${resp.status}: ${text.slice(0, 200)}`);
  }
  return JSON.parse(text);
}
