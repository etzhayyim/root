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
