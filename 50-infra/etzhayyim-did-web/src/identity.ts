/**
 * Domain-independent member identity (ADR-2606061800).
 *
 * The canonical member identity is the self-certifying passkey-derived
 * **`did:key`**, NOT `did:web:etzhayyim.com:<handle>`. `did:web` roots trust in
 * domain/TLS ownership — if `etzhayyim.com` changes hands the new owner could
 * publish a different DID Document for the same handle and hijack the name. So
 * `did:web` is DEMOTED to a non-authoritative resolution alias (`alsoKnownAs`),
 * and the handle↔key binding is made **self-certifying**: the controller
 * `did:key` itself signs a compact EdDSA attestation `{ iss, handle }`, which
 * anyone can verify against the key in the DID with NO domain, NO TLS, NO
 * registry. A forged did:web document is detectable (it is not signed by the
 * member's key).
 *
 * This verifier is the apex's hook: before serving a member handle's DID doc it
 * confirms the binding is the `did:key`'s own assertion, not something a domain
 * owner asserted. Zero-dependency (WebCrypto Ed25519, reuses cacao.ts).
 */

import { parseEd25519DidKey } from "./cacao.ts";
import { cidV1Raw } from "./cid.ts";

export interface HandleAttestationResult {
  valid: boolean;
  /** the controller did:key that signed the binding (canonical identity). */
  did?: string;
  /** the handle the did:key claims. */
  handle?: string;
  reason?: string;
}

function b64urlToBytes(s: string): Uint8Array {
  const pad = s.length % 4 === 0 ? "" : "=".repeat(4 - (s.length % 4));
  const bin = atob(s.replace(/-/g, "+").replace(/_/g, "/") + pad);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i += 1) out[i] = bin.charCodeAt(i);
  return out;
}

async function verifyEd25519(
  pubkey: Uint8Array,
  message: Uint8Array,
  signature: Uint8Array,
): Promise<boolean> {
  if (signature.length !== 64) return false;
  const key = await crypto.subtle.importKey(
    "raw",
    pubkey as BufferSource,
    { name: "Ed25519" },
    false,
    ["verify"],
  );
  return crypto.subtle.verify(
    { name: "Ed25519" },
    key,
    signature as BufferSource,
    message as BufferSource,
  );
}

/**
 * Verify a self-certifying handle attestation — a compact EdDSA JWS
 * `b64url(header).b64url(payload).b64url(sig)` where `payload.iss` is the
 * controller `did:key`, `payload.handle` the claimed handle, signed by that key.
 *
 * Trust roots in the `did:key` (the key is IN the DID), NOT in the domain — so
 * the result holds regardless of who owns `etzhayyim.com`. `nowSecs` is injected
 * for deterministic testing; pass an `exp`-less attestation for a permanent
 * binding (the kotoba append-only record carries the as-of history).
 */
export async function verifyHandleAttestation(
  jws: unknown,
  nowSecs: number,
): Promise<HandleAttestationResult> {
  if (typeof jws !== "string") {
    return { valid: false, reason: "attestation must be a compact JWS string" };
  }
  const parts = jws.split(".");
  if (parts.length !== 3) {
    return { valid: false, reason: "malformed JWS (expected header.payload.sig)" };
  }
  const [h, p, s] = parts;
  let header: { alg?: string; typ?: string };
  let payload: { iss?: string; sub?: string; handle?: string; iat?: number; exp?: number };
  try {
    header = JSON.parse(new TextDecoder().decode(b64urlToBytes(h)));
    payload = JSON.parse(new TextDecoder().decode(b64urlToBytes(p)));
  } catch {
    return { valid: false, reason: "JWS header/payload not valid base64url JSON" };
  }
  if (header.alg !== "EdDSA") {
    return { valid: false, reason: `unsupported alg '${header.alg}' (need EdDSA)` };
  }
  if (typeof payload.iss !== "string" || typeof payload.handle !== "string") {
    return { valid: false, reason: "payload must carry string iss + handle" };
  }
  if (payload.sub !== undefined && payload.sub !== payload.iss) {
    return { valid: false, reason: "payload.sub must equal payload.iss (self-attestation)" };
  }
  if (payload.exp !== undefined && nowSecs > payload.exp) {
    return { valid: false, reason: "handle attestation expired", did: payload.iss };
  }

  let pubkey: Uint8Array;
  try {
    pubkey = parseEd25519DidKey(payload.iss);
  } catch (e) {
    return {
      valid: false,
      reason: `iss must be an ed25519 did:key: ${e instanceof Error ? e.message : String(e)}`,
    };
  }
  let sig: Uint8Array;
  try {
    sig = b64urlToBytes(s);
  } catch {
    return { valid: false, reason: "signature not valid base64url" };
  }
  const signingInput = new TextEncoder().encode(`${h}.${p}`);
  let ok = false;
  try {
    ok = await verifyEd25519(pubkey, signingInput, sig);
  } catch (e) {
    return { valid: false, reason: `ed25519 verify error: ${e instanceof Error ? e.message : String(e)}` };
  }
  if (!ok) return { valid: false, reason: "signature mismatch — handle not attested by this did:key" };
  return { valid: true, did: payload.iss, handle: payload.handle };
}

// ─── account-block read verification (ADR-2606061800) ───────────────────────

/** Parse a `did:key:z`+hex(32B) — the kotoba-publish / `block.put` author form
 *  (distinct from the standard base58 `did:key:z6Mk…` login form) → raw pubkey. */
export function parseDidKeyHex(did: string): Uint8Array {
  const PREFIX = "did:key:z";
  if (!did.startsWith(PREFIX)) throw new Error("not a did:key:z+hex");
  const h = did.slice(PREFIX.length);
  if (h.length !== 64 || !/^[0-9a-f]+$/.test(h)) {
    throw new Error("did:key:z+hex must be 64 lowercase hex chars");
  }
  const out = new Uint8Array(32);
  for (let i = 0; i < 32; i += 1) out[i] = parseInt(h.slice(i * 2, i * 2 + 2), 16);
  return out;
}

function eqBytes(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i += 1) d |= a[i] ^ b[i];
  return d === 0;
}

export interface AccountBlockResult {
  valid: boolean;
  /** canonical did:key (standard base58 z6Mk form) of the account. */
  did?: string;
  handle?: string;
  reason?: string;
}

/**
 * Verify a published account record block before trusting its handle↔key binding
 * (the apex read endpoint's gate). Two checks, both domain-independent:
 *   1. the block AUTHOR (`did:key:z`+hex, the `block.put` signer) encodes the SAME
 *      Ed25519 key as the record's canonical `account/did` (standard base58
 *      `did:key:z6Mk…`) — reconciling the two did:key string forms so a block
 *      cannot claim an `account/did` it didn't author;
 *   2. when a handle is present, `account/handle-attestation` is the canonical
 *      `did:key`'s OWN signature over the handle (`verifyHandleAttestation`) —
 *      self-certifying, no domain/TLS.
 * `authorDidHex` is the `did` the apex already verified on `block.put` (it signed
 * the root CID); this binds that proven author to the record's canonical identity.
 */
export async function verifyAccountBlock(
  blockBytes: Uint8Array,
  authorDidHex: string,
  nowSecs: number,
): Promise<AccountBlockResult> {
  let rec: Record<string, unknown>;
  try {
    rec = JSON.parse(new TextDecoder().decode(blockBytes)) as Record<string, unknown>;
  } catch {
    return { valid: false, reason: "account block is not valid JSON" };
  }
  const canonicalDid = rec["account/did"];
  const handle = rec["account/handle"];
  if (typeof canonicalDid !== "string") {
    return { valid: false, reason: "record missing account/did" };
  }
  let authorPub: Uint8Array;
  let canonPub: Uint8Array;
  try {
    authorPub = parseDidKeyHex(authorDidHex);
  } catch (e) {
    return { valid: false, reason: `author did: ${e instanceof Error ? e.message : String(e)}` };
  }
  try {
    canonPub = parseEd25519DidKey(canonicalDid);
  } catch (e) {
    return {
      valid: false,
      reason: `account/did must be a base58 ed25519 did:key: ${e instanceof Error ? e.message : String(e)}`,
    };
  }
  if (!eqBytes(authorPub, canonPub)) {
    return {
      valid: false,
      reason: "block author key ≠ account/did key (the signer is not this account's controller)",
      did: canonicalDid,
    };
  }
  if (typeof handle === "string" && handle.length > 0) {
    const att = rec["account/handle-attestation"];
    if (typeof att !== "string") {
      return { valid: false, reason: "handle present but no account/handle-attestation", did: canonicalDid };
    }
    const r = await verifyHandleAttestation(att, nowSecs);
    if (!r.valid || r.did !== canonicalDid || r.handle !== handle) {
      return {
        valid: false,
        reason: "handle-attestation does not bind this did:key to this handle",
        did: canonicalDid,
      };
    }
  }
  return {
    valid: true,
    did: canonicalDid,
    handle: typeof handle === "string" ? handle : undefined,
  };
}

/**
 * Resolve an account from a content-addressed block — the **read side**, with NO
 * KV and NO central node (ADR-2606061800). Given a block fetched **by CID** from
 * IPFS (kotobase.net pin / any gateway), this (1) re-computes the CID and asserts
 * it matches the bytes (content-address integrity — the block cannot have been
 * tampered with), then (2) verifies the record's self-certifying
 * handle-attestation (`account/did`'s own signature over `account/handle`). Trust
 * roots in the content-address + the member's `did:key` — never a domain, a
 * central node, or a KV. The caller supplies the CID-fetched bytes (e.g. via the
 * apex trustless `/ipfs/<cid>` gateway, which itself re-verifies the CID).
 */
export async function resolveAccountFromBlock(
  cid: string,
  blockBytes: Uint8Array,
  nowSecs: number,
): Promise<AccountBlockResult> {
  let recomputed: string;
  try {
    recomputed = await cidV1Raw(blockBytes as BufferSource);
  } catch (e) {
    return { valid: false, reason: `CID recompute failed: ${e instanceof Error ? e.message : String(e)}` };
  }
  if (recomputed !== cid) {
    return { valid: false, reason: "block bytes do not match the CID (content-address integrity failure)" };
  }
  let rec: Record<string, unknown>;
  try {
    rec = JSON.parse(new TextDecoder().decode(blockBytes)) as Record<string, unknown>;
  } catch {
    return { valid: false, reason: "account block is not valid JSON" };
  }
  const did = rec["account/did"];
  const handle = rec["account/handle"];
  if (typeof did !== "string") {
    return { valid: false, reason: "record missing account/did" };
  }
  // the canonical did:key must be a well-formed ed25519 did:key
  try {
    parseEd25519DidKey(did);
  } catch (e) {
    return { valid: false, reason: `account/did invalid: ${e instanceof Error ? e.message : String(e)}` };
  }
  if (typeof handle === "string" && handle.length > 0) {
    const att = rec["account/handle-attestation"];
    if (typeof att !== "string") {
      return { valid: false, reason: "handle present but no account/handle-attestation", did };
    }
    const r = await verifyHandleAttestation(att, nowSecs);
    if (!r.valid || r.did !== did || r.handle !== handle) {
      return { valid: false, reason: "handle-attestation does not bind this did:key to this handle", did };
    }
  }
  return { valid: true, did, handle: typeof handle === "string" ? handle : undefined };
}

/**
 * Build the self-certifying DID Document for a member account. The `id` is the
 * canonical **`did:key`** (domain-independent); `did:web:etzhayyim.com:<handle>`
 * appears only in `alsoKnownAs` as a NON-authoritative convenience alias. So a
 * resolver trusts the `did:key`, and a change of domain owner cannot forge the
 * member's identity — only the readable alias's resolution endpoint moves.
 */
export function selfCertifyingDidDoc(
  didKey: string,
  handle?: string,
): Record<string, unknown> {
  const alsoKnownAs: string[] = [];
  if (handle) alsoKnownAs.push(`did:web:etzhayyim.com:${handle}`);
  return {
    "@context": ["https://www.w3.org/ns/did/v1"],
    id: didKey,
    alsoKnownAs,
    // The verification method IS the did:key itself (self-certifying — the key
    // is in the DID). No server-minted key (ADR-2605231525).
    verificationMethod: [
      {
        id: `${didKey}#key-1`,
        type: "Ed25519VerificationKey2020",
        controller: didKey,
        publicKeyMultibase: didKey.slice("did:key:".length),
      },
    ],
    authentication: [`${didKey}#key-1`],
    assertionMethod: [`${didKey}#key-1`],
  };
}
