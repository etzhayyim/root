/**
 * Self-certifying DID-document attestation (ADR-2606015600).
 *
 * Completes IPFS-based DID retrieval (ADR-2606015400): instead of trusting
 * `etzhayyim.com` (TLS) for the handle→CID binding, the actor's OWN ed25519 key
 * signs `{did, didDocCid}`. Because the signing key is expressed as a `did:key`
 * (the key IS the identifier), verifying the signature is **self-certifying** —
 * no external trust anchor needed. The server only ever VERIFIES; the private
 * key is the actor/operator's (ADR-2605231525 — no server-held key).
 *
 * Chain of trust (resolving by key): `did:key:z6Mk…` → verify the attestation's
 * signature against the key in its proof → trust `didDocCid` → fetch + CID-verify
 * the did.json (apex `/ipfs/<cid>` or any gateway) → confirm `doc.id` + that the
 * doc lists this `did:key` in `alsoKnownAs`/`verificationMethod`. TLS optional.
 */

// ── base58btc (Bitcoin alphabet) — multibase 'z' ────────────────────────────
const B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
const B58MAP: Record<string, number> = {};
for (let i = 0; i < B58.length; i++) B58MAP[B58[i]] = i;

export function base58btcEncode(bytes: Uint8Array): string {
  let zeros = 0;
  while (zeros < bytes.length && bytes[zeros] === 0) zeros++;
  const digits: number[] = [];
  for (let i = zeros; i < bytes.length; i++) {
    let carry = bytes[i];
    for (let j = 0; j < digits.length; j++) {
      carry += digits[j] << 8;
      digits[j] = carry % 58;
      carry = (carry / 58) | 0;
    }
    while (carry > 0) {
      digits.push(carry % 58);
      carry = (carry / 58) | 0;
    }
  }
  let out = "1".repeat(zeros);
  for (let i = digits.length - 1; i >= 0; i--) out += B58[digits[i]];
  return out;
}

export function base58btcDecode(str: string): Uint8Array {
  let zeros = 0;
  while (zeros < str.length && str[zeros] === "1") zeros++;
  const bytes: number[] = [];
  for (let i = zeros; i < str.length; i++) {
    let carry = B58MAP[str[i]];
    if (carry === undefined) throw new Error(`invalid base58 char: ${str[i]}`);
    for (let j = 0; j < bytes.length; j++) {
      carry += bytes[j] * 58;
      bytes[j] = carry & 0xff;
      carry >>= 8;
    }
    while (carry > 0) {
      bytes.push(carry & 0xff);
      carry >>= 8;
    }
  }
  const out = new Uint8Array(zeros + bytes.length);
  for (let i = 0; i < bytes.length; i++) out[zeros + bytes.length - 1 - i] = bytes[i];
  return out;
}

// ── did:key (ed25519, multicodec 0xed 0x01) ─────────────────────────────────
const ED25519_MULTICODEC = [0xed, 0x01];
// mldsa-65-pub = 0x1211 (multicodec registry, draft; FIPS 204) → varint [0x91, 0x24].
const MLDSA65_MULTICODEC = [0x91, 0x24];
const MLDSA65_PUB_BYTES = 1952;

/** raw 32-byte ed25519 public key → `did:key:z6Mk…` (== "did:key:" + the
 *  Ed25519VerificationKey2020 publicKeyMultibase). */
export function ed25519PubToDidKey(pubRaw: Uint8Array): string {
  if (pubRaw.length !== 32) throw new Error("ed25519 public key must be 32 bytes");
  const prefixed = new Uint8Array(2 + 32);
  prefixed.set(ED25519_MULTICODEC, 0);
  prefixed.set(pubRaw, 2);
  return "did:key:z" + base58btcEncode(prefixed);
}

/** `did:key:z…` (or a bare `z…` publicKeyMultibase) → raw 32-byte ed25519 key. */
export function didKeyToEd25519Pub(didKeyOrMultibase: string): Uint8Array {
  let mb = didKeyOrMultibase.startsWith("did:key:")
    ? didKeyOrMultibase.slice("did:key:".length)
    : didKeyOrMultibase;
  mb = mb.split("#")[0];
  if (!mb.startsWith("z")) throw new Error("expected multibase 'z' (base58btc)");
  const decoded = base58btcDecode(mb.slice(1));
  if (decoded[0] !== 0xed || decoded[1] !== 0x01) throw new Error("not an ed25519 multicodec key");
  return decoded.slice(2);
}

/** raw 1952-byte ML-DSA-65 public key → `did:key:z…` (multicodec mldsa-65-pub,
 *  0x1211 draft). Suite pqh-v1, ADR-2606111300. */
export function mlDsa65PubToDidKey(pubRaw: Uint8Array): string {
  if (pubRaw.length !== MLDSA65_PUB_BYTES) {
    throw new Error(`ml-dsa-65 public key must be ${MLDSA65_PUB_BYTES} bytes`);
  }
  const prefixed = new Uint8Array(2 + MLDSA65_PUB_BYTES);
  prefixed.set(MLDSA65_MULTICODEC, 0);
  prefixed.set(pubRaw, 2);
  return "did:key:z" + base58btcEncode(prefixed);
}

/** `did:key:z…` (or a bare `z…` publicKeyMultibase) → raw 1952-byte ML-DSA-65 key. */
export function didKeyToMlDsa65Pub(didKeyOrMultibase: string): Uint8Array {
  let mb = didKeyOrMultibase.startsWith("did:key:")
    ? didKeyOrMultibase.slice("did:key:".length)
    : didKeyOrMultibase;
  mb = mb.split("#")[0];
  if (!mb.startsWith("z")) throw new Error("expected multibase 'z' (base58btc)");
  const decoded = base58btcDecode(mb.slice(1));
  if (decoded[0] !== MLDSA65_MULTICODEC[0] || decoded[1] !== MLDSA65_MULTICODEC[1]) {
    throw new Error("not an ml-dsa-65 multicodec key");
  }
  const pub = decoded.slice(2);
  if (pub.length !== MLDSA65_PUB_BYTES) {
    throw new Error(`ml-dsa-65 public key must be ${MLDSA65_PUB_BYTES} bytes`);
  }
  return pub;
}

// ── attestation ─────────────────────────────────────────────────────────────
export interface AttestationPayload {
  readonly did: string;
  readonly didDocCid: string;
  readonly signedAt: string; // ISO-8601
  readonly sequence: number; // monotonic; lets a later attestation supersede
}

export interface DidDocAttestation extends AttestationPayload {
  readonly type: "EtzhayyimDidDocAttestation";
  readonly proof: {
    readonly type: "Ed25519Signature2020";
    readonly verificationMethod: string; // did:key:z…
    readonly proofValue: string; // multibase 'z' base58btc signature
  };
  /**
   * Optional post-quantum companion proof (suite pqh-v1, ADR-2606111300):
   * ML-DSA-65 over the SAME attestationMessage bytes. AND-composed — when
   * present (or required by the verifier) BOTH signatures must verify, so a
   * forger has to break Ed25519 AND ML-DSA-65.
   */
  readonly pqProof?: {
    readonly type: "MlDsa65Signature2026";
    readonly verificationMethod: string; // did:key:z… (mldsa-65-pub multicodec)
    readonly proofValue: string; // multibase 'z' base58btc signature (3309 bytes)
  };
}

/** Deterministic bytes signed by the attestation (payload only, stable order). */
export function attestationMessage(p: AttestationPayload): Uint8Array {
  return new TextEncoder().encode(
    JSON.stringify({ did: p.did, didDocCid: p.didDocCid, signedAt: p.signedAt, sequence: p.sequence }),
  );
}

export interface VerifyResult {
  readonly valid: boolean;
  readonly did: string;
  readonly didDocCid: string;
  readonly didKey: string;
  readonly reason?: string;
}

export interface VerifyOpts {
  /**
   * Require a valid pqProof (suite pqh-v1). Flip on once an actor publishes
   * an ML-DSA did:key — a stripped pqProof then fails closed instead of
   * silently downgrading to Ed25519-only. Default false for one R-cycle
   * (crypto-agility read-compat).
   */
  readonly requirePq?: boolean;
  /**
   * Pin the expected ML-DSA did:key (or bare multibase), as published in the
   * CID-verified did.json's verificationMethod. Without the pin, a pqProof
   * only proves SOME ML-DSA key signed the payload — a quantum-capable
   * attacker (who can forge the Ed25519 proof) could substitute their own
   * key with a self-consistent signature. The pin closes that substitution:
   * the trust anchor under the PQ threat model is the doc-published key,
   * not the Ed25519 binding.
   */
  readonly expectedPqDidKey?: string;
}

/** Verify a self-certifying attestation. If `expectedDidDocCid` is given, also
 *  checks the signed CID matches it. Self-certifying: the signing key comes from
 *  the proof's `did:key`, so no external anchor is consulted. When a pqProof is
 *  present (or `opts.requirePq`), the ML-DSA-65 signature over the same bytes
 *  must ALSO verify (AND-composition per ADR-2606111300). */
export async function verifyDidDocAttestation(
  att: DidDocAttestation,
  expectedDidDocCid?: string,
  opts?: VerifyOpts,
): Promise<VerifyResult> {
  const didKey = att.proof?.verificationMethod ?? "";
  const base: Omit<VerifyResult, "valid" | "reason"> = {
    did: att.did,
    didDocCid: att.didDocCid,
    didKey,
  };
  try {
    if (att.type !== "EtzhayyimDidDocAttestation") return { ...base, valid: false, reason: "wrong type" };
    if (expectedDidDocCid && att.didDocCid !== expectedDidDocCid) {
      return { ...base, valid: false, reason: "didDocCid mismatch" };
    }
    const msg = attestationMessage(att);
    const pub = didKeyToEd25519Pub(didKey);
    const sigMb = att.proof.proofValue;
    if (!sigMb.startsWith("z")) return { ...base, valid: false, reason: "proofValue not multibase z" };
    const sig = base58btcDecode(sigMb.slice(1));
    const key = await crypto.subtle.importKey("raw", pub, { name: "Ed25519" }, false, ["verify"]);
    const ok = await crypto.subtle.verify({ name: "Ed25519" }, key, sig, msg);
    if (!ok) return { ...base, valid: false, reason: "bad signature" };

    if ((opts?.requirePq || opts?.expectedPqDidKey) && !att.pqProof) {
      return { ...base, valid: false, reason: "pqProof required but absent" };
    }
    if (att.pqProof) {
      if (att.pqProof.type !== "MlDsa65Signature2026") {
        return { ...base, valid: false, reason: "unsupported pqProof type" };
      }
      if (opts?.expectedPqDidKey) {
        // Compare raw key bytes, tolerating did:key vs bare-multibase forms.
        const expected = didKeyToMlDsa65Pub(opts.expectedPqDidKey);
        const actual = didKeyToMlDsa65Pub(att.pqProof.verificationMethod);
        let same = expected.length === actual.length;
        for (let i = 0; same && i < expected.length; i++) same = expected[i] === actual[i];
        if (!same) {
          return { ...base, valid: false, reason: "pqProof key does not match pinned key" };
        }
      }
      const pqSigMb = att.pqProof.proofValue;
      if (!pqSigMb.startsWith("z")) {
        return { ...base, valid: false, reason: "pq proofValue not multibase z" };
      }
      const pqPub = didKeyToMlDsa65Pub(att.pqProof.verificationMethod);
      const pqSig = base58btcDecode(pqSigMb.slice(1));
      // No WebCrypto ML-DSA yet — pure-JS FIPS 204 from the noble family.
      const { ml_dsa65 } = await import("@noble/post-quantum/ml-dsa.js");
      const pqOk = ml_dsa65.verify(pqSig, msg, pqPub);
      if (!pqOk) return { ...base, valid: false, reason: "bad pq signature" };
    }
    return { ...base, valid: true };
  } catch (e) {
    return { ...base, valid: false, reason: e instanceof Error ? e.message : "verify error" };
  }
}
