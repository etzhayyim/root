// ─────────────────────────────────────────────────────────────────────────
// google-workspace-oauth.ts — shared OAuth2 / KEK envelope / Google API
// helpers for Google Workspace ingest apps.
//
// USAGE: **Inline-copy** these helpers into each app's src/app.ts.
// Per 60-apps/CLAUDE.md "Single-file principle (CRITICAL)", imports
// between app files are forbidden. This template is a reference only.
//
// Apps that inline this: gmail (live), calendar, drive, contacts, tasks,
// docs, sheets, slides, meet.
// ─────────────────────────────────────────────────────────────────────────

// ── Env typing (extend per app) ────────────────────────────────────────
export interface GoogleWorkspaceEnv {
  /** per-app D1 binding, e.g. CALENDAR_DB / DRIVE_DB / CONTACTS_DB / ... */
  [dbKey: string]: unknown;
  /** Google Cloud Console Web OAuth client id */
  SS_GOOGLE_OAUTH_CLIENT_ID?: string;
  /** Google Cloud Console Web OAuth client secret */
  SS_GOOGLE_OAUTH_CLIENT_SECRET?: string;
  /** 32-byte base64url KEK shared across all Workspace apps for token envelope */
  SS_GWORKSPACE_TOKEN_KEK?: string;
}

export interface D1Database {
  prepare(query: string): D1PreparedStatement;
  batch(stmts: D1PreparedStatement[]): Promise<unknown[]>;
  exec(query: string): Promise<unknown>;
}
export interface D1PreparedStatement {
  bind(...values: unknown[]): D1PreparedStatement;
  run(): Promise<{ success: boolean }>;
  first<T = Record<string, unknown>>(): Promise<T | null>;
  all<T = Record<string, unknown>>(): Promise<{ results: T[] }>;
}

// ── base64url (compact) ────────────────────────────────────────────────
export function b64uEncode(buf: ArrayBuffer | Uint8Array): string {
  const bytes = buf instanceof Uint8Array ? buf : new Uint8Array(buf);
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}
export function b64uDecode(s: string): Uint8Array {
  let t = s.replace(/-/g, "+").replace(/_/g, "/");
  while (t.length % 4) t += "=";
  return Uint8Array.from(atob(t), (c) => c.charCodeAt(0));
}

// ── KEK envelope encryption (ADR-0010 Stage 1) ────────────────────────
export async function importKek(kekB64: string): Promise<CryptoKey> {
  return crypto.subtle.importKey("raw", b64uDecode(kekB64), { name: "AES-GCM" }, false, ["encrypt", "decrypt"]);
}
export async function envelopeEncrypt(
  kekB64: string,
  plaintext: string,
): Promise<{ ciphertext: string; wrappedDataKey: string; iv: string }> {
  const kek = await importKek(kekB64);
  const dataKey = crypto.getRandomValues(new Uint8Array(32));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const dataKeyCrypto = await crypto.subtle.importKey("raw", dataKey, { name: "AES-GCM" }, false, ["encrypt"]);
  const ct = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, dataKeyCrypto, new TextEncoder().encode(plaintext));
  const wrapped = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, kek, dataKey);
  return { ciphertext: b64uEncode(ct), wrappedDataKey: b64uEncode(wrapped), iv: b64uEncode(iv) };
}
export async function envelopeDecrypt(
  kekB64: string,
  ciphertext: string,
  wrappedDataKey: string,
  ivB64: string,
): Promise<string> {
  const kek = await importKek(kekB64);
  const iv = b64uDecode(ivB64);
  const dataKeyBuf = await crypto.subtle.decrypt({ name: "AES-GCM", iv }, kek, b64uDecode(wrappedDataKey));
  const dataKeyCrypto = await crypto.subtle.importKey("raw", dataKeyBuf, { name: "AES-GCM" }, false, ["decrypt"]);
  const pt = await crypto.subtle.decrypt({ name: "AES-GCM", iv }, dataKeyCrypto, b64uDecode(ciphertext));
  return new TextDecoder().decode(pt);
}

// ── OAuth2 token exchange ──────────────────────────────────────────────
export interface GoogleTokenResponse {
  access_token: string;
  refresh_token?: string;
  expires_in: number;
  scope: string;
  id_token?: string;
}

export async function exchangeAuthCode(
  env: GoogleWorkspaceEnv,
  code: string,
  redirectUri: string,
): Promise<GoogleTokenResponse> {
  if (!env.SS_GOOGLE_OAUTH_CLIENT_ID || !env.SS_GOOGLE_OAUTH_CLIENT_SECRET) {
    throw new Error("Google OAuth client credentials not configured");
  }
  const body = new URLSearchParams({
    code,
    client_id: env.SS_GOOGLE_OAUTH_CLIENT_ID,
    client_secret: env.SS_GOOGLE_OAUTH_CLIENT_SECRET,
    redirect_uri: redirectUri,
    grant_type: "authorization_code",
  });
  const resp = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });
  if (!resp.ok) throw new Error(`token exchange failed: ${resp.status} ${await resp.text()}`);
  return resp.json() as Promise<GoogleTokenResponse>;
}

export async function refreshAccessToken(
  env: GoogleWorkspaceEnv,
  refreshToken: string,
): Promise<GoogleTokenResponse> {
  if (!env.SS_GOOGLE_OAUTH_CLIENT_ID || !env.SS_GOOGLE_OAUTH_CLIENT_SECRET) {
    throw new Error("Google OAuth client credentials not configured");
  }
  const body = new URLSearchParams({
    refresh_token: refreshToken,
    client_id: env.SS_GOOGLE_OAUTH_CLIENT_ID,
    client_secret: env.SS_GOOGLE_OAUTH_CLIENT_SECRET,
    grant_type: "refresh_token",
  });
  const resp = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: body.toString(),
  });
  if (!resp.ok) throw new Error(`token refresh failed: ${resp.status} ${await resp.text()}`);
  return resp.json() as Promise<GoogleTokenResponse>;
}

export function decodeJwtPayload(jwt: string): Record<string, unknown> {
  const parts = jwt.split(".");
  if (parts.length !== 3) return {};
  try {
    return JSON.parse(new TextDecoder().decode(b64uDecode(parts[1])));
  } catch {
    return {};
  }
}

// ── Token store (D1, per-app). Table name varies per service. ─────────
export interface TokenRow {
  account_did: string;
  email: string;
  encrypted_refresh_token: string;
  wrapped_data_key: string;
  iv: string;
  scope: string;
  access_token_cache: string | null;
  access_expires_at: number | null;
  status: string;
  /** service-specific cursor: Gmail history_id, Calendar syncToken, Drive startPageToken, ... */
  cursor: string | null;
  last_sync_at: string | null;
}

export function buildTokenTableDdl(tableName: string): string {
  return `CREATE TABLE IF NOT EXISTS ${tableName} (
    vertex_id TEXT PRIMARY KEY,
    account_did TEXT NOT NULL,
    email TEXT NOT NULL,
    encrypted_refresh_token TEXT NOT NULL,
    wrapped_data_key TEXT NOT NULL,
    iv TEXT NOT NULL,
    scope TEXT NOT NULL,
    access_token_cache TEXT,
    access_expires_at INTEGER,
    status TEXT NOT NULL DEFAULT 'active',
    cursor TEXT,
    last_sync_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(account_did, email)
  )`;
}

// ── Unified scopes requested on every consent (one grant, all services) ─
export const GOOGLE_WORKSPACE_UNIFIED_SCOPES = [
  "openid",
  "email",
  "profile",
  "https://www.googleapis.com/auth/gmail.modify",
  "https://www.googleapis.com/auth/calendar",
  "https://www.googleapis.com/auth/drive",
  "https://www.googleapis.com/auth/contacts.readonly",
  "https://www.googleapis.com/auth/contacts.other.readonly",
  "https://www.googleapis.com/auth/directory.readonly",
  "https://www.googleapis.com/auth/tasks",
  "https://www.googleapis.com/auth/documents.readonly",
  "https://www.googleapis.com/auth/spreadsheets.readonly",
  "https://www.googleapis.com/auth/presentations.readonly",
  "https://www.googleapis.com/auth/meetings.space.readonly",
].join(" ");

export function buildAuthUrl(
  clientId: string,
  redirectUri: string,
  state: string,
  scope: string,
  loginHint?: string,
): string {
  return (
    `https://accounts.google.com/o/oauth2/v2/auth` +
    `?client_id=${encodeURIComponent(clientId)}` +
    `&redirect_uri=${encodeURIComponent(redirectUri)}` +
    `&response_type=code` +
    `&scope=${encodeURIComponent(scope)}` +
    `&state=${encodeURIComponent(state)}` +
    `&access_type=offline` +
    `&prompt=consent` +
    (loginHint ? `&login_hint=${encodeURIComponent(loginHint)}` : "")
  );
}

// ── Authenticated fetch helpers ───────────────────────────────────────
export async function googleApiGet<T>(
  accessToken: string,
  url: string,
): Promise<T> {
  const resp = await fetch(url, { headers: { Authorization: `Bearer ${accessToken}` } });
  if (!resp.ok) throw new Error(`google api GET ${url}: ${resp.status} ${await resp.text()}`);
  return resp.json() as Promise<T>;
}

export async function googleApiPost<T>(
  accessToken: string,
  url: string,
  body: unknown,
): Promise<T> {
  const resp = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "content-type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new Error(`google api POST ${url}: ${resp.status} ${await resp.text()}`);
  return resp.json() as Promise<T>;
}
