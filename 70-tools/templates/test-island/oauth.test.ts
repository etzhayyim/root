/**
 * google-workspace-oauth template — helper tests (coverage loop iteration 18).
 *
 * The OAuth template ships the security-relevant primitives every Google
 * Workspace integration copies: base64url, KEK envelope AES-GCM (refresh
 * tokens at rest), JWT payload decode, and the consent-URL builder. Zero
 * tests. Pure WebCrypto/stdlib; isolated island keeps the root pnpm-lock
 * untouched.
 */
import { describe, it, expect } from "vitest";
import {
  b64uEncode, b64uDecode,
  envelopeEncrypt, envelopeDecrypt,
  decodeJwtPayload,
  buildAuthUrl,
  buildTokenTableDdl,
  GOOGLE_WORKSPACE_UNIFIED_SCOPES,
} from "../google-workspace-oauth.ts";

// 32-byte KEK, base64url (AES-256-GCM)
const KEK = b64uEncode(new Uint8Array(32).map((_, i) => (i * 7) & 0xff));

// ── base64url ────────────────────────────────────────────────────────────────

describe("b64url", () => {
  it("roundtrips arbitrary bytes with url-safe, unpadded output", () => {
    const bytes = new Uint8Array([0, 1, 250, 251, 252, 253, 254, 255, 62, 63]);
    const enc = b64uEncode(bytes);
    expect(enc).not.toMatch(/[+/=]/);
    expect(Array.from(b64uDecode(enc))).toEqual(Array.from(bytes));
  });

  it("accepts an ArrayBuffer and decodes its own encoding of empty", () => {
    expect(b64uEncode(new Uint8Array([1, 2, 3]).buffer)).toBe(b64uEncode(new Uint8Array([1, 2, 3])));
    expect(Array.from(b64uDecode(b64uEncode(new Uint8Array())))).toEqual([]);
  });
});

// ── KEK envelope encryption ──────────────────────────────────────────────────

describe("envelope AES-GCM", () => {
  it("encrypt → decrypt recovers the plaintext; each envelope is unique", async () => {
    const env = await envelopeEncrypt(KEK, "refresh-token-секрет");
    expect(env.ciphertext).not.toContain("refresh");
    expect(await envelopeDecrypt(KEK, env.ciphertext, env.wrappedDataKey, env.iv)).toBe("refresh-token-секрет");
    const env2 = await envelopeEncrypt(KEK, "refresh-token-секрет");
    expect(env2.iv).not.toBe(env.iv); // fresh random IV + data key per call
    expect(env2.ciphertext).not.toBe(env.ciphertext);
  });

  it("a wrong KEK cannot unwrap the data key", async () => {
    const env = await envelopeEncrypt(KEK, "secret");
    const wrongKek = b64uEncode(new Uint8Array(32).fill(9));
    await expect(envelopeDecrypt(wrongKek, env.ciphertext, env.wrappedDataKey, env.iv)).rejects.toThrow();
  });

  it("tampered ciphertext fails the GCM tag", async () => {
    const env = await envelopeEncrypt(KEK, "secret");
    const raw = b64uDecode(env.ciphertext);
    raw[0] ^= 0x01;
    await expect(envelopeDecrypt(KEK, b64uEncode(raw), env.wrappedDataKey, env.iv)).rejects.toThrow();
  });
});

// ── JWT payload decode ───────────────────────────────────────────────────────

describe("decodeJwtPayload", () => {
  it("decodes the payload segment of a 3-part JWT", () => {
    const payload = { sub: "123", email: "a@b.test", exp: 9999999999 };
    const jwt = `header.${b64uEncode(new TextEncoder().encode(JSON.stringify(payload)))}.sig`;
    expect(decodeJwtPayload(jwt)).toEqual(payload);
  });

  it("returns {} for a non-3-part token or undecodable payload", () => {
    expect(decodeJwtPayload("only.two")).toEqual({});
    expect(decodeJwtPayload("a.!!!notbase64json!!!.c")).toEqual({});
  });
});

// ── OAuth consent URL ────────────────────────────────────────────────────────

describe("buildAuthUrl", () => {
  it("builds the consent URL with offline access + forced consent and encodes params", () => {
    const url = buildAuthUrl("client&1", "https://app.test/cb?x=1", "st ate", "scope a", "user@x.test");
    const u = new URL(url);
    expect(u.origin + u.pathname).toBe("https://accounts.google.com/o/oauth2/v2/auth");
    const q = u.searchParams;
    expect(q.get("client_id")).toBe("client&1");          // decoded back → was encoded
    expect(q.get("redirect_uri")).toBe("https://app.test/cb?x=1");
    expect(q.get("response_type")).toBe("code");
    expect(q.get("scope")).toBe("scope a");
    expect(q.get("state")).toBe("st ate");
    expect(q.get("access_type")).toBe("offline");
    expect(q.get("prompt")).toBe("consent");
    expect(q.get("login_hint")).toBe("user@x.test");
  });

  it("omits login_hint when not provided", () => {
    expect(buildAuthUrl("c", "r", "s", "scope")).not.toContain("login_hint");
  });
});

// ── misc ─────────────────────────────────────────────────────────────────────

describe("token table DDL + unified scopes", () => {
  it("DDL is idempotent (IF NOT EXISTS) and uses the given table name", () => {
    const ddl = buildTokenTableDdl("vertex_gmail_tokens");
    expect(ddl).toContain("CREATE TABLE IF NOT EXISTS vertex_gmail_tokens");
    expect(ddl).toContain("encrypted_refresh_token TEXT NOT NULL");
  });

  it("unified scopes include openid + the core workspace APIs as a space-joined string", () => {
    const scopes = GOOGLE_WORKSPACE_UNIFIED_SCOPES.split(" ");
    expect(scopes).toContain("openid");
    expect(scopes).toContain("https://www.googleapis.com/auth/gmail.modify");
    expect(scopes).toContain("https://www.googleapis.com/auth/calendar");
    expect(scopes).toContain("https://www.googleapis.com/auth/drive");
    expect(new Set(scopes).size).toBe(scopes.length); // no duplicates
  });
});
