/**
 * Standalone local verification for kotoba-service-auth (run: npx tsx this file).
 *
 * Proves the full chain WITHOUT deploying:
 *   mint (ES256, signed with SS_SERVICE_AUTH_PRIVATE_KEY)
 *     → publish SS_AUTH_PUBLIC_KEY_B64 as did:key multibase
 *     → decode + verify EXACTLY as the PDS verifyServiceAuthJWT does.
 * This is the gate for the curve-mismatch risk (R2): if the published key
 * does not verify the minted token, this fails loudly.
 */
import {
  mintServiceAuth,
  isMintableLxm,
  MintError,
  uncompressedPubkeyB64UrlToMultibase,
  type KotobaAuthEnv,
} from "../svelte/src/lib/kotoba-service-auth.ts";

// ── PDS-side decode, copied verbatim from atproto/src/auth/verify.ts ──────────
function decodeMultibase(encoded: string): Uint8Array | null {
  if (!encoded.startsWith("z")) return null;
  const ALPHA = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
  let n = 0n;
  for (const c of encoded.slice(1)) {
    const i = ALPHA.indexOf(c);
    if (i < 0) return null;
    n = n * 58n + BigInt(i);
  }
  const bytes: number[] = [];
  while (n > 0n) { bytes.unshift(Number(n & 0xffn)); n >>= 8n; }
  for (const c of encoded.slice(1)) { if (c === "1") bytes.unshift(0); else break; }
  return new Uint8Array(bytes);
}
function modpow(base: bigint, exp: bigint, mod: bigint): bigint {
  let r = 1n; base %= mod;
  while (exp > 0n) { if (exp & 1n) r = (r * base) % mod; exp >>= 1n; base = (base * base) % mod; }
  return r;
}
function decompressP256Point(compressed: Uint8Array): Uint8Array {
  const p = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffffn;
  const a = p - 3n;
  const b = 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604bn;
  let xn = 0n; for (const byte of compressed.slice(1)) xn = (xn << 8n) | BigInt(byte);
  const y2 = (modpow(xn, 3n, p) + ((a * xn) % p) + b) % p;
  let y = modpow(y2, (p + 1n) / 4n, p);
  if ((compressed[0] & 1) === 0 ? y % 2n !== 0n : y % 2n === 0n) y = p - y;
  const out = new Uint8Array(65);
  out[0] = 0x04;
  for (let i = 31; i >= 0; i--) { out[1 + i] = Number(xn & 0xffn); xn >>= 8n; }
  for (let i = 31; i >= 0; i--) { out[33 + i] = Number(y & 0xffn); y >>= 8n; }
  return out;
}
function b64url(s: string): Uint8Array {
  s = s.replace(/-/g, "+").replace(/_/g, "/");
  while (s.length % 4) s += "=";
  return Uint8Array.from(atob(s), (c) => c.charCodeAt(0));
}

/** Reproduce the PDS verifier: resolve the published multibase, verify ES256. */
async function pdsVerify(token: string, publishedMultibase: string): Promise<boolean> {
  const parts = token.split(".");
  if (parts.length !== 3) return false;
  const header = JSON.parse(new TextDecoder().decode(b64url(parts[0])));
  if (header.alg !== "ES256") return false;
  const raw = decodeMultibase(publishedMultibase);
  if (!raw) return false;
  const keyData = raw[0] === 0x80 && raw[1] === 0x24 ? raw.slice(2) : raw;
  const uncompressed = keyData.length === 33 ? decompressP256Point(keyData) : keyData;
  const pubKey = await crypto.subtle.importKey("raw", uncompressed, { name: "ECDSA", namedCurve: "P-256" }, false, ["verify"]);
  return crypto.subtle.verify(
    { name: "ECDSA", hash: "SHA-256" },
    pubKey,
    b64url(parts[2]),
    new TextEncoder().encode(`${parts[0]}.${parts[1]}`),
  );
}

// ── Fixture: a fresh P-256 keypair → (d base64url, uncompressed pub base64url) ─
function b64urlEncode(bytes: Uint8Array): string {
  let bin = ""; for (const x of bytes) bin += String.fromCharCode(x);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}
async function makeKeypair(): Promise<{ d: string; pubUncompressed: string }> {
  const kp = await crypto.subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign", "verify"]);
  const jwk = await crypto.subtle.exportKey("jwk", kp.privateKey);
  const rawPub = new Uint8Array(await crypto.subtle.exportKey("raw", kp.publicKey)); // 65B 0x04||x||y
  return { d: jwk.d!, pubUncompressed: b64urlEncode(rawPub) };
}

// ── Assertions ────────────────────────────────────────────────────────────────
let failures = 0;
function ok(cond: boolean, msg: string) {
  console.log(`${cond ? "  PASS" : "  FAIL"}  ${msg}`);
  if (!cond) failures += 1;
}

async function main() {
  console.log("== kotoba-service-auth local verification ==");

  const kp = await makeKeypair();
  const env: KotobaAuthEnv = {
    SS_SERVICE_AUTH_PRIVATE_KEY: kp.d,
    SS_AUTH_PUBLIC_KEY_B64: kp.pubUncompressed,
    PDS_DID: "did:web:atproto.gftd.ai",
  };

  // 1. Mint → decode header/claims
  const { token, jti, exp } = await mintServiceAuth(env, {
    iss: "did:web:atproto.gftd.ai",
    aud: "did:web:atproto.gftd.ai",
    lxm: "com.atproto.repo.uploadBlob",
  });
  const [h, p] = token.split(".");
  const header = JSON.parse(new TextDecoder().decode(b64url(h)));
  const payload = JSON.parse(new TextDecoder().decode(b64url(p)));
  ok(header.alg === "ES256" && header.typ === "JWT", "header alg=ES256 typ=JWT");
  ok(payload.iss === "did:web:atproto.gftd.ai", "iss = service DID");
  ok(payload.aud === "did:web:atproto.gftd.ai", "aud = service DID (verify.ts hardcodes this)");
  ok(payload.lxm === "com.atproto.repo.uploadBlob", "lxm carried as capability");
  ok(typeof payload.sub === "string" && payload.sub.startsWith("did:"), "sub present (DID)");
  ok(payload.jti === jti && payload.exp === exp, "jti/exp returned match payload");
  ok(payload.exp > payload.iat && payload.exp - payload.iat <= 60, "exp within 60s of iat (fail-safe temporal)");

  // 2. THE curve-mismatch gate: published multibase must verify the token
  const multibase = uncompressedPubkeyB64UrlToMultibase(env.SS_AUTH_PUBLIC_KEY_B64!);
  ok(multibase.startsWith("z"), `published multibase formed (${multibase.slice(0, 12)}…)`);
  ok(await pdsVerify(token, multibase), "PDS-style verify of token against PUBLISHED multibase ✓ (curve-match)");

  // 3. Negative control: a different key must NOT verify
  const other = await makeKeypair();
  const otherMb = uncompressedPubkeyB64UrlToMultibase(other.pubUncompressed);
  ok(!(await pdsVerify(token, otherMb)), "token does NOT verify against an unrelated key");

  // 4. Capability gate
  ok(isMintableLxm("com.atproto.repo.uploadBlob"), "uploadBlob is mintable");
  ok(isMintableLxm(undefined), "unscoped (no lxm) is allowed");
  ok(!isMintableLxm("com.atproto.server.createSession"), "createSession is NOT mintable");
  ok(!isMintableLxm("not-an-nsid"), "malformed lxm rejected");
  let threw = "";
  try { await mintServiceAuth(env, { lxm: "com.atproto.admin.deleteAccount" }); } catch (e) { threw = e instanceof MintError ? e.code : "other"; }
  ok(threw === "lxmNotMintable", "mint rejects non-allowlisted lxm with lxmNotMintable");

  // 5. did:gftd not wired yet (Phase 3) → explicit, not a silent secret-branch fallthrough
  let gftdErr = "";
  try { await mintServiceAuth(env, { iss: "did:gftd:abc123", aud: "did:web:atproto.gftd.ai" }); } catch (e) { gftdErr = e instanceof MintError ? e.code : "other"; }
  ok(gftdErr === "issuerUnsupported", "did:gftd minting explicitly unsupported (Phase 3)");

  console.log(failures === 0 ? "\nALL PASS" : `\n${failures} FAILURE(S)`);
  process.exit(failures === 0 ? 0 : 1);
}

main().catch((e) => { console.error("test crashed:", e); process.exit(1); });
