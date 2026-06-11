#!/usr/bin/env node
/**
 * sign-diddoc — operator/actor tool that produces a self-certifying DID-document
 * attestation (ADR-2606015600). The ed25519 private key is the ACTOR's, held by
 * the operator — NEVER the server (ADR-2605231525). The apex Worker only verifies
 * (src/diddoc-attest.ts).
 *
 *   node scripts/sign-diddoc.mjs --did did:web:etzhayyim.com:actor:kanae \
 *        --cid <didDocCid> [--key <64-hex-seed>] [--seq 1] \
 *        [--pq | --pq-key <64-hex-seed>]
 *
 * With --actor <h> instead of --cid, reads out/actor-records/<h>.diddoc.cid
 * (run publish-actor-records.mjs first). Without --key, generates a fresh
 * keypair and prints the seed (save it — it is the actor's identity).
 *
 * --pq / --pq-key adds the pqh-v1 companion proof (ADR-2606111300): an
 * ML-DSA-65 (FIPS 204) signature over the same attestation bytes, keyed by a
 * second 32-byte seed. Save the pq seed alongside the ed25519 seed.
 */
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve, join } from "node:path";
import { ml_dsa65 } from "@noble/post-quantum/ml-dsa.js";
import {
  ed25519PubToDidKey,
  mlDsa65PubToDidKey,
  base58btcEncode,
  attestationMessage,
} from "../src/diddoc-attest.ts";

const __dirname = dirname(fileURLToPath(import.meta.url));

const hex = (b) => [...b].map((x) => x.toString(16).padStart(2, "0")).join("");
const unhex = (s) => Uint8Array.from(s.match(/.{2}/g).map((h) => parseInt(h, 16)));

/** Generate a fresh ed25519 keypair → { priv (CryptoKey), pubRaw (32B), seed (32B) }. */
export async function ed25519Key() {
  const kp = await crypto.subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"]);
  const pubRaw = new Uint8Array(await crypto.subtle.exportKey("raw", kp.publicKey));
  const pkcs8 = new Uint8Array(await crypto.subtle.exportKey("pkcs8", kp.privateKey));
  const seed = pkcs8.slice(pkcs8.length - 32); // last 32 bytes of the PKCS8 = seed
  return { priv: kp.privateKey, pubRaw, seed };
}

// derive the public key from a seed by importing through node's KeyObject API
// (WebCrypto has no direct seed→pub).
async function ed25519PubFromSeed(seed32) {
  const pkcs8 = new Uint8Array([
    0x30, 0x2e, 0x02, 0x01, 0x00, 0x30, 0x05, 0x06, 0x03, 0x2b, 0x65, 0x70,
    0x04, 0x22, 0x04, 0x20, ...seed32,
  ]);
  // node exposes the matching public key only via the KeyObject API:
  const { createPrivateKey, createPublicKey } = await import("node:crypto");
  const privKo = createPrivateKey({ key: Buffer.from(pkcs8), format: "der", type: "pkcs8" });
  const spki = createPublicKey(privKo).export({ format: "der", type: "spki" });
  return new Uint8Array(spki.slice(spki.length - 32));
}

/** Generate (or derive from a 32-byte seed) an ML-DSA-65 keypair. */
export function mlDsa65Key(seed32) {
  const seed = seed32 ?? crypto.getRandomValues(new Uint8Array(32));
  const { publicKey, secretKey } = ml_dsa65.keygen(seed);
  return { publicKey, secretKey, seed };
}

/** Sign a payload → a complete attestation object. Pass `pqKey` (from
 *  mlDsa65Key) to add the pqh-v1 companion proof over the same bytes. */
export async function signDidDocAttestation(payload, priv, pubRaw, pqKey) {
  const msg = attestationMessage(payload);
  const sig = new Uint8Array(await crypto.subtle.sign({ name: "Ed25519" }, priv, msg));
  const att = {
    type: "EtzhayyimDidDocAttestation",
    ...payload,
    proof: {
      type: "Ed25519Signature2020",
      verificationMethod: ed25519PubToDidKey(pubRaw),
      proofValue: "z" + base58btcEncode(sig),
    },
  };
  if (pqKey) {
    const pqSig = ml_dsa65.sign(msg, pqKey.secretKey);
    att.pqProof = {
      type: "MlDsa65Signature2026",
      verificationMethod: mlDsa65PubToDidKey(pqKey.publicKey),
      proofValue: "z" + base58btcEncode(pqSig),
    };
  }
  return att;
}

async function main() {
  const args = process.argv.slice(2);
  const val = (f) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : undefined; };
  const did = val("--did");
  let cid = val("--cid");
  const actor = val("--actor");
  if (!cid && actor) {
    cid = readFileSync(resolve(__dirname, `../out/actor-records/${actor}.diddoc.cid`), "utf8").trim();
  }
  if (!did || !cid) { console.error("need --did and --cid (or --actor)"); process.exit(1); }

  const seedHex = val("--key");
  const seed = seedHex ? unhex(seedHex) : undefined;
  let key;
  if (seed) {
    const priv = await crypto.subtle.importKey("pkcs8", new Uint8Array([0x30,0x2e,0x02,0x01,0x00,0x30,0x05,0x06,0x03,0x2b,0x65,0x70,0x04,0x22,0x04,0x20,...seed]), { name: "Ed25519" }, true, ["sign"]);
    key = { priv, pubRaw: await ed25519PubFromSeed(seed), seed };
  } else {
    key = await ed25519Key();
  }

  const pqSeedHex = val("--pq-key");
  const wantPq = pqSeedHex !== undefined || args.includes("--pq");
  const pqKey = wantPq ? mlDsa65Key(pqSeedHex ? unhex(pqSeedHex) : undefined) : undefined;

  const payload = {
    did,
    didDocCid: cid,
    signedAt: val("--at") ?? "1970-01-01T00:00:00.000Z",
    sequence: Number(val("--seq") ?? 1),
  };
  const att = await signDidDocAttestation(payload, key.priv, key.pubRaw, pqKey);
  const outDir = resolve(__dirname, "../out/attestations");
  mkdirSync(outDir, { recursive: true });
  const file = join(outDir, `${did.split(":").pop()}.attestation.json`);
  writeFileSync(file, JSON.stringify(att, null, 2) + "\n");
  console.log(`did:key  = ${att.proof.verificationMethod}`);
  console.log(`seed     = ${hex(key.seed)}  (the actor's identity — keep it safe, server never sees it)`);
  if (pqKey) {
    console.log(`pq did:key = ${att.pqProof.verificationMethod}`);
    console.log(`pq seed    = ${hex(pqKey.seed)}  (ML-DSA-65 identity — keep alongside the ed25519 seed)`);
  }
  console.log(`written  → ${file}`);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
