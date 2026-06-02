/**
 * kotoba-service-auth — DID-rooted AT Protocol service-auth minter.
 *
 * Replaces the old design where `com.atproto.server.getServiceAuth` was
 * proxied to a remote MCP router (`mcp.etzhayyim.com`) — a central hop that
 * hung and took platform-wide bearer minting down with it.
 *
 * Modeled on the kotoba auth design (crates/kotoba-auth) applied as PRINCIPLES,
 * not wire format (AT Protocol fixes the ES256 JWT contract — no CACAO here):
 *   - DID-rooted, self-certifying: the issuer signs with ITS OWN key, locally;
 *     no delegation to a remote service to produce a token (kotoba "no central
 *     hop"). did:web service DIDs sign with the worker secret key; did:gftd
 *     account DIDs decrypt their KEK envelope from KEYS_DB (Phase 3).
 *   - Capability scoping: the AT `lxm` (lexicon method) is treated as a
 *     capability (kotoba `kotoba://can/{op}`) and checked against a mintable
 *     allowlist before a token is ever signed (kotoba CapabilityDenied).
 *   - Fail-safe temporal bounds: tokens carry a short `exp` (the audited signer
 *     uses 60s) + a unique `jti` for the revocation store (Phase 3).
 *
 * Wire format stays AT-compatible: ES256 (P-256) JWT with
 * {iss, sub, aud, exp, iat, jti, lxm}, verifiable by the PDS
 * `verifyServiceAuthJWT` against the issuer's P-256 key published in did.json.
 */
import { decodeBase64Url, encodeBase64Url, encodeJsonBase64Url } from "./base64url";

// ── Env contract ────────────────────────────────────────────────────────────

export interface KotobaAuthEnv {
  /** P-256 private scalar `d` (base64url) for the platform service DID. */
  SS_SERVICE_AUTH_PRIVATE_KEY?: string;
  /** Uncompressed P-256 public key (65B, 0x04||x||y, base64url) — for did.json. */
  SS_AUTH_PUBLIC_KEY_B64?: string;
  /** Rotation: next/previous keypair (published in did.json grace window). */
  SS_SERVICE_AUTH_PRIVATE_KEY_NEXT?: string;
  SS_AUTH_PUBLIC_KEY_B64_NEXT?: string;
  /** Service DID this worker is authoritative for (default did:web:atproto.gftd.ai). */
  PDS_DID?: string;
  /** KEK (hex, 32B) for did:gftd KEYS_DB envelope decrypt (Phase 3). */
  SS_REPO_SIGNING_KEK?: string;
  /**
   * D1 key custody (did:gftd signing keys + revocation) — Phase 3. Typed
   * minimally because the svelte project does not pull @cloudflare/workers-types;
   * the Phase 3 KEK branch narrows it to the bind/first/run shape it uses.
   */
  KEYS_DB?: D1Like;
}

/** Minimal D1 surface used by the Phase 3 KEK / revocation branches. */
export interface D1Like {
  prepare(query: string): {
    bind(...values: unknown[]): {
      first<T = Record<string, unknown>>(): Promise<T | null>;
      run(): Promise<unknown>;
    };
  };
}

// ── Capability model (kotoba `kotoba://can/{op}` → AT lxm) ────────────────────

/** NSID syntax (AT Protocol lexicon method id). */
const NSID_RE = /^[a-z][a-z0-9]*(?:\.[a-z][a-z0-9]*){2,}$/i;

/**
 * lxm values this minter is allowed to scope a token to. A service-auth bearer
 * is a write/admin capability against the PDS, so the surface is deliberately
 * narrow: repo read/write methods only. (kotoba: capability attenuation —
 * a token may only carry capabilities the minter is willing to grant.)
 */
export const MINTABLE_LXM: ReadonlySet<string> = new Set([
  "com.atproto.repo.uploadBlob",
  "com.atproto.repo.createRecord",
  "com.atproto.repo.putRecord",
  "com.atproto.repo.deleteRecord",
  "com.atproto.repo.applyWrites",
  "com.atproto.repo.listRecords",
  "com.atproto.repo.getRecord",
]);

/**
 * A token may be unscoped (no `lxm` — AT Protocol allows this and the PDS
 * accepts it). A scoped token's lxm must be a syntactically valid NSID present
 * in the allowlist.
 */
export function isMintableLxm(lxm?: string): boolean {
  if (lxm === undefined || lxm === null || lxm === "") return true;
  return NSID_RE.test(lxm) && MINTABLE_LXM.has(lxm);
}

export class MintError extends Error {
  constructor(public code: string, message?: string) {
    super(message ?? code);
    this.name = "MintError";
  }
}

// ── P-256 / ES256 signer (vendored from src-ts/service-auth.ts) ───────────────
// The svelte deploy bundles only files reachable from src/; it does not import
// worker/src-ts. This is a faithful copy of the audited signer so the wire
// format (and the published verifying key) stay identical.

const SERVICE_AUTH_EXPIRY_SECS = 60;

const P = BigInt("0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff");
const A = BigInt("0xffffffff00000001000000000000000000000000fffffffffffffffffffffffc");
const GX = BigInt("0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296");
const GY = BigInt("0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5");

type Point = { x: bigint; y: bigint } | null;

function nowSecs(): number {
  return Math.floor(Date.now() / 1000);
}

function mod(value: bigint): bigint {
  const result = value % P;
  return result >= 0n ? result : result + P;
}

function modPow(base: bigint, exp: bigint): bigint {
  let result = 1n;
  let current = mod(base);
  let power = exp;
  while (power > 0n) {
    if (power & 1n) result = mod(result * current);
    current = mod(current * current);
    power >>= 1n;
  }
  return result;
}

function inv(value: bigint): bigint {
  return modPow(value, P - 2n);
}

function addPoints(p1: Point, p2: Point): Point {
  if (!p1) return p2;
  if (!p2) return p1;
  if (p1.x === p2.x && mod(p1.y + p2.y) === 0n) return null;
  const lambda =
    p1.x === p2.x && p1.y === p2.y
      ? mod((3n * p1.x * p1.x + A) * inv(2n * p1.y))
      : mod((p2.y - p1.y) * inv(p2.x - p1.x));
  const x = mod(lambda * lambda - p1.x - p2.x);
  const y = mod(lambda * (p1.x - x) - p1.y);
  return { x, y };
}

function scalarMultiply(scalar: bigint, point: Point): Point {
  let n = scalar;
  let result: Point = null;
  let current = point;
  while (n > 0n) {
    if (n & 1n) result = addPoints(result, current);
    current = addPoints(current, current);
    n >>= 1n;
  }
  return result;
}

function bytesToBigInt(bytes: Uint8Array): bigint {
  return BigInt(`0x${Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("")}`);
}

function bigIntToBytes(value: bigint, length: number): Uint8Array {
  const hex = value.toString(16).padStart(length * 2, "0");
  const out = new Uint8Array(length);
  for (let i = 0; i < length; i += 1) {
    out[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  }
  return out;
}

function derivePublicCoordinates(privateKeyB64: string): { x: string; y: string } {
  const scalar = bytesToBigInt(decodeBase64Url(privateKeyB64));
  const point = scalarMultiply(scalar, { x: GX, y: GY });
  if (!point) throw new Error("invalid derived public key");
  return {
    x: encodeBase64Url(bigIntToBytes(point.x, 32)),
    y: encodeBase64Url(bigIntToBytes(point.y, 32)),
  };
}

let cachedPrivateKey: { b64: string; key: CryptoKey } | null = null;

async function importPrivateKey(privateKeyB64: string): Promise<CryptoKey> {
  if (cachedPrivateKey && cachedPrivateKey.b64 === privateKeyB64) return cachedPrivateKey.key;
  const { x, y } = derivePublicCoordinates(privateKeyB64);
  const key = await crypto.subtle.importKey(
    "jwk",
    { kty: "EC", crv: "P-256", d: privateKeyB64, x, y, ext: true },
    { name: "ECDSA", namedCurve: "P-256" },
    false,
    ["sign"],
  );
  cachedPrivateKey = { b64: privateKeyB64, key };
  return key;
}

/** Sign an AT Protocol service-auth JWT (ES256). Returns the compact JWT. */
async function signServiceAuthJwt(
  privateKeyB64: string,
  iss: string,
  aud: string,
  lxm?: string,
  sub?: string,
): Promise<string> {
  const now = nowSecs();
  const headerB64 = encodeJsonBase64Url({ alg: "ES256", typ: "JWT" });
  const payloadB64 = encodeJsonBase64Url({
    iss,
    sub: sub || iss,
    aud,
    exp: now + SERVICE_AUTH_EXPIRY_SECS,
    iat: now,
    jti: crypto.randomUUID(),
    ...(lxm ? { lxm } : {}),
  });
  const signingInput = `${headerB64}.${payloadB64}`;
  const key = await importPrivateKey(privateKeyB64);
  const signature = await crypto.subtle.sign(
    { name: "ECDSA", hash: "SHA-256" },
    key,
    new TextEncoder().encode(signingInput),
  );
  return `${signingInput}.${encodeBase64Url(signature)}`;
}

// ── DID-rooted key resolution (kotoba: did:web / did:gftd) ─────────────────────

function defaultServiceDid(env: KotobaAuthEnv): string {
  return env.PDS_DID?.trim() || "did:web:atproto.gftd.ai";
}

/**
 * Resolve the issuer's P-256 signing scalar (base64url `d`), kotoba dual source:
 *   - did:web:*  (service DID)  → SS_SERVICE_AUTH_PRIVATE_KEY worker secret
 *   - did:gftd:* (account DID)  → KEYS_DB KEK envelope decrypt (Phase 3)
 */
export async function loadIssuerPrivateKeyB64(env: KotobaAuthEnv, iss: string): Promise<string> {
  if (iss.startsWith("did:web:")) {
    const d = env.SS_SERVICE_AUTH_PRIVATE_KEY?.trim();
    if (!d) throw new MintError("signerUnavailable", "SS_SERVICE_AUTH_PRIVATE_KEY not configured");
    return d;
  }
  if (iss.startsWith("did:gftd:")) {
    // Phase 3: decrypt vertex_gftd_key_signing envelope under SS_REPO_SIGNING_KEK.
    throw new MintError("issuerUnsupported", `did:gftd minting not yet wired: ${iss}`);
  }
  throw new MintError("badIss", `unsupported issuer DID method: ${iss}`);
}

export interface MintRequest {
  iss?: string;
  aud?: string;
  lxm?: string;
  sub?: string;
}

export interface MintResult {
  token: string;
  jti: string;
  exp: number;
}

function decodeJtiExp(jwt: string): { jti: string; exp: number } {
  const parts = jwt.split(".");
  const payload = JSON.parse(new TextDecoder().decode(decodeBase64Url(parts[1]))) as {
    jti?: string;
    exp?: number;
  };
  return { jti: String(payload.jti ?? ""), exp: Number(payload.exp ?? 0) };
}

/**
 * Mint an AT Protocol service-auth bearer. Self-certifying: signs locally with
 * the issuer's own key. Enforces the capability allowlist before signing.
 */
export async function mintServiceAuth(env: KotobaAuthEnv, req: MintRequest): Promise<MintResult> {
  const iss = (req.iss?.trim() || defaultServiceDid(env));
  const aud = (req.aud?.trim() || defaultServiceDid(env));
  const lxm = req.lxm?.trim() || undefined;
  const sub = req.sub?.trim() || undefined;

  if (!iss.startsWith("did:")) throw new MintError("badIss", `iss must be a DID: ${iss}`);
  if (!aud.startsWith("did:")) throw new MintError("badAud", `aud must be a DID: ${aud}`);
  if (!isMintableLxm(lxm)) throw new MintError("lxmNotMintable", `lxm not mintable: ${lxm}`);

  const priv = await loadIssuerPrivateKeyB64(env, iss);
  const token = await signServiceAuthJwt(priv, iss, aud, lxm, sub);
  const { jti, exp } = decodeJtiExp(token);
  return { token, jti, exp };
}

// ── did.json publication helper (P-256 multibase) ─────────────────────────────
// Mirrors src-ts/did.ts uncompressedPubkeyB64UrlToMultibase: encodes the
// uncompressed P-256 public key as `z<base58(0x80 0x24 || compressed)>` —
// the multicodec prefix the PDS verifier (verify.ts) decodes. Vendored so the
// /internal/service-auth-pubkey route (served from this deploy) can compute it.

const MULTICODEC_P256_PREFIX = new Uint8Array([0x80, 0x24]);
const BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";

function base58Encode(bytes: Uint8Array): string {
  if (bytes.length === 0) return "";
  const digits = [0];
  for (const byte of bytes) {
    let carry = byte;
    for (let i = 0; i < digits.length; i += 1) {
      carry += digits[i] * 256;
      digits[i] = carry % 58;
      carry = Math.floor(carry / 58);
    }
    while (carry > 0) {
      digits.push(carry % 58);
      carry = Math.floor(carry / 58);
    }
  }
  let out = "";
  for (const byte of bytes) {
    if (byte !== 0) break;
    out += BASE58_ALPHABET[0];
  }
  for (let i = digits.length - 1; i >= 0; i -= 1) out += BASE58_ALPHABET[digits[i]];
  return out;
}

function compressPoint(x: Uint8Array, y: Uint8Array): Uint8Array {
  const prefix = (y[y.length - 1] & 1) === 0 ? 0x02 : 0x03;
  const out = new Uint8Array(33);
  out[0] = prefix;
  out.set(x, 1);
  return out;
}

/** Uncompressed P-256 pub (65B, 0x04||x||y, base64url) → did:key multibase. */
export function uncompressedPubkeyB64UrlToMultibase(b64url: string): string {
  const bytes = decodeBase64Url(b64url);
  if (bytes.length !== 65 || bytes[0] !== 0x04) {
    throw new Error("expected 65-byte uncompressed P-256 key (0x04 || x || y)");
  }
  const compressed = compressPoint(bytes.slice(1, 33), bytes.slice(33, 65));
  const prefixed = new Uint8Array(MULTICODEC_P256_PREFIX.length + compressed.length);
  prefixed.set(MULTICODEC_P256_PREFIX, 0);
  prefixed.set(compressed, MULTICODEC_P256_PREFIX.length);
  return `z${base58Encode(prefixed)}`;
}

export interface ServiceAuthPubkey {
  multibase: string;
  kind: "current" | "next";
}

/**
 * The P-256 service-auth verification keys to publish in the service DID's
 * did.json (so the PDS verifyServiceAuthJWT can resolve them). Includes the
 * rotation `_NEXT` key if configured (grace window — the PDS tries all keys).
 */
export function serviceAuthPubkeysMultibase(env: KotobaAuthEnv): ServiceAuthPubkey[] {
  const out: ServiceAuthPubkey[] = [];
  if (env.SS_AUTH_PUBLIC_KEY_B64?.trim()) {
    out.push({ multibase: uncompressedPubkeyB64UrlToMultibase(env.SS_AUTH_PUBLIC_KEY_B64.trim()), kind: "current" });
  }
  if (env.SS_AUTH_PUBLIC_KEY_B64_NEXT?.trim()) {
    out.push({ multibase: uncompressedPubkeyB64UrlToMultibase(env.SS_AUTH_PUBLIC_KEY_B64_NEXT.trim()), kind: "next" });
  }
  return out;
}
