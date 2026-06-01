// s3-sigv4.ts — AWS Signature Version 4 verifier for /s3/* (P3.2).
//
// Verifies an inbound `Authorization: AWS4-HMAC-SHA256 …` header against
// the raw `aws_secret_access_key` stored in vertex_api_key. Two side
// effects:
//
//   1. Resolves the access_key_id → owner_did + product_scope so the
//      yatabase Worker can build the same DispatcherCallerContext used
//      by the Bearer-token path.
//   2. Caches the (access_key_id → row) mapping for 60s in a per-isolate
//      Map to keep the hot path at zero Hyperdrive round-trip after
//      first hit.
//
// Reference (canonical request, string-to-sign, signing key derivation):
//   https://docs.aws.amazon.com/AmazonS3/latest/API/sig-v4-authenticating-requests.html
//
// Implementation note:
//   - We support only the header-based AWS4-HMAC-SHA256 flow. Pre-signed
//     URL flow (X-Amz-Algorithm in query string) is handled separately
//     in P3.2.5 alongside multipart copy.
//   - Body hash is taken from the `x-amz-content-sha256` header. For
//     PUT requests the client MUST send this header (boto3 / aws-sdk-js
//     do by default). When the header value is `UNSIGNED-PAYLOAD` we
//     skip the body hash check (intended for streaming upload).
//   - Clock skew tolerance is ±15 minutes (AWS standard).

interface AnyKyselyDb {
  selectFrom(table: string): {
    select(cols: string[]): {
      where(col: string, op: string, val: unknown): {
        where(col: string, op: string, val: unknown): {
          limit(n: number): {
            executeTakeFirst(): Promise<Record<string, unknown> | undefined>;
          };
        };
      };
    };
  };
}

export interface SigV4VerifyEnv {
  HYPERDRIVE?: unknown;
  YATABASE_AUTH_CACHE?: KVNamespace; // P86: KV mirror of aws creds
}

export interface SigV4VerifyResult {
  ownerDid: string;
  scopes: string[];
  productScope: "yata" | "obj" | null;
  awsAccessKeyId: string;
}

interface CachedKeyRow {
  ownerDid: string;
  scopes: string[];
  productScope: "yata" | "obj" | null;
  secret: string;
  at: number;
}

const _akCache = new Map<string, CachedKeyRow | null>();
const AK_CACHE_TTL = 60_000;

const SKEW_TOLERANCE_SEC = 15 * 60;

// ──────────────────────────────────────────────────────────────────────
// Helpers — parse Authorization header
// ──────────────────────────────────────────────────────────────────────

interface ParsedAuth {
  algorithm: "AWS4-HMAC-SHA256";
  credential: string;        // <accessKeyId>/<date>/<region>/<service>/aws4_request
  accessKeyId: string;
  date: string;              // YYYYMMDD
  region: string;
  service: string;
  signedHeaders: string[];   // sorted lowercase
  signature: string;         // hex
}

export function parseAuthorizationHeader(h: string): ParsedAuth | null {
  if (!h.startsWith("AWS4-HMAC-SHA256 ")) return null;
  const body = h.slice("AWS4-HMAC-SHA256 ".length);
  const parts: Record<string, string> = {};
  for (const pair of body.split(",")) {
    const eq = pair.indexOf("=");
    if (eq < 0) continue;
    parts[pair.slice(0, eq).trim()] = pair.slice(eq + 1).trim();
  }
  const credential = parts.Credential;
  const signedHeadersStr = parts.SignedHeaders;
  const signature = parts.Signature;
  if (!credential || !signedHeadersStr || !signature) return null;
  const credParts = credential.split("/");
  if (credParts.length !== 5 || credParts[4] !== "aws4_request") return null;
  return {
    algorithm: "AWS4-HMAC-SHA256",
    credential,
    accessKeyId: credParts[0]!,
    date: credParts[1]!,
    region: credParts[2]!,
    service: credParts[3]!,
    signedHeaders: signedHeadersStr.split(";").map(s => s.trim().toLowerCase()).sort(),
    signature,
  };
}

// ──────────────────────────────────────────────────────────────────────
// Helpers — canonical request
// ──────────────────────────────────────────────────────────────────────

function uriEncodePath(p: string): string {
  // AWS canonical URI: percent-encode each segment except `/`.
  return p
    .split("/")
    .map(seg => encodeURIComponent(seg)
      .replace(/[!'()*]/g, c => "%" + c.charCodeAt(0).toString(16).toUpperCase()))
    .join("/");
}

function canonicalQuery(qs: string): string {
  if (!qs) return "";
  const pairs: [string, string][] = [];
  for (const p of qs.split("&")) {
    if (!p) continue;
    const eq = p.indexOf("=");
    const k = eq < 0 ? p : p.slice(0, eq);
    const v = eq < 0 ? "" : p.slice(eq + 1);
    pairs.push([decodeURIComponent(k), decodeURIComponent(v)]);
  }
  pairs.sort((a, b) => (a[0] === b[0] ? (a[1] < b[1] ? -1 : 1) : a[0] < b[0] ? -1 : 1));
  return pairs
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join("&");
}

function canonicalHeadersBlock(req: Request, signedHeaders: string[]): string {
  const lines: string[] = [];
  for (const name of signedHeaders) {
    const val = req.headers.get(name) ?? "";
    lines.push(`${name}:${val.trim().replace(/\s+/g, " ")}`);
  }
  return lines.join("\n") + "\n";
}

async function sha256HexBytes(bytes: Uint8Array): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("");
}

async function sha256HexString(s: string): Promise<string> {
  return sha256HexBytes(new TextEncoder().encode(s));
}

async function hmacRaw(keyBytes: Uint8Array, msg: string): Promise<Uint8Array> {
  const key = await crypto.subtle.importKey(
    "raw", keyBytes, { name: "HMAC", hash: "SHA-256" }, false, ["sign"],
  );
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(msg));
  return new Uint8Array(sig);
}

function bytesToHex(b: Uint8Array): string {
  return Array.from(b).map(x => x.toString(16).padStart(2, "0")).join("");
}

// ──────────────────────────────────────────────────────────────────────
// Hyperdrive lookup
// ──────────────────────────────────────────────────────────────────────

async function lookupApiKeyRowByAwsAccessKeyId(
  env: SigV4VerifyEnv,
  awsAccessKeyId: string,
): Promise<CachedKeyRow | null> {
  const cached = _akCache.get(awsAccessKeyId);
  if (cached !== undefined && cached !== null && Date.now() - cached.at < AK_CACHE_TTL) {
    return cached;
  }
  if (cached === null && _akCache.has(awsAccessKeyId)) {
    return null;
  }
  // P86: KV mirror first (auth-cache populated at signup mint-time). The
  // Worker can no longer touch Hyperdrive directly (ADR-2605111200) so
  // when the KV row is present we use it as authoritative.
  try {
    const { lookupCachedAwsCreds } = await import("./auth-cache");
    const kvRow = await lookupCachedAwsCreds(env as never, awsAccessKeyId);
    if (kvRow) {
      const productScope: "yata" | "obj" | null = (() => {
        const ps = kvRow.productScope?.toLowerCase();
        return ps === "yata" ? "yata" : ps === "obj" ? "obj" : null;
      })();
      const row: CachedKeyRow = {
        ownerDid: kvRow.ownerDid,
        scopes: kvRow.scopes.split(/[,\s]+/).map(s => s.trim()).filter(Boolean),
        productScope,
        secret: kvRow.secret,
        at: Date.now(),
      };
      _akCache.set(awsAccessKeyId, row);
      return row;
    }
  } catch (e) {
    console.warn("[s3-sigv4] kv lookup threw:", e);
  }
  if (!env.HYPERDRIVE) return null;

  try {
    const sdk = await import("@etzhayyim/magatama-host-sdk");
    const db = sdk.createKyselyDb(env.HYPERDRIVE as never) as unknown as AnyKyselyDb;
    const row = await db
      .selectFrom("vertex_api_key")
      .select(["owner_did", "scopes", "product_scope", "aws_secret_access_key"])
      .where("aws_access_key_id", "=", awsAccessKeyId)
      .where("status", "=", "active")
      .limit(1)
      .executeTakeFirst();
    if (!row) {
      _akCache.set(awsAccessKeyId, null);
      return null;
    }
    const ownerDid = String(row.owner_did ?? "");
    if (!ownerDid.startsWith("did:")) {
      _akCache.set(awsAccessKeyId, null);
      return null;
    }
    const productScope = (() => {
      const ps = String(row.product_scope ?? "").toLowerCase();
      return ps === "yata" ? "yata" : ps === "obj" ? "obj" : null;
    })();
    const cacheRow: CachedKeyRow = {
      ownerDid,
      scopes: String(row.scopes ?? "read").split(/[,\s]+/).map(s => s.trim()).filter(Boolean),
      productScope,
      secret: String(row.aws_secret_access_key ?? ""),
      at: Date.now(),
    };
    _akCache.set(awsAccessKeyId, cacheRow);
    return cacheRow;
  } catch (e) {
    console.warn("[s3-sigv4] hyperdrive lookup failed:", e);
    return null;
  }
}

// ──────────────────────────────────────────────────────────────────────
// Verify
// ──────────────────────────────────────────────────────────────────────

export interface VerifyContext {
  /** Raw incoming Request (used for canonical query + canonical headers). */
  req: Request;
  /** Body bytes — read by the caller before invoking verify (we cannot
   *  read the stream twice). Pass empty Uint8Array for GET/HEAD/DELETE. */
  bodyBytes: Uint8Array;
  /** Hyperdrive binding for vertex_api_key lookup. */
  env: SigV4VerifyEnv;
}

/**
 * Verify an AWS SigV4 signed Request. Returns the resolved auth context
 * on success; null on any failure (invalid signature, expired, unknown
 * key, etc).
 *
 * Supports two flows (P3.2.6):
 *
 *   1. Header-based: `Authorization: AWS4-HMAC-SHA256 Credential=...,
 *      SignedHeaders=..., Signature=...` (boto3 default)
 *   2. Query-string-based: `?X-Amz-Algorithm=AWS4-HMAC-SHA256&
 *      X-Amz-Credential=...&X-Amz-Date=...&X-Amz-Expires=...&
 *      X-Amz-SignedHeaders=...&X-Amz-Signature=...` (presigned URLs)
 *
 * Pre-signed URL flow uses the same canonical request structure but
 * with the X-Amz-* parameters in the query string and the body hash
 * as `UNSIGNED-PAYLOAD`.
 */
export async function verifySigV4(ctx: VerifyContext): Promise<SigV4VerifyResult | null> {
  const url = new URL(ctx.req.url);
  if (url.searchParams.get("X-Amz-Algorithm") === "AWS4-HMAC-SHA256") {
    return verifySigV4QueryString(ctx, url);
  }
  const authHeader = ctx.req.headers.get("authorization") ?? "";
  const parsed = parseAuthorizationHeader(authHeader);
  if (!parsed) return null;

  // Clock skew check.
  const xAmzDate = ctx.req.headers.get("x-amz-date") ?? "";
  if (!/^[0-9]{8}T[0-9]{6}Z$/.test(xAmzDate)) return null;
  const reqEpoch = Date.UTC(
    Number(xAmzDate.slice(0, 4)),
    Number(xAmzDate.slice(4, 6)) - 1,
    Number(xAmzDate.slice(6, 8)),
    Number(xAmzDate.slice(9, 11)),
    Number(xAmzDate.slice(11, 13)),
    Number(xAmzDate.slice(13, 15)),
  ) / 1000;
  if (Math.abs(reqEpoch - Math.floor(Date.now() / 1000)) > SKEW_TOLERANCE_SEC) return null;

  // Look up the secret.
  const row = await lookupApiKeyRowByAwsAccessKeyId(ctx.env, parsed.accessKeyId);
  if (!row || !row.secret) return null;

  // Body hash. Trust the header value — recomputing here would force
  // the caller to buffer the body even for streaming upload.
  const bodyHashHeader = ctx.req.headers.get("x-amz-content-sha256") ?? "";
  let payloadHash: string;
  if (bodyHashHeader === "UNSIGNED-PAYLOAD" || bodyHashHeader === "STREAMING-UNSIGNED-PAYLOAD-TRAILER") {
    payloadHash = bodyHashHeader;
  } else if (bodyHashHeader) {
    payloadHash = bodyHashHeader;
  } else {
    payloadHash = await sha256HexBytes(ctx.bodyBytes);
  }

  // Canonical request. (`url` was hoisted at function entry above.)
  const canonReq = [
    ctx.req.method.toUpperCase(),
    uriEncodePath(url.pathname),
    canonicalQuery(url.search.slice(1)),
    canonicalHeadersBlock(ctx.req, parsed.signedHeaders),
    parsed.signedHeaders.join(";"),
    payloadHash,
  ].join("\n");

  // String-to-sign.
  const scope = `${parsed.date}/${parsed.region}/${parsed.service}/aws4_request`;
  const stringToSign = [
    "AWS4-HMAC-SHA256",
    xAmzDate,
    scope,
    await sha256HexString(canonReq),
  ].join("\n");

  // Derive signing key.
  const kDate = await hmacRaw(
    new TextEncoder().encode("AWS4" + row.secret),
    parsed.date,
  );
  const kRegion = await hmacRaw(kDate, parsed.region);
  const kService = await hmacRaw(kRegion, parsed.service);
  const kSigning = await hmacRaw(kService, "aws4_request");
  const sig = await hmacRaw(kSigning, stringToSign);
  const expected = bytesToHex(sig);

  if (expected.length !== parsed.signature.length) return null;
  let diff = 0;
  for (let i = 0; i < expected.length; i++) {
    diff |= expected.charCodeAt(i) ^ parsed.signature.charCodeAt(i);
  }
  if (diff !== 0) return null;

  return {
    ownerDid: row.ownerDid,
    scopes: row.scopes,
    productScope: row.productScope,
    awsAccessKeyId: parsed.accessKeyId,
  };
}

// ──────────────────────────────────────────────────────────────────────
// Pre-signed URL query-string flow (P3.2.6)
// ──────────────────────────────────────────────────────────────────────

/**
 * Verify a request that carries SigV4 in the query string instead of
 * the Authorization header. Used when the client follows a yatabase-
 * minted presigned URL.
 *
 * Required query parameters (all mandatory per AWS spec):
 *   X-Amz-Algorithm     = AWS4-HMAC-SHA256
 *   X-Amz-Credential    = <accessKeyId>/<date>/<region>/s3/aws4_request
 *   X-Amz-Date          = YYYYMMDDTHHMMSSZ
 *   X-Amz-Expires       = seconds (1..604800)
 *   X-Amz-SignedHeaders = host (typically just `host`)
 *   X-Amz-Signature     = hex
 */
async function verifySigV4QueryString(
  ctx: VerifyContext,
  url: URL,
): Promise<SigV4VerifyResult | null> {
  const credential = url.searchParams.get("X-Amz-Credential") ?? "";
  const date       = url.searchParams.get("X-Amz-Date") ?? "";
  const expiresStr = url.searchParams.get("X-Amz-Expires") ?? "";
  const signedHdrs = url.searchParams.get("X-Amz-SignedHeaders") ?? "host";
  const signature  = url.searchParams.get("X-Amz-Signature") ?? "";
  if (!credential || !date || !expiresStr || !signature) return null;

  const credParts = credential.split("/");
  if (credParts.length !== 5 || credParts[4] !== "aws4_request") return null;
  const accessKeyId = credParts[0]!;
  const dateShort   = credParts[1]!;
  const region      = credParts[2]!;
  const service     = credParts[3]!;

  if (!/^[0-9]{8}T[0-9]{6}Z$/.test(date)) return null;
  const reqEpoch = Date.UTC(
    Number(date.slice(0, 4)),
    Number(date.slice(4, 6)) - 1,
    Number(date.slice(6, 8)),
    Number(date.slice(9, 11)),
    Number(date.slice(11, 13)),
    Number(date.slice(13, 15)),
  ) / 1000;
  const expires = Number.parseInt(expiresStr, 10);
  if (!Number.isFinite(expires) || expires < 1 || expires > 604800) return null;
  if (Math.floor(Date.now() / 1000) > reqEpoch + expires) return null;

  const row = await lookupApiKeyRowByAwsAccessKeyId(ctx.env, accessKeyId);
  if (!row || !row.secret) return null;

  // Canonical query string: same params except X-Amz-Signature, sorted.
  const params: [string, string][] = [];
  for (const [k, v] of url.searchParams.entries()) {
    if (k === "X-Amz-Signature") continue;
    params.push([k, v]);
  }
  params.sort((a, b) => (a[0] === b[0] ? (a[1] < b[1] ? -1 : 1) : a[0] < b[0] ? -1 : 1));
  const canonicalQuery = params
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join("&");

  const signedNames = signedHdrs.split(";").map(s => s.trim().toLowerCase()).sort();
  const canonicalHeaders = signedNames
    .map(n => `${n}:${(ctx.req.headers.get(n) ?? "").trim().replace(/\s+/g, " ")}\n`)
    .join("");

  // Pre-signed URLs use UNSIGNED-PAYLOAD as the body hash.
  const payloadHash = "UNSIGNED-PAYLOAD";

  const canonReq = [
    ctx.req.method.toUpperCase(),
    uriEncodePath(url.pathname),
    canonicalQuery,
    canonicalHeaders,
    signedNames.join(";"),
    payloadHash,
  ].join("\n");

  const scope = `${dateShort}/${region}/${service}/aws4_request`;
  const stringToSign = [
    "AWS4-HMAC-SHA256",
    date,
    scope,
    await sha256HexString(canonReq),
  ].join("\n");

  const kDate    = await hmacRaw(new TextEncoder().encode("AWS4" + row.secret), dateShort);
  const kRegion  = await hmacRaw(kDate, region);
  const kService = await hmacRaw(kRegion, service);
  const kSigning = await hmacRaw(kService, "aws4_request");
  const sig      = await hmacRaw(kSigning, stringToSign);
  const expected = bytesToHex(sig);

  if (expected.length !== signature.length) return null;
  let diff = 0;
  for (let i = 0; i < expected.length; i++) {
    diff |= expected.charCodeAt(i) ^ signature.charCodeAt(i);
  }
  if (diff !== 0) return null;

  return {
    ownerDid: row.ownerDid,
    scopes: row.scopes,
    productScope: row.productScope,
    awsAccessKeyId: accessKeyId,
  };
}
