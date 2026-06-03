#!/usr/bin/env node
/**
 * One-shot generator for the etzhayyim private-chain Clique sealer.
 *
 * Outputs (under 50-infra/vultr/geth-private/.local-secrets/, gitignored):
 *   - sealer.priv         raw 32-byte private key (hex, 0x-prefixed)
 *   - sealer.address      0x-prefixed checksum-ish lowercase address
 *   - sealer.password     20-byte random password (hex)
 *   - sealer-keystore.json  Geth-compatible Web3 Secret Storage v3 file
 *
 * Also emits:
 *   - manifests/genesis.json with chainId 260425, Clique period 5s, sealer
 *     address embedded in extraData and pre-funded.
 *
 * Crypto: @noble/curves@2 (secp256k1) + @noble/hashes@2 (keccak/sha256/scrypt
 * via direct path imports, since the package only re-exports under specific
 * subpaths). These are already in workspace node_modules from the SIWE work.
 *
 * Re-running the script regenerates everything — only run once.
 */

import { secp256k1 } from "@noble/curves/secp256k1.js";
import { keccak_256 } from "@noble/hashes/sha3.js";
import { sha256 } from "@noble/hashes/sha2.js";
import { scrypt } from "@noble/hashes/scrypt.js";
import { randomBytes as cryptoRandomBytes, createCipheriv } from "node:crypto";
import { mkdirSync, writeFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID } from "node:crypto";

const __dirname = dirname(fileURLToPath(import.meta.url));
const outDir = join(__dirname, "..", ".local-secrets");
const manifestsDir = join(__dirname, "..", "manifests");

if (!existsSync(outDir)) mkdirSync(outDir, { recursive: true });
if (!existsSync(manifestsDir)) mkdirSync(manifestsDir, { recursive: true });

if (existsSync(join(outDir, "sealer.priv"))) {
  console.error("[gen-sealer] sealer.priv already exists — refusing to overwrite. Delete .local-secrets/ to regenerate.");
  process.exit(1);
}

function bytesToHex(bytes) {
  let out = "";
  for (let i = 0; i < bytes.length; i += 1) out += bytes[i].toString(16).padStart(2, "0");
  return out;
}

function rand(n) {
  return new Uint8Array(cryptoRandomBytes(n));
}

const priv = rand(32);
const pub = secp256k1.getPublicKey(priv, false); // 0x04 || X || Y
const xy = pub.slice(1);
const addrBytes = keccak_256(xy).slice(-20);
const addressHex = "0x" + bytesToHex(addrBytes);
const addressNo0x = bytesToHex(addrBytes);

// ── Web3 Secret Storage v3 (scrypt + aes-128-ctr + keccak256 MAC) ───────────
const password = bytesToHex(rand(20));
const salt = rand(32);
const iv = rand(16);
const N = 262144, r = 8, p = 1, dklen = 32;
const dk = scrypt(new TextEncoder().encode(password), salt, { N, r, p, dkLen: dklen });
const cipherKey = dk.slice(0, 16);
const macSeed = dk.slice(16, 32);
const cipher = createCipheriv("aes-128-ctr", cipherKey, Buffer.from(iv));
const ciphertext = Buffer.concat([cipher.update(Buffer.from(priv)), cipher.final()]);
const mac = keccak_256(new Uint8Array(Buffer.concat([Buffer.from(macSeed), ciphertext])));

const keystore = {
  version: 3,
  id: randomUUID(),
  address: addressNo0x,
  crypto: {
    cipher: "aes-128-ctr",
    cipherparams: { iv: bytesToHex(iv) },
    ciphertext: ciphertext.toString("hex"),
    kdf: "scrypt",
    kdfparams: { dklen, n: N, r, p, salt: bytesToHex(salt) },
    mac: bytesToHex(mac),
  },
};

writeFileSync(join(outDir, "sealer.priv"), "0x" + bytesToHex(priv) + "\n", { mode: 0o600 });
writeFileSync(join(outDir, "sealer.address"), addressHex + "\n", { mode: 0o644 });
writeFileSync(join(outDir, "sealer.password"), password + "\n", { mode: 0o600 });
writeFileSync(join(outDir, "sealer-keystore.json"), JSON.stringify(keystore), { mode: 0o600 });

// ── genesis.json (Clique PoA, chainId 260425) ───────────────────────────────
const extraData =
  "0x" +
  "00".repeat(32) +              // 32 bytes vanity
  addressNo0x +                   // 20 bytes signer
  "00".repeat(65);                // 65 bytes proposer signature placeholder

// Pre-fund sealer with ~10^59 wu (~ 10^41 NETH worth of gas; private chain only)
const genesis = {
  config: {
    chainId: 260425,
    homesteadBlock: 0,
    eip150Block: 0,
    eip155Block: 0,
    eip158Block: 0,
    byzantiumBlock: 0,
    constantinopleBlock: 0,
    petersburgBlock: 0,
    istanbulBlock: 0,
    berlinBlock: 0,
    londonBlock: 0,
    clique: {
      period: 5,                  // seconds per block
      epoch: 30000,
    },
  },
  nonce: "0x0",
  timestamp: "0x0",
  extraData,
  gasLimit: "0x1c9c380",          // 30M
  difficulty: "0x1",
  mixHash: "0x0000000000000000000000000000000000000000000000000000000000000000",
  coinbase: "0x0000000000000000000000000000000000000000",
  alloc: {
    [addressHex]: { balance: "0x200000000000000000000000000000000000000000000000000000000000000" },
  },
};

writeFileSync(join(manifestsDir, "genesis.json"), JSON.stringify(genesis, null, 2) + "\n");

// secp256k1 curve order n. crypto.randomBytes(32) producing a value >= n has
// probability ~2^-128 — for our purposes treating the random key as valid is
// safe. getPublicKey would have already thrown if priv was zero.

console.log("Sealer address:  " + addressHex);
console.log("ChainId:         260425");
console.log("Outputs:");
console.log("  .local-secrets/sealer.priv          (KEEP SECRET, gitignored)");
console.log("  .local-secrets/sealer.address");
console.log("  .local-secrets/sealer.password");
console.log("  .local-secrets/sealer-keystore.json (KEEP SECRET, gitignored)");
console.log("  manifests/genesis.json");

// Self-test: decrypt our own keystore to make sure password+kdf+cipher round-trip
{
  const dk2 = scrypt(new TextEncoder().encode(password), salt, { N, r, p, dkLen: dklen });
  const macCheck = keccak_256(new Uint8Array(Buffer.concat([Buffer.from(dk2.slice(16, 32)), ciphertext])));
  if (bytesToHex(macCheck) !== bytesToHex(mac)) throw new Error("self-test MAC mismatch");
  const decipher = createCipheriv("aes-128-ctr", dk2.slice(0, 16), Buffer.from(iv));
  const recovered = Buffer.concat([decipher.update(ciphertext), decipher.final()]);
  if (Buffer.compare(recovered, Buffer.from(priv)) !== 0) throw new Error("self-test priv mismatch");
}
console.log("Self-test:       keystore round-trips ok");
