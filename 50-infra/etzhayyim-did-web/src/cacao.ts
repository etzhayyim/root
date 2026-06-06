/**
 * CACAO (CAIP-74) verify-only surface for the apex Worker.
 * ADR-2606060000 — `/profile` same-origin auth (WebAuthn / passkey / SIWE).
 *
 * This is a no-server-key surface: the Worker holds NO signing key and never
 * mints a session. It VERIFIES a member-signed CACAO and returns the resolved
 * DID + capability scope. Three sign-in methods converge on ONE artifact — a
 * member-signed CACAO — so the apex Worker only needs one verifier:
 *
 *   - WebAuthn passkey → PRF → ARK → k_session → Ed25519 session key (did:key)
 *     signs an `EdDSA` CACAO. Verified LOCALLY here via WebCrypto Ed25519
 *     (native in the Workers runtime + Node ≥ 20) — zero dependencies.
 *   - Wallet / SIWE (EIP-4361) → did:pkh:eip155 EOA or ERC-4337 smart account
 *     signs an `eip191` CACAO. The plaintext + structure are validated locally;
 *     secp256k1 recovery / ERC-1271 is the audited Rust SSoT in `kotoba-auth`
 *     (`verify_signature_eip191_smart`), so the apex relays the CACAO to the
 *     kotoba node for signature recovery (the apex bundles no secp256k1). When
 *     the kotoba endpoint is not enabled (R0) the `eip191` leg reports `gated`.
 *
 * The CACAO wire shape is byte-identical to kotoba's
 * `40-engine/kotoba/crates/kotoba-auth/src/cacao.rs` (`Cacao { h, p, s }`), so
 * the same token verifies here and on the kotoba node.
 */

// ─── CACAO types (mirror of kotoba-auth/src/cacao.rs) ───────────────────────

export interface CacaoHeader {
  /** "eip4361" | "caip122" */
  t: string;
}

export interface CacaoPayload {
  /** Issuer DID — did:key:z6Mk… | did:pkh:eip155:N:0x… | did:erc725:… */
  iss: string;
  /** Audience — this node's DID or URI (we bind it to the apex origin). */
  aud: string;
  /** Issued-at, strict UTC ISO-8601. */
  iat: string;
  /** Expiry, strict UTC ISO-8601 (optional). */
  exp?: string;
  /** Single-use nonce. */
  nonce: string;
  /** Requesting domain (e.g. "etzhayyim.com"). */
  domain?: string;
  /** EIP-4361 optional statement. */
  statement?: string;
  /** Message version (default "1"). */
  version?: string;
  /** Capability resources as URIs (kotoba://op/… + kotoba://graph/…). */
  resources?: string[];
}

export interface CacaoSig {
  /** "eip191" | "EdDSA" */
  t: string;
  /** hex (0x-prefixed or bare) or base64 signature. */
  s: string;
}

export interface Cacao {
  h: CacaoHeader;
  p: CacaoPayload;
  s: CacaoSig;
}

export type VerifyOutcome =
  | { valid: true; did: string; sigType: string; method: "ed25519-local" }
  | {
      valid: false;
      reason: string;
      /** true ⇒ structurally valid but crypto-verify must run on the kotoba node. */
      gated?: boolean;
      sigType?: string;
    };

// ─── base58btc (Bitcoin alphabet) — for did:key decode ──────────────────────

const B58_ALPHABET =
  "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
const B58_MAP: Record<string, number> = (() => {
  const m: Record<string, number> = {};
  for (let i = 0; i < B58_ALPHABET.length; i += 1) m[B58_ALPHABET[i]] = i;
  return m;
})();

export function base58btcDecode(input: string): Uint8Array {
  if (input.length === 0) return new Uint8Array(0);
  const bytes: number[] = [0];
  for (const ch of input) {
    const value = B58_MAP[ch];
    if (value === undefined) throw new Error(`invalid base58 char: ${ch}`);
    let carry = value;
    for (let j = 0; j < bytes.length; j += 1) {
      carry += bytes[j] * 58;
      bytes[j] = carry & 0xff;
      carry >>= 8;
    }
    while (carry > 0) {
      bytes.push(carry & 0xff);
      carry >>= 8;
    }
  }
  // leading '1's → leading zero bytes
  for (let k = 0; k < input.length && input[k] === "1"; k += 1) bytes.push(0);
  return new Uint8Array(bytes.reverse());
}

/**
 * Parse a `did:key:z6Mk…` Ed25519 DID into its raw 32-byte public key.
 * did:key = "did:key:" + multibase('z' = base58btc, 0xed 0x01 || 32-byte-key).
 */
export function parseEd25519DidKey(did: string): Uint8Array {
  const PREFIX = "did:key:z";
  if (!did.startsWith(PREFIX)) {
    throw new Error("not a base58btc did:key");
  }
  const decoded = base58btcDecode(did.slice(PREFIX.length));
  // multicodec ed25519-pub = 0xed 0x01, then 32-byte key.
  if (decoded.length !== 34 || decoded[0] !== 0xed || decoded[1] !== 0x01) {
    throw new Error("did:key is not ed25519-pub (expected 0xed01 + 32 bytes)");
  }
  return decoded.slice(2);
}

// ─── signature decode (hex or base64) ───────────────────────────────────────

function hexToBytes(hex: string): Uint8Array {
  const clean = hex.startsWith("0x") ? hex.slice(2) : hex;
  if (clean.length % 2 !== 0) throw new Error("hex length must be even");
  const out = new Uint8Array(clean.length / 2);
  for (let i = 0; i < out.length; i += 1) {
    const byte = parseInt(clean.slice(i * 2, i * 2 + 2), 16);
    if (Number.isNaN(byte)) throw new Error("invalid hex");
    out[i] = byte;
  }
  return out;
}

function base64ToBytes(b64: string): Uint8Array {
  const bin = atob(b64.replace(/-/g, "+").replace(/_/g, "/"));
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i += 1) out[i] = bin.charCodeAt(i);
  return out;
}

/** Decode a CACAO signature string (hex with/without 0x, or base64). */
export function decodeSigBytes(s: string): Uint8Array {
  const isHex = /^(0x)?[0-9a-fA-F]+$/.test(s) && (s.replace(/^0x/, "").length % 2 === 0);
  if (isHex) return hexToBytes(s);
  return base64ToBytes(s);
}

// ─── strict UTC ISO-8601 + expiry (fail-safe, mirror of cacao.rs) ───────────

const STRICT_UTC_ISO8601 =
  /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$/;

export function isStrictUtcIso8601(s: string): boolean {
  if (!STRICT_UTC_ISO8601.test(s)) return false;
  const ms = Date.parse(s);
  return Number.isFinite(ms);
}

/**
 * Returns true iff the CACAO has an `exp` that is in the past. A malformed
 * `exp` is treated as expired (fail-safe), matching the Rust `is_expired`.
 */
export function isExpired(cacao: Cacao, nowMs: number): boolean {
  const exp = cacao.p.exp;
  if (exp === undefined || exp === null) return false;
  if (!isStrictUtcIso8601(exp)) return true;
  return nowMs > Date.parse(exp);
}

// ─── SIWE message reconstruction (byte-identical to cacao.rs siwe_message) ──

export function siweMessage(cacao: Cacao): string {
  const p = cacao.p;
  const segments = p.iss.split(":");
  const address = segments[segments.length - 1] || p.iss;
  // did:key → CAIP-122 default chain "1"; did:pkh:eip155:N:0x.. → N
  const chainId = p.iss.startsWith("did:key:")
    ? "1"
    : segments.length >= 2
      ? segments[segments.length - 2]
      : "1";

  const lines: string[] = [];
  lines.push(`${p.domain ?? ""} wants you to sign in with your Ethereum account:`);
  lines.push(address);
  lines.push("");
  if (p.statement) {
    lines.push(p.statement);
    lines.push("");
  }
  lines.push(`URI: ${p.aud}`);
  lines.push(`Version: ${p.version ?? "1"}`);
  lines.push(`Chain ID: ${chainId}`);
  lines.push(`Nonce: ${p.nonce}`);
  lines.push(`Issued At: ${p.iat}`);
  if (p.exp) lines.push(`Expiration Time: ${p.exp}`);
  if (p.resources && p.resources.length > 0) {
    lines.push("Resources:");
    for (const r of p.resources) lines.push(`- ${r}`);
  }
  return lines.join("\n");
}

// ─── structural validation ──────────────────────────────────────────────────

export function isWellFormed(c: unknown): c is Cacao {
  if (!c || typeof c !== "object") return false;
  const cc = c as Record<string, unknown>;
  const h = cc.h as Record<string, unknown> | undefined;
  const p = cc.p as Record<string, unknown> | undefined;
  const s = cc.s as Record<string, unknown> | undefined;
  if (!h || typeof h.t !== "string") return false;
  if (!s || typeof s.t !== "string" || typeof s.s !== "string") return false;
  if (!p) return false;
  for (const k of ["iss", "aud", "iat", "nonce"]) {
    if (typeof p[k] !== "string" || (p[k] as string).length === 0) return false;
  }
  return true;
}

// ─── Ed25519 verification (WebCrypto, zero-dep) ─────────────────────────────

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
 * Verify a CACAO. Stateless, no-server-key.
 *
 * - `EdDSA`  → verified locally (WebCrypto Ed25519). Issuer must be a
 *   `did:key:z6Mk…` Ed25519 key (the passkey-derived session key).
 * - `eip191` → structure + SIWE plaintext validated; signature recovery is
 *   `gated` (must run on the kotoba node — see module docs).
 *
 * Temporal/structural checks (well-formed, not-expired) run for BOTH types.
 */
export async function verifyCacao(
  cacao: Cacao,
  nowMs: number,
): Promise<VerifyOutcome> {
  if (!isWellFormed(cacao)) {
    return { valid: false, reason: "malformed CACAO" };
  }
  if (isExpired(cacao, nowMs)) {
    return { valid: false, reason: "CACAO expired", sigType: cacao.s.t };
  }

  const sigType = cacao.s.t;
  if (sigType === "EdDSA") {
    let pubkey: Uint8Array;
    try {
      pubkey = parseEd25519DidKey(cacao.p.iss);
    } catch (e) {
      return {
        valid: false,
        reason: `EdDSA issuer must be did:key ed25519: ${
          e instanceof Error ? e.message : String(e)
        }`,
        sigType,
      };
    }
    let sig: Uint8Array;
    try {
      sig = decodeSigBytes(cacao.s.s);
    } catch (e) {
      return {
        valid: false,
        reason: `signature decode: ${e instanceof Error ? e.message : String(e)}`,
        sigType,
      };
    }
    const message = new TextEncoder().encode(siweMessage(cacao));
    let ok = false;
    try {
      ok = await verifyEd25519(pubkey, message, sig);
    } catch (e) {
      return {
        valid: false,
        reason: `ed25519 verify error: ${
          e instanceof Error ? e.message : String(e)
        }`,
        sigType,
      };
    }
    if (!ok) return { valid: false, reason: "ed25519 signature mismatch", sigType };
    return { valid: true, did: cacao.p.iss, sigType, method: "ed25519-local" };
  }

  if (sigType === "eip191") {
    // Structural validation only — secp256k1 recovery / ERC-1271 is the kotoba
    // SSoT verifier (no secp256k1 bundled in the apex). Confirm the issuer is a
    // did:pkh:eip155 address and the signature decodes; the caller relays to the
    // kotoba node for cryptographic recovery (or reports gated at R0).
    if (!/^did:pkh:eip155:\d+:0x[0-9a-fA-F]{40}$/.test(cacao.p.iss)) {
      return {
        valid: false,
        reason: "eip191 issuer must be did:pkh:eip155:N:0x<addr>",
        sigType,
      };
    }
    try {
      decodeSigBytes(cacao.s.s);
    } catch (e) {
      return {
        valid: false,
        reason: `signature decode: ${e instanceof Error ? e.message : String(e)}`,
        sigType,
      };
    }
    return {
      valid: false,
      gated: true,
      reason:
        "eip191 signature recovery delegated to the kotoba node " +
        "(verify_signature_eip191_smart); not enabled at R0",
      sigType,
    };
  }

  return { valid: false, reason: `unsupported sig type: ${sigType}`, sigType };
}
