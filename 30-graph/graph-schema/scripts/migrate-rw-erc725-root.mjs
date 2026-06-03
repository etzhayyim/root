#!/usr/bin/env node

import { Pool } from "pg";
import { keccak_256 } from "@noble/hashes/sha3.js";
import { utf8ToBytes } from "@noble/hashes/utils.js";

const DEFAULT_CHAIN_ID = "260425";
const DEFAULT_REGISTRY_ADDR = "0x11405300Fb75C5CDd665B9c0Ef445F8E312e3ee8";

const ZERO_32 = `0x${"0".repeat(64)}`;
const ZERO_ADDR = `0x${"0".repeat(40)}`;

function usage() {
  console.log(`Usage:
  DATABASE_URL=postgres://... ETH_PRIVATE_RPC_URL=http://... \\
    node scripts/migrate-rw-erc725-root.mjs [--apply] [--limit N] [--did DID]

Defaults:
  --dry-run                  No writes unless --apply is set.
  ETH_PRIVATE_CHAIN_ID       ${DEFAULT_CHAIN_ID}
  etzhayyim_ROOT_IDENTITY_REGISTRY_ADDR ${DEFAULT_REGISTRY_ADDR}
`);
}

function parseArgs(argv) {
  const out = { apply: false, limit: 0, did: "", verbose: false };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (a === "--apply") out.apply = true;
    else if (a === "--verbose") out.verbose = true;
    else if (a === "--help" || a === "-h") {
      usage();
      process.exit(0);
    } else if (a === "--limit") {
      out.limit = Number(argv[++i] ?? "0");
    } else if (a === "--did") {
      out.did = argv[++i] ?? "";
    } else {
      throw new Error(`unknown argument: ${a}`);
    }
  }
  if (!Number.isFinite(out.limit) || out.limit < 0) {
    throw new Error("--limit must be a positive integer");
  }
  out.limit = Math.floor(out.limit);
  return out;
}

function hex(bytes) {
  return `0x${Buffer.from(bytes).toString("hex")}`;
}

function keccakHex(text) {
  return hex(keccak_256(utf8ToBytes(text)));
}

function selector(signature) {
  return Buffer.from(keccak_256(utf8ToBytes(signature))).subarray(0, 4).toString("hex");
}

function encodeBytes32(v) {
  if (!/^0x[0-9a-fA-F]{64}$/.test(v)) {
    throw new Error(`expected bytes32 hex, got ${v}`);
  }
  return v.slice(2).toLowerCase();
}

function decodeAddress(word) {
  if (!word || word.length !== 64) return ZERO_ADDR;
  return `0x${word.slice(24)}`.toLowerCase();
}

function decodeBytes32(word) {
  if (!word || word.length !== 64) return ZERO_32;
  return `0x${word.toLowerCase()}`;
}

function facadeMethod(did) {
  const m = /^did:([^:]+):/.exec(did);
  return m?.[1] ?? "";
}

async function rpcCall(rpcUrl, to, data) {
  const res = await fetch(rpcUrl, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: 1,
      method: "eth_call",
      params: [{ to, data }, "latest"],
    }),
  });
  if (!res.ok) throw new Error(`eth_call failed: HTTP ${res.status}`);
  const body = await res.json();
  if (body.error) throw new Error(`eth_call failed: ${body.error.message ?? JSON.stringify(body.error)}`);
  return body.result ?? "0x";
}

async function callBytes32Getter(rpcUrl, registryAddr, signature, arg) {
  const data = `0x${selector(signature)}${encodeBytes32(arg)}`;
  const result = await rpcCall(rpcUrl, registryAddr, data);
  return decodeBytes32(result.slice(2, 66));
}

async function callAddressGetter(rpcUrl, registryAddr, signature, arg) {
  const data = `0x${selector(signature)}${encodeBytes32(arg)}`;
  const result = await rpcCall(rpcUrl, registryAddr, data);
  return decodeAddress(result.slice(2, 66));
}

async function loadCandidates(pool, onlyDid, limit) {
  if (onlyDid) return [onlyDid];
  const limitSql = limit > 0 ? `LIMIT ${limit}` : "";
  const q = `
    SELECT did FROM (
      SELECT did FROM vertex_etzhayyim_identity WHERE did IS NOT NULL AND did <> ''
      UNION
      SELECT legacy_did AS did FROM vertex_etzhayyim_identity WHERE legacy_did IS NOT NULL AND legacy_did <> ''
      UNION
      SELECT federation_did AS did FROM vertex_etzhayyim_identity WHERE federation_did IS NOT NULL AND federation_did <> ''
      UNION
      SELECT claimant_did AS did FROM vertex_claim_stake WHERE claimant_did IS NOT NULL AND claimant_did <> ''
      UNION
      SELECT challenger_did AS did FROM vertex_claim_challenge WHERE challenger_did IS NOT NULL AND challenger_did <> ''
    ) s
    WHERE did LIKE 'did:etzhayyim:%'
       OR did LIKE 'did:web:%'
       OR did LIKE 'did:plc:%'
       OR did LIKE 'did:ethr:%'
       OR did LIKE 'did:pkh:%'
    ORDER BY did
    ${limitSql}
  `;
  const { rows } = await pool.query(q);
  return rows.map((r) => r.did);
}

async function deleteInsert(pool, table, keyColumn, keyValue, columns, values) {
  await pool.query(`DELETE FROM ${table} WHERE ${keyColumn} = $1`, [keyValue]);
  const names = columns.join(", ");
  const params = columns.map((_, i) => `$${i + 1}`).join(", ");
  await pool.query(`INSERT INTO ${table} (${names}) VALUES (${params})`, values);
}

async function applyProjection(pool, row) {
  const now = new Date().toISOString();
  const rootColumns = [
    "vertex_id",
    "owner_did",
    "root_did",
    "root_did_hash",
    "root_identity_addr",
    "chain_id",
    "registry_addr",
    "source",
    "status",
    "created_at",
    "updated_at",
  ];
  await deleteInsert(pool, "vertex_erc725_root_identity", "vertex_id", row.rootDid, rootColumns, [
    row.rootDid,
    row.rootDid,
    row.rootDid,
    row.rootDidHash,
    row.identity,
    row.chainId,
    row.registryAddr,
    "etzhayyim-root-registry",
    "active",
    now,
    now,
  ]);

  const edgeId = `edge:erc725-facade:${row.rootDidHash}:${row.facadeDidHash}`;
  const edgeColumns = [
    "edge_id",
    "src_vid",
    "dst_vid",
    "owner_did",
    "root_did",
    "root_did_hash",
    "facade_did",
    "facade_did_hash",
    "facade_method",
    "root_identity_addr",
    "chain_id",
    "registry_addr",
    "status",
    "created_at",
    "updated_at",
  ];
  await deleteInsert(pool, "edge_erc725_facade_did", "edge_id", edgeId, edgeColumns, [
    edgeId,
    row.rootDid,
    row.facadeDid,
    row.rootDid,
    row.rootDid,
    row.rootDidHash,
    row.facadeDid,
    row.facadeDidHash,
    facadeMethod(row.facadeDid),
    row.identity,
    row.chainId,
    row.registryAddr,
    "active",
    now,
    now,
  ]);

  await pool.query(
    `UPDATE vertex_etzhayyim_identity
        SET root_did = $1,
            root_did_hash = $2,
            root_identity_addr = $3,
            facade_did = $4,
            facade_did_hash = $5,
            identity_method = 'did:erc725',
            migration_status = 'erc725_migrated',
            updated_at = $6
      WHERE did = $4 OR legacy_did = $4 OR federation_did = $4`,
    [row.rootDid, row.rootDidHash, row.identity, row.facadeDid, row.facadeDidHash, now],
  );

  await pool.query(
    `UPDATE vertex_claim_stake
        SET legacy_claimant_did = CASE
              WHEN legacy_claimant_did IS NULL OR legacy_claimant_did = '' THEN claimant_did
              ELSE legacy_claimant_did
            END,
            claimant_did = $1,
            did_hash = $2,
            root_did = $1,
            root_did_hash = $2,
            root_identity_addr = $3
      WHERE claimant_did = $4`,
    [row.rootDid, row.rootDidHash, row.identity, row.facadeDid],
  );

  await pool.query(
    `UPDATE vertex_claim_challenge
        SET legacy_challenger_did = CASE
              WHEN legacy_challenger_did IS NULL OR legacy_challenger_did = '' THEN challenger_did
              ELSE legacy_challenger_did
            END,
            challenger_did = $1,
            challenger_did_hash = $2,
            root_did = $1,
            root_did_hash = $2,
            root_identity_addr = $3
      WHERE challenger_did = $4`,
    [row.rootDid, row.rootDidHash, row.identity, row.facadeDid],
  );
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const databaseUrl = process.env.DATABASE_URL || process.env.RW_URL;
  const rpcUrl = process.env.ETH_PRIVATE_RPC_URL;
  const registryAddr = (process.env.etzhayyim_ROOT_IDENTITY_REGISTRY_ADDR ?? DEFAULT_REGISTRY_ADDR).toLowerCase();
  const chainId = Number(process.env.ETH_PRIVATE_CHAIN_ID ?? DEFAULT_CHAIN_ID);

  if (!databaseUrl) throw new Error("DATABASE_URL or RW_URL is required");
  if (!rpcUrl) throw new Error("ETH_PRIVATE_RPC_URL is required");
  if (!/^0x[0-9a-fA-F]{40}$/.test(registryAddr)) {
    throw new Error(`invalid etzhayyim_ROOT_IDENTITY_REGISTRY_ADDR: ${registryAddr}`);
  }

  const pool = new Pool({ connectionString: databaseUrl, max: 2 });
  const summary = { candidates: 0, registered: 0, migrated: 0, unmapped: 0 };
  const samples = [];

  try {
    const candidates = await loadCandidates(pool, args.did, args.limit);
    summary.candidates = candidates.length;
    for (const facadeDid of candidates) {
      const facadeDidHash = keccakHex(facadeDid);
      const rootDidHash = await callBytes32Getter(rpcUrl, registryAddr, "rootByFacadeDid(bytes32)", facadeDidHash);
      if (rootDidHash === ZERO_32) {
        summary.unmapped += 1;
        if (args.verbose) samples.push({ facadeDid, status: "unmapped" });
        continue;
      }
      const identity = await callAddressGetter(rpcUrl, registryAddr, "identityByRootDid(bytes32)", rootDidHash);
      if (identity === ZERO_ADDR) {
        summary.unmapped += 1;
        samples.push({ facadeDid, status: "root_without_identity", rootDidHash });
        continue;
      }
      const rootDid = `did:erc725:etzhayyim:${chainId}:${identity}`;
      const canonicalRootDidHash = keccakHex(rootDid);
      const row = {
        facadeDid,
        facadeDidHash,
        rootDid,
        rootDidHash: canonicalRootDidHash,
        registryRootDidHash: rootDidHash,
        registryRootHashMismatch: canonicalRootDidHash !== rootDidHash,
        identity,
        chainId,
        registryAddr,
      };
      summary.registered += 1;
      if (samples.length < 20) samples.push(row);
      if (args.apply) {
        await applyProjection(pool, row);
        summary.migrated += 1;
      }
    }
  } finally {
    await pool.end();
  }

  console.log(JSON.stringify({ mode: args.apply ? "apply" : "dry-run", summary, samples }, null, 2));
}

main().catch((err) => {
  console.error(err.stack ?? err.message);
  process.exit(1);
});
