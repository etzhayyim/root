#!/usr/bin/env bash
# scaffold-google-app.sh — generate per-service Google Workspace ingest app.
#
# Creates 60-apps/ai-gftd-project-{service}/appview/{service}-mcp-component/
# with magatama.jsonld, wrangler.jsonc, src/app.ts pre-wired for OAuth2 +
# unified-scope consent + scheduled sync. Each app's sync function is a
# TODO stub — operators wire the per-API client (events.list / files.list /
# people.connections.list / tasks.list / documents.get / spreadsheets.get /
# presentations.get / conferenceRecords.list).
#
# Usage:
#   scaffold-google-app.sh drive    drive.etzhayyim.com    GDRIVE     "Google Drive"
#   scaffold-google-app.sh contacts contacts.etzhayyim.com GCONTACTS  "Google Contacts"
#   scaffold-google-app.sh tasks    tasks.etzhayyim.com    GTASKS     "Google Tasks"
#   scaffold-google-app.sh docs     docs.etzhayyim.com     GDOCS      "Google Docs"
#   scaffold-google-app.sh sheets   sheets.etzhayyim.com   GSHEETS    "Google Sheets"
#   scaffold-google-app.sh slides   slides.etzhayyim.com   GSLIDES    "Google Slides"
#   scaffold-google-app.sh meet     meet.etzhayyim.com     GMEET      "Google Meet"
#
# After scaffolding:
#   1. wrangler d1 create {service}-tokens   # paste id into wrangler.jsonc
#   2. gftd deploy
#   3. Repeat OAuth consent per account.

set -euo pipefail

SVC="${1:?service name required (drive|contacts|tasks|docs|sheets|slides|meet)}"
DOMAIN="${2:?domain required (e.g. drive.etzhayyim.com)}"
DB_PREFIX="${3:?db var prefix (e.g. GDRIVE)}"
DISPLAY_NAME="${4:?display name required}"

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PROJ_DIR="${REPO_ROOT}/60-apps/ai-gftd-project-${SVC}"
APP_DIR="${PROJ_DIR}/appview/${SVC}-mcp-component"
SRC_DIR="${APP_DIR}/src"

mkdir -p "$SRC_DIR"

NANOID="${SVC}-mcp"
COLLECTION_PREFIX="ai.gftd.apps.${SVC}"
DB_BINDING="${DB_PREFIX}_DB"
DB_NAME="${SVC}-tokens"
TOKEN_TABLE="vertex_$(echo "$DB_PREFIX" | tr 'A-Z' 'a-z')_oauth_token"

cat > "${APP_DIR}/magatama.jsonld" <<EOF
{
  "@context": "https://etzhayyim.com/ns/magatama/v1",
  "@id": "did:web:${DOMAIN}",
  "name": "${SVC}",
  "nanoid": "${NANOID}",
  "performerType": "service",
  "runtimeType": "worker",
  "project": "${SVC}",
  "profile": {
    "displayName": "${DISPLAY_NAME}",
    "description": "${DISPLAY_NAME} ingest — OAuth2 + continuous sync into RisingWave graph",
    "isBot": true,
    "agentType": "autonomous",
    "category": "google-workspace",
    "operator": "etzhayyim",
    "capabilities": ["domain-query","data-management","oauth"]
  },
  "triggers": {
    "subscribeRepos": {
      "collections": [
        "${COLLECTION_PREFIX}.account",
        "${COLLECTION_PREFIX}.syncJob"
      ]
    }
  }
}
EOF

cat > "${APP_DIR}/wrangler.jsonc" <<EOF
{
  "name": "magatama-${NANOID}",
  "main": "src/app.ts",
  "compatibility_date": "2025-03-17",
  "compatibility_flags": ["nodejs_compat","nodejs_als"],
  "vars": {
    "APP_NANOID": "${NANOID}",
    "APP_DISPLAY_NAME": "${DISPLAY_NAME}",
    "APP_FRAMEWORK": "ts-native",
    "APP_PERFORMER_TYPE": "service",
    "APP_UI_TYPE": "appview"
  },
  "hyperdrive": [
    { "binding": "HYPERDRIVE", "id": "e84c0a2babe44fc7b74818e394b4b896" }
  ],
  "d1_databases": [
    { "binding": "${DB_BINDING}", "database_name": "${DB_NAME}", "database_id": "REPLACE_AFTER_wrangler_d1_create" }
  ],
  "services": [
    { "binding": "PDS_SERVICE", "service": "ai-gftd-pds-2603241700" },
    { "binding": "PDS_RPC", "service": "ai-gftd-pds-2603241700", "entrypoint": "PdsRPC" }
  ],
  "secrets_store_secrets": [
    { "binding": "SS_GOOGLE_OAUTH_CLIENT_ID", "store_id": "1824561668fe47cc9127d493961885af", "secret_name": "google_oauth_client_id" },
    { "binding": "SS_GOOGLE_OAUTH_CLIENT_SECRET", "store_id": "1824561668fe47cc9127d493961885af", "secret_name": "google_oauth_client_secret" },
    { "binding": "SS_GWORKSPACE_TOKEN_KEK", "store_id": "1824561668fe47cc9127d493961885af", "secret_name": "gworkspace_token_kek" }
  ],
  "triggers": {
    "crons": ["*/30 * * * *"]
  },
  "routes": [
    { "pattern": "${DOMAIN}/*", "zone_name": "etzhayyim.com" }
  ]
}
EOF

cat > "${SRC_DIR}/app.ts" <<APPEOF
import {
  asAgentTool,
  createWorkerExport,
  withCapabilityTags,
  type HostSDK,
  nowISO,
  str,
  genID,
  nsid,
} from "@gftd/magatama-host-sdk";

// ─────────────────────────────────────────────────────────────────────────
// ai-gftd-project-${SVC} — ${DISPLAY_NAME} ingest (Phase 0 scaffold).
//
// OAuth2 unified-scope consent + KEK-enveloped refresh tokens in D1
// + scheduled per-account sync. Per-API client TODO — wire to:
//   ${COLLECTION_PREFIX}.* records → graph migration
//   30-graph/graph-schema/migrations/20260417140000_vertex_google_workspace_tables.ts
//
// Pattern: 60-apps/ai-gftd-project-gmail/appview/ai-gftd-wasm-gmail-gm4il0x1/src/app.ts
// Template: 70-tools/templates/google-workspace-oauth.ts
// ─────────────────────────────────────────────────────────────────────────

interface Env {
  ${DB_BINDING}?: D1Database;
  SS_GOOGLE_OAUTH_CLIENT_ID?: string;
  SS_GOOGLE_OAUTH_CLIENT_SECRET?: string;
  SS_GWORKSPACE_TOKEN_KEK?: string;
}
interface D1Database { prepare(q: string): D1PreparedStatement; exec(q: string): Promise<unknown> }
interface D1PreparedStatement { bind(...v: unknown[]): D1PreparedStatement; run(): Promise<{ success: boolean }>; first<T=Record<string,unknown>>(): Promise<T|null>; all<T=Record<string,unknown>>(): Promise<{ results: T[] }> }

const REDIRECT_URI = "https://${DOMAIN}/oauth/callback";
const TOKEN_TABLE = "${TOKEN_TABLE}";
const SCOPES = [
  "openid","email","profile",
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

function b64uEnc(buf: ArrayBuffer | Uint8Array): string { const b = buf instanceof Uint8Array ? buf : new Uint8Array(buf); let s = ""; for (const x of b) s += String.fromCharCode(x); return btoa(s).replace(/\+/g,"-").replace(/\//g,"_").replace(/=+$/g,""); }
function b64uDec(s: string): Uint8Array { let t = s.replace(/-/g,"+").replace(/_/g,"/"); while (t.length%4) t += "="; return Uint8Array.from(atob(t), c => c.charCodeAt(0)); }
async function importKek(k: string) { return crypto.subtle.importKey("raw", b64uDec(k), { name: "AES-GCM" }, false, ["encrypt","decrypt"]); }
async function envEnc(k: string, pt: string) { const kek=await importKek(k); const dk=crypto.getRandomValues(new Uint8Array(32)); const iv=crypto.getRandomValues(new Uint8Array(12)); const dkC=await crypto.subtle.importKey("raw",dk,{name:"AES-GCM"},false,["encrypt"]); const ct=await crypto.subtle.encrypt({name:"AES-GCM",iv},dkC,new TextEncoder().encode(pt)); const wr=await crypto.subtle.encrypt({name:"AES-GCM",iv},kek,dk); return { ciphertext: b64uEnc(ct), wrappedDataKey: b64uEnc(wr), iv: b64uEnc(iv) }; }
async function envDec(k: string, ct: string, wr: string, iv: string) { const kek=await importKek(k); const ivB=b64uDec(iv); const dkBuf=await crypto.subtle.decrypt({name:"AES-GCM",iv:ivB},kek,b64uDec(wr)); const dkC=await crypto.subtle.importKey("raw",dkBuf,{name:"AES-GCM"},false,["decrypt"]); const pt=await crypto.subtle.decrypt({name:"AES-GCM",iv:ivB},dkC,b64uDec(ct)); return new TextDecoder().decode(pt); }
function decodeJwt(jwt: string): Record<string,unknown> { const p=jwt.split("."); if (p.length!==3) return {}; try { return JSON.parse(new TextDecoder().decode(b64uDec(p[1]))); } catch { return {}; } }
async function exchangeAuthCode(env: Env, code: string) { if (!env.SS_GOOGLE_OAUTH_CLIENT_ID||!env.SS_GOOGLE_OAUTH_CLIENT_SECRET) throw new Error("Google OAuth creds missing"); const body=new URLSearchParams({code, client_id: env.SS_GOOGLE_OAUTH_CLIENT_ID, client_secret: env.SS_GOOGLE_OAUTH_CLIENT_SECRET, redirect_uri: REDIRECT_URI, grant_type: "authorization_code"}); const r=await fetch("https://oauth2.googleapis.com/token", {method: "POST", headers: {"content-type": "application/x-www-form-urlencoded"}, body: body.toString()}); if (!r.ok) throw new Error(\`token exchange: \${r.status} \${await r.text()}\`); return r.json() as Promise<{access_token: string; refresh_token?: string; expires_in: number; scope: string; id_token?: string}>; }
async function refreshAccess(env: Env, rt: string) { if (!env.SS_GOOGLE_OAUTH_CLIENT_ID||!env.SS_GOOGLE_OAUTH_CLIENT_SECRET) throw new Error("Google OAuth creds missing"); const body=new URLSearchParams({refresh_token: rt, client_id: env.SS_GOOGLE_OAUTH_CLIENT_ID, client_secret: env.SS_GOOGLE_OAUTH_CLIENT_SECRET, grant_type: "refresh_token"}); const r=await fetch("https://oauth2.googleapis.com/token", {method: "POST", headers: {"content-type": "application/x-www-form-urlencoded"}, body: body.toString()}); if (!r.ok) throw new Error(\`token refresh: \${r.status} \${await r.text()}\`); return r.json() as Promise<{access_token: string; expires_in: number}>; }

interface TokenRow { account_did: string; email: string; encrypted_refresh_token: string; wrapped_data_key: string; iv: string; scope: string; access_token_cache: string|null; access_expires_at: number|null; status: string; cursor: string|null; last_sync_at: string|null }

let _tableReady: Promise<unknown>|null = null;
async function ensureTable(env: Env) {
  if (!env.${DB_BINDING}) throw new Error("${DB_BINDING} binding missing");
  if (!_tableReady) {
    _tableReady = env.${DB_BINDING}.exec(\`CREATE TABLE IF NOT EXISTS \${TOKEN_TABLE} (
      vertex_id TEXT PRIMARY KEY,
      account_did TEXT NOT NULL, email TEXT NOT NULL,
      encrypted_refresh_token TEXT NOT NULL, wrapped_data_key TEXT NOT NULL, iv TEXT NOT NULL,
      scope TEXT NOT NULL, access_token_cache TEXT, access_expires_at INTEGER,
      status TEXT NOT NULL DEFAULT 'active', cursor TEXT, last_sync_at TEXT,
      created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
      UNIQUE(account_did, email))\`);
  }
  await _tableReady;
}
async function storeToken(env: Env, accountDid: string, email: string, rt: string, scope: string) {
  if (!env.SS_GWORKSPACE_TOKEN_KEK) throw new Error("SS_GWORKSPACE_TOKEN_KEK missing");
  await ensureTable(env);
  const e = await envEnc(env.SS_GWORKSPACE_TOKEN_KEK, rt);
  const now = nowISO();
  await env.${DB_BINDING}!.prepare(\`INSERT INTO \${TOKEN_TABLE} (vertex_id, account_did, email, encrypted_refresh_token, wrapped_data_key, iv, scope, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?, 'active', ?, ?) ON CONFLICT(account_did,email) DO UPDATE SET encrypted_refresh_token=excluded.encrypted_refresh_token, wrapped_data_key=excluded.wrapped_data_key, iv=excluded.iv, scope=excluded.scope, status='active', updated_at=excluded.updated_at\`).bind(\`\${accountDid}|\${email}\`, accountDid, email, e.ciphertext, e.wrappedDataKey, e.iv, scope, now, now).run();
}
async function loadByEmail(env: Env, email: string): Promise<TokenRow|null> {
  await ensureTable(env);
  return env.${DB_BINDING}!.prepare(\`SELECT * FROM \${TOKEN_TABLE} WHERE email=? AND status='active' LIMIT 1\`).bind(email).first<TokenRow>();
}
async function getAccess(env: Env, t: TokenRow): Promise<string> {
  const now = Math.floor(Date.now()/1000);
  if (t.access_token_cache && t.access_expires_at && t.access_expires_at > now+30) return t.access_token_cache;
  const rt = await envDec(env.SS_GWORKSPACE_TOKEN_KEK!, t.encrypted_refresh_token, t.wrapped_data_key, t.iv);
  const fresh = await refreshAccess(env, rt);
  const exp = now + fresh.expires_in;
  await env.${DB_BINDING}!.prepare(\`UPDATE \${TOKEN_TABLE} SET access_token_cache=?, access_expires_at=?, updated_at=? WHERE account_did=? AND email=?\`).bind(fresh.access_token, exp, nowISO(), t.account_did, t.email).run();
  return fresh.access_token;
}

function write(sdk: HostSDK, collection: string, rec: Record<string, unknown>): void {
  const full = \`${COLLECTION_PREFIX}.\${collection}\`;
  const pds = sdk.pds as unknown as { createRecord?: (c: string, r: Record<string, unknown>) => unknown; dispatch?: (m: { type: string; payload: unknown }) => unknown };
  if (typeof pds.createRecord === "function") { pds.createRecord(full, rec); return; }
  pds.dispatch?.({ type: "com.atproto.repo.createRecord", payload: { collection: full, recordJson: JSON.stringify(rec) } });
}

// ── Per-service Google API sync — TODO: implement against ${COLLECTION_PREFIX}.* schema.
// See 30-graph/graph-schema/migrations/20260417140000_vertex_google_workspace_tables.ts
// for the canonical column list.
async function syncFromGoogle(_sdk: HostSDK, env: Env, token: TokenRow): Promise<{ synced: number }> {
  const accessToken = await getAccess(env, token);
  // TODO Phase 1: replace this no-op with the real list/changes call:
  //   - drive    → GET /drive/v3/changes?pageToken=...
  //   - contacts → GET /v1/people/me/connections?syncToken=...
  //   - tasks    → GET /tasks/v1/users/@me/lists then /lists/{id}/tasks
  //   - docs/sheets/slides → driven by drive changes feed; fetch by file_id
  //   - meet     → GET /v2/conferenceRecords?filter=start_time>...
  void accessToken;
  return { synced: 0 };
}

export default createWorkerExport((sdk: HostSDK) => {
  const env = sdk.env as unknown as Env;

  sdk.router.get("/oauth/callback", async (c) => {
    const url = new URL(c.req.url);
    const code = url.searchParams.get("code");
    const err = url.searchParams.get("error");
    const state = url.searchParams.get("state") ?? "";
    if (err) return c.html(\`<h1>${SVC} connect failed</h1><p>\${err}</p>\`, 400);
    if (!code) return c.html(\`<h1>Missing code</h1>\`, 400);
    try {
      const tokens = await exchangeAuthCode(env, code);
      if (!tokens.refresh_token) throw new Error("no refresh_token (revoke prior consent at myaccount.google.com/permissions)");
      const idP = tokens.id_token ? decodeJwt(tokens.id_token) : {};
      const email = str(idP.email ?? "");
      if (!email) throw new Error("email missing from id_token");
      const accountDid = state || "did:anonymous";
      await storeToken(env, accountDid, email, tokens.refresh_token, tokens.scope ?? SCOPES);
      write(sdk, "account", { accountDid, email, displayName: str(idP.name ?? ""), status: "active", scope: tokens.scope ?? SCOPES, connectedAt: nowISO(), createdAt: nowISO() });
      return c.html(\`<h1>${DISPLAY_NAME} connected</h1><p>\${email}</p>\`);
    } catch (e) { return c.html(\`<h1>${SVC} connect error</h1><pre>\${(e as Error).message}</pre>\`, 500); }
  });

  sdk.app.command(nsid("${COLLECTION_PREFIX}.connectAccount"),
    async (ctx, params) => {
      if (!env.SS_GOOGLE_OAUTH_CLIENT_ID) return { error: "SS_GOOGLE_OAUTH_CLIENT_ID not configured" };
      const accountDid = str((ctx as unknown as { did?: string })?.did ?? params?.accountDid ?? "did:anonymous");
      const email = str(params?.email ?? "");
      const url = \`https://accounts.google.com/o/oauth2/v2/auth?client_id=\${encodeURIComponent(env.SS_GOOGLE_OAUTH_CLIENT_ID)}&redirect_uri=\${encodeURIComponent(REDIRECT_URI)}&response_type=code&scope=\${encodeURIComponent(SCOPES)}&state=\${encodeURIComponent(accountDid)}&access_type=offline&prompt=consent\${email ? \`&login_hint=\${encodeURIComponent(email)}\` : ""}\`;
      return { status: "pending_oauth", oauthUrl: url };
    },
    asAgentTool("Start ${DISPLAY_NAME} OAuth2 connect flow"),
    withCapabilityTags("${SVC}", "google", "oauth"),
  );

  sdk.app.command(nsid("${COLLECTION_PREFIX}.syncFromGoogle"),
    async (_ctx, params) => {
      const email = str(params?.email ?? "");
      if (!email) return { error: "email required" };
      const t = await loadByEmail(env, email);
      if (!t) return { error: "No active account. connectAccount first." };
      const jobId = \`gsync-\${genID()}\`;
      try {
        const r = await syncFromGoogle(sdk, env, t);
        write(sdk, "syncJob", { jobId, email, kind: "google", status: "completed", messagesSynced: r.synced, completedAt: nowISO(), createdAt: nowISO() });
        return { jobId, synced: r.synced };
      } catch (e) {
        write(sdk, "syncJob", { jobId, email, kind: "google", status: "failed", error: (e as Error).message, completedAt: nowISO(), createdAt: nowISO() });
        return { error: (e as Error).message, jobId, status: "failed" };
      }
    },
    asAgentTool("Sync ${DISPLAY_NAME} into the graph"),
    withCapabilityTags("${SVC}", "google", "sync"),
  );

  sdk.app.scheduled?.(async () => {
    if (!env.${DB_BINDING}) return;
    try {
      await ensureTable(env);
      const { results } = await env.${DB_BINDING}.prepare(\`SELECT * FROM \${TOKEN_TABLE} WHERE status='active' ORDER BY COALESCE(last_sync_at, created_at) ASC LIMIT 10\`).all<TokenRow>();
      for (const t of results) {
        try { await syncFromGoogle(sdk, env, t); }
        catch (e) { console.error(\`[${SVC}] gsync \${t.email}: \${(e as Error).message}\`); }
      }
    } catch (e) { console.error(\`[${SVC}] cron error: \${(e as Error).message}\`); }
  });
});
APPEOF

echo "✅ scaffolded ${APP_DIR}"
echo "   next:"
echo "     wrangler d1 create ${DB_NAME}    # paste id into wrangler.jsonc"
echo "     cd ${APP_DIR} && gftd deploy"
echo "     # implement syncFromGoogle() per ${COLLECTION_PREFIX}.* schema"
