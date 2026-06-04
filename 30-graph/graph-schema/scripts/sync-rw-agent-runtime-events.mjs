#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import pg from "pg";

const DEFAULT_PROOF = "90-docs/proof/kami-agent-erc8004-publish-attempt.local.json";
const DEFAULT_REGISTRATION = "90-docs/proof/kami-agent-erc8004-registration.local.json";
const DEFAULT_RPC = "https://geth.etzhayyim.com";

function argValue(name, fallback = "") {
  const idx = process.argv.indexOf(name);
  return idx >= 0 ? process.argv[idx + 1] || fallback : fallback;
}

function hasFlag(name) {
  return process.argv.includes(name);
}

function readJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

function keychain(service, account) {
  try {
    return execFileSync("security", ["find-generic-password", "-s", service, "-a", account, "-w"], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    }).trim();
  } catch {
    return "";
  }
}

function castCall(registry, signature, args = [], rpcUrl = DEFAULT_RPC) {
  return execFileSync("cast", ["call", registry, signature, ...args, "--rpc-url", rpcUrl], {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  }).trim();
}

function parseIntMaybe(value) {
  if (value == null || value === "") return null;
  if (typeof value === "number") return value;
  const text = String(value).trim();
  if (text.startsWith("0x")) return Number.parseInt(text, 16);
  return Number.parseInt(text, 10);
}

function sha256(value) {
  return "sha256:" + createHash("sha256").update(value).digest("hex");
}

function buildRow({ proof, registration, rpcUrl }) {
  const chain = proof.chain || {};
  const agentRegistration = proof.agentRegistration || {};
  const registry = chain.registry || "0xcA3480edDAfa39c9377B83eEB18291286C8Cb865";
  const tokenId = String(chain.tokenId || registration.agent?.agentId || "");
  const rootDidHash = String(chain.rootDidHash || "");
  const agentURI = String(chain.agentURI || agentRegistration.uri || registration.agent?.agentURI || "");
  const owner = String(chain.owner || registration.rootIdentity?.address || "");

  if (!tokenId || !rootDidHash || !agentURI || !owner) {
    throw new Error("proof is missing tokenId/rootDidHash/agentURI/owner");
  }

  const chainTokenId = castCall(registry, "tokenByRootDid(bytes32)(uint256)", [rootDidHash], rpcUrl);
  const chainAgentURI = castCall(registry, "agentURI(uint256)(string)", [tokenId], rpcUrl).replace(/^"|"$/g, "");
  const chainOwner = castCall(registry, "ownerOf(uint256)(address)", [tokenId], rpcUrl);
  if (String(chainTokenId) !== tokenId) {
    throw new Error(`chain token mismatch: proof=${tokenId} chain=${chainTokenId}`);
  }
  if (chainAgentURI !== agentURI) {
    throw new Error(`chain agentURI mismatch: proof=${agentURI} chain=${chainAgentURI}`);
  }
  if (chainOwner.toLowerCase() !== owner.toLowerCase()) {
    throw new Error(`chain owner mismatch: proof=${owner} chain=${chainOwner}`);
  }

  const now = new Date().toISOString();
  const actorDid = registration.rootIdentity?.facadeDids?.[0] || "did:web:kami-agent.etzhayyim.com";
  const rootDid = registration.rootIdentity?.rootDid || "";
  return {
    vertex_id: `agent-publication-${chain.chainId || 260425}-${tokenId}`,
    created_date: now.slice(0, 10),
    sensitivity_ord: 1,
    owner_did: rootDid || actorDid,
    token_id: tokenId,
    root_did_hash: rootDidHash,
    agent_owner_addr: owner,
    agent_uri: agentURI,
    agent_uri_hash: sha256(agentURI),
    metadata_hash: chain.metadataHash || registration.publish?.agentRegistration?.sha256 || agentRegistration.sha256 || "",
    registry_addr: registry,
    chain_id: Number(chain.chainId || 260425),
    tx_hash: chain.txHash || "",
    block_number: parseIntMaybe(chain.blockNumber),
    log_index: parseIntMaybe(chain.logIndex) ?? 0,
    registered_at: now,
    status: "verified",
    org_id: actorDid,
    user_id: actorDid,
    actor_id: actorDid,
    created_at: now,
    updated_at: now,
    actor_did: actorDid,
    org_did: rootDid || "anon",
  };
}

async function upsertRow(row) {
  const rwUrl = process.env.RW_URL || keychain("etzhayyim.rw", "ROOT_URL");
  if (!rwUrl) throw new Error("RW_URL missing and Keychain etzhayyim.rw/ROOT_URL unavailable");
  const client = new pg.Client({ connectionString: rwUrl });
  await client.connect();
  try {
    await client.query("DELETE FROM vertex_agent_publication WHERE vertex_id = $1", [row.vertex_id]);
    const columns = Object.keys(row);
    const placeholders = columns.map((_, i) => `$${i + 1}`).join(", ");
    await client.query(
      `INSERT INTO vertex_agent_publication (${columns.join(", ")}) VALUES (${placeholders})`,
      columns.map((column) => row[column]),
    );
  } finally {
    await client.end();
  }
}

async function status() {
  const rwUrl = process.env.RW_URL || keychain("etzhayyim.rw", "ROOT_URL");
  if (!rwUrl) throw new Error("RW_URL missing and Keychain etzhayyim.rw/ROOT_URL unavailable");
  const client = new pg.Client({ connectionString: rwUrl });
  await client.connect();
  try {
    const result = await client.query(
      "SELECT COUNT(*)::int AS verified_agent_publications FROM vertex_agent_publication WHERE status = 'verified'",
    );
    console.log(JSON.stringify(result.rows[0], null, 2));
  } finally {
    await client.end();
  }
}

async function main() {
  if (hasFlag("--status")) {
    await status();
    return;
  }
  const proof = readJson(argValue("--proof", DEFAULT_PROOF));
  const registration = readJson(argValue("--registration", DEFAULT_REGISTRATION));
  const rpcUrl = argValue("--rpc-url", DEFAULT_RPC);
  const row = buildRow({ proof, registration, rpcUrl });
  if (hasFlag("--apply")) {
    await upsertRow(row);
  }
  console.log(JSON.stringify({ ok: true, applied: hasFlag("--apply"), row }, null, 2));
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
});
